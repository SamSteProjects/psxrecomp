#include "disc_relocation_package.h"

#include <cstdlib>
#include <fstream>
#include <iostream>
#include <iterator>

static void check(bool value,const char* message) { if (!value) { std::cerr<<message<<'\n';std::exit(1); } }
static void word(std::vector<uint8_t>& bytes,size_t offset,uint32_t value) {
    for (unsigned i=0;i<4;++i) bytes[offset+i]=uint8_t(value>>(8*i));
}

int main(int argc,char** argv) {
    using namespace PS1;
    std::vector<uint8_t> bytes(96+8192+2*2120);
    std::memcpy(bytes.data(),"PSXDRLOC",8);
    word(bytes,8,1);word(bytes,12,60);word(bytes,16,30);word(bytes,20,2);word(bytes,24,4);word(bytes,28,2);
    std::vector<uint8_t> original(4096);std::memset(original.data(),30,2048);std::memset(original.data()+2048,31,2048);
    auto source_hash=DiscHash(original.data(),original.size());std::memcpy(bytes.data()+32,source_hash.data(),32);
    std::memset(bytes.data()+96,'R',8192);auto proposed=DiscHash(bytes.data()+96,8192);std::memcpy(bytes.data()+64,proposed.data(),32);
    size_t position=96+8192;
    for (uint32_t old:{16u,40u}) {
        word(bytes,position,old);word(bytes,position+4,old+(old>=32 ? 2 : 0));
        DiscRelocation::Sector source{};source.fill(uint8_t(old));auto before=DiscHash(source.data(),source.size());
        std::memcpy(bytes.data()+position+8,before.data(),32);std::memset(bytes.data()+position+72,int(old+100),2048);
        auto after=DiscHash(bytes.data()+position+72,2048);std::memcpy(bytes.data()+position+40,after.data(),32);position+=2120;
    }
    DiscRelocationPayload payload;std::string error;
    check(ParseDiscRelocationPayload(bytes,DiscHash(bytes.data(),bytes.size()),payload,&error)&&error.empty(),"native payload parse failed");
    check(payload.plan.source_sector_count==60&&payload.plan.prot_lba==30&&payload.plan.replacement.size()==8192&&payload.plan.metadata.size()==2,"native decoded ownership differs");
    auto reader=[](uint32_t lba,uint8_t* output) { if (lba>=60) return false;std::memset(output,int(lba),2048);return true; };
    check(VerifyDiscRelocationSource(payload,60,reader,&error)&&error.empty(),"native source verification failed");
    check(!VerifyDiscRelocationSource(payload,61,reader,&error),"changed source count accepted");
    for (uint32_t changed:{30u,40u}) {
        check(!VerifyDiscRelocationSource(payload,60,[&](uint32_t lba,uint8_t* out) { reader(lba,out);if(lba==changed)out[0]^=1;return true; },&error),"changed preimage accepted");
    }
    check(!VerifyDiscRelocationSource(payload,60,[](uint32_t,uint8_t*){return false;},&error),"failed source read accepted");
    auto mutated=payload;mutated.plan.replacement[0]^=1;
    check(!VerifyDiscRelocationSource(mutated,60,reader,&error),"changed parsed PROT candidate accepted");
    mutated=payload;mutated.plan.metadata.begin()->second[0]^=1;
    check(!VerifyDiscRelocationSource(mutated,60,reader,&error),"changed parsed metadata candidate accepted");
    for (unsigned test=0;test<12;++test) {
        auto bad=bytes;
        switch(test) {
        case 0:word(bad,8,2);break;
        case 1:word(bad,12,0);break;
        case 2:word(bad,16,60);break;
        case 3:word(bad,24,1);break;
        case 4:word(bad,28,4097);break;
        case 5:bad[96]^=1;break;
        case 6:bad[96+8192+72]^=1;break;
        case 7:word(bad,96+8192+4,30);break;
        case 8:word(bad,96+8192+2120,16);break;
        case 9:bad.pop_back();break;
        case 10:bad.push_back(0);break;
        case 11:bad[0]^=1;break;
        }
        check(!ParseDiscRelocationPayload(bad,DiscHash(bad.data(),bad.size()),payload,&error)&&!error.empty(),"malformed payload accepted");
        check(payload.plan.replacement.size()==8192&&payload.plan.metadata.size()==2,"failed parse modified prior output");
    }
    DiscDigest stale{};check(!ParseDiscRelocationPayload(bytes,stale,payload),"stale manifest hash accepted");
    if (argc>=2) {
        std::ifstream input(argv[1],std::ios::binary);check(bool(input),"Python payload file missing");
        std::vector<uint8_t> python((std::istreambuf_iterator<char>(input)),{});
        check(ParseDiscRelocationPayload(python,DiscHash(python.data(),python.size()),payload,&error),"Python payload rejected by native parser");
        check(payload.plan.source_sector_count==60&&payload.plan.replacement==std::vector<uint8_t>(8192,'R')&&payload.plan.metadata.size()==5,"Python/native decoded values differ");
        const std::array<uint32_t,5> old_lbas{16,22,40,42,43}, new_lbas{16,22,42,44,45};
        for (size_t index=0;index<5;++index)
            check(payload.preimages[index].source_lba==old_lbas[index]&&payload.preimages[index].proposed_lba==new_lbas[index],"Python/native metadata mapping differs");
        if (argc==3) {
            std::ifstream source(argv[2],std::ios::binary);check(bool(source),"Python source sectors missing");
            std::vector<uint8_t> sectors((std::istreambuf_iterator<char>(source)),{});
            check(sectors.size()==60*2048,"Python source sector count differs");
            check(VerifyDiscRelocationSource(payload,60,[&](uint32_t lba,uint8_t* out) {
                if (lba>=60) return false;
                std::memcpy(out,sectors.data()+size_t(lba)*2048,2048);
                return true;
            },&error),"Python/native source verification differs");
        }
    }
    std::cout<<"disc relocation payload checks passed\n";
}
