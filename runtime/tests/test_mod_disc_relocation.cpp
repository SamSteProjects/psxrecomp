#include "mod_packages.h"
#include "disc_relocation_package.h"
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>

using namespace PSXRecompV4;
namespace fs=std::filesystem;
static void check(bool ok,const char* message) { if(!ok){std::cerr<<message<<'\n';std::exit(1);} }
static void write(const fs::path& file,const std::string& text) {fs::create_directories(file.parent_path());std::ofstream out(file,std::ios::binary);out<<text;check(bool(out),"fixture write failed");}
static std::string hash(const std::string& bytes) {auto digest=PS1::DiscHash(reinterpret_cast<const uint8_t*>(bytes.data()),bytes.size());std::string result;for(auto value:digest){result+="0123456789abcdef"[value>>4];result+="0123456789abcdef"[value&15];}return result;}
static std::string payload() {
    std::string bytes(96+8192,'\0');std::memcpy(bytes.data(),"PSXDRLOC",8);
    auto word=[&](size_t at,uint32_t value){for(unsigned i=0;i<4;++i)bytes[at+i]=char(value>>(8*i));};
    word(8,1);word(12,60);word(16,30);word(20,2);word(24,4);
    std::memset(bytes.data()+96,'R',8192);auto digest=PS1::DiscHash(reinterpret_cast<const uint8_t*>(bytes.data()+96),8192);
    std::memcpy(bytes.data()+64,digest.data(),32);return bytes;
}
static std::string manifest(const std::string& id,const std::string& sha,bool enabled=false) {
    return "format_version=7\nid=\""+id+"\"\nversion=\"1.0.0\"\nname=\"Relocation\"\nresolver=\"declarative\"\n"
        "[[target]]\ngame_id=\"SLUS-TEST\"\ndisc_sha256=\""+std::string(64,'a')+"\"\n"
        "[[feature]]\nid=\"scene\"\nname=\"Scene\"\ndefault_enabled="+(enabled ? "true" : "false")+"\n"
        "[[disc_relocation]]\nfeature=\"scene\"\nfile=\"assets/relocation.bin\"\nsha256=\""+sha+"\"\n";
}
int main() {
    auto root=fs::temp_directory_path()/("psx_mod_relocation_"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    auto folder=root/"installed"/"reloc.one"/"1.0.0";auto bytes=payload();auto text=manifest("reloc.one",hash(bytes));
    write(folder/"assets/relocation.bin",bytes);write(folder/"manifest.toml",text);
    ModPackage parsed;std::string error;
    check(ModPackageManager::read_manifest(folder/"manifest.toml",parsed,&error)&&parsed.disc_relocations.size()==1,"valid feature declaration rejected");
    for(int test=0;test<6;++test) {
        auto bad=text;
        if(test==0)bad.replace(bad.find("format_version=7"),16,"format_version=6");
        if(test==1) {
            const std::string field="file=\"assets/relocation.bin\"";
            bad.replace(bad.find(field),field.size(),"file=\"../escape.bin\"");
        }
        if(test==2)bad+="unexpected=1\n";
        if(test==3)bad.replace(bad.find("feature=\"scene\""),15,"feature=\"missing\"");
        if(test==4)bad+=bad.substr(bad.find("[[disc_relocation]]"));
        if(test==5)bad.replace(bad.find("disc_sha256=\""),13,"unused_sha=\"");
        write(folder/"bad.toml",bad);
        check(!ModPackageManager::read_manifest(folder/"bad.toml",parsed,&error),"malformed relocation declaration accepted");
    }
    ModPackageManager manager(root);check(manager.scan(&error),"catalog scan failed");
    auto disabled=manager.resolve("SLUS-TEST",{},std::string(64,'a'));
    check(disabled.ok&&disabled.disc_relocations.empty(),"disabled relocation entered plan");
    check(manager.set_feature_enabled("reloc.one","scene",true,&error),"enable failed");
    auto active=manager.resolve("SLUS-TEST",{},std::string(64,'a'));
    check(active.ok&&active.disc_relocations.size()==1&&active.fingerprint!=disabled.fingerprint,"enabled relocation missing or fingerprint unchanged");
    write(folder/"assets/relocation.bin",bytes+"X");
    auto stale=manager.resolve("SLUS-TEST",{},std::string(64,'a'));
    check(!stale.ok&&stale.disc_relocations.empty(),"changed installed payload accepted");
    write(folder/"assets/relocation.bin",bytes);
    auto other=root/"installed"/"reloc.two"/"1.0.0";write(other/"assets/relocation.bin",bytes);write(other/"manifest.toml",manifest("reloc.two",hash(bytes),true));
    check(manager.scan(&error),"two-provider scan failed");
    auto conflict=manager.resolve("SLUS-TEST",{},std::string(64,'a'));
    check(!conflict.ok&&conflict.disc_relocations.empty(),"two relocation providers accepted");
    check(manager.set_feature_enabled("reloc.two","scene",false,&error),"disable competing provider failed");
    const std::string overlay="ABC";write(folder/"assets/overlay.bin",overlay);
    write(folder/"manifest.toml",text+"[[overlay]]\nfeature=\"scene\"\ntarget=\"disc_user\"\noffset=0\nfile=\"assets/overlay.bin\"\nsha256=\""+hash(overlay)+"\"\n");
    check(manager.scan(&error),"overlay conflict scan failed");
    conflict=manager.resolve("SLUS-TEST",{},std::string(64,'a'));
    check(!conflict.ok&&conflict.disc_relocations.empty()&&conflict.overlays.empty(),"relocation/overlay conflict accepted");
    fs::remove_all(root);std::cout<<"mod disc relocation checks passed\n";
}
