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
