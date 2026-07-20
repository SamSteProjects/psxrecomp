#ifndef OVERLAY_CAPTURE_H
#define OVERLAY_CAPTURE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* overlay_capture: capture plus generic executable-image lifecycle evidence.
 *
 * On every CD DMA completion into game-code RAM (dest < 0x1C0000), the runtime
 * calls overlay_capture_on_dma().  Each unique load_addr is stored exactly once
 * in a write-once set.  At clean process exit, overlay_capture_write_json()
 * writes overlay_captures.json next to the executable for user contribution.
 *
 * The legacy contribution capture set remains write-once. Independently, the
 * lifecycle layer records every bounded post-handoff DMA span and supersedes
 * overlapping prior instances. It does not infer that adjacent transfers form
 * one overlay and does not claim unload events the runtime cannot observe.
 */

/* Call once at startup (before the run loop) with the exe directory.
 * Sets the output path for overlay_captures.json.  Capture is not yet
 * active — it activates automatically on the first post-game DMA transfer. */
void overlay_capture_set_out_dir(const char *out_dir);

/* Legacy init alias kept for compatibility; same as set_out_dir. */
void overlay_capture_init(const char *out_dir);

/* Enable/disable overlay capture. Off by default; main() enables it only when
 * the overlay cache is turned on in [runtime] config. When disabled,
 * overlay_capture_on_dma() and overlay_capture_write_json() are no-ops. */
void overlay_capture_set_enabled(int enabled);

/* Call from dma.c execute_ch3_cdrom() after every forward CH3 transfer with
 * load_start < 0x1C0000 and fntrace_is_game_started().
 * load_addr is the physical RAM destination, size is byte count,
 * bytes points to the RAM buffer at that address (already written by DMA). */
void overlay_capture_on_dma(uint32_t load_addr, uint32_t size,
                             const uint8_t *bytes);

/* Write overlay_captures.json to the directory supplied at init time.
 * Safe to call even if no overlays were captured (writes nothing).
 * Called from shutdown_runtime() in main.cpp. */
void overlay_capture_write_json(void);

/* Returns number of unique overlays captured so far. */
int overlay_capture_count(void);

/* Variant-capture automation (step 2.8): per-vblank tick that fires an
 * automatic capture + background compile when the dirty-RAM interpreter
 * shows sustained pressure inside a capture window (an uncovered variant
 * being executed) at a coherent (not-loading) moment. Enabled by main()
 * when [runtime] overlay_autocompile_cmd is configured. */
void overlay_autocapture_set_enabled(int on);
void overlay_autocapture_tick(void);
void overlay_autocapture_get_status(int *enabled, uint32_t *triggers,
                                    uint64_t *last_delta);

/* Compute CRC32 of the DMA-time bytes for the region [region_start,
 * region_start+region_size).  Zero-filled for gaps between DMA blocks,
 * exactly as overlay_captures.json bytes_b64 is assembled.  Use this
 * in overlay_loader to build a consistent DLL filename without reading
 * live RAM (which has scatter-load gap contamination). */
uint32_t overlay_capture_get_region_crc(uint32_t region_start,
                                         uint32_t region_size);

/* Generic executable-image lifecycle and backend-neutral execution ownership.
 * DMA completion is an authoritative content-instance event. Dispatch owners
 * are noted only at existing backend acquisition points; this instrumentation
 * never changes dispatch priority or validity. All IDs are process-local. */
enum {
    OVERLAY_EXEC_OWNER_UNAVAILABLE = 0,
    OVERLAY_EXEC_OWNER_STATIC_NATIVE = 1,
    OVERLAY_EXEC_OWNER_CACHED_NATIVE = 2,
    OVERLAY_EXEC_OWNER_RUNTIME_NATIVE = 3,
    OVERLAY_EXEC_OWNER_INTERPRETER = 4,
    OVERLAY_EXEC_OWNER_AMBIGUOUS = 5
};

enum {
    OVERLAY_LIFECYCLE_CREATED = 1,
    OVERLAY_LIFECYCLE_SUPERSEDED = 2,
    OVERLAY_LIFECYCLE_OWNER_ACQUIRED = 3,
    OVERLAY_LIFECYCLE_OWNER_CHANGED = 4
};

enum {
    OVERLAY_EXEC_REASON_NONE = 0,
    OVERLAY_EXEC_REASON_MAIN_COMPILED = 1,
    OVERLAY_EXEC_REASON_STATIC_COMPILED = 2,
    OVERLAY_EXEC_REASON_NATIVE_DISPATCH = 3,
    OVERLAY_EXEC_REASON_NATIVE_VALIDATION_FALLBACK = 4,
    OVERLAY_EXEC_REASON_DIRTY_INTERPRETER = 5
};

typedef struct {
    uint64_t instance_id;
    uint64_t predecessor_id;
    uint64_t successor_id;
    uint32_t lifecycle_generation;
    uint32_t capture_base;
    uint32_t known_length;
    uint32_t capture_crc32;
    uint32_t first_observed_frame;
    uint32_t last_observed_frame;
    uint32_t last_execution_frame;
    uint32_t last_execution_owner;
    uint32_t observed_owner_mask;
    int active;
} OverlayLifecycleInstance;

typedef struct {
    uint32_t phys;
    uint32_t owner;
    uint32_t first_observed_frame;
    uint32_t last_observed_frame;
    uint64_t hits;
    uint64_t instance_id;
    uint32_t registration_id;
    uint32_t reason;
    uint32_t watched_generation_at_observation;
    uint32_t instruction_word_at_observation;
} OverlayExecutionOwner;

typedef struct {
    uint64_t sequence;
    uint32_t frame;
    uint32_t kind;
    uint64_t instance_id;
    uint64_t related_instance_id;
    uint32_t base;
    uint32_t length;
    uint32_t previous_owner;
    uint32_t new_owner;
    uint32_t reason;
} OverlayLifecycleEvent;

void overlay_lifecycle_note_execution(uint32_t addr, uint32_t owner,
                                      uint32_t registration_id,
                                      uint32_t reason);
void overlay_lifecycle_set_tracking_enabled(int enabled);
int overlay_lifecycle_tracking_enabled(void);
uint32_t overlay_lifecycle_tracking_started_frame(void);
int overlay_lifecycle_instance_count(void);
int overlay_lifecycle_get_instance(int index, OverlayLifecycleInstance *out);
int overlay_lifecycle_owner_count(void);
int overlay_lifecycle_get_owner(int index, OverlayExecutionOwner *out);
int overlay_lifecycle_owner_at(uint32_t addr, OverlayExecutionOwner *out);
int overlay_lifecycle_owner_observation_current(const OverlayExecutionOwner *owner);
uint64_t overlay_lifecycle_event_latest_sequence(void);
uint64_t overlay_lifecycle_event_oldest_sequence(void);
uint32_t overlay_lifecycle_event_capacity(void);
int overlay_lifecycle_get_event(uint64_t sequence, OverlayLifecycleEvent *out);
uint64_t overlay_lifecycle_catalog_token(void);
int overlay_lifecycle_overflowed(void);

#ifdef __cplusplus
}
#endif

#endif /* OVERLAY_CAPTURE_H */
