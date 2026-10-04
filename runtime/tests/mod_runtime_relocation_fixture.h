#pragma once
#include "disc_relocation_package.h"
#include "cd_sector.h"
#include <algorithm>
#include <array>
#include <cstring>
#include <vector>
#include <string>

// Tiny synthetic source, independent of any retail disc or private fixture.
namespace RuntimeRelocationFixture {
using Sector=std::array<uint8_t,2048>;
inline void word(uint8_t* out,uint32_t value,bool big=false) {
    for(unsigned i=0;i<4;++i)out[i]=uint8_t(value>>(8*(big?3-i:i)));
}
inline void both(uint8_t* out,uint32_t value) { word(out,value);word(out+4,value,true); }
inline std::vector<uint8_t> record(const std::string& name,uint32_t lba,uint32_t size,bool dir) {
    std::vector<uint8_t> out(33+name.size()+(name.size()%2==0));
    out[0]=uint8_t(out.size());both(out.data()+2,lba);both(out.data()+10,size);
    out[25]=dir?2:0;out[32]=uint8_t(name.size());
    std::copy(name.begin(),name.end(),out.begin()+33);return out;
}
inline Sector directory(uint32_t root,uint32_t size,uint32_t movie) {
    Sector out{};size_t at=0;
    for(auto row:{record(std::string(1,'\0'),root,2048,true),record(std::string(1,'\1'),root,2048,true),
                  record("PROT.DAT;1",30,size,false),record("MOVIE.STR;1",movie,2048,false)}) {
        std::copy(row.begin(),row.end(),out.begin()+at);at+=row.size();
    }
    return out;
}
inline Sector table(uint32_t root,bool big) {
    Sector out{};out[0]=1;word(out.data()+2,root,big);out[big?7:6]=1;return out;
}
inline Sector pvd(uint32_t root,uint32_t volume) {
    Sector out{};out[0]=out[6]=1;std::memcpy(out.data()+1,"CD001",5);
    both(out.data()+80,volume);out[129]=out[130]=8;both(out.data()+132,10);
    word(out.data()+140,root+2);word(out.data()+148,root+3,true);
    auto row=record(std::string(1,'\0'),root,2048,true);
    std::copy(row.begin(),row.end(),out.begin()+156);return out;
}
inline void make(std::vector<uint8_t>& source,std::vector<uint8_t>& payload) {
    std::vector<Sector> sectors(60);
    for(unsigned i=0;i<60;++i)sectors[i].fill(uint8_t(i));
    sectors[16]=pvd(40,58);sectors[40]=directory(40,4096,48);
    sectors[42]=table(40,false);sectors[43]=table(40,true);
    source.resize(60*2352);
    for(unsigned i=0;i<60;++i) {
        PS1::CDSector::Raw raw{};for(unsigned j=1;j<11;++j)raw[j]=0xff;
        raw[15]=2;raw[17]=1;raw[18]=i==31?0x89:0x08;
        std::memcpy(raw.data()+20,raw.data()+16,4);std::memcpy(raw.data()+24,sectors[i].data(),2048);
        PS1::CDSector::RelocateMode2(raw,i);PS1::CDSector::EncodeForm1(raw);
        std::copy(raw.begin(),raw.end(),source.begin()+i*2352);
    }
    payload.assign(96+8192+4*2120,0);std::memcpy(payload.data(),"PSXDRLOC",8);
    word(payload.data()+8,1);word(payload.data()+12,60);word(payload.data()+16,30);
    word(payload.data()+20,2);word(payload.data()+24,4);word(payload.data()+28,4);
    std::vector<uint8_t> original;
    for(unsigned i:{30u,31u})original.insert(original.end(),sectors[i].begin(),sectors[i].end());
    const auto old_hash=PS1::DiscHash(original.data(),original.size());
    std::copy(old_hash.begin(),old_hash.end(),payload.begin()+32);
    std::fill(payload.begin()+96,payload.begin()+96+8192,'R');
    const auto new_hash=PS1::DiscHash(payload.data()+96,8192);
    std::copy(new_hash.begin(),new_hash.end(),payload.begin()+64);
    const unsigned lbas[]={16,40,42,43};
    const Sector proposed[]={pvd(42,60),directory(42,8192,50),table(42,false),table(42,true)};
    for(unsigned i=0;i<4;++i) {
        auto* out=payload.data()+96+8192+i*2120;
        word(out,lbas[i]);word(out+4,lbas[i]+(lbas[i]>=32?2:0));
        const auto pre=PS1::DiscHash(sectors[lbas[i]].data(),2048),post=PS1::DiscHash(proposed[i].data(),2048);
        std::copy(pre.begin(),pre.end(),out+8);std::copy(post.begin(),post.end(),out+40);
        std::copy(proposed[i].begin(),proposed[i].end(),out+72);
    }
}
} // namespace RuntimeRelocationFixture
