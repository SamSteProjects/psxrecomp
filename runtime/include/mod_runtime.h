#pragma once

#include <stdint.h>

#ifdef __cplusplus
#include <filesystem>
#include <string>
#include <memory>
namespace PS1 { class ISOReader; }
#if defined(RECOMP_LAUNCHER)
#include "recomp_launcher.h"
#endif

namespace PSXRecompV4 {

bool mod_runtime_initialize(const std::filesystem::path& root,
                            const std::string& game_id,
                            uint32_t game_entry_pc,
                            const std::filesystem::path& exe_path = {},
                            std::string* error = nullptr);
bool mod_runtime_commit(const std::filesystem::path& disc_path = {},
                        std::string* error = nullptr);
/* Drop the in-session mod plan for a netplay launch without rewriting the
 * user's persisted offline selection on disk. Netplay is always vanilla for
 * now (no synced mod plans). */
bool mod_runtime_clear_for_netplay(std::string* error = nullptr);
const std::string& mod_runtime_fingerprint();
const std::filesystem::path& mod_runtime_effective_disc_path();
// Open the committed relocation reader, or a stock reader when no relocation is active.
// Retained handles must check current ownership before each read.
bool mod_runtime_open_iso_reader(const std::filesystem::path& path,
    std::shared_ptr<PS1::ISOReader>& reader, std::string* error = nullptr);
bool mod_runtime_iso_reader_current(const std::shared_ptr<PS1::ISOReader>& reader);

#if defined(RECOMP_LAUNCHER)
const ::RecompLauncherCModProvider* mod_runtime_launcher_provider();
#endif

} // namespace PSXRecompV4
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Bounded, read-only snapshot. Read on the runtime thread, like disc patching.
 * Counters measure actual overlay memcpy work, including repeated reads and
 * replay. They reset on initialize, successful commit and clear, never rewind
 * with guest savestates, and do not claim unique sectors or guest execution. */
typedef struct ModRuntimeStatus {
    uint32_t initialized;
    uint32_t plan_committed;
    uint32_t main_applied;
    uint32_t disc_enabled;
    uint32_t disc_guard_failed;
    uint64_t active_write_count;
    uint64_t active_overlay_count;
    uint64_t counter_epoch;
    uint64_t overlay_sector_applications;
    uint64_t overlay_bytes_copied;
    uint32_t has_last_overlay_lba;
    uint32_t last_overlay_lba;
    char plan_fingerprint[65];
    char disc_sha256[65]; /* Committed source-disc identity; empty if unavailable. */
} ModRuntimeStatus;
void mod_runtime_get_status(ModRuntimeStatus* out);

/* Called before a guest dispatch. Applies the complete main-EXE plan
 * transactionally on the first dispatch to the configured entry point. */
void mod_runtime_on_dispatch(uint32_t target);
/* A full-machine savestate restores guest RAM after the initial entry-point
 * application. Reapply the already-validated main-EXE plan so the current
 * enabled mod selection remains authoritative after the restore. */
void mod_runtime_on_savestate_loaded(void);
/* Invokes activation callbacks for the committed plan. Call after the final
 * launcher commit and before renderer/window initialization. */
void mod_runtime_activate_plugins(void);
void mod_runtime_on_vblank(void);
void mod_runtime_patch_disc_sector(uint32_t lba, int raw_sector,
                                   uint8_t* bytes, uint32_t size);
void mod_runtime_enable_disc_patches(void);

#ifdef __cplusplus
}
#endif
