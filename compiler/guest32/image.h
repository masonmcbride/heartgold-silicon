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
  bool returnsTwice=false,noReturn=false,executable=true,nativeBoundary=false;
  std::string returnHook;
  std::vector<unsigned> returnArguments;
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
      S.returnsTwice=O.getBoolean("returns_twice").value_or(false);
      S.noReturn=O.getBoolean("noreturn").value_or(false);
      S.executable=O.getBoolean("executable").value_or(true);
      S.returnHook=O.getString("return_hook").value_or("").str();
      if(auto *Arguments=O.getArray("return_arguments"))for(auto &V:*Arguments){
        auto Index=V.getAsInteger();if(!Index || *Index<0 || (uint64_t)*Index>=S.type->getNumParams())reject("return hook argument index");
        S.returnArguments.push_back(*Index);
      }
      if(auto *U=O.getArray("used_flat"))for(auto &V:*U)S.used.push_back(V.getAsBoolean().value_or(true));
      codes.emplace(S.key,std::move(S));
    }
  }
};
static bool hasArgumentHomes(FunctionType *T){return T->isVarArg() && T->getNumParams()!=0;}
static FunctionType *guestSignature(FunctionType *T,LLVMContext &C){
  SmallVector<Type*> A{PointerType::getUnqual(C)};
  std::function<void(Type*)> Add=[&](Type *P){if(auto *X=dyn_cast<ArrayType>(P)){for(unsigned I=0;I<X->getNumElements();++I)Add(X->getElementType());}else A.push_back(valueType(P));};
  for(Type *P:T->params())Add(P);
  // Original MSL va_start takes the address of the last named argument. Native
  // ARM64 varargs do not have that layout. Pass one explicit guest home address.
  if(hasArgumentHomes(T))A.push_back(Type::getInt32Ty(C));
  return FunctionType::get(valueType(T->getReturnType()),A,T->isVarArg() && !hasArgumentHomes(T));
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
static Value *guestCall(IRBuilder<> &B,FunctionCallee Callee,ArrayRef<Value*> Args,Type *Return,bool SignReturn,bool Extra,const std::vector<bool> *Used=nullptr,bool Homes=false){
  SmallVector<Value*> Flat;for(Value *A:Args)flattenValue(B,A,Flat);Args=Flat;
  FunctionType *T=Callee.getFunctionType();
  if(Homes){
    unsigned Fixed=T->getNumParams()-2;
    if(Args.size()<Fixed+1)reject("missing fixed variadic argument: "+Callee.getCallee()->getName());
    SmallVector<Value*> Passed{Args[0]},Words;
    uint64_t Bytes=0;
    for(unsigned I=1;I<Args.size();++I){
      Value *V=I<=Fixed?adaptScalar(B,Args[I],T->getParamType(I)):Args[I];
      Type *K=V->getType();
      if(!K->isIntegerTy() && !K->isDoubleTy())reject("unsupported ARM32 argument home type");
      if(I>Fixed && K->isIntegerTy() && K->getIntegerBitWidth()<32)reject("unpromoted variadic integer");
      if(K->isIntegerTy() && K->getIntegerBitWidth()>64)reject("oversized ARM32 argument home");
      Bytes+=alignTo((K->getPrimitiveSizeInBits().getFixedValue()+7)/8,4);
      Words.push_back(V);if(I<=Fixed)Passed.push_back(V);
    }
    Value *Frame=runtime(B,*B.GetInsertBlock()->getModule(),"g32_frame_enter",B.getPtrTy(),{Args[0]});
    auto &M=*B.GetInsertBlock()->getModule();
    Value *Home=runtime(B,M,"g32_stack_alloc",B.getInt32Ty(),{Args[0],Frame,B.getInt64(Bytes),B.getInt32(4)});
    uint64_t Offset=0;
    for(Value *V:Words){
      unsigned Size=(V->getType()->getPrimitiveSizeInBits().getFixedValue()+7)/8;
      Value *P=runtime(B,M,"g32_resolve",B.getPtrTy(),{Args[0],B.CreateAdd(Home,B.getInt32(Offset)),B.getInt32(Size),B.getInt32(0)});
      B.CreateAlignedStore(V,P,Align(1));Offset+=alignTo(Size,4);
    }
    Passed.push_back(Home);Value *R=B.CreateCall(Callee,Passed);
    runtime(B,M,"g32_frame_leave",B.getVoidTy(),{Args[0],Frame});
    if(Return->isVoidTy())return R;
    if(T->getReturnType()->isVoidTy())reject("void variadic provider used as value");
    return adaptScalar(B,R,Return,SignReturn);
  }
  // Separately reconstructed original declarations may spell an ARM register
  // pair as two words. Reconstitute only complete, aligned 64-bit lanes for a
  // known definition; never extend one word or discard a high word.
  if(Extra && !T->isVarArg() && Args.size()>T->getNumParams()){
    SmallVector<Value*> Packed{Args[0]};unsigned Source=1,Lane=0;bool Valid=true;
    for(unsigned I=1;I<T->getNumParams();++I){
      Type *Want=T->getParamType(I);
      if(Source>=Args.size()){Valid=false;break;}
      if(Want->isIntegerTy(64) && Args[Source]->getType()->isIntegerTy(32)){
        if((Lane&1) || Source+1>=Args.size() || !Args[Source+1]->getType()->isIntegerTy(32)){Valid=false;break;}
        Value *Low=B.CreateZExt(Args[Source],Want),*High=B.CreateZExt(Args[Source+1],Want);
        Packed.push_back(B.CreateOr(Low,B.CreateShl(High,32)));Source+=2;Lane+=2;
      }else{
        if(!scalarCompatible(Args[Source]->getType(),Want)){Valid=false;break;}
        Packed.push_back(Args[Source++]);Lane+=Want->isIntegerTy(64)?2:1;
      }
    }
    if(Valid && Source==Args.size()){Flat=Packed;Args=Flat;}
  }
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
    if(!K.addressTaken || !K.executable)continue;
    if(!K.definition && !Interfaces.calls.count(K.name))continue;
    FunctionType *T=guestSignature(K.type,C);
    unsigned Fixed=T->getNumParams()-(hasArgumentHomes(K.type)?1:0);
    if(Values.size()<Fixed)continue;
    if(!Site->getReturnType()->isVoidTy() && !scalarCompatible(T->getReturnType(),Site->getReturnType()))continue;
    bool Match=true;for(unsigned I=0;I<Fixed;++I)if(!scalarCompatible(Values[I]->getType(),T->getParamType(I)))Match=false;
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
      // Address-taken local functions have globally unique generated identities.
      // Their guest-ABI entry must remain bindable by a peer image dispatcher.
      R=guestCall(D,Target,Values,Site->getReturnType(),K.signReturn,true,nullptr,hasArgumentHomes(K.type));
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
    if(!I->second.definition && !I->second.nativeBoundary){
      // A declaration is not proof that a code coordinate exists. In particular
      // linker absolute symbols written as functions must not become invented
      // callback IDs. Retain a genuine unresolved coordinate until its owning
      // original provider or linker contract supplies it.
      Module &M=*B.GetInsertBlock()->getModule();std::string Name="guest32_code_address_"+F->getName().str();
      auto *Coordinate=M.getNamedGlobal(Name);
      if(!Coordinate)Coordinate=new GlobalVariable(M,B.getInt32Ty(),true,GlobalValue::ExternalLinkage,nullptr,Name);
      return B.CreateLoad(B.getInt32Ty(),Coordinate);
    }
    return B.getInt32(I->second.address);
  }
  if(isa<ConstantPointerNull>(X))return B.getInt32(0);
  if(isa<ConstantInt,ConstantFP>(X))return X;
  if(isa<UndefValue>(X))return UndefValue::get(valueType(X->getType()));
  if(isa<PoisonValue>(X))return PoisonValue::get(valueType(X->getType()));
  if(isa<ConstantAggregateZero>(X))return Constant::getNullValue(valueType(X->getType()));
  if(auto *K=dyn_cast<Constant>(X);K && K->getType()->isAggregateType()){
    Type *T=K->getType();Value *Result=PoisonValue::get(valueType(T));
    unsigned Count=isa<StructType>(T)?cast<StructType>(T)->getNumElements():cast<ArrayType>(T)->getNumElements();
    for(unsigned I=0;I<Count;++I)Result=B.CreateInsertValue(Result,constantValue(K->getAggregateElement(I),B,DL,Values,Img,External),{I});
    return Result;
  }
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
  // The owning initializer has already zeroed the entire original object,
  // including padding. Do not emit a second resolver/store for every zero byte.
  if(K->isNullValue())return;
  if(auto *Data=dyn_cast<ConstantDataSequential>(K)){
    SmallVector<uint8_t> Bytes;
    for(unsigned I=0;I<Data->getNumElements();++I){
      Constant *E=Data->getElementAsConstant(I);APInt Bits;
      if(auto *N=dyn_cast<ConstantInt>(E))Bits=N->getValue();
      else if(auto *N=dyn_cast<ConstantFP>(E))Bits=N->getValueAPF().bitcastToAPInt();
      else reject("unsupported constant data element");
      unsigned Size=DL.getTypeAllocSize(E->getType()).getFixedValue();
      Bits=Bits.zextOrTrunc(Size*8);
      for(unsigned J=0;J<Size;++J)Bytes.push_back((uint8_t)Bits.extractBitsAsZExtValue(8,J*8));
    }
    auto *Template=ConstantDataArray::get(Out.getContext(),Bytes);
    auto *Storage=new GlobalVariable(Out,Template->getType(),true,GlobalValue::PrivateLinkage,Template,"guest_initializer_bytes");
    Value *Dest=runtime(B,Out,"g32_resolve",B.getPtrTy(),{Base,B.getInt32(Offset),B.getInt32(Bytes.size()),B.getInt32(0)});
    B.CreateMemCpy(Dest,Align(1),Storage,Align(1),Bytes.size());return;
  }
  if(auto *S=dyn_cast<StructType>(T)){
    for(unsigned I=0;I<S->getNumElements();++I)initializeConstant(B,Out,DL,Base,Offset+DL.getStructLayout(S)->getElementOffset(I),K->getAggregateElement(I),Values,Img,External);
  } else if(auto *A=dyn_cast<ArrayType>(T)){
    for(unsigned I=0;I<A->getNumElements();++I)initializeConstant(B,Out,DL,Base,Offset+I*DL.getTypeAllocSize(A->getElementType()).getFixedValue(),K->getAggregateElement(I),Values,Img,External);
  } else {
    Value *P=runtime(B,Out,"g32_resolve",B.getPtrTy(),{Base,B.getInt32(Offset),B.getInt32(DL.getTypeStoreSize(T).getFixedValue()),B.getInt32(0)});
    B.CreateAlignedStore(constantValue(K,B,DL,Values,Img,External),P,Align(1));
  }
}
