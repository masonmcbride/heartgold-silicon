// Source-owned compiler for the pinned data-only script/event language.
// No precompiled game payloads or executable object admission. SPDX-License-Identifier: MIT
#include "nlohmann/json.hpp"
#include <CommonCrypto/CommonDigest.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <thread>
#include <vector>
using J=nlohmann::json;
namespace fs=std::filesystem;
using I=int64_t;
static std::string read(const fs::path &p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("missing declared input: "+p.string());return {std::istreambuf_iterator<char>(f),{}};}
static std::string trim(std::string s){auto a=s.find_first_not_of(" \t\r\n");if(a==s.npos)return {};return s.substr(a,s.find_last_not_of(" \t\r\n")-a+1);}
static std::string sha(const std::string &s){unsigned char out[CC_SHA256_DIGEST_LENGTH];if(s.size()>UINT32_MAX)throw std::runtime_error("asset input exceeds declared 32-bit file extent");CC_SHA256(s.data(),(CC_LONG)s.size(),out);std::ostringstream f;for(auto b:out)f<<std::hex<<std::setw(2)<<std::setfill('0')<<(unsigned)b;return f.str();}
static std::vector<std::string> lines(std::string text){
 for(size_t p=0;(p=text.find("/*",p))!=text.npos;){auto e=text.find("*/",p+2);if(e==text.npos)throw std::runtime_error("unterminated source comment");for(size_t i=p;i<e+2;++i)if(text[i]!='\n')text[i]=' ';}
 std::istringstream in(text);std::vector<std::string> out;std::string line;
 while(std::getline(in,line)){bool quote=false;char q=0;for(size_t i=0;i<line.size();++i){char c=line[i];if(quote){if(c=='\\')++i;else if(c==q)quote=false;}else if(c=='\'' || c=='"'){quote=true;q=c;}else if(c==';' || (c=='/' && i+1<line.size() && line[i+1]=='/')){line.resize(i);break;}}line=trim(line);if(!line.empty())out.push_back(line);}return out;
}
static std::vector<std::string> split(const std::string &s){std::vector<std::string> r;int depth=0;size_t start=0;for(size_t i=0;i<s.size();++i){if(s[i]=='(')++depth;else if(s[i]==')')--depth;else if(s[i]==',' && !depth){r.push_back(trim(s.substr(start,i-start)));start=i+1;}}if(start<s.size() || !r.empty())r.push_back(trim(s.substr(start)));return r;}
static std::pair<std::string,std::string> instruction(const std::string &s){auto p=s.find_first_of(" \t");return {s.substr(0,p),p==s.npos?"":trim(s.substr(p+1))};}
struct Scope;
struct Expr {
 Scope &S;std::string Text;size_t Pos=0;unsigned Depth;
 Expr(Scope &s,std::string t,unsigned depth=0):S(s),Text(std::move(t)),Depth(depth){if(depth>96)throw std::runtime_error("recursive constant expression");}
 void ws(){while(Pos<Text.size() && isspace((unsigned char)Text[Pos]))++Pos;}
 bool take(const std::string &s){ws();if(Text.compare(Pos,s.size(),s)==0){Pos+=s.size();return true;}return false;}
 I atom();I parse(int min=1);I value(){I v=parse();ws();if(Pos!=Text.size())throw std::runtime_error("unsupported expression: "+Text.substr(Pos)+" in "+Text);return v;}
};
struct Scope {
 const J &Constants;std::map<std::string,I> &Cache;const std::map<std::string,I> &Messages;
 std::map<std::string,I> Numbers,Labels;std::map<std::string,std::string> Defines;I PC=0;
 I symbol(const std::string &name,unsigned depth){
  if(name==".")return PC;
  auto n=Labels.find(name);if(n!=Labels.end())return n->second;
  n=Numbers.find(name);if(n!=Numbers.end())return n->second;
  auto d=Defines.find(name);if(d!=Defines.end())return Expr(*this,d->second,depth+1).value();
  auto m=Messages.find(name);if(m!=Messages.end())return m->second;
  auto found=Cache.find(name);if(found!=Cache.end())return found->second;
  auto c=Constants.find(name);if(c==Constants.end() || !c->at("params").is_null())throw std::runtime_error("unresolved relocations: "+name);
  I value=Expr(*this,c->at("body"),depth+1).value();Cache[name]=value;return value;
 }
 I call(const std::string &name,const std::vector<I> &args,unsigned depth){
  auto f=Constants.find(name);if(f==Constants.end() || f->at("params").is_null() || f->at("params").size()!=args.size())throw std::runtime_error("undeclared constant function: "+name);
  std::map<std::string,I> bindings;for(size_t i=0;i<args.size();++i)bindings[(*f)["params"][i]]=args[i];
  std::string body=(*f)["body"],result;
  for(size_t i=0;i<body.size();){if(isalpha((unsigned char)body[i]) || body[i]=='_'){size_t end=i+1;while(end<body.size() && (isalnum((unsigned char)body[end]) || body[end]=='_'))++end;auto word=body.substr(i,end-i);auto b=bindings.find(word);result+=b==bindings.end()?word:"("+std::to_string(b->second)+")";i=end;}else result+=body[i++];}
  return Expr(*this,result,depth+1).value();
 }
};
I Expr::atom(){
 ws();if(take("+"))return atom();if(take("-"))return -atom();if(take("~"))return ~atom();if(take("!"))return !atom();
 if(take("(")){I v=parse();if(!take(")"))throw std::runtime_error("unclosed expression: "+Text);return v;}
 if(Pos==Text.size())throw std::runtime_error("empty expression: "+Text);
 if(isdigit((unsigned char)Text[Pos])){char *end=nullptr;const char *start=Text.c_str()+Pos;auto v=strtoull(start,&end,0);if(start==end)throw std::runtime_error("invalid number");Pos=end-Text.c_str();while(Pos<Text.size() && (Text[Pos]=='u' || Text[Pos]=='U' || Text[Pos]=='l' || Text[Pos]=='L'))++Pos;return (I)v;}
 if(Text[Pos]=='\''){++Pos;if(Pos==Text.size())throw std::runtime_error("invalid character");I c=Text[Pos++];if(!take("'"))throw std::runtime_error("invalid character literal");return c;}
 size_t begin=Pos;while(Pos<Text.size() && (isalnum((unsigned char)Text[Pos]) || Text[Pos]=='_' || Text[Pos]=='.'))++Pos;
 if(begin==Pos)throw std::runtime_error("invalid expression token: "+Text.substr(Pos));
 auto name=Text.substr(begin,Pos-begin);if(!take("("))return S.symbol(name,Depth);
 std::vector<I> args;if(!take(")")){do{args.push_back(parse());}while(take(","));if(!take(")"))throw std::runtime_error("constant function argument list");}
 return S.call(name,args,Depth);
}
I Expr::parse(int min){
 I left=atom();
 static const std::vector<std::pair<std::string,int>> ops={{"||",1},{"&&",2},{"|",3},{"^",4},{"&",5},{"==",6},{"!=",6},{"<=",7},{">=",7},{"<<",8},{">>",8},{"<",7},{">",7},{"+",9},{"-",9},{"*",10},{"/",10},{"%",10}};
 while(true){ws();std::string op;int rank=0;for(auto &candidate:ops)if(Text.compare(Pos,candidate.first.size(),candidate.first)==0){op=candidate.first;rank=candidate.second;break;}if(rank<min || !rank)break;Pos+=op.size();I right=parse(rank+1);
  if(op=="+")left=(I)((uint64_t)left+right);else if(op=="-")left=(I)((uint64_t)left-right);else if(op=="*")left=(I)((uint64_t)left*right);
  else if(op=="/" || op=="%") {if(!right)throw std::runtime_error("division by zero");left=op=="/"?left/right:left%right;}
  else if(op=="<<" || op==">>"){if(right<0 || right>=64)throw std::runtime_error("invalid shift");left=op=="<<"?(I)((uint64_t)left<<right):left>>right;}
  else if(op=="|")left|=right;else if(op=="&")left&=right;else if(op=="^")left^=right;else if(op=="||")left=left||right;else if(op=="&&")left=left&&right;
  else if(op=="==")left=left==right;else if(op=="!=")left=left!=right;else if(op=="<")left=left<right;else if(op==">")left=left>right;else if(op=="<=")left=left<=right;else if(op==">=")left=left>=right;
 }return left;
}
struct Macro {std::vector<std::string> Params,Defaults,Body;};
struct Program {
 std::map<std::string,Macro> Macros;std::vector<std::string> Init;
 void load(const fs::path &path){auto source=lines(read(path));for(size_t i=0;i<source.size();++i){auto [op,args]=instruction(source[i]);if(op==".macro"){
   auto [name,params]=instruction(args);Macro m;for(auto p:split(params)){auto at=p.find('=');m.Params.push_back(trim(p.substr(0,at)));m.Defaults.push_back(at==p.npos?"":trim(p.substr(at+1)));}
   while(++i<source.size() && source[i]!=".endm")m.Body.push_back(source[i]);if(i==source.size() || !Macros.emplace(name,std::move(m)).second)throw std::runtime_error("invalid macro owner: "+name);
  }else if(op==".set" || op==".equ")Init.push_back(source[i]);else if(op!=".ifndef" && op!=".endif" && op!=".option" && op[0]!='#')throw std::runtime_error("unsupported original macro directive: "+source[i]);}}
};
struct Assembler {
 Scope S;const Program &P;std::vector<unsigned char> Bytes;
 struct Fixup {size_t Offset;unsigned Width;std::string Expression;};std::vector<Fixup> Fixups;
 std::string Section;
 Assembler(const J &c,std::map<std::string,I> &cache,const std::map<std::string,I> &messages,const Program &p):S{c,cache,messages},P(p){execute(p.Init);}
 I eval(std::string text){return Expr(S,std::move(text)).value();}
 void data(unsigned width,const std::string &args){if(Section!=".rodata" && Section!=".data")throw std::runtime_error("unexpected executable code or section");if(args.empty())throw std::runtime_error("missing active data operand");for(auto &arg:split(args)){Fixups.push_back({Bytes.size(),width,arg});Bytes.resize(Bytes.size()+width);S.PC=Bytes.size();}}
 void execute(const std::vector<std::string> &code,unsigned depth=0){
  if(depth>64)throw std::runtime_error("recursive script macro");
  struct Condition {bool Parent,Test;};std::vector<Condition> stack;bool active=true;
  for(auto &line:code){auto [op,args]=instruction(line);
   if(op==".if"){bool test=active && eval(args);stack.push_back({active,test});active=active&&test;continue;}
   if(op==".else"){if(stack.empty())throw std::runtime_error("unmatched .else");active=stack.back().Parent&&!stack.back().Test;continue;}
   if(op==".endif"){if(stack.empty())throw std::runtime_error("unmatched .endif");active=stack.back().Parent;stack.pop_back();continue;}
   if(!active)continue;
   if(op=="#include" || op==".include" || op==".option")continue;
   if(op=="#define"){auto [name,value]=instruction(args);S.Defines[name]=value;continue;}
   if(op==".set" || op==".equ"){auto pair=split(args);if(pair.size()==1){auto [name,value]=instruction(args);pair={name,value};}if(pair.size()!=2)throw std::runtime_error("invalid constant assignment");S.Numbers[pair[0]]=eval(pair[1]);continue;}
   if(op==".rodata" || op==".data" || op==".text" || op==".section"){
    std::string name=op==".section"?split(args).at(0):op;
    if(name==".text"){Section=name;continue;}
    if(name!=".data" && name!=".rodata")throw std::runtime_error("unexpected script data section: "+name);
    if(!Section.empty() && Section!=".text" && Section!=name)throw std::runtime_error("multiple script data sections");Section=name;continue;}
   if(op==".byte" || op==".short" || op==".word" || op==".long"){data(op==".byte"?1:op==".short"?2:4,args);continue;}
   if(op==".balign"){auto p=split(args);I alignment=eval(p.at(0)),fill=p.size()>1?eval(p[1]):0;if(alignment<=0 || (alignment&(alignment-1)) || alignment>65536)throw std::runtime_error("invalid original alignment");Bytes.resize((Bytes.size()+alignment-1)&~(alignment-1),(unsigned char)fill);S.PC=Bytes.size();continue;}
   if(op==".error")throw std::runtime_error("original script constraint: "+args);
   if(op.back()==':' && args.empty()){auto name=op.substr(0,op.size()-1);if(!S.Labels.emplace(name,Bytes.size()).second)throw std::runtime_error("duplicate script label: "+name);continue;}
   auto macro=P.Macros.find(op);if(macro==P.Macros.end())throw std::runtime_error("undeclared script instruction: "+line);
   auto values=split(args);const auto &m=macro->second;
   if((op=="InitScriptEntry_OnResume" || op=="InitScriptEntry_OnTransition") && values.size()==2 && values[1]=="0")values.pop_back();
   if(values.size()>m.Params.size())throw std::runtime_error("extra macro operands: "+line);
   values.resize(m.Params.size());std::map<std::string,std::string> bindings;
   for(size_t i=0;i<values.size();++i){if(values[i].empty())values[i]=m.Defaults[i];bindings[m.Params[i]]=values[i];}
   std::vector<std::string> expanded;for(auto &body:m.Body){std::string out;for(size_t i=0;i<body.size();){if(body[i]=='\\'){size_t end=i+1;while(end<body.size() && (isalnum((unsigned char)body[end]) || body[end]=='_'))++end;auto name=body.substr(i+1,end-i-1);auto binding=bindings.find(name);if(binding==bindings.end())throw std::runtime_error("unbound macro parameter: "+name);out+=binding->second;i=end;}else out+=body[i++];}expanded.push_back(std::move(out));}execute(expanded,depth+1);
  }if(!stack.empty())throw std::runtime_error("unclosed script condition");
 }
 std::vector<unsigned char> finish(){if(Bytes.empty())throw std::runtime_error("empty script payload");for(auto &f:Fixups){S.PC=f.Offset;I value=eval(f.Expression);for(unsigned i=0;i<f.Width;++i)Bytes[f.Offset+i]=(uint64_t)value>>(8*i);}return std::move(Bytes);}
};
static fs::path declared(const std::string &key,const J &request){auto pos=key.find(':');std::string scope=key.substr(0,pos);std::string base=scope=="generated"?"generated":scope;return fs::path(request.at(base).get<std::string>())/key.substr(pos+1);}
static void definitions(const fs::path &path,std::map<std::string,I> &values){for(auto &line:lines(read(path))){auto [op,rest]=instruction(line);if(op!="#define")continue;auto [name,value]=instruction(rest);if(value.empty())continue;char *end=nullptr;I number=strtoll(value.c_str(),&end,0);if(end==value.c_str() || !trim(end).empty())throw std::runtime_error("nonliteral generated constant: "+line);auto [it,inserted]=values.emplace(name,number);if(!inserted && it->second!=number)throw std::runtime_error("conflicting generated constant: "+name);}}
static std::vector<unsigned char> event(const J &data,Scope &s){std::vector<unsigned char> bytes;
 auto emit=[&](unsigned width,I value){for(unsigned i=0;i<width;++i)bytes.push_back((uint64_t)value>>(8*i));};
 const std::vector<std::pair<std::string,std::vector<std::pair<std::string,unsigned>>>> groups={
  {"bgs",{{"scriptId",2},{"type",2},{"x",4},{"z",4},{"y",4},{"dir",4}}},
  {"objects",{{"id",2},{"spriteId",2},{"movement",2},{"type",2},{"eventFlag",2},{"scriptId",2},{"facingDirection",2},{"param0",2},{"param1",2},{"param2",2},{"xRange",2},{"yRange",2},{"x",2},{"z",2},{"y",4}}},
  {"warps",{{"x",2},{"z",2},{"header",2},{"anchor",2},{"y",4}}},
  {"coords",{{"scriptId",2},{"x",2},{"z",2},{"w",2},{"h",2},{"y",2},{"val",2},{"var",2}}}};
 size_t expected=16;
 for(auto &g:groups){auto found=data.find(g.first);size_t count=found==data.end() || found->is_null()?0:found->size();emit(4,count);unsigned extent=0;for(auto &f:g.second)extent+=f.second;expected+=extent*count;
  if(count)for(auto &row:*found)for(auto &f:g.second){auto &v=row.at(f.first);I number=v.is_string()?Expr(s,v.get<std::string>()).value():v.get<I>();emit(f.second,number);}}
 if(bytes.size()!=expected)throw std::runtime_error("event record layout mismatch");return bytes;
}
static std::vector<unsigned char> recordData(const J &data,Scope &scope,const std::string &format){
 std::vector<unsigned char> bytes;
 auto emit=[&](unsigned width,I value){for(unsigned i=0;i<width;++i)bytes.push_back((uint64_t)value>>(8*i));};
 auto number=[&](const J &v)->I{return v.is_string()?Expr(scope,v.get<std::string>()).value():v.is_boolean()?I(v.get<bool>()):v.get<I>();};
 if(format=="mmodel"){
  const auto &rows=data.at("data");emit(4,rows.size());
  for(auto &row:rows)emit(2,number(row.at("unk0")));
  for(auto &row:rows)emit(1,number(row.at("unk1")));
  for(auto &row:rows)emit(1,number(row.at("unk2")));
 }else if(format=="ppark"){
  for(auto &mon:data.at("mons")){std::string area=mon.at("area");I value=scope.symbol("PP_ENCTYPE_"+area,0);bool land=area=="FOREST" || area=="MOUNTAIN" || area=="FIELD";
   emit(1,land?value:0);emit(1,land?0:value-4);
   for(auto &name:{"score","encounter_rate","unk4","unk5"})emit(1,number(mon.at(name)));
  }
  if(bytes.size()!=6*data.at("mons").size())throw std::runtime_error("original Pal Park record extent changed");
 }else if(format=="resdat"){
  if(data.contains("kind") && data.at("kind").is_string()){
   const std::vector<std::string> kinds={"char","pltt","cell","anim","multicell","multianim"};auto found=std::find(kinds.begin(),kinds.end(),data.at("kind").get<std::string>());if(found==kinds.end())throw std::runtime_error("unknown original resource kind");emit(4,found-kinds.begin());
   for(auto &res:data.at("graphics")){
    for(auto &name:{"narc","file","compressed","id"})emit(4,number(res.at(name)));
    for(auto &value:res.at("extra"))emit(4,number(value));
   }
   for(int i=0;i<6;++i)emit(4,-2);
   if(bytes.size()!=4+24*(data.at("graphics").size()+1))throw std::runtime_error("original resource record extent changed");
  }else{
   for(auto &entry:data.at("entries"))for(auto &name:{"graphics","palette","cell","anim","multicell","multianim","transfer","priority"})emit(4,entry.contains(name)?number(entry.at(name)):-1);
   for(int i=0;i<8;++i)emit(4,-2);
   if(bytes.size()!=32*(data.at("entries").size()+1))throw std::runtime_error("original resource list extent changed");
  }
 }else throw std::runtime_error("undeclared data format: "+format);
 return bytes;
}
int assetHost(const J &,const char *,const char *);
int main(int argc,char **argv){try{
 if(argc!=3)throw std::runtime_error("expected request and report");auto started=std::chrono::steady_clock::now();J request=J::parse(read(argv[1]));if(request.value("mode","")=="host")return assetHost(request,argv[2],argv[0]);J catalogue=J::parse(read(request.at("catalogue").get<std::string>()));
 if(catalogue.at("version")!=1)throw std::runtime_error("unknown source constant catalogue");
 const auto &jobs=request.at("jobs");J inputHashes=J::object();std::map<fs::path,std::string> originals;
 auto capture=[&](const fs::path &path)->const std::string &{auto found=originals.find(path);if(found==originals.end()){auto bytes=read(path);inputHashes[path.string()]=sha(bytes);found=originals.emplace(path,std::move(bytes)).first;}return found->second;};
 capture(fs::canonical(argv[0]));capture(request.at("catalogue").get<std::string>());
 for(auto it=catalogue.at("inputs").begin();it!=catalogue.at("inputs").end();++it){auto path=declared(it.key(),request);capture(path);if(inputHashes.at(path.string())!=it.value())throw std::runtime_error("source constant contract changed: "+it.key());}
 std::map<std::string,I> messages;std::set<fs::path> headers,outputs;std::map<fs::path,fs::path> parents;
 auto binary=fs::weakly_canonical(request.at("binary").get<std::string>()).string()+"/";
 for(auto &job:jobs){auto source=job.at("source").get<std::string>();capture(declared("game:"+source,request));const auto &route=catalogue.at("routes").at(source);
  for(auto &h:route.at("headers"))if(h.at("path").get<std::string>().rfind("generated:",0)==0)headers.insert(declared(h.at("path"),request));
  fs::path output=fs::path(job.at("output").get<std::string>()).lexically_normal();auto parent=output.parent_path();auto found=parents.find(parent);if(found==parents.end())found=parents.emplace(parent,fs::weakly_canonical(parent)).first;
  output=found->second/output.filename();if(output.string().rfind(binary,0)!=0 || fs::is_symlink(output) || !outputs.insert(output).second)throw std::runtime_error("invalid asset output ownership");
 }
 for(auto &h:headers)capture(h);
 fs::path receipt=request.at("receipt").get<std::string>();
 J previous;if(fs::exists(receipt))previous=J::parse(read(receipt));
 fs::remove(argv[2]);
 if(!previous.is_null() && previous.at("jobs")==jobs && previous.at("inputs")==inputHashes){
  bool valid=true;for(auto &job:jobs){auto path=job.at("output").get<std::string>();if(!fs::exists(path) || sha(read(path))!=previous.at("outputs").at(path)){valid=false;break;}}
  if(valid){std::ofstream report(argv[2]);report<<J{{"jobs",jobs.size()},{"executed",0},{"seconds",std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count()}}.dump(2)<<'\n';return report?0:1;}
 }
 fs::remove(receipt);
 Program field,battle;field.load(declared("game:asm/macros/script.inc",request));field.load(declared("game:asm/macros/movement.inc",request));battle.load(declared("game:asm/macros/btlcmd.inc",request));
 for(auto &h:headers)definitions(h,messages);
 std::vector<std::vector<unsigned char>> results(jobs.size());std::vector<std::string> errors(jobs.size());std::atomic<size_t> next{0};std::atomic<bool> failed{false};std::vector<std::thread> threads;
 unsigned workers=request.value("workers",4u);if(!workers || workers>64)throw std::runtime_error("invalid asset worker count");
 for(unsigned w=0;w<std::min<size_t>(workers,jobs.size());++w)threads.emplace_back([&]{std::map<std::string,I> fieldCache,battleCache;while(!failed){size_t i=next.fetch_add(1);if(i>=jobs.size())break;try{auto name=jobs[i].at("source").get<std::string>();const auto &text=originals.at(declared("game:"+name,request));auto profile=catalogue.at("routes").at(name).at("profile").get<std::string>();bool isField=profile=="field";const auto &constants=catalogue.at("profiles").at(profile);auto &cache=isField?fieldCache:battleCache;
  auto bind=[&](Scope &scope){for(auto &h:catalogue.at("routes").at(name).at("headers")){auto key=h.at("path").get<std::string>();auto found=catalogue.at("header_scopes").find(key);if(found!=catalogue.at("header_scopes").end())for(auto it=found->begin();it!=found->end();++it)scope.Defines[it.key()]=it.value().get<std::string>();}};
  if(name.size()>=5 && name.substr(name.size()-5)==".json"){Scope scope{constants,cache,messages};bind(scope);auto &route=catalogue.at("routes").at(name);results[i]=route.contains("format")?recordData(J::parse(text),scope,route.at("format").get<std::string>()):event(J::parse(text),scope);}
  else {Assembler assembler(constants,cache,messages,isField?field:battle);bind(assembler.S);assembler.execute(lines(text));results[i]=assembler.finish();}
 }catch(const std::exception &e){errors[i]=e.what();failed=true;}}});
 for(auto &t:threads)t.join();if(failed){for(size_t i=0;i<errors.size();++i)if(!errors[i].empty())std::cerr<<jobs[i].at("source")<<": "<<errors[i]<<'\n';return 1;}
 J outputHashes=J::object();
 // All semantic/relocation/layout checks complete before any output is published.
 for(size_t i=0;i<jobs.size();++i){fs::path output=jobs[i].at("output").get<std::string>();fs::create_directories(output.parent_path());std::string bytes(results[i].begin(),results[i].end());outputHashes[output.string()]=sha(bytes);if(fs::exists(output) && read(output)==bytes)continue;std::ofstream f(output,std::ios::binary);f.write(bytes.data(),bytes.size());f.flush();if(!f)throw std::runtime_error("cannot publish asset output");}
 fs::create_directories(receipt.parent_path());{std::ofstream f(receipt);f<<J{{"jobs",jobs},{"inputs",inputHashes},{"outputs",outputHashes}}.dump()<<'\n';if(!f)throw std::runtime_error("cannot publish data receipt");}
 double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();std::ofstream report(argv[2]);report<<J{{"jobs",jobs.size()},{"executed",jobs.size()},{"seconds",elapsed}}.dump(2)<<'\n';return report?0:1;
 }catch(const std::exception &e){std::cerr<<"asset compiler: "<<e.what()<<'\n';return 1;}}
