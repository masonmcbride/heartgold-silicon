// Symbol identity and constants in a relocatable guest image. MIT
#include "llvm/IR/Operator.h"
#include "llvm/IR/IntrinsicInst.h"
#include "llvm/IR/Intrinsics.h"
static Function *directCallee(const CallBase &Call){return dyn_cast<Function>(Call.getCalledOperand()->stripPointerCasts());}
static std::string typeText(Type *T){std::string S;raw_string_ostream OS(S);T->print(OS);return S;}
static json::Value describeType(Type *T){
  if(auto *A=dyn_cast<ArrayType>(T))return json::Object{{"array",(int64_t)A->getNumElements()},{"element",describeType(A->getElementType())}};
  if(auto *S=dyn_cast<StructType>(T)){json::Array E;for(Type *T:S->elements())E.push_back(describeType(T));return json::Object{{"struct",std::move(E)}};}
  return typeText(T);
}
static Type *readType(LLVMContext &C,const json::Value &V){
  if(auto S=V.getAsString()){
    if(*S=="void")return Type::getVoidTy(C);if(*S=="ptr")return PointerType::getUnqual(C);
    if(*S=="float")return Type::getFloatTy(C);if(*S=="double")return Type::getDoubleTy(C);
    if(S->starts_with("i")){unsigned N=0;if(!S->drop_front().getAsInteger(10,N))return IntegerType::get(C,N);}
  }
  if(auto *O=V.getAsObject()){
    if(auto N=O->getInteger("array"))return ArrayType::get(readType(C,*O->get("element")),*N);
    if(auto *A=O->getArray("struct")){SmallVector<Type*> E;for(auto &V:*A)E.push_back(readType(C,V));return StructType::get(C,E);}
  }
  reject("unsupported image signature type");
}
static std::string symbolKey(const GlobalValue &G){
  return G.hasLocalLinkage()?G.getParent()->getSourceFileName()+"|"+G.getName().str():G.getName().str();
}
struct CodeSymbol {
  uint32_t address;
  std::string key,name,source,native;
  FunctionType *type;
  bool local, signReturn, addressTaken, definition,coalesce;
  std::vector<bool> used;
};
struct RegisterEdge {
  std::string source,function,target,previous,mode; unsigned line,argument,offset;
};
struct Image {
  std::vector<RegisterEdge> registerEdges;
  std::map<std::string,CodeSymbol> codes;
  void read(StringRef Path,LLVMContext &C){
    auto B=MemoryBuffer::getFile(Path);if(!B)reject("image catalog file");
    auto J=json::parse((*B)->getBuffer());if(!J){consumeError(J.takeError());reject("image catalog JSON");}
    if(auto *E=J->getAsObject()->getArray("register_edges"))for(auto &V:*E){auto &O=*V.getAsObject();
      registerEdges.push_back({O.getString("source")->str(),O.getString("function")->str(),O.getString("target")->str(),O.getString("previous").value_or("").str(),O.getString("mode")->str(),(unsigned)*O.getInteger("line"),(unsigned)O.getInteger("argument").value_or(0),(unsigned)O.getInteger("offset").value_or(0)});
    }
    auto *A=J->getAsObject()->getArray("codes");if(!A)reject("image code catalog");
    for(auto &V:*A){auto &O=*V.getAsObject();SmallVector<Type*> Args;
      for(auto &T:*O.getArray("params"))Args.push_back(readType(C,T));
      CodeSymbol S{(uint32_t)*O.getInteger("address"),O.getString("key")->str(),O.getString("name")->str(),O.getString("source")->str(),O.getString("native")->str(),
        FunctionType::get(readType(C,*O.get("return")),Args,O.getBoolean("varargs").value_or(false)),O.getBoolean("local").value_or(false),O.getBoolean("sign_return").value_or(false),O.getBoolean("address_taken").value_or(false),O.getBoolean("definition").value_or(false),O.getBoolean("coalesce").value_or(false),{}};
      S.used.push_back(true);
      if(auto *U=O.getArray("used_flat"))for(auto &V:*U)S.used.push_back(V.getAsBoolean().value_or(true));
      codes.emplace(S.key,std::move(S));
    }
  }
};
static FunctionType *guestSignature(FunctionType *T,LLVMContext &C){
  SmallVector<Type*> A{PointerType::getUnqual(C)};
  std::function<void(Type*)> Add=[&](Type *P){if(auto *X=dyn_cast<ArrayType>(P)){for(unsigned I=0;I<X->getNumElements();++I)Add(X->getElementType());}else A.push_back(valueType(P));};
  for(Type *P:T->params())Add(P);
  return FunctionType::get(valueType(T->getReturnType()),A,T->isVarArg());
}
static void flattenValue(IRBuilder<> &B,Value *V,SmallVectorImpl<Value*> &Out){
  if(auto *A=dyn_cast<ArrayType>(V->getType()))for(unsigned I=0;I<A->getNumElements();++I)flattenValue(B,B.CreateExtractValue(V,{I}),Out);
  else Out.push_back(V);
}
static Value *rebuildArgument(IRBuilder<> &B,Type *T,Function::arg_iterator &A){
  if(auto *X=dyn_cast<ArrayType>(T)){
    Value *V=PoisonValue::get(valueType(T));
    for(unsigned I=0;I<X->getNumElements();++I)V=B.CreateInsertValue(V,rebuildArgument(B,X->getElementType(),A),{I});
    return V;
  }
  return &*A++;
}
static bool scalarCompatible(Type *From,Type *To){
  if(From==To)return true;
  return From->isIntegerTy() && To->isIntegerTy() && From->getIntegerBitWidth()<=32 && To->getIntegerBitWidth()<=32;
}
static Value *adaptScalar(IRBuilder<> &B,Value *V,Type *T,bool Sign=false){
  if(V->getType()==T)return V;
  if(!scalarCompatible(V->getType(),T))reject("incompatible guest call scalar "+typeText(V->getType())+" -> "+typeText(T));
  return Sign?B.CreateSExtOrTrunc(V,T):B.CreateZExtOrTrunc(V,T);
}
static Value *guestCall(IRBuilder<> &B,FunctionCallee Callee,ArrayRef<Value*> Args,Type *Return,bool SignReturn,bool Extra,const std::vector<bool> *Used=nullptr){
  SmallVector<Value*> Flat;for(Value *A:Args)flattenValue(B,A,Flat);Args=Flat;
  FunctionType *T=Callee.getFunctionType();
  if(Args.size()<T->getNumParams()){
    for(unsigned I=Args.size();I<T->getNumParams();++I){
      if(!Used || I>=Used->size() || (*Used)[I])reject("missing observable guest argument: "+Callee.getCallee()->getName()+" argument "+Twine(I-1));
      Flat.push_back(PoisonValue::get(T->getParamType(I)));
    }
    Args=Flat;
  }
  if(!T->isVarArg() && !Extra && Args.size()!=T->getNumParams())
    reject("guest call argument count: "+Callee.getCallee()->getName()+" got "+Twine(Args.size())+" expected "+Twine(T->getNumParams()));
  SmallVector<Value*> Passed;
  for(unsigned I=0;I<T->getNumParams();++I)Passed.push_back(adaptScalar(B,Args[I],T->getParamType(I)));
  if(T->isVarArg())for(unsigned I=T->getNumParams();I<Args.size();++I)Passed.push_back(Args[I]);
  Value *R=B.CreateCall(Callee,Passed);
  if(Return->isVoidTy())return R;
  if(T->getReturnType()->isVoidTy())reject("void guest provider used as value: "+Callee.getCallee()->getName());
  return adaptScalar(B,R,Return,SignReturn);
}
static json::Object argumentUse(Argument &Arg){
  bool Observed=false;json::Array Dependencies;std::set<Value*> Visited;
  std::function<void(Value*)> Walk=[&](Value *V){
    if(!Visited.insert(V).second)return;
    for(Use &U:V->uses()){
      auto *I=dyn_cast<Instruction>(U.getUser());if(!I){Observed=true;continue;}
      if(auto *Call=dyn_cast<CallBase>(I)){
        Function *F=directCallee(*Call);
        if(!F || F->isIntrinsic() || &U==&Call->getCalledOperandUse()){Observed=true;continue;}
        for(unsigned J=0;J<Call->arg_size();++J)if(Call->getArgOperand(J)==V)
          Dependencies.push_back(json::Object{{"function",symbolKey(*F)},{"argument",(int64_t)J}});
      }else if(isa<BinaryOperator,CastInst,GetElementPtrInst,SelectInst,PHINode,ICmpInst,FCmpInst,ExtractValueInst,InsertValueInst>(I))Walk(I);
      else Observed=true;
    }
  };Walk(&Arg);
  return json::Object{{"observed",Observed},{"dependencies",std::move(Dependencies)}};
}
static Function *indirectDispatcher(Module &Out,Image &Img,ABI &Interfaces,Module &Input,StringRef Prefix,FunctionType *Site,
    std::map<FunctionType*,Function*> &Cache){
  if(Cache.count(Site))return Cache.at(Site);
  LLVMContext &C=Out.getContext();SmallVector<Type*> A{PointerType::getUnqual(C),Type::getInt32Ty(C)};
  for(unsigned I=1;I<Site->getNumParams();++I)A.push_back(Site->getParamType(I));
  auto *F=Function::Create(FunctionType::get(Site->getReturnType(),A,false),GlobalValue::InternalLinkage,"guest_indirect",Out);
  Cache[Site]=F;auto *Entry=BasicBlock::Create(C,"entry",F),*Bad=BasicBlock::Create(C,"bad_signature_or_identity",F);
  IRBuilder<> B(Entry);auto *S=B.CreateSwitch(F->getArg(1),Bad);
  SmallVector<Value*> Values{F->getArg(0)};for(unsigned I=2;I<F->arg_size();++I)Values.push_back(F->getArg(I));
  for(const auto &Pair:Img.codes){
    const CodeSymbol &K=Pair.second;
    if(!K.addressTaken)continue;
    FunctionType *T=guestSignature(K.type,C);
    if(Values.size()<T->getNumParams())continue;
    if(!Site->getReturnType()->isVoidTy() && !scalarCompatible(T->getReturnType(),Site->getReturnType()))continue;
    bool Match=true;for(unsigned I=0;I<T->getNumParams();++I)if(!scalarCompatible(Values[I]->getType(),T->getParamType(I)))Match=false;
    if(!Match)continue;
    auto *Case=BasicBlock::Create(C,"code_"+Twine(K.address),F);S->addCase(B.getInt32(K.address),Case);
    IRBuilder<> D(Case);
    Value *R=nullptr;
    auto Boundary=Interfaces.calls.find(K.name);
    if(!K.local && Boundary!=Interfaces.calls.end()){
      if(Values.size()!=Boundary->second.args.size()+1)reject("indirect native boundary shape");
      R=bridgeCall(D,Out,Values[0],Boundary->second,ArrayRef<Value*>(Values).drop_front());
      if(!Site->getReturnType()->isVoidTy())R=adaptScalar(D,R,Site->getReturnType(),K.signReturn);
    }else{
      auto Target=Out.getOrInsertFunction(K.native,T);
      if(K.local)cast<GlobalValue>(Target.getCallee())->setVisibility(GlobalValue::HiddenVisibility);
      R=guestCall(D,Target,Values,Site->getReturnType(),K.signReturn,true);
    }
    if(Site->getReturnType()->isVoidTy())D.CreateRetVoid();else D.CreateRet(R);
  }
  IRBuilder<> D(Bad);runtime(D,Out,"g32_bad_code",D.getVoidTy(),{F->getArg(0),F->getArg(1)});D.CreateUnreachable();
  return F;
}
static Value *constantValue(Value *X,IRBuilder<> &B,const DataLayout &DL,
    std::map<const Value*,Value*> &Values,Image &Img,std::map<const GlobalVariable*,GlobalVariable*> &External){
  if(Values.count(X))return Values.at(X);
  if(auto *G=dyn_cast<GlobalVariable>(X)){
    if(External.count(G))return B.CreateLoad(B.getInt32Ty(),External.at(G));
  }
  if(auto *F=dyn_cast<Function>(X)){
    auto I=Img.codes.find(symbolKey(*F));if(I==Img.codes.end())reject("missing guest code identity: "+F->getName());
    return B.getInt32(I->second.address);
  }
  if(isa<ConstantPointerNull>(X))return B.getInt32(0);
  if(isa<ConstantInt,ConstantFP>(X))return X;
  if(isa<UndefValue>(X))return UndefValue::get(valueType(X->getType()));
  if(isa<PoisonValue>(X))return PoisonValue::get(valueType(X->getType()));
  if(isa<ConstantAggregateZero>(X))return Constant::getNullValue(valueType(X->getType()));
  if(auto *E=dyn_cast<ConstantExpr>(X)){
    Value *A=constantValue(E->getOperand(0),B,DL,Values,Img,External);
    if(auto *G=dyn_cast<GEPOperator>(E)){
      APInt Offset(32,0);if(!G->accumulateConstantOffset(DL,Offset))reject("nonconstant constant GEP");
      return B.CreateAdd(A,B.getInt32(Offset.getZExtValue()));
    }
    Type *T=valueType(E->getType());
    if(E->getOpcode()==Instruction::IntToPtr || E->getOpcode()==Instruction::PtrToInt)return B.CreateZExtOrTrunc(A,T);
    if(Instruction::isCast(E->getOpcode()))return A->getType()==T?A:B.CreateCast((Instruction::CastOps)E->getOpcode(),A,T);
    if(E->getNumOperands()==2)return B.CreateBinOp((Instruction::BinaryOps)E->getOpcode(),A,constantValue(E->getOperand(1),B,DL,Values,Img,External));
  }
  reject("unmapped SSA/constant value");
}
static void initializeConstant(IRBuilder<> &B,Module &Out,const DataLayout &DL,Value *Base,uint32_t Offset,Constant *K,
    std::map<const Value*,Value*> &Values,Image &Img,std::map<const GlobalVariable*,GlobalVariable*> &External){
  Type *T=K->getType();
  if(auto *S=dyn_cast<StructType>(T)){
    for(unsigned I=0;I<S->getNumElements();++I)initializeConstant(B,Out,DL,Base,Offset+DL.getStructLayout(S)->getElementOffset(I),K->getAggregateElement(I),Values,Img,External);
  } else if(auto *A=dyn_cast<ArrayType>(T)){
    for(unsigned I=0;I<A->getNumElements();++I)initializeConstant(B,Out,DL,Base,Offset+I*DL.getTypeAllocSize(A->getElementType()).getFixedValue(),K->getAggregateElement(I),Values,Img,External);
  } else {
    Value *P=runtime(B,Out,"g32_resolve",B.getPtrTy(),{Base,B.getInt32(Offset),B.getInt32(DL.getTypeStoreSize(T).getFixedValue()),B.getInt32(0)});
    B.CreateAlignedStore(constantValue(K,B,DL,Values,Img,External),P,Align(1));
  }
}
