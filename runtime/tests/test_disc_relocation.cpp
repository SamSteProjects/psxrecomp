#include "disc_relocation.h"

#include <algorithm>
#include <cstdlib>
#include <iostream>

static void require(bool condition, const char* message) {
    if (!condition) { std::cerr << message << '\n'; std::exit(1); }
}

int main() {
    using Mapper = PS1::DiscRelocation;
    Mapper mapper;
    Mapper::Address address;
    require(!mapper.Resolve(0, address), "inactive mapping must fail");
    Mapper::Plan plan;
    plan.source_sector_count = 60;
    plan.prot_lba = 30;
    plan.source_prot_sectors = 2;
    plan.replacement.resize(4 * 2048, 'R');
    for (uint32_t lba : {16u, 22u, 42u, 44u, 45u}) {
        Mapper::Sector sector{}; sector.fill(static_cast<uint8_t>(lba + 100));
        plan.metadata.emplace(lba, sector);
    }
    std::string error;
    require(mapper.Configure(plan, &error) && error.empty(), "valid mapping must configure");
    require(mapper.SectorCount() == 62 && mapper.GrowthSectors() == 2, "new sector count must include insertion");
    uint32_t reads = 0;
    auto reader = [&](uint32_t lba, uint8_t* out) {
        ++reads;
        require(lba < 60, "source read exceeds original disc");
        std::memset(out, static_cast<uint8_t>(lba), 2048);
        return true;
    };
    for (uint32_t lba = 0; lba < 62; ++lba) {
        Mapper::Sector out{};
        require(mapper.Resolve(lba, address), "all virtual sectors must resolve");
        require(mapper.ReadUserSector(lba, out.data(), reader), "mapped sector read failed");
        uint8_t expected;
        if (plan.metadata.count(lba)) {
            expected = static_cast<uint8_t>(lba + 100);
            require(address.kind == Mapper::Address::Kind::Metadata, "metadata must override source");
            require(address.source_lba == (lba < 34 ? lba : lba - 2), "metadata source framing LBA changed");
        } else if (lba >= 30 && lba < 34) {
            expected = 'R';
            require(address.kind == Mapper::Address::Kind::Replacement && address.replacement_offset == (lba - 30) * 2048,
                    "replacement offset differs from logical reference");
        } else {
            expected = static_cast<uint8_t>(lba < 34 ? lba : lba - 2);
            require(address.kind == Mapper::Address::Kind::Source && address.source_lba == expected,
                    "shifted source mapping differs from logical reference");
        }
        require(std::all_of(out.begin(), out.end(), [&](uint8_t value){ return value == expected; }),
                "whole mapped sector changed");
    }
    require(reads == 53, "replacement/metadata must not read underlying source");
    require(mapper.Resolve(61, address) && address.source_lba == 59, "last sector must map to original tail");
    require(!mapper.Resolve(62, address), "virtual disc end must reject");
    Mapper::Sector sentinel{}; sentinel.fill(0xAA);
    const auto before = sentinel;
    require(!mapper.ReadUserSector(0, sentinel.data(), [](uint32_t, uint8_t* out){out[0] = 0; return false;}),
            "failed source read must fail");
    require(sentinel == before, "failed source read leaked partial bytes");
    require(!mapper.ReadUserSector(0, nullptr, reader), "null output must reject");
    require(!mapper.ReadUserSector(0, sentinel.data(), {}), "missing source reader must reject");
    for (int test = 0; test < 7; ++test) {
        auto bad = plan;
        switch (test) {
        case 0: bad.source_sector_count = 0; break;
        case 1: bad.prot_lba = 59; break;
        case 2: bad.replacement.resize(2048); break;
        case 3: bad.replacement.pop_back(); break;
        case 4: bad.metadata.emplace(30, Mapper::Sector{}); break;
        case 5: bad.metadata.emplace(62, Mapper::Sector{}); break;
        case 6: bad.source_sector_count = UINT32_MAX; break;
        }
        require(!mapper.Configure(std::move(bad), &error) && !error.empty(), "invalid plan must reject");
        require(mapper.Active() && mapper.SectorCount() == 62, "invalid plan changed active mapping");
    }
    auto same = plan; same.replacement.resize(4096); same.metadata.clear();
    require(mapper.Configure(std::move(same)), "same-size replacement must configure");
    require(mapper.SectorCount() == 60 && mapper.GrowthSectors() == 0, "same-size count changed");
    require(mapper.Resolve(59, address) && address.source_lba == 59, "same-size tail mapping changed");
    mapper.Clear(); require(!mapper.Active() && !mapper.Resolve(0, address), "clear must discard mapping");
    std::cout << "disc relocation mapping checks passed\n";
}
