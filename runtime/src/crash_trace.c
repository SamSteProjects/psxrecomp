/* crash_trace.c — unified crash diagnostic dump.
 *
 * Writes a single JSON report file (psx_last_run_report.json) on:
 *   - signal (SIGSEGV / SIGABRT)
 *   - Windows SEH unhandled exception
 *   - atexit
 *   - fail-fast psx_unknown_dispatch
 *   - trap_crash
 *   - TCP "post_mortem_dump" command (future)
 *
 * Mirrors the sibling SuperMarioWorldRecomp project's src/post_mortem.c. The file
 * is OVERWRITTEN on each dump (last-write-wins, single file per run);
 * this is not a log per CLAUDE.md §3 — it's a one-shot final state
 * snapshot for crashes the running TCP server cannot intercept.
 *
 * All payload comes from already-existing rings; this module is a
 * serializer, not a recorder.
 */

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <intrin.h>     /* __readgsqword — fiber TEB stack bounds for native_stack walk */
#endif

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>   /* va_start/va_end — not pulled in transitively off Windows */
#include <time.h>

#include "cpu_state.h"
#include "bios_hle.h"
#include "cdrom.h"
#include "crash_trace.h"
#include "spu.h"
#include "audio_trace.h"

/* Output path — overwritten per dump. */
static const char *kReportPath = "psx_last_run_report.json";

/* Preserve the command/sector/audio timeline beside manual captures.  PCM can
 * prove that a sound reached the speakers, but not why a back-to-back action
 * failed to start a second stream; this bounded archive ties guest CD commands
 * to the selected XA file/channel and the corresponding decoded samples. */
static void dump_manual_audio_cd_timeline(uint64_t frame)
{
    char path[112];
    snprintf(path, sizeof(path), "psx_audio_%llu_timeline.json",
             (unsigned long long)frame);
    FILE *f = fopen(path, "wb");
    if (!f) return;

    const CDROMCommandHistoryEntry *commands = NULL;
    const CDROMSectorHistoryEntry *sectors = NULL;
    uint64_t command_total = cdrom_debug_get_command_history(&commands);
    uint64_t sector_total = cdrom_debug_get_sector_history(&sectors);
    uint64_t command_start = command_total > 1024u ? command_total - 1024u : 0u;
    uint64_t sector_start = sector_total > 1024u ? sector_total - 1024u : 0u;
    AudioTraceEvent *events = (AudioTraceEvent *)malloc(4096u * sizeof(*events));
    uint32_t event_count = events ? audio_trace_events_get(events, 4096u) : 0u;

    fprintf(f, "{\n\"frame\":%llu,\n\"commands\":[",
            (unsigned long long)frame);
    int comma = 0;
    for (uint64_t seq = command_start; seq < command_total; seq++) {
        const CDROMCommandHistoryEntry *e =
            &commands[seq % CDROM_COMMAND_HISTORY_CAP];
        if (e->seq != seq) continue;
        fprintf(f, "%s{\"seq\":%llu,\"frame\":%u,\"kind\":%u,\"cmd\":%u,"
                   "\"pc\":%u,\"func\":%u,\"params\":[",
                comma ? "," : "", (unsigned long long)e->seq, e->frame,
                e->kind, e->cmd, e->pc, e->func);
        for (uint32_t p = 0; p < e->param_count; p++)
            fprintf(f, "%s%u", p ? "," : "", e->params[p]);
        fprintf(f, "],\"mode\":%u,\"irq\":%u,\"reading\":%u,"
                   "\"pending\":%u,\"queued\":%u}",
                e->mode, e->irq_flag, e->reading,
                e->pending_pending, e->queued_pending);
        comma = 1;
    }
    fprintf(f, "],\n\"sectors\":[");
    comma = 0;
    for (uint64_t seq = sector_start; seq < sector_total; seq++) {
        const CDROMSectorHistoryEntry *e =
            &sectors[seq % CDROM_SECTOR_HISTORY_CAP];
        if (e->seq != seq) continue;
        fprintf(f, "%s{\"seq\":%llu,\"frame\":%u,\"lba\":%d,"
                   "\"file\":%u,\"channel\":%u,\"submode\":%u,"
                   "\"coding\":%u,\"xa\":%u,\"skip\":%u}",
                comma ? "," : "", (unsigned long long)e->seq, e->frame,
                e->lba, e->xa_file, e->xa_channel, e->xa_submode,
                e->xa_coding, e->xa_audio_delivered, e->skip_reason);
        comma = 1;
    }
    fprintf(f, "],\n\"audio_events\":[");
    for (uint32_t i = 0; i < event_count; i++) {
        const AudioTraceEvent *e = &events[i];
        fprintf(f, "%s{\"seq\":%llu,\"sample\":%llu,\"frame\":%u,"
                   "\"kind\":%u,\"a\":%u,\"b\":%u}",
                i ? "," : "", (unsigned long long)e->seq,
                (unsigned long long)e->sample_idx, e->frame, e->kind,
                e->a, e->b);
    }
    fprintf(f, "]\n}\n");
    free(events);
    fclose(f);
}

extern uint32_t g_ra_load_watch, g_ra_load_snap_pc, g_ra_load_snap_insn;
extern uint32_t g_ra_load_snap_before_ra, g_ra_load_snap_srcaddr;
extern uint32_t g_ra_load_snap_gpr[32];
extern int g_ra_load_snap_valid;

/* Build identity, embedded into every report so a user-submitted crash can be
 * correlated to an exact build (issue #1 reports had no version field). The git
 * rev comes from runtime.cmake (PSX_BUILD_REV); __DATE__/__TIME__ are a always-
 * available fallback that still distinguishes builds. */
#ifndef PSX_BUILD_REV
#define PSX_BUILD_REV "unknown"
#endif
static const char *kBuildId = PSX_BUILD_REV " (" __DATE__ " " __TIME__ ")";

/* CPU state pointer (set by debug server at init). */
extern CPUState *debug_cpu_ptr;

/* Frame counter from debug_server.c (non-static). */
extern uint64_t s_frame_count;

/* Globals from debug_server.c we want to capture. */
extern uint32_t g_debug_current_func_addr;
extern uint32_t g_debug_last_store_pc;

/* XA/CD callback density probe from interrupts.c.  These are intentionally
 * aggregate counters so manual snapshots can compare a laggy battle action
 * against a clean field transition without adding trace overhead. */
extern uint64_t g_xa_callback_cd_deliver_count;
extern uint64_t g_xa_callback_overlay_preempt_count;
extern uint32_t g_xa_callback_frame;
extern uint32_t g_xa_callback_deliveries_this_frame;
extern uint32_t g_xa_callback_max_deliveries_per_frame;
extern uint32_t g_xa_callback_last_interrupted_pc;
extern uint32_t g_xa_callback_last_s4;
extern uint64_t g_cdrom_deliver_count;
extern uint64_t g_cdrom_irq_probe_deliver_count;
extern uint64_t g_cdrom_overlay_preempt_count;
extern uint32_t g_cdrom_irq_frame;
extern uint32_t g_cdrom_irq_deliveries_this_frame;
extern uint32_t g_cdrom_irq_max_deliveries_per_frame;
extern uint32_t g_cdrom_irq_last_interrupted_pc;
extern void psx_cd_irq_probe_reset(void);
extern void debug_phase_probe_get(uint64_t *, uint64_t *, uint64_t *,
                                  uint64_t *, uint64_t *, uint64_t *);
extern int debug_phase_probe_hot_get(uint32_t *, uint64_t *, int);
extern void debug_phase_probe_reset(void);

/* Native dispatch nesting depth (generated/SCPH1001_dispatch.c). Incremented per
 * nested psx_dispatch_call, decremented on return. A huge value at crash time is
 * the direct fingerprint of runaway recursion (the host C stack mirrors the guest
 * call graph, so an unbounded call chain overflows it -> STATUS_STACK_OVERFLOW
 * 0xC00000FD). Pairs with the dirty_block tail, which names the recursing PCs. */
extern int g_psx_dispatch_depth;

/* Dispatch ring — accessor wrappers exported by debug_server.c. */
#define DISPATCH_TRACE_CAP (1 << 16)
extern uint32_t crash_trace_dispatch_ring_get(int idx);
extern uint64_t crash_trace_dispatch_seq_get(void);

/* Unknown-dispatch ring — layout must match debug_server.c's
 * UnknownDispatchEntry. Accessor wrappers exported by debug_server.c. */
typedef struct {
    uint64_t seq;
    uint32_t addr, phys, ra, a0, a1, frame, pad;
} UnknownDispatchEntry;
#define UNKNOWN_DISPATCH_CAP (1 << 16)
extern UnknownDispatchEntry crash_trace_unknown_get(uint64_t seq);
extern uint64_t crash_trace_unknown_seq_get(void);

/* IRQ delivery/restore ring (interrupts.c). Keep this layout in sync with
 * IrqCtxEntry there and with debug_server.c's irqctx_ring serializer. Including
 * it in the post-mortem report makes same-thread restore failures diagnosable
 * even when the process wedges before a TCP snapshot can be requested. */
typedef struct {
    uint64_t seq, cycle;
    uint32_t frame, istat, imask, sr, d44, cdrom_active, is_vblank;
    int dma_depth;
    uint32_t take_pc, real_epc, exit_pc, exit_reason, same_thread, restored;
    uint32_t v1_exit, v1_saved, ra_exit, ra_saved, redirects, entry_sp, pump_site;
} CrashIrqCtxEntry;
#define IRQCTX_RING_CAP 4096u
extern CrashIrqCtxEntry g_irqctx_ring[];
extern uint64_t g_irqctx_seq;

/* Dirty-RAM block log (defined in dirty_ram_interp.c). */
#include "dirty_ram_interp.h"

/* JSON helpers. Hand-rolled to avoid allocations on the SEH path. */

static int append_str(char *buf, size_t cap, size_t *pos, const char *s) {
    size_t n = strlen(s);
    if (*pos + n >= cap) return 0;
    memcpy(buf + *pos, s, n);
    *pos += n;
    buf[*pos] = 0;
    return 1;
}

static int append_fmt(char *buf, size_t cap, size_t *pos, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(buf + *pos, cap - *pos, fmt, ap);
    va_end(ap);
    if (n < 0 || (size_t)n >= cap - *pos) return 0;
    *pos += (size_t)n;
    return 1;
}

/* Escape a string for use as a JSON string value: backslash and double-quote
 * are backslash-escaped, control chars are dropped. Windows module paths
 * (e.g. C:\Games\...\TombaRecomp.exe) otherwise emit invalid JSON that parsers
 * reject — which is exactly what happened to a user-submitted crash report. */
static void json_escape(const char *in, char *out, size_t outcap) {
    size_t o = 0;
    for (size_t i = 0; in && in[i] && o + 2 < outcap; i++) {
        unsigned char ch = (unsigned char)in[i];
        if (ch == '\\' || ch == '"') { out[o++] = '\\'; out[o++] = (char)ch; }
        else if (ch >= 0x20)         { out[o++] = (char)ch; }
    }
    out[o] = 0;
}

/* Serialize a single uint32_t hex value as a JSON string. */
static void hex32(char *out, uint32_t v) {
    snprintf(out, 16, "\"0x%08X\"", v);
}

/* ── Exit origin ─────────────────────────────────────────────────────── */

/* Deliberate exit() callers tag themselves here so an "atexit" report can
 * distinguish a TCP quit from an SDL window close from an unexplained
 * exit.  "unknown" in a report means NOBODY tagged — main returned or an
 * untagged exit() fired; that is a finding, not noise. */
static const char *s_exit_origin = "unknown";

void psx_crash_trace_set_exit_origin(const char *origin) {
    if (origin) s_exit_origin = origin;
}

/* ── Native call-stack snapshot ──────────────────────────────────────────
 *
 * The recent_fn ring is TIME-ORDERED (function entries over time), so for a
 * runaway recursion its tail is dominated by whatever leaf was churning at the
 * trip — it does NOT show the actual recursion CYCLE. This walks the running
 * fiber's native stack at the fatal instant and recovers the true cycle:
 *
 *   - Walk from the current/faulting RSP up to the fiber StackBase (TEB GS:[8]).
 *   - Keep only qwords that are genuine return addresses: a value pointing into
 *     this module's .text whose immediately-preceding bytes are a `call`
 *     instruction (filters spilled function pointers / stale data that merely
 *     look like code addresses).
 *   - Run-length-collapse consecutive equal frames and emit module-relative
 *     RVAs, plus a small frequency histogram (the recursion participants each
 *     appear ~depth times and dominate it).
 *
 * Emitted RVAs are build-relative (module base + RVA). Symbolize offline against
 * the exact binary with nm (see _freeze_specimens/analyze_named.py, which reads
 * this `native_stack` block directly). Works on BOTH the SEH path (uses the
 * faulting ContextRecord->Rsp) and the graceful stack-guard halt path (walks the
 * current frame), in debug and release — no minidump required. */
#ifdef _WIN32
static int crash_is_retaddr(uintptr_t v, uintptr_t text_lo, uintptr_t text_hi) {
    if (v < text_lo + 7u || v >= text_hi) return 0;
    const unsigned char *p = (const unsigned char *)(v - 7);
    if (p[2] == 0xE8) return 1;                       /* call rel32  -> E8 at v-5 */
    unsigned char m = p[5];                            /* byte at v-2 */
    if (p[4] == 0xFF && ((m >= 0xD0 && m <= 0xD7) ||   /* call reg            */
                         (m >= 0x10 && m <= 0x17)))    /* call [reg]          */
        return 1;
    if (p[1] == 0xFF && p[2] == 0x15) return 1;        /* call [rip+disp32]   */
    if (p[3] == 0xFF && p[4] >= 0x50 && p[4] <= 0x57)  /* call [reg+disp8]    */
        return 1;
    return 0;
}

static void append_native_stack(char *buf, size_t cap, size_t *pos, uintptr_t start_sp) {
    HMODULE h = GetModuleHandleW(NULL);
    uintptr_t mb = (uintptr_t)h;
    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)h;
    IMAGE_NT_HEADERS *nt  = (IMAGE_NT_HEADERS *)((BYTE *)h + dos->e_lfanew);
    IMAGE_SECTION_HEADER *sec = IMAGE_FIRST_SECTION(nt);
    uintptr_t text_lo = 0, text_hi = 0;
    for (int i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        if (!memcmp(sec[i].Name, ".text", 5)) {
            text_lo = mb + sec[i].VirtualAddress;
            text_hi = text_lo + sec[i].Misc.VirtualSize;
            break;
        }
    }
    uintptr_t base = (uintptr_t)__readgsqword(0x08);   /* fiber StackBase (high) */
    char probe;
    if (start_sp == 0) start_sp = (uintptr_t)&probe;
    start_sp &= ~(uintptr_t)7;

    append_fmt(buf, cap, pos,
        "  \"native_stack\": {\n"
        "    \"module_base\": \"0x%llX\",\n"
        "    \"text_lo_rva\": \"0x%llX\",\n"
        "    \"text_hi_rva\": \"0x%llX\",\n"
        "    \"frames\": [",
        (unsigned long long)mb,
        (unsigned long long)(text_lo - mb),
        (unsigned long long)(text_hi - mb));

    enum { HCAP = 24, MAX_RUNS = 256 };
    uint32_t hk[HCAP]; uint32_t hc[HCAP]; int hn = 0;
    uint32_t prev_rva = 0; int run = 0, emitted = 0, total = 0;

    /* This runs in the crash/halt path, so it MUST never fault: bound every
     * read with VirtualQuery and stop at the first non-committed / non-readable
     * page or the PAGE_GUARD page (touching it would re-arm the overflow). The
     * fiber StackBase (base) is only a hint — if it's stale/bogus the region
     * walk terminates safely at the real committed-stack top anyway. */
    if (text_lo && start_sp) {
        MEMORY_BASIC_INFORMATION mbi;
        uintptr_t region_end = 0;
        for (uintptr_t a = start_sp; total < 300000; a += 8) {
            if (base > start_sp && a + 8 > base) break;       /* don't pass a good StackBase */
            if (a + 8 > region_end) {                          /* (re)validate the page region */
                if (!VirtualQuery((void *)a, &mbi, sizeof(mbi))) break;
                if (!(mbi.State & MEM_COMMIT)) break;
                if (mbi.Protect & PAGE_GUARD) break;
                DWORD pr = mbi.Protect & 0xFFu;
                if (!(pr & (PAGE_READONLY | PAGE_READWRITE | PAGE_WRITECOPY |
                            PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY)))
                    break;
                region_end = (uintptr_t)mbi.BaseAddress + mbi.RegionSize;
            }
            uintptr_t v = *(uintptr_t *)a;
            if (!crash_is_retaddr(v, text_lo, text_hi)) continue;
            uint32_t rva = (uint32_t)(v - mb);
            total++;
            int found = 0;
            for (int k = 0; k < hn; k++) { if (hk[k] == rva) { hc[k]++; found = 1; break; } }
            if (!found && hn < HCAP) { hk[hn] = rva; hc[hn] = 1; hn++; }
            if (total > 1 && rva == prev_rva) { run++; continue; }
            if (run > 0 && emitted < MAX_RUNS) {
                append_fmt(buf, cap, pos, "%s{\"rva\":\"0x%X\",\"n\":%d}",
                           emitted ? "," : "", prev_rva, run);
                emitted++;
            }
            prev_rva = rva; run = 1;
        }
        if (run > 0 && emitted < MAX_RUNS)
            append_fmt(buf, cap, pos, "%s{\"rva\":\"0x%X\",\"n\":%d}",
                       emitted ? "," : "", prev_rva, run);
    }
    append_fmt(buf, cap, pos,
        "],\n    \"total_frames\": %d,\n    \"runs_emitted\": %d,\n    \"histogram\": [",
        total, emitted);
    for (int k = 0; k < hn; k++)
        append_fmt(buf, cap, pos, "%s{\"rva\":\"0x%X\",\"n\":%u}", k ? "," : "", hk[k], hc[k]);
    append_str(buf, cap, pos, "]\n  },\n");
}
#endif /* _WIN32 */

/* ── Main entry ──────────────────────────────────────────────────────── */

void psx_crash_trace_dump(const char *reason, void *seh_info) {
    /* Pre-allocate large stack buffer; avoid heap on SEH path. */
    static char buf[8 * 1024 * 1024]; /* 8 MB */
    size_t pos = 0;
    uint64_t phase_total = 0, phase_interp = 0, phase_native = 0;
    uint64_t phase_static = 0, phase_gpu = 0, phase_exc = 0;
    SpuDebugInfo spu_info;
    memset(&spu_info, 0, sizeof(spu_info));
    spu_debug_info(&spu_info);
    debug_phase_probe_get(&phase_total, &phase_interp, &phase_native,
                          &phase_static, &phase_gpu, &phase_exc);

    /* Header */
    char ts[64] = {0};
    {
        time_t now = time(NULL);
        struct tm *tm = gmtime(&now);
        if (tm) strftime(ts, sizeof(ts), "%Y-%m-%dT%H:%M:%SZ", tm);
    }

    append_fmt(buf, sizeof(buf), &pos,
        "{\n"
        "  \"reason\": \"%s\",\n"
        "  \"exit_origin\": \"%s\",\n"
        "  \"build\": \"%s\",\n"
        "  \"timestamp\": \"%s\",\n"
        "  \"frame\": %llu,\n"
        "  \"dispatch_depth\": %d,\n"
        "  \"last_func_addr\": \"0x%08X\",\n"
        "  \"last_store_pc\": \"0x%08X\",\n",
        reason ? reason : "(unknown)",
        s_exit_origin,
        kBuildId,
        ts,
        (unsigned long long)s_frame_count,
        g_psx_dispatch_depth,
        g_debug_current_func_addr,
        g_debug_last_store_pc);

    append_fmt(buf, sizeof(buf), &pos,
        "  \"xa_callback\": {\"total_cd_deliveries\":%llu,"
        "\"overlay_preemptions\":%llu,\"frame\":%u,"
        "\"deliveries_this_frame\":%u,\"max_deliveries_per_frame\":%u,"
        "\"last_interrupted_pc\":\"0x%08X\",\"last_s4\":\"0x%08X\"},\n",
        (unsigned long long)g_xa_callback_cd_deliver_count,
        (unsigned long long)g_xa_callback_overlay_preempt_count,
        g_xa_callback_frame, g_xa_callback_deliveries_this_frame,
        g_xa_callback_max_deliveries_per_frame,
        g_xa_callback_last_interrupted_pc, g_xa_callback_last_s4);
    append_fmt(buf, sizeof(buf), &pos,
        "  \"cd_irq\": {\"interval_deliveries\":%llu,\"lifetime_deliveries\":%llu,\"overlay_preemptions\":%llu,"
        "\"frame\":%u,\"deliveries_this_frame\":%u,"
        "\"max_deliveries_per_frame\":%u,\"last_interrupted_pc\":\"0x%08X\"},\n",
        (unsigned long long)g_cdrom_irq_probe_deliver_count,
        (unsigned long long)g_cdrom_deliver_count,
        (unsigned long long)g_cdrom_overlay_preempt_count,
        g_cdrom_irq_frame, g_cdrom_irq_deliveries_this_frame,
        g_cdrom_irq_max_deliveries_per_frame, g_cdrom_irq_last_interrupted_pc);
    append_fmt(buf, sizeof(buf), &pos,
        "  \"phase_probe\": {\"samples\":%llu,\"interp\":%llu,\"native\":%llu,"
        "\"static\":%llu,\"gpu\":%llu,\"exception\":%llu},\n",
        (unsigned long long)phase_total, (unsigned long long)phase_interp,
        (unsigned long long)phase_native, (unsigned long long)phase_static,
        (unsigned long long)phase_gpu, (unsigned long long)phase_exc);
    append_fmt(buf, sizeof(buf), &pos,
        "  \"spu_cd\": {\"ctrl\":\"0x%04X\",\"cd_vol_l\":%d,\"cd_vol_r\":%d,"
        "\"queued_frames\":%u,\"pushed_frames\":%llu,"
        "\"overflow_frames\":%llu,\"underflow_frames\":%llu,"
        "\"reset_count\":%llu,\"last_pushed_frames\":%llu,"
        "\"last_overflow_frames\":%llu,\"last_underflow_frames\":%llu,"
        "\"lifetime_pushed_frames\":%llu,\"lifetime_overflow_frames\":%llu,"
        "\"lifetime_underflow_frames\":%llu,"
        "\"last_discarded_on_reset_frames\":%llu,"
        "\"lifetime_discarded_on_reset_frames\":%llu,"
        "\"lifetime_inaudible_push_frames\":%llu},\n",
        (unsigned)(spu_info.ctrl & 0xFFFFu), (int)spu_info.cd_l, (int)spu_info.cd_r,
        spu_info.cd_frames,
        (unsigned long long)spu_info.cd_push_frames,
        (unsigned long long)spu_info.cd_overflow_frames,
        (unsigned long long)spu_info.cd_underflow_frames,
        (unsigned long long)spu_info.cd_reset_count,
        (unsigned long long)spu_info.cd_last_push_frames,
        (unsigned long long)spu_info.cd_last_overflow_frames,
        (unsigned long long)spu_info.cd_last_underflow_frames,
        (unsigned long long)spu_info.cd_lifetime_push_frames,
        (unsigned long long)spu_info.cd_lifetime_overflow_frames,
        (unsigned long long)spu_info.cd_lifetime_underflow_frames,
        (unsigned long long)spu_info.cd_last_discarded_on_reset_frames,
        (unsigned long long)spu_info.cd_lifetime_discarded_on_reset_frames,
        (unsigned long long)spu_info.cd_lifetime_inaudible_push_frames);
    {
        uint32_t hot_addr[16] = {0};
        uint64_t hot_count[16] = {0};
        int hot_n = debug_phase_probe_hot_get(hot_addr, hot_count, 16);
        append_str(buf, sizeof(buf), &pos, "  \"phase_hot_static\": [");
        for (int i = 0; i < hot_n; i++) {
            append_fmt(buf, sizeof(buf), &pos,
                "%s{\"addr\":\"0x%08X\",\"samples\":%llu}",
                i ? "," : "", hot_addr[i], (unsigned long long)hot_count[i]);
        }
        append_str(buf, sizeof(buf), &pos, "],\n");
    }

#ifdef _WIN32
    if (seh_info) {
        EXCEPTION_POINTERS *info = (EXCEPTION_POINTERS *)seh_info;
        DWORD code = info->ExceptionRecord->ExceptionCode;
        void *addr = info->ExceptionRecord->ExceptionAddress;
        const char *kind = "?";
        ULONG_PTR fault_addr = 0;
        if (code == EXCEPTION_ACCESS_VIOLATION) {
            ULONG_PTR k = info->ExceptionRecord->ExceptionInformation[0];
            kind = (k == 0) ? "read" : (k == 1) ? "write" : "execute";
            fault_addr = info->ExceptionRecord->ExceptionInformation[1];
        }
        append_fmt(buf, sizeof(buf), &pos,
            "  \"seh\": {\n"
            "    \"code\": \"0x%08lX\",\n"
            "    \"address\": \"%p\",\n"
            "    \"access\": \"%s\",\n"
            "    \"fault_addr\": \"0x%p\",\n",
            code, addr, kind, (void *)fault_addr);

        /* Module-relative location of the faulting instruction, so the
         * address survives ASLR and feeds straight into addr2line. */
        {
            MEMORY_BASIC_INFORMATION mbi;
            char mod_name[MAX_PATH] = "?";
            void *mod_base = NULL;
            if (VirtualQuery(addr, &mbi, sizeof(mbi))) {
                mod_base = mbi.AllocationBase;
                GetModuleFileNameA((HMODULE)mod_base, mod_name, sizeof(mod_name));
            }
            char mod_esc[MAX_PATH * 2];
            json_escape(mod_name, mod_esc, sizeof(mod_esc));
            append_fmt(buf, sizeof(buf), &pos,
                "    \"module\": \"%s\",\n"
                "    \"module_base\": \"%p\",\n"
                "    \"module_offset\": \"0x%llX\",\n",
                mod_esc, mod_base,
                (unsigned long long)((char *)addr - (char *)mod_base));
        }

        /* Poor-man's backtrace: scan the faulting thread's stack for values
         * that point into executable module regions and report them
         * module-relative. Noisy but enough to pin the faulting call path. */
        append_str(buf, sizeof(buf), &pos, "    \"stack_scan\": [");
        {
            CONTEXT *ctx = info->ContextRecord;
            ULONG_PTR *sp = (ULONG_PTR *)ctx->Rsp;
            int emitted = 0;
            for (int i = 0; i < 512 && emitted < 24; i++) {
                ULONG_PTR v;
                MEMORY_BASIC_INFORMATION mbi;
                if (!VirtualQuery(&sp[i], &mbi, sizeof(mbi)) ||
                    !(mbi.State & MEM_COMMIT)) break;
                v = sp[i];
                if (v < 0x10000) continue;
                if (!VirtualQuery((void *)v, &mbi, sizeof(mbi))) continue;
                if (mbi.Type != MEM_IMAGE) continue;
                if (!(mbi.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ |
                                     PAGE_EXECUTE_READWRITE))) continue;
                char mod_name[MAX_PATH] = "?";
                GetModuleFileNameA((HMODULE)mbi.AllocationBase, mod_name,
                                   sizeof(mod_name));
                const char *base = strrchr(mod_name, '\\');
                char bn_esc[MAX_PATH * 2];
                json_escape(base ? base + 1 : mod_name, bn_esc, sizeof(bn_esc));
                append_fmt(buf, sizeof(buf), &pos,
                    "%s\n      {\"module\": \"%s\", \"offset\": \"0x%llX\"}",
                    emitted ? "," : "", bn_esc,
                    (unsigned long long)(v - (ULONG_PTR)mbi.AllocationBase));
                emitted++;
            }
        }
        append_str(buf, sizeof(buf), &pos, "\n    ]\n  },\n");
    }
#else
    (void)seh_info;
#endif

    /* CPU state */
    if (debug_cpu_ptr) {
        CPUState *cpu = debug_cpu_ptr;
        append_str(buf, sizeof(buf), &pos, "  \"cpu\": {\n");
        append_fmt(buf, sizeof(buf), &pos,
            "    \"pc\": \"0x%08X\",\n"
            "    \"hi\": \"0x%08X\",\n"
            "    \"lo\": \"0x%08X\",\n"
            "    \"sr\": \"0x%08X\",\n"
            "    \"cause\": \"0x%08X\",\n"
            "    \"epc\": \"0x%08X\",\n"
            "    \"gpr\": [",
            cpu->pc, cpu->hi, cpu->lo,
            cpu->cop0[12], cpu->cop0[13], cpu->cop0[14]);
        for (int i = 0; i < 32; i++) {
            append_fmt(buf, sizeof(buf), &pos,
                "%s\"0x%08X\"", i == 0 ? "" : ",", cpu->gpr[i]);
        }
        append_str(buf, sizeof(buf), &pos, "]\n  },\n");
    } else {
        append_str(buf, sizeof(buf), &pos, "  \"cpu\": null,\n");
    }

    /* Targeted save-point probe: the first interpreted instruction that
     * establishes the wild return address. */
    append_fmt(buf, sizeof(buf), &pos,
        "  \"ra_load_watch\": {\"watch\":\"0x%08X\",\"valid\":%d,"
        "\"pc\":\"0x%08X\",\"insn\":\"0x%08X\","
        "\"before_ra\":\"0x%08X\",\"src_addr\":\"0x%08X\"},\n",
        g_ra_load_watch, g_ra_load_snap_valid, g_ra_load_snap_pc,
        g_ra_load_snap_insn, g_ra_load_snap_before_ra,
        g_ra_load_snap_srcaddr);

    /* Recursion fingerprint (build-independent GUEST addresses): the func entered
     * when the native stack guard tripped, plus the recent recompiled-function-
     * entry ring — for a runaway, recent_fn's tail repeats the recursing func, so
     * the report names the culprit even when the native stack_scan is absent (the
     * graceful-halt path) or unmappable (host offsets vs a different build). */
    {
        extern uint32_t g_psx_recent_fn[];
        extern uint32_t g_psx_recent_fn_i;
        extern uint32_t g_psx_recursion_func;
        enum { RECENT_FN_CAP = 64 };
        uint32_t total = g_psx_recent_fn_i;
        int count = (total < (uint32_t)RECENT_FN_CAP) ? (int)total : RECENT_FN_CAP;
        append_fmt(buf, sizeof(buf), &pos,
            "  \"recursion_func\": \"0x%08X\",\n"
            "  \"recent_fn\": {\n    \"total\": %u,\n    \"count\": %d,\n    \"addrs\": [",
            g_psx_recursion_func, total, count);
        uint32_t start = total - (uint32_t)count;
        for (int i = 0; i < count; i++) {
            uint32_t a = g_psx_recent_fn[(start + (uint32_t)i) & (RECENT_FN_CAP - 1u)];
            append_fmt(buf, sizeof(buf), &pos, "%s\"0x%08X\"", i == 0 ? "" : ",", a);
        }
        append_str(buf, sizeof(buf), &pos, "]\n  },\n");
    }

    /* Re-entry flight recorder (RECURSION_BUG.md §15): per-frame count of the
     * interp->0x8001A954 edge + cycle counter, leading up to the trip — answers
     * "ordinary bounded per-frame behavior that stopped terminating, or new edge?" */
    {
        extern int dirty_ram_re954_json(char *out, int cap);
        static char re954[8192];
        int k = dirty_ram_re954_json(re954, (int)sizeof(re954));
        if (k > 0) append_str(buf, sizeof(buf), &pos, re954);
    }

    /* Host-stack-usage profile (RECURSION_BUG.md §17): the climb curve —
     * flat-then-cliff vs linear-across-frames — that discriminates the freeze's
     * two models. Emitted BEFORE the early-flush below so it survives even if the
     * native_stack walk faults on the exhausted fiber stack. */
    {
        extern int stack_profile_json(char *out, int cap);
        static char sp[24576];
        int k = stack_profile_json(sp, (int)sizeof(sp));
        if (k > 0) {
            append_str(buf, sizeof(buf), &pos, "  \"stack_profile\": ");
            append_str(buf, sizeof(buf), &pos, sp);
            append_str(buf, sizeof(buf), &pos, ",\n");
        }
    }

    /* Boundary control-flow flight recorder (RECURSION_BUG.md §18): the per-frame
     * summary (shape over frames) + per-crossing detail (onset transfer). Emitted
     * before the early-flush so it survives a native_stack-walk fault. */
    {
        extern int dirty_ram_xprobe_json(char *out, int cap);
        static char xp[1048576];
        int k = dirty_ram_xprobe_json(xp, (int)sizeof(xp));
        if (k > 0) {
            append_str(buf, sizeof(buf), &pos, "  \"xprobe\": ");
            append_str(buf, sizeof(buf), &pos, xp);
            append_str(buf, sizeof(buf), &pos, ",\n");
        }
    }

    /* §19 compiled-entry depth profile: true intra-frame stack depth + raw TEB
     * values at the trip (real recursion vs garbage guard-read). */
    {
        extern int ce_profile_json(char *out, int cap);
        static char ce[49152];
        int k = ce_profile_json(ce, (int)sizeof(ce));
        if (k > 0) {
            append_str(buf, sizeof(buf), &pos, "  \"ce_profile\": ");
            append_str(buf, sizeof(buf), &pos, ce);
            append_str(buf, sizeof(buf), &pos, ",\n");
        }
    }

    /* Native call-stack snapshot — the TRUE recursion cycle (recent_fn above is
     * time-ordered and shows leaf churn, not the recursing frames).
     *
     * SAFETY: append_native_stack walks raw host stack memory and, despite its
     * VirtualQuery bounding, can still fault on a hostile crash state (e.g. the
     * recursion's own exhausted fiber stack). Because it runs INSIDE the dump,
     * such a fault would take the whole report with it (silent SIGSEGV, no
     * psx_last_run_report.json). So flush a complete-but-native_stack-less report
     * to disk FIRST; if the walk faults, the trigger context (reason, cpu,
     * recent_fn) is already on disk. If it survives, the final fwrite at the end
     * of this function overwrites this snapshot with the full report. */
#ifdef _WIN32
    {
        size_t safe_pos = pos;
        append_str(buf, sizeof(buf), &safe_pos, "  \"native_stack\": null\n}\n");
        FILE *pf = fopen(kReportPath, "wb");
        if (pf) { fwrite(buf, 1, safe_pos, pf); fclose(pf); }

        uintptr_t sp = 0;
        if (seh_info)
            sp = (uintptr_t)((EXCEPTION_POINTERS *)seh_info)->ContextRecord->Rsp;
        append_native_stack(buf, sizeof(buf), &pos, sp);
    }
#endif

    /* dispatch_ring tail (last 256) */
    {
        uint64_t total = crash_trace_dispatch_seq_get();
        int avail = (total < DISPATCH_TRACE_CAP) ? (int)total : DISPATCH_TRACE_CAP;
        int count = avail < 256 ? avail : 256;
        append_fmt(buf, sizeof(buf), &pos,
            "  \"dispatch_tail\": {\n"
            "    \"total\": %llu,\n"
            "    \"count\": %d,\n"
            "    \"addrs\": [",
            (unsigned long long)total, count);
        uint64_t start = total - (uint64_t)count;
        for (int i = 0; i < count; i++) {
            uint32_t a = crash_trace_dispatch_ring_get((int)((start + i) & (DISPATCH_TRACE_CAP - 1)));
            append_fmt(buf, sizeof(buf), &pos, "%s\"0x%08X\"", i == 0 ? "" : ",", a);
        }
        append_str(buf, sizeof(buf), &pos, "]\n  },\n");
    }

    /* unknown_dispatch tail (last 50) */
    {
        uint64_t total = crash_trace_unknown_seq_get();
        int avail = (total < UNKNOWN_DISPATCH_CAP) ? (int)total : UNKNOWN_DISPATCH_CAP;
        int count = avail < 50 ? avail : 50;
        append_fmt(buf, sizeof(buf), &pos,
            "  \"unknown_dispatch_tail\": {\n"
            "    \"total\": %llu,\n"
            "    \"count\": %d,\n"
            "    \"entries\": [",
            (unsigned long long)total, count);
        uint64_t start = total - (uint64_t)count;
        for (int i = 0; i < count; i++) {
            UnknownDispatchEntry e = crash_trace_unknown_get(start + i);
            append_fmt(buf, sizeof(buf), &pos,
                "%s{\"seq\":%llu,\"addr\":\"0x%08X\",\"phys\":\"0x%08X\","
                "\"ra\":\"0x%08X\",\"a0\":\"0x%08X\",\"a1\":\"0x%08X\","
                "\"frame\":%u}",
                i == 0 ? "" : ",",
                (unsigned long long)e.seq, e.addr, e.phys,
                e.ra, e.a0, e.a1, e.frame);
        }
        append_str(buf, sizeof(buf), &pos, "]\n  },\n");
    }

    /* IRQ-delivery/restore tail (last 64). This is the decisive evidence for
     * hangs that remain inside the BIOS event/exception continuation: it shows
     * whether the interrupted thread was identified correctly and whether its
     * live GPRs were restored before resuming. */
    {
        uint64_t total = g_irqctx_seq;
        uint64_t avail = total < IRQCTX_RING_CAP ? total : IRQCTX_RING_CAP;
        int count = (int)(avail < 64u ? avail : 64u);
        append_fmt(buf, sizeof(buf), &pos,
            "  \"irqctx_tail\": {\n"
            "    \"total\": %llu,\n"
            "    \"count\": %d,\n"
            "    \"entries\": [",
            (unsigned long long)total, count);
        uint64_t start = total - (uint64_t)count;
        for (int i = 0; i < count; i++) {
            CrashIrqCtxEntry *e =
                &g_irqctx_ring[(start + (uint64_t)i) & (IRQCTX_RING_CAP - 1u)];
            append_fmt(buf, sizeof(buf), &pos,
                "%s{\"seq\":%llu,\"cycle\":%llu,\"frame\":%u,"
                "\"vblank\":%u,\"istat\":\"0x%08X\",\"imask\":\"0x%08X\","
                "\"take_pc\":\"0x%08X\",\"real_epc\":\"0x%08X\","
                "\"exit_pc\":\"0x%08X\",\"exit_reason\":%u,"
                "\"same_thread\":%u,\"restored\":%u,"
                "\"v1_exit\":\"0x%08X\",\"v1_saved\":\"0x%08X\","
                "\"ra_exit\":\"0x%08X\",\"ra_saved\":\"0x%08X\","
                "\"entry_sp\":\"0x%08X\",\"redirects\":%u,\"pump_site\":%u}",
                i == 0 ? "" : ",",
                (unsigned long long)e->seq, (unsigned long long)e->cycle,
                e->frame, e->is_vblank, e->istat, e->imask,
                e->take_pc, e->real_epc, e->exit_pc, e->exit_reason,
                e->same_thread, e->restored,
                e->v1_exit, e->v1_saved, e->ra_exit, e->ra_saved,
                e->entry_sp, e->redirects, e->pump_site);
        }
        append_str(buf, sizeof(buf), &pos, "]\n  },\n");
    }

    /* BIOS-HLE route tail.  Keep this in the automatic report so a crash in
     * an IRQ-delivered event can distinguish "the direct DeliverEvent route
     * never activated" from "it activated and a callback/path after it
     * wedged" without relying on an interactive debug-server request. */
    {
        uint64_t total = psx_hle_ring_seq();
        uint64_t avail = total < PSX_HLE_RING_CAP ? total : PSX_HLE_RING_CAP;
        int count = (int)(avail < 32u ? avail : 32u);
        append_fmt(buf, sizeof(buf), &pos,
            "  \"bios_hle\": {\"enabled\":%d,\"total\":%llu,\"count\":%d,\"entries\":[",
            psx_bios_hle_enabled(), (unsigned long long)total, count);
        uint64_t start = total - (uint64_t)count;
        for (int i = 0; i < count; i++) {
            const PsxHleCallEntry *e = psx_hle_ring_entry(start + (uint64_t)i);
            if (!e) continue;
            append_fmt(buf, sizeof(buf), &pos,
                "%s{\"seq\":%llu,\"vector\":\"0x%08X\",\"fn\":\"0x%08X\","
                "\"a0\":\"0x%08X\",\"a1\":\"0x%08X\",\"ra\":\"0x%08X\","
                "\"v0\":\"0x%08X\",\"repeat\":%u,\"route\":%u,\"in_exc\":%u}",
                i == 0 ? "" : ",", (unsigned long long)e->seq, e->vector, e->fn,
                e->a0, e->a1, e->ra, e->v0, e->repeat, e->route, e->in_exc);
        }
        append_str(buf, sizeof(buf), &pos, "]},\n");
    }

    /* CD controller terminal state.  This is deliberately a compact snapshot
     * rather than the high-volume MMIO trace: a guest-side CD/libcd wait can
     * survive long enough to make the ordinary tail unhelpful, whereas the
     * controller's visible IRQ, pending command, and one-deep data-ready state
     * identify an acknowledgement/response ordering wedge directly. */
    {
        CDROMDebugState cd;
        cdrom_debug_snapshot(&cd);
        append_fmt(buf, sizeof(buf), &pos,
            "  \"cdrom\":{\"seq\":%llu,\"index\":%u,\"stat\":%u,"
            "\"request\":%u,\"irq_enable\":%u,\"irq_flag\":%u,"
            "\"pending_cmd\":%u,\"pending\":%d,\"pending_delay\":%d,"
            "\"queued_cmd\":%u,\"queued\":%u,\"reading\":%d,"
            "\"read_delay\":%d,\"sector_available\":%d,\"sector_pos\":%d,"
            "\"sector_size\":%d,\"int1_pending\":%u,\"int1_pended\":%llu,"
            "\"int1_lost\":%llu,\"i_stat\":\"0x%08X\"},\n",
            (unsigned long long)cd.seq, cd.index_reg, cd.stat_reg,
            cd.request_reg, cd.irq_enable, cd.irq_flag,
            cd.pending_cmd, cd.pending_pending, cd.pending_delay,
            cd.queued_cmd, cd.queued_pending, cd.reading,
            cd.read_delay, cd.sector_available, cd.sector_read_pos,
            cd.sector_size, cd.int1_pending_now,
            (unsigned long long)cd.int1_pended,
            (unsigned long long)cd.int1_lost, cd.i_stat);
    }

    /* Legaia-specific evidence without changing emulation: Andrew Altimit's
     * documented Tetsu-tutorial Healing Leaf freeze is caused when the SsAPI
     * sound/effect pointer table at 0x800794F0 is overwritten.  The item-use
     * path also reseats its field-pack pointer at 0x8007B8D0.  Record both
     * live values so the next failure separates a corrupt item-use asset from
     * an IRQ/CD timing fault. */
    if (debug_cpu_ptr && debug_cpu_ptr->read_word) {
        uint32_t ssapi[8];
        for (int i = 0; i < 8; i++)
            ssapi[i] = debug_cpu_ptr->read_word(0x800794F0u + (uint32_t)i * 4u);
        append_fmt(buf, sizeof(buf), &pos,
            "  \"legaia_item_use\":{\"field_pack\":\"0x%08X\",\"ssapi_794f0\":["
            "\"0x%08X\",\"0x%08X\",\"0x%08X\",\"0x%08X\","
            "\"0x%08X\",\"0x%08X\",\"0x%08X\",\"0x%08X\"]},\n",
            debug_cpu_ptr->read_word(0x8007B8D0u),
            ssapi[0], ssapi[1], ssapi[2], ssapi[3],
            ssapi[4], ssapi[5], ssapi[6], ssapi[7]);
    }

    /* dirty_block_log tail (last 100) */
    {
        uint64_t total = g_dirty_ram_block_log_seq;
        uint64_t avail = (total < DIRTY_RAM_BLOCK_LOG_CAP) ? total : DIRTY_RAM_BLOCK_LOG_CAP;
        int count = (int)((avail < 100) ? avail : 100);
        append_fmt(buf, sizeof(buf), &pos,
            "  \"dirty_block_tail\": {\n"
            "    \"total\": %llu,\n"
            "    \"count\": %d,\n"
            "    \"entries\": [",
            (unsigned long long)total, count);
        uint64_t start = total - (uint64_t)count;
        for (int i = 0; i < count; i++) {
            DirtyRamBlockLogEntry *e =
                &g_dirty_ram_block_log[(start + i) & (DIRTY_RAM_BLOCK_LOG_CAP - 1u)];
            append_fmt(buf, sizeof(buf), &pos,
                "%s{\"seq\":%llu,\"target\":\"0x%08X\",\"ra\":\"0x%08X\","
                "\"a0\":\"0x%08X\",\"a1\":\"0x%08X\",\"t1\":\"0x%08X\",\"frame\":%u}",
                i == 0 ? "" : ",",
                (unsigned long long)e->seq,
                e->target, e->ra, e->a0, e->a1, e->t1, e->frame);
        }
        append_str(buf, sizeof(buf), &pos, "]\n  }\n");
    }

    append_str(buf, sizeof(buf), &pos, "}\n");

    /* Write to file. Overwrite previous report. */
    FILE *f = fopen(kReportPath, "wb");
    if (f) {
        fwrite(buf, 1, pos, f);
        fclose(f);
    }
}

void psx_crash_trace_manual_snapshot(void) {
    /* Preserve the immediately preceding manual capture before overwriting the
     * latest one.  This makes a two-step A/B (laggy action, then clean field
     * transition) possible with the existing single Ctrl+F12 hotkey. */
    {
        FILE *old = fopen("psx_manual_snapshot.json", "rb");
        FILE *prev = fopen("psx_manual_snapshot_prev.json", "wb");
        if (old && prev) {
            char copy_buf[8192]; size_t copy_n;
            while ((copy_n = fread(copy_buf, 1, sizeof(copy_buf), old)) != 0)
                fwrite(copy_buf, 1, copy_n, prev);
        }
        if (old) fclose(old);
        if (prev) fclose(prev);
    }
    /* Reuse the normal bounded serializer, then preserve its output under a
     * distinct name so a later atexit/SEH report cannot overwrite it. */
    psx_crash_trace_dump("manual_snapshot", NULL);
    FILE *src = fopen(kReportPath, "rb");
    FILE *dst = fopen("psx_manual_snapshot.json", "wb");
    if (!src || !dst) { if (src) fclose(src); if (dst) fclose(dst); return; }
    char buf[8192];
    size_t n;
    while ((n = fread(buf, 1, sizeof(buf), src)) != 0) fwrite(buf, 1, n, dst);
    fclose(dst);
    fclose(src);
    /* Also retain a frame-numbered archive.  The rolling latest/previous pair
     * is convenient, but repeated hotkey presses must not erase the one frame
     * that captured an intermittent audio dropout. */
    {
        char archive_name[96];
        snprintf(archive_name, sizeof(archive_name),
                 "psx_manual_snapshot_%llu.json",
                 (unsigned long long)s_frame_count);
        FILE *latest = fopen("psx_manual_snapshot.json", "rb");
        FILE *archive = fopen(archive_name, "wb");
        if (latest && archive) {
            char archive_buf[8192]; size_t archive_n;
            while ((archive_n = fread(archive_buf, 1, sizeof(archive_buf), latest)) != 0)
                fwrite(archive_buf, 1, archive_n, archive);
        }
        if (latest) fclose(latest);
        if (archive) fclose(archive);
    }
    /* Preserve the last 15 seconds at each audio pipeline stage alongside the
     * JSON capture.  This distinguishes silent/wrong decoded XA (CD input)
     * from loss in SPU mixing or the final host queue without requiring the
     * TCP debug server to be available during a battle. */
    {
        static const char *tap_name[4] = { "spu", "cd", "host", "voices" };
        for (int tap = 0; tap < 4; tap++) {
            uint64_t total = audio_trace_tap_total(tap);
            uint64_t count = (uint64_t)audio_trace_tap_rate(tap) * 15u;
            if (count > total) count = total;
            int64_t start = (int64_t)(total - count);
            char wav_name[112];
            snprintf(wav_name, sizeof(wav_name), "psx_audio_%llu_%s.wav",
                     (unsigned long long)s_frame_count, tap_name[tap]);
            (void)audio_trace_dump_wav(tap, wav_name, start, count);
        }
    }
    dump_manual_audio_cd_timeline(s_frame_count);
    /* Begin the next manual-capture interval only after the current report is
     * completely written.  Three presses now retain action-vs-field reports:
     * baseline/reset, action/reset, then field. */
    psx_cd_irq_probe_reset();
    debug_phase_probe_reset();
}

/* ── Fatal halt ──────────────────────────────────────────────────────── */

const char *g_psx_fatal_reason = NULL;

/* freeze_heartbeat.c — full ring dump with wedge_kind "fatal". */
extern void freeze_heartbeat_fatal_dump(const char *reason);

void psx_fatal_halt(const char *reason) {
    /* Re-entry guard: a post-mortem TCP command served from the halt
     * loop below can itself trip a fatal site. Don't re-dump (the first
     * fatal is the real one) and don't recurse another serve loop. */
    static int s_halted = 0;
    if (!s_halted) {
        s_halted = 1;
        g_psx_fatal_reason = reason ? reason : "(fatal)";
        psx_crash_trace_dump(g_psx_fatal_reason, NULL);
        freeze_heartbeat_fatal_dump(g_psx_fatal_reason);
    }
#ifndef PSX_NO_DEBUG_TOOLS
    /* Halt-and-serve: emulation is dead but the rings are not. Keep the
     * TCP debug server pumping on this (main) thread so a post-mortem
     * client can run wtrace_dump / read_ram / screenshot / etc. against
     * the exact crash state. */
    extern void debug_server_poll(void);
    fprintf(stderr,
            "FATAL: %s — emulation halted; TCP debug server stays live "
            "for post-mortem ring queries.\n", g_psx_fatal_reason);
    fflush(stderr);
    for (;;) {
        debug_server_poll();
#ifdef _WIN32
        Sleep(1);
#else
        struct timespec req = {0, 1000000};
        nanosleep(&req, NULL);
#endif
    }
#else
    exit(1);
#endif
}

/* ── Crash handlers ──────────────────────────────────────────────────── */

#include <signal.h>

static void psx_signal_handler(int sig) {
    static char reason[64];
    snprintf(reason, sizeof(reason), "signal_%d", sig);
    psx_crash_trace_dump(reason, NULL);
    /* Involuntary death: dump the full freeze-style rings too, so the
     * crash doesn't take every ring with it. freeze_heartbeat_fatal_dump
     * guards against overwriting an earlier fatal dump. */
    if (!g_psx_fatal_reason) g_psx_fatal_reason = reason;
    freeze_heartbeat_fatal_dump(reason);
    /* Reraise default handler so debugger / OS can also act. */
    signal(sig, SIG_DFL);
    raise(sig);
}

#ifdef _WIN32
static LONG WINAPI psx_seh_handler(EXCEPTION_POINTERS *info) {
    psx_crash_trace_dump("seh", info);
    /* Same as the signal path: keep the rings on involuntary death. */
    if (!g_psx_fatal_reason) g_psx_fatal_reason = "seh";
    freeze_heartbeat_fatal_dump("seh");
    return EXCEPTION_EXECUTE_HANDLER;
}
#endif

static void psx_atexit_handler(void) {
    /* Only dump if no crash dump has been written yet. We can't easily
     * detect that, so just always overwrite — last write wins. */
    psx_crash_trace_dump("atexit", NULL);
}

void psx_crash_trace_install_handlers(void) {
    signal(SIGSEGV, psx_signal_handler);
    signal(SIGABRT, psx_signal_handler);
#ifdef _WIN32
    SetUnhandledExceptionFilter(psx_seh_handler);
    /* Suppress Windows error dialog so SEH unwinds straight to our
     * filter and we can write the report without the user having to
     * dismiss a popup first. */
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
#endif
    atexit(psx_atexit_handler);
}
