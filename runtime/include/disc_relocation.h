#pragma once

#include "cd_sector.h"

#include <array>
#include <cstdint>
#include <cstring>
#include <functional>
#include <map>
#include <string>
#include <utility>
#include <vector>

namespace PS1 {

// Qualified package activation owns hashes/ISO validation. This mapper owns
// bounds, sector mapping and payload reads; it never opens or rewrites a disc.
class DiscRelocation {
public:
    static constexpr uint32_t kSectorBytes = 2048;
    using Sector = std::array<uint8_t, kSectorBytes>;
    using SourceReader = std::function<bool(uint32_t, uint8_t*)>;
    // Callback must fill one 2352-byte raw sector, not a 2048-byte user sector.
    using RawSourceReader = std::function<bool(uint32_t, uint8_t*)>;
    struct Plan {
        uint32_t source_sector_count = 0;
        uint32_t prot_lba = 0;
        uint32_t source_prot_sectors = 0;
        std::vector<uint8_t> replacement;
        // Keys are proposed logical LBAs, after ISO metadata relocation.
        std::map<uint32_t, Sector> metadata;
    };
    struct Address {
        enum class Kind { Source, Replacement, Metadata };
        Kind kind = Kind::Source;
        uint32_t source_lba = 0;
        uint64_t replacement_offset = 0;
    };

    bool Configure(Plan proposed, std::string* error = nullptr) {
        auto reject = [&](const char* message) {
            if (error) *error = message;
            return false;
        };
        if (!proposed.source_sector_count || !proposed.source_prot_sectors ||
            proposed.replacement.empty() || proposed.replacement.size() % kSectorBytes)
            return reject("disc relocation requires whole-sector source and replacement extents");
        const uint64_t old_end = uint64_t(proposed.prot_lba) + proposed.source_prot_sectors;
        const uint64_t new_sectors = proposed.replacement.size() / kSectorBytes;
        if (old_end > proposed.source_sector_count || new_sectors < proposed.source_prot_sectors)
            return reject("disc relocation PROT ownership exceeds source or shrinks");
        const uint64_t growth = new_sectors - proposed.source_prot_sectors;
        const uint64_t total = uint64_t(proposed.source_sector_count) + growth;
        // CD addresses use two-digit BCD minutes, including the 150-frame bias.
        if (total > 100u * 60u * 75u - 150u)
            return reject("disc relocation exceeds CD MSF addressing range");
        const uint64_t new_end = uint64_t(proposed.prot_lba) + new_sectors;
        for (const auto& item : proposed.metadata) {
            if (item.first >= total || (item.first >= proposed.prot_lba && item.first < new_end))
                return reject("disc relocation metadata is outside disc or overlaps PROT");
        }
        // Validate completely before replacing an already active plan.
        plan_ = std::move(proposed);
        growth_ = static_cast<uint32_t>(growth);
        sector_count_ = static_cast<uint32_t>(total);
        active_ = true;
        if (error) error->clear();
        return true;
    }

    bool ReadRawSector(uint32_t lba, uint8_t* output, const RawSourceReader& reader) const {
        Address address;
        if (!output || !reader || !Resolve(lba, address)) return false;
        CDSector::Raw candidate{};
        uint32_t source_lba = address.source_lba;
        if (address.kind == Address::Kind::Replacement) {
            const uint64_t final_lba = uint64_t(plan_.prot_lba) + plan_.replacement.size() / kSectorBytes - 1;
            source_lba = lba == final_lba ? plan_.prot_lba + plan_.source_prot_sectors - 1 : plan_.prot_lba;
        }
        if (!reader(source_lba, candidate.data())) return false;
        if (address.kind != Address::Kind::Source) {
            const uint8_t* payload = address.kind == Address::Kind::Replacement
                ? plan_.replacement.data() + address.replacement_offset : plan_.metadata.at(lba).data();
            std::memcpy(candidate.data() + 24, payload, kSectorBytes);
            if (!CDSector::EncodeForm1(candidate)) return false;
        }
        if (source_lba != lba && !CDSector::RelocateMode2(candidate, lba)) return false;
        std::memcpy(output, candidate.data(), candidate.size());
        return true;
    }

    void Clear() {
        plan_ = Plan{};
        growth_ = sector_count_ = 0;
        active_ = false;
    }
    bool Active() const { return active_; }
    uint32_t SectorCount() const { return sector_count_; }
    uint32_t GrowthSectors() const { return growth_; }

    bool Resolve(uint32_t lba, Address& result) const {
        if (!active_ || lba >= sector_count_) return false;
        Address proposed;
        const uint64_t new_end = uint64_t(plan_.prot_lba) + plan_.source_prot_sectors + growth_;
        proposed.source_lba = lba - (lba >= new_end ? growth_ : 0);
        if (plan_.metadata.find(lba) != plan_.metadata.end()) {
            proposed.kind = Address::Kind::Metadata;
        } else if (lba >= plan_.prot_lba &&
                   uint64_t(lba) - plan_.prot_lba < plan_.replacement.size() / kSectorBytes) {
            proposed.kind = Address::Kind::Replacement;
            proposed.replacement_offset = (uint64_t(lba) - plan_.prot_lba) * kSectorBytes;
        } else {
            proposed.kind = Address::Kind::Source;
        }
        result = proposed;
        return true;
    }

    bool ReadUserSector(uint32_t lba, uint8_t* output, const SourceReader& reader) const {
        Address address;
        if (!output || !Resolve(lba, address)) return false;
        Sector candidate{};
        switch (address.kind) {
        case Address::Kind::Source:
            if (!reader || !reader(address.source_lba, candidate.data())) return false;
            break;
        case Address::Kind::Replacement:
            std::memcpy(candidate.data(), plan_.replacement.data() + address.replacement_offset, kSectorBytes);
            break;
        case Address::Kind::Metadata:
            candidate = plan_.metadata.at(lba);
            break;
        }
        // Failed source reads never expose partially filled caller buffers.
        std::memcpy(output, candidate.data(), kSectorBytes);
        return true;
    }

private:
    Plan plan_;
    uint32_t growth_ = 0;
    uint32_t sector_count_ = 0;
    bool active_ = false;
};

} // namespace PS1
