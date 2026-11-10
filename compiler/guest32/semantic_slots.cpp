// Source-preserving native pointer-slot legalization. SPDX-License-Identifier: MIT
// Runs before optimization. Never supplies missing original call arguments.
#include "llvm/ADT/PostOrderIterator.h"
#include "llvm/Analysis/LazyValueInfo.h"
#include "llvm/Analysis/AssumptionCache.h"
#include "llvm/IR/ConstantRange.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/DebugInfo.h"
#include "llvm/IR/Dominators.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/InstIterator.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Operator.h"
#include "llvm/IR/Verifier.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/Signals.h"
#include "llvm/Transforms/Utils/PromoteMemToReg.h"
#include <map>
#include <set>
#include <algorithm>
#include <cstdlib>
#include <memory>
#include <optional>
#include <vector>
using namespace llvm;
namespace {
[[noreturn]] void fail(const Twine &s) { errs()<<"semantic slots: "<<s<<'\n'; exit(1); }
struct Unit { LLVMContext context; std::unique_ptr<Module> module; std::string path; };
void prepare(Module &m) {
  StripDebugInfo(m);
  for(auto &f:m) if(!f.isDeclaration()) {
    SmallVector<AllocaInst*> allocas;
    for(auto &i:f.getEntryBlock()) if(auto *a=dyn_cast<AllocaInst>(&i))
      if(isAllocaPromotable(a)) allocas.push_back(a);
    DominatorTree dt(f); PromoteMemToReg(allocas,dt);
  }
}
std::unique_ptr<Unit> readUnit(StringRef path) {
  auto u=std::make_unique<Unit>();u->path=path.str(); SMDiagnostic d;
  u->module=parseIRFile(path,d,u->context);
  if(!u->module) { d.print("semantic slots",errs());fail("cannot read input"); }
  if(u->module->getDataLayout().getPointerSize()!=8) fail("promotion requires a native 64-bit module; guest layout must remain separate");
  prepare(*u->module);return u;
}
json::Value readJSON(StringRef path) {
  auto b=MemoryBuffer::getFile(path);if(!b)fail("cannot read "+path);
  auto j=json::parse((*b)->getBuffer());if(!j)fail(toString(j.takeError()));return std::move(*j);
}
void writeJSON(StringRef path,json::Value j) {
 std::error_code ec;raw_fd_ostream o(path,ec);if(ec)fail(ec.message());o<<formatv("{0:2}\n",j);
}
std::string key(StructType *s,unsigned i) { return s->getName().str()+":"+std::to_string(i); }
using Fields=std::set<std::string>;
using Env=std::map<const Argument*,ConstantRange>;
bool contains(Type *,const std::set<std::string> &,std::set<Type*> seen={});
struct World {
 std::vector<std::unique_ptr<Unit>> units;
 std::map<std::string,Function*> definitions;
 std::map<std::string,std::string> conflicts;
 std::map<std::string,std::pair<std::string,unsigned>> fieldTypes;
 std::map<std::string,Fields> rejected;
 std::map<std::string,Fields> storageLinks;
 std::set<std::string> candidates;
 std::map<Function*,std::vector<CallBase*>> callers;
 std::map<Value*,Fields> addressCache;
 std::map<std::string,Fields> callCache;
 std::set<Function*> addressReturning;
 std::map<Function*,std::set<BasicBlock*>> reachable;
 std::map<Function*,std::unique_ptr<AssumptionCache>> assumptions;
 std::map<Function*,std::unique_ptr<LazyValueInfo>> ranges;
 std::map<Function*,std::unique_ptr<DominatorTree>> dominators;
 std::set<std::pair<std::string,unsigned>> releases;
 Function *definition(Function *f) {
  if(!f)return nullptr;if(!f->isDeclaration())return f;
  auto p=definitions.find(f->getName().str());return p==definitions.end()?nullptr:p->second;
 }
 ConstantRange project(Value *target,Value *expression,ConstantRange allowed,unsigned depth=0) {
  auto full=ConstantRange::getFull(target->getType()->getIntegerBitWidth());
  if(depth>16)return full;if(target==expression)return allowed;
  if(auto *c=dyn_cast<CastInst>(expression))if(c->getOperand(0)->getType()->isIntegerTy()) {
   unsigned bits=c->getOperand(0)->getType()->getIntegerBitWidth();
   if(c->getOpcode()==Instruction::ZExt || c->getOpcode()==Instruction::SExt) {
    auto domain=ConstantRange::getFull(bits).castOp(c->getOpcode(),allowed.getBitWidth());
    return project(target,c->getOperand(0),allowed.intersectWith(domain).truncate(bits),depth+1);
   }
  }
  return full;
 }
 ConstantRange range(Value *v,const Env &env,Instruction *at,unsigned depth=0) {
  unsigned bits=v->getType()->getIntegerBitWidth();auto full=ConstantRange::getFull(bits);
  if(depth>32)return full;
  if(auto *c=dyn_cast<ConstantInt>(v))return ConstantRange(c->getValue());
  ConstantRange r=full;
  if(auto *a=dyn_cast<Argument>(v)) {auto p=env.find(a);if(p!=env.end())r=p->second;}
  if(auto *c=dyn_cast<CastInst>(v))if(c->getOperand(0)->getType()->isIntegerTy())r=range(c->getOperand(0),env,at,depth+1).castOp(c->getOpcode(),bits);
  if(auto *b=dyn_cast<BinaryOperator>(v))r=range(b->getOperand(0),env,at,depth+1).binaryOp(b->getOpcode(),range(b->getOperand(1),env,at,depth+1));
  if(auto *cmp=dyn_cast<ICmpInst>(v))if(cmp->getOperand(0)->getType()->isIntegerTy()) {
   auto lhs=range(cmp->getOperand(0),env,at,depth+1),rhs=range(cmp->getOperand(1),env,at,depth+1);
   if(lhs.icmp(cmp->getPredicate(),rhs))r=ConstantRange(APInt(1,1));
   else if(lhs.icmp(CmpInst::getInversePredicate(cmp->getPredicate()),rhs))r=ConstantRange(APInt(1,0));
  }
  if(at) {
   auto *f=at->getFunction();auto &lvi=ranges[f];if(!lvi) {auto &ac=assumptions[f];ac=std::make_unique<AssumptionCache>(*f);lvi=std::make_unique<LazyValueInfo>(f,ac.get());}
   r=r.intersectWith(lvi->getConstantRange(v,at,false));
   auto &dt=dominators[f];if(!dt)dt=std::make_unique<DominatorTree>(*f);
   for(auto &bb:*f)if(dt->dominates(&bb,at->getParent()))if(auto *br=dyn_cast<CondBrInst>(bb.getTerminator())) {
    bool yes=dt->dominates(br->getSuccessor(0),at->getParent()),no=dt->dominates(br->getSuccessor(1),at->getParent());
    if(yes==no)continue;
    if(auto *cmp=dyn_cast<ICmpInst>(br->getCondition())) {
     Value *x=cmp->getOperand(0);auto *constant=dyn_cast<ConstantInt>(cmp->getOperand(1));auto pred=cmp->getPredicate();
     if(!constant){constant=dyn_cast<ConstantInt>(x);x=cmp->getOperand(1);pred=CmpInst::getSwappedPredicate(pred);}
     if(constant){if(no)pred=CmpInst::getInversePredicate(pred);auto allowed=ConstantRange::makeExactICmpRegion(pred,constant->getValue());r=r.intersectWith(project(v,x,allowed));}
    }
   }
  }
  return r;
 }
 std::optional<int64_t> number(Value *v,const Env &env) {
  if(!v->getType()->isIntegerTy())return {};
  // Respect integer truncation/extension. Stripping a cast could select the
  // default arm for (u8)287 instead of the original arm for 31.
  auto r=range(v,env,nullptr);if(auto *n=r.getSingleElement())if(n->getSignificantBits()<=64)return n->getSExtValue();
  return {};
 }
 Fields addresses(Value *v,const Env &env={},unsigned depth=0,std::set<Value*> seen={}) {
  if(!v->getType()->isPointerTy())return {};
  if(depth==0 && env.empty()) {
   auto p=addressCache.find(v);if(p!=addressCache.end())return p->second;
   auto r=address(v,env,depth,std::move(seen));addressCache[v]=r;return r;
  }
  return address(v,env,depth,std::move(seen));
 }
 Fields address(Value *v,const Env &env,unsigned depth,std::set<Value*> seen) {
  if(depth>32 || !seen.insert(v).second)return {"<unproved-alias>"};
  if(auto *a=dyn_cast<Argument>(v)) {
   Fields r;
   auto *owner=definition(a->getParent());
   // An argument's callers range over all invocations, not just the currently
   // specialized outer accessor path. Do not cache a path-pruned alias union.
   auto savedReachable=std::move(reachable);reachable.clear();
   for(auto *c:callers[owner])if(a->getArgNo()<c->arg_size()) {
    auto q=addresses(c->getArgOperand(a->getArgNo()),{},depth+1,seen);r.insert(q.begin(),q.end());
   }
   reachable=std::move(savedReachable);return r;
  }
  if(auto *g=dyn_cast<GEPOperator>(v)) {
   Type *t=g->getSourceElementType();Fields result;
   bool first=true;
   for(Value *idx:g->indices()) {
    if(first){first=false;continue;}
    if(auto *s=dyn_cast<StructType>(t)) {
     auto *n=dyn_cast<ConstantInt>(idx);if(!n)return {};
     unsigned i=n->getZExtValue();if(i>=s->getNumElements())return {};
     auto k=key(s,i);fieldTypes[k]={s->getName().str(),i};result={k};t=s->getElementType(i);
    } else if(auto *a=dyn_cast<ArrayType>(t))t=a->getElementType();else return {};
   }
   if(!result.empty())return result;
   return addresses(g->getPointerOperand(),env,depth+1,seen);
  }
  if(auto *p=dyn_cast<PHINode>(v)) {
   Fields r;for(unsigned i=0;i<p->getNumIncomingValues();i++) {
    auto q=reachable.find(p->getFunction());if(q!=reachable.end()&&!q->second.count(p->getIncomingBlock(i)))continue;
    auto a=addresses(p->getIncomingValue(i),env,depth+1,seen);r.insert(a.begin(),a.end());
   }return r;
  }
  if(auto *s=dyn_cast<SelectInst>(v)) {
   auto r=addresses(s->getTrueValue(),env,depth+1,seen),q=addresses(s->getFalseValue(),env,depth+1,seen);r.insert(q.begin(),q.end());return r;
  }
  if(auto *c=dyn_cast<CastInst>(v))return addresses(c->getOperand(0),env,depth+1,seen);
  if(auto *call=dyn_cast<CallBase>(v)) {
   Function *f=definition(call->getCalledFunction());if(!f || f->isDeclaration())return {};
   if(!addressReturning.count(f))return {};
   Env e;for(unsigned i=0;i<std::min<unsigned>(call->arg_size(),f->arg_size());i++)if(call->getArgOperand(i)->getType()->isIntegerTy() && f->getArg(i)->getType()->isIntegerTy()) {
    auto r=range(call->getArgOperand(i),env,call);unsigned bits=f->getArg(i)->getType()->getIntegerBitWidth();
    if(r.getBitWidth()!=bits) {
     if(r.getBitWidth()<bits && call->paramHasAttr(i,Attribute::SExt))r=r.signExtend(bits);
     else if(r.getBitWidth()<bits && call->paramHasAttr(i,Attribute::ZExt))r=r.zeroExtend(bits);
     else r=ConstantRange::getFull(bits);
    }
    e.insert_or_assign(f->getArg(i),r);
   }
   std::string cacheKey;raw_string_ostream cacheStream(cacheKey);cacheStream<<static_cast<const void*>(f);for(auto &[arg,r]:e)cacheStream<<":"<<arg->getArgNo()<<"="<<r;
   auto cached=callCache.find(cacheKey);if(cached!=callCache.end())return cached->second;
   std::set<BasicBlock*> reached;SmallVector<BasicBlock*> pending{&f->getEntryBlock()};Fields r;SmallVector<Value*> returns;
   while(!pending.empty()) {
    auto *b=pending.pop_back_val();if(!reached.insert(b).second)continue;
    auto *term=b->getTerminator();
    if(auto *ret=dyn_cast<ReturnInst>(term)) {
     if(ret->getReturnValue()) returns.push_back(ret->getReturnValue());
    }else if(auto *sw=dyn_cast<SwitchInst>(term)) {
     if(auto n=number(sw->getCondition(),e)) {
      auto *target=sw->getDefaultDest();for(auto c:sw->cases())if(c.getCaseValue()->getSExtValue()==*n)target=c.getCaseSuccessor();pending.push_back(target);
     }else {
      auto r=range(sw->getCondition(),e,sw);if(std::getenv("HG_SLOT_RANGE_TRACE"))errs()<<"selector "<<f->getName()<<" "<<r<<'\n';pending.push_back(sw->getDefaultDest());
      for(auto c:sw->cases())if(r.contains(c.getCaseValue()->getValue()))pending.push_back(c.getCaseSuccessor());
     }
    }else if(auto *br=dyn_cast<BranchInst>(term)) {
     if(br->isConditional()) {if(auto n=number(br->getCondition(),e))pending.push_back(br->getSuccessor(*n?0:1));else {pending.push_back(br->getSuccessor(0));pending.push_back(br->getSuccessor(1));}}
     else pending.push_back(br->getSuccessor(0));
    }else for(unsigned i=0;i<term->getNumSuccessors();i++)pending.push_back(term->getSuccessor(i));
   }
   auto previous=reachable.find(f);bool had=previous!=reachable.end();std::set<BasicBlock*> saved;if(had)saved=previous->second;
   reachable[f]=std::move(reached);
   for(auto *rv:returns){auto a=addresses(rv,e,depth+1,seen);r.insert(a.begin(),a.end());}
   if(had)reachable[f]=std::move(saved);else reachable.erase(f);
   callCache[cacheKey]=r;
   return r;
  }
  return {};
 }
 bool pointerValue(Value *v,unsigned depth=0) {
  if(depth>20)return false;
  if(v->getType()->isPointerTy() && v->getType()->getPointerAddressSpace())return false;
  if(auto *c=dyn_cast<CallBase>(v)) {auto *f=definition(c->getCalledFunction());return f && f->getReturnType()->isPointerTy() && !f->getReturnType()->getPointerAddressSpace() && !conflicts.count(f->getName().str());}
  if(auto *c=dyn_cast<CastInst>(v)) {
   if(isa<PtrToIntInst>(c)||isa<IntToPtrInst>(c)||isa<BitCastInst>(c))return pointerValue(c->getOperand(0),depth+1);
   return false;
  }
  if(auto *l=dyn_cast<LoadInst>(v)) {
   if(l->getType()->isPointerTy())return true;
   auto a=addresses(l->getPointerOperand());return !a.empty() && std::all_of(a.begin(),a.end(),[&](auto &k){return candidates.count(k);});
  }
  if(auto *s=dyn_cast<SelectInst>(v)) {
   bool a=pointerValue(s->getTrueValue(),depth+1),b=pointerValue(s->getFalseValue(),depth+1);
   return (a||b) && (a||matchZero(s->getTrueValue())) && (b||matchZero(s->getFalseValue()));
  }
  if(auto *p=dyn_cast<PHINode>(v)) {
   bool any=false;for(auto &x:p->incoming_values())if(x!=p) {bool pointer=pointerValue(x,depth+1);any|=pointer;if(!pointer&&!matchZero(x))return false;}return any;
  }
  if(auto *g=dyn_cast<GEPOperator>(v))return pointerValue(g->getPointerOperand(),depth+1);
  if(auto *c=dyn_cast<ConstantExpr>(v)) {
   if(c->getOpcode()==Instruction::IntToPtr)return false;
   if(c->isCast())return pointerValue(c->getOperand(0),depth+1);
  }
  if(v->getType()->isPointerTy())return isa<Argument>(v)||isa<AllocaInst>(v)||isa<GlobalValue>(v)||isa<ConstantPointerNull>(v);
  return false;
 }
 Fields valueFields(Value *v,std::set<Value*> seen={}) {
  if(!seen.insert(v).second)return {};
  if(auto *l=dyn_cast<LoadInst>(v))return addresses(l->getPointerOperand());
  if(auto *c=dyn_cast<CastInst>(v))return valueFields(c->getOperand(0),seen);
  Fields r;
  if(auto *p=dyn_cast<PHINode>(v))for(auto &a:p->incoming_values()){auto q=valueFields(a,seen);r.insert(q.begin(),q.end());}
  if(auto *s=dyn_cast<SelectInst>(v))for(auto *a:{s->getTrueValue(),s->getFalseValue()}){auto q=valueFields(a,seen);r.insert(q.begin(),q.end());}
  return r;
 }
 void reject(const Fields &f,StringRef reason) {for(auto &k:f)if(candidates.count(k))rejected[k].insert(reason.str());}
 // Validate every use of an integer-carried pointer before changing its type.
 void uses(Value *v,const Fields &f,std::set<Value*> &seen) {
  if(isa<Constant>(v))return;
  if(v->getType()->isPointerTy())return;
  if(!seen.insert(v).second)return;
  for(User *user:v->users()) {
   if(auto *c=dyn_cast<CastInst>(user)) {
    if(isa<IntToPtrInst>(c)||isa<PtrToIntInst>(c)||isa<BitCastInst>(c))uses(c,f,seen);else reject(f,"integer width conversion observes pointer representation");
   }else if(auto *s=dyn_cast<StoreInst>(user)) {
    if(s->getValueOperand()!=v){reject(f,"pointer-carried value used as an untyped address");continue;}
    auto a=addresses(s->getPointerOperand());if(a.empty())reject(f,"pointer value escapes to unproved storage");
    for(auto &k:a)if(!candidates.count(k))reject(f,"pointer value escapes to nonpromoted storage");
   }else if(auto *c=dyn_cast<ICmpInst>(user)) {
    if(!c->isEquality() || !(isa<ConstantPointerNull>(c->getOperand(1)) || matchZero(c->getOperand(1))))reject(f,"non-null pointer comparison observes integer representation");
   }else if(isa<PHINode>(user)||isa<SelectInst>(user))uses(cast<Value>(user),f,seen);
   else if(auto *c=dyn_cast<CallBase>(user)) {
    auto *d=definition(c->getCalledFunction());
    if(d && conflicts.count(d->getName().str()))reject(f,"ambiguous original provider ABI");
    for(unsigned i=0;i<c->arg_size();i++)if(c->getArgOperand(i)==v && (!d || i>=d->arg_size() || !d->getArg(i)->getType()->isPointerTy() || d->getArg(i)->getType()->getPointerAddressSpace()))reject(f,"integer pointer escapes across an unproved call boundary");
   }else reject(f,"unsupported pointer-value consumer");
  }
 }
 static bool matchZero(Value *v) {auto *c=dyn_cast<ConstantInt>(v);return c && c->isZero();}
 void analyze() {
  errs()<<"semantic slots: indexing "<<units.size()<<" native modules\n";
  for(auto &u:units) for(auto &f:*u->module)if(!f.isDeclaration() && !f.hasLocalLinkage()) {
   auto n=f.getName().str();auto p=definitions.find(n);
   if(p==definitions.end())definitions[n]=&f;
   else if(p->second->arg_size()!=f.arg_size() || p->second->getReturnType()->isPointerTy()!=f.getReturnType()->isPointerTy())conflicts[n]="inconsistent original definitions";
   else for(unsigned j=0;j<f.arg_size();j++)if(p->second->getArg(j)->getType()->isPointerTy()!=f.getArg(j)->getType()->isPointerTy())conflicts[n]="inconsistent original argument representations";
  }
  for(auto &u:units)for(auto &f:*u->module)for(auto &i:instructions(f))if(auto *c=dyn_cast<CallBase>(&i))
   if(auto *d=definition(c->getCalledFunction()))callers[d].push_back(c);
  bool changed=true;
  while(changed) {
   changed=false;
   for(auto &u:units)for(auto &f:*u->module)if(!f.isDeclaration() && f.getReturnType()->isPointerTy() && !addressReturning.count(&f)) {
    SmallVector<Value*> pending;std::set<Value*> seen;bool found=false;
    for(auto &bb:f)if(auto *r=dyn_cast<ReturnInst>(bb.getTerminator()))if(r->getReturnValue())pending.push_back(r->getReturnValue());
    while(!pending.empty()) {auto *v=pending.pop_back_val();if(!seen.insert(v).second)continue;
     if(isa<GEPOperator>(v)||isa<Argument>(v))found=true;
     if(auto *c=dyn_cast<CallBase>(v))if(addressReturning.count(definition(c->getCalledFunction())))found=true;
     if(auto *p=dyn_cast<PHINode>(v))for(auto &a:p->incoming_values())pending.push_back(a);
     if(auto *s=dyn_cast<SelectInst>(v)){pending.push_back(s->getTrueValue());pending.push_back(s->getFalseValue());}
     if(auto *c=dyn_cast<CastInst>(v))pending.push_back(c->getOperand(0));
    }
    if(found){addressReturning.insert(&f);changed=true;}
   }
  }
  errs()<<"semantic slots: resolving pointer stores\n";
  changed=true;
  while(changed) {
   changed=false;
   for(auto &u:units)for(auto &f:*u->module)for(auto &i:instructions(f))if(auto *s=dyn_cast<StoreInst>(&i)) {
    if(!s->getValueOperand()->getType()->isIntegerTy(32) || !pointerValue(s->getValueOperand()))continue;
    auto a=addresses(s->getPointerOperand());for(auto &k:a)if(fieldTypes.count(k))changed|=candidates.insert(k).second;
   }
  }
  for(auto &u:units)for(auto &f:*u->module)for(auto &i:instructions(f))if(auto *s=dyn_cast<StoreInst>(&i)) {
   auto from=valueFields(s->getValueOperand()),to=addresses(s->getPointerOperand());
   for(auto &a:from)for(auto &b:to)if(candidates.count(a)&&candidates.count(b)){storageLinks[a].insert(b);storageLinks[b].insert(a);}
  }
  for(auto &u:units)for(auto &f:*u->module)for(auto &i:instructions(f)) {
   if(auto *g=dyn_cast<GetElementPtrInst>(&i)) {
    auto a=addresses(g->getPointerOperand());bool zero=true;for(auto &idx:g->indices())zero&=matchZero(idx);
    if(!zero)reject(a,"arithmetic on a pointer-slot address");
   }
   if(auto *c=dyn_cast<PtrToIntInst>(&i))reject(addresses(c->getPointerOperand()),"pointer-slot address escapes as an integer");
   if(auto *s=dyn_cast<StoreInst>(&i))if(s->getValueOperand()->getType()->isPointerTy())reject(addresses(s->getValueOperand()),"slot address escapes to unresolved memory alias");
   if(auto *c=dyn_cast<CallBase>(&i))for(unsigned j=0;j<c->arg_size();j++) {
    auto a=addresses(c->getArgOperand(j));if(a.empty())continue;
    auto *d=definition(c->getCalledFunction());
    if(!d || d->isDeclaration() || j>=d->arg_size())reject(a,"slot address escapes to an unknown or raw-byte consumer");
   }
   Value *address=nullptr;Value *stored=nullptr;
   if(auto *s=dyn_cast<StoreInst>(&i)){address=s->getPointerOperand();stored=s->getValueOperand();}
   if(auto *l=dyn_cast<LoadInst>(&i))address=l->getPointerOperand();
   if(address) {
    auto a=addresses(address);bool relevant=false;for(auto &k:a)relevant|=candidates.count(k);
    if(!relevant)continue;
    // A pre-existing native pointer view needs no integer representation
    // rewrite, even through a dynamic accessor. Its access width is unchanged.
    if((stored && stored->getType()->isPointerTy()) || (isa<LoadInst>(i) && i.getType()->isPointerTy()))continue;
    if(std::getenv("HG_SLOT_TRACE")) {errs()<<"slot access "<<f.getName()<<": "<<i<<" ->";for(auto &k:a)errs()<<" "<<k;errs()<<'\n';}
    for(auto &k:a)if(!candidates.count(k))reject(a,"accessor may alias a nonpromoted field");
    if(auto *l=dyn_cast<LoadInst>(&i)) {
     if(l->isVolatile()||l->isAtomic()||!l->getType()->isIntegerTy(32))reject(a,"fixed-width or volatile slot observation");
     std::set<Value*> seen;uses(l,a,seen);
    }
    if(auto *s=dyn_cast<StoreInst>(&i)) {
     if(s->isVolatile()||s->isAtomic()||(!pointerValue(stored)&&!matchZero(stored)))reject(a,"nonpointer or volatile slot store");
     if(pointerValue(stored)){std::set<Value*> seen;uses(stored,a,seen);}
    }
   }
  }
  // Constant/global slot-address aliases are not ordinary scalar SSA. Refuse
  // promotion rather than losing those aliases behind a pointer load.
  for(auto &u:units) {
   SmallVector<Constant*> pending;std::set<Constant*> seen;
   for(auto &g:u->module->globals())if(g.hasInitializer())pending.push_back(g.getInitializer());
   for(auto &a:u->module->aliases())pending.push_back(a.getAliasee());
   while(!pending.empty()) {auto *c=pending.pop_back_val();if(!seen.insert(c).second)continue;
    if(auto *g=dyn_cast<GEPOperator>(c)) {
     reject(addresses(c),"constant slot-address alias requires legalization");
     // Clang folds constant field addresses to byte GEPs, so their source
     // element type no longer describes the original record member.
     if(auto *base=dyn_cast<GlobalVariable>(g->getPointerOperand()->stripPointerCasts()))
      for(auto &k:candidates)if(contains(base->getValueType(),{fieldTypes[k].first}))rejected[k].insert("constant byte alias into promoted owner requires legalization");
    }
    for(auto &v:c->operands())if(auto *child=dyn_cast<Constant>(v))pending.push_back(child);
   }
  }
  errs()<<"semantic slots: checked "<<candidates.size()<<" candidate fields\n";
 }
};
}
namespace {
bool contains(Type *t,const std::set<std::string> &types,std::set<Type*> seen) {
 if(!seen.insert(t).second)return false;
 if(auto *s=dyn_cast<StructType>(t)) {
  if(s->hasName() && types.count(s->getName().str()))return true;
  if(!s->isOpaque())for(auto *e:s->elements())if(contains(e,types,seen))return true;
 } else if(auto *a=dyn_cast<ArrayType>(t))return contains(a->getElementType(),types,seen);
 return false;
}
void validateLayouts(World &w) {
 for(auto &u:w.units) {
  auto &m=*u->module;const auto &dl=m.getDataLayout();
  for(auto &k:w.candidates) {
   auto [name,index]=w.fieldTypes.at(k);auto *s=StructType::getTypeByName(m.getContext(),name);if(!s)continue;
   if(s->isOpaque() || index>=s->getNumElements() || s->isPacked() || !s->getElementType(index)->isIntegerTy(32)){w.rejected[k].insert("packed or incompatible field declaration");continue;}
   // This bounded promotion uses existing native padding. There is no guessed
   // sizeof constant rewrite: all enclosing extents, alignments and strides
   // must remain identical. Layout-changing components remain guest32.
   SmallVector<Type*> es(s->elements());es[index]=PointerType::getUnqual(m.getContext());
   auto *replacement=StructType::get(m.getContext(),es,s->isPacked());
   auto *a=dl.getStructLayout(s),*b=dl.getStructLayout(replacement);
   if(a->getSizeInBytes()!=b->getSizeInBytes() || a->getAlignment()!=b->getAlignment())w.rejected[k].insert("native allocation extent/stride change is not proved");
   for(unsigned i=0;i<s->getNumElements();i++)if(a->getElementOffset(i)!=b->getElementOffset(i))w.rejected[k].insert("native field offset change is not proved");
  }
 }
 // Whole-object byte observations and fixed-offset aliases must be identified
 // before admitting a field, even when its native extent fits existing padding.
 std::set<std::string> types;for(auto &k:w.candidates)types.insert(w.fieldTypes[k].first);
 std::map<Value*,std::set<std::string>> roots;
 std::map<Value*,std::set<uint64_t>> rootSizes;
 for(auto &u:w.units)for(auto &f:*u->module)for(auto &i:instructions(f)) {
  if(auto *g=dyn_cast<GetElementPtrInst>(&i))for(auto &name:types)if(contains(g->getSourceElementType(),{name})) {
   roots[g->getPointerOperand()].insert(name);rootSizes[g->getPointerOperand()].insert(u->module->getDataLayout().getTypeAllocSize(g->getSourceElementType()));
  }
  if(auto *a=dyn_cast<AllocaInst>(&i))for(auto &name:types)if(contains(a->getAllocatedType(),{name})) {
   roots[a].insert(name);rootSizes[a].insert(u->module->getDataLayout().getTypeAllocSize(a->getAllocatedType()));
  }
 }
 std::map<Value*,SmallVector<Value*>> flow;
 const auto staticRoots=roots;
 const auto staticSizes=rootSizes;
 auto edge=[&](Value *from,Value *to){if(from->getType()->isPointerTy() && to->getType()->isPointerTy())flow[from].push_back(to);};
 std::map<Function*,std::set<unsigned>> returnedArguments;
 for(auto &u:w.units)for(auto &f:*u->module)if(!f.isDeclaration() && f.getReturnType()->isPointerTy()) {
  SmallVector<Value*> pending;std::set<Value*> seen;
  for(auto &bb:f)if(auto *r=dyn_cast<ReturnInst>(bb.getTerminator()))if(r->getReturnValue())pending.push_back(r->getReturnValue());
  while(!pending.empty()) {auto *v=pending.pop_back_val();if(!seen.insert(v).second)continue;
   if(auto *arg=dyn_cast<Argument>(v))if(arg->getParent()==&f)returnedArguments[&f].insert(arg->getArgNo());
   if(auto *cast=dyn_cast<CastInst>(v))pending.push_back(cast->getOperand(0));
   if(auto *phi=dyn_cast<PHINode>(v))for(auto &a:phi->incoming_values())pending.push_back(a);
   if(auto *sel=dyn_cast<SelectInst>(v)){pending.push_back(sel->getTrueValue());pending.push_back(sel->getFalseValue());}
  }
 }
 for(auto &u:w.units)for(auto &f:*u->module)for(auto &i:instructions(f)) {
  if(auto *p=dyn_cast<PHINode>(&i))for(auto &v:p->incoming_values()){edge(v,p);edge(p,v);}
  if(auto *c=dyn_cast<CastInst>(&i)){edge(c->getOperand(0),c);edge(c,c->getOperand(0));}
  if(auto *s=dyn_cast<SelectInst>(&i)){edge(s->getTrueValue(),s);edge(s->getFalseValue(),s);}
  if(auto *c=dyn_cast<CallBase>(&i))if(auto *d=w.definition(c->getCalledFunction()))if(!d->isDeclaration()) {
   for(unsigned j=0;j<std::min<unsigned>(d->arg_size(),c->arg_size());j++)if(!w.releases.count({d->getName().str(),j})) {
    auto *arg=c->getArgOperand(j);auto *formal=d->getArg(j);edge(arg,formal);
    // A callee's actual typed GEP is a caller constraint. Only static type
    // requirements flow backward; dynamically accumulated owner facts do not
    // unify unrelated clients of a generic void-pointer function.
    if(auto r=staticRoots.find(formal);r!=staticRoots.end())roots[arg].insert(r->second.begin(),r->second.end());
    if(auto r=staticSizes.find(formal);r!=staticSizes.end())rootSizes[arg].insert(r->second.begin(),r->second.end());
   }
   if(c->getType()->isPointerTy())for(auto &bb:*d)if(auto *ret=dyn_cast<ReturnInst>(bb.getTerminator()))if(auto *rv=ret->getReturnValue()) {
    if(auto r=staticRoots.find(rv);r!=staticRoots.end())roots[c].insert(r->second.begin(),r->second.end());
    if(auto r=staticSizes.find(rv);r!=staticSizes.end())rootSizes[c].insert(r->second.begin(),r->second.end());
   }
   // Returned argument aliases are specialized per call. Common allocator and
   // release implementations never unify all callers' allocation identities.
   for(auto j:returnedArguments[d])if(j<c->arg_size())edge(c->getArgOperand(j),c);
  }
 }
 SmallVector<std::pair<Value*,std::string>> pending;
 for(auto &[value,names]:roots)for(auto &name:names)pending.emplace_back(value,name);
 while(!pending.empty()) {
  auto [value,name]=pending.pop_back_val();auto found=flow.find(value);if(found==flow.end())continue;
  for(auto *to:found->second)if(roots[to].insert(name).second)pending.emplace_back(to,name);
 }
 SmallVector<std::pair<Value*,uint64_t>> sizes;
 for(auto &[value,extents]:rootSizes)for(auto extent:extents)sizes.emplace_back(value,extent);
 while(!sizes.empty()) {
  auto [value,extent]=sizes.pop_back_val();auto found=flow.find(value);if(found==flow.end())continue;
  for(auto *to:found->second)if(rootSizes[to].insert(extent).second)sizes.emplace_back(to,extent);
 }
 for(auto &u:w.units)for(auto &f:*u->module)for(auto &i:instructions(f)) {
  auto rejectTypes=[&](const std::set<std::string> &ts,StringRef why){for(auto &k:w.candidates)if(ts.count(w.fieldTypes[k].first))w.rejected[k].insert(why.str());};
  if(auto *cast=dyn_cast<PtrToIntInst>(&i))rejectTypes(roots[cast->getPointerOperand()],"owner address carried as an integer requires logical-address proof");
  if(auto *g=dyn_cast<GetElementPtrInst>(&i))if(g->getSourceElementType()->isIntegerTy(8) && !roots[g->getPointerOperand()].empty())rejectTypes(roots[g->getPointerOperand()],("fixed byte offset into promoted owner: "+f.getName()).str());
  if(auto *c=dyn_cast<CallBase>(&i)) {
   auto *fn=c->getCalledFunction();auto n=fn?fn->getName():StringRef();
   bool bytes=n.contains("memcpy")||n.contains("memmove")||n.contains("memcmp")||n=="fwrite"||n=="write";
   if(bytes)for(auto &v:c->args())rejectTypes(roots[v],("raw-byte or serialized owner observation: "+f.getName()).str());
   auto *definition=w.definition(fn);
   if(!definition || definition->isDeclaration())for(unsigned j=0;j<c->arg_size();j++) {
    auto *arg=c->getArgOperand(j);if(roots[arg].empty() || c->doesNotAccessMemory())continue;
    bool fullZero=false;
    if(j==0 && (n=="memset" || n=="__memset_chk" || n.starts_with("llvm.memset.")) && c->arg_size()>=3 && World::matchZero(c->getArgOperand(1))) {
     if(auto *count=dyn_cast<ConstantInt>(c->getArgOperand(2))) {
      auto &extents=rootSizes[arg];fullZero=!extents.empty() && std::all_of(extents.begin(),extents.end(),[&](auto size){return size==count->getZExtValue();});
     }
    }
    if(!fullZero)rejectTypes(roots[arg],"owner escapes to an unproved byte-observing boundary: "+(fn?n.str():std::string("<indirect>")));
   }
  }
  if(auto *s=dyn_cast<StoreInst>(&i))if(contains(s->getValueOperand()->getType(),types))for(auto &k:w.candidates)w.rejected[k].insert("aggregate value copy requires field legalization");
  if(auto *l=dyn_cast<LoadInst>(&i))if(contains(l->getType(),types))for(auto &k:w.candidates)w.rejected[k].insert("aggregate value load requires field legalization");
 }
 bool changed=true;
 while(changed) {
  changed=false;
  for(auto &[field,links]:w.storageLinks)if(!w.rejected[field].empty())for(auto &other:links)
   if(w.rejected[other].empty()){w.rejected[other].insert("connected pointer-storage component is blocked");changed=true;}
 }
}
json::Object signature(Function &f) {
 json::Array args;for(auto &a:f.args())args.push_back(a.getType()->isPointerTy());
 return json::Object{{"pointer_return",f.getReturnType()->isPointerTy()},{"pointer_args",std::move(args)}};
}
void apply(World &w,Unit &u,const json::Object &plan,StringRef output) {
 auto &m=*u.module;auto &ctx=m.getContext();auto *ptr=PointerType::getUnqual(ctx);std::set<std::string> admitted;
 for(auto &row:*plan.getArray("slots")) {
  auto &r=*row.getAsObject();auto name=r.getString("struct")->str();unsigned idx=*r.getInteger("field");
  admitted.insert(name+":"+std::to_string(idx));
 }
 std::map<Value*,Value*> values;std::set<Instruction*> remove;
 std::map<Function*,Function*> functions;
 for(auto &entry:*plan.getObject("signatures")) {
  auto *old=m.getFunction(entry.first);if(!old || !old->isDeclaration())continue;
  auto &sig=*entry.second.getAsObject();auto *args=sig.getArray("pointer_args");SmallVector<Type*> ts;
  // Missing arguments are an independent ARM register-recovery obligation.
  // Never add a parameter at a call site that did not provide its value.
  if(old->arg_size()!=args->size())continue;
  bool change=false;unsigned j=0;for(auto &a:old->args()) {bool p=*(*args)[j++].getAsBoolean();auto *t=p?ptr:a.getType();ts.push_back(t);change|=t!=a.getType();}
  Type *ret=*sig.getBoolean("pointer_return")?ptr:old->getReturnType();change|=ret!=old->getReturnType();
  if(!change)continue;
  // Do not rewrite an unrelated ABI mismatch in this module.
  bool related=false;for(auto *user:old->users())if(auto *call=dyn_cast<CallBase>(user)) {
   if(ret==ptr)for(auto *cu:call->users())if(auto *s=dyn_cast<StoreInst>(cu))for(auto &k:w.addresses(s->getPointerOperand()))related|=admitted.count(k);
   for(auto &a:call->args())if(auto *l=dyn_cast<LoadInst>(a))for(auto &k:w.addresses(l->getPointerOperand()))related|=admitted.count(k);
  }
  if(!related)continue;
  std::string name=old->getName().str();old->setName(name+".slot.old");auto *nf=Function::Create(FunctionType::get(ret,ts,old->isVarArg()),old->getLinkage(),name,m);
  nf->setCallingConv(old->getCallingConv());nf->setAttributes(old->getAttributes());
  if(ret==ptr){nf->removeRetAttr(Attribute::SExt);nf->removeRetAttr(Attribute::ZExt);}
  for(unsigned j=0;j<ts.size();j++)if(ts[j]==ptr){nf->removeParamAttr(j,Attribute::SExt);nf->removeParamAttr(j,Attribute::ZExt);}
  functions[old]=nf;
 }
 // Create pointer SSA nodes before wiring their users, including loop PHIs.
 for(auto &f:m)for(auto &i:instructions(f)) {
  if(auto *cast=dyn_cast<PtrToIntInst>(&i)) {
   bool relevant=false;
   for(auto *user:cast->users())if(auto *s=dyn_cast<StoreInst>(user))for(auto &k:w.addresses(s->getPointerOperand()))relevant|=admitted.count(k);
   if(relevant){values[cast]=cast->getPointerOperand();remove.insert(cast);}
  }
  if(auto *l=dyn_cast<LoadInst>(&i)) {
   if(l->getType()->isPointerTy())continue;
   bool relevant=false;for(auto &k:w.addresses(l->getPointerOperand()))relevant|=admitted.count(k);
   if(relevant){IRBuilder<> b(l);auto *load=b.CreateLoad(ptr,l->getPointerOperand(),"slot.pointer");load->setAlignment(l->getAlign());values[l]=load;remove.insert(l);}
  }
  if(auto *c=dyn_cast<CallInst>(&i))if(functions.count(c->getCalledFunction())) {
   auto *nf=functions[c->getCalledFunction()];SmallVector<Value*> args;for(auto &a:c->args())args.push_back(a);
   // Placeholder pointer arguments are wired below after slot loads exist.
   for(unsigned j=0;j<args.size();j++)if(nf->getFunctionType()->getParamType(j)==ptr && !args[j]->getType()->isPointerTy())args[j]=PoisonValue::get(ptr);
   IRBuilder<> b(c);auto *nc=b.CreateCall(nf,args);nc->setCallingConv(c->getCallingConv());nc->setAttributes(c->getAttributes());
   if(nf->getReturnType()==ptr){nc->removeRetAttr(Attribute::SExt);nc->removeRetAttr(Attribute::ZExt);}
   for(unsigned j=0;j<args.size();j++)if(nf->getFunctionType()->getParamType(j)==ptr){nc->removeParamAttr(j,Attribute::SExt);nc->removeParamAttr(j,Attribute::ZExt);}
   values[c]=nc;remove.insert(c);
  }
 }
 bool changed=true;
 while(changed) {changed=false;for(auto &f:m)for(auto &i:instructions(f)) {
  if(values.count(&i))continue;
  if(auto *c=dyn_cast<CastInst>(&i))if(values.count(c->getOperand(0))) {if(isa<IntToPtrInst>(c)||isa<PtrToIntInst>(c)||isa<BitCastInst>(c)){values[c]=values[c->getOperand(0)];remove.insert(c);changed=true;}}
  if(auto *p=dyn_cast<PHINode>(&i)) {bool any=false;for(auto &a:p->incoming_values())any|=values.count(a);if(any){auto *np=PHINode::Create(ptr,p->getNumIncomingValues(),"slot.phi",p);values[p]=np;remove.insert(p);changed=true;}}
  if(auto *s=dyn_cast<SelectInst>(&i))if(values.count(s->getTrueValue())||values.count(s->getFalseValue())) {IRBuilder<> b(s);values[s]=b.CreateSelect(s->getCondition(),PoisonValue::get(ptr),PoisonValue::get(ptr),"slot.select");remove.insert(s);changed=true;}
 }}
 auto mapped=[&](Value *v)->Value* {if(values.count(v))return values.at(v);if(World::matchZero(v))return ConstantPointerNull::get(ptr);return v;};
 for(auto &[old,nv]:values) {
  if(auto *p=dyn_cast<PHINode>(old)) {auto *np=cast<PHINode>(nv);for(unsigned j=0;j<p->getNumIncomingValues();j++)np->addIncoming(mapped(p->getIncomingValue(j)),p->getIncomingBlock(j));}
  if(auto *s=dyn_cast<SelectInst>(old)) {auto *ns=cast<SelectInst>(nv);ns->setOperand(1,mapped(s->getTrueValue()));ns->setOperand(2,mapped(s->getFalseValue()));}
  if(auto *c=dyn_cast<CallBase>(old))if(auto *nc=dyn_cast<CallBase>(nv))for(unsigned j=0;j<c->arg_size();j++)if(nc->getFunctionType()->getParamType(j)==ptr)nc->setArgOperand(j,mapped(c->getArgOperand(j)));
 }
 SmallVector<Instruction*> work;for(auto &f:m)for(auto &i:instructions(f))work.push_back(&i);
 for(auto *i:work)if(!remove.count(i)) {
  if(auto *s=dyn_cast<StoreInst>(i)) {
   if(s->getValueOperand()->getType()->isPointerTy())continue;
   bool relevant=false;for(auto &k:w.addresses(s->getPointerOperand()))relevant|=admitted.count(k);
   if(relevant){auto *v=mapped(s->getValueOperand());if(!v->getType()->isPointerTy())fail("unproved pointer store during application");IRBuilder<> b(s);auto *store=b.CreateStore(v,s->getPointerOperand());store->setAlignment(s->getAlign());remove.insert(s);}
  }
  if(auto *c=dyn_cast<ICmpInst>(i))if(values.count(c->getOperand(0))||values.count(c->getOperand(1))) {
   IRBuilder<> b(c);auto *n=b.CreateICmp(c->getPredicate(),mapped(c->getOperand(0)),mapped(c->getOperand(1)));c->replaceAllUsesWith(n);remove.insert(c);
  }
  if(auto *c=dyn_cast<CallBase>(i))for(unsigned j=0;j<c->arg_size();j++)if(values.count(c->getArgOperand(j)) && c->getFunctionType()->getParamType(j)==ptr)c->setArgOperand(j,mapped(c->getArgOperand(j)));
 }
 for(auto *i:remove)for(auto *user:i->users())if(auto *ui=dyn_cast<Instruction>(user))if(!remove.count(ui))fail("unlegalized integer pointer consumer in "+ui->getFunction()->getName());
 for(auto *i:remove)i->dropAllReferences();for(auto *i:remove)i->eraseFromParent();
 for(auto &[old,nf]:functions){if(!old->use_empty())fail("unlegalized function-address boundary");old->eraseFromParent();}
 for(auto &row:*plan.getArray("slots")) {
  auto &r=*row.getAsObject();auto name=*r.getString("struct");unsigned idx=*r.getInteger("field");auto *s=StructType::getTypeByName(ctx,name);if(!s)continue;
  SmallVector<Type*> es(s->elements());es[idx]=ptr;s->setBody(es,s->isPacked());
 }
 for(auto &f:m)for(auto &i:instructions(f))if(auto *g=dyn_cast<GetElementPtrInst>(&i)) {
  SmallVector<Value*> indices(g->indices());
  g->setResultElementType(GetElementPtrInst::getIndexedType(g->getSourceElementType(),indices));
 }
 // LLVM 23 upgrades the old nocapture optimization annotation to captures().
 // Apple's production LLVM reader predates that spelling. Intrinsic effects
 // are recovered by that reader; omit only this redundant optimizer promise,
 // retaining argument extension, alignment, ABI and memory-effect attributes.
 for(auto &f:m) {
  for(unsigned j=0;j<f.arg_size();j++)f.removeParamAttr(j,Attribute::Captures);
  for(auto &i:instructions(f))if(auto *c=dyn_cast<CallBase>(&i))for(unsigned j=0;j<c->arg_size();j++)c->removeParamAttr(j,Attribute::Captures);
 }
 if(verifyModule(m,&errs()))fail("invalid promoted module");
 std::error_code ec;raw_fd_ostream o(output,ec);if(ec)fail(ec.message());m.print(o,nullptr);
}
}
int semanticSlotsMain(int argc,char **argv) {
 sys::PrintStackTraceOnErrorSignal(argv[0]);
 if(argc!=4 && argc!=5)fail("usage: --semantic-slots analyze manifest.json plan.json | apply plan.json input.ll output.ll");
 World w;
 if(StringRef(argv[1])=="analyze") {
  auto input=readJSON(argv[2]);auto *paths=input.getAsArray();json::Array lifetimes;
  if(auto *object=input.getAsObject()) {
   paths=object->getArray("modules");
   if(auto *boundaries=object->getArray("lifetimes"))for(auto &b:*boundaries) {
    auto &r=*b.getAsObject();w.releases.insert({r.getString("function")->str(),unsigned(*r.getInteger("argument"))});lifetimes.push_back(b);
   }
  }
  if(!paths)fail("missing native module list");for(auto &path:*paths)w.units.push_back(readUnit(*path.getAsString()));
  w.analyze();validateLayouts(w);
  json::Array slots,blocked,modules,accessors,affected;json::Object signatures;
  for(auto &[name,f]:w.definitions)signatures[name]=signature(*f);
  for(auto &k:w.candidates) {
   auto [name,index]=w.fieldTypes[k];json::Object row{{"struct",name},{"field",index}};
   if(w.rejected[k].empty()) {
    for(auto &u:w.units)if(auto *s=StructType::getTypeByName(u->context,name)) {
     auto *layout=u->module->getDataLayout().getStructLayout(s);
     row["native_layout"]=json::Object{{"size",int64_t(layout->getSizeInBytes())},{"alignment",int64_t(layout->getAlignment().value())},{"slot_offset",int64_t(layout->getElementOffset(index))},{"old_slot_bytes",4},{"new_slot_bytes",8},{"offsets_and_allocation_extents_preserved",true}};break;
    }
    slots.push_back(std::move(row));
   }else {json::Array reasons;for(auto &r:w.rejected[k])reasons.push_back(r);row["reasons"]=std::move(reasons);blocked.push_back(std::move(row));}
  }
  for(auto &u:w.units) {
   modules.push_back(u->path);bool accessor=false,touched=false;
   for(auto &slot:slots) {
    auto &r=*slot.getAsObject();auto name=*r.getString("struct");auto k=name.str()+":"+std::to_string(*r.getInteger("field"));
    if(StructType::getTypeByName(u->context,name))touched=true;
    for(auto &f:*u->module)for(auto &i:instructions(f)) {
     if(auto *g=dyn_cast<GetElementPtrInst>(&i))if(w.addresses(g).count(k))accessor=true;
     if(auto *c=dyn_cast<CallBase>(&i))if(w.addresses(c).count(k))touched=true;
    }
   }
   if(accessor)accessors.push_back(u->path);
   if(touched)affected.push_back(u->path);
  }
  auto count=slots.size();writeJSON(argv[3],json::Object{{"schema",1},{"slots",std::move(slots)},{"blocked",std::move(blocked)},{"signatures",std::move(signatures)},{"modules",std::move(modules)},{"lifetimes",std::move(lifetimes)},{"accessor_modules",std::move(accessors)},{"affected_modules",std::move(affected)},{"layout_policy","preserve all native offsets, extents, alignment and array strides; guest32 input is excluded"}});
  outs()<<"admitted semantic pointer slots: "<<count<<'\n';return 0;
 }
 if(StringRef(argv[1])=="apply" && argc==5) {
  auto plan=readJSON(argv[2]);auto u=readUnit(argv[3]);
  // Accessor summaries are reconstructed from the exact analyzed modules.
  for(auto &p:*plan.getAsObject()->getArray("accessor_modules"))if(*p.getAsString()!=StringRef(argv[3]))w.units.push_back(readUnit(*p.getAsString()));
  w.units.push_back(std::move(u));
  w.analyze();apply(w,*w.units.back(),*plan.getAsObject(),argv[4]);return 0;
 }
 fail("invalid semantic-slot command");
}
