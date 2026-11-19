// Source-owned Mach-O symbol inventory. SPDX-License-Identifier: MIT
#include "llvm/BinaryFormat/MachO.h"
#include "llvm/Object/Archive.h"
#include "llvm/Object/ArchiveWriter.h"
#include "llvm/Object/MachO.h"
#include "llvm/Support/Error.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/FormatVariadic.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/Path.h"
#include <set>
using namespace llvm;
using namespace llvm::object;
namespace {
ExitOnError Checked("guest32 object inventory: ");
struct Table {
  std::set<std::string> defined, undefined;
  json::Array hardware;
};
void scan(Binary &B,Table &T,const std::set<std::string> &Hardware) {
  if(auto *A=dyn_cast<Archive>(&B)) {
    Error E=Error::success();
    for(const auto &Child:A->children(E)) {
      auto Member=Checked(Child.getAsBinary());
      scan(*Member,T,Hardware);
    }
    Checked(std::move(E));return;
  }
  auto *M=dyn_cast<MachOObjectFile>(&B);
  if(!M)Checked(createStringError(inconvertibleErrorCode(),"expected original native Mach-O object/archive"));
  for(const auto &S:M->symbols()) {
    auto Raw=S.getRawDataRefImpl();
    uint8_t Type;uint16_t Desc;uint64_t Value;
    if(M->is64Bit()) {auto N=M->getSymbol64TableEntry(Raw);Type=N.n_type;Desc=N.n_desc;Value=N.n_value;}
    else {auto N=M->getSymbolTableEntry(Raw);Type=N.n_type;Desc=N.n_desc;Value=N.n_value;}
    if((Type&MachO::N_STAB) || !(Type&MachO::N_EXT))continue;
    std::string Name=Checked(S.getName()).str();
    unsigned Kind=Type&MachO::N_TYPE;
    if(Kind==MachO::N_UNDF && !Value) {T.undefined.insert(Name);continue;}
    if(Kind==MachO::N_SECT && Hardware.count(Name)) {
      auto Section=Checked(S.getSection());
      StringRef SectionName=Checked(Section->getName());
      StringRef Segment=M->getSectionFinalSegmentName(Section->getRawDataRefImpl());
      StringRef Letter=Segment=="__TEXT" && SectionName=="__text"?"T":
                       Segment=="__DATA" && SectionName=="__data"?"D":"S";
      // Keep occurrences, including multiple definitions within one archive.
      T.hardware.push_back(json::Object{{"name",Name},{"kind",Letter}});
    }
    if((Type&MachO::N_PEXT) || (Desc&(MachO::N_WEAK_REF|MachO::N_WEAK_DEF)))continue;
    T.defined.insert(Name);
  }
}
json::Array names(const std::set<std::string> &Names) {
  json::Array Result;for(const auto &Name:Names)Result.push_back(Name);return Result;
}
}
int objectSymbolsMain(const char *Input,const char *Output) {
  auto Buffer=Checked(errorOrToExpected(MemoryBuffer::getFile(Input)));
  auto Request=Checked(json::parse(Buffer->getBuffer()));
  auto *O=Request.getAsObject();
  if(!O || !O->getArray("paths") || !O->getArray("hardware_symbols"))
    Checked(createStringError(inconvertibleErrorCode(),"object inventory request schema"));
  std::set<std::string> Hardware;
  auto *Archives=O->getObject("archives");
  if(O->get("archives") && !Archives)
    Checked(createStringError(inconvertibleErrorCode(),"archives must map object paths to archive paths"));
  std::set<std::string> Inputs,Outputs;
  for(const auto &V:*O->getArray("paths")) {
    auto Path=V.getAsString();
    if(!Path || !Inputs.insert(Path->str()).second)
      Checked(createStringError(inconvertibleErrorCode(),"invalid or duplicate inventory artifact"));
  }
  if(Archives)for(const auto &Entry:*Archives) {
    auto Output=Entry.second.getAsString();
    if(!Inputs.count(Entry.first.str()) || !Output || Inputs.count(Output->str()) ||
       !Outputs.insert(Output->str()).second)
      Checked(createStringError(inconvertibleErrorCode(),"invalid or duplicate archive ownership"));
  }
  for(const auto &V:*O->getArray("hardware_symbols")) {
    auto S=V.getAsString();if(!S)Checked(createStringError(inconvertibleErrorCode(),"hardware identity must be a string"));
    Hardware.insert(S->str());
  }
  json::Object Tables;
  for(const auto &V:*O->getArray("paths")) {
    auto Path=V.getAsString();if(!Path)Checked(createStringError(inconvertibleErrorCode(),"artifact path must be a string"));
    auto Member=Checked(NewArchiveMember::getFile(*Path,true));
    auto B=Checked(createBinary(Member.Buf->getMemBufferRef()));
    Table T;scan(*B,T,Hardware);
    if(Archives)if(auto Output=Archives->getString(*Path)) {
      if(!isa<MachOObjectFile>(B.get()))
        Checked(createStringError(inconvertibleErrorCode(),"provider archive input must be a Mach-O object"));
      Member.MemberName=sys::path::filename(*Path);
      auto Kind=Member.detectKindFromObject();
      Checked(writeArchive(*Output,ArrayRef<NewArchiveMember>(Member),
          SymtabWritingMode::NormalSymtab,Kind,true,false));
    }
    json::Object Record{{"defined",names(T.defined)},
        {"undefined",names(T.undefined)},{"hardware",std::move(T.hardware)}};
    if(Archives)if(auto Output=Archives->getString(*Path))Record["archive"]=*Output;
    if(!Tables.try_emplace(*Path,std::move(Record)).second)
      Checked(createStringError(inconvertibleErrorCode(),"duplicate inventory artifact"));
  }
  std::error_code EC;raw_fd_ostream OS(Output,EC);
  if(EC)Checked(errorCodeToError(EC));
  OS<<formatv("{0}",json::Value(std::move(Tables)))<<'\n';return 0;
}
