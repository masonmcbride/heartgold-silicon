// Finite native IR codegen batch using the installed Clang driver's own options.
// SPDX-License-Identifier: MIT
#include "clang/Basic/CodeGenOptions.h"
#include "clang/CodeGen/CodeGenAction.h"
#include "clang/Driver/Compilation.h"
#include "clang/Driver/Driver.h"
#include "clang/Driver/Job.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/CompilerInvocation.h"
#include "clang/Frontend/TextDiagnosticPrinter.h"
#include "llvm/IR/LLVMContext.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/Path.h"
#include "llvm/Support/TargetSelect.h"
#include "llvm/Support/VirtualFileSystem.h"
#include "llvm/TargetParser/Host.h"
#include <atomic>
#include <chrono>
#include <filesystem>
#include <set>
#include <thread>
using namespace llvm;

static int fail(const Twine &Message){errs()<<"guest32-codegen: "<<Message<<'\n';return 1;}

int main(int argc,char **argv){
  if(argc!=3)return fail("expected request and report paths");
  auto Begin=std::chrono::steady_clock::now();
  auto Buffer=MemoryBuffer::getFile(argv[1]);if(!Buffer)return fail("cannot read request");
  auto Parsed=json::parse((*Buffer)->getBuffer());
  if(!Parsed){consumeError(Parsed.takeError());return fail("invalid request JSON");}
  auto *Root=Parsed->getAsObject();if(!Root)return fail("request must be an object");
  auto *Rows=Root->getArray("jobs");auto Workers=Root->getInteger("workers");
  if(!Rows || !Workers || *Workers<1 || *Workers>64)return fail("invalid jobs/worker declaration");
  auto Canonical=[](const std::string &Path){return std::filesystem::weakly_canonical(Path).string();};
  std::set<std::string> Inputs{Canonical(argv[0]),Canonical(argv[1])},Outputs{Canonical(argv[2])};
  std::vector<std::vector<std::string>> Jobs;
  std::string Clang;
  for(const auto &Row:*Rows){
    auto *Arguments=Row.getAsArray();if(!Arguments || Arguments->size()!=6)return fail("expected clang -O2 -c input -o output");
    std::vector<std::string> Command;
    for(const auto &Argument:*Arguments){
      auto Text=Argument.getAsString();
      if(!Text || Text->empty() || Text->contains('\0'))return fail("invalid command argument");
      Command.push_back(Text->str());
    }
    if(Command[1]!="-O2" || Command[2]!="-c" || Command[4]!="-o")return fail("unsupported codegen command");
    if(Clang.empty())Clang=Command[0];
    if(Command[0]!=Clang || Canonical(Clang)!=Canonical(HG_CLANG_EXECUTABLE))return fail("compiler differs from linked Clang installation");
    Inputs.insert(Canonical(Command[3]));
    if(!Outputs.insert(Canonical(Command[5])).second)return fail("duplicate output owner");
    Jobs.push_back(std::move(Command));
  }
  Inputs.insert(Canonical(HG_CLANG_EXECUTABLE));
  for(const auto &Output:Outputs)if(Inputs.count(Output))return fail("output overwrites an input");
  if(auto EC=sys::fs::remove(argv[2]))return fail("cannot invalidate report: "+EC.message());
  json::Array Records;
  if(!Jobs.empty()){
    // Expand the actual driver command once, rather than maintaining a second
    // copy of target, SDK, optimization, relocation and codegen defaults.
    clang::DiagnosticOptions Options;
    auto Diagnostics=clang::CompilerInstance::createDiagnostics(*vfs::getRealFileSystem(),Options);
    clang::driver::Driver Driver(Clang,sys::getDefaultTargetTriple(),*Diagnostics);
    SmallVector<const char*> Args;for(auto &Arg:Jobs.front())Args.push_back(Arg.c_str());
    std::unique_ptr<clang::driver::Compilation> Plan(Driver.BuildCompilation(Args));
    if(!Plan || Plan->getJobs().size()!=1 || Diagnostics->hasErrorOccurred())return fail("expected one native compiler action");
    auto CC1=Plan->getJobs().begin()->getArguments();
    if(CC1.empty() || StringRef(CC1[0])!="-cc1")return fail("expected Clang frontend options");
    auto Base=std::make_shared<clang::CompilerInvocation>();
    if(!clang::CompilerInvocation::CreateFromArgs(*Base,ArrayRef(CC1).drop_front(),*Diagnostics,Clang.c_str()))return fail("cannot parse native compiler invocation");
    if(Base->getFrontendOpts().ProgramAction!=clang::frontend::EmitObj ||
       Base->getFrontendOpts().Inputs.size()!=1 ||
       Base->getFrontendOpts().Inputs.front().getKind().getLanguage()!=clang::Language::LLVM_IR)
      return fail("expected IR-to-object action");
    // CLI cc1 exits after one module. Batch workers release each module's
    // compiler allocations normally; this changes memory lifetime, not passes.
    Base->getFrontendOpts().DisableFree=false;
    InitializeNativeTarget();InitializeNativeTargetAsmPrinter();InitializeNativeTargetAsmParser();
    struct Result {bool Success=false;double Seconds=0;std::string Diagnostics;};
    std::vector<Result> Results(Jobs.size());
    std::atomic<size_t> Next{0};std::atomic<bool> Failed{false};
    std::vector<std::thread> Threads;
    for(unsigned W=0;W<std::min<size_t>(*Workers,Jobs.size());++W)Threads.emplace_back([&]{
      LLVMContext Context;
      while(!Failed){
        size_t I=Next.fetch_add(1);if(I>=Jobs.size())break;
        auto Started=std::chrono::steady_clock::now();auto &Result=Results[I];
        auto Invocation=std::make_shared<clang::CompilerInvocation>(*Base);
        Invocation->getFrontendOpts().Inputs.clear();
        Invocation->getFrontendOpts().Inputs.emplace_back(Jobs[I][3],clang::InputKind(clang::Language::LLVM_IR));
        Invocation->getFrontendOpts().OutputFile=Jobs[I][5];
        Invocation->getCodeGenOpts().MainFileName=sys::path::filename(Jobs[I][3]).str();
        raw_string_ostream Log(Result.Diagnostics);
        clang::TextDiagnosticPrinter Printer(Log,Invocation->getDiagnosticOpts());
        clang::CompilerInstance Compiler(Invocation);Compiler.createDiagnostics(&Printer,false);
        Compiler.setVerboseOutputStream(Log);
        clang::EmitObjAction Action(&Context);
        Result.Success=Compiler.ExecuteAction(Action);
        Result.Seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-Started).count();
        if(!Result.Success)Failed=true;
      }
    });
    for(auto &Thread:Threads)Thread.join();
    if(Failed){
      for(size_t I=0;I<Jobs.size();++I)if(!Results[I].Success && !Results[I].Diagnostics.empty())
        errs()<<Jobs[I][3]<<":\n"<<Results[I].Diagnostics;
      return fail("native compilation batch failed");
    }
    for(size_t I=0;I<Jobs.size();++I)Records.push_back(json::Object{
      {"output",Jobs[I][5]},{"seconds",Results[I].Seconds},{"stderr",Results[I].Diagnostics}});
  }
  double Seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-Begin).count();
  std::error_code EC;raw_fd_ostream OS(argv[2],EC);if(EC)return fail("cannot write report");
  OS<<formatv("{0:2}",json::Value(json::Object{{"jobs",std::move(Records)},
      {"driver_expansions",Jobs.empty()?0:1},{"seconds",Seconds}}))<<'\n';
  OS.close();return OS.has_error()?1:0;
}
