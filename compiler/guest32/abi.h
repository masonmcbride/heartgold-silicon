// Compile-time typed boundaries. No dynamic import table. SPDX-License-Identifier: MIT
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include <set>

struct BoundaryType {
  std::string type, role;
  uint32_t bytes = 0;
  int bytesArg = -1, aliasArg = -1;
  bool nullable = false;
};
struct Boundary {
  std::string native;
  int64_t entryOwner = -1;
  std::vector<BoundaryType> args;
  BoundaryType result;
};
struct Placement { uint32_t offset, size; };

class ABI {
  static void keys(const json::Object &O, std::initializer_list<StringRef> Allowed) {
    for (const auto &K : O) {
      bool Found = false; for (StringRef A : Allowed) if (StringRef(K.first) == A) Found = true;
      if (!Found) reject("unknown ABI key " + K.first);
    }
  }
  static std::string str(const json::Object &O, StringRef K) {
    auto S = O.getString(K); if (!S) reject("missing ABI string " + K); return S->str();
  }
  static uint32_t number(const json::Object &O, StringRef K) {
    auto N = O.getInteger(K); if (!N || *N < 0 || *N > UINT32_MAX) reject("invalid ABI number " + K);
    return (uint32_t)*N;
  }
  static BoundaryType type(const json::Value &V, bool Result) {
    auto *O = V.getAsObject(); if (!O) reject("ABI type must be object");
    keys(*O, {"type", "role", "bytes", "bytes_arg", "argument", "nullable"});
    BoundaryType T; T.type = str(*O, "type");
    if (T.type != "ptr") {
      if (O->size() != 1 || (T.type != "i32" && T.type != "i64" &&
          T.type != "f32" && T.type != "f64" && !(Result && T.type == "void")))
        reject("unsupported ABI scalar/type " + T.type);
      return T;
    }
    T.role = str(*O, "role");
    if (Result ? (T.role != "alias" && T.role != "owned") :
                 (T.role != "borrow" && T.role != "consume")) reject("ABI pointer ownership role");
    auto Nullable = O->getBoolean("nullable"); if (!Nullable) reject("ABI pointer needs nullable boolean");
    T.nullable = *Nullable;
    if (bool(O->get("bytes")) == bool(O->get("bytes_arg"))) reject("ABI pointer needs exactly one extent");
    if (O->get("bytes")) T.bytes = number(*O, "bytes");
    else {
      uint32_t N = number(*O,"bytes_arg"); if (N > INT32_MAX) reject("extent argument overflow"); T.bytesArg = N;
    }
    if (T.role == "alias") {
      uint32_t N = number(*O,"argument"); if (N > INT32_MAX) reject("alias argument overflow"); T.aliasArg = N;
    }
    else if (O->get("argument")) reject("argument only valid on alias result");
    return T;
  }
  static void signatures(const json::Object *O, std::map<std::string, Boundary> &Dest) {
    if (!O) return;
    for (const auto &Entry : *O) {
      auto *S = Entry.second.getAsObject(); if (!S) reject("ABI function must be object");
      keys(*S, {"native", "args", "result", "entry_owner"});
      Boundary B; B.native = str(*S, "native");
      if(S->get("entry_owner"))B.entryOwner=number(*S,"entry_owner");
      if (B.native.empty()) reject("empty native symbol");
      auto *Args = S->getArray("args"); auto *Ret = S->get("result");
      if (!Args || !Ret) reject("missing ABI arguments/result");
      for (const auto &A : *Args) B.args.push_back(type(A, false));
      B.result = type(*Ret, true);
      auto Check = [&](const BoundaryType &T) {
        if (T.bytesArg >= 0 && ((size_t)T.bytesArg >= B.args.size() || B.args[T.bytesArg].type != "i32"))
          reject("extent must reference an i32 argument");
        if (T.aliasArg >= 0 && ((size_t)T.aliasArg >= B.args.size() || B.args[T.aliasArg].type != "ptr"))
          reject("alias must reference pointer argument");
      };
      for (const auto &A : B.args) Check(A); Check(B.result);
      Dest.emplace(Entry.first.str(), std::move(B));
    }
  }
public:
  std::map<std::string, Boundary> calls, exports;
  std::map<std::string, Placement> globals;
  std::map<std::string, uint32_t> absoluteSymbols;
  static Type *nativeType(LLVMContext &C, const BoundaryType &T) {
    if (T.type == "ptr") return PointerType::getUnqual(C);
    if (T.type == "void") return Type::getVoidTy(C);
    if (T.type == "i32") return Type::getInt32Ty(C);
    if (T.type == "i64") return Type::getInt64Ty(C);
    if (T.type == "f32") return Type::getFloatTy(C);
    if (T.type == "f64") return Type::getDoubleTy(C);
    reject("unknown ABI type");
  }
  static FunctionType *nativeSignature(LLVMContext &C, const Boundary &S) {
    SmallVector<Type *> A{PointerType::getUnqual(C)};
    for (const auto &T : S.args) A.push_back(nativeType(C, T));
    return FunctionType::get(nativeType(C, S.result), A, false);
  }
  static void checkGuest(const Function &F, const Boundary &S) {
    if (F.isVarArg() || F.arg_size() != S.args.size() || F.getCallingConv() != CallingConv::C)
      reject("guest ABI signature: " + F.getName());
    if (F.getReturnType() != nativeType(F.getContext(), S.result)) reject("guest ABI return: " + F.getName());
    unsigned I = 0; for (const Argument &A : F.args()) {
      if (A.getType() != nativeType(F.getContext(), S.args[I++]) || A.hasByValAttr() || A.hasStructRetAttr())
        reject("guest ABI argument: " + F.getName());
    }
  }
  void read(StringRef Path, Module &Native) {
    auto Buffer = MemoryBuffer::getFile(Path); if (!Buffer) reject("cannot read ABI manifest");
    auto Parsed = json::parse((*Buffer)->getBuffer());
    if (!Parsed) { consumeError(Parsed.takeError()); reject("invalid ABI JSON"); }
    auto *Root = Parsed->getAsObject(); if (!Root) reject("ABI root must be object");
    keys(*Root, {"version", "calls", "exports", "globals", "absolute_symbols"});
    if (Root->getInteger("version") != 1) reject("ABI version");
    for (StringRef K : {"calls","exports","globals","absolute_symbols"})
      if (Root->get(K) && !Root->getObject(K)) reject("ABI section must be object: " + K);
    signatures(Root->getObject("calls"), calls); signatures(Root->getObject("exports"), exports);
    if (auto *A = Root->getObject("absolute_symbols")) for (const auto &Entry : *A)
      absoluteSymbols.emplace(Entry.first.str(), number(*A, Entry.first));
    if (auto *G = Root->getObject("globals")) for (const auto &Entry : *G) {
      auto *O = Entry.second.getAsObject(); if (!O) reject("global placement must be object");
      keys(*O, {"offset", "size"});
      Placement P{number(*O, "offset"), number(*O, "size")};
      if (P.offset < 4096 || !P.size || (uint64_t)P.offset+P.size > UINT32_MAX) reject("invalid global placement");
      globals.emplace(Entry.first.str(), P);
    }
    for (const auto &A : absoluteSymbols)
      if (globals.count(A.first)) reject("absolute symbol also has storage: " + A.first);
    for (const auto &E : calls) {
      if(E.second.entryOwner>=0)reject("entry_owner is only valid on native exports");
      Function *F = Native.getFunction(E.second.native);
      if (!F || F->getFunctionType() != nativeSignature(Native.getContext(), E.second) ||
          F->getCallingConv() != CallingConv::C) reject("native ABI signature: " + E.second.native);
    }
    for (const auto &E : exports) {
      Function *F = Native.getFunction(E.second.native);
      if (!F || F->getFunctionType() != nativeSignature(Native.getContext(), E.second) ||
          F->getCallingConv() != CallingConv::C) reject("native callback ABI signature: " + E.second.native);
    }
  }
};

// These helpers also guard callbacks; no host address is truncated into a word.
static Value *runtime(IRBuilder<> &B, Module &M, StringRef Name, Type *Ret, ArrayRef<Value *> Args) {
  SmallVector<Type *> Types; for (Value *A : Args) Types.push_back(A->getType());
  return B.CreateCall(M.getOrInsertFunction(Name, FunctionType::get(Ret, Types, false)), Args);
}
static Value *extent(IRBuilder<> &B, const BoundaryType &T, ArrayRef<Value *> Args) {
  return T.bytesArg >= 0 ? Args[T.bytesArg] : B.getInt32(T.bytes);
}
static Value *decode(IRBuilder<> &B, Module &M, Value *Base, Value *Offset, const BoundaryType &T, ArrayRef<Value *> Args) {
  return runtime(B, M, "g32_resolve", B.getPtrTy(), {Base, Offset, extent(B,T,Args), B.getInt32(T.nullable)});
}
static Value *encode(IRBuilder<> &B, Module &M, Value *Base, Value *Pointer, const BoundaryType &T, ArrayRef<Value *> Args) {
  return runtime(B, M, "g32_encode", B.getInt32Ty(), {Base, Pointer, extent(B,T,Args), B.getInt32(T.nullable)});
}
static void postconditions(IRBuilder<> &B, Module &M, Value *Base, const Boundary &S,
                           ArrayRef<Value *> Args, Value *Result, Value *Epoch) {
  for (unsigned I = 0; I < S.args.size(); ++I) if (S.args[I].role == "consume")
    runtime(B,M,"g32_check_consumed",B.getVoidTy(),{Base,Args[I]});
  if (S.result.type == "ptr") {
    if (S.result.role == "owned") runtime(B,M,"g32_check_owned",B.getVoidTy(),{Base,Result,Epoch});
    else runtime(B,M,"g32_check_alias",B.getVoidTy(),{Base,Result,Args[S.result.aliasArg]});
  }
}
static Value *bridgeCall(IRBuilder<> &B,Module &M,Value *Base,const Boundary &S,ArrayRef<Value*> GuestArgs){
  if(GuestArgs.size()!=S.args.size())reject("typed boundary argument count");
  SmallVector<Value*> NativeArgs{Base};
  Value *Epoch=S.result.role=="owned"?runtime(B,M,"g32_epoch",B.getInt64Ty(),{Base}):nullptr;
  for(unsigned I=0;I<S.args.size();++I)NativeArgs.push_back(S.args[I].type=="ptr"?decode(B,M,Base,GuestArgs[I],S.args[I],GuestArgs):GuestArgs[I]);
  Value *R=B.CreateCall(M.getOrInsertFunction(S.native,ABI::nativeSignature(M.getContext(),S)),NativeArgs);
  if(S.result.type=="ptr")R=encode(B,M,Base,R,S.result,GuestArgs);
  postconditions(B,M,Base,S,GuestArgs,R,Epoch);return R;
}
