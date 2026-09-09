/* Execute the production loader, DMA/SIO readers and variable MDEC parser.
 * Other device callbacks are deterministic in-memory test doubles. */
#include "boot_state.h"
#include "overlay_api.h"
#include "mdec.h"
#include "savestate.h"
#include "gpu.h"
#include "pst_wire.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#define RAM_N (2u * 1024u * 1024u)
#define VRAM_N (1024u * 512u * 2u)
static uint8_t ram[RAM_N], spad[1024], spuram[512u * 1024u];
static uint16_t vram[1024u * 512u];
static uint32_t bitmap[16], timer_marker, phase, gpu_marker, spu_marker, cd_marker;
uint32_t i_stat, i_mask, g_psx_icache_tv[1024];
uint64_t psx_cycle_count, s_frame_count;
uint64_t psx_next_service_cycle;
uint32_t g_psx_cyc_batch, g_psx_cyc_batch_limit, *g_psx_cyc_local_acc;
int psx_in_device_service, g_event_step_conservative, g_ls_replay_active;
void psx_devices_service_to_now(void) {}
void psx_advance_cycles_slow(uint32_t cycles) { psx_cycle_count += cycles; }
static unsigned side_effects, allocations;
static size_t last_realloc_size;
static int fail_at = -1, live_boot_allocations;
static int commit_failure;
static uint64_t cd_restore_clock;
static uint32_t resumed_pc;
static unsigned load_fail_notices;
static int live_dispatchable = 1;
int psx_hle_scheduler_enabled(void) { return 1; }
int psx_is_dispatchable(uint32_t pc) { return live_dispatchable && pc && pc!=PSX_EXC_SENTINEL_PC; }
int psx_irq_resume_context_snapshot_site(void) { return 0; }
uint32_t psx_irq_resume_context_snapshot_pc(void) { return 0; }
uint32_t psx_compiled_irq_resume_pc(void) { return 0; }
uint32_t psx_last_irq_check_pc(void) { return 0; }
uint32_t psx_netplay_rb_sticky_bb_pc(void) { return 0; }
int psx_irq_resume_context_snapshot_safe_at(uint32_t pc) { (void)pc;return 1; }
void psx_frontend_on_savestate_notify(int load,int slot,int ok) { (void)slot;if(load&&!ok)load_fail_notices++; }
void psx_frontend_on_savestate_loaded(void) { side_effects++; }
void psx_cycles_resync_after_restore(CPUState* cpu) { (void)cpu;side_effects++; }
void interrupts_resync_after_restore(void) { side_effects++; }
void cdrom_accelerate_after_savestate(void) { side_effects++; }
/* Production unwinds here; the test records its target and returns for checks. */
void psx_scheduler_resume_at(uint32_t pc) { resumed_pc=pc; }
void gpu_get_display_info(GpuDisplayInfo* out) { memset(out,0,sizeof *out); }
uint32_t gpu_display_pixel_argb(const GpuDisplayInfo* di,uint32_t x,uint32_t y) { (void)di;(void)x;(void)y;return 0; }

void* bs_test_malloc(size_t n) {
    if ((int)allocations++ == fail_at) return NULL;
    void* p = malloc(n);
    if (p) live_boot_allocations++;
    return p;
}
void bs_test_free(void* p) {
    if (p) live_boot_allocations--;
    free(p);
}
void* bs_test_realloc(void* p, size_t n) {
    if ((int)allocations++ == fail_at) return NULL;
    last_realloc_size=n;
    return realloc(p, n);
}
uint8_t* memory_get_ram_ptr(void) { return ram; }
uint8_t* memory_get_scratchpad_ptr(void) { return spad; }
uint8_t* spu_get_ram_ptr(void) { return spuram; }
uint32_t spu_get_ram_bytes(void) { return sizeof spuram; }
const uint16_t* gpu_get_vram(void) { return vram; }
void gr_vram_transfer_in(int x, int y, int w, int h, const uint16_t* p) {
    (void)x;(void)y;(void)w;(void)h; memcpy(vram,p,sizeof vram); side_effects++;
}
void gr_vram_transfer_out(int x, int y, int w, int h, uint16_t* p) {
    (void)x;(void)y;(void)w;(void)h; memcpy(p,vram,sizeof vram);
}
int gpu_vram_dirty_tracking(void) { return 0; }
int gpu_vram_dirty_verify_enabled(void) { return 0; }
uint32_t gpu_vram_dirty_row_count(void) { return 512; }
const uint64_t* gpu_vram_dirty_mask(void) { static uint64_t mask[8]; return mask; }
void gpu_vram_dirty_clear(void) {}
void psx_kernel_bless_note_range(uint32_t p, uint32_t n) { (void)p;(void)n;side_effects++; }
void overlay_watch_invalidate_after_ram_restore(void) { side_effects++; }
void gte_canonicalize_cpu_state(CPUState* cpu) { cpu->gpr[0] = 0; side_effects++; }
void interrupts_set_cycles_since_vblank(uint32_t p) { phase = p; side_effects++; }
uint32_t interrupts_get_cycles_since_vblank(void) { return phase; }
void timers_get_snapshot(uint16_t c[3],uint32_t m[3],uint16_t t[3],int32_t i[3],uint32_t f[3]) {
    for(int k=0;k<3;k++){c[k]=(uint16_t)timer_marker;m[k]=timer_marker;t[k]=3;i[k]=1;f[k]=4;}
}
void timers_set_snapshot(const uint16_t c[3],const uint32_t m[3],const uint16_t t[3],const int32_t i[3],const uint32_t f[3]) {
    (void)c;(void)t;(void)i;(void)f;timer_marker=m[0];side_effects++;
}
uint32_t dirty_ram_get_bitmap_word_count(void) { return 16; }
uint32_t dirty_ram_get_bitmap_word(uint32_t i) { return bitmap[i]; }
void dirty_ram_set_bitmap_words(const uint32_t* p,uint32_t n) { assert(n==16);memcpy(bitmap,p,64);side_effects++; }
#define DEVICE(name, marker) \
uint32_t name##_snapshot_bytes(void) { return 4; } \
void name##_snapshot_write(uint8_t* p) { PstW w;pst_w_init(&w,p,4);pst_w_u32(&w,marker); } \
int name##_snapshot_read(const uint8_t* p,uint32_t n) { \
    PstR r;if(n!=4||commit_failure)return 0;pst_r_init(&r,p,n);pst_r_u32(&r,&marker); \
    if(&marker==&cd_marker)cd_restore_clock=psx_cycle_count;side_effects++;return 1; }
DEVICE(gpu,gpu_marker)
DEVICE(spu,spu_marker)
DEVICE(cdrom,cd_marker)
void gpu_ws_end_linked_list(void) { side_effects++; }
void gpu_ws_begin_linked_list(void) { side_effects++; }
void gpu_ws_prepass_linked_list(uint32_t p) { (void)p;side_effects++; }
void gpu_ws_restore_linked_list_rank(uint32_t p) { (void)p;side_effects++; }

static uint32_t u32(const uint8_t* p) { PstR r;uint32_t v;pst_r_init(&r,p,4);assert(pst_r_u32(&r,&v));return v; }
static void put32(uint8_t* p,uint32_t v) { PstW w;pst_w_init(&w,p,4);assert(pst_w_u32(&w,v)); }
static void put64(uint8_t* p,uint64_t v) { PstW w;pst_w_init(&w,p,8);assert(pst_w_u64(&w,v)); }
static size_t section(const uint8_t* p,size_t n,uint32_t wanted) {
    size_t off=36;
    for(uint32_t i=0;i<u32(p+28);i++) {
        assert(off+16<=n);uint32_t tag=u32(p+off);uint32_t len=u32(p+off+8);
        if(tag==wanted)return off;
        off+=16+len;
    }
    assert(!"section missing");return 0;
}
static void snapshot(CPUState* cpu,uint8_t** p,size_t* n) {
    assert(boot_state_save_buffer_raw(cpu,0x12345678,0x80010000,p,n));
}
static void unchanged(CPUState* cpu,const uint8_t* before,size_t before_n,
                      const uint8_t* candidate,size_t candidate_n) {
    unsigned effects=side_effects;int outstanding=live_boot_allocations;
    assert(!boot_state_load_buffer(candidate,candidate_n,0x12345678,0x80010000,cpu));
    assert(side_effects==effects);assert(live_boot_allocations==outstanding);
    fail_at=-1;
    uint8_t* after;size_t after_n;snapshot(cpu,&after,&after_n);
    assert(after_n==before_n && !memcmp(before,after,before_n));bs_test_free(after);
}

int main(int argc, char** argv) {
    CPUState cpu;memset(&cpu,0,sizeof cpu);cpu.pc=0x80010000;cpu.gpr[3]=123;
    memset(ram,0x55,sizeof ram);memset(vram,0x66,sizeof vram);memset(spuram,0x77,sizeof spuram);
    timer_marker=91;i_stat=8;i_mask=7;psx_cycle_count=100000;phase=123;
    uint8_t *base,*wire;size_t n;snapshot(&cpu,&base,&n);wire=malloc(n+256);
    if(argc==2 && !strcmp(argv[1],"--commit-failure")) {
        commit_failure=1;
        (void)boot_state_load_buffer(base,n,0x12345678,0x80010000,&cpu);
        fputs("BUG: returned from failed commit\n",stderr);return 2;
    }
    size_t cpu_off=section(base,n,BS_SEC_CPU),dma_off=section(base,n,BS_SEC_DMA);
    size_t mdec_off=section(base,n,BS_SEC_MDEC),icache_off=section(base,n,BS_SEC_ICACHE);
    size_t dirty_off=section(base,n,BS_SEC_DIRTY);
    /* Early CPU/RAM would change if the old one-pass loader were used. */
    for(int failure=0;failure<11;failure++) {
        memcpy(wire,base,n);put32(wire+cpu_off+16+12,456);
        size_t candidate_n=n;
        switch(failure) {
        case 0: candidate_n=n-1;break; /* truncated final payload */
        case 1: put32(wire+dirty_off,0x9000);break; /* required section absent */
        case 2: put32(wire+icache_off,BS_SEC_CPU);break; /* duplicate */
        case 3: put32(wire+icache_off+4,2);break; /* unknown known-tag flags */
        case 4: put64(wire+icache_off+8,UINT64_MAX);break;
        case 5: put32(wire+mdec_off+16,99);break; /* bad MDEC version */
        case 6: put32(wire+mdec_off+16+48,1);break; /* output_pos beyond FIFO */
        case 7: wire[dma_off+16+7*12+8+3*18+1]=255;break; /* LL phase */
        case 8: put32(wire+28,u32(wire+28)+1);break; /* missing late header */
        case 9: wire[n]=7;candidate_n++;break; /* unframed trailing data */
        case 10: put32(wire+mdec_off+16+8,UINT32_MAX);break; /* unbounded command reserve */
        }
        unchanged(&cpu,base,n,wire,candidate_n);
    }
    /* Missing palette-like/device bytes are tested by shortening a known
     * section while keeping the outer stream structurally correct. */
    memcpy(wire,base,n);put32(wire+dirty_off+8,u32(wire+dirty_off+8)-4);
    memmove(wire+dirty_off+16+60,wire+dirty_off+16+64,n-(dirty_off+16+64));
    unchanged(&cpu,base,n,wire,n-4);

    /* Corrupt compressed known section late in the stream. */
    memcpy(wire,base,n);put32(wire+icache_off+4,BOOT_STATE_SEC_ZLIB);
    put32(wire+icache_off+16,4096);memset(wire+icache_off+20,0,64);
    unchanged(&cpu,base,n,wire,n);
    /* Allocation failure during raw preflight (aligned DIRTY staging). */
    allocations=0;fail_at=0;unchanged(&cpu,base,n,base,n);
    /* MDEC's first and second reservations can fail independently. The second
     * failure is allowed to leave a larger host input capacity, but no guest
     * scalar/FIFO or device callback may change. */
    allocations=0;fail_at=1;unchanged(&cpu,base,n,base,n);
    allocations=0;fail_at=2;unchanged(&cpu,base,n,base,n);

    /* Unknown sections keep forward compatibility even with future flags and
     * non-zlib bytes: only their encoded span is meaningful to this reader. */
    memcpy(wire,base,n);put32(wire+28,u32(wire+28)+1);put32(wire+n,0x9999);
    put32(wire+n+4,0xFFFF);put64(wire+n+8,3);memset(wire+n+16,0xDD,3);
    assert(boot_state_load_buffer(wire,n+19,0x12345678,0x80010000,&cpu));
    /* Baseline read/write byte identity and repeated restore determinism. */
    uint8_t *again;size_t again_n;snapshot(&cpu,&again,&again_n);
    assert(again_n==n && !memcmp(base,again,n));bs_test_free(again);
    assert(boot_state_load_buffer(base,n,0x12345678,0x80010000,&cpu));
    snapshot(&cpu,&again,&again_n);assert(again_n==n&&!memcmp(base,again,n));bs_test_free(again);
    /* On-disk section order cannot move CD deadline reconstruction ahead of
     * CLOCK or the DMA prepass ahead of RAM/VRAM. Reverse all wire sections. */
    size_t offsets[64],lengths[64],pos=36;uint32_t count=u32(base+28);assert(count<64);
    for(uint32_t i=0;i<count;i++){offsets[i]=pos;lengths[i]=16+u32(base+pos+8);pos+=lengths[i];}
    memcpy(wire,base,36);pos=36;
    for(uint32_t i=count;i>0;i--){memcpy(wire+pos,base+offsets[i-1],lengths[i-1]);pos+=lengths[i-1];}
    assert(pos==n);psx_cycle_count=7;
    assert(boot_state_load_buffer(wire,n,0x12345678,0x80010000,&cpu));
    assert(cd_restore_clock==100000);
    snapshot(&cpu,&again,&again_n);assert(again_n==n&&!memcmp(base,again,n));bs_test_free(again);

    /* Valid compressed input follows the same staged commit path. */
    uint8_t *compressed;size_t compressed_n;
    assert(boot_state_save_buffer(&cpu,0x12345678,0x80010000,&compressed,&compressed_n));
    assert(boot_state_load_buffer(compressed,compressed_n,0x12345678,0x80010000,&cpu));
    bs_test_free(compressed);
    snapshot(&cpu,&again,&again_n);assert(again_n==n&&!memcmp(base,again,n));bs_test_free(again);
    /* Raw hot loads only allocate the 64-byte aligned dirty bitmap, never
     * backups of RAM/VRAM/SPURAM or a second MDEC FIFO. */
    allocations=0;
    assert(boot_state_load_buffer(base,n,0x12345678,0x80010000,&cpu));
    assert(allocations==1);

    /* A paused partial command must reserve its future FIFO extent before
     * resumed CPU/DMA writes, even though the wire stores zero input words. */
    uint8_t partial[340]={0};put32(partial,1);put32(partial+4,0x2000FFFF);
    put32(partial+8,131070);partial[64]=1; /* busy */
    assert(mdec_snapshot_prepare(partial,sizeof partial));
    assert(last_realloc_size>=131070u*2u);
    assert(mdec_snapshot_read(partial,sizeof partial));
    for(unsigned i=0;i<300;i++)mdec_write(0,0x12345678);
    uint32_t partial_n=mdec_snapshot_bytes();uint8_t* partial_saved=malloc(partial_n);
    mdec_snapshot_write(partial_saved);
    assert(u32(partial_saved+324)==600 && partial_n==340+1200);
    for(unsigned i=0;i<300;i++)assert(u32(partial_saved+340+i*4)==0x12345678);
    /* Both reserve failures preserve an already populated FIFO, including
     * direct module reads. A successful first realloc may move its pointer. */
    uint8_t* grow=calloc(1,340+8192);memcpy(grow,partial,340);
    put32(grow+8,262140);put32(grow+328,8192);
    for(int failure=0;failure<3;failure++) {
        allocations=0;fail_at=failure==1?1:0;
        if(failure<2)assert(!mdec_snapshot_prepare(grow,340+8192));
        else assert(!mdec_snapshot_read(grow,340+8192));
        fail_at=-1;
        assert(mdec_snapshot_bytes()==partial_n);
        uint8_t* unchanged_fifo=malloc(partial_n);mdec_snapshot_write(unchanged_fifo);
        assert(!memcmp(partial_saved,unchanged_fifo,partial_n));free(unchanged_fifo);
    }
    free(grow);
    free(partial_saved);
    /* Return to the original snapshot before the final whole-state proof. */
    assert(boot_state_load_buffer(base,n,0x12345678,0x80010000,&cpu));
    if(argc==2) {
        /* Exercise the real savestate_poll for both blob and file requests.
         * Invalid incoming PCs reject before CPU/RAM/device mutation. */
        savestate_configure(argv[1],0x12345678,0x80010000,NULL,0);
        const uint32_t invalid[]={0,PSX_EXC_SENTINEL_PC,0x80000080,0xBFC00180,0x80000000,0x80010002};
        for(unsigned disk=0;disk<2;disk++)for(unsigned i=0;i<sizeof invalid/sizeof invalid[0];i++) {
            memcpy(wire,base,n);put32(wire+cpu_off+16+128,invalid[i]);
            put32(wire+cpu_off+16+12,456);
            unsigned effects=side_effects,notices=load_fail_notices;
            if(disk) {
                assert(savestate_write_slot(0,wire,n));assert(savestate_request_load_protocol(0));
            } else assert(savestate_request_load_blob_protocol(wire,n));
            savestate_poll(&cpu,cpu.pc);
            assert(savestate_take_load_failed() && !savestate_take_load_completed());
            assert(side_effects==effects && load_fail_notices==notices+1);
            snapshot(&cpu,&again,&again_n);assert(again_n==n&&!memcmp(base,again,n));bs_test_free(again);
        }
        /* The callback sees the decompressed CPU wire too. */
        CPUState bad_cpu=cpu;bad_cpu.pc=0;
        assert(boot_state_save_buffer(&bad_cpu,0x12345678,0x80010000,&compressed,&compressed_n));
        unsigned effects=side_effects;
        assert(savestate_request_load_blob_protocol(compressed,compressed_n));
        savestate_poll(&cpu,cpu.pc);assert(savestate_take_load_failed());
        assert(side_effects==effects);bs_test_free(compressed);
        /* Incoming address policy must not consult old live overlay ownership.
         * A valid address plus changed incoming CPU/RAM commits and resumes. */
        memcpy(wire,base,n);put32(wire+cpu_off+16+128,0x80123450);
        put32(wire+cpu_off+16+12,456);wire[section(wire,n,BS_SEC_RAM)+16]=0x44;
        live_dispatchable=0;
        assert(savestate_request_load_blob_protocol(wire,n));
        savestate_poll(&cpu,cpu.pc);
        assert(resumed_pc==0x80123450 && cpu.pc==resumed_pc && cpu.gpr[3]==456 && ram[0]==0x44);
        assert(savestate_take_load_completed()&&!savestate_take_load_failed());
        live_dispatchable=1;
        assert(boot_state_load_buffer(base,n,0x12345678,0x80010000,&cpu));
        puts("PASS real savestate blob/file resume-PC rejection precedes mutation and valid incoming state resumes");
    }
    bs_test_free(base);free(wire);assert(live_boot_allocations==0);
    puts("PASS staged snapshot corruption rejection, raw/zlib roundtrip, unknown sections and repeat restore");
    return 0;
}
