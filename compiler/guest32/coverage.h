// Exhaustive admission diagnostics, independent of fail-fast code emission. MIT
#include "llvm/IR/DebugInfoMetadata.h"
static json::Array coverage(Module &M, const ABI &A) {
  json::Array Issues;
  auto Add = [&](StringRef Kind, StringRef Reason, const Function *F, const Instruction *I, StringRef Symbol = "") {
    std::string Op; if (I) { raw_string_ostream S(Op); I->print(S); }
    json::Object O{{"kind",Kind},{"reason",Reason},{"function",F ? F->getName() : ""},
                   {"symbol",Symbol},{"llvm",Op},{"source",M.getSourceFileName()},{"line",0},{"column",0}};
    if (I && I->getDebugLoc()) {
      auto *L = I->getDebugLoc().get();
      O["source"] = (L->getDirectory()+"/"+L->getFilename()).str();
      O["line"] = (int64_t)L->getLine(); O["column"] = (int64_t)L->getColumn();
    }
    Issues.push_back(std::move(O));
  };
  for (GlobalVariable &G : M.globals()) {
    if (G.use_empty()) continue;
    if (G.isDeclaration() && !A.globals.count(G.getName().str()))
      Add("global-placement","shared guest image coordinate required",nullptr,nullptr,G.getName());
    else if (G.hasInitializer() && !G.getInitializer()->isNullValue())
      Add("static-data","guest bytes and relocations required",nullptr,nullptr,G.getName());
  }
  for (Function &F : M) if (!F.isDeclaration()) {
    if (F.isVarArg()) Add("varargs","guest argument homes and traversal required",&F,nullptr);
    for (const Argument &Arg : F.args()) if (Arg.hasByValAttr() || Arg.hasStructRetAttr())
      Add("aggregate-call","guest aggregate argument classification required",&F,nullptr,Arg.getName());
    for (BasicBlock &BB : F) for (Instruction &I : BB) {
      if (auto *X = dyn_cast<AllocaInst>(&I)) {
        if (!isAllocaPromotable(X)) Add("guest-frame","addressable guest stack object required",&F,&I);
      } else if (auto *X = dyn_cast<CallInst>(&I)) {
        auto *Callee = directCallee(*X);
        if (!Callee) Add("indirect-call","guest code identity and typed dispatch required",&F,&I);
        else if (Callee->isDeclaration() && !A.calls.count(Callee->getName().str()))
          Add(Callee->isIntrinsic()?"intrinsic":"external-call",
              Callee->isIntrinsic()?"guest intrinsic semantics required":"guest provider or typed native boundary required",&F,&I,Callee->getName());
      } else if (auto *X = dyn_cast<LoadInst>(&I)) {
        if (X->isVolatile() || X->isAtomic()) Add("memory-effect","volatile/atomic effect semantics required",&F,&I);
      } else if (auto *X = dyn_cast<StoreInst>(&I)) {
        if (X->isVolatile() || X->isAtomic()) Add("memory-effect","volatile/atomic effect semantics required",&F,&I);
      } else if (!isa<PHINode,GetElementPtrInst,BinaryOperator,ICmpInst,CastInst,SelectInst,
                      CondBrInst,UncondBrInst,ReturnInst>(I))
        Add("instruction","instruction lowering required",&F,&I,I.getOpcodeName());
      for (Value *V : I.operands()) {
        if (isa<ConstantExpr>(V)) Add("constant-expression","guest constant-expression elaboration required",&F,&I);
        if (isa<Function>(V) && !isa<CallInst>(I)) Add("code-value","stored guest function identity required",&F,&I);
      }
    }
  }
  return Issues;
}
