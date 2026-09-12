"""Execute production output-health reporting against failed and ready host paths."""
from pathlib import Path
from test_debug_input_ports import execute

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / 'runtime/src/main.cpp').read_text(encoding='utf-8')
start = source.index('extern "C" int psx_audio_out_stats(')
function = source[start:source.index('\n}', start) + 2]
pump_start = source.index('        rab_stats st;', source.index('static void sdl_audio_pump('))
pump_snapshot = source[pump_start:source.index('        static uint64_t prev_underruns', pump_start)]
fixture = r'''
#include <cassert>
#include <cstdint>
static bool legacy_mode, s_drc_ready, sdl_audio_resumed;
static unsigned sdl_audio_device;
static int g_audio_host_rate = 48000;
static uint64_t g_legacy_underruns = 7;
static unsigned bridge_reads, locks, unlocks;
static bool locked;
static void psx_sdl_audio_lock(unsigned device) { assert(device && !locked); locked=true; ++locks; }
static void psx_sdl_audio_unlock(unsigned device) { assert(device && locked); locked=false; ++unlocks; }
static bool audio_legacy_mode() { return legacy_mode; }
static unsigned psx_sdl_audio_queued_size(unsigned) { return 1764; }
struct rab_stats { double last_fill_ms; uint64_t underrun_events, overflow_drops; double last_correction; };
struct Bridge { struct { double target_ms; } cfg; } s_drc = {{40.0}};
static void rab_get_stats(Bridge *, rab_stats *out) {
    assert(locked); ++bridge_reads; *out = {20.0, 3, 4, 0.001};
}
'''
checks = r'''
static void check_unavailable() {
    double fill=9, target=9, correction=9; uint64_t under=9, drops=9; int legacy=-1, rate=-1;
    unsigned reads=bridge_reads, before_locks=locks;
    assert(!psx_audio_out_stats(&fill,&target,&under,&drops,&correction,&legacy,&rate));
    assert(fill==0 && target==0 && under==0 && drops==0 && correction==0);
    assert(bridge_reads==reads && legacy==int(legacy_mode) && rate==48000);
    assert(locks==before_locks && !locked && locks==unlocks);
}
int main() {
    sdl_audio_device=1; sdl_audio_resumed=true; s_drc_ready=false;
    check_unavailable(); // Open device, but pull callback would emit silence.
    s_drc_ready=true; sdl_audio_resumed=false;
    check_unavailable(); // SDL3 resume failure.
    legacy_mode=true; check_unavailable();
    sdl_audio_resumed=true; sdl_audio_device=0; check_unavailable();
    legacy_mode=false; check_unavailable();
    sdl_audio_device=1;
    double fill,target,correction; uint64_t under,drops; int legacy,rate;
    assert(psx_audio_out_stats(&fill,&target,&under,&drops,&correction,&legacy,&rate));
    assert(fill==20 && target==40 && under==3 && drops==4 && correction==0.001 && legacy==0);
    assert(!locked && locks==1 && unlocks==1);
    check_pump_snapshot();
    assert(!locked && locks==2 && unlocks==2);
    legacy_mode=true; s_drc_ready=false;
    assert(psx_audio_out_stats(&fill,&target,&under,&drops,&correction,&legacy,&rate));
    assert(fill==10 && target==0 && under==7 && drops==0 && legacy==1);
}
'''
execute('audio-output-health', fixture + function + '\nstatic void check_pump_snapshot() {\n' + pump_snapshot + '\n}\n' + checks, cxx=True)
print('Audio output health checks passed')
