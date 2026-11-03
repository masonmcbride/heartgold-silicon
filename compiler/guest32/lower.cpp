// Guest32 sequential-RAM IR compiler. SPDX-License-Identifier: MIT
// Input is unoptimized, 32-bit Clang IR. Output uses a private native ABI:
// guest pointers become i32 offsets; the first argument is the host RAM base.
#include "llvm/ADT/MapVector.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Module.h"
#include "llvm/TargetParser/Triple.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/IR/Verifier.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Transforms/Utils/PromoteMemToReg.h"
#include "llvm/IR/Dominators.h"
#include "llvm/IR/StructuralHash.h"
#include <map>
#include <functional>
using namespace llvm;

[[noreturn]] static void reject(const Twine &S) {
  errs() << "guest32: unsupported: " << S << '\n'; exit(1);
}
static Type *valueType(Type *T) {
  if (auto *P = dyn_cast<PointerType>(T)) {
    if (P->getAddressSpace()) reject("nondefault address space");
    return Type::getInt32Ty(T->getContext());
  }
  if (T->isIntegerTy() || T->isFloatingPointTy() || T->isVoidTy()) return T;
  if(auto *A=dyn_cast<ArrayType>(T))return ArrayType::get(valueType(A->getElementType()),A->getNumElements());
  reject("aggregate/vector value or call ABI");
}
#include "abi.h"
#include "image.h"
#include "coverage.h"

int main(int argc, char **argv) {
  if (argc < 3) { errs() << "usage: guest32-lower input.ll output.ll [--asan] [--abi file --native-ir file] [--entry symbol] [--prefix text]\n"; return 2; }
  bool Asan = false, GuestExternals=false; std::string AbiPath, NativePath, Prefix, Report, ImagePath;
  std::set<std::string> Entries;
  for (int I = 3; I < argc; ++I) {
    StringRef Flag(argv[I]);
    if (Flag == "--asan") { Asan = true; continue; }
    if (Flag == "--guest-externals") { GuestExternals=true;continue; }
    if (++I == argc) reject("missing option value");
    if (Flag == "--abi") AbiPath = argv[I];
    else if (Flag == "--native-ir") NativePath = argv[I];
    else if (Flag == "--entry") Entries.insert(argv[I]);
    else if (Flag == "--prefix") Prefix = argv[I];
    else if (Flag == "--diagnose") Report = argv[I];
    else if (Flag == "--image") ImagePath = argv[I];
    else reject("unknown option " + Flag);
  }
  if (AbiPath.empty() != NativePath.empty()) reject("--abi and --native-ir are required together");
  LLVMContext C; SMDiagnostic E;
  auto In = parseIRFile(argv[1], E, C);
  if (!In) { E.print(argv[0], errs()); return 1; }
  if (verifyModule(*In, &errs())) return 1;
  ABI Interfaces;
  Image Img;if(!ImagePath.empty())Img.read(ImagePath,C);
  if (!AbiPath.empty()) {
    auto Native = parseIRFile(NativePath, E, C);
    if (!Native) { E.print(argv[0], errs()); return 1; }
    if (verifyModule(*Native, &errs())) return 1;
    if (Native->getDataLayout().getPointerSizeInBits() != 64) reject("native ABI needs 64-bit pointers");
    Interfaces.read(AbiPath, *Native);
    for (const auto &S : Interfaces.calls) if (Function *F = In->getFunction(S.first)) ABI::checkGuest(*F,S.second);
    for (const auto &S : Interfaces.exports) {
      Function *F = In->getFunction(S.first);
      if (!F || F->isDeclaration()) reject("export has no guest definition: " + S.first);
      ABI::checkGuest(*F,S.second);
    }
  }
  if (!Report.empty()) {
    for(Function &F:*In)if(!F.isDeclaration()){
      SmallVector<AllocaInst*> A;for(Instruction &I:F.getEntryBlock())if(auto *X=dyn_cast<AllocaInst>(&I))if(isAllocaPromotable(X))A.push_back(X);
      DominatorTree DT(F);PromoteMemToReg(A,DT);
    }
    auto Issues = coverage(*In,Interfaces);
    json::Array Functions,Globals,Calls;
    for(Function &F:*In)if(!F.isIntrinsic()){
      bool AddressTaken=false;
      for(Use &U:F.uses()){auto *Call=dyn_cast<CallBase>(U.getUser());if(!Call || &U!=&Call->getCalledOperandUse())AddressTaken=true;}
      json::Array Args;for(Argument &A:F.args())Args.push_back(describeType(A.getType()));
      json::Array Uses;for(Argument &A:F.args())Uses.push_back(argumentUse(A));
      std::string Origin;unsigned OriginLine=0;
      if(auto *SP=F.getSubprogram()){Origin=(SP->getDirectory()+"/"+SP->getFilename()).str();OriginLine=SP->getLine();}
      Functions.push_back(json::Object{{"name",F.getName()},{"key",symbolKey(F)},{"params",std::move(Args)},
        {"return",describeType(F.getReturnType())},{"varargs",F.isVarArg()},{"local",F.hasLocalLinkage()},
        {"definition",!F.isDeclaration()},{"source",In->getSourceFileName()},{"sign_return",F.hasRetAttribute(Attribute::SExt)},{"address_taken",AddressTaken},{"argument_uses",std::move(Uses)},
        {"origin",Origin},{"origin_line",(int64_t)OriginLine},{"body_hash",F.isDeclaration()?"":formatv("{0:x}",StructuralHash(F,true)).str()}});
    }
    for(GlobalVariable &G:In->globals())if(G.getValueType()->isSized())Globals.push_back(json::Object{{"name",G.getName()},{"key",symbolKey(G)},
      {"size",(int64_t)In->getDataLayout().getTypeAllocSize(G.getValueType()).getFixedValue()},
      {"alignment",(int64_t)G.getAlign().valueOrOne().value()},{"definition",!G.isDeclaration()},{"local",G.hasLocalLinkage()}});
    for(Function &F:*In)if(!F.isDeclaration())for(BasicBlock &BB:F)for(Instruction &I:BB)if(auto *Call=dyn_cast<CallInst>(&I)){
      Function *Target=directCallee(*Call);if(Target && Target->isIntrinsic())continue;
      json::Array Args;for(Value *A:Call->args())Args.push_back(describeType(A->getType()));
      std::string Text;raw_string_ostream OS(Text);I.print(OS);
      json::Object O{{"function",F.getName()},{"target",Target?symbolKey(*Target):""},{"args",std::move(Args)},
        {"return",describeType(Call->getType())},{"result_used",!Call->use_empty()},{"llvm",Text},{"source",In->getSourceFileName()},{"line",0},{"column",0}};
      if(I.getDebugLoc()){O["line"]=(int64_t)I.getDebugLoc().getLine();O["column"]=(int64_t)I.getDebugLoc().getCol();}
      Calls.push_back(std::move(O));
    }
    json::Object O{{"source",In->getSourceFileName()},{"issues",std::move(Issues)},{"functions",std::move(Functions)},{"globals",std::move(Globals)},{"calls",std::move(Calls)}};
    std::error_code EC;raw_fd_ostream OS(Report,EC);if(EC)reject("coverage output");
    OS << formatv("{0:2}",json::Value(std::move(O))) << '\n';return 0;
  }
  std::set<Function *> Selected;
  std::function<void(Function *)> Select = [&](Function *F) {
    if (!Selected.insert(F).second) return;
    for (BasicBlock &BB : *F) for (Instruction &I : BB) if (auto *Call = dyn_cast<CallInst>(&I)) {
      Function *Callee = directCallee(*Call);
      if (Callee && !Callee->isDeclaration() && !Interfaces.calls.count(Callee->getName().str())) Select(Callee);
    }
  };
  if (Entries.empty()) { for (Function &F : *In) if (!F.isDeclaration()) Select(&F); }
  else for (const auto &Name : Entries) {
    Function *F = In->getFunction(Name); if (!F || F->isDeclaration()) reject("missing entry definition: " + Name);
    Select(F);
  }
  for (const auto &S : Interfaces.exports) Select(In->getFunction(S.first));
  std::set<GlobalVariable *> Globals;
  std::function<void(Value *)> Reference = [&](Value *V) {
    if (auto *G = dyn_cast<GlobalVariable>(V)) Globals.insert(G);
    else if (auto *K = dyn_cast<ConstantExpr>(V)) for (Value *A : K->operands()) Reference(A);
  };
  for (Function *F : Selected) for (BasicBlock &BB : *F) for (Instruction &I : BB)
    for (Value *A : I.operands()) Reference(A);
  if(GuestExternals)for(GlobalVariable &G:In->globals())if(G.hasInitializer()){
    Globals.insert(&G);
    std::function<void(Constant*)> Visit=[&](Constant *K){
      if(auto *G=dyn_cast<GlobalVariable>(K)){Globals.insert(G);return;}
      if(isa<Function>(K))return;
      for(Value *V:K->operands())if(auto *A=dyn_cast<Constant>(V))Visit(A);
    };Visit(G.getInitializer());
  }
  const DataLayout DL = In->getDataLayout();
  if (DL.getPointerSizeInBits() != 32 || DL.isBigEndian())
    reject("requires little-endian 32-bit source layout");
  // Only promotion, never guest optimization, precedes address elaboration.
  for (Function &F : *In) if (Selected.count(&F)) {
    SmallVector<AllocaInst *> A;
    for (Instruction &I : F.getEntryBlock()) if (auto *AI = dyn_cast<AllocaInst>(&I)) {
      if (!isAllocaPromotable(AI)) {
        if (AbiPath.empty()) reject("addressable guest stack frame in " + F.getName());
      } else A.push_back(AI);
    }
    DominatorTree DT(F); PromoteMemToReg(A, DT);
    if(F.isVarArg() && GuestExternals)for(BasicBlock &BB:F)for(Instruction &I:BB)
      if(isa<PtrToIntInst,VAArgInst>(I))reject("observed guest variadic argument homes in "+F.getName());
  }
  Module Out("guest32", C);
  Out.setTargetTriple(Triple("arm64-apple-macosx14.0.0"));
  Out.setDataLayout("e-m:o-i64:64-i128:128-n32:64-S128");
  std::map<const Value *, Value *> V;
  std::map<const Function *, Function *> Functions;
  std::map<FunctionType*,Function*> Dispatchers;
  std::map<const GlobalVariable*,GlobalVariable*> ExternalAddresses;
  uint64_t Next = 4096;
  // Explicit placements may intentionally overlap (interior labels). Automatic
  // definitions must never accidentally alias any explicitly placed image byte.
  for (const auto &G : Interfaces.globals)
    Next = std::max(Next,(uint64_t)G.second.offset + G.second.size);
  for (GlobalVariable &G : In->globals()) {
    if (!Globals.count(&G)) continue;
    auto Placement = Interfaces.globals.find(G.getName().str());
    if (G.isDeclaration() && Placement == Interfaces.globals.end()) {
      if(!GuestExternals)reject("external global image placement: " + G.getName());
      ExternalAddresses[&G]=new GlobalVariable(Out,Type::getInt32Ty(C),true,GlobalValue::ExternalLinkage,nullptr,Prefix+"address_"+G.getName());
      continue;
    }
    if (G.getAddressSpace()) reject("nondefault global address space");
    if (G.isThreadLocal() || !G.getValueType()->isSized()) reject("unsized/TLS global");
    if (G.hasInitializer() && !G.getInitializer()->isNullValue() && !GuestExternals)
      reject("nonzero static initializer/relocation");
    Next = alignTo(Next, DL.getABITypeAlign(G.getValueType()));
    auto Size = DL.getTypeAllocSize(G.getValueType()).getFixedValue();
    if (Placement != Interfaces.globals.end()) {
      if (Size > Placement->second.size) reject("global declaration exceeds placement: " + G.getName());
      V[&G] = ConstantInt::get(Type::getInt32Ty(C), Placement->second.offset);
      outs() << G.getName() << " " << Placement->second.offset << " " << Placement->second.size << '\n';
      Next = std::max(Next,(uint64_t)Placement->second.offset + Placement->second.size);
      continue;
    }
    if (!Size) reject("zero-sized global");
    if (Next + Size > UINT32_MAX) reject("global address overflow");
    V[&G] = ConstantInt::get(Type::getInt32Ty(C), Next);
    outs() << G.getName() << " " << Next << " " << Size << '\n';
    Next += Size;
  }
  for (Function &F : *In) {
    if (!Selected.count(&F) && !(GuestExternals && F.isDeclaration() && !F.isIntrinsic())) continue;
    if (F.isVarArg() && !GuestExternals) reject("varargs");
    SmallVector<Type *> Args{PointerType::getUnqual(C)};
    for (Argument &A : F.args()) {
      if (A.hasByValAttr() || A.hasStructRetAttr()) reject("aggregate argument");
      Args.push_back(valueType(A.getType()));
    }
    FunctionType *NativeType=guestSignature(F.getFunctionType(),C);
    auto Canonical=Img.codes.find(symbolKey(F));
    if(GuestExternals && Canonical!=Img.codes.end() && Canonical->second.definition)NativeType=guestSignature(Canonical->second.type,C);
    std::string Name=(Prefix+F.getName()).str();
    if(GuestExternals && Canonical!=Img.codes.end())Name=Canonical->second.native;
    auto *NF = Function::Create(NativeType,
                               F.hasLocalLinkage() && !GuestExternals?GlobalValue::InternalLinkage:GlobalValue::ExternalLinkage, Name, Out);
    if(F.hasLocalLinkage() && GuestExternals)NF->setVisibility(GlobalValue::HiddenVisibility);
    if(GuestExternals && !F.isDeclaration() && Canonical!=Img.codes.end() && Canonical->second.coalesce)NF->setLinkage(GlobalValue::WeakODRLinkage);
    if (Asan) NF->addFnAttr(Attribute::SanitizeAddress);
    Functions[&F] = NF;
  }
  for (Function &F : *In) if (Selected.count(&F)) {
    Function *NF = Functions.at(&F);
    auto Arg = NF->arg_begin(); Value *Base = &*Arg++; Base->setName("ram");
    std::map<const BasicBlock *, BasicBlock *> Blocks;
    for (BasicBlock &BB : F) Blocks[&BB] = BasicBlock::Create(C, BB.getName(), NF);
    IRBuilder<> Arguments(Blocks.at(&F.getEntryBlock()));
    for(Argument &A:F.args())V[&A]=rebuildArgument(Arguments,A.getType(),Arg);
    Value *ImplicitR0=Arg!=NF->arg_end()?&*Arg:nullptr;
    bool HasFrame=false;
    for(BasicBlock &BB:F)for(Instruction &I:BB)if(isa<AllocaInst>(I))HasFrame=true;
    Value *Frame=nullptr;
    if(HasFrame){IRBuilder<> B(Blocks.at(&F.getEntryBlock()));Frame=runtime(B,Out,"g32_frame_enter",B.getPtrTy(),{Base});}
    IRBuilder<> *Current=nullptr;
    auto Get = [&](Value *X) -> Value * {return constantValue(X,*Current,DL,V,Img,ExternalAddresses);};
    // Create all PHIs before translating edges, including loop backedges.
    for (BasicBlock &BB : F) for (PHINode &P : BB.phis())
      V[&P] = PHINode::Create(valueType(P.getType()), P.getNumIncomingValues(), "", Blocks.at(&BB));
    for (BasicBlock &BB : F) {
      IRBuilder<> B(Blocks.at(&BB));
      Current=&B;
      Value *PreviousResult=nullptr;std::string PreviousTarget;
      auto Address = [&](Value *P, Type *T) {
        // i32 arithmetic wraps before zero-extension. No host inbounds promise.
        if (!AbiPath.empty()) return runtime(B,Out,"g32_resolve",B.getPtrTy(),
            {Base,Get(P),B.getInt32(DL.getTypeStoreSize(T).getFixedValue()),B.getInt32(0)});
        return B.CreateGEP(B.getInt8Ty(), Base, B.CreateZExt(Get(P), B.getInt64Ty()));
      };
      for (Instruction &I : BB) {
        if (isa<PHINode>(I)) continue;
        Value *R = nullptr;
        if (auto *A = dyn_cast<AllocaInst>(&I)) {
          Value *Bytes=B.CreateMul(B.CreateZExtOrTrunc(Get(A->getArraySize()),B.getInt64Ty()),B.getInt64(DL.getTypeAllocSize(A->getAllocatedType()).getFixedValue()));
          R=runtime(B,Out,"g32_stack_alloc",B.getInt32Ty(),{Base,Frame,Bytes,B.getInt32(A->getAlign().value())});
        } else if (auto *G = dyn_cast<GetElementPtrInst>(&I)) {
          SmallMapVector<Value *, APInt, 4> Vars; APInt Const(32, 0);
          if (!G->collectOffset(DL, 32, Vars, Const)) reject("nonlinear GEP");
          R = B.CreateAdd(Get(G->getPointerOperand()), B.getInt32(Const.getZExtValue()));
          for (auto &Term : Vars) {
            Value *Index = B.CreateSExtOrTrunc(Get(Term.first), B.getInt32Ty());
            R = B.CreateAdd(R, B.CreateMul(Index, B.getInt32(Term.second.getZExtValue())));
          }
        } else if (auto *L = dyn_cast<LoadInst>(&I)) {
          if (L->isAtomic() || (L->isVolatile() && !GuestExternals)) reject("atomic/volatile effect");
          R = B.CreateAlignedLoad(valueType(L->getType()), Address(L->getPointerOperand(),L->getType()), Align(1));
          cast<LoadInst>(R)->setVolatile(L->isVolatile());
        } else if (auto *S = dyn_cast<StoreInst>(&I)) {
          if (S->isAtomic() || (S->isVolatile() && !GuestExternals)) reject("atomic/volatile effect");
          R = B.CreateAlignedStore(Get(S->getValueOperand()), Address(S->getPointerOperand(),S->getValueOperand()->getType()), Align(1));
          cast<StoreInst>(R)->setVolatile(S->isVolatile());
        } else if (auto *X = dyn_cast<BinaryOperator>(&I)) {
          R = B.CreateBinOp(X->getOpcode(), Get(X->getOperand(0)), Get(X->getOperand(1)));
        } else if (auto *X = dyn_cast<ICmpInst>(&I)) {
          R = B.CreateICmp(X->getPredicate(), Get(X->getOperand(0)), Get(X->getOperand(1)));
        } else if (auto *X = dyn_cast<FCmpInst>(&I)) {
          R=B.CreateFCmp(X->getPredicate(),Get(X->getOperand(0)),Get(X->getOperand(1)));
        } else if (auto *X = dyn_cast<CastInst>(&I)) {
          Value *A = Get(X->getOperand(0)); Type *T = valueType(X->getType());
          if (X->getOpcode() == Instruction::PtrToInt || X->getOpcode() == Instruction::IntToPtr)
            R = B.CreateZExtOrTrunc(A, T);
          else if (A->getType() == T) R = A;
          else R = B.CreateCast(X->getOpcode(), A, T);
        } else if (auto *X = dyn_cast<SelectInst>(&I)) {
          R = B.CreateSelect(Get(X->getCondition()), Get(X->getTrueValue()), Get(X->getFalseValue()));
        } else if (auto *X = dyn_cast<CondBrInst>(&I)) {
          R = B.CreateCondBr(Get(X->getCondition()), Blocks.at(X->getSuccessor(0)), Blocks.at(X->getSuccessor(1)));
        } else if (auto *X = dyn_cast<UncondBrInst>(&I)) {
          R = B.CreateBr(Blocks.at(X->getSuccessor(0)));
        } else if (auto *X = dyn_cast<SwitchInst>(&I)) {
          auto *S=B.CreateSwitch(Get(X->getCondition()),Blocks.at(X->getDefaultDest()),X->getNumCases());
          for(auto Case:X->cases())S->addCase(Case.getCaseValue(),Blocks.at(Case.getCaseSuccessor()));R=S;
        } else if (auto *X = dyn_cast<ReturnInst>(&I)) {
          if(Frame){
            if(X->getReturnValue() && X->getReturnValue()->getType()->isPointerTy())
              runtime(B,Out,"g32_check_return",B.getVoidTy(),{Base,Frame,Get(X->getReturnValue())});
            runtime(B,Out,"g32_frame_leave",B.getVoidTy(),{Base,Frame});
          }
          R = X->getReturnValue() ? B.CreateRet(Get(X->getReturnValue())) : B.CreateRetVoid();
        } else if (auto *X = dyn_cast<CallInst>(&I)) {
          Function *Callee = directCallee(*X);
          if(!Callee && GuestExternals){
            SmallVector<Value*> Args{Base};SmallVector<Type*> Types;
            for(Value *A:X->args())flattenValue(B,Get(A),Args);
            for(Value *A:Args)Types.push_back(A->getType());
            FunctionType *Site=FunctionType::get(valueType(X->getType()),Types,false);
            auto *Dispatcher=indirectDispatcher(Out,Img,Interfaces,*In,Prefix,Site,Dispatchers);
            Args.insert(Args.begin()+1,Get(X->getCalledOperand()));
            R=B.CreateCall(Dispatcher,Args);V[&I]=R;continue;
          }
          if(Callee && Callee->isIntrinsic()){
            if(auto *M=dyn_cast<MemIntrinsic>(X)){
              Value *N=Get(M->getLength());
              auto Resolve=[&](Value *P){return runtime(B,Out,"g32_memory_span",B.getPtrTy(),{Base,Get(P),N});};
              Value *Dest=Resolve(M->getRawDest());
              if(auto *T=dyn_cast<MemTransferInst>(M)){
                if(isa<MemMoveInst>(M))R=B.CreateMemMove(Dest,Align(1),Resolve(T->getRawSource()),Align(1),N,M->isVolatile());
                else R=B.CreateMemCpy(Dest,Align(1),Resolve(T->getRawSource()),Align(1),N,M->isVolatile());
              }
              else R=B.CreateMemSet(Dest,Get(cast<MemSetInst>(M)->getValue()),N,Align(1),M->isVolatile());
            } else if(Callee->getIntrinsicID()==Intrinsic::fmuladd){
              SmallVector<Value*> Args;for(Value *A:X->args())Args.push_back(Get(A));
              R=B.CreateCall(Intrinsic::getOrInsertDeclaration(&Out,Intrinsic::fmuladd,{X->getType()}),Args);
            } else reject("intrinsic "+Callee->getName());
            V[&I]=R;continue;
          }
          auto Boundary = Interfaces.calls.find(Callee ? Callee->getName().str() : "");
          if (Boundary != Interfaces.calls.end()) {
            const auto &S = Boundary->second; SmallVector<Value *> GuestArgs, NativeArgs{Base};
            if(X->arg_size()!=S.args.size() || X->getType()!=ABI::nativeType(C,S.result))reject("callsite ABI signature: "+Callee->getName());
            for (Value *A : X->args()) GuestArgs.push_back(Get(A));
            Value *Epoch = S.result.role == "owned" ? runtime(B,Out,"g32_epoch",B.getInt64Ty(),{Base}) : nullptr;
            for (unsigned J = 0; J < S.args.size(); ++J)
              NativeArgs.push_back(S.args[J].type == "ptr" ? decode(B,Out,Base,GuestArgs[J],S.args[J],GuestArgs) : GuestArgs[J]);
            auto Native = Out.getOrInsertFunction(S.native, ABI::nativeSignature(C,S));
            R = B.CreateCall(Native,NativeArgs);
            if (S.result.type == "ptr") R = encode(B,Out,Base,R,S.result,GuestArgs);
            postconditions(B,Out,Base,S,GuestArgs,R,Epoch);
            V[&I] = R; continue;
          }
          if (!Callee || !Functions.count(Callee))
            reject("external/indirect call boundary: " + I.getFunction()->getName() +
                   " -> " + (Callee ? Callee->getName() : StringRef("<indirect>")));
          SmallVector<Value *> Args{Base}; for (Value *A : X->args()) Args.push_back(Get(A));
          auto K=Img.codes.find(symbolKey(*Callee));
          bool Known=K!=Img.codes.end() && K->second.definition;
          const RegisterEdge *Edge=nullptr;
          for(const auto &E:Img.registerEdges)if(E.source==In->getSourceFileName() && E.function==F.getName() && E.target==Callee->getName() && I.getDebugLoc() && E.line==I.getDebugLoc().getLine()){
            if(Edge)reject("duplicate register edge");Edge=&E;
          }
          if(Edge && Edge->mode=="previous-result"){
            if(PreviousTarget!=Edge->previous || !PreviousResult || !PreviousResult->getType()->isIntegerTy())reject("register edge producer mismatch in "+F.getName());
            Args.push_back(PreviousResult);
          }else if(Edge && Edge->mode=="live-in"){
            if(!ImplicitR0)reject("missing register live-in");Args.push_back(ImplicitR0);
          }
          Type *ResultType=X->use_empty()?B.getVoidTy():valueType(X->getType());
          bool Preserved=Edge && Edge->mode=="preserved-argument";
          R = guestCall(B,Functions.at(Callee),Args,Preserved?B.getVoidTy():ResultType,K!=Img.codes.end() && K->second.signReturn,
                        X->getFunctionType()->isVarArg() || (GuestExternals && Known),Known?&K->second.used:nullptr);
          if(Preserved){if(Edge->argument+1>=Args.size())reject("register return argument index");R=adaptScalar(B,Args[Edge->argument+1],ResultType);}
          PreviousResult=R;PreviousTarget=Callee->getName().str();
        } else reject("instruction " + Twine(I.getOpcodeName()));
        V[&I] = R;
      }
    }
    for (BasicBlock &BB : F) for (PHINode &P : BB.phis()) {
      auto *NP = cast<PHINode>(V.at(&P));
      for (unsigned J = 0; J < P.getNumIncomingValues(); ++J)
        { IRBuilder<> Edge(Blocks.at(P.getIncomingBlock(J))->getTerminator());Current=&Edge;
          NP->addIncoming(Get(P.getIncomingValue(J)), Blocks.at(P.getIncomingBlock(J))); }
    }
  }
  if(GuestExternals){
    // One explicit, caller-invoked initializer per original C member.
    auto *Init=Function::Create(FunctionType::get(Type::getVoidTy(C),{PointerType::getUnqual(C)},false),GlobalValue::ExternalLinkage,
      Prefix+"initialize_"+Twine(hash_value(In->getSourceFileName())).str(),Out);
    IRBuilder<> B(BasicBlock::Create(C,"entry",Init));Value *Base=Init->getArg(0);
    for(GlobalVariable &G:In->globals())if(G.hasInitializer() && V.count(&G)){
      uint32_t Offset=(uint32_t)cast<ConstantInt>(V.at(&G))->getZExtValue();
      Value *P=runtime(B,Out,"g32_resolve",B.getPtrTy(),{Base,B.getInt32(Offset),B.getInt32(DL.getTypeAllocSize(G.getValueType()).getFixedValue()),B.getInt32(0)});
      B.CreateMemSet(P,B.getInt8(0),DL.getTypeAllocSize(G.getValueType()).getFixedValue(),Align(1));
      initializeConstant(B,Out,DL,Base,Offset,G.getInitializer(),V,Img,ExternalAddresses);
    }
    B.CreateRetVoid();
  }
  for (const auto &Entry : Interfaces.exports) {
    const auto &S = Entry.second;
    if (Out.getFunction(S.native)) reject("export symbol collision: " + S.native);
    auto *Wrapper = Function::Create(ABI::nativeSignature(C,S),GlobalValue::ExternalLinkage,S.native,Out);
    if (Asan) Wrapper->addFnAttr(Attribute::SanitizeAddress);
    IRBuilder<> B(BasicBlock::Create(C,"entry",Wrapper));
    auto A = Wrapper->arg_begin(); Value *Base = &*A++;
    SmallVector<Value *> NativeArgs, GuestArgs, CallArgs{Base};
    for (; A != Wrapper->arg_end(); ++A) NativeArgs.push_back(&*A);
    Value *Epoch = S.result.role == "owned" ? runtime(B,Out,"g32_epoch",B.getInt64Ty(),{Base}) : nullptr;
    for (unsigned J = 0; J < S.args.size(); ++J) {
      Value *G = S.args[J].type == "ptr" ? encode(B,Out,Base,NativeArgs[J],S.args[J],NativeArgs) : NativeArgs[J];
      GuestArgs.push_back(G); CallArgs.push_back(G);
    }
    Value *R = B.CreateCall(Functions.at(In->getFunction(Entry.first)),CallArgs);
    postconditions(B,Out,Base,S,GuestArgs,R,Epoch);
    if (S.result.type == "ptr") R = decode(B,Out,Base,R,S.result,GuestArgs);
    if (S.result.type == "void") B.CreateRetVoid(); else B.CreateRet(R);
  }
  if (verifyModule(Out, &errs())) return 1;
  std::error_code EC; raw_fd_ostream OS(argv[2], EC);
  if (EC) { errs() << EC.message() << '\n'; return 1; }
  Out.print(OS, nullptr);
}
