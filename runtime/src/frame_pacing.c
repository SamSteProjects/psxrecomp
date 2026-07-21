/*
 * frame_pacing.c — race-free wall-clock frame pacing.
 * See frame_pacing.h for the Bug B history this replaces.
 */
#include "frame_pacing.h"

/* FRAME_PACING_PURE_ONLY: tests compile only the SDL-free decision
 * function (tests/test_frame_pacing.c includes this file directly). */
#ifndef FRAME_PACING_PURE_ONLY
#include <SDL.h>
#if defined(_WIN32)
#include <windows.h>
#include <mmsystem.h>
#endif
#endif

uint32_t frame_pacing_sleep_ms(uint64_t now, uint64_t deadline,
                               uint64_t freq, uint64_t period) {
    if (now >= deadline) return 0;            /* compare BEFORE subtract */
    uint64_t remaining = deadline - now;       /* cannot underflow */
    if (remaining > period) remaining = period;/* hard cap: one frame max */
    if (freq == 0) return 0;
    /* remaining <= period (~one frame of ticks), so *1000 cannot overflow. */
    uint64_t ms = (remaining * 1000u) / freq;
    if (ms < 2) return 0;                      /* sub-2ms: spin instead */
    return (uint32_t)(ms - 1);                 /* undershoot; spin covers rest */
}

#ifndef FRAME_PACING_PURE_ONLY

#if defined(_WIN32)
/* Windows' legacy default timer quantum can round an 11-12 ms SDL_Delay up to
 * roughly 15.6 ms. At a 59.94 Hz deadline that produces a 20 ms frame followed
 * by a deliberately unpaced catch-up frame, visible as 12/21 ms cadence even
 * though the long-run average is 60 Hz. Request 1 ms precision only while a
 * paced runtime is active. This changes host sleep granularity, not emulated
 * cycles, interrupt timing, audio scheduling, or the guest frame rate. */
static int s_high_resolution_timer_active = 0;

static void frame_pacer_enable_high_resolution_timer(void) {
    if (!s_high_resolution_timer_active && timeBeginPeriod(1) == TIMERR_NOERROR)
        s_high_resolution_timer_active = 1;
}
#else
static void frame_pacer_enable_high_resolution_timer(void) { }
#endif

/* Bounded catch-up window, in periods. A transient stall (heavy frame, CD
 * burst) leaves next_deadline in the past; KEEPING that debt and running
 * unpaced until it is repaid preserves the long-term rate at exactly one
 * period per frame — which the audio pipeline depends on (the SPU produces
 * 768 guest cycles per output sample; every re-anchor that forgives debt
 * permanently starves the audio ring by the forgiven amount. Measured on
 * MMX5: forgiving all >1-period debt averaged 59.80 Hz against a 59.94
 * target = -0.4% chronic audio underrun). Only debt beyond this window —
 * sustained sub-realtime emulation, not a hiccup — is forgiven, else the
 * pacer would demand unbounded catch-up. */
/* Vigilante 8's streamed FMV transitions have measured host stalls near
 * 140 ms. Eight 60 Hz periods are only 133.3 ms, so the old bound classified
 * those finite transitions as sustained slowness and permanently forgave the
 * guest/audio debt. Keep a bounded 12-period (200 ms at 60 Hz) window: enough
 * to repay the observed transition without turning a real hang, suspend, or
 * sub-realtime workload into an unbounded catch-up burst. */
#define FRAME_PACER_CATCHUP_MAX_PERIODS 12u

void frame_pacer_wait(FramePacer *p, double period_ms) {
    frame_pacer_enable_high_resolution_timer();
    uint64_t freq = SDL_GetPerformanceFrequency();
    uint64_t period = (uint64_t)((double)freq * (period_ms / 1000.0));
    uint64_t now = SDL_GetPerformanceCounter();

    if (p->next_deadline == 0 ||
        now >= p->next_deadline + period * FRAME_PACER_CATCHUP_MAX_PERIODS) {
        /* First frame, or sustained slowness beyond the catch-up window:
         * re-anchor (forgive the debt). */
        p->next_deadline = now + period;
        return;
    }
    if (now >= p->next_deadline) {
        /* In debt from a recent stall: run this frame unpaced and advance
         * the deadline, repaying one period of debt per fast frame. */
        p->next_deadline += period;
        return;
    }

    for (;;) {
        now = SDL_GetPerformanceCounter();     /* ONE read per iteration */
        uint32_t ms = frame_pacing_sleep_ms(now, p->next_deadline, freq, period);
        if (ms == 0) break;
        SDL_Delay(ms);
    }
    while (SDL_GetPerformanceCounter() < p->next_deadline) {
        /* final sub-ms spin */
    }
    p->next_deadline += period;
}

void frame_pacer_shutdown(void) {
#if defined(_WIN32)
    if (s_high_resolution_timer_active) {
        timeEndPeriod(1);
        s_high_resolution_timer_active = 0;
    }
#endif
}
#endif /* FRAME_PACING_PURE_ONLY */
