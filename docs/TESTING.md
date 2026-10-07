# Testing

## Original WAV recovery and reviewed registration removal (2026-10-06)

The sample editor now provides **Save retained input WAV**, **Review input removal** and **Remove reviewed input** for the selected Current receipt. Original-input recovery is separate from decoded preview WAV export. It freshly verifies Current ownership and exact file bytes, independently checks RIFF/chunk extents and mono signed16 PCM frame/rate fields, and downloads the original bytes without normalization. Unknown bounded chunks and their padding remain intact.

Removal uses the existing reviewed command/history service. Review and Discard preserve registration and native data; Remove commits one metadata history entry while keeping the WAV file on disk. The native-bound selected receipt cannot be removed until its native binding is cleared. Removal proposals lock input selection and competing drafts; malformed/stale responses or mismatched hashes fail recovery. Save/Open and Undo continue to validate retained files. These controls recover Current registrations; browsing frozen historical Build WAV sidecars still needs editor integration.

Six focused Node suites passed: recovery RIFF/hash/removal contracts, sample editor contracts/lifecycle, source bank, bank authoring, sequence authoring and source audition. Unreviewed removal is disabled; active native input removal is disabled. A fresh muted headless editor run passed exact original WAV download, unchanged state after download/review/discard, reviewed unused-input removal, Undo, preserved native bank/sequence/sample bindings, and wide/400px layouts with no page errors. Screenshots were inspected. The original file remained exact on disk, and the restored registrations/native entry survived Save/Open. The first browser run used an incorrect Undo-button wait after undoing its only command; the corrected fresh run passed. Private evidence: `local-output/sdk-20260909/audio-sample-recovery-20261006/pass2/` (`proof.json`, `browser.log`, `recovered.wav`, `wide.png`, `narrow.png`) and the preserved initial log.

No new native asset family or runtime behavior was introduced, and no native Build was run for this UI recovery checkpoint. Gameplay verification remains deferred. No game launch, runtime attachment, mod installation or full-disc export occurred. The broader SDK goal remains active and work stays solo.

## Native sample import and waveform editor (2026-10-06)

The Audio Asset Database bank inspector now exposes `Source sample spans` → `Edit sample N`. Its separate editor shows Retail, Current and reviewed Proposed waveform layers. Mono PCM WAV upload has local draft, source review and explicit retention; retention preserves input bytes without applying native data. Existing qualified receipts can then be reviewed for native Apply. Reviewed retail restoration clears only the selected sample. Discard, no-op handling, refresh and shared project history keep these steps distinct.

Each layer loads freshly qualified PCM, verifies its hash and amplitude bins, and requires an explicit preview rate before Play or WAV export. Preview playback uses 20% amplitude, zero initial predictor history and one decoded prefix without loop replay. Changing drafts/layers/rates, mutation, stale state and closing release playback ownership; the source inspector disposes its sample child. Client contracts independently qualify receipt identity/extent, upload-byte hashes, source/carrier ownership, full entry hashes, exact sample audit fields, changed-byte bounds, unchanged flag/tail ownership, PCM hashes/envelopes and encoded error bounds. Rate remains a preview choice, not native pitch or audible-game acceptance.

Five Node suites passed (new sample contract/lifecycle plus source bank, bank authoring, sequence authoring and source audition regressions); affected JS/Python syntax and diff checks passed. The actual muted headless editor workflow passed WAV Review/Retain, native Review/Apply/Clear/Undo, no-op, nonmutating review/discard, all three PCM layers, explicit-rate playback, parent/child disposal and wide/400px layouts with no page errors. Screenshots were inspected. Its first run exposed a global canvas-height collision with action buttons; explicit waveform height fixed it. A fresh final browser rerun also passed the stricter upload/native-audit guards.

Browser-authored edits survived Save/Open with bank parameters, sequence operands and the other sample binding unchanged. A fresh native Build passed independent PCM/error/hash calculations, exact flags/tails and full-entry directory/ZIP readback, one composed overlay, unchanged project inputs, verified Current Build identity and exact frozen WAV sidecars. Native package SHA-256: `316f931f4fe05fc64060e746a77faa9a2dca33cd3a7a3e81cb0f2d1a66837e86`. Private evidence: `local-output/sdk-20260909/audio-sample-native-20261006/editor-2/` (`proof.json`, `native-proof.json`, `wide.png`, `narrow.png`) and final `editor-3/` (`proof.json`, `contract-fixture.json`, `browser.log`). Contract checks use a freshly qualified retail fixture: `node integrations/legaia/tests/test_audio_sample_editor.mjs <fixture.json>`; retail fixtures/PCM are private artifacts.

Runtime pitch/instrument assignment, interpreted envelopes, bank/sequence synthesis, sample allocation changes and game playback remain open. Manual gameplay verification is deferred. No game launch, runtime attachment, installation or full-disc export was performed. The broader goal remains active and development stays solo.

## Fresh sample preview layers (2026-10-06)

`POST /api/audio-sample-preview` exposes bounded mono PCM and waveform metadata for Retail, Current and reviewed Proposed sample layers. Every request binds the full Current authoring identity, original entry and selected sample hash. Proposed additionally requires the operation, freshly recomputed review key and retained receipt for Apply. Clear previews Retail bytes. Exact HTTP fields reject proposed bindings on Retail/Current reads. The response carries PCM/sample hashes and leaves sample rate unspecified; preview clients must choose their own rate.

The retail-enabled HTTP workflow passed Retail/Proposed readback without mutation, Current matching after Apply, proposed Clear matching Retail, stale proposal rejection, wrong sample/review hash rejection and extraneous-field rejection. PCM hashes match reviewed native decoding. This earlier checkpoint provides the preview backend; the subsequent editor checkpoint above integrates sample import/waveform and preview playback controls. No game actions were performed.

## Persistent native WAV samples and shared audio delivery (2026-10-06)

Reviewed retained WAVs now have source-qualified native sample bindings, Retail/Current metadata, fresh Apply/Clear reviews, atomic commands, history, dirty tracking, Save/Open, project copies and Build snapshots. Bindings reconstruct candidates from verified WAV bytes and fresh native source data; historical candidate receipts are not replay authority. Active bindings prevent source-receipt removal. Native sample Undo/Redo validates the proposed bindings and files before changing history.

Bank parameters, sequence operands and multiple samples compose into one overlay per physical PROT entry. Clearing one family or sample preserves the others. Build independently decodes the encoded sample prefix, verifies PCM/error audits, and checks exact allocation, flags, opaque tail and all remaining entry bytes. Authored audio appears once with all family summaries. Empty sample collections preserve legacy identity. Existing bank/sequence editors accept sample-authored Current hashes and preserve samples during reviews and retail parameter restoration.

Twenty retail-enabled Python workflow/regression checks and both affected Node contract suites passed. Fresh fixed-span and relocated Builds each applied two samples, passed independent full-entry directory/ZIP readback, preserved bank/sequence edits and prior authored data, and passed Save/Open and Build verification. Clear made the Build stale; Undo restored input matching. Actual browser bank/sequence Review/Discard and bank retail-restoration review against the sample-authored project passed with unchanged state and no page errors. Fixed package SHA-256: `3dc1fff9b5238d467b1efbcd41927cb59d4622e3c97ad5deed2fe578a64d8a20`; relocated: `ca18caf4733dd4a5033309eed8a3c9c1f17c1021005e7d80aac5f24a823f3106`. Private evidence: `local-output/sdk-20260909/audio-sample-native-20261006/` (`focused.log`, `regression.log`, `proof.json`, `browser-proof.json`).

This earlier native delivery checkpoint preceded the waveform/import editor and Current/Proposed audition implemented above. Only fixed-allocation complete sample prefixes are supported; input WAV rate remains metadata, and runtime pitch, instruments, playback and allocation changes remain unresolved. No game launch, attachment, installation or full-disc export was performed. Manual gameplay acceptance is deferred; the broader goal remains active and work stays solo.

## Reviewed retained WAV inputs (2026-10-06)

Source-qualified WAV review now creates recoverable historical input receipts through exact HTTP/command fields. Retention/removal use history and dirty tracking; Save/Open, copies and export snapshots verify the exact hash-addressed WAV bytes. Normal native Builds preserve WAV-input sidecars keyed by authored input identity, while unchanged native bank/SEQ artifacts can be reused with distinct input receipts. Frozen sidecars remain readable independently of later Current source removal and reject modified files/metadata. Retaining a WAV does not apply its candidate to game data; native sample bindings and shared composition are now implemented in the subsequent checkpoint above; editor preview/import controls are now implemented in the subsequent editor checkpoint above.

Fifteen retail-enabled source/bank/SEQ regression checks plus one frozen-input snapshot check passed. The initial HTTP size failure was fixed with dedicated bounded Review/Retain routes. Fresh before/after native Builds retained exact WAV sidecar bytes and identical bank/SEQ edits/overlay bytes/native ZIP (`d8d4dc95410712ba9fe59ec708a120c0f889dfebae20cae0cc25072582da9647`); Save/Open and Current input receipt verification passed. See [sample authoring and retained inputs](legaia-audio-sample-authoring.md). Private proof: `local-output/sdk-20260909/audio-sample-sources-20261006/`. No game launch, attachment, installation or full-disc export. The goal remains active and development stays solo.

## PCM WAV/native sample codec groundwork (2026-10-06)

A source-qualified mono signed16 WAV-to-SPU-ADPCM codec now replaces a complete bounded sample prefix without changing allocation, loop/end flags, trailing bytes, VAB tables, other samples or SEQ chunks. Predictor/shift trials use closed-loop native integer history and report decoded PCM hash and lossy encoding errors. Input WAV rate is metadata only; runtime rate/pitch and instrument assignment remain unknown. This earlier codec checkpoint preceded the persistent bindings and shared Build composition implemented above. Editor import/preview controls are implemented in the subsequent editor checkpoint above.

All nine focused sample/waveform Python checks passed with no skips. A full sample inventory across 202 qualified banks found 1694 encoded ends, one empty sample and one over the decode budget. The first eligible sample in each of all 202 banks passed encoding, independent integer PCM/error readback and exact flags/tail/non-sample byte preservation. This covers 202 replacements, not every eligible sample; unavailable banks/empty/budget-limited samples remain unsupported. See [sample authoring groundwork](legaia-audio-sample-authoring.md); private evidence is `local-output/sdk-20260909/audio-sample-codec-20261006/`. No game launch, runtime attachment, installation, SDK Build or full-disc export. Development remains solo and the broader goal remains active.

## Bank parameter editor (2026-10-06)

The Audio Asset Database's source bank inspector now opens a separate Retail/Current/reviewed-Proposed parameter editor. Master fields, explicit program slots and packed tone page/record identities expose all 27 qualified native scalar fields. Encoded u8/u16/signed16 bounds, Review/Apply/Discard, retail staging, Clear and refresh use the verified command layer. Source-row actions select the correct slot or packed record. Drafts/proposals lock navigation; stale state withdraws layers, and closing the source inspector disposes its child. Source bank tables, waveform inspection and sample audition remain Retail views.

Eleven retail-enabled Python workflow checks, three Node contract suites and affected-module syntax checks passed. Actual browser Review/Discard, Apply/reload, no-op, retail staging, all three table sections, signed bounds, invalid slot recovery, source-row navigation, Clear/Undo/stale refresh and wide/400px layouts passed with no page errors. Screenshots were inspected. The browser-authored edit survived Save/Open and exact full-entry directory/ZIP native readback with the sequence edit and imported sources unchanged (package SHA-256 `a9424c2b5d6f6bd5699e4c95744e214691e7a27906302f589659d29383990bd2`). See [bank authoring](legaia-audio-bank-authoring.md); private proof is `local-output/sdk-20260909/audio-bank-editor-20261006/`. Instrument assignment, interpreted envelopes, sample replacement/allocation, composition synthesis and runtime playback remain open. No game launch, attachment, installation or full-disc export; development stays solo and the broader goal stays active.

## Persistent VAB parameters and shared bank/SEQ delivery (2026-10-06)

Source-qualified bank parameter editing now has Retail/Current metadata, reviewed atomic commands, history, dirty tracking, Save/Open, project copies, Build input snapshots and native audits. Bank and sequence bindings remain independent; one composed native PROT entry preserves both families. Clear or retail restoration of either family preserves the other, and cross-family changes invalidate old reviews. Shared authored audio appears once in the project asset list. Empty bank metadata preserves legacy document and Build input identity.

The 26 regression checks and six focused bank/composition checks passed; two affected lifecycle/HTTP checks were rerun after integration cleanup. Both fresh fixed-span and relocated Builds passed independent full-entry directory/ZIP readback with all 27 bank fields, sequence edits and prior authored changes preserved. Actual sequence-editor Review/Apply/Clear against a bank-authored project passed with no page errors. The subsequent UI checkpoint adds bank editing controls; these HTTP/command and Build capabilities do not establish audible effects, instrument assignment or runtime playback. See [bank authoring and shared delivery](legaia-audio-bank-authoring.md). Private proof: `local-output/sdk-20260909/audio-bank-native-20261006/`. No game launch, attachment, installation or full-disc export. The broader goal stays active and work remains solo.

## Running the tests

```sh
cmake -S recompiler -B recompiler/build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build recompiler/build
cd recompiler/build && ctest --output-on-failure
```

That is the whole thing. 38 tests, under 5 seconds, and it needs **no BIOS dump,
no disc image, and no generated code** — a plain recompiler build is enough. This
is the check to run before opening a PR.

Until 2026-07-27 no document in this repository mentioned `ctest`, `pytest`, or
how to run a test at all, so the suite was effectively invisible. If you add a
test, add it to `ctest` in the same commit — an unregistered test cannot fail,
and a test that cannot fail is not a test.

> On a memory-constrained machine, parallel builds of this tree can crash
> `cc1plus` while compiling the toml11-heavy `config_loader.cpp`. If
> `cmake --build` dies with no diagnostic, retry with `-j 2` or `-j 1`; the
> failure is resource exhaustion, not a code error.

### Running one test

```sh
ctest -R overlay_guard_codegen --output-on-failure   # by name (regex)
ctest -N                                             # list without running
```

Every test is also a plain executable or script, so you can run it directly:

```sh
./recompiler/build/bios_address_model_test
python recompiler/tests/test_overlay_guard_codegen.py \
       --recompiler "$(pwd)/recompiler/build/psxrecomp-game.exe"
```

> Pass the recompiler as an **absolute** path. A relative path satisfies the
> test's own `os.path.isfile` check but then fails inside `subprocess.run` on
> Windows with `WinError 2`, which looks like a broken test rather than a bad
> argument.

## What the suite covers

| Group | Where | Needs |
|---|---|---|
| C/C++ unit tests | `recompiler/tests/`, `runtime/tests/` | recompiler build |
| Codegen contract tests | `recompiler/tests/test_*.py` | `psxrecomp-game` |
| Runtime source-invariant guards | `runtime/tests/test_*.py` | nothing — they read source |

The source-invariant guards are the cheapest and most useful class here. They
assert structural properties of the runtime (an ordering holds, a fast path is
invalidated, a fallback exists) by reading the source, so they cost milliseconds
and catch whole regression classes without running a game. Registered from
`recompiler/CMakeLists.txt` rather than `runtime/CMakeLists.txt`, because the
runtime tree cannot configure until a BIOS has been generated, and these need
neither.

## Known-failing tests (not registered)

Three tests exist and are **deliberately left out of `ctest`** because they fail
today. They are not registered because a suite with a known-red test is a suite
people stop believing — the exact failure mode that took CI off pull requests in
the first place (see `.github/workflows/cli-release.yml`). Fix or retire them,
then wire them in.

| Test | Status |
|---|---|
| `runtime/tests/test_interpreter_perf_guards.py` | Asserts `psx_devices_mmio_sync` invalidates the inline cycle limit. It does not: the function delegates to `psx_devices_service_to_now()` (which clears `g_psx_cycle_fast_limit`, `psx_cycles.c:161`) **or** to `psx_devices_recompute_deadline()` (`:153-157`), and that second branch never clears it. Needs a timing owner to decide whether the guard found a real hole or the invariant moved. The guard is also partly stale — it still names `s_next_service_cycle`, since renamed to `psx_next_service_cycle`. |
| `runtime/tests/test_runtime_perf_diag_guards.py` | Asserts a substring that is no longer present in the runtime source. Either the diagnostic was removed or it was renamed; the guard has not been updated either way. |
| `runtime/tests/test_overlay_pair_dedup_runtime.py` | Needs its companion harness (`overlay_pair_dedup_harness.c`) built. Unlike the other Python tests it is not source-only, so it needs a build target before it can be registered. |

## Tests that are not in `ctest` and should not be

`runtime/tests/` also holds fixtures and harnesses (`*_fixture.c`, `*_harness.c`)
that are inputs to other tests, not tests themselves. Do not register them.

Several C tests under `runtime/tests/` require a **built runtime**, which
requires a generated BIOS (see [`BUILDING.md`](BUILDING.md)). Those are wired
into `runtime/CMakeLists.txt` and run from `runtime/build`:

```sh
cd runtime/build && ctest --output-on-failure
```

## CI

`.github/workflows/cli-release.yml` runs on `workflow_dispatch` and published
releases only. Its header explains why per-PR triggers were removed on
2026-07-25: the Windows job failed often enough that a red check stopped
carrying information, and a check nobody trusts costs attention without buying
confidence.

That reasoning still holds. The gap it left was that no fast, trustworthy
alternative existed. The `ctest` suite above is a candidate: it is hermetic
(no BIOS, no disc, no network), takes under five seconds, and is currently
green. Restoring a per-PR check on top of it is a smaller decision than
restoring the old one.

## Native SEQ operand codec (2026-10-06)

Run `python -m unittest test_audio_sequence_authoring test_audio_sequence -v` with `PYTHONPATH=.;integrations/legaia;integrations/legaia/tests` and `LEGAIA_DISC_BIN` configured for the local verified USA source. Ten checks passed without skips. The retail test independently constructs expected changed bytes for all 83 carriers and restores exact originals; fixtures exercise channel/tempo widths, running status, partial tails, carrier isolation and rejection. This is serializer verification, not SDK command, emitted Build or gameplay acceptance. See [SEQ operand groundwork](legaia-audio-sequence-authoring.md).

## Persistent audio operands and native delivery (2026-10-06)

Run `python -m unittest test_audio_authoring test_audio_sequence_authoring test_audio_sequence test_build_report test_project_workflow -v` with the same retail environment. All 31 focused checks passed. Private native proofs cover exact full-entry fixed overlay and relocated PROT delivery, directory/ZIP integrity, preserved imported metadata and existing script/animation composition, and stale Build inputs after Clear/Undo. Browser editing controls are pending; these checks do not establish audible game playback. See [SEQ authoring and delivery](legaia-audio-sequence-authoring.md).

## Sequence operand editor (2026-10-06)

Run the Node suites `test_audio_sequence_authoring.mjs`, `test_audio_sequence.mjs` and `test_audio_note_timeline.mjs`; source/current ownership, channel/tempo proposal spans/timing, stale and late-close guards all passed. Nine retail-enabled Python command/HTTP/inspection checks passed. Private browser evidence includes actual source event selection, review/discard, Apply/reload, no-op, Clear/Undo/stale refresh, invalid values, partial inspection, final wide/400px layouts and full native delivery of the browser-authored entry. Source/other authored state is preserved. This does not verify game sequence playback. See [sequence authoring](legaia-audio-sequence-authoring.md).

## Native VAB parameter codec (2026-10-06)

Run `python -m unittest test_audio_bank_authoring test_audio_bank -v` with the retail environment. Nine checks passed without skips/errors/failures. All 202 qualified retail bank carriers passed independently encoded 27-field edits and exact entry restoration. Fixtures cover scalar widths/identities, reserved/sample/opaque preservation, all carrier shapes, Current composition/no-op and rejection. These tests qualify a codec, not SDK commands, emitted native packages or audible playback. See [VAB parameter groundwork](legaia-audio-bank-authoring.md).
