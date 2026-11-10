// Structural storage proof for existing resident definitions. MIT.
// This describes LLVM storage, never a callable ABI or an admission waiver.
static llvm::json::Value storageShape(llvm::Type *T,const llvm::DataLayout &DL){
  using namespace llvm;
  json::Object O;
  if(!T->isSized()){O["kind"]="unsized";return O;}
  O["size"]=(int64_t)DL.getTypeAllocSize(T).getFixedValue();
  if(T->isPointerTy())O["kind"]="pointer";
  else if(T->isIntegerTy()){O["kind"]="integer";O["bits"]=(int64_t)T->getIntegerBitWidth();}
  else if(T->isFloatingPointTy()){O["kind"]="float";O["bits"]=(int64_t)T->getPrimitiveSizeInBits().getFixedValue();}
  else if(auto *A=dyn_cast<ArrayType>(T)){O["kind"]="array";O["count"]=(int64_t)A->getNumElements();O["element"]=storageShape(A->getElementType(),DL);}
  else if(auto *S=dyn_cast<StructType>(T)){
    O["kind"]="struct";json::Array Fields;const auto *L=DL.getStructLayout(S);
    for(unsigned i=0;i<S->getNumElements();i++)Fields.push_back(json::Object{{"offset",(int64_t)L->getElementOffset(i)},{"type",storageShape(S->getElementType(i),DL)}});
    O["fields"]=std::move(Fields);
  }else O["kind"]="unsupported";
  return O;
}
static bool storageBytes(llvm::Constant *C,const llvm::DataLayout &DL,std::vector<uint8_t> &B,uint64_t At){
  using namespace llvm;
  if(!C || !C->getType()->isSized())return false;
  if(C->isNullValue() && !C->getType()->isPointerTy())return true;
  if(auto *I=dyn_cast<ConstantInt>(C)){
    unsigned N=DL.getTypeStoreSize(I->getType()).getFixedValue();
    for(unsigned i=0;i<N;i++)B[At+i]=(uint8_t)I->getValue().extractBitsAsZExtValue(std::min(8u,I->getBitWidth()-i*8),i*8);
    return true;
  }
  if(auto *F=dyn_cast<ConstantFP>(C))return storageBytes(ConstantInt::get(C->getContext(),F->getValueAPF().bitcastToAPInt()),DL,B,At);
  if(auto *A=dyn_cast<ArrayType>(C->getType())){
    auto Stride=DL.getTypeAllocSize(A->getElementType()).getFixedValue();
    for(uint64_t i=0;i<A->getNumElements();i++)if(!storageBytes(C->getAggregateElement((unsigned)i),DL,B,At+i*Stride))return false;
    return true;
  }
  if(auto *S=dyn_cast<StructType>(C->getType())){
    auto *L=DL.getStructLayout(S);
    for(unsigned i=0;i<S->getNumElements();i++)if(!storageBytes(C->getAggregateElement(i),DL,B,At+L->getElementOffset(i)))return false;
    return true;
  }
  return false;
}
static int storageContract(const char *input,const char *output){
  using namespace llvm;
  LLVMContext C;SMDiagnostic E;auto M=parseIRFile(input,E,C);
  if(!M){E.print("guest32 storage",errs());return 1;}
  if(verifyModule(*M,&errs()))return 1;
  json::Array Globals;
  for(auto &G:M->globals())if(!G.isDeclaration()){
    std::vector<uint8_t> B(M->getDataLayout().getTypeAllocSize(G.getValueType()).getFixedValue());
    std::string Hex;
    if(storageBytes(G.getInitializer(),M->getDataLayout(),B,0))for(uint8_t V:B){Hex+="0123456789abcdef"[V>>4];Hex+="0123456789abcdef"[V&15];}
    Globals.push_back(json::Object{
    {"name",G.getName()},{"local",G.hasLocalLinkage()},{"constant",G.isConstant()},
    {"alignment",(int64_t)G.getAlign().valueOrOne().value()},
    {"shape",storageShape(G.getValueType(),M->getDataLayout())},{"initial_bytes",Hex}});
  }
  std::error_code EC;raw_fd_ostream O(output,EC);if(EC)return 1;
  O<<formatv("{0:2}\n",json::Value(json::Object{{"source",M->getSourceFileName()},
    {"pointer_bits",(int64_t)M->getDataLayout().getPointerSizeInBits()},{"globals",std::move(Globals)}}));
  return 0;
}
