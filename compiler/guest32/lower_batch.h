// Finite declared job batch: private worker contexts, shared work within a worker.
// SPDX-License-Identifier: MIT
#include <atomic>
#include <filesystem>
#include <thread>

static int lowerBatch(const char *Request,const char *Report){
  auto Begin=std::chrono::steady_clock::now();
  auto Buffer=MemoryBuffer::getFile(Request);if(!Buffer)reject("lower batch request");
  auto Parsed=json::parse((*Buffer)->getBuffer());
  if(!Parsed){consumeError(Parsed.takeError());reject("lower batch JSON");}
  auto *Root=Parsed->getAsObject();if(!Root)reject("lower batch object");
  auto Workers=Root->getInteger("workers");
  auto *Rows=Root->getArray("jobs");
  if(!Workers || *Workers<1 || *Workers>64 || !Rows)reject("lower batch worker/job declaration");
  std::vector<std::vector<std::string>> Jobs;
  std::set<std::string> Inputs,Outputs;
  auto Canonical=[](const std::string &Path){return std::filesystem::weakly_canonical(Path).string();};
  Inputs.insert(Canonical(Request));
  Outputs.insert(Canonical(Report));
  for(const auto &Row:*Rows){
    auto *Arguments=Row.getAsArray();
    if(!Arguments || Arguments->size()<3)reject("lower batch argument vector");
    std::vector<std::string> Args;
    for(const auto &Argument:*Arguments){
      auto Text=Argument.getAsString();if(!Text || Text->contains('\0'))reject("lower batch argument string");
      Args.push_back(Text->str());
    }
    if(Args[1].empty() || Args[1][0]=='-')reject("lower batch requires an IR input");
    Inputs.insert(Canonical(Args[1]));
    if(!Outputs.insert(Canonical(Args[2])).second)reject("duplicate lower batch output owner");
    for(size_t I=3;I<Args.size();++I){
      if(Args[I]=="--image" || Args[I]=="--native-ir" || Args[I]=="--abi"){
        if(++I==Args.size())reject("lower batch option value");
        Inputs.insert(Canonical(Args[I]));
      }else if(Args[I]=="--source-ir" || Args[I]=="--diagnose"){
        if(++I==Args.size())reject("lower batch option value");
        if(!Outputs.insert(Canonical(Args[I])).second)reject("duplicate lower batch output owner");
      }
    }
    Jobs.push_back(std::move(Args));
  }
  for(const auto &Path:Outputs)if(Inputs.count(Path))reject("lower batch output overwrites input");
  if(auto EC=sys::fs::remove(Report))reject("cannot invalidate lower batch report: "+EC.message());
  struct Result { int Status=0;double Seconds=0;LowerTimes Times;std::string Log; };
  std::vector<Result> Results(Jobs.size());
  std::atomic<size_t> Next{0};std::atomic<bool> Failed{false};
  std::atomic<unsigned> CatalogLoads{0};
  std::vector<std::thread> Threads;
  for(unsigned Worker=0;Worker<std::min<size_t>(*Workers,Jobs.size());++Worker)
    Threads.emplace_back([&]{
      LLVMContext Context;
      std::map<std::string,Image> Images;
      while(!Failed){
        size_t Index=Next.fetch_add(1);if(Index>=Jobs.size())break;
        auto &Args=Jobs[Index];std::vector<char*> Argv;
        for(auto &Arg:Args)Argv.push_back(Arg.data());
        auto Started=std::chrono::steady_clock::now();
        auto &R=Results[Index];
        raw_string_ostream Log(R.Log);
        R.Status=lowerOne(Argv.size(),Argv.data(),&Context,&Images,&R.Times,&Log);
        R.Seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-Started).count();
        if(R.Status)Failed=true;
      }
      CatalogLoads.fetch_add(Images.size());
    });
  for(auto &Thread:Threads)Thread.join();
  if(Failed)return 1; // No successful batch report, hence no successful receipts.
  json::Array Records;
  for(size_t I=0;I<Jobs.size();++I){auto &R=Results[I];
    Records.push_back(json::Object{{"output",Jobs[I][2]},{"seconds",R.Seconds},{"stdout",R.Log},
      {"parse_seconds",R.Times.parse},{"catalog_seconds",R.Times.catalog},
      {"transform_seconds",R.Times.transform},{"output_seconds",R.Times.output}});
  }
  double Seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-Begin).count();
  std::error_code EC;raw_fd_ostream OS(Report,EC);if(EC)reject("lower batch report");
  OS<<formatv("{0:2}",json::Value(json::Object{{"jobs",std::move(Records)},
     {"catalog_loads",(int64_t)CatalogLoads.load()},{"seconds",Seconds}}))<<'\n';
  OS.close();return OS.has_error()?1:0;
}
