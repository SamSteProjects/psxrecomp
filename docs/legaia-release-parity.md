# Legaia stability and release parity

Audit date: 2026-09-09. The initial pass implements runtime/precompilation
stability and input fixes from the supplied SDK prompts. The subsequent SDK
buildout adds an integrated editor, generic guarded observation protocol and
private placement-package workflow; see `FEATURE_MATRIX.md` for current limits.

## Subsequent SDK runtime validation

The generic observer port restores protocol discovery, main executable source
identity, executable registration/lifecycle catalogues, requested-PC witnesses,
scoped guards and bounded RAM-region reads from our prior SDK implementation.
It adapts the current SHA API and preserves bitmap interpreter tracking.
Strict scalar parsing rejects malformed addresses, fractions and overflow;
only physical/KSEG0/KSEG1 RAM aliases are accepted. Speculative shadow/replay
execution cannot publish witnesses. Soft reboot rotates the session identity;
restore invalidates ownership without reviving prior observations.

Source provenance includes `5874ead2` (identity), `f3e9ed62`/`f40f8dda`
(lifecycle), `340298cc`/`fd996246` (witnesses), and `7f29231f` (guards).
Executable lifecycle/bounds harnesses and the original two restore/five
pair-dedup scenarios pass after adapting their explicit fixture dependencies.
The Windows Release build and live executable hash/capability negotiation pass.
The title screen and opening story render. At those stages the field profile
correctly withholds observations for a missing required execution witness.
This is not accepted field actor traversal or a performance oracle.

The SDK's private format-6 disc-user package passed the real package parser,
installer, fresh-process selection reload and resolver, including wrong-disc
rejection. A concrete generic installer defect was fixed: parsed asset paths
retained their staging location after installation. The installer now re-reads
and validates the final manifest before publishing manager state, with rollback
on failure. The new regression fails against the old code and passes with the
fix. Runtime boot with the enabled package reaches the opening story; visible
authored actor placement remains a separate acceptance gate.

The final `mod_status` build exposes bounded plan/disc identity and actual
overlay-copy counters. In the private package run it reported the expected
fingerprint, one active overlay, matching disc SHA-256 and no guard failure.
It remained at zero copied overlay bytes during the bounded opening narrative;
that scene had not demonstrated consumption of the town01 replacement. The
later field-profile attempt rejected an execution-witness backend mismatch at
`0x801CF754`. Do not label this run accepted live field traversal or a visible
modified actor. The executable mod-runtime tests independently prove exact
sector/byte accounting, repeated reads, restore retention and reset semantics.

SDK milestones are `4d7e955f` (editor/import/project/model inspection),
`aa3b22ab` (placement package build), `bae00098` (installer final-path fix), and
`be90a25d` (guarded runtime observer and mod-consumption diagnostics). The final
MSVC validation executable is SHA-256
`bc6cf5b04cfda6fe90c0d6ee6c9e87148a540e9653ef6b39988eb01bda7e5d4a`.
Its source mapping and private run evidence are recorded in ignored
`local-output/sdk-20260909/validation-manifest.json`; it was compiled before
the final commit, so its embedded revision carries a dirty-worktree suffix.

## Source and artifact identity

- Target: `Recomp`, branch `codex/legaia-upstream-20260909`, starting commit
  `56892d6216cf1ccf87d4a376c8e0feec67ac4182` (reapplied Legaia fixes).
- Upstream base: `1a64f611`. Local release reference:
  `release-full-fixes`, `3ac7d410bf3da25f64a1e013ff8a99f7d3c694fa`.
- Recovery ref before these edits: `codex/recovery-legaia-stability-20260909`.
- Release packaging repository: `legaia-release`, commit
  `261a40d12a800a73426367f643d2267e8393db3f`. Its v0.1.7 notes identify runtime
  source `ce833027`; packaging identity is not runtime source identity.
- Known-good sibling executable: `LegaiaRecomp/build/Release/LegaiaRecomp.exe`,
  SHA-256 `CD863E57F4750AA0A22EF6B7E621E297A7228D3B948DCBB310B21F4621B72D08`.
  The sibling's prior run report identifies `v0.1.0-alpha-655-g3ba5c32`, while
  its current old vcxproj embeds `v0.1.0-alpha-725-g3c6c81f-dirty`. Newer split
  generated sources also coexist there. These files do not establish a single
  reproducible source revision for the old executable; do not equate them.
- Ghidra's existing `Legaia3.0` project was started and its active bridge
  connection verified. No disassembly or program data was changed.
- Andrew reference pin remains `d6e64c68ede25813d35db20980da82a1a025549b` as
  cited by earlier project evidence. This pass does not change that pin or
  claim new Andrew-source research. Generic fixes below are established from
  actual build/loader behavior, not inferred retail structures.

## Compatibility ledger

| Area / symptom | Release source or evidence | Current implementation and disposition | Validation in this pass / remaining acceptance |
| --- | --- | --- | --- |
| Healing Leaf / Spirit synchronous VSync deadlock | Release fix log, July 17 and August 24; release runtime `interrupts.c` | Preserved in `interrupts_service_scheduled_events`: scheduled device edges advance during exception context; interrupt delivery remains gated. Generic mechanism. | Existing CD/XA scheduling regression passes. In-battle playthrough still required. |
| Battle XA runs ahead of animation | Release `cdrom.c`, launcher enables `PSX_CD_RESPONSE_VISIBILITY_DELAY=1` | Preserved response visibility gating in `cdrom.c`; configurable build default in `runtime.cmake`. Generic mechanism with title-owned enablement. | Source contract test passes; listening and animation synchronization not revalidated. |
| Later Hyper Art loses XA | Release seek/header correction in `cdrom.c` | Preserved SeekL/SeekP reported-position refresh and realtime XA sector event behavior. Normal XA speed remains 1. | Source contract test passes; back-to-back Hyper Art playthrough still required. |
| Windows startup / C11 atomics | Reapplied `56892d62` runtime/build fixes | Preserved unbuffered streams, C11 MSVC flags, declarations/linkage and SIO initialization. Generic. | Portability test passes; fresh Windows build recorded below. |
| Pacing stalls / sleep underflow | `frame_pacing.c` and `host_time.c` match `3ac7d410` byte-for-byte | Already at release parity. Earlier 3ms sleep/spin experiment is superseded by current host timer/pacing implementation. | Executable deadline/underflow pacing test passes. No new real-time smoothness claim. |
| Short recovered hitches are undiagnosed | Release diagnostic recorder; reapplied `56892d62` | Preserved bounded heartbeat/manual/hitch records and cumulative CD/XA telemetry. Generic. | Existing always-on capture test passes. |
| First clean static-overlay build fails to link | Actual CMake/Ninja reproduction: configure glob sees no generated part files | Fixed `runtime.cmake` plus `psx_static_overlay_parts.cmake`: fixed wrapper sources discover parts after dispatcher codegen. Generic. | Clean build, grow/shrink, split/monolithic switches, and 35 namespaced images compile and execute in synthetic fixture. |
| Body-only overlay regeneration links stale objects | Actual Ninja restat reproduction | Fixed `write_static_outputs` in `tools/compile_overlays.py`: dispatcher timestamp signals changed parts; wrapper hashes invalidate affected objects. Generic. | Body-only mutation changes executable result in the build regression. |
| Restore reuses stale ownership or retains negative owner memo | Real loader/DLL fixture reproduces stale native call under generation collision | Fixed `overlay_loader_resync_validation_after_restore`: explicit unvalidated state, clear manifest/negative/range/static memos, retain semantic/self-modification blacklists. No DLL unloading or new dynamic-cache enablement. Generic. | Entry and CPS continuation tests reject stale bytes and regain native execution after repeated restores. This fixes the demonstrated class; the reported retail savestate performance issue still needs in-game measurement. |
| Debug injection cannot select PSX port 2 | Historical SDK input API; current SDL/SIO already supports two ports | Port-selectable debug input, default port 1, bounded validation and release/neutralization; normal input sampled on unaffected ports. Generic. | Focused protocol/routing tests and fresh build; physical controller test remains manual. |
| Stale same-address static overlay | Existing static match/range validation and watched-generation checks | Preserved. Restored memory explicitly invalidates static match cache. | Existing inactive-loader guard passes; runtime-native same-address replacement fixture passes. Retail field transition remains manual. |
| Muscle Dome loss-return TMD pointer crash | `docs/legaia-fix-log.md` records a title-owned relocation before `FUN_80024D78` via `FUN_800268DC` | **Documented claim absent from the proven reference binary function.** Current generated function also lacks the guard; no tracked implementation recovered. See investigation below. | Recover original title-layer patch or independently establish the defect and correct layer against the retail engine. No unverified patch ported; not claimed fixed. |

### Muscle Dome relocation provenance investigation (2026-09-09)

The original July 18 commit `c44d0e24b3ddf9fd0f8afc3dbc56dbc4ce06632c`
adds the relocation claim to `docs/legaia-fix-log.md`, but its implementation
diff in `runtime/src/main.cpp` concerns developer-menu input and fishing entry.
It does not implement the described TMD guard. Narrow all-ref pickaxe searches
over owned C/C++/Python sources found no implementation containing either
`80024D78` or `800268DC`. Current sibling generated source
`LegaiaRecomp/generated/SCUS_942.54_full_05.c:15091` enters the original actor
resource lookup after normal continuation/timing instrumentation.

The retained reference build provides stronger evidence than its mixed source
timestamps:

- Reference executable: `C:\Users\sammo\OneDrive\Documents\LegaiaRecomp\build\Release\LegaiaRecomp.exe`,
  SHA-256 `cd863e57f4750aa0a22ef6b7e621e297a7228d3b948dcbb310b21f4621b72d08`.
- Retained object: `C:\Users\sammo\OneDrive\Documents\LegaiaRecomp\build\psx-runtime.dir\Release\SCUS_942.54_full.obj`,
  SHA-256 `aa79f2969fc567a57bf8d6da108638a3f879da131f097ca23f87b5ebde880441`.
- COFF symbol `func_80024D78` belongs to section 298, whose raw body starts at
  object offset `0x17C32B` and spans 2,967 bytes. Its unique initial 64-byte
  signature occurs at executable file offset `0x5EA740`. Comparing all 2,967
  bytes while masking the 240 bytes described by COFF linker relocations found
  **zero other mismatches**. This ties the inspected object function to the
  actual retained executable, without inferring a whole-build source revision.
- Its relocation targets comprise timing, guest-load, debug-entry and store-PC
  helpers. There is no call target for `func_800268DC` or a TMD validation helper.
  Native disassembly enters the original actor `+0x64` lookup after ordinary
  instrumentation; no TMD-header validation/relocation prologue was found.

Fresh read-only Ghidra calls against program `SCUS_942.54` confirm the retail
mechanisms, using exact addresses because the functions have descriptive names:
`80024D78` (`InitItemPointerTableFromResourceIndex`) selects
`0x8007C018[actor+0x64]`, reads its object count at `+8`, and builds the actor's
`+0x44` table from descriptors beginning at TMD `+0x0C`. It does not call a
relocator. `800268DC` (`relocate_packed_table_entries_once`) checks whether
TMD `+4` equals 1; otherwise it sets that flag and rebases descriptor fields
`+0`, `+8`, and `+0x10` by masking their low two bits and adding TMD `+0x0C`.
The descriptors are `0x1C` bytes each. Its identified retail caller is
`80026B4C` (`Model_RegisterAndInit`), which validates header `0x80000002` before
registration and relocation. The actor-table builder's identified caller is
`80020F88` (`Actor_LoadOrRefreshStateFromResource`).

This establishes that the documented extra guard is absent from the inspected
reference function, **not** that every possible external runtime hook has been
disproved or that a fresh Muscle Dome failure has been reproduced. No source
patch with sufficient provenance was recovered, and none was ported. A future
title-owned repair must first establish the failing lifecycle and compare it
with the retail engine. Existing trusted function-entry plugin infrastructure
(`mod_plugins.h` and `[recompiler] mod_function_entry_funcs`) offers an explicit
integration boundary if a title repair is justified; it is not evidence that
this repair already exists. Generic runtime address checks and direct edits to
generated C remain inappropriate substitutes.

## Overlay inventory and project boundaries

The sibling static capture generator and both current static/merged manifests
contain the ten intended roles: 0897, 0898, 0900, 0967, 0970, 0971, 0972, 0975,
0976, 0980. Capture 0899 remains excluded. Numbered translation-unit count is
not capture count. MAPDSIP is not claimed to have complete static coverage.
Both current normal game TOMLs disable dynamic caching; this pass does not
enable it. Historical v0.1.7 dynamic-cache playtest packaging is a distinct
configuration and does not override that policy.

The sibling CMake file still has project-level issues outside the writable
target: main codegen omits the recompiler executable from `DEPENDS`; overlay
codegen omits the TOML input; generated outputs are shared across build trees.
Its newer cache also enables optional menu-runtime capture, although the
currently inspected merged manifest contains only the ten static roles.
Do not infer actual compiled coverage from that cached option alone.
The sibling, its known-good executable, private assets, saves and previous
builds were preserved. No proprietary payload is part of these source changes.

## Validation record

Completed focused checks:

- `runtime/tests/test_overlay_restore_runtime.py`: real loader plus synthetic
  DLL; stale-call reproduction failed before the fix, entry/continuation pass
  after it. Generation collision, repeated restore, native recovery and warm
  reuse are exercised.
- `runtime/tests/test_overlay_pair_dedup_runtime.py`: five executable scenarios
  pass. Updated its harness for current callbacks and configuration/flavor cache
  identity; unrelated fixture callbacks abort on unexpected use.
- `tools/tests/test_static_overlay_build.py`: executable CMake/Ninja inventory
  regression, including repeated helper names and more than 32 images.
- Existing static-split, CD/XA callback, always-on hitch, MSVC portability,
  overlay initialization and executable frame-pacing checks pass.

Fresh Windows validation completed using MSVC 19.50 / Visual Studio 18, SDL3,
Release configuration and two build workers. A separate local project reads
the existing generated game/BIOS inputs and never runs the sibling project's
codegen. Git Bash avoided the Windows `PATH`/`Path` compiler-detection collision.
Dependencies were reused offline. CMake warned about stale unused OpenBIOS
generation metadata; the linked BIOS backend is SCPH1001. Vulkan SDK tools are
absent, so this is a software-renderer validation, not Vulkan acceptance.

Artifact: `local-output/stability-20260909/build/Release/LegaiaStability.exe`,
SHA-256 `FCFB92BC55B3CE5DA0B2AFEE8D18B14462B49D101C2EDA75598C9670434A9121`.
The tested artifact embeds `nightly-1-g56892d62-dirty`: it was built with this
patch set before commit, not from an unchanged `56892d62`. The private local
validation manifest records source hashes independently of that display label.

The bounded live run used shipping HLE boot with LLE fallback, software video,
CD response delay enabled, normal XA speed, port 4387, and separate temporary
saves. It reached frame 2720 and exited normally via TCP quit (exit code 0).
Live checks verified port-2 injection, port-1 isolation, malformed-port
rejection without state mutation, and neutralization/disconnection on release.
Audio telemetry recorded 1,169,375 nonzero host frames with active output;
CD/XA decoding advanced. This establishes audio data reaching the host output,
not listening quality or battle synchronization. Audio telemetry also recorded
53,655 overflow drops; no audio-continuity or performance acceptance is claimed.

Early and later one-shot screenshots were blank (white and black respectively).
There is therefore **no visual gameplay/FMVs acceptance** from this smoke run.
The initial smoke harness incorrectly reused a socket against the runtime's
one-request-per-connection transport; correcting that harness made the protocol
checks pass. The runtime was advancing throughout. Local smoke results, build
logs and screenshot are under `local-output/stability-20260909/` and are ignored.

Source tests and this startup smoke do not establish smooth FMVs, safe Muscle
Dome return, or town0c/map01 performance. Savestate-restored runs remain
unsuitable as performance truth until the retail comparison below passes.

## Remaining targeted acceptance

| Priority | Check | Fixture / platform | Acceptance |
| --- | --- | --- | --- |
| P0 | Restore/replacement matrix | Synthetic loader; Windows and Linux | Positive/negative owner decisions revalidate, quarantines persist, stale native body never executes; static and dynamic owners covered. |
| P0 | Savestate file failure integrity | Synthetic whole-machine snapshots | Truncated/malformed sections cannot leave a partly applied runnable machine. Current serializer needs separate transactional validation work. |
| P0 | Muscle Dome relocation | Authorized retail input; Windows | Recover title patch, prove idempotent relocation and finish loss/win return paths. |
| P1 | Fresh vs restored same scene | Authorized retail input; Windows | Compare native/interpreted instructions and frame timings after restore and return; no restore-only sustained fallback. |
| P1 | CD/XA battle sequence | Authorized retail input; Windows; manual audio | Healing Leaf, Spirit, two Hyper Arts and summon finish with synchronized audible audio. |
| P1 | FMV and field transitions | Authorized retail input; Windows | Cold-process FMV, town0c -> map01 -> town0c; current build identity, ownership and timing captured. |
| P1 | Controller release and isolation | Keyboard plus two physical pads | Inject each port, expire/clear/switch it; unaffected port remains responsive and physical input resumes. |
| P2 | Other build generators | Synthetic generated source; MSVC/Make/Ninja | First-build and inventory/body regeneration produce the same executable behavior. |
