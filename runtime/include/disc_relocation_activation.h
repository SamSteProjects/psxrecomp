#pragma once

#include "disc_relocation_package.h"
#include "iso_reader.h"
#include <algorithm>
#include <set>

namespace PS1 {

// Qualify a parsed payload on an unmodified reader bound to the committed source
// identity. Caller publishes the reader only after success. Raw framing and PVD
// bounds are additionally checked by ISOReader installation.
inline bool PrepareDiscRelocationReader(ISOReader& reader, DiscRelocationPayload payload,
                                       std::string* error = nullptr) {
    auto reject=[&](const char* message) { if(error)*error=message;return false; };
    if (!reader.IsOpen() || reader.HasDiscRelocation()) return reject("relocation preflight requires an unmodified open reader");
    if (!VerifyDiscRelocationSource(payload,reader.GetSectorCount(),
            [&](uint32_t lba,uint8_t* out) { return reader.ReadSector(lba,out); },error)) return false;
    struct Entry { std::string path;ISOFileEntry source; };
    std::vector<Entry> entries;
    std::vector<std::string> directories{std::string{}};
    std::map<std::string,size_t> child_counts;
    std::set<std::string> paths;
    const uint64_t old_end=uint64_t(payload.plan.prot_lba)+payload.plan.source_prot_sectors;
    const uint32_t growth=uint32_t(payload.plan.replacement.size()/2048-payload.plan.source_prot_sectors);
    const uint32_t proposed_prot_bytes=uint32_t(payload.plan.replacement.size());
    const uint32_t prot_lba=payload.plan.prot_lba;
    const auto expected_digest=payload.proposed_prot_digest;
    const auto original_root=reader.GetRootDirectory();
    if(!original_root.size || original_root.size>4*1024*1024 ||
        uint64_t(original_root.lba)+(uint64_t(original_root.size)+2047)/2048>reader.GetSectorCount())
        return reject("relocation preflight source root exceeds bounds or budget");
    for(size_t index=0;index<directories.size();++index) {
        if(directories.size()>4096) return reject("relocation preflight directory budget exceeded");
        const auto children=reader.ListFiles(directories[index]);
        size_t count=0;
        for(const auto& child:children) {
            if(child.name=="." || child.name=="..") continue;
            if(child.name.empty() || child.name.find_first_of("/\\")!=std::string::npos)
                return reject("relocation preflight directory name is invalid");
            const std::string path=directories[index].empty()?child.name:directories[index]+"/"+child.name;
            if(path.size()>4096 || !paths.insert(path).second || entries.size()>=100000)
                return reject("relocation preflight entry identity or budget is invalid");
            const uint64_t end=uint64_t(child.lba)+(uint64_t(child.size)+2047)/2048;
            const bool is_prot=path=="PROT.DAT";
            if(end>reader.GetSectorCount() ||
                (is_prot && (child.is_directory || child.lba!=prot_lba || child.size!=uint64_t(payload.plan.source_prot_sectors)*2048)) ||
                (!is_prot && child.lba<old_end && end>prot_lba))
                return reject("relocation preflight source ISO allocation overlaps PROT or disc end");
            if(child.is_directory) {
                if(!child.size || child.size>4*1024*1024) return reject("relocation preflight directory extent exceeds budget");
                directories.push_back(path);
            }
            entries.push_back({path,child});++count;
        }
        child_counts[directories[index]]=count;
    }
    if(!paths.count("PROT.DAT")) return reject("relocation preflight source PROT identity is absent");
    DiscRelocation::Sector source_pvd{};
    if(!reader.ReadSector(16,source_pvd.data())) return reject("relocation preflight source PVD read failed");
    const auto number=[](const uint8_t* data,bool big) {
        uint32_t value=0;
        for(unsigned i=0;i<4;++i)value|=uint32_t(data[i])<<(8*(big?3-i:i));
        return value;
    };
    const auto table_size=number(source_pvd.data()+132,false);
    if(!table_size || table_size>1024*1024 || table_size!=number(source_pvd.data()+136,true))
        return reject("relocation preflight path-table size copies or budget are invalid");
    struct Table { unsigned descriptor_offset;bool big;uint32_t lba;std::vector<uint8_t> expected; };
    std::vector<Table> tables;
    auto expected_pvd=source_pvd;
    const auto write_number=[](uint8_t* data,uint32_t value,bool big) {
        for(unsigned i=0;i<4;++i)data[i]=uint8_t(value>>(8*(big?3-i:i)));
    };
    write_number(expected_pvd.data()+80,number(source_pvd.data()+80,false)+growth,false);
    write_number(expected_pvd.data()+84,number(source_pvd.data()+84,true)+growth,true);
    write_number(expected_pvd.data()+158,original_root.lba+(original_root.lba>=old_end?growth:0),false);
    write_number(expected_pvd.data()+162,original_root.lba+(original_root.lba>=old_end?growth:0),true);
    const auto read_range=[&](uint32_t lba,uint32_t size,std::vector<uint8_t>& bytes) {
        bytes.resize(size);DiscRelocation::Sector sector{};
        for(uint32_t position=0;position<size;position+=2048) {
            if(!reader.ReadSector(lba+position/2048,sector.data()))return false;
            const size_t take=std::min<size_t>(2048,size-position);
            std::memcpy(bytes.data()+position,sector.data(),take);
        }
        return true;
    };
    std::set<uint32_t> source_directory_lbas{original_root.lba};
    for(const auto& entry:entries)if(entry.source.is_directory)source_directory_lbas.insert(entry.source.lba);
    for(unsigned slot=0;slot<4;++slot) {
        const unsigned offset=140+slot*4;const bool big=slot>=2;
        const uint32_t lba=number(source_pvd.data()+offset,big);
        if(!lba) {
            if(slot==0 || slot==2)return reject("relocation preflight mandatory path table is absent");
            continue;
        }
        const uint64_t end=uint64_t(lba)+(uint64_t(table_size)+2047)/2048;
        if(end>reader.GetSectorCount() || (lba<old_end && end>prot_lba))
            return reject("relocation preflight path table overlaps PROT or disc end");
        Table table{offset,big,lba+(lba>=old_end?growth:0),{}};
        write_number(expected_pvd.data()+offset,table.lba,big);
        if(!read_range(lba,table_size,table.expected))return reject("relocation preflight source path-table read failed");
        size_t position=0;
        while(position<table.expected.size()) {
            if(position+8>table.expected.size())return reject("relocation preflight path-table header is truncated");
            const unsigned length=table.expected[position];
            const size_t next=position+8+length+(length&1);
            if(!length || next>table.expected.size() || table.expected[position+1])
                return reject("relocation preflight path-table record is invalid or extended");
            const uint32_t original=number(table.expected.data()+position+2,big);
            if(!source_directory_lbas.count(original))return reject("relocation preflight path table names an unowned directory extent");
            const uint32_t proposed=original+(original>=old_end?growth:0);
            for(unsigned i=0;i<4;++i)table.expected[position+2+i]=uint8_t(proposed>>(8*(big?3-i:i)));
            position=next;
        }
        tables.push_back(std::move(table));
    }
    if(!reader.InstallDiscRelocation(std::move(payload.plan),error)) return false;
    auto rollback=[&](const char* message) { reader.ClearDiscRelocation();return reject(message); };
    const auto root=reader.GetRootDirectory();
    if(root.size!=original_root.size || root.lba!=original_root.lba+(original_root.lba>=old_end?growth:0))
        return rollback("relocation preflight root mapping differs from source");
    DiscRelocation::Sector proposed_pvd{};
    if(!reader.ReadSector(16,proposed_pvd.data()) || proposed_pvd!=expected_pvd ||
        number(proposed_pvd.data()+132,false)!=table_size || number(proposed_pvd.data()+136,true)!=table_size)
        return rollback("relocation preflight changed path-table size");
    for(unsigned slot=0;slot<4;++slot) {
        const unsigned offset=140+slot*4;const bool big=slot>=2;
        const uint32_t original=number(source_pvd.data()+offset,big);
        const uint32_t expected=original?original+(original>=old_end?growth:0):0;
        if(number(proposed_pvd.data()+offset,big)!=expected)
            return rollback("relocation preflight path-table descriptor mapping differs");
    }
    for(const auto& table:tables) {
        std::vector<uint8_t> reopened;
        if(!read_range(table.lba,table_size,reopened) || reopened!=table.expected)
            return rollback("relocation preflight path-table contents differ from source transformation");
    }
    for(const auto& entry:entries) {
        ISOFileEntry reopened;
        const uint32_t expected_lba=entry.source.lba+(entry.source.lba>=old_end?growth:0);
        const uint32_t expected_size=entry.path=="PROT.DAT"?proposed_prot_bytes:entry.source.size;
        if(!reader.FindFile(entry.path,reopened) || reopened.lba!=expected_lba || reopened.size!=expected_size ||
            reopened.is_directory!=entry.source.is_directory)
            return rollback("relocation preflight reopened ISO entry differs from source mapping");
    }
    for(const auto& directory:child_counts) {
        size_t count=0;
        for(const auto& child:reader.ListFiles(directory.first))
            if(child.name!="." && child.name!="..") ++count;
        if(count!=directory.second) return rollback("relocation preflight changed directory membership");
    }
    psx_sha256_ctx digest;psx_sha256_init(&digest);DiscRelocation::Sector sector{};
    for(uint32_t index=0;index<proposed_prot_bytes/2048;++index) {
        if(!reader.ReadSector(prot_lba+index,sector.data())) return rollback("relocation preflight PROT readback failed");
        psx_sha256_update(&digest,sector.data(),sector.size());
    }
    DiscDigest actual{};psx_sha256_final(&digest,actual.data());
    if(actual!=expected_digest) return rollback("relocation preflight PROT readback hash differs");
    if(error)error->clear();
    return true;
}

} // namespace PS1
