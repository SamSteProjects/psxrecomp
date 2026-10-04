#include "cd_sector.h"

#include <cstdlib>
#include <fstream>
#include <iostream>

static void require(bool condition, const char* message) {
    if (!condition) { std::cerr << message << '\n'; std::exit(1); }
}

int main(int argc, char** argv) {
    using namespace PS1::CDSector;
    std::ofstream golden;
    if (argc == 2) { golden.open(argv[1], std::ios::binary); require(bool(golden), "golden output failed"); }
    for (unsigned test = 0; test < 64; ++test) {
        Raw source{};
        for (unsigned i = 0; i < source.size(); ++i) source[i] = static_cast<uint8_t>(i * 37 + test * 19);
        source[0] = source[11] = 0;
        for (unsigned i = 1; i < 11; ++i) source[i] = 0xFF;
        source[15] = 2;
        source[16] = static_cast<uint8_t>(test); source[17] = static_cast<uint8_t>(test ^ 91);
        source[18] = test % 2 ? 0x89 : 0x09; source[19] = 0;
        std::memcpy(source.data() + 20, source.data() + 16, 4);
        require(RelocateMode2(source, test * 123), "source MSF failed");
        Raw encoded = source;
        require(EncodeForm1(encoded), "valid Form 1 encoding failed");
        require(std::memcmp(source.data(), encoded.data(), 2072) == 0, "encoding changed framing or payload");
        Raw repeated = encoded;
        require(EncodeForm1(repeated) && repeated == encoded, "encoding must be idempotent");
        const unsigned target = test == 63 ? 449849 : test * 7001;
        require(RelocateMode2(encoded, target), "target MSF failed");
        require(std::memcmp(encoded.data() + 15, repeated.data() + 15, encoded.size() - 15) == 0,
                "relocation changed data or protection bytes");
        repeated = encoded;
        require(EncodeForm1(repeated) && repeated == encoded, "protection must exclude relocated MSF");
        if (golden.is_open()) golden.write(reinterpret_cast<const char*>(encoded.data()), encoded.size());
        for (int bad_case = 0; bad_case < 4; ++bad_case) {
            Raw bad = source;
            switch (bad_case) {
            case 0: bad[0] = 1; break;
            case 1: bad[15] = 1; break;
            case 2: bad[20] ^= 1; break;
            case 3: bad[18] |= 0x20; bad[22] |= 0x20; break;
            }
            const Raw before = bad;
            require(!EncodeForm1(bad) && bad == before, "invalid Form 1 must reject without mutation");
        }
        Raw out_of_range = source;
        require(!RelocateMode2(out_of_range, 449850) && out_of_range == source, "MSF overflow must reject unchanged");
        Raw form2 = source; form2[18] |= 0x20; form2[22] |= 0x20;
        const auto original_form2 = form2;
        require(RelocateMode2(form2, 100), "Form 2 address relocation failed");
        require(std::memcmp(form2.data() + 15, original_form2.data() + 15, form2.size() - 15) == 0,
                "Form 2 relocation changed XA data");
    }
    if (golden.is_open()) { golden.flush(); require(bool(golden), "golden write failed"); }
    std::cout << "Mode 2 sector codec checks passed\n";
}
