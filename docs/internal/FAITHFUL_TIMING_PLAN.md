# Faithful Timing Core — Game Plan (psxrecomp)

**READ THIS EACH SESSION.** Referenced from CLAUDE.md Rule -1 and from the
auto-memory ([[psxrecomp-build-faithful-core-not-hacks]],
[[precise_irq_slice_state]]). This is the authoritative plan; update the
"Status / Log" section every session.

---

## 0. North star + guardrails (non-negotiable)

Build the **faithful hardware-timing core** of the static recompiler. The PSX
recompiler is being BUILT, not preserved:

- The correct fix is ALWAYS the faithful, class-level core — NEVER a surgical
  per-game patch, symptom workaround, `game.toml` hack, or "make native agree
  with interp even if both are fake."
- Breaking other titles is acceptable; they were built on a faulty ecosystem and
  will be **regenerated**. Backward-compat is NOT a constraint.
- No stubs, no HLE, no interpreter-as-fallback (Architecture A locked). Fix the
  recompiler/runtime and regenerate; never edit `generated/*.c`.
- Don't guess (PRINCIPLES). Confirm every mechanism with the oracle + rings
  BEFORE changing code. Build observability first.
- Confer with ChatGPT via the **Chrome MCP browser at chatgpt.com** — the
  existing "PSX Static Recompiler Debug" chat (the user has Plus logged in).
  NOT the `codex` CLI (usage-limited).

## 1. The problem (diagnosis, confirmed)

A static recompiler charges cycles **block-granular** (instruction count up front
at each block leader) and checks IRQs at **block edges**. Real HW and the
sanctioned dirty-RAM interpreter have a **per-instruction** cycle timeline and
take IRQs at the exact instruction. Games that read timers / poll IRQ-driven
flags in tight loops fork between backends.

Tomba 2 (SCUS-94454) logo→FMV stall is the canonical case. The cascade:
1. Timer1 debounce value-fork @ pc 0x8008592C (frame 1823) — fixed by exact block
   cycle costs ("Fix A", already in tree).
2. **CURRENT BLOCKER:** measured **−8 cycle drift** (native BEHIND interp),
   entering in the BIOS→overlay init transition (func 0x80050B0C subtree). The
   frame-1824 logo-delay wait loop (caller 0x8008AE48 → RCnt reader 0x80085900;
   exits when *0x80102748[=960] < elapsed Timer1) loops ~1557× in interp (reaches
   FMV) vs ~42× native (stuck on logo).
   **Mechanism (located in code_generator.cpp):** when a branch's delay slot is
   ALSO a block leader (`exit_has_delay && !delay_slot_in_block`, ~line 1243), the
   branch block's `instruction_count` excludes the delay slot; on the TAKEN path
   the delay-slot clone runs but its cycle is charged by neither the branch block
   nor the (unentered) delay-slot block → undercount 1/site. ~8 sites = −8.
3. Interrupt take-point granularity (block-edge vs exact instruction) — the
   "precise IRQ slicing" track. PARKED (default off); it is a later correctness
   upgrade, NOT the FMV blocker. Validated design exists (block-leader
   continuations); see §5.

## 2. The target architecture (what "faithful core" means)

Per ChatGPT (validated) + standard practice:
- ONE shared **per-instruction cycle-cost function** `psx_instr_base_cycles(pc,
  insn)` used by BOTH the dirty-interp and the recompiler. No two approximate
  models.
- Recompiler emits **exact** accumulated cycle charges (collapses to a constant
  per pure-compute block); every dynamically executed instruction charged exactly
  once; delay slots owned by the branch bundle.
- **Segmented charge** before any guest-visible time observation (MMIO read/write
  to timers/GPUSTAT/SPUSTAT/DMA/CD/I_STAT/I_MASK, BIOS/device calls, backedges,
  calls/returns) so native and interp observe devices at the same architectural
  boundary.
- **Timers derived on-demand** from a global guest-cycle counter at read time;
  DMA/CD/GPU/IRQ on **scheduled event deadlines** (not per-cycle ticking) so
  compiled stays fast.
- Invariant: *every execution backend may differ in host implementation, but not
  in guest-visible time.* At same-PC convergence points, native cycle total ==
  interp cycle total.
- pc=0 means ONLY a real guest pc=0 / explicit termination — NEVER "dispatcher
  couldn't re-enter." Fail closed + log on undispatchable PCs.

## 3. Phased plan (each phase: confirm → build → regen → run → measure → screenshot)

- **P1 — Cycle-audit observability.** Add a per-function/at-convergence cycle
  audit: record native vs interp cumulative guest cycles at same-PC points; expose
  via TCP/ring. SUCCESS: reproduces the flat −8 and pinpoints the entering site(s).
- **P2 — Delay-slot cycle ownership (the −8).** Fix in code_generator.cpp: branch
  bundle charges its delay slot; not-taken fallthrough → branch_pc+8 (not the
  delay-slot leader); delay-slot-as-standalone-leader charges itself; no
  double-count on the not-taken path. SUCCESS: audit shows −8 → 0; Tomba 2 reaches
  the intro FMV (screenshot). Likely the FMV unblock.
- **P3 — Shared per-instruction cost function.** Single `psx_instr_base_cycles`
  consumed by both backends; recompiler emits exact accumulated charges with
  MMIO/boundary segmentation. SUCCESS: first-divergence hashes identical past frame
  1824 across a longer run; audit stays 0.
- **P4 — On-demand timers + event deadlines.** Timer1/2/0 computed from global
  cycle counter at read; devices on scheduled deadlines. SUCCESS: no perf
  regression; timing-sensitive paths stable.
- **P5 — Precise take-points (fold in parked work).** Re-enable slicing; emit
  EVERY block leader as a CPS continuation (global dispatch → owning func w/
  cpu->pc; never a new entry; fail-closed on undispatchable). SUCCESS: exact-
  instruction IRQ delivery with bounded (one-block) hand-back.
- **P6 — Regression + faithfulness.** Regen + screenshot-smoke ALL titles (BIOS,
  Tomba 1, MMX6, Ape, Tomba 2); delete Tomba2 `overlay_native_block` (must still
  reach FMV/title); calibrate the shared model against Beetle/psx-spx. Pin bump is
  user-gated.

## 3b. Cycle-cost model SOURCE (no clean-room needed — transcribe + verify)

The HW-intended cycle model is documented AND available as reference source we
already have in-tree (our oracle's own code). Stage-2 = transcribe the NUMBERS
(facts, not GPL-protected expression; also in psx-spx) into OUR shared cost
function, then VERIFY each against Beetle at runtime. Do NOT paste Beetle code
(architecture differs + GPLv2 hygiene); write our own informed by the facts.

Extraction map — `psxrecomp/beetle-psx/mednafen/psx/` (main checkout):
- **CPU base / instruction fetch:** cpu.cpp `ReadInstruction()` (~L534) — icache
  model: `timestamp += 4` cache-disabled (0xA000_0000+), `+3` on cache miss/fill,
  `+1` per fill word, near-0 on hit. For a static recompiler this becomes a
  per-block fetch-cost constant (assume cache-enabled steady state; calibrate).
- **Memory wait-states:** cpu.cpp `ReadMemory()` (~L365) / `WriteMemory()` (~L454)
  — `timestamp += (ReadFudge>>4)&2`, the `lts` delta from `PSX_MemRead*` is the
  region wait-state; `LDAbsorb = lts - timestamp` is the load-delay absorb. Charge
  in OUR psx_read/write path by region (RAM fast, BIOS ROM slow, scratchpad fast,
  MMIO per-device). Split clean from CPU base (don't double-count).
- **Mult/Div latency:** cpu.cpp `MULT_Tab24` (~L101), `muldiv_ts_done` (~L154) —
  mult/div set a completion timestamp; a later MFHI/MFLO stalls until then. Model
  as a documented latency (mult ~6-13 by operand magnitude via MULT_Tab; div/divu
  ~36). Encode as instruction cost + optional stall-on-read.
- **GTE/COP2 per-command cycles:** gte.cpp `GTE_Instruction()` (L1713) returns the
  count via each op fn (DPCS/MVMVA/NCDS/…). Well-known table (also psx-spx):
  RTPS=15 RTPT=23 MVMVA=8 SQR=5 OP=6 AVSZ3=5 AVSZ4=6 NCLIP=8 NCDS=19 NCDT=44
  NCCS=17 NCCT=39 NCS=14 NCT=30 CC=11 CCS? CDP=13 DPCS=8 DPCT=17 DCPL=8 INTPL=8
  GPF=5 GPL=5 (verify each against gte.cpp op-fn returns + psx-spx before use).
- **Timers (already partly faithful):** timer.cpp — divider ratios already used
  (T1 hblank ÷2146 etc.); move to on-demand counter = f(global cycles) at read.

Build order for the model (P3 → Stage-2):
1. Shared header (single source of truth) consumed by interp (runtime) AND
   recompiler (it already includes ../../runtime/include/*.h): identity first
   (cost=1) → regen → prove byte-identical generated cycle charges (zero behaviour
   change) → seam established.
2. Fill real costs from the extraction map, ONE component at a time, each verified
   against Beetle at runtime (native cumulative cycles == Beetle at convergence).
3. Memory wait-states in the psx_read/write path (region table).
DO each transcription with the Beetle source open + a runtime cross-check; a wrong
cycle number CREATES divergence, so verify, don't rush.

## 3c. STAGE 2 — full hardware cycle accuracy (the goal; -8 is DONE/past)

The -8 was backend-disagreement (native vs our interp); FIXED (FMV reached). Stage 2
makes the cycle model match REAL R3000A timing, validated against Beetle. We are NOT
hardware-cycle-accurate yet: model is ~1 cycle/instruction; Beetle charges ~2x.

### The validation breakthrough: DELTA comparison (offset-independent)
Absolute-cycle comparison through boot is meaningless (native is ~121M cycles off
Beetle due to turbo-loads/overlay load-model differences). BUT the cyc_watch
comparator's per-hit DELTAS cancel that offset: between two consecutive hits of the
same anchor (one iteration of identical code), native charged 46 cycles vs Beetle 91
(@0x80017FC4). That ~2x gap IS the cycle-model inaccuracy, measured cleanly. So:
  VALIDATE STAGE 2 BY MATCHING native Δcycles == Beetle Δcycles over identical
  regions (consecutive same-anchor hits, or entry/exit anchor pairs), NOT absolute.
First concrete target: make the 0x80017FC4 inter-hit Δ 46 -> 91 (== Beetle).

### Stage-2 progress log
- #1a data-load cost DONE (2ef47bd): psx_instr_base_cycles +2 per CPU load (LWC2 +1).
  Δ gate @0x80017FC4: native per-iter 46 -> 56 (Beetle 91). FMV still streams (no
  regression). Closed ~10/45. Approximation: no scratchpad-free / region / load-delay
  ABSORB yet — those are refinements (absorb would LOWER native, so it's not the
  remaining 35; the remaining gap is other components below).
- REMAINING ~35 cyc: DISASSEMBLED func_80017FC4 — it is only loads/stores/ALU/branches
  + a countdown delay loop; NO mult/div/GTE/MMIO. So the gap is NOT those, for this fn.
  BUT func_80017FC4 exits via a CPS TAIL-CALL to 0x8001EFFC (no normal return), so the
  single-anchor entry-to-next-entry window SPANS MULTIPLE functions (80017FC4 ->
  8001EFFC -> ... -> re-call). => single-anchor Δ is TOO COARSE for per-component
  attribution; the 56/91 covers code we haven't disassembled.
- TOOLING NEXT (before more cost components): add a TWO-ANCHOR region mode to cyc_watch
  (capture cycles at region START anchor A and END anchor B; report Δ(B−A) per pass) on
  BOTH backends. Then validate the cost model on a KNOWN, fully-disassembled single
  code path (no calls/loops crossing out) — e.g. a leaf function entry→its terminator.
  That gives rigorous per-component attribution instead of an opaque multi-fn window.
  Only then resume adding components (fetch / mult-div-stall / GTE / load-absorb).

### Components to transcribe (from in-tree Beetle + psx-spx; verify each by Δ)
The ~2x gap is dominated by what 1/insn ignores. Implement one at a time, re-measure Δ:
1. **Memory access wait-states (biggest lever).** Real loads/stores cost >1 cycle by
   region (RAM/BIOS-ROM/scratchpad/MMIO). Beetle: cpu.cpp ReadMemory `lts` delta +
   LDAbsorb (load-delay). Charge in the load/store path: interp exec_one's mem ops AND
   the recompiler-emitted cpu->read/write (or a per-load/store charge). Region table.
2. **Instruction fetch / I-cache timing.** Beetle ReadInstruction (+1 hit / +fill on
   miss). For the recompiler, fold a per-block fetch-cost constant.
3. **Mult/Div latency.** Beetle MULT_Tab/muldiv_ts_done: mult ~6-13, div ~36, stall on
   HI/LO read. Encode in psx_instr_base_cycles (+ optional stall-on-read).
4. **GTE/COP2 per-command.** Beetle gte.cpp GTE_Instruction table (RTPS=15, NCDS=19,
   NCDT=44, ...). Encode in psx_instr_base_cycles for COP2 ops.
All land in the single-source psx_instr_base_cycles (opcode costs) + a memory-path
wait-state charger (address-dependent). Both backends consume the same model (seam
already in place). Each component: transcribe -> regen/build -> Δ-compare vs Beetle
on a fixed region -> next.

### Caveats
- Δ-region must be IDENTICAL code on both (a tight loop body, or a pure-compute
  function). Avoid regions that cross turbo-load / overlay / dirty boundaries.
- Relocated BIOS-shell funcs (phys 0x30000-0x5AFFF) dispatch at a different native
  phys — anchor on game-text / BIOS-ROM, or the relocated phys.
- This is a multi-component effort; do it methodically, one validated component at a
  time. The comparator (cyc_watch + cycle_compare.py) is the validation backbone.

## 4. Tooling / oracle
- Runtime TCP port 4500; Beetle oracle 4382. Always-on rings: `event_ring`,
  `wtrace_all` (write trace; `newest=1`). `freeze_check` has slice-trace + cycle
  fields. `PSX_EXIT_HALT=1` halts-and-serves at the pc=0 exit for post-mortem.
- Build runtime: `cmake --build Tomba2Recomp/build-t2 --target psx-runtime`
  (PATH=/c/msys64/mingw64/bin). Recompiler: `cmake --build
  _wt-tomba2/psxrecomp/recompiler/build-t2 --target psxrecomp-game`. Regen:
  `recompiler/build-t2/psxrecomp-game.exe --config game.toml` (rebuild tool first).
- Reference: nocash psx-spx; the dirty-RAM interp is the in-process oracle for
  compiled code; Beetle is the HW oracle.

## 5. Status / Log (update every session)

### 2026-09-12 — Shared placed-scenery handles and regression completion

- Previous turn made verified implementation progress. Re-polled its existing discovery process to terminal exit 0: all 344 retail-enabled SDK tests passed in 140.705 seconds. Log: local-output/sdk-20260909/sdk-suite-recheck-20260912.log. This is SDK regression evidence, not runtime or full-goal acceptance.
- Added explicit Inspector activation for shared placed-scenery X/Z handles, using source-qualified environment commands and signed source offsets. Activation expires when project/source identity changes; retail/live/stale previews remain guarded. Decoration handles retain individual scope.
- Actual browser drag on Dolk2 cell01442/record133 moved X by33 units, preserved Z and368 unrelated instances, invalidated handle activation after mutation, and Undo restored the exact preview. The selected record has one visible instance, so multi-instance drag browser acceptance remains open. Private evidence: local-output/sdk-20260909/shared-scenery-handles-check.json. No page errors; JS syntax and whitespace checks passed. No game launched or project saved by this check.
- Gameplay stays deferred; broader SDK work and full objective remain active.


### 2026-09-12 — SDK regression sweep and continuous top-view orbit

- Previous turn was verified progress (retail/authored movement overlays). This turn removed the first-drag camera pitch snap from Top view. Real browser drags preserve top pitch on horizontal movement and change it by exactly 0.02 radians for four upward pixels, without mutation commands or page errors. Private evidence: local-output/sdk-20260909/camera-top-orbit-check.json.
- Retail-enabled discovery ran 344 tests in 129.688 seconds with two failures and two errors. Fixed missing shared-animation/world-map synthetic loader mocks, aligned the stale HTTP flag count with the independently tested 1249-reference catalog, and replaced the empty animation clip-choice error with an explicit unsupported-preview explanation.
- All seven affected tests passed in 13.966 seconds. Full discovery recheck started with output at local-output/sdk-20260909/sdk-suite-recheck-20260912.log; final result still pending at this checkpoint. No game launched; manual verification remains deferred. Full SDK goal remains active.


### 2026-09-12 — Retail/authored movement target viewport layers

- Added explicit source/effective target layers, source-key invalidation and verified-report gating. NPC_RUN effective parked status is recomputed separately from the immutable imported status.
- Seven focused movement project/serializer tests passed. Actual Dolk2 browser comparison confirmed retail X9280 versus saved authored X9408, two unchanged targets, partial partition-2 authored preview disabled, zero browser errors and zero mutation commands. Authored screenshot inspected; evidence remains private under local-output/sdk-20260909/movement-overlay-layers-20260912.
- No game launched. Gameplay remains deferred in the verification queue; broader SDK goal stays active and offline work remains.


### 2026-09-12 — Streaming and experimental disc movement composition

- Connected ScriptMovement to streaming and descriptor draft preparation, including verified rebasing after NPC append and separate movement_changes audits. Existing layout, source preimage, word padding, PROT rebuild and final disc readback guards remain in force. Export-history summaries now identify Script movement without exposing script payloads.
- Fresh multi-scene project exported Dolk2 actor0002 MOVE_TO X9408 plus town01 actor0011 NPC_RUN X9728 and one Dolk2 donor0001 NPC at X64/Z16320. Selected the donor's source scene before creating the draft after an initial fixture correctly rejected a cross-scene donor. No production validation was weakened.
- Completed export: `local-output/sdk-20260909/movement-disc-20260912/Export/draft.bin`;466716768bytes; SHA2562b9a12bdffbaebf93941623e35b3ba5afc77157ae2b2e35ab3c8fb6e20faccce. Reopened PROT matched the rebuilt archive. Saved project and Inputs snapshot retain both overrides and the draft. Dolk2 target rebased7492->7495; town01 retained7948. Completed report.json contains both movement audits; gameplay_verified remains false.
- Seven focused export/serializer/merge tests passed before the export-history category update; three focused history tests also passed, followed by JavaScript syntax/diff checks. Added the private combined package to the deferred gameplay queue. This verifies composition and disc readback, not trigger execution, scheduling, donor behavior or runtime rendering. Effective target overlays and manual gameplay acceptance remain outstanding. Full SDK goal remains incomplete.


### 2026-09-12 — Movement edits after MAN actor append

- MovementAuthoringContext.patch_appended now relocates each original owner by partition/record identity, rechecks unique extent and decoded instruction layout, verifies the coordinate preimage and patches only its rebased bytes. Candidate dispatch context is recorded separately from source context; appended donor records remain untouched. This helper expects an independently validated append candidate, not an arbitrary replacement MAN.
- Five focused serializer/merge tests passed, including donor-copy preservation, no-op identity, changed-preimage rejection and altered-opcode rejection.
- Fresh retail append checks: Dolk2 actor0002 target offset7492 rebased to7495 and X9408; town01 actor0011 offset7948 rebased to7951 and X9728. Each changed exactly one candidate byte, retained all other candidate bytes and preserved the complete appended MAN layout. Private outputs and hashes: `local-output/sdk-20260909/movement-appended-20260912/retail-check.json` and two edited MAN files.
- No game launched. This closes the append-aware serializer step; wiring it into streaming/experimental disc composition, effective target overlays and gameplay verification remain outstanding. Full SDK goal remains incomplete.


### 2026-09-12 — Descriptor MAN movement Build integration

- Build now collects ScriptMovement edits, verifies source-owner membership and requested encoded coordinates, merges audited X/Z bytes with other supported descriptor MAN edits and serializes within original LZS capacity. Rejects conflicting, unaudited, wrong-owner or wrong-request bytes. Reports movement world coordinates and stable instruction IDs separately from initial actor placement. Package description identifies movement edits and retains unverified runtime status.
- Fresh town01 project combines actor0011 initial X2880->128 with NPC_RUN PC0x23 target X9664->9728. Built one24894-byte MAN overlay; opening the emitted psxmod and decompressing its actual payload reproduced exactly the two audited byte changes. Byte7948=203 independently resolves X9728. Package SHA25685cf0202a129ad3fe176830c14d016382a17f9ac52a17f5f5b7ac6a107c8da84; no runtime launch.
- Private saved project/package and evidence: `local-output/sdk-20260909/movement-build-20260912/{project.legaia.json,build-check.json,package-verification.json}`. Initial build-check used the earlier raw-byte report presentation; package-verification includes the corrected world-coordinate report from the same emitted audit. Payload identity is unchanged.
- Four focused movement/transition merge and project checks passed; wrong requested coordinates, overlapping prior spans, unaudited bytes and wrong owners reject. JavaScript syntax/diff checks passed. Streaming/appended MAN packaging, experimental disc integration, effective viewport overlays and gameplay acceptance remain outstanding. Full SDK goal remains incomplete.


### 2026-09-12 — Script movement editor controls

- Script inspector now exposes verified movement targets with retail/authored/effective X/Z, Apply, Clear and Discard. Exact64-unit form validation, source-key/owner guards and existing script draft management preserve command ownership. Pending drafts disable project history/save controls until applied or discarded. Unsupported target records retain reasons and unresolved override clearing.
- Browser workflow on the isolated Dolk2 project: rejected X65, discarded to9344, applied9408, Undo9344/Redo9408, saved and reloaded, cleared to retail9280 and undid Clear. Z10816 and retail X9280 remain distinct. No browser errors. A separate ProjectService disk reopen confirmed saved X9408. The private project intentionally retains this review edit.
- Screenshot visually inspected: `local-output/sdk-20260909/movement-editor-20260912/authored.png`; browser harness/results in the same folder. JavaScript syntax and diff checks passed. Temporary browser/editor server stopped; no game launched.
- The UI explicitly states that the instruction table/target overlay still show retail source coordinates and playable Build integration is pending. Composed packaging, effective target overlays and gameplay acceptance remain required; full SDK work remains incomplete.


### 2026-09-12 — Movement authoring service integration

- Actor, partition-2 and trigger script responses now include movement_authoring options using server-verified owner identities. Unsupported records retain their read-only script inspection and clearable unresolved override IDs. Actor movement reporting is independent of dialogue-authoring failures.
- Added strict HTTP command shapes for set_movement_target / clear_movement_target; client-provided source offsets, extra fields and invalid identities are rejected before dispatch. Exact coordinate validation and source membership remain in the project/serializer layer.
- Six focused HTTP/project checks passed with the retail disc configured. Actual Dolk2 actor0002 report/edit/report confirmed retail X9280 and effective X9344; HTTP Undo/Redo/Clear passed. Invalid65, boolean coordinates, null identities and injected source offsets returned400. Dolk2 partition-2 script0007 retained decoded instructions while its unsupported authoring report stayed disabled. Existing town01/Dolk2 transition HTTP workflows passed as regressions. Temporary servers shut down and joined.
- No gameplay launched. Editor authoring controls and composed Build/disc integration remain outstanding, and playable Build continues explicitly rejecting saved ScriptMovement edits. Full SDK goal remains incomplete.


### 2026-09-12 — Script movement project commands and persistence

- Added a separate ScriptMovement component with set_movement_target / clear_movement_target commands, immutable retail/authored/effective target layers, undo/redo, offline schema validation and save/reopen. Source owner/PC membership and serializer constraints are freshly checked before applying edits; clearing remains possible offline. Actor and partition-2 authored asset summaries now include movement targets.
- Playable Build explicitly rejects this component while composition support is pending, preventing silent omission. Editor controls, HTTP report integration, composed MAN packaging and appended-record handling remain outstanding.
-14 focused project/movement/transition/workflow tests passed. Fresh isolated Dolk2 project changed actor0002 PC0x27 X9280->9344 while retaining imported X9280 and Z10816; Undo/Redo, save/reopen, Clear/Undo and unchanged imported metadata passed. Build returned the explicit pending-integration error without generating a package.
- Private saved project and evidence: `local-output/sdk-20260909/movement-project-20260912/{project.legaia.json,project-check.json}`. Existing review projects and game builds were untouched; no game launched. Diff checks passed. Full SDK goal remains incomplete.


### 2026-09-12 — Bounded script movement authoring foundation

- Added `importer/movement_authoring.py`: verified MAN owner/PC identities, immutable context, target options and atomic exact-byte X/Z patch audits for decoded MOVE_TO and NPC_RUN. Uses the existing exact retail placement-grid encoder; does not change instruction lengths, control flow, extended context, depth/move operands or Y. Unknown/conflicting stops, aliased owners, foreign IDs, nonrepresentable coordinates and mismatched baselines reject authoring.
- Reference refreshed at d6e64c68ede25813d35db20980da82a1a025549b: engine-vm field step.rs opcode0x23, helpers.rs grid_to_world, and menu_ctrl/nibble_5_6_7.rs sub0x51. No runtime dependency on the reference repository.
- Focused tests cover all256 coordinate-byte no-op roundtrips across four ordinary/extended opcode forms, preserved operands/context, invalid/unvisited/truncated inputs, immutable MAN baselines and parked-target metadata. Initial fixtures used unsupported/unresolved terminal instructions and correctly failed the stop guard; corrected fixtures use a decoded scene-transfer terminator, with no relaxation of authoring checks.
- Retail offline proof: Dolk2 actor0002 MOVE_TO PC0x27 X9280->9344 changes only MAN byte7492; town01 actor0011 NPC_RUN PC0x23 X9664->9728 changes only byte7948. Each has identical MAN layout, unchanged Z, exact no-op bytes and fresh reinspection of the requested X. Dolk2 raw payload stays44036bytes. Town01 re-encodes24891bytes within24894 and independently decodes exactly to the edited MAN.
- Private artifacts and hashes: `local-output/sdk-20260909/movement-authoring-20260912/retail-check.json` plus source-sized edited MAN/payload files. Source disc and existing projects/builds remain untouched.
- Validation:36 focused movement/transition/script-inspection tests passed with the retail disc configured, no skips. Diff whitespace checks passed.
- Integration remains required: project commands/undo/save, editor authored/retail controls, composed Build/disc packaging and later gameplay verification. This is a serializer foundation, not an exposed or gameplay-accepted editor feature. Full SDK goal remains incomplete.


### 2026-09-12 — Viewport target to source instruction navigation

- Added a source-instruction selector and explicit Pick script target mode to the movement overlay. Marker or visible-label picking reopens the verified actor or partition-2 script report at that exact PC. Normal mesh selection remains the default; transform handles are disabled while explicitly picking script targets.
- Overlapping hit candidates require an explicit selector choice; no first-match actor identity is inferred. Source invalidation clears hit regions and picking mode. Missing source owners and stale overlays cannot navigate.
- Retail browser checks: Dolk2 actor0002 marker -> actor-script PC0x27; selector -> PC0x30; partition-2 script0007 marker -> partition-two-script PC0x36. The selected row and retained unresolved target248 were visually inspected. Overlay and instruction-dialog screenshots retained privately.
- An isolated browser overlay fixture moved two markers to the same point: the editor refused automatic navigation and prompted selector use. A source-key invalidation fixture cleared all hits and pick mode. The complete workflow issued zero authored commands and zero page errors. JavaScript syntax and diff checks passed.
- Evidence: `local-output/sdk-20260909/script-target-navigation-20260912/{check.cjs,browser-check.json,browser-top.png,browser-partition-two.png,source-instruction.png}`. Only the temporary editor server and browser were used; no game launch, runtime execution claim or gameplay acceptance. Full SDK work remains incomplete.


### 2026-09-12 — Script movement targets in the scene workspace

- Added camera-only overlays from decoded MOVE_TO / NPC_RUN instructions in actor and partition-2 script views. An explicit reference Y is required; source X/Z, record PC, parked status and unresolved extended actor contexts are retained. No route or branch execution is inferred.
- Frame/Clear controls, source-key invalidation, 256-target budget and collision-aware screen labels keep the overlay separate from authored transforms and live observations. Partial reports remain labeled partial. Labels that cannot fit remain counted as hidden; markers remain available at the current zoom.
- Retail browser acceptance: Dolk2 actor0002's three MOVE_TO targets at PCs0x27/0x30/0x39 rendered at X/Z9280/10816,8640/11200,8384/10304. Blank Y rejected. Clear and framing passed. Partition-2 script0007 opened through the production editor function in a test harness, retaining four contexts65/75/66/248 and converting reference Y=-128 to display Y=128. Source-key invalidation fixture removed the overlay. No authored commands or browser page errors.
- Final top-down actor/partition-2 screenshots inspected; close labels no longer overlap each other or target markers. Private evidence: `local-output/sdk-20260909/script-target-overlay-20260912/{check.cjs,browser-check.json,browser-top.png,browser-partition-two.png}`. JavaScript syntax and diff checks passed. Browser harness quoting errors were corrected before the successful checks; no game was launched.
- Gameplay verification remains deferred. This is source-coordinate inspection, not runtime placement or execution acceptance; the full SDK goal remains incomplete.


### 2026-09-12 — Scene export metadata node budget

- Fixed assembled GLB hierarchy budgeting so unavailable instances' metadata roots count toward the same 32,768-node cap as renderable instances and their object children. Previously an unavailable instance after a full hierarchy could exceed the cap.
- Added a bounded regression covering exact-cap success and rejection with unavailable instances before or after renderable instances; source preview remains unchanged.
- Validation: `test_scene_export`, `test_importer_export`, and `test_animation_clip_export`: 11 tests passed with the verified retail disc configured, no skips. `git diff --check` passed.
- No game launch or gameplay acceptance claimed. Deferred gameplay remains queued; broader SDK work remains incomplete.


- **2026-09-12 (Balden2 script selector evidence):** Previous turn progressed in840ec7de. Fresh verified retail script catalog identifies7Balden2 selector-bearing scripts: actor0015 selector161,0016=241,0017=242,0062=243,0063/64/65=244. Saved metadata-only report balden2-model-selectors-20260912.json privately. Fresh importer/script checks show actor0008 initial model138/animation38, partial report and no decoded model selector; this does not exclude changes in unvisited/opaque paths or other contexts and does not resolve6channels/4objects. Actor0015 initial model161/animation9 numerically matches its selector161, without proving runtime pool bases. No model reassignment or pose fallback was justified or applied. This new evidence narrows the selector hypothesis but retains the unresolved preview boundary. No game launched or controlled. Further useful work requires source evidence for binding/animation execution or separate offline SDK features; full goal remains active.


- **2026-09-12 (script model-selector asset navigation):** Previous turn progressed in4d540a7d. Script catalogs now expose bounded model_selection_references with exact source PC/file offset, extended context, signed/u16 selector and unresolved pool binding. Counts participate in total relationship budget. Asset search discovers selectors; resource inspector links to their exact decoded instruction without synthesizing model asset references. Eight focused catalog tests passed. Actual Dolk2 Edge catalog found10references across10scripts; actor0002 selector241/pool flag set at0xA opened through the verified actor-script route with zero page errors. No runtime pool resolution, model assignment or branch execution is inferred. Browser/server stopped; no game launched or controlled. Broad SDK goal remains active.


- **2026-09-12 (script model selector inspection):** Previous turn progressed in87487e0e. Inspected pinned engine-vm/field/step/menu_ctrl/nibble_5_6_7.rs and host.rs op4c_n5_sub0_set_actor_model: 0x4C50 reads signed LE16, compares signed value>=0xF0 for the pool flag, then invokes host model selection whose effective index depends on pool bases. Decoder now exposes signed/u16 selector, high-pool flag and explicit unresolved asset binding/runtime effect. Script operand UI presents these separately from raw metadata; no imported asset is guessed from selector alone. Twenty-five focused script tests passed, including threshold239/240, negative values and extended target context; JS syntax passed. Fresh retail branch and UI visual acceptance were not run for this addition. No game launched or controlled. Source metadata is progress toward appearance diagnosis, not script execution or model authoring; broad SDK goal remains active.


- **2026-09-12 (script movement asset discovery):** Previous turn progressed in579d2537. Script resource catalog now retains bounded NPC_RUN/MOVE_TO reference metadata: exact PC/file offset, extended target context, decoded XYZ with unknown Y, parked status when applicable and unevaluated runtime effect. Counts participate in the shared relationship budget. Asset search can find these values; script-resource inspector links directly to the originating instruction. Seven focused catalog tests passed including metadata-only payload checks. Actual Dolk2 Edge refresh found14targets across9scripts; opened actor0002 script from asset search and followed MOVE_TO0x27 X9280/Z10816 to its verified source report, zero page errors. Browser/server stopped; no game launched or controlled. Story execution, opaque script paths and movement authoring remain unverified/unsupported. Broad SDK goal active.


- **2026-09-12 (MOVE_TO teleport target locator):** Previous turn progressed in56473852. Rechecked pinned engine-vm/field/helpers.rs grid_to_world evidence and exposed existing MOVE_TO world_xz values as normalized target_position with unknown Y, teleport kind and unevaluated runtime effect. Shared script operand UI now labels teleport targets and provides Locate target, retaining raw encoded details and requiring manual/source-sampled reference height. Twenty-four focused script tests passed including low/high-bit coordinates and unchanged legacy world_xz. Actual Edge component fixture invoking production operand renderer transferred X3136/Z2560 into locator, kept Yblank and form invalid until height supplied. This fixture is UI wiring evidence, not a reached retail branch or script execution. No script byte authoring added; no game launched or controlled. Browser/server stopped; broad SDK goal active.


- **2026-09-12 (authored NPC draft scene export acceptance):** Previous turn progressed in42bb810d. Opened saved streaming-npc-review project and verified442/442 assembled preview instances. Selected the existing authored UUID00000000-0000-4000-8000-000000000003 through its hierarchy row and exported one-instance GLB from the browser. Retail representation request for the same draft correctly returned400. Independent glTF-Transform import retained the authored UUID, actor_draft kind and world translation[64,0,16320]; Khronos validation found zero errors/warnings/no truncation. Private draft-receipt.json and draft-consumer.json retained under scene-export-20260912. Zero browser page errors. This completes offline selected-export checks for actor, scenery, terrain and draft paths; external rendered appearance and actual draft spawning/script behavior remain unverified. No game launched or controlled; browser/server stopped. Broad SDK goal remains active.


- **2026-09-12 (selected scenery and terrain export acceptance):** Previous turn progressed indac03c4f. Actual Edge selection/export workflow verified map01 decoration cell02656 and the ground surface separately. Each receipt identifies exactly one source instance and one geometry. Khronos validation found zero errors/warnings without truncation; independent glTF-Transform import recovered one root per file and matched freshly decoded full-scene bounds exactly (maximum error0 for both). No implementation changes required. Private environment-receipts.json and environment-consumer.json retain file paths/evidence under scene-export-20260912. This verifies scenery transform and terrain adapter export paths; authored NPC draft export and external rendered appearance remain separate checks. Browser/server stopped; no game launched or controlled. Broad SDK goal active.


- **2026-09-12 (selected scene instance GLB export):** Previous turn progressed in390b09cf. Added Export selected GLB using stable actor/draft/scenery selection, server-side instance lookup and exact geometry pruning after verified scene decoding. Preserves scene placement, authored/retail representation and selected identity in audit; missing, ambiguous or nonrenderable selections reject. Complete-scene export remains separate. Focused synthetic test confirms selected root matrix equals the same instance in full export and leaves input unchanged. Actual map01 browser exported only actor0001/onegeometry, zero page errors. Independent glTF-Transform import found one root and bounds matching freshly decoded full-scene source within0.0001units. Private selected-receipt.json retains output path/audit. No game launched or controlled; rendered consumer and gameplay acceptance remain open. Broad SDK goal active.


- **2026-09-12 (retail/authored assembled export parity):** Previous turn progressed in4e55b0a8. Reopened the retained streaming-placement export Inputs read-only and generated retail/authored Dolk2 scene GLBs through the same preview_project representation layer used by the editor. Both contain441instances and independently validate with zero errors/warnings/no truncation. glTF-Transform consumer bounds comparison found exactly actor0001 changed: X delta-16256 (16320to64); other440instances unchanged. Source project file SHA256 stayed identical. Private GLBs/audits/input hash/comparison report retained under scene-export-20260912/placement-comparison. This verifies representation separation for a saved authored placement fixture and shared-scene export, not gameplay placement or script scheduling. Existing deferred manual fixture remains pending; no game launched or controlled. Full SDK goal remains active.


- **2026-09-12 (assembled GLB independent consumer parity):** Previous turn progressed in079b3d36. Independently imported the actual browser-exported scene through installed glTF-Transform4.5.0 NodeIO with extensions. Compared every root instance against freshly decoded source geometry using original model_to_scene matrices and referenced triangle vertices, requiring matching source key. All313identities matched,91object meshes/87textures loaded; maximum world-bounds difference0.00000902764sourceunits. Reports source-bounds.json and consumer-bounds.json retained privately. This proves independent hierarchy/transform interpretation, not rendered Blender/Unity appearance. Tightened encoder empty-geometry rejection and expanded node budget32768 to prevent invalid empty resource arrays and excessive instance expansion; focused scene-export regression passed. No runtime/game launched or controlled. External rendered appearance and broader SDK features remain pending.


- **2026-09-12 (assembled scene GLB editor workflow):** Previous turn progressed inb88c09c9. Connected Export scene GLB to the verified scene preview route with exact source-key validation before decoding and after encoding. Shared exclusive private writer preserves reparse/symlink guards and unique model/scene filenames. UI requires a current preview and no temporary pose/model draft, exports the complete authored/retail representation including temporarily hidden instances, and shows instance/geometry/unavailable counts plus provenance. Actual map01 Edge workflow passed: stale key400, valid export313instances/38geometries, zero page errors, visually inspected receipt screenshot. Saved file scene-04e4e18c3e2b43e186c63eca5d965359.glb independently validated with zero errors/warnings and no truncation. Eight focused exporter tests ran:6passed/2disc-gated skipped; JS syntax passed. Private receipt/validator/screenshot retained under scene-export-20260912. External rendered consumer acceptance remains open. No game launched or controlled; broad SDK goal active.


- **2026-09-12 (assembled scene GLB encoder):** Previous turn progressed inee300a78. Added bounded static scene GLB composition using the existing verified model exporter, shared meshes, per-instance affine transforms and source evidence. Converts the scene actor-local alias explicitly and adapts the decoded Y-down heightfield into one export object; unknown coordinate systems still reject. Unavailable instances retain metadata nodes. Focused synthetic two-instance test checks independent transformed positions, mesh sharing, unchanged input and missing-geometry rejection. Actual map01 export succeeded:313instances,38geometries,4,612,800bytes. Khronos validation repeated with sufficient issue capacity found zero errors/warnings and no truncation; informational NPOT/default-matrix notes retained in private validator.json. Initial attempts identified missing PYTHONPATH then the explicit actor-local coordinate alias, both corrected. Private map01.glb/audit.json retained in scene-export-20260912. UI/private-write integration and independent rendered consumer inspection remain next; this is encoder progress, not a completed editor export workflow. No game launched or controlled; broad SDK goal remains active.


- **2026-09-12 (remaining kingdom browser coverage):** Previous turn progressed inf55a5a55 with the synchronized audio runtime build. Opened the existing isolated map02 and map03 review projects in actual Edge editor sessions. map02 rendered283/283 and map03 rendered263/263 with zero page errors. Frame all, perspective rendering and Top(X/Z) orthographic rendering completed; all four private screenshots were visually inspected and show assembled terrain/ocean/scenery. Per-scene browser-check.json and browser-perspective.png/browser-top.png retained under their map0N-coverage-20260912 folders. Grid overlays remain visible over ocean at the shared plane; source elevation/blending/visibility approximations remain. Updated feature matrix to remove the no-longer-pending browser coverage item, without claiming retail camera, water animation, encounters or gameplay parity. Both browser and server sessions stopped. No game launched or controlled; broader SDK goal remains active.


- **2026-09-12 (audio snapshot synchronization MSVC build):** Previous turn progressed in698087e5. Verified existing isolated project/build roots and preserved97f0f026... executable as audio-stats-lock-20260912/LegaiaStability-before.exe. Reconfigured to refresh embedded source identity. Initial PowerShell build failed before CL execution on duplicate Path/PATH; Git Bash retry completed MSVC Release psx-runtime parallel2 exit0. New executable SHA2563ce6d5461628e8962bb9dd6459ddc5c2a442747500500d4b361eee644f2bcd6d contains nightly-282-g698087e5. Private verification.json records binary/source/log hashes and no runtime execution. Existing compiler warnings remain in the log; no gameplay or audible-acceptance claim. No game launched or controlled. Broader SDK goal and deferred gameplay queue remain active.


- **2026-09-12 (runtime audio statistics synchronization):** Previous turn progressed in1087d787. Release-ledger review identified two unlocked rab_get_stats copies while the host callback updates non-atomic bridge statistics. Wrapped pump diagnostics and psx_audio_out_stats snapshots with the existing SDL audio lock/unlock, matching producer synchronization. Clarified bridge threading contract to include read-only statistics. The executable output-health test compiles both production snapshot blocks and requires a held lock during copy, balanced release, and no locks on unavailable paths; passed twice as coverage expanded. No sample scheduling, DRC controller or overflow policy changed. This does not explain or fix startup overflow. Full runtime build is still pending for this source change; latest previously accepted runtime hash remains unchanged. No game launched or controlled; full SDK goal remains active.


- **2026-09-12 (SDK landmark inspector and global source scope):** Previous turn progressed in0f25fd76. Corrected derived global asset cards to retain their declared scope instead of labeling them as the active scene. Global asset details now say Source scope. Landmark details expose destination ID/label, menu X/Y, discovery index and unknown runtime state outside the collapsed raw provenance section. Added direct Inspect destination source navigation with project/disc context guard; retained full landmark dialog access. Actual Edge map01 workflow passed:20-record category, global-worldmap-menu scope, Rim Elm96/25 inspection, and direct map01 catalog lookup, zero page errors. JS syntax passed. Editor browser/server stopped; no game launched or controlled. No source-menu authoring or runtime discovery/reachability acceptance claimed; broader SDK goal remains incomplete.


- **2026-09-12 (SDK world-map asset database integration):** Previous turn progressed in c7b5bbe6. Global landmark menu records now enter the verified derived resource catalog with stable worldmap identities, record coordinates/offsets, executable/disc and CDNAME provenance, reference pin and explicit unobserved runtime state. Added the worldmap resource kind, browser category and asset-details link to the landmark workflow. Actual map01 browser refresh discovered20 records; category filtering, Rim Elm record0000 provenance opening and navigation to the world-map dialog passed with zero page errors. Three focused world-map decoder tests and JS syntax check passed. No imported facts or authored project state changed; no gameplay launched or controlled. Cataloging menu records does not establish runtime discovery, reachability or 3D world-map behavior. Full SDK goal remains active.


- **2026-09-12 (SDK cursor-anchored scene zoom):** Previous turn progressed in cb554c09. Scene wheel zoom now preserves the cursor intersection with the camera target-height plane in perspective and orthographic views, subject to valid forward intersection. Wheel input cancels active viewport gestures before changing camera distance, preventing mid-move camera changes from silently affecting an authored drag. Twenty-four focused math checks passed across both projections, three pitches and zoom limits. Actual Edge map01 check preserved X13889.650992/Z9998.191784 exactly, cancelled an active pan, and sent zero authoring commands with zero page errors. First browser attempt compared fractional automation coordinates against browser-rounded wheel coordinates; corrected the harness to integer screen coordinates and repeated successfully. This is target-plane anchoring, not terrain-surface picking. Node syntax passed; editor server and browser stopped, no game launched or controlled. Broad SDK work remains active and gameplay acceptance deferred.


- **2026-09-12 (SDK orthographic placement inspection):** Previous turn progressed in aacf0451. Added perspective/orthographic projection selection and Top (X/Z), with +X right and +Z down. Shared WebGL rendering/picking matrix, canvas overlays and move-handle plane rays support the selected projection; camera changes preserve authored data. Eight independent projection/matrix/ray comparisons passed across both projections, oblique/top orientations and two heights. Actual Edge map01 browser rendered313/313, switched projection without errors and produced the visually inspected orthographic-map01-20260912.png private screenshot. Corrected the static viewport heading after screenshot review. Node syntax checks passed. No game launched or controlled; runtime coordinate and visual parity remain deferred, and the full SDK goal remains incomplete.


- **2026-09-12 (SDK terrain locator outer-edge sampling):** Corrected source-height sampling at X/Z16384: these coordinates belong to the final rendered quad but previously produced no sample despite being accepted by the locator endpoint. Bound-check coordinates before clamping the cell index; preserve triangle interpolation and reject outside/nonfinite/boolean inputs and missing source coverage. Twelve focused terrain/scene-preview tests passed, including decoder-produced final-cell corners, outer edges, empty cells and non-bilinear triangle interpolation. No game launched or controlled. This is source-preview correctness, not runtime elevation acceptance; the broader SDK goal remains incomplete and manual gameplay remains deferred.


- **2026-09-12 (SDK source-surface coordinate locator):** Prior turn made progress in1a539a9a. Added Use source surface height to the shared coordinate locator, reusing the verified /api/terrain-point path. X/Z must be explicitly entered and bounded; a covered point fills Y and labels it source surface/runtime-unverified. Missing coverage keeps manual Y without inventing zero. Coordinate edits, dialog closure and scene/source changes invalidate pending samples; source-labelled markers require an unchanged sampled XYZ. Actual Edge map01 check passed: X8000/Z8000 ->Y-192 with the existing source triangle sampler; a deliberately delayed sample was ignored after X changed and manual Y123 stayed intact. Zero page errors; syntax check passed. No authored transforms, source terrain or gameplay were changed. Terrain editing, runtime elevation parity and other broad SDK work remain incomplete.


- **2026-09-12 (SDK kingdom overworld scene coverage):** Prior turn made progress in fc01b50e. Source-driven isolated imports proved existing field structures also supply kingdom overworld geometry, consistent with pinned scene/cutscene.rs sharing mode0x03 while requiring separate world-map behavior. Saved three review projects under local-output/sdk-20260909/map0N-coverage-20260912. Full preview results: map01 8actors/47models,305environment,16,251terrain cells,313/313instances,36,075triangles; map02 7actors/43models,276environment,16,381cells,283/283instances,35,421triangles; map03 19actors/62models,244environment,16,374cells,263/263instances,38,704triangles. No animation/environment/terrain errors or unavailable instances in these source previews. map01 actual browser313/313 with zero page errors and screenshot browser.png visually inspected: continent terrain/scenery assembled. map02/map03 were decoded checks, not browser visual acceptance. Current coordinate/blend/GTE approximations remain. No code change was required to enable this geometry; the evidence expands verified scene coverage and identifies world-map behavior, encounters/camera/visibility and visual parity as separate work. No game launched or controlled; broad goal remains active.


- **2026-09-12 (SDK landmark destination source navigation):** Previous turn made progress in e5bfb8dc. Verified exact CDNAME definitions for the five menu destination IDs:85map01,244map02,354son,391map03,533korout. Added per-record source labels with CDNAME hash/association provenance; absent exact definitions remain null and nearest-name inference is not used. World-map menu rows now offer Inspect source, opening the existing import catalog at that exact label without automatically importing. Three focused decoder/linkage tests passed. First browser check found the generic Close selector overwrote the first new source button; corrected it to the direct child Close button. Repeated actual browser workflow passed with no page errors: Rim Elm -> map01 -> source catalog reports1descriptor scene/8placements, model resolution not checked. No full scene/render/gameplay claim follows from that discovery result. No gameplay launched or controlled; broad goal remains active. Next useful evidence: isolated map01 import and geometry coverage, preserving world-map versus field interpretation limits.


- **2026-09-12 (SDK world-map landmark menu vertical slice):** Prior turn made progress in a25d0d8e. Added a source-verified PS-X executable decoder for world-map menu name/placement tables, following pinned LegaiaRE crates/asset/src/worldmap_menu.rs. Exact disc verification, bounded executable/table spans, required terminator, per-record file offsets, source hashes and stable IDs retained. Unknown name indices remain unresolved instead of silently dropped; repeated records are preserved without simulating menu deduplication. Loopback /api/worldmap-menu accepts only the project's disc with an empty request. Editor World-map landmarks dialog exposes16names/20source records with destination IDs, menu-screen X/Y and discovery flag index; raw metadata/provenance remains inspectable. Two focused tests passed for source offsets, unknown names, deterministic metadata and bad headers/bounds/terminator. Actual retail/browser flow passed with20rows and no page errors; screenshot worldmap-menu-browser-20260912.png visually inspected. This is menu metadata, not3D world-map geometry, resolved destinations, live discovery state or authoring. No gameplay launched or controlled. Full SDK goal remains active.


- **2026-09-12 (SDK scope/current feature-matrix reconciliation):** Previous turn made progress in1bab5822. Revisited the user objective's workflow-based acceptance and subsystem classification against current code, recent local commits and FEATURE_MATRIX.md. Updated the current matrix to include isolated scene animation inspection, complete rigid GLB export, partial-object posing, clipless multipart props and script movement navigation. Corrected obsolete STATIC-only/no-animation-export entries and distinguished the original import-preview count from later441/441 Dolk2 coverage. Preserved historical live evidence and all unproven boundaries; did not reinterpret validator/import acceptance as Blender animation playback or gameplay parity. No tests or runtime actions were represented as newly run. Remaining broad frontiers include world-map authoring/MAPDSIP, arbitrary model topology/material replacement, script execution/authoring breadth, runtime pose/visibility parity and deferred gameplay acceptance. Documentation reconciliation is progress, not a completion claim; active goal remains unchanged.


- **2026-09-12 (SDK model-preview interaction/source guards):** Previous turn made progress in c88d650a with independent GLB validation. Fixed preview buttons that remained clickable during selection requests despite openModel's busy early return. Buttons now render disabled while busy and re-enable through setBusy; authoring buttons retain the Edit-mode requirement. Added an export guard requiring the model dialog's captured scene/source request key to match the current context, preventing a stale reviewed model from initiating either frame or full-clip export after source/scene comparison changes. Syntax passed. Actual Edge editor test deliberately held an actor selection request: preview disabled, re-enabled after completion, and opened successfully. Changed authored/retail comparison while its dialog was open: export displayed the reopen-preview message, sent zero export requests and produced no page errors. No gameplay launched or controlled. Broader SDK goal remains active.


- **2026-09-12 (SDK animated GLB external validation/import):** Previous turn made progress in0367a1ee. Validated the actual browser-exported model-347bca2ad3b54f5c9bbe9e335aa27b8b.glb with the installed Khronos gltf-validator:0errors,0warnings,3informational NPOT crop notes (58x42,56x19,11x19). Independent @gltf-transform/core4.5.0 NodeIO import with registered extensions succeeded:1clip,10nodes,20STEPchannels,31input/output samples per track,2seconds at chosen15fps. Reports retained privately as clip-export-validator-20260912.json and clip-export-consumer-20260912.json. Updated README workflow and corrected the dated buildout report's obsolete no-animation-export limitation. No dependency installed, source artifact modified, Blender/game process launched or runtime controlled. These are validator/independent-import checks; rendered animation playback in Blender/Unity and gameplay parity remain unverified. Full goal remains active.


- **2026-09-12 (SDK full-clip GLB editor integration):** Previous turn made progress in b13120c2. Exposed full rigid clip export through model, actor-animation and authored-appearance export endpoints, preserving existing frame exports. Server validates exactly one nonnegative frame index or explicit1..120fps rate before animation decode; output paths/source bindings remain project-controlled. Model dialog now offers Export full clip GLB with a separate Export fps input and an accurate receipt describing selected timing/receiving-player looping. Six focused HTTP/clip/appearance tests passed, including early rejection before preview loading, private writes and unchanged frame-export behavior. Fixed the new test's HTTPError cleanup warning. Actual browser editor export of Dolk2 actor0001 succeeded:30decodedframes at15fps,10objects,281triangles,3textures, no page errors; receipt screenshot visually inspected. Reopened saved GLB and verified10nodes/20STEPchannels/31samples including terminal hold. Private artifact: local-output/sdk-20260909/catalog-import-workflow-20260912/Exports/model-347bca2ad3b54f5c9bbe9e335aa27b8b.glb; receipt clip-export-browser-receipt-20260912.json. No game launched. External consumer/validator playback remains next; this check proves editor-to-file integration, not downstream application acceptance or retail animation timing.


- **2026-09-12 (SDK full rigid-animation GLB encoder):** Previous turn made progress in e54c793e. Added optional explicit clip_fps to encode_model_glb/write_model_export. Full clips retain unposed object geometry and emit per-object translation/quaternion channels with STEP interpolation, Y-reflected Rz*Ry*Rx transforms, float32 timeline bounds, and a final held sample so the last decoded frame has one frame interval. The caller chooses1..120fps; metadata explicitly excludes retail timing and automatic loop claims. Frame snapshots remain separate; mixed frame/clip export, posed bases, invalid rates and inconsistent channel identities reject. Existing64MiB output cap plus4096frame/100000channel-sample bounds apply. Checked Khronos glTF2 specification at https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#animations. Synthetic quaternion reconstruction matched independent source pose_vertices across all-axis rotations; source preservation, invalid inputs, buffer-view targets and terminal hold passed. Initial exporter run:7passed/2retail skipped. Explicit retail rerun:3focused tests passed, including full Station7-object and Balden2 one-object clips through the server preview adapter. These were in-memory artifacts, no gameplay. Remaining next: HTTP/editor full-clip export integration and external consumer validation; do not present full-clip export as an exposed editor capability yet.


- **2026-09-12 (SDK shared reference clips in scene inspector):** Previous turn made progress in 62f5af08. Fixed the global actor Inspector button that hardcoded idle and therefore failed for F3/F4 loop-only models. It now selects the first supported clip and uses the generic Preview reference animation label. Added a separate scene-inspection actor identity to the model dialog; shared clips retain their model-based API/export routing while gaining isolated in-scene playback. Clip changes preserve inspection identity, and the viewport explicitly labels these Reference clip. Actual Edge editor check on Dolk2 actor0061 passed: request asset://legaia/models/global-special/00f3 with loop through /api/animation-preview, 30-frame model dialog, scene playback toframe3, pause and restore, no page errors. No live/initial actor clip assignment is inferred. Syntax check passed. No game launched or controlled; full goal remains active.


- **2026-09-12 (SDK in-scene animation playback):** Previous turn made progress in 9c491d4c. Added play/pause and explicit preview fps (5/10/15/30/60, default10) to isolated actor animation inspection. Playback advances existing vertex buffers and wraps the loaded clip; this is chosen preview timing, not inferred retail cadence. Scrubbing pauses, rate changes reset accumulated time, restoration cancels the animation callback, and playback stops for stale context, source refresh, Live mode, hidden document, busy operations, hidden models, lost graphics context or a newly opened model dialog. Full editor Edge test on Dolk2 actor0001 passed: advance at30previewfps, pause holds atframe4, manual scrub pauses, final-frame wrap, restore hides controls, zero page errors. Serialized server project state was identical before and after playback. Syntax check passed. No gameplay launched or controlled; runtime timing and appearance acceptance remain deferred. Broader SDK goal remains incomplete.


- **2026-09-12 (SDK actor animation inspection in scene):** Prior turn made progress with export integration coverage in 9e83b89b. Implemented Inspect animation in scene from an actor's loaded model dialog. The scene receives a separate geometry key for that actor, preserving other instances that share its original model. A labelled inspection-only frame slider updates vertex buffers; Restore scene pose reinstalls the original preview. Inspection uses existing scene transforms, does not author data, and clears on refreshed source/scene/mode changes. Geometry assembly preserves the original scene document and drops unused geometry; the existing 128-asset limit remains enforced. Syntax and isolated shared-geometry/source-preservation checks passed. Actual editor browser flow on Dolk2 passed: 441/441 meshes, actor0001 imported clip, in-scene frame3/30, restore, no page errors. Screenshot inspected at local-output/sdk-20260909/in-scene-animation-20260912.png. Initial browser attempts used a wrong button label and then clicked during selection busy state; after waiting for selection completion the full flow passed. No game launched or controlled. Remaining: automatic scene playback, full-clip export and runtime alignment/acceptance are not proven by this scrub-only feature.


- **2026-09-12 (SDK partial-object export integration verified):** Previous turn made progress in 0afcac78. Traced partial-object scene animation through EditorServer.actor_animation_preview, texture association, and encode_model_glb. No export implementation repair was needed. Added a focused private-disc regression for Station actor 0010 and Balden2 actor 0015, exporting first and last frames through the real server adapter without starting its request loop or connecting to a game. Four GLBs passed container/buffer-view parsing, active-object node identity, expected 290/174 triangle counts and three exported positions per triangle; preview input remained unchanged. One focused integration test passed. These are in-memory posed snapshots, not complete animated-clip exports, and no permanent proprietary artifact was written. Gameplay remains deferred; whole SDK goal incomplete.


- **2026-09-12 (SDK script-to-viewport coordinate navigation):** Previous turn made progress in d0b62196. Added readable NPC_RUN target summaries and Locate target actions to the shared instruction renderer used by actor and trigger script inspectors. The action closes its script dialog, opens the existing coordinate locator with decoded X/Z, and leaves required Y blank with an explicit unknown-height prompt. Parked targets and unobserved branch/runtime state remain visible; no source coordinates or project data are changed. Captured scene/project context rejects stale navigation after a scene switch. Node syntax check passed. Isolated Edge DOM check against the actual appendScriptOperands function passed: X3136/Z2560 filled, source dialog closed, locator opened, empty required Y prevented submission, stale-scene click rejected. This was a component DOM check, not a full editor or game acceptance run. No gameplay launched; broad SDK goal remains active.


- **2026-09-12 (SDK script movement coordinates):** Previous turn made progress in e4205ae8. Investigated remaining Balden2 actor 0008 with the verified source script. Its three prologue NPC_RUN instructions depend on story flags 468/469; no proven model-rebinding explanation for the 6-channel/4-object mismatch was found, so that pose remains unavailable. Extended NPC_RUN inspection to expose encoded X/Z, depth, move ID, decoded source-world X/Z, unknown Y, parked-sentinel status and explicit runtime-not-evaluated evidence. Decode follows pinned field_disasm/decode_subops.rs and man_field_scripts/npc_motion.rs::grid_byte_to_world; no branch is chosen or scene coordinate overridden. Twenty-four script-inspection tests passed with private retail checks, including ordinary/extended targeting, half-tile coordinates, parked targets and every truncated operand span. Fresh Balden2 script targets: PC25 (3136,2560), PC36 (1856,12864), PC47 (3392,2240). Private original inspection saved at local-output/sdk-20260909/balden2-actor0008-script-20260912.json. No gameplay launched; mismatch investigation remains open.


- **2026-09-12 (SDK partial-object scene animations):** Prior turn made progress in 1a2a0a9e. Investigated all three remaining Station/Balden2 animation mismatches against retail bytes and pinned LegaiaRE field_npc_placements_disc.rs (FUN_8001B964 count contract, reference d6e64c68ede25813d35db20980da82a1a025549b). Scene clips may track fewer leading objects than their model; trailing untracked objects are excluded, not left at the origin. Implemented this in shared pose/full-animation geometry with per-request trimming so cached full geometry remains intact. Catalog bindings now retain active/excluded object indices. Eleven focused scene-animation/catalog tests passed, including cache preservation, source validation and excess-channel rejection. Retail checks: Station actor 0010 has 7 channels/8 objects, 15 frames and 290 retained triangles; Balden2 actor 0015 has 1 channel/10 objects, 15 frames and 174 retained triangles. Their full-animation frame zero equals the single pose and all triangle indices stay in bounds. Balden2 actor 0008 has 6 channels/4 objects and remains rejected; do not infer compatibility or silently truncate its channels. No game launched; runtime appearance remains unverified. Whole-scene rendered counts were not rerun in this change.


- **2026-09-12 (SDK clipless multipart scene props):** Previous turn made progress (shared animation catalog committed as 3beeb070). Added raw multipart rendering for verified actors with initial animation ID zero, following pinned LegaiaRE field_npc.rs play-catalog behavior at d6e64c68ede25813d35db20980da82a1a025549b. All objects retain raw vertices and share the existing actor transform; preview includes source/reference evidence and explicitly does not claim observed runtime state. Nonzero unresolved animation IDs still reject multipart fallback. Eight scene-preview tests passed, including cache separation and source-evidence rejection. Private retail actor-only previews: Station 19/20, newly supported actor man-p1/0007; Balden2 64/66. Remaining Station actor 0010 and Balden2 actors 0008/0015 fail channel/object-count matching. Evidence: local-output/sdk-20260909/clipless-preview-20260912/report.json. These counts exclude environment and terrain. No gameplay was launched or controlled; runtime acceptance remains deferred. Next source-driven work: investigate the three animation/model count mismatches.


- **2026-09-12 (SDK shared animation discovery — offline verified):** Added a metadata-only shared field animation catalog for the eight supported reference model/clip pairs (records 0, 1, 7, 8, 14, 15, 21, 22). Resource refresh independently discovers these alongside scene MAN animations. Asset Browser entries expose source provenance, frame/channel counts and a direct reference-clip preview; no initial or live actor assignments are inferred. Five focused animation catalog tests passed with the private retail disc, including stable town01/Dolk2 results without geometry loading. Headless editor-browser check passed: Dolk2 441/441 preview, eight shared resources, savepoint opens loop frame 1/30, no page errors. This is editor-only verification; no game was launched or controlled. Runtime animation timing and all existing manual acceptance checks remain deferred in docs/legaia-gameplay-verification-queue.md. The broad SDK/stability goal remains incomplete; continue work that does not require gameplay.


### 2026-09-12 — Graphics lifecycle recovery acceptance

- Actual WEBGL_lose_context test on the retail savepoint viewer: rendered frame3 normally, returned to frame2, lost context, advanced to frame3 while lost, restored context. Canvas screenshot bytes exactly matched the normal frame3 screenshot; no page errors. This validates current-frame recovery rather than only retained source metadata.
- Fixed restoration path discarding mesh-upload failure reports. Recovery now keeps the renderer unavailable and reports the upload error instead of sending a successful/null status.
- Injected upload-failure check across an actual context loss/restore produced the expected failure message, lost=true and no success status. Initial same-task restoration attempt timed out; issuing restore in a separate browser task passed. No game/runtime implication from that test scheduling issue.
- JavaScript syntax passed. Private model-context-restored-20260912.png retained. No game launched or project saved; browser/server stopped. Full SDK goal remains active.


### 2026-09-12 — Unified model and scene rendering

- Replaced the standalone model viewer's separate Canvas2D affine/painter path with the shared WebGL renderer. Model/animation inspection now receives the same vertex-color modulation, depth tests, texture sampling and decoded blend/STP behavior as the scene viewport. Existing local-Y reflection and orbit framing remain explicit.
- Added validated vertex-buffer updates for same-layout animation frames: retained interleaved buffers and textures, refreshed bounds and latest source vertices for context restoration. Object/clip changes rebuild the bounded mesh; frame changes update positions only. No arbitrary topology changes.
- Browser opened savepoint loop, scrubbed to frame2/30, selected object0 and returned to animated assembly, with no page/model/WebGL errors. Inspected savepoint-model-webgl-20260912.png: lit translucent structure replaces prior opaque gray panels. GPU check proved retained buffer identities, updated X/bounds95, latest restore-source95, invalid vertex-count rejection and zero GL errors. Actual graphics-context loss was not simulated this turn.
- Both viewers retain approximate blended ordering and no retail ordering-table/GTE equivalence claim. No game launched or project saved; temporary browser/server stopped, full goal active.


### 2026-09-12 — Scene blend preview

- Scene WebGL renderer consumes decoded ABE/ABR and per-texel STP evidence. STP is encoded into a spare uploaded alpha value while zero-transparent texels remain discarded; it is not treated as blanket opacity. Invalid masks/modes reject mesh upload.
- Added opaque/depth-write pass then enabled-fragment blend pass using half-add, add, reverse-subtract and quarter-source-add. Blended instances sort back to front by transformed bounds center, with no depth writes. Picking bypasses color blending while preserving transparent holes. Grid and next-frame state are restored.
- Actual WebGL pixel checks against foreground204/51/102 and background51/102/153 returned127/76/127,255/153/255,0/51/51,102/115/179 for modes0–3 (within2 units of independent equations). STP0 stayed opaque, STP1 blended, alpha0 exposed/picked the background; all other cases picked foreground, zero GL errors. Private evidence scene-blend-gpu-check-20260912.json.
- Retail browser kept441/441 Dolk2 entities, selected/framed actor0061, no page errors. Inspected dolk2-scene-blend-preview-20260912.png. Badge labels approximate blends; exact retail ordering-table submission, intra-mesh translucent sorting, GTE/color precision and transparent canvas-background interaction are not established. Standalone model viewer still uses its prior opaque rendering path.
- No game launched or project saved. Temporary browser/server stopped, full SDK goal active.


### 2026-09-12 — Preserve transparency evidence through preview transport

- Renderer audit found that decoded per-texel STP masks were discarded by model_preview before reaching clients. Added stp_base64 alongside matched RGBA data, requiring one binary byte per pixel and accounting for both payloads in per-model and combined-scene budgets.
- Materials expose decoded ABE enable, tpage ABR mode and textured-STP versus untextured-all-fragment gating. Untextured ABR0 is explicitly reference-default evidence from pinned crates/tmd/src/mesh/color.rs, not a captured draw environment.
- Retail savepoint probe verified all four matched masks against texture dimensions and binary domain; material modes are1,0,0,0,1 with their original enable flags. Ten scene-cache/boot-underlay checks passed.
- This completes the transport prerequisite only: current renderers still draw without PSX blend reconstruction. No visual/gameplay acceptance claim, game launch or project save. Direct server socket closed; full goal active.


### 2026-09-12 — Boot texture coverage for scene models

- Extended verified boot UI underlay to scene texture catalogs, below scene-owned words. Authored texture replacement keeps the underlay through the existing catalog deep copy; unknown/conflicting scene upload order remains rejected.
- Fresh town01 assembled preview comparison: before56 vertex-colored materials,279 address matches,8 missing; after56 vertex-colored and287 address matches,zero missing. Exactly eight status changes, all missing -> address_match, source boot-ui/raw-0/8: model0074 material0,0021/0,0002/3,0040/1,0026/0,0041/0,0061/2,0071/0. This agrees with pinned reference scene_entry/system_ui_bundle documentation for environment use of boot-resident pages.
- Private metadata reports: town01-textures-before-boot-20260912.json and town01-textures-after-boot-20260912.json. Twenty-three focused underlay, retail texture and texture-build tests passed. No new browser visual acceptance this turn; material address coverage does not prove transparency, current VRAM residency or gameplay fidelity.
- No game launched or project saved; direct probe server sockets closed. Full SDK goal remains active and manual gameplay remains deferred.


### 2026-09-12 — Boot UI texture underlay for shared field models

- Savepoint materials1/4 lacked word(960,496), with CLUT32644. Pinned reference system_ui_bundle.rs and scene/host/scene_entry.rs establish the boot-resident page and raw TOC entries0/1, including table-order overwrites and six clipped row patches.
- Added bounded raw-entry decoder with exact20/1 member counts, atlas rectangle fingerprint, six pinned row patches, source-member hashes and ordered image/flat-CLUT uploads. Retail produces36 uploads. No arbitrary memory capture or guessed texture substitution.
- Shared field model catalogs now use this ordered boot bank as an underlay only where no field upload owns a word. Conflicting field uploads remain ambiguous. Metadata exposes source locators/rectangles without pixels; row patches clip at the VRAM edge.
- Twenty focused texture/underlay tests passed with private retail input. Direct source checks and browser confirm savepoint's four textured materials all match; the fifth uses vertex colors. Inspected savepoint-boot-textures-20260912.png: opaque gray effect surfaces remain because semi-transparent blending is still unsupported. No browser errors; scene remains441/441.
- Scope currently covers shared field-model texture routing; scene-environment integration remains next work. No game launched or project saved; temporary browser/server stopped, broader goal active.


### 2026-09-12 — Shared F3/F4 pose reconstruction

- Fresh Dolk2 audit isolated all nine unrendered entities to F3/F4 (actor0061 and0062–0069). Pinned reference d6e64c68ede25813d35db20980da82a1a025549b docs/formats/anm.md and character_pack.rs identify shared bank record21/savepoint and22/auxiliary. Retail decoding confirms3 channels/30 frames and2 channels/15 frames.
- Expanded exact global associations to five pack slots. Party10-of12 equipment-template handling remains unchanged; F3/F4 retain all3/2 objects. Shared texture routing uses the five-model loader's section2 upload described in field_char_textures.rs. Complete provenance and count checks remain required.
- Scene preview uses the advertised default clip and labels nonparty samples reference_global_loop. HTTP animation/export validation now consults each model's supported clip list; browser found and fixed the former idle/walk-only guard.
- Thirty-six focused animation/texture/scene tests passed with private retail input, including all original party clips, new counts and tampered provenance rejection. Browser preview returns441/441 entities,9 newly assembled poses; savepoint scrub reached frame2/30 with no page errors. F4 HTTP preview returns15 frames and matching textured material. Inspected savepoint-reference-loop-20260912.png; unmatched savepoint material remains explicit.
- Initial direct probe omitted a loader positional argument and failed before completion; corrected probe established the baseline. No game launched or project saved. Runtime visibility/scale/timing, auxiliary semantic role and full material parity remain pending. Temporary server/browser stopped; full goal active.


### 2026-09-12 — Catalog-to-import persistence workflow

- Empty review project completed browser catalog search -> Dolk2 selection -> Import -> assembled scene -> Save. Preview reported432/441, with72 actor records and no browser errors.
- Independent ProjectService.open from saved project.legaia.json confirmed Dolk2,72 actors, retained disc path and clean state. Review artifact: local-output/sdk-20260909/catalog-import-workflow-20260912.
- Project state exposes its existing local disc path so an empty import-path field can reuse it. User-entered nonempty paths remain intact. Added bounded scrolling for scene results/import dialog and readable field-format labels.
- Inspected catalog-import-browser-20260912.png at1360x900: catalog and Import control are readable in one dialog. Python reopen and JavaScript syntax passed. No runtime/game launched; temporary browser/server stopped. Remaining nine Dolk2 preview entities and gameplay compatibility remain unverified, full goal active.


### 2026-09-12 — Verified scene discovery in the import workflow

- Connected the existing bounded retail scene catalog to a new read-only /api/scene-catalog route, with strict disc/offset/prefix fields and a fixed 16-block page. Boolean offsets and out-of-range values reject before disc reading.
- Import dialog now provides prefix search, Previous/Next, placement-readable scene selection, carrier kind, actor count and expandable unsupported reasons. Selecting fills the import name; it does not mutate the project. Disc/prefix changes and dialog closure invalidate old results.
- Retail browser scan found two Dolk scenes and selected dolk2 with no page errors; invalid boolean offset returned HTTP400. Two full unfiltered pages scanned16 blocks each, had disjoint names and next offset32 of124 structural blocks (14 then16 supported placements). An initial pagination probe using town had no next page and rejected null offset; the unfiltered probe exercised actual pagination.
- Python/JavaScript syntax and diff checks passed. No game launched, no project import/save performed. Models and gameplay are explicitly not established by placement discovery. Temporary server/browser stopped; full goal active.


### 2026-09-12 — Iterative animation channel editing

- Successful animation commands now reopen verified channel options at the selected frame/object, preserving editing context while refreshing authored values and shared effective evidence.
- Added Clear selected channel contribution, preserving this actor's edits on other frame/object pairs and all other actors' contributions. Unapplied field changes must first be applied or discarded; all mutations use the existing validated command/undo path.
- Browser opened the channel editor directly from authored asset details, applied TX117 at frame1/object0, verified the reopened editor retained frame1 and its value, then cleared only that contribution. Fresh API state retained the fixture's original frame0/object0 TX100 edit. No page errors; JavaScript syntax passed.
- No project save or game launch. Original fixture stayed on disk unchanged; temporary editor/browser stopped. Runtime playback remains deferred and the broader goal stays active.


### 2026-09-12 — Authored animation discovery and preview navigation

- Authored actor cards now summarize sparse animation channel edits, so animation-only changes are discoverable by name in the project-wide authored browser.
- Asset details offer direct channel editing and authored animation preview, selecting the source actor/scene first. The model viewer status now distinguishes authored shared animation, authored appearance and retail assigned animation.
- Three catalog tests passed, including animation-only summary and snapshot isolation; JavaScript syntax passed. Browser searched Animation in authored assets and opened the existing town01 actor0011 authored clip from asset details, showing AUTHORED shared animation with no page errors. The new direct edit action was not separately browser-tested.
- Existing animation fixture unchanged; no game launched. Temporary browser/server stopped, manual gameplay remains deferred and full goal active.


### 2026-09-12 — Cross-scene authored asset navigation acceptance

- Created an isolated local review project from existing two-scene and model-shape fixtures, adding a town01 draft while opening town0c. Original fixtures were not modified.
- Browser verified draft navigation town0c -> town01 with its dedicated Inspector, and a separate authored model card navigation town0c -> town01 opening AUTHORED object-local shape with the persistent replacement. No page errors.
- A combined automation attempted the second click before its scene request completed and timed out; the rerun waited for the completed scene preview and passed. Asset cards/details now visibly disable while busy, including newly rendered rows, instead of presenting ignored actions as available. JavaScript syntax passed.
- No game launched; temporary browser/server closed. Runtime acceptance remains deferred, broader goal active.


### 2026-09-12 — Complete authored asset discovery for drafts and model shapes

- Fixed Asset Browser filtering that discarded model replacement records. Added project-wide NPC draft catalog records with stable IDs, source scenes, retail donor references and isolated authored snapshots.
- Draft cards use dedicated selection/framing, including the existing scene-switch and authored-view behavior, instead of the imported actor selection endpoint.
- Six focused authored-catalog/draft tests passed; JavaScript syntax passed. Browser navigation from the saved Dolk2 review project's Authored assets card opened the draft Inspector without page errors. Initial early click during scene loading was ignored; rerun waited for the completed 433/442 preview before checking navigation. Cross-scene browser acceptance remains untested.
- Refreshed stale feature-matrix text claiming all draft builds were rejected. No game launched or authored project saved; manual gameplay remains deferred.


### 2026-09-12 — Bounded comparison geometry reuse

- Scene previews retain at most two decoded geometry sets, allowing retail/authored comparison and appearance undo to reuse verified geometry. Each entry retains the existing geometry/triangle/texture budgets; a cache miss evicts before decoding a third set.
- Source stamps and authored replacement checks remain ahead of cache lookup. Transform projection and response copies remain per request; failed decoding clears all retained entries.
- Eight focused scene-preview tests passed, including appearance undo without decoding, least-recently-used eviction, replacement rejection on a cache hit, source changes, response isolation and failed regeneration. No game launched; gameplay queue remains deferred and the broader goal remains active.


### 2026-09-12 — Donor pose evidence and animation inspection

- Investigated the unusual framed Dolk2 donor pose. Actor0001 binds model0133, animation record34, ten objects/channels and thirty frames. Frame0 contains substantial encoded rotations; no evidence justified forcing an upright orientation. SDK transform equations match pinned reference d6e64c68ede25813d35db20980da82a1a025549b `crates/tmd/src/mesh/mod.rs::rot_zyx` (Rx, Ry, Rz) and the eight-byte channel layout documented in player_anm.rs.
- Draft Inspector now identifies the sampled preview pose and offers Inspect donor animation for scene-bound clips. This connects the frame0 scene view to the existing full-clip viewer without changing authored appearance or disc data.
- Browser verified the frame0 label and actual donor-animation endpoint/dialog with thirty decoded frames. JavaScript syntax passed; temporary browser/editor server stopped. Runtime correctness and semantic stance remain unverified; no game launched, full goal active.


### 2026-09-12 — Draft selection across comparison layers

- Retail hierarchy identifies NPC drafts as Authored only. Framing a selected draft explicitly switches back to the authored scene, retains selection, and waits for matching geometry before framing. Draft Inspector exposes this as Show in authored scene.
- Added persistent Inspector notice distinguishing retail viewport comparison from authored property fields, beyond the transient switch notification.
- Browser verified retail draft label/notice, layer switch, retained selection and authored geometry restoration; inspected `local-output/sdk-20260909/retail-draft-return-authored-20260912.png`. Existing donor pose appearance remains reference-derived, not gameplay verified. JavaScript syntax passed. Temporary browser/editor server stopped; project unsaved state was not changed.
- No game launched. Full SDK goal active; manual gameplay deferred.


### 2026-09-12 — Comparison resource request regression repair

- Found and repaired a regression introduced with the viewport switch: resource-catalog, scene-transition and scene-flag requests had unintentionally gained the scene representation field. These separate endpoints require empty request bodies. Restored their contracts without changing the comparison endpoint.
- Entering retail comparison now clears a carried-over collision overlay and selects imported collision, avoiding silent effective-collision carryover. Coordinate locator remains an explicit guest-coordinate camera marker and does not substitute authored transforms.
- Browser verified resource refresh, transitions and flag references in retail mode: all HTTP200 with exact empty request bodies. JavaScript syntax passed; browser and temporary editor server closed. No game launched; goal active.


### 2026-09-12 — Retail/authored viewport switch

- Added explicit Authored scene / Retail scene comparison control. Requests and cache readiness include representation; stale responses cannot replace the selected layer. Switching cancels gestures and clears stale geometry while preserving the camera and project edits.
- Retail actor fallback positions use imported transforms, authored-difference markers are hidden, and viewport movement handles/scenery transform actions are disabled. Inspector remains explicitly authored project state, rather than silently substituting retail values.
- Browser workflow passed authored433/442 -> retail432/441 -> authored433/442 with unchanged draft data/dirty state and no JavaScript errors. A separate awaited selection check confirmed retail hierarchy selection synchronizes the Inspector. Inspected `scene-retail-comparison-browser-20260912.png` and `scene-retail-selection-browser-20260912.png` under local-output/sdk-20260909. JavaScript syntax passed.
- Both temporary editor/browser sessions stopped. No game launched; comparison is editor-derived rather than live acceptance. Broader SDK goal remains active.


### 2026-09-12 — Whole-scene retail/authored preview service

- Added explicit authored/retail scene preview projection and HTTP request support. Retail uses a separate view with overrides, NPC drafts and model/TIM replacements excluded; the working project and undo history are preserved. Model/texture resolution receives that projected view rather than leaking the server's authored state into retail geometry.
- Responses identify their representation, projected source key and current project source key. Unknown representations/client geometry remain rejected. Seven focused preview tests passed, including authored->retail->authored position restoration and no project/history mutation.
- Real saved-project HTTP check: authored 433 renderable meshes/one draft; retail 432/zero drafts. Both agree on project source identity and the authored-state digest remained unchanged. Private metadata `local-output/sdk-20260909/scene-comparison-http-20260912.json`. Temporary HTTP server stopped.
- This is service groundwork: viewport comparison control, marker/picking layer consistency and editing restrictions remain to implement before claiming the complete comparison workflow. No game launched; full goal active.


### 2026-09-12 — Saved streaming NPC browser review workflow

- Rechecked the original Unity-like workflow requirements and exercised the saved streaming NPC project in the actual editor browser. Scene preview loaded 433/442 supported meshes; Export history displayed the matching one-draft export. Its Verify saved files button passed the disc and two snapshot file checks.
- Visual inspection showed long private paths/hash text dominating the dialog. Moved those fields into an expandable Saved files and source hashes section, retaining the scene/edit summary and review actions in the main view. Browser check verified collapsed defaults and expansion revealing the recorded hash; JavaScript syntax check passed.
- Inspected screenshots: `local-output/sdk-20260909/streaming-npc-history-browser-20260912.png` and `streaming-npc-history-compact-20260912.png`. Both temporary editor/browser sessions stopped; no game launched and no project mutation.
- Remaining product frontier includes whole-scene retail/authored comparison and broader SDK acceptance gaps; saved-export review does not establish runtime behavior. Full goal active; gameplay deferred.


### 2026-09-12 — Reviewable export history summaries

- Export history now presents recorded NPC draft count and audited edit categories for both per-scene streaming/multi-scene reports and legacy single-scene reports. Missing legacy counts remain unknown, not zero; private dialogue payloads and draft names are not copied into summaries.
- Corrected empty-history guidance to include edit-only exports. Three history tests and editor JavaScript syntax check passed. The saved streaming NPC review export reports exactly one draft and the NPC additions category from its completed report.
- No game launched. This improves later artifact selection; file integrity checks and gameplay acceptance remain separate. Full goal active.


### 2026-09-12 — Persistent streaming NPC review artifact

- Saved isolated project `local-output/sdk-20260909/streaming-npc-review-20260912`, retaining the original model-import fixture. One donor-0001 boundary NPC at X64/Z16320; no other authored edits.
- Completed disc export under Builds/experimental-drafts-00000000000040008000000000000003. Output 466716768 bytes, SHA256 a0e2f44dcfeec3f3ce0f6621eb6390f11001a6c362dd60427fe2f176053386bf. Output-disc MAN independently reopened with 73 exposed actors and exact final MAN hash; added record73 has authored coordinates.
- Export history recognizes the completed output and matches saved project inputs. On-demand verifier passed disc hash and both input snapshot files. Queue now records exact artifacts, limitations and deferred gameplay checks. No game launched or controlled; full goal active.


### 2026-09-12 — Streaming project NPC draft composition

- Enabled validated same-scene NPC drafts in streaming preparation, appending retail donor records before rebasing existing dialogue, appearance, placement and transition edits. Final raw MAN padding is applied only after all edits. Selected streaming drafts route through the shared multi-scene archive composer, retaining animation/model/texture/MAP verification.
- Nine composition/export tests passed; two extended retail integration checks then passed with fresh baseline partition-count comparison and NPC+animation+appearance composition. Dolk2 becomes 73 exposed actors, with its partition-1 count increasing from 73 to 74 because one record is not an exposed actor. Existing dialogue glyph offsets rebase, transitions remain audited and the shifted animation bank verifies in the final archive.
- No game launched. This remains experimental serialization: reached script references are handled, opaque paths and actual spawn behavior are not proven. A persistent review project/disc for later manual gameplay remains to be prepared. Full goal active.


### 2026-09-12 — Reopen shifted streaming animation banks

- Streaming animation carrier evidence now includes structural chunk ordinal/type. Final-archive verification traverses the physical owner's complete chunk chain and validates type, payload length and hash, so an earlier grown MAN cannot leave validation at a stale byte offset.
- Three retail streaming composition tests passed. The animation test now grows the MAN after composing its channel edit, successfully verifies the shifted bank, and proves that the old unbound offset and a wrong chunk type reject. Failed checks remove prior success flags.
- This closes the shifted-bank verification gap needed for streaming NPC project integration. Project draft composition remains next; no game launched, manual gameplay still deferred, full goal active.


### 2026-09-12 — Streaming NPC physical archive growth

- Connected the streaming MAN growth primitive to sector-aligned physical archive replacement and TOC relocation. Equal-span batch requests retain the existing byte-preserving path; growth requests reopen and compare the complete relocated carrier and structural chunk sequence.
- Eight focused streaming/archive tests passed, covering unchanged-size behavior and growth with preserved later chunks and archive suffix. Real Dolk2 donor append reopened successfully: MAN +176 bytes, PROT +2048 bytes. Private audit: `local-output/sdk-20260909/streaming-npc-archive-growth-20260912.json`.
- Project NPC export remains disabled pending draft composition and rebasing the final verification of animation banks shifted within the grown MAN carrier. No playable disc or game launch in this step. Full goal active; manual gameplay deferred.


### 2026-09-12 — Streaming NPC chunk-growth primitive

- Added source-bound MAN chunk growth with explicit size-word rewriting and structural rebasing of every following chunk. Neighbor bytes and the opaque terminator/tail are preserved exactly. Wrong hashes, non-MAN targets, incomplete chains, unaligned sizes, shrinkage and size-budget violations reject.
- Three streaming primitive tests passed. A real Dolk2 donor-0001 append produced 73 actors and 176 bytes of aligned growth; subsequent type-4/type-5/type-7 headers shifted by exactly 176 bytes, including the animation bank. Private audit: `local-output/sdk-20260909/streaming-npc-chunk-growth-20260912.json`.
- This is an in-memory chunk candidate, not an exported playable disc. Physical archive relocation, final animation-carrier rebasing and project NPC integration remain required before streaming NPC export can be enabled. No game launched; goal active.


### 2026-09-12 — Streaming model shape export

- Connected streaming scene model bindings to the existing source-bound model overlay writer and final carrier reopening. This supports existing-layout vertex/normal XYZ replacement; topology, materials, descriptors and padding remain protected. It does not add arbitrary models or change topology.
- A real Dolk2 model-0000 vertex probe passed compressed-capacity and rebuilt-carrier checks. Private metadata: `local-output/sdk-20260909/streaming-model-composition-20260912.json`.
- Seven focused model/OBJ/streaming composition tests passed with retail checks enabled. The combined model+texture test uses separate compressed sections of one physical entry, reopens the final archive, decodes each pack and compares exact replacement TMD/TIM bytes; both source-disc assets remain unchanged.
- No game launched. Streaming NPC additions/payload growth remain unfinished; model visual suitability and gameplay behavior remain deferred. Full goal active.


### 2026-09-12 — Streaming texture replacement export

- Texture authoring now resolves entry-head asset directories independently of MAN presence, matching the existing texture catalog's four/five-entry streaming-directory support. Descriptor type/offset, alias, span, TIM layout and compressed capacity checks remain enforced.
- Streaming scene export now composes verified project texture bindings through shared archive overlays and final carrier verification. NPC growth and model replacement support remain separate unfinished work.
- Eleven retail-enabled texture/import/export/composition tests passed. A Dolk2 TIM probe is independently decoded from the final archive and compared byte-for-byte with the replacement; original disc TIM remains unchanged. Private metadata evidence: `local-output/sdk-20260909/streaming-texture-composition-20260912.json`. No proprietary payloads were added to Git.
- No game launched; visual appearance in gameplay remains deferred. Full goal active.


### 2026-09-12 — Streaming animation export composition

- Added raw type-5 animation bank serialization to the shared archive patch path. It verifies the physical owner, complete terminated chunk chain, original bank identity, equal word-aligned payload size and unchanged structural boundaries before composing the replacement.
- Streaming scene preparation now accepts validated `AnimationChannels` edits and passes carrier evidence through final-archive reopening. Shared-clip conflicts and original actor/record binding checks remain enforced by the existing animation authoring layer.
- Eight focused tests passed with retail checks enabled. New Dolk2 integration coverage composes a channel translation edit with a separate actor appearance edit, independently reopens the final archive, compares both exact payloads and proves all other archive bytes unchanged. No runtime playback, timing or scene behavior claim follows from this byte-level verification.
- No game launched. Streaming NPC growth and model/texture replacement export remain unfinished; gameplay checks remain deferred and the full goal active.


### 2026-09-12 — Streaming actor appearance composition

- Extended initial MAN donor assignment contexts to verified raw streaming MAN and ANM sources. Existing scene donor, non-aliased record, object/channel count and decoded-animation validation remain enforced; raw serialization preserves payload length without LZS impersonation.
- Streaming export now composes same-scene `ActorAppearance` with positions, dialogue, transitions and MAP edits. Dolk2 actor 0001 -> donor 0041 changes exactly two header bytes; private metadata evidence: `local-output/sdk-20260909/streaming-appearance-composition-20260912.json`.
- Validation: all 14 assignment tests passed with retail checks enabled. New retail integration test composed appearance, placement, dialogue and P2 transition changes, reopened the output archive, matched the exact candidate, and preserved every byte outside the MAN payload. The fixture deliberately omits Y because MAN placement serialization supports X/Z only.
- No game launches or live writes. Actual donor suitability and script behavior remain deferred; streaming NPC growth, animation channel and model/texture replacement export remain unfinished. Full goal active.


### 2026-09-12 — Streaming script catalog and P2 editor access

- Connected streaming script/dialogue resources and partition-2 inspection to the typed raw MAN source. Preserved descriptor behavior and source bounds; raw record coordinates are explicitly `raw_man_payload` and carry no invented LZS offsets.
- Retail Dolk2 catalog/P2 source offsets and record hashes agree, including P2[0]'s named map01 transition. Metadata remains payload-free. Town01 catalog equals the committed catalog exactly; refreshed stale aggregate test expectations (550 dialogue segments, 1249 flag references).
- Focused retail-enabled script/dialogue/transition suite: 37 tests passed. Additional Dolk2 and Town01 HTTP edit/undo/redo/clear and client-source rejection tests both passed. Prior streaming dialogue disc and transition composition evidence remain in the deferred queue/private audits.
- No game was launched or controlled. Streaming NPC growth and model/TIM replacement composition remain implementation work; runtime scene, dialogue and arrival behavior remains unverified. The full goal remains active.


### 2026-09-12 Streaming partition-2 dialogue and transition export composition

- Previous turn verified streaming dialogue browser/disc behavior. Transition contexts already inherit the typed dialogue source; connected validated transition-entry edits to streaming preparation using boundary-preserving rebasing onto the composed MAN.
- Eligible scene changes in the inspected streaming scenes occur in P2 scripts rather than the actor rows checked. Streaming preparation now admits exact same-scene P2 owner identifiers for Dialogue/Transitions only; Transform remains actor-only, and source context still verifies membership, aliases and instruction paths.
- Real dolk2 P2[0] transition PC0x1A to map01 changed entry_x_encoded54 to55 and reopened successfully through project preparation. Metadata audit `local-output/sdk-20260909/streaming-transition-composition-20260912.json`; no destination name or instruction layout changed. Runtime entry behavior remains unverified.
- No game or disc writer launched this turn. Browser/P2 authoring and end-to-end transition disc coverage remain outstanding; broader streaming components remain unfinished.

### 2026-09-12 Streaming dialogue browser and disc acceptance

- Previous turn implemented verified raw dialogue preparation. On a separate private project copy, browser Apply changed actor0003's eligible 15-byte run to SDK plus padding; Undo restored the source and dirty=false. Screenshot `local-output/sdk-20260909/streaming-dialogue-applied-20260912.png` inspected. Temporary browser/editor closed.
- Exported separate probe disc under `streaming-dialogue-export-20260912`, SHA256 `cb8f9914ee04069625b066d7bf043171e5003bc7b62789fdc58065c595ec564f`, 466,714,416 bytes. Independent hash, directly reopened MAN text spans and all snapshot hashes passed. Added exact artifact and branch-execution caveat to deferred gameplay queue.
- Sixteen focused dialogue/draft tests ran: fifteen passed, one skipped. No gameplay launched; no claim that the edited branch has executed. Broader streaming components and NPC additions remain unfinished.

### 2026-09-12 Equal-span dialogue authoring for raw streaming MAN

- Previous turn checkpointed verified placement/MAP exports. Dialogue context now distinguishes verified raw source bytes from LZS input, preserves existing span/instruction-boundary checks and reports raw packaging limits accurately. Streaming project preparation composes validated actor dialogue runs with positions and MAP edits; unsupported components still reject.
- Real dolk2 actor0003 run `script://dolk2/actors/man-p1/0003/dialogue/0017/run/0018` (15-byte capacity) accepted `SDK` with padding and passed archive reopen verification. Metadata audit `local-output/sdk-20260909/streaming-dialogue-composition-20260912.json`. Actor0001 has no eligible run and remains non-editable under unchanged safety checks.
- Fifteen dialogue/archive tests ran before adding the raw-source parity regression: fourteen passed, one skipped. Added raw-versus-LZS patch parity and source/compression rejection coverage. Browser dialogue authoring review and final dialogue disc remain outstanding. No game or disc writer ran.

### 2026-09-12 Mixed descriptor/streaming relocation and MAP composition

- Previous turn produced a verified streaming disc artifact. Added mixed-format archive regression: compressed owner growth relocates a later streaming owner, whose equal-span MAN patch still reopens correctly; reversing request order gives identical bytes/audit and tail sectors remain unchanged. Ten focused archive/draft regressions pass.
- Real saved town01 NPC draft plus an in-memory dolk2 placement edit composed into 121,255,936 bytes; owners 4 and 70 both reopened successfully. Metadata audit `local-output/sdk-20260909/mixed-streaming-descriptor-project-20260912.json`.
- Real dolk2 placement plus collision row30/column30/quadrant0 false-to-true bit (MAP offset20254, mask16) also composed and passed final MAP verification. Audit `local-output/sdk-20260909/streaming-map-composition-20260912.json`.
- Source projects were not saved with these probe edits, no additional disc was written, and no gameplay launched. Broader streaming authoring/NPC growth remains unfinished.

### 2026-09-12 Streaming placement disc export and deferred test artifact

- Previous goal turn made verified project preparation progress. Exported dolk2 actor-0001 X64/Z16320 initial placement probe through the shared experimental disc/snapshot writer. Output `local-output/sdk-20260909/streaming-placement-export-20260912/draft.bin`, 466,714,416 bytes, SHA256 `834a22c50b0bc527bd8b9327246ca8c342b34ad82548501e42a3cc47c28f36de`.
- Independent file hash, all retained input hashes, saved project override and direct output-disc MAN decoding passed. The ordinary importer rejected the modified SHA as designed; lower-level Mode2/PROT readers verified output without changing that retail-only gate. Reopened actor fields are X64/Z16320, model133, animation35.
- Twelve focused archive/draft export regressions passed. Added precise artifact and limitations to the deferred gameplay queue. This is a boundary-placement serialization probe; scripts may move/hide it, so visibility at initial coordinates is not promised.
- No game launched. Mixed-scene and MAP composition checks plus broader streaming authoring remain unfinished.

### 2026-09-12 Streaming project preparation joins experimental export composition

- Previous turn checkpointed verified writer primitives. Batch MAN preparation now distinguishes descriptor requests from structural streaming chunk requests while retaining distinct-owner checks and stable entry order.
- Added streaming project preparation for actor X/Z and supported MAP scenery/collision components through the existing experimental export path. Other authored components and NPC additions reject explicitly; no unsupported edits are silently omitted. Fresh imported evidence and authored-state keys are verified before/after preparation.
- Real dolk2 project override traversed `prepare_draft_archive` and produced a 121,253,888-byte logical PROT with reopened streaming MAN verification true; audit `local-output/sdk-20260909/streaming-project-preparation-20260912.json`. Seven archive/payload regressions pass.
- No disc was written or gameplay launched. Final disc/snapshot export, composed MAP acceptance and mixed descriptor/streaming relocation coverage remain next; broad streaming authoring is not complete.

### 2026-09-12 Streaming archive writer regression checkpoint

- Previous goal turn made verified retail archive-writer progress. Added a synthetic, parsed MAN-in-PROT roundtrip regression that verifies retained TOC bytes, neighboring chunks/sectors and candidate bytes, plus rejection of boolean indices, nonstructural offsets, stale preimages and payload growth.
- Seven archive/streaming tests pass. Initial synthetic PROT fixture lacked bytes required by its indexed read window; extending fixture backing bytes corrected the test without relaxing production validation. Retail one-byte archive evidence from the preceding turn remains the integration proof.
- No game or disc writer ran. Streaming project composition remains the next task; no build-ready or gameplay-complete claim.

### 2026-09-12 Streaming MAN archive replacement and reopened verification

- Previous goal turn made verified streaming-payload writer progress. Added equal-span streaming MAN archive replacement with expected archive/payload hashes, unique physical-owner resolution, MAN validation, retained TOC and reopened payload verification. An animation chunk cannot be targeted through the MAN writer.
- Real dolk2 actor-1 X patch changed exactly one byte across PROT; reopened MAN matched candidate and TOC stayed identical. Metadata-only audit `local-output/sdk-20260909/streaming-man-archive-patch-20260912.json` records source/result hashes and keeps build_ready false. No disc output or gameplay run.
- Focused payload regression tests still pass. Project export composition, growing NPC payloads and final disc validation remain unfinished; this archive writer is the next integration foundation rather than an export-completion claim.

### 2026-09-12 Streaming payload replacement foundation

- Previous turn completed verified editor visibility work. Traced draft export's compressed MAN assumption and added a separate source-hash/preimage-verified streaming payload replacement primitive for word-aligned, equal-size MAN/animation chunks. It requires a complete terminated structural chain, preserves all other bytes, and rechecks chunk boundaries. Growing payloads and archive relocation remain separate unfinished work.
- Two focused streaming tests passed, covering neighbor preservation, changed size rejection and stale source/preimage rejection. Real dolk2 MAN actor-1 X edit exercised the existing placement encoder and the new carrier replacement; private metadata-only audit `local-output/sdk-20260909/streaming-man-placement-patch-20260912.json` records changed bytes and hashes. No disc was written or game launched.
- This is a writer primitive, not completed streaming project export. Next work must compose supported authored components and verify the final archive/disc before exposing export readiness.

### 2026-09-12 Hidden hierarchy state and visibility scope acceptance

- Previous turn made verified visibility implementation progress. Hidden hierarchy rows now carry an accessible Hidden badge; selected objects can be restored individually. Visibility and layer actions refresh the hierarchy, and project/scene scope remains client-only.
- Browser checks passed hidden badge creation/removal and Show selected behavior. Project-switch verification passed through actual Project/Open controls from Station to Balden2: all 149 supported Balden2 entities visible and Show hidden disabled. An initial test attempted to call a module-private API function from page scope and failed; the UI-path rerun passed. JavaScript syntax passed.
- No game launched. Temporary browser/editor closed; authored scene data remains unchanged.

### 2026-09-12 Temporary per-entity and model-instance visibility

- Previous goal turn was verified texture progress. Added Hide selected, Hide model instances and Show hidden controls to the viewport. Visibility is client-only, scoped to project/scene, reset on scope changes and merged with existing layer hiding. Renderer picking/bounds already consume the hidden-ID set; actor markers and frame-all point bounds now respect it too.
- Browser test on Station selected model-0001 scenery, hid both instances (304 to 302 visible), restored all (304), and confirmed project dirty remained false with no page errors. Screenshot `local-output/sdk-20260909/scene-visibility-controls-20260912.png` inspected. JavaScript syntax passed before browser execution.
- No game launched or authored geometry changed. Temporary browser/editor closed. Runtime visibility semantics remain outside these explicitly temporary inspection controls.

### 2026-09-12 Station sky texture opaque TIM flag support

- Previous turn identified a verified visual defect. Station descriptor TIM slots 11/22 are structurally bounded 66,080-byte members with flags `0x80000008`, previously rejected. Pinned TIM parser's lenient structural-asset path retains reserved bits. Added this exact observed opaque flag variant, retaining flags and all block validation rather than broadly accepting reserved values.
- Station catalog grows from 46 to 48 textures; page-138 material now resolves to `texture://station/227/0/11`. Browser screenshot `local-output/sdk-20260909/streaming-station-texture-fixed-20260912.png` inspected: gray shapes are now textured sky domes. Their size is source geometry, not a reason to rescale positions; selective visibility is a future editor usability improvement.
- Twenty-four focused texture/project tests ran: twenty-one passed, three skipped. No gameplay launched; temporary browser/editor closed. Full runtime palette, visibility and placement parity remain deferred.

### 2026-09-12 Station and Balden2 integrated previews expose missing Station textures

- Previous goal turn was verified implementation progress. Fresh private projects and full preview reports created for station/balden2 under `local-output/sdk-20260909/streaming-{scene}-preview-20260912` and `streaming-{scene}-full-preview-20260912.json`.
- Station resolves 304/306 entities and Balden2 149/155; neither raises terrain, environment or animation-source errors. Both browser previews loaded and were visually inspected (`streaming-{scene}-browser-20260912.png`).
- Station fails visual acceptance: large gray scenery surfaces occlude the scene. Traced models 0001/0012 to missing texture VRAM (640,0), page 138; do not change geometry scale/placement as a workaround. Balden2 room geometry is visible but runtime parity remains unverified. Coverage report records this distinction; mesh counts alone are not acceptance.
- No gameplay launched. Temporary editor server and browser closed. Next source work is Station missing texture upload coverage.

### 2026-09-12 Station extended animation bank and Balden2 five-entry asset table

- Previous goal turn produced actionable coverage evidence. Station entry 228 has a 96,256-byte indexed window but a 165,888-byte extended footprint; its type-5 bank is complete only in the latter (140,144 bytes at offset 22580). Streaming animation now reads the extended footprint while clipping to scene ownership and rechecking MAN provenance.
- Balden2 entry 319 uses five descriptors (types 1,2,6,7,20) with first payload at 48. Structural asset parsing now accepts this count without changing the separate MAN-bearing bundle gate. Fresh import resolves 66/66 actor models from 162 scene plus five shared models; 48 actor animation bindings validate. Station validates 15 bindings over 57 records.
- Updated public streaming coverage report; browser integration for these scenes remains pending, and no runtime acceptance is claimed. No game launched.

### 2026-09-12 Streaming coverage beyond dolk2

- Previous turn was verified source/browser progress. Reviewed unresolved dolk2 actors: all nine use shared multipart F3/F4 models with missing pose association; do not substitute unassembled geometry or claim model-reference failure.
- Fresh offline checks across dolk2/rikuroa/rayman/station/balden2 establish full model-reference coverage in the first four, supported scene animation bindings in the first three, and terrain in all five. Station has no uniquely resolved same-carrier type-5 bank; balden2 lacks a resolved scene model pack (7/66 actors resolve through shared models).
- Saved `docs/legaia-streaming-scene-status.md` and private `local-output/sdk-20260909/streaming-scene-coverage-20260912.json`. These newly identified source-discovery gaps guide the next implementation work and do not require immediate gameplay. No game or browser launched this turn.

### 2026-09-12 Streaming scenery and integrated browser review

- Previous turn made verified animation progress. Environment previews now consume the same verified streaming animation bank through an immutable-byte/copied-provenance handoff, retaining existing per-placement pose checks and MAP transforms. Streaming animation reading is clipped to scene ownership, rechecks MAN bytes and limits bank size.
- Integrated dolk2 browser preview now returns 432 renderable entities out of 441: source terrain, scenery and supported actors. Nine actors remain markers. Inspected `local-output/sdk-20260909/streaming-dolk2-actors-browser-20260912.png`; visible room layouts/scenery are present, but this is not runtime visibility, palette or placement parity proof.
- Eighteen focused environment/terrain/animation/scene tests ran: sixteen passed, two skipped. The test editor and browser were closed. No game launched, no authored coordinates changed, and manual gameplay remains deferred.

### 2026-09-12 Streaming scene actor animation poses

- Previous goal turn made verified model-slot progress. The verified dolk2 MAN carrier entry 70 also contains one raw type-5 bank at payload offset 44088, length 114764, SHA256 `0d168cb7093fb4034de9f494b93635b30a27f886ac16918b27dc2e3ad6f80006`.
- All 58 animation records decode; all 56 nonzero scene-model actor bindings match the source model object counts. Added same-carrier, unique-type-5 animation loading with explicit raw chunk provenance and per-actor binding validation. Compressed descriptor behavior is unchanged; raw animation offsets are not labeled as decoded LZS.
- Retail service preview now renders 63/72 actors plus terrain (64/73 instances, 17 geometries, 7,719 triangles). Private report `local-output/sdk-20260909/streaming-dolk2-posed-preview-20260912.json`. These are initial reference poses, not live scene behavior. Streaming scenery assembly remains unsupported; gameplay and browser visual review of the new poses remain outstanding.
- No game launched; temporary service socket closed. Model and animation changes remain available in the worktree for the next integrated browser check.

### 2026-09-12 Explicit streaming scene model slots

- Previous goal turn made verified texture progress. The generic dolk2 scan reports 142 TMD hits (141 from entry-69 descriptor 1, one incidental raw hit in entry 70). Added an explicit single-pack streaming model reader using the scene asset directory and word-offset pack slots; invalid members cannot silently compress slot numbering, and multiple competing packs reject resolution.
- Fresh dolk2 import resolves all 72 actor model references from 141 scene slots plus five shared models. New private project `local-output/sdk-20260909/streaming-dolk2-models-20260912` preserves the older fixture rather than replacing its imported evidence.
- Real service preview now renders seven actors plus terrain (eight instances, 5,152 total triangles). Scene animation assembly remains unavailable, so resolved references are not claimed as fully rendered or runtime-verified. Report `local-output/sdk-20260909/streaming-dolk2-model-preview-20260912.json`; no game launched and temporary service socket closed.

### 2026-09-12 MAN-less asset directories supply streaming terrain textures

- Previous goal turn was verified implementation/browser progress. Retail dolk2 had zero catalog textures because its entry-69 four-descriptor asset directory lacks MAN; the texture importer incorrectly required a six/seven-descriptor MAN-bearing directory.
- Split structural asset-directory parsing (four/six/seven entries) from MAN source selection (unchanged six/seven plus MAN requirement). Texture decoding now accepts the owned entry-head directory and bounds each LZS stream by the next descriptor, rejecting overlapping active resource offsets.
- All six dolk2 terrain material queries changed from missing VRAM words to static address matches. Browser screenshot `local-output/sdk-20260909/streaming-dolk2-textured-browser-20260912.png` inspected: terrain now displays texture data, but this is not proof of runtime palette/upload-order or UV parity. Scene remains incomplete with scenery and most actor models unresolved.
- Twenty-six focused texture/source/project tests ran: twenty-three passed, three skipped; regression confirms a four-entry asset directory is not accepted as a MAN bundle. Browser scene preview returned 200. No game launched; temporary server and browser closed.

### 2026-09-12 Streaming MAN floor heights enable dolk2 terrain

- Previous turn made verified source and retail-preview progress. Connected environment placement/terrain decoding to the typed streaming MAN when no owned descriptor bundle exists; preserved existing descriptor decoding and recorded explicit raw carrier provenance. Streaming mesh/animation assembly remains unsupported rather than assuming a descriptor layout.
- Retail dolk2 resolves MAP entry 66 and streaming MAN entry 70 (SHA256 `a623b1a0534d2e70ca6186037af19693df26cdc7874cd071a9cd2a54319c46b2`): 2,054 terrain cells, 4,108 triangles and six material records. Private output `local-output/sdk-20260909/streaming-dolk2-terrain-20260912.json` includes source hashes.
- Fifteen focused terrain/environment/scene tests ran: fourteen passed, one skipped. Browser `/api/scene-preview` returned 200 and displayed five meshes among 73 entities (ground plus four actor instances). Inspected screenshot `local-output/sdk-20260909/streaming-dolk2-terrain-browser-20260912.png` confirms ground layout; terrain texture association remains unresolved/gray, and scenery meshes are missing.
- No authored coordinates changed and no gameplay ran. Temporary editor and browser closed. Streaming scene-local model mapping, animation carriers, textures and export remain ongoing work.

### 2026-09-12 Keep independently supported models when scene animation is unavailable

- Previous goal turn was verified progress (checkpoint `937a5ab9`). Continued offline scene-preview work; the pinned streaming carrier reference and current service showed the animation-catalog factory aborted the entire scene before supported models were attempted.
- A retail animation-source error now remains in preview metrics while independent reference poses and unanimated single-object geometry can render. Actors requiring the missing scene pose stay unresolved; authored animation channels still require a verified catalog and reject the preview otherwise. Import provenance mismatch remains fatal.
- Six focused scene-preview tests passed, including the missing-catalog static/animated distinction and authored-channel rejection. Real dolk2 service preview now returns 72 actors with four renderable instances, two geometries and 984 triangles; unsupported terrain/environment/animation sources remain explicit. Private report: `local-output/sdk-20260909/streaming-dolk2-preview-20260912.json`. A report-print key typo was corrected; final report was written successfully.
- This does not complete streaming model mapping or terrain support and does not establish runtime placement. No game launched; the temporary service socket was closed.

### 2026-09-12 Streaming script browser presentation and source checkpoint

- Continued offline SDK implementation under the user's deferred-gameplay instruction. Browser inspection of dolk2 actor 0001 displays 34 decoded instructions and one dialogue segment from its own raw streaming MAN.
- Replaced premature text-edit capability labeling with source inspection; unavailable authoring controls are hidden, and streaming scenes explicitly explain their read-only text/transition status. Existing descriptor serialization rejects streaming sources with an accurate operation-specific error.
- Focused importer/script/project checks: 37 tests, 36 passed and one skipped. Browser assertion verified the streaming read-only message and hidden authoring toolbar; screenshot inspected at `local-output/sdk-20260909/streaming-script-browser-20260912.png`. JavaScript syntax passed. Initial browser locator and misspelled test-module failures were corrected before acceptance.
- Added source-handoff regression coverage for ambiguous raw carriers, explicit uncompressed provenance, bounded LZS input and no fallback after malformed preferred descriptors. Streaming scene-local models, terrain and serialization remain unfinished; no game was launched or gameplay acceptance claimed. Temporary editor server and test browser closed.

### 2026-09-12 Streaming actor script inspection

- Actor-script inspection now reads typed MAN sources, exposes raw carrier provenance and reports no compressed-byte consumption for streaming payloads. Shared descriptor reader now enforces the next descriptor's compressed-span ceiling.
- Retail dolk2 actor0001 inspection decoded34 supported instructions and one dialogue segment with partial coverage. Editor service returned the inspection while explicitly reporting dialogue authoring unsupported; write safety was not inferred.
- Focused script/preview/stream checks passed. Browser script interaction, streaming dialogue/transition authoring and model mapping remain pending. No game launched or saved project changes.


### 2026-09-12 Streaming placement project import

- Scene catalog and import now consume typed MAN sources. Raw streaming actor records carry entry/payload offsets, hash, exact byte sizes and compression=none; descriptor metadata remains unchanged for existing bundle scenes.
- Imported dolk2's72 actor records into local-output/sdk-20260909/streaming-dolk2-import-20260912, saved and reopened with identical metadata.13 global-special model references resolve; scene-local models remain explicitly unresolved pending streaming pool mapping. Scene catalog reports raw_streaming_man rather than the neighboring suimon bundle.
- Saved town01 import digest unchanged. Streaming model/resource preview, authoring serializers and export remain incomplete; no gameplay launched or existing user project modified.


### 2026-09-12 Typed descriptor and streaming MAN source handoff

- Added ManSource/read_man_source with decoded payload, parsed actors, encoded size, physical locator and explicit compression kind. Descriptor failures do not silently select a different streaming script; streaming fallback requires exactly one validated carrier with actor records.
- Existing pipeline MAN handoff now uses this abstraction but explicitly rejects raw streaming project imports until source metadata and consumers are adapted. This prevents fabricated descriptor/LZS provenance. Retail checks resolved town01 plus five streaming scenes; town01 saved metadata digest unchanged. Seven focused stream/boundary/preview tests passed.
- No game launched or retail data modified. Streaming project import, resource mapping and export remain the next implementation work.


### 2026-09-12 Raw streaming MAN discovery prototype

- Added bounded streaming chunk walker using the pinned reference's truncated-word advance and zero-size termination. Discovery validates type03 payloads as MAN, clips scene read windows, records raw/noncompressed provenance and avoids duplicate physical payloads.
- Retail dolk2 carrier entry70 decoded44036 bytes with counts29/73/17, SHA256 a623b1a0534d2e70ca6186037af19693df26cdc7874cd071a9cd2a54319c46b2. Also found distinct carriers in rikuroa,rayman,station,balden2; bubu1/opkorout/opmap01 unresolved by this path. Metadata: local-output/sdk-20260909/streaming-man-carriers-20260912.json.
- Two focused stream/boundary tests passed. Importer/editor/export integration remains pending; candidates explicitly do not claim export readiness. No gameplay launched or retail bytes changed.


### 2026-09-12 Streaming MAN carrier reference identified

- Bounded four-byte-aligned scan found no supported6/7-descriptor MAN tables within the seven unresolved field-scene windows. Evidence: local-output/sdk-20260909/unaligned-scene-table-scan-20260912.json.
- Read pinned LegaiaRE d6e64c68ede25813d35db20980da82a1a025549b crates/engine-core/src/scene_bundle.rs::streaming_man_payloads and chapter1_hub_sweep_oracle evidence. Reference explicitly corrects dolk2/suimon aliasing as read-window bleed and identifies dolk2's own streaming MAN (partition counts29/73/17).
- Next importer work should decode validated type03 streaming chunks with independent provenance, rather than treating them as compressed descriptor-table MANs. Existing authoring/export callers assume descriptor compression and require deliberate adaptation. No runtime/game changes or speculative table fallback enabled.


### 2026-09-12 Reject borrowed MAN tables beyond scene boundaries

- find_scene_bundle now bounds candidate table origins and full descriptor tables by the next scene's physical start. Overlapping indexed read windows no longer establish ownership of a following scene's MAN table.
- Synthetic overlap regression plus preview/routing checks:9 passed. Retail rescan preserved88 tables exactly, changed none, and rejected the same9 out-of-range labels from the prior inventory. Report: local-output/sdk-20260909/scene-bundle-boundary-check-20260912.json. Saved town01 import digest independently unchanged.
- gameover_data,dolk2,rayman,station,balden2,bubu1,opkorout,opmap01,vab_01 remain unresolved by this discovery path; their true formats/ownership need further evidence. This is not a complete payload ownership or asset-pool audit. No gameplay launched or retail bytes changed.


### 2026-09-12 Retail MAN physical-owner inventory

- Inventoried all124 CDNAME labels on the verified retail disc:97 returned supported MAN-bearing bundles,27 did not. Nine apparent shared-owner groups resolve to identical physical table offsets, not distinct tables requiring composition.
- Report: local-output/sdk-20260909/retail-man-owner-inventory-20260912.json. Added each bounded scene range and whether the discovered physical owner falls inside it. Overlapping indexed read windows can expose a following scene's table; discovery boundary validation is the next investigation before enabling shared-owner rebuilds.
- This is source-layout evidence, not proof of complete scene ownership or relocation safety. No game launched, archive modified or import behavior changed.


### 2026-09-12 Editable export copy browser acceptance

- Browser opened an editable copy through Export history from a separate snapshot-only test project. Result: ReviewCopies/export-10758c5134214dd5a59b103bdab8d84f, scene town01, clean project state. Original collision-export snapshot file hashes independently rechecked unchanged.
- Test fixture retained under local-output/sdk-20260909/export-copy-browser-20260912; it contains report/input copies only, not a copied disc. No file-integrity or gameplay claim was made for that test fixture's absent disc.
- Temporary editor4406 and headless browser stopped; working project and game untouched. Saved-input reopening UI check is complete.


### 2026-09-12 Open editable copies of retained export inputs

- Export history now offers Open editable copy for snapshot-bearing exports. It checks saved file hashes, writes a unique ReviewCopies project, validates reopening, then uses the existing project-switch path. Original export inputs are retained unchanged.
- Requires a saved current project in Edit mode. Invalid paths, duplicated inputs and corrupted snapshot bytes reject. Four focused history/export tests passed, including editing the copy without changing original snapshot bytes; JavaScript syntax passed.
- Browser interaction remains to be checked. No game launched or user project switched during implementation.


### 2026-09-12 Donor editing browser and retail candidate acceptance

- Browser changed Candidate NPC donor0011 to0012 with X3008 retained; Undo restored0011. Used the separate saved-input snapshot project and did not save. Temporary editor4406 and headless browser stopped.
- Independent retail candidate preparation selected donor record12 (509 bytes, model105, animation13), appended record53 and retained authored X3008/Z5440. Reopened MAN verification passed. Final decoded MAN SHA256 f04e20876dd1a11583ff4be9ef39d89d106989d468b3fa094d4085ce82ce6c94.
- Candidate audit still reports incomplete script relocation, context allocation and spawn scheduling acceptance. No gameplay or working-project mutation; broader SDK objective remains active.


### 2026-09-12 Change an authored NPC draft's retail donor

- Added set_actor_draft_donor using the validated draft/history path. Same-scene donor changes preserve identity, name and position; undo/redo and project persistence remain supported. Invalid donors reject without history mutation.
- Draft Inspector now offers a retail donor selector and explains that export clones the donor script as well as its appearance. This is persistent authoring, not a live actor change.
- Eleven focused draft/preview/catalog tests passed and editor JavaScript syntax passed. Browser control interaction remains to be checked; no game launched or working-project save.


### 2026-09-12 Collision locator browser acceptance

- Actual browser flow reopened collision-only saved inputs, refreshed resources, opened wall editing, selected the authored cell and located it. Terrain endpoint returned X3872/Y-128/Z3744; the dialog closed and viewport displayed the reference marker plus effective edited-cell outline.
- Inspected screenshot local-output/sdk-20260909/collision-terrain-locator-20260912.png. The collision overlay remains explicitly Y0; only camera/reference-marker elevation uses source terrain. No runtime height or movement claim.
- Temporary editor4406 and headless Edge closed; no game launched or saved project edits. This completes the pending browser check for terrain-aware cell location.


### 2026-09-12 Terrain-aware collision cell locator

- Existing wall-cell locator now requests a source-key-guarded terrain sample rather than always aiming at Y0. The source preview elevation changes camera/probe display only; authored wall data and positions remain untouched. Missing terrain is explicitly labeled as a Y0 placeholder.
- Added bounded read-only /api/terrain-point service; actual HTTP check sampled the collision fixture center X3872/Z3744 at guest Y-128. Stale source, boolean X and negative X requests rejected with400; project document unchanged. Temporary HTTP server closed, no game launched.
- JavaScript syntax check passed. Full rendered locator interaction remains to be checked; this does not prove runtime elevation or collision acceptance.


### 2026-09-12 Isolated collision disc and saved input acceptance

- Exported a project with no drafts and exactly one town01 collision wall-bit edit. Output: local-output/sdk-20260909/collision-only-export-20260912/draft.bin, 466714416 bytes, SHA256 f77fb410addd646904208f184b2a1a174f73d9b7378f7fa54c28a25c90822c5d.
- MAP and PROT reopening passed; independent final hash, every saved input hash and collision-only snapshot reopen passed. Eleven focused preview/export tests passed. Queue records exact bounds and later manual movement comparison.
- No game launched, no working-project save, no extra authored NPC or model/texture/animation changes. Broader SDK goal and gameplay acceptance remain incomplete.


### 2026-09-12 Project-wide experimental export without NPC drafts

- Generalized authored archive routing to accept projects with supported edits and no drafts. The new Export disc toolbar action and /api/export/project route use the existing snapshot/report/history pipeline; CLI --draft is optional. Empty projects still reject experimental export.
- Six focused export tests passed; HTTP coverage includes project export without a draft and rejects caller output paths. Real retail town01 preparation with zero drafts and only actor0011 X2880-to3072 emitted a 121253888-byte archive and passed reopened MAN verification. No disc/game launch or project save occurred.
- This enables isolated asset/scene gameplay fixtures without an unrelated NPC addition. Shared physical container composition and broader runtime acceptance remain incomplete.


### 2026-09-12 Draft-aware scene instance counts

- Corrected preview metrics to count projected actors/drafts rather than internal cached donor bindings. Added draft and total instance/renderable counts; geometry-cache metrics remain separate.
- Hierarchy totals include active-scene drafts. Mesh badge denominator now uses the same preview instance inventory as the renderer, preventing impossible loaded/total ratios during draft authoring.
- Five scene-preview checks passed after handling legacy actor instances with no kind field. Regression covers a draft cloned from a donor with an authored appearance without counting its internal retail binding. No game launched.


### 2026-09-12 Frame newly authored entities after preview completion

- Diagnosed duplicate framing before the new preview exists: placeholder height and absent model bounds put the camera inside scenery. Entity framing now waits for the matching project/scene/source preview, then uses its rendered position and bounds.
- Camera interaction, explicit selection or a newer frame request cancels the pending request; source-key and camera-revision guards prevent stale completion from moving the camera.
- Actual duplicate workflow in the separate snapshot project passed. Inspected local-output/sdk-20260909/draft-frame-ready-20260912.png: selected NPC visible on terrain at unchanged authored X3008/Z5440, versus the prior inside-scenery framing. Temporary editor/browser stopped; no game or working-project mutation.


### 2026-09-12 Draft rename and duplication workflow

- Added Edit-mode rename/duplicate commands, validated names, independent UUIDs, shared retail donor provenance, exact position copies and existing command history/persistence integration. Duplicate respects the 128-draft bound; identical rename adds no undo entry.
- Inspector exposes name editing and Duplicate draft, selects the new draft and explains that it starts at the same position. Five focused lifecycle/catalog checks passed; actual browser rename/duplicate selected Gate resident copy at X3008 in a separate snapshot project, without saving.
- Temporary editor and browser stopped. Screenshot: local-output/sdk-20260909/draft-duplicate-20260912.png. Working project and game were untouched; gameplay checks remain deferred.


### 2026-09-12 NPC draft asset usage and navigation

- Model assignment references now include authored NPC drafts across imported scenes. Draft references retain the retail donor independently of authored donor appearance, distinguish draft versus imported assignments, and make no runtime identity claim. Animation usage projection retains that draft identity.
- Four focused catalog/draft lifecycle tests passed. Actual town01 model0105 browser inspection listed Candidate NPC; clicking its usage entry selected the draft Inspector at X3008 after correcting the separate draft selection path. Screenshot: local-output/sdk-20260909/draft-asset-usage-20260912.png.
- Temporary editor port4406 and headless test browser stopped. No game launched or authored project data changed; gameplay queue remains deferred.


### 2026-09-12 Persistent export history and integrity verification

- Added project-local export history with completed/incomplete status, authored-input comparison, saved-input location and explicit on-demand disc/snapshot hash verification. Reading history never implies gameplay acceptance.
- Four focused tests passed, including corruption and path rejection; actual browser HTTP workflow verified the saved town01 disc hash f8a75661a02acd537257029a9df9e7e79ec1703b766a942a333e63c217e04f97. Screenshot inspected at local-output/sdk-20260909/export-history-20260912.png.
- Browser test used an isolated editor on port4406 and headless Edge, both stopped afterward. No game launched or user editor restarted. Shared physical MAN/container composition remains incomplete; broader SDK goal remains active.


### 2026-09-12 Deferred export input preservation

- Combined export regression suite: 29 tests, 28 passed and one skipped; no game launched.
- New exports retain a reopenable Inputs project, imported evidence and referenced authored model/TIM bytes, with per-file hash/readback inventory in the completion report. Live project save state and history remain unchanged.
- Added unsaved-draft snapshot reopen/independence regression and exposed the snapshot project path in the export result. Shared physical MAN owners remain rejected until full container relocation is supported.


### 2026-09-12 Combined asset disc fixture prepared

- Exported saved draft plus model0105 shape, clip0012 channel, TIM5/raw/0 payload, cell1833 scenery and one collision edit to combined-assets-export-20260912. Session47565 exited0. Final carrier/MAN/PROT checks passed; independently rehashed disc matches8e1fd5be2cc845c06aa6293964bd0b581a06d3db5d4c6a86c54d65c9bc0f805f.
- Added exact artifact contents and manual scope to the deferred gameplay queue. Removed an incidental test-file trailing blank line found by diff checking. No project Save or game launch.

### 2026-09-12 Descriptor verification regression

- Added synthetic scene-table test proving final descriptor position supersedes stale carrier offset and wrong descriptor type rejects without retaining success flags. Fixture includes the required MAN descriptor and canonical first payload offset.
- Asset/animation/routing checks:9 passed,1 optional retail test skipped. No game interaction or output artifact created.

### 2026-09-12 Model/animation/draft combination

- Composed model0105's one-coordinate shape edit and clip0012 frame0/object0 translation X100 with the saved NPC draft in one private archive. Final model carrier, descriptor-relocated animation carrier and decoded MAN all verified.
- This exercises simultaneous asset families rather than separate successful builds. No project Save, disc output or game launch. Full shared-carrier overlap support and gameplay acceptance remain open.

### 2026-09-12 Retail animation plus draft acceptance

- Applied actor0011's verified clip0012 frame0/object0 translation X100 through the project command and composed it with the saved draft. The final ANM carrier followed its relocated descriptor and matched exactly; MAN reopening also passed.
- Updated documented animation export scope. No project Save, disc output or game launch. Shared clip/gameplay effects remain deferred to the manual queue.

### 2026-09-12 Descriptor-relative animation verification

- Animation carrier audits now bind the original scene-table offset, descriptor index/type and physical owner. Final verification reparses that descriptor to locate the stream after internal MAN growth rather than using its stale relative offset.
- Existing asset/animation checks passed. Retail combined animation-plus-draft verification remains next; no game interaction or disc output.

### 2026-09-12 Animation channel export wiring

- Added existing-channel ANM patch preparation using the verified catalog and equal-span compression serializer. Draft composition now accepts validated actor AnimationChannels, includes resulting patches and requires final carrier verification.
- Routing/export tests passed. Retail animation-plus-draft composition remains unverified; MAN growth can shift ANM within the same physical owner, requiring descriptor-relative relocation handling before that case can pass. No game launch or disc output.

### 2026-09-12 Retail model shape plus draft acceptance

- Applied one source-valid vertex-X increment to town01 model0105 through ProjectService.set_model_replacement, then composed the model with the saved draft. Final relocated model carrier hash and reopened MAN both passed.
- Private content-addressed TMD created; project not saved, no disc export or game launch. Updated supported export scope. Model gameplay and shared-carrier composition remain separate outstanding work.

### 2026-09-12 Model shape draft-export integration

- Added source-verified model overlay preparation, reused common disc-to-archive carrier conversion, and wired model source scenes/patches/final carrier verification into draft export. Shared overlapping carriers still reject pending joint decoding/composition.
- Model authoring and draft routing/export tests passed; module compilation passed. Retail model-plus-draft composition remains next. No project Save, disc output or game launch.

### 2026-09-12 Combined scene asset archive acceptance

- Ran private town01 composition with decoration cell1833 Z-256, one collision-bit toggle, TIM5/raw/0 edit and saved NPC draft simultaneously. Final relocated MAP, texture carrier and decoded MAN all verified; exactly one scenery and one collision change remained audited.
- Updated native actor export documentation with current composition scope and model/animation gaps. No project Save, disc output or game launch. The combined archive check does not replace a future hash-identified manual fixture.

### 2026-09-12 Relocated asset verifier regression

- Added synthetic verification of a carrier resolved through a shifted TOC entry, plus corruption rejection. Verification flags are now cleared before checking and published only after every asset passes, avoiding retained success flags on failed revalidation.
- Eight asset/routing/archive/export checks passed; the focused flag-recovery regression also passed after the fix. No game interaction or disc output.

### 2026-09-12 Final texture carrier verification

- Texture preparation now records physical owner/relative span and rejects carriers crossing physical boundaries. Single/multi-scene exports reread final relocated carrier bytes and require the authored hash; audits distinguish payload verification from MAP verification.
- Private retail TIM5/raw/0 plus draft passed final carrier equality after MAN relocation. No disc output or game launch; shared-carrier internal relocation remains fail-closed pending composition support.

### 2026-09-12 Texture replacements composed with drafts

- Draft exports now route texture bindings by source scene, including texture-only scenes, and compose their source-verified archive patches before MAN growth. Texture changes remain separate in each scene audit. Shared overlapping carriers still reject.
- Private town01 TIM5/raw/0 payload edit plus saved draft composed with one texture change and exact MAN reopening. Private content-addressed TIM file created; no project Save, disc export or game launch. Final relocated texture reread remains next.

### 2026-09-12 Texture archive patch preparation

- Added sdk.texture_build adapter for existing verified TIM replacement serializers. It validates imported source metadata and private payload hashes, converts disc-relative overlays to PROT-relative spans and checks original carrier bytes and archive bounds.
- Module compilation passed. Retail texture composition and draft-path wiring remain next; no runtime interaction or output artifact created.

### 2026-09-12 Scenery/collision/draft composition acceptance

- Private retail fixture combined decoration cell1833 Z-256, one collision-bit toggle and the saved NPC draft. One scenery and one collision change survived final relocated MAP hash verification; MAN reopening also passed in121255936-byte archive.
- Added equal-span patch regression for exact output, order independence, overlap, bounds and stale preimage rejection. Archive/environment/routing tests passed. No Save, disc output or game launch; combined gameplay remains deferred.

### 2026-09-12 Final relocated MAP verification

- Added final TOC-based MAP rereads for single- and multi-scene draft exports. Full authored MAP span hashes must match after all MAN growth; successful audits gain reopened_map_verified.
- Retail collision-plus-draft archive passed final MAP equality. Deliberately incorrect expected MAP hash rejected. No game interaction or disc output; gameplay checks remain deferred.

### 2026-09-12 MAP edits integrated with draft archive rebuilding

- Single- and multi-scene draft paths now gather scene-level scenery/collision MAP patches and apply them to the original archive before MAN growth. Source archive hashes remain distinct from composed archive hashes; per-scene MAP audits are retained. Unsupported scene components still reject.
- Private collision-bit override plus saved town01 draft composed successfully with one audited wall change and reopened MAN equality. Six routing/export/archive tests passed. Final relocated MAP reread and scenery combination acceptance remain next; no game interaction or disc output.

### 2026-09-12 Shared MAP patch preparation

- Added sdk.map_build.prepare_map_patch using existing source-validated scenery/collision serializers. It merges collision masks into scenery output with overlap rejection and emits one equal-span source-hashed archive patch plus separate audits.
- Private retail collision-bit toggle produced exactly one audited wall change in an unchanged-size MAP. Archive/draft integration remains next; no Save, disc output or game launch.

### 2026-09-12 Equal-span archive asset composition primitive

- Reviewed existing MAP/scenery/collision serialization and added source-addressed archive span composition for use before MAN relocation. Requires exact original span hashes, bounded immutable bytes and disjoint spans; shared containers must be composed before calling.
- Synthetic check passed exact output, deterministic request ordering and overlap rejection. MAP integration remains next; no disc output or game interaction.

### 2026-09-12 Edit-only scene regression

- Added routing coverage proving an edited scene without drafts receives its authored changes with no invented actor identity, and that a concurrent position change rejects the assembled result. Updated documented export scope accordingly.
- Multi-scene routing, export and archive tests:6 passed. No runtime interaction; queued manual acceptance remains deferred.

### 2026-09-12 Include edited scenes without new drafts

- Draft archive composition now includes imported scenes referenced by authored overrides even when they contain no drafts. Those scenes serialize original-record edits without fabricating an appended actor; unknown scene ownership still rejects.
- Private town01 draft plus town0c existing actor X edit passed both rebuilt MAN checks; town0c audit contains zero drafts and exactly one placement change. Routing/export tests passed. No Save, disc output or game launch.

### 2026-09-12 Two-scene disc export acceptance

- Exported town01 and town0c drafts through the full archive/disc pipeline into local-output/sdk-20260909/multiscene-draft-export-20260912. Session72659 exited0; both MAN rebuild checks and final PROT reopen passed. Independently rehashed disc matches dd54463f70ad4b183b7f4033352b9999dbb3421ce5b719c187d5345683e57c10.
- Updated export documentation for current multi-scene scope and remaining explicit rejections. Project edits were in memory only; no game launch. Manual multi-scene gameplay remains deferred.

### 2026-09-12 Multi-scene routing and audit semantics

- Scene subreports now identify prepared MAN inputs rather than falsely retaining the untouched PROT hash as a scene rebuild result. Added cross-scene disc identity agreement and restored explicit draft-ID type validation.
- Routing regression verifies each scene receives only its own overrides/drafts, source state remains unchanged and unrelated-scene edits reject before rebuilding. Routing/archive/export checks:5 passed. No game interaction.

### 2026-09-12 Multi-scene project draft composition

- Connected draft-bearing scenes to deterministic multi-owner archive rebuilding with per-scene source/override validation, shared archive equality and whole-project freshness checks. Edits outside draft-bearing scenes still reject; shared physical owners and secondary PROT headers remain unsupported. Updated export progress text to describe project-wide drafts.
- Private town01 plus town0c drafts produced121257984 bytes with both MAN entries independently reopened exactly. No Save, disc output or game interaction. Full multi-scene disc/browser acceptance and remaining asset composition continue separately.

### 2026-09-12 Multi-owner MAN archive rebuild

- Added deterministic batch rebuild for distinct physical MAN owners, resolving each stable entry index against the relocated archive and independently reopening its decoded MAN. Duplicate owners reject pending shared-container composition.
- Three archive tests pass, including two growing containers, reversed request order, relocated TOC and preserved trailing payload. Synthetic fixture was corrected to accommodate production overlapping read windows and preserved container padding. Project multi-scene wiring remains next; no game interaction.

### 2026-09-12 Deferred gameplay queue and continued implementation scope

- User explicitly requested all work that does not require immediate gameplay verification continue, with manual checks saved for later. Added docs/legaia-gameplay-verification-queue.md separating the hash-identified ready NPC disc from features still needing dedicated fixtures, and recording manual steps/expected results without claiming runtime acceptance.
- Reviewed PROT rebuild and existing texture overlay interfaces for remaining container composition. No game launch, process restart or new runtime claim. Gameplay gaps do not block independent implementation.

### 2026-09-12 Transition append regression acceptance

- Added structural-append transition regression covering two requested entry bytes, exact relocated offset changes, unchanged surrounding content, modified-preimage rejection and immutable original source.
- Transition importer/build/project plus draft HTTP checks:11 passed. No retail disc output or game interaction. These tests do not extend gameplay acceptance.

### 2026-09-12 Transition arrival edits composed with drafts

- Connected supported actor/P2 Transitions entries to draft export with exact component structure, source owner validation, retail MAN guard and rebased operand writes. The archive audit retains transition changes separately.
- Private saved draft plus town01 P2[0] arrival-X97 produced121255936 bytes with exactly one transition change and exact reopened MAN verification. No Save, disc output or game interaction. Other override families, multi-scene builds and runtime acceptance remain open.

### 2026-09-12 Transition entry rebasing prototype

- Existing transition authoring edits encoded arrival X/Z/direction, not destination names. Added patch_appended to relocate those verified operand bytes by original record identity with extent/preimage/layout guards and dual-offset audit.
- Real town01 MAN after donor11 append changed exactly one requested P2[0] entry-X byte96->97 at source offset+3. Draft archive integration remains next; no disc write or game interaction. This does not establish runtime transition acceptance.

### 2026-09-12 Export progress retention and error recovery

- Prevented Close/Escape from dismissing the export dialog during an active request, which otherwise hid the completed artifact paths. Completion or failure restores Close and editor controls.
- Isolated browser with delayed400 response verified Escape retains progress, Close remains disabled while pending, the actual error appears and controls recover afterward. Browser closed and temporary server92627 stopped. No disc output or game interaction.

### 2026-09-12 Real browser-to-disc draft export acceptance

- Clicked the real Inspector export button in isolated Edge with no intercepted response. HTTP completed, the dialog displayed completion, and the produced report confirmed exact reopened MAN/PROT. Independently streamed SHA256 of the output matched f8a75661a02acd537257029a9df9e7e79ec1703b766a942a333e63c217e04f97, identical to the earlier CLI export.
- Private report: actor-draft-persistence-check/Builds/experimental-drafts-1d81808d84844b5fa04eb9392b6bda28/report.json under local-output/sdk-20260909. Browser process22157 exited0; temporary server53188 stopped. No project Save or game launch. Script scheduling and gameplay remain unverified.

### 2026-09-12 Draft export browser workflow acceptance

- Isolated Edge editor session selected the saved draft and clicked Export experimental disc. A delayed intercepted export response verified exact authored UUID request, disabled export control, visible build progress and completed report path/hash presentation. Dialog closed normally.
- This browser test mocked only the export response, creating no disc. Real CLI export and HTTP handler acceptance remain separate evidence above. Browser closed and temporary server75058 stopped; no game interaction or project Save.

### 2026-09-12 Draft export HTTP contract acceptance

- Added an actual loopback HTTP regression with only the expensive export writer mocked. Verified200 completed response and project-contained report path,400 for missing/unknown/wrong-type identities, client output-path injection and Live-mode export. Writer called once and normal last_build remains unset.
- Test passed and its server/thread closed. This verifies routing/service guards, not a real disc write through HTTP or rendered browser interaction. No game interaction.

### 2026-09-12 Draft Inspector export control

- Added Export experimental disc to the draft Inspector with Edit-mode/busy gating, progress dialog, completed disc/report paths and SHA256, and explicit gameplay status. Uses the dedicated service endpoint without invoking Run. Corrected stale effective-donor preview wording to the implemented retail assignment behavior.
- JavaScript syntax check passed. Actual HTTP/browser acceptance remains next; no game launch or export executed this turn.

### 2026-09-12 Editor service draft export endpoint

- Added /api/export/actor-drafts with exact draft identity input, Edit-mode/active-scene guards and a project-contained unique Builds directory. Returns completed report/disc paths and output hash, explicitly experimental; does not launch or replace normal last_build.
- Mocked service check passed project output containment, result labels and rejection in Live mode before export. Browser control and real HTTP acceptance remain next. No game interaction or disc output in this check.

### 2026-09-12 Draft export checkpoint

- Reviewed scoped worktree changes and passed git diff --check. Checkpoint includes deterministic batch appending, saved-draft archive/disc export, appearance/dialogue composition, retail donor preview bindings and focused regressions. Private disc/project outputs remain excluded.
- Existing focused test and private export evidence above remains bounded; editor Play, additional override families, multi-scene composition and complete runtime acceptance remain open. No game interaction or remote push.

### 2026-09-12 P2 dialogue append regression

- Extended synthetic P2 dialogue coverage through the production structural donor append, then verified the relocated glyph span, all surrounding bytes and parsed actor placements. The fixture's short controller record prevents full script-reindex candidate acceptance, so this test explicitly covers structural append composition; the private retail candidate check remains separate evidence.
- Dialogue importer/build/export checks:13 passed,3 optional retail checks skipped. Initial full-candidate fixture attempt rejected on script coverage as designed; no production guard was relaxed. No game interaction.

### 2026-09-11 P2 dialogue composed with drafts

- Draft archive composition now recognizes exact same-scene P2 script identities for Dialogue only; source context verifies record existence and run ownership. Actor-only components on P2 identities reject.
- Private town01 P2[37] dialogue edit composed with the saved draft into121255936 bytes, with exact reopened MAN verification and audited glyph offset44605->44608. An injected P2 Transform override rejected. Updated export support documentation. No Save, output disc or game launch; gameplay remains unverified.

### 2026-09-11 Original actor dialogue composed with drafts

- Connected supported original actor Dialogue runs to draft archive serialization with owner validation, source baseline guard and relocated glyph-span application after appearance/placement edits. Audit separates dialogue changes and their semantic owners. P2 dialogue and other component families remain unsupported in this path.
- Private retail composition combined the saved draft, actor49 donor15 appearance and one equal-span dialogue replacement. Exactly2 appearance changes and1 dialogue change entered a121255936-byte archive with exact reopened MAN verification. No Save, disc output or game launch.

### 2026-09-11 Dialogue rebasing for appended actor tables

- Added verified equal-span dialogue patch rebasing by original record identity and relative glyph offset. It checks record extent, exact glyph preimage and unchanged MAN layout, retaining original and relocated offsets in the audit. Original source dialogue validation still owns allowable text and control boundaries.
- Synthetic grown-table check verifies only the relocated five-byte text span changes and rejects an already-modified preimage. Dialogue importer suite:9 passed,1 optional retail test skipped. Draft archive wiring remains next; no game interaction.

### 2026-09-11 Batch draft regression and combined checks

- Added synthetic batch coverage proving byte-identical output and audit under reversed input ordering, stable authored identity to record mapping, exact independent X/Z placements, duplicate identity rejection and rejection of donors that exist only after appending.
- Combined actor structure, script reindex, appearance assignment, scene preview, draft lifecycle and export tests:22 passed,1 optional retail test skipped. No runtime launch. These checks retain explicit incomplete script/scheduling and gameplay status.

### 2026-09-11 Saved draft end-to-end disc export

- Ran the new CLI against the private saved one-draft project. Session44160 exited0 and published local-output/sdk-20260909/saved-draft-export-20260911/report.json plus draft.bin. Output466716768 bytes, SHA256 f8a75661a02acd537257029a9df9e7e79ec1703b766a942a333e63c217e04f97, independently rehashed after completion.
- Report confirms reopened MAN and PROT equality and one authored draft. Documented export invocation, supported composition and incomplete-output semantics. No game launch; script/scheduling and gameplay acceptance remain open. This does not validate every non-PROT sector independently for this new image.

### 2026-09-11 Experimental saved-draft disc export entry point

- Added export_draft_disc and a module CLI accepting saved project, draft UUID and a new output directory. It connects archive composition to the existing verified disc writer and publishes report.json only after successful write and unchanged full authored identity. Existing directories reject; failed artifacts remain diagnostic and no game is launched.
- Synthetic export test passed for successful report publication, overwrite rejection and concurrent-edit rejection without a completion report. CLI help passed. Full saved-draft disc export and gameplay remain unverified; editor Play integration remains open.

### 2026-09-11 Complete draft build-input freshness guard

- Draft serializer now snapshots the shared authored build identity, copies imported donor evidence and checks the complete identity before returning an archive. Previously only drafts and actor overrides were compared, allowing a concurrent texture/model/import/source change to escape the completion guard. Audit now includes the authored state key.
- Injected a texture edit after the real private archive rebuild: serialization rejected the completed result with ProjectError instead of returning stale output. No project Save, disc write or game interaction. This addresses freshness, not support for those additional override families.

### 2026-09-11 Draft preview donor assignment parity

- Found draft viewport copied the donor's effective appearance while serialization intentionally clones its retail assignment. Geometry decoding now retains a retail binding for appearance-overridden actors; drafts use that binding without altering the original actor's effective preview.
- Scene preview regression creates a draft from an appearance-overridden target and verifies original geometry/source identity, authored placement and geometry cache reuse. All5 scene preview tests pass. Shared authored asset edits can still affect preview and remain explicitly identified; no game interaction or browser acceptance this turn.

### 2026-09-11 Appearance assignments composed with NPC drafts

- Draft archive serialization now accepts same-scene ActorAppearance alongside X/Z overrides. It checks the exact selected donor against the verified assignment context, guards the retail MAN baseline and applies relocated header edits after donor appending. Audit includes donor identity and both header offsets.
- Private saved-draft project composed actor49's donor15 assignment (model103/animation15 to94/18) into a121255936-byte archive with reopened MAN equality. Both header offsets shifted by3; archive following payload preservation passed. No project Save, output disc write or game interaction. Playable Build integration and other override families remain open.

### 2026-09-11 Appearance patch rebasing for grown MAN tables

- Added ManAssignmentContext.patch_appended to validate appearance assignments against the retail context and resolve original actor header offsets in a grown MAN. The audit retains both source and relocated offsets; changed header preimages reject. Appended donor appearances are not implicitly changed.
- Synthetic table-growth regression verifies exactly two relocated bytes change and rejects a mismatched baseline header. Assignment suite: 7 passed, 1 optional retail test skipped. Draft archive wiring and retail composition verification remain next; no game interaction.

### 2026-09-11 SDK status report refresh

- Reviewed the feature matrix, release parity report and latest work log for the user's status request. Updated the matrix's draft row to include accepted X/Z gizmos and the same-scene logical archive prototype.
- Playable draft Build integration, complete script/scheduling coverage and broader runtime acceptance remain open. This documentation refresh ran no game or new runtime tests.

### Existing actor placements composed with drafts

- Draft archive serialization now accepts same-scene X/Z actor overrides and applies them to original record indices after draft append. Audit separates existing placement changes from appended records and includes final MAN hash; other component/scene mixtures still reject.
- Private donor0011 X3264 override composed with draft X3008 and exact reopened MAN verification. No Save/disc write/game interaction. Remaining override families and multi-scene composition are still open.

### Multiple project drafts serialized together

- Saved-draft serializer now gathers all same-scene drafts, validates each donor and passes stable IDs into batch MAN appending. Version2 audit maps every authored draft to its generated record. Changed draft collections reject after serialization.
- Private two-draft project produced records53/54 and reopened MAN equality in a121255936-byte logical archive. No Save/disc write/game interaction. Multiple scenes and other authored override composition still reject explicitly and remain implementation work.

### Deterministic batch actor candidates

- Added append_actor_candidates with unique authored IDs, original-source donor validation and stable identity ordering. Each append rebases reached references against the current MAN, including previously appended records.
- Retail two-donor check produced records53/54 at requested positions and byte-identical output when request order reversed. Opaque script coverage remains unverified; batch project serialization is the next integration step. No disc write/game interaction.

### Saved draft to logical archive

- Added sdk.draft_build.prepare_draft_archive connecting persisted authored UUID/donor/XZ to source-verified MAN append and logical PROT rebuild. Audit retains draft metadata, imported document digest, source disc/PROT hashes and structural/encoding evidence.
- Private saved draft produced121255936 bytes and exact reopened MAN verification. Current prototype rejects multiple drafts and other overrides rather than silently omitting them; composing those remains required for full Build support. No output write or game interaction.

### Draft Z handle and gesture cancellation acceptance

- Isolated browser moved draft Z5440->5504 with X3008 unchanged, verified exact-grid command and Undo restoration. Separate Escape-during-X-drag check issued no command and left saved position unchanged.
- Temporary server68527 stopped; no Save/game interaction. Draft editor checkpoint follows; playable new-NPC output remains unfinished.

### Draft gizmo browser acceptance

- Inspected draft-handles-20260911.png showing main Inspector and X/Z handles on the rendered draft. Isolated browser dragged X from3008 to3072, verified set_actor_draft_position with unchanged Z5440 and64-unit alignment, then Undo restored3008.
- Temporary server77847 stopped; no Save/game interaction. Z-axis drag, broader gesture cancellation and playable integration remain unverified.

### Draft transform handles

- Extended movable selection and handle drawing to authored NPC drafts. Drag preview uses the draft identity; release dispatches set_actor_draft_position with the untouched other axis. Draft handles use64-unit snapping to match serialized placement constraints, documented in Inspector.
- JavaScript syntax passed. Actual drag/Undo browser acceptance remains pending. No runtime interaction or project Save.

### Draft workflow regression checks

- Added two synthetic draft lifecycle checks covering create/edit/delete, undo/redo, Save/Open, immutable donor evidence, build-key invalidation, explicit Build rejection and invalid-input mutation isolation.
- Ran with existing project workflow and candidate service checks:10 passed. Updated feature matrix with the accepted draft editor workflow and remaining playable integration work. No game interaction.

### Saved draft candidate browser acceptance

- Added stable busy-state handling to the draft candidate button. Isolated browser verified saved draft X3008/Z5440 report, absence of duplicate creation form and script navigation to imported donor0011. Temporary server10300 stopped; no Save or game interaction.
- Updated native actor report with persistent draft UI/viewport/inspection workflow and current Build/runtime limitations. Full SDK goal remains active.

### Saved draft candidate inspection

- Connected draft IDs to source-bound candidate service using validated same-scene donor and draft X/Z, with explicit authored_npc_draft_candidate representation. Main Inspector now offers Inspect serialized candidate; donor script navigation resolves the imported donor and duplicate creation form is omitted for drafts.
- Fresh saved-draft service call passed exact identity/position and physical encoding; JavaScript syntax passed. Browser verification of this new route remains pending. No disc write or game interaction.

### Draft build identity and donor reimport protection

- Found build snapshot identity omitted new drafts. Added drafts so authored creation/edits invalidate previously built packages; private position/Undo check confirmed exact key changes and restoration.
- Changed reimport now rejects active drafts or draft undo/redo history tied to the scene, preventing donor evidence from silently changing. Both active and deleted-with-history cases passed. No Save/build/game interaction.

### Draft Inspector editing and focus acceptance

- Added draft support to toolbar Focus/F shortcut and busy-state reset for authored controls. Isolated browser completed repeated command edits and Focus. Exact imported-row label in harness timed out; text-filter retry verified imported selection clears draft Inspector.
- Temporary server15881 stopped; no Save/game interaction. Draft main Inspector workflow now has bounded browser acceptance; transforms via gizmo, runtime scheduling and playable Build remain open.

### Draft main Inspector integration

- Previous turn verified rendered drafts/picking. Draft hierarchy and viewport clicks now select a dedicated authored draft in the main Inspector, with identity/donor evidence, X/Z command editing, frame and delete controls. Imported actor selection and environment selection clear draft selection; draft selection suppresses imported transform tools.
- JavaScript syntax passed. Browser acceptance of this main-Inspector revision remains pending, including selection lifecycle and editing refresh. No game interaction.

### Draft viewport visual and picking acceptance

- Isolated browser verified hierarchy->Frame draft, inspected local screenshot draft-viewport-20260911.png showing two separate donor/draft models, and clicked the rendered draft to open its exact authored controls. First workflow reported zero page errors.
- Updated UI copy now that draft rendering is verified. Temporary server11680 stopped; no Save/game interaction. Main inspector integration and playable Build remain unfinished.

### Draft hierarchy and viewport routing

- Previous turn added draft preview instances. Added active-scene draft hierarchy rows, focused draft-management opening from viewport hits and Frame draft camera action. Draft hits no longer go to imported-actor selection, which rejects authored IDs.
- JavaScript syntax and diff checks passed. Actual browser visual/picking acceptance remains pending; draft controls are currently a focused dialog rather than the main component inspector. No runtime interaction.

### Draft scene geometry projection

- Added scene-preview instances for active-scene drafts using effective donor geometry, explicit authored identity/position and source-ground sampling without fabricating retail coordinates. Evidence distinguishes effective donor preview from retail candidate serialization. Draft transforms invalidate projection but retain geometry cache.
- Fresh scene-preview API returned262 entities including the saved draft at X3008/Z5440 and null retail position. Initial harness assumed every entity had kind; corrected optional-kind lookup passed. Temporary server32982 stopped. Browser visual/picking acceptance and playable integration remain open.

### NPC draft management panel

- Added toolbar draft count and panel listing stable identities/donors, X/Z editing and deletion through commands. Live mode disables edits. Browser check exposed a toolbar click accepted during an in-flight API call; tied the button to busy state and reran successfully.
- Isolated browser verified edit, reopen with new position, delete and Undo restoration. Temporary server81931 stopped; no Save or game interaction. Draft viewport and playable output integration remain open.

### Browser NPC draft creation

- Previous turn added draft position command. Candidate dialog now includes name and exact-grid X/Z inputs plus Create NPC draft using the normal command API, with scene-change guard and explicit draft/build limitations.
- Isolated browser created Browser NPC draft at X3136, closed the dialog on success and verified matching server draft state. No Save; temporary server22013 stopped and browser closed. Persistent draft display/edit UI, viewport and playable Build integration remain open.

### Draft position editing and dirty-section reporting

- Previous turn added persistent drafts. Added validated set_actor_draft_position command with identity preservation, undo/redo and no-op suppression. Included drafts in saved-section accounting so UI can identify unsaved new-NPC changes.
- Private saved draft check passed position change, undo to clean state, redo and no-op history preservation. No Save or game interaction. Draft creation UI, viewport and playable Build remain unfinished.

### Persistent authored NPC drafts

- Previous turn checkpointed source. Added stable authored UUID drafts with imported donor/scene, exact X/Z and name; create/delete commands use undo/redo and serialize separately from retail entities. Open validates drafts and state exposes them. Build rejects drafts explicitly until integrated, preventing silent omission.
- Private create/undo/redo/save/reopen check passed with stable identity. Initial fixture copied a model override without its asset after changing root; removed that unrelated override from the private in-memory fixture and reran successfully. User project unchanged. Viewport/hierarchy/UI creation and playable integration remain open.

### Candidate and disc implementation checkpoint

- Previous turn browser-verified placement inheritance and authored coordinates. Ran the focused structural/reindex/container/physical-layout/ISO/service checks together:15 passed. Updated feature matrix to include experimental disc output and its acceptance limits.
- Checkpoint scope contains only SDK/framework source, synthetic tests and documentation; private disc and reports remain outside staging. Full SDK goal remains active: persistent new-entity authoring, script completeness and gameplay acceptance are not established by this checkpoint.

### Candidate placement browser acceptance

- Previous turn added explicit placement labels. Isolated Edge against temporary editor4406 verified retail inheritance text and donor-script navigation without page errors. Applied unsaved X3008 to actor0011 in the temporary project session and verified the authored coordinate label.
- First authored harness used an exact button label changed by authored state and timed out; selecting via stable actor ID passed. Test browsers closed and temporary server37121 was stopped. No Save, user editor change or game interaction.

### Candidate override reporting and service isolation

- Previous turn forwarded authored placement. Added a focused service check proving only X/Z reaches candidate construction, authored Y/appearance remain explicitly excluded, missing actors reject and project/undo state is unchanged. The check passed.
- Candidate dialog now lists exact included coordinate values and excluded authored components/axes outside the technical JSON. Browser validation remains pending; persistent new-entity commands and gameplay scheduling are still open.

### Candidate inspection consumes authored placement

- Previous turn added appended-record positioning. Connected optional position through importer inspection and the editor service, taking only selected actor authored X/Z. Report names included overrides, excluded components and excluded transform axes explicitly; browser copy distinguishes positioned candidates from retail placement.
- Fresh retail positioned donor11 inspection and physical container encoding passed; editor JavaScript syntax passed. Browser workflow remains unverified for this addition. No entity is created or saved by inspection, and no disc/game interaction occurred.

### Explicit placement for appended actor candidates

- Previous turn fixed integration imports and checked ISO transforms. Reviewed existing project templates/commands; added optional X/Z placement to append_actor_candidate through the existing exact retail placement serializer, with byte-change audit and structural-layout preservation.
- Retail donor11 candidate record53 accepted X3008/Z5440. Exactly one placement byte differed from the unpositioned candidate; unsupported Y, off-grid X and boolean X rejected. Existing NPC records were unchanged relative to the base candidate. No project persistence, disc rewrite or game interaction in this turn; command/viewport integration remains open.

### Disc integration import and ISO regression checks

- Previous turn validated experimental output. Fixed disc writer's dependency on launching from repository root: it now resolves the generic sector codec relative to its source checkout. Verified import/codec loading from local-output with only integrations/legaia on PYTHONPATH.
- Added3 focused synthetic ISO checks covering relocated root and nonstandard path-table locations, both endian formats, exact zero-growth behavior, boundary extents, padding/truncation and overlapping/mismatched records. All passed. No new disc write or runtime interaction.

### Generated disc content and encoding validation

- Previous turn emitted experimental donor11 disc. Compared source/output directory inventories (47 entries), sizes/relocated extents and all44 non-PROT file hashes. Compared139219 unchanged-sector payload/protection regions exactly across relocation. Saved metadata-only preservation report beside private image.
- Reopened through normal scene lookup and verified exact regenerated donor11 MAN, SHA256646b9d6183a999e59160ef3e7d401c207a13f40c26d533780b230d81111221de. Checked all59215 regenerated PROT/metadata sectors with the encoder; process5516 exited0. This is internal parity verification, not an independent encoder oracle or gameplay acceptance. Initial harness import error was corrected before execution.
- No game interaction. Actor scheduling/reference completeness and project authoring integration remain unfinished.

### Experimental actor disc emitted and reopened

- Previous turn integrated ISO metadata relocation. Implemented streaming write_grown_prot_disc: exclusive new destination, source disc/PROT hashes, bounded metadata transforms, full EDC/ECC, MSF relocation and reopened PROT equality. Retail framing inspection found59205 ordinary subheaders and one terminal subheader; the writer preserves the terminal distinction.
- Actual donor11 candidate rebuilt and wrote local-output/sdk-20260909/native-actor-disc-20260911.bin; process64639 exited0. Output466716768 bytes, SHA256325db468440bd9246181de2e70290fb17e8431131de0043b87b9449d1ab4a56a. One sector growth,8 ISO metadata sectors, reopened PROT exact. Source disc hash rechecked unchanged.
- No game launch/input. Full-image independent validation, script completeness, runtime scheduling and project Build integration remain open; experimental output is not gameplay-accepted.

### Integrated ISO metadata relocation pass

- Previous turn verified generic sector parity. Connected PVD, path tables and bounded recursive directory traversal into collect_metadata_relocation, returning changed logical sectors keyed by original LBA for the upcoming streaming writer.
- Source-preimage and overlapping-patch conflict checks preserve composed sector edits; directory aliases, record boundaries and traversal limits are checked. Retail one-sector growth produces8 changed metadata sectors at16,18,19,20,21,22,59448,138777 across53 records/3 directories/4 tables. Zero growth produces no changed sectors.
- No disc output or game interaction. Streaming output and full-image reopening remain next; actor runtime acceptance is still open.

### Generic Mode 2 sector encoding

- Previous turn implemented PVD relocation. Added tools/cd_sector.py with generic Form1 EDC/P/Q encoding and bounded BCD MSF address relocation. Existing prepare_disc.py zeroes ECC, so it was not sufficient for this writer. Cross-checked layout and parity parameters against pinned iso/write.rs.
- Fresh comparison reproduced521 retail sectors byte-for-byte (ISO front matter plus512 PROT sectors). Relocating each header by one LBA preserved valid EDC/P/Q and every byte outside the address. No source disc mutation or game interaction.
- Integrated streaming disc output, full-image verification and project Build remain outstanding.

### Primary volume descriptor relocation

- Previous turn implemented path-table relocation. Added the PVD transform for matching dual-endian volume size, derived table pointers and embedded root record, with block-size, overlap and overflow validation.
- Retail one-sector growth updated volume198433->198434 in both copies and preserved all other PVD bytes; zero growth was byte-identical. A deliberately mismatched volume copy rejected. Physical sector serialization and integrated disc verification remain open; no disc write or game interaction.

### ISO path-table relocation

- Previous turn implemented dual-endian directory relocation. Added primary-descriptor path-table discovery and bounded endian-aware path-table transforms, preserving identifiers, parent references and padding; malformed records and overflow reject.
- Fresh retail check read all four locations from the PVD (18,19,20,21), relocated MOV/XA by one sector and confirmed all four decoded tables agree. Zero-growth output preserved each source table exactly. PVD size/address rewriting and physical sector serialization remain open; no disc write or runtime interaction.

### ISO directory relocation preserves dual-endian metadata

- Previous turn completed logical candidate archive roundtrip. Added iso_relocation.relocate_directory_record to grow the exact PROT file record and relocate later extents at the insertion boundary, updating both endian copies while preserving unrelated fields.
- Rejects mismatched endian fields, overlapping allocations, unsupported extended/interleaved/multi-extent records and integer overflow. Fresh retail traversal checked53 records in3 directories:46 changed for one-sector growth; both endian copies agree and zero-growth output equals every original record. Original retail endian fields were confirmed consistent.
- Physical sector writer, PVD/path-table transforms and integrated disc output remain outstanding. No source disc write or game interaction.

### 2026-09-11: actor candidate through rebuilt logical archive

- Previous reporting turn refreshed the feature matrix; resumed implementation by composing MAN encoding, sector padding and raw TOC relocation in prot_rebuild.rebuild_man_entry.
- The function reopens the rebuilt archive through the production parser, resolves the target scene table and independently decompresses the MAN, requiring exact candidate equality. Source hash, physical ownership and caller/header agreement remain checked.
- Fresh retail donor11 append passed the composed path: one sector growth,1229 relocated starts and exact reopened MAN equality. All work stayed in memory; no disc image emitted, project mutation or game interaction. Disc serialization and complete actor scheduling/reference acceptance remain open.

### SDK status report lookup

- Read current FEATURE_MATRIX.md, release parity summary and native actor candidate report for the user's status-report request. Updated the matrix's candidate row to include logical PROT relocation and distinguish the unfinished disc-level writer.
- These reports document bounded acceptance, not full SDK completion. No runtime interaction or new build validation performed in this reporting turn.

### Logical PROT growth implementation

- Previous turn made progress by verifying physical ownership and reviewing the reference disc writer. Implemented source-hashed, sector-aligned physical replacement and downstream raw TOC relocation in prot_rebuild.py; malformed/nonmonotonic tables, unknown successor, shrink and stale source reject.
- Retail in-memory entry4 growth check shifted1229 starts, including index1233 end sentinel59206->59207, and preserved all following payload bytes. Raw TOC is required because the importer read-window list excludes that sentinel. No disc output or game interaction.
- Added focused synthetic coverage for no-op, preserved adjacent payloads, shifted sentinel, terminal zero and invalid inputs. Full disc relocation and actor Build integration remain outstanding.

### Physical span verification and disc relocation review

- Previous clarification turn recorded the user's interior-placement constraint; this turn resumed source-bound actor work. Fresh donor11 inspection confirmed physical entry4,227328 source bytes,229376 rounded candidate bytes and one-sector growth.
- Added focused synthetic checks for boundary ownership, overlapping read windows, missing successor rows, unresolved tails and ambiguous physical spans. Candidate remains read-only and not build-ready.
- Reviewed pinned iso/relayout.rs and rando/disc.rs: full growth requires downstream TOC, sector framing/checksums and ISO reference updates. Reference writer hardcodes path-table locations and visibly patches only LE directory extent/size fields; documented these limitations before implementing a disc writer. No game launch/input or disc write.

### User clarification: side-of-map interior NPC placements

- User reports that the remaining NPCs appear correctly placed inside houses beside the map. Treat this as a placement hypothesis to verify against interior geometry and live actor identity, not evidence of a global coordinate error.
- Preserve authored NPC coordinates; do not automatically ground or move actors based on missing exterior floor geometry. No game launch or input performed for this clarification.

### Physical entry candidate encoding
- Previous turn identified true scene owner entry4. Source-bound inspection now reads its exact consecutive-start physical span, passes the scene-table offset relative to that span to container encoding and reports sector-rounded candidate size/growth.
- Retail donor11 passed emitted table/MAN verification in physical entry4:227328 source bytes,229376 sector-rounded candidate bytes, one sector growth. Extended read-window bytes are no longer treated as the resizable candidate container. No archive/disc write or runtime interaction; downstream TOC/ISO relocation remains open.

### Physical scene owner identified
- Previous turn browser-verified candidate model navigation. Found pinned rando/disc.rs grow_prot_entries and entry_true_footprint_sectors: relocation uses consecutive-start physical spans, preserves index space, rewrites downstream TOC starts, then full ISO LBA relocation. Overlapping read windows are not the allocation spans.
- Retail town01 scene table resides at physical entry4 LBA243..354, offset0, although find_scene_bundle found it through entry2's extended read window at offset8192. This changes the next packaging action: target entry4's true span, not grow entry2's read window.
- Added bounded locate_physical_span with exact consecutive indices and ambiguity rejection; tails with missing next rows remain unresolved. No disc/runtime mutation. Full relocation still unimplemented.

### Candidate busy-state fix and model navigation acceptance
- Previous browser turn exposed a timing failure. Candidate Inspector button did not reflect busy state although its handler ignored clicks while busy. Added stable button ID and disabled-state updates during rendering/setBusy.
- Isolated Edge against temporary editor4406/session64576 now completed actor0011 selection, candidate inspection, Preview donor model, exact asset0105 request to /api/preview and RETAIL viewer state with zero page errors. Browser closed; temporary server stopped with terminal exit. No project Save or game interaction.

### Candidate model browser check incomplete
- Previous turn added model navigation. Temporary editor4406/session91971 and isolated Edge tests attempted the workflow. First harness waited for incorrect /api/model-preview instead of actual /api/preview and timed out; corrected run then timed out waiting for candidate model button. Browser acceptance is not established; investigate editor busy/selection timing and dialog contents next.
- Test browsers closed through finally; temporary server stopped with terminal exit. No project Save or game interaction. Do not claim model navigation accepted from syntax/API checks alone.

### Candidate model dependency navigation
- Previous turn added verified donor asset bindings. Candidate dialog now shows model identity and initial animation frame/channel metadata, with Preview donor model routed to the existing imported model viewer. Missing model/animation bindings remain explicit; scene changes reject navigation.
- Node syntax/diff checks passed. Browser model-navigation acceptance remains pending. No user server restart, project write or runtime interaction; full goal stays incomplete.

### Candidate donor asset dependencies
- Previous turn retained partial container diagnostics. Added freshly imported donor model reference and verified initial scene-animation asset bindings to candidate response, retaining unavailable status when animation binding is not established.
- Retail actor11 resolved model0105 and animation scene-anm0012 from original ID13. No geometry/payload export or project write; script-selected assets and runtime compatibility are not inferred. Full goal remains incomplete.

### Partial candidate inspection retention
- Previous turn added context-ID representability. Candidate inspection now retains verified actor/archive diagnostics if container encoding raises a supported-domain error, reporting supported false/reason/null growth instead of hiding all evidence. Structural source errors still fail normally.
- UI renders unavailable growth with the reason. Injected container failure under retail source inspection preserved actor53/archive overlap data and false build readiness; Node syntax passed. No runtime/project mutation.

### Context target representability
- Previous turn established reference spawn ID rules. Pinned field_channels::resolve_target explicitly excludes F8/FB special contexts and accepts byte-encoded targets. Added actor_context_reference_status to candidate audits, distinguishing ordinary byte IDs, known reserved targets and IDs outside byte range without claiming allocation validity.
- Focused checks passed town01 ID89, reserved F8/FB and ID256. These are diagnostics rather than invented global actor-count limits. No runtime or project mutation; full goal remains incomplete.

### Reference actor spawn rule established
- Previous turn strengthened container roundtrip. Pinned engine-core/field_channels.rs documents FUN_8003AEB0 calling FUN_8003A1E4 per P1 placement at scene entry; context bytecode base is record base and script ID=N0+record index. This is reference evidence, not our runtime acceptance.
- Candidate audit now exposes expected context ID89/entry PC for town01 appended actor. Reindex inventories expose extended-context target operands as a separate reference family requiring review, beyond opcode44 spawn indices.
- Retail inspection verified context ID89 and searched reached extended references in shifted P2 range. No runtime interaction; native spawn acceptance and full relocation remain incomplete.

### Emitted container verification
- Previous turn improved script coverage reasons. Container encoder now rejects descriptors pointing inside the table, reparses its emitted table, checks every type/size/offset against the intended relocation and independently decodes the emitted MAN payload.
- Synthetic container test and retail town01 donor11 inspection passed the stronger checks (368-byte growth unchanged). No archive packaging or runtime interaction; full goal remains incomplete.

### Explicit candidate coverage reasons
- Previous turn browser-verified donor navigation. Inspected project template validation: current scopes are position/appearance presets, not complete native actor definitions. Preserved that distinction rather than treating preset duplication as native creation.
- Reindex audits and partition inventory now expose each stop's PC/reason and opaque byte count, without raw script data. Candidate technical evidence therefore explains partial coverage instead of only labeling it partial. Four focused reindex tests passed. No runtime/project mutation; spawnable template semantics remain unfinished.

### Candidate-to-script browser acceptance
- Previous turn added script navigation. Separate Edge against temporary editor4406/session35130 selected actor0011, opened candidate diagnostics and followed Inspect donor script. Captured actor-script POST retained scene://town01/actors/man-p1/0011 and returned200; candidate dialog removed, script dialog opened/closed, zero page errors.
- Browser closed and temporary server stopped by Ctrl-C with terminal exit. No project Save or game interaction. Native actor creation and full SDK acceptance remain incomplete.

### Candidate-to-script navigation
- Previous turn verified all52 town01 candidate inspections. Added Inspect donor script to candidate diagnostics, connecting directly to the existing script/dialogue inspector with the same stable actor identity.
- Candidate request now aborts when closed and rejects scene changes before presenting results or opening donor script. Node syntax and diff checks passed; direct browser navigation acceptance remains pending. No project or runtime mutation.

### All town01 donor inspection acceptance
- Previous turn checkpointed work at073eddc2. Ran the integrated source-bound inspection across all52 town01 donors under one verified disc scope:52 passed, no rejected candidates, container growth24..1492 bytes.
- Every response retained read_only true/build_ready false. Updated native actor guide with measured scope. This verifies construction across donors, not runtime behavior or complete relocation. No project Save, persistent server or game interaction.

### Candidate workflow local checkpoint
- Previous turn updated the feature matrix and ran combined regressions. Preparing a scoped local checkpoint of source-bound actor candidates, script decoding/reindexing, container/PROT diagnostics, browser-verified Inspector control and previously verified authored OBJ iteration changes.
- Explicit source/test/docs paths only; private retail/Blender/game artifacts excluded. No push, project Save or runtime interaction. Native actor creation and the full SDK objective remain incomplete.

### Feature matrix and combined regression review
- Previous turn browser-validated candidate inspection. Updated feature matrix with its actual source-bound/structural/browser scope, remaining native creation requirements and user's interior-NPC observation without asserting unverified placement correctness.
- Reviewed pending authored OBJ source changes alongside candidate integration; ran focused OBJ, model authoring and script-inspection suites. No user editor/game restart or project Save. Full goal remains incomplete.

### Candidate browser workflow acceptance
- Previous turn verified HTTP. Started isolated test editor4406/session44088 and separate automated Edge. Initial exact accessible-name selector timed out before clicking actor; corrected to observed button text and reran against the same server.
- Browser selected actor0011, opened candidate dialog, verified368-byte growth, expanded technical evidence/build_ready false, closed dialog and observed zero page errors. Browser closed; temporary editor received Ctrl-C. No project Save or game interaction. Full actor creation remains incomplete.

### Candidate HTTP acceptance
- Previous turn added Inspector control. Opened the saved isolated model-shape test project in a temporary loopback EditorServer on an OS-assigned port. Actual HTTP POST by stable actor ID returned200 with matching identity/read_only true/build_ready false. Extra client path field returned400.
- Temporary server shutdown and socket close completed in finally; no persistent server restart, project Save or game interaction. Browser rendering remains unverified; full SDK goal stays incomplete.

### Inspector candidate diagnostics control
- Previous turn added stable-entity API. Added advertised actor_candidate_inspection capability and an Inspector button opening retail donor diagnostics: changed spawn references, partial script count, growth and overlapping archive count, with expandable metadata evidence.
- UI explicitly says no NPC is created and project overrides are excluded. Uses textContent for response data and discards results after dialog closure; no commands or writes. Node syntax and diff checks passed. Browser/HTTP acceptance remains pending; no user server restart or runtime interaction.

### Editor candidate inspection route
- Previous turn added source-bound importer diagnostics. Added /api/actor-candidate-inspection accepting only entity_id, resolved through the active scene's imported actor. Response marks retail_donor_candidate and includes_project_overrides false; no project command, asset creation or runtime write occurs.
- Direct editor-service retail smoke resolved actor11's stable identity and verified response identity plus false build readiness/override inclusion. HTTP/browser control still needs validation and UI integration. Full goal remains incomplete.

### Source-bound actor candidate inspection API
- Previous turn documented the integrated candidate pipeline. Added inspect_actor_candidate(disc, scene, donor_record_index), owning one verified disc scope and returning metadata-only actor/container/archive diagnostics with disc hash and pinned reference revision. Raw MAN/container payloads remain internal and nothing is written.
- Retail town01 donor11 inspection passed: new record53,368 bytes candidate growth, three overlapping archive entries, explicit read_only true/build_ready false. JSON output contained neither raw_hex nor encoded_hex payload fields.
- This is an importer API foundation for editor diagnostics, not a project command or playable build. Full goal remains incomplete.

### Native actor candidate integration handoff
- Previous turn established exact shared TOC provenance. Added docs/legaia-native-actor-candidates.md describing implemented API sequence, pinned evidence, measured retail outcomes and explicit remaining scheduling/reference/archive/project/UI/build acceptance work.
- Seven focused structural/reindex/container tests passed together. No runtime interaction or completion claim; candidate workflow remains development-only and full SDK scope is preserved.

### PROT shared TOC provenance
- Previous turn established overlapping read windows. Pinned crates/prot/src/archive.rs uses the same sliding TOC formulas as our parser; overlap is not introduced by a newly divergent size formula. The same TOC words contribute to multiple entry interpretations.
- Footprint inspector now exposes exact TOC word indices, byte offsets, values and indexed/footprint formulas. Retail entry2's three inputs were verified directly against raw TOC bytes and reproduced118 indexed sectors.
- No archive mutation. Independent entry resize remains unverified; shared TOC/reference handling must precede packaging. Full SDK goal remains active.

### PROT overlapping read-window constraint
- Previous turn verified container preservation. Inspected authoritative ProtArchive sizing: town01 scene buffer is entry2 LBA239/read118 sectors, while entry3 starts LBA240. Entry3 overlaps117 sectors of that read window. A scene-buffer roundtrip does not prove an independently resizable archive member.
- Added inspect_entry_footprint exposing all overlapping indexed read windows and explicitly false independent-resize verification. Retail check confirmed entry3 overlap. Container growth stays a development candidate, not an archive patch; relocation needs shared archive reference analysis.
- No source disc, project or runtime mutation. Broader goal remains active; other SDK work remains available while archive ownership is investigated.

### Container preservation regression
- Previous turn verified retail container growth. Fixed unchanged MAN encoding to retain original compressed bytes, and report moved descriptors only when growth actually occurs. Updated module description to reflect optional relocation.
- Added synthetic container test: exact no-op, default over-capacity rejection, opt-in growth, four-byte growth alignment, decompression equality and five subsequent payloads preserved at relocated descriptors. Test passed. No runtime or archive packaging; full goal remains incomplete.

### Container growth candidate roundtrip
- Previous turn implemented bounded slot encoding. Measured retail town01 slot24894 bytes, original re-encode24891, actor candidate25259: growth is not merely a baseline compressor regression.
- Added explicit allow_growth candidate mode: insert four-byte-rounded capacity, adjust following descriptor offsets, preserve following payload bytes exactly, update decoded size and expose external-container-size work. Default still rejects growth; build_ready remains false.
- Retail candidate roundtrip passed with368 bytes growth and four relocated descriptor offsets. Reparsed descriptor/decompressed MAN exactly matched candidate. No PROT archive resize/build integration or game interaction; opaque external references and script/scheduling gaps remain open.

### MAN container candidate encoding
- Previous turn integrated structural append and reached spawn rewrites. Inspected core scene descriptor parsing and pinned scene_asset_table encode_size_word: high byte type, low24 decoded size.
- Added encode_man_candidate with verified container/decoded hashes, unique descriptor and bounded slot checks, compression roundtrip, descriptor-size update and explicit build_ready false. It preserves container length and rejects compressed growth beyond the existing slot.
- Retail town01 donor11 candidate exceeded existing compressed slot capacity and was correctly rejected. This establishes that container repacking/descriptor offset relocation is needed for this candidate; no output was packaged or game launched. Full actor creation remains incomplete.

### Integrated structural actor candidate
- Previous turn added synthetic structural regression coverage. Added append_actor_candidate combining source-bound donor append, validated index mapping, reached P1/P2 rewrites and cloned-donor rewrites. It validates operand preimages and unchanged layout/length, records structural/final hashes and exact changed bytes, and marks build_ready false.
- Retail donor11 candidate changed exactly three existing spawn operands. Donor10 candidate changed exactly four, including the cloned donor's own operand. Byte diffs matched audit offsets precisely; final hashes verified. No project output packaged or runtime interaction.
- Partial paths, partition0, other global references, scheduling and descriptor sizing remain open; candidate creation is integrated but not playable acceptance.

### Structural append regression fixture
- Previous turn added fixed actor-interaction decoding while preserving unresolved acquire semantics. Added two compact synthetic MAN regressions for partition-table growth, original record/section byte preservation, donor coordinates, shifted global target identity, stale source rejection, aliased donor rejection and modified target rejection.
- Both tests passed without retail data. Fixture contains synthetic bytes only. No runtime interaction; structural tests do not establish script scheduling or playable append acceptance.

### Actor-control continuation evidence
- Previous turn expanded P1/P2 reindex inventory. Current stop census is dominated by dialogue picker/external continuation uncertainty, then halt and actor-control0/1. Pinned actor_ctrl.rs acquire forms read a signed target through operand+4 but advance only header+4 in the narrow form; this boundary inconsistency requires retail verification before decoding.
- Added the independently unambiguous ACTOR_CTRL2 THREE_ACTOR_TALK form: three encoded actor operands, u16 argument and trailing byte, fixed header+7. Normal/extended forms and every payload truncation passed focused smoke. Actor IDs/effects remain encoded/not observed.
- No invented acquire widths or runtime interaction. Full relocation remains incomplete.

### Partition-wide reached spawn rewrite inventory
- Previous turn added focused decoder regressions. Added inspect_spawn_reindex combining validated target mapping and existing bounded P2 header parsing to inventory all P1/P2 candidate rewrites without mutating source/candidate buffers.
- Retail town0192 records:32 decoded-supported-paths,60 partial, no rejected records. Three reached operands require rewriting: P1[0], P1[10], P2[6]. The newly decoded scene-entry path therefore exposed an additional real reference, and P2 coverage found another.
- Partition0 is explicitly excluded; partial paths and other reference families remain unverified. No playable build or game interaction. Complete relocation remains false.

### Focused script authoring regression checks
- Previous turn completed supported-path decoding of town01 entry. Added four focused regressions for extended spawn-target preservation, opaque spawn-like bytes left untouched, missing/invalid mappings and stale hash rejection, BBOX backward/wrapped branch bases and truncated payload rejection, plus fixed MENU_CTRL payload boundaries and signed values.
- All four tests passed. These cover the new decoding/rewriting byte boundary risks without expanding into the deferred comprehensive test campaign. No game interaction; full native actor creation and the broader SDK goal remain incomplete.

### Town01 entry supported-path decode completed
- Previous turn expanded bounding-box branches. Pinned menu_ctrl.rs proves outer nibble1 consumes five payload bytes and advances header+6. Added MENU_CTRL_SUB1 for10..1F with host-defined destination semantics, without inventing effects for13.
- All16 selectors passed normal/extended fixed-width smoke. Town01 P1[0] now decodes180 instructions with decoded_supported_paths and no stops, up from77. This proves coverage of the inspector's encoded paths, not runtime reachability or native-spawn acceptance. No game interaction.

### Bounding-box branch decoding
- Previous turn expanded scene-entry coverage to opcode4D. Read pinned executing step.rs and helpers.rs: six operand bytes, inside fallthrough, outside signed/wrapped16 skip from the skip-word location. Tile conversion depends on runtime global state.
- Added BBOX_TEST with both encoded successors and explicit runtime-dependent coordinate mode. Normal/extended backward-branch smoke exercised the correct base and wrapping. No game interaction; broader native-actor acceptance remains open.

### Scene-entry script coverage expansion
- Previous turn verified retail actor10 reindexing. Town01 P1 system record0 stopped after32 instructions at MENU_CTRL8A. Inspected pinned executing nibble_8.rs: fixed header+10 continuation, three signed16 operands and one u24 operand.
- Added WRITE_FIELD_QUAD decoding with host-defined destination semantics; normal/extended synthetic forms verified signed extrema and packed u24. Town01 entry now decodes57 instructions, stopping at unsupported opcode4D at PC175. No byte recovery or invented width.
- Existing script-inspection suite22 passed/1 skipped. No runtime interaction. Entry scheduling and remaining opcode4D decoding are still incomplete.

### Retail spawn rewrite target preservation
- Previous turn implemented reached operand rewriting. Retail pass across52 actor scripts found one decoded spawn operand in actor10, with no missing-map rejection; partial paths remain partial and partition0/system/P2 coverage is not implied.
- Added spawn_index_map derived from old/new MAN layouts. It requires unchanged P2 count and exact target-record bytes and rejects encoded byte overflow. This replaces hand-specified index arithmetic with validated structural identity for this step.
- Retail actor10 operand95 rewrote to96 while retaining P2 record6. Deliberately changing the rebuilt target's bytes was rejected. No runtime or playable-build acceptance; full reference coverage and scheduling remain open.

### Reached spawn operand rewriting
- Previous turn progressed MAN target resolution. Added script_reindex.reindex_spawn_operands with exact source hash and bounded byte-index map. It changes only reached opcode44 operand bytes, supports extended actor-target headers, rejects missing mappings/overflow and checks instruction boundaries, successors and opaque bytes after rewriting.
- Synthetic normal/extended sequence changed exactly offsets1 and4; overflow, boolean keys and missing target mapping rejected. Audit retains partial/full supported-path coverage and explicitly does not claim complete relocation. Caller must still validate mapping against MAN layouts; other reference families and opaque paths remain unresolved.
- No build/UI connection or runtime interaction. This is a serializer step toward native actor creation, not playable acceptance.

### Resolve encoded spawn references
- Previous turn established the global-index dependency. Added resolve_spawn_record against the bounded MAN layout: byte operands resolve to partition2 record index and source span, or explicitly outside_partition2. Donor diagnostics now carry resolved target metadata rather than an unqualified numeric operand.
- Retail town01 check classified all256 byte operands and verified all39 partition2 targets preserve identical record bytes after +1 index remapping in the structural candidate. Old operand89 becomes invalid after append, directly demonstrating why a byte-preserving append alone is not playable.
- Existing script-inspection suite:23 tests ran, one retail test skipped without its environment variable. No auto-rewrite of opaque scripts, build integration or game interaction. Full goal remains incomplete.

### Global script index dependency established
- Previous turn progressed donor coverage diagnostics. Pinned engine-vm/src/field/step.rs establishes opcode44 operand as a GLOBAL record index rebased by N0+N1 into partition2 (FUN_8003BDE0), not a partition1 NPC identifier. Appending P1 changes those global identities even when every old record byte is retained.
- Inspector now decodes global_record_index, target_partition and index semantics for normal/extended SPAWN_RECORD instructions. Donor audits include reached spawn references and explicitly require global-index rewriting; town01 P2 range89..127 shifts by1. No automatic rewrite through undecoded bytes.
- Focused smoke passed normal/extended operand decoding and retail town01 shift audit. Playable append remains unverified until all affected encoded references and scheduling are handled. No runtime interaction.

### Donor script coverage diagnostics
- Previous turn progressed source-bound donor selection. Inspected pinned engine-vm field/step/flow.rs and camera.rs plus engine-core man_field_scripts/records.rs. Camera apply uses an absolute PC within supplied bytecode; reference record walking supplies a record slice. This is distinct from an absolute MAN file offset. Pinned flow.rs also documents correction of older 0x4E absolute-jump interpretations; do not blindly rewrite operands based on old man_edit comments.
- Donor candidate audits now include supported-path instruction/dialogue counts, opaque byte and stop counts, camera-apply jumps and explicit spawn counts using the existing bounded graph inspector. No raw script/dialogue payload is included; decoded coverage never enables relocation/spawn acceptance automatically.
- All52 retail donor reports produced successfully:49 partial and3 decoded-supported-paths. Both relocation and spawn-scheduling verification remain false. Full execution-base/host behavior and actor scheduling still require evidence. No game or user project mutation.

### Source-bound native actor donor selection
- Previous turn made progress verifying structural append. Inspected pinned Andrew man_edit.rs address handling: its record resizing keeps the table-derived payload base fixed, whereas adding an actor grows the table. Its relocation acceptance cannot establish our actor-append safety.
- Added append_actor_donor: resolves an existing partition1 actor from a verified source hash, rejects non-integer/system/out-of-range and aliased donor identifiers, and records donor offsets, model/animation and original coordinates. It accepts no caller-supplied script payload.
- Retail town01 passed all52 source-bound donor clones and six invalid-identifier checks. Candidate audits explicitly retain false script-relocation and spawn-scheduling verification. No project/build wiring or runtime mutation; executable script-address semantics and scheduling remain the next native-creation work.

### Actor append structure and coordinate preservation
- Previous response only acknowledged the user's interior-NPC observation (no progress). Resumed by inspecting current source and running the pending structural append against retail town01.
- Structural append adds partition1 record53, retaining existing indices and bytes, and preserves all six trailing sections. Added source/result/donor hashes, before/after sizes and partition counts to its audit, plus an explicit result-size invariant.
- All52 retail donor records independently appended and parsed as a 53rd actor; existing X/Z and model/animation assignments remained unchanged. Empty/malformed donor and stale source hash were rejected. The initial expanded smoke used incorrect dataclass field names; corrected it to world_x/world_z/model_index before rerunning successfully.
- NPC coordinates remain intact: the user's report that remaining NPCs belong inside houses is plausible, not yet independently verified. No game interaction occurred. Absolute script relocation, external decoded-size updates, project/UI/build integration and native-spawn gameplay acceptance remain incomplete; this structural prototype is not packaged as playable content.

### Native actor structural layout foundation
- Previous turn made progress verifying authored OBJ revision. Began native actor frontier by reading current MAN parser and pinned Andrew d6e64c68 man_edit.rs/reference tree. Offset-table growth moves the derived data base; edited-record jumps and external decoded-size descriptors are separate concerns, so merely cloning editor entities is insufficient.
- Added bounded read_man_layout exposing all partition record offsets/spans, six section spans and trailing bytes. It does not claim arbitrary script relocation or allocate a native actor yet.
- Retail town01 check matched every existing actor offset/length against parse_man. This layout reader is a structural serialization foundation; script reference handling, actor-record creation, descriptor resizing, commands/UI/build and runtime acceptance remain open.

### Authored OBJ revision acceptance
- Previous turn made progress with authored source downloads and preserving current TMD normals. Retail model0009 test authored a normal then changed a vertex through OBJ; normal bytes remained intact.
- Stopped only isolated editor4405/session69467 after confirmed completion, restarted current code as session74672. Separate automated Edge browser downloaded authored and retail OBJ from saved test model0000; all50 authored vertices were X+100 relative to retail, with correct distinct filenames. Test18026 completed successfully.
- No user editor/game interaction or project Save. Iterative authored OBJ download now browser-verified; broad source formats and gameplay remain open.

### Continue editing authored shapes
- Previous turn made progress checkpointing OBJ workflow. Added explicit imported/authored source download layers with separate original/effective TMD hashes; browser offers Download authored OBJ when an override exists.
- OBJ application now begins from the validated current TMD shape, preserving any previously authored normal words while changing positions. Final output is still checked against immutable retail source by the existing replacement validator.
- Retail authored OBJ download/reupload was a history-free no-op; retail download stayed distinct with equal source/effective hashes. Node syntax passed. Browser authored-download control and existing authored-normal preservation need direct checks. No user project/runtime mutation.

### OBJ workflow checkpoint
- Previous turn made progress accepting actual browser file input/upload. Added2 focused OBJ regressions covering decimal integer exports, UTF8 BOM, ignored external material declarations, exact byte scope, topology/order/count rejection, negative indices and nonrepresentable coordinates.
- All15 focused OBJ/model/importer/project checks passed, plus Node syntax and diff checks. Updated feature matrix to reflect browser and Blender acceptance and retain scene/gameplay/shared-stream gaps.
- Local checkpoint includes upload draft guards, optional model collection build fix and OBJ interchange/UI/documentation. Only explicit source/test/docs paths selected; private Blender outputs remain untracked.

### Browser OBJ file-upload workflow acceptance
- Previous turn made progress verifying Blender roundtrip. Located bundled Playwright via workspace dependencies and used a separate headless Edge test browser, not the user browser or game. Started fresh isolated editor4405/session69467 for the existing private model-shape test project.
- Automated actual file input selected Blender-edited NPC0105 OBJ, verified view/export disabled, discarded it, reselected/uploaded, verified authored preview and cleared override back to retail. Zero page errors. Test process7716 completed successfully; scene rebuild requests accounted for its elapsed time.
- No project Save or game interaction. Existing saved model0000 test override was retained; temporary NPC0105 override cleared. Updated user guide with browser acceptance. Gameplay and broader external-tool configurations remain unverified.

### Blender OBJ external-tool roundtrip
- Previous turn made progress integrating OBJ source/upload. Located installed Blender through uninstall registry at D:/Games/Steam/steamapps/common/Blender/blender.exe; version5.2.1. Used factory-startup background processes only, no existing scene changes.
- Private NPC model0105 (130vertices/225triangles) exported to OBJ, imported unsplit with validation off and Y-forward/Z-up, then exported matching axes with modifiers/UV/normals/materials off. SDK reimport preserved every original TMD byte.
- Second Blender run moved vertex0 X+20; SDK reimport audited exactly one X coordinate+20 and preserved all other source bytes. Documented supported settings/limitations in docs/legaia-model-shapes.md. Browser file-picker and gameplay remain pending.

### OBJ source/upload editor integration
- Previous turn made progress implementing ordered OBJ interchange. Added source format choice and16MiB OBJ upload route with strict base64 limits, routed through existing shape validation/storage. TMD path retains4MiB limit.
- Model inspector now offers Download shape OBJ and accepts TMD/OBJ files; common draft context guards and authored preview are reused. UI explains unchanged normals, source axes/integer positions and required vertex/face order.
- Fresh temporary HTTP server passed retail OBJ download, one vertex X+10 upload and exact authored-vs-retail preview comparison; other vertices identical. Node/Python syntax checks passed. Browser upload and external3D-tool roundtrip remain unverified. No user project/runtime changes.

### Ordered OBJ model shape interchange
- Previous turn made progress verifying combined NPC animation/shape. Added standard OBJ source export and position-only import into source TMD, preserving source vertex/face order, topology, materials, normal words and padding.
- OBJ requires positive indices, exact source triangulation, bounded UTF8 input and signed16 integer positions; material-file references are ignored, never followed. Added project adapter through existing validated TMD asset storage/history.
- Synthetic no-op roundtrip and single-vertex edit passed; fractional coordinates, changed face order and extra vertices rejected. OBJ HTTP/UI and external-tool roundtrip remain to implement/verify. This does not add arbitrary topology replacement or normal recalculation.

### NPC shape plus authored animation acceptance
- Previous turn made progress protecting upload drafts. Read animation-browser-check without saving; copied metadata/animation override into a temporary project and authored one20unit vertex change on actor0011's model0105.
- Corrected the check's authored_bank argument to use AnimationChannels values (initial invocation passed whole components and raised KeyError; no source defect). All15 NPC pose frames retained a20unit transformed vertex delta, identical other vertices, immutable input pose and both authored-animation/shape provenance.
- Combined shape+animation build produced2 overlays. No user project mutation or game input. This proves local posed geometry and package composition for these separate streams, not live gameplay or exact shared-stream composition.

### Model upload draft ownership
- Previous turn made progress verifying mixed model/texture build. Added explicit selected-TMD draft ownership (file, model, project/scene), guard before/after asynchronous file reading, and discard action.
- Pending files block model/layer changes, clear and export; failed upload retains its selection, successful upload clears before reopening authored view, closing inspector discards only the unsubmitted file. Empty upload action is disabled.
- Node syntax passed. File-picker browser interaction remains unverified; these draft controls are implementation progress, not an acceptance claim. Existing projects/runtime untouched.

### Mixed model and texture package verification
- Previous turn made progress checkpointing501c47f8. Ran texture build guards: nine fault subcases initially raised AttributeError because older project adapters omit model_overrides. Build now treats an absent optional model collection as empty, matching texture handling.
- All3 texture-build tests passed after correction, including stale source/payload/audit/overlap rejection and retail texture/MAN composition.
- Temporary retail model0000 one-coordinate edit plus town01 TIM5/raw/0 payload edit built two nonoverlapping overlays, with both model.shape and texture.tim audit records. This establishes that pair only; exact shared compressed-stream cross-family composition remains unresolved. No user project or runtime mutation.

### Model shape checkpoint verification
- Previous turn made progress with party animation and authored navigation. Added two focused synthetic regressions for every source byte including normal XYZ/padding, vector alias rejection, known90degree pose result, immutable input, and missing transform rejection.
- All31 focused model/importer/export/project/build-report/scene/MAP-build checks passed with retail input. Updated FEATURE_MATRIX with implemented model-shape scope and unverified boundaries.
- Checkpoint includes earlier collision review/difference display improvements. No proprietary payloads are among the explicitly selected source/test/document paths. Browser file upload, NPC/scene visual acceptance, mixed shared-container composition and gameplay remain pending; full SDK goal remains incomplete.

### Animated shape verification and authored asset navigation
- Previous turn made progress with effective scene shapes. Registered model shapes in project-wide Authored Assets with their imported source records, separate authored bindings, and source-scene navigation to explicit authored model view.
- Retail party idle test passed all15frames: one local vertex displaced20units retains20unit distance after rigid pose, all other vertices identical,10object equipment-excluding prefix unchanged; imported preview remained unchanged. Authored model entry was present. Node syntax passed.
- Browser authored-asset navigation, NPC animation shape and scene visual checks remain pending; no gameplay or user project changes.

### Effective scene model shape integration
- Previous turn made progress with browser preview/export and GLB provenance. Added preview_model_shape: validates existing object ranges, supports party prefix excluding equipment, and reapplies explicit frame/pose transforms to authored local vertices without changing retail geometry or channels.
- Scene route opts into effective shapes via model loader adapter; ordinary retail preview remains unchanged. Shape bindings enter scene geometry cache identity, and file/source validity is checked before cache reuse.
- Fresh retail scene service found one authored-shape geometry from the isolated model0000 project. Five scene-preview tests passed. Animated shape and browser scene rendering still require direct verification; existing4404 server predates this adapter. No game or user project changes.

### Browser model shape and GLB provenance verification
- Previous turn made progress adding browser controls. Created isolated model-shape-browser-check project with model0000 object0 X+100, started fresh editor4404/session43064 (module has no direct main invocation; used explicit main()), and browser tab73.
- Browser loaded authored object-local preview and exported50 source vertices/72triangles/two textures. Export inspection found missing authored shape metadata; added representation and authored_shape binding to GLB extras/audit.
- Fresh direct-service export independently parsed216 expanded GLB positions and matched all converted authored vertices plus representation and source/replacement hashes. Fresh file model-bfe979b780224999abc62ef4ac17aabb.glb is verified; the earlier browser export predates the metadata fix. Current4404 server also predates that Python exporter fix.
- Browser file-picker/upload interaction remains unverified (API upload passed previously). No user project/game changes. Scene/posed model shape integration and mixed-container composition remain pending.

### Model shape browser controls
- Previous turn made progress verifying source/upload/preview/clear HTTP workflow. Added capability-gated model inspector controls for source TMD download, bounded edited TMD upload, retail/authored unposed views and clear override. Upload captures project/scene/asset context across file reading; server validates all bytes.
- Authored shape preview is labeled separately, and Export GLB selects the authored-shape route when that layer is displayed. Existing animation selection remains imported/assigned; main-scene and posed shape integration are still pending.
- Node syntax and Python compile checks passed. Browser rendering/upload/export controls require verification against a fresh isolated editor; existing user editor/game remain untouched. No claim of UI acceptance yet.

### Model shape upload and explicit preview API
- Previous turn made progress packaging model shapes. Added bounded4MiB model upload route, authored object-local preview and authored GLB-export route, explicit clear command/history, and model_overrides in editor state.
- Temporary real HTTP server passed source download, replacement upload, authored preview, retail preview and clear. Exactly one vertex X changed by1; source_record remained equal between layers. Server shut down after check; no existing editor restart or user project change.
- Authored GLB route is implemented but unverified. Browser upload controls, main scene/posed geometry integration and authored asset browser still pending. Preview currently object-local shape only, preserving imported animation behavior.

### Model shape package integration
- Previous turn made progress with persisted model assets. Added raw member overlays and grouped compressed-container shape composition, conservative same-span LZS encoding, original disc-span checks and coordinate audit records; removed the temporary blanket Build rejection.
- Model shapes now participate in build authored-state identity and report before/after hashes. First temporary build exposed missing scene in shape audit; corrected it and reran successfully.
- Two town01 scene models with one coordinate edit each built as one overlay with two audited model changes and verified compression roundtrip. UI/preview remains pending; raw model packaging and mixed edit families need verification. Existing cross-family overlapping-overlay rejection remains, so shared-container texture/animation composition is not yet complete. No game input or user project changes.

### Persistent model shape assets
- Previous turn made progress validating all119 retail model layouts and adding private source access. Added project model_overrides with content-addressed Authored/Models TMDs, strict binding/hash/size/path validation and fresh imported-source validation.
- Registration requires Edit mode and exact supported shape layout, supports128 entries, uses shared undo/redo, tracks dirty sections, saves/reopens with revalidation, and clears the override when original source is supplied. Build explicitly rejects these overrides until packaging is connected, preventing silent omission.
- Retail temporary-project workflow passed registration, undo/redo, dirty section, save/reopen, content equality, source restoration and undo of restoration. No user project save, game launch or input. Model preview/UI upload, authored browser listing and package integration remain pending.

### Retail shape compatibility and private source API
- Previous turn made progress with shape serializer. Extracted load_model_source from the existing preview reader so downloads/replacements share disc/container/source-span guards; preview delegates to it without changing decoding behavior.
- Retail town01 check accepted one local vertex-coordinate edit for all 119 imported models with exactly one audit item each; no alias/primitive overlap rejection. Four existing model decoder tests passed. This proves bounded shape compatibility, not arbitrary replacement or gameplay.
- Added freshly reimport-verified model_shape_source service and /api/model-shape-source route for private base64 TMD downloads keyed by active-scene asset identity. Python compile/diff checks passed; new HTTP route and UI download remain unverified/not wired respectively. No game or saved-project changes.

### Model shape replacement serializer foundation
- Previous turn made progress with removed collision visualization. Inspected current assets.py decoder and source locators before starting the model replacement frontier.
- Added source-hash-bound same-layout TMD shape replacement validator for vertex/normal XYZ words. Protects descriptors, topology, materials, vector padding and opaque bytes; rejects vector aliasing and primitive overlap. This is a serializer foundation, not yet an editor import/build workflow or arbitrary topology replacement.
- Synthetic textured-quad mutation check changed each byte independently, accepting only 24 coordinate bytes and rejecting all protected bytes; no-op preserved identical source. Retail shape replacement, normal-vector fixtures, service registration, previews, persistence and packaged output remain to implement/verify.

### Authored collision viewport differences
- Previous turn made progress with individual wall review/restoration. Added bounded audit validation and effective-layer delta drawing: added walls green solid, removed walls pink dashed, with counts in the legend. Imported geometry remains unchanged.
- Browser tab72/editor4403 visually verified temporary removal at row14/column41/quadrant0: pink dashed rectangle centered at X5280/Y0/Z1696 and Removed1 legend over the scene. Restored the temporary edit through the form afterward; no project save or game input.
- Node syntax and diff checks passed. Added-wall green appearance remains unverified visually; removed-wall display is verified. Source collision height remains a labeled placeholder.

### Review and restore individual collision edits
- Previous turn made progress and checkpointed collision workflow at 4ee77392; tracked worktree was clean before this extension.
- Added sorted Applied wall edits selector and Restore selected cell to retail. Both respect unapplied draft protection. Apply now requires a change and removes an existing override when the checkbox returns to retail; removing the final edit clears Collision only.
- Isolated browser tab71/editor4403 verified a temporary row1/column0/quadrant0 blocked edit appearing in the list, then restored it: unblocked baseline, empty disabled edit selector, disabled restore/clear actions. No project save or game interaction. Node syntax passed; the final placeholder selection correction is syntax-checked only.

### Collision authored asset integration and checkpoint
- Previous turn made progress with browser-verified cell location. Reviewed current serializer, project commands, persistence, resource preview, server and MAP composition changes.
- Fixed collision overrides missing from Authored Assets: scenes now expose one combined authored entry for Collision and Environment, while retaining separate component provenance.
- Added a retail workflow check: collision-only authored listing, scenery coexistence, clear/undo, save/reopen, combined authored listing, exactly one built MAP, and exact two-byte change scope. All 16 focused collision/importer/MAP-build/scene-preview checks passed with retail input.
- Collision package behavior remains unverified in gameplay. No game launch, controller input or user project save; tests use temporary private projects.

### Collision cell viewport locator
- Previous turn made progress implementing draft protection. Verified it in isolated browser tab70/editor4403: toggling Blocked disabled all cell selectors; Discard restored navigation and row2 showed X(0,64], Z[128,192).
- Added Locate cell in viewport, using the selected quadrant center and the existing reference marker/camera. It rejects stale project context, invalid cells, and pending wall drafts; it changes no authored or runtime positions.
- Browser verification of row14/column41/quadrant0 showed the wall-side collision overlay and Reference X5280 Y0 Z1696. Y0 remains an explicitly labeled display placeholder, not decoded floor height. Node syntax and diff checks passed. No game input or project save.

### Collision form draft protection
- Previous response was no progress (acknowledged the user's house-interior explanation). Revalidated current branch e02d73a3 and pending collision implementation before continuing.
- Preserve remaining NPC coordinates: missing sampled ground does not establish incorrect placement or scene membership.
- Collision form now locks row/column/quadrant while its blocked checkbox differs from the inspected value. Added explicit discard of the unapplied wall change; programmatic input events also restore the draft cell instead of transferring its value.
- Node syntax check and all 15 focused collision/importer/build/scene-preview checks passed with retail input. The new draft UI has not yet been browser-verified. No game launch, input, or user project save.

### Collision undo and preservation regression
- Previous turn made progress with browser Apply and route-validator correction. Fresh HTTP check verified browser Undo: effective rectangle set equals imported and authored collision override is absent.
- Added focused exhaustive byte/quadrant preservation test (256 byte values, 1024 wall-bit changes), deterministic audit/revert, no-op, malformed/bool indices, duplicate/capacity and hash/size rejection.
- Fifteen collision/importer/MAP-build/scene-preview checks passed with retail input. No runtime/game launch or saved project mutation.


### Browser collision apply and route correction
- Previous turn made progress adding collision controls. Fresh isolated editor on4403/tab69 exposed a misplaced layer validator: collision still rejected layer while neighboring route accepted it. Restored neighboring strict validator and corrected collision route, then restarted only isolated server (current75133).
- Browser form showed cell row1/column0/quadrant0 unblocked and world bounds X(0,64], Z[0,64). Checked Blocked and Apply; independent HTTP comparison showed one additional effective rectangle and unchanged imported data. Invoked browser Undo; no save or game interaction. Cleared stale dialog errors on successful preview reload.


### Collision layer selector and source wall controls
- Previous goal turn made progress with effective collision preview and source-key invalidation. Added retail/effective viewport selector, explicit overlay labels and response-layer validation.
- Collision resource inspector now opens source wall controls for canonical row/column/quadrant, reports integer world bounds and current effective blocked state, and applies one wall bit while retaining existing overrides through the command system. Clear scene wall edits and stale-context/Edit-mode guards included.
- JavaScript syntax passed. Browser apply/undo/build workflow verification and runtime movement acceptance remain pending.


### Imported and effective collision preview
- Previous turn made progress with collision persistence and composed MAP build. Added explicit imported/effective field-map preview layers; effective rectangles use verified wall overrides while retaining imported asset provenance and separate authored audit. Runtime collision claims remain excluded.
- Retail single-bit check changed exactly one effective rectangle and preserved imported rectangles/asset metadata. Collision override identity now participates in preview source keys without forcing actor geometry reconstruction. Browser layer controls remain pending.


### Collision commands and composed MAP packaging
- Previous turn made progress adding exact wall-bit serializer. Added strict source-bound Collision component commands, undo/redo and saved project reopening.
- Build composes collision bits and scenery changes into one verified MAP overlay, preventing overlapping output spans and preserving independent edits. Retail smoke combined one changed collision bit with existing wall-decoration edit: one overlay/two audited fields.
- Isolated save/reopen retained Collision and Environment together; undo/redo preserved other edits. No user project save or game launch. Browser collision controls and runtime movement acceptance remain pending.


### Source collision authoring foundation
- Previous turn made progress checkpointing channel inspector. Reviewed broader feature ledger and selected source collision authoring as next scene workflow; existing field_map evidence defines four upper-nibble wall bits and canonical row/column/quadrant mapping.
- Added source-hash-bound equal-size wall-bit serializer, strict bounded requests, duplicate rejection, deterministic audit and unaudited-bit verification. Low floor-tier nibble and other MAP content remain untouched.
- Synthetic all-four-quadrant write/decode/revert check passed, including exact source-byte restoration. Project commands, browser controls, composed MAP builds and runtime movement acceptance remain to implement/verify. Updated stale animation table status to match prior authoring evidence.


### Channel inspector regression checkpoint
- Previous turn made progress finding/fixing browser draft selector bug and validating discard. Extended existing shared-bank regression to cover retail/effective channel values, contributors, composed hash, invalid indices and geometry-free inspection.
- Sixteen focused animation and scene-preview tests passed with retail input; JavaScript syntax passed. Checkpoint includes source/effective readout, conflict-at-Apply validation, navigation/discard and position-ghost correction. Full SDK/runtime acceptance remains incomplete.


### Browser draft guard correction
- Previous turn made progress adding discard, but tab unavailable. Refreshed the exact isolated server session on port4403 after stopping80930; new session82116 and tab68. Browser verified retail/effective values, contributor IDs and applied-channel picker.
- Browser input showed onchange did not protect frame selection promptly. Changed selector handling to oninput and added Apply channel-identity guard. Retest retained frame0 and draft X125 when switching to frame1, displayed Apply/Discard message; Discard restored applied X100 and disabled itself. No applied override or save occurred.


### Discard unapplied channel changes
- Previous turn made progress adding applied-channel navigation and draft protection. Added explicit Discard unapplied channel changes action, enabled only after axis input, restoring the selected actor applied values without project mutation. Navigation message now explains Apply or Discard.
- JS syntax passed. Browser verification attempt found tab67 no longer belonged to the active browser session; no browser acceptance claimed for these latest controls. Full goal remains active; no game interaction.


### Applied animation channel navigation
- Previous turn made progress rejecting shared conflicts before mutation. Added sorted applied-channel picker listing frame/object and edited axis values, with explicit empty state and scoped navigation.
- Prevented channel navigation from silently discarding un-applied input: selectors restore the edited channel and request Apply before switching. No project mutation from navigation. JavaScript syntax passed; browser acceptance remains pending.


### Reject shared animation conflict before Apply
- Previous turn made progress adding effective channel values and contributor disclosure. Project animation validation now composes the proposed override with existing scene contributions before mutating state, preventing conflicting saves from breaking preview/build later.
- Retail isolated-project check rejected Actor0012 X=99 against Actor0011 X=100 with overrides and undo/redo unchanged; independent Y=-80 accepted and effective XYZ became 100/-80/0. No save.
- Conflict diagnostics now identify clip/frame/object/axis and requested values.


### Effective shared channel inspection
- Previous goal turn made progress verifying retail readout and main scene in browser. Extended one-channel inspection with retail/effective values, composed record hash and contributing actor identities. UI separates applied shared values from the selected actor editable inputs.
- Retail service check on Actor0012 returned retail X=0, effective X=100 and contributor Actor0011 from the saved isolated test override, proving cross-owner effect disclosure without mutating imported values. JS syntax passed. Updated effective readout browser acceptance remains pending.


### Browser retail readout and authored scene acceptance
- Previous turn made progress adding one-channel retail inspection. Updated isolated editor on 4403/session80930, browser tab67. Prior tab66 was no longer available; new tab used without touching the user game.
- Browser readout showed retail XYZ 0/-89/0 and rotation 0/0/0 separately from authored X=100. Main scene Focus visually showed displaced heads on selected Actor0011 and another shared-clip actor.
- Visual check exposed a bogus imported-position marker for animation-only changes; restricted position ghost to transform edits/drafts. No saved project writes this turn. Runtime animation acceptance remains pending.


### Retail animation channel inspection
- Previous goal turn made progress checkpointing animation workflow. Added bounded one-channel source lookup, project/HTTP adapter, and retail translation/rotation readout in the animation dialog. No mesh/pose expansion needed.
- UI checks source record hash and ignores stale request/context responses when frame/object selection changes. Synthetic lookup returned expected X=10, rejected five invalid/bool index cases, and proved no geometry load. Eleven existing checks passed with two retail skips; JS syntax passed. New readout browser acceptance remains pending.


### Animation workflow checkpoint validation
- Previous turn made progress hardening commands and correcting shared-clear wording. Reviewed accumulated animation workflow changes before checkpoint.
- Ran 33 focused animation, scene-preview, serialization, build-report, MAP and appearance-assignment checks with retail input. 32 passed; one MAP test expected the old no_MAN audit label. Updated it to no_compressed_scene_overlay (MAN and ANM now participate), then both MAP build tests passed.
- Full goal remains active. Checkpoint covers partial exact-channel authoring workflow, not arbitrary animation import or game playback acceptance. No game launch or user project mutation.


### Animation command boundary and shared clear wording
- Previous goal turn made progress independently parsing authored GLB output. Added exact set/clear command key validation and nonempty string actor identity checks in ProjectService before state mutation.
- Five malformed command shapes plus Live-mode clear were rejected with overrides and undo/redo stacks unchanged on the isolated project.
- Corrected channel editor clear/blank wording: clearing removes only the selected actor contribution; contributions from other actors sharing the clip remain. No user project save or game interaction.


### Authored baked GLB export verification
- Previous turn made progress verifying real scene vertex deltas. Exported imported and authored Actor 0011 frame zero through EditorServer into the isolated test project Exports.
- Independently parsed GLB headers, JSON/BIN chunks, buffer views and float32 POSITION accessors: both contain 675 positions; deltas are exactly +100 X or unchanged. Embedded animation representation and authored audit retain the selected source/change evidence.
- Imported file model-e6209792d71d496aab2e86f5653ed160.glb; authored file model-a3a7b727797d464e8e8b36867d0fc8e1.glb. Static baked pose export only; no skeletal animation channel export claim. External viewer and live game acceptance remain pending.


### Retail main-scene geometry evidence and feature ledger
- Previous goal turn made progress connecting authored bank poses and source-key invalidation. Fresh scene service on the isolated saved project confirmed Actor 0011 authored frame-zero metadata, followed by imported metadata and a new source key after removing only in-memory overrides.
- Compared actual scene vertices: deltas were exactly (100,0,0) for the edited object or (0,0,0) for unaffected vertices. No project save or game interaction.
- Updated FEATURE_MATRIX to reflect implemented persistence, browser channel controls, shared preview/build composition, guarded package emission and measured scene geometry, while retaining explicit runtime, main-scene browser and GLB export acceptance gaps.


### Main scene authored pose integration
- Previous goal turn made progress through browser author/apply/save/preview/undo verification. Found the main scene still used imported frame zero; connected the shared authored bank to bounded single-frame pose generation and tagged changed poses as authored.
- Animation overrides now participate in scene geometry cache identity. Shared affected actors and appearance donors resolve through the same composed bank; unrelated clips preserve imported poses. Authored asset detection now includes direct animation overrides.
- Sixteen focused animation/scene-preview tests passed. Browser rendering of this new main-scene path and live playback remain pending; the isolated browser server still runs its prior Python code until deliberately refreshed.


### Browser animation workflow acceptance
- Previous turn made progress with shared-bank preview parity. Started isolated editor on port 4402 (session 52315), using new local-output/sdk-20260909/animation-browser-check project; original wall project and game untouched.
- Browser selected Actor 0011, opened source-verified controls, listed six shared actor references, applied frame 0/object 0/translation X=100 and saved. Fresh ProjectService.open verified exact persisted override.
- Visually inspected authored preview: head displaced sideways by the test channel edit. Switching to imported clip restored assembled pose. Browser Undo removed authored button state; Redo restored command. This verifies editor preview and persistence, not game playback.


### Shared animation preview parity
- Previous goal turn made progress with packaged animation overlays. Corrected preview/build mismatch: authored preview now consumes the same composed scene animation bank as build, including contributions from other actor overrides. Actors sharing an authored clip can select its authored preview even without a direct override.
- Animation authoring options and dialog list imported same-clip actor references without claiming runtime actor identity or reachability.
- Added one focused two-owner composition check: separate X/Y writes merge into the expected posed vertex; contradictory X writes fail. Eleven animation checks passed with retail input; JavaScript syntax passed. Browser acceptance and live playback remain outstanding.


### Shared animation package build
- Previous goal turn made progress by connecting authored/imported previews. Added shared-bank composition with contradictory axis rejection and unchanged surrounding byte checks. Reused bounded LZS encoding with independent decode verification; no descriptor relocation or source writes.
- Build now emits animation overlays alongside existing MAN/MAP/texture overlays, validates the exact source disc span, and reports shared-clip scope. Editor describes shared effects, compression capacity, and outstanding runtime acceptance.
- Retail Actor 0011 frame 0 object 0 X=100 plus the existing wall override successfully built under local-output/sdk-20260909/animation-package-smoke. Package SHA 7bf95ced33244b2058adaa80a409acb9d27ead9b404a3300c55713e3b376a97a. No user project save or game launch. This is packaging evidence, not live playback acceptance.


### Authored animation preview integration
- Previous goal turn made progress: implemented channel editor controls and validated syntax/decoder behavior.
- Actor animation preview now accepts explicit imported/authored representation, validates saved source-bound overrides, and exposes both clips. Editor clip selection and frame export retain that representation; imported defaults remain unchanged.
- Retail service exercise on Actor 0011 confirmed the edited frame changes while all other frames and the subsequent imported preview remain equal. The exercise changed only in-memory state and did not save the user project or control the game.
- Thirteen focused animation and appearance HTTP tests passed with retail input; JavaScript syntax and diff whitespace checks passed. Browser visual acceptance, animation export acceptance, and playable ANM packaging remain pending.


### Animation channel editor controls
- Previous goal turn was no progress (acknowledged user interpretation of interior NPC positions); resumed concrete implementation without changing actor coordinates.
- Added source-verified animation channel dialog with zero-based frame/object selectors, exact translation and PSX rotation axes, inherited blank axes, preservation of other channel overrides, and clear-all command. Guards reject stale project/scene/selection and Live mode edits.
- Existing animation persistence API is connected through normal command/undo/save flow. Playable packaging remains explicitly unsupported; authored preview integration and browser workflow acceptance remain pending.
- Ten focused animation tests passed with the retail disc enabled; JavaScript syntax check passed. No game process launched or controlled.


### Editor animation options API
- Added strict actor-ID-only /api/animation-authoring-options route and exposed saved channel overrides in both options and entity Animation component. The UI can now obtain source-bound clip metadata and display authored edits separately.
- Python compilation passed; ten focused animation checks passed with two retail-dependent skips in this invocation (prior disc-enabled run passed all ten). HTTP/browser route acceptance and editing controls remain pending.


### Animation persistence workflow acceptance
- In a separate temporary project populated from imported town01 evidence, set Actor0011 frame0/object0 translationX100; undo removed it, redo restored it, save/reopen retained exact source-bound edits, and clear removed it. Original user project was not saved or modified.
- Build rejected AnimationChannels rather than silently omitting it. Replaced generic component error with explicit saved-but-packaging-unimplemented explanation. Temporary project removed by scoped TemporaryDirectory cleanup. Playable animation packaging remains required work.


### Persistent animation command integration
- Added set/clear_animation_channels commands using the existing override undo/redo representation, strict imported animation identity/source digest/channel serialization validation, and save/load component recognition. Opening these components currently requires the retail source for validation.
- Read-only-opened current project in a separate Python process and applied Actor0011 frame0/object0 translationX100 in memory; validation succeeded against animation0012. Did not save or alter the user project. Save/reopen/undo/build-rejection verification remains pending; build currently rejects the new unsupported component.


### Project animation authoring options
- Added ProjectService animation_authoring_options with fresh imported-disc digest comparison and supported imported actor binding resolution, exposing exact translation/rotation limits and animation metadata. Read-only validation against current project resolved Actor0011 to animation0012, 15 frames and 6 rigid channels.
- Build validation currently rejects unknown authored components rather than silently dropping them. Animation override persistence remains not implemented; options are the verified context for the next command integration.


### Unified animation serialization and preview
- Authored animation preview now uses the public authored-record serializer, so preview and future packaging share the same binding/hash validation and audit. Extended focused check verifies decoded edited value, identical metadata/effective digest, immutable imported preview, and no model expansion in record-only serialization.
- Ten animation authoring/scene checks passed with private retail disc enabled, no skips (first run without disc skipped two). This is serializer/preview validation, not project persistence or playable output.


### Animation authoring record API
- Traced existing serializer/catalog and ProjectService command boundaries. Added public authored_animation_record API that verifies actor/model binding and record hash, serializes bounded channel edits, and returns private bytes plus source-coordinate/audit metadata without expanding posed meshes. This supports subsequent project validation and packaging without accessing private catalog buffers.
- Existing animation-authoring checks rerun with both integration and tests import paths (first invocation lacked tests path). Project persistence/editor/build integration remains unfinished.


### Node field checkpoint and next authoring gap
- Reviewed field-inspector changes and feature ledger. Node field expansion is browser-verified on an unmatched node; notes formatting is included.
- Authoritative ledger still identifies sparse rigid animation editing as SDK-preview-only: project persistence, editor controls, playable carrier packaging and gameplay acceptance are absent. ProjectService search found no animation override integration. This is the next substantial authoring workflow to extend after the inspector checkpoint; arbitrary import/extra channels remain distinct requirements.


### Unmatched node fields browser acceptance
- Reloaded editor service only (session 64288) and captured 90 nodes. Filtered unmatched 80083284 and expanded Captured fields and evidence. Browser displayed raw data, Unknown conditional interpretation, unresolved applicability, strongly_inferred/confirmed/contradictory confidence, and reference notes without asserting subclass identity.
- Separated evidence notes into a block with whitespace after visible concatenation was found. No extra guest reads beyond the existing Observe actors operation.


### Unmatched node field inspector
- Independent runtime-node entries now expose copied decoded fields from the already guarded prefix capture, without additional memory reads. Collapsible UI displays interpreted/raw values, confidence, applicability, unresolved status, notes and evidence IDs. This enables inspection without an imported actor match.
- Eight correlation tests and JavaScript syntax pass. Server reload/fresh browser field expansion remains pending.


### Runtime overlay checkpoint
- Pick runtime node is now disabled when live epoch/correlation evidence is unavailable and its active mode clears when that evidence is lost, avoiding a misleading pressed tool in Edit mode.
- Checkpoint includes visually verified cyan overlays, mode suppression, isolated guard checks, frame/node inspector links, overlapping subset checks, and browser-confirmed explicit picking of 31 stacked nodes. Alt-key shortcut remains not independently browser-accepted.


### Runtime picking browser acceptance
- Read current browser API documentation: LocatorClickOptions does not support position, explaining prior center-click misses. Used documented tab.click([1126,700]) against the visible cyan stack with Pick runtime node enabled. Dialog opened 31 of 31 captured nodes, including distinct node IDs at 16320/0/16320.
- Explicit picking and overlapping-hit selection are now browser-accepted. Alt shortcut remains separately unverified. No authored state or game input changed. Updated README to reflect actual evidence.


### Explicit runtime picking mode
- Added Pick runtime node toggle which enables the runtime layer and selects node hits without requiring Alt. Empty hits report no sampled node and do not select scenery.
- Browser toggle activated and empty-hit path verified, preserving Actor 0011 selection. Attempted positional click did not hit the visible marker; browser coordinate delivery remains unresolved. Syntax passes.


### Runtime marker browser picking attempt
- Refreshed screenshot confirms 90 cyan runtime positions and the relocated legend clear of the preview badge.
- Attempted Alt-modified viewport click through browser automation. The labeled viewport accepted the action but selected scenery rather than opening the node dialog. End-to-end picking is therefore not accepted; next investigation must distinguish modifier delivery/coordinate mapping from hit-handler behavior. Existing Observed nodes list remains usable.


### Runtime inspection workflow documentation
- Reviewed accumulated runtime overlay/picking diff and documented the complete read-only workflow in integrations/legaia/README.md: connect, observe, display nodes, filter/frame, inspect candidates, refresh semantics, and overlapping picks. Kept pending Alt-click browser acceptance explicit.
- Previous turn made implementation and focused-validation progress. Broader SDK authoring and release acceptance remain open; no completion claim.


### Overlapping runtime marker inspection
- Alt-click hit handling now opens all sampled nodes within the hit radius rather than choosing the first. Dialog refresh preserves the hit-ID subset; current epoch rejection still clears stale samples.
- Executed the actual dialog renderer with two overlapping selected IDs and a third excluded node: two rows retained, refresh remained scoped, and stale epoch emptied the list. JavaScript syntax/diff checks pass. Physical browser Alt-click remains unverified.


### Viewport runtime-node picking
- Added Alt-click on cyan runtime markers to open the observed-node dialog filtered by captured node ID. Normal click retains frontmost scene-mesh selection. Hit entries rebuild each draw and are checked against accepted live epoch before opening.
- JavaScript syntax passes; browser gesture acceptance remains pending. Overlapping markers currently open the first sampled hit and do not assert entity identity; multi-hit chooser is a follow-up usability item.


### Runtime overlay guard checks
- Executed the actual drawRuntimeNodeLayer function in an isolated Node context: valid sample draws, Edit mode, absent runtime, unavailable correlation, stale correlation epoch, stale node epoch, and invalid coordinate suppress drawing (7 checks passed). No user-game disruption.
- Browser mode round-trip cleared captured overlays and requires fresh Observe actors, as intended. Refreshed observation requested; adjusted legend visual confirmation remains pending until capture renders.


### Runtime layer visual acceptance
- Browser screenshots show cyan sampled-node diamonds over the scene in Live mode and their removal after switching to Edit, with the authored scene retained. This proves mode suppression, not disconnect/epoch-change suppression.
- Found runtime legend overlapping the existing preview badge; moved its canvas baseline from 42 to 78 pixels. Updated placement needs a refreshed visual check. Current wide camera views scenery backs; it is not a game-camera parity view.


### All-node viewport layer
- Added optional Runtime positions layer: cyan diamond overlays for up to 128 finite XYZ samples in the accepted live epoch, independent of imported candidate identity. Legend explicitly includes occluded nodes; authored meshes remain separate. Edit mode and invalid epochs suppress markers.
- JavaScript syntax passed and browser toggle was activated/verified pressed on revision runtime-position-layer. Pixel-level overlay and invalidation verification remain pending.


### Candidate timing live verification
- Reloaded comparison service only (session 49105). Browser freshly captured nodes, filtered 80082c9c, and selected Actor 0011. Inspector showed Binding capture frame 168271 separately from Position capture frames 168238-168238. This verifies distinct read provenance through the complete observer-to-inspector path.
- Reviewed observer/schema diff and whitespace check; no game input or authored transform changes. Full SDK goal remains incomplete beyond this inspector checkpoint.


### Candidate inspector sample timing
- Candidate records now carry the coordinate read interval separately from their later binding-evidence frame. Inspector labels both explicitly; older samples show unknown coordinate timing.
- Added a focused regression proving coordinate frame 100 remains separate from later binding reads and legacy records do not invent a coordinate timestamp. Eighteen correlation/service checks and JavaScript syntax pass. Browser served Python must reload before newly added candidate intervals appear.


### Runtime node to entity inspector workflow
- Observed nodes now includes Inspect candidate actions for existing scene entities, guarded by current live epoch and project/scene context. Selection uses the existing project selection API; no identity is promoted to confirmed and no transform is authored.
- JavaScript syntax passed. Browser filtered node 80082c9c and activated Inspect candidate Actor 0011. First click during page initialization needed retry after loading; subsequent dialog and selection actions succeeded.


### Fresh capture interval acceptance
- Restarted comparison editor service only (session 11991, port 4394); user game remained connected. Fresh observation exposed rejection of the new node frame interval by the strict observation schema. Added the optional typed position_capture_frames schema property.
- Retried through the browser successfully: 90 nodes, filter 80082c9c retained through Refresh captured list, position frames 154611-154611 and XYZ 9664/0/8640. Seventeen observer service/correlation checks pass. This resolves the prior fresh-capture and refresh-list acceptance items.


### Coordinate capture provenance and dialog refresh
- Added Refresh captured list inside Observed nodes, retaining its filter without closing the dialog. This refresh displays the latest accepted sample already held by the editor.
- Node traversal now records the guarded read frame interval beside decoded coordinates. Independent runtime-node entries use this interval instead of the later MAN binding-read frame; older samples explicitly show unknown. The separate candidate summary frame still denotes binding evidence.
- JavaScript syntax and seven correlation checks pass. Server restart/fresh capture and browser acceptance of these latest changes remain pending.


### Observed-node browser acceptance
- Previous continuation made implementation progress. Browser 4394 was refreshed, Live mode entered, and Observe actors captured 90 nodes. Filtering 80082c9c reduced the dialog to 1 of 90 at guest XYZ 9664/0/8640; Frame node activated and closed the dialog. No controller input or authored coordinate mutation was issued.
- Opening the dialog while capture was still pending showed an empty snapshot; reopening after completion populated it. Refresh-in-dialog and exact coordinate capture-frame provenance remain follow-up improvements. This is inspector workflow evidence, not full scene parity acceptance.


### Observed-node inspector continuation
- Added bounded scrolling and filtering by runtime node identity, coordinates, or candidate entity ID to the captured-node dialog. Camera framing remains guarded by live mode, project/scene context, and accepted observation epoch.
- JavaScript syntax check passed. Seven correlation checks passed with PYTHONPATH=integrations/legaia (initial invocation lacked the required import path). Editor API on port 4394 currently reports runtime available. Browser interaction acceptance of the new filter remains pending; no game input or authored NPC coordinate changes were made.


### User interior-placement clarification
- User reports that remaining NPCs appear correctly positioned in houses beside the main map. Preserve their imported coordinates; absence of a displayed source-ground cell is an unresolved preview elevation, not proof of a misplaced NPC. The previously inspected furnished interior supports this interpretation, but individual runtime placements remain to be verified.


### 2026-09-10 — Inspect runtime nodes without imported matches

- Previous turn was progress: committed coordinate workflow checkpoint. Added observed XYZ/epoch/frame to independent runtime-node correlation entries, including nodes without candidate entities. Added Observed nodes dialog with captured coordinates, candidate counts and camera-only Frame node actions.
- Dialog framing rechecks live mode/epoch; captured marker hides when mode/epoch changes and is labeled separately from a manual reference. No identity inference or runtime write is introduced.
- Seven correlation tests and JavaScript syntax pass. Server refresh and browser acceptance for the new node dialog remain pending.

### 2026-09-10 — Checkpoint coordinate comparison workflow

- Previous turn was progress: checked interior geometry and preserved unresolved positions. Preparing a scoped checkpoint of the preview refresh fixes, separate derived elevations, live coordinate/header tables, sampled framing and manual coordinate locator, together with the user's rendered-wall acceptance evidence.
- Focused tests and browser checks are recorded above. Interior/script placement, comprehensive identity binding and the full SDK buildout remain incomplete; this checkpoint is not goal completion.

### 2026-09-10 — Check unresolved actors against interior geometry

- Previous turn was progress: reviewed checkpoint diff before user clarified interior placement. Tested transformed scenery bounds at the four unresolved coordinate groups. Positions4544/12096 and3776/12096 overlap objects168/184;12096/7488 overlaps decoration280;16320/16320 overlaps no preview scenery bounds.
- Browser framing Actor0036 at12096/7488 shows a furnished room and bed at its location. This supports the user's interior-geometry explanation for at least this actor. Bounds overlap alone does not establish floor height or correct pose, and the screenshot does not validate its character mesh appearance.
- Preserved all actor coordinates; no automatic terrain snap or inferred relocation. Twenty-two actors at the boundary remain unclassified. No game input sent.

### 2026-09-10 — Expose unresolved preview surface placement

- Previous turn was progress: regression checks and capability documentation. Examined the captured height-preview output:22 of27 unsampled actors share16320/16320; remaining five occupy4544/12096 (two),3776/12096 (two),12096/7488 (one). No semantic inactive/parked classification is inferred from that distribution.
- Added explicit preview_height_status and an unresolved-elevation inspector section explaining missing displayed source-ground cells and the ground-plane fallback. Source interpolation is still separate from imported/authored/runtime heights.
- JavaScript syntax and five scene-preview tests pass. Browser/server refresh acceptance for this label remains pending. No game inputs sent.

### 2026-09-10 — Check coordinate preview regressions and capability scope

- Previous turn was progress: browser-validated coordinate locator and local landmarks. Ran seven existing scene-preview/environment-project tests; all pass, covering transform cache reuse and authored state behavior. These are focused fixture checks, not full game acceptance.
- Updated FEATURE_MATRIX with current derived-height coverage, live coordinate/header comparisons, camera framing, coordinate locator and retained-preview evidence, explicitly preserving unresolved heights and identity/registration limits.
- No game inputs or source payload tracking. Full goal remains incomplete.

### 2026-09-10 — Verify coordinate locator against captured wall landmarks

- Previous turn was progress: user confirmed rendered scenery gap. Browser-tested Locate coordinates with the earlier live position1886/0/1740. Marker and camera target use guest values through the existing Y display conversion; no actor correspondence or authored position mutation.
- After orbiting to the inner wall face, screenshot shows the reference on the pale path between the broken ramp and the dark rock at the wall base, consistent with the earlier user screenshot at that coordinate. This supports local visual agreement, not complete scene registration or exact camera parity.
- Locator is functional in-browser; global height/actor/script placement and full SDK requirements remain open. No game inputs sent.

### 2026-09-10 — User confirms rendered wall edit

- User explicitly confirmed the opposite wall instance is missing and supplied `C:/Users/sammo/AppData/Local/Temp/codex-clipboard-3f2b5ce9-901a-4087-8bc7-1e4b7ba48cd6.png`. Screenshot visibly shows a gap at the wall base beside Vahn and the pale path. Combined with the prior matching package/live MAP spans, this supplies user-observed visual acceptance of the edited scenery gap.
- This validates the visible change in the manual run, not collision changes, full-scene coordinate parity or all NPC placement. The individual offset moves a wall section; it does not author a collision opening.
- Coordinate-locator implementation began before the user message (camera-only reference marker, not yet browser-validated). Broader coordinate and live-inspector work remains open.

### 2026-09-10 — Establish repeated wall model instances

- Previous turn was progress: browser-validated live framing. Queried scene placements near captured player1886/1740: nearest wall is record193 cell1805 at1728/0/1856, using model0007; edited record194 cell1833 uses the same model0007 at5312/0/2112. Record193 has Y rotation2048 versus record194 rotation0.
- Selected/framed record193 in the browser and orbited the camera to inspect the surrounding village. This establishes repeated model instances and disqualifies texture resemblance alone as landmark identity. It does not yet prove complete scene alignment or the rendered edit.
- No game inputs or authored edits. Current browser selection is the nearby unedited wall for comparison.

### 2026-09-10 — Browser-validate sampled-position camera framing

- Previous turn was progress: implemented Frame live samples. Refreshed comparison editor4394 and invoked it with Actor0011's retained epoch-scoped sample. Camera centered the purple sampled marker in the separate interior geometry region, while the inspector retained imported placement and derived previewY-128 as distinct values.
- Switching to Edit disabled Frame live samples. The browser also displays the new Preview elevation section with cell5398. No game input or new continuous sampling was sent.
- This verifies camera/inspector interaction only, not candidate identity or scene/runtime registration. Full goal remains incomplete.

### 2026-09-10 — Frame sampled actor locations in the viewport

- Previous turn was progress: exposed captured placement-header evidence. Added Frame live samples to the scene toolbar, using only selected actor candidates accepted by existing live-mode/epoch/finite-coordinate guards. It frames all candidates together, preserving ambiguity, and changes only the editor camera.
- Button disables when no eligible sample remains; activation rechecks the guard. Guest positions pass through the existing display conversion. Syntax and whitespace checks pass; browser interaction validation remains pending. No game input sent.

### 2026-09-10 — Distinguish placement headers from runtime relocation

- Previous turn was progress: live coordinate table accepted. Inspected the retained authoritative observer output: Actor0011 candidate header2880/5440 agrees with imported placement despite current9664/8640. The prior appearance-only explanation was incomplete; matching header is additional evidence, while scripted relocation and unconfirmed identity remain possible.
- Added placement-header agreement and captured header X/Z to each candidate inspector. Clarified that runtime-minus-effective deltas are not coordinate calibration. Several other headers also agree while current positions differ, so no global offset is justified by these samples.
- JavaScript syntax and whitespace checks pass. No new game input, sampling or guest writes. Coordinate registration remains open.

### 2026-09-10 — Exercise live coordinate table through guarded sampling

- Previous turn was progress: browser-checked terrain-derived Actor0011 placement. In comparison editor4394, Check runtime, Live and Follow live succeeded. The new comparison table displays sampled guest coordinates and missing imported height correctly; stopped following after inspection.
- Actor0011 imported2880/unknown/5440 has an unconfirmed appearance candidate at9664/0/8640, node80082c9c (sample frame82403), yielding X/Z deltas6784/3200. This does not establish that actor identity or a coordinate offset; appearance reuse remains ambiguous and must not drive placement correction.
- Corrected the SDK preview limitation text to describe terrain-derived height fallback. No controller input or guest writes. Full registration remains unresolved.

### 2026-09-10 — Load and inspect terrain-derived actor elevations

- Previous turn was progress: implemented source-terrain interpolation. Restarted only editor4394 (new server session84253), leaving user's game untouched. Fresh service output samples25/52 actors, eight at nonzero height; all sampled actors retain imported Y=null and model matrices use the reflected preview Y. Remaining27 lack a source-ground cell.
- Refreshed the user's comparison tab and framed Actor0011 at2880/-128/5440: screenshot shows the actor on the raised grass surface. Added a separate derived preview-elevation inspector section and corrected the obsolete ground-plane-only text. Syntax passes; the added label needs a further browser refresh.
- Full coordinate registration and broader live-inspector acceptance remain open. No game input sent.

### 2026-09-10 — Derive actor preview elevation from visible terrain

- User requested continued coordinate/live-inspector implementation. Added triangle interpolation over the decoded source ground mesh for actors whose imported/effective Y is unknown. SDK output keeps original position unchanged and exposes separate preview_position and preview_ground_sample evidence; viewport actor positions consume that derived value only for a current preview.
- Both source triangle slopes, diagonal seam, missing cells, negative/invalid coordinates passed focused checks. The user's last captured X1886/Z1740 samples source terrainY0, agreeing with the earlier liveY0 at that one point. This is a single-point agreement, not global coordinate registration or runtime collision validation.
- Syntax/diff checks pass. Server restart/browser acceptance and wider live landmark comparison remain pending. No game input or runtime writes.

### 2026-09-10 — Begin coordinate comparison inspector

- User prioritized position/coordinate agreement and a live inspector prototype. Added a guest XYZ comparison table to existing sampled candidate panels: imported, effective, observed and observed-minus-effective, preserving unknown heights and uncertain correspondence.
- Actual coordinate helper checks pass for authored deltas, missing heights and signed guest Y; JavaScript syntax and diff checks pass. Browser/live acceptance of this new table is pending. NPC floor placement and decoration/runtime alignment are still unresolved and remain the priority; this table does not claim to fix either.
- Recovered an interrupted local text write using HEAD plus the exact prior preview-refresh edits, then checked the restored file's syntax and scoped diff. No game input sent.

### 2026-09-10 — Compare user wall screenshot and preview limitations

- User's new screenshot shows Vahn on the pale path beside a textured wall and broken stone ramp, matching the kinds and arrangement of landmarks in the framed preview; the game wall appears continuous where the editor shows a gap. This is a visual mismatch requiring registration, not proof the user chose a wrong location.
- Read-only current player capture is1886/0/1740. Editor cell1833 origin5312/0/2112 and local mesh bounds[-64,-1216,-128]..[128,0,128] cannot be reconciled by merely calling the origin a wide mesh boundary. Exact landmark/instance correspondence remains unresolved; repeated scenery is possible.
- Source confirms actor preview height still substitutes a ground plane when imported Y is unknown, while terrain uses decoded elevations. This can put NPC meshes under terrain and is not a faithful assembled-scene placement implementation. No runtime input or source patch was made for this comparison.

### 2026-09-10 — Inspect user's manual wall verification

- User requested focused investigation while broader goal remains paused. Captured their manually launched runtime (identity proc-abd75bec0a104051650be98afddbb94bf87d94b858174adf9487bc55aae71c1a), without controller input. Screenshot shows Vahn beside cliff/trees; read-only player position1838/-192/2794 differs from authored decoration5312/0/2112.
- Active overlay plan matches the intended package;36 sectors consumed. Live descriptor5 has Z offset-256, descriptor194 remains unchanged and cell1833 references5, confirming MAP byte delivery in this fresh manual run. This does not establish rendered behavior.
- Opened the actual saved build project in separate editor4394 for visual location comparison. The earlier inability to access tool-launched windows remains a user-reported launch problem; a window handle alone was insufficient evidence of usability.

### 2026-09-10 — Browser-check retained scenery inspector

- Previous turn was progress: handled Undo during preview refresh. Opened a separate copied project on4395 (server session89045, browser tab63); no writes to the user's running project's saved data and no game input.
- Browser loaded260/261 meshes. Cell1833 individual X64 produced effective5376/0/2112; X128 produced5440/0/2112. Captured the intermediate DOM showing both previous-preview position labels and the disabled individual Apply button, with the selected decoration still present. This verifies the retained-inspector path in-browser; rapid Undo timing remains covered by the deferred-response function check rather than a browser capture.

### 2026-09-10 — Handle undo during retained-preview refresh

- Previous turn was progress: retained same-scene preview and gated scenery edits. Added cancellation when Undo returns to the already loaded source key, clearing the pending badge immediately and rejecting the superseded response. Same-scene refresh errors retain renderer geometry for a later Undo recovery.
- Executed the actual refresh function with a deferred response: Undo aborts the request, preserves geometry and rejects its late response without loading it. Node syntax passes. Browser acceptance remains pending; no runtime input sent while user navigates.

### 2026-09-10 — Retain scene context during preview refresh

- Previous turn was progress: consolidated capability documentation. While user controls the existing game, changed the editor to retain the previous preview for the same project/scene during refresh, with an explicit previous-preview badge and position label.
- Scenery numeric controls and move handles are disabled until the source key is current; command callbacks reject stale inspector keys. Different projects/scenes cannot reuse the retained preview. No game input was sent.
- Node syntax and diff whitespace checks passed. Actual helper-function checks cover retained/current previews, project/scene isolation, failed preview and capability removal. Browser refresh acceptance remains pending; no new browser claim is made.

### 2026-09-10 — Consolidate current scene-editor capability status

- Previous turn was progress: verified windowed runtime and released input for user navigation. No controller input sent this turn.
- Replaced contradictory superseded scene-editor milestone paragraphs at the top of FEATURE_MATRIX with a current capability/evidence/remaining-work table. Preserved explicit boundaries between browser acceptance, package-byte/runtime consumption evidence and still-pending rendered-wall acceptance. Animation and broader SDK requirements remain unchanged.
- This documentation change does not claim full scene parity or goal completion. User retains navigation control.

### 2026-09-10 — Hand navigation to user in existing windowed runtime

- Previous turn was progress: finished Mei dialogue and resumed movement. Continued normal input around plaza to4802/-192/3502. User offered to navigate to the wall in a non-headless run.
- Verified PID30176 already owns a native game window titled `Legend of Legaia Recompiled`, handle10488622. No replacement launch needed. At frame83970, pad status confirms override=-1, override_frames=0 and released buttonsFFFF; automated input is inactive. Preserve this run and let user navigate.
- Scenery visual acceptance remains pending; full goal active.

### 2026-09-10 — Finish Mei introduction and restore route movement

- Previous turn was progress: identified the active dialogue as the movement gate. Finished Mei's conversation through visible choices and ordinary Cross input, selecting the offered not-now response for measurements. Text and camera advanced; Mei departed.
- Repeated Right40 after conversation completion moved Vahn from2368/-64/3392 to2688/-64/3392 at frame77111, proving normal control resumed in the same identity-checked4399 runtime. Package consumption remains36 sectors. Private evidence: `route-east-retry-after.json/png`.
- Next route segment heads toward higher Z around the source collision boundary. Full SDK goal and scenery appearance acceptance remain open.

### 2026-09-10 — Identify active Mei dialogue on viewing route

- Previous turn was progress: decoded a source-grid viewing approach. Revalidated the same runtime through controller/capture requests. Right40 left player2368/-64/3392 unchanged; inspecting the screenshot revealed Mei's active introduction dialogue, so this movement result is not collision evidence.
- Advanced two visible dialogue pages with ordinary Cross inputs. Camera and text advance normally; no process restart, guest writes or savestate loads. Continue the conversation before attempting the route. Scenery visual acceptance remains open.

### 2026-09-10 — Revalidate runtime and inspect source route

- Previous goal turn was no progress (acknowledged the Select correction only). Revalidated the same live process through runtime identity and a fresh player read: frame60414, position2368/-64/3392, 36 overlay sectors consumed. No restart or guest writes.
- Decoded the retail collision baseline before further movement. The edited wall coordinate5312/2112 lies in a blocked source subcell; walking directly to its center is therefore an unsuitable acceptance route. A private breadth-first source-grid route now identifies the nearest reachable viewing approach, with runtime collision/script differences explicitly unverified. Evidence: `local-output/sdk-20260909/decoration-gizmo-browser/source-route.json` and `near-wall-route.json`.
- Scenery rendering acceptance and the full SDK goal remain open.

### 2026-09-10 — Route toward the edited wall and reproduce step visibility

- Previous turn was progress: reached controllable field. Continued bounded normal movement in the same4399 run. At3152/32/3182 and3282/96/3246 Vahn was not visibly rendered; moving up to3282/128/3486 restored visibility. This reproduces the earlier step-area symptom on executable97f0f026, without establishing cause or implicating the scenery edit.
- Western route retained visibility at2668/-64/3294; Down stopped atZ3182. Continued around the west side to2368/-64/3392 near the round house, frame46514. These are measured route constraints, not an accepted gameplay collision bug diagnosis. Latest private screenshot `west-around-boundary-after.png`.
- Host53840 remains live and identity checks pass. Full MAP overlay consumption unchanged; no RAM writes/state loads. Edited wall rendering still unverified; full goal active.

### 2026-09-10 — Reach controllable field with edited scenery loaded

- Previous turn was progress: exact runtime MAP spans matched the package. Advanced the elder introduction using normal Cross inputs and the visible Yes choice. At frame35393 the camera returned to normal field view. A bounded30-frame Down input visibly moved Vahn away from the tree; before/after player captures provide coordinates for routing.
- Same identity-checked runtime4399 and host session53840 remain live. Full overlay consumption remains36 sectors/73728 bytes with no guard failure. Private `elder-page-*.png` and `player-before/after.json` preserve evidence. No restart, RAM write or savestate load.
- This additionally accepts interactive field progression for the current stability executable with the instance package. The edited wall's rendered placement remains unverified; full goal active.

### 2026-09-10 — Verify individual scenery bytes in the running field

- Previous turn was progress: Select skipped prologue and full MAP overlay consumption was observed. Same4399 process advanced through the name prompt with normal inputs; Vahn rendered beside the Genesis Tree in the field introduction.
- Revalidated the previously observed MAP address candidate0x80139530 through exact package comparisons: descriptor5 is a32-byte match including authored Z=-256; descriptor194 remains a32-byte source match; cell1833 contains0x2005 and counterpart2089 contains0x20c2. All four bounded reads match generated package spans exactly. Runtime identity was checked before reading; no RAM writes or state loads.
- Evidence: private `map-candidate.json` and `runtime-map-comparison.json`, frame25298, plus field-intro screenshot. This accepts loaded runtime data, not final rendered-wall placement or collision behavior. Host session53840 remains live; full objective active.

### 2026-09-10 — Skip prologue and observe edited MAP consumption

- User supplied the correct prologue skip input: Select. Sent normal port1 Select (active-low65534,8frames) to the same identity-checked4399 run. The prologue skipped; overlay telemetry advanced from0 to36 sector applications/73728 bytes, lastLBA480.
- At frame18375 the runtime visibly rendered the town field establishing view (`field-loaded.png`). This proves the package's full MAP overlay was consumed and field rendering began; the edited wall instance itself has not yet been located/compared in-game. Evidence is `after-select.json` and `field-loaded.json` under the private decoration-gizmo-browser directory.
- Host session53840 remains live for continuation. No restart, RAM writes or savestate loads. Full SDK goal active.

### 2026-09-10 — Verify New Game progression in the retained run

- Previous turn was progress/verified live observation, but its claim that Cross selected New Game was too strong. The character movie returned to the title menu: treat those images as attract-sequence evidence only. Corrected that interpretation before continuing.
- Same identity-checked process on4399 remained live (host session53840). Start from the title menu reached the rendered story prologue at frame12140; subsequent Cross inputs advanced its text/scene. Latest capture `story-current-2.png` is frame14250. No restart, memory mutation or savestate load.
- MAP overlay consumption remains0 sectors; field scenery is not yet accepted. Continue the retained process from the story prologue. Full goal remains active.

### 2026-09-10 — Advance persistent scenery validation toward the field

- Previous turn was progress: built and cold-launched the saved gizmo package. Started a separate persistent RunService host, session53840, runtime PID30176 on4399, run `20260911T000231Z-d6cb2b6e`, identity `proc-91ac4df721f370c2fb84739d64acbfd3c6d4e5bed055996ab707ad86be236415`. Its live handle was polled successfully; this run remains active for continuation. Stop via the private `stop-field-run` marker to let the owner close its exact process handle.
- Normal port1 Cross selected New Game. The title image persisted while FMV/XA state was active; captured pad/MDEC/FM V diagnostics rather than assuming a crash. Normal Start advanced to the visible Genesis Tree opening sequence at frame5896. No RAM writes or savestate loads.
- Package remains enabled and disc guard intact, but overlay sector consumption is still0: target field not yet loaded. Evidence and identity-checking control script live under `local-output/sdk-20260909/decoration-gizmo-browser`; original runtime4397 remains untouched. Full goal active; continue this same process rather than relaunching on an observation timeout.

### 2026-09-10 — Build and cold-launch the viewport-authored decoration

- Previous turn was progress: browser-accepted and committed decoration gizmos. Built the actual saved cell1833 Z=-256 override from the gizmo project into private package8fdcffdf488d06cf, SHA256823dd770b419003b7d09a655bb9246d2f3f966bd719744be7b16d6acc1195dde. Audit reports one individual cell edit and one73728-byte MAP overlay.
- Cold launched through RunService on separate port4399 using executable SHA25697f0f0260f7d4c977a385e0dcd3b5f625c7112f9eefd04bcfeab1684998fd4aa. Initial capture was prematurely at frame0/display-disabled and stopped cleanly. A second bounded cold launch reached frame837 and visibly rendered the Prokion logo. Runtime identity, disc identity and one committed enabled overlay were verified; disc guard did not fail. Both owned runs stopped with exit0; original runtime/editor sessions were untouched.
- Evidence: `local-output/sdk-20260909/decoration-gizmo-browser/{build-result.json,early-launch.json,cold-launch.json,scenery-cold.png}`. Overlay consumption remained0 sectors: the target field has not loaded, so this is package activation/startup evidence only, not scenery gameplay acceptance. Full objective active.

### 2026-09-10 — Browser acceptance for scenery move handles

- Previous turn was progress: implemented decoration X/Z handles and checked command conversion. In isolated town01 editor4395, dragging the X handle moved cell1833 from X5312 to5619; viewport outline and inspector matched, Undo restored5312. Enabling64-unit snapping and dragging Z moved1856 to2112, encoded as individual offsetZ=-256.
- Selecting the other record194 instance at41,16 showed its original position and offsetZ0. Save succeeded. The test server was stopped cleanly; private project retained under `local-output/sdk-20260909/decoration-gizmo-browser`. Post-command preview responses completed within the next logged second, consistent with geometry reuse.
- JavaScript syntax and diff checks pass. Pointer release, snapping, command/preview agreement and Undo are browser-accepted; continuous mid-drag rendering and gesture cancellation were not separately captured. In-game scenery behavior and full SDK/release-parity scope remain open.

### 2026-09-10 — Add direct decoration movement handles

- Previous turn was progress: committed cached scenery transform projection with retail timings. Extended the existing X/Z gesture path to selected static decorations, with individual overrides, inherited shared axes, existing snapping, draft geometry position and selection/context cancellation. Hidden scenery and spawnable objects do not acquire these individual handles.
- A Node check executing the actual `moveDecoration` function verified X delta, reversed Z delta, preserved rotation/other-instance bindings, rejected out-of-range offsets and unchanged source binding. JavaScript syntax and diff checks pass. This proves command conversion, not pointer interaction: browser drag/render/undo acceptance remains pending.
- Full scene editor, in-game scenery behavior and the wider SDK/release-parity objective remain active; no completion claim.

### 2026-09-10 — Reuse scene geometry for scenery transform edits

- Previous turn was progress: browser-accepted and committed individual decoration editing. Split preview request identity from geometry identity so Environment overrides update transforms without invalidating imported meshes, poses or textures. Source-disc, appearance and texture dependencies still invalidate geometry; final source identity is rechecked before returning projected transforms.
- Five scene-preview tests and two environment-project tests pass. New cache test verifies moved/reverted transforms, unchanged geometry, distinct request identity and no loader calls after editing. Diff checks pass.
- Fresh retail service measurement against the saved individual-browser project: cold18.423s, clearing override0.386s, undo/restoring1.122s. All asset payloads were equal; cell1833 projected X5440 ->5312 ->5440 with matching authored flags. The measurement opened an ephemeral server without running it and closed its observer; no game input or saved-project mutation. Browser latency after this change remains unmeasured. Full objective remains active.

### 2026-09-10 — Browser acceptance for individual decoration editing

- Previous turn was progress: integrated instance editing across SDK layers. In an isolated town01 editor on4395, selected decoration194 at41,14, applied individual X128, then verified effective X5440 with a textured viewport and selection outline. The shared counterpart at41,16 retained X5312 and no individual override.
- Browser Save and Undo succeeded. After preview completed, the original instance returned to X5312/offset0 with Redo available. Private project is under `local-output/sdk-20260909/individual-browser`; the owned test server was stopped without touching original runtime/editor ports.
- All20 retail-enabled build tests passed in46.188s. JavaScript syntax and diff checks passed. Browser exposed a remaining usability issue: transform edits regenerate scene geometry and temporarily replace scenery hierarchy/inspector during loading; a selector timeout during Undo resolved after that same request completed. No runtime allocation acceptance is claimed; full objective active.

### 2026-09-10 — Connect individual decoration authoring across SDK layers

- Previous turn was progress: introduced bounded instance serialization. Fresh retail town01 allocation for cell1833 copies descriptor194 into zero-filled unreferenced slot5, redirects only that cell, and changes9 bytes for X128. This is retail data evidence, not runtime acceptance.
- Project Environment bindings now support individual cell edits alongside shared record edits, validated before command mutation and on reopen/build. Shared edits apply first; individual axes take precedence. Preview retains original cell identities and projects both layers. Build audits record allocation, exact allowed descriptor/grid spans and affected cell identity.
- Added individual inspector controls for static decorations; shared edits preserve individual bindings and vice versa. The UI is syntax-checked but not yet browser-accepted. Two retail tests pass in8.679s, covering shared packaging plus combined command/undo/redo/save/reopen/preview/build and unchanged unrelated bytes. Existing environment tests passed (10 plus1 skipped) before the UI addition.
- Spawnable scenery remains shared-only. Browser workflow, in-game allocation behavior and broader runtime consumers remain unverified. Full SDK/release-parity objective remains active.

### 2026-09-10 — Begin independent decoration serialization

- Previous turn was progress: committed the shared-scenery workflow after 19 retail-enabled build tests passed. Inspected pinned Andrew `field_regions.rs` descriptor/grid consumers before extending allocation.
- Added a source-hash-bound instance serializer for static decorations. It copies a descriptor into an unreferenced, zero-filled, non-reserved slot, changes selected transform axes, and redirects only the selected cell while preserving its upper flag bits. Allocation is deterministic; full tables, duplicate cells, reserved descriptors and spawnable objects are rejected. This is a serializer foundation, not an accepted editor feature; grid-reference absence does not establish every possible runtime consumer.
- Four focused authoring tests pass, including exact output bytes, unchanged shared source, deterministic allocation and exhaustion rejection. The first test run exposed a fixture's accidental no-op value; corrected the fixture to request an actual change. Project persistence, preview/build integration and retail/runtime instance validation remain next; the full objective remains active.

### 2026-09-10 — Verify and checkpoint shared scenery authoring

- Previous turn was a status response, with no implementation progress. Revalidated the working tree and resumed the pending authoring checkpoint. The earlier test process is no longer present among current Python processes; its missing output was not treated as a passing result.
- Ran all 19 `test_build*.py` tests with `LEGAIA_DISC_BIN` supplied: all passed in 29.469 seconds, including source-bound environment packaging. Environment tests: 8 passed, 1 retail-dependent skip in the separate invocation. JavaScript syntax and diff whitespace checks passed.
- Shared scenery transforms now connect inspector editing, effective scene preview, undo/save/reopen, authored asset review and guarded MAP build output. Changes remain shared-record edits; independent instance allocation and in-game scenery behavior are not accepted. The full SDK and release-parity objective remains active.

### 2026-09-10 — Regress environment packaging against retail source

- Previous turn was progress: authored scene catalog and shared-cell build report. Verified town01 MAPentry1 and town0c MAPentry19 have identical content hashes but distinct disc spans; this town01 overlay does not target town0c's separate entry.
- Existing build suite:18 tests,14 passed and4 retail-dependent skips. Added and ran retail environment build acceptance: save/reopen, exact single-byte payload delta, before/after hashes, two affected grid cells, report count and uncompressed audit status all pass. No runtime launch. Full objective active.

### 2026-09-10 — Surface saved scenery edits in project review

- Previous turn was progress: updated packaging UI/audit evidence. Scene-owned environment overrides now appear in the project-wide authored asset catalog with record counts and Open scene navigation. Build reports carry affected-grid-cell counts, displayed beside shared edit scope. Uncompressed-only build validation gets a readable label.
- Save/reopen regression now asserts the authored scene catalog retains the Environment binding. Two project tests, JavaScript syntax and diff checks pass. Browser authored-catalog/build-report acceptance remains open; full objective active.

### 2026-09-10 — Align scenery authoring UI and build evidence

- Previous turn was progress: guarded MAP packaging and independent byte comparison. Updated stale read-only/packaging UI wording and scene workflow documentation. Regenerated private build3c52729fcb515a4c, packageSHA cf245f3d6eb7819c354de104764dd76801ab84159b2421d689ae34720efd8e81; audit reports shared offset.x0 to128, fresh provenance, preserved opaque bytes and no required MAN LZ decode. Runtime remains not_run.
- Four environment authoring/project tests, JavaScript syntax and diff checks pass. Full objective active; in-game scenery acceptance, independent instance edits and remaining SDK/stability scope remain unfinished.

### 2026-09-10 — Package shared scenery transform edits

- Previous turn was progress: browser edit/save/undo acceptance. Build now reimports environment source, patches audited descriptor axes and emits a guarded private MAP overlay. It checks direct disc-span identity and unchanged non-audited bytes, retains overlap rejection, and reports shared-record scope.
- Built saved record194 X offset0 to128 into private build6929f680c304c0f0 (packageSHA91a3951e83cbf230d8022b18aeb934a13268df513e94202526679e152c0e4410). Independent comparison confirms only MAP byte6208 changes, with73727 other bytes identical. Runtime not launched. Corrected audit LZ label for uncompressed-only outputs afterward; fresh build ID will differ. UI packaging note still needs updating. Full objective active.

### 2026-09-10 — Accept shared scenery edit/save/undo workflow

- Previous turn was progress: inspector transform controls. Isolated4395/tab60 edited record194 X offset0 to128. Both instances show effective X5312 to5440 with their distinct Z1856/2112 intact. Saved through editor; separately reopened saved project with ProjectService and confirmed offset128 and clean state. Browser Undo restored offset0 and effective X5312, with Redo available.
- Initial verification helper passed a string to ProjectService.open, which requires Path; corrected the helper and reran successfully. Existing read-only section labels need refinement now that a shared-transform authoring section exists. Stopped isolated editor through owned stop file. MAP packaging/runtime acceptance remains open; full objective active.

### 2026-09-10 — Expose shared scenery transform authoring in the inspector

- Previous turn was progress: effective environment preview projection. Added source offsets/hash to preview metadata and scene-wide authored binding to response. Inspector now provides imported-labeled offset/rotation controls, effective position and Apply shared transform, preserving edits on other records. Returning axes to imported values removes that record's override. Live mode disables inputs.
- Environment selection survives successful same-identity preview refresh. UI explicitly states packaging is not yet supported. JavaScript syntax and two environment project tests pass; browser save/undo/reopen acceptance remains next. Full objective active.

### 2026-09-10 — Project authored scenery transforms into scene preview

- Previous turn was progress: persistent source-bound Environment overrides. Preview cache now includes these overrides. Verified descriptor changes project onto all matching instances with subtractive source Z offsets and authored rotations; source transforms remain intact and effective transforms are separate response fields.
- Six project/scene-preview tests pass, including shared-instance deltas, Z sign, rotation and imported metadata preservation. Editor controls and MAP packaging remain next. Full objective active.

### 2026-09-10 — Persist source-bound scenery edits with undo

- Previous turn was progress: exact shared-record patcher. Connected scene-owned Environment overrides to project commands, source revalidation, undo/redo, clear and offline save/reopen validation. A stale MAP hash is rejected before project mutation. Build explicitly rejects these overrides until MAP packaging is integrated, preventing silent baseline output.
- Focused project workflow test passes for dirty state, undo/redo, save/reopen, offline clear/undo and stale-source nonmutation. Python compile checks pass. Editor controls, effective preview and build packaging remain next; full objective active.

### 2026-09-10 — Implement audited shared environment transform writes

- Previous turn was progress: full source-grid impact counts. Added source-hash-guarded MAP descriptor transform patcher for signed offsets and exact PSX rotations. Only requested two-byte axes change; audit records all affected grid cells. Duplicate/out-of-range/unknown/unreferenced edits are rejected; anchor, collision and other descriptor bytes remain untouched.
- Two tests pass for exact output bytes, shared-cell audit, no-op identity and invalid/stale rejection. This is infrastructure for the next persistent editor/build workflow, not completed scenery authoring. Full objective active.

### 2026-09-10 — Count complete source-grid sharing before scenery writes

- Previous turn was progress: committed selection/disconnect workflow. Traced existing project command persistence and build validation paths for next authoring work. Added complete MAP-grid reference counts to environment preview source evidence and the shared-record inspector, including references outside visible placement gates. This distinguishes source write impact from preview-instance counts.
- Fresh town01 check: house137 has1 source reference; decoration194 has2. No currently previewed record has extra hidden-grid references in this scene, and every source count is at least its preview count. JavaScript syntax/diff checks pass. Persistent scenery overrides and packaging remain unimplemented; full objective active.

### 2026-09-10 — Record the assembled scene inspection workflow

- Previous turn was progress: disconnect response fix with focused tests. Added docs/legaia-sdk/scene-inspection.md documenting the end-to-end hierarchy, direct picking, framing, visibility and shared-record navigation workflows, with explicit current counts and fidelity/authoring limits.
- Rechecked disconnect tests, JavaScript syntax and diff formatting before consolidating the selection/inspection and response handling changes. Full objective remains active; documentation does not promote unverified parity or environment authoring to complete.

### 2026-09-10 — Handle disconnected editor responses cleanly

- Previous turn was progress: shared-record browser navigation acceptance and observed closed-tab response failure. Response transport now closes on ConnectionError/TimeoutError instead of allowing the POST exception handler to send a second400 response over the failed socket. Scope is response writes only; unrelated OSError remains visible.
- Two focused tests pass, including eight header/body disconnect variants and unrelated-error propagation. Diff check passes. Full SDK/editor/stability objective remains active.

### 2026-09-10 — Accept shared-record navigation workflow

- Previous interrupted turn was a verified wait on editor session58671. Its browser tab58 was removed while the scene response was in flight; server remained live, so reused it in tab59 without restarting. The disconnected response produced ConnectionAbortedError and an attempted400 response; request-disconnect handling warrants cleanup.
- Selected decoration194 at41,14: inspector lists two instances. Chose41,16 through the shared-record combobox: identity changed01833 to02089, Z1856 to2112, hierarchy selection and framed gold bounds moved to the second wall segment. Screenshot inspected. Stopped isolated server through its owned stop file. Full goal remains active.

### 2026-09-10 — Expose shared scenery placement records

- Previous turn was progress: selection highlight browser acceptance. Before environment authoring, expose record sharing in the inspector: matching imported instances share descriptor offsets/rotations. Added a count and selector that selects/frames another instance using the same MAP record. Counts explicitly refer to imported instances, not all grid or runtime references.
- This addresses authoring scope visibility without offering a misleading independent-instance write to a shared descriptor. Syntax/diff checks pass; browser workflow acceptance and actual environment authoring remain next. Full objective active.

### 2026-09-10 — Accept scenery selection feedback in the browser

- Previous turn was progress: environment selection bounds overlay. Isolated4395/tab57 selected/framed house137. Screenshot confirms the dashed gold box encloses its transformed mesh and shows its name. Hiding Scenery removes both house and selection overlay; inspector selection remains available. Badge changes260 visible to52 visible, confirming the visibility count path.
- Stopped isolated editor through its owned stop file. This verifies selection feedback and hidden-layer behavior; complete scene parity, environment authoring and the remaining full SDK/stability scope remain open.

### 2026-09-10 — Show selected scenery bounds in the viewport

- Previous turn was progress: direct mesh and hidden-layer picking acceptance. Added a dashed gold selection box and name for the selected environment instance using the renderer's transformed geometry bounds. The overlay respects hidden layers and unavailable geometry; it does not add transform handles or imply collision editing.
- JavaScript syntax and diff checks pass. Visual acceptance of this new overlay remains next. Full scene/editor/stability objective remains active.

### 2026-09-10 — Verify direct mesh picking and hidden-layer exclusion

- Previous turn was progress: mesh-first selection ordering. Isolated4395/tab56 framed house137, switched selection to Actor0002 without moving the camera, then clicked canvas center: inspector changed to house environment identity03238. Disabled Scenery and clicked the same point: inspector changed to ground. This directly verifies mesh selection and hidden-scenery exclusion.
- Browser role selectors did not resolve the canvas; its exact accessible label via getByLabel worked. Loaded/visible badge was also visible in the screenshot. Stopped isolated server through its own stop file. Actor-marker occlusion overlap is not separately reproduced; full scene parity and remaining SDK requirements remain open.

### 2026-09-10 — Respect visible geometry when selecting scene objects

- Previous turn was progress: consolidated decoration/layer commit. Source review found pointer-up selection tested projected actor markers before the depth-tested mesh pick, allowing a marker behind scenery to intercept the scenery click. Changed click ordering to visible mesh first, then marker fallback when no mesh is hit. Existing alpha discard and layer filtering are shared by render and GPU pick passes.
- JavaScript syntax and diff checks pass. Direct browser occlusion/picking acceptance remains required; this is an implemented ordering correction, not a claim that all interaction cases are verified. Full objective remains active.

### 2026-09-10 — Clarify loaded versus visible scene meshes

- Previous turn was progress: browser-verified layer isolation. Preview badge now separates loaded mesh count from visible mesh count, accounting for the layer filters. Seven focused Python checks and both JavaScript syntax checks pass. Diff review caught an extra EOF blank line from the earlier shell edit; removed it and diff check passes.
- Consolidating decoration decoder/catalog integration, regression tests and layer controls as one scene-inspection change. Full goal remains active; direct viewport picking, broader visual parity and remaining authoring/stability requirements are not complete.

### 2026-09-10 — Browser-verify scene layer visibility

- Previous turn was progress: layer controls implemented. Isolated4395/tab55 loaded the combined scene. Disabled Actors and Scenery, then Frame all: screenshot confirms isolated textured ground and no actor markers. Disabled Ground: screenshot confirms only the editor grid remains. Restored all three controls. Toolbar fits at the tested1740px viewport width; narrower widths remain unverified.
- Existing preview badge counts loaded meshes rather than visible meshes, so its260/261 count remains unchanged when layers hide; a visibility count would clarify this. Direct canvas picking still needs interaction acceptance. Stopped the isolated editor through its own stop file; full objective active.

### 2026-09-10 — Add scene inspection layer controls

- Previous turn was progress: second-scene decoder evidence and regression coverage. Added Actors, Scenery and Ground viewport visibility controls. Hidden meshes are excluded from drawing, GPU picking and frame-all bounds; hidden actor markers are excluded too. Controls cancel an active transform gesture and preserve project data.
- Node syntax checks pass for editor and renderer. Corrected an initially wrong gesture helper name during source review. Browser interaction/toolbar fit remain next; full objective active.

### 2026-09-10 — Check second-scene decoration resolution

- Previous turn was progress: combined browser rendering and hierarchy acceptance. Fresh town0c preview resolves162 decoration instances, with zero missing mesh identities; all decode (10019 instance triangles). This is catalog acceptance, not a second-scene visual parity claim.
- Added three passing decoration regressions covering field-versus-walk gate separation, placed exclusion, zero/special mesh selectors, signed offsets/floor nibble masking/rotations, stable distinct cell identities and malformed source bounds. Full objective remains active.

### 2026-09-10 — Browser-verify assembled decorations

- Previous turn was progress: 162 decorations connected to the preview catalog. Fresh isolated decoration editor on4395/tab54 completed scene loading with261 hierarchy instances and260 renderable models. Search returns162 decoration entries.
- Selected MAP decoration194 at41,14 and used Frame object. Inspected screenshot shows the textured wall, shoreline, ground and adjacent scenery; inspector exposes the decoration identity and source transform. This verifies hierarchy selection/framing and combined rendering, not direct canvas picking or complete retail visual parity. Original4388 remained untouched; isolated server stopped through its owned stop file.

### 2026-09-10 — Resolve field decorations into the environment preview

- Previous turn was progress: bounded decoration source decoder. Connected its normal-field sweep to the verified environment preview catalog, preserving the existing inferred scene mesh pool and source hash checks. Decorations remain unposed, separate from placed-object animation bindings.
- Fresh town01 retail read resolves all 162 decoration instances with zero missing mesh identities; all 162 geometry previews decode, totaling 10019 instance triangles. Existing scene preview path exposes these as environment hierarchy/viewport instances. Browser appearance and direct selection remain unverified; full scene and SDK objective remain active.

### 2026-09-10 — Separate the field decoration source sweep

- Previous goal turn was a status restatement (no progress). Revalidated the pinned field renderer: normal field decorations use cell bit 0x2000 and exclude placed records; world-map decoration rules use a different gate and must not be substituted.
- Added a bounded field decoration decoder with stable cell IDs, source hashes, mesh selectors and source transforms. Synthetic smoke passed for the field gate, placed-record exclusion and origin transform. Mesh resolution, retail counts and editor rendering remain next; no full scene completion claim.

### 2026-09-10 — Render textured ground alongside scene objects

- Previous turn was progress: source terrain decoder. Added verified terrain loading, scene texture association with authored texture overrides, and combined-service geometry/texture budgets. The ground surface is a separate read-only selectable environment instance with source/limitation evidence; no asset provenance is replaced.
- All11 town01 ground materials resolve address_match. Four scene-preview checks pass. Isolated4395/tab53 browser shows98/99 models and selects/frames Ground surface. Framing house137 visibly shows paths, grass and beach beneath the house and coastal structures; screenshots inspected. This is source surface acceptance, not retail camera/visibility parity; holes and missing decorations remain explicit next work.
- Prior tab52 was no longer available, so opened a new isolated tab without touching original4388. Stopped the owned terrain editor through its stop file. Full objective active; decorations, cell-level ground inspection, broader scene coverage and remaining SDK/stability work remain unfinished.

### 2026-09-10 — Decode the source ground surface

- Previous turn was progress: browser-verified environment hierarchy/framing. Added importer/terrain.py from pinned field_objects.rs build_walk_heightfield conventions: walk-visible1000 cell gate, four floor-LUT corner heights, clamped grid-edge heights, PSX quad diagonal and decreasing V along increasing row.
- Unknown page/atlas selectors remain explicitly untextured; no reference fallback grass is invented. This is a source heightfield preview, not collision-ramp geometry or a complete reproduction of the retail ground emitter.
- Fresh town01 data yields1946 cells/3892 triangles, all1946 with supported source selectors. Two focused synthetic checks passed for corner/UV ordering and border/missing-page behavior. Texture resolution, scene-service integration and visual comparison remain next; no browser/runtime mutation this turn. Full objective active.

### 2026-09-10 — Browser-verify environment inspection and framing

- Previous turn was progress: environment selection UI. Isolated editor4395/tab52 displayed97/98 meshes. Searched MAP object137, selected its hierarchy row, opened the read-only source/transform inspector and framed the textured house. Screenshot visually inspected: house, walls/coastal backdrop and other scene objects render, while missing ground is clearly visible. No claim of complete scene or retail camera parity.
- Returned through hierarchy search to Actor0002 and verified its actor inspector, preserving authoring separation. Corrected combined hierarchy count and the obsolete actor-only coordinate note; Node syntax passed and browser reload verified98 count,97/98 models and the new environment/actor distinction. An initial shell text insertion was malformed and caught by Node; corrected before reload.
- Direct canvas picking still needs explicit interaction verification. Ground/decorations remain unfinished. Stopped the isolated editor through its owned stop file; original4388 browser/runtime untouched. Full objective active.

### 2026-09-10 — Connect environment hierarchy and inspector selection

- Previous turn was progress: combined textured scene service. Added searchable environment hierarchy rows from the current verified scene preview, read-only transform/model/pose/source inspector, geometry framing, and viewport-pick routing. Environment selection is derived preview UI state; actor authoring tools receive no selected actor while it is active.
- Actor selections clear environment selection; a rebuilt preview clears stale selection. Hierarchy refreshes after geometry arrives and the model badge denominator includes environment instances. Frame button and F key support the selected environment object.
- Node syntax and git diff whitespace checks pass. Browser rendering/interaction has not yet been verified; no full-scene acceptance claimed. Next launch an isolated editor for visual inspection and selection checks, then implement remaining ground/decorations. Original4388 browser/runtime untouched. Full objective active.

### 2026-09-10 — Connect textured environment to scene preview service

- Previous turn was progress: resolved environment meshes/poses. ScenePreviewService now accepts the verified environment catalog, shares repeated geometry, runs prepared prop meshes through the existing server texture adapter, and appends separately identified environment instances with source metadata and full world matrices. The HTTP scene-preview route enables this path.
- World matrices apply source rotation before the single editor Y reflection. Existing actor placement overrides remain independent. Existing geometry/texture/entity budgets apply to the combined scene; environment failures remain explicit in metrics/instance reasons.
- Fresh retail service execution completed in8.608s:52 actors/51 renderable,46 environment/46 renderable,57 shared geometries,9858 unique-geometry triangles and2282409 estimated texture bytes; no environment failures. Private combined preview retained at local-output/sdk-20260909/environment-service/preview.json. Four focused scene-preview tests passed, including a quarter-turn world-transform check.
- Browser rendering and environment hierarchy/inspector selection still unverified/unimplemented respectively. Next complete that UI workflow, then ground/decorations. This service check did not use or restart the original browser/runtime. Full objective active.

### 2026-09-10 — Resolve environment meshes and initial prop poses

- Previous turn was progress: imported46 MAP placements. Added verified environment catalog resolution using the pinned field_env.rs largest scene-entry mesh-pool heuristic, explicitly labeled inferred. Town01 has one scene model carrier: PROT4/section0 with114 meshes; all46 placement indices resolve to existing stable asset IDs.
- Added bounded MAN partition-0 bind-header resolution with alias/section checks. Primary kind-1 trigger order wins and initialization ignores the dispatch gate, matching the reference consumer. Town01 resolves37 header binds and9 unbound static placements;14 placements reference nonzero animation IDs.
- Added EnvironmentPreviewCatalog, verifying animation descriptor boundaries and channel/object counts before applying the existing rigid pose decoder. Executed all46 retail previews:32 unposed static and14 posed,5371 total instance triangles, no decode failures. Five focused tests pass including header truncation and imported-pose/static separation. No browser or live-render parity claim.
- Next connect these geometries, texture adapter and world transforms to ScenePreviewService and synchronized hierarchy/inspector selection; ground/decorations remain separate unfinished layers. Full objective active, original browser/runtime untouched, no proprietary payload staged.

### 2026-09-10 — Prioritize full scene assembly and import environment placements

- Previous conversational status/agenda turns made no implementation progress. Applied the user's Unity-style full-scene priority: inspected current actor-only ScenePreviewService and pinned field_objects.rs, field_env.rs, scene_ty.rs and field_render.rs. Ground, decoration and placed prop layers require distinct consumers; do not call actor meshes a complete scene.
- Added importer/environment.py with verified MAP/MAN loading and deterministic per-cell environment identities, signed XYZ offsets, PSX rotations, placement-cell floor tier and negated MAN height LUT, anchor ownership metadata and exact source hashes. Preserves unresolved pack/animation bindings. The reference's floor_nibble comment says anchor, but executable parser uses the placement cell; implementation and fixture follow the latter explicitly.
- Three focused checks pass including retail town01's46 placements,37 bind-owned anchors and9 remaining placements, house137 at4864/-192/3208 and cave168 tile32/93. Initial synthetic MAN fixtures omitted six section headers; corrected fixtures now pass the existing parser without relaxing validation.
- Not yet a rendered environment: next resolve scene-pack meshes and partition-0 prop poses, add viewport/hierarchy/inspector selection, then tiled ground/decorations. Original browser4388 and runtime sessions untouched. No proprietary payload tracked. Full SDK/stability objective remains active.

### 2026-09-10 — Begin exact animation channel authoring

- Previous turn was progress: reconciled the authoritative patch ledger. Checked current importer/build paths before selecting new feature work: MAN placement has only model/animation/X/Z, and heading remains script-owned/unresolved. Did not invent a heading byte.
- Re-read pinned d6e64c68 player_anm.rs packing/layout evidence. Added importer/animation_authoring.py: source-hash-bound sparse frame/object channel edits, signed12 translation and exact16-step PSX rotations, deterministic audit, duplicate/unknown/range rejection, unchanged header/counts/trailer and opaque nibble. A requested optional Ghidra text path was absent; no new retail disassembly proof is claimed.
- Connected authored_animation_preview to the verified scene animation catalog. It poses effective frames and labels authored hashes/changes separately while preserving imported provenance and caches. This is a serializer and SDK preview foundation; project commands/persistence, editor controls, compressed carrier build integration and gameplay acceptance remain to implement.
- Five new focused checks passed with the retail disc, including exhaustive signed12 wire no-op coverage and unchanged referenced town01 records. Five existing scene-animation checks passed, including all39 imported bindings. No proprietary fixture was tracked, runtime input/restore/restart occurred, or comprehensive test campaign started. Full goal active.

### 2026-09-10 — Reconcile renewed patch inclusion request

- Re-read both renewed attachment prompts and verified clean tracked checkout at ce4a2fe6 on codex/legaia-upstream-20260909. The existing full SDK goal remains active; this request does not narrow it to diagnostics.
- Added a current patch inclusion table to docs/legaia-release-parity.md covering precompile discovery/invalidation, restore ownership, retained release compatibility, host audio, input and DMA diagnostics. Corrected obsolete pending-build/capture language using the later recorded97 build and title-restore evidence, preserving exact binary boundaries and unresolved gameplay cases.
- No runtime source change, new test, runtime input, savestate load or restart in this reconciliation. Muscle Dome, field/cross-scene restoration, current visibility behavior and broader SDK authoring remain unfinished; none is marked fixed merely from a historical prompt.

### 2026-09-10 — Resolve callback trace from saved overlay bytes

- Previous turn was progress: fixed-quad flag consumer distinguished. Attempted to follow node+0C address801D1344 through generated overlays, but same-address candidates contain different instructions (nop or lhu) from checkpoint08's actual lui8008/lwBAF4/prologue. Rejected those candidates as identity evidence rather than attributing the live callback to their named owner.
- Decoded saved RAM directly with tools/disasm_helper.py over801D1344..801D188C; private `arrival-live/player-callback-disassembly.txt` preserves the bounded trace. It saves argument a0 as s2, accesses actor+10, and calls multiple field routines; its final call at801D1854 targets main800172C0. Follow that actual-byte path next. This does not prove a native ownership failure: same-address alternatives are expected and generated-symbol lookup alone cannot establish the selected owner.
- No runtime input, restore, restart or implementation change. Full objective active; existing player remains visible west of the steps.

### 2026-09-10 — Identify a bounded render consumer of actor flag00800000

- Previous turn was progress: collision baseline and west-route recovery. Traced main function8001C394: argument actor+10 flag00800000 selects linked-list insertion at OT base+scaled value-40bytes versus no bias. Compared47 generated instruction comments in8001C508..8001C5C8 against checkpoint08 RAM; all match. Private evidence `arrival-live/actor-flag-ot-branch.json`.
- Crucially this routine constructs fixed GP0 opcode2E/color808080, CLUT7F86, tpage001F quads. Those differ from identified player-model CLUTs7780..7783. This proves a render-path consumer, not that the main player mesh takes this bias or that changing it would fix visibility. Exact primitive role remains unproven; no shadow/model naming assumption promoted to fact.
- No runtime input, restore, restart or code patch. Continue tracing the actual player-mesh path or retail behavior; do not apply a generic OT adjustment from this helper. Full objective active.

### 2026-09-10 — Match retail collision and recover visibility west of steps

- Previous turn was progress: constrained movement checkpoint. Offline slot08 comparison finds zero differing bytes across the16384-byte retail/live collision grid. In tiles23..28 on each axis, only object cell25/26 differs:0800→0C00. Evidence `arrival-live/collision-baseline-comparison.json`. Direct south/east restrictions align with retail wall cells; no collision-paint corruption demonstrated.
- Guarded West90frames moved player3282/96/3246→2562/-64/3246 and restored visibility in inspected west-route.png. Flags changed09820880→09020880, clearing00800000. Subsequent South90 reached2562/-64/3182, still visible (west-south-route.png). Current run remains there; no load/restart/RAM write.
- Visibility is region-dependent and clears on the open west route. This supports terrain/actor-layer handling as the next trace, not a persistent lost-player or general GPU failure. It does not establish retail-emulator parity or prove the occlusion correct. Named transition still unvisited; full objective active.

### 2026-09-10 — Reproduce constrained movement below the steps

- Previous turn was progress:97 title restores. Revalidated preserved96 arrival-live process identity through controller guard, captured visible field-resume.png at player3264/128/3440. Down90frames reached3152/32/3182 with no visible player; Right180frames reached3282/96/3246 and remained invisible in east-clearance.png. Images inspected; surrounding NPC/camera rendering remains present. These displacements are constrained, not unrestricted travel farther across the village.
- Saved fresh slot08 without loading: generation4/pending0/last_ok1. Existing09/10/11 remain available. Evidence and guarded command responses remain in arrival-live/acceptance.json. Current player stays at3282/96/3246; no further input this turn.
- Floor sampler sets actor flag00800000 according to object-cell1000/0800 state; next investigation should connect these flags/collision restrictions to actor rendering rather than infer a generic GPU ordering defect. Exact flag meaning remains unproven. Edited named transition has not been reached; full objective active.

### 2026-09-10 — Repeated title restore on diagnostic rebuild

- Previous turn was progress: separated startup drops from settled-title counters. Fresh isolated97f0f026... SDK run, port4399/PID33520, saved title slot11 and completed three acknowledged loads. Five-second windows advanced303/301/301frames; final screenshot retains intact title/logo/menu. Runtime exited0. Private evidence `local-output/sdk-20260909/dma-title-restore/acceptance.json`, before.png and after.png.
- Across all restore samples audio remained active, underruns0 and cumulative overflow_drops71622 without increase. Final GPU dump contains51 commands with kick PC8005A160. This accepts bounded title restoration and resumed capture, not immediate in-flight DMA attribution, field/cross-scene ownership or subjective audio quality.
- No existing-field-run input, restore or restart. Full SDK objective remains active; next work should return to field rendering/transition evidence rather than repeat settled-title tests.

### 2026-09-10 — Separate startup audio drops from settled-title behavior

- Previous turn was progress:97 cold title/capture acceptance. Traced overflow_drops to rab_push dropping oldest source frames when its ring fills; the counter is cumulative, not an instantaneous continuity indicator.
- Fresh isolated97 run on4399 sampled audio three times after18seconds, spaced5.02seconds. Over10.04seconds drops remained71622 and underruns remained0; fill moved189.2→182.4→178.8ms around180ms target. Host nonzero frames49978→271360→492742. Process41652 exited0. Private evidence `local-output/stability-20260909/dma-audio-live/result.json`.
- This accepts no additional drops/underruns in that bounded settled-title interval, not startup continuity, subjective sound quality, field/XA/FMV audio or a universal audio fix. Startup losses remain unexplained; do not tune the ring from cumulative counters alone. No implementation or existing-field-run changes this turn. Full objective active.

### 2026-09-10 — Cold title and GPU capture on diagnostic rebuild

- Previous turn was progress: full MSVC link. Launched97f0f026... in isolated `local-output/stability-20260909/dma-live`, port4399, separate saves, shipping HLE/software configuration. PID48756 reached the visually inspected title menu; captured51 GP0 commands and exited0 after quit. Private result.json retains identity, packet and audio responses; startup.png retains visual evidence.
- All51 captured command PCs are8005A160. Generated code at that site stores01000401 through the pointer at80078E34, consistent with the linked-list DMA kick; completion func/RA differ and are not builder evidence. This establishes live capture on97, not field visibility or restore acceptance.
- Audio host tap has47742 nonzero frames/peak15822, but overflow_drops71617; no audio-continuity claim. Original field PID50140 was rechecked alive and untouched. New-binary restore/field acceptance and visibility root cause remain outstanding. Full objective active.

### 2026-09-10 — Rebuild complete game with DMA diagnostic fixes

- Previous turn was progress: reset/restore provenance fix. Rebuilt private stability target psx-runtime with MSVC Release, parallel2, using the existing generated main/static-overlay sources; command exited0 and staged mod catalog verification passed. Existing compiler deprecation/synthetic-recursion warnings remain. Log: `local-output/stability-20260909/build-dma-provenance.log`.
- New executable SHA25697f0f0260f7d4c977a385e0dcd3b5f625c7112f9eefd04bcfeab1684998fd4aa, built from688c58cb. Private `dma-provenance-build.json` records source hashes. Verified PID50140 remains live at its separate arrival-live run path and that preserved executable still hashes96eaf949050d28009958cbc4f5d305c06976ac7e1eefbd7d62eaa6cb97993203.
- Full generated-game link is accepted; new-binary startup/capture/restore behavior is not yet live-validated. No game restart or input this turn. Existing visibility evidence belongs to96, not97. Full objective remains active.

### 2026-09-10 — Invalidate DMA diagnostic provenance across restore

- Previous turn was progress: GPU DMA ring PC correction. Lifecycle review found per-channel kick PCs and execution-scope metadata were neither serialized nor cleared by dma_init/dma_snapshot_read. They could therefore falsely attribute a restored transfer to the pre-restore run.
- Added shared provenance reset on DMA initialization and successful snapshot read, after validation/deserialization and before GPU linked-list context reconstruction. Snapshot wire format and emulated channel state are unchanged. Invalid input does not clear current provenance.
- New focused C harness invokes actual dma.c initialization and snapshot routines: reset, truncated-input rejection, idle restore and active linked-list restore all pass. Active restore preserves transfer/rank and invokes existing end/begin/prepass/rank callbacks. Registered the harness for GNU CTest builds using whole-program elimination to avoid unrelated device stubs; compiled/executed directly with GCC. Initial link without elimination failed on unrelated device dependencies; corrected build passed. MSVC harness/full runtime rebuild not claimed. Private live game unchanged; full objective active.

### 2026-09-10 — Correct asynchronous GPU diagnostic PC attribution

- Previous turn was progress: ramp-filter browser acceptance. Followed captured RA801D1064 to the generated field call of80036888; checkpoint10 instruction words at801D1048/105C/1060 and80036C18 match the inspected generated sites. The recorded PC80036C18 writes zero to RAM800740E8, not the GPU. Thus this captured CPU context cannot identify the terrain packet builder.
- GPU ring previously always copied g_debug_last_store_pc, including asynchronous DMA completion. It now uses the channel2 kick PC already preserved and republished by dma.c while the DMA execution scope is active. Unknown kick remains zero. Direct CPU submission retains its CPU-store PC; header comments explicitly distinguish completion-time func/RA from a packet builder.
- Compiled and executed the existing GPU C harness extended with actual-ring checks for deferred kick attribution, unknown kick, stale channel outside DMA and other-channel scope. PASS, including existing textured-dot checks. GCC needed its UCRT bin directory on PATH; initial compiler invocations exited1 without diagnostics, corrected invocation succeeded. No full game rebuild, runtime mutation or new live acceptance this turn. Visibility root cause remains unresolved; full objective active.

### 2026-09-10 — Verify and filter the ramp inspector

- Previous turn was progress: ramp metadata and inspector implemented. Fresh private editor4395/tab51 displayed235 retail town01 ramp rows. Added a token filter matching table, record index or tile coordinates, with matching/total count and an explicit empty state; preserved source order.
- Browser verified query `25 26` returns primary227/tile25,26/coarse-4/delta128, query201 returns tile25,25/coarse-3/delta96, and unmatched input returns zero records. Inspected screenshots before and after correcting search-field spacing; final table and notes fit the dialog. Node syntax check passed. Private verification project is under `local-output/sdk-20260909/ramp-browser`.
- No game runtime input, RAM writes, restore or restart. Original editor tab8 untouched. Visibility root cause and full SDK objective remain active.

### 2026-09-10 — Expose source ramp adjustments in the collision inspector

- Previous turn was progress: saved floor heights matched kind-2 ramp records. Converted that evidence into an SDK feature: field-map catalog now retains primary/fallback kind-2 records on the collision resource, signed coarse steps, four ordered subcell Y adjustments and per-record provenance. Duplicate coordinates and lookup order are preserved. Existing asset identities and trigger counts are unchanged.
- Collision inspector adds a read-only ramp table and explains the object-cell0800 condition, corner-mean dependency, subcell ordering and positive-down Y. This is relative adjustment metadata, not a complete terrain mesh or live floor sampler.
- Six focused field-map tests passed with LEGAIA_DISC_BIN supplied, including retail town01 matching the two visibility tiles and synthetic signed extremes/subcell order/duplicate precedence; Node syntax check passed. New table has not yet been browser-verified. No runtime input, mutation or restart. Terrain geometry/ordering root cause remains unresolved; full objective active.

### 2026-09-10 — Verify player floor height against saved ramp records

- Traced generated main routine `80019278`: scratchpad `1F8003EC` supplies the field map base, `1F80035C` the signed height LUT, map+4000 the corner tiers, and map+8000 the object-cell flags. The `0800` branch calls `801D5630(2,tile_x,tile_z)` and uses the corner mean minus signed coarse*32 minus packed subcell*16. This agrees with pinned Andrew `world/field_movement.rs` and `world/field_elevation.rs`; generated instructions inspected, not yet a new full retail-byte comparison.
- Read saved states09/10/11 offline without loading or writing runtime RAM. All three use map base80139530, zero corner tiers and the ramp flag. Primary kind-2 records at80149992/8014992A/8014967A respectively have coarse -4/-3/1 and zero subcell steps, reproducing observed Y128/96/-32 exactly. Private evidence: `local-output/sdk-20260909/arrival-live/floor-height-comparison.json`, with state hashes and record addresses.
- This excludes a missing-ramp calculation as the simple explanation of these samples; it does not prove terrain geometry, camera transforms or ordering are correct. No speculative runtime patch, savestate restore, process restart or gameplay input this turn. Follow terrain geometry/ordering construction next. Full SDK and release-parity objective remains active.

### 2026-09-10 — Compare terrain submission placement across visibility views

- Previous turn was progress: opaque terrain sample. GPU comparison shows identified player packets581..707/traversal ranks1708..1716 in invisible frame;565..681/ranks1701..1709 in visible near-step frame. Matching terrain texture quad occurs later in both, but moves from rawY108..138 to143..178; therefore changing screen overlap, not disappearance of player submission, distinguishes these captures. Evidence `arrival-live/ordering-comparison.json`.
- Verified gpu_set_gp0_linked_list_node increments diagnostic OT rank only for zero-word linked-list nodes. These rank numbers are traversal order, not direct geometric depth and must not be used as Z evidence.
- Existing gpu_frame_layers rasterizes geometry but intentionally does not sample textures, so it cannot prove exact opaque coverage by itself. Next work should trace terrain geometry/height or retail OT construction; no unsupported sorting patch made. Full objective active; private runtime unchanged this turn.


### 2026-09-10 — Sample opaque terrain overdraw candidate

- Previous turn was progress: player packet identification. Parsed private checkpoint10 VRAM and sampled candidate GP0 quad772 (page0C/CLUT7D00) at raw polygon pixels155/117,154/116,156/118. Barycentric UVs and all four floor/ceil neighboring texels produce nonzero15-bit colors, supporting opaque coverage rather than transparent holes. Evidence `arrival-live/overdraw-texture-samples.json`.
- Captured frame setup before candidate: E2zero texture window, E6zero mask, E5offset(0,4). VRAM and GP0 timestamps differ, so this is not an exact raster replay. No texture/transparency bug demonstrated; ordering/terrain height remains the next question.
- No runtime mutation, restart or renderer patch. Full objective active; edited arrival still not reached.


### 2026-09-10 — Identify submitted player geometry and overdraw candidate

- Previous turn was progress: same-view GPU pair. Parsed checkpoint09 player+44 model table800C9568 into10 bounded object records; every decoded primitive count matches its declared count (132,90,16,18,18,16,16,29,16,29). Textured groups use CLUT7780/7783/7781/7782, confirming the previously candidate GPU groups belong to player geometry. Evidence `arrival-live/player-model-cluts.json`.
- Invisible frame57910 contains player packets581..707. Later textured quad772 (op2C, OTrank1754, source0009E750) spans (172,138),(126,137),(186,108),(119,110), overlapping player screen region. Captured exact packet in player-overdraw-candidate.json. Submission exists; texture coverage/raster depth/order cause remains unverified. No blanket ordering or terrain hack applied.
- Same runtime remains available; no state load or RAM write. Next useful step is exact quad texture/raster coverage or retail renderer ordering comparison. Full objective active.


### 2026-09-10 — Capture GPU frames across same-view visibility change

- Previous turn was progress: offline player-record comparison. Same runtime produced invisible-frame GPU dump57910 with915commands. Initial newest-1 sample had0commands; newest-2 captured a rendered frame. North20 then made Vahn visible within the same village camera view; captured frame59344 with910commands. Screenshots and bounded GP0/GTE captures retained as invisible-render-2/near-step-render under arrival-live.
- Compared textured-polygon CLUT groups and raw XY bounds. Small groups7780..7783 exist near expected player location in both frames; identity is not yet mapped to Vahn's model, and draw offsets/order matter. No missing-submission conclusion or renderer fix justified yet. Candidate ordering/occlusion investigation remains open.
- Saved visible same-view checkpoint9 for a closer pair with invisible checkpoint10, with completion receipt in acceptance.json. No loads or RAM writes. Same runtime50140/editor48160/session45118 remains live at visible near-step position. Full objective active.


### 2026-09-10 — Inspect saved visibility states without loading

- Previous turn was progress: paired private checkpoints. Parsed version7 PST header/section wire and zlib RAM sections offline, checking declared lengths and complete file consumption; no live-state restore or RAM write. Checkpoints share player pointer80083794 and flags09820880, and unchanged model-related words in the bounded156-byte record. Changed words include XYZ/duplicate XYZ, heading, offsets2C/30/34,68 and98.
- Checkpoint11 SHA bf83862f822d8614deddd2abfb806285fe6840bf5774e81b2e6fad707913e077; checkpoint10 SHA7ae3ceb37682b3e8db7613dabe383e644293073b84b037af9ee372691f19639d. Evidence `arrival-live/checkpoint-player-comparison.json`.
- These checkpoints span a local camera transition; unidentified offsets2C/30/34 must not be assumed screen coordinates. No flag/model-pointer corruption demonstrated, no root cause established. Same live runtime responded to identity-guarded player read. Next useful isolation is matching visible/invisible samples within the same view or renderer submission tracing. Full objective active.


### 2026-09-10 — Narrow and checkpoint field visibility reproduction

- Previous turn was progress: live visibility issue captured. North90 restored visible Vahn through local camera transition (north-check-2.png). Diagonal90 returned to village steps visibly; subsequent Down30 made Vahn disappear (short-south.png), with player XYZ3264/128/3520 ->3264/96/3280. NPC/camera behavior and identity checks remain responsive. This narrows a location-dependent reproduction without identifying root cause.
- Created private save checkpoint11 at visible approach (generation1 last_ok1) and checkpoint10 after disappearance (generation2 last_ok1). No loads performed; cold run provenance intact. An initial slot12 request was rejected because valid slots are0..11; no state saved by that rejected request.
- Same runtime50140/editor48160/session45118 remains live; controller supports checkpoint slot and checkpoint-status. Checkpoints are confined to private run20260910T213334Z-15f81d42. Next: diagnose/compare paired states before further exit traversal. Full objective active; no runtime fix or arrival acceptance claimed.


### 2026-09-10 — Field traversal reveals player visibility issue

- Previous turn was progress: guarded cold field reached. Continued same runtime50140/editor48160/session45118, moved south from Genesis Tree through step/camera view. Vahn was visible on steps, then absent in subsequent ground view while NPCs and camera continued responding. East input changed player record; repeated south movement made unclear progress. No exit transition claimed.
- Read-only pointer8007C364 resolves player80083794. Captured record samples changed XYZ3154/32/3182 ->3282/96/3246 after east input; flags09820880 retained. These observations do not yet identify the cause (terrain/visibility/camera/movement). Controller overrides released normally; guarded town01 actor observation remained available.
- Evidence screenshots south-1..6/east-1..2 and samples in arrival-live/acceptance.json. Runtime intentionally remains running for bounded reproduction/diagnosis; no RAM writes or restart. Authored exit script has not executed; do not attribute this issue to the entry patch without baseline comparison. Full objective active.


### 2026-09-10 — Cold town01 field reached with authored arrival package

- Previous turn was progress: owned runtime launched and New Game begun. Continued same runtimePID50140/editorPID48160 (session45118), identity-checked screenshots showed story progression. Completed naming via Start/Up/Cross, elder dialogue and Yes choice, then reached field control (elder-9.png). No savestate or RAM writes used.
- Guarded v2 attach and actor observation succeeded at frame25992; evidence `arrival-live/field-observation.json`. Runtime consumed one enabled MAN overlay (13sector applications/24894cumulative bytes), disc guard false. This establishes cold field loading on binary96eaf949..., not exit arrival acceptance.
- Added identity-guarded read-only arrival-global capture to private controller. Runtime remains live at town01 field control for exit traversal; no restart needed. Full objective active.


### 2026-09-10 — Start cold arrival runtime acceptance

- Previous turn was progress: composed package exactness. Prepared private arrival-live Project with town01 P2[0] X12416 and package SHA c58bd9410562a079bd89dcd2d1e87ba0e6835556abd0edffccc9429e3c07262c. Launched latest rebuilt executable96eaf949050d28009958cbc4f5d305c06976ac7e1eefbd7d62eaa6cb97993203 through EditorServer4396/runtime4397.
- Owned editor PID48160/tool session45118, runtime PID50140; run directory20260910T213334Z-15f81d42. Identity, BIOS, disc and one-overlay plan verified. First screenshot returned display disabled during startup; recheck of same live process reached title. Cross8 entered cold New Game story; startup-2.png/new-game.png inspected. No savestate loaded.
- Runtime/editor intentionally remain running for continuation of live arrival acceptance. Use arrival-live/control.py ready/capture/press and verify process identity as built into helper; do not restart merely on timeout. Current stage cold_new_game_story. Acceptance not complete; full objective active.


### 2026-09-10 — Verify composed transition and dialogue package

- Previous turn was progress: browser draft conflict fix. Fresh private town01 Project authored P2[0] arrival X12416/facing2 plus one P2[36] dialogue glyph, saved/reopened, then built. Decoded MAN exactly matched independently composed patches: three audited fields and exactly three changed bytes. Clear of both components reproduced the baseline package SHA.
- Package SHA13e4b54628d8fc55567eb0b7176d9273d83325bf228bfba42a470283709fda0b; evidence `local-output/sdk-20260909/transition-dialogue-composition/verification.json`. Updated feature matrix with the implemented transition workflow and its remaining limitations.
- No runtime launched; live arrival, world-map route coverage and full SDK requirements remain incomplete. Full objective active.


### 2026-09-10 — Prevent competing transition drafts

- Previous turn was progress: browser arrival authoring. Fixed two forms for the same entry allowing conflicting drafts to survive a refresh and later overwrite each other. An arrival draft now disables byte inputs/Apply/Clear; a byte draft disables arrival inputs/Apply. Explanatory tooltips and Discard remain available.
- Private tab50/editor4395 verified both directions: arrival12352->12416 locked byte form; Discard restored access; byte96->97 locked arrival form; final Discard restored baseline. Browser errors empty; JavaScript syntax passed. No authored command or runtime launched. QA root `local-output/sdk-20260909/arrival-draft-browser`.
- Full objective active; live transition arrival acceptance still pending.


### 2026-09-10 — Arrival coordinate controls verified in browser

- Previous turn was progress: verified arrival command. Added Arrival X/Z and facing-sector inspector form, exact-grid HTML validation, draft/discard handling and shared project action guards. Existing encoded-byte controls remain available.
- Private browser tab49/editor4395: town01 P2[0] X12352 ArrowUp ->12416; Apply arrival produced encoded X224 (from96), preserved Z25/direction4 and refreshed preview. Clear restored encoded96 and coordinate12352. Browser errors empty; JavaScript syntax passed. QA root `local-output/sdk-20260909/arrival-browser`; no runtime launched.
- Facing/draft invalid-input browser paths and live arrival acceptance remain unverified. Full objective active.


### 2026-09-10 — Author exact arrival coordinates through project commands

- Previous turn was progress: retail handler arithmetic matched. Added set_transition_arrival command accepting exact X/Z grid values and facing_sector0..7, translated through the same persisted encoded-entry component/build path. Facing changes preserve upper5 direction bits; omitted fields retain effective source values. Source membership is verified before command mutation.
- Six serializer tests passed, including exhaustive256-byte coordinate roundtrip and invalid-grid/sector rejection. Retail HTTP lifecycle passed (8.133 s): arrival X128 encodes128, facing sector2 previews1024, Undo restores the baseline, and existing byte edit/redo/clear flow still works.
- Arrival-coordinate UI controls and live scene arrival remain pending; no runtime launched. Full objective active.


### 2026-09-10 — Match arrival arithmetic to retail overlay

- Previous turn was progress: generated-handler trace. Hashed-disc probe found one matching instruction window among the ten retained static roles: PROT897 offset66312, entry SHA216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b. All36 words at generated801DEB20..801DEBAC match the expected retail window, including BEQ delay slots, low7 coordinate extraction, high-bit adjustment, direction&7 and table lookup. Evidence: `local-output/sdk-20260909/transition-handler-retail.json`.
- Together with prior direct executable table evidence this supports static coordinate/facing interpretation. Added effective arrival preview data and inspector text; runtime_verified remains false. No runtime launched. Destination height and live arrival behavior remain unverified; full objective active.


### 2026-09-10 — Trace generated arrival handler operations

- Previous turn was progress: direct retail facing table. Located generated overlay function ov_001CE818_7717AFDB_7D82C23B_func_801DE840 in sibling generated/overlays_static_0000.c (read only). Named path copies length-prefixed destination; 801DEB20..7C extracts low7 X/Z, shifts7, adds64 and substitutes128 on high-bit branches, storing globals80073EF4/80073EF8. 801DEB8C..AC loads trailing direction, masks7, indexes signed-half table80073F04 and stores80073EFC.
- Private evidence with generated-file SHA and bounded excerpt: `local-output/sdk-20260909/transition-handler-generated.json`. This agrees with pinned reference semantics and the independently observed retail table, but generated instruction words have not yet been matched to the retail overlay payload. No retail parity or live behavior claim added.
- Next: match named-path instruction window to hashed retail overlay before promoting coordinate semantics. Full objective active; no runtime launched.


### 2026-09-10 — Verify retail arrival-facing table

- Previous turn was progress: pinned reference interpretation. Independently read supported retail SCUS_942.54 through the hashed disc context, verified PS-X EXE header/load span, and resolved virtual80073F04 to file offset411396. Eight little-endian signed entries are0,512,1024,1536,2048,2560,3072,3584, exactly matching the pinned reference table.
- Disc SHA e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c; executable SHA292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482. Private evidence: `local-output/sdk-20260909/transition-facing-table.json`.
- This is direct static table evidence only. Retail transition-handler indexing, coordinate arithmetic, arrival globals and live scene execution remain unverified. No runtime launched or disc modified. Next source step is the retail FUN801DE840 opcode3F handler; full objective active.


### 2026-09-10 — Trace reference arrival coordinate semantics

- Previous turn was progress: authored graph layers. Read pinned d6e64c68 engine-core world/vm_hosts.rs:815, scene/host/scene_entry.rs:1492 and world/field_loop.rs:275-308. Named transition queues bytes, loads destination, then seats/faces player. Actual seat implementation uses low7*128 plus64/128 selected by bit7; facing is (dir&7)*512. Nearby e2e test prose uses a simpler tile formula, so it is insufficient for high-bit evidence.
- Added labelled pinned-reference interpretation to transition options with runtime_verified=false and source path; no new world-coordinate write mode or runtime claim. Boundary test covers0/127/128/255 and direction255.
- Retail FUN_801DE840/table80073F04 parity and live arrival acceptance remain pending. Full objective active.


### 2026-09-10 — Show authored entry layers in scene graph

- Previous turn was progress: shared descriptor guards. Scene-transition graph now carries separate imported/authored/effective entry layers and stable transition IDs; the editor displays authored effective bytes alongside imported provenance. Build revalidation remains explicit; graph reachability stays not evaluated.
- Three focused graph tests passed, including partial override inheritance and protection of original catalog/project data. JavaScript syntax check passed. Browser layer display and live gameplay remain unverified; full objective active.


### 2026-09-10 — Guard shared script authoring descriptor ownership

- Previous turn was progress: transition report navigation. Shared dialogue/transition MAN loader now rejects active descriptor aliases at the selected stream offset and enforces its 4 MiB bound before decompression, matching source ownership expectations of authored byte edits.
- Nine importer dialogue-authoring tests passed with retail enabled. New malformed-descriptor test proves alias/oversize rejection occurs before decoder invocation. Retail scene authoring remains accepted.
- No runtime launched. Browser report navigation and live transition behavior remain pending; full objective remains active.


### 2026-09-10 — Navigate build changes to transition entry fields

- Previous turn was progress: browser Apply/Clear and recovery controls. Fixed build-report navigation so P1 transition changes open script inspection and P2 links focus the exact transition entry field. Transition fields now expose a stable focus target; source navigation scrolls it into view. Renamed authored script action to Open script workspace.
- JavaScript syntax and transition merge test passed. Added report identity check for transition resource ID, owner, encoded before/after and scope. Browser report-link click remains unverified; no runtime launched. Full objective active.


### 2026-09-10 — Browser transition editing and recovery controls

- Previous turn was progress: isolated source-error handling. Added clear controls for unresolved transition IDs and responsive entry form styling; corrected the scene graph's obsolete no-edit-support note.
- Private browser tab 48 / editor 4395: Scene transitions -> Inspect source script -> town01 P2[0] at 0x16. ArrowUp changed X96 to97; Apply retained97 after refresh; Clear restored96 and disabled Clear. Z25/direction4 retained. Browser errors empty; screenshot inspected with all entry controls legible and within dialog width.
- QA root: `local-output/sdk-20260909/transition-browser`. No runtime launched; user's editor untouched. Unresolved recovery button itself and live gameplay remain unverified. Full goal remains active.


### 2026-09-10 — Isolate unavailable transition authoring

- Previous turn was progress: inspector controls and HTTP lifecycle. Added a bounded unavailable transition response so alias/source authoring errors no longer replace valid dialogue data or suppress read-only script inspection. Stored transition IDs remain in the response for recovery.
- Updated the legacy P2 HTTP flag-count assertion from 1123 to the current 1183, reflecting already-evidenced decoder expansion. The full retail P2 dialogue HTTP test then passed (11.190 s), including trigger edits, refresh, clear and rejected requests. Two transition project tests passed, including unavailable-report source failure handling.
- Browser transition controls, unresolved-override recovery controls and live gameplay transition acceptance remain pending. No runtime launched; full objective remains active.


### 2026-09-10 — Transition inspector controls and HTTP lifecycle

- Previous turn was progress: exact retail package and clear-baseline verification. Added transition authoring data to script responses, strict command HTTP keys, and inspector byte inputs with Apply/Clear/Discard, imported values and shared draft/history guards.
- JavaScript syntax check passed. Focused retail HTTP lifecycle passed: inspect, apply, effective refresh, undo, redo, clear and rejection of client source offsets. No runtime launched.
- Existing P2 dialogue HTTP test failed before reaching edit assertions because its flag total expects 1123; current catalog has 1183 after prior decoder expansions. Preserved that failure for later coverage maintenance; no broad regression pass claimed.
- Browser layout/interaction validation remains pending, as does live transition gameplay acceptance. Full goal remains active.


### 2026-09-10 — Package encoded transition entry overrides

- Previous turn was progress: persistent transition commands committed. Build now accepts validated P1/P2 Transitions, rechecks source membership, merges exact byte audits with header/dialogue edits, and preserves the existing compressed-capacity and round-trip guards. Reports retain transition resource IDs and package descriptions identify the new scope.
- Private town01 P2[0] package decoded exactly to the expected one-byte MAN patch; clearing restored the exact baseline package hash. Evidence: `local-output/sdk-20260909/transition-build/verification.json`. Initial probe used Path instead of the project's string disc_path contract; corrected probe passed.
- Focused merge test covers full-span dialogue overlap, single-byte overlap, owner mismatch and unaudited changes; existing dialogue build tests passed (3 passed, 2 retail opt-ins skipped). No runtime launched. Editor controls and live transition acceptance remain pending; full goal active.


### 2026-09-10 — Persist authored transition entries

- Previous goal turn classified as progress: committed verified transition context and a retail source-span probe.
- Added Transitions component commands for set/clear, fresh source validation before mutation, bounded encoded-byte syntax, undo/redo, offline persistence and authored asset summaries for P1/P2 owners. Source failure leaves project state unchanged.
- Validation: transition project lifecycle test passed; existing dialogue project tests 3/3 passed. No retail runtime or build executed this turn.
- Next: connect transition audits to Build MAN composition and expose editor controls. Build still rejects Transitions explicitly through its component whitelist; no authored entry is silently packaged or ignored. Full objective remains active.


### 2026-09-10 — Verified transition MAN context

- Added a request-scoped transition authoring context around the bounded entry-byte serializer, with stable owner/PC IDs, exact optional baseline guards, unique source-record checks, deterministic audited byte composition and overlap rejection. Shared MAN record access reuses the existing P1/P2 ownership validation without requiring editable dialogue.
- Focused validation: transition tests 4/4 passed; dialogue tests 7 passed with 1 opt-in retail test skipped. A separate private retail loader probe resolved town01 P2[0] transition PC 0x16 and changed exactly one audited byte; evidence: `local-output/sdk-20260909/transition-context-probe.json`.
- No runtime launched or package built for this change. Transition project commands, editor controls and playable packaging remain unconnected. The full SDK/recomp goal remains active, including broader gameplay acceptance and unresolved source semantics.


- **2026-09-10 (transition serializer foundation):** Previous cold appearance
  revert was progress. Verified pinned3F entry layout and added bounded
  record-level entry X/Z/direction byte serializer with source audit. Two tests
  pass; private town01 P2[0] probe changes exactly one byte at unchanged length.
  No world-coordinate interpretation, destination relocation, project command
  or build integration yet. Next work is verified MAN-context/project integration.
  Full SDK goal remains active.


- **2026-09-10 (cold appearance revert accepted):** Previous baseline preparation
  was progress. Matched2be69467... cold launch traversed attract FMV, returned
  title, then story/name/elder to field control. Original child visible; prior
  donor screenshot compared. Guarded v2 capture90nodes and actor0049 imported+
  effective candidate retained (binding unconfirmed). Zero writes/overlays/bytes,
  guard false. Owned runtime29164/editor35424 both exited0. Private acceptance
  updated; no save load or new-binary acceptance. One donor-pair revert accepted;
  full SDK goal remains active.


- **2026-09-10 (appearance revert preparation):** Previous rebuilt title restore
  was progress. Recovered prior appearance input sequence and exact2be69467...
  executable. Prepared private appearance-revert-live project through actual
  set/clear donor commands, save and fresh retail build: zero changes/overlays,
  package969e649b.... Launch configuration uses the prior appearance-tested
  binary for a matched comparison. Runtime not launched; cold revert remains
  pending. Prior appearance evidence/project retained unchanged. Full goal active.


- **2026-09-10 (rebuilt-binary restore check):** Previous path search was
  progress. Exact96eaf949... private baseline completed three title restores;
  five-second windows advanced300/303/302 frames. Host active, underruns0,
  cumulative overflow71739 unchanged. Final screenshot full title menu; owned
  runtime exit0. Private protocol evidence retained. Field/cross-scene/input
  restore acceptance remains separate; full SDK goal active.


- **2026-09-10 (decoded-path search):** Previous precompile consumer audit was
  progress. Added local bounded-query search to shared script paths, retaining
  all graph rows and Back history. Browser4395/tab47 found seven actor0001
  pickers, advanced/reversed exact PCs and disabled controls for no matches
  without clearing selection. Errors empty; Node syntax passes. Owned QA server
  stopped via sentinel. No source edits or runtime behavior implied; full goal active.


- **2026-09-10 (static-output consumer audit):** Previous dialogue navigation
  was progress. Checked remaining filename consumers; production paths use the
  corrected helpers. Existing static split/CRC dispatch suite passes all10 tests
  with GCC (0.204s); initial direct run skipped compiler coverage. Test-only
  ResourceWarnings remain, no production failure found. No retail acceptance
  extension or new runtime patch. Full SDK goal remains active.


- **2026-09-10 (menu successor browser and dialogue navigation):** Previous
  conflict diagnostics were progress. Owned editor4395/tab46 verified choice1
  0x6B ->0xC4 and Back. Found decoded dialogue targets falsely labeled not decoded;
  merged dialogue nodes into shared path navigation using verified lengths/text.
  Reload verified choice0 ->0xD6 dialogue and Back; errors empty, Node syntax
  passes. Server stopped via owned sentinel. No runtime execution or authoring
  guard change; full SDK goal remains active.


- **2026-09-10 (P2 menu conflict provenance):** Previous menu traversal was
  progress. Traced P2[20] conflict to camera0x551 targeting0x44 inside emitter
  0x3D/14bytes. Pinned camera executor agrees with absolute target; retail
  semantics remain unresolved. Improved conflict stops with owner_pc and
  readable ownership offset. Six focused and23 retail inspection tests pass.
  Private trace retained; no guessed branch adjustment or guard relaxation.
  Full SDK goal remains active.


- **2026-09-10 (menu choice graph traversal):** Previous flag indexing was
  progress. Followed proved per-choice targets without a guessed fallthrough;
  pager remains unresolved. Same-run prior-decoder comparison isolates113 added
  and17 withdrawn dialogue IDs (P2[20] conflict), net522 dialogues/613 assets/
  1183 flags. Synthetic opaque-skip/conflict checks and44 targeted tests pass.
  Authoring guards remain unchanged; choice-link browser acceptance pending.
  Full SDK goal remains active.


- **2026-09-10 (flag-word catalog integration):** Previous menu-link browser
  acceptance was progress. Found decoded FLAG_WORD_BRANCH absent from flag
  catalog; pinned host confirms bank mapping. Added metadata references with
  masked index, retained width uncertainty and unknown live value. Isolated11
  new town01 references (1145 total) before updating expected count. Seven
  retail-enabled tests pass; source-PC browser checks remain pending. Full goal active.


- **2026-09-10 (menu catalog browser path):** Previous catalog integration was
  progress. Fresh isolated editor4395/tab45 refreshed town01 resources, searched
  Scripts0001, opened actor metadata and followed its four-option menu link.
  Verified source report selected DIALOGUE_PICKER0x6B with options and read-only
  warning intact. Browser errors empty; owned server stopped via sentinel. P2
  link/browser path and runtime execution remain separate. Full SDK goal active.


- **2026-09-10 (menu catalog integration):** Previous masked-control work was
  progress. Added metadata-only menu counts/spans/hashes to script assets and
  exact-PC source-inspection links in resource details, with old-catalog refresh
  handling. Labels remain private. Six retail-enabled catalog tests and JS
  syntax pass; navigation browser acceptance remains pending. No menu authoring
  or execution claim; full SDK goal remains active.


- **2026-09-10 (masked menu controls):** Previous browser correction was
  progress. Implemented pinned high-bit MES picker semantics: A7/A8/A9 do not
  consume an actor-target byte; masked continuation controls retain one-byte
  width. Raw bytes and entry-relative targets remain exact. Five focused,
  twenty-three retail inspection and five retail catalog tests pass. No menu
  execution or authoring claim; full SDK goal remains active.


- **2026-09-10 (menu browser acceptance and repair):** Previous menu decoder was
  progress. Isolated editor4395/tab44 opened real actor0001 picker0x6B with four
  options and correct read-only warning. Screenshot exposed oversized expanded
  raw operands; collapsed menu details by default, reloaded and visually verified
  all choices fit in the selected row. Browser errors empty; Node syntax passes.
  Private picker-browser server stopped via owned sentinel; no runtime launched.
  Full SDK goal remains active.


- **2026-09-10 (dialogue option menus):** Previous new-binary startup was
  progress. Located pinned MES picker evidence for27/28/29 and implemented
  structurally bounded read-only menu tables/labels with entry-relative signed
  targets. Shared script UI lists options; pager continuation stays unresolved.
  Retail actor0001 PC107 exposes four options and remains non-writable. All32
  targeted tests and JS syntax pass; catalog totals unchanged. Browser layout
  and menu runtime execution remain unaccepted. Full SDK goal remains active.


- **2026-09-10 (new executable cold start):** Previous actual build was progress.
  Fresh private baseline launch of96eaf949... verified readiness/process identity,
  rendered full title menu and advanced301 frames over five seconds. Active
  host nonzero PCM increased with zero added underrun/overflow; startup71153
  drops retained. MDEC/CD-in stayed0. Owned runtime exited0; private acceptance
  and inspected screenshot retained. No FMV/field/restore claim for this binary.
  Full SDK goal remains active.


- **2026-09-10 (actual Legaia precompile build):** Previous generator acceptance
  was progress. Inspected private CMake configuration, preserved61d99eac...,
  rebuilt actual psx-runtime Release with existing sibling generated inputs and
  current staging helper: exit0. New executable96eaf949... has build-only
  acceptance; prior live results remain bound to the preserved binary. Private
  build log and hash manifest retained. No gameplay run or sibling regeneration
  was performed. Full SDK goal remains active.


- **2026-09-10 (Windows discovery-fix acceptance):** Previous filename fix was
  progress. Verified clean tracked state and ran both static-overlay tests on
  Visual Studio18/MSVC (14.670s) and NMake/GCC (27.045s), each exit0. Both cover
  all nine executable inventory transitions and sparse high-index/neighbor
  discovery checks. GNU Make and retail runtime acceptance remain separate.
  No production changes this turn; full SDK goal remains active.


- **2026-09-10 (precompile filename agreement fix):** Previous empty-inventory
  acceptance was progress. Found producer indices beyond9999 were omitted by
  discovery and cleanup could include backup-name neighbors. Updated Python and
  CMake to recognize exact numeric suffixes of four or more digits. Sparse
  high-index staging/cleanup and nine executable Ninja/GCC variants pass (two
  tests,6.909s). No arbitrary inventory limit, runtime policy or retail payload
  changed. Full SDK goal remains active.


- **2026-09-10 (empty precompile inventory):** Previous dialogue integrity
  regression was progress. Inspected stale split-output cleanup and extended
  the executable build fixture through four-to-zero-to-two overlays, asserting
  exact source inventory alongside execution. Nine Ninja/GCC variants pass in
  6.627s after approved retry of a sandbox-denied Ninja startup. Existing cleanup
  handles the transition; no runtime patch was justified. Other generators have
  not run the two added cases. Full SDK goal remains active.


- **2026-09-10 (extended-context dialogue safety):** Previous editor operand
  presentation was progress. Audited source-span authoring against unresolved
  extended targets: runtime identity is not required to replace an independently
  bounded glyph span. Added immediate/timed extended-position regression proving
  all non-glyph bytes and decoded instructions remain identical after an actual
  patch. Eight authoring tests pass with retail input enabled. No new restriction
  or runtime fix was justified; gameplay and broad SDK completion remain open.


- **2026-09-10 (script position presentation):** Previous decoder implementation
  was progress. Connected position operands to the shared actor/trigger script
  table: immediate unchanged axes, timed encoded ticks, unresolved runtime
  position and extended target context are explicit. Original encoded operands
  remain available; other instructions retain expanded values. Node syntax and
  focused DOM behavior checks passed for sentinel scope, target warning and raw
  preservation. Both production call sites use the shared renderer. Browser
  layout and gameplay were not tested in this turn. Full SDK goal remains active.


- **2026-09-10 (scripted position inspection):** Previous acceptance-summary
  correction was progress. Investigated actual halt-acquire blocker; pinned
  target-read/fallthrough overlap remains unresolved and unsupported. Added
  evidenced ACTOR_CTRL sub9 inspection with unsigned XYZ/ticks, immediate-only
  unchanged-axis sentinels and explicit unevaluated host tween. Three focused
  tests and five retail-enabled catalog tests pass; catalog counts unchanged.
  No authoring guard relaxed or runtime behavior changed. Full SDK goal active.


- **2026-09-10 (acceptance summary reconciliation):** Verified previous commit
  4143ed40 and clean tracked state. Reconciled feature matrix and leading release
  parity summary with recorded NMake, bounded title/story restore, donor appearance
  gameplay and latest script-catalog evidence. Removed obsolete counts and broad
  unverified claims without extending acceptance to field/cross-scene restore,
  appearance revert, GNU Make or partial-graph dialogue writing. Documentation
  only; no new game run or runtime patch. Full SDK goal remains active.

- **2026-09-10 (new dialogue authoring boundary):** Previous flag-word decoding
  was progress. Checked new P2[4] dialogue against the real authoring service;
  it exposes no writable runs because PC5 targets outside the record and PC483
  stops at unsupported0x27. Initial expected-run assertion failed; corrected
  investigation identified the guard. Actual set_dialogue_text rejected with
  exact project-state digest unchanged. No build attempted or guard relaxed.
  Private flag-branch-dialogue-build/rejection.json retained. Newly exposed
  dialogue remains read-only; full SDK goal active.


- **2026-09-10 (flag-word branch decoding):** Previous retail check was progress.
  Inventoried actual scene stops, then used pinned executing nibble_9_a/host
  evidence to decode A0/A1/A2 fixed-width signed-target branches. Both outcomes
  remain unevaluated; negative targets stay invalid. Prior-decoder comparison
  isolates five new P2[4] dialogue IDs. Town01 now426 dialogue/517 assets/1134
  flag refs,91 scripts/60 partial unchanged. Updated expected counts only after
  comparison;34 targeted retail-enabled tests pass. Private stop/coverage JSON
  retained. Browser/execution acceptance pending; full SDK goal active.


- **2026-09-10 (facing decoder retail non-regression):** Previous facing decoder
  was implementation progress. All32 script inspection/catalog/trigger tests
  passed with the private disc enabled. Bounded catalog instrumentation found
  town01:91 scripts/421 dialogue/60 partial; town0c:74/287/48. No decoded path
  reached FACE_ROTATION_SETUP/RESET, so new opcode semantics remain pinned-
  reference and synthetic-only, not retail-observed. Initial probe used a wrong
  scene_id result key; corrected probe completed and retained private
  facing-script-coverage.json. Full SDK goal remains active.


- **2026-09-10 (facing script inspection):** Previous preset error check was
  verified progress. Inspected reference facing explanation and pinned d6e64c68
  decoder plus executing actor_ctrl VM: sub7 width16 operands/sub8 width1 agree.
  Added read-only FACE_ROTATION_SETUP/RESET decoding, explicit numeric operands
  and no scalar-heading inference. Unsupported subops still stop. Focused
  normal/extended/truncation tests pass;29 existing script tests pass with3
  retail skips. New retail/browser acceptance pending. Full goal remains active.


- **2026-09-10 (preset rename failure browser check):** Previous rename workflow
  was verified progress. Synthetic browser attempted Original->OTHER while
  Other existed. Case-insensitive duplicate rejection stayed visible in the
  dialog, draft OTHER remained editable and original card names stayed intact.
  Exact before/after server-side preset dictionaries matched. Private
  preset-error-browser service exited0. No production defect or patch needed;
  full SDK goal remains active.


- **2026-09-10 (preset rename browser acceptance):** Previous rename command
  was implementation progress. Synthetic browser expanded Rename preset,
  changed Original to Courtyard, submitted Save name and showed the updated
  card with X128 unchanged. Browser Save plus independent ProjectService.open
  proved exact original ID/source/components and clean saved state. Browser
  errors empty; private preset-rename-browser service stopped normally.
  Full SDK and release-parity goal remains active.


- **2026-09-10 (actor preset renaming):** Previous story/title restoration was
  verified progress. Added rename_actor_template to the existing command/history
  path and an inline preset-library form. Names validate before mutation; source,
  components and stable ID remain intact. Same-name submission is a no-op;
  case-insensitive duplicate names reject. Seven workflow tests pass including
  rename/Undo/Redo/no-op/invalid names/save-open; appearance tests also passed
  before the focused addition. JS syntax/diff checks pass. Browser acceptance
  pending; full SDK goal remains active.


- **2026-09-10 (story/title lifecycle restore):** Previous input-after-restore
  run was verified progress. Fresh owned61d99eac... reached opening story after
  three title loads, loaded saved title from story (generation5,last_ok1),
  displayed full menu and restarted story on another12-frame Cross press.
  Final frame5869, neutral pad, active audio, underruns0; exit0. Private
  story-title-restore evidence retained. This bounded lifecycle is accepted;
  field/cross-scene ownership and physical/audio quality gates remain open.
  Full SDK goal remains active.


- **2026-09-10 (input after repeated restores):** Previous NMake check was
  verified progress. Fresh owned61d99eac... completed three title loads and a
  12-frame port1 Cross press; override expired to neutral. Five-second capture
  was black, so a second bounded run retained15/25/35-second captures showing
  opening story text and illustrated story progression at frames3463/4064/4664.
  Both runs exit0; explicit input clear succeeded. MDEC0 means no FMV claim.
  Private restore-title-input(-long) evidence retained. No runtime patch needed;
  physical input and field/cross-scene restore remain open. Full goal active.


- **2026-09-10 (NMake precompile acceptance):** Previous project-issue browser
  workflow was verified progress. MinGW Makefiles configuration failed because
  GNU make was absent. Located installed Visual Studio18 x64 NMake and ran the
  same generated-overlay fixture with NMake Makefiles/UCRT GCC: seven variants
  passed executable checks in21.347s. No production fix was required. GNU Make
  remains unaccepted; updated parity ledger without broadening gameplay claims.
  Full SDK goal remains active.


- **2026-09-10 (project issue navigation acceptance):** Previous whole-project
  issue list was implementation progress. Synthetic browser started in second
  scene, showed one invalid actor from fixture, and navigated via issue link to
  the correct scene/selected actor and X125 warning. Undo removed warning and
  toolbar issue button. Browser errors empty; fixed singular actor count label.
  Private project-issues-browser server stopped normally. No retail gameplay
  claim; full SDK goal remains active.


- **2026-09-10 (project-wide placement issues):** Previous coordinate submission
  acceptance was progress. Extracted one serializer-backed placement issue helper
  shared by Inspector and a whole-project issue list. State reports affected
  actor/scene identities even with no active scene or selection. Toolbar opens
  the issue list and links each actor through normal scene/selection APIs.
  Scope explicitly excludes other build/source validation. Six workflow tests
  pass including inactive-scene issue discovery; JS syntax/diff checks pass.
  Browser acceptance pending. Full SDK goal remains active.


- **2026-09-10 (placement submission browser verification):** Previous warning
  check was progress with an explicit submission gap. Reproduced automation
  fill/blur changing only the displayed number (Undo remained disabled).
  Native ArrowUp/ArrowDown number-input controls submitted changes; effective
  X128, dirty state and Undo became visible with no warning. Browser Save and
  independent ProjectService.open proved persisted X128 and clean state.
  No production handler defect established; no source workaround added.
  Browser errors empty; private placement-submit-browser server stopped normally.
  Full SDK goal remains active.


- **2026-09-10 (placement warning browser acceptance):** Previous serializer
  feedback was implementation progress. Synthetic editor displayed the exact
  X125 grid/range warning and authored Y0 project-only warning. Browser Undo
  removed both; entering X128 showed no warnings, but the retained server log
  does not confirm submission of that edit. Valid-coordinate service behavior
  is established by the preceding focused test, not this browser input.
  Browser errors empty; private placement-feedback-browser server stopped
  normally. This is synthetic editor acceptance, not a retail build or gameplay
  result. Full SDK and release-parity goal remains active.


- **2026-09-10 (placement build feedback):** Prior save-status browser work was
  verified progress. Inspected MAN placement serialization and referenced heading
  evidence; no supported heading field established. Transform state now exposes
  build_issues using the actual coordinate encoder, and Inspector displays them
  before Build. Invalid X/Z grid/range and project-only authored Y are explicit;
  edits remain usable in project space. Six workflow tests pass including
  invalid125/Y0, valid64/16384 boundaries and Undo clearing warnings. Syntax/diff
  checks pass; browser acceptance pending. Full SDK goal remains active.


- **2026-09-10 (save-status browser acceptance):** Previous section metadata
  was implementation progress. Retail P2 navigation showed Unsaved: Active scene;
  applying a text edit added Actor and dialogue edits and made Build report
  stale. Undo restored freshness and scene-only status; Save displayed Project
  saved. Browser exposed a non-UTF8 separator introduced by the edit script;
  replaced it with ASCII comma, verified strict UTF8 decode and JS syntax, then
  reloaded after Save and verified a new authored edit label. Initial dirty-page
  reload did not replace the UI; no verification relied on that attempt.
  Browser errors empty. Private save-status-browser service stopped normally;
  full goal remains active.


- **2026-09-10 (unsaved project sections):** Previous title visual comparison
  was evidence-producing progress. ProjectService now retains per-section saved
  digests alongside the existing dirty digest and exposes unsaved section labels.
  Texture/dialogue status identifies Active scene versus actor/dialogue edits,
  texture replacements, presets and other saved metadata. Save/Open initializes
  section baselines; persistence format remains unchanged. Eight workflow/report
  tests pass; targeted selection/navigation/edit/Undo/Redo/reopen checks pass;
  JS syntax/diff clean. Browser label acceptance remains pending. Full goal active.


- **2026-09-10 (title restore visual A/B):** Prior repeated-restore probe was
  evidence-producing progress. Separate cold control/save-only and three-load
  runs completed with exit0. Control's final screenshot was also logo-only;
  restored final screenshot contained the full menu again. Thus previous
  missing-text capture does not establish persistent restore-only corruption.
  Intermittent appearance cause remains unknown. Private staged evidence in
  title-restore-visual-ab; bounded title visual recovery only, with no field/
  cross-scene or input/audio-quality acceptance. Full goal remains active.


- **2026-09-10 (repeated title restore probe):** Previous texture workflow was
  verified progress. Fresh owned61d99eac... run completed one save and three
  loads with successful status generations. Five-second windows advanced302,
  300,302 frames; active host audio/nonzero samples continued, underruns0 and
  overflow71912 unchanged. Process exit0. Before screenshot shows title menu;
  final screenshot lacks menu text while retaining logo. Cause/persistence not
  established, so visual restoration remains unresolved. Private evidence in
  repeated-title-restore; full goal active, field/cross-scene gates still open.


- **2026-09-10 (texture build-report browser acceptance):** Previous P2 browser
  acceptance was progress. Fresh private project changed one TIM payload byte
  in texture://town01/5/raw/0 through the verified replacement service. Build
  reported one texture change,33312 overlay bytes and passing provenance/opaque/
  LZS checks. From town0c, the report link opened the effective authored texture
  in town01:256x256,4bpp,16 palettes; replacement SHA101eb864cf57 matched the
  report. Browser errors empty. Private texture-report-browser evidence retained
  under local-output/sdk-20260909. No runtime launched or visual gameplay claim.
  Full SDK goal remains active.


- **2026-09-10 (P2 build-report browser acceptance):** Previous resource links
  were implementation progress. Fresh private build changed town01 P2 script36
  run0x11 from Greetings. to Greetings!, retaining ten-byte capacity. Report
  showed one change,24894 overlay bytes and passed provenance/opaque/LZS checks.
  Clicking its run link from town0c switched to town01, opened script36 and
  focused the authored textbox at0x11 with Greetings!. Browser errors empty.
  Private p2-report-browser evidence retained under local-output/sdk-20260909.
  No game runtime launched; P2 gameplay display and texture-report browser
  navigation remain unaccepted. Full SDK goal remains active.


- **2026-09-10 (resource build-report navigation):** Previous actor browser
  acceptance was progress. Extended build-change links to current authored TIM
  and partition-two script records resolved through assetRecords. Texture links
  switch source scenes and use the existing verified preview; P2 links open the
  owned script with the edited run focused. Missing authored resource owners
  remain plain report text. Four extracted production-handler same/cross-scene
  scenarios plus missing-owner checks pass; syntax/diff checks pass. Resource
  navigation browser acceptance remains pending. Full SDK goal remains active.


- **2026-09-10 (build report browser acceptance):** Previous source navigation
  implementation was progress. Fresh private town01/town0c project built three
  actor49 changes: model103->94, animation15->18 and Z12096->12288. Report showed
  24894 overlay bytes, current authored state and passing provenance/opaque/LZS
  checks. From town0c, clicking the Z report row switched to town01 and selected
  actor49 with authored Z12288 in Inspector. Browser errors empty. Private
  build-navigation-browser evidence retained under local-output/sdk-20260909;
  no game runtime launched. Dialogue focus remains handler-only acceptance.
  Full SDK goal remains active.


- **2026-09-10 (build report source navigation):** Previous freshness regression
  repair was progress. Build reports now retain audited owner_id alongside the
  changed resource ID. Actor rows open the source scene and actor; dialogue
  rows additionally focus the supported text run. Older reports and non-actor
  rows remain readable without invented navigation. Three report tests and JS
  syntax pass; an extracted production-handler harness verifies seven same/
  cross-scene, dialogue, busy, missing-scene and failed-request scenarios.
  Browser acceptance remains pending; this adds no runtime gameplay claim.
  Full SDK and release-parity goal remains active.


- **2026-09-10 (build freshness regression repair):** Previous MSVC generator
  acceptance was verified progress. Source review found the selection-exclusion
  test wrote an unused selection attribute instead of exercising ProjectService.
  Corrected it to select(None)/select(actor) and assert actual selected state.
  Added a focused real-command sequence proving edit changes the build key,
  Undo restores it, Redo recovers the edited key, template capture leaves it
  unchanged and Save/Open preserves it. Three build-report tests pass. No
  production freshness defect was found; no runtime/build acceptance is inferred.
  Full SDK goal remains active.


- **2026-09-10 (MSVC precompile inventory acceptance):** Previous preset-control
  fix was verified progress. Extended the existing executable overlay fixture
  with generator selection and Release output handling for multi-config builds.
  Visual Studio18/MSVC passed seven growth/shrink/body/split variants including
  35 images in12.083s. Default Ninja/GCC passed in6.401s after an initial sandbox
  denial of Ninja; no runtime source changes were needed. Updated release parity
  with exact scope; Make and retail transition acceptance remain open. Full SDK
  goal remains active.


- **2026-09-10 (preset eligibility browser acceptance):** Retail town0c actor1
  correctly disables Apply for a town01 donor preset and shows the scene reason.
  Browser verification exposed empty authored appearance objects enabling Capture
  with a blank donor label; the editor now requires an actual donor_entity_id.
  Reload verified disabled name/capture controls and useful guidance for actor1;
  town01 actor49 with donor15 retains enabled Capture/Apply and the explicit
  verification-on-Apply message. Browser error log empty; JS syntax and diff checks
  pass. Private QA preset-eligibility-browser under local-output/sdk-20260909.
  This is editor acceptance only; no game runtime was launched. Full goal remains
  active, including unresolved release parity and broader authoring features.


- **2026-09-10 (preset application eligibility):** Previous appearance preset
  buildout was verified progress. Project state now supplies selected-actor
  eligibility and reasons for preset cards; incompatible scene/donor structure,
  missing selection and Live mode disable Apply before a failed request. This
  derived metadata is not persisted and performs no fresh disc parsing. Eligible
  appearance presets explicitly retain verification-on-Apply. Three focused
  preset tests pass, including actual cross-scene command rejection without
  state mutation and an assertion that state rendering never calls disc-backed
  appearance_options. Existing workflow/HTTP-template checks and JS syntax pass.
  UI change not separately browser-accepted this turn. Full goal remains active.

- **2026-09-10 (reusable appearance presets):** Previous title PCM evidence was
  progress. Extended actor templates with explicit authored-appearance-v1 scope;
  capture stores a donor pair separately from position presets. Applying delegates
  to the existing freshly verified appearance command, preserving position and
  using normal history/persistence/build paths. Validation rejects wrong source
  scenes/donors and mixed components. Two targeted preset tests passed; existing
  workflow/appearance/HTTP-template/catalog suite12 passed1 private-disc skip.
  Retail browser captured Axe worker from actor49 donor15, cleared override,
  applied preset, saved and built model103->94/animation15->18 only. Fresh import,
  opaque bytes and LZS checks passed; no browser errors. Independent open verified
  persisted template/assignment. Private QA appearance-template-browser under
  local-output/sdk-20260909, server exit0. No new gameplay run; native actor
  creation and unrestricted model/animation authoring remain incomplete.

- **2026-09-10 (title audio PCM acceptance):** Prior startup checks were verified
  progress. Two cold baseline runs of61d99eac... reached title and exited0;
  MDEC0/CD-in0 means no FMV/XA acceptance. Nonzero SPU/host counters advanced.
  Initial WAV request captured oldest silent startup frames; retained that
  mistake, then captured recent explicit indices in a second run. Ten-second
  44100Hz stereo SPU/host captures have peaks21845/21853, RMS3637.92/3612.03,
  zero clipped samples and zero fully silent frames. Surrounding20.005s window
  has zero underrun/overflow deltas; startup71904 overflow count retained.
  Private evidence: local-output/sdk-20260909/audio-output-health/title, including
  pcm-analysis.json and acceptance.json. This verifies bounded title PCM delivery,
  not subjective/hardware audibility or battle synchronization. Full goal active.

- **2026-09-10 (audio startup runtime acceptance):** Previous reporter fix and
  MSVC build were progress. Launched exact binary61d99eac... twice with RunService
  identity/mod guards and isolated zero-overlay projects. Normal SDL driver:
  output active1, bridge-pull,519057 host frames. Child-only unavailable driver:
  active0, zero host frames,532140 guest SPU frames. Both exited0; no OS audio
  settings changed. All early samples were zero; normal cumulative overflow
  drops71624 retained, so no audible/queue-quality acceptance claimed. Actual
  runtime evidence in local-output/sdk-20260909/audio-output-health/live/
  acceptance.json. Full SDK/stability goal remains incomplete.

- **2026-09-10 (host audio readiness reporting):** Previous turn completed
  browser/build workflow acceptance. Returning to prompt stability targets found
  audio_stats falsely accepted an open device with an uninitialized pull bridge;
  callback emits silence there. Track successful SDL resume, clear on close and
  require ready bridge/device before reporting output available. No guest timing
  change. Production reporter regression fails old source and passes fixed
  missing-device/resume-failure/bridge-failure plus healthy legacy/pull cases.
  MSVC Release build exit0; new binary61d99eac... has not run. Previous gameplay
  binary2be69467... preserved in local-output/sdk-20260909/audio-output-health;
  verification.json records full source/binary hashes. Updated release-parity
  evidence; audible continuity and full SDK goal remain unaccepted.

- **2026-09-10 (snapped transform browser/build acceptance):** Prior lifecycle
  fix was progress. Fresh town01 browser physically dragged actor0049 Z handle
  with256-unit snapping: imported12096 -> authored12288. Undo removed the override,
  redo restored it, Save/Open existing retained it, and selecting actor49 after
  reopen showed separate imported/effective values. Build emitted one position.z
  change and24894 overlay bytes; fresh-import/opaque-byte/LZS checks passed.
  Package SHA e6e12b3da548662f9e8beb9f33ab3185be7c8f5a2c5625fc126db9a9aba70744
  verified on disk. Independent ProjectService.open confirmed saved transform.
  Browser errors empty; private QA under local-output/sdk-20260909/snap-workflow-
  browser, browser-final-state.json is authoritative after project reopen (the
  harness final-state.json refers to its original service object). QA server
  stopped exit0; no runtime launched. Browser API has only completed drag, so
  Escape mid-gesture remains handler-tested rather than browser-accepted.

- **2026-09-10 (viewport gesture lifecycle):** Previous turn made verified
  snapping progress. Found drag lifetime only handled pointercancel: Escape,
  window blur and lost capture could leave a draft active. Added shared gesture
  cancellation, pointer ownership, hidden-tab cancellation and cancellation when
  other API work starts. Transform release rechecks Edit capability, selected
  entity, project/scene/source context and original position; changed state
  cannot commit a stale drag. Normal state rendering also cancels stale gestures.
  Actual handlers in local-output/sdk-20260909/transform-lifecycle-qa.cjs passed
  snapping plus Escape/blur/hidden/lost capture, changed context/position, busy
  release, unrelated pointer events and normal single-command release. Syntax
  and diff checks passed. No browser drag or game runtime acceptance this turn.
  Full SDK/recomp goal remains incomplete.

- **2026-09-10 (optional transform snapping):** Prior turn was implementation
  progress. Added off-by-default X/Z gizmo snapping with16/64/256/1024 scene-unit
  steps aligned to the origin, plus proposed coordinate feedback while dragging.
  Gesture start captures the chosen step; release uses the existing undoable
  set_transform command and pointer cancellation discards the draft. Executed
  actual pointer handlers in a focused Node harness: positive/negative snapping,
  changed controls during drag, release-only command, cancellation and unsnapped
  movement passed. Existing project workflow tests5/5 passed. Fresh town01 browser
  verified checkbox and256-unit selection with no errors; physical pointer drag
  and cold gameplay were not repeated. QA: local-output/sdk-20260909/transform-
  snap-qa.cjs and transform-snap-browser. Heading/native actor creation remain
  incomplete; full goal remains active.

- **2026-09-10 (transition instruction navigation):** Previous turn was verified
  implementation progress. Transition source links now select their exact decoded
  SCENE_CHANGE operation. Fresh town01 browser project accepted partition-two
  script0 at0x16 with incoming0xF. Also closed the previous flag-navigation P2
  coverage gap: context19 reference selected CFLAG_SET at0xC in that same script.
  Browser errors empty; JavaScript syntax and diff checks passed. QA project and
  final state retained in local-output/sdk-20260909/transition-path-browser.
  No game runtime launched; actual transition execution remains unaccepted.

- **2026-09-10 (flag instruction navigation):** Connected individual flag-reference
  operations to the exact decoded instruction in the shared script workspace.
  The instruction section expands, selects and focuses the source PC, with
  incoming links available immediately. Missing PCs produce an explicit notice.
  Fresh town01 browser acceptance selected actor0049 SYSFLAG_TEST at0x45 from
  its flag group, with incoming0x44/0xF8 and empty Back history; no browser errors.
  JavaScript syntax and diff checks passed. Private QA: local-output/sdk-20260909/
  flag-path-browser; no runtime launched. P2 uses the same owner route but was
  not separately exercised this turn. Full SDK goal remains incomplete.

- **2026-09-10 (script control-flow navigation):** Prior candidate inspector
  integration was progress. Added shared instruction rendering for actor/dialogue
  and trigger reports with decoded successor buttons, incoming source links,
  selection highlight/focus and Back history. Unknown targets remain text with
  branch condition and available decoder stop reason; no invented instructions
  or execution simulation. Fresh retail browser project tested actor0049's23
  instructions: flag_set0x18 ->0x39(CFLAG_CLEAR), Back ->0x18(SYSFLAG_TEST), incoming
  From0x16 ->CFLAG_SET. Actor0001's9instruction partial report retained nonclickable
  0x1E/0x33 successors and unsupported0x29 stop0x6B. Browser errors empty, JS syntax
  and diff checks pass. Isolated service session62789 exited0; private project
  and final state under `local-output/sdk-20260909/script-path-browser`. Trigger
  view integration shares the helper but separate trigger browser acceptance
  remains pending. Script control editing, execution analysis and full goal open.

- **2026-09-10 (correlation inspector integration):** Prior authored correlation
  fix was progress. Added readable unconfirmed candidate summaries with matched
  appearance layers, optional donor, capture frame and world position; raw
  evidence remains available. Isolated browser service replayed the retained
  appearance capture, explicitly historical: actor0049 showed Effective,
  donor0015, frame36175, position4288/-128/11712. Clearing the appearance override
  through the browser removed the candidate after the response completed and
  displayed the capture-again reason; service state confirmed no authored assets
  and unavailable correlation. Browser errors empty, JS syntax/diff checks pass,
  owned session9079 exited0. Private project/final state under
  `local-output/sdk-20260909/appearance-correlation-browser`. No game was launched
  or new capture claimed. Fresh live integration and full SDK goal remain open.

- **2026-09-10 (authored appearance correlation fix):** Previous cold appearance
  gameplay was progress and exposed imported-only matching. Correlation now
  evaluates imported/effective appearance variants without changing imported
  documents; model/animation come from the donor while the target retains its
  local-count and placement provenance. Each candidate records matching layers
  and effective donor; ambiguity/zero confirmed matches remain intact. Project
  appearance changes invalidate cached correlation, including clear/undo rather
  than reviving a stale match. Retained gameplay capture replay now finds only
  effective candidate80080c8c for actor0049; the earlier retail capture matches
  the imported layer separately. Both replays preserve capture history and do
  not claim a fresh live observation. Regression run:18tests,17passed/1private
  disc skip, including different donor local-count, source immutability and
  invalidation. Private replay script/output beside the appearance acceptance
  evidence. Fresh browser/live integration remains pending; full goal active.

- **2026-09-10 (appearance cold gameplay):** Prior authored animation preview was
  progress. Fresh project under `local-output/sdk-20260909/appearance-live-20260910`
  authored only actor0049 -> donor0015: model103/animation15 -> model94/animation18.
  Build audit proved exactly2changed fields, unchanged opaque bytes and LZS
  roundtrip. Package SHA25687e19d16304b00b91cdf0c1f41482b9dd992a8343d8e980168763d6e2bfb740e;
  existing runtime SHA2562be69467c02937d6ccfc86a6030f9380bc5654ea6404694ea3e801a25b716fab.
  Cold runtime PID34860 consumed24894bytes/13sectors, guard_failed=false. First
  title confirm entered attract playback; second entered normal opening story,
  naming and field without restore or skips. `appearance-dialogue.png` visibly
  shows the axe-carrying replacement speaking the original actor0049 Genesis Tree
  dialogue at the child's location; `following-dialogue.png` shows it closed.
  Guarded v2 capture accepted90nodes, epoch a9107ab50bc591adf2319fde32f91acdcbf982efaa438eb83f700a668e926e71.
  Node80080c8c header has model94/animation18/local_count8 and placement4544/12096.
  Candidate identity remains unconfirmed: current correlation reports actor0049
  unmatched because it compares imported appearance only. This is a concrete
  authored-correlation integration gap to fix next. Clearing the override in a
  separate in-memory project generated zero overlays/zero changed fields; cold
  revert acceptance remains open. Runtime and editor PID47184 exited0; editor
  session1918 terminal. Broader compatibility/full SDK goal remain unaccepted.

- **2026-09-10 (authored animation resource preview):** Previous usage-link
  acceptance was progress. Animation asset preview choices now include authored
  effective assignments through the existing guarded appearance preview service,
  retaining separate imported choices. Exact verified usage replaces the old
  independent actor/model membership filter. Isolated browser project assigned
  actor0046 to actor0040; clip0012 offered Actor0040 Authored effective/model0099,
  opened an Authored appearance preview with15frames and stepped to2/15. Clip0008
  separately offered Actor0040 Imported/model0092 and opened Imported animation
  with25frames. Browser errors were empty; JS syntax and the39binding usage smoke
  passed. Private project/final state under
  `local-output/sdk-20260909/animation-preview-browser`; owned service exited0.
  No game process or retail mutation. Runtime timing, appearance gameplay and
  the full SDK goal remain unaccepted.

- **2026-09-10 (animation usage browser acceptance):** Prior animation usage
  implementation was progress. Fresh isolated service/project on port4394
  imported town01 and assigned supported actor0046 appearance to actor0040.
  Browser resource refresh and clip0012 details showed actor0040 Effective;
  following the link selected actor0040 and displayed donor0046. Undo invalidated
  the resource catalog; the first attempt to open clip0008 therefore found no
  record. Refreshing through the UI restored it and displayed actor0040 as
  Imported + Effective. Browser errors were empty. Graceful shutdown saved final
  state under `local-output/sdk-20260909/animation-usage-browser`; selected actor
  was0040 with zero authored assets in Edit mode, process exit0. No retail or
  runtime mutation. This closes animation-link browser acceptance, not runtime
  animation semantics or the full SDK goal.

- **2026-09-10 (animation asset usage):** Previous cross-scene model navigation
  acceptance was progress. Extended asset detail usage links to animations,
  joining verified MAN/ANM actor-model bindings with imported/effective donor
  assignments. Exact donor identity preserves different clips on the same model;
  no animation identity is guessed from numeric IDs or channel count. A fresh
  private town01 catalog supplied 14 animations / 39 bindings, all matching the
  editor's usage calculation. Verified appearance command actor0040 -> actor0046
  changed effective clip0008 to clip0012 while retaining original usage, and undo
  restored the reference baseline. Node checks exercised the actual UI helper,
  the same-model/different-clip case, absent bindings and JavaScript syntax.
  Initial QA import-path setup failed and was fixed before rerunning successfully.
  Private evidence: `local-output/sdk-20260909/animation-usage-qa/fixture.json`
  plus the adjacent Python/CJS runners. New animation-link browser acceptance,
  live animation semantics and the full SDK goal remain open. No runtime or
  retail data was modified.

- **2026-09-10 (cross-scene model usage acceptance):** Prior model relationship
  implementation was progress. Fresh private project imported town01 and town0c,
  yielding 96 initial assignment records. Browser details for shared model 00f1
  listed town01 actor0003 and town0c actor0002 as Imported + Effective. Following
  the latter switched to town0c and selected actor0002 with matching model;
  following the return usage selected town01 actor0003. Final service state
  confirmed the destination and zero authored assets. Browser errors were empty,
  and the isolated service shut down gracefully. Evidence project and reference
  records remain under `local-output/sdk-20260909/model-usage-browser`. No game
  process or retail mutation. Broader asset relationships and full goal remain open.

- **2026-09-10 (model usage relationships):** Prior captured-flag UI acceptance
  was progress. Added project-wide model reference records derived from imported
  actors and effective appearance donors, independent of active scene. Imported
  and effective assignments remain distinct after an override; relationships
  carry scene and actor IDs without claiming runtime residency. Model details
  now offer Used by links that switch to the owning scene and select the actor.
  Project/appearance suite ran 11 tests (10 passed, one private-disc skip),
  including save/open, undo, output isolation and inactive-scene references;
  JavaScript syntax passed. Browser navigation remains to be verified. Broader
  texture/animation/script dependency relationships are still incomplete, and
  the full SDK goal remains active.

- **2026-09-10 (captured flag browser acceptance):** Previous snapshot adapter
  was progress. A private QA service replayed the retained cold-gameplay
  observation, marked historical, into the normal endpoint. Browser expansion
  showed epoch boundary frame 18487, the correct epoch-scoped node IDs, words
  and bit lists (including 0x08820882 -> 1,7,11,17,23,27), and the explicit
  captured-only/no-owner-binding statement. After graceful service shutdown,
  reopened the panel against a fresh service with no observation: the previous
  table disappeared and the no-matching-capture message appeared. Browser
  errors were empty. This is UI acceptance using retained data, not fresh live
  flag acceptance; no game process was launched. Full SDK goal remains active.

- **2026-09-10 (captured runtime node flags):** Prior pagination work was
  progress. Pinned Andrew script-VM documentation distinguishes local +0x62,
  scratchpad global and context +0x10 banks; the current guarded v2 profile
  already captures the confirmed generic node flag word at +0x10. Added an SDK
  adapter and flag-browser snapshot section for those existing captured words,
  showing epoch-scoped nodes, hexadecimal values and set-bit indices without
  claiming a script-owner binding or present-time values. Rejects wrong scene,
  mixed epoch, unstable capture and unsupported field evidence. Four tests,
  including the retail HTTP workflow, passed in 9.327 seconds; the retained
  cold-gameplay observation yielded 90 captured words. JavaScript syntax passed.
  Browser rendering of the new snapshot section is still unverified. No new
  memory reads, profile relaxation or flag writes. Local/global/system bank
  observation and confirmed script binding remain pending; full goal is active.

- **2026-09-10 (flag browser pagination):** Previous flag-index implementation
  was progress, but its first-100 result cap left broad searches incomplete.
  Added previous/next navigation with bounded 100-group rendering, exact result
  ranges, disabled boundary controls and page reset on search. Browser verified
  town01 page 1 (1-100), page 5 (401-418), empty results and a one-result P2 search
  from the last page. JavaScript syntax and browser error checks passed. No
  authored project or runtime change. Full SDK goal remains active.

- **2026-09-10 (scene flag reference browser):** Prior cold dialogue acceptance
  was progress. Added a pure SDK flag-reference index, source-verified active
  scene endpoint and searchable editor view with P1/P2 source navigation.
  Groups preserve script, bank, encoded index and extended target rather than
  merging unproven runtime identities. Unknown paths remain absent; values and
  runtime bindings remain explicitly unresolved. Town01 has 1123 references,
  418 groups, 91 scripts (60 partial). Two semantic-isolation tests and the
  retail HTTP workflow passed (3 tests, 8.582 seconds); JavaScript syntax passed.
  Browser search for P2[0] found context index 19 / extended target 248 and
  opened the matching CFLAG_SET at PC 0xC; browser errors were empty. No runtime
  or authored project mutation was required. Live flag observation, symbolic
  story-state semantics and editing remain pending; full SDK goal is active.

- **2026-09-10 (dialogue gameplay acceptance):** The preceding failed run was
  progress because it isolated an acceptance-navigation gap. Compared the
  recorded screenshots/inputs: the successful prior title confirmation followed
  its screenshot within about 8 seconds, versus about 24 seconds in the failed
  attempt. A fresh isolated cold run at HEAD 51a42dbb confirmed promptly from
  the visible title, entered the narrated story, completed name confirmation
  and the Village Elder conversation, and reached normal town control. Walked
  to the nearby child and visibly rendered `VahnSDK VERIFIED` followed by
  unchanged `Genesis Tree, too!`; the preserved name token accounts for the
  concatenation. A further normal Confirm closed the dialogue and restored
  field control. This accepts the actor-49 fixed-run dialogue edit in gameplay;
  it does not establish arbitrary script editing or P2 gameplay acceptance.
  The same package SHA f44a8fc57ee981abd4ce90d7d1a1298fad3c477d6457ca11e0cdcf9971f01bd9
  consumed 24894 overlay bytes across 13 sectors, with no disc guard failure.
  No restore, guest-memory write, or runtime patch was used. Runtime and editor
  both exited 0. Evidence: private `dialogue-navigation-20260910` QA directory
  under `local-output/sdk-20260909`, including screenshots, commands, observed
  scene, build provenance and process identities. Full SDK goal remains active.

- **2026-09-10 (dialogue cold-run acceptance attempt):** Prior scene-transition
  explorer work was progress. Created a separate private town01 project at
  `local-output/sdk-20260909/dialogue-live-20260910` from HEAD d9bc87f6. Actor
  49's supported 12-byte dialogue run at decoded MAN offset 27164 was changed
  to `SDK VERIFIED`; the authored build audit proves fixed-span compression,
  round-trip equality, and unchanged opaque bytes. One overlay loaded with
  the expected source identities and no disc guard failure. The cold runtime
  remained responsive but repeated the title/movie sequence despite recorded
  normal controller inputs; no field arrival or visible edited dialogue was
  established, and overlay consumption remained zero. This is a failed
  gameplay acceptance attempt, not evidence of a dialogue serializer defect
  or a diagnosed core stability bug. Preserved commands, screenshots, audit,
  and identity evidence in the private QA directory; stopped the owned runtime
  cleanly (exit 0) and requested graceful editor shutdown. No speculative
  runtime patch, savestate restore, or gameplay-success claim. Next: resolve
  title navigation against the earlier accepted cold-run route before another
  dialogue acceptance attempt; the full SDK goal remains active.

- **2026-09-10 (scene-transition explorer):** Prior P2 catalog work was progress.
  Added a pure SDK graph adapter, source-verified active-scene endpoint and
  read-only editor view. Edges preserve script owner, record provenance, PC,
  encoded entry and unresolved reachability; unknown names do not become named
  scenes. The graph reports partial coverage and offers source-script and
  already-imported destination navigation. Town01 has one map01 reference in
  P2[0] at PC 0x16 (encoded 96/25/direction4), under a partial script graph.
  Three focused tests passed, including synthetic unknown/self references,
  metadata isolation and real HTTP retail source. Browser IAB20/editor4394
  showed the reference, correctly disabled the unimported destination, and
  opened P2[0]'s three instructions including SCENE_CHANGE. Error log empty;
  no screenshot-based layout acceptance claimed. Owned server session76775
  interrupted after checks (exit1); no runtime or authored mutation. Node
  syntax and diff whitespace checks passed. Runtime transitions remain open.

- **2026-09-10 (P2 resource catalog):** Previous saved-asset workflow was
  progress. Extended the metadata-only script catalog to all bounded P2 records,
  reusing the verified prefix/record decoder without scanning unknown tails.
  Town01 now exposes 91 scripts (52 P1 actors plus 39 P2), 421 dialogue segments,
  1,123 scoped flag references and one encoded transition; 60 graphs remain
  partial. The full browser catalog contains 908 records. Script and dialogue
  resources open the P2 workspace directly, and authored badges merge on the
  canonical script asset ID rather than duplicating a scene-owner ID. Synthetic
  alias/unknown-tail coverage and retail determinism/payload-free checks pass;
  ten catalog/resource tests passed, with the existing real P2 HTTP workflow
  also passing earlier in this turn. Node syntax check passed. IAB tab 19,
  private editor 4394: opened P2[37] dialogue from discovery, applied SDK, observed
  one authored script entry, reopened/cleared it and returned to Project saved
  with no browser errors. Owned server session 27510 interrupted (exit 1).
  No runtime launched; no reachability or gameplay text-display claim.

- **2026-09-10 (saved P2 dialogue discovery):** Prior stability recheck was
  progress: five executable regressions supplied fresh evidence. Continued the
  authoring workflow by listing P2 Dialogue overrides as project-wide script
  assets, independent of actors and derived catalogs. Shared bounded P2 source
  inspection now supports direct structural identity as well as verified trigger
  references; the HTTP endpoint rejects wrong scene/partition/record identities.
  Browser IAB tab 18 on private editor 4394 applied/saved SDK, reopened the
  project, opened P2[37] from its authored asset and retained the text. Clear/save
  removed the authored asset; browser error log was empty. Owned editor session
  1949 was interrupted after acceptance (exit 1); no game was launched. Main
  project and runtime remained untouched. Gameplay text display remains open.
  Nine focused HTTP/importer/catalog/project tests passed, including offline
  cross-scene discovery and returned-record isolation; Node syntax and diff
  whitespace checks passed.

- **2026-09-10 (renewed stability requirement):** Read the supplied SDK prompts
  and rechecked the existing runtime/precompile fixes at `b46f770b`. The static
  overlay clean/incremental build fixture, restore entry/CPS fixture, production
  CD/XA data-ready regression, staged snapshot transaction/resume-PC harness and
  diagnostic-independent header rejection all completed with exit zero.
  Initial restricted-shell compiler discovery/skips and Ninja denial were not
  counted; Git Bash with approved compiler execution passed. Updated the parity
  ledger with current evidence and explicit remaining gameplay gates. No runtime
  source, generated game input or proprietary payload changed. Prior P2 browser
  acceptance remains progress; the broader SDK goal is not complete.

- **2026-09-10 (P2 browser acceptance):** Separate private project
  `p2-browser-qa`, editor 4394, IAB tab 17: refreshed resources, searched trigger
  0008, opened referenced P2[37], and entered the shared dialogue workspace.
  Applied `SDK` to its ten-byte run; UI showed three authored bytes and seven
  padding spaces, with Clear enabled. Clear restored inherited text and the
  exact clean baseline (`dirty=false`, Edit); Save was correctly disabled,
  so no save action was executed. Browser error log was empty. The owned
  exec server session 60453 was interrupted after verification (exit 1);
  no runtime was launched. Main editor/project untouched. This verifies the
  user-facing P2 edit/clear path; gameplay display and opening ownership remain.

- **2026-09-10 (P2 HTTP acceptance):** Added and passed a private-disc test
  against the real EditorServer on an ephemeral loopback port. Trigger 0008
  resolves an authorable P2 owner; command Apply is reflected by a fresh
  trigger request with correct space padding, and Clear removes the override.
  Opening trigger 0045 still returns unsupported authoring and zero runs.
  All six HTTP requests returned 200; server shutdown and thread termination
  were verified. Temporary project only, no saved user project or runtime
  changes. Browser interaction acceptance remains outstanding.

- **2026-09-10 (P2 dialogue workspace wiring):** Trigger-script inspection now
  returns freshly verified dialogue options and offers Open dialogue workspace.
  The shared text editor routes refreshes through the trigger identity, verifies
  the returned script identity, and uses existing Apply/Clear/history/save
  commands for P2 owners. Unsupported records retain their authoring reason.
  JavaScript syntax and focused resource/project/trigger tests pass. Browser
  interaction acceptance is still pending; the running editor was not restarted
  and no runtime or authored project was changed in this turn.

- **2026-09-10 (retail P2 package verification):** A fresh scan of town01's
  39 P2 records finds records 36 and 37 authorable, each with one ten-byte run.
  Added a private-disc P2[36] package regression: one punctuation byte changes,
  the packaged MAN decompresses to exactly the audited result, and clearing
  the override reproduces the baseline package hash. The test found and fixed
  build audit labels incorrectly assigning P2 edits to same-index P1 actors;
  dialogue audit identity now comes from the verified source run owner.
  Focused build, project dialogue and authoring tests pass. This proves package
  construction, not in-game display; browser controls and opening ownership
  work remain. No runtime or saved editor project was modified.

- **2026-09-10 (P2 project/build plumbing):** Added P2 dialogue identities to
  project source resolution, commands, undo/redo and offline persistence.
  Set commands still reverify the imported scene and exact source run; failed
  verification is transactional. Builds accept only Dialogue on P2 targets,
  resolve the imported scene, and pass record/run ownership through the same
  context patch and audited merge as P1. Focused project/history, core authoring
  and build tests pass; P2 history/save/reopen and failed-source preservation
  have dedicated coverage. P2 browser controls and a real P2 package acceptance
  are not yet implemented/verified. Opening tail ownership remains unresolved.

- **2026-09-10 (P2 authoring core):** DialogueAuthoringContext now accepts
  scene-scoped P2 script identities and uses the existing all-partition alias,
  section-overlap and prefix bounds before exposing runs. Equal-span patching
  reuses immutable baseline guards and before/after graph checks. Synthetic
  P2 edit proves only the selected glyph span changes; aliased records and
  unresolved terminal ownership remain rejected. Private town01 P2[3] is
  confirmed unsupported for authoring, with no runs exposed. All 44 focused
  tests pass. This is importer-core support; editor commands and build project
  integration for P2 are still outstanding, as is opening tail ownership.

- **2026-09-10 (retail opening halt identified):** Retail field dispatch at
  0x801DE95C indexes `(opcode & 0x7F) - 0x21` into 0x801CECC0. Entry for
  2A points to 0x801E3568; its mask 0x20 misses the 0x50/60/70 flag routes,
  returning the unchanged PC via 0x801E35C8 and 0x801E3628. Ordinary 2A is
  now displayed as DISPATCH_HALT with no successor, retaining an explicit
  trailing-entry-ownership stop for authoring. The eight reached opening
  segments remain inspectable; trailing bytes are not scanned. Extended 2A
  remains unsupported. Evidence uses the previously disc-matched PROT 897
  capture and corresponding generated code. All 43 focused tests pass.
  Next work is bounded P2 entry/terminal ownership and authoring integration,
  rather than guessing an operand length after this verified halt.

- **2026-09-10 (opening dialogue reached):** Added MENU_CTRL 85/8E/8F acquire
  forms with full payload bounds and explicit advance/wait edges, using pinned
  `nibble_8.rs` blob `d64782c800d120ce30606979a475d916166ce493`.
  Actual opening P2[3] reaches 261 instructions and eight dialogue segments at
  PCs 1343, 1363, 1491, 1522, 1556, 1593, 1628 and 1661. It remains partial
  at PC 1697 opcode 2A, absent from pinned field VM/disassembler cases.
  P1 actor 40 now reveals a target-inside-instruction conflict at PC 30;
  its graph is withdrawn, not accepted as editable. Catalog has 342 dialogue
  segments, 402 flag references and 49 partial scripts. Opening authoring is
  still gated; no text edit or runtime acceptance is claimed.

- **2026-09-10 (emitter and wall-paint script coverage):** Added MENU_CTRL
  60 six signed words, 61 bounded acquire payload with advance/wait edges,
  and 70-73 collision wall paint with distinct masked/unmasked widths.
  Evidence: exact pin d6e64c68 executing `menu_ctrl/nibble_5_6_7.rs`, blob
  `0146f87c0c381d06ffaa14d27f4f8197b04ec587`. All 41 focused script,
  trigger, catalog, dialogue project and build tests pass, including truncated
  payloads and extended headers. Actual opening P2[3] reaches 222 instructions
  and stops at PC 1284 MENU_CTRL 85, still with zero accepted dialogue.
  These are encoded script effects, not runtime collision-state reconstruction.
  Runtime and saved projects unchanged; next coverage target is acquire form 85.

- **2026-09-10 (retail CD continuation):** Verified the retained 202728-byte
  field capture equals the prefix of private-disc PROT entry 897 at offset 0.
  C-family dispatch masks the selector low nibble at 0x801E25E0 and indexes
  table 0x801CEF88; entry 13 targets 0x801E29E0. s8 receives the input PC at
  0x801DE848 and s4 preserves it at 0x801DE890. CD increments s8 by two:
  null allocation or returned-context flags bit 3 returns the advanced PC;
  otherwise 0x801E2A18 restores s4 and returns the original PC via 0x801DEE50.
  Ordinary CD now exposes advance and wait edges, correcting the pinned VM's
  incomplete halt model. Extended-context CD remains explicitly unresolved.
  Private `retail-cd-verification.json` records disc/capture hashes and matching
  generated instruction words. All 40 focused tests pass; opening P2[3] reaches
  61 instructions and stops at PC 327 MENU_CTRL 60, with zero dialogues yet.
  No runtime execution or saved-project mutation was needed for this evidence.

- **2026-09-10 (retail allocation discrepancy found):** Read-only inspection of
  the sibling generated field overlay capture finds SHA-256
  `3026cd12a22c12f94ed05ef5af551df786267d2d29c330b5c57e82c5ec5aae19`.
  Its contiguous C-family-looking table has entry 13 at 0x801CEFBC pointing
  to 0x801E29E0. Generated code there increments s8 by two, calls 0x8003CF04
  with callback 0x801DC0BC, and branches on its result at 0x801E29FC; the
  delay slot copies the incremented s8 to v0. Null returns branch to
  0x801E3628, non-null continues at 0x801E2A04. This contradicts the pinned
  VM's unconditional same-PC halt model and changes the next investigation:
  prove table selection, non-null return path, s8 meaning and capture-to-disc
  provenance before authorizing encoded continuation. No decoder semantics
  changed from this preliminary finding; no runtime was launched. Evidence
  source: sibling generated/overlay_captures_static.json record 0 and
  generated/overlays_static_0000.c, both read-only.

- **2026-09-10 (recognized external control-flow boundaries):** Inspection now
  displays CD as SCRIPT_CONTEXT_ALLOC with its verified encoded width and no
  successor, retaining an explicit unresolved-control-flow stop. This separates
  recognized bytes from unsupported bytes without authorizing the opaque tail.
  Exact-pin search finds the allocation hook only in the host default, VM
  dispatcher and test implementation; no production allocation behavior proves
  a resume address. Referenced original dispatcher dumps are absent locally.
  Actual opening P2[3] shows 35 instructions, zero dialogues, and the boundary
  at PC 194. All 39 focused tests pass, including ordinary/extended boundary
  ownership and existing dialogue authoring rejection checks. Opening progress
  requires independent retail dispatch/resumption evidence, not advancing past
  the hook by assumption. Runtime and saved editor projects remain unchanged.

- **2026-09-10 (script allocation boundary):** Pinned MENU_CTRL CD allocates a
  script context and returns Halt at the current PC, not an encoded fallthrough.
  Inspection now reports the unresolved allocated-context entry explicitly;
  opening P2[3] remains bounded at PC 194. Added the 14 neighboring C-family
  forms with fixed continuations, preserving signed slot values and the CB/CC
  frame-delta sentinel. C9 remains host-dependent and opaque. Evidence:
  d6e64c68 `menu_ctrl/nibble_c.rs` blob
  `5d7fb2b1cd7e4a687965ec6fa5edc5b0f0455052`. All 39 focused decoder,
  trigger, catalog, dialogue project and build tests pass with the private disc.
  Next opening work must resolve context allocation/entry ownership rather than
  assume sequential execution past CD. Runtime and editor projects unchanged.

- **2026-09-10 (camera and render script coverage):** Implemented both 0x46
  render layouts and all four 0x45 camera forms: load payload, save, unsigned
  absolute apply jump and sparse ten-slot configuration. Exact pin d6e64c68
  executing `field/step.rs` blob `9c7801d1626c6f6eb8bd48f9f7c3e5851379e674`
  and `step/camera.rs` blob `f0612a77815d9453819a8ee54e44634d98b22fce`
  establish widths, selector masks and continuations. All 37 focused script,
  trigger, catalog, dialogue project and build tests pass with the private disc.
  Opening P2[3] now reaches 34 instructions, stopping at PC 194 MENU_CTRL CD;
  no opening dialogue is accepted yet. Retail P1 catalog expectations remain
  unchanged. Runtime and saved editor projects were not modified.

- **2026-09-10 (field menu instruction coverage):** Added pinned MENU_CTRL 0x81
  model/animation operands, 0x30-3F field-state continuations and the 0x40-4D
  ramp family except host-dependent 0x49. Explicitly decode the wider 0x45
  layout and encoded absolute jumps in 0x43/44. Evidence is executing
  LegaiaRE d6e64c68 `menu_ctrl/nibble_8.rs` blob
  `d64782c800d120ce30606979a475d916166ce493` and `nibble_3_4.rs` blob
  `8e6bf5c521460228664efaaefce629b2e897db36`. Opening P2[3] reaches 30
  instructions and stops at PC 139 on opcode 0x46, with no accepted dialogue.
  Comparison against the committed decoder finds ten additional P1 dialogue
  segments in actors 25-30 and 36, 354 total, and 416 encoded flag references;
  49 scripts remain partial. Focused tests cover truncation, unsigned model
  fields, extended headers and both jump polarities. Runtime is unchanged.

- **2026-09-10 (opening effect instructions):** Extended bounded script decoding
  for opcode 0x34 color/intensity (sub 0) and animation trigger (sub 3), including
  extended context headers. Evidence: LegaiaRE pin
  `d6e64c68ede25813d35db20980da82a1a025549b`, executing
  `crates/engine-vm/src/field/step/effect.rs`, blob
  `e94f1afc597a036f2b45a486ec4294b70e2f51ad`. Host-dependent sub 1/2 and
  unimplemented forms remain opaque. All 33 focused script, trigger, catalog,
  dialogue authoring, project and build checks pass with the private retail disc.
  Actual town01 opening P2[3] now reaches nine instructions and stops at PC 49
  on MENU_CTRL 0x81; no dialogue is accepted yet. Next work is evidence for that
  continuation and P2 authoring integration. Runtime was not changed or launched.

- **2026-09-10 (Live follow and restore recovery):** Added opt-in bounded actor
  following and separate candidate markers, with epoch chaining, cancellation,
  no overlapping polls and no automatic retry after rejection. Browser checks
  found and fixed explicit-restart cached-epoch reuse; repeated captures,
  manual Stop, Edit cancellation and runtime-stop cleanup passed. Ten observer
  tests and the real-source controller harness pass. One cold same-scene save/
  load recovered 90-node Live observation after normal dialogue input; settled
  windows measured 60.130/59.999 FPS without cache misses or buffer underruns.
  The private parser lost the first invalidation response, so retained pre-input
  evidence is explicitly delayed. See `legaia-sdk/restore-live-acceptance.md`.

- **2026-09-10 (automatic cold field observation):** The new production launch
  preparation passed a full cold New Game without manual witness requests or
  restore. Opening movie completed 1,337 frames, town01 rendered, and the
  unchanged v2 guard accepted 90 nodes with all three witnesses current.
  Zero-overlay baseline retained zero writes/consumption; runtime and isolated
  editor exited zero. Protected project hashes were unchanged. Restored and
  cross-scene Live acceptance remain separate.

- **2026-09-10 (opening dialogue scope):** Verified the opening town01
  conversation is referenced by MAN P2 record 3, outside current P1 text
  authoring. Added two pinned-VM instruction forms for bounded inspection;
  five opening instructions are now exposed before unsupported opcode 0x34.
  All 31 focused script/dialogue checks passed with retail input. Unknown
  paths remain opaque. This is source inspection, not gameplay text acceptance
  or a runtime change; see the trigger inspection documentation.

- **2026-09-10 (texture runtime acceptance):** Cold authored and zero-overlay
  baseline runs visibly prove magenta ground replacement and removal; both
  exited zero without savestate restore or RAM writes. Late exact-PC witness
  collection caused authored Live rejection; manual early preparation let the
  baseline pass the unchanged v2 guard. Discovery/launch now prepare required
  PCs after identity checks. A separate startup probe verified automatic
  preparation and exited zero; twelve focused tests passed. Runtime/profile
  sources and the main editor project remain unchanged.

- **2026-09-10 (build review):** Added an editor-facing report of the audited
  changes included in a package, with authored-snapshot freshness and explicit
  build-time validation scope. Browser checks found and corrected old command
  invalidation that discarded reports; edits now retain a stale report and undo
  restores its authored-state match. Two report and fourteen build checks pass.
  Runtime behavior is unchanged; no game was launched for this slice.

- **2026-09-10 (trigger script navigation):** Connected verified MAP gate-1
  trigger identities to bounded MAN P2 records and read-only script inspection.
  Source record boundaries and decoded paths remain distinct from runtime
  reachability or named transition claims. All 51 town01 eligible references
  resolve; 35 reports retain explicit partial decoding. Focused service/importer
  checks and browser navigation passed. Runtime implementation unchanged.

- **2026-09-10 (field map workspace):** Implemented source-base wall grid,
  trigger and region discovery from verified field MAP carriers. Source wall
  geometry is shown on a display ground plane, with runtime paints,
  actor collision, floor heights and unresolved scene destinations excluded
  from claims. Town01 exposes 4228 rectangles, 99 triggers and 14 regions.
  Five importer and five resource/project checks passed; browser toggle,
  inspectors and refresh invalidation passed. Runtime unchanged.

- **2026-09-10 (authored asset browser):** Connected project-wide actor edits,
  TIM replacements and position templates to a dedicated browser category.
  Authored references remain separate from immutable imports and derived
  catalogs; navigation uses source scene and stable identity. Eight project tests
  and cross-scene browser routing, template, deduplication and provenance checks
  passed. Runtime unchanged.

- **2026-09-10 (authored TIM replacements):** Implemented content-addressed
  authored TIM references, project history/persistence, separate imported and
  effective preview layers, and carrier-preserving build integration. Headers,
  pixel mode, VRAM rectangles and palette layout remain source-validated;
  replacement image/palette content is user-authored. Project integrity tests
  reject modified authored files before save/open. Five writer and twelve build
  tests passed; browser layer/Clear/Undo/Redo/Save and HTTP boundary/model-pixel
  checks passed. File-picker and gameplay acceptance remain outstanding.
  Runtime source is unchanged.

- **2026-09-09 (central script resources):** Connecting bounded actor scripts
  and inline dialogue to the asset database and existing authoring inspector.
  Town01 supplies 52 scripts, 344 segments and 380 flag references. Category
  search, actor navigation, exact segment focus and project-switch invalidation
  pass in the browser; ten focused catalog/workflow/HTTP checks pass.
  Per-instruction flag references and named scene changes retain encoded source
  provenance and unresolved runtime scope. Catalog metadata is derived and does
  not alter imported or authored state. Runtime timing/source remains unchanged;
  actual gameplay routes and flag values are outside static catalog acceptance.

- **2026-09-09 (bounded dialogue authoring and compression):** Added supported
  plain-text run commands, history/persistence, editor controls and guarded
  composition with appearance/placement builds. Source controls and opaque
  bytes remain unchanged. A bounded exact-expansion optimal LZS fallback now
  rescues greedy overflow without relocating data; no-op and already-fitting
  encodings retain their bytes. Actual custom text fits the original town01
  stream and decoded output is verified. Gameplay dialogue display and broader
  script authoring remain unaccepted. Runtime source and stability fixes are
  unchanged by this SDK milestone.

- **2026-09-09 (central texture and animation resources):** Added explicit
  source-verified resource discovery to the central asset database and browser.
  Town01 exposes 96 TIM textures and 14 animations covering 39 evidenced actor
  bindings. Texture inspection supports local palette selection; animation
  inspection resolves an explicit imported actor before using the clip preview.
  Catalog metadata never dirties imported/authored project state and contains
  no pixels or frame payloads. Unknown timing, unsupported bindings, shared
  texture banks and unreferenced ANM records remain explicit scope limits.
  Runtime source and prior stability acceptance are unchanged.

- **2026-09-09 (donor appearance authoring integration):** Connected verified
  same-scene model/animation pairs to project commands, Undo/Redo, Save/Open,
  the scene viewport, authored frame preview/export and bounded mod builds.
  Browser actor0049/donor0036 workflow passes through Apply, undo/redo, export,
  reopen, build and clear. Combined donor/X edits produce one overlay with
  three audited fields; clearing edits reproduces the baseline package hash.
  Invalid or stale donor evidence fails before output. Runtime code is unchanged;
  donor gameplay compatibility and broader SDK authoring remain open.

- **2026-09-09 (asset search and actor content inspection):** Connected NPC
  animation playback/frame export, searchable SDK model/actor/scene records,
  and bounded script/inline-dialogue inspection to the editor. Browser checks
  verify model-reference search, actor selection, frame playback/export and
  explicit unknown-opcode boundaries. No runtime or generated game code was
  changed; existing stability acceptance remains scoped as recorded below.
  A separate donor model/animation header serializer passes a private two-byte
  round trip and compression-capacity rejection; interactive authoring and
  gameplay validation for that helper remain the next integration frontier.

- **2026-09-09 (central scene geometry and NPC poses):** Added verified
  scene-header ANM poses and a textured WebGL authoring viewport. Town01
  renders 51/52 entities; 39 NPC poses match 5,028 independent reference
  vertices. Browser mesh picking, move/undo and marker toggle pass. Request-
  scoped disc reuse removes repeated full-image hashing within one preview,
  with source-change guards and no persistent path-only verification cache.
  Runtime code and accepted cold/restore evidence are unchanged. Scripted
  placement/visibility, NPC timing, native entity authoring and broader runtime
  transition/restore acceptance remain open.

- **2026-09-09 (visible revert, restore comparison and export):** Cold authored
  and retail runs now prove savepoint0052 move/revert with the same binary,
  corresponding guarded world coordinates, and zero overlays in the retail
  baseline. Both exited 0. One idle save/load retained 59.85/60.02 FPS
  cold/restored, matching frame-period p95 and recurrent static ownership;
  no settled CRC churn or new audio underruns. The nonrecurrent VM witness was
  correctly cleared and remained unavailable, so full observer reacquisition
  and repeated/cross-scene restore acceptance stay open. Textured party
  idle/walk preview and private static GLB export now work in the editor;
  Khronos validation and Blender import/render pass for Vahn and a scene tree.

- **2026-09-09 (XA data-ready correction and posed SDK assets):** Reproduced
  the 17-frame FMV stall without input or restore. Actual sector/DMA evidence
  plus retail Ghidra validation showed XA-only arrivals reissuing the previous
  video header through erroneous INT1. Generic CD routing now returns actual
  CPU data readiness and keeps realtime XA away from CPU delivery; no title
  patch. Production-controller tests fail before/pass after, including mode,
  filter, mute, coding and DMA scheduling cases. The fixed optimized binary
  decoded 1,337 movie frames and exited movie mode; a further no-input cold run
  visibly reached the title menu and attract playback. Audible quality remains
  unaccepted. SDK party idle/walk
  poses and source-scoped shared textures match independent pinned controls;
  retail baseline builds support revert without fake unchanged overlays.

- **2026-09-09 (snapshot transaction and SDK run verification):** All known
  snapshot sections validate/prepare before guest mutation; partial MDEC
  commands reserve full expected input capacity. Caller resume-PC rejection
  also occurs before commit. Production corruption/OOM/reordered/raw/zlib and
  caller regressions pass. Runtime identity now receives the build revision.
  Authored transform templates and private Build & Run are connected and
  verified. One late-input FMV run exhibited a repeated STR acquisition
  timeout with advancing CD/XA/VBlank and idle MDEC; cause remains unproven.
  Do not attribute it to optimization or claim FMV/audio acceptance. A fresh
  early-input optimized run reached New Game/name selection and consumed the
  complete guarded MAN overlay. No restored run was used as timing truth.

- **2026-09-09 (SDK connected field workflow):** Cold town01 runs consumed the
  guarded MAN replacement (24,894 bytes / 13 sectors); revisioned field-v2
  observation accepted 90 actor nodes and conservative MAN-header candidates.
  Editor Build & Run verifies private runtime identity and mod activation,
  with graceful owned-process Stop. TIM previews retain explicit association
  limits. Default-stack disc fingerprinting and diagnostic-independent snapshot
  identity rejection are fixed. Initial private field builds lacked generic
  optimization flags, so their timing is not performance evidence; subsequent
  private MSVC configuration explicitly restores `/O2 /Ob2 /DNDEBUG /EHsc`.
  Malformed-state transaction validation is handled separately from guest
  timing or post-restore performance acceptance.


- **2026-09-09 (Legaia SDK authoring):** Restored evidence-backed field import
  and bounded observer/profile services; added a central project/asset/scene
  model, separate authored transform commands, persistence and local editor.
  Ported the generic guarded observation protocol without replacing bitmap
  execution tracking, added private MAN placement packages and repaired mod
  installer paths. MSVC build, observer bounds/restore fixtures and title/story
  rendering pass. Live field acceptance remains gated on the profile's actual
  execution witnesses; editor validation is not timing or gameplay acceptance.

- **2026-09-09 (Legaia stability parity):** Preserved current CD/XA scheduling,
  startup, bounded hitch telemetry and host frame pacing. Added explicit
  savestate overlay-ownership invalidation and build-time split-source
  discovery, with executable regression fixtures. Debug input gains generic
  port selection without taking over the other physical controller. See
  `docs/legaia-release-parity.md` for source identities, validation and remaining
  retail gates; this is not a new timing/oracle acceptance claim.

- **2026-08-31 (GPU DMA2 review correction — source gate passed):**
  The first fork review found two valid timing defects in the DMA2 candidate. The
  linked-list engine now reads and emits one live payload word at each
  one-clock boundary. A CPU rewrite after an earlier word transfers can now
  affect a later word. The optional widescreen prepass now fingerprints its
  cached nodes and commands. It discards all cached transform metadata if live
  RAM differs. The second fork review found three more valid issues. Late
  service now consumes every elapsed DMA boundary. Header and link rewrites
  now invalidate cached prepass topology at the exact header-read boundary.
  The obsolete opt-in polygon-drop filter was removed. The focused regressions
  and full build pass. The runtime suite passes 61 of 62 enabled tests. The
  remaining `mod_runtime_test` crash reproduces on the unchanged upstream base,
  and two pre-existing tests remain disabled. Fresh Spot and Vampire Hunter D
  builds also pass their
  600-frame headless gates. Visible software-renderer routes and another fork
  review are still required before the public branch can change.

- **2026-07-28 (per-game host audio cushion — implemented, parser validated):**
  Added `[audio] buffer_ms` as a runtime-only developer setting with a guarded
  30–500 ms range. The compatibility default remains 180 ms, preserving the
  reserve required by titles with long streamed-stage production gaps; a game
  may opt into a lower target after validation to reduce audible latency.
  `audio_stats` and the opt-in runtime cadence report now expose both actual
  fill and configured target. This changes only the host playback bridge and
  does not alter guest SPU state, instruction timing, or code generation.
  Recompiler build and all 33 registered tests pass.

- **2026-07-27 (BIOS boot-skip parity across BIOS images — FIXED, validated):**
  `bios_hle`'s boot-skip did nothing under the bundled OpenBIOS. Root cause was
  ordering, not policy: `main.cpp` correctly forced the *kernel-call* tier off
  when an image exports no `deliver_event_ret`, by assigning `bios_hle = false`,
  and then derived `boot_skip` from that already-mutated flag. OpenBIOS omits
  `deliver_event_ret` (B0 semantics unvalidated) but DOES export
  `shell_entry_phys`, so the skip was structurally available and got cancelled
  anyway — one player-facing flag meaning two different things depending on a
  BIOS detail no player can see. Enhancement-phase (load-time) defect; no
  timing-core change.
  Fix: the two axes are now decided by one pure, dependency-free function,
  `psx_bios_hle_plan()` (`runtime/src/bios_hle_plan.c`), which reads the
  REQUESTED `bios_hle` for the boot decision and gates each axis on only the
  anchor it actually needs; refusals are reported at startup instead of silently
  downgrading. `psx_bios_hle_configure()` additionally clamps `boot_skip` to
  `shell_entry_phys != 0` so the banner and `hle_dump` cannot overstate what can
  fire. New `bios_hle_plan_test` (16/16 runtime ctest green) pins the matrix,
  including an exhaustive 64-case sweep asserting the boot decision is
  independent of `deliver_event_ret` and the call decision independent of
  `shell_entry_phys`.
  Validated on Ape Escape (SCUS-94423) built against this framework, both BIOS
  backends linked, headless: OpenBIOS → `bios_boot=skip to game (shell
  skipped)`, `hle_dump route=2` shows the one-shot fire at `vec 0x30000`,
  `ra=0xBFC06EA8` (the exact continuation `bios/OpenBIOS.toml` documents),
  game running on screen. Retail SCPH-1001 → same banner, same `vec 0x30000`
  fire at `ra=0xBFC0702C`, game running; differs only in
  `bios_backend=HLE (LLE fallback)` vs `LLE (recompiled BIOS)`. Negative control
  `PSX_BIOS_HLE=0` on OpenBIOS → `bios_boot=real intro`, ring total 0 (hook not
  installed), display 640x478 shell mode: the flag still turns the skip off.
  Also in this pass: a BIOS profile's `[runtime]` block was parsed into
  `BiosConfig::runtime` and read by NOTHING, and `bios/OpenBIOS.toml` carried an
  inert `bios_hle = false` there that read as the reason HLE was off.
  `load_bios_config` now REJECTS `[runtime]` in a BIOS profile. And
  `psx_icache_fastpath_test` had been unbuildable ("redefinition of
  `psx_advance_cycles`" — the test's counting stub vs the header's `static
  inline`), which blocked every runtime test registered after it; it now builds
  with `PSX_OVERLAY_DLL_BUILD=1`, the seam `psx_cycles.h` already provides.

- **2026-07-21 (VLC load-charge batching — shipped; dual still ~22 ms):**
  Runtime-only batch: under `psx_next_service_cycle`, `psx_cyc_charge`
  accumulates into `g_psx_cyc_batch` (no per-insn `psx_cycle_count` store);
  flush at IRQ check / MMIO sync / savestate / advance-past-deadline.
  Absorb/fudge still per-insn; guest totals at barriers unchanged; no MotK
  regen. Dual headless MotK (`PSX_NETPLAY_TIMING=1`, pinned halves): heavy
  25–50 band host med ≈39.7 fps / guest ≈21.9 ms/f / admit ≈3.1 (guest peer
  ≈39.8 / 22.5 / 2.8) — same floor as pre-batch (~21 ms / ~40–42). Counter
  publish was not the dual-peer tax; residual remains load-delay volume /
  LLC under phase-locked VLC. Next: PGO retrain after hot-path edits, or
  accept same-machine lockstep FMV floor.
- **2026-07-21 (MotK FMV host cost — MDEC/IRQ/charge; dual still ~21 ms):**
  Aimed to cut MotK FMV host work so two lockstep peers fit ~16.7 ms/f.
  Shipped bit-exact host opts: MDEC MB output reserve (no per-byte
  ensure_capacity), sparse-column IDCT, ch0 DMA burst feed
  (`mdec_dma_write_words`), sticky-IRQ undeliverable early-out in
  `psx_check_interrupts`, `psx_cyc_charge` pre-deadline bump on compiled
  loads/steps. Dual headless MotK (`PSX_NETPLAY_TIMING=1`, pinned halves):
  band 25–50 fps still guest ≈21 ms/f / fps ≈40–42 (admit ≈2.5–3) — same
  floor as before. HARD_CAP 16K→64K tried, no gain (real CD/timer events
  already shorten the deadline); reverted. Residual is phase-locked dual
  VLC load-delay volume / LLC contention, not MDEC FIFO or present/admit.
  Next: emitter-level load-charge batching for VLC leaves, PGO retrain
  after these hot-path edits, or accept same-machine lockstep FMV floor.
- **2026-07-21 (netplay FMV — lockstep guest inflation, not present/admit):**
  User A/B: two windowed offline MotK intros fine; headless netplay FMV still
  slow vs offline headless. Opt-in `PSX_NETPLAY_TIMING=1` splits the [FPS]
  line into guest ms/f vs admit ms/f. Heavy FMV (~25–50 fps samples): guest
  ≈21 ms/f, admit ≈3 ms/f (median) — frame time is dominated by the guest
  quantum under phase-locked dual MDEC, not Swap and not INPUT_CONFIRM wait.
  Offline headless same stretch is ~17 ms/f (≈57 fps). Pipelined CONFIRM
  tried in recomp-net (tip publish, drain next tick) — no FPS gain on
  localhost (~41→~41.5); reverted. Present-path / half-rate work is a dead
  end for this regression. Next lever: reduce MotK FMV host cost so two
  aligned peers fit a 16.7 ms budget (or accept same-machine lockstep floor).
- **2026-07-21 (netplay FMV — restore present-before-admit):**
  User confirmed early same-machine netplay FMV was ~50–60 and gameplay
  under lockstep stays ~60 — so the rematch-safe `finish→admit→pace→present`
  order was the FMV regression (expensive depth24 CPU present after admit).
  Restored `finish→present→admit/pace` via RAII `NetplayVblankTail` (admit
  on every return path; offline still paces before present). Kept half-rate
  depth24 present skip + UDP `poll()` barrier; no `SDL_Delay(0)`. Verify
  MotK intro FPS + tick-0 arm after rebuild.
- **2026-07-21 (netplay FMV — re-land half-rate depth24 present):**
  Windowed same-machine MotK netplay FMV was back at ~30–40 after the
  rematch-safe `finish→admit→pace→present` order. Re-landed host-only
  half-rate depth24 present: after admit, skip pace+Swap every other
  depth24 vblank (present first, then alternate); admit/barrier unchanged
  (no `SDL_Delay(0)` / present-before-admit). Offline path untouched.
  Rebuild MotK `build-release` + verify intro FPS and tick-0 arm.
- **2026-07-21 (lobby game_version + release pins):**
  WS lobby now carries `game_version` alongside `game_name` (create/list/join).
  Server rejects `version_mismatch` / `game_mismatch`; list can filter by either.
  MotK/MW bake release pins from repo `VERSION` (Release → e.g. `0.1.0`, else
  `dev`) via `PSX_GAME_VERSION` / `SNESRECOMP_BUILD_VERSION`. Clients send the
  pin on create/join and filter the lobby browser. Redeploy lobby server for
  remote matchmaking. Docs: `recomp-net-server/docs/WS_LOBBY.md`.
- **2026-07-21 (portable .pst / boot_state v3 LE wire):**
  Savestate / boot_state version → 3: header + section framing and all
  module snapshots emit little-endian field wires (`pst_wire.h`) — no
  host-struct padding (TimerRegs, DMA async/delayed, SpuVoice, McSlotState,
  CDROM Pending/Queued). Netplay host→guest blob transfer is identical on
  Win/Linux x86_64 and macOS ARM. Old v2 `.pst` files are rejected (recapture).

- **2026-07-20 (netplay match_caps — host settings enforce):**
  Lobby `create` / `set_match_caps` / `start` carry host sim caps
  (aspect, turbo_loads, bios_hle, fast_boot, auto_skip_fmv, input_delay,
  language). Server echoes on join/update/launch; guests apply before boot.
  recomp-net-server + psx_lobby_client + MotK launcher. SNES mirror:
  widescreen/hud/ignore_aspect/input_delay/ws_extra via snes_lobby + MW main.

- **2026-07-20 (launcher: persist controller selection immediately):**
  Device/mode/deadzone now write `settings.toml` on change (not only Launch),
  so Refresh / Quit / soft-return keep the pad. Refresh falls back to saved
  GUID if the dropdown index is stale.

- **2026-07-20 (lobby default → public host):**
  `psx_lobby_default_url` now `ws://netplay.retcomm.net:8765`
  (match SNES); override still `PSX_NET_LOBBY_URL`. Synced MotK vendored
  `psx_lobby_client.{c,h}` + recomp-net `docs/lobby.md`.

- **2026-07-20 (Metal Warriors H2H: top-edge prop pop):**
  Full-frame present recenters dual cam ~$40 up; spawn/OAM top was only
  −$70/−$70 so platforms popped at Y=0. Spawn −$A8, OAM CMP −144, present
  Y wrap peek for −64..0, dist-limit +64 when vert-widen.

- **2026-07-20 (launcher: controller Refresh rescan):**
  Dashboard Device row (P1 + offline P2) has Refresh — pumps SDL joysticks,
  re-enumerates gamecontrollers, keeps selection by GUID. Offline + netplay.

- **2026-07-20 (launcher: lobby lock emoji via symbol fallback font):**
  Password lobbies showed □ for 🔒 because the primary face has no emoji.
  Load a symbol fallback face through the shared Dear ImGui font atlas so
  missing glyphs resolve.

- **2026-07-20 (launcher lobbies: button order + dblclick join):**
  Lobbies actions: Return to Launcher → Change Player Name → Host Game →
  Join Lobby. Double-click a lobby row joins (same path as Join Lobby,
  including password modal).

- **2026-07-20 (launcher: offline↔netplay switch buttons):**
  Dashboard footer: "Switch to Netplay" beside Launch Game (only when
  `PSX_HAS_RECOMP_NET`); "Switch to Offline" beside Netplay Lobbies.
  Home Netplay tile gated the same way; no-netplay builds skip home chooser.

- **2026-07-20 (netplay load — apply freeze after hash match):**
  Suppressing INPUT at `np_begin_load_apply` deadlocked both peers in
  `netplay_barrier_admit`: tips stopped → `try_admit` never succeeded →
  guest never ran → `savestate_poll` never applied. Fix: keep INPUT during
  APPLYING; suppress only at `np_enter_load_ready` until `hard_resync`+prime.

- **2026-07-20 (netplay load — false peer_disconnect → lobby):**
  Hash-match apply suppresses INPUT for seconds → `peer_disconnected(1500)`
  fired → soft-exit to lobby → rematch. Fix: timeout=0 (BYE-only) while
  `in_load_barrier`; HELLO keepalive every 250 ms during suppress/stall.

- **2026-07-20 (netplay post-load — stale INPUT clobber):**
  2nd+ loads: correct frame, then ~3–5s frozen while FPS lived. Cause: during
  LOAD apply/ready the slower peer kept emitting pre-resync INPUT tips; those
  ticks share ring slots with the new tip (`tick % 128`) and first-wins /
  overwrite races blocked `remotes_ready_for_sim` after `hard_resync`. Fix:
  suppress INPUT sends for the load barrier; reject out-of-window remote ticks;
  host `probe_finish` before sync+prime; re-anchor frame pacer on restore.

- **2026-07-20 (savestate load — force GL present after identical frame):**
  2nd+ load of the same `.pst` left FPS climbing while the picture stayed
  frozen: `gl_renderer_present_vram` / wide early-out skipped `SwapWindow`
  when display rect + present-dirty matched the last swap (common after
  restoring into an already-shown frame). Fix: `gl_renderer_invalidate_present`
  marks all present tiles dirty, clears path latches, resets interp history,
  and forces 8 presents; called from `psx_frontend_on_savestate_loaded`.

- **2026-07-20 (netplay post-load — admit barrier symmetric):**
  Host dropped `LOAD_READY` before `try_admit` (guest did not) → confirm
  wait with barrier already down; keeping remotes let stale tip=D
  first-wins. Fix: both stay in `LOAD_READY` until admit; `hard_resync`
  clears remotes again; sync+prime at mutual ready only.

- **2026-07-20 (netplay post-load — mutual-ready sync):**
  `hard_resync`+prime at apply let the later peer wipe the earlier tip
  (2nd load slower). Sync once at mutual ready. (Remote-keep reverted —
  see admit-barrier note above.)

- **2026-07-20 (netplay post-load — symmetric ready release):**
  Guest cleared `LOAD_READY` on READY ACK while host still had
  `state_stall_sim` → confirm wait / intermittent hitch. Guest now ACKs
  but stays in `LOAD_READY` until `try_admit` succeeds (pre-sends
  INPUT_CONFIRM so host can admit on the same poll as `probe_finish`).
  Ready-probe retransmit 40→8 ms; confirm retransmit 16→4 ms. MotK rebuild.

- **2026-07-20 (netplay post-load resume — frozen picture + FPS):**
  After load, FPS kept climbing while the window stayed on a stale/blank
  frame: (1) present blank-latch skipped redraw after restore; (2) delay
  rings empty after `hard_resync` while peers could still advance during
  APPLYING. Fix: `hard_resync` resets `sim_tick→0` + `prime_delay_inputs`;
  stall admit for APPLYING when `!savestate_pending` and all LOAD_READY;
  `psx_frontend_on_savestate_loaded` forces restage/blank once; skip FPS
  CLI during load barrier. MotK rebuild.

- **2026-07-20 (netplay host-only save/load commands):**
  User `savestate_request_*` refused on netplay guest; F-keys / debug TCP /
  `PSX_LOAD_SLOT` host-only or routed via `psx_netplay_request_*`. Guest
  follow-host sync uses `savestate_request_*_protocol`.

- **2026-07-20 (netplay load — post-restore lockstep rendezvous):**
  Hash-match load applied on each peer at different times after early
  `hard_resync` → rings/ticks drifted → admit hang / starvation. Fix:
  stage load → apply while admit runs → `hard_resync` only after restore →
  LOAD size=0 ready probe until both ACK → then resume. Heartbeat in
  admit barrier. MotK rebuild.

- **2026-07-20 (netplay save hang — coord probe must not stall):**
  Shift+F1 stalled admit before `savestate_poll` could write → deadlock.
  Fix: `STATE_PROBE` with `size==0` (coord) leaves admit running; only
  hash probe (`size!=0`) + chunk transfer stall. Guest retransmit replies
  without re-staging saves. MotK rebuild after sync.

- **2026-07-20 (netplay host-owned saves — hash probe + chunk transfer):**
  recomp-net: `RNET_STATE_MAX` → 8 MiB, `STATE_PROBE`/`PROBE_REPLY`, stall
  admit through probe + transfer; restored `rnet_session_wait_recv`.
  psx_netplay: guest sandbox `saves/netplay/`, host-only F-keys, match-start
  memcard probe, save = coord local write → hash-agree → transfer on miss +
  post-CRC verify; load same pattern + `hard_resync`. MotK `build-release`
  linked; verify Shift+F1 / F1 across LAN.

- **2026-07-20 (MotK title after FMV — leave-depth24 restage):**
  On exit from GP1 depth24, GL/VK `depth24_upload_policy` restaged full
  CPU VRAM as 1555 into the FBO. CPU still held packed RGB888 from MDEC →
  rainbow/static title background (text/overlays still drew as prims).
  V2: skip only framebuffer-sized depth24 transfers (keep texture A0s);
  on leave scissor-clear the skipped FB union (GL) — never blind-restage
  RGB888-as-1555. Char-select shrink-to-left-center still under probe
  (OFX=256 @ 512 CRTC looks correct; may be authored layout / separate).

- **2026-07-20 (MotK 2nd intro right-edge stretch):**
  `depth24_fix_trailing_margin` replicated the last good column when any
  chroma>40 pixel sat in the trailing 8 cols. On the starfield FMV that
  smeared stars into an 8-wide flickering strip. Now requires dense chroma
  (~12% of margin) and black-fills instead of column-replicate. Still no
  CRTC/content_w crop.

- **2026-07-20 (MotK netplay FMV — lockstep floor, not present path):**
  A/B: offline headless FMV ~59; two offline headless concurrent ~59; two
  netplay headless ~38–40. Not dual-CPU contention and not GL present.
  Lockstep (INPUT_CONFIRM frame barrier + same-tick input rendezvous)
  keeps both MDEC peaks aligned. Async confirm / peer drift made FMV
  *worse* (~22–28) via overlapped memory traffic. Barrier now UDP `poll()`
  (not `SDL_Delay(1)`); localhost peers pin to disjoint CPU halves (~45
  in A/B). Pipeline admit rewrite hung tick-0 — reverted.

- **2026-07-20 (MotK netplay FMV — restore pre-rematch vblank order):**
  User: same-machine netplay was 50–60 before rematch playback tweaks.
  Reverted `NetplayVblankGuard` present-before-admit and half-rate depth24
  present. Order is again finish→admit→pace→present. Kept: `s_present_w/h`
  clear (black rematch FMV), depth24 FBO upload skip, trailing-margin
  in-buffer fix, vsync-off while lockstep armed.

- **2026-07-20 (MotK netplay tick-0 hang — revert admit latency hacks):**
  After half-rate present, both peers armed lockstep then sat at frame 0
  until peer_disconnect. Cause: `SDL_Delay(0)` busy-spin starved peer UDP
  on dual localhost; same-call `try_admit` publish when CONFIRM pre-seen
  also unsafe. Reverted both.

- **2026-07-20 (MotK FMV netplay FPS — half-rate depth24 present):**
  Measured: headless dual-peer lockstep holds ~60 guest FPS through intro;
  windowed dual-peer ~30–40. Bottleneck is two GL CPU-presents serializing
  before the guest fiber resumes — not admit/guest. Fix: under netplay +
  depth24, present every other vblank (host-only; admit still every tick).

- **2026-07-20 (MotK FMV netplay FPS — skip depth24 FBO upload queue):**
  MDEC A0 was still queued as 1555 CPU→FBO uploads (`UP_RECTS_MAX`=16),
  force-flushing mid-movie. While `gpu_display_is_depth24()`, do not queue
  GL/VK uploads; on leave, drop queue (no full restage — see leave-depth24
  log above). Alone did not restore
  windowed netplay to offline rates (present cost remained).

- **2026-07-20 (netplay FMV host FPS — present/vsync ordering):**
  Offline MotK intro ~50+; netplay ~30–40 was host path, not guest
  divergence. Fixes (determinism unchanged): (1) force GL/VK swap
  interval 0 while lockstep is armed (restore on soft-exit) so driver
  vsync does not double-block after the wall pacer; (2) move
  `finish_frame`→present→`admit`+pacer so local Swap overlaps the peer's
  guest quantum. `turbo_loads` stays off in netplay.

- **2026-07-19 (MotK FMV right-edge — no present-width crop):**
  Upload-span + `content_w` left-aligned GL crop removed the chroma junk
  but replaced it with a flickering black pillar (span varied per frame,
  especially during lighting). Rework: keep full CRTC width always;
  `depth24_fix_trailing_margin` only replicates the last good column
  into the last 8 RGB cols when chroma junk is detected — in-buffer,
  no viewport shrink. Half-texel nearest UV clamp remains.

- **2026-07-19 (MotK FMV right-edge — trailing margin, not CRTC shrink):**
  Root cause: MotK depth24 crawl is 512×128 CRTC, but ~8 trailing RGB
  columns are stale/black in VRAM; GL edge sampling flickered that strip
  as garbage. Fix (no 2/3 width): track A0 upload span
  (`gpu_depth24_rgb_limit`); blank/crop last 8 cols on short depth24
  bands (`h<240`); `gl_renderer_present(..., content_w)` left-aligned
  UV crop + half-texel nearest clamp; screenshot skips `sync_cpu` on
  depth24 (was clobbering RGB888). MotK release+PGO rebuilt; user-verify
  2nd intro (Star Wars logo) edge + ~50 FPS.

- **2026-07-19 (MotK FMV right-edge / 2/3 revert):**
  Tried depth24 width=(CRTC*2)/3 (512→341) for right-edge junk; MotK
  intros rendered left-shifted with the right of the video clipped —
  confirms the Jul-18 finding (logo is centered in a 512 RGB line).
  Reverted 2/3. Kept: depth24→fmv_frame, short-band without force_4_3
  gate, nearest present on depth24. Right-edge junk needs a different
  fix (not shrinking CRTC width).

- **2026-07-19 (MotK FMV FPS after rematch patches):**
  Rematch video fixed; ~30–40 vs prior ~50+ was not a present-path
  regression. Prior ~50 med was MotK intro PGO (`PSX_PGO=use`); LTO-only
  baseline is ~39. Mistakenly cleared PGO — restored `PSX_PGO=use` with
  existing intro `.gcda`. `fmv_frame` restored (depth24 only forces
  `pin_43` short-band letterbox). Re-train via `scripts/pgo_motk_intro.sh`
  after large rematch edits if profiles go stale.

- **2026-07-19 (netplay rematch: black FMV = stale present tex size):**
  Root cause: `s_present_w/h` survived GL context destroy; rematch FMV same
  size as prior CPU present took `glTexSubImage2D` into a new unallocated
  `s_present_tex` → black. Cleared on shutdown + init_context. Also dropped
  per-frame `flush_cpu_uploads` on depth24 (was cutting intro ~50→~30 FPS);
  depth24 CPU scanout needs neither FBO sync nor upload flush.

- **2026-07-19 (netplay rematch: black FMV, audio OK):**
  Rematch linked and played, but MotK intros had XA audio with black video
  (FPS still dipped ~30–40 → MDEC ran). Earlier mis-attribution to sync_cpu;
  also reset present/FPS/MDEC/iso session statics; `iso_close` before reopen;
  depth24 forces 4:3 pin for short-band letterbox.

- **2026-07-19 (netplay rematch: sticky I_STAT/I_MASK):**
  After cycle-reset fix, rematch still starved: dump meta showed
  `psx_cycle_count=4` with leftover `i_stat=VBlank` + game `i_mask`.
  `interrupts_init` / `memory_init` now clear I_STAT/I_MASK (+ mem_ctrl);
  `starvation_ring_reset` on `session_reboot` so dumps are rematch-clean.

- **2026-07-19 (stick→D-Pad axial deadzone again):**
  Radial+sign for digital stick→D-Pad made left/right fire Up/Down from tiny
  Y drift (jump/crouch). Stick→button sources use per-axis `controller_deadzone`
  again; analog `axes_to_pad_pair` / hybrid stick-detect stay radial.

- **2026-07-19 (netplay rematch: stuck `psx_in_device_service`):**
  Rematch still froze after `lockstep armed`: soft-exit longjmps out of the
  vblank callback while inside `psx_devices_service_to_now`, leaving
  `psx_in_device_service=1`. Every later `psx_advance_cycles` then skips
  device service → no vblanks → hang after tick-0. Fix: clear the guard on
  every scheduler longjmp escape; `psx_cycles_reset_for_boot()` zeros the
  guest clock + deadline bookkeeping at `session_reboot`.

- **2026-07-19 (Digital stick→D-Pad radial deadzone):**
  Stick-as-D-Pad used a per-axis square threshold so centre drift twitched
  movement even with a large launcher deadzone. Stick axis→button sources now
  require radial magnitude past `controller_deadzone` (same idea as
  `axes_to_pad_pair`); triggers stay per-axis. Hybrid stick-detect matches.

- **2026-07-19 (netplay rematch HLE shell-skip latch):**
  After soft-return rematch both peers linked (`lockstep armed`) then froze:
  `s_shell_skipped` stayed set from the first match so HLE boot-skip never
  re-fired and both ran the interactive BIOS shell under netplay.
  `psx_bios_hle_configure` now clears the latch; `cdrom_init` resets boot
  disc speed to 1x; lobby launch uses `input_player=-1` (auto) again.

- **2026-07-19 (netplay rematch session_id + endpoint guard):**
  Rematch HELLO hang: server now allocates a fresh `session_id` on every
  `start`/`launch` (stale BYE/HELLO from the prior UDP session no longer match)
  and refuses start when host/guest endpoints are empty. Client refuses
  `fill_netplay_launch` / `launch_pending` when `peer_hostport` is missing.

- **2026-07-19 (netplay return-to-lobby rematch):**
  Lobby WS stays up across Launch. Window-close / Escape / peer BYE soft-exits
  via `PSX_RUN_RETURN_TO_LOBBY` (scheduler longjmp or pre-entry flag) instead of
  `exit(0)` when the match started from a lobby room. Teardown keeps the WS;
  launcher resumes on `netplay_room` with ready cleared; rematch Launch
  re-enters `session_reboot` (re-init guest + netplay). Server clears ready on
  `start` so both peers must Ready again.

- **2026-07-19 (lobby server → closed-source Rust):**
  Proprietary `recomp-net-server` (Rust) owns WS lobby + privacy/docs;
  removed C `servers/lobby` from open `recomp-net`. Client WS helpers
  vendored at `runtime/src/lobby_ws/`. Default
  `ws://netplay.retcomm.net:8765`.

- **2026-07-19 (netplay lobby server + launcher menus):**
  Lobby WS+JSON owned by proprietary `recomp-net-server` (was C
  `servers/lobby/` under open recomp-net);
  `psx_lobby_client` + shared launcher home → Offline / Netplay → lobbies table
  (host/join/password). Launch hands `PsxNetplayConfig` to
  `psx_netplay_start` (LAN endpoints from lobby). ICE relay stubbed.

- **2026-07-19 (netplay peer disconnect QoL):**
  Barrier `SDL_PollEvent` on `SDL_QUIT`/Escape → `shutdown_runtime`+exit.
  recomp-net `BYE` (pkt 7) + `rnet_session_peer_disconnected(~1.5s)`;
  `psx_netplay_shutdown` sends BYE. Surviving peer prints and exits instead
  of spinning in admit.

- **2026-07-19 (netplay latch + INPUT_CONFIRM + exclusive capture):**
  Host stages one pad per sim tick (`latched_for_tick`); barrier only
  re-samples via `needs_local_sample`, stalls on `input_desync`
  (INPUT_CONFIRM hash mismatch). Netplay capture is exclusive to the
  assigned PlayerInput (no keyboard-all / all-controllers merge) so peer
  hashes agree. Cleared on `finish_frame` advance. recomp-net: preserve
  early peer INPUT_CONFIRM when activating (wipe raced slower peer into
  permanent stall). Smoke: two headless MotK peers both `lockstep armed`,
  frames advance, no INPUT desync.

- **2026-07-19 (netplay lockstep stall + per-peer input device):**
  True delay-sync gate: pre-scheduler + each vblank `finish_frame` then
  blocking `poll_admit` (guest fiber parks; no free-run on admit fail /
  linking). Auto/`--net-input-player`: host samples P1 device, guest samples
  P2 when assigned (same-PC C40+keyboard); pad blob deadzone normalize.

- **2026-07-19 (netplay pad ownership — session slots always plugged):**
  Host local device → net-slot 0 (sim P1); guest local → net-slot 1 (sim P2).
  While active, SIO is network-only (no local/`override` writes). Both session
  ports stay connected from `psx_netplay_start` through linking so in-game
  2P/VS detect works; `refresh_player_devices` no longer clears them.

- **2026-07-19 (delay-sync netplay bring-up — recomp-net LAN):**
  Wired `recomp-net` into the runtime as CLI/env LAN delay-sync (not GGPO).
  `psx_netplay.{c,h}` + CMake auto-discover `../recomp-net`; vblank owns
  `pump`/`try_admit`/`publish`/`advance`; local pads stage only — publish is
  sole SIO writer while active. Turbo + low-latency re-sample gated off.
  Lobby UI / ICE server deferred. Smoke: two procs with `--netplay --net-slot`.

- **2026-07-19 (MotK title/char-select — savestate PC + flat GEO batch):**
  User still saw ~10 FPS after draw-area reject. Real char-select profile:
  ~30k/s on-screen GP0(68h) starfield dots, `gpu_share`~0.8 (not empty clip).
  Also: `boot_state_load` forced `pc=entry_pc`, so F1 loads desynced (display
  off; false ~60 FPS). Restored saved PC; batched flat GEO tris in
  `gpu_gl_renderer.c`. Char-select Shift+F1: **~60 FPS locked**, gpu_share~0.06.

- **2026-07-19 (MotK title/char-select — GPU draw-area reject re-applied):**
  Shift+F1 title + Arcade char select were &lt;10 FPS: same OT drain as the
  inter-movie cliff — GP0(E3/E4)=(0,0)-(0,0) + thousands of clipped `0x68`
  dots / quads; GL built 2 tris/prim. Re-applied inclusive draw-area reject
  in `gpu.c` (prior revert blamed a “gap race”; crawl wrap was the separate
  24bpp present-width bug). Alone insufficient for live starfield menus.

- **2026-07-19 (MotK intro — native/hot/inline + multi-run PGO):**
  Shipped `-march=native`, `[recompiler] hot_funcs` for VLC
  `0x8006A9F8`/`0x8006CBE4`, Release-inline `debug_server_log_call_entry`
  (cpu_state.h), HIT-inline `psx_icache_fetch` (psx_icache.h), multi-run
  PGO train (`PGO_TRAIN_RUNS`/`PGO_TRAIN_SECS`). Remeasure clean logo still
  **~51 med** (more mid/high-50 samples; not locked 60). Load-delay cycle
  volume remains the ceiling. Inter-movie cliff open. No MotK VSync HLE.

- **2026-07-19 (MotK intro — PGO + advance_cycles host cost):**
  (1) `psx_advance_cycles`: drop per-charge watchdog/PC-sample (moved into
  `service_to_now`, HARD_CAP cadence); (2) `psx_devices_mmio_sync` recomputes
  deadline in-place instead of dirtying `next_service=0` (was forcing service
  on the next insn after every GPU/CD/MDEC MMIO); (3) MotK intro PGO via
  `scripts/pgo_motk_intro.sh` (`-DPSX_PGO=generate|use`, 311 .gcda). Clean
  logo (until inter-movie cliff): **~49–51 med** (was ~39 LTO-only). Crawl
  after gap recovers ~47–50. Inter-movie ~7 FPS GPU cliff still open. No
  MotK VSync HLE.

- **2026-07-19 (MotK intro — VLC host opts + Release LTO):**
  Host-side work on MotK VLC (`0x8006A9F8`/`0x8006CBE4`), not disc cache:
  (1) idle_skip no longer defeats IRQ fast-path; deferred idle GPR snap;
  (2) IRQ mid-path when bits already pending; (3) `psx_slice_block` header
  inline when parked; (4) main-RAM `psx_cyc_load_word`/`half` inlined;
  (5) MotK Release `CMAKE_INTERPROCEDURAL_OPTIMIZATION_RELEASE` (-flto).
  Logo window: ~34 med → ~39 med (samples mostly 38–40). Still short of 50;
  load-delay cycle volume remains the ceiling (PSX_LOAD_DELAY=0 → hundreds
  FPS). Inter-movie ~5–7 FPS GPU cliff open. No MotK VSync HLE.

- **2026-07-18 (MotK intro — FMV pace: inline cycle advance):**
  Host FPS still short of 50 with real MDEC/XA. Inlined `psx_advance_cycles`
  (deadline fast path) + merged load fudge/cost into one charge; bit-exact
  DC-only MDEC IDCT. Release FMV ~33 med / ~39 avg (steadier; was dipping to
  teens). Gap ~7. Remaining: static VLC `0x8006A9F8`/`0x8006CBE4` + load-delay
  host cost. Do not revive MotK VSync HLE / HARD_CAP without mdec rising.

- **2026-07-18 (MotK intro — 24bpp CRTC width + short-band present):**
  MotK FMV CRTC is 512 (X1/X2÷5); logo centered in 512 RGB (~86..431).
  Reverted blanket 24-bit mode×2/3 (341 cropped the right). Width = GP1(06h)÷
  dot-clock for 15/24-bit. Short GP1(07h)=128 no longer fills 4:3 — present
  letterboxes src_h/240 (GL/SDL/VK). Inter-movie GPU cliff still open.
  CD-only `spu_render` kept.

- **2026-07-18 (MotK intro FMV — false 60 FPS / no video; rollback):**
  MotK `load_accel.vsync_query` + event-horizon_any / HARD_CAP→564480 /
  in-exception VBlank chunking produced host FPS ~60 with **no MDEC**
  (`mdec_decode_count` stayed 0, display disabled) — guest time raced past the
  STR. A/B: VSync(-1) HLE alone is enough to keep MotK MDEC at 0; disabling
  it restores decode/XA. Reverted those accelerations for MotK; kept sticky
  CD IRQ deadline, load-delay coalesce, MDEC DMA bulk/IDCT skips. Real intro
  with video is again ~30–40 FPS host-bound under load-delay. Do not claim
  MotK FMV pace wins without `fmv_state.mdec_decode_count` rising.

- **2026-07-18 (earlier same day — sticky CD deadline + load-path host cost):**
  `cdrom_cycles_to_irq` sticky presented IRQ → 1-cycle deadline after sync;
  fixed. Load-delay coalesce + inline `psx_advance_cycles`. Necessary but not
  sufficient for MotK FMV ≥50 with video.

- **2026-07-11 (Tomba 2 OpenGL full-attract performance + audio acceptance):**
  Resolved the shared renderer/overlay/capture cascade that made Beach, Whoopee
  FMVs, Mines, and Mine Cart slow. OpenGL now avoids mandatory present readback,
  batches Tomba's painter-ordered blend stream, and suppresses unchanged 30 Hz
  source presents. Overlay dispatch now distinguishes exact lazy entries from
  CPS interior continuations: continuations use the loaded range owner first,
  while exact entries reached inside local dirty flow can publish their cached
  native DLL. The hot `0x80106424`/`0x80106688` FMV helpers consequently dropped
  from ~60 interpreted entries/frame to zero. Small dynamic-text DLL images are
  mapped on a bounded worker (141 Tomba variants, not the 712-DLL vault), and
  auto-capture base64/file I/O now runs from a coherent RAM/seed snapshot on a
  low-priority worker. The audio bridge uses real callback duration, bounded
  P-only correction, and a measured 160 ms reserve inside its existing 250 ms
  ring. Release acceptance: 540 s / 107 five-second records, Beach -> Whoopee ->
  Mines -> Mine Cart -> repeat, guest min 59.76 Hz / median 59.94 Hz, **zero
  output underruns**, zero post-start overflows, and no cache growth (849 DLLs).
  Current-code screenshots visually confirmed Beach, FMV, Mines, and Mine Cart.

- **2026-07-10 (Tomba 2 Whoopee auto-skip dwell + native-wide Beach backdrop):**
  Added an opt-in silent-MDEC post-decode hold so presentation-side FMV
  auto-skip remains unpaced through a preloaded logo's authored release wait;
  the faithful guest timeline is unchanged and the default remains four
  vblanks. Added title-opted native-wide mirror gates for flat primitives and
  the textured pre-shaded backdrop phase. This keeps the canonical 4:3 buffer
  untouched while filling Tomba 2 Beach Town at 16:9 and 21:9 without stretching
  the later 3D foreground. Also fixed JSON escaping in the `fmv_state` path and
  extended its resolved-config reporting. Validated Release build, unattended
  first-attract captures at 4:3/16:9/21:9, and zero unknown dispatches.

- **2026-07-02 (HLE PIVOT implemented — HLE as a first-class swappable tier, gbarecomp model):**
  USER-DIRECTED pivot (supersedes "no HLE" §0; CLAUDE.md amended 2026-07-02, memory
  hle_tier_architecture.md). Built the full stack this session: (1) EMITTER —
  full_function_emitter.cpp now emits a null-by-default `g_psx_bios_hle_hook` consult at
  the top of every psx_dispatch_impl iteration (pre-normalize phys, BEFORE the game/
  dirty-RAM/static backends; handled ⇒ resume at $ra; NULL default = pure LLE,
  dispatch-identical). (2) RUNTIME TIER — runtime/src/bios_hle.c(+.h): v1 call-HLE =
  the B0 event family (DeliverEvent/OpenEvent/CloseEvent/TestEvent/EnableEvent/
  DisableEvent) ground-truthed against the SCPH1001 kernel disassembly (Ghidra,
  0xBFC11644..0xBFC11A84; EvCB [0x120]/[0x124], stride 0x1C), operating on the real
  guest EvCBs, callback delivery via psx_dispatch_call with the kernel-true $ra
  0x1720; everything else (WaitEvent/threads/pads/card/A0/C0) falls through to LLE.
  (3) BOOT HLE — one-shot shell-entry intercept (RAM 0x30000; LoadRunShell's indirect
  call always dispatches): real recompiled kernel init + SYSTEM.CNF + EXE load run
  authentically under boot-turbo; only the shell (boot animation) is skipped. The old
  fast_boot snapshot restore is REMOVED (fast_boot=true now aliases boot-skip only).
  (4) SELECTION — [runtime] bios_hle / bios_hle_keep_intro / hle_scheduler in
  config_loader (+ settings.toml bios_hle mirror), PSX_BIOS_HLE / PSX_BIOS_HLE_KEEP_INTRO
  env, startup banner bios_backend=/bios_boot=. PSX_HLE_SCHEDULER spike folded in
  (default via psx_hle_scheduler_set_default, env wins). (5) OBSERVABILITY — always-on
  16K HLE ring (route LLE/HLE/boot-skip) + hle_dump TCP command (../TCP_COMMANDS.md).
  Regen era-consistent: BIOS + Tomba + MMX6 images (emitter changed). NEXT: Tomba
  save+load validation under BOTH backends (user drives); overlay-shard cg-tag refresh
  per title; grow the handler set (UnDeliverEvent, RCnt, A0 libc) with kernel-decompile
  + Beetle checks per handler.
- **2026-07-01 (Tomba pause-menu wedge RESOLVED — stale-recompiler shards, guard shipped):**
  The post-merge Tomba menu wedge (loaded saves only) was NOT the IRQ-resume class the
  prior handoff claimed. Added an always-on exception-EXIT half to irqctx_ring
  (interrupts.c: take_pc/real_epc/exit_pc/exit_reason/same_thread/restored/v1/ra/redirects)
  — it proved every VBLANK resume restores the interrupted GPRs correctly, and the
  0x80016588 "spin" is the normal per-frame vsync wait. Real root cause: autocompiled
  overlay shards were emitted by a recompiler binary (build-t2, 07:39) OLDER than the
  09:28 emitter changes (553d993), yet stamped with the CURRENT cg tag (compile_overlays
  derives the tag from --runtime-include, nothing verified the emitting binary). The
  stale-emitter shards corrupted the display-list task queue (0x801FD800 slots) during
  load-game at Stormy Mountain → menu drew nothing. Repro matrix (compiled/interp ×
  newgame/load), cache-absent A/B, and RAM diff (empty OT 0x8009CA10 vs linked prims
  @0x800Bxxxx) pinned it; recompiler mtime vs emitter commit time was the smoking gun.
  FIXED: rebuilt recompiler, purged + regenerated build-cosim AND build-prod caches —
  menu opens with cache fully enabled. GUARD (class-closing, general): psxrecomp-game
  now bakes the emitter-source hash (shared canonical list
  runtime/codegen_hash_sources.cmake + hash_codegen.cmake) and prints it via
  `--codegen-hash`; compile_overlays.py HARD-FAILS when the binary hash ≠ the tag hash
  (verified positive + negative, both cache and --static modes). Kept the
  same_thread_resume GPR-restore refinement in interrupts.c (ring-verified equal-value
  no-op in practice; faithful). Tooling gaps logged in memory
  (divergence_tooling_gaps_2026_07_01). PENDING: MMX6 cutscene→gameplay gate
  (interrupts.c changed), user validation of prod build (menu + title/save-menu lag —
  lag likely the same stale-shard all-interp fallback + rehash churn).

- **2026-06-27 (device-region MMIO read waits — DONE, branch wt/tomba2-mmio-waits off the
  I-cache tip):** Replaced the placeholder `region = (phys<RAM_SIZE)?3:0` in psx_cyc_readmem
  (memory.c) with the full Beetle MemRW device-region read-wait table (libretro.cpp:859-1131),
  size-aware: main RAM (phys<0x800000) +3; SPU 0x1F801C00-1FFF +36 (32-bit) / +16 (8/16-bit);
  CDC 0x1F801800-180F +6×size; GPU/MDEC/SysControl/FrontIO/SIO/IRQ/DMA/Timers (within
  0x1F801000-113F) +1; BIOS ROM / Expansion-PIO / unmatched +0; scratchpad +0 (early-out).
  Threaded the access size (1/2/4) from psx_cyc_load_word/half/byte + psx_cyc_lwc2_read into
  psx_cyc_readmem (the SPU/CDC waits are width-dependent). The device wait combines with the
  existing +2 completion (+1 LWC2) and fudge exactly as Beetle ReadMemory (LDAbsorb = region +
  completion). RUNTIME-ONLY — psx_cyc_load_* signatures unchanged, so NO emitter regen; just
  rebuild runtime/cyctest. New ruler #2 loops `mmio_timer` (Timer0 read → +3 = 1 dev + 2 compl)
  and `mmio_spu` (32-bit SPU read → +38 = 36 + 2). VALIDATED: cyctest COMPILED (4600) == Beetle
  (4382) EXACT on ALL 15 loops incl. mmio_timer +3 / mmio_spu +38; the 13 prior loops unchanged.
  Tomba 2 boots past the BIOS to its "SCEA Presents" intro splash, total_checks advancing, no
  freeze (the faster-MMIO change did not trigger a device-timing cascade like load=4 did).
  RESIDUAL (documented, unmodeled dynamic axis): DMACycleSteal — Beetle adds the live DMA
  bus-steal count to EVERY read (libretro.cpp:868); non-zero only during active DMA, needs the
  steal count threaded out of the DMA controller, can't be isolated by a static ruler.
  memory.c + gen_testrom.py.

- **2026-06-27 (I-cache fetch — Stage 2 DONE: compiled-path emit + production default-on):**
  Both static emitters now charge the I-cache fetch cost at each cache-line LEADER, BEFORE
  the per-instruction interlock/load (Beetle ReadInstruction order, so a fetch miss clears
  the pending load give-back first). Leader = a block leader / mid-block jump-table target
  (any non-fall-through entry → possibly-cold line) OR a 16-byte-line start (addr&0xC==0);
  intra-line fall-through followers are provably hits (the leader refilled the line to its
  end) so they emit nothing (+0). code_generator (game): `addr` is already the KSEG0 runtime
  PC. full_function_emitter (BIOS): the loop addr is the ROM/compile addr, mapped to the
  RUNTIME guest PC via the existing `relocate_ra` (BIOS main stays in-place KSEG1 0xBFC..
  uncached; kernel Part 2 → 0x500+, shell → 0x80030000+) so the shared TV array evolves
  identically to the interp's cpu->pc and the KSEG1 (>=0xA0000000) uncached test sees the
  true virtual address. The compiled path emits at the SAME address value the interp would
  for the same instruction (they share s_icache_tv), so mixed compiled/interp stays
  consistent. VALIDATED: ruler #2 COMPILED (port 4600, PSX_ICACHE=1) == Beetle (4382) EXACT
  on all 13 loops incl. `icache_miss +14` (was +0 pre-Stage-2); ruler #1 [0x1C5C→0x1CA4]
  steady delta 0 (56==56) AND native now produces the I-cache cold-refill spikes (77/84,
  Beetle's range) that were absent before — exact per-hit magnitude varies run-to-run
  because the two processes free-run (Rule 16), not a bug. Tomba 2 boots past the load wedge
  → intro FMV (jungle) + crisp PS BIOS logo, total_checks advancing, no freeze. Then flipped
  `psx_icache_enabled()` DEFAULT ON (PSX_ICACHE=0 still disables for A/B) — re-validated the
  default-on path (cyctest no-env == +14; Tomba 2 boots clean). psx_icache.c + both emitters.
  NEXT axis: DMA cycle-steal / device-region MMIO load waits (SPU +36 etc.), currently
  unmodeled. Eventually merge wt/tomba2-load-accuracy to master after cross-title regen+smoke.

- **2026-06-27 (I-cache fetch — MODEL built + interp-validated EXACT; Stage 1 of 2):**
  New runtime/src/psx_icache.c: faithful direct-mapped (4 KB / 256-line) instruction-cache
  fetch cost, transcribed from Beetle PS_CPU::ReadInstruction — HIT +0 (no give-back clear),
  KSEG1/uncached +4, cached miss +3 + refill from the missing word to the line end (earlier
  words stay invalid), miss clears the load give-back. Mirrors only the per-word TV tag array.
  Wired into the dirty-RAM interp (exec_one) per instruction, charged BEFORE §1 (Beetle order).
  New ruler #2 loop `icache_miss` (loop top + victim 0x1000 apart alias the same line → refill
  miss every iteration). VALIDATED interp vs Beetle (PSX_FORCE_INTERP=1 PSX_ICACHE=1):
  icache_miss native +14 == Beetle +14; the other 12 loops unchanged at +0 fetch. So the
  hit AND refill-miss costs are MEASURED equal to the oracle on the interp path. Opt-in via
  PSX_ICACHE=1 (default OFF) — charging fetch in only one backend would fork mixed
  compiled/interp timing. Default-off → no production change (Tomba 2 FMV/logo verified
  byte-identical). Commit 958a928.
  STAGE 2 (pending): emit psx_icache_fetch at each cache-line leader in BOTH static emitters
  (code_generator + full_function_emitter), using the RUNTIME address (handle ROM->RAM
  relocated shell code); flip PSX_ICACHE default on so both backends charge it; validate
  ruler #1's cold first-hit spike (Beetle 84/77 vs steady 56) reproduces on the compiled
  path. RISK: the compiled cache state must match Beetle cycle-for-cycle across the whole
  boot to reproduce the cold spike — a careful cache-state-fidelity validation.

- **2026-06-27 (interp-path Δ-ruler — INTERP == Beetle EXACT on all 12 components):**
  Closed the last validation gap: the dirty-RAM INTERPRETER is now MEASURED equal to the
  oracle, not just shared-by-construction. New tooling: `PSX_FORCE_INTERP=1` makes
  `dirty_ram_is_dirty` (memory.c) report all RAM above the kernel window dirty, so the
  dispatcher routes clean compiled game text through the dirty-RAM interpreter (the same path
  overlays take) — no emitter/dispatch change. Launch psx-cyctest with the env set; the test
  ROM runs interpreted (dirty_ram_insns → hundreds of millions). measure.py --port 4600
  (interp) vs 4382 (Beetle): ALL 12 loops match EXACTLY (baseline/alu/load/load2/load_use/
  div/div_spaced/mult/gte_rtps/gte_nclip/gte_read_use/ld_div). Commit b0391bc.
  TWO PROCESS LESSONS (cost real time — now in cyctest README): (1) launch psx-cyctest via
  PowerShell Start-Process — a bash '&' launch fails to boot (pc=0); (2) sample cyc_watch /
  freeze_check AT STEADY STATE — an early query (before the BIOS boots to the EXE entry)
  reports dirty_ram_insns=0 / warm-up values. That premature-sampling artifact was the entire
  "dispatch paradox" I chased (the interp engages only after the EXE entry is reached).
  NEXT axis: I-cache fetch (ruler #1 84/77 cold-refill spikes).

- **2026-06-27 (GTE-read + MFC0 + muldiv give-back — IMPLEMENTED + VALIDATED, ruler #2 100%):**
  Closed the last steady-state divergences. KEY METHODOLOGY FINDING (Rule 15): Beetle's
  cyc_watch must be sampled at STEADY STATE — its boot/warm-up window reports the
  no-give-back value, which is why earlier sessions mis-recorded gte_rtps as "+15 EXACT"
  (true steady = +11). Added ruler #2 probes (load_use, gte_read_use, ld_div) to Δ-gate it.
  Shipped: `psx_gte_read` (MFC2/CFC2: stall to gte_ts_done AND arm ld_absorb=stall/
  ld_which_t=rt give-back; MTC2/CTC2 keep stall-only `psx_gte_stall`); MFC0 arms
  ld_absorb=0/ld_which_t=rt (suppresses a following load's fudge); `psx_muldiv_stall` now
  CONSUMES read_absorb during the MFLO/MFHI stall + the muldiv_ts_done-1 off-by-one — all
  transcribed from Beetle cpu.cpp:1332-1341/1723-1736, in both emitters + the interp.
  **All 12 ruler #2 loops == Beetle at steady state** (gte_rtps 18→14, gte_nclip 11→7,
  gte_read_use 19→14, ld_div 45→49 fixed; the 8 CPU-load/alu/div/mult loops held); ruler #1
  delta 0; Tomba 2 FMV plays (no regression). The R3000A load-delay + GTE/muldiv interlock
  is now hardware-faithful across every micro-benchmark. NEXT axis: I-cache fetch (ruler #1
  84/77 cold-refill spikes). Commits on wt/tomba2-load-accuracy (unpushed).

- **2026-06-27 (load ReadFudge/LDAbsorb — IMPLEMENTED + VALIDATED, both rulers exact):**
  Shipped the shared per-instruction R3000A load-delay interlock. New `runtime/include/
  psx_cyc.h`: §1 base + GPR_DEPRES + DO_LDS (`psx_cyc_step`) as static-inline helpers over
  new CPUState fields `read_absorb[33]/read_absorb_which/read_fudge/ld_which_t/ld_absorb`;
  `psx_cyc_load_word/half/byte` + `psx_cyc_lwc2_read` in memory.c do the Beetle ReadMemory
  timing (clear give-back, +2 fudge iff predecessor committed no load, region RAM +3 +
  completion +2/+1 as the LDAbsorb give-back, scratchpad +0). The pure dep/res classifier
  `psx_cyc_dep_res_mask` (transcribed from Beetle per-opcode GPR_DEP/RES) lives in
  psx_instr_cost.h. Wired into the dirty interp + BOTH static emitters (code_generator game,
  full_function_emitter+strict_translator BIOS); loads now route value reads through the
  UNCHARGED psx_read_* (cpu->read_* rewired in main.cpp; the flat +4 charge_main_ram_read is
  gone). **Δ-validated against Beetle:** ruler #2 `load2` +10 → **+11** == Beetle, every other
  component still exact (alu+1/load+5/div+38/mult+15/gte_rtps+15/gte_nclip+8); ruler #1
  [c5c→ca4] 54 → **56** == Beetle steady-state (84/77 spikes = I-cache cold refill, P2). Tomba2
  boots to the intro FMV (screenshot pixels, no regression). Builds clean (tools/BIOS/game/
  runtime/cyctest). FOLLOW-UP (separate commit): GTE-read/MFC0 give-back + muldiv-stall
  give-back consumption (don't affect rulers; needed for mixed-code faithfulness). Supersedes
  the "MODEL NAILED, impl pending" entry below.

- **2026-06-27 (load ReadFudge/LDAbsorb — MODEL NAILED empirically, impl pending):**
  Derived the last load-path component (the residual on both rulers) by measuring
  Beetle's PER-INSTRUCTION cost via adjacent-PC region cyc_watch. Confirmed:
  fudge = +2 iff the previous instruction committed no pending load (ReadFudge=0x20;
  `(reg>>4)&2` is 0 for all real regs), else 0; region+completion=5 (LDAbsorb excludes
  fudge); the load-delay-slot instruction does NOT absorb (its §1 precedes its DO_LDS),
  the instructions after it do. Per-instruction Beetle data: load = lw7/addiu1/bne0/nop0;
  load2 = lw7/lw6/addiu1/bne0/nop0. Full model + implementation spec in
  `accuracy/load_readfudge_ldabsorb.md`. Implementation is pervasive (per-instruction
  ReadAbsorb + GPR_DEP/RES in both emitters + interp) → a focused next task on a clean
  tree; validate via the ruler-loop anchors (baseline 3 / load 8 / load2 14). No code
  changed this step (read-only empirical derivation).

- **2026-06-27 (interp-path cycle ruler — enabler DONE + validated):** The dirty
  interp now emits `debug_server_cyc_observe(pc)` per instruction (gated), so
  interp-executed PCs are cyc_watch-anchorable (were not). Validated: a live
  Tomba2 overlay interp loop (0x8010724C) records stable cyc_watch hits at 38
  cyc/iter, parity with compiled-PC anchoring; FMV no-regression over 150M+
  interp insns. Commit fc85d8b. This lets interp-side cycle work (the muldiv +
  GTE stalls) be MEASURED, not just by-construction. REMAINING for a fully
  isolated single-component interp ruler: the cyctest harness does not route
  indirect jumps to the dirty interp (a jalr to a scratch dirty address left
  dirty_ram_insns=0 there), so a clean dirty-RAM component loop needs cyctest
  interp-dispatch wiring (or an overlay_cache=off Tomba2 component anchor).

- **2026-06-27 (GTE per-command completion-stall — VALIDATED EXACT):** Modeled
  GTE (COP2) command latency + stall-on-COP2-access. New CPUState.gte_ts_done;
  a GTE command arms it (now + cost-1, serializing back-to-back ops); any COP2
  reg access (MFC2/CFC2/MTC2/CTC2/LWC2/SWC2) stalls to it. Cost table
  (psx_cycles.c) transcribed+verified from beetle gte.cpp op returns (note
  AVSZ4=5 not the psx-spx-doc's 6). Set armed in the shared gte_execute (both
  backends); stall emitted at every COP2 reg-access site in both emitters + the
  interp (offset cancels like muldiv). Added gte_rtps/gte_nclip loops to ruler
  #2: native +15/+8 == Beetle +15/+8 EXACT; all other components unchanged;
  Tomba2 boots to FMV no-regression. Commit ec1fd76. Required regen. UNPUSHED.

- **2026-06-27 (dirty-interp mult/div completion-stall — backend parity):**
  Completed the mult/div stall to the SECOND backend. The dirty-RAM interpreter
  (Tomba2 overlays) charged 0 for mult/div while the compiled emitters already
  set `muldiv_ts_done` + stall MFHI/MFLO — an inter-backend cost inconsistency
  that drifts the shared guest-cycle timeline. `dirty_ram_interp.c` now mirrors
  the compiled emitter exactly via the shared helpers (MULT→`psx_mult_latency_s`,
  MULTU→`_u`, DIV/DIVU→37, MFHI/MFLO→`psx_muldiv_stall`), under
  `PSX_ENABLE_BLOCK_CYCLES`. The interp charges base after exec_one (vs compiled
  "+1 at top") but the set/stall offset cancels (verified algebraically). The
  latency VALUES are already oracle-EXACT on rulers #1/#2 (compiled path); this
  makes the interp apply the identical model. Validated: Tomba2 boots to FMV,
  no regression. Caveat: validation is by-construction + no-regression, NOT a
  direct interp Δ — interp emits no cyc_observe and the testrom isn't an overlay,
  so a true interp-path ruler (interp cyc_observe + force-interp routing) is
  future tooling. Commit 75d5d1a, runtime-only, no regen, UNPUSHED.

- **2026-06-27 (load=4 boot wedge RESOLVED — faithful guest-cycle pad ACK):**
  The oracle-accurate load wait-state (=4) had deterministically wedged Tomba 2
  boot in the BIOS shell (handle s1=104 → 1672-stride table index → wild ptr
  0x8013B608 → RAM corruption → pc=0). Step A (confirm, not hypothesise): the
  proximate runaway was **100% controller (pad) polling** — `sio_irq_dump` showed
  the last 150+ SIO IRQs all `source=pad, delay=4, active_device=PAD, mc_state=0`
  (card idle), NOT the memcard enumeration the handoff guessed. Source-confirmed
  unfaithfulness: the pad fast-path (`sio.c:1386`) armed the access-paced
  `sio_irq_countdown=SIO_IRQ_DELAY_PAD(4)`, decremented once **per SIO register
  access** (sio_tick is only ever called cycles=0), so pad ACK→IRQ7 was
  access-count-paced, not guest-cycle-paced; the faster (accurate) CPU fired it at
  the wrong guest-cycle phase vs the cycle-paced timers/VBLANK → BIOS pad-detect
  state machine diverged. Step B (faithful fix): the pad fast-path now arms the
  **guest-cycle-paced ack scheduler** (`sio_pending_ack`/`sio_ack_remaining =
  BAUD+ACK = 1258 cyc`, driven by `sio_advance`←`psx_advance_cycles`), identical
  to the already-faithful card path. RESULT: load=4 boots **past the wedge to the
  intro FMV** (screenshot-verified, frame 11k+ stable). Ruler #1 native 54 vs
  Beetle 56 = the known load-ReadFudge gap on the load=4 branch, NOT a regression
  (SIO timing can't change CPU instruction cost). Runtime-only (`runtime/src/sio.c`),
  no regen, UNCOMMITTED. Write-up: WEDGE_load4_shell_rootcause.md. Follow-up
  (completeness, non-blocking): axis5 Fix-6 / "1.0e-e2" fully removes the pad
  fast-path so pad+card share one shifter path — needs menu input validation.

- **2026-06-27 (BIOS emitter muldiv stall — ruler #1 now EXACT):** Applied
  per-instruction cycle charging + the mult/div completion-stall to the BIOS
  emitter (full_function_emitter.cpp: +1 at the top of every in-function
  instruction + the 4 inlined orphaned-delay-slot sites; block-up-front charge
  off in per-insn mode) and StrictTranslator (MULTU/DIV/DIVU → psx_muldiv_set,
  MFHI/MFLO → psx_muldiv_stall). RESULT: ruler #1 [0x80001C5C→0x80001CA4] native
  30→56 == Beetle 56, STEADY DELTA 0 — EXACT. Both rulers now match the oracle for
  mult/div (ruler #2 game-side already exact). FMV no regression (i_stat 0x8D,
  full frame). Commit 180b821. The +1-at-top convention cancels the divu-set /
  mflo-stall offset identically to the game emitter (both exact). NEXT: I-cache
  fetch (ruler #1 residual = Beetle's 84-on-cold-hit refill spikes vs native flat
  56); then load wait-state calibration (memory.c +6 → ReadFudge model); then GTE.

- **2026-06-27 (RULER #2 closed + mult/div completion-stall VALIDATED EXACT):**
  Built the full cycle micro-benchmark harness (ruler #2) and used it to land the
  biggest Stage-2 component.
  - **ruler #2 = `tools/cycle_testrom/`**: hand-encoded PS-X EXE of single-component
    isolation loops (baseline/alu/load/load2/div/div_spaced/mult), each measured by
    consecutive-anchor Δ = one iteration; baseline subtraction isolates the cost.
    Both backends boot the SAME synthetic disc (mkpsxiso; license region extracted
    from an OWNED disc via dumpsxiso — LOCAL ONLY, gitignored). Beetle loads it via
    --disc; native via a dedicated psx-cyctest runtime target (boots disc, serial
    CYCT-00101 so disc-identity matches). measure.py compares per-component costs.
  - **Beetle ORACLE costs** (the HW targets): baseline 3, alu +1, load +5, load2
    +11 (2nd load +1 = ReadFudge), div +38 (~36 stall), div_spaced +38 (fillers
    ABSORBED), mult +15 (~13 stall).
  - **MULT/DIV completion-stall IMPLEMENTED + VALIDATED EXACT.** MULT/MULTU/DIV/DIVU
    set CPUState.muldiv_ts_done = now+latency (DIV=37; MULT via MULT_Tab24 14/10/7
    on operand magnitude); MFLO/MFHI stall guest cycles to the deadline
    (psx_muldiv_set/stall in psx_cycles.c). Native previously charged ZERO. Required
    PER-INSTRUCTION cycle charging (PSX_CODEGEN_CYCLE_PER_INSN) — now the DEFAULT on
    this audit branch — so the stall absorbs (the running cycle count must be
    accurate mid-block; block-up-front can't). Game emitter emits set/stall at the
    op sites. RESULT vs oracle: div +38==+38, div_spaced +38==+38 (absorb correct),
    mult +15==+15 — ALL EXACT. Tomba 2 still reaches the FMV (no regression).
  - **Load double-count fix** (earlier today): psx_instr_base_cycles reverted to
    pure execute base (loads=1); memory.c owns the data-access wait-state.
  - Commits 9cec60a, 2b5ad88, 47bcfec, a3e8f28 (+ cyc_watch dedupe). NOT pushed.
  NEXT: (1) calibrate memory.c load wait-state (native +7 vs Beetle +5: flat +6 →
  ~4 + a ReadFudge term). (2) Apply per-instruction mode + muldiv stall to the BIOS
  emitter (full_function_emitter.cpp) + dirty interp → closes ruler #1's div-stall
  gap (still 30 vs 56). (3) GTE per-command cycles (same stall mechanism, gte.cpp
  table). (4) I-cache fetch. Each Δ-gated on the rulers, FMV-verified.

- **2026-06-26 (RULER #1 BUILT + load double-count bug found & fixed):** Built the
  game-independent BIOS-kernel cycle ruler the §3c "TOOLING NEXT" called for, and
  it immediately paid off. Details:
  - **New oracle-model doc `CYCLE_MODEL_BEETLE.md`** — transcribed the full R3000A
    cycle model verbatim from in-tree Beetle cpu.cpp (base +1/insn minus load-delay
    absorb; I-cache fetch +0 hit / +4 KSEG1 / +3+refill miss; ReadMemory loads
    scratchpad=0/region-wait+2, posted stores; mult 6-13 / div 36 stall-on-MFHI/LO;
    GTE per-command table). This is the calibration ground truth.
  - **cyc_watch double-fire FIXED** (debug_server.c): observe was called from BOTH
    the dispatcher (trace_dispatch) AND the function prologue (log_call_entry) at the
    same cycle → every dispatched entry double-recorded. Added (phys,cycle) dedupe.
    Real tooling bug (Rule 15); native deltas were corrupted before this.
  - **Per-block-leader cycle observe ADDED** (full_function_emitter.cpp →
    debug_server_cyc_observe, #ifndef PSX_NO_DEBUG_TOOLS so prod = zero overhead).
    Native previously observed only at FUNCTION ENTRIES; now it samples at EVERY
    compiled block leader, matching Beetle's before-every-instruction sample. This
    lets cyc_watch anchor ANY block-leader PC (interior loop tops, prologue exits) →
    a clean KNOWN-instruction region on both backends. Emitted at normalize_address()
    (runtime phys) so relocated-kernel anchors match.
  - **THE RULER:** BIOS kernel EvCB-search fn at guest 0x80001C5C (relocated ROM,
    identical in every PSX title). Region [0x80001C5C→0x80001CA4] (18-insn prologue,
    contains divu+mflo + 2 RAM loads, no MMIO/GTE). Both backends now record it.
  - **BUG FOUND — loads double-counted.** Native [c5c→ca4] = 34, fully decomposed:
    block c5c advance 20 (=14×1 + **2 loads×3**) + block c9c 2 + **memory.c +6×2 = 12**
    = 34. The Stage-2 #1a commit (2ef47bd) made psx_instr_base_cycles return 3 for
    loads (+2 data-access) WHILE memory.c's charge_main_ram_read already charged +6
    per main-RAM read — the load data-access cost was counted TWICE. The opaque
    0x80017FC4 window hid this because the load over-charge masked the entirely-
    unmodeled divu→mflo stall (~30 cyc Beetle, 0 native). **FIX:** reverted
    psx_instr_base_cycles to pure execute base (loads=1), per the header's own stated
    "data access charged separately in the memory path" contract. memory.c is the
    single address-keyed owner (like Beetle's ReadMemory). Regen BIOS+game, rebuild.
  - **RESULT:** native [c5c→ca4] 34→**30** (exact: 16+2+12), dead stable. Beetle 56
    steady (84 cold = I-cache line refill). FMV still streams (i_stat 0x8D, no
    regression). The remaining −26 gap is now HONEST and decomposed: native is
    missing the divu→mflo execute stall, and memory.c's flat +6/load needs Beetle
    calibration. NEXT: isolate those two components — the BIOS prologue combines
    div+loads in one block (leader anchors can't split them), so the principled next
    step is **ruler #2 (HW test ROM, Amidog)** for hand-crafted single-component
    isolation loops (div-only, load-only), per the user's "do both rulers /
    completeness not convenience" directive. Then Δ-gate each EXECUTE-latency
    component (mult/div, GTE) into psx_instr_base_cycles and CALIBRATE memory.c's
    wait-state per region. All on wt/tomba2-cycle-audit, uncommitted.

- **2026-06-26 (measure: Beetle cycle clock BUILT + VALIDATED):** Added absolute
  guest-cycle exposure to the Beetle oracle (MAIN checkout, additive diagnostic):
  beetle-psx/libretro.cpp accumulates per-frame `timestamp` (CPU->Run slice) into
  `beetle_total_guest_cycles` (+ reset on init) with `extern "C"
  beetle_core_get_guest_cycles()`; runtime/src/beetle_debug_server.c h_ping now
  reports `guest_cycles`. Rebuilt beetle static lib + psx-beetle. VALIDATED (Rule
  0): guest_cycles advances ~565,022 cyc/frame = real PSX rate (33.8688MHz/~59.94).
  Beetle needs the .CUE (not raw .bin). FIRST CROSS-CHECK: native psx_cycle_count
  rate = 565,470 cyc/frame vs Beetle 565,022 (within 0.08%) => gross cycle-rate
  parity confirmed; remaining drift is fine per-instruction-path (needs same-PC
  alignment). Main-checkout Beetle edits are UNCOMMITTED (additive; master has
  other prior uncommitted work — leave for user to manage).
  NEXT (aligned comparator): Beetle has get_registers (PC) but NO run-to/step/pause,
  so same-PC cycle comparison needs a "capture guest_cycles when guest reaches PC X"
  hook on BOTH servers (native has run_to_frame/step; Beetle needs a PC-watch). Then
  diff cycles@PC native vs Beetle to see the residual drift, and Stage-2 cost
  transcription verified against it.
- **2026-06-26 (P3 step 1 DONE — single-source cost seam, identity):** Created
  runtime/include/psx_instr_cost.h `psx_instr_base_cycles(insn)` (identity, 1/insn).
  Routed BOTH backends through it: interp (exec_delay_slot, dirty-dispatch loop,
  precise-slice) + recompiler (code_generator.cpp sums it per block + outside
  delay-slot clone, folding into the compile-time block charge). PROVEN behavior-
  preserving: regen byte-identical (full.c + dispatch.c diff = empty) and Tomba 2
  still streams the FMV (i_stat 0x8D). Commit b00b81f. Stage-2 now edits ONLY this
  one function. ACCURACY_BURNDOWN.md added (all-axes burndown; axis-5 peripherals,
  esp. SIO/controller hybrid-pad bug, flagged weakest), 09a5d45.
  NEXT (measure before Stage-2 costs — don't guess): build the native↔Beetle cycle
  comparator. Feasibility CONFIRMED: beetle_debug_server.c (in worktree) already
  exposes beetle_get_frame_count via the beetle glue — add a parallel
  beetle_get_guest_cycles. Sub-steps: (1) find mednafen's running master-cycle
  timestamp in beetle-psx/mednafen/psx (psx.cpp PSX_Update / the CPU
  pscpu_timestamp_t accumulator — note it's slice-relative, must accumulate to an
  absolute guest-cycle count); (2) add a C accessor through beetle_libretro.cpp +
  a `guest_cycles` debug command; (3) rebuild Beetle static lib + psx-beetle
  (slow: `cd beetle-psx && make platform=mingw_x86_64 STATIC_LINKING=1
  HAVE_LIGHTREC=0 -j8`); (4) comparator: native psx_cycle_count (already in
  freeze_check) vs Beetle guest_cycles at same-PC convergence. THEN transcribe
  Stage-2 costs (mult/div, GTE table, mem wait-states) one at a time, each verified
  by this comparator. Native cycle side already exists; Beetle side is the gap.
- **2026-06-26 (holistic cycle-model audit, post-P2):** Audited ALL cycle-charging
  sites for the dominant class (delay-slot undercount) + cost-model consistency:
  - GAME + OVERLAY emitter (code_generator.cpp `translate_basic_block`): FIXED in
    P2 (block_exec_cycles +1 for outside delay-slot clone). Overlay/alias path
    shares translate_basic_block → covered.
  - BIOS emitter (full_function_emitter.cpp): NO undercount — different model. It
    emits delay slots IN-LINE at their real address (charged by the owning block
    via block_cycles count to next leader) and defers the branch via
    psx_taken_/psx_delay_ flags, rather than emitting an uncounted clone. So the
    delay-slot-is-leader case charges correctly. No change needed.
  - INTERP (exec_one callers): charges psx_advance_cycles(1u) per instruction
    (3 sites). 
  => The cost MODEL is "1 cycle/instruction", duplicated in 3 places (interp hard
  1u; game emitter instruction_count; BIOS emitter leader-to-leader count). They
  agree (Stage-1 backend-equivalent) but are NOT a shared function and NOT HW-
  accurate (Stage-2). recompiler CAN include runtime headers (already includes
  ../../runtime/include/ws_backdrop_detect.h) → a shared psx_instr_base_cycles()
  header is feasible for P3.
  NEXT CORRECTNESS STEPS (deliberate, not tail-of-session):
  1. MEASURE FIRST (don't guess HW costs): native exposes psx_cycle_count already;
     build the Beetle half — add additive guest-cycle exposure to the Beetle oracle
     (main checkout beetle_debug_server.c) + a native-vs-Beetle cycle/first-
     divergence harness (find_divergence.py is STALE/DuckStation-era port 4371 —
     replace with a Beetle 4382 comparator). This is the holistic correctness
     instrument; it makes drift visible for ALL code/titles, FMV being one measure.
  2. P3 shared psx_instr_base_cycles() seam (identity first → byte-identical regen
     proof → then Stage-2 real R3000A costs calibrated against the measure).
  3. P6: regress other titles (breaking is OK per Rule -1; just know), delete
     Tomba2 overlay_native_block.
  COMMIT: f9d50d7 on wt/tomba2 (local, not pushed, not merged to master).
- **2026-06-26 (P2 DONE — Tomba 2 reaches the intro FMV):** Implemented the
  delay-slot cycle-ownership fix in code_generator.cpp (translate_basic_block):
  `block_exec_cycles = instruction_count + (exit branch sits AT end_addr with a
  delay slot outside the block ? 1 : 0)` — charges the always-executed delay-slot
  clone that was previously uncounted (the -8 undercount). Applied to BOTH the
  slice budget and the block cycle charge. Regen + build clean. RESULT: native
  progresses past the frame-1824 logo-delay loop; screen animates; i_stat shows
  CDROM+DMA+SIO active; screenshot = the lush jungle intro FMV. The multi-week
  logo stall is GONE via the faithful fix (no hack, overlay_native_block untouched
  for now). Mechanism was structurally confirmed (instruction_count excludes the
  outside delay-slot clone) before the change; end-to-end confirmed by FMV
  screenshot. NEXT: P3 (shared per-instruction cost fn + MMIO segmentation), P6
  validation (delete overlay_native_block; regress other titles), and Stage-2 HW
  cycle calibration vs Beetle/psx-spx (current model is 1 cycle/insn = backend-
  equivalent, NOT yet hardware-accurate). Apply the same delay-slot fix to the
  BIOS emitter (full_function_emitter.cpp) and overlay/alias paths.
- **2026-06-26 (earlier):** Diagnosis corrected (timing-faithfulness, not take-point).
  Directive persisted (CLAUDE.md Rule -1, memory, MEMORY.md banner). Precise
  slicing root-caused (mid-function clean-text resume not dispatchable) + ChatGPT-
  validated fix (all block leaders = CPS continuations) — PARKED default-off;
  `psx_game_is_function_entry` predicate + slice-trace diagnostics + env toggle
  `PSX_PRECISE_SLICE` left in tree (inert). −8 mechanism located in
  code_generator.cpp (delay-slot-is-leader undercount). Tree builds + boots clean.
  NEXT: P1 (cycle-audit) → P2 (delay-slot ownership fix).
