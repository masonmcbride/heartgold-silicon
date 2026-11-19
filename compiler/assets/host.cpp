// Bulk execution of original graphics/message algorithms, with declared ownership.
// SPDX-License-Identifier: MIT
#include "nlohmann/json.hpp"
#include "MessagesEncoder.h"
#include <CommonCrypto/CommonDigest.h>
#include <atomic>
#include <algorithm>
#include <condition_variable>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <mutex>
#include <set>
#include <sstream>
#include <thread>
extern "C" int hg_nitrogfx_entry(int,char**);
using J=nlohmann::json;
namespace fs=std::filesystem;
static std::string read(const fs::path &p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("missing declared asset input: "+p.string());return {std::istreambuf_iterator<char>(f),{}};}
static std::string digest(const std::string &s){unsigned char out[32];if(s.size()>UINT32_MAX)throw std::runtime_error("asset input exceeds declared 32-bit file extent");CC_SHA256(s.data(),(CC_LONG)s.size(),out);std::ostringstream f;for(auto b:out)f<<std::hex<<std::setw(2)<<std::setfill('0')<<(unsigned)b;return f.str();}
static void write(const fs::path &path,const std::string &data){fs::create_directories(path.parent_path());if(fs::exists(path) && read(path)==data)return;std::ofstream f(path,std::ios::binary);f.write(data.data(),data.size());f.flush();if(!f)throw std::runtime_error("cannot publish asset: "+path.string());}
class Encoder:public MessagesEncoder {
 public:
 explicit Encoder(Options &o):MessagesEncoder(o){ReadCharmap();}
 void reset(Options &options){MessagesEncoder fresh(options);MessagesConverter::operator=(fresh);}
};
int assetHost(const J &request,const char *reportPath,const char *executable){try{
 auto started=std::chrono::steady_clock::now();const auto &jobs=request.at("jobs");
 fs::path receiptPath=request.at("receipt").get<std::string>();J previous;
 if(fs::exists(receiptPath))previous=J::parse(read(receiptPath));
 std::map<std::string,std::string> snapshots;
 auto fileHash=[&](const std::string &name)->std::string{auto old=snapshots.find(name);if(old!=snapshots.end())return old->second;auto hash=digest(read(name));snapshots[name]=hash;return hash;};
 J common=J::object();common[fs::canonical(executable).string()]=fileHash(fs::canonical(executable).string());
 for(auto &path:request.value("common",J::array()))common[path.get<std::string>()]=fileHash(path.get<std::string>());
 J records=J::array();std::vector<size_t> pending;
 std::map<std::string,size_t> owners;std::set<fs::path> parents;
 std::map<fs::path,fs::path> parentPaths;std::map<std::string,std::string> outputNames;
 auto key=[&](const std::string &name){fs::path path(name);if(!path.is_absolute())throw std::runtime_error("asset paths must be absolute");path=path.lexically_normal();auto parent=path.parent_path();auto found=parentPaths.find(parent);if(found==parentPaths.end())found=parentPaths.emplace(parent,fs::weakly_canonical(parent)).first;return (found->second/path.filename()).string();};
 auto binary=fs::weakly_canonical(request.at("binary").get<std::string>()).string()+"/";
 for(auto scope:{"game","ntr"})if(request.contains(scope)){auto source=fs::weakly_canonical(request.at(scope).get<std::string>()).string()+"/";if(source.rfind(binary,0)==0 || binary.rfind(source,0)==0)throw std::runtime_error("binary owner overlaps original sources");}
 fs::remove(reportPath);
 for(size_t i=0;i<jobs.size();++i){auto &job=jobs[i];for(auto &out:job.at("outputs")){auto path=key(out.get<std::string>());if(path.rfind(binary,0)!=0 || fs::is_symlink(path))throw std::runtime_error("asset output escapes its binary owner");if(!owners.emplace(path,i).second)throw std::runtime_error("duplicate asset output owner");outputNames[path]=out;parents.insert(fs::path(path).parent_path());}}
 // The configure-time plan is already topologically ordered. Verify that
 // relation once; execution never probes files to discover producer ownership.
 std::vector<std::vector<size_t>> dependents(jobs.size());std::vector<unsigned> counts(jobs.size());
 for(size_t i=0;i<jobs.size();++i){J inputs=J::object();std::set<size_t> producers;
  for(auto &in:jobs[i].at("inputs")){std::string path=in;auto owner=owners.find(key(path));if(owner!=owners.end()){if(owner->second>=i)throw std::runtime_error("asset plan is not topologically ordered");producers.insert(owner->second);}else inputs[path]=fileHash(path);}
  records.push_back(J{{"recipe",jobs[i]},{"inputs",inputs},{"outputs",J::object()}});
  counts[i]=producers.size();for(auto p:producers)dependents[p].push_back(i);
 }
 for(auto &path:parents)fs::create_directories(path);
 double preparationSeconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
 // Remove the sole successful receipt before any producer can change bytes.
 fs::remove(receiptPath);
 std::vector<size_t> ready;for(size_t i=0;i<jobs.size();++i)if(!counts[i])ready.push_back(i);
 size_t next=0,completed=0,executed=0;bool failed=false;std::string error;
 std::mutex scheduling,jsonParser;std::condition_variable condition;
 unsigned workers=request.value("workers",4u);if(!workers || workers>64)throw std::runtime_error("invalid asset worker count");
 std::vector<std::thread> threads;
 for(unsigned worker=0;worker<std::min<size_t>(workers,jobs.size());++worker)threads.emplace_back([&]{
  std::unique_ptr<Encoder> encoder;std::string charmap;
  while(true){size_t i;
   {std::unique_lock<std::mutex> lock(scheduling);condition.wait(lock,[&]{return failed || next<ready.size() || completed==jobs.size();});if(failed || completed==jobs.size())return;i=ready[next++];}
   try{
    const auto &job=jobs[i];auto &record=records[i];
    // Generated-input hashes come from the completed declared producer record.
    for(auto &in:job.at("inputs")){std::string path=in;auto canonical=key(path);auto owner=owners.find(canonical);if(owner!=owners.end())record["inputs"][path]=records[owner->second]["outputs"].at(outputNames.at(canonical));}
    bool reuse=!previous.is_null() && previous.value("common",J())==common && previous.at("jobs").size()==jobs.size();
    if(reuse){const auto &old=previous["jobs"][i];reuse=old["recipe"]==job && old["inputs"]==record["inputs"];
     if(reuse)for(auto &output:job.at("outputs")){std::string path=output;if(!fs::exists(path) || digest(read(path))!=old["outputs"].at(path)){reuse=false;break;}}
    }
    if(!reuse){std::string kind=job.at("kind");
     if(kind=="copy")write(job.at("outputs")[0].get<std::string>(),read(job.at("inputs")[0].get<std::string>()));
     else {std::vector<std::string> args=job.at("args").get<std::vector<std::string>>();std::vector<char*> argv;for(auto &arg:args)argv.push_back(arg.data());
      if(kind=="gfx"){
       bool hasJSON=std::any_of(args.begin(),args.end(),[](const std::string &s){return s.find(".json")!=s.npos;});
       std::unique_lock<std::mutex> lock(jsonParser,std::defer_lock);if(hasJSON)lock.lock();
       if(hg_nitrogfx_entry(argv.size(),argv.data()))throw std::runtime_error("original graphics converter failed");
      }else if(kind=="message"){
       Options options(argv.size(),argv.data());if(!options.failReason.empty() || options.mode!=CONV_ENCODE || options.textFormat!=Options::GamefreakGMM)throw std::runtime_error("invalid original message recipe");
       if(!encoder || charmap!=options.charmap){encoder=std::make_unique<Encoder>(options);charmap=options.charmap;}else encoder->reset(options);
       encoder->ReadInput();encoder->Convert();encoder->WriteOutput();
      }else throw std::runtime_error("undeclared host asset operation: "+kind);
     }
    }
    for(auto &out:job.at("outputs")){std::string path=out;record["outputs"][path]=digest(read(path));}
    {std::lock_guard<std::mutex> lock(scheduling);executed+=!reuse;++completed;for(auto consumer:dependents[i])if(!--counts[consumer])ready.push_back(consumer);}condition.notify_all();
   }catch(const std::exception &e){{std::lock_guard<std::mutex> lock(scheduling);failed=true;error=e.what();}condition.notify_all();return;}
  }
 });
 for(auto &thread:threads)thread.join();if(failed)throw std::runtime_error(error);
 double conversionSeconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count()-preparationSeconds;
 J result={{"common",common},{"jobs",records}};write(receiptPath,result.dump()+"\n");
 double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
 write(reportPath,J{{"jobs",jobs.size()},{"executed",executed},{"preparation_seconds",preparationSeconds},{"conversion_seconds",conversionSeconds},{"seconds",seconds}}.dump(2)+"\n");return 0;
 }catch(const std::exception &e){std::cerr<<"asset host: "<<e.what()<<'\n';return 1;}}
