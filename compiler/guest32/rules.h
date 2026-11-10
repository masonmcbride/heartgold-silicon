// Closed, versioned contracts for the existing lowerer. SPDX-License-Identifier: MIT
// This registry selects no arbitrary code and never supplies unknown ABI facts.
#include "rules_catalog.h"
#include "llvm/IR/Metadata.h"
#include <algorithm>

class Rules {
  struct Rule {
    std::string id, operation;
    unsigned version, phase;
    std::set<std::string> requires, provides, depends, incompatible;
  };
  std::map<std::string,Rule> rules;
  std::map<std::string,std::string> operations;
  std::vector<std::string> order;
  std::map<std::string,uint64_t> applications;
  // These are implementation capabilities, not assertions accepted from JSON.
  const std::map<std::string,std::set<std::string>> requirements{
    {"layout",{}}, {"allocation",{"guest32-layout"}},
    {"interior",{"guest32-layout"}}, {"memory",{"guest32-layout"}},
    {"pointer-word",{"guest32-layout"}}, {"aggregate",{"guest32-layout"}},
    {"integer",{"guest32-layout"}}, {"callback",{"guest32-layout","image-catalog"}},
    {"bulk-memory",{"guest32-layout"}}, {"static-data",{"guest32-layout"}},
    {"boundary",{"guest32-layout","typed-boundary"}},
  };
  static std::string string(const json::Object &o,StringRef k) {
    auto v=o.getString(k);if(!v || v->empty())reject("rule missing string "+k);return v->str();
  }
  static std::set<std::string> strings(const json::Object &o,StringRef k) {
    auto *a=o.getArray(k);if(!a)reject("rule missing array "+k);
    std::set<std::string> r;for(auto &v:*a){auto s=v.getAsString();if(!s || s->empty() || !r.insert(s->str()).second)reject("invalid rule array "+k);}return r;
  }
public:
  explicit Rules(StringRef text) {
    auto j=json::parse(text);if(!j)reject("rule JSON: "+toString(j.takeError()));
    auto *root=j->getAsObject();if(!root || root->getInteger("schema")!=1)reject("rule schema version");
    for(auto &k:*root)if(k.first!="schema" && k.first!="rules")reject("unknown rule catalog field "+k.first);
    auto *list=root->getArray("rules");if(!list)reject("missing rules");
    for(auto &v:*list){
      auto *o=v.getAsObject();if(!o)reject("rule must be object");
      for(auto &k:*o)if(k.first!="id" && k.first!="version" && k.first!="operation" && k.first!="phase" && k.first!="requires" && k.first!="provides" && k.first!="depends" && k.first!="incompatible" && k.first!="invariants" && k.first!="evidence" && k.first!="tests" && k.first!="status")reject("unknown rule field "+k.first);
      Rule r; r.id=string(*o,"id");r.operation=string(*o,"operation");
      auto version=o->getInteger("version"),phase=o->getInteger("phase");
      if(version!=1 || !phase || *phase<0 || *phase>1)reject("unsupported rule version/phase");
      r.version=*version;r.phase=*phase;
      if(string(*o,"status")!="admitted")reject("rule is not explicitly admitted: "+r.id);
      r.requires=strings(*o,"requires");r.provides=strings(*o,"provides");r.depends=strings(*o,"depends");r.incompatible=strings(*o,"incompatible");
      for(StringRef field:{"invariants","evidence","tests"})if(strings(*o,field).empty())reject("rule lacks evidence/invariants/tests: "+r.id);
      if(!requirements.count(r.operation) || r.requires!=requirements.at(r.operation))reject("unsupported rule preconditions: "+r.id);
      if(r.phase!=(r.operation=="layout"?0u:1u))reject("rule phase mismatch: "+r.id);
      std::set<std::string> provides=r.operation=="layout"?std::set<std::string>{"guest32-layout"}:std::set<std::string>{};
      if(r.provides!=provides)reject("rule cannot assert representation facts: "+r.id);
      if(!rules.emplace(r.id,r).second)reject("duplicate rule identity: "+r.id);
      if(!operations.emplace(r.operation,r.id).second)reject("ambiguous competing rules for "+r.operation);
    }
    // DFS is finite over the immutable rule graph; no fixpoint or retry loop.
    std::map<std::string,unsigned> state;
    std::function<void(const std::string&)> visit=[&](const std::string &id){
      if(!rules.count(id))reject("unknown rule dependency: "+id);
      if(state[id]==1)reject("rule dependency cycle: "+id);
      if(state[id]==2)return;state[id]=1;
      const auto &r=rules.at(id);
      for(const auto &bad:r.incompatible)if(rules.count(bad))reject("incompatible rules: "+id+" / "+bad);
      for(const auto &dep:r.depends){visit(dep);if(rules.at(dep).phase>r.phase)reject("backward rule phase: "+id);}
      state[id]=2;order.push_back(id);
    };
    for(auto &p:rules)visit(p.first);
    for(const auto &p:requirements)if(!operations.count(p.first))reject("missing implemented rule family: "+p.first);
    for(const auto &p:rules)if(p.second.operation!="layout"){
      if(!p.second.depends.count(operations.at("layout")))reject("rule requires explicit layout dependency: "+p.first);
      // Operation rules consume facts established by phase zero or verified
      // external contracts. They do not produce facts for another instruction.
      if(p.second.depends.size()!=1)reject("unsupported operation dependency: "+p.first);
    }
  }
  void apply(StringRef operation,Module &out,const std::set<std::string> &facts) {
    const auto &r=rules.at(operations.at(operation.str()));
    for(const auto &f:r.requires)if(!facts.count(f))reject("rule precondition unknown: "+r.id+" requires "+f);
    ++applications[r.id];
  }
  void layout(const DataLayout &dl,Module &out,std::set<std::string> &facts) {
    if(dl.getPointerSizeInBits()!=32 || dl.isBigEndian() || dl.getIndexSizeInBits(0)!=32)reject("rule layout needs little-endian 32-bit pointers and indices");
    apply("layout",out,facts);facts.insert("guest32-layout");
  }
  void instruction(const Instruction &i,Module &out,const std::set<std::string> &facts) {
    StringRef op;
    if(isa<AllocaInst>(i))op="allocation";
    else if(isa<GetElementPtrInst>(i))op="interior";
    else if(isa<LoadInst>(i) || isa<StoreInst>(i))op="memory";
    else if(i.getOpcode()==Instruction::PtrToInt || i.getOpcode()==Instruction::IntToPtr)op="pointer-word";
    else if(isa<InsertValueInst>(i) || isa<ExtractValueInst>(i))op="aggregate";
    else if(isa<BinaryOperator>(i) && i.getType()->isIntegerTy())op="integer";
    else if(isa<MemIntrinsic>(i))op="bulk-memory";
    else if(auto *c=dyn_cast<CallBase>(&i);c && !c->getCalledFunction())op="callback";
    if(op=="callback" && !facts.count("image-catalog"))
      reject("indirect call requires original image catalog (rule precondition unknown: g32.callback)");
    if(!op.empty())apply(op,out,facts);
  }
  void evidence(Module &out) {
    auto *m=out.getOrInsertNamedMetadata("guest32.rules");auto &c=out.getContext();
    for(const auto &id:order)if(applications.count(id))m->addOperand(MDNode::get(c,{MDString::get(c,id),MDString::get(c,std::to_string(rules.at(id).version)),MDString::get(c,std::to_string(applications.at(id)))}));
  }
};
