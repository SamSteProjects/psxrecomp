#pragma once

#include "disc_relocation.h"
#include "psx_sha256.h"

namespace PS1 {

using DiscDigest = std::array<uint8_t, 32>;
inline DiscDigest DiscHash(const uint8_t* data, size_t size) {
    DiscDigest result{}; psx_sha256_compute(data, size, result.data()); return result;
}

struct DiscRelocationPayload {
    struct Preimage { uint32_t source_lba, proposed_lba; DiscDigest digest, proposed_digest; };
    DiscRelocation::Plan plan;
    DiscDigest source_prot_digest{}, proposed_prot_digest{};
    std::vector<Preimage> preimages;
};

inline bool ParseDiscRelocationPayload(const std::vector<uint8_t>& bytes,
        const DiscDigest& expected, DiscRelocationPayload& output, std::string* error = nullptr) {
    auto reject = [&](const char* message) { if (error) *error = message; return false; };
    if (bytes.size() < 96 || bytes.size() > 1024ull*1024*1024 || DiscHash(bytes.data(),bytes.size()) != expected)
        return reject("disc relocation payload hash or budget changed");
    const auto word = [&](size_t offset) {
        return uint32_t(bytes[offset]) | uint32_t(bytes[offset+1]) << 8 |
               uint32_t(bytes[offset+2]) << 16 | uint32_t(bytes[offset+3]) << 24;
    };
    const uint32_t count=word(12), start=word(16), old=word(20), proposed=word(24), number=word(28);
    if (std::memcmp(bytes.data(),"PSXDRLOC",8) || word(8)!=1 || !count || !old || proposed<old ||
        uint64_t(start)+old>count || uint64_t(count)+proposed-old>449850 || number>4096 ||
        96ull+uint64_t(proposed)*2048+uint64_t(number)*2120 != bytes.size())
        return reject("disc relocation payload header or extent is invalid");
    DiscRelocationPayload candidate;
    candidate.plan.source_sector_count=count; candidate.plan.prot_lba=start; candidate.plan.source_prot_sectors=old;
    std::memcpy(candidate.source_prot_digest.data(),bytes.data()+32,32);
    std::memcpy(candidate.proposed_prot_digest.data(),bytes.data()+64,32);
    const size_t replacement_end=96+size_t(proposed)*2048;
    if (DiscHash(bytes.data()+96,replacement_end-96)!=candidate.proposed_prot_digest)
        return reject("disc relocation proposed PROT hash changed");
    candidate.plan.replacement.assign(bytes.begin()+96,bytes.begin()+replacement_end);
    size_t position=replacement_end;
    uint32_t previous=0; bool have_previous=false;
    for (uint32_t index=0;index<number;++index) {
        const uint32_t original=word(position), target=word(position+4);
        DiscDigest before{},after{};
        std::memcpy(before.data(),bytes.data()+position+8,32);
        std::memcpy(after.data(),bytes.data()+position+40,32);
        if ((have_previous && original<=previous) || original>=count ||
            (original>=start && uint64_t(original)<uint64_t(start)+old) ||
            uint64_t(target)!=uint64_t(original)+(uint64_t(original)>=uint64_t(start)+old ? proposed-old : 0) ||
            uint64_t(target)>=uint64_t(count)+proposed-old ||
            (target>=start && uint64_t(target)<uint64_t(start)+proposed) ||
            DiscHash(bytes.data()+position+72,2048)!=after)
            return reject("disc relocation metadata ownership or hash changed");
        DiscRelocation::Sector sector{}; std::memcpy(sector.data(),bytes.data()+position+72,2048);
        candidate.plan.metadata.emplace(target,sector);
        candidate.preimages.push_back({original,target,before,after});
        previous=original;have_previous=true;position+=2120;
    }
    output=std::move(candidate);
    if (error) error->clear();
    return true;
}

// Call on an unmodified reader bound to the committed source-disc identity.
// Complete ISO qualification and feature conflict checks remain activation work.
inline bool VerifyDiscRelocationSource(const DiscRelocationPayload& payload, uint32_t source_count,
        const DiscRelocation::SourceReader& reader, std::string* error = nullptr) {
    auto reject = [&](const char* message) { if (error) *error = message; return false; };
    if (!reader || !source_count || source_count!=payload.plan.source_sector_count ||
        !payload.plan.source_prot_sectors || uint64_t(payload.plan.prot_lba)+payload.plan.source_prot_sectors>source_count ||
        payload.plan.replacement.empty() || payload.plan.replacement.size()%2048 ||
        payload.plan.replacement.size()/2048<payload.plan.source_prot_sectors ||
        payload.preimages.size()!=payload.plan.metadata.size() ||
        DiscHash(payload.plan.replacement.data(),payload.plan.replacement.size())!=payload.proposed_prot_digest)
        return reject("disc relocation source count or reader changed");
    psx_sha256_ctx digest; psx_sha256_init(&digest);
    DiscRelocation::Sector sector{};
    for (uint32_t index=0;index<payload.plan.source_prot_sectors;++index) {
        if (!reader(payload.plan.prot_lba+index,sector.data())) return reject("disc relocation PROT source read failed");
        psx_sha256_update(&digest,sector.data(),sector.size());
    }
    DiscDigest actual{};psx_sha256_final(&digest,actual.data());
    if (actual!=payload.source_prot_digest) return reject("disc relocation source PROT hash changed");
    for (const auto& row:payload.preimages) {
        const auto candidate=payload.plan.metadata.find(row.proposed_lba);
        if (row.source_lba>=source_count || candidate==payload.plan.metadata.end() ||
            DiscHash(candidate->second.data(),candidate->second.size())!=row.proposed_digest ||
            !reader(row.source_lba,sector.data()) || DiscHash(sector.data(),sector.size())!=row.digest)
            return reject("disc relocation metadata preimage changed");
    }
    if (error) error->clear();
    return true;
}

} // namespace PS1
