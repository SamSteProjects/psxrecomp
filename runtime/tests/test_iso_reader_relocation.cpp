#include "iso_reader.h"
#include "disc_relocation_activation.h"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>

static void check(bool ok, const char* message) {
    if (!ok) { std::cerr << message << '\n'; std::exit(1); }
}
static void both(uint8_t* out, uint32_t value) {
    for (unsigned i = 0; i < 4; ++i) { out[i] = uint8_t(value >> (8*i)); out[4+i] = uint8_t(value >> (8*(3-i))); }
}
static void single(uint8_t* out,uint32_t value,bool big=false) {
    for(unsigned i=0;i<4;++i)out[i]=uint8_t(value>>(8*(big?3-i:i)));
}
static PS1::DiscRelocation::Sector path_table(uint32_t root,bool big) {
    PS1::DiscRelocation::Sector out{};out[0]=1;single(out.data()+2,root,big);
    out[big?7:6]=1;return out;
}
static std::vector<uint8_t> record(const std::string& name, uint32_t lba, uint32_t size, bool directory) {
    std::vector<uint8_t> out(33 + name.size() + (name.size()%2 == 0));
    out[0] = uint8_t(out.size()); both(out.data()+2,lba); both(out.data()+10,size);
    out[25] = directory ? 2 : 0; out[32] = uint8_t(name.size());
    std::copy(name.begin(),name.end(),out.begin()+33); return out;
}
static PS1::DiscRelocation::Sector directory(uint32_t root, uint32_t prot_bytes, uint32_t movie) {
    PS1::DiscRelocation::Sector out{}; size_t offset = 0;
    for (auto row : {record(std::string(1,'\0'),root,2048,true), record(std::string(1,'\1'),root,2048,true),
                     record("PROT.DAT;1",30,prot_bytes,false), record("MOVIE.STR;1",movie,2048,false)}) {
        std::copy(row.begin(),row.end(),out.begin()+offset); offset += row.size();
    }
    return out;
}
static PS1::DiscRelocation::Sector descriptor(uint32_t root, uint32_t volume) {
    PS1::DiscRelocation::Sector out{}; out[0] = out[6] = 1; std::memcpy(out.data()+1,"CD001",5);
    both(out.data()+80,volume); out[129] = out[130] = 8;
    both(out.data()+132,10);
    single(out.data()+140,42+(root-40));single(out.data()+144,44+(root-40));
    single(out.data()+148,43+(root-40),true);single(out.data()+152,45+(root-40),true);
    auto row=record(std::string(1,'\0'),root,2048,true); std::copy(row.begin(),row.end(),out.begin()+156); return out;
}

int main(int argc,char** argv) {
    namespace fs=std::filesystem;
    auto root=fs::temp_directory_path()/("psxrecomp_iso_relocation_test_"+
        std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    fs::create_directories(root); auto path=root/"source.bin";
    std::vector<PS1::DiscRelocation::Sector> sectors(60);
    for (unsigned i=0;i<60;++i) sectors[i].fill(uint8_t(i));
    sectors[16]=descriptor(40,58); sectors[40]=directory(40,4096,48);
    sectors[42]=path_table(40,false);sectors[43]=path_table(40,true);
    sectors[44]=path_table(40,false);sectors[45]=path_table(40,true);
    {
        std::ofstream file(path,std::ios::binary);
        for (unsigned lba=0;lba<60;++lba) {
            PS1::CDSector::Raw raw{}; for (unsigned i=1;i<11;++i) raw[i]=0xFF;
            raw[15]=2; raw[17]=1; raw[18]=lba==31 ? 0x89 : 0x08;
            std::memcpy(raw.data()+20,raw.data()+16,4); std::memcpy(raw.data()+24,sectors[lba].data(),2048);
            check(PS1::CDSector::RelocateMode2(raw,lba)&&PS1::CDSector::EncodeForm1(raw),"fixture encoding failed");
            file.write(reinterpret_cast<const char*>(raw.data()),raw.size());
        }
        check(bool(file),"fixture write failed");
    }
    PS1::ISOReader reader; check(reader.Open(path.string()),"source ISO open failed");
    check(reader.GetSectorCount()==60 && reader.GetRootDirectory().lba==40,"original ISO layout changed");
    PS1::DiscRelocation::Plan plan; plan.source_sector_count=60; plan.prot_lba=30; plan.source_prot_sectors=2;
    plan.replacement.resize(8192,'R'); plan.metadata[16]=descriptor(42,60); plan.metadata[42]=directory(42,8192,50);
    plan.metadata[44]=path_table(42,false);plan.metadata[45]=path_table(42,true);
    plan.metadata[46]=path_table(42,false);plan.metadata[47]=path_table(42,true);
    std::string error;
    for (unsigned test=0;test<4;++test) {
        auto bad=plan;
        if (test==0) bad.source_sector_count=61;
        if (test==1) bad.prot_lba=29;
        if (test==2) bad.metadata[16]=descriptor(42,59);
        if (test==3) bad.metadata[16]=descriptor(100,60);
        check(!reader.InstallDiscRelocation(std::move(bad),&error)&&!error.empty(),"invalid ISO plan accepted");
        check(!reader.HasDiscRelocation()&&reader.GetSectorCount()==60&&reader.GetRootDirectory().lba==40,"rejection changed reader");
    }
    check(reader.InstallDiscRelocation(plan,&error)&&error.empty(),"valid ISO plan failed");
    check(reader.GetSectorCount()==62&&reader.GetRootDirectory().lba==42,"reader did not expose grown layout");
    PS1::ISOFileEntry entry;
    check(reader.FindFile("PROT.DAT",entry)&&entry.lba==30&&entry.size==8192,"reopened PROT differs");
    std::vector<uint8_t> payload(8192); check(reader.ReadFile("PROT.DAT",payload.data(),payload.size())==payload.size()&&payload==plan.replacement,"replacement file read differs");
    check(reader.FindFile("MOVIE.STR",entry)&&entry.lba==50,"movie extent did not move");
    check(reader.ReadFile("MOVIE.STR",payload.data(),2048)==2048&&std::all_of(payload.begin(),payload.begin()+2048,[](uint8_t value){return value==48;}),"shifted movie bytes differ");
    PS1::CDSector::Raw raw{}; check(reader.ReadRawSector(33,raw.data())&&raw[18]==0x89,"terminal framing differs");
    check(std::all_of(raw.begin()+24,raw.begin()+2072,[](uint8_t value){return value=='R';}),"raw replacement differs");
    check(reader.ReadRawSector(61,raw.data())&&raw[24]==59,"final raw sector mapping differs");
    auto sentinel=raw; check(!reader.ReadRawSector(62,raw.data())&&raw==sentinel,"out-of-range raw read changed buffer");
    std::array<uint8_t,12> subq{}; bool valid=false;
    check(reader.ReadSubChannelQ(61,subq.data(),&valid)&&valid,"virtual tail subQ failed");
    check(!reader.ReadSubChannelQ(62,subq.data(),&valid),"subQ exceeded virtual disc");
    check(!reader.InstallDiscRelocation(plan,&error)&&reader.HasDiscRelocation(),"duplicate install changed active reader");
    reader.ClearDiscRelocation(); check(!reader.HasDiscRelocation()&&reader.GetSectorCount()==60&&reader.GetRootDirectory().lba==40,"clear did not restore source layout");
    check(reader.GetFileSize("PROT.DAT")==4096,"clear did not restore original PROT");
    check(reader.InstallDiscRelocation(plan),"reinstall after clear failed"); reader.Close();
    check(!reader.HasDiscRelocation()&&reader.GetSectorCount()==0,"close retained relocation");
    check(reader.Open(path.string())&&!reader.HasDiscRelocation()&&reader.GetSectorCount()==60,"reopen retained relocation");
    reader.Close();
    check(reader.Open(path.string()),"preflight source open failed");
    PS1::DiscRelocationPayload qualified;qualified.plan=plan;
    std::vector<uint8_t> original_prot;
    original_prot.insert(original_prot.end(),sectors[30].begin(),sectors[30].end());
    original_prot.insert(original_prot.end(),sectors[31].begin(),sectors[31].end());
    qualified.source_prot_digest=PS1::DiscHash(original_prot.data(),original_prot.size());
    qualified.proposed_prot_digest=PS1::DiscHash(plan.replacement.data(),plan.replacement.size());
    for(const auto& metadata:plan.metadata) {
        const uint32_t old_lba=metadata.first>=34?metadata.first-2:metadata.first;
        qualified.preimages.push_back({old_lba,metadata.first,PS1::DiscHash(sectors[old_lba].data(),2048),
            PS1::DiscHash(metadata.second.data(),2048)});
    }
    auto stale=qualified;stale.source_prot_digest[0]^=1;
    check(!PS1::PrepareDiscRelocationReader(reader,std::move(stale),&error)&&!reader.HasDiscRelocation(),"stale source preflight accepted");
    auto wrong=qualified;wrong.plan.metadata[42]=directory(42,8192,51);
    for(auto& preimage:wrong.preimages)if(preimage.proposed_lba==42)preimage.proposed_digest=PS1::DiscHash(wrong.plan.metadata[42].data(),2048);
    check(!PS1::PrepareDiscRelocationReader(reader,std::move(wrong),&error)&&!reader.HasDiscRelocation()&&reader.GetRootDirectory().lba==40,
          "incorrect movie relocation must fail and restore source layout");
    wrong=qualified;auto hidden=record("HIDDEN.BIN;1",55,2048,false);
    auto& dir=wrong.plan.metadata[42];size_t end=0;while(dir[end])end+=dir[end];std::copy(hidden.begin(),hidden.end(),dir.begin()+end);
    for(auto& preimage:wrong.preimages)if(preimage.proposed_lba==42)preimage.proposed_digest=PS1::DiscHash(dir.data(),2048);
    check(!PS1::PrepareDiscRelocationReader(reader,std::move(wrong),&error)&&!reader.HasDiscRelocation(),"hidden directory member must reject and rollback");
    for(unsigned test=0;test<5;++test) {
        wrong=qualified;
        if(test==0)single(wrong.plan.metadata[44].data()+2,43);
        if(test==1)single(wrong.plan.metadata[47].data()+2,43,true);
        if(test==2)wrong.plan.metadata[45][9]^=1;
        if(test==3)single(wrong.plan.metadata[16].data()+152,49,true);
        if(test==4)wrong.plan.metadata[16][40]^=1;
        for(auto& preimage:wrong.preimages)preimage.proposed_digest=PS1::DiscHash(wrong.plan.metadata.at(preimage.proposed_lba).data(),2048);
        check(!PS1::PrepareDiscRelocationReader(reader,std::move(wrong),&error)&&!reader.HasDiscRelocation()&&reader.GetRootDirectory().lba==40,
              "invalid path-table extent/padding/pointer must reject and rollback");
    }
    check(PS1::PrepareDiscRelocationReader(reader,std::move(qualified),&error)&&reader.HasDiscRelocation(),"qualified relocation preflight failed");
    check(reader.GetFileSize("PROT.DAT")==8192&&reader.FindFile("MOVIE.STR",entry)&&entry.lba==50,"preflight did not expose qualified ISO layout");
    reader.Close(); fs::remove(path); fs::remove(root);
    if(argc==3) {
        check(reader.Open(argv[1]),"Python ISO fixture open failed");
        std::ifstream input(argv[2],std::ios::binary);check(bool(input),"Python payload fixture missing");
        std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(input)),{});
        PS1::DiscRelocationPayload decoded;
        check(PS1::ParseDiscRelocationPayload(bytes,PS1::DiscHash(bytes.data(),bytes.size()),decoded,&error),"Python payload parse failed");
        check(PS1::PrepareDiscRelocationReader(reader,std::move(decoded),&error),"Python/native complete ISO preflight differs");
        check(reader.GetSectorCount()==62&&reader.GetFileSize("PROT.DAT")==8192&&reader.FindFile("MOV/MOVIE.STR",entry)&&entry.lba==50,
              "Python/native reopened ISO mapping differs");
        reader.Close();
    }
    std::cout<<"ISOReader relocation checks passed\n";
}
