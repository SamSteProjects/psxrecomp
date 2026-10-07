# Legaia SDK validation plan

## Structured ADSR register-word editing - accepted offline (2026-10-06)

**Bank parameter editor -> Packed tone record -> adsr1 / adsr2** now decodes the selected native u16 word into structured envelope fields. ADSR1 exposes attack mode/shift/step, decay shift and sustain-level code; ADSR2 exposes sustain mode/direction/shift/step and release mode/shift. Each Retail/Current/Reviewed Proposed layer displays its decoded fields alongside the raw word. Structured controls stage one local word through the existing source-qualified Review -> Apply command, history and persistence flow. Invalid values block Review; pending controls lock; Discard, Retail staging, raw-word edits and stale/closed views synchronize or withdraw the structured controls. ADSR2's reserved bit 13 stays held by structured edits; intentional raw u16 authoring remains available.

The bit layout and VAB offsets were checked directly against pinned Andrew reference `d6e64c68ede25813d35db20980da82a1a025549b`, `crates/engine-audio/src/spu/adsr.rs` and `crates/vab/src/lib.rs`, with an independent check of `runtime/src/spu.c` register extraction. This is encoded register interpretation, not a synthesized envelope or confirmed runtime instrument. Shift/step codes are not milliseconds; `(sustain-level code + 1) * 2048` is the encoded target formula, not a live counter or normalized amplitude. No runtime SPU implementation, native serializer, persistence format or mutation command changed. The new client helper is served through the editor's explicit static-file map.

Acceptance: all 184 client suites and 183 editor syntax checks passed in 21.01 seconds; all six retail-enabled bank workflow checks passed in 81.98 seconds including runner overhead. Focused client checks use independent bit masks, integer/type rejection, detached decoding, reserved-bit preservation and field/raw/history lifecycle guards. The private muted editor passed actual ADSR1/2 structured editing, invalid/Discard, immutable Review, locked Proposed controls, two Apply commands, Undo stale withdrawal, completed Redo/Refresh, Save and wide/400px layouts with zero page errors or launch requests. The first browser history probe refreshed while Redo was still in flight; its terminal stale-view evidence is preserved separately. The corrected probe explicitly waits for completed history commands and passes.

Save/Open and independent full-entry construction proved that only the intended two tone words changed and all other saved fields/native bytes survived, including the existing Current SEQ/WAV edits. Normal private Build integrity passed; its directory and ZIP overlay both match the entire independently constructed entry, SHA-256 `2763446be4afa339ba8e6a10266e9216a96162608138e2f7f635894c37a60b40`. Package SHA-256 `6f7917476ef60101c3c845abbc5c516ebd0f5c22305af8be6d7108cbac06a3ee`. Build left document/history inputs unchanged; retained runtime/precompile stability source hashes still match their accepted baseline. Evidence: `local-output/sdk-20260909/audio-adsr-editor-20261006/acceptance.json`, `node.json`, `python.json`, `browser.json`, `native-proof.json`, `build-proof.json`, logs and inspected wide/narrow screenshots. No game launch, runtime attachment, mod installation or full-disc export occurred. Audible behavior and runtime assignment remain deferred; the full SDK goal stays active and development remains solo.

## Current note to Retail bank record navigation - accepted offline (2026-10-06)

**Sequence operand editor -> Inspect Current encoded bank links** now opens the exact Retail program slot, packed tone page/row or bounded sample span from each encoded candidate. The source bank inspector focuses one verified record; **Show all source rows** restores the table, including unused program slots. Its existing parameter editor qualifies Retail/Current/Reviewed Proposed separately at the selected tone/slot, and its sample editor remains available at the exact source sample index. Current sample hashes are never substituted for Retail hashes: navigation takes the Retail bank identity from the source Asset Database record and freshly qualifies the bank through the existing API. Missing identities, malformed selections and out-of-range records are refused; no packed-page/program equivalence or runtime instrument assignment is inferred.

Child ownership now follows the sequence editor -> note links -> bank -> parameter/sample/waveform chain. Closing or invalidating a parent disposes its owned child and suppresses late publication; the bank inspector now also owns its waveform dialog and audition. Narrow layouts wrap bank provenance and put the new Retail navigation actions first in the horizontally scrollable candidate table. This adds no persistence format, mutation command, native serializer or runtime write.

Acceptance: all 183 client suites and 182 editor syntax checks passed in 21.39 seconds. Focused regressions cover sparse/unused slots, exact packed row/sample focus, detached targets, malformed/out-of-range refusal, Show all, Current/Retail hash separation, stale input, pending close and child disposal. Both existing retail-enabled Current-note backend checks passed in 16.33 seconds. The private muted editor passed actual Current note -> Retail program/tone/sample navigation, parameter Review/Discard, Current sample-editor entry, 128-slot Show all, waveform inspection, three-level parent disposal and wide/400px layouts without page errors or launch requests. Screenshots were inspected and corrected to keep hashes/actions visible. The first browser attempt reached the correct editor but expected an obsolete status string; its terminal failure evidence is preserved separately before the corrected successful proof.

Fresh native readback and Save/Open proved unchanged project document/history/saved content, complete Current audio entry and Build input key. Retail bank SHA-256 `56ca3b0be30b19b4173f0a42a47bf9da72803f7ae6af3fd78f9829908482ed82` and Current bank SHA-256 `3e2cd444fb6d20a5a650ebe434473482249aa50e4dd39c6ad73433ef0d13b072` were explicitly distinct. Evidence: `local-output/sdk-20260909/note-bank-navigation-20261006/acceptance.json`, `node.json`, `python.json`, `browser.json`, `native-proof.json`, browser log and wide/narrow/parameter screenshots. Retained runtime/precompile source hashes still match their accepted baseline. This is offline editor workflow acceptance; native Build and gameplay revalidation were not required for this navigation-only change. Synthesis, runtime instruments and gameplay remain unverified; the full SDK goal stays active and development remains solo.

## Request-local WAV reference qualification - accepted offline (2026-10-06)

Project-wide asset references now qualify retained WAV inputs and compose Current native sample bindings once per request, then share detached proofs across scene adapters and imported-only comparisons. Previously each imported scene repeated both operations twice; 64 scenes could reconstruct the same project audio bindings 128 times. `sdk/audio_reference_snapshot.py` uses navigation-independent persistent project identity, without a global or persisted cache. Before publication it rereads every retained WAV, verifies each unique original native carrier and bank hash/ownership, and checks project identity again. Scene membership, availability, edge identities, historical/Current proof contracts and runtime limitations stay unchanged. The private snapshot is not an HTTP input or an authoring command.

Acceptance: all 51 affected retail-enabled Python tests passed in 80.98 seconds including runner overhead; all 183 client suites and 182 editor syntax checks passed in 20.76 seconds. New regressions cover a 64-scene request with one native qualification and one carrier recheck, detached evidence, navigation reuse, project mutation, native body/bank/ownership drift, and an actual WAV byte change with file size and modification time held. A fresh Town01/Town0c project produced an exactly identical graph to commit `9abce65`: native qualification calls fell from four to one, with observed query times of 16.63 and 7.19 seconds. These are local measurements, not a general latency guarantee.

The private muted editor passed project Asset Database refresh, historical and Current native/WAV reference navigation, exact WAV download, dialog closure and wide/400px layouts without page errors or game launch requests. Document/history/build inputs stayed unchanged; the five retained runtime/precompile stability source hashes still match their accepted baseline. Evidence: `local-output/sdk-20260909/audio-reference-snapshot-20261006/acceptance.json`, `python.json`, `node.json`, `retail.json`, both graph snapshots, `browser.json`, `server-acceptance.json` and screenshots. This is focused offline reference inspection acceptance; no fresh full Python campaign, native Build or gameplay verification was required for this query-only change. Gameplay verification remains deferred and the broad SDK goal stays active.

## Retained animation translation range offsets - accepted offline (2026-10-06)

**Edit retained content -> Frame sequence tools -> Stage translation offset** now shifts the selected rigid object's X/Y/Z translation across an inclusive output frame range. The base is the effective frozen captured donor plus the current frame mapping and local channel drafts, so inherited axes can be shifted without first authoring every frame. Exact integer deltas use -4095..4095; every resulting axis must fit native signed twelve-bit -2048..2047. Any overflow rejects the entire operation. Zero axes preserve inheritance and do not add channels; rotations, other objects/frames, mapping, opaque channel data, header and trailer remain held. These are native rigid object-local channels, not world-space placement or a general skeleton retargeter.

The source-qualified `POST /api/animation-record-offset` returns a detached recipe and per-axis before/after evidence after frozen donor reconstruction and the existing complete ledger/reference validation. The editor validates exact request identity, counts, arithmetic, draft values, hashes and untouched channels before staging. Pending inputs lock; stale/closed responses cannot publish. Staging clears only the prior Review, never project state. The existing Review -> Proposed pose -> Return -> Apply command updates the retained record and its referring initial assignments atomically, with Undo/Redo and Save/Open. No persistence format or mutation command was added.

Acceptance: the final three retail-enabled offset/existing retained-editor Python tests passed in 104.10 seconds (104.46 seconds including runner overhead), including exact HTTP fields, typed bounds, overflow/zero behavior, immutable staging, native channel/header/trailer readback, unchanged other transforms, Apply/history/reopen and existing active/retired assignment updates. All 183 client suites and 182 editor syntax checks passed in 20.62 seconds. The first discovery run also executed four imported GLB test cases; its six tests passed, and the new test module now imports that fixture module without adding unrelated cases to discovery.

The private muted headless editor passed actual Asset Database navigation, inherited/draft range staging, disabled Apply before Review, Proposed model pose rendering, return, Apply, Save, and wide/400px layouts without page errors or launch requests. The initial proof expected a scene return control before leaving the model dialog; that timeout and its not-applied native state are retained separately. The corrected workflow succeeded. Source imports stayed unchanged; staging left document/history untouched; reopening reproduced the same native bank. The saved and generated record SHA-256 was `cdd948e0f9e843318563d1d4e8908dbc3936f49ddda99bda0896ee552d311319`. A normal private Build produced package SHA-256 `3428d54ffb2830be54e0e0b67f9a012f689d60aff8572a5bc5f3c1f1477d944c`; its animation audit matches the Current bank, the packaged relocation payload hash/size were streamed and verified, and Build left project/history inputs unchanged.

Evidence: `local-output/sdk-20260909/animation-record-offset-20261006/acceptance.json`, `python.json`, `node.json`, `browser.json`, `server-acceptance.json`, `build-readback.json`, and wide/narrow/Proposed pose screenshots. This is focused offline authoring/native package acceptance, not a fresh full Python campaign or gameplay acceptance. No game launch, runtime attachment, mod installation or full-disc export occurred. Gameplay appearance, scheduling and timing remain deferred, and the broad SDK goal remains active.

## Current authored WAV dependencies - accepted offline (2026-10-06)

The retained WAV inspector now separates historical capture receipts from Current authored native sample bindings. Inspection contract `legaia.audio-input-inspection.v2` adds `current_bindings`: native asset/sample, capture and binding scenes, receipt identity, authored binding hash, retail/Current full-entry hashes, Current sample hash and exact native byte span. `sdk/audio_input_bindings.py` qualifies the saved sample binding against retail ownership, reconstructs its reviewed WAV candidate, composes all Current audio edits and checks that the resulting sample bytes match the retained candidate. The global resource/sample budgets remain 32; no runtime voice, bank residency, playback pitch or instrument identity is inferred.

Asset references add `current_native_sample_wav_binding` Effective edges separately from `retained_wav_sample_input` historical Authored edges. The client validates exact endpoint/scene/receipt/hash/span contracts and displays Current byte evidence with runtime usage unknown. The existing reviewed sample Apply/Clear workflow remains authoritative: assigning a WAV adds the Current dependency, Clear withdraws it while retaining historical capture metadata, and Undo/Redo and Save/Open preserve the distinction. No new mutation command or persistence format is introduced.

Acceptance: all 57 affected retail-enabled Python tests passed in 67.33 seconds (67.74 seconds including runner overhead); the added retail test verifies Current entry/sample hashes against reconstructed output, graph layers/proofs, unchanged query state, Clear/Undo/Redo and Save/Open. A fresh final run passed all 182 client suites and 182 editor syntax checks in 20.96 seconds. Three older reference tests now import the module normally so its shared decoder dependency resolves; their original assertions are preserved. The initial ambiguous ready-text assertion and obsolete data-URL loader failures remain recorded as non-green history.

The private muted headless editor proof passed separate Historical/Current sections and hashes, exact WAV recovery, wide/400px layout, close disposal, both graph edge kinds and WAV/native/WAV reference navigation. Project document, undo/redo stacks and authored Build key stayed unchanged. Evidence: `local-output/sdk-20260909/audio-input-current-bindings-20261006/acceptance.json`, `python.json`, `node.json`, `browser.json`, `server-acceptance.json`, and screenshots. No game was launched or attached, no Build installed and no full disc exported. This is offline native dependency acceptance; a fresh full Python campaign and existing manual gameplay gates remain deferred, and the full SDK goal remains active.

## Retained WAV inputs in the Asset Database - accepted offline (2026-10-06)

Retained WAV inputs now have one `audio-input://legaia/wav/<content-sha256>` Asset Database identity per exact blob, shared across historical receipts and imported capture scenes. Inventory and read-only inspection/download verify the canonical project file, mono 16-bit PCM rate/frame extent, receipt ownership, capture-disc identity and fresh project source key. Files are requalified before publication; missing, changed, stale or foreign inputs fail closed. The inspector presents duration, rate, file identity and historical native sample targets, and downloads the exact original bytes after independent client hash/RIFF/PCM verification.

The reference graph records `retained_wav_sample_input` authored edges with receipt, disc, entry, bank and source-sample hashes. Capture targets are unavailable without a qualified catalog entry; conflicting entry hashes reject the graph. Shared blob scene memberships remain explicit. Reference navigation opens the retained file inspector even from active scene scope. These receipts describe historical inputs, not Current native sample assignments, runtime residency or playback pitch.

Validation: all 56 affected retail-enabled Python tests passed in 37.67 seconds, covering inventory, HTTP envelopes, files/provenance, graph availability/shared memberships, existing audio retention/authoring and inspector schema. A fresh final campaign passed all 182 client suites and 182 editor syntax checks in 20.89 seconds, with the required private sample/model/world-map fixtures and the new retail WAV fixture supplied. The private muted headless editor proof passed Asset Database action routing, exact download SHA-256, wide and 400-pixel layouts, close-event disposal, public project-reference readback and WAV/native/WAV reference navigation. Client tests additionally qualify stale contexts, changed receipts, failed metadata comparisons and closed/late responses. Project document, undo/redo history and authored Build key stayed unchanged. Evidence: `local-output/sdk-20260909/audio-input-assets-20261006/acceptance.json`, `browser.json`, `server-acceptance.json`, `node.json`, and wide/narrow screenshots. Earlier proof setup failures are preserved separately. No game was launched or attached; manual gameplay remains deferred.

The full Python baseline below remains the accepted 1,756-case campaign at `6f51eaa`; this feature adds eight tests and has focused Python acceptance, not a new full Python campaign. The SDK goal remains active, with general runtime/interpreter, synthesis/instrument semantics, MAPDSIP/world-map and deferred gameplay acceptance still open.

## Integration refresh and remaining acceptance priorities — 2026-10-06

This checkpoint follows the feature implementations through `be089836`. It is a regression/acceptance plan, not a declaration that the full SDK or any unresolved runtime semantics are complete. The fresh existing-suite campaign is recorded under `local-output/sdk-20260909/sdk-integrated-offline-refresh-20261006/`. Node completed 181 suites and 181 editor syntax checks in 20.03 seconds with no failures. Its optional world-map export fixture coverage passed in a separate current-code run against retained private retail Current/Proposed artifacts. Python completed all 1,756 cases in 1,959.35 seconds with 213 error events, two assertion failures and two private-fixture skips; revision/digest stayed unchanged. Its terminal `python.json` and `triage.json` preserve this non-green baseline. Shared model hierarchy and floor-height Build repairs passed a fresh 108-test check across 22 affected modules in 129.51 seconds, with zero errors/failures/skips and unchanged repair digest; the six stale fixture modules additionally passed all 25 tests in 28.70 seconds after adding explicit audio/WAV collections and synthetic catalog mocks. Both repair waves preserve the existing assertions and have stable per-run implementation digests. These scoped results do not establish a green full-suite result; the fresh integrated recheck at `6f51eaaeee47b305bc4e12b8c7a892be90043348` under `sdk-integrated-offline-recheck-20261006` passed all 1,756 Python tests in 2,006.32 seconds with zero errors/failures/skips, using both qualified private projects. Node passed all 181 suites and 181 syntax checks in 20.92 seconds with no partial checks. Its terminal `acceptance.json` passed all 15 predicates, including unchanged revision/digest, five supplied fixture hashes, Python log hash and eight retained stability source/fixture hashes. This qualifies the existing offline campaign; unresolved feature implementation and manual gameplay boundaries below remain open. The two optional private-fixture tests additionally passed in 15.92 seconds with a stable revision/digest (`optional-coverage-pass2-python.json`): the mesh replacement scene proposal used a fresh retail Town01 import, and the NPC package reopened a copied retained exact authored fixture. Both checked unchanged project inputs. The initial optional runner passed its test assertions but failed JSON serialization after a setup variable overwrote its revision string; that log/failure is preserved, and the fresh second receipt is authoritative. These prepared projects will supply the next integrated run; no gameplay claim follows from these checks.

The following estimates are planning budgets per focused group, not measured full-suite durations. All private retail fixtures/inputs stay local. Automated source qualification, native package integrity, historical metadata and live gameplay acceptance are separate evidence layers. Existing manual acceptance remains deferred under the user's instruction; this plan does not authorize a game launch or attachment.

| Test name / required assertion | Feature | Level | Fixture | Retail required | Estimated budget | Platform | Mode | Priority / present evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Composed audio native entry: SEQ, VAB and multiple WAV samples only change independently expected spans; one overlay; full entry in directory/ZIP; flags/tails retained | Native audio authoring | Serializer + command + Build | Synthetic carriers and private fixed/relocated projects | Yes for retail Build | 1–10 min | Python/Node; Windows retail workflow | Automated | P0; focused codecs/commands and private package proofs exist; fresh aggregate pending Python completion |
| PCM WAV to fixed-allocation SPU: malformed RIFF, unknown padded chunks, exact prefix/allocation, bounded error, flags and opaque tail | Sample encoder | Pure codec + independent decoder | Small synthetic PCM/ADPCM plus qualified samples | Optional / retail corpus required for carrier coverage | 1–5 min | Python | Automated | P0; existing independent decoder and all-bank inventory checks; native audible acceptance is separate |
| Paired/bulk channel key changes preserve FIFO pair identities, velocity-zero releases and all other event bytes; key and canonical/request budgets reject atomically | Sequence note authoring | Pure policy + DTO + native integration | Complete/partial synthetic sequences and private edited sequence | Yes for complete native/UI proof | <30 s pure; 1–3 min integration | Node/Python/Edge | Automated | P0; channel transpose proof covers 72 notes/144 operands; pairing remains an editor policy |
| Complete saved-document resource identity: every persisted collection/future field invalidates; navigation/transient work follows declared scope; snapshot drift rejects | Central asset/reference database | Service + HTTP + UI | Detached synthetic projects and private audio-edited project | Optional / yes for actual editor Apply | <30 s pure; 1–2 min UI | Python/Node/Edge | Automated | P0/P1; 30 focused tests and actual Apply/Refresh/Undo/Save/Open proof exist; identity is not file integrity |
| All whole-degree coefficients/owner grids match between Python and browser; signed halfway values, bounds, zero no-op, field strictness and complete proposal decoding | Mixed placement angle rotation | Math + command + DTO | Portable integer vectors plus actor/NPC/scenery fixture | No for core; yes for package | <30 s pure; 1–3 min native proof | Python/Node/Edge | Automated | P0; 4,314 private cross-language vectors, 17 Python cases and native MAN/MAP proof exist; keep table parity a required regression |
| Current encoded note/program/tone/sample report binds exact Current hashes/history; sparse packed pages, unresolved/initial/standalone cases remain explicit | Audio relationship inspector | Service + HTTP + DTO | Synthetic bank/sequence and composed private Current project | Yes for native source report | <30 s synthetic; 1–2 min retail/UI | Python/Node/Edge | Automated | P1; five backend checks and actual download/disposal proof exist; runtime instrument selection is unresolved |
| Retained original WAV and historical frozen snapshots: exact original bytes, receipts/manifests/inventory; Current registration removal/file drift cannot substitute replay authority | Asset input retention/recovery | File integrity + service + UI | Two frozen input keys, removed Current registration, tampered sidecars | Yes for authored native lineage | 1–3 min | Python/Node/Edge | Automated | P0/P1; frozen recovery/private Build proof exists; qualify historical inputs separately from Current/native artifact |
| Geometry/texture/animation allocation composes into verified native containers with exact unknown-byte preservation, stale refusal, source ownership and descriptor bounds | Models/textures/animations | Codec + command + Build | Synthetic and private allocated/retired native tables | Yes for emitted retail container | 1–10 min per family | Python/Node | Automated | P0; existing family suites/private proofs; general skinning/retargeting is not covered or implemented |
| Script/dialogue/transition/collision changes preserve instruction ownership, opaque records and exact emitted MAN/MAP data; partial flow does not imply execution | Scene content authoring | Decoder + serializer + package | Synthetic control flow and supported private field records | Yes for emitted retail record | 1–5 min per family | Python/Node | Automated | P0/P1; existing suites/private readback; complete interpreter/story/scheduler remains open |
| Review/local drafts/Proposed/Current stay separate; stale response, close, parent disposal and busy state withdraw old action authority | Editor lifecycle | Contract + browser | Fake delayed transport and private editor project | Optional / yes for qualified native controls | <30 s contract; 1–3 min browser | Node/Edge | Automated | P1/P2; recent browser proofs exist; aggregate Node is passing |
| Group layouts hold height/facing/orientation; native grid rounding and donor snapshots; Current/Proposed viewport matrices; one history step; no-op retains history | Scene transform tools | Command + browser + native readback | Mixed actor/NPC/scenery source selection | Yes for native MAN/MAP | 1–3 min | Python/Node/Edge | Automated | P1/P2; whole-degree source/native proof exists; actual field placement/collision remains manual |
| Save/Open/project copy preserve source identities, retained inputs and history integrity; corrupted/stale retained files fail closed | Project architecture | Metadata + file + command integration | Temporary projects with changed/missing receipts/source files | Optional / retail variants needed for native lineage | <60 s synthetic; 1–5 min native | Python | Automated | P0/P1; existing campaign exercises these modules; wait for current aggregate result |
| Runtime observer executable/process/witness/epoch qualification; bounded topology; null/misaligned/loop/partial reads; no correlation by list order | Read-only runtime bridge | Fake transport + native unit checks | Synthetic topology and guarded fake lifecycle | No for deterministic guards | <60 s | Python; Windows transport variants | Automated | P0/P1; existing mocked tests; fake/historical inputs do not establish current live actor identity |
| Cold normal-window startup, FMV/prologue Select skip, input/controller release, shutdown and audio continuity | Recomp stability | Runtime behavior | Exact current Release executable + private user-owned disc | Yes | 5–15 min | Windows | Manual, deferred | P0; current compiled/runtime provenance and actual behavior must be freshly recorded; no launch authorized in this offline campaign |
| Edited wall/actor/NPC/floor appearance, repeated field/scene transitions and restore; matching editor/native coordinates and live identity | Gameplay/live inspector acceptance | Full end-to-end | Verified package + exact executable and reproducible scene/save location | Yes | 10–30 min per scoped scenario | Windows + editor | Manual, deferred | P0/P1; editor matrices and package bytes alone are insufficient; unconfirmed identity remains explicit |
| Complete MAPDSIP/world-map coverage, runtime instrument/synthesis semantics, general skinning/retargeting and full interpreter/scheduler/story behavior | Remaining SDK implementation | Research + feature integration + later acceptance | Source-qualified examples and independently justified semantics | Usually yes | Estimate after source evidence | Python/Node/native Windows | Implementation then automated/manual | P0/P1; open buildout work, not a waived test gate |

Record each result with the exact implementation revision/source digest, fixture identity, command, measured duration, pass/fail/skip reason and relevant private artifact hashes. A skipped required fixture is incomplete coverage until a separate qualified run supplies it. Never treat a passing import/metadata/DTO test as independent native-byte or gameplay verification. Keep failures and first attempts preserved; a repair requires a fresh scoped proof, and source changes invalidate broad claims based on an older digest.

The current refresh uses append-only progress evidence to avoid the previous Windows progress-file replacement failure. Its Python process guard permits the known offline interpreter/build helpers and rejects unexpected executables. Native runtime launch/attachment and manual gameplay are outside this campaign. The full goal stays active until the implementation and all required acceptance boundaries are proven; no automatic completion follows a green suite.

## Connected and inverse model vertex selections (2026-10-06)

The 3D movement editor now expands selected vertices through Current object preview triangles and inverts a group within its object-local table. These are local selection actions; coordinates/normals/topology and history stay unchanged until an explicit group Save. Existing saved-group Recall, Undo/Redo and Save/Open preserve the exact selection. Coincident positions/shared normals are not links; malformed/cross-object triangle references and results over4096 vertices reject atomically. Geometry drafts lock these selection tools.

Actual Town01 editor selection/recall, no-op and wide/narrow checks passed; source/model state is preserved. Fresh native Build packages before/after group Save are byte-identical. Focused connectivity and existing movement Node guards pass. See [Current vertex connectivity](legaia-model-vertex-connectivity.md); private evidence is in `local-output/sdk-20260909/vertex-connectivity-20261006/`. Gameplay stays deferred and development remains solo.


## Native-grid snapping for selected model vertices (2026-10-06)

The existing 3D model movement editor now stages a selected group's Current object-local coordinates onto a native-unit grid, with explicit X/Y/Z axes and integer spacing. Halfway values round away from zero; signed16 overflow rejects the whole operation. Draft/Current/Retail and scene Review/Return remain separate from one atomic Apply. Selected rows/axes change; normals, topology and other rows/objects retain their existing native qualification. Already snapped rows are a no-op; Undo/Redo and Save/Open use the model replacement workflow. This adds authored geometry, not a runtime grid or actor-placement rule.

Workflow and acceptance boundary: [vertex grid tool](legaia-model-vertex-grid.md). Private evidence is in `local-output/sdk-20260909/vertex-grid-20261006/`. Development continues solo; gameplay verification remains deferred.


## Selected script operand layers (2026-10-06)

The source-flow workspace now inspects a selected original instruction/message boundary across Retail, composed Current and reviewed Proposed layers. It shows decoded operands, dispatch/length/successor fields and exact encoded byte differences by record PC. Pending nonbranch form drafts are excluded; unavailable inspections and boundaries not decoded on a layer remain explicit. Review invalidation/Discard, failed Apply, stale source/state and close withdraw the displayed proposal. This is read-only static inspection, with no VM or runtime observation.

Actual Town01 Current RGB/intensity edits and a separately reviewed actor branch proposal passed the editor workflow, exact selected-byte comparison, wide/narrow display and unchanged project/history checks. The surrounding branch flow and new focused operand-layer Node checks pass. See [selected script layers](legaia-script-node-layers.md); private evidence is in `local-output/sdk-20260909/script-node-layers-20261006/`. Gameplay verification remains deferred.


## Retail versus saved Build script comparison (2026-10-06)

Imported actor and standalone script editors now expose a read-only comparison with an intact saved Build matching current inputs. The SDK reads actual native MAN records from relocated PROT or qualified overlays, verifies source disc/package receipts, retains retail/generated hashes and offsets, and reports exact changed record bytes alongside paired decoded paths. Bounded display and a complete local comparison download preserve stops/opaque regions. Stale inputs, ambiguous records and layout changes reject inspection. This does not establish script execution or gameplay acceptance.

Actual Town01 editor receipt selection/comparison/download and wide/narrow layouts passed; the emitted record exactly matches the independently decoded preceding color-edit Build. HTTP boundaries, stale input rejection and unchanged project/history were verified. Details and acceptance hashes: [source Build script guide](legaia-source-build-script.md). Private evidence: `local-output/sdk-20260909/source-build-script-20261006/`. Development remains solo; gameplay verification stays deferred.


## Fixed source effect color/intensity authoring (2026-10-06)

Qualified source scripts now expose an **EFFECT_COLOR_INTENSITY** operand editor with encoded red/green/blue bytes (0–255) and signed16 intensity (-32768–32767). Retail, authored and effective values remain separate. Apply/Clear use project commands, atomic history and Save/Open. Source instruction rows link to the editor; standalone script assets, component navigation/reset and source-bound operand file/bundle workflows recognize `ScriptEffectColors`. No renderer or runtime memory write is introduced.

The patcher qualifies reached sub0 instructions only in records without decoder stops, preserves opcode/extended actor context and the complete selector byte, writes only the five-byte RGB/intensity window, and rechecks instruction/continuation layout. Native Build composition checks source/preimage hashes, requested bytes, overlap and unaudited changes. Normal, appended and streaming composition paths register the new family; the accepted retail workflow independently verifies normal Build delivered its full partition-two record. Allocated-NPC-specific color authoring and actual host rendering remain incomplete.

Validation: 13 focused Python authoring/project/Build/HTTP/operand-transfer tests passed; the existing streaming native Build regression also passed; the two new source patch tests additionally verify the typed package report/change kind. Five existing Node script lifecycle/navigation/operand/reset checks passed, as did changed JavaScript syntax and Python parsing. Town01 discovery found ten qualified source targets. Fresh retail-project browsers edited partition-two script0000, rejected invalid inputs, showed separate value layers, cleared/restored the override and downloaded exact typed operand metadata with no page errors; wide/narrow screenshots were inspected. Invalid field/width requests rejected before mutation; one-step Apply, no-op reapply, Undo/Redo, Save/Open, project-copy recovery and unchanged imported/reference data passed. Two missing Build-family gates were caught by the initial package audit and corrected before acceptance. Independent final package decoding read back the entire expected script record exactly (SHA-256 `97fc68f29f8bce703a84abc34b14c6410d9b9227fa88759521b7e74640ef7223`); package SHA-256 is `a397f445e3fc290d89f4f0583a638c92ccae2d9ceb2aa7ee72846d54d66d341c`. The first omitted delivery is superseded by this final readback. Private proof: `local-output/sdk-20260909/script-effect-color-20261006/`. No game launch, runtime attachment, installation or full-disc export; gameplay and the full SDK goal remain open.


## Source sequence note timeline (2026-10-06)

**Inspect sequence events → Show note timeline** opens a graphical encoded-note view in the Audio Asset Database. It has independent channel filtering, 4/8/16/32/64-quarter-note tick windows, Earlier/Later navigation, mouse/keyboard selection and direct navigation to start/release source rows. Channel colors, velocity brightness, source ticks and selected event details aid inspection. At most 512 notes are drawn per window; denser windows explicitly request a narrower range/channel.

Relationships are derived display evidence: a release matches the earliest open start with the same channel and key (FIFO), with overlapping starts marked ambiguous. Velocity-zero note-on events act as releases, consistent with the pinned Andrew `crates/seq/src/lib.rs` evidence at `d6e64c68ede25813d35db20980da82a1a025549b`. Missing starts/releases stay counted and unmatched; dashed notes extend only through the decoded display prefix and never receive an invented end event. Sustain/controllers, instrument resolution, voices, looping and audible duration are not evaluated. Partial source reports remain partial. No project data or retail bytes are authored by this view.

Validation: focused Node checks passed channel-isolated pairing, ambiguity, zero-velocity release, partial/unmatched boundaries, source immutability and the 32,768-event budget; the existing sequence/bank/waveform/audition checks also passed. Source changes withdraw both table and timeline; close/late-reply ownership remains guarded. Fresh retail-project browsers passed complete/partial timelines, window/channel navigation, pointer/keyboard selection, source-row navigation, hide/reopen, exact unchanged metadata download and wide/narrow layouts with no page errors. Screenshots were inspected. Project documents, history/files and reference fixture were unchanged; normal private native Build before/after browsing was byte-identical (SHA-256 `c309f270d2705d0f72ac3899248b99744689ec553b927c004bc2dfa5c7af2e30`). Private proof: `local-output/sdk-20260909/audio-note-timeline-20261006/`. No game launch, runtime attachment, installation or full-disc export; gameplay remains deferred and the full SDK goal remains active.


## Explicit GLB joint-rig motion mapping (2026-10-06)

Both imported-actor and allocated-record animation editors accept an explicitly selected GLB skin and one explicitly mapped joint node per native object. The node inventory labels skin joints and mesh instances. Review qualifies scene reachability, joint uniqueness, a common ancestor, optional skeleton and bounded affine inverse-bind matrices. It samples mapped joint/ancestor translation and rotation into existing native channels. Other selected-skin joint tracks are validated and reported as ignored. Mapping/skin changes invalidate Review; the selector is disabled while the dialog is busy. Original GLB, binding and receipt recovery retain the selected skin.

This is rigid joint motion only: native geometry and opaque channel packing are preserved. Inverse-bind matrices and mesh weights do not deform native geometry. Anatomical skinning, automatic correspondence, rest-pose retargeting, relevant-node scale deformation and gameplay cadence remain incomplete.

Validation: 60 existing focused Python animation tests passed in the broad run; three new rig tests passed after correcting their missing mesh-manifest fixture. Node rig/mapping/lifecycle contracts and changed module syntax passed. Fresh browsers exercised both workflows through Review, Pose, Return, Apply and exact input recovery without page errors. Undo/Redo, Save/Open and project-copy recovery passed. A further browser check covered busy selector ownership and changed/reverted skin invalidation without Apply. Normal private Build readback exactly matched the composed native bank (SHA-256 `b478a4e572459b837ae2be01b1eb94c160cec9aad4b1952c602e1123a356009d`). Reference fixtures were unchanged. Proof: `local-output/sdk-20260909/animation-glb-joint-rig-20261006/`. No game launch, runtime attachment, installation or full-disc export; manual gameplay verification remains deferred and the full SDK goal remains active.


## Source SEQ event inspector checkpoint (2026-10-06)

Validation: all 41 retail-enabled focused Python tests passed without skips/errors/failures. Node source/summary/timing contracts, stale-source withdrawal, close/late-response ownership and existing asset inspector guards passed; all three changed JavaScript modules passed syntax checks. The production frontend decoder qualified all 83 freshly read retail source reports (258,065 events). Fresh browsers passed complete and partial carriers, hidden unsupported actions, pagination/filtering, exact metadata download, pending close and wide/narrow layouts, with no page errors; final screenshots inspected. HTTP exact-field, stale-key/hash and unsupported carrier checks rejected before mutation. Project/history/files and reference fixture were unchanged. Normal native Build before/after inspection was byte-identical (SHA-256 `1e358a48f13f35757fb08a06fd2550b74e5957cf94495ce45fca5c0b75aa6eec`). Private proof: `local-output/sdk-20260909/audio-sequence-20261006/proof.json`, `retail-sequences.json`, `all-source-node.json` and focused logs. No game launch, runtime attachment, installation or full-disc export; gameplay remains deferred and the full SDK goal stays active.

Supported source audio records now offer **Inspect sequence events**. The read-only inspector shows bounded ordered channel/meta instructions, source byte ranges, encoded operands, running-status use, cumulative ticks and timing integrated from declared SEQ tempo. Kind/channel/search filters, 128-row pagination and complete metadata download work on complete or explicitly partial sequences. Missing sequence carriers expose no action. Source changes withdraw displayed events; close/late-response ownership prevents stale publication. The source-qualified HTTP reader requires exact request fields, the current project scene source key and the original physical entry hash, freshly verifies imported/disc provenance and reads only that entry's supported sequence carrier.

The pinned Andrew SEQ parser supplies format evidence for VLQ/running status and fixed-size tempo/end-of-track meta events. Unlike its synthesized termination on unknown system/meta events, this SDK stops at the unresolved source offset and labels the decoded prefix partial without inventing end-of-track. Across all 83 supported retail carriers, 82 reached encoded end-of-track and PROT 1045 stopped at a non-seven-bit channel operand; 258,065 events were decoded, with at most 6,451 in one source. These are source syntax/timing facts, not waveform validity, audible duration, looping, scene assignment or runtime cadence. Waveform synthesis, playback and audio authoring remain incomplete.


## Source audio Asset Database checkpoint (2026-10-06)

Validation: the retail-enabled 37-test focused Python regression passed with no skips/errors/failures; four existing Node contract checks and all five changed JavaScript module syntax checks passed. Fresh retail-project browser checks passed active/project discovery, source/confidence filtering, typed complete/partial header inspection, provenance visibility, metadata download and reference navigation with no page errors. Wide/narrow screenshots were inspected. Project documents, files, Undo/Redo history and the reference fixture remained unchanged. Normal native Build before/after browsing was byte-identical (package SHA-256 `7ec8b65439c3a5893fc264b95ba1d4a7d8c11af7f7687fe7dc7344a3bfbb6b98`). Private proof: `local-output/sdk-20260909/audio-catalog-20261006/proof.json`. No game launch, runtime attachment, installation or full-disc export occurred; gameplay remains deferred and the full SDK goal remains active.

Audio is now a central read-only resource category in active-scene and project Asset Database scopes, with stable PROT identities, searchable provenance/confidence, a typed header inspector, reference navigation and metadata evidence download. Discovery checks leading signatures across the verified archive and reads recognized entries only inside physical next-TOC boundaries. Retail source evidence found 218 records: 83 supported VAB+SEQ sound packs and 135 qualified leading VAB headers in unresolved containers. Partial records preserve their header and failure reason; they do not invent a sequence or complete bank. Source/chunk hashes, declared programs/samples and SEQ timing headers remain separate from runtime playback.

Evidence uses the pinned Andrew reference `d6e64c68ede25813d35db20980da82a1a025549b` (`sound_pack.rs`, VAB and SEQ header parsers), read through `git show` because the reference checkout HEAD has advanced. The catalog neither adopts that newer revision nor adds it as a runtime dependency. Events, waveform tables, audio preview/edit/replacement, duration, XA, interior audio containers and scene playback assignments remain incomplete. No runtime or gameplay acceptance is asserted. Private evidence: `local-output/sdk-20260909/audio-catalog-20261006/`.


## 2026-10-06: repeat and ping-pong sampling for external animation clips

Both the imported-actor and allocated-record GLB editors now expose **External timeline behavior** under explicit external sampling: Hold endpoints (legacy default), Repeat clip and Ping-pong clip. Repeat wraps the shared first-to-last channel key extent and excludes its final endpoint; ping-pong reverses at both endpoints. Negative rates reverse traversal, zero holds, and zero-extent/static clips stay constant. Native frame/object counts, source packing and ownership remain fixed. The selected mode is retained with original inputs and bound to Review, Pose and Apply; changing it invalidates the prior Review even if native poses coincide. Existing two-field sampling bindings and explicit clamp mode retain their canonical legacy identities. Cyclic time arithmetic avoids early float32 division rounding at reverse seams while keeping the legacy clamp calculation unchanged.

Validation: independent native-byte cases cover repeat/ping-pong, reverse/hold, seams, STEP curves, static inputs and legacy normalization; review-choice tests reject reuse across modes. Fresh browsers exercised imported Repeat and allocated Ping-pong through Review, Pose, Return and Apply, mode invalidation and wide/narrow layouts with no page errors. Private HTTP checks rejected mismatched mode/Review before mutation; each accepted edit created one history step and preserved exact retained inputs. Undo/Redo and Save/Open passed. Normal native Build delivered an independently decompressed animation bank exactly matching the composed bank (`f3c7c25e11490c13220ee2d5055874a7b0fc8f6b4974ce4fae232bf73ce015cb`). Reference fixtures were unchanged. Evidence: `local-output/sdk-20260909/animation-glb-cycles-20261006/pass1/proof.json`, screenshots and targeted regression logs. The retail-enabled animation regression passed all 77 tests with no skips, errors or failures; focused Node contracts and syntax checks for all three changed JavaScript modules passed. No game launch, runtime attachment, installation or full-disc export; native game cadence/assignment acceptance remains deferred. The full SDK goal stays active/incomplete.


## 2026-10-06: compare historical samples with selected actor coordinates

The historical viewport toolbar now offers **Compare selected actor coordinates** for a selected imported actor and a displayed node key. Its detached snapshot shows retail native, current native, explicit authored overrides, viewport native and separate viewport surface coordinates. Captured-minus-reference deltas are shown per axis for the selected file layer, including both baseline/comparison samples. Unknown native Y stays unknown, even when a source surface supplies preview height. File-listed candidate IDs remain unconfirmed; numeric agreement does not bind identities or establish a coordinate convention. Metadata-only comparison download preserves scene/source key, actor/key, representation, declared epoch/profile and capture frames. Changing the editor source, selection, representation, sample/file or layer disables export of the old snapshot. The historical toolbar also resynchronizes after API requests, fixing controls left disabled after actor selection.

Validation: focused Node arithmetic/context/authority checks and existing historical review/comparison tests passed, as did editor/module syntax. Fresh browser workflows over retail town01 with synthetic saved samples passed actual dialog/download, native versus preview height, authored placement deltas, both file layers, wide/narrow layout, source-change snapshot withdrawal, no-selection disable and camera/selection preservation. The existing paired-overlay, layer, framing, marker-picking and return/clear browser regression passed. Final screenshots were inspected; no page errors. Authored/imported state and its Build state key were unchanged after verification. Evidence: `local-output/sdk-20260909/historical-actor-coordinate-comparison-20261006/final/proof.json`, metadata downloads and `regression/proof.json`. The first browser run exposed a missing static module route; a subsequent flow exposed the stale toolbar busy state. Both were fixed before acceptance; a private verifier UTF-8 title mismatch was corrected separately. No game launch, runtime attachment, installation, full-disc export or real captured-coordinate acceptance occurred. Manual gameplay remains deferred and the full SDK goal active/incomplete.


## 2026-10-06: integrated offline verification and current SDK overview

The [current SDK overview](SDK_CURRENT_STATUS.md) now distinguishes implemented workflows, incomplete subsystems and deferred manual acceptance. The implementation baseline remains `5591cc37`; this checkpoint changes test fixtures/assertions and documentation only. Production SDK/runtime validation is unchanged.

Validation: 164 Node checks and 160 editor-module syntax checks passed without fixture skips. The 1,669-test retail-enabled Python baseline completed in a 369-test prefix plus a 1,300-test continuation after Windows denied progress-file replacement. That baseline recorded 81 error events, five assertion failures and two specialized-fixture skips. Tracebacks showed outdated fixture stores/catalog fields/source-key mocks and capability, manifest, budget, catalog-count and branch expectations. All 39 affected modules were rerun after corrections: 128 passed, one specialized fixture skipped, zero errors/failures. This is targeted acceptance, not a fresh all-green full-suite rerun. The private Retail V7 scene-preview and composed Town01 NPC-package fixture checks remain unexecuted. Evidence: `local-output/sdk-20260909/sdk-integrated-offline-20261006/final/acceptance.json`, `remaining/python.json`, `corrected/python.json`, `shared-fixture/python.json` and `node.json`. No game launch, attachment, installation or full-disc export; manual gameplay remains deferred and the full SDK goal active/incomplete.


## 2026-10-06: inspect historical samples from the viewport

## Source sample audition and WAV export checkpoint (2026-10-06)

Nonempty waveform prefixes now offer **Load audition**, an explicit **Preview rate**, **Play sample**, **Stop sample**, preview volume and **Save preview WAV…**. Loading never plays automatically. Changing rate, Stop, closing the waveform view or a source change cancels pending/active playback; closing releases its audio context. WAV export preserves the decoded mono 16-bit PCM at the chosen preview rate, independently of preview volume. Rate and preview seconds are user choices, not retail pitch/duration facts. Encoded loops are not replayed; source limits/termination stay visible. Empty prefixes expose no audition controls.

The private `/api/audio-pcm` route requires exact scene/entry/bank/sample freshness fields, requalifies imported/disc provenance and emits only the existing bounded decoded prefix. The browser validates the waveform contract, exact frame extent, PCM SHA-256 and each envelope bin before allowing playback or export. A shared waveform contract serves display and audition. PCM preview bytes remain separate from imported/project metadata; native runtime and Build implementations are unchanged.

Validation: 49 retail-enabled focused Python tests passed without skips/errors/failures; waveform/audition/bank/asset-inspector Node contracts and all three changed editor module syntax checks passed. Of 1,696 source sample spans, 1,695 nonempty prefixes passed frontend PCM/hash/envelope and WAV checks (59,052,168 verified PCM bytes); PROT 1035 sample table slot 9 is zero-length and rejects PCM preview. Actual browser workflow passed no autoplay, explicit rate, nonzero Web Audio buffers at 22,050/44,100 Hz, Stop, rate-change cancellation, natural end, close cleanup, exact WAV/metadata downloads and wide/narrow layouts with no page errors; screenshots inspected. Automation muted device output; listening and native game audio remain unverified. A private fixture initially misdecoded its UTF-8 button label, then passed after correction. Exact HTTP/stale identity guards rejected before mutation. Project/document/history/files and reference fixture stayed unchanged; native packages before/after were byte-identical (SHA-256 `7c72cf0fa141c5076692f77d417576365438d7760f2de0bea4c2a891b8cd29c4`). Private evidence: `local-output/sdk-20260909/audio-audition-20261006/proof.json`, `all-source-node.json`, `empty-source.json`, `preview.wav`, focused logs and acceptance manifest. No game launch, runtime attachment, installation or full-disc export; gameplay remains deferred and the full goal stays active.

## Source sample waveform inspector checkpoint (2026-10-06)

Qualified bank sample rows now offer **Inspect waveform N**. The read-only view decodes a bounded PSX SPU-ADPCM prefix with zero initial predictor history, shows an amplitude envelope in decoded frame coordinates, exposes hover ranges and encoded end/repeat/loop-start markers, and downloads the complete derived evidence. It preserves source sample/table/hash identities and withdraws changed sources; pending close rejects late publication. This does not assume pitch, sample rate, audible duration, instrument assignment or runtime playback. No loops are replayed. Unknown predictors/flag bits and incomplete blocks stop the prefix without synthesized silence; reserved shift values 13–15 use effective shift 9 following the pinned SPU decoder.

The pinned Andrew `crates/engine-audio/src/spu/adpcm.rs` and `crates/xa/src/lib.rs` supply integer decode and coefficient evidence. All 1,696 source samples from the 202 qualified retail banks passed the frontend envelope/marker/prefix contract: 29,526,084 decoded frames, 1,694 encoded ends, one source-span exhaustion and one explicit 4,096-block preview limit. These counts describe source prefix inspection, not audible acceptance. Samples are never treated as whole compositions or scene playback assignments.

Validation: 48 retail-enabled focused Python tests passed without skips/errors/failures, including signed low-nibble order, cross-block predictor history, stop semantics, reserved shifts, envelope budgets and stale bank/sample hashes. Waveform/bank/asset-inspector Node contracts and lifecycle checks passed; both changed editor modules passed syntax checks. Actual browsers passed sample-row navigation, nonblank canvas, hover frame ranges, exact export, pending close and wide/narrow layouts without page errors; screenshots inspected. Exact HTTP fields and stale scene/entry/bank/sample identities were rejected. Project/document/history/files and reference fixture stayed unchanged; normal native packages before/after were byte-identical (SHA-256 `a87378af2252cf133a130558a22a4496bbee7cc65a037a19885577cc21a4d084`). Private proof: `local-output/sdk-20260909/audio-waveform-20261006/proof.json`, `preservation.json`, `all-source-node.json`, browser evidence and acceptance manifest. No game launch, runtime attachment, installation, full-disc export or audio playback. Gameplay remains deferred; the full goal stays active.

## Source VAB bank table inspector checkpoint (2026-10-06)

Audio records now offer **Inspect bank tables** when their complete bank can be independently qualified. The read-only inspector separates all 128 program slots, packed tone pages and size-table sample spans; it supports used-slot/page/search filters, pagination, bounded tone-to-sample navigation and exact metadata download. Packed pages are not assumed to be program slot indices. Each table row and sample span carries its source hash. Current scene/entry/bank identities guard publication; source changes withdraw rows and closed views reject late replies.

The pinned Andrew VAB and split-bank parsers supply format evidence. Of 218 recognized audio entries, 202 have qualified bank tables and 16 retain explicit unavailable reasons. Bank qualification is independent of SEQ container coverage (83 supported sequence carriers, 135 unresolved sequence containers). The frontend decoder accepted all 202 fresh retail reports: 17,264 tone rows and 1,696 sample spans. Source table entry zero stays an uninterpreted spacer; sample operands resolve only when bounded by the one-based source sample table. These facts do not establish waveform validity, pitch, audible duration, runtime instruments, playback or replacement.

Validation: 45 retail-enabled focused Python tests passed without skips/errors/failures; bank DTO/lifecycle and existing asset inspector Node checks passed, as did syntax checks for all three changed editor modules. Actual browsers passed program/tone/sample views, filters/pagination, sample navigation, banks without sequences, hidden unsupported actions, exact download, pending close and wide/narrow layouts without page errors; screenshots inspected. Exact HTTP fields, stale source/hash and unsupported banks were rejected. Project/document/history/files and the reference fixture were unchanged after inspection; native packages before/after were byte-identical (SHA-256 `82fcb1dab13822a5f8d6c88ba018133e42c51d106ba75e07a5e584416f384551`). The initial fixture snapshot incorrectly preceded baseline Build output creation; the repeat separated preservation checks and passed. Private evidence: `local-output/sdk-20260909/audio-bank-20261006/proof.json`, `preservation.json`, `baseline-copy-delta.json`, `retail-banks.json`, `all-source-node.json` and focused logs. No game launch, runtime attachment, installation or full-disc export. Gameplay remains deferred; the full goal remains active.

Historical overlays now expose a bounded node selector and **Inspect historical sample**, plus an explicit **Pick historical sample** viewport mode. Inspection opens the existing detached review or comparison filtered to that key, preserving complete evidence and original download metadata. Single-file details expand to show coordinates, capture frames and recorded fields. Coincident baseline/comparison markers deduplicate their declared key; different overlapping keys require choosing the selector. Explicit pick gestures take precedence over scene mesh selection and transform handles, guard project/source/camera/viewport context, and never submit authoring commands. Dragging remains camera navigation. Empty layers disable inspection/picking and withdraw pick mode; source changes retain the existing overlay withdrawal. Imported entity selection stays independent.

Validation: Node screen-space hit tests passed the 256-point bound, duplicate-key handling, ambiguity, empty samples and invalid geometry. Existing review/comparison and editor syntax checks passed. Fresh retail-source browsers with synthetic historical files passed selector and actual canvas inspection for single reviews and paired comparisons, capture evidence, preserved camera/selection, all layers, wide/narrow framing, clear/return, empty/foreign rejection and source-change withdrawal. Authored state and its build-state key were unchanged after verification; no page errors. Evidence dialogs inspected. Proofs: `local-output/sdk-20260909/historical-runtime-sample-inspector-20261006/proof.json` and `comparison/proof.json`. No real runtime capture, game launch, attachment, installation or gameplay acceptance occurred. Full SDK goal remains active/incomplete.


## 2026-10-06: spatial comparison of historical runtime files

The saved-runtime comparison report now connects to the central viewport through **Show historical comparison positions**. Baseline samples are blue, comparison samples amber, with Both/Baseline/Comparison layer selection. Dashed segments join different complete coordinates with the same declared node key; file-only keys have markers without segments. Matching keys remain unconfirmed identities, and lines imply neither motion paths nor chronology. Each file is revalidated and the comparison is reconstructed rather than trusting report rows. The limit is 128 nodes per file / 256 displayed samples; missing or out-of-range XYZ values are skipped independently. Frame uses only the selected layer and disables for an empty layer. Return reopens the full comparison evidence; Clear and source-context withdrawal remain ephemeral.

Validation: Node guards passed layer construction, detached evidence, complete-key segments, unchanged positions, file-only keys, missing coordinates, same-scene/Edit/profile checks, malformed layer rejection and the 256-sample bound. Existing runtime review/comparison and camera tests passed. Fresh retail-source browser workflows with synthetic historical files passed both-file rendering, all three layers, layer-switch display preservation, framing, wide/narrow layouts, Return/Clear, empty-layer disable, foreign-scene rejection, source-change withdrawal and Undo; authored state and its build-state key were unchanged after verification. The single-file browser regression also passed. Final comparison screenshots inspected; no page errors. Evidence: `local-output/sdk-20260909/historical-runtime-comparison-viewport-20261006/final-pass/proof.json`, with the single-file proof in `single-regression/`. The first comparison run exposed Return rebuilding a closed dialog without reopening it; this was fixed before passing runs. No real runtime capture, game launch, attachment, installation or gameplay acceptance occurred. Full SDK goal remains active/incomplete.


## 2026-10-06: historical runtime positions in the central viewport

Saved runtime node reviews now offer **Show historical positions** for the matching current Edit-mode scene. Complete bounded XYZ file samples appear as dashed amber markers with historical/unconfirmed labels, using the existing scene display transform. Incomplete and out-of-range samples are skipped with counts; no Y or identity is inferred. Active controls stay outside the collapsed scene-tool drawer: Frame historical positions, Return to historical review and Clear. Showing samples preserves the camera; explicit framing preserves its angles/projection and scene visibility. These samples are ephemeral display data, not Live observations, actor bindings or persistent edits. Project/mode/scene/source/representation changes withdraw the overlay, and Undo does not resurrect it.

Validation: focused Node review tests passed detached data, matching Edit-scene checks, bounded complete coordinates and authority rejection; existing review/comparison and camera projection tests also passed. A fresh browser with synthetic historical files over the actual retail town01 scene passed show/frame/return/clear, wide/narrow layout, foreign-scene and empty-sample rejection, real source-change withdrawal and Undo. Authored/imported state and its build-state key remained unchanged after verification; no page errors. Wide and narrow screenshots inspected. Evidence: `local-output/sdk-20260909/historical-runtime-viewport-20261006/final-pass/proof.json`. The first browser run exposed hidden controls in the tool drawer, which were fixed. Subsequent verifier corrections distinguished collapsed evidence text and read-only preview requests from authoring. No game launch, runtime attachment, installation or new gameplay validation occurred. Real captured-coordinate/identity acceptance remains deferred; the full SDK goal remains active/incomplete.


## 2026-10-06: frame isolated selections

**Frame isolated** fits the currently visible mesh bounds of the captured isolation group in the viewport. It preserves yaw, pitch, projection, manual hidden instances and layer switches, and accounts for current instance transforms, perspective depth and viewport aspect with ten-percent edge padding. Hidden-layer members are skipped; the action is disabled when no isolated mesh is visible. Saved scene views retain and recall the fitted camera through the existing metadata workflow. Scene content and game coordinates are unchanged.

Validation: the pure camera helper passed eighteen perspective/orthographic, aspect and orientation combinations against the actual renderer projection, plus mutation and invalid-input checks. A fresh retail-source editor browser passed Perspective, Front, Side and narrow-viewport fitting of every current mesh corner, layer skipping/disable, exact saved camera recall, NPC deletion/recovery, metadata history and portable Open. Wide and narrow screenshots were inspected; no page errors. Complete native Build output remained identical before and after the view changes (SHA-256 `ec0f718a3ebfc735e209f6cd935d4d726c5827650095422c5256557c7f7811e3`). Evidence: `local-output/sdk-20260909/scene-isolation-framing-20261006/final/proof.json`. No game launch, runtime attachment or installation occurred. Gameplay acceptance remains deferred and the full SDK goal remains active/incomplete.


## 2026-10-06: saved NPC visibility and unavailable-draft recovery

Saved scene views now capture NPC draft isolation, mixed actor/NPC/static-decoration groups and manually hidden NPCs in the Authored scene representation. NPC-only visibility uses the authored entity identity without inventing a MAP provenance binding; environment members retain the existing source MAP checks. Save/Replace require available, validated same-scene drafts. The existing saved-placement identity validator is reused. Portable Open retains canonical references to deleted drafts, allowing view metadata to remain manageable rather than blocking the project.

Recall is disabled with an explicit missing-draft count and recovery note when hidden or isolated NPC IDs are unavailable. A fresh-state missing-draft guard runs before scene/representation/camera changes. Client validation also checks actual draft scene membership even when preview eligibility IDs are outdated, plus per-instance renderability and Authored representation. Undo restoration of the original draft identity makes all affected views recallable again. Metadata Rename/Delete remain available for unavailable views. This supersedes the earlier saved-NPC-visibility exclusion.

Validation: thirteen focused Python view tests passed, including NPC save/open, deletion with retained portable metadata, unavailable Save/Replace rejection, Undo restoration, malformed IDs and foreign-scene/retail-representation rejection. Node visibility/representation/missing-membership guards and editor syntax passed. A fresh retail-source browser saved and recalled single-NPC, mixed-NPC and hidden-NPC views, deleted the draft, checked all three disabled recalls with unchanged display, saved the unavailable project, restored the draft with Undo and recalled every view. Portable Open passed for both unavailable and restored snapshots; native Build matched the pre-view package hash. The existing group, hidden-member and changed-source withdrawal checks also passed; no page errors. Screenshot inspected. Evidence: `local-output/sdk-20260909/scene-npc-visibility-20261006/final/proof.json`. A Node negative case exposed and led to fixing stale eligibility accepting a foreign-scene NPC before the final passing runs. No game launch, runtime attachment or installation occurred; the full SDK goal remains active/incomplete and gameplay acceptance stays deferred.


## 2026-10-06: selection-group isolation and saved group views

The viewport now isolates the active actor, scenery or mixed placement selection (1..128 renderable instances), including temporary groups containing NPC drafts. Isolation is pinned to the captured group; Restore preserves the camera, manual hidden instances and scene-layer switches. A selected hidden or unrenderable member disables isolation. Scene/project/source/representation changes and active proposals withdraw it, using the existing current-scene binding. Single-instance behavior remains available.

Saved scene views now retain canonical group isolation IDs for imported actors, static decorations and ground, with source MAP binding and every-instance membership/renderability checks. Existing scalar single-instance bookmarks and views without visibility retain their format and behavior. Metadata CRUD/history/Save/Open and Recall use the normal view workflow; NPC-draft visibility remains unsupported in saved views, as before. These are editor display changes, not scene-content edits.

Validation: eleven focused Python saved-view tests and Node view/visibility guards passed, including group history, portable Open, exact static MAP ownership, malformed/duplicate/oversized/hidden-member rejection and legacy compatibility. The actual retail-source browser passed actor-group and mixed actor/NPC/decoration isolation, Restore preservation, mixed actor/decoration bookmark save/recall, metadata Undo/Redo/Save, hidden-member rejection and withdrawal after a private transform change (then Undo). No page errors occurred. Save/Open retained the group exactly; the native package matched the pre-view Build hash. Screenshot inspected. Evidence: `local-output/sdk-20260909/scene-group-isolation-20261006/final/proof.json`. The initial browser verifier assumed an actor kind tag absent from the actual preview; selection now uses SDK entity identity and the corrected workflow passed. No game launch, runtime attachment or installation occurred. The full SDK goal remains active/incomplete, with gameplay acceptance deferred.


## 2026-10-06: floor-height delivery with NPC appends and raw streaming

Native package composition is now exercised against retail Town01 and Dolk2: one NPC in a compressed fixed span, eight NPCs requiring compressed relocation, a raw streaming MAN without an NPC, and a raw streaming MAN with an appended NPC requiring relocation. Each height-edited package is reopened independently and its complete decoded MAN compared with an otherwise identical NPC/MAP build using retail heights; only the requested two-byte tier entry may differ. The complete emitted MAP also matches an independent wall-bit and floor-selector calculation, including relocated archive delivery. Actor counts, imported metadata, authored state and history remain unchanged by Build; the authored project passes Save/Open and Review Build. This supersedes the earlier unexercised appended/streaming height-delivery limitation.

Build summaries now name source floor heights when an NPC composition contains the emitted height audit. Missing/empty/unrelated nested audits cannot add that label. Relocation feature descriptions retain the packaged edit list and no longer claim that all allocated clips are unassigned. Gameplay remains explicitly unverified.

Validation: four opt-in retail delivery checks and nine focused Build-report checks passed against the final code (13 total); Python syntax and diff checks passed. Evidence: `local-output/sdk-20260909/floor-height-delivery-20261006/final/proof.json`. The initial compressed verifier used an incorrect carrier field name; that verifier was corrected before the final passing run. No game launch, runtime attachment, installation or full-disc export occurred. Manual floor collision, movement, ramps and NPC behavior acceptance remain deferred; the full SDK goal remains active/incomplete.


## 2026-10-06: height-table editor and Proposed scene inspection

`Edit floor heights` now opens from the source collision inspector and Scene Tools, exposing all sixteen source-qualified Retail/Current/draft MAN values and draft reference Y. Signed integer bounds, reset-to-retail, discard-to-Current, fresh Review and normal one-command Apply are connected. Input changes withdraw old Apply and scene-inspection authority. Owned reads abort on close and reject stale scene/project context; the dialog remains bound to its reviewed source. The SDK context route supplies Current values without authoring a change.

Inspect proposed height scene builds a detached project view, validates the original Review and Current scene key, then uses the existing Proposed/Current scene comparison and Return to height review. The source project stays unchanged until Apply. Scene changes invalidate the retained editor. The endpoint rejects foreign active-scene ownership and changed height/Review inputs. Client qualification checks signed vectors, source carrier/hash identity and every exact two-byte MAN audit span, including raw-streaming carrier bounds. This completes the prior height-authoring foundation's normal editor workflow; actual appended/streaming package acceptance and gameplay remain pending.

Validation: four focused Python height codec/context/history/proposal and preview checks passed; the new Node height Review validator passed typed bounds, source identity, exact MAN audit and detached-response guards. Editor/module syntax and diff checks passed. A private retail browser workflow passed sixteen-tier loading, edit/Review, invalid-value withdrawal, retail and Current resets, fresh Review, read-only Proposed inspection/Return, Apply, Undo/Redo and Save/Open. Independent Proposed and Current comparisons matched all ground vertices (1,088 changed corners) and all 208 qualified placed/decorative reference transforms; source records remained immutable. Normal Build independently matched the complete decoded MAN and MAP, retaining prior wall and selector edits. Native MAN SHA-256 `c6dc3f80d15540c7017f2d48b23fa85acc5234eb6d757f84b4d1614d23d5aa31`; MAP SHA-256 `2222ae211d70fa0b303fb7f5010ceb88699cad90edefd5cdd7b5a70c126e66e1`; package SHA-256 `99c3a091359cb948193cab4b3f0f18b7acd9c0fa85b11b060bd8c4e99e2041fd`. Wide/narrow dialog screenshots were inspected; no page errors occurred. Evidence: `local-output/sdk-20260909/floor-height-editor-20261006/proof.json`. No game launch, runtime attachment or installation occurred. The full SDK goal remains active/incomplete and gameplay verification stays deferred.


## 2026-10-06: native MAN floor-height authoring foundation

A source-qualified `FloorHeights` scene component now authors the sixteen signed MAN table values independently of MAP floor selectors. Read-only HTTP Review exposes separate Retail/Current/Proposed values and a sealed Apply key; strict typed bounds, source disc/import/MAN identity, stale-input rejection, one normal Undo step, retail restoration and Save/Open are implemented. The low-level serializer changes only requested two-byte entries in MAN `0x02..0x22`; partition counts, actor records and opaque bytes stay fixed. Build labels distinguish source floor heights, floor selectors and collision walls.

Ordinary Build composes header edits with supported MAN data and independent MAP overrides. Appended-NPC and streaming preparation have explicit height composition hooks, separate from MAP handling, with overlap rejection. Synthetic appended-header composition is checked; actual appended/streaming package delivery has not been exercised for this new component. No new runtime behavior or allocation support is inferred from those hooks.

Current ground geometry and placed/decorative object reference transforms now consume the effective authored MAN LUT, composed with Current selectors and scenery transforms. Height edits invalidate geometry cache identity. Decoration metadata now carries its evidenced source selector/LUT/record-offset facts, enabling the same height delta without replacing imported transforms. Floor-selector Review and reusable patterns qualify the Current height table. Source metadata remains immutable; ramps, native runtime overrides and movement acceptance remain unverified. Editor height-table controls and retained Proposed scene inspection are pending next; this checkpoint is a writable SDK/Build and Current-preview foundation.

Validation: twelve distinct focused Python checks passed across height codec/history/HTTP/native Build, floor preview composition, existing selector authoring/history/HTTP and decoration decoding; module imports and diff checks passed. Private retail HTTP Review/Apply, stale heights, one-step Undo/Redo and Save/Open passed. Independent complete decoded MAN and MAP comparisons passed, preserving the existing wall/selector edits. Every ground vertex matched its expected tier delta (1,088 changed corners), and all 208 qualified placed/decorative transforms matched independently while retaining source metadata. Geometry cache identity changed. Native MAN SHA-256 `c6dc3f80d15540c7017f2d48b23fa85acc5234eb6d757f84b4d1614d23d5aa31`; MAP SHA-256 `2222ae211d70fa0b303fb7f5010ceb88699cad90edefd5cdd7b5a70c126e66e1`; final labelled package SHA-256 `99c3a091359cb948193cab4b3f0f18b7acd9c0fa85b11b060bd8c4e99e2041fd`. Evidence: `local-output/sdk-20260909/floor-heights-20261006/proof.json`. An initial test used the wrong MAP filename; it was corrected before the passing native check. The labelled package was written to a fresh output directory after the existing-output guard correctly refused replacing an older manifest. No game launch, runtime attachment or installation occurred. The full SDK goal remains active/incomplete; gameplay acceptance stays deferred.


## 2026-10-06: reusable authored floor patterns

The floor editor now captures authored selector operations as portable JSON, loads them at a destination, rotates clockwise, mirrors X/Z and repeats them with whole native selector-step gaps. Keep Current captures only explicit paint operations; uniform tier/retail operations capture the selected extent. Loading and transforms stage drafts only, preserving unpainted Current selectors and requiring a fresh source-qualified Review before scene inspection or Apply. Retail restoration resolves against the destination source. File reads are bounded to 512 KiB and reject stale dialog/project context; invalid pattern, repeat or destination choices retain the existing draft.

Each pattern carries its sixteen signed MAN reference values. Every used numeric tier must have the same value at the destination index; different scene height tables reject rather than guessing a replacement. Duplicate-height indices remain distinct. Native floor rows/columns 0..127 are supported, independently of wall row bias; complete extents and operation counts stay within the 4096-selector Review budget. Rotation, mirroring and repetition preserve typed operations; gaps do not copy source retail values. No native Apply authority travels in pattern files.

A browser-discovered no-op bug was fixed: differing storage order of equivalent existing floor edits no longer makes Current Review appear changed. Review compares canonical selector content, and sealed no-op Apply returns without rewriting overrides or adding history. Regression checks preserve an unsorted existing component exactly.

Validation: four focused Python floor authoring/history/HTTP checks passed, including the new no-op regression; Node floor pattern and floor Review checks passed, plus module syntax and diff checks. A fresh private retail browser workflow passed pointer/keyboard painting, rotation, mirroring, a 2-by-2 repeat with gaps, exact download/reimport, invalid-repeat draft preservation, mismatched MAN-height rejection, fresh Review, exact Proposed/Current ground and placed-object reference heights, Return, Apply, Undo/Redo and Save/Open. Its twelve staged operations covered twenty-five selectors; an existing gap selector, outside floor edit and wall bit survived. Independent complete MAP Build readback matched exactly. Native MAP SHA-256 `831bf000fc402b6fa419c1bb0df3d462b09968d52a7b8e8a7cc66317537dc884`; package SHA-256 `22ccffe40e1a13e3c80852b28b371375feb1e89b549b1f2b0d542e7430d172fe`. Wide/narrow screenshots were inspected; no page errors occurred. Evidence: `local-output/sdk-20260909/floor-pattern-20261006/attempt2/proof.json`. The first run exposed the storage-order no-op bug; the fresh run passed after the fix. No game launch, runtime attachment or installation occurred. Gameplay acceptance remains deferred; the full SDK goal stays active and incomplete.


## 2026-10-06: mixed floor-selector painting

The source floor editor now paints individual native shared corner selectors inside one bounded rectangle. Keep Current preserves unpainted selectors; the brush supports any existing MAN tier or retail restoration. Pointer and Enter/Space editing show numbered Proposed points with native coordinates and reference heights. Painting withdraws old Review authority; changing rectangle inputs clears the draft. Fresh Review, Proposed scene inspection/return and normal Apply carry the same canonical selector list. The reviewed patch is one normal Undo step.

The optional v2 Review seals sorted unique row/column/tier operations with the existing project, MAP/MAN, disc and height-table evidence. Duplicate, out-of-bounds, untyped, null and stale inputs reject. Uniform v1 requests remain supported. Native Build preserves wall high bits, unpainted Current selectors and outside authored floor selectors; restoring retail removes redundant overrides. Shared-corner reference heights remain distinct from ramp behavior and live gameplay acceptance.

Validation: nineteen distinct focused Python checks passed across floor authoring/history/HTTP, preview composition, terrain and scene caching. Node mixed floor Review and viewport picking guards passed, with editor/module syntax and diff checks. A fresh private retail browser project passed pointer and keyboard painting, retail restoration, fresh Review, exact Proposed/Current ground and placed-object reference heights, immutable source transforms, Return, Apply, Undo/Redo and Save/Open. Independent full MAP construction matched ordinary Build exactly while retaining a wall edit in the same byte and an outside authored selector. Native MAP SHA-256 `753e0544250c26503d30a2483a85e1d13ed9e36149ae9a8111f003e763db0d40`; package SHA-256 `b62a156e1e1e4926d80b92f66fe45c2549e96c3cdef85f887f93ee3363e795cb`. Wide/narrow screenshots were inspected; page errors were empty. Evidence: `local-output/sdk-20260909/floor-paint-20261006/attempt2/proof.json`. The first harness compared JavaScript negative zero with serialized zero; its expectation was corrected before the fresh successful run. No game launch, runtime attachment or installation occurred. The full SDK goal remains active and incomplete; gameplay verification stays deferred.


## 2026-10-06: native floor picking in the scene viewport

`Pick floor selector` now resolves the actually visible ground instance and GPU-selected triangle, then opens its nearest projected corner in the floor editor. The draft is seeded with the exact native row/column and Current tier, not an inferred height. Ground preview metadata carries each vertex's source-qualified selector index, so tiers with equal MAN heights remain distinct. Picking can load the scene's collision source automatically and does not change authored state; Review remains required before Apply. Dragging still orbits. Stale scene/project/camera/viewport context and foreign or partial ground ownership reject selection. Outer preview corners use the decoder's evidenced edge clamp and are explicitly labelled when selected.

The independent bounded picker qualifies source cell identity, four-corner coordinates, two-triangle connectivity and typed tier metadata. Floor row zero is supported without the wall-grid bias. The new mode shares the existing viewport controls and excludes competing model-face picking and transition arrival movement. Current authored ground tiers are re-picked from the rebuilt preview, while source provenance stays immutable.

Validation: fourteen distinct focused Python cases passed across terrain metadata, floor preview and scene caching; new floor picking, floor Review and existing model face Node checks passed, as did editor/module syntax. Actual retail browser workflow used real WebGL picking to open native floor row0/column127 at its original tier, confirmed a no-op Review with disabled Apply, made one reviewed private change, and picked again at the authored Current tier. Undo/Redo, Save/Open and independent full MAP Build readback passed while retaining an earlier wall edit. Native MAP SHA-256 `7f2948c1b0212b9dd38041ed8b9d78ef5ae72c965fcc8f5eeace13051e13022b`; package SHA-256 `82db32a6a81544bfbd2f9dc4057a599ebac95b6b73a3fc1d8f796a00be3c1e31`. The picked-floor screenshot was inspected; no page errors occurred. Evidence: `local-output/sdk-20260909/floor-picking-20261006/attempt2/proof.json`. The first test used a point measured before the toolbar layout resized the canvas; a fresh attempt recalculated after source load/layout and passed. No game launch, runtime attachment or installation occurred. Source ground remains a reference surface; native ramps, reachability and gameplay acceptance are deferred. The full SDK goal remains incomplete.


## 2026-10-06: floor editor and authored height previews

The collision inspector now opens `Edit floor tiers`, with bounded native floor rows/columns, sixteen source-qualified MAN selector choices, retail restoration and separate Retail/Current/Proposed rows. Review supplies the immutable signed MAN values and reference Y labels; input changes withdraw old Apply authority. Inspect proposed floor scene uses a detached SDK project view and the existing Proposed/Current scene comparison with Return to floor review. Apply is one normal floor command, followed by the usual history, Save and Build workflow. The dialog and reader reject stale context and dispose owned requests on close.

Current ground geometry now decodes authored low-nibble selectors before texture association. Floor edits participate in geometry cache identity. Current placed-object transforms use the same evidenced placement-cell selector, composing its LUT height delta with existing scenery offsets/rotations. Retail source records/transforms remain immutable. Adjacent corner consumers and unknown actor preview surface sampling use the updated reference ground. These are source-derived preview heights; native ramp behavior, object visibility and live movement remain unverified.

Validation: eighteen focused Python checks passed across new floor preview composition, floor Review/history/HTTP, environment/texture projection and scene caching. Node floor decoder and existing wall guards passed; editor/module syntax checks passed. Actual retail browser workflow passed typed LUT labels, input invalidation, fresh Review, Proposed scene inspection/return, private Apply, Undo/Redo and Save/Open. Independent vertex-by-vertex comparison proved exact changed ground corners, unchanged topology/materials/UVs and the expected placed-object height delta; source transforms remained identical. Normal private Build matched the full MAP independently, preserving the existing wall bit in the same byte. Native MAP SHA-256 `25bdeeb8a832129ae434a1e072beeb24bbe9e7e2909738c38042cb1120bdb5b7`; package SHA-256 `b91a7e2c9366b65f39517d1df050ab9edf608629bc939ab8006f6216c19ddd7e`. Wide/narrow dialog screenshots were inspected; no page errors occurred. Evidence: `local-output/sdk-20260909/floor-editor-20261006/attempt2/proof.json`. The first browser attempt exposed an inaccessible modal entry point; the collision inspector entry was added before the successful fresh attempt. No game launch, runtime attachment or installation occurred. The full SDK goal remains incomplete; gameplay acceptance stays deferred.


## 2026-10-06: native floor-selector authoring backend

A distinct `FloorTiers` scene component now authors existing MAN height selectors in the MAP low nibble, independently of wall quadrants. The bounded floor rectangle service exposes read-only source-qualified Review and sealed Apply, supporting tier 0..15 or restoration to each selected retail value. Canonical floor rows/columns are 0..127, including row zero; the wall-biased row/Z convention is not reused. At most 4096 combined authored selectors are accepted. Imported MAP/MAN disc identity, MAP hash, LUT values and MAN provenance bind the Review; changed inputs or project state reject Apply.

Normal commands preserve other scene components, support one Undo step, dirty tracking, Save/Open and component review. Ordinary Build and the shared MAP composer merge low-nibble changes with wall high-nibble edits while rejecting overlapping edits; audits identify floor masks and before/after tiers. Existing LUT entries, ramp flags/records and other native spans are not changed. Shared selectors can affect neighboring surfaces and placed objects; complete live floor heights and gameplay behavior remain unverified.

Validation: four focused Python floor cases and seven existing wall rectangle/paint cases passed. Private retail HTTP Review/Apply, stale rectangle rejection, one Undo step, Undo/Redo and Save/Open passed. Independent full MAP construction matched both ordinary Build and the shared composer exactly, including wall/floor edits in the same byte. Native MAP SHA-256 `77fdc3c86a4f14bbdd7948a4734d916a6358aa23c2cf24ae72ae14666f387820`; package SHA-256 `2c21fc94ca8259ad88dd988b488e7be7e0914d53b6dc938d08443dffb30f0392`. Evidence: `local-output/sdk-20260909/floor-authoring-20261006/proof.json`. The shared composer was exercised with Town01, not with an actual appended-NPC or streaming scene. Status: writable SDK backend; editor controls and Current authored terrain/placement preview are pending next. No game launch, runtime attachment or installation occurred. The full SDK goal remains incomplete.


## 2026-10-06: repeated wall-pattern placement

Source wall patterns now support repeated rows/columns with explicit gaps in whole 128-unit native grid cells. Stage repeated pattern expands the current authored operations into one Current-baseline draft, preserving quadrant parity and all untouched gap bits. A fresh Review is required before the single atomic Apply. Counts do not change the draft until Stage; repeating again repeats the newly staged pattern. The expanded pattern remains downloadable in the existing portable format and supports rotation/mirroring.

The pure repetition service rejects invalid counts/gaps, grid extent overflow, more than 4096 operations and selected-quadrant Review extent overflow before mutating controls. Sparse gaps count toward the Review extent budget. The existing native source validation, rectangle review seals, serializer and command history remain authoritative.

Validation: both Node pattern/rectangle checks, JavaScript syntax and three focused Python paint/history/HTTP checks passed. Node coverage includes exact operation placement, gap preservation, quadrant parity, rotation equivalence, detached input and count/extent/destination rejection. Actual retail editor workflow staged a 2-by-2 pattern with gaps, downloaded its exact 12 operations, rejected oversized repetition without altering the draft, completed fresh Review and scene inspection/return, and passed private Apply, Undo/Redo and Save/Open. The Review selected 60 wall bits with seven effective changes. Independent full MAP Build readback exactly matched the intended repeated bits and a pre-existing authored gap bit; all floor nibbles and unrelated bytes were preserved. Native MAP SHA-256 `8f9440f1f32d5e842fb14e38a3e878ef4f93920bc478a40b5f3f97448def4d3b`; package SHA-256 `2f2a3d306971882239cef8a88e8f7a4769891d1c34c4b4fe09ab389962c098d9`. Wide/narrow layouts were inspected and browser errors were empty. Evidence: `local-output/sdk-20260909/wall-pattern-repeat-20261006/proof.json`. No game launch, runtime attachment or installation occurred. Gameplay acceptance remains deferred and the full SDK goal remains incomplete.


## 2026-10-06: reusable authored wall patterns

Source wall drafts can now be downloaded as portable JSON, loaded at a new First row/column, rotated clockwise or mirrored across X/Z. Patterns contain authored Block, Unblock and Restore retail operations only. They contain no captured retail/Current source bits or write authority. Loading and transforming stage a Current-baseline draft and withdraw previous Review; a fresh native Review is required before Apply. Restore retail resolves the destination's verified source value. Uniform fills retain their full operation set through export and transforms.

The strict `legaia.wall-pattern.v1` format uses relative 64-unit subcells, even bounded dimensions and at most 4096 unique typed operations. File imports are bounded to 512 KiB. Destination staging preserves the existing 4096 selected-bit Review budget, including single-quadrant selections, and rejects out-of-grid placements before changing draft controls. Invalid files preserve existing draft values and disable old Apply authority; closed or superseded readers cannot publish a draft.

Validation: three focused Python native paint/history/HTTP checks and both Node wall-pattern and rectangle programs passed. Maximum-size 4096-operation JSON round-trips within the file budget. Actual retail browser checks passed relocation, rotation, mirroring, exact download/reimport, invalid-file rejection, fresh Review, scene inspection/return, private Apply, Undo/Redo and Save/Open. Wide/narrow screenshots were inspected; no page errors occurred. Private Build readback matched all MAP bytes independently: only wall bits at byte `0x4815` changed (XOR `0x50`); every floor nibble and other byte remained exact. Native MAP SHA-256 `e2b15ff7fdf124d3979af68b6e11f49a6a7cb6905f1e5eecd5faabd4528d8aa0`; package SHA-256 `9c0b5fb9e856dc8343ee1977b9cc89edad5e847193b7863ba4ec6965e003581d`. Evidence: `local-output/sdk-20260909/wall-pattern-20261006/proof.json`. No game launch, runtime attachment or mod installation occurred. Gameplay acceptance remains deferred and the full SDK goal remains incomplete.


## 2026-10-06: source wall quadrant painting

The source wall rectangle comparison is now an editable paint workspace. `Keep Current walls; paint individual quadrants` preserves the selected rectangle's Current baseline; Block, Unblock and Restore retail brushes change individual Proposed quadrants by pointer click/drag or keyboard Enter/Space. Painting clears the previous Review and disables Apply until fresh Review. Keyboard painting retains focus. Rectangle input changes discard the paint draft. Current/Retail comparison layers remain read-only; fresh reviewed patterns can be inspected in the scene and applied as one Undo step. Scene inspection now expands Scene tools so Return to wall review is accessible.

The version-2 rectangle review binds a canonical, bounded `cell_edits` list to the same imported MAP/source/project context. Duplicate, out-of-selection, invalid and stale quadrant requests reject. The existing source wall-bit serializer merges the pattern with authored edits outside the selection and preserves all floor nibbles and unrelated MAP bytes. Uniform rectangle requests retain their version-1 contract.

Validation: twelve focused Python rectangle/HTTP/painting checks and Node rectangle/paint qualification checks passed. Actual retail browser workflow passed pointer drag, keyboard focus, retail restoration, draft invalidation, fresh Review, scene inspection/return, private Apply, Undo/Redo and Save/Open, with no page errors. Native private Build readback matched exactly: two wall bits in one MAP byte changed; every floor nibble and unrelated byte remained identical. Package SHA-256 `3410ed6f08330eca2e0866f34bedadd052f50584cbc7bec9d307f4a8cf3b1ec5`. Evidence: `local-output/sdk-20260909/wall-paint-20261006/proof.json`; wide/narrow screenshots inspected. No game launch, runtime attach or mod installation occurred. Source walls remain a static reference baseline; runtime/script collision paints, actor blockers and gameplay acceptance are deferred. The full SDK goal remains incomplete.


## 2026-10-06: Current native mesh import comparison

`Project mesh inputs` now compares each historical receipt with the complete Current native model and reports how many faces introduced by that import are active or retired. The reader requalifies the library and retained input, replays exact before/after ledger spans, checks the historical candidate hash and Current replay bytes, and seals receipt/root/mode/import/native/disc context before returning. The UI validates exact response fields and hash/count consistency. A whole-model difference can reflect later edits or imports; active face identities do not assert unchanged face content or gameplay acceptance. Comparison requests are read-only and require no active source scene change.

Validation: five focused Python checks passed (three library regressions and two comparison workflows), with the two comparison checks rerun after the final model-byte bound. Exact match, later-import difference with all original faces active, one-face retirement, Undo restoration, HTTP exact fields/stale receipt/root/key and context drift reject paths passed. Node library/comparison validation, hash truth, bounded face totals and no-write claim checks passed. Actual retail-backed browser comparison ran from another scene and matched complete SDK responses and displayed counts for a single import (1 of 2 active, 1 retired) and batch import (4 of 4 active). Independent baseline showed the batch's exact native match, and Undo restored it after private fixture retirement. Comparison reads preserved project document/history/files; original project untouched. Wide/narrow screenshots inspected. Evidence: `local-output/sdk-20260909/mesh-native-comparison-20261006/proof.json`. The private fixture used a qualified native face retirement and Undo to exercise lifetime reporting; no Build, game launch, runtime attach or installation occurred. Full SDK and gameplay acceptance remain incomplete.


## 2026-10-06: project-wide retained mesh input library

The editor now offers `Project mesh inputs` alongside the model and animation input libraries. It finds retained native mesh import GLBs and their historical single/batch recipes across source scenes, filters by scene/model/hash/import kind, recovers original GLB/settings/receipts and opens the Current model in its source scene. The SDK reconstructs each model's retained ledger inputs within a verified disc operation. Complete project/import/native context seals the library key; downloads verify fresh membership, exact receipt, byte length and independently hashed GLB. Navigation requalifies before and after changing scenes. This is read-only recovery: settings remain editable input requiring fresh Review and explicit Apply. The library supports at most 128 receipts and 64 MiB of distinct registered GLBs and refuses larger catalogs without truncation.

Validation: three new Python library checks plus five existing mesh retention checks passed, including HTTP exact-field rejection, stale project/key/mode, corrupt input, late context mutation, global budgets and no project/history/file changes. Node library decoding/filtering, exact recovery, hash-time context and qualified scene navigation passed. Actual browser proof started in `town0c`, recovered all six artifacts from two `town01` imports, filtered single/batch inputs, opened the source scene's exact authored model and verified its native SHA-256. No page errors; wide/narrow library and Current model screenshots inspected. Original and private project files, native receipts and Undo history stayed unchanged; scene selection changed as requested. Evidence: `local-output/sdk-20260909/mesh-input-library-20261006/proof.json`. No native Apply, Build, game launch, runtime attach or installation occurred. Gameplay acceptance and the full SDK goal remain open.


## 2026-10-06: recovered mesh settings become editable drafts

`Import GLB mesh` now accepts the bounded JSON downloaded by `Retained mesh sources` after a GLB is chosen. Single settings restore scene/section, unit scale, XYZ origin/rotation, UV channel, color choice and packet-group mode. Batch settings open the section donor editor with saved section selection, per-section UVs and group/object replacement choices. Both paths request a fresh SDK inventory of the selected GLB before publishing controls, clear any previous Review, and require fresh Review plus explicit Apply. Unavailable Current triangle donors remain unselected; no donor is substituted. Unknown fields, invalid bounds, missing sections/scenes/UVs and conflicting mappings reject.

Validation: new Node settings decoder/qualification checks and the existing recovery/download Node checks passed; all five Python mesh source retention/history/HTTP tests passed. Actual browser checks restored both saved recipes, rejected malformed settings without changing draft choices, required missing-donor reselection, and completed fresh single and mapped Reviews. No Apply, project/history/file mutation, game launch, runtime attach or installation occurred. Wide and narrow screenshots inspected. Evidence: `local-output/sdk-20260909/mesh-settings-draft-20261006/proof.json`. Gameplay acceptance remains deferred; the full SDK goal is incomplete.


## 2026-10-06 checkpoint: verified mesh import settings recovery

Retained mesh sources now downloads a separate import-settings JSON alongside the
original GLB and complete receipt. All three artifacts requalify the Current SDK
receipt and original source bytes before publication; selected receipt metadata
must match the displayed snapshot, and GLB length/SHA-256 must match independently.
The panel validates receipt fields, ledger spans, unique identities and recipe
shape, returns detached data and rejects stale context before and after hashing.
Closing it aborts pending reads; concurrent artifact downloads are suppressed.
Superseded reads cannot notify a later context. Loading punctuation is corrected.

The parent Import GLB mesh dialog disables Retained mesh sources until its source
is ready, avoiding an enabled button whose early click was silently ignored.
Recovered settings remain historical: choose Current donors and Review again for
a new import. No receipt is replay authority and no native format changes.

Five focused Python source-retention checks and the new Node recovery check passed.
The full editor resource-browser path recovered six exact files from saved single
and batch imports; wide/narrow views were inspected, with no page errors. Project
files, native content and history remained unchanged. Proof:
`local-output/sdk-20260909/mesh-settings-recovery-20261006/proof.json`.
No native Apply, Build, game launch or runtime attachment was used. This workflow
needs no immediate gameplay verification. The full SDK goal remains incomplete.


## 2026-10-06 checkpoint: mirrored model GLB transforms

Current-profile fixed-layout model editing now imports signed nonzero axis scales
and reflected static TRS/matrices through parent hierarchies. Positions bake into
native source coordinates. Inverse-transpose normal directions retain their
stored magnitude, including the determinant sign. The final composed orientation
controls winding: reflected native triangles/quads exchange corners 1 and 2,
carrying vertex references, UV bytes, Gouraud RGB and Gouraud normal references
together. Flat fields, material words, command bytes, padding, capacities and
source provenance stay fixed. Two cancelling reflections do not reverse faces.
Local/composed scale magnitude limits and integer-domain checks remain in force.
Legacy GLB profiles reject reflected objects; current v6 has every required field.
Animation/skinning and local matrix shear remain unsupported by this model path.

Validation: 70 focused Python tests and three Node checks passed, including all
24 packet families against independent native packing, nondegenerate quad winding,
signed normal orthogonality, TRS/matrix equivalence, cancellation, mixed objects,
legacy rejection, retained additions/removal bases and ordinary history. Actual
browser Review -> proposed textured preview -> Return -> Apply passed with a fresh
Town01 model0009 export, renamed/reordered objects and a reflected nonuniform
matrix parent. Wrong Review/zero scale/stale binding rejected. Undo/Redo and
Save/Open preserved the exact candidate. Normal private Build independently
decoded to the expected model; neighboring container bytes remained unchanged.
Proof: `local-output/sdk-20260909/model-glb-reflection-20261006/proof.json`.
Build `4d46cd1c3a7a6abb`, package SHA-256
`7510b165dfddc87adacd5ec79a4005d1d284ef97a73c7fa80c44b888f50ed8d0`.
Native model SHA-256
`886d5dfa69b1c78dec6329be19a8523e2cfbb24cd3138a09cef41cd671e5445e`.
No game launch, runtime attachment or installation occurred. In-game rendering
and lighting verification stays deferred; it does not block further offline
SDK work. The full SDK goal remains active and incomplete. This supersedes earlier
reflection exclusions for current-profile fixed-layout model imports.


## 2026-10-06 checkpoint: bounded model container reuse during scene generation

Cold scene generation now reuses immutable decoded model LZS sections within one
verified disc operation. The cache belongs to that operation's PROT archive and
retains at most eight sections / 16 MiB. It clears on successful or failed exit;
new operations still hash the entire supported disc. Every model read still
checks its disc identity, entry/section identity, compressed-stream offset,
containing size and byte span. Raw PROT model reads retain their existing path.

A fresh Town01 sample improved from 19.445 to 11.611 seconds (about 40 percent).
Model-container decompressions fell from 118 to 2. The complete normalized preview
hash matched before/after, including 261 entities, 119 geometries, 17,970 triangles
and decoded texture data. These are local samples, not a general latency guarantee.
State refresh was already about 0.258 seconds and required no change.

Validation: 50 focused Python checks passed, covering locator rejection after a
cache hit, immutable section reuse, section separation, count/byte eviction,
oversized items, decoder failures, context cleanup, real full-hash rejection,
scene transforms and model proposal workflows. Fresh real-disc SDK HTTP cold/warm
scene requests matched the prechange preview; separate model reads each hashed
and decoded afresh. Project files and history stayed unchanged. Proof and timings:
`local-output/sdk-20260909/editor-state-batching-20261006/{proof,before,after}.json`.
No game launch, runtime attach or native Apply was used. No immediate gameplay
verification is needed for this response-preserving change; existing manual
scene/runtime acceptance remains pending. The full SDK goal remains incomplete.


## 2026-10-06 checkpoint: saved animation input native content comparison

Project animation inputs now offers Compare current native clip. Imported inputs
compare the exact shared scene-ANM clip recorded by the receipt, independently of
the source actor's later initial assignment. Retained inputs reconstruct the exact
UUID from verified frozen donor data and current edits. The panel separates byte
matches from active/retired membership in the authored native bank; retired captures
remain readable without restoring or emitting them. It shows current clip identity,
hash and frame/object counts. Matching bytes do not authorize stale binding replay
or establish runtime playback/timing.

The read-only route verifies receipt/library/root context, Retail record/model
witnesses, native ledger content, rigid-profile/byte bounds, selected scene evidence
and disc path. Comparison does not navigate the active scene or modify project,
source inputs, native content, history or files. Recovery remains separate from
this disc-dependent qualification.

Verification: 19 focused Python tests and five Node checks passed. A strengthened
profile rejection also passed in the twelve-test source module rerun. Actual editor
checks, while town0c remained active, identified both matching and older town01
shared inputs and compared the retained UUID as active and then retired. A normal
private retirement followed by Undo restored emitted-bank membership; comparison
operations themselves preserved every project file and authoring/history collection.
Fresh SDK HTTP readback confirmed the final profile bounds. No Build, mod install,
runtime attach or game launch was performed for this read-only feature.
Evidence: `local-output/sdk-20260909/animation-source-comparison-20261006/proof.json`.
The full SDK goal and manual gameplay acceptance remain open.


## 2026-10-06 checkpoint: saved animation input source navigation

Project animation inputs now exposes Open source actor for imported inputs and
Open retained source clip for retained inputs. Navigation verifies the receipt and
project library before and after switching to its source scene. Actor inputs select
the exact source entity in the normal hierarchy/viewport/inspector. Retained inputs
refresh the SDK asset catalog and open the exact retained UUID through its existing
inspector, including current preview, content/GLB editing and lifecycle controls.
Captured clip identity stays separate from an actor's current assignment.

Five Node checks passed. An actual private retail editor workflow started from
town0c for both paths, selected the town01 source actor, opened the exact retained
clip, and downloaded a fresh retained GLB binding through the normal authoring UI.
Native overrides, retained inputs, history and non-export files stayed unchanged;
the explicit export generated normal files under Exports. Stale/missing/duplicate
actor or clip targets, wrong asset types and changed library contexts reject.
No native Apply, Build, runtime attach or game launch was performed for navigation.
Evidence: `local-output/sdk-20260909/animation-source-navigation-20261006/proof.json`.
The full SDK goal and manual gameplay acceptance remain open.


## 2026-10-06 checkpoint: historical model input versus current native content

Project model inputs now offers Compare current native model. The read-only SDK
operation verifies the selected receipt, matching retail disc, imported source
model and current replacement bytes, then reports the Retail source hash, current
native hash/size, Retail or authored representation and whether the historical
candidate matches current content. It uses the receipt's source scene without
changing active scene or selection. Recovery itself still does not require this
comparison. A byte match does not make a historical binding valid for replay.

Disc-path, imported-evidence and library changes during comparison reject. Exact
HTTP fields, receipt identity and current result claims are qualified by the SDK
and browser. Missing discs, missing receipts and stale keys fail without writes.

Verification: 33 focused Python tests and five Node checks passed; the strengthened
disc-path race assertion also passed in the eight-test source module. Actual editor
checks in a private project compared a town01 receipt while town0c remained active,
showed matching authored content, showed a difference after one qualified private
vertex edit, and returned to matching after Undo. Each comparison preserved project
state, receipt metadata, history and every project file. An encoding regression in
panel punctuation was caught by visual inspection and corrected before the final
browser pass. No Build, mod installation or game launch was performed for this
read-only feature.
Evidence: `local-output/sdk-20260909/model-source-comparison-20261006/proof.json`.
The full SDK goal and manual gameplay acceptance remain open.


## 2026-10-06 checkpoint: saved model input to source inspector navigation

Project model inputs now provides Open model in source scene. The editor verifies
the exact historical receipt against the current library, navigates to its imported
scene, requalifies project/mode/library after navigation and verifies membership in
the current model asset inventory. It opens authored geometry when an override is
present, otherwise Retail. Pending model edits, busy/stale project contexts,
missing receipts and absent or wrong-type target assets reject navigation.

The workflow opens the normal model inspector and current GLB export controls;
it does not replay historical input bindings. Five Node checks passed, including
navigation races and membership guards. An actual private retail editor workflow
started in town0c, navigated to the saved town01 model, inspected authored geometry
and downloaded a fresh binding matching its native candidate. History, native
content, receipts and all non-export project files stayed unchanged. The normal
export generated files under Exports, as intended. The first verifier incorrectly
included those expected generated files in its unchanged-file assertion; the
completed proof qualifies them separately. No native Apply, Build or game launch
was needed for this navigation feature.
Evidence: `local-output/sdk-20260909/model-source-navigation-20261006/proof.json`.
The full SDK goal and manual gameplay acceptance remain outstanding.


## 2026-10-06 checkpoint: project-wide model input library

The editor now exposes Project model inputs beside the project browsing tools.
Saved original GLBs, bindings and receipts can be searched by scene, model identity
or hash across all recorded scenes, without changing the active scene or selecting
the original model. Scene filters, receipt/unique-file/registered-byte totals,
SHA-qualified downloads and explicit reviewed removal are integrated in one panel.
Live mode permits recovery; removal requires Edit mode and creates one Undo/Redo
step. Native model content and physical GLB files remain intact.

The SDK library qualifies every registered file and binds root, mode, complete
receipt collection and native model overrides into its library key. Stale keys,
wrong project roots, missing receipts, changed files and extra request fields
reject. Empty projects remain supported; existing receipt budgets still apply.

Verification: 31 focused Python tests and five Node checks passed. A private retail
project copy passed actual browser search, three independently verified downloads,
Review/removal, one-step Undo/Redo, Save/Open, Build snapshot omission and independent
native package/neighbor-byte readback. Cross-scene/shared-input behavior was checked
in unit tests. Initial browser proof clicked during startup before any mutation;
the completed proof waits for the editor startup response.
Build `f002edf888522d59`, package SHA-256
`8dc79289873e9591ac09d1e90912a32ba49553cd3edccae41b45a69e3f0a51b4`.
Evidence: `local-output/sdk-20260909/model-source-library-20261006/proof.json`.
Physical orphan cleanup remains open. No game was launched; manual gameplay checks
and the full SDK goal remain outstanding.


## 2026-10-06 checkpoint: reviewed model input receipt removal

The retained model inputs dialog now offers Review followed by explicit removal of
a selected receipt. Review binds the project context, complete receipt collection
and native project document. Removal creates one metadata-only Undo/Redo step;
the authored native model and original GLB file remain intact. Shared inputs free
registered byte budget only when their last receipt is removed. Physical orphan
cleanup and a project-wide model input library remain open.

Verification: 30 focused Python tests and four Node checks passed. A private
project copy passed actual editor Review/removal, wrong-key/extra-field/repeat
rejection, one-step Undo/Redo, Save/Open and omitted removed inputs in Build
snapshots. Independent package readback matched the unchanged native model and
all neighboring decoded bytes. Shared-blob accounting was checked in unit tests.
Build `402f72dba263da9a`, package SHA-256
`19d4b2d34b285dd3949eed1014162f423cb7e84f3d7427b57272ea25302afee4`.
Evidence: `local-output/sdk-20260909/model-glb-source-removal-20261006/proof.json`.
No game was launched; gameplay verification and the broader SDK goal remain open.


## 2026-10-06 checkpoint: original model GLB input retention and recovery

Successful fixed-layout model GLB Apply now retains the exact original GLB,
source binding (including explicit node mapping), proposed native hash and Review
key in a sealed historical receipt. Native publication and receipt metadata form
one grouped Undo/Redo step; failure restores both collections and history. Immutable
source files remain available for Redo. These inputs are historical recovery data,
not replay authority: export a fresh binding and Review before applying again.

Projects optionally persist `model_sources` (32 receipts, 32 MiB per GLB, 64 MiB of
distinct inputs). Save/Open checks receipt identities, file lengths/hashes and
mapping bounds. Registered GLBs under `Authored/Models/GLBSources` travel through
project copies and Build input snapshots; source receipts contribute to authored
state keys. Empty/legacy collections preserve previous document/key shapes. The
native replacement/package formats and retail source cache remain intact.

The model GLB dialog provides Recover model inputs with verified downloads of
original GLB, binding JSON and receipt JSON. Recovery is read-only, context-bound,
SHA-qualified and guarded against close/abort and stale busy ownership. No implicit
re-import or physical source-file deletion occurs. Receipt removal, project-wide
model input browsing and orphan-file cleanup remain future work.

Validation: 98 focused Python tests and four Node checks passed. A strengthened
retail HTTP Apply check directly asserts exact GLB/binding/candidate receipt
publication. Source corruption, receipt/mapping tampering, budgets, rollback and
Undo/Redo persistence are covered. The actual private retail model workflow
completed Review/Preview/Return/Apply; its subsequent recovery proof initially
tried the closed owner dialog. The applied fixture was independently requalified
and restored from immutable native/source blobs before Save, without repeating
native Apply. A fresh read-only resource-browser session downloaded all three exact
inputs. Recovery screenshot inspected. Undo/Redo, Save/Open, project copy, Build
input retention and independent native TMD/neighbor readback passed.

Evidence: `local-output/sdk-20260909/model-glb-sources-20261006/proof.json`.
Build: `4afce3b9c89bd196`.
Package SHA-256: `fdbdacb0da2b0f3cd937326bd2a4a649707d0fb64beb10b67956fd334cabee90`.
Native TMD SHA-256: `ebc9882475655eda330d4aa9f49b7e5277b522c4b3e3862890652a8e42fa129e`.
No game launch, mod installation or retail-disc export occurred. Gameplay remains
deferred; solo work and the full SDK goal remain active and incomplete.


## 2026-10-06 checkpoint: explicit external model object mapping

Model GLB authoring now accepts an optional ordered `external_object_nodes`
binding choice. This recovers renamed/reordered external nodes after source
extras are removed, while preserving complete native object ownership. One
distinct GLB node is required per native object (including empty objects), within
0..1023. Existing source tags/canonical names must agree; detached, unowned,
duplicate and conflicting nodes reject. Source corner attributes, topology,
normal/vertex aliases, material masks and integer/transform bounds remain active.
This does not import arbitrary meshes without source attributes or allocate new
objects, packets, skeletal channels or images.

The dialog exposes mapping text and bounded node index/name inventory. Mapping
changes withdraw Review; pending operations lock the control. The Review digest
seals the choice even if different mappings produce identical native bytes.
Proposed-model inspection/Return retains it. Material-face selection uses the
same qualified mapping after exact native no-op verification. Default source
binding and Review shapes remain unchanged when the choice is omitted.

Validation: 57 focused Python checks and three Node checks passed. A private
retail town01 model 0009 fixture used untagged, renamed, reversed object nodes,
explicit mapping [4,3,2,1], nonuniform parent scale and a rotated child. Actual
resource-browser Review, mapping-change invalidation, proposed-model inspection,
Return, Apply, Undo/Redo, Save/Open and normal Build passed. Independent native
positions and inverse-transpose normals matched complete TMD readback; 21 normal
slots changed and neighboring decoded bytes/retail inputs remained unchanged.
A separate Current no-op mapped material selection qualified 103 native faces
without changing project files or history. Invalid/missing mapping, zero scale,
wrong Review and stale binding requests rejected before mutation.

Evidence: `local-output/sdk-20260909/model-glb-object-mapping-20261006/proof.json`
and `material-proof.json` in the same directory; mapping controls screenshot inspected.
Build: `467769b5cc21a856`.
Package SHA-256: `edd3eaa96ae7f83b5dba686320e91e179725a1c81bd3eb9085c4f4162c4509f3`.
Native TMD SHA-256: `ebc9882475655eda330d4aa9f49b7e5277b522c4b3e3862890652a8e42fa129e`.
The first browser attempt found a missing module route before Apply; it was fixed.
Subsequent proof waits were corrected to scope Apply to the model dialog; saved
project state was checked unchanged before resuming. No native edit was repeated.
No game was launched or mod installed. Gameplay remains deferred; solo work and
the full SDK goal stay active and incomplete.


## 2026-10-06 checkpoint: measured composed model scale bounds

Model GLB hierarchy qualification now measures the actual composed singular
scales instead of multiplying conservative ancestor axis minima/maxima. This
admits reciprocal nonuniform parent/child scales whose final transform is valid.
Local axes and every composed ancestor remain bounded 1/1024..1024; excessive
intermediate transforms still reject. A bounded one-sided Jacobi calculation
preserves small-axis precision without squared normal equations or a new runtime
dependency. Floating-point endpoint allowance is 64 ulps of the largest measured
scale. Native geometry, normal transforms, quantization and review formats stay
unchanged. This supersedes the earlier conservative cancellation limitation.

Validation: 53 focused Python checks and both model GLB Node checks passed.
Analytic composite-shear singular values, reciprocal native no-op, out-of-range
composition and rotated boundary/over-limit cases are covered. A final-code
read-only HTTP check accepted the saved Current fixture as a native no-op with
project files/history unchanged; 100 rotated extreme-axis fixtures passed.

A fresh private town01 project used axes [1024,1/1024,1] followed by reciprocal
child axes and an independently packed native translation of model 0009. The
actual resource browser completed Review, proposed model inspection, Return and
Apply, followed by Undo/Redo, Save/Open and normal Build. Complete native TMD
readback matched; normals, decoded neighboring bytes and retail inputs remained
unchanged. Invalid scale, incorrect Review and stale bindings rejected.

Evidence: `local-output/sdk-20260909/model-glb-composed-scale-20261006/proof.json`
and `final-code-proof.json` in the same directory.
Build: `3594b3faedff0fe6`.
Package SHA-256: `c4e265df8ceceda9d3b8e4abf296233f58e445fa82792c2bc829b4523eb0b917`.
Native TMD SHA-256: `96e94ff3778b07af810b88dc9640c09dd699da2ddda8c3205773813b30328b28`.
The proposed model screenshot was inspected. No game was launched or mod
installed. Gameplay remains deferred; the full SDK goal is active and incomplete.


## 2026-10-06 checkpoint: positive nonuniform model scale

Fixed-layout model GLB imports now bake positive per-axis node scale through
TRS or affine matrices that decompose into local TRS. Parent and child linear
transforms compose fully, including the nonorthogonal basis produced by a
rotated child under nonuniform parent scale. Normals use inverse-transpose
direction and restore their original raw magnitude before signed-i16 rounding;
uniform-only hierarchies retain the existing rotation path. Zero and negative
scale, local matrix shear, reflection and perspective reject. Animation imports
still require unit scale. Composed bounds use conservative products of local
axis minima/maxima within 1/1024..1024; extreme cancelling transforms may reject.

Validation: 48 focused Python checks and both model GLB Node checks passed.
A fresh private town01 project exercised the actual resource browser, GLB Review,
proposed model inspection, Return, Apply, Undo/Redo, Save/Open and normal Build.
Retail model 0009 used nonuniform parent scale and a rotated, nonuniform child.
Independent position and inverse-transpose calculations matched the complete
native TMD; 21 normal slots changed. Decoded neighboring bytes and retail input
remained unchanged. Invalid scale and stale bindings rejected before mutation.

Evidence: `local-output/sdk-20260909/model-glb-nonuniform-scale-20261006/proof.json`.
Build: `41c2164f505b1d0c`.
Package SHA-256: `45d8f215188cfb5b694ec180808c0a3df3b52572d0f5c449962790f641c27631`.
Native TMD SHA-256: `ebc9882475655eda330d4aa9f49b7e5277b522c4b3e3862890652a8e42fa129e`.
The proposed model browser screenshot was inspected. No game was launched or mod
installed. Gameplay appearance remains deferred; the full SDK goal is active
and incomplete. This checkpoint supersedes earlier nonuniform-scale exclusions.


## 2026-10-06 checkpoint: positive uniform model scale

Fixed-layout model GLB imports now bake positive uniform node and parent scale
through TRS or uniformly scaled affine matrices. Model-specific transform
composition multiplies child translations by parent scale before rotation, and
bakes composed scale into represented positions. Raw normal magnitudes stay
intact; normals use only the composed rotation. Local and composed scales are
bounded 1/1024..1024, alongside the existing native signed-i16, alias, topology,
source ownership and capacity checks. Zero/negative TRS scales, nonuniform scale,
shear, reflection and perspective reject. Animation GLB retains unit scale.

Validation: 44 focused Python checks and both model GLB Node checks passed.
The actual resource browser completed Review/Pose/Return/Apply for a retail model
with scaled parent matrix, fractional object scale and translated child. Exact
independent native calculations covered all represented positions, and its
44 lit normal operands stayed intact. Identity-scale no-op, native
material-face qualification, nonuniform and excessive scale rejection, wrong
Review and stale binding rejection passed. Ordinary native authoring remained one
history step, with exact Undo/Redo and Save/Open.

Normal Build `0619403f0e09be22` package SHA-256:
`9b5d470ac05ab943d248b5abfc6dbad081a553deefb240f85e79f80d684f935d`.
Independent native model readback matched
`c9c6464c58d7616929443da00bbe29bbd75e7f8c83a9d1b2dc30346819f9cf46` exactly; neighboring
decoded bytes, imported metadata and retail source remained unchanged.
Evidence: `local-output/sdk-20260909/model-glb-uniform-scale-20261006/proof.json`,
`browser-proof.json`, `proposed-model.png` and `review-returned.png`.
No game launched. Scene placement, native animation timing and gameplay lighting
are separate concerns; gameplay verification remains deferred. Full SDK goal
remains active, including nonuniform scale, general skinning and reported gaps.


## 2026-10-06 checkpoint: fixed-layout model rigid hierarchy baking

Static rigid GLB object transforms and parent groups now bake into existing native
positions and stored normal words through the reviewed model workflow. Parent-first
TRS/matrix composition shares the bounded animation hierarchy implementation, with
model-specific one-scene, 1024-node, complete reachability and source ownership
checks. Stored normals rotate through native/GLB axes without normalization;
unlit sentinels, unused vector slots, padding, packet layout and opaque bytes stay
intact. Scale, shear, reflection, perspective, animation and skinning reject.
Legacy lit profiles without normal authoring reject rotation; unlit legacy objects
and translation retain their field scope. Scene placements are not changed.

Validation: 39 focused Python checks passed with the retail disc configured and
both model GLB Node checks passed. The actual resource browser completed
Review/Pose/Return/Apply for a transformed retail wall model. A second lit retail
model, `asset://town01/models/scene-tmd/0013`, passed exact SDK/HTTP pose,
Review and Apply with 8 referenced normal slots. Both ordinary native
commands passed exact Undo/Redo and Save/Open. Identity parent no-op, native
material-face qualification, wrong Review and nonrigid rejection passed.
Normal Build `6a80be847d43ac0b` package SHA-256:
`bfcceace5790ef8dab37eb0f1d366b00b4e972f96e6b6a202d135eec1679a971`.
Independent native readback matched both TMD candidates:
`9224765f5ab7336f86f926b0c43696905a168baf3c3737c2edc1c675f3b11b4d` and
`c4fa5ea4f473f1c1264ffc2bd0753aab7ed7f2ea4b9cd015127176242fad2615`.
Every unedited decoded bank byte and retail/imported source remained unchanged.

Evidence: `local-output/sdk-20260909/model-glb-rigid-hierarchy-20261006/proof.json`,
`browser-proof.json`, `proposed-model.png` and `review-returned.png`.
Initial expected-byte checks were corrected to preserve unused native vector slots.
The extra lit-model proof resumed the completed saved editor state after selecting
an unlit NPC and correcting proof-only donor discovery; no completed native edit
was repeated. No game launched. Gameplay appearance and retail lighting remain
unverified; full SDK buildout remains active, including general skinning, packet
allocation and the other reported feature gaps.


## 2026-10-06 checkpoint: model GLB object identity survives external names

Fixed-layout model GLB editing now resolves preserved source-object tags before
canonical object-N name fallback. Tagged nodes may be renamed, unnamed, reordered
or use reordered mesh indices. Malformed, duplicated and out-of-range identities
and canonical name/tag contradictions reject. The existing flat scene, complete
object coverage, topology, transform and source alias checks remain unchanged.
Material image-to-native-face selection uses the same resolver after its complete
Current model qualification; source tags do not establish retail ownership.

Validation: 35 focused Python checks passed with the retail disc configured;
both model GLB Node checks passed. A private town01 model went through the actual
resource browser and Review/Pose/Return/Apply. Native commands remained one history
step, with exact Undo/Redo and Save/Open. Renamed baseline no-op, material-face
qualification, conflicting tag rejection, wrong Review rejection and stale binding
rejection also passed. Normal Build `84131c7a8e37f333` produced package SHA-256
`c912aeb56aaa12c18e739e4a8c5c5abd33badf8f423ca89854ed9295c76ff3d7`. Independent native TMD
readback matched `b67a8c302a03a9586f80996e64ec6c03b2160f4bb4f836417457aad98cd1c3db` exactly;
neighbor decoded bytes and imported/retail data stayed unchanged.

Evidence: `local-output/sdk-20260909/model-glb-node-identity-20261006/proof.json`,
`browser-proof.json`, `proposed-model.png` and `review-returned.png`.
The first browser check stopped before Apply on an incorrect proof-only close
selector; terminal state and unchanged saved native data were verified before
correcting it and completing the workflow. No game launched. Manual visual
acceptance remains deferred; the complete SDK goal remains active. This feature
does not add model hierarchy, arbitrary packet allocation or skeletal skinning.


## 2026-10-06 checkpoint: external animation time sampling

Implemented optional external GLB sampling in both imported and retained animation
workflows. Choose a start time (0..3600 seconds) and rate (-16..16): negative rates
sample in reverse, zero holds a pose, and out-of-range samples hold endpoints.
Native frame count and playback timing remain unchanged. Longer external clips
require this explicit choice; ordinary imports retain the existing duration guard.
The choice is bound to Review and original-input receipts, separately from retail
identity. Changing it invalidates Review even if native output would be identical.

Validation: 65 focused Python checks and 8 Node checks passed. Actual editor
workflows passed Review/Pose/Return/Apply, exact input recovery, Undo/Redo,
Save/Open and reopened project copies for both animation kinds. A separate
read-only browser check verified sampling and mapping invalidation, invalid input
blocking, and final control layout. Fixed float32 STEP boundary sampling by
rounding the exported native frame clock before applying start/rate; a 15-frame
round-trip regression covers it.

Evidence: `local-output/sdk-20260909/animation-glb-sampling-20261006/proof.json`
and `sampling-ui-proof.json`. Normal Build `951632452fa96414`, package SHA-256
`3dfaac2d58a6379f17ad5d4ed2d0eaa121373a2d4c30f5d9b4d5cd85a95af166`.
Independent native ANM bank readback matched authored composition exactly:
`b478a4e572459b837ae2be01b1eb94c160cec9aad4b1952c602e1123a356009d`.
Reference project unchanged; game not launched. Manual animation/gameplay
acceptance remains deferred. Full SDK goal remains active; general skinning,
automatic retargeting, native playback timing and other reported gaps remain open.


## Explicit external rigid-object animation mapping - 2026-10-06

Both animation GLB editors now accept an optional ordered list of external GLB
node indices, display bounded node names/indices, and invalidate Review after
mapping changes. This permits renamed, reordered rigid rigs without exported
source tags. Each native object maps to one distinct reachable node; wrong
counts, duplicate/out-of-range/boolean indices and contradictory preserved
source identities reject. Hierarchy baking, native quantization, signed12
bounds, unchanged opaque/layout bytes and existing ownership checks remain.
The optional binding authoring choice `external_object_nodes` is separated from
retail binding qualification, included in Review identity (even for identical
native outcomes), and retained in original-input receipts. Save/Open and copies
preserve it. This is rigid-node mapping, not skeletal/skinned retargeting.

**Verified:** 59 focused Python checks and seven Node editor checks passed.
Private retail workflows for both imported actors and retained UUID clips used
renamed/reordered untagged rigs, explicit mapping, selected-clip Review/Pose/
Return/Apply, exact source recovery, single-step Undo/Redo, Save/Open and actual
project-copy reopening. A fresh read-only browser check verified invalid-map
blocking, mapping-change Review invalidation and corrected narrow-layout labels.
Normal Build `6a151206eecda995` passed independent native-bank readback
(SHA-256 `417cb5b4e63e551cf600333b3fc4373fe8b639cb3ab391bad85839343fd8dd02`).
Package SHA-256 `4a7fec8d35731fc0de84aef21097bff25f35943518108760cce89e7421c4c37f`.
Evidence: `local-output/sdk-20260909/animation-glb-object-mapping-20261006/`.
A copied browser-label encoding error was corrected before Apply; the feature
label encoding was then corrected and checked in a fresh browser. Reference
inputs remained unchanged. No game was launched. Full SDK completion, skeletal
retargeting/skinning and retail animation playback/timing remain open.


## Project-wide animation input browser - 2026-10-06

The Asset database tools now expose **Project animation inputs**. The SDK
catalogs all Current animation input receipts independently of active scene or
actor selection, verifies referenced files once per distinct blob, and reports
receipt/file/registered-byte totals. Search matches scene, target, kind and
hash; the scene filter preserves recorded source identities. Original GLB,
parsed binding and receipt downloads recheck project/library identity and exact
source hashes. Historical inputs remain separate from native authoring authority.
Edit mode offers reviewed receipt removal, automatic catalog refresh and one
Undo/Redo metadata command. Library keys bind project root, mode, receipts and
native overrides; changed inputs reject pending recovery/removal operations.

**Verified:** 55 focused Python checks and five Node editor checks passed.
A private retail editor workflow with no active scene recovered all nine files
from three imported/retained receipts, filtered results, reviewed/removed an
input and refreshed the open browser. Undo/Redo, Save/Open and an actual project
copy preserved Current and native overrides. Normal Build `2274e2fa360d4ac7`
passed independent native-bank readback; native bytes are unchanged (SHA-256
`3abfb27bb04dde0e553dafe0c683509eb873856b48136776d1485139d1d3f384`). Package
SHA-256 `52ac5f3faaabe999b80baeb0fb32effc63e0094f37894e51eba638835025ca87`.
Evidence: `local-output/sdk-20260909/animation-source-library-20261006/`.
The browser fixture initially targeted a responsive tab hidden at desktop width;
that was corrected before mutation. Verification later resumed from saved state
to accommodate existing Open behavior that selects the first imported scene.
No edits were repeated and no game was launched. Physical orphan-file cleanup,
full SDK completion and retail animation playback/timing remain open.


## Animation source receipt management - 2026-10-06

Both animation GLB editors now offer Review source removal and an explicit
Remove reviewed source receipt action. Review binds the target, active scene,
source key, full receipt collection and native authored overrides. Apply uses
ProjectService commands, removes only the receipt from Current and creates one
metadata Undo/Redo step. Shared blobs free registered-byte budget only after
the last Current receipt is removed. Local GLB files remain available for Undo;
this feature does not reclaim physical disk space or revert native animation.
Save/Open and project copies persist the remaining referenced receipts/files.

**Verified:** 53 focused Python checks and four Node editor checks passed.
Private retail browser workflows for imported actors and retained UUID clips
passed Review/Apply, one-step Undo/Redo, stale-review rejection and parent-editor
closure. Narrow recovery dialogs were visually checked. Save/Open and actual
project-copy reopening preserved Current. Normal Build `fa3db4c512283b8c`
passed independent native-bank readback; the bank is unchanged from the input
project (SHA-256 `3abfb27bb04dde0e553dafe0c683509eb873856b48136776d1485139d1d3f384`).
Package SHA-256 `9adfef330764716b7920ba695eb7eb947b08cfbff4c0e93d3dbcd5d31469b95c`.
Evidence: `local-output/sdk-20260909/animation-source-management-20261006/`.
A diagnostic filename mistake stopped the first verifier after Save/Open and
copy assertions; verification resumed from saved state without repeating edits.
No game was launched. Physical blob cleanup, project-wide library browsing,
full SDK completion and retail playback/timing acceptance remain open.


## Animation source retention and recovery - 2026-10-06

Both imported-actor and retained UUID GLB Applies now retain exact source GLB
bytes and parsed binding/clip/mapping receipts in the project. Source receipt
and native overrides share one atomic Undo/Redo history step. Save/Open checks
receipt seals and source hashes; export inputs and project copies include the
referenced sources. Build-input identity includes populated receipts while
legacy projects keep their previous key shape. Recovery dialogs download the
GLB, parsed binding and receipt; browser hashing verifies the exact GLB.
Receipts are historical inputs, not replay authority: fresh binding/Review is
still required for authoring. Metadata and blob bounds are 32 receipts, 64 MiB
of distinct GLBs and 32 MiB per file; shared blobs are verified once per scan.
Native serializers and imported retail provenance are unchanged.

**Focused checks:** 51 Python checks and four Node editor checks passed. Guards
cover tampering/missing inputs, identity/mapping, count/byte bounds and native
command failure rollback. Full workflow proof is retained beneath
`local-output/sdk-20260909/animation-glb-sources-verified-20261006/`.
Both browser workflows passed Review/Pose/Return/Apply and recovered exact
GLB bytes, parsed bindings and receipts. One-step Undo/Redo, Save/Open and
actual project-copy reopening passed with source metadata and bytes intact.
Normal Build `34c90e71595b063f` passed independent native-bank readback
(SHA-256 `3abfb27bb04dde0e553dafe0c683509eb873856b48136776d1485139d1d3f384`);
package SHA-256 `91f5264f1d31e7426027882adcb4ee4bcd7f5d5174415b5abcccceda0b5eaf0d`.
The reference project remained unchanged. No game was launched.

Receipt pruning/source-library management remain incomplete, along with the
full SDK goal and retail animation playback/timing acceptance.


## Static rigid GLB matrix support - 2026-10-06

Animation GLB import now accepts static rigid matrices on source objects and
ancestors, decomposing column-major affine transforms into translation and
normalized rotation before hierarchy baking. The basis must be orthonormal
and determinant +1 within 1e-5 float32-noise tolerance; huge/malformed numeric
values, scale, shear, reflection and perspective reject. Mixed matrix/TRS and
any animated matrix node reject. Source mapping, selected-clip Review binding,
native quantization, opaque bytes and the original output layout are retained.

**Focused checks:** 45 Python checks and two Node editor checks passed. Matrix
fixtures preserve native bytes for identity, 180-degree and arbitrary rotations
including float32 conversion, and match independent TRS hierarchy outcomes.
Negative cases cover all unsupported matrix classes and animated/mixed nodes.
Pinned `2f64b0c5` rejects the same transformed static matrix that now produces
an exact native no-op. Private retail editor and Build evidence is beneath
`local-output/sdk-20260909/animation-glb-rigid-matrix-20261006/`.
The full SDK goal and retail animation playback/timing remain unverified.

Both real retail browser workflows passed selected matrix-parent clip Review,
Pose/Return, selection invalidation and Apply, each in one Undo step. Undo/Redo,
Save/Open and byte-for-byte reference preservation passed. Normal Build
`521d41100d73ea0c` produced package SHA-256
`33796273faff464cef510d424b1df1c77e59714200badd82ee2f0142b436807e`.
Independent relocated-carrier decompression exactly reproduced the authored
animation bank SHA-256
`6c1bd95f47855b285e17f3f928fd07b652d894f8fbe3b8c5bc7c92970e4716a2`.
No game launch, installation or full-disc export occurred.


## Rigid GLB parent-transform baking - 2026-10-06

GLB animation import now composes static and animated ancestor TRS into each
source object's scene-space pose before native quantization. Mapped parents
and shared ancestors work without inventing native skeleton fields. Quaternion
composition applies parent before child; parent rotation also rotates local
translation. Whole-file/source/clip Review binding and existing contribution
and retained-record serializers remain unchanged. Only mapped objects and their
ancestors are sampled, in iterative parent-first order, with a 65536 total
sampled-node bound. Unit-scale, matrix, cycle, unique-parent, target, accessor
and native-coordinate qualification remain explicit. Skinning, nonidentity
matrices and general skeleton retargeting remain unsupported.

**Focused checks:** 41 Python checks and two Node editor checks passed. Independent
expectations cover rotated translations, noncommuting rotations, animated
ancestors, mapped parents, exact native/opaque reparented no-ops, composed
overflow, unrelated targets and iterative depth/work limits. Pinned `0f1fbe1a`
rejects the same transformed-root fixture that now preserves native bytes.
Private retail editor and Build proof is retained beneath
`local-output/sdk-20260909/animation-glb-hierarchy-20261006/`.
The full SDK goal and retail playback/timing acceptance remain incomplete.

Both private retail browser workflows passed selected hierarchical-clip Review,
Pose/Return, selection-change invalidation and Apply, each in one Undo step.
Undo/Redo, Save/Open and byte-for-byte reference preservation passed. Normal
Build `f4321357aa43f665` produced package SHA-256
`b23c0059ce6497a8583f11a3de4ac2fd6ff9a649c866134f17bc0fa7d80aff46`.
Independent relocated-carrier decompression exactly matched authored native
animation bank SHA-256
`6c1bd95f47855b285e17f3f928fd07b652d894f8fbe3b8c5bc7c92970e4716a2`.
No game launch, installation or full-disc export occurred.


## Equal-pose GLB selections require distinct Review keys - 2026-10-06

Imported-actor GLB Review now directly includes any explicit selected animation
index in its digest. Previously two clips in the same uploaded file could
quantize to identical native poses and share a key, allowing Apply with a
different index from the reviewed choice. Whole-file hashing and candidate
hashing alone do not distinguish this case. Implicit single-clip digests remain
byte-for-byte compatible. Retained UUID Review already includes the selection
in its full analysis digest and needed no implementation change.

**Verification:** 17 focused Python checks passed. The pinned `a060db0c` SDK
reproduced colliding Review keys on a private retail fixture. Current imported
and retained HTTP workflows produced equal native candidates with distinct
keys, rejected mismatched Apply without mutation, accepted matching Apply in
one Undo step, and passed Undo/Redo and Save/Open. Native candidates match the
pinned baseline; imported data and the reference project are unchanged. Proof:
`local-output/sdk-20260909/animation-glb-selection-digest-20261006/proof.json`.
No Build or game launch was needed for this review-identity-only correction.
Parent-transform baking is still unimplemented; the full SDK goal remains open.


## External animation object names retain native identity - 2026-10-06

Rigid GLB nodes may now use readable external names, or omit display names,
when they preserve the exported `extras.source_object.object_index`. Node order
may change with consistent scene/channel indices. Without that property, the
existing `object-N` fallback remains. Canonical names contradicting preserved
indices reject, as do malformed, duplicate and out-of-range identities. Every
source object must still occur once in the selected scene, independently of
other mapped source objects. Native layout, quantization and source-bound
Review/Apply remain unchanged; this does not infer skinning or retargeting.

**Verification:** 33 focused Python cases passed, including exact native/opaque
no-op preservation after renaming/reordering, exact edited-object targeting,
unnamed nodes, name-only fallback and malformed/conflicting identity rejection.
Pinned `5d6ae248` reproduced the original rejection on the same renamed fixture.
Private retail editor and normal Build evidence lives in
`local-output/sdk-20260909/animation-glb-node-identity-20261006/`.
Gameplay acceptance and the full SDK goal remain incomplete.

Both real retail browser workflows passed named second-clip Review, Pose/Return,
selection invalidation and explicit Apply with renamed/reordered nodes. Each
Apply produced one undoable command; Undo/Redo and Save/Open held exact state.
Normal Build `b13165dd5963e983` produced package SHA-256
`ffe8073a5067765b2b519bf2a4dd173f8f5f435ffdce5b4be195656c59ef2ce6`.
Independent relocated-carrier decompression matched the authored native bank
SHA-256 `6c1bd95f47855b285e17f3f928fd07b652d894f8fbe3b8c5bc7c92970e4716a2`.
The reference project remained byte-for-byte unchanged; no game was launched.


## Named GLB animation selection - 2026-10-06

Both imported-actor and retained UUID GLB editors now list the uploaded file's
clip indices and names. Multi-clip files require explicit selection; only that
clip is sampled. The bounded catalog permits up to 64 clips within the existing
32 MiB GLB budget. Single-clip and static-transform inputs preserve the legacy
request and report behavior. Review binds the selected index into its digest;
changing the dropdown invalidates Review, and mismatched Apply rejects. Native
records, contribution ownership and retained-recipe serialization are unchanged.

**Checks:** 29 focused Python cases and four Node editor checks passed. Private
retail browser workflows exercised named second-clip Review, Pose/Return, choice
change invalidation and explicit Apply for both editors. Both HTTP workflows
rejected ambiguous selection and mismatched Apply without mutation; the first
clip remained a no-op. Undo/Redo and Save/Open and package readback are recorded
in `local-output/sdk-20260909/animation-glb-clip-selection-20261006/proof.json`.
No game launch or installation; retail animation playback remains deferred.
General skinned retargeting and the full SDK goal remain incomplete.

**Build:** `c4544dc8c892acc0`; package SHA-256
`baa026a800d1b5fedfcf55023292f056463b3fb675c93c95aef07e10e3b18ef8`.
Independent relocated-carrier decompression exactly reproduced the authored
animation bank SHA-256
`81b02af2d194c1e81e8cd07293bf585ed6426ff8337266bbf13682c77123d9cc`.
The private reference project remained byte-for-byte unchanged.


## Animation GLB numeric overflow rejection - 2026-10-06

**Stability fix:** huge JSON integers in node vectors, integer quaternion
components or interchange FPS could raise uncaught `OverflowError`. Vector
validation now turns float-conversion overflow into the existing import error;
quaternion components reject outside the existing unit tolerance before squared
norm arithmetic. Import/export and both SDK FPS guards check range before float
finiteness. Valid source ranges, quaternion tolerance, sidecars and serializers
are unchanged. Invalid inputs return ordinary HTTP 400 instead of losing the
request to an uncontrolled exception.

**Verification:** 25 focused numeric/import/cubic/unit-scale checks passed.
The pinned `1ed42e61` importer reproduced `OverflowError` for oversized
translation, quaternion and FPS; the new importer rejected each with `ImportError`.
HTTP checks covered huge rates on imported export and retained Review plus a
usable follow-up request. A private retail retained upload returned 400 for huge
translation, quaternion and scale, then 200 for a valid no-op with the original
record hash. Project/history and reference files stayed unchanged. No new Build,
game launch, installation or full-disc export was required or performed.

Evidence: `local-output/sdk-20260909/animation-glb-numeric-bounds-20261006/`
(`verify.py`, pinned `baseline.py`, and `proof.json`). Gameplay verification and
the remaining full SDK/runtime requirements remain deferred/open.


## GLB constant unit-scale interoperability - 2026-10-06

**Implemented external animation compatibility:** imported-channel and retained
UUID GLB workflows now accept provably constant `[1,1,1]` scale tracks from
external editors. STEP/LINEAR keys must all be exactly unit scale. Cubic values
must be unit and every tangent participating in an interval must be zero; unused
first incoming/final outgoing tangents may be finite nonzero values. This proves
neutral scale over the whole curve, including between native frame samples.
Identity ancestors may carry neutral scale tracks; their animated translation,
rotation and matrices remain unsupported. Native rigid records have no scale
channel, so neutral tracks add no native edits. Nonunit/nonfinite scale,
intermediate cubic excursions, duplicate targets, malformed accessors/times and
animated matrices reject. The 256-track bound accommodates all 64 object TRS
triplets plus neutral ancestors; the existing key/component/native budgets hold.
Review exposes this support in both SDK workflows without changing sidecars or
report schemas. General retargeting and native scale animation remain incomplete.

**Verification:** 22 focused importer/cubic/scale checks and three Node
GLB/routing/library checks passed. A real private Town01 browser workflow reviewed
an edited GLB containing cubic unit-scale tracks and an identity root scale track,
rendered its proposed pose, returned and applied it with zero page errors.
Pose and narrow Review captures were inspected. Retail imported and retained
no-op imports preserved exact content; both Review/pose/Apply, Undo/Redo and
Save/Open passed. Normal Build `3174f674d5c90450` passed independent relocation
carrier ANM readback. Package SHA-256:
`256afa0542cf80dee8d7c6146666352cc3340bd4c8301a41f35fe79e4dad415a`.
Native bank SHA-256:
`95b3e07936a68715cd51db48cfb80ceff4a86527aa25046a973343a97a2af959`.
Private reference files stayed unchanged. No game launch, installation or
full-disc export occurred; gameplay playback/timing remains deferred.

Evidence: `local-output/sdk-20260909/animation-glb-identity-scale-20261006/`
(`verify.py`, browser script, GLB/binding, captures and `proof.json`). Interpolation
and TRS interpretation follow the primary Khronos glTF 2.0 specification,
sections 3.5.3, 3.11 and Appendix C.5. The full SDK/runtime goal stays open.


## Independent retained animation duplication - 2026-10-06

**Implemented editor workflow:** Saved allocated clips now offers **Review
independent duplicate** followed by explicit Apply. It also works from an
inspected retained asset lifecycle panel. The source's frozen donor recipe,
frame mapping, edits and opaque native content are freshly reconstructed and
copied into a new UUID; existing clips and actor assignments stay intact.
The duplicate is active and unassigned, including when copied from a retired
capture. Existing content/GLB editing, assignment, lifecycle and normal Build
consume it without a new native format or serializer. Review is read-only;
Apply uses one standard scene history command. Exact source/review guards and
64-record/revision, 4096-channel and metadata budgets remain enforced. This
supports independent copies of retained clips; general animation retargeting
and arbitrary new donor structures remain incomplete.

**Verification:** six focused Python duplication/ledger checks and three Node
library/routing/component checks passed; JavaScript syntax passed. The real
private Town01 editor reviewed and applied a duplicate with zero page errors;
wide/narrow captures were inspected. Native records were identical on creation.
One-step Undo/Redo and Save/Open passed. Editing only the duplicate preserved
the source record and its actor assignment. Normal Build `3e5c84bacab35ad6`
passed independent relocation-carrier ANM readback and native initial-selector
readback. Package SHA-256:
`693eff499c5469d309b1e93f80ff488e77e94322b2d73cdfb1c6e7119484c5ef`.
Native bank SHA-256:
`4fd3648d54e81113f910365d95531463210a495bb239688eede0f872172f8e14`.

Private evidence: `local-output/sdk-20260909/retained-animation-duplicate-20261006/`
(`verify.py`, `finish-readback.py`, browser script, captures and `proof.json`).
The readback initially assumed a standalone animation asset; it was corrected
to decode the completed package's declared relocation carrier, without another
Build. No game launch, installation or full-disc export occurred. Gameplay
playback/timing verification remains deferred, and the full SDK goal is open.


## Actor inspector GLB routing for retained assignments - 2026-10-06

**Implemented offline workflow:** the actor inspector now exposes GLB editing
without first entering imported channel authoring. Imported actors use the
existing rigid-channel editor. Actors with an allocated initial assignment open
the existing retained UUID GLB editor directly; no assignment clearing or
replacement capture is needed. The read-only resolver qualifies the current
scene source, selected actor, exact assignment UUID/hash/model and active library
row. Late actor, assignment, project or source changes reject before opening.
A capture from another actor sharing the qualified model remains supported.
Retained content Apply continues through the existing single command that updates
all referring initial assignments together. This adds no native serializer and
keeps imported and retained GLB sidecar contracts distinct.

**Verification:** 12 inspector-schema Python checks, the retail retained GLB
roundtrip/frame-growth/reference/Undo-Redo/reopen test, and three Node checks
(actor routing, library lifecycle, component action guards) passed. JavaScript
syntax checks passed. A real private Town01 full-editor browser check opened the
assigned actor action, loaded the matching retained dialog and prepared export
with zero page errors. Wide/narrow captures were inspected. Assignment and
history stayed unchanged. The new resolver has an explicit static server route.
An older schema expectation was refreshed for already registered NPC branch,
model-selector and flag actions.

Private evidence: `local-output/sdk-20260909/actor-animation-glb-20261006/`
(`proof.json`, saved private fixture, browser script and wide/narrow captures).
No game launch, installation, full-disc export or new native package was performed.
Manual initial playback/timing and general external animation retargeting remain
pending; this workflow does not require immediate gameplay verification.


## Verified model-source derivation cache - 2026-10-06

**Implemented offline inspection performance:** model source reads share a bounded
in-memory service for previously qualified scene metadata and immutable retail
TMD bytes. A new operation still verifies the full supported disc hash before
using cached derivations. Keys include scene identity, exact imported-document
hash and verified disc digest. The service retains at most eight scene
qualifications and 32 models/32 MiB; it never caches authored model files or
retained GLB bytes. Qualification/decoder failures clear its derived entries.
Project staging/Build-review deepcopies receive fresh independent service state.

Retained-source reconstruction reuses the already verified Retail bytes inside
its detached view, with imported-evidence checks before/after reconstruction.
GLB bytes, native ledger spans and exact reconstructed results still qualify on
every model read. Nested verified disc scopes now also check their file stamp
on exit, preventing early cache publication after a nested read changes input.

In the private retail Town01 model 0036 comparison, retained-model read was
**8.44s before / 1.54s after**, with exact native bytes.
Warm original-model reads were approximately0.45s and still verified the disc.
These are local measurements, not general scene-loading/runtime guarantees.
Evidence: `local-output/sdk-20260909/model-source-cache-20261006/proof.json`.
Twenty-one focused cases passed, including the separately retail-enabled GLB
HTTP workflow. Checks cover full hash rejection after same-size/same-mtime input
mutation, exit drift, imported metadata drift, eviction/bounds, independent
staging caches, source reconstruction and existing authoring/copy workflows.
Actual editor GLB/receipt downloads and read-only normal Build review passed;
all reference project files and history were held. No game launch, package
installation or full-disc export. The full SDK goal remains active/incomplete.


## Retained source inputs in editable project copies - 2026-10-06

**Implemented offline workflow:** Copy project and saved export input snapshots
now carry the original GLBs referenced by Current mesh import receipts. Sources
are qualified and included in the inventory/file hashes; shared originals are
deduplicated. Missing/changed inputs reject before copy creation. Unreferenced
files and excluded Undo/Redo dependencies stay excluded. Copy byte/file limits
include retained inputs. The editor and saved-copy discovery now also accept
retained texture PNGs, fixing rejection of otherwise valid texture-source copies.

Validation: **26 focused Python cases plus the project-copy Node checks** passed.
Checks cover copied native qualification, original GLB recovery, shared-input
deduplication, snapshot recovery, texture PNG/STP source recovery, corruption,
source preservation, bounds, and editor inventory/path guards. Private retail
Town01 proof used the actual Copy project, saved-copy list, Open copy and mesh
source download controls at wide/narrow widths. Both GLBs and JSON receipts
matched. Original files/history and the separate source reference were held.
Copied-project normal Build **6dc800e2b077da1a**, package SHA-256
`1f3be0e69bbf76e36e52a9394e2613e1460587ba8982ead81c67f72991fe3c9a`, verified Current inputs and
matched native model 0036 bytes in the package. Evidence:
`local-output/sdk-20260909/mesh-source-project-copy-20261006/proof.json`.

No game launch, installation or full-disc export. Export input recovery was
checked with synthetic saved-snapshot metadata. Older snapshots lacking mesh
sources are not repaired implicitly. Gameplay acceptance remains queued and the
full SDK goal remains active/incomplete.


## Retained GLB mesh sources and import receipts - 2026-10-06

Reviewed single and mapped mesh Apply now retain original GLB bytes under
`Authored/Models/Sources/<sha256>.glb`, plus exact import settings in the native
model binding. Each receipt identifies its append-only native ledger span,
input/result hashes and GLB hash. Reading a saved model checks the source bytes
and reconstructs the original import against the preceding ledger prefix;
missing or changed sources and inconsistent recipes reject. Legacy bindings
without receipts remain supported; their original files cannot be recovered.

**Import GLB mesh > Retained mesh sources** lists Current imports, shows settings,
and downloads original GLBs or JSON receipts. Recovery is read-only and guarded
by Current model context. Settings describe historical donors; a new import
still requires fresh donor selection and Review. Native vector/content edits
and face removal preserve receipts. Undo/Redo follows the binding in the same
single command; retained files remain available for Redo. No implicit cleanup.

Limits: 32 receipts per model, 32 MiB per original GLB, 64 MiB of distinct source
bytes per model, alongside the existing stricter native operation/geometry
budgets. Source GLBs stay in the project and are not distributed in Build.

Validation: **26 focused regression cases** across source retention, rotation,
single/mapped imports, scene node ownership and object/group replacement. The
private retail Town01 model 0036 proof retained two imports, checked original
GLB/receipt downloads in the actual editor at wide/narrow widths, held all
project files/history during recovery, and passed Undo/Redo and Save/Open.
Normal Build **39fb8fd720902191**, package SHA-256
`4f94303104d773eb22fe26e8843de0932b7fe2b67703b2c57321ca44a8189b96`,
has verified Current inputs and native package readback. Evidence:
`local-output/sdk-20260909/model-mesh-sources-20261006/proof.json`.

No game launch, installation or full-disc export. Gameplay acceptance remains
queued; this source recovery feature needs no immediate gameplay verification.
The full SDK goal remains incomplete.


## Native import orientation in GLB authoring - 2026-10-06

The GLB importer now exposes **Native import rotation (degrees)** for X/Y/Z.
Active right-handed rotations apply in X, then Y, then Z order (`Rz Ry Rx`)
after node transforms, unit scaling and GLB Y reflection, before origin offset
and integer rounding. Normal directions use the same rotation before normalized
Q12 conversion. UVs, colors and winding retain their source conversion. This
orients static imported geometry inside the shared native model; actor facing,
scene placement and animation channels remain separate.

Inventory, Review, scene Review and Apply accept optional `source_rotation` XYZ
degrees. Values must be finite numbers in -360..360. Missing/zero rotations
preserve earlier reports/behavior. Nonzero rotation metadata is bound throughout
the candidate chain and Review keys, even for a full turn yielding identical
native bytes. Editing an angle withdraws Review and rechecks source inventory,
retaining section/UV choices. Map section donors inherits the chosen rotation
and origin for all selected sections. Native coordinate/normal and topology
budgets remain enforced. Oversized numeric rotation/offset/scale inputs now
reject cleanly before floating-point conversion can overflow.

Validation: 21 focused regression cases passed, including Node report guards;
the affected 11 cases were rechecked after the numeric-guard adjustment. Checks
cover native axes, rotation order, node/scale/offset composition, rotated normals,
limits, distinct Review keys for identical bytes, read-only posed scene Review,
atomic history and native Build. Actual browser angle editing/reinventory,
single-donor Review, stale Review withdrawal and mapped Apply passed. Private
Town01 model0036 used rotation `[90,0,90]` and offset `[1500,256,-1000]` across
three sections/two objects, retiring 177 faces and importing 6. Undo/Redo,
Save/Open, reference-project preservation and exact native Build readback passed.
Rotation controls and desktop/540-pixel comparison captures were inspected.

Private Build `2d06d44bda9966bb`; package SHA-256
`b2a234864b5e973cff5d0a7347eea0e0209310ea452436fcc3e50eddb9430b56`;
model SHA-256
`1f62042c41586d80a362e00eab55cd1929243eff76d416890d4505183cfcc7df`.
Evidence: `local-output/sdk-20260909/model-mesh-rotation-20261006/`.
No game launch, mod installation or full-disc export occurred. Gameplay acceptance
remains deferred. Arbitrary images/layouts, general animation import and the
broader SDK specification remain incomplete; the goal remains active.

## Native origin offsets in GLB import - 2026-10-06

The GLB importer now exposes explicit **Native origin offset** X/Y/Z controls.
Offsets apply after node-hierarchy transforms, unit scaling and Y reflection,
before native integer rounding. They move imported vertices inside the shared
model; they do not move actor placements, rotate normals or change UVs. Native
Y increases downward. Map section donors inherits one common chosen origin for
all selected sections. Existing append, group/object replacement and preserved
source-section modes compose with this origin.

Inventory, Review, scene Review and Apply accept optional `source_offset` XYZ.
Components must be finite numbers from -32768 through 32767; final rounded
coordinates still must fit signed native storage and nondegenerate triangles.
Missing/zero offsets preserve existing reports and behavior. Nonzero origin
metadata is present in inventory/geometry/reports and bound to Review keys,
including identical rounded candidates. Changing an input withdraws Review and
refreshes source inventory while retaining UV/section choices. Normal Build
serializes the shifted authored vectors through the existing model ledger.

Validation passed 19 focused Python cases, including Node report guards. Actual
browser input/reinventory, single-donor Review, origin-withdrawal and mapped
Review/Apply passed without page errors. Private retail Town01 model0036 mapped
three sections into two objects at `[1500,256,-1000]`, retired 177 original faces,
and imported 6 faces with normals/UVs unchanged. One-step Undo/Redo, Save/Open,
reference-project preservation and exact native normal-Build readback passed.
Desktop and 540-pixel captures were inspected.

Private Build `05d29e44e4b276ed`; package SHA-256
`ce8275cd30f033178cce644431ef8ccda873485c41e24668f62ac352f146dd1e`;
model SHA-256
`081f0f637d0b2cc3f0b10ee41fa6205b31eeaa9988298cbffb6af156e467c1d2`.
Evidence: `local-output/sdk-20260909/model-mesh-offset-20261006/`.
No game launch, mod installation or full-disc export occurred. Gameplay acceptance
remains queued; arbitrary images/layouts and general animation import remain
incomplete. The full SDK goal remains active.

## Visible geometry framing for GLB comparisons - 2026-10-06

Single-donor and mapped-section GLB dialogs now expose **Camera framing** and
**Frame mesh**. The default shared frame covers visible triangles in both
Current and Proposed at the same scale. Active-layer visible framing ignores
unused vertex rows, including rows retained after object/group retirement.
Stored-vertex framing remains available to inspect their full native extent.
Frame mesh resets zoom while retaining orbit. These are display controls: they
preserve Review, native coordinates/bounds, authored geometry and history.

Validation passed 13 focused Python workflow/scene cases and two Node suites for
framing and existing scene cameras. Actual retail HTTP Reviews exercised both
dialogs, all three frame modes, shared layer switching, zoom reset, and inspected
desktop / 540-pixel captures. In the mapped Town01 model0036 proposal, retiring
177 faces across two objects changed the useful visible radius to 70.7107 from
the stored-vector radius 429.2534; the retained native vectors remain untouched.
Camera actions issued no API requests, Apply was not used, and all private
project-file hashes, document state and Undo history remained unchanged.

Evidence: `local-output/sdk-20260909/model-visible-frame-20261006/proof.json`
and `validated/` captures/reports. No game launch, mod installation or new Build
was required for this camera-only change. Gameplay acceptance remains deferred;
the complete SDK goal remains active and incomplete.

## Replace mapped objects with per-section native materials - 2026-10-06

**Map GLB section donors** now offers **Replace all existing geometry in mapped
donor objects**. Each selected section first allocates its own group using its
chosen Current triangle donor. Once every section is allocated, the transaction
retires exactly the original Current faces in those mapped native objects. Newly
imported sections survive, unmapped objects remain, and Apply publishes one Undo
entry. Multiple selected objects can be replaced together. Per-section group
replacement conflicts are rejected and disabled in this mode. Native identities,
original vector rows, tombstones and historical allocation budgets remain.

Batch Review, Apply and scene Review accept the strict optional `replace_objects`
boolean. True produces `legaia.model-mesh-batch-review.v2`, with exact
`replaced_object_indices`, `removed_face_ids` and a qualified final `retirement`
stage after all allocation steps. V1 remains supported. Review keys bind the
mode, selected donors, source sections and complete retirement. Editor validators
check the candidate chain, ownership, surviving native render packets and ledger
history; changing the checkbox withdraws Review and requires another Review.
Scene proposals compose qualified existing poses without publishing changes.

Validation: 14 focused Python cases (including Node report mutation checks),
actual browser upload/mapping/Review/Apply, mode-withdrawal checks and inspected
Current/Proposed captures at desktop and 540-pixel widths. A private retail
Town01 model0036 replaced object0's 7 groups / 163 faces with 2 mapped groups /
4 faces, while the other object's 14 packets remained byte-exact. Donors retained
distinct flags `0x15` / `0x25` and CLUTs 31424 / 31434: the lit section imported
normals, the unlit section imported RGB, and both imported UVs. One-step Undo/Redo,
Save/Open, source-project preservation and normal Build native readback passed.

Private Build `d67317911957cd29`; package SHA-256
`f359b62f382c0f1bdf7369926015fd9c39e33dc5fe4dbd58347854e2978c99a3`;
model SHA-256
`e3af801a20dd4191af9d6cf83e2b9566444b99da6d0219e3a00c94189b8748f1`.
Local evidence: `local-output/sdk-20260909/retail-mapped-object-mesh-20261006/`.
No game launch, mod installation or full-disc export occurred. Manual gameplay
acceptance remains queued. This maps existing native material bindings; arbitrary
new images, packet layouts and general animation import remain incomplete.

## Replace complete native object geometry from GLB - 2026-10-06

The mesh importer now offers **Replace donor object geometry** alongside append,
new-group and donor-group replacement. It imports the selected static GLB mesh
into independent groups, then retires every Current face in the selected native
TMD object as one published command. Other objects, object identity and existing
vector rows remain. Retired source/authored faces stay reserved and restorable;
all existing historical allocation budgets still apply. Preserving GLB primitives
creates separate new groups, all inheriting the selected triangle donor's layout
and material binding. This replaces a native object's geometry within a shared
model asset; it does not allocate arbitrary packet layouts, images or animation
channels, or replace every object in a multi-object model in one operation.

V8 Review explicitly identifies the object and complete retired face set. Its key
binds object replacement separately from group replacement, including when both
would yield identical model bytes. Strict booleans, mutually exclusive replacement
choices, independent-group requirements, typed topology/render qualification,
source freshness and reviewed Apply remain enforced. Scene proposals use the
same reviewed choice and compose existing qualified poses. V1-V7 review modes and
existing ledger schemas remain supported.

Twenty-five focused cases passed, including multi-group/copied-object retirement,
other-object ownership, restorability, wrong-mode and forged-review rejection,
one-step Undo/Redo, Save/Open, normal native Build, HTTP scene-review and existing
pose composition. A real browser upload/Review/Apply on a private retail Town01
project replaced model 0036 object 0's seven groups / 163 faces with two groups /
four faces. Object 1's 14 faces remained. Mode changes withdrew Review; desktop
and 540-pixel captures were inspected, including the rendered comparison. A
follow-up read-only browser review held all project files.

Retail normal Build `9014063760bfb107` passed integrity and native model readback.
Package SHA-256:
`1af6201e5b9f1b4c10c9703f6b3731467dd06437fcd9f787926febfdb701be0c`.
Decoded model SHA-256:
`0e5faa86128f2eb9aa1a1124ee5afe152058ef3771ed5c96353dfcaf38fd8380`.
Private evidence: `local-output/sdk-20260909/retail-object-mesh-20261006/`.
No game was launched, no mod was installed and no full-disc export was performed.
Manual rendered/gameplay acceptance remains queued; the larger SDK goal stays
active and solo.


## Retail 512-face delivery and packet allocation performance - 2026-10-06

The expanded mesh capacity now has a private retail normal-Build proof. Town01
model 0036 replaced one 44-face donor group with 512 triangles and 1,536 distinct
new vertices. All 133 retained packets remained byte-exact. The emitted compressed
pack verified all 114 model slots, including existing neighbor overrides, and
held the five other resource sections. Review stayed read-only; one-step Undo/Redo,
Save/Open, imported facts and the source reference project were preserved.

Build `e8d7fab1e309a97f` has package SHA-256
`e931e795d441b30b7b60e37411f6fac82f327aac1e7bc456ee7a17a5364b1fa2`.
Its decoded model SHA-256 is
`b6fe27e3864e721531c55337d387a366bc42b511f1b96755aa5dfc05567d5e59`.
A fresh normal Build with the optimized allocator produced the identical package
SHA-256, with current-input verification and project history held.
Private evidence is under
`local-output/sdk-20260909/retail-mesh-capacity-20261006/`.

Face/group allocation also no longer patches and requalifies an entire model
once per new face. It inspects the immutable source once, reuses the existing
typed operand writer on each bounded packet, and qualifies the complete assembled
model once. Public primitive authoring retains its existing source/candidate
qualification. Packet layout, material/footer ownership, normal/vertex domains,
source hashes and candidate validation remain enforced.

A direct 512-face retail comparison against revision `0963a9c2` produced identical
allocation bytes and audit: one measured allocation took 6.448 seconds before and
0.009 seconds after. Full saved model replay took 0.654 seconds. These are focused
serialization timings, not a gameplay or general editor performance claim.
Forty-three focused tests passed with retail primitive checks enabled, including
all 24 packet families and constant source/final qualification counts at 1 and
512 faces. No game was launched, no mod was installed, and no full-disc export
was performed. Manual rendered/gameplay/performance acceptance remains queued;
the broader SDK goal stays active and solo.


## Authored model capacity expanded to 512 faces - 2026-10-06

The model ledger and native face/group/object allocation paths now allow 512
historically allocated authored faces, including retired identities. The editor
uses one shared face-budget module for GLB bindings, mesh inventory, selected
section Review, primitive/material ownership and topology consumers. Existing
projects and smaller imports retain their schemas and replay behavior. Inventory
can qualify 128 source sections of up to 512 triangles each (65,536 total); one
selected import is still bounded to 512 triangles and the ledger's remaining
face budget. Native vector/address, group, model-byte and carrier-capacity checks
remain independent and unchanged.

A focused exact-limit proof replaced a synthetic Retail donor group with 512
triangles and 1,536 distinct vertices. Editor Review qualification, one-step
Undo/Redo, Save/Open replay and byte-for-byte normal Build package readback passed;
513 triangles rejected before changing the project. A 576-triangle file also
qualified as inventory: selecting 288 triangles passed HTTP Apply/history/Build,
while selecting both sections rejected. Another 47 focused Python tests and seven
JavaScript suites passed. These are synthetic-disc/native serialization proofs,
not a new retail gameplay or rendered 512-face acceptance claim.

No game was launched or controlled, and no full-disc export was performed.
Manual visual/performance verification remains queued. The SDK goal remains
active, with solo offline implementation continuing; arbitrary packet layouts,
new image allocation and general animated mesh retargeting remain incomplete.


## NPC-owned transition arrival serialization foundation - 2026-10-06

A native serializer now supports independently owned arrival bytes for qualified
SCENE_CHANGE instructions in appended NPC records. It uses the existing transition
adapter and the shared final-allocation guard, which now accepts the adapter's
transition target collection. Typed partial/full requests alter only encoded
entry X, Z and direction bytes. Destination names, full opcode/context/argument
preimages, untouched arrival bytes and layout remain bound to the retail donor,
even for no-op requests. Branch composition must follow operand serialization.

Validation: 24 focused native transition and NPC selector/branch/wait/flag checks
pass. Coverage includes ordinary/extended dispatch, two independent final clones,
partial/full byte edits, retained waits, no-op preimages, malformed values, changed
names/arguments/context, foreign ownership and forged allocation rejection.

Retail eligibility remains unresolved: a fresh source-qualified scan found no
eligible actor-owned named transitions in Town01, Dolk2, Town0b or map01. This does
not establish absence of runtime transitions. The first Town01 clone-proof attempt
stopped at that eligibility assertion; no retail clone proof is claimed. The scan
preserved project documents, histories and all file hashes. Evidence:
`local-output/sdk-20260909/npc-transitions-native-20261006/discovery.json`.

This is a native foundation with synthetic ownership/composition evidence, not a
completed retail editor workflow. Project review, editor, Build, presets and saved
comparison remain pending; a qualified actor donor or supported script-binding
extension is needed before a retail vertical workflow can be proven. No game
launch or full-disc export occurred. Gameplay acceptance is deferred and the full
SDK goal remains active; other offline SDK work remains available.

## Portable NPC model-selector presets v9 - 2026-10-06

NPC presets now freeze and transfer signed SET_ACTOR_MODEL operands alongside
all seven earlier edit families. Capture, export, import review and placement
freshly qualify selector ownership/instructions; complete branch composition
includes the frozen selectors, including instructions skipped by changed edges.
Metadata-only v9 stores stable source IDs and typed signed16 values, without
model payloads or an inferred runtime model binding. Earlier v1-v8 envelopes and
size bounds remain supported; selector-bearing files cannot claim an older schema.
Import adds a library entry only. New instances require separate reviewed placement.

Validation: 20 focused Python checks and both Node preset suites pass. Checks
cover freezing, branch/movement/facing/wait retention, skipped-body composition,
invalid signed values, extra/foreign fields, missing native targets, forged saved
preset placement, atomic history and Save/Open. Actual browser capture/download,
upload, review withdrawal, library Undo/Redo, Save/reload and detached scene
placement pass. The 1211-byte v9 file and 540px review were inspected.

Recipient Build `13dd8005234017a7` independently reopens selector0 at PC12; its
entire NPC record matches the expected donor clone, placement and selector word.
Source NPC drafts and recipient imports remain unchanged. Package SHA256:
`f26852879064a47e1d8fb8d272bba54a8bc6930a1eaca1089df04f8d4ea5b58d`.
Evidence: `local-output/sdk-20260909/npc-model-selectors-presets-20261006/proof.json`.

This supersedes the earlier NPC selector-preset capture restriction. No game
launch or full-disc export occurred. Runtime pool identity, restaging, pairing
and story execution remain unverified; manual gameplay acceptance stays deferred
and the full SDK goal active/incomplete.

## Saved NPC model-selector explanations - 2026-10-06

Saved-build comparison now explains NPC-owned SET_ACTOR_MODEL selector words.
Native qualification binds the typed signed16 request, original donor/PC/opcode,
extended context, source hash and separate retail/generated offsets to the exact
receipt and emitted bytes. Browser decoding independently verifies MENU_CTRL
sub-op0x50, signed word encoding, source metadata, instruction width and held
dispatch. Retained selectors still qualify when a changed branch skips their
original instruction. Source-identical requests receive no authored change span.

Validation: 17 focused Python checks with private retail input and the Node
comparison suite pass. Signed boundaries, ordinary/extended forms, no-ops,
skipped-body composition, forged requests/receipts and duplicate spans are covered.
A fresh read-only Town01 Build `47211a52e78d1b75` comparison labels one selector
byte out of three changed bytes; two stay unexplained. The 540px table was visually
inspected. Streaming Build `a283762d47e6985f` qualifies the requested -1 word and
correctly leaves the source-identical 240 request unlabelled. The private helper's
initial assumption that both requests changed bytes was corrected using each
retail preimage. Both project documents, histories and every file hash stay held.
Evidence:
`local-output/sdk-20260909/npc-model-selectors-script-comparison-20261006/proof.json`.

Portable NPC model-selector presets remain pending. No new Build, game launch or
full-disc export occurred. Runtime pool identity, restaging, pairing and story
execution remain unknown; manual acceptance is deferred and the SDK goal active.

## NPC model selectors through editor and normal Build - 2026-10-05

Independent NPC SET_ACTOR_MODEL signed selectors now connect source inspection,
complete reviewed entries, Apply/Clear, Undo/Redo, Save/Open, root Inspector and
Asset Details. Normal compressed and streaming Builds compose selector words
before NPC branches. Branch review includes selectors in its complete frozen
composition, retaining original operands when a changed edge skips them.
Repetition qualifies and retains entries. Preset capture explicitly rejects
selector-bearing NPCs until portable interchange is connected; saved authored
comparison for this family also remains pending.

Validation: 24 focused Python checks with private retail input and the Node source,
review and opener contract pass. Checks include stale review, typed fields,
HTTP rejection, history/persistence, repetition and a changed branch skipping a
retained selector. Actual Town01 browser Review/Apply/Clear, changed-input
withdrawal, Undo/Redo and Save/reload pass; the 540px dialog was visually inspected.
Build `47211a52e78d1b75` reopens selector0 at PC12, preserving every other record
byte against its baseline Build. Package SHA256:
`f12191b0735f0c0de979219c6f145e121e09a2870cb2bbba236373ce2f886293`.
Streaming Rayman Build `a283762d47e6985f` reopens two independent NPC selectors
240/-1 at PC12 with only their word bytes changed. Package SHA256:
`7319c7612354b6cf878a31c33d69ec745968a98de51dbfeb3df59d8d304aa3ab`.
Evidence: `local-output/sdk-20260909/npc-model-selectors-editor-20261005/proof.json`
and `local-output/sdk-20260909/npc-model-selectors-streaming-20261005/proof.json`.

Selectors are encoded script operands, not resolved model assets. Runtime pool
identity, pairing, restaging and story execution remain unverified. No game launch
or full-disc export occurred. Manual acceptance stays deferred; the SDK goal stays
active/incomplete.

## NPC-owned script model selector foundation - 2026-10-05

Appended NPC scripts now have independent native SET_ACTOR_MODEL selector-word
serialization using the existing source-qualified MENU_CTRL 0x50 adapter. The
shared final-allocation guard binds each unique clone to its immutable donor.
Signed16 values preserve encoded meaning, opcode, sub-op, extended context and
all other bytes. No-op requests still verify full instruction/word preimages.
This changes script operands; runtime model-pool resolution and mesh restaging
are not inferred, and the viewport does not simulate this instruction.

Validation: 10 focused native/model-selector/wait Python checks pass. Ordinary and
extended forms, signed boundaries, two independent clones, final offsets, retained
wait operands, no-op preimages, invalid types/owners and forged allocations reject
or retain bytes as required. A fresh retail Town01 actor0003 two-clone proof sets
PC12 to selectors240/-1, preserving the retail donor, complete MAN layout, every
unrelated byte, project document, Undo/Redo history and all project file hashes.
Evidence: `local-output/sdk-20260909/npc-model-selectors-native-20261005/proof.json`.

Project commands, editor review, normal Build, portable presets and saved authored
comparison are still pending for NPC-owned model selectors. The existing imported
actor workflow is unchanged. No game launch or full-disc export occurred; runtime
model identity, pairing, restaging and story execution remain unverified. The full
SDK goal remains active and manual gameplay verification remains deferred.

## Portable NPC branch presets v8 - 2026-10-05

NPC presets now freeze independent branch destinations with all six earlier edit
families. Capture, export, import review and new-instance placement qualify the
complete frozen script composition against the retail donor. Metadata-only v8
stores stable branch IDs and typed target PCs; original boundaries, conditions,
selectors and dispatch remain native-qualified. Earlier v1-v7 envelopes and bounds
remain available. Branch-bearing files cannot use an older schema. Import creates
only a library entry; reviewed placement creates an independent undoable NPC.

Validation: 19 focused Python checks with private retail input and both Node
preset suites pass. Coverage includes freezing after source edits, all earlier
families, skipped-body composition, atomic history, Save/Open, invalid/interior
PCs, forged ownership/fields and freshly qualified stored-template placement.
Actual browser capture/download/upload, changed-review withdrawal, library
Undo/Redo, Save/reload, detached scene inspection and new-instance Apply pass.
The 2583-byte v8 file and 540px import review were inspected.

Recipient normal Build `ee559898bc7a73de` independently reopens branch PC14 target11,
flag bit0, facing sector0, wait11, movement X3200/Z5696/MOVE_ID10, appearance105/13
and text `Wait NPC`. Source drafts and recipient imports stay unchanged. Package
SHA256: `3a1ee99cfc40358682941c2afc850393303255f64b6e39f309072d47a0a24f71`.
Evidence: `local-output/sdk-20260909/npc-branches-presets-20261005/proof.json`.

This supersedes the earlier branch-preset capture restriction. No game launch or
full-disc export occurred. Runtime activation, story reachability, scheduling and
termination remain unverified; manual acceptance is deferred and the goal active.

## Saved NPC branch explanations - 2026-10-05

Saved-build comparison now explains source-qualified NPC branch destination words
alongside appearance, dialogue, waits, movement, facing and flag bits. Native
qualification binds original instruction boundaries and the final graph to the
saved receipt. Browser decoding independently checks all eight supported branch
word families, exact dispatch, targets, original boundaries and held selectors.
Edits retained in instructions skipped by a changed branch still qualify: facing
and flag checks use a private copy with original branch words restored, while the
comparison always displays exact saved bytes. No project data is changed.

Validation: 11 focused Python checks with private retail input and the Node
comparison suite pass, including skipped-body edits and forged receipt rejection.
A fresh saved Town01 Build `6e6a47c3f7d988fe` comparison renders all seven edit
families and accounts for 30 of 33 changed bytes; three stay unexplained. The 540px
comparison was visually inspected. Streaming Build `0dc504a3a5d7cf6f` independently
qualifies both NPC branch spans. Both projects, Undo/Redo history and every project
file hash remain unchanged. Evidence:
`local-output/sdk-20260909/npc-branches-script-comparison-20261005/proof.json`.

Portable branch presets remain pending. No game launch, new Build or full-disc
export occurred; branch activation, story reachability and termination remain
unverified. Manual gameplay acceptance stays deferred and the SDK goal is active.

## NPC branch authoring through editor and normal Build - 2026-10-05

NPC branch destinations now connect source-qualified review to the root Inspector
and Asset Details, reviewed commands, Undo/Redo, Save/Open and both normal Build
carrier paths. Review composes existing own dialogue/movement/facing/flags/waits
before qualifying the proposed graph. Build composes branch destinations after all
six existing NPC edit families, retaining original instruction spans even when
changed edges skip them. Conditions, selectors and extended dispatch stay held.
Repetition qualifies and retains branches. Branch-bearing preset capture rejects
until portable interchange is connected; saved authored-span explanations are also
pending. See [NPC branch workflow](legaia-npc-branches.md).

Validation: 19 focused Python checks pass with retail input enabled; the Node
source/review/opener contract suite passes. Actual browser Review/Apply/Clear,
changed-input withdrawal, Undo/Redo and Save/reload pass. A module export mismatch
found by the first browser probe was corrected and the opener export is now
checked. The saved 540px dialog top and bottom were visually inspected without
project/history/file mutation. Private Town01 Build `6e6a47c3f7d988fe` reopens
branch PC14 with target11 and changes only its destination word against the
verified six-family baseline. Package SHA256:
`df94104dd232c590cf6a1fc99633ff58b34b8c3a6a2919dd8aa0e9b61fa92636`.
Streaming Rayman Build `0dc504a3a5d7cf6f` reopens two NPC branches at PC12 with
targets9/10, with only branch-word changes and all six prior families retained.
Package SHA256: `7d3ea68002c864c4580f3fb3d2ce60abb802af573f9499d5b90a1f585104c18d`.
Evidence: `local-output/sdk-20260909/npc-branches-editor-20261005/proof.json`
and `local-output/sdk-20260909/npc-branches-streaming-20261005/proof.json`.

No game launch or full-disc export occurred. Branch activation, story reachability
and termination remain unknown. Manual acceptance stays deferred and the full SDK
goal remains active/incomplete.

## NPC-owned branch destination serialization foundation - 2026-10-05

Appended NPC records now have a native branch-word serializer using the existing
source-qualified BranchAuthoringContext. It resolves final clone allocations,
qualifies each clone against immutable donor graph anchors and composes complete
branch requests together. Original opcodes, dispatch contexts, branch conditions,
selectors, word preimages and record boundaries stay held. Targets must be reached
source instruction or atomic message starts; opaque/interior targets reject.
Original source spans remain retained when edited edges make them unreachable.
Branch composition belongs after other qualified NPC operand edits.

Validation: 13 focused Python checks pass with the retail fixture enabled.
Synthetic cases cover ordinary/extended supported family words, two independent
clones, final offsets, no-op preimages, invalid types/owners and changed conditions
or selectors. A fresh retail Town01 donor0040 two-clone proof changes the qualified
SYSFLAG_TEST at PC14 to source boundaries11/12, preserving appearance, waits,
movement, flags, the source donor, MAN structure, every unrelated byte and project
files/history. Evidence:
`local-output/sdk-20260909/npc-branches-native-20261005/proof.json`.

This is a serialization foundation. Project review/history, editor controls,
normal Build, portable presets and saved-script explanations are not yet connected.
Branch activation, termination and story reachability remain unknown. No game
launch or full-disc export occurred. Manual acceptance stays deferred and the full
SDK goal remains active/incomplete.

## Portable NPC presets retain qualified flag-bit overrides - 2026-10-05

NPC preset capture now freezes source-qualified flag entries alongside appearance,
dialogue, waits, movement and facing. Flag-bearing exports use metadata-only
`legaia.npc-preset-file.v7` with the existing 512 KiB bound; v1-v6 retain their
previous schema selection and limits. Export/import and reviewed placement freshly
qualify donor operands. The browser checks exact owner/PC namespaces and typed
entries, preserves the complete reviewed draft and shows flag counts. The temporary
flag-bearing capture rejection is removed. Runtime flag identity and story meaning
remain unknown. See [NPC flag workflow](legaia-npc-flags.md).

Validation: 18 focused Python checks and two Node suites pass. Tests cover frozen
capture, independent library import without NPC creation, history/persistence,
older-format rejection, malformed entries, special side-effect exclusions and
fresh placement requalification. Actual retail browser capture/download/upload,
Review withdrawal, library Apply/Undo/Redo, Save/reload and Review/Inspect/Apply new
instance all pass. Existing entities/imports and the source NPC stay held. The
540px import review was visually inspected. Recipient NPC
`authored-actor://4df9310b-5efd-5626-be23-39aa19404402` retains bit0, sector0,
wait11, own text, model105/animation13 and own movement X3200/Z5696/move10 at
placement X3200/Z5824. Normal Build `248da4af5e7947dd` independently reopens all
six families and preserved upper bits. Package SHA256:
`0092b428d9d6ed60852905fa54a917adc6c0e98fe5de4220f10d4a026346e495`.
Evidence: `local-output/sdk-20260909/npc-flags-presets-20261005/proof.json`.

No game launch or full-disc export occurred. Manual runtime acceptance stays
deferred and the full SDK goal remains active/incomplete.

## Source-qualified saved NPC flag explanations - 2026-10-05

Saved-script comparison now labels NPC-owned flag-bit index bytes alongside
appearance, dialogue, waits, movement and facing. Each explanation is bound to the
current NPC's typed request, source donor/PC/opcode/context, exact native source
change, final record allocation and saved before/after bytes. Both records must
qualify the supported instruction; widths and special side effects stay excluded.
Upper bits, extended dispatch, no-op receipts, stale/forged metadata and overlap
are checked independently. Other differences remain unexplained. This does not
assert runtime flag identity, story meaning or behavioral equivalence.

Validation: 13 focused Python checks and the Node comparison suite pass, including
all nine operations in ordinary/extended forms, forged receipts, typed values,
upper bits and dispatch. Existing saved Town01 Build `9ad4a9c1b39b7fda` explains
28 of31 changed bytes across all six authored families, leaving three unexplained.
Streaming Build `ee3148f1c5861326` independently qualifies one flag span in each of
two NPC records. Actual read-only browser comparison renders all six labels; its
540px table was visually inspected. Project documents, history and all file hashes
stay unchanged for both projects. Evidence:
`local-output/sdk-20260909/npc-flags-script-comparison-20261005/proof.json`.

No new Build, game launch or full-disc export was needed. Flag-bearing portable
presets remain to be connected. Manual gameplay acceptance stays deferred and the
full SDK goal remains active/incomplete.

## NPC-owned flag authoring through editor and normal Build - 2026-10-05

NPC flags now connect source-qualified inspection and review to the root Inspector
and Asset Details, reviewed project commands, Undo/Redo, Save/Open and both normal
Build carrier paths. Complete entries belong to the NPC's recorded donor; stale
reviews, foreign owners, invalid bit indices and unsupported side-effect selectors
reject. Input changes withdraw browser proposals. Repetition qualifies and retains
flags. Preset capture currently rejects flag-bearing NPCs to prevent losing their
entries; portable preset integration and saved-script authored-span explanations
remain pending. See [NPC flag workflow](legaia-npc-flags.md).

Validation: 22 focused Python checks pass with the private retail fixture enabled;
two Node suites pass. A later added stale-position review regression also passes.
The actual browser verifies Review/Apply/Clear, changed-input withdrawal,
Undo/Redo and Save/reload; the 540px dialog was visually inspected. Private Town01
Build `9ad4a9c1b39b7fda` independently reopens with bit0; its record differs from
the verified prior five-family record by exactly one operand byte. Package SHA256:
`11c66953be270113d45838106195c8a1bdacd307cc499751c59bee36294c68b1`.
Private streaming Rayman Build `ee3148f1c5861326` independently reopens two NPCs
with indices3/4 and exactly one changed byte per record against their verified
baseline. Package SHA256:
`032ff923b60c8299c500c0ea5ee9521ccfe48889781aa7166d9b81f61689d6b6`.
Upper bits, the five existing own script families, placement, imports and other
draft fields stay held. Evidence: `local-output/sdk-20260909/npc-flags-editor-20261005/proof.json`
and `local-output/sdk-20260909/npc-flags-streaming-20261005/proof.json`.

No game launch or full-disc export occurred. Runtime variable identity, story
meaning and gameplay effects remain unknown; manual acceptance stays deferred.
The full SDK goal remains active/incomplete.

## NPC-owned flag operand serialization foundation - 2026-10-05

Appended NPC records now have a native serializer for source-qualified LFLAG,
GFLAG and CFLAG SET/CLEAR/TEST bit indices. It resolves final record allocations,
requires each donor-qualified instruction and operand preimage, preserves the
upper three operand bits and extended dispatch context, and changes only the
requested low five bits. Existing width and special side-effect exclusions remain
in force. No-op requests still require an exact preimage. Unsupported paths,
foreign owners, duplicate requests and invalid typed values reject.

Validation: 14 focused Python checks pass, including all nine supported operations
with ordinary and extended dispatch. A fresh private retail Town01 proof appends
two donor0040 clones, composes independent appearance, waits and movement, then
sets separate flag-bit indices 3 and 4. Exactly two bytes change; the source donor,
MAN layout, upper bits, all unrelated bytes, project files and history stay held.
Evidence: `local-output/sdk-20260909/npc-flags-native-20261005/proof.json`.

At this earlier checkpoint it was a serialization foundation; the newer
checkpoint above connects editor/project/normal Build. Presets and saved-script explanations also remain to be connected.
Runtime variable identity, story meaning and gameplay effects are not asserted.
No game launch or full-disc export occurred. Manual gameplay acceptance remains
deferred and the full SDK goal remains active/incomplete.

## Keep dense source scenes previewable with authored NPCs - 2026-10-05

The Rayman viewport failure was a combined entity-budget mismatch, not an endless
decode. Its supported source scene occupies 512 actor/scenery entries plus one
derived ground mesh; two authored NPCs raised the total to 515 and the old final
512-entry check rejected the whole preview after decoding. Scene preview now keeps
separate allowances for 512 source entries, one terrain instance and 128 independent
NPC drafts, with an explicit combined ceiling of 641 entries. A 129th active-scene draft
rejects before geometry decoding. Existing geometry/triangle/texture budgets stay
held. Shared scene constants align animation, NPC repetition/group/appearance,
preset proposal and texture-usage decoders with the supported total. The separate
world-source scene graph keeps its own existing budget.

Validation: 16 focused Python checks and nine Node suites pass. The synthetic
boundary includes all 512 source entries, ground and 128 NPCs with unchanged project
history/imports and exact source identity retention; 129 drafts reject. Actual retail
Rayman browser preview now reaches readiness in 9896 ms (one measured cold load),
with 515 entities, 514 rendered instances, 93 geometries, 15971 triangles and 5533230
texture bytes. Environment/terrain/animation errors are null. Frame All and the
NPC Focus control pass, including changed camera target and closer distance.
Overview, focused NPCs and 540px scene screenshots were visually inspected.
Project/imports/history and existing file hashes stay unchanged. Evidence:
`local-output/sdk-20260909/rayman-preview-loading-20261005/proof.json`.
A separately profiled server preview takes about 23 seconds with profiler overhead;
the earlier 60-second readiness failure is resolved by the capacity fix.

No Build/Save/authoring command, game launch or full-disc export occurred.
One unsupported scenery instance remains a source marker. Unknown NPC height,
initial heading and live placement are still explicit preview conventions; rendered
models do not establish gameplay alignment. Manual runtime acceptance stays deferred
and the full SDK goal remains active/incomplete.

## Streaming NPC readback and saved-inspector receipt fix - 2026-10-05

A fresh normal Build of the retail streaming `rayman` scene now has independent
readback proof for two NPC clones carrying appearance, dialogue, waits, movement
and NPC_RUN facing. The check found and fixed a saved-inspector bug: streaming
receipts use `actor_changes` for allocations, while compressed receipts use `actor`.
The inspector now selects the exact family from the qualified carrier schema and
rejects unknown/ambiguous receipts or missing/unbounded allocation rows. Output
DTOs remain unchanged; compressed saved inspection is also reverified.

Validation: 20 focused Python checks pass; one optional private Town01-fixture
check skips. Saved streaming Build `e5ec43a38c122f65` independently reopens record92
with sector0/wait12/X3264 and record93 with sector7/wait11/X3200. Both retain Z5696
movement, appearance model90/animation22, own padded text, placement Z5760 and upper
facing flags. The entire emitted MAN equals a separately reconstructed post-append
baseline plus intended clone edits and terminal zero padding; all other record bytes
stay held. Project/imports/history stay fixed. Package SHA256:
`04a1befcb91bfbe3c54002b02ab04123eef33537b3079cd4c27cb29e782b704f`.
Read-only browser comparison labels all five families, and the 540px table was
visually inspected. Browser project files/history stay unchanged. Evidence:
`local-output/sdk-20260909/npc-owned-streaming-20261005/proof.json`.
This closes the separate retail streaming check for NPC-owned facing and movement
and supplies retail streaming evidence for own waits/text/appearance together.

The first browser probe exceeded its 60-second full-scene viewport readiness
window. The script comparison was then verified after project readiness, separately
from scene rendering. Rayman preview loading was subsequently diagnosed as an entity-budget mismatch
and resolved in the newer checkpoint above. This earlier checkpoint did not verify
its full rendered scene. No game or full-disc export
ran. Runtime allocation/scheduling, branch execution and visible facing still need
later gameplay acceptance. The full SDK goal remains active/incomplete.

## Explain NPC-owned facing in saved script comparison - 2026-10-05

The retail-donor/generated-NPC comparison now labels **Own script facing sector**
for exact source-qualified authored bytes. Receipt rows must match the native
facing serializer, retail donor/PC/context/hash, current owned sector, final clone
allocation and separate source/generated offsets. The generated target must remain
supported after own movement. Typed sectors, full upper flags, opcode/dispatch and
CAM_CFG mode stay bound. No-op or duplicate/overlapping spans, parked targets and
forged/stale receipt rows reject. The browser independently checks raw ordinary and
extended CAM_CFG/NPC_RUN forms and the exact owned nibble. Other bytes remain
unexplained; labels establish no branch execution or runtime heading.

Validation: 39 focused Python checks and the Node comparison suite pass with the
retail disc enabled. Read-only actual browser inspection of saved Build
`2ef03e22f5a78f7b` accounts for 27 of 30 changed bytes across appearance, dialogue,
waits, movement and facing; three remain unexplained. The 540px comparison table
was visually inspected. Project document/history and all existing project file
hashes stayed fixed. Evidence:
`local-output/sdk-20260909/npc-facing-script-comparison-20261005/proof.json`.
No Build/Save/authoring command or game launch occurred. The separate own-facing
retail streaming package check is now verified above; later gameplay remains open.
The full SDK goal remains active/incomplete.

## Transfer NPC-owned facing presets - 2026-10-05

NPC preset capture now freezes supported own facing sectors alongside appearance,
dialogue, waits and movement. Facing-bearing exports use **legaia.npc-preset-file.v6**;
v1-v5 retain their existing formats and bounds. V6 contains bounded source-bound
metadata only. Export/import and instance placement freshly qualify the facing
against the same donor and its own movement-composed record; parked targets reject.
The import/placement dialogs show facing counts and require separate reviewed Apply.
Frozen presets stay independent of later source NPC edits. History and Save/Open
retain exact facing metadata without changing existing actors or imported scenes.

Validation: 37 focused Python checks and two Node suites pass. Actual editor
capture/download/upload, reviewed library import, changed-input withdrawal,
Undo/Redo, Save/reload and reviewed detached-scene placement passed. The 540px
import dialog was visually inspected. Recipient normal Build `2ef03e22f5a78f7b`
was independently reopened: sector0 and upper flags, X3200/Z5696/selector10,
wait11, own text and model105/animation13 all survived. Placement was X3200/Z5824;
source NPCs/imports stayed fixed. Package SHA256:
`8a4c6fb933dce117e9796c2a2ad35944ada8db6f7eab37aaac2cfc6dbdc65524`.
Evidence: `local-output/sdk-20260909/npc-facing-presets-20261005/proof.json`.
No game launched. Visible facing, dispatch and branch execution still need later
gameplay acceptance. Facing explanations in saved-script comparison are now supported, as recorded
above. The separate own-facing retail streaming package check is now verified above.
The full SDK goal remains active/incomplete.

## Independently author NPC script facing - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC script facing**.
Source-qualified CAM_CFG/NPC_RUN targets expose an own sector0..7 override with
retail sector, preserved upper flags and unresolved dispatch context. Review
changes withdraw Apply. Apply/Clear use one history step; Undo/Redo and Save/Open
retain facing with appearance, dialogue, waits, movement, name and placement.
Script donor changes require clearing the retained facing binding first.

Facing qualifies the NPC's own movement-composed record. Parked NPC_RUN targets
are unavailable, and movement review rejects parking a target with an owned facing
override. Normal compressed/streaming MAN composition applies facing after movement,
uses final clone allocation and records npc_facing_changes. Repetition qualifies and
retains own facing. Preset capture and v6 transfer now retain facing; see the latest
checkpoints above. Saved-script facing explanations are also now supported.

Validation: 45 focused Python checks and two Node suites pass. Actual root editor
Review/Apply/withdrawal/Clear/history/persistence and the inspected 540px dialog
passed. Normal Build `a27a96074d841507` independently reopened sector0 with preserved
upper flags, own X3200/Z5696/selector10 movement, wait11, text and model105/animation13.
Placement, imports and existing preset metadata stayed fixed. Package SHA256:
`582f053dd091e1234eaabf2383620fef902b74f5852608b85f5641f924fdb910`.
Evidence: `local-output/sdk-20260909/npc-facing-editor-20261005/proof.json`.
This earlier package check covers compressed MAN; streaming readback is now
verified in the newer rayman checkpoint above. Source operands establish no
initial/live Transform heading, dispatch identity or execution. No game launched;
gameplay stays deferred and the full SDK goal is active/incomplete.

## NPC-owned facing serializer foundation - 2026-10-05

Added source-qualified facing serialization for uniquely allocated NPC clones.
Simple CAM_CFG and nonparked NPC_RUN targets accept sector0..7 only. Requests bind
a draft, its retail script donor and supported instruction ID. The shared allocation
guard verifies final record indices, extent, local/script entry ownership and aliases.
Dispatch/opcode, CAM_CFG mode and full operand preimages remain source-bound,
including no-op requests. Only the low facing nibble changes; upper flags stay held.

Facing composes with independently authored NPC_RUN movement X/Z/selectors and
wait/appearance edits. A composed parked NPC_RUN target rejects facing authoring.
Unknown/conflicting paths, nondirection LUT slots, halt-acquire CAM_CFG mode, wrong
owners/fields/types, stale flags/context, aliased records and duplicate writes reject.
The adapter emits exact source/final byte offsets and hashes, and asserts no runtime
dispatch, initial Transform heading or gameplay behavior.

Validation: 17 focused Python checks pass with the retail disc enabled. Synthetic
cases cover both opcode families, ordinary/extended contexts, all eight sectors,
two final clones, no-op/stale and unsupported targets, aliases and composition.
A fresh town01 donor0040 check composed own movement, waits and initial appearance,
then wrote sector0/7 to two clones. Exactly two facing bytes changed; upper flags,
all other candidate bytes, MAN layout and source donor records stayed fixed relative
to the post-append/composition baseline. Project document, history and existing file
hashes stayed unchanged. Evidence:
`local-output/sdk-20260909/npc-facing-native-20261005/proof.json`.
Project commands, editor controls and normal Build integration have now landed;
see the latest checkpoints above, including v6 preset transfer. No Build, export or game launch
occurred. Manual gameplay remains deferred; the full SDK goal is active/incomplete.

## Inspect NPC-owned movement targets in the scene - 2026-10-05

The NPC movement editor now offers retail donor, current NPC and reviewed proposal
scene target layers. Enter an explicit reference Y and choose **Show NPC script
targets**. The existing viewport target overlay frames qualified MOVE_TO/NPC_RUN
X/Z markers with source PCs. Selector-only EXEC_MOVE has no scene position.
Script Y, dispatch identity, branch execution and live actor position stay unknown;
markers never move NPC placement or scene geometry.

Target selection/Inspect returns to the retained movement editor at that instruction,
including unapplied inputs and reviewed Apply. Changed inputs invalidate a proposal
overlay. Clear, stale source state or overlay replacement dispose the hidden editor;
ordinary imported-script overlays keep their existing behavior. Inspector and Asset
Details use the same NPC movement editor entry.

Validation: 18 focused Python checks and two Node suites pass. Actual browser
verified three markers, explicit/invalid height guards, current X3200/Z5696,
reviewed X3264/Z5696 and retail X13888/Z5056, return-to-editor review retention,
input withdrawal and Clear cleanup. The scene overlay and 540px scrollable controls
were visually inspected. Project document, history and all existing file hashes
remained unchanged; only source/review preview requests ran. Evidence:
`local-output/sdk-20260909/npc-movement-target-scene-20261005/proof.json`.
No Build/Save/authoring command or game launch occurred. Reference Y is a display
choice, not a recovered script height or gameplay alignment claim. Manual gameplay
remains deferred and the full SDK goal stays active/incomplete.

## Preserve NPC-owned edits through repetition - 2026-10-05

Line/grid and selected-arrangement repetition retain each source NPC's own
appearance, dialogue, wait targets and script movement in independent copies.
The single-NPC browser decoder now compares each complete proposed draft with
its source; omitted, substituted or extra fields reject. UUID uniqueness and
placement remain checked. Spacing changes placement only, never script targets.

Repetition now freshly qualifies retained source operands/appearance witnesses
before review and Apply. The single review binds the complete project source key,
checks freshness after qualification, and rejects direct Live-mode review.
Line/grid review algorithms advance to v2; saved NPC identities are unchanged.
A library or other project change withdraws a prior review rather than replaying it.
Arrangement copies use the same source qualification with atomic batch history.

Validation: 30 focused Python checks and two Node suites pass. Actual editor review,
detached scene comparison, input withdrawal, Apply/Undo/Redo and Save/reload passed
for a four-family NPC. Existing scene entities, the original NPC and imports stayed
fixed; the 540px scrollable dialog was inspected. Normal compressed MAN Build
`0be50da61dbc2529` reopened both independently allocated records with retained
appearance/dialogue/wait/movement edits. Positions differ at X3200 vs X3264,
Z5760; script targets remain X3200/Z5696 with selector10 and own wait11.
Package SHA256: `c021d76f28f93bc257c3e0b25386df826b3544b9dc17d6cbb12e4ef3e6ad1e80`.
Evidence: `local-output/sdk-20260909/npc-owned-repetition-20261005/proof.json`.
No game launched. This proves editor metadata and emitted bytes, not runtime
allocation, scheduling or movement behavior. Gameplay stays deferred; the full
SDK goal remains active/incomplete.

## Explain NPC movement edits in saved-script comparison - 2026-10-05

The saved normal Build comparison now labels source-qualified NPC movement
operand bytes alongside appearance, dialogue and waits. Each movement audit row
must match its recorded script donor, reached supported instruction, PC, field,
dispatch context, source hash and exact requested before/after bytes. Final record
allocation and source/generated relative offsets must match. Missing audit rows
or other bytes receive no explanation; invalid rows reject the comparison.
The browser independently checks raw ordinary/extended opcodes, operand offsets,
current authored values and exact byte encoding before rendering X/Z/selector
labels. Bounded span counts accommodate all supported operand families.

Validation: 23 focused Python checks and the Node comparison suite pass, including
MOVE_TO/NPC_RUN/EXEC_MOVE, ordinary/extended contexts, missing bindings, forged
owners/fields/context/offsets, byte substitutions, overlap and collection bounds.
Actual saved Build `4725587333eecfe2` yielded 29 changed bytes: 26 accounted for by
qualified appearance/dialogue/wait/movement spans and three remaining unexplained.
The real editor comparison and inspected 540px table passed without authoring,
Build/Save or Run calls. Project document, history and all existing file hashes
remained unchanged. Evidence:
`local-output/sdk-20260909/npc-movement-script-comparison-20261005/proof.json`.
This explains exact authored bytes only; it proves no runtime dispatch, movement
behavior or branch execution. No game launched; gameplay stays deferred and the
full SDK goal remains active/incomplete.

## Movement-bearing NPC presets - 2026-10-05

NPC preset capture now freezes supported own script movement together with
appearance, dialogue and waits. Export uses **legaia.npc-preset-file.v5** when
movement is present, with the existing 512 KiB metadata bound. Formats v1-v4
remain supported. Capture, export/import and reviewed placement freshly qualify
the donor-owned instruction targets and operand fields; malformed owners, types,
grid coordinates, missing targets and unsupported opcode fields reject. Frozen
metadata stays independent of subsequent source-draft edits. Import adds only a
library entry; a separate reviewed placement creates the NPC.

The library/import summary reports movement target counts. Review changes withdraw
Apply, and exact reviewed placement metadata must retain all supported edit families.
Script movement coordinates remain separate from the chosen NPC placement.

Validation: 35 focused Python checks passed, one existing optional check skipped,
and two Node suites passed. The actual editor captured/downloaded/uploaded a v5
preset, reviewed an independent library import, exercised Undo/Redo and Save/reload,
and reviewed/inspected/applied an independent instance. Existing entities and source
draft/import metadata stayed fixed. The 540px import dialog was visually inspected.
Normal compressed MAN Build `4725587333eecfe2` was independently reopened: emitted
NPC movement X3200/Z5696/selector10, own wait11, own text and model105/animation13
all survived transfer. Chosen placement X3200/Z5760 remained independent.
Package SHA256: `48a4564f2c96a8224f1413583f8732262a74c05d3ed2565f211a97272f001ed8`.
Evidence: `local-output/sdk-20260909/npc-movement-presets-20261005/proof.json`.
The private readback helper initially expected a hex field instead of an audit byte;
corrected readback passed against the existing Build without rerunning gameplay.
No game was launched. Runtime dispatch/selector behavior and streaming retail
package acceptance remain unverified; gameplay is deferred. The full SDK goal is
active/incomplete.

## Independently author NPC script movement - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC script movement**.
The source-qualified picker groups reached instructions and exposes only their
supported X/Z and encoded move-selector fields. Each field has a retail value and
an independent own-override checkbox. Review preserves unselected operands; input
changes withdraw Apply. Apply/Clear use one NPC history step. Undo/Redo and
Save/Open retain script donor, appearance, dialogue, waits, name and placement.
Changing script donor requires clearing retained movement first.

The editor labels encoded dispatch context as unresolved. Script targets remain
separate from placement/live coordinates; selector meaning, Y, depth, branch
execution and runtime behavior are not inferred. Native serialization composes
NPC movement before other supported edits against final allocated record IDs.
Normal compressed/streaming MAN paths record npc_movement_changes separately.
Movement-bearing NPC preset capture/transfer/placement is now supported; see the
latest v5 checkpoint above.

Validation: 40 focused Python checks and two Node suites pass. Actual root editor
source loading, field Review/Apply, withdrawal, Clear, Undo/Redo and Save/reload
passed; the 540px grouped dialog was inspected. Normal Build `f58172af849a0417`
independently reopened the emitted NPC record with X3200/Z5696/move selector 10,
retained 11-tick wait, own dialogue and model105/animation13. Imports and authored
placement remained fixed. Package SHA256:
`46cca87024e38f696ab6749d2b151e1792e2abc8d4ec1fce620b02bb07567c08`.
Evidence: `local-output/sdk-20260909/npc-movement-editor-20261005/proof.json`.
The actual package check covers compressed MAN; streaming integration has not yet
received a separate retail package check for NPC movement. Saved-script comparison
now explains qualified movement operands; other unqualified changes stay unexplained. No game was launched.
Gameplay remains deferred and the full SDK goal stays active/incomplete.

## NPC-owned movement operand serializer - 2026-10-05

Added native serialization for source-qualified movement operands in allocated
NPC scripts: MOVE_TO/NPC_RUN encoded X/Z and NPC_RUN/EXEC_MOVE move selectors.
Requests name a draft, its retail script donor and stable supported instruction
IDs. Final clone indices, local/script entry ownership, exact extent and alias
checks are now shared with NPC wait serialization. Source-stopped paths, wrong
owners, unsupported fields, stale opcode/dispatch/operand preimages and overlapping
writes reject. Source-identical requests also qualify current preimages.

Only requested fixed-width operand bytes may change. NPC_RUN depth, extended
context, Y, placement, opaque bytes and unrelated candidate content remain held.
Script targets are not current NPC transforms or live actor coordinates; selector
meanings and runtime dispatch remain unresolved. Bounds remain 128 allocated drafts
and 1024 requested targets with a 4 MiB MAN candidate.

Validation: 18 focused Python checks pass across movement/waits/appearance/dialogue.
Ordinary/extended MOVE_TO/NPC_RUN/EXEC_MOVE, two clones, final offsets, no-op,
wrong values/fields/donors, aliases and stopped paths are covered. A fresh retail
actor0040 two-clone candidate composes independent X/Z and selector edits with own
waits and initial appearance. Exactly six movement bytes changed; layout, waits,
all unrelated candidate bytes and every project file/history entry remain held.
The existing retail NPC wait probe passed again after sharing allocation guards.
Evidence: `local-output/sdk-20260909/npc-movement-native-20261005/proof.json`.
Project commands, persistence, editor controls, presets and normal Build integration
remain next. No game was launched; runtime movement remains deferred. The full SDK
goal stays active/incomplete.

## Explain NPC authored edits in saved-script comparison - 2026-10-05

Retail donor/generated NPC comparison now labels exact bytes accounted for by
saved initial-appearance, own-dialogue and own-wait audit spans. Each span binds
the emitted allocation, separate retail/generated offsets, exact before/after
bytes and the current NPC authored field. Overlapping or inconsistent spans,
wrong owners, preimages, values or allocations reject. Source/header bounds and
receipt integrity are rechecked. The browser independently verifies the same
span bytes and authored bindings before displaying the explanations.

Unaccounted changes remain **Other record change - unexplained**. They are not
classified as authored edits or presumed to be harmless append rebasing. Counts
report only changed bytes within qualified spans. Existing header/tail byte
comparison, opaque-path limits and runtime uncertainty remain intact. The whole
workflow is read-only and the bounded/paged comparison table remains available.

Validation: 19 focused Python checks and the Node comparison contract pass.
Actual retail saved Build `a61cd16b02574b72` contains 26 changed bytes: 23 accounted
for by initial appearance, own dialogue and own wait; 3 remain unexplained. The
real server/dialog rendered all categories, the 540px screenshot was inspected,
and every project file/history entry remained unchanged. No command, Save, Build
or Run was called. Evidence:
`local-output/sdk-20260909/npc-authored-script-comparison-20261005/proof.json`.
No game was launched. Gameplay equivalence remains unverified and the full SDK
goal stays active/incomplete.

## Preserve NPC-owned waits in reusable presets - 2026-10-05

NPC preset capture now freezes supported own wait targets together with own
dialogue and independent initial appearance. Capturing, portable transfer and
reviewed placement freshly qualify the wait operands against the recorded script
donor. Changing the source draft later does not change the captured definition.
Library import creates an independent preset identity; placement remains a separate
reviewed command. Inspector library/import summaries show the owned wait count.
The preceding temporary rejection of wait-bearing capture is superseded.

Wait-bearing presets use portable format **legaia.npc-preset-file.v4**, bounded
at 512 KiB. V1 donor-only, v2 text and v3 appearance formats retain their formats and
bounds. Exact donor-owned wait IDs and duration_ticks integers 0..32767 are required;
older formats cannot carry wait bindings. Presets contain metadata, not retail
script/model payloads or live state. Undo/Redo and Save/Open retain all bindings.

Validation: 19 focused Python checks and two Node suites pass, including frozen
capture, v4 transfer/placement, wrong types/owners and older-format rejection.
Actual browser capture/download/upload, reviewed library import with input
withdrawal, Undo/Redo, Save/reload and scene-reviewed placement passed across two
private projects. The 540px review was visually checked. Normal recipient Build
`a61cd16b02574b72` independently read back own wait 11 ticks, model105/animation13
and complete own dialogue. Package SHA256:
`006d1deec3bfce5982734a2844e2ef647975c15ce50befe3af72bff4adf26889`.
Evidence: `local-output/sdk-20260909/npc-waits-presets-20261005/proof.json`.
No game was launched; runtime timing, residency and script compatibility remain
deferred. The full SDK goal stays active/incomplete.

## Independently author NPC wait targets - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC wait targets**.
The source-qualified picker separates retail targets from optional NPC-owned
WAIT_FRAMES overrides and accepts integer duration_ticks 0..32767. Review binds the
full current project/draft; input changes withdraw Apply, and stale reviews reject.
Apply/Clear make one existing NPC history step. Undo/Redo and Save/Open retain
script donor, own appearance, own dialogue, name and placement. Changing the script
donor with retained waits requires clearing them first. Asset summaries label own
wait targets separately; no runtime timing, seconds or reachability is asserted.

Normal compressed/streaming MAN composition now uses the native clone adapter
against final allocated record identities. The saved package records a separate
npc_wait_changes audit. NPC preset capture currently rejects wait-bearing drafts
explicitly, preventing silent omission; preset capture/transfer/placement support
is still next.

Offline validation: 36 focused Python checks and two Node contracts pass.
The actual root editor passed source loading, reviewed Apply, input withdrawal,
Clear, Undo/Redo and Save/reload. The 540px dialog screenshot was inspected.
Normal Build `5e3865fd5768fd42` independently reopened the emitted NPC script with an
exact 11-tick operand, model105/animation13 and complete own dialogue. Other drafts
and imports stayed fixed. Package SHA256:
`e3ab5e46486e9869c807360b6f3192b24f3b0ecbdea78ba2600c0e889948e54b`.
Evidence: `local-output/sdk-20260909/npc-waits-editor-20261005/proof.json`.
This actual package check covers the compressed MAN route; streaming composition
is integrated but has not received a separate retail package check for own waits.
No game was launched. Runtime timing acceptance remains deferred and the full
SDK goal remains active/incomplete.

## NPC-owned wait operand native adapter - 2026-10-05

Added a source-qualified serializer for independent WAIT_FRAMES operands on
allocated NPC scripts. Requests bind a draft, recorded retail script donor and
supported stable wait IDs with integer duration_ticks 0..32767. The adapter resolves
final record indices after all appends, verifies extent/local entry ownership,
rejects aliases/retail targets, requalifies current instruction layout and checks
exact operand preimages. Only selected two-byte targets can change. Limits are
128 drafts and1024 targets per candidate. Seconds and runtime scheduling are not
inferred; unknown/stopped source paths remain unsupported.

Nine focused checks pass across NPC waits, existing wait/appearance/dialogue
adapters. Coverage includes two independent clones, ordinary/extended waits,
boundaries, source-identical no-op, stale preimages, final offsets, aliases,
malformed ownership/values and decoder stops. Fresh town01 discovery qualifies
waits for actors0040/0044/0046. A retail two-clone candidate from actor0040 holds
independent11/22-tick targets, composed with the existing model/animation appearance
patch. Layout, all non-wait candidate bytes, donor candidate record and every
project file/history entry remain unchanged. Append's supported spawn-reference
rebasing is already part of the pre-wait candidate baseline; this is not a claim
that append preserves raw retail records byte-for-byte.
Evidence: `local-output/sdk-20260909/npc-waits-native-20261005/proof.json`.
Project commands, persistence, presets, editor controls and normal Build integration
remain next. No game was launched; runtime timing acceptance stays deferred.
The full SDK goal remains active and incomplete.

## Review NPC appearance in the placed scene - 2026-10-05

The NPC appearance picker now offers **Inspect NPC appearance in scene** after
Review. It renders a detached Proposed scene at the selected NPC's existing
placement, with Current/Proposed switching and Return to NPC appearance. Return
retains the reviewed choice; changing the choice withdraws inspection and Apply.
The SDK requalifies the witness and review before creating the detached view.
Project metadata, retail imports, script donor, own dialogue and history remain
unchanged. Scene identity, retained placement/script/evidence, unrelated entities
and model/geometry ownership are checked before displaying the proposal.

Offline validation: 11 focused Python checks and the Node appearance contracts
pass. Actual retail HTTP rejects stale reviews and unsupported fields. The full
editor passed clear-override model92-to-model105 comparison, both layer switches,
return-to-review and changed-choice withdrawal without command, Save, Build or
Run calls. The scene screenshot was inspected. Evidence: proposal-proof.json and
appearance-proposal-scene.png under
`local-output/sdk-20260909/npc-appearance-editor-20261005/`.
This is a visual authoring preview; runtime compatibility remains unverified.
No game was launched. Gameplay acceptance stays deferred and the full goal active.

## Independently author an NPC initial appearance - 2026-10-05

NPC Inspector and registered Asset Details now offer **Choose NPC initial
appearance**. The reviewed picker uses freshly source-qualified retail witnesses
for existing local model/animation pairs. Apply changes one authored binding,
retaining the script donor, own dialogue, name and placement. Changing the picker
withdraws Apply. Clear restores the script donor's initial pair. Undo/Redo and
Save/Open preserve the independent binding; changing script donor while bindings
are retained requires clearing them first.

Scene preview, asset/model references, model navigation and animation inspection
follow the appearance witness; retail script inspection continues to follow the
script donor. Frame inspection still targets the authored NPC placement. Normal
compressed/streaming MAN composition uses the native adapter from the preceding
checkpoint to patch final allocated header offsets only. Saved Build inspection
now qualifies the emitted pair against its recorded appearance witness.

NPC presets capture both supported own appearance and dialogue. Portable format
v3 binds the appearance witness to the script donor and owning import, retaining
the 512 KiB authored metadata bound. V1 donor-only and v2 text-only files retain
their existing formats/bounds. Transfer and placement reverify compatible pairs;
no retail script/model payload or runtime state is copied into the preset.

Offline evidence: 42 focused Python checks and five Node contracts pass. Actual
Inspector/Asset Details review, withdrawal, Apply, Undo/Redo, Save/reload, scene
and model reference checks passed; the 540px layout was inspected. Normal Build
`47edfdee85c4fdb2` contains exact model92/animation9 and the complete authored glyph
span, preserving script donor0012 and other drafts/imports. Retail witness0040
animation inspection and frame1 scene placement passed without history changes.
V3 capture/export and synthetic cross-project transfer/instantiation preserve both
bindings. Evidence is under `local-output/sdk-20260909/npc-appearance-editor-20261005/`.
No game was launched. Initial assignment does not prove script compatibility,
residency, eventual appearance or gameplay; those checks remain deferred.

## Independent NPC appearance native adapter - 2026-10-05

Added a source-qualified native adapter that keeps an NPC's script donor separate
from its initial model/animation witness. Requests identify an allocated draft and
a retail witness record; native numbers and bytes are not supplied by clients.
The existing MAN assignment validator checks local bank membership, compatible
object/channel counts and donor ownership. Only the selected clone's two initial
header bytes can change. Final record identities resolve offsets after all appends;
intermediate allocation offsets are not reused. Retail records, aliases, ambiguous
allocations, unsupported pairs and changed header preimages reject.

Focused synthetic checks cover two clones, later table growth, exact byte scope,
repeat/preimage rejection, malformed ownership, aliases and incompatible channels.
A retail town01 candidate changed model105/animation13 to qualified model92/
animation9 from donor0040 while retaining script donor0012 and authored dialogue.
Exactly two header bytes changed; all other bytes and the second clone remained
unchanged. Project state/history/files were preserved. Evidence is under
`local-output/sdk-20260909/npc-appearance-native-20261005/`.

This is native foundation work, not yet an editor feature or normal Build input.
Next: integrate an independent appearance binding into project commands, scene
preview/asset/animation references, persistence, presets and normal Build, then
verify the complete editor workflow. Runtime compatibility and gameplay remain
unverified; no game was launched. The full SDK goal remains active.

## Retain NPC dialogue in reusable presets - 2026-10-05

Capturing an NPC preset now freezes its supported own dialogue with the retail
donor, name and native-grid placement defaults. Later edits or deletion of the
capture NPC do not change the preset. Reviewed placement deep-copies those edits
into an independent new NPC, where normal dialogue authoring and Build apply.
Capture, transfer and placement reverify the text runs through the existing
source-qualified equal-span serializer; unknown/aliased runs, controls, oversized
text and a mismatched donor reject. Runtime state and other script edits remain
outside this snapshot.

NPC preset JSON v2 carries only source-bound preset metadata and user-authored
text edits, with a 512 KiB file bound. Donor-only NPC v1 and ordinary actor preset
files retain their 8 KiB bound and original format. A version/content mismatch
rejects. The editor displays the owned-run count and verifies that placement
retains the exact captured text. No retail script bytes or native packets are
included in the portable file.

Offline evidence: 16 focused Python checks and the NPC preset/file browser
contracts pass. A real two-project browser workflow captured text, downloaded
and uploaded v2 JSON, reviewed/imported a new library identity, passed Undo/Redo
and Save/reload, then reviewed scene placement and created an independent NPC.
Existing source drafts/imports and recipient scene entities remained unchanged.
The inspected 540px layout is readable. Normal Build `2e2e86485096975f` reads
back the complete authored glyph span including space padding. Evidence is under
`local-output/sdk-20260909/npc-dialogue-presets-20261005/`. No game was launched;
manual spawning, reachability and dialogue-layout acceptance remain deferred.

## Author dialogue independently for an NPC - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC dialogue**.
The workspace freshly verifies the retail donor's supported plain-glyph runs,
shows retail and authored text separately, and reviews a complete NPC-local edit
set before Apply. Checked runs override this NPC only; unchecking restores retail
text. Shorter replacements are space-padded, longer text and control/substitution
edits reject. Existing decoder gates for unknown stops, aliases and menu ownership
remain intact. Static paths do not establish runtime dialogue reachability.

One reviewed command updates the authored NPC draft with one Undo step. Undo/Redo,
Save/Open, draft copies and authored-input freshness retain the NPC-local text.
Changing donor while text is retained rejects with an explicit clear-first message;
text-run identities cannot silently migrate to another donor. NPC presets still
capture donor/placement definitions; text presets remain a separate future feature.

Normal Build patches only the audited appended record, after allocation and before
other scene composition, using freshly verified source glyph preimages and bounded
equal-span offsets. Compressed and streaming MAN paths share the same adapter.
Retail donor records, other NPCs, record extents, controls and section layout remain
unchanged by these text edits. Build audits expose the NPC-owned text spans.

Offline evidence: 41 focused Python checks and four Node contract suites pass. Real editor
Review/Apply/Undo/Redo/Save workflows and inspected 540px layouts passed in private
format6 fixed-span and format7 relocated projects. Normal packages independently
read back exact NPC text; complete generated donor records match their prior
Builds exactly. Asset Details reopening shows the persisted own text; its action
row now wraps to keep buttons inside the dialog. Both source/generated
comparisons show 26 changed bytes including placement headers. Evidence is under
`local-output/sdk-20260909/npc-dialogue-20261005/`. No game was launched; spawning,
reachability, text layout and runtime behavior remain deferred manual acceptance.

## Compare saved NPC records with retail donors - 2026-10-05

The generated NPC script workspace now offers **Compare generated record with
retail donor**. Both records are freshly inspected against the current project,
verified source disc and intact saved Build receipt. The dialog compares exact
bytes at the same relative record offsets and retains separate retail and
generated MAN offsets, record hashes, lengths and script-entry offsets.

Changes before both script entries are labelled record header; other changes
are labelled script or remaining record bytes. Missing bytes are explicit, and
large differences are paginated in groups of 128. Script tails include opaque
and unvisited data. Matching bytes establish neither instruction equivalence
nor runtime spawning, scheduling or execution. Closing returns to the generated
record workspace with the selected NPC retained. Stale inputs and inconsistent
comparison counts, bytes, scopes or identities reject before rendering.

Offline evidence: focused Python and Node comparison, generated-record and
retail-source checks pass. Real browser comparison passed format6 fixed-span
and format7 relocated packages, including inspected 540px layouts. Both have
2 changed header bytes and 507 identical common bytes; their script tails match.
Retail MAN offset 8487 remains distinct from generated offsets 44648 and 44720.
Project history, authored inputs and every preexisting file remained unchanged;
no Save, Build or game launch occurred. Evidence is under
`local-output/sdk-20260909/npc-script-comparison-20261005/`. Manual gameplay
verification remains deferred; this milestone is read-only package evidence.

## Inspect NPC scripts emitted in saved Builds - 2026-10-05

NPC Inspector and Asset Details now offer **Inspect saved Build script...**.
Choose an intact saved package matching current authored inputs. The SDK verifies
the receipt/audit/manifest/archive and user-owned source disc, reconstructs the
emitted PROT from verified fixed-span overlays or relocation data, then reads the
actual generated MAN record by the audited NPC allocation index. Final table
spans are parsed from emitted bytes, never copied from intermediate append offsets.

The read-only workspace exposes generated dialogue, instruction navigation and
raw/record evidence with Build-scoped script identities. Retail donor inspection
remains separate. Stale inputs, wrong NPC/record/package identities, changed
payloads, ambiguous overlay spans and invalid record bounds reject. Package and
source-disc integrity do not establish runtime spawning, scheduling or execution.
The former **Inspect serialized candidate** label is corrected to **Inspect donor
append prototype**; prototype text now directs complete-project readiness to
Review Build rather than claiming that normal NPC Build is unavailable.

Offline evidence: 21 focused Python checks and Node generated/donor/Asset/NPC
Inspector contracts pass. Actual browser workflows passed both Inspector entries,
generated/retail separation, path navigation and inspected 540px layouts for a
format6 fixed-span package and a format7 relocated package. Stale-input receipts
reject. Final bounded payload reads and record/hash guards accept both actual
package responses. Generated offsets are44648 and 44720 respectively. Project,
history, Build input identity and preexisting files are unchanged. No new Build,
Save, game launch, install or disc export occurred. Evidence:
`local-output/sdk-20260909/npc-saved-build-script-20261005/` (`proof.json`,
`final-readback.json`, `fixed-540.png`, `relocated-540.png`). Gameplay remains deferred.

## NPC retail donor script inspection - 2026-10-05

Authored NPCs now expose **Inspect retail donor script...** in the NPC Inspector
and a registered **Inspect retail donor script** action in Asset Details. The SDK
qualifies the active draft/donor and freshly verifies the imported donor against
the user-owned disc. The read-only workspace shows decoded dialogue, searchable
instruction paths, flow overview, successor navigation, source spans, raw record
and explicit decoder stops. Unknown paths and branch reachability stay unknown.

The report captures full project source identity and exact draft/donor provenance;
stale or forged bindings and authoring/generated claims reject. Source offsets
belong to the imported donor, not allocated NPC code or a live actor. This view
adds no NPC script authoring or runtime execution claim. Donor authoring remains
separate from this retail-only inspection.

Offline: 20 focused Python checks and donor-script, Asset Inspector and NPC
Inspector Node contracts pass. The private retail browser passed both entry points,
exact source response, instruction navigation and retained NPC selection. The
540px layout was inspected. Donor0012 has 25 decoded instructions and16 dialogue
segments; its record SHA-256 is
`5063e5eb8bfd400fba142b0eabee28f50c46b900aa319ebdf86fd0b4eea73a65`.
Project document, Undo/Redo history, normal Build input identity and preexisting
files stayed unchanged. No commands, Save, Build, game launch, install or disc
export occurred. Evidence: `local-output/sdk-20260909/npc-donor-script-20261005/`
(`proof.json`, `browser.log`, `donor-script-540.png`). Gameplay remains deferred.
See [NPC donor script workflow](legaia-npc-donor-scripts.md).

## Copy selected NPC arrangements - 2026-10-05

**Repeat draft...** now offers **Copy selected NPC arrangement** when the current
or recalled selection contains at least two same-scene NPC drafts. Mixed selection
members outside the NPC group are excluded with a count. Copy the arrangement in
a line or rectangular grid: each member keeps its own retail donor and receives
the same native-grid offset per repetition, preserving relative X/Z positions.
Copies receive independent stable IDs and bounded member-derived names. They are
independent NPC drafts; no parenting, prefab inheritance or runtime spawning is
asserted. The project-wide 128-draft limit and native coordinate bounds apply.

Review creates no project changes. Detached scene inspection retains original
entities and each copied member's model binding, with Current/Proposed/Return.
Source/input changes withdraw the review. Apply adds all copies in one Undo step;
Redo and Save/Open preserve them through the existing normal Build pipeline.

Offline: 13 focused Python checks and Node proposal/scene contracts pass. A private
retail browser copied two differently bound NPCs, checked held originals, exact
relative placement and member-specific geometry, then Apply/Undo/Redo/reload.
The 540px review was inspected. Normal format-7 Build independently decoded the
complete candidate MAN and all nine appended records: new record57 is X3392/Z5632,
model105/animation13; record58 is X3072/Z5632, model111/animation56. Current saved
receipt and preserved project/history/preexisting files pass. Evidence lives in
`local-output/sdk-20260909/npc-arrangement-repeat-20261005/` (`project-verified-2`,
`proof.json`, `normal-build-proof.json`, `arrangement-540.png`). Package SHA-256:
`88fe43534bacd8dfe12a5d9a9e02d3b56f0d2fc834e636cc2397880056c2f6ab`.
Gameplay spawning, scheduling, scripts, collision and visibility remain deferred.
No game launch, install or disc export occurred.

## Reviewed NPC group retail donor assignment - 2026-10-05

The NPC Inspector now offers **Assign NPC group donor...** for 2 through 128
same-scene drafts. Current or recalled scene selections seed the dialog; mixed
selections retain only NPC members with an exclusion note. Choose an imported
retail donor, review the exact membership, then inspect the detached proposed
scene with Current/Proposed comparison and Return before Apply. Identity, name
and X/Z stay fixed; imported actors and unselected scene content stay unchanged.

This changes inherited native model, initial animation, scripts and related actor
data. It is donor reuse, not arbitrary model/animation assignment. Source changes,
input changes and malformed proposals reject or withdraw Apply. One Apply creates
one Undo step; Redo and Save/Open preserve the reviewed donor bindings.

Offline evidence: eight focused Python cases and the Node proposal guards pass.
The actual private browser passed Review without mutation, detached scene model
bindings, Current/Proposed/Return, input withdrawal, Apply, Undo/Redo and reload.
The final read-only check passed the tightened guards and an inspected 540px
layout. Normal Build independently decoded the complete format-7 compressed MAN:
selected records 53/54 retained X/Z 2944/5568 and 3136/5568 while changing donor
model/animation from 105/13 to 111/56. All five unselected appended records retained
105/13 and their positions. Saved receipt freshness and project preservation pass.
Evidence: `local-output/sdk-20260909/npc-donor-group-20261005/` (`proof.json`,
`normal-build-proof.json`, `ui-final.log`, `donor-group-540.png`). Package SHA-256:
`e936966c4e152a74f4fe35c1ffd722b499c888d79e3316e3ef9eac486117a58c`.
Gameplay visibility, spawning, scheduling and inherited script behavior remain
unverified. No game launch, install or disc export occurred.

## Repair saved selections after NPC deletion - 2026-10-05

Saved selections containing deleted NPCs now support **Replace with current
placements**. Select available placements in the saved scene, then replace the
membership. The set keeps its stable identity and name; one Undo restores its
previous members, including missing NPC references. The dialog identifies
unavailable NPCs and explains the repair path. Recall still rejects missing NPCs.

Replacement proves the original import and MAP binding before dropping members,
including removal of all scenery. New membership must be available in the owning
scene. Stale keys, source drift, empty/invalid replacements or a project change
during source proof reject before publication. Repair changes editor metadata only.

Validation: 16 focused scene/actor selection Python cases and both Node selection
suites passed. Checks cover source drift, stale keys, unavailable replacements,
metadata Undo/Redo, persistence and unchanged Build identity. Actual private Town01
browser checks passed the missing-member note, rejected Recall, same-ID/name repair,
Undo/Redo, Save/reload, disk reopen and successful repaired NPC focus. The 540px
message was inspected; no page errors occurred. Imports, game overrides, NPC data
and Build input identity stayed unchanged. Evidence:
`local-output/sdk-20260909/npc-selection-repair-20261005/proof.json`.
No game launch, Build, installation or full-disc export ran for this metadata-only
repair. Gameplay remains deferred; the full SDK goal stays active and work stays solo.
See [Saved scene selections](legaia-scene-selections.md).

## Saved NPC selections feed group authoring - 2026-10-05

Opening **Move NPC draft group...** now checks the NPC members of the current
scene placement selection, including recalled saved selections. A focused draft
remains the default when no NPC group is selected. The dialog copies membership
and qualifies every selected NPC against the active scene before opening.
Unavailable, wrong-scene, duplicate or oversized selections reject with a visible
error. Existing checkbox/search controls still let the user change membership.

For mixed selections, the NPC tool includes only NPC members and reports how many
other placements it excludes. Use mixed scene placements to edit all kinds together.
This closes the saved-selection-to-authoring handoff for offset/layout/removal review;
selection alone does not change project or game data. The existing review source
binding, detached scene proposal, atomic command history and serializer remain.

Validation: 16 focused SDK group/selection cases, the expanded group and saved
selection Node checks, and editor syntax passed. Actual private Town01 browser
checks covered focused default membership, saving/reloading/recalling an NPC pair,
exact checked members and review targets, preview without mutation, Apply/Undo/Redo,
unchanged unselected drafts, explicit mixed-selection scope, Save/reload and disk
reopen. The 540px dialog was inspected; no page errors occurred. Normal format 7
Build readback matched the complete prepared MAN and all seven appended NPC rows,
including the edited pair with donor model/animation preserved. Saved package
verification matches current inputs; Build preserves project/history/preexisting
files. Package SHA256:
`cafe9311747208ea97b8dbc54cb50e7a772397aaaeb1189761b8444011550cc4`.
Evidence: `local-output/sdk-20260909/npc-selection-group-handoff-20261005/proof.json`
and `normal-build-proof.json`. No game launch, installation or full-disc export ran.
Gameplay remains deferred; the full SDK goal remains active and work stays solo.

## Native-grid NPC group rotation, scale and reflection - 2026-10-05

The NPC group Inspector tool now adds position rotation (-90/+90/180 degrees),
spacing scale (1-1000 integer percent), and X/Z coordinate reflection about a
selected NPC anchor. It operates on 2-128 existing NPC drafts in the active Edit
scene. Rotation uses exact X/Z quarter-turn permutations; scale rounds final
coordinates to the native 64-unit grid with half steps away from zero. Reflection
changes one coordinate. The selected anchor stays fixed. These layouts change
positions, preserving model geometry, facing, donor bindings and other metadata.
Rounded placements can coincide; inspect Current/Proposed before Apply.

Exact typed layout requests, a distinct native-layout review-key binding, complete
source snapshots and full bounds validation qualify the whole group. Invalid,
stale or out-of-bounds proposals publish nothing. The existing detached scene
preview and atomic Apply/Undo/Redo work unchanged; no-ops retain redo history.
Offset, alignment, distribution and removal remain compatible.

Validation: 16 focused Python cases and group/repetition/mixed-NPC Node checks passed.
Actual private Town01 browser checks covered all three rotations, scale and both
reflection axes, fixed anchor, input withdrawal, Current/Proposed/Return, exact
renderer matrices, unchanged geometry/unselected entities and preview without
mutation. One reflection passed atomic Apply/Undo/Redo, Save/reload and disk reopen;
the 540px dialog was inspected, with no page errors. Normal format 7 Build readback
matched the complete prepared MAN and all seven appended NPC positions, model 105
and animation 13. Saved package verification matched current inputs; Build preserved
project/history/preexisting files. Package SHA256:
`b3185a16a71aea60a3ffba163d1f0131f021daeab4168751fb07f0ac72eab560`.
Evidence: `local-output/sdk-20260909/npc-native-layout-20261005/proof.json` and
`normal-build-proof.json`. No game launch, installation or full-disc export ran.
Gameplay remains deferred; the full SDK goal stays active and work stays solo.
See [NPC draft group workflow](legaia-npc-draft-groups.md).

## Saved scene selections include NPC drafts - 2026-10-05

**Saved scene selections** now stores 1-128 scene placements including authored
NPC drafts, imported actors and static decorations. Save an individual NPC from
its Inspector focus or capture a mixed selection. Recall focuses the NPC Inspector
for a single draft and restores mixed membership for the placement tool, including
when switching from another imported scene. Saved sets retain identities, so NPC
moves and renames do not restore old transforms or duplicate actors.

NPC-only sets require no MAP hash. Scenery membership retains fresh MAP source
proof, and NPC members must be available in the owning scene for Create/Replace/
Recall. Deleted NPC references remain portable metadata: Save/Open, Rename and
Delete still work, while Recall reports the unavailable member. Undoing deletion
restores recall. Existing source-bound actor/scenery sets remain compatible.

Validation: 17 focused Python cases, scene/actor selection Node checks and editor
syntax passed. Actual private Town01 browser checks passed mixed and NPC-only Save,
library Undo/Redo, Save/reload, NPC Inspector focus, cross-scene mixed recall, opening
the recalled mixed placement dialog, missing-NPC rejection and deletion Undo.
The 540px dialog was inspected; no page errors occurred. Imports, NPC content,
game overrides and Build input identity remained unchanged by selection metadata.
Evidence: `local-output/sdk-20260909/npc-saved-selections-20261005/proof.json`.
No game launch, Build, installation or full-disc export ran for this metadata-only
feature. Gameplay remains deferred and the full SDK goal remains active. Work is solo.
See [Saved scene selections](legaia-scene-selections.md).

## NPC drafts in mixed scene placement groups — 2026-10-05

**Scene tools → Select scene placements → Move scene placement group** now accepts
2–128 members spanning at least two of imported actors, authored NPC drafts and
static decorations. Shared offsets, alignment, distribution, spacing scale, position
rotation and coordinate reflection use the existing review workflow. NPCs keep native
64-unit X/Z coordinates and may be layout anchors. Their donor, name and other
metadata stay unchanged. Current/Proposed inspection holds source preview height.

NPC-inclusive reviews use version 2 and bind the full Current draft snapshot. NPC
Retail placement is absent and shown as **Authored only**; Retail reset is disabled
and rejected for the entire group. Existing actor/scenery version 1 reviews remain.
Apply validates the whole proposal before changing overrides and NPC drafts, then
records one combined Undo step. No-op operations preserve history and redo. Saved
selection sets and runtime placement semantics are separate work.

Validation: 31 focused Python cases, new NPC source/DTO guards, legacy mixed-placement
Node checks and editor syntax passed. Actual private Town01 browser checks covered
three-kind selection, hierarchy membership, exact proposals with held height, review
without mutation, Current/Proposed inspection, atomic Apply/Undo/Redo and Save/reopen.
The 540px review was inspected; no page errors occurred. Normal Build emitted a
format 6 package whose complete native MAN and MAP carriers match preparation.
Readback confirmed imported actor record 12 at X/Z 3840/1920 and appended NPC record
53 at 3008/5696 with donor model 105 and animation 13. The decoded-size patch and
saved receipt match current inputs; Build preserved project/history/preexisting files.
Package SHA256: `e728785c95c6e58f925b3873b785c21b93396e6c711bb9c64f2f465182b61361`.
Evidence: `local-output/sdk-20260909/mixed-npc-placement-20261005/proof.json` and
`normal-build-proof.json`. No game launch, installation or full-disc export ran.
Gameplay remains deferred; the full SDK goal remains active. Work continues solo.
See [Mixed scene placements](legaia-scene-placement-groups.md).

## NPC preset file transfer — 2026-10-05

NPC presets now use metadata-only `legaia.npc-preset-file.v1` JSON in the shared
preset export/import workflow. The editor downloads `npc-preset.json`, reviews an
independent named library import, then places a new NPC through the separate
reviewed placement workflow. File/schema scope, exact source/components, capture
provenance, matching import hashes and the 8 KiB limit are checked. Export/import
freshly verify the owning retail scene against the project user's disc. Unknown
payload fields, changed sources and stale library reviews reject. Imported-actor
preset application remains separate.

Actual private two-project browser acceptance verifies download/upload, a new
library identity with retained provenance/defaults, changed-name review withdrawal,
library Undo/Redo, Save/reload and disk reopen, then detached scene inspection and
placement without the original capture draft. Source project document/history and
all file bytes stay unchanged; recipient imports and existing scene entities stay
unchanged. The 946-byte exported file contains metadata only. The 540px import
review is visually inspected with no page errors. Focused NPC/template-file Python
and Node checks and existing animation-preset regression checks pass.

The recipient's private normal format-6 Build uses the compressed reserved-span
route. Native MAN bytes exactly match preparation; descriptor decoded size and
new record 53 read back at X 2944 / Z 5632, model index 105, animation ID 13. Saved
receipt verification matches current inputs. Package SHA-256:
`5f3f409de8ac2e613f18602bb1771312bca52b00c2d2caf1dbcfd9adf3d3b5c6`.
Evidence: `local-output/sdk-20260909/npc-preset-transfer-20261005/proof.json`,
`normal-build-proof.json` and `transfer-review-540.png`. No game, install or full-disc
export occurred. Prefab inheritance, cross-scene remapping and runtime gameplay
acceptance remain unsupported or deferred. See [NPC presets](NPC_PRESETS.md).

## Reusable NPC draft presets — 2026-10-05

The preset library now supports a separate `npc-draft-preset-v1` scope. Select an
NPC draft and choose **NPC presets…** to capture its retail donor, authored name
and native X/Z defaults with owning scene, import hash and original draft provenance.
Review a new named instance at a chosen 64-unit-grid placement, compare the detached
scene with Current, then Apply. Capture and placement each have their own Undo step;
rename, delete, Save and reopen use the existing project template library. A preset
survives deletion of its original draft. Imported-actor template Apply rejects this
scope; cross-scene, stale, Live-mode and invalid placement requests fail closed.

Focused Python/Node checks and an actual private browser pass capture, changed-input
review withdrawal, exactly one scene addition, preservation of existing entities,
Apply, atomic Undo/Redo, Save/reload and disk reopen. Narrow review actions wrap
within the 540px viewport. A private normal format-7 Build contains all seven authored
NPC rows; the preset instance reads back from native MAN at X 3008 / Z 5632. Complete
native MAN bytes match preparation and saved receipt verification matches current
inputs. Package SHA-256:
`18ea1110520c28bdb321499dc8f466f868512be03b982736eddc8429c1e43adc`.
Evidence: `local-output/sdk-20260909/npc-presets-20261005/proof.json`,
`normal-build-proof.json` and `preset-review-540.png`.

This is project-local donor/placement reuse, not prefab inheritance or an authored
script/appearance snapshot. Shared asset edits remain project-wide. See the NPC
preset transfer milestone for file interchange; cross-scene remapping remains
unsupported. Runtime spawning,
scheduling, collision and visibility remain deferred to manual gameplay; no game,
install or full-disc export was performed. See [NPC presets](NPC_PRESETS.md).

## NPC animation frames at authored scene placement — 2026-10-05

**Inspect animation in scene** now targets the selected NPC draft when entered
through its donor animation Inspector. The donor remains the verified animation
source; the NPC becomes the explicit display target. Existing imported-actor
inspection retains its prior target selection. A dedicated adapter qualifies the
current scene source, unique authored entity, recorded donor/model and authored
X/Z placement before accepting an NPC target. Wrong source, model, donor, duplicate
entity or changed placement rejects the inspection.

The existing isolated geometry workflow changes only the target's display geometry
key. Authored/source position, sampled elevation, display position and model-to-scene
transform remain intact. NPC selection and framing synchronize with the inspection;
the scene bar uses its authored name. Frame changes retain the same NPC geometry
instance. Restore returns the qualified Current scene. This is display-only pose
inspection, not animation assignment, runtime playback or gameplay acceptance.

Focused NPC Inspector Node checks pass source/target/placement rejection. Actual
private browser with shared authored channels and a different authored donor
appearance verifies exact frame vertices, unchanged donor/all other entities,
retained authored transform, NPC selection, frame advancement and restoration.
The 540px viewport is visually inspected with no page errors. Project document,
history and every project file byte remain unchanged. Evidence:
`local-output/sdk-20260909/npc-animation-scene-target-20261005/proof.json` and
`npc-scene-540.png`. No Build, game launch, install or disc export occurred.

## NPC animation Inspector matches shared authored preview — 2026-10-05

The NPC animation button previously opened the imported donor clip even when the
Authored viewport showed shared authored animation channels. It now uses a
qualified SDK draft model reference and the current NPC pose kind: imported pose
opens the retail donor clip; authored pose opens shared authored channels. Labels
identify the representation. Unsupported/missing poses have no fallback action;
pending refresh, busy state and detached scene proposals cannot arm navigation.
The click rechecks source context and binding before opening the model dialog.

The retail donor model and clip owner remain explicit. The donor's authored
appearance is separate. `ModelRenderer.asset_id` already retained the retail
model; inspection corrected the initial suspected wrong-model diagnosis. This
change fixes the animation representation mismatch and strengthens binding checks,
without claiming an NPC runtime animation identity or an established idle stance.

Focused NPC Inspector and Asset Inspector Node checks pass source/pose coherence,
imported/authored channel choice, unknowns and mismatched donor/model rejection.
Actual private browser uses a verified donor appearance override (0105 to 0092)
and a native shared channel edit in `animation://town01/scene-anm/0012`. It opens
model 0105 with the correct donor owner and authored representation; its first
frame differs from the retail response. The 540px dialog passes with no page errors.
Project document, history and all file bytes remain unchanged during inspection.
Evidence: `local-output/sdk-20260909/npc-donor-animation-binding-20261005/proof.json`.
No Build, game launch, install or disc export occurred. Gameplay stays deferred.

## NPC recorded donor-model inspection — 2026-10-05

Authored NPC records and central project inventory entries now expose the SDK's
existing `draft_initial_model_assignment` reference. It retains source draft/name,
owning scene, model asset ID, retail donor ID and `runtime_binding=not_asserted`.
Unresolved donor model references remain null. The draft assignment uses the retail
donor independently of that donor's authored appearance.

NPC Asset Details shows **Recorded donor model** as a read-only SDK reference and
provides **Inspect recorded donor model** when model preview capability and a
coherent assignment are present. The adapter qualifies source/name/scene/donor,
assignment kind and layer before registering navigation; the editor checks the
current SDK reference again before opening the imported model view. The project
inventory adapter also rejects inconsistent model bindings. There is no runtime
residency/pose claim or property-writing action.

Validation: 22 focused Python Inspector/inventory cases pass, including retail
donor separation and explicit unknowns. Asset Inspector and project inventory Node
checks pass binding, malformed-reference, capability and unresolved-action checks.
Actual private browser matches SDK fields in active/project scopes and opens the
exact recorded model response; 540px layout passes, with no page errors. Document,
Undo/Redo and all project file bytes remain unchanged. Evidence:
`local-output/sdk-20260909/npc-donor-model-navigation-20261005/proof.json`.
No Build, game launch, install or disc export was performed. Gameplay stays deferred.

## Reviewed NPC draft group removal — 2026-10-05

The NPC group tool now offers **Remove selected NPC drafts** alongside offset,
alignment and distribution. Review retains exact selected draft metadata and a
full-project source-bound key. Its detached scene proposal removes those authored
instances while preserving every imported and unselected entity. Changing the
operation withdraws Apply. **Remove reviewed drafts** issues `delete_actor_drafts`
and creates one atomic Undo entry; Undo restores stable identities and all metadata.
Only two through 128 existing drafts in the active Edit scene are eligible.
Malformed requests, wrong command types, missing drafts and stale reviews reject
before mutation. Imported donor actors remain unchanged.

Focused SDK group/repetition checks (eleven Python cases) and Node report/scene
qualification pass. Actual private browser verifies review without mutation,
detached removal, operation invalidation, Apply, exact Undo/Redo, save/reload and
independent disk reopen; 540px layout passes with no page errors. A private normal format-7 Build passes current-input saved package verification.
Its final decompressed native MAN matches the prepared candidate and contains
exactly the four remaining appended NPC rows, with both removed identities absent.
Package SHA-256: `e1026d3eb4f83f54970f58b475c157177258f71a05c5b2d5672631dae16b90ef`.
Build leaves the project document/history and preexisting file bytes unchanged.
Evidence is under
`local-output/sdk-20260909/npc-draft-removal-20261005/`. Gameplay remains unverified;
no game launch, install or disc export was performed.

## NPC drafts in the central project Asset Database — 2026-10-05

The SDK project inventory now registers each validated NPC draft as an explicitly
`authored` actor entry. Its stable authored UUID, exact name, donor binding and
X/Z placement remain project metadata. The single owning-scene membership carries
that import's hash as context; it has no retail source record or decoded-catalog
key. Imported/catalog records cannot supply authored NPC identities. Existing
source freshness and asset/membership/metadata budgets cover these entries.

The browser retains imported and authored distinctions, filters by owning scene,
and opens the typed NPC Asset Details and Inspector through existing selection.
The membership control says **Authored NPC owning scene** and explains that its
import hash is context, not a retail origin. Project scope is labeled **Project
resources**. This does not establish runtime residency, spawning or visibility.

Focused validation: nine SDK inventory cases plus two HTTP cases pass; Node
checks cover authored membership, donor/scene/coordinate coherence, source
substitution rejection and scene filtering. Actual private browser checks verify
indexed NPC membership, exact SDK fields, selection and the 540px layout, with no
page errors or project/document/history/file changes. Evidence is under
`local-output/sdk-20260909/npc-project-assets-20261005/`. No Build, game launch,
install or disc export was needed. Manual gameplay verification remains deferred.

## Authored NPC Asset Details — 2026-10-05

NPC draft cards in active-scene and project scopes now use the SDK-owned
`AssetNpcDraft` descriptor. It presents the authored identity, name, project scene,
retail donor binding and authored X/Z coordinates with Project/Authored state
badges. Imported actor cards retain their existing descriptor. The separate
`authored_asset_inspectors` mapping preserves imported asset contracts.

The adapter rejects inconsistent draft identities, scene/name/donor records and
invalid native-grid coordinates before mounting the descriptor. Its only registered
action, **Select NPC draft**, uses existing scene navigation and opens the draft
Inspector. This exposes current SDK authored records; it does not add imported
Asset Database memberships or establish runtime spawning/visibility.

Validation: twelve Python Inspector schema cases and the expanded Node asset
Inspector checks pass. Actual private browser checks match every SDK property in
both scopes, select the correct NPC Inspector and pass at 540px with no page errors.
Project document, Undo/Redo and all project file bytes remain unchanged. Evidence:
`local-output/sdk-20260909/npc-draft-asset-inspector-20261005/proof.json` and
`asset-540.png`. No Build, game launch, install or disc export was performed;
manual gameplay verification remains deferred.

## NPC draft Inspector schema checkpoint — 2026-10-05

Eleven Python Inspector schema cases pass read-only contracts, authored X/Z paths,
separate unresolved placement Y/derived preview elevation, no fallback paths,
donor source metadata and detached schema instances. New NPC rendering and prior
environment Node checks pass escaping, no input generation, authored versus preview
values, unknowns and pending/source-during-proposal/unavailable labels. Both editor
module syntax checks pass. Actual private browser matches every SDK property,
retains specialized controls, verifies current snapshot and controlled stale/proposal
context, Retail missing-preview and Authored return. The540px Inspector screenshot
is inspected, with no page errors. All project document/history/files stay unchanged;
only scene-preview reads occur, with no authoring/Save/Build/Run/game/install/export.
Proof: `local-output/sdk-20260909/npc-draft-inspector-schema-20261005/proof.json`.
Campaign follow-up: live pending-refresh/close races, changed donor while geometry
loads, unavailable geometry and source surface, all pose kinds and broader component
migration. Existing gameplay spawning/visibility/collision gates remain separate.

## NPC draft layout/normal-package checkpoint — 2026-10-05

Ten focused Python group/repetition cases and expanded Node contracts pass selected
anchor, exact layout fields, command type binding, preserved other axis, nearest
64-unit distribution/endpoints, insufficient span, changed-count/no-op handling,
atomic history and persistence. Existing offset/detached scene guards remain.
Module syntax passes. Actual private HTTP/browser passes three-member distribution,
Proposed/Current scene qualification, operation-change withdrawal, Undo/Redo, Z
alignment, Save/reload and independent disk reopen. Both layouts use separate batch
history entries; imported/donor metadata and unselected drafts remain unchanged.
The540px layout is inspected and no page errors occur.

Private ordinary Build review includes six drafts and reports ready. Format7 normal
package uses compressed NPC capacity-growth relocation; saved-package verification
matches current inputs. Full decoded final MAN equals the prepared candidate byte
for byte and all appended positions match authored state. Build leaves project
metadata/history and preexisting files unchanged. No gameplay, installation or disc
export. Proof: `local-output/sdk-20260909/npc-draft-layout-20261005/{proof,normal-build-proof}.json`.
Campaign follow-up: Z distribution, X alignment, all tie orders, endpoint span/count
edges, late/closed/stale anchor responses, mixed donors/scenes and runtime spawning,
scheduling, visibility, collision and total actor-pool headroom acceptance.

## NPC draft group movement checkpoint — 2026-10-05

Eight focused Python group/repetition cases pass detached full-group review,
canonical selection order, exact offsets, invalid last target, stale/tampered
review, Live rejection, zero-delta no-op, one Undo entry and Save/Open. New Node
contracts pass source/request/target binding, detached copies, unchanged unselected
scene content, donor/model/display preservation and malformed response rejection.
Existing repetition Node and both editor module syntax checks pass.

Actual private HTTP/browser passes selected subset movement, visible/search
selection, detached scene qualification, no preview mutation, zero delta/bounds
rejection, Apply/Undo/Redo/Save/reload and independent disk reopen. Initial shared-
prefix name search was corrected to stable ID. Narrow clipped actions and cramped
table cells were fixed; the read-only recheck preserves all document/history/files.
Final540px screenshot inspected, no page errors. Native prepared PROT readback
matches six draft positions, including two moved members, and final MAN/PROT hashes;
all project files stay unchanged during native preparation/readback. Initial copied
helper path was corrected to this fixture. No normal Build, gameplay or disc export.
Proof: `local-output/sdk-20260909/npc-draft-group-20261005/{proof,native-proof}.json`.
Campaign follow-up: close/abort races, fresh server project switches, maximum count,
source reimport/other-scene donors, source terrain changes, normal-package routes
and runtime visibility/collision/scheduling/actor-pool headroom acceptance.

## NPC grid repetition checkpoint — 2026-10-05

Twelve focused Python repetition/review cases and expanded Node coordinate checks
pass. Cover row-major grid with negative spacing, distinct pattern binding, stale
columns rejection, project-wide count limit, grid/bounds validation, single-row
zero Z spacing, detached preview, one batch history entry and persistence.
Actual private HTTP/browser review and detached scene pass exact grid coordinates;
line omits optional columns and keeps legacy placement. Pattern changes withdraw
Apply, multi-row zero Z rejects, preview creates no drafts, and Apply/Undo/Redo/
Save/reload plus independent disk reopen pass. No page errors; 540px inspected.
Native prepared PROT reopen/decompression matches all six draft placements and
final MAN hash, with partition-one count59 and one growth sector. Original donor
binding/imports stay unchanged. No normal Build, game, install or disc export.
Proof: `local-output/sdk-20260909/npc-grid-repetition-20261005/proof.json` and
`native-proof.json` in the same directory. Initial out-of-bounds fixtures and
logical-versus-physical table-offset assumptions were corrected before acceptance.
Campaign follow-up: grid columns/count edges, all four spacing sign combinations,
close during scene inspection, multi-scene drafts, normal-package routes and
runtime spawning, scheduling, visibility, collision and actor-pool total headroom.

## NPC Build scope presentation checkpoint — 2026-10-05

Ten focused Python draft repetition/review/HTTP cases, both existing Node contracts
and repetition module syntax pass. Current builder scope is shared by repetition
and experimental review: qualified compressed fixed-span/capacity-growth and raw
streaming relocation routes retain existing gates. Experimental review explicitly
says normal Build readiness is not assessed here; its legacy false flag remains.
Actual SDK scope notes equal visible repetition notes, malformed notes clear the
report and disable Apply, and the 540px dialog is inspected. Close cleanup passes,
no page errors occur, and project document/history/files remain unchanged after
fixture setup. No Build, gameplay, install or full-disc export runs.
Proof: `local-output/sdk-20260909/npc-build-scope-notes-20261005/proof.json`.
This corrects author-facing scope only; it adds no serializer or runtime support.
Campaign follow-up: candidate variants and full-project Review Build readiness,
plus runtime spawning/scheduling and actor-pool headroom remain separate checks.

## General saved-Build freshness checkpoint — 2026-10-05

Expanded general/asset Node Build-history contracts and module syntax pass.
Receipt binding covers archive/disc hashes, kind, report count and current-input
flag agreement with the receipt key. Actual private saved package verification
passes; controlled stale `/api/state` responses withdraw verification tables and
reject history listing before rendering entries, even with unchanged local cache.
A forged returned receipt hash rejects against the selected list entry after a
valid server-state check. Close removes the dialog, 540px failure screenshot is
inspected and no page errors occur. Project document/history/files stay unchanged;
no new Build, Command/Save/Run, game, install or full-disc export occurs.
Proof: `local-output/sdk-20260909/build-history-freshness-20261005/proof.json`.
Campaign follow-up: compare responses during server changes, server path switches,
GET-state failures, close during freshness reads, additional input receipts and
package replacement between list/verify. This fixes presentation freshness and
receipt selection binding; native package serialization and runtime are unchanged.

## Asset saved-Build evidence checkpoint — 2026-10-05

Six focused Python Build-history integrity cases, new asset matching/receipt
Node contracts, existing Build-history decoder checks and module syntax pass.
Cover exact direct versus owner IDs, full nested ledger retention, detached data,
current versus historical inputs, receipt/hash/kind/count mismatch, malformed
identity and no-record semantics. Private normal Town01 Build and actual saved
package verification pass. Asset Details inspection equals SDK verification and
retains all 130 model coordinate words. Controlled DTO UI checks cover complete
301-row paging, removed callback inertia, fresh-server source-key withdrawal and
close cleanup. Pending Verify is disabled and 540px actions/layout are inspected.
The initial harness used hidden `innerText`; corrected full record readback passes.
Inspection leaves project document/history/files unchanged and creates no output;
fixture setup performs the private normal Build. No game or install ran.
Proof: `local-output/sdk-20260909/asset-build-records-20261005/proof.json`.
Campaign follow-up: multiple real receipts, all asset families, owner-only records,
zero matches, invalid/incomplete/truncated histories, selecting another Build,
closing during verification, stale source membership and package file tampering
between list/verify. Shared-ID membership and source-disc/native gameplay integrity
are separate evidence gates; absence from an edit audit is not absence from a game.

## Shared scenery Inspector layout checkpoint — 2026-10-05

Three focused Node Inspector checks and module syntax pass. Actual private
Town01 browser verifies seven scenery section toggles, all header arrows/Home/End,
collapse/expand all, retained unsubmitted individual-transform input values,
same-instance collapsed state and focused-header restoration, detached old header/
tool callback rejection, layout retention across scenery, actor filter/layout
regression and the actual controller's project-boundary reset. Every header fits
at 540px and the Inspector-tab screenshot is inspected. Project document, history
and files stay unchanged; only preview/selection requests occur, with no page
errors or authoring/Save/Build/Run. Evidence:
`local-output/sdk-20260909/scenery-inspector-sections-20261005/proof.json`.
Campaign follow-up: mixed actor/scenery rerenders, unavailable scenery snapshots,
project/source/representation changes, maximum evidence and focused form inputs.
Collapsing retains form nodes; selection/source rerenders retain existing draft
behavior. This is session layout, with no persistence or native byte changes.
No manual gameplay gate is added by this display feature.

## SDK scenery Inspector checkpoint — 2026-10-05

12 focused Python inspector-schema/environment-project cases, scenery adapter
Node checks and module syntax pass. Cover detached read-only metadata definitions,
separate Retail/Current paths, missing Current values without invented inheritance,
escaping, no authoring controls and explicit pending-preview status. Actual private
Town01 browser checks all properties of the four SDK sections, authored placement
versus imported placement, matching GPU translation, Frame and existing shared/
individual source-qualified controls, root Inspector pending-warning withdrawal,
Retail/Authored reload with reselection and the 540px Inspector-tab layout.
Project document, history and files remain unchanged; no page errors or
Command/Save/Build/Run requests. Evidence:
`local-output/sdk-20260909/environment-inspector-schema-20261005/proof.json`.
Earlier browser harness failures remain recorded; final fresh fixture passes.
Campaign follow-up: ground/unrenderable instances, missing source fields, shared
record compensation, individual rotation, source withdrawal during authoring,
maximum evidence size and future schema upgrades. Existing Build/native-byte
placement checks remain separate; no native serialization path changed here.
Runtime transforms, visibility and collision still need deferred gameplay checks.

## Selected asset evidence download checkpoint — 2026-10-05

Focused export and asset-inspector Node checks, nine Python inspector-schema
cases and module syntax pass. Cover complete selected records, separate authored
metadata, multiple membership retention, UTF-8 size bounds, unsupported/cyclic
metadata, busy/pending duplicate suppression, local/server source withdrawal and
closed details during pending fetch. Private Town01 browser downloads actual
active and project-scope model records; both JSON files equal the selected records,
with source hashes and authored settings retained. Fresh-server source mismatch
blocks download; 540px button bounds and screenshot pass. Project document,
history and files remain unchanged. No authoring, Save, Build or Run requests.
Proof: `local-output/sdk-20260909/asset-record-evidence-20261005/proof.json`.
The first attempt failed due to a missing static route; its log is retained and
the route fix passed a fresh-fixture browser run. Campaign follow-up: every asset
family, multiple actual shared-scene memberships, unavailable source records,
source replacement during pending fetch and near-budget project metadata. This
is catalog evidence export; native payload integrity and gameplay are not claimed.

## Mixed placement mirror checkpoint — 2026-10-05

28 focused Python layout/group/HTTP cases, expanded mixed-placement Node checks and
module syntax pass. Cover both native reflection axes, off-grid fixed anchor, final
actor half rounding, unchanged other-axis metadata, atomic invalid/stale requests,
native bounds/offset overflow, no-op redo and forged/safe arithmetic. Actual private
Town01 browser checks both axes, operation withdrawal, Current/Proposed GPU matrices
with height/rotation held, Return and one Apply at 540px. Undo/Redo, Save/Open and
normal Build pass with full MAP directory/ZIP and independent MAN placement/opaque
readback; the unchanged actor axis remains unauthored. Screenshot inspected, no page
errors. Proof: `local-output/sdk-20260909/mixed-placement-mirror-20261005/proof.json`.
Campaign follow-up: maximum mixed selections, coincident results, both anchor types,
repeated reflection, boundary coordinates, source withdrawal and shared MAP ownership.
Model geometry/facing/rotations and collision are retained, not reflected; script-driven
placement and collision consistency remain separate manual gates. No game,
installation or full-disc export ran.

## Native-precision mixed rotation checkpoint — 2026-10-05

25 focused Python layout/group/HTTP cases, mixed-placement Node checks and module
syntax pass. Cover exact quarter turns, integer/off-grid anchors, final actor half
rounding, fixed anchor, native bounds, scenery overflow, no-op/history, stale/old
algorithm tokens and forged/safe arithmetic. Actual private Town01 browser checks
-90/+90/180 about an off-grid decoration, operation withdrawal, Current/Proposed GPU
matrices with height/rotation held, Return and 540px one Apply. Undo/Redo, Save/Open and
normal Build pass, with complete MAP directory/ZIP and independent native MAN placement
and opaque-byte readback. Screenshot inspected, no page errors. Proof:
`local-output/sdk-20260909/mixed-placement-native-rotation-20261005/proof.json`.
Campaign follow-up: maximum selections, extreme source/offset bounds, rounding
coincidences, repeated turns and actor anchors with native integer scenery distances.
Rotation changes positions only; actor facing, scenery rotation, collision consistency
and script-driven runtime placement remain separate manual gates. No game,
installation or full-disc export ran.

## Saved scene visibility/grid checkpoint — 2026-10-05

Nine focused Python view cases, scene-view/camera Node suites and both editor syntax
checks pass. Cover typed visibility/grid, canonical IDs, imported actor membership,
source-qualified static cells, MAP hash mismatch, atomic rejection, history/persistence
and legacy views. Private Town01 browser saves a manually hidden actor and isolated
static decoration; actual renderer display checks camera/grid/visibility recall and
Restore preserving manual hiding. Metadata Undo/Redo, Save/Open and 540px recall from
Retail to Authored after preview reload pass, with no page errors and unchanged imported,
authored-game, normal-Build and scene-preview keys. Screenshot inspected. Proof:
`local-output/sdk-20260909/saved-scene-visibility-20261005/proof.json`.
Campaign follow-up: maximum hidden selections, ground-only binding, cross-scene recall,
closed/stale context during preview loading, unavailable source meshes, shared model
hiding and source replacement. New NPC draft visibility remains unsupported. This is
editor metadata; runtime appearance/collision parity remains a separate manual gate.
No package, game, installation or full-disc export ran.

## Complete Build-review download checkpoint — 2026-10-05

Ordinary/NPC Build-review Node suites and module syntax pass. Cover all 301 changes
beyond the display cap, all native/other records, blocked and null assessments, v2
candidate coverage, stale/source/no-output claims and a 32 MiB UTF-8 limit. Actual
private retail browser downloads match the entire accepted response at desktop/540px,
including 130 coordinate records, with pending disable and mounted UI stale rejection.
Narrow action bounds, screenshot, close disposal, no page errors and unchanged project,
history and all fixture files pass. Proof:
`local-output/sdk-20260909/build-review-download-20261005/proof.json`.
Campaign follow-up: near-limit reports, actual server serialization blockers, project
replacement during review and repeated downloads/close while another operation is busy.
The export is metadata only; packaging and gameplay are separate gates. No game,
installation, package or full-disc export ran.

## Build-review native coordinate checkpoint — 2026-10-05

Nine focused Python Build-review/model-growth/normal-package cases, ordinary and
NPC Build-review Node suites, and module syntax pass. Cover source/no-output guards,
relocation ledger retention, independent signed native-word readback, deterministic
normal package output, immutable 128-row pages and malformed ledger rejection.
Actual private Town01 browser reads 130 native changes across both pages, checks
paging bounds and close disposal, and preserves project/history/all fixture files.
The 540px screenshot is inspected; no page errors or authoring/Save/Build/Run requests.
Evidence: `local-output/sdk-20260909/build-review-model-coordinates-20261005/proof.json`.
Campaign follow-up: maximum ledger size, normal-coordinate records, mixed primitive
and removal records, authored-input withdrawal while paging, and topology layouts.
Topology bindings without ledgers remain hashes/relocation evidence only. Synthetic
normal packages were tested; this retail browser check writes no package. Gameplay
acceptance remains manual; no game, installation or full-disc export ran.

## Model vertex distribution checkpoint — 2026-10-05

Six focused Python distribution/alignment cases cover signed extrema, nearest spacing,
coordinate/index ties, endpoint/other-word preservation, stale/invalid HTTP requests,
preview without mutation, no-op/history and allocated vector ownership. Expanded Node
checks cover immutable local geometry and forged operation/value/source/full-preview
replies; both changed editor-module syntax checks pass. Actual Town01 browser exercises
locks, no-op/Discard, Current/Draft, single/all-instance scene comparison, Return/Restore,
540px Apply and Undo/Redo with no page errors. Save/Open and normal Build pass, with
complete decoded carrier directory/ZIP readback and a single changed model byte.
Evidence: `local-output/sdk-20260909/vertex-distribution-20261005/proof.json`.
Campaign follow-up: maximum selections, multiple objects and authored topology layouts,
all three source axes, coincident results, source withdrawal and history across reopening.
Normals/collision are retained; gameplay appearance remains a separate manual gate.
No game, installation or full-disc export ran.

## Native-precision mixed placement scale checkpoint — 2026-10-05

18 focused Python layout/group cases, expanded Node DTO checks and module syntax pass.
The earlier four HTTP checks passed at the grid-only checkpoint; this checkpoint's
actual retail browser exercises the layout-review/command routes with an off-grid
anchor. Coverage includes signed half-away rounding at native actor/decor precision,
100-percent identity, 1–1000 integer limits, actor native bounds, scenery signed-offset
overflow, exact operation qualification, atomic rejection/history and persistence.
Actual Town01 browser checks 50/100/175 percent, fixed off-grid anchor, Current/Proposed
GPU matrices, withdrawal/Return, one Apply and all action bounds at 540px. Undo/Redo,
Save/Open and normal Build pass with independent MAN placement/opaque-byte checks,
complete MAP readback and ZIP integrity. Proof:
`local-output/sdk-20260909/mixed-placement-native-scale-20261005/proof.json`.
Campaign follow-up: 128 placements, percentage extremes, coincident rounding results,
source replacement during review, mixed descriptor ownership and repeated history.
Runtime movement, collision consistency and gameplay appearance remain manual gates.
No game, installation or full-disc export ran.

## Asset-reference download checkpoint — 2026-10-05

Focused Node checks cover full Active/Project JSON round trips, exact source/root/scope
qualification, input immutability, safe bounded filenames and the 32 MiB UTF-8 budget.
Actual private retail browser checks exercise both downloads while a zero-match filter
is active, pending-discovery disable, decoder readback, dialog disposal and 540px button
reachability. Document/history/files and project/scene/selection stay unchanged, with no
authoring, Save, Build or Run. Proof:
`local-output/sdk-20260909/asset-reference-download-20261005/proof.json`.
Campaign follow-up: withdraw source context while open, busy transitions, failed/aborted
project discovery, close during discovery, all resource kinds and maximum-sized reports.
Saved references do not establish runtime use or gameplay acceptance.

## Retained project provenance search checkpoint — 2026-10-05

Focused Node checks cover variant names/aliases, import/catalog hashes, claim/evidence
metadata, positive/excluded fields and immutable chosen-source qualification. Eight
existing project-source Python cases and both modified editor syntax checks pass.
Actual three-scene retail browser proof reproduces the prior module's missing hash,
finds a shared asset by nonchosen Map01 provenance, keeps chosen Dolk2 in Details and
checks exclusions/540px UI with unchanged document/history/files and no authoring,
Save, Build or Run. Private proof:
`local-output/sdk-20260909/project-provenance-search-20261005/proof.json`.
Campaign follow-up: all resource kinds, absent catalogs, 64 memberships, alternate source
scene filters, long/quoted aliases and source-refresh withdrawal. Search metadata is not
runtime use or a joined cross-membership binding; gameplay acceptance stays separate.


## Inspector property-category checkpoint — 2026-10-05

Focused Node checks cover category/query/actual authored-identity composition, empty
categories and immutable inputs; component state/reference suites and syntax also pass.
Actual retail browser evidence covers exact visible IDs, zero search results, category
retention across two actors, Reset, asset navigation, 540px layout, collapse/keyboard
restoration and unchanged document/history/files with zero authoring/Save/Build/Run.
Private proof: `local-output/sdk-20260909/inspector-property-category-20261005/proof.json`.
Campaign follow-up: an absent remembered category, translated/long labels, unregistered
components, stale detached filter controls and alternate project/mode refresh. Category
labels do not establish actual authored overrides or live observation; gameplay remains
deferred separately.


## Inspector property-state checkpoint — 2026-10-05

Focused checks cover catalog completeness/detachment/no capabilities, layer ownership,
precise authored workflow, unknown/malformed/escaped state labels, unknown/false values,
unsupported Y Build status and unchanged command/action/reference eligibility. Actual
retail browser proof covers actor/asset labels against the SDK, reference navigation,
540px legibility, collapse/keyboard restore and unchanged document/history/files with
zero authoring/Save/Build/Run requests. Private evidence:
`local-output/sdk-20260909/inspector-property-states-20261005/proof.json`.
Campaign follow-up: all registered component/asset inspectors, empty inherited states,
localized/long labels, mode/source refresh and screen-reader explanation. Real live
capture freshness/identity remains in the deferred runtime acceptance work, not proven
by a property-state presentation label.


## Mixed actor/scenery position rotation checkpoint — 2026-10-05

Focused development checks completed: -1/+1/2 exact quarter turns, actor and decoration
anchors, fixed pivot, invalid/bool/float/extra fields, off-grid anchor, native actor bound
rejection, stale Apply, preserved Y/rotation/shared/unselected data, no-op redo, one history
step and Save/Open. Existing offset/layout/reset and Node proposal-qualification checks
pass. Private retail browser/native package proof:
`local-output/sdk-20260909/mixed-placement-rotation-20261005/proof.json`.
All three turns, input withdrawal, Current/Proposed matrices, Return, one Apply, full MAP
readback and independent MAN coordinates/opaque preservation passed; no game ran.

Campaign follow-up: mixed selections up to 128, signed MAP/capacity boundaries, source and
selection changes during pending rotation, narrow viewport accessibility and exact native
readback for all turns. Deferred gameplay must check visibility, facing retained as
reviewed, collision and script-owned placement/lifecycle in the produced runtime.


## Mixed placement Retail reset checks

- Restore exact Retail X/Z for every selected actor/static decoration; clear selected
  actor X/Z overrides, prune empty containers and preserve height/facing/other components.
- Qualify Current authored-axis witnesses; distinguish coordinate changes from redundant
  override clearing. A second reset is a no-op and preserves history/redo/dirty state.
- Preserve shared scenery edits, selected Y/rotation and unselected instances; use
  per-instance compensation for source positions when shared transforms remain authored.
- Recover invalid off-grid integer actor coordinates through a valid source candidate;
  reject extra reset fields, stale sources and forged authored-axis reports.
- Verify readonly review/scene Return, one Apply/history, Undo/Redo, Save/Open, exact MAN
  source positions and full MAP Build directory/ZIP readback with unselected edits intact.
- Keep game visibility, collision and gameplay acceptance separate and deferred.

## Mixed scene placement layout checks

- Align X/Z to a selected actor/decoration anchor; require the 64-unit actor grid.
- Distribute grid-aligned mixed coordinates with fixed endpoints, nearest spacing,
  upward half ties and stable-ID ordering for equal positions; reject insufficient span.
- Validate all actor bounds, static descriptor ranges/capacity and complete merged MAP
  bindings before an atomic Apply; preserve unselected axes/components/shared edits.
- Qualify exact operation/selection/source and arithmetic; mode/anchor changes withdraw
  review. Layout scene inspection holds height/rotation and has no shared-offset handles.
- Compare Current/Proposed GPU matrices and Return; verify readonly files before Apply,
  one Undo/Redo step, no-op, Save/Open and full MAP plus independent MAN Build readback.
- Keep runtime height, collision, script behavior and gameplay acceptance deferred.

## Retained animation assignment-user navigation checks

- List all authored initial users with stable actor identities; keep capture provenance
  and runtime playback distinct. Unassigned and retired clips show an empty state.
- Match registered users to exact Current retained record/hash/model components and
  effective initial-animation identities; reject missing/duplicate/extra/forged users.
- Guard source/project/scene changes, busy actions and pending previews. Close aborts
  a pending preview without selecting a user or publishing an authored change.
- Navigate to each listed actor through normal selection, frame and synchronize the
  Hierarchy/Inspector; preserve document, history, files, mode and scene.
- Keep every action reachable at desktop and 540px widths; long clip/source IDs wrap.
- No Build/Save/game request is needed for this readonly Inspector workflow.

## Selected vertex group rotation checks

- Compare native/browser X/Y/Z turns -90/+90/180 about source origin and group bounds
  center, including half-unit pivot rounding and positive-Y-down conventions.
- Reject invalid axis/turn/pivot, booleans, duplicate/out-of-range rows, stale source
  hashes and signed16 overflow atomically. A centered single-row turn is a no-op.
- Preserve other vertices, stored normals, opaque padding, packets and allocated ownership.
- Check staging, Discard, locks, layers, qualified scene Current/Proposed, Return/Restore
  and all instances without project/file mutation before explicit Apply.
- Verify one history step, refreshed Current, Undo/Redo, Save/Open and normal Build;
  independently decode directory and ZIP payloads to the complete expected section.
- Defer game appearance/lighting acceptance; native byte preservation is not gameplay proof.

## Selected vertex group scaling checks

- Compare browser and native candidate at origin/bounds-center pivots, including
  negative and half-unit rounding,100% no-op and signed16 overflow rejection.
- Reject duplicate/out-of-range indices, booleans, invalid percent/pivot and stale hash.
- Preserve unselected words, normals, packet topology and allocated row ownership.
- Stage/Discard, layer comparison, selection/history locks, scene Return/Restore and
  all-instance inspection must preserve a readonly exact draft before explicit Apply.
- Verify one project history entry, refreshed Current, Undo/Redo, Save/Open and normal
  Build; independently decode directory/ZIP payloads to the complete expected section.
- Keep manual game appearance/lighting acceptance separate from source byte readback.

## Retained asset-to-selected-actor assignment checks

- Select an imported actor distinct from the capture owner and open an active clip.
- Verify exact asset scope, explicit target ID and source row qualification; block
  retired clips, missing/non-imported target, Live mode and missing capability.
- Review an incompatible target: report the captured-model/retargeting blocker without
  a command. Review a compatible target and verify source/native-selector witnesses.
- Preview the proposed target initial pose and return to reviewed assignment; Apply
  exactly once. Preserve target selection, imports, capture owner and retained ledger.
- Verify fresh assigned-actor metadata, Undo/Redo, Save/Open and normal Build readback.
- Exercise target/source changes and prevent asset assignment views from issuing
  lifecycle or Clear commands. Game suitability/playback acceptance remains manual.

## Direct retained asset lifecycle checks

- Open exact assigned, unassigned and retired assets with unrelated actor selected.
- Verify single-record identity/hash/owner/model/count/status qualification; mismatched
  library data must never publish actionable controls.
- Verify asset lifecycle view hides and guards actor-assignment actions.
- Preview and Review stay readonly; assigned retirement reports its reference blocker
  without clearing an actor. Retire unassigned and restore retired through exact Apply.
- Verify automatic catalog status, stable UUID/capture hash, imports/selection unchanged,
  two atomic commands, Undo/Redo, Save/Open and normal Build/native readback.
- Exercise stale source, late result, close, Live and capability handoff guards.
- Retain manual game appearance/playback acceptance separately.

## Direct retained asset GLB workflow checks

- Open assigned and retired animation assets without selecting their capture actor.
- Prepare explicit-rate export and verify both downloads against the bound response.
- Select changed rigid-channel GLB and original binding; Review and pose preview
  remain readonly. Closing preview returns to the reviewed replacement editor.
- Apply exactly once; verify stable UUID, new hash, atomic assignment witnesses,
  preserved retirement, fresh resource catalog and unchanged retail imports.
- Verify Undo/Redo, Save/Open and normal private Build readback.
- Reject busy/stale source handoffs, Live mode, missing capability and stale bindings.
- Defer game appearance/playback acceptance to manual gameplay verification.

## Direct retained asset editing - 2026-10-05

Open an assigned and retired clip from the Asset Database with a different actor
selected. Verify source options finish loading before interacting, native axis
Review, proposed-pose preview/return, exact Apply, unchanged actor selection and
source-qualified automatic resource refresh. Require stable IDs, changed record
hashes, updated assignment hashes, unchanged retirement/imported provenance and
one atomic command per Apply. Cover Undo/Redo, Save/Open and normal package output.
Check Edit/source-scene/capability guards, current project/source ownership and
pending/disposed contexts. Actor-library selection lifetime must remain unchanged.
Runtime appearance and timing remain separate deferred acceptance.


## Retained animation Asset Database workflow - 2026-10-05

Discover assigned, unassigned and retired captures in active/Project catalogs;
require stable authored identity, source scene, exact capture witnesses/counts and
honest active/runtime distinctions. Browse Animations and Authored assets; open
all three kinds, inspect provenance, captured model/actor navigation, and preview
saved frames in the normal model viewer. Retired inspection must never activate a
record or assign a native slot. Check captured-model edges and navigable registered
clip rows separately from active assignment native/bank evidence. Discovery and
preview must preserve document/history/files/mode/scene. Cover stale source, wrong
identity/model, extra/malformed HTTP and metadata fields, closed/pending dialogs,
changed project context and frame/channel bounds. Gameplay playback remains a
separate deferred acceptance requirement.


## Retained initial animation references - 2026-10-05

Require original decoded initial references to remain, with retained assignments
replacing only the effective inherited relationship. Check actor -> retained clip
-> captured model and inverse queries in active/Project scopes; unavailable scene
catalogs must not assert retained proof. Bind exact ledger/record/native bank and
assignment hashes, owner/model identities and current resolved native slot/selector.
Cover malformed hashes, cross-scene/canonical owners, wrong layers, extra fields,
selector/frame/channel bounds, shared model IDs and detached output. Standalone
retained navigation remains unavailable; the actor Inspector manages/previews it.
Clear must restore inheritance; Undo and Save/Open must restore retained evidence.
Queries in Edit and observation contexts must preserve document, history, files,
active scene and mode. Browser filters/provenance must not issue authoring, Build,
Save or game requests. This feature does not accept gameplay playback.


## Project script bookmark navigation - 2026-10-05

Cover all-scene and scene-filtered catalogs, token search including padded/unpadded
hex offsets and source hashes, empty catalogs, duplicate/invalid IDs, detached rows
and size/source bounds. Exercise same-scene and cross-scene actor/P2 open routes;
require exact original record qualification before selection focus. Changed source
must expose an error with no focused row or stale report/controls. Test changed
catalog/project keys, pending/busy dispatch and closed/disposed dialogs. Compare the
complete document, history, Authored files and Build key after a roundtrip. This
navigation changes active scene/selection context; it must issue no authoring,
history, Build or Save commands. Native map01/town01 actor/P2 and wrong-hash cases,
focused JavaScript guards and20 neighboring Python regressions passed. Screenshots
inspected; private proof: `local-output/sdk-20260909/project-script-bookmarks-20261005/`.
No game launch or new gameplay acceptance is needed for this navigation feature.


## Saved script bookmark regression coverage - 2026-10-05

Exercise original instruction and dialogue boundaries, actor and partition-two
owners, exact record/import hashes, stale review keys, bool/noninteger/out-of-range
PCs, unknown and ambiguous offsets, duplicate names, quota and Edit mode. Cover
create/rename/retarget/delete, no-op history, Undo/Redo, Save/Open without disc access,
project copy and reimport guards including deleted-record history. In the browser,
verify Recall changes only focus; pending script drafts, busy/stale/closed contexts
must prevent mutations. Compare native Build payloads with/without bookmark metadata.
Existing evidence:20 focused bookmark/view/copy cases, JavaScript source qualification,
Town01 browser CRUD/history/recall, partition-two persistence and paired normal Build
payload equality. Private proof: `local-output/sdk-20260909/script-bookmarks-final-20261005/`.
This feature needs no game launch. Broader runtime/gameplay acceptance stays deferred.


**Retail NPC actor-pool lower bound (2026-10-03):** Normal Review Build/Build now qualify the complete SCUS executable and seven retail function spans, derive the143-slot/216-byte actor pool, and reject unavoidable initial-placement overflow before MAN encoding. Source setup evidence establishes the anchor plus partition-1 loop; successful audit metadata keeps other scenery/channel/script demand unknown. Candidate features stay disabled and runtime allocation/gameplay unverified. See [pool check and evidence](legaia-npc-actor-pool.md).

Validation: six focused private-enabled Python checks and existing Node review guards pass. A bounded instruction harness executes the actual pool initializer/pop/failure path:143 distinct slots, then zero without memory changes. Six browser checks prove a normal one-draft package plus a real91-draft Town01 blocker (minimum144 nodes), disabled reviewed Build, unchanged authoring and540px layout. Independent full carrier readback preserves the earlier candidate MAN and fixed-span ownership. Package SHA256 `e8907db2b03619303d72cf3e09fbe2ac82bff7815534733d15c9337a00443c06`. Private proof: `local-output/sdk-20260909/npc-runtime-source-20261003/`. Helpers are closed; no game, install or disc export ran. Full runtime demand/acceptance remain deferred.

**Packet-group texture-binding copy (2026-10-02):** The source-binding picker now fills all textured primitives in a qualified target group in one draft action, with explicit target count. Other group/object drafts, group ABE, untextured rows, target UVs/geometry and source-owned bits remain separate. The complete resulting batch validates before draft replacement; over-budget groups reject atomically. Review, Proposed/Return, one Apply, history, persistence and Build reuse the existing material workflow. See [group copy](legaia-material-binding-picker.md#packet-group-copy-evidence-2026-10-02).

Validation: focused donor/material Node guards and seven actual browser workflows pass. Fresh effective-model hashes verify Undo/Redo. Independent complete TMD construction and packaged carrier readback match:14 target primitives,13 changed rows,26 CLUT/TPage word changes and39 additional bytes, preserving earlier edits and decoded neighbors. Package SHA256 `f1e9c622f00bf4b07fbee0ef1926ecd83872e8430125c94ebda325effcfd39c0`. Private proof: `local-output/sdk-20260909/material-group-binding-20261002/parent/`. Helpers are closed; no game, install or disc export ran. Native appearance/residency acceptance remains deferred.

**Imported model texture-binding picker (2026-10-02):** The material editor now browses active-scene AssetDB models and qualifies their Current source primitive bindings. Explicit Copy fills page/depth/indexed CLUT draft controls while retaining target UVs, geometry and blend flags. Review/Apply, Proposed/Return, history, persistence and normal Build reuse the existing source material command. See [binding picker](legaia-material-binding-picker.md).

Validation: three catalog Python cases, donor Node guards and the existing material lifecycle suite pass. Seven actual browser checks pass through one Apply and Build; a separate visual follow-up verifies UTF-8 labels and540px layout. Independent complete TMD construction/readback proves Current-to-Proposed bytes1102/1103/1106 only, retaining prior ABE byte1095; the entire carrier's neighboring decoded bytes stay unchanged. Package SHA256 `a952ee4f6443068d63f8ddc5b6f636aa31168d3625851d01fcc6a14d0e8a89a3`. Private proof: `local-output/sdk-20260909/material-binding-picker-20261002/parent/`. Helpers are closed. No game, install or disc export ran; UV suitability, live residency, palette animation and native blend appearance remain deferred.

**Assigned actor animation GLB interchange (2026-10-02):** Qualified appearance/initial-clip assignments now export and preview the assigned existing rigid pose. V2 sidecars bind the selected actor, imported clip contribution owner and inherited model witness; the export/review names ownership before Apply. Changes use the owner's existing AnimationChannels command, preserving the selected actor's original clip edits and assignments. Fresh witness/source checks and existing shared-axis conflict guards remain in force; unassigned v1 sidecars remain compatible. See [assigned GLB workflow](legaia-assigned-animation-glb.md).

Validation: four distinct private-retail Python workflow cases and the v1/v2 Node guard suite pass with no skips. Eight actual browser workflows pass through owner-labelled review, retained pose Return,540px controls, explicit Apply, Undo/Redo, Save/reload and normal Build. Independent complete ANM/MAN readback matches: town0b actor0019 retains clip0013 edits; witness0049 owns the clip0012 GLB change. Only ANM bytes8880/10336 and MAN byte9471 differ from retail. Package SHA256 `2d9eaec92f5076624af50f568c6494cd2f01b4b3b27b7f39becb60f2b3ad0aa7`. Private proof: `local-output/sdk-20260909/assigned-animation-glb-20261002/parent/`. No game, install or disc export ran, and helpers are closed. Native clip selection/timing and shared-user gameplay remain deferred.

**World source yaw rotation ring (2026-10-02):** World placements now offers an exclusive source-yaw ring with encoded-unit snapping, perspective-correct frozen-plane pointer conversion, continuous angle unwrapping and 0..4095 wrapping. Shared-record confirmation remains explicit. Temporary previews preserve positions and update every affected instance; Review and Apply use the existing source-qualified command, Undo, persistence, Build and export path. Current comparison gates hidden drafts and cancellation restores prior values/review. See [source yaw ring](legaia-worldmap-placement-yaw.md).

Validation: three focused Node suites and two private-retail Python source/package regressions pass with no skips. Seventeen browser checks pass, including both turn directions, wrapping, independent matrices and unchanged positions for all57 shared instances, cancellation, tool switching,540px controls, one Apply, Undo/Redo, Save/reload, normal Build and stale-source withdrawal. Independent full MAP readback matches X1280/Y256/Z256/yaw448; prior offsets persist and only the two yaw bytes additionally change. Package SHA256 `4a953cf8acfb12105dd121b7c3f6416f9469bfa00907ef4c2999d4e9bc9de6bf`. Private proof: `local-output/sdk-20260909/worldmap-placement-yaw-20261002/parent/`. No game, install or disc export ran; helpers are closed. Native runtime behavior remains deferred.

**World source viewport translation handles (2026-10-02):** World placements now offers source X/Y/Z pointer handles, 1/16/64/128-unit snapping and Frame anchor. Explicit shared scope is required. All affected instances and numeric offsets preview together; release retains a draft, Review qualifies it, and Apply alone records one command/Undo step. Cancellation restores prior draft/review state, and source/camera/layout changes invalidate frozen gestures. A dialog-close race was fixed so cancellation cannot clear another command's busy state. See [translation handles](legaia-worldmap-placement-gizmo.md).

Validation: two focused Node suites and fourteen Python regression cases pass with private input and no skips. Fifteen browser checks pass, including nonzero source/display X/Y/Z movement for all57 shared instances, cancellation, 540px layout, source invalidation, one Apply, Undo/Redo, Save/reload and normal Build. Independent complete MAP readback agrees exactly: record0477 is X1280/Y256/Z256/yaw1536, and only four retail source bytes differ. Package SHA256 `d15d8464e9486a9463dac0b5653e1005aadd9fa942c13e11ebf95fee8d28b6b7`. Private proof: `local-output/sdk-20260909/worldmap-placement-gizmo-20261002/parent/`. No game, install or disc export ran; owned helpers are closed. Native behavior and gameplay verification remain deferred.

**Current/Proposed world placement GLB export (2026-10-02):** World placements now downloads complete qualified kingdom scenes with applied record transforms or an exact reviewed proposal. Exports retain retail geometry, shared meshes, textures and ground, add source/current/exported MAP identities and per-instance retail/exported transform provenance, and preserve unknown runtime visibility/resting state. Proposal export does not Apply, Save or Build. The browser verifies representation, review identity, MAP hashes and binary digest, and rejects late or stale downloads. Existing World ground exports stay retail-source. See [authored world export](legaia-worldmap-placement-export.md).

Validation: six focused Python cases pass with private input and no skips, including unchanged legacy source exports. Independent all-three-kingdom MAP construction verifies every exported translation, yaw and record hash; geometry/image binaries remain identical to retail exports. Node guards validate actual private artifacts. Seven browser scenarios pass with no commands, game requests or page errors; Current and Proposed downloads match independent artifacts byte-for-byte, each with302 entities and57 changed source seeds. Saved project/import/Build files remain exact. The Current MAP hash matches the previously verified Build payload. Private proof: `local-output/sdk-20260909/worldmap-placement-export-20261002/`. No game, install or disc export ran.

**World source placement authoring (2026-10-02):** The World placements viewport now edits qualified shared object-record offsets and yaw for all three walk kingdoms. Source record selection and mesh picking, effective coordinates, shared-record scope, Current/Proposed comparison, frame/orbit, reviewed atomic Apply, Undo/Redo, Save/Open, Authored assets and normal Build are connected. Exact field masks preserve cells, anchors, model references, flags, other axes and opaque bytes. Disjoint MAP overlays compose; conflicting writes reject. Source spawn seeds remain separate from script-evaluated resting positions and visibility. See [world placement workflow](legaia-worldmap-placement-authoring.md).

Validation:17 focused Python cases pass with private source input and no skips, including all-three-kingdom source/package readback and ordinary Build regressions. Node source/review guards and independent transform arithmetic pass. Eight actual browser scenarios verify pending selection and Save/history guards, explicit shared scope, Proposed GPU pixels/matrices,540px controls, history/persistence, normal Build and actual GPU mesh selection. Independent browser-package readback matches all73,728 MAP bytes and changes only bytes15265/15275 against retail; shared record0477 affects57 seeds. No page errors, game requests, installs or disc exports ran. Private proof: `local-output/sdk-20260909/worldmap-placement-authoring-20261002/`. Gameplay acceptance remains deferred.

**Source NPC candidates in normal Build (2026-10-02):** Saved donor drafts now enter inclusive v2 Build review and normal package generation for qualified compressed MAN scenes whose complete candidate fits the original consumed stream. Two source-hashed overlays update that stream and its descriptor size word; carrier size, pointers, neighboring payloads, TOC and disc layout stay unchanged. Supported existing actor/P2 edits compose after append, while other asset overlays retain the normal pipeline. Streaming or oversized additions remain rejected. Packages identify source candidates and keep their feature disabled by default. Native allocation, spawning, scheduling and opaque script behavior remain unverified. See [NPC Build boundaries](legaia-npc-build-candidates.md).

Validation: eleven focused Python checks and sixteen ordinary Build regressions pass with private retail input and no skips; legacy and v2 Node review guards pass. Independent Town01 package readback verifies donor scripts, reached spawn-reference rebasing, existing placement/facing composition and counts `[36,53,39]` to `[36,54,39]`. Optimal LZS uses24,856 bytes within the original24,894-byte stream; decoded MAN grows45,338 to45,917 bytes. Four actual browser scenarios verify inclusive read-only review,540px controls, reviewed Build and unchanged authored/import files with no game requests or page errors. No game, install or disc export ran. Private proof: `local-output/sdk-20260909/npc-normal-build-20261002/`. This supersedes earlier blanket normal-Build draft rejection statements; broader gameplay acceptance remains deferred.

This is the post-feature acceptance plan, not a claim that every test exists.
The current buildout uses focused synthetic checks, retail import probes and
local browser validation. Larger automation follows connected product features.
See `FEATURE_MATRIX.md` and `legaia-release-parity.md` for actual current results.

## Latest integrated offline result — 2026-10-02

**World-map source GLB export (2026-10-02):** World ground inspection now connects to private GLB downloads for all resolved source placements plus terrain, terrain alone when the placement layer is hidden, or one selected source entity. Shared meshes, source transforms, embedded matched textures and source provenance use the existing scene exporter. Fresh source checks bind exports to the imported disc and current project; late responses after closing or changing sources cannot trigger downloads. Exported placement seeds retain unknown runtime resting positions and visibility. Exports create private artifacts without authored commands or Build/disc output. See [world-source export](legaia-worldmap-export.md).

Validation: 16 focused Python cases passed with private retail input and no skips; three Node guard suites and frontend syntax checks passed. Independent all-three-kingdom readback verifies source world corners, reflected winding, shared meshes, UVs, stored colors, embedded PNG pixels and provenance. Nine actual browser scenarios pass, including five downloaded artifacts, ground-only visibility scope, selected seed scope, 540px controls, cancelled late responses and stale-source withdrawal. Downloaded geometry binaries and normalized metadata match the independent exports. Blender 5.2.2 LTS imports the complete map01 scene with 302 entity roots, 303 mesh objects, 67 materials and 60 images; all local triangles match, and maximum world-coordinate float error is 0.0009765625 source unit. Saved project/import/Build files remain unchanged; no game, authoring command or disc export ran. Private proof: `local-output/sdk-20260909/worldmap-glb-20261002/`.

**Scenery group source-angle rotation (2026-10-02):** The existing anchor rotation workflow now accepts every integer source yaw delta from 0 through 4095, alongside its compatible quarter-turn controls. A frozen Q30 quarter-wave table and signed integer nearest-half-away rounding produce reviewed X/Z positions; cardinal turns remain exact. The editor independently checks the same arithmetic before accepting a report. Review, retained Proposed/Current inspection, atomic Apply, Undo/Redo, Save/Open and normal Build preserve source Y, other rotation axes, shared descriptors and unrelated components. Rounded positions can change distances slightly; this authoring convention does not establish retail GTE rounding or gameplay acceptance. See [group rotation workflow](legaia-scenery-group-rotation.md).

Validation: 19 focused Python cases passed with no skips; two Node guard suites and frontend syntax checks passed. All 4096 angles match between Python integers and JavaScript BigInt for six signed displacement pairs, with identical frozen tables. Twelve actual browser scenarios verify custom angle review, invalid-input rejection, retained Proposed/Current comparison, history, Save/reload, normal Build, cancellation and stale-state withdrawal; the 540px layout was visually inspected. Independent renderer matrices and reopened full 73,728-byte MAP package readback match the reviewed 45° proposal. Only bytes 171/256/260/267 change against the prior authored fixture; source Y, other axes, shared records, prior Collision and retail MAP remain intact. No game or disc export ran. Private proof: `local-output/sdk-20260909/scenery-group-angle-20261002/`.

**Source-bound GLB material editing (2026-10-02):** Fresh profile v6 adds
`_LEGAIA_SOURCE_MATERIAL` for full stored CLUT/TPage words and shared group ABE.
Exact integer primitive aliases and whole-group transparency aliases must agree.
Qualified masks preserve reserved CLUT bits, source ABR, other mode bits, row
commands and allocation. Untextured CLUT/TPage retain -1; group ABE remains
editable. Existing source positions, UV/RGB, normals and references compose;
legacy profiles retain their earlier field permissions. Review/Proposed
inspection/Apply/history/Save/Build use the normal model replacement workflow.
Shader assignments and texture images are separate; static associations may
remain partial. Retail blend/appearance acceptance remains deferred. See
[material GLB workflow](legaia-model-glb-materials.md).

Validation: 44 focused Python cases passed with the private retail disc (no
skips), two Node guard suites and frontend syntax checks. Actual Blender 5.2.2
no-op roundtrips are byte-exact; independent CLUT/group ABE, TPage and untextured
sentinel proofs change only bytes131/138, byte142 and byte299 respectively.
Twelve integrated browser checks cover fresh exports, no-op, reviewed source
fields, Proposed/Return, 540px layout, Apply/history/Save/stale withdrawal and
normal Build. Reopened package readback retains prior normal-reference/XYZ
bytes2940/3332 and adds only material bytes131/138, preserving neighboring data
and the 154,547-byte compressed capacity. No game was launched and no disc output written.
Private proof: `local-output/sdk-20260909/model-glb-materials-20261002/`.

**World-map source placement inspection (2026-10-02):** **World ground** now
opens a source scene with 301/272/236 sparse model placements in map01/map02/map03.
The hierarchy, mesh picking, Frame selected and Source model placements toggle
expose stable entity IDs, MAP cells, record hashes, dictionary slots and source
XYZ. Column-major source yaw/translation becomes a row-major renderer transform
with one display Y flip. The ground asset and source coordinates remain unchanged.
This is read-only; source changes withdraw geometry and pending-close cancels reads.
Runtime visibility, script-adjusted resting positions and animation remain
unverified. Model textures are partially resolved and missing associations stay
explicit. See [placement workflow](legaia-worldmap-placements.md).

Validation: eleven focused Python cases passed with the private retail disc
(no skips), plus ground and placement Node guards and frontend syntax checks.
Independent raw-source comparisons match every seed position, rotation, record
hash, model slot, loaded model topology and source-member hash in all kingdoms;
ground geometry remains unchanged. Nine integrated browser checks cover actual
rendering, hierarchy/coordinates, mesh picking, toggles, camera controls, 540px
layout, source withdrawal, pending-close and exact saved project/Build file hashes.
No game was launched or disc output written. Private proof:
`local-output/sdk-20260909/worldmap-placements-20261002/`.

**World-map walk-ground workspace (2026-10-02):** The editor's **World ground**
resource action now opens source-backed textured 3D ground for map01, map02 and
map03 through the shared scene renderer. The importer qualifies the overlapping
kingdom carriers, exact 0x12000 MAP footprint, slot-2 MAN floor LUT and slot-0
TIM atlas. Orbit/zoom, Frame ground, Top view, Wireframe and source details are
read-only; source changes withdraw retained geometry and closing pending reads
releases controls. Imported field selection, authored state, history and Build
files remain unchanged. Source Y-down coordinates flip only at the renderer.
Overview/MAPDSIP, script-managed resting transforms, sky/fog and runtime parity remain pending.
See [world-ground workflow](legaia-worldmap-geometry.md).

Validation: six focused Python cases passed with the private retail disc (no
skips), plus Node source/geometry/texture guards and frontend syntax checks.
Independent readback matches every ordered vertex, triangle, UV and visible-cell
selector in all three kingdoms. Visible cells are 16,251/16,381/16,374; source
texture coverage is 23/23, 17/18 and 15/16. Missing palettes stay explicit, without
fallback textures. Eight browser checks cover actual three-kingdom rendering,
camera controls, 540px layout, stale withdrawal, pending-close and unchanged
project files. No game was launched, no disc output written. Private proof:
`local-output/sdk-20260909/worldmap-geometry-20261002/`.

**Source-bound GLB normal-reference editing (2026-10-02):** Fresh profile v5
adds `_LEGAIA_SOURCE_NORMAL_INDEX` for selecting an existing normal within the
source object. Immutable corners retain packet ownership; flat references and
all raw XYZ aliases must agree. Unlit index -1 and XYZ sentinel remain explicit.
Changed references use `tmd-content-v3`; older content versions keep normal
references immutable. Review/Apply/history/Save/Open and normal Build compose
reference changes with earlier authored normal words. Material inspection,
source-bound JSON/TMD review and object transforms preserve the new references.
Counts, allocation, padding and unrelated source bytes remain fixed. Retail
lighting and gameplay parity remain deferred. See
[normal-reference workflow](legaia-model-glb-normal-references.md).

Validation: 42 focused Python tests passed with the private retail disc (no
skips), plus Node workflow and frontend syntax checks. Twelve integrated browser
checks cover actual Blender review/no-op, proposed inspection, Apply/history/
Save, 540px layout, stale rejection and Build. Independent flat/Gouraud rewiring
changes only byte2940/byte4284 respectively, retaining the earlier normal edit.
Integrated Build retains bytes2940 and3332, unchanged neighbors and the original
154,547-byte compressed capacity. Legacy content downgrades reject the changed
reference. No game was launched. Private proof:
`local-output/sdk-20260909/model-glb-normal-references-20261002/`.

**Source-bound GLB normal editing (2026-10-02):** Fresh model profile v4 adds
`_LEGAIA_SOURCE_NORMAL` raw signed-i16 XYZ for existing lit packet normal owners.
Shared flat/Gouraud aliases must agree after rounding. Retail axes remain
[x,y,z], without POSITION's Y flip or normalization; unlit corners retain the
out-of-domain [32768,32768,32768] sentinel. Display NORMAL is ignored. Normal
references, padding, allocation and unrelated bytes remain unchanged. Review,
Apply, undo/redo, Save/Open and normal Build use the existing model replacement
workflow. Legacy v1-v3 codec behavior remains; SDK editing requires a fresh v4
export. Retail normal-based lighting and gameplay acceptance remain pending.
See [normal workflow](legaia-model-glb-normals.md).

Validation: 27 focused Python tests passed with the private retail disc (no
skips), plus Node workflow and frontend syntax checks. Twelve browser checks
cover actual Blender no-op/edit review, proposed geometry, Apply/history/Save,
540px layout, stale rejection and normal Build. Independent Blender 5.2.2
readback changes only byte3332 for a shared flat normal and byte4640 for a
Gouraud normal. Integrated Build preserves all decoded neighbors and the
154,547-byte compressed capacity. No game was launched. Private proof:
`local-output/sdk-20260909/model-glb-normals-20261002/`.

**NPC facing composition and output review (2026-10-02):** Source script facing
edits now compose with appended NPC drafts in compressed and streaming MAN
carriers. Original record ownership is re-resolved after append; only the facing
nibble changes, upper flags remain intact, and donor clones retain retail facing.
The editor's **Review NPC output** prepares an in-memory archive and reports
source identities, relocated fields and allocation limits without writing a
package/disc, changing history or launching the game. Normal Build still rejects
NPC drafts; gameplay, scheduling and general allocation remain unverified.
See [draft facing workflow](legaia-draft-facing.md).

Validation: 16 focused Python tests passed with the private retail disc (no
skips), plus Node metadata guards and frontend syntax checks. Six integrated
browser checks cover actual two-scene review, exact metadata, 540px layout,
stale-input withdrawal, pending-close handling and unchanged saved files.
Independent Town0b/Dolk2 readback verifies four/one facing-byte changes, each
rebased by three bytes after append; donor copies and unrelated bytes are retained.
Private proof: `local-output/sdk-20260909/draft-facing-20261002/`.

**Source-bound GLB face rewiring (2026-10-02):** Model profile v3 adds existing
polygon vertex references to the external mesh workflow. Immutable source corner
IDs retain face ownership; qualified vertex IDs may select existing vertices in
the same object. Seam/quad reference and coordinate aliases must agree. Review
shows exact source/current/proposed references before ordinary Apply/history/
persistence/Build. Object, vector, polygon and packet capacities stay fixed;
new objects/polygons, normal tables and material allocation remain pending.
Legacy v1/v2 codec behavior is retained; SDK authoring requires a fresh v3 export.
See [face workflow](legaia-model-glb-faces.md).

Validation: 22 focused Python cases passed with the private retail disc (no
skips), plus the Node workflow and frontend syntax checks. Twelve browser checks
cover exact reference Review, regenerated proposed geometry, no-op and stale
rejection, 540px layout, Apply/history/Save and normal Build. Actual Blender 5.2.2
updates both aliases of one quad corner, vertex 17 to 0; independent readback
changes only byte434 (136 to 0). Build retains earlier RGB/material bytes300,
1095 and1102, all decoded neighbors and the 118,461-byte compressed capacity.
No game was launched; gameplay appearance and general allocation remain pending.
Private proof: `local-output/sdk-20260909/model-glb-faces-20261002/`.

**Raw RGB model GLB editing (2026-10-02):** The existing external model workflow
now imports qualified baked RGB through `_LEGAIA_SOURCE_RGB` in the raw 0..255
byte domain. Profile v2 binds each flat/shared or Gouraud/corner color to its
source packet; duplicate aliases must agree, and packets without stored RGB
retain explicit -1 sentinels. Review exposes exact fields and rounding error
before ordinary Apply/history/persistence/Build. Display `COLOR_0`, shader colors,
normals, references, material words and allocation remain outside this lane.
Fresh exports use v2; the codec retains legacy v1 positions/UV behavior. Existing
bindings require a fresh export for SDK Apply. See [RGB workflow](legaia-model-glb-rgb.md).

Validation: 18 focused Python cases passed with the private retail disc (no
skips), plus the Node workflow and frontend syntax checks. Twelve browser checks
cover no-op, exact RGB Review, proposed model, 540px layout, file invalidation,
Apply, Undo/Redo, Save, Build and stale-source rejection. Actual Blender 5.2.2
round trips flat and Gouraud edits exactly. The saved Dolk2 Build adds only byte
300 (24 to 25) to the two existing material bytes, preserving decoded neighbors
and the 118,461-byte compressed capacity. No game was launched; runtime lighting
and appearance remain deferred. Private proof: `local-output/sdk-20260909/model-glb-rgb-20261002/`.

**Coordinated scene animation:** Six focused Python cases and the Node lifecycle
suite pass. Actual Dolk2 integrated preparation loads 69 actors/15 shared tracks
and 46,015 frame vertices in Retail and Authored views. Independent Town01 source
proof covers 42 actors/22 tracks and 67,947 frame vertices. Sampled poses retain
source geometry, ordered object ranges and material mappings; authored frame zero
matches the composed shared bank and differs from Retail. Browser checks cover
multi-mesh sampling, unchanged canonical/placement/material/history, Play/Pause,
paused command rejection, exact Restore, narrow layout and representation guards.
No page/HTTP errors or game launches. Runtime timing/scheduling and live clip
identity remain unverified. Private evidence: scene-animation-20261002/parent
and research under local-output/sdk-20260909/.

**Source-qualified model materials:** 22 focused Python tests (nine new material
cases), three Node workflow suites and six real-browser checks pass. Checks cover
masked CLUT/TPage fields, shared group ABE, strict legacy reads, v2 material splits,
merges/reordering with retained rigid poses, source/draft/stale/no-op guards and
model/scene Return retention. Actual Dolk2 Apply, Undo/Redo, Save/Open and Build
preserve geometry and GLB bytes. Package readback changes only source bytes 1095
and 1102, retains the 118,461-byte compressed capacity and every decoded neighbor.
540px layout passes; page/HTTP errors and Run requests are zero. Runtime blend
state, texture residency and gameplay appearance remain unverified. Private
evidence: `local-output/sdk-20260909/model-material-20261002/parent/`.

**Source-bound texture PNG editing:** 12 focused Python cases pass with no skips:
4/8/16/24-bpp exact no-ops, duplicate indices, selected-row/pixel byte masks,
raw RGB nearest choices, deterministic palette reduction, binary alpha/STP,
PNG filters/indexed samples, bounded malformed/zlib/profile rejection, fresh
binding and read-only review/pixels, reviewed Apply, history, persistence and
HTTP envelopes. The Node suite covers exact Files/mode/context, export/download,
read-only pixels, immutable scene Return, stale/closed/late/busy guards and
Apply reply validation. Both frontend syntax checks and 11 browser checks pass,
including 540px layout and normal Save/Build, with zero page/HTTP errors or
game-launch requests. Independent Pillow verifies retail conversion and color
errors. Town01 package readback matches the exact reviewed TIM within its
33,312-byte allocation; other palettes, source metadata and neighbors remain
unchanged. Scene proposal affects 26 materials/10 instances and preserves all
geometry/placements. Private proof:
`local-output/sdk-20260909/texture-png-20261002/parent/final-evidence.json`.
Later gameplay acceptance must check texture appearance, palette consumers and
STP blending under matching runtime provenance. Large-image performance remains
unverified. See [workflow and limits](legaia-texture-png.md).

**Source-bound model GLB editing:** 14 focused Python cases pass with the private
disc and no skips: 24 packet families, exact alias/quad byte masks, indexed and
interleaved accessors, topology/bounds rejection, fresh binding, read-only review
and proposal, effective model composition, Apply/history/persistence and normal
Build readback. The Node suite covers immutable Files, stale/closed/late replies,
no-op and preview Return. Both frontend syntax checks and 12 browser checks pass,
including 540px layout and normal model rendering, with zero page/HTTP errors or
game launches. Actual Blender 5.2.2 receives a fresh SDK GLB and preserves source
bytes on re-export; its edit changes exactly one vertex X and one quad UV U.
Merge Vertices or lost attributes reject. RGB and normals are preserved.
The saved Dolk2 browser Build reconstructs the exact candidate within its source
capacity with unchanged decoded neighbors. Private proof:
`local-output/sdk-20260909/model-glb-20261002/parent/final-evidence.json`.
Later gameplay acceptance must check matching model/UV appearance and shared
instances. No immediate game verification is required. See [workflow](legaia-model-glb.md).

**Imported project Asset Database (2026-10-02):** The primary browser uses
source-qualified project inventories with retained shared memberships, scene
filters, field search, pagination and canonical cross-scene inspectors. The
Town01/Dolk2/map01 audit returns 3,637 identities and 3,703 memberships with
explicit partial coverage. It preserves populated source/material caches,
authored values, selection, Undo/Redo entries and saved files. Source freshness
ignores ordinary navigation and rejects authored drift. The focused backend,
HTTP dispatch checks total 18 passing Python tests. Two Node suites, both
changed-module syntax checks and 19 integrated browser checks passed. Private
evidence retains exact P2 owner/PC focus, canonical tool handoffs, authored
invalidation/Undo, stale action rejection and reviewed 540px layout. Page/HTTP
errors and game-launch requests were zero. This read-only inventory feature adds no
gameplay edit or new gameplay verification requirement. Complete format and
runtime coverage remain pending. See [workflow](legaia-project-assets.md).

**Source-qualified global landmark authoring (2026-10-02):** The world-map
workspace edits the 20 existing SCUS menu records with separate Retail,
Authored, Current and reviewed Proposed values. Existing name/discovery,
CDNAME destination and encoded X/Y fields have a duplicate-safe 2D diagram,
exact byte review, Apply/reset, Undo/Redo and Save/Open. Authored asset links and
normal Build reports reopen the source row. Normal Build emits a guarded
126-byte SCUS data overlay, with independent whole-executable reconstruction;
field placement composition retains both overlays and unchanged imports.
Experimental Export disc rejects this global component explicitly.

Name and discovery consumers are now qualified by retail static analysis.
Destination and X/Y meanings remain reference interpretations; drawing,
travel, discovery activation and gameplay are not verified. The table has 20
rows, terminator row 20 and two padding bytes before 16 immutable name slots.
See [landmark authoring workflow and evidence](legaia-worldmap-authoring.md).

Validation: 36 selected Python tests passed with the private retail disc and no
skips; two Node suites, both changed-module syntax checks and 16 browser
workflows passed. Browser page/HTTP errors and game-launch requests were zero.
The saved browser package independently reconstructs the executable with only
file byte 0x6429C changed 96-to97 (row 0 X), while fresh scene imports still match.
Review exposes field changes, byte offsets and the candidate hash; draft gates,
reset/history/persistence, 540px layout and Build-to-source navigation passed.
Private proof is in `local-output/sdk-20260909/worldmap-authoring-20261002/`.
The full SDK and gameplay acceptance remain incomplete.

**Source-qualified field branch authoring (2026-10-02):** The script workspace
now links a selectable source-flow diagram to disassembly and reviews existing
JMP, conditional, bounding-box, flag-word and ordinary system-flag destinations.
Retail, authored, current and proposed edges remain separate; encoded conditions
are not evaluated. Targets must be original instruction or atomic MES starts
through PC32767. Reviewed Apply/reset uses ordinary Undo/Redo and Save/Open;
normal Build, streaming export, appended-record composition and operand files/
bundles retain record layout and independently qualify changed flow. Other
authored operands survive branches that make source nodes unvisited.

Retail handler validation also corrects three existing decoder interpretations:
camera apply and FIELD43/44 continue, and flag-word targets use relative offsets.
Ordinary SYSFLAG forms cover50..7F; extended forms stop with an explicit reason.
The pinned Andrew reference remains unchanged. Town01 now has619 decoded dialogue
segments and1339 flag references; Dolk2 has629 segments and744 references.
See [field branch workflow and evidence](legaia-script-branches.md).

Validation:88 integrated Python regression cases passed with the private retail
disc and no skips, including compressed Town01 and raw Dolk2 normal packages.
Three HTTP cases reject18 malformed/foreign requests and stale Apply without
changing evidence or history. Four Node suites and15 browser workflows passed;
browser page/HTTP errors and game-launch requests were zero. The browser's
reviewed Town01 package independently reads back with only byte4791 changed
(PC31 target15-to11); its saved imports still match a fresh source import.
Dolk2 PC28 target63-to9 changes only bytes7481/7482. Real Town01 donor append
preserves that branch at rebased byte4794 in the prepared MAN; full rebuilt-disc
acceptance is deferred. Current/Proposed navigation, multiple pending choices,
reviewed Apply/reset, Undo/Redo, Save, no-op/stale gates, narrow layout and exact
Build-to-source navigation were checked. Private evidence remains in
`local-output/sdk-20260909/script-branches-20261002/`. Runtime branch activation,
story behavior and termination remain deferred; the full SDK remains incomplete.

**Model primitive content authoring (2026-10-02):** The integrated model
face/UV/baked-RGB workflow now spans source inspection, reviewed paired previews,
existing posed scene instances, atomic Apply, vector composition, Undo/Redo,
Save/Open, authored TMD export and normal Build audit navigation. Source packet
ownership, all24 flag layouts, bounded fields, stale/late requests, unchanged
opaque bytes and Vahn's actual idle-animation prefix are checked. Added objects,
packet/vector allocation, changed material bindings and runtime rendering
acceptance remain unfinished. See [model content contract](legaia-model-content.md).

Validation: 31 selected Python cases passed with the private retail disc enabled
and zero skips; 3 Node suites and 2 changed-module syntax checks passed. Sixteen
actual browser workflows passed with zero page/HTTP errors and zero game-launch
requests, including normal Build review/package/source navigation. Reviewed,
scene, Build and narrow-layout captures were inspected. Town01 model0000 changes
exactly source bytes48/52/62/64; independent package readback verifies the complete
304116-byte decoded container, 154518 encoded bytes within the 154547-byte source
capacity, and unchanged unused encoded tail. Imported metadata is unchanged and
Save/Open retains the exact versioned binding. Vahn idle retains its verified
12-to-10 object prefix and frame coordinates. Gameplay appearance/lighting/culling
remain deferred; no game was launched or package installed. Private evidence is
under `local-output/sdk-20260909/model-primitives-20261002/`.

**Visual transition graph workspace (2026-10-02):** Scene and Project
transitions now open a selectable node/arrow diagram, scene list, search,
imported-only filter, direct-reference focus, zoom/pan/Fit and paginated source
instructions. Parallel instructions remain independent records; arrow badges
group only equal source/destination pairs. Retail, Authored and Effective entry
bytes stay separate. Source-script navigation selects the exact owner and PC;
imported destinations use ordinary scene selection. Coverage, unavailable
catalogs and unresolved names remain explicit. Project-only freshness changes,
stale responses and pending-close/reopen cleanup and old-request isolation invalidate retained controls. The
canvas draws at most 80 scenes and 160 pairs; every matching instruction remains
accessible in 20-row pages. No gameplay route or story reachability is inferred.
See [transition graph workflow](legaia-project-transitions.md).

Validation: 26 selected retail-enabled Python cases passed with zero skips;
6 Node suites and 3 changed-module syntax checks passed. Thirteen actual browser
workflow checks passed with zero page/HTTP errors, zero authoring commands and
zero game-launch requests. The four-scene Town01/Dolk2/Town0b/map01 fixture has
17 nodes, 18 grouped pairs and 35 instructions from 319 scripts (195 partial,
zero unavailable). Graph, narrow-layout and entry-layer captures were inspected;
long arrows avoid intervening scene boxes and badges remain selectable above
crossing lines. Imported metadata and the saved project are unchanged. This
source-reference workspace is accepted offline; gameplay/runtime verification
remains deferred for the wider SDK. No game was launched or package installed.

**Reviewed primary trigger cells (2026-10-02):** Existing primary MAP kind-0
teleport and kind-1 binding rows now have an Edit trigger cell action. Retail,
Authored, Current and Proposed X/Z cells remain separate, with outline and scene
comparison, per-row retail reset, one-step Undo/Redo and Save/Open. Fresh source
and review keys qualify the complete retained binding; stable row identity stays
independent of coordinates. Only two lookup-coordinate bytes are writable.
Destinations, record/gate payloads, row order, footprints, elevation and all other
MAP bytes remain unchanged. A separate trigger key invalidates annotations
without reloading geometry. Normal Build composes triggers, regions, scenery and
collision walls in one exact MAP overlay, independently binding every trigger
byte to the requested cells. Build report links reopen the source resource.
Fallback rows remain read-only; unknown gates keep their unresolved behavior.
Moving a row can change first-match shadowing. Height, contact, activation and
playable behavior remain deferred. See [trigger cell workflow](legaia-trigger-cells.md).

Validation:50 selected retail-enabled Python cases verified without skips,
including the12 affected/neighbor cases rerun after repairs;6 Node suites and3
changed-module syntax checks passed. Thirteen actual browser workflow checks
passed with zero page/HTTP errors and zero game-launch requests. Visually
inspected review and viewport captures are readable. The retained Town01
kind-0/0000 fixture changes only MAP65554 from30 to31, preserving destination
bytes146/132. Fresh disc-span, ZIP and imported-metadata readbacks agree. The
package is built, not installed or played; full SDK/runtime scope remains incomplete.

**Source-facing instruction authoring and object-index correction (2026-10-02):**
The actor Inspector now opens source-qualified facing controls for simple
CAM_CFG and nonparked NPC_RUN instructions. Retail, Authored and Effective
sectors remain separate; drafts have a numeric compass preview, Apply/Clear,
Undo/Redo and Save/Open. Source-bound operand JSON and scene bundles include
ScriptFacing. Normal Build composes the exact low-nibble writes with other MAN
edits and checks the full byte audit and compressed capacity. Retail dispatch,
LUT reads and actor-facing stores were verified statically before implementation.
The shared Inspector also renders additional registered components through their
schema. Gate-0 object references now preserve unresolved flat MAN indices;
gate-1 remains explicitly P2-local. Initial/live actor heading, branch selection,
experimental NPC append export and gameplay acceptance remain unresolved.
See [source-facing workflow](legaia-script-facing.md).

Validation:56 focused retail-enabled Python tests passed without skips in70.133s;
7 Node checks and3 changed-module syntax checks passed. Nine actual browser
workflow checks passed with zero page/HTTP errors and zero game-launch requests;
a real P2 report independently validates/renders31 controls with explicit
extended-context uncertainty. Retained Town0b actor0019 packaging changes only
MAN byte9479 from0x81 to0x85, preserving the upper flag. Imports remain unchanged.
The package is not installed or played; full SDK/runtime scope is incomplete.

**Reviewed field region bounds (2026-10-02):** Primary MAP regions now have
an Edit region bounds action, four strict corner inputs, separate Retail /
Authored / Current / Proposed layers, and outline/viewport comparison. Apply
and per-row retail reset use one undo step; inherited/no-op values normalize
without dirtying the project. Source-qualified effective annotations leave the
imported spatial envelope intact, and a separate region key invalidates views
without reloading geometry. Save/Open and normal Build preserve the region
type, padding, source order and all bytes outside audited corners. Region edits
compose with scenery and collision walls in one MAP overlay. Browser review,
frame, comparison, Apply, history, persistence and scene cleanup passed with
zero page/HTTP errors and zero game-launch requests. The retained Town01
fixture changes only MAP byte66692 from58 to59; its package is built but not
installed or played. Height, activation and movement acceptance remain deferred.
See [region bounds workflow](legaia-region-bounds.md). The full SDK/runtime
objective remains incomplete.

Region milestone validation:54 retail-enabled Python tests passed with no skips in74.565s;42 Node checks and40 module syntax checks passed. Actual browser comparison passed10 workflow checks with zero page/HTTP errors and zero run requests. Independent package readback confirms one byte changes; imported scene hashes remain unchanged. No game launched or package installed.

**Field source cells and script links (2026-10-02):** Verified trigger and
region rows now appear in the scene hierarchy and shared Inspector, with
viewport outlines, framing and explicit source-cell picking. Trigger dispatch
uses `world >> 7`; region lookup uses `(world - 64) >> 7`, preserving the
64-unit difference. Display Y=0 remains an inspection plane with unknown
height. Coincident rows retain separate source identities. Gate-1 rows link to
unique bounded P2 scripts in Active/Project reference graphs with both record
hashes; object binds, unknown gates and missing/aliased targets stay unresolved.
Town01 supplies 99 trigger cells,14 region bounds and 51 eligible script links.
Read-only HTTP, source qualification, browser navigation/picking and stale-scene
cleanup passed. No game launched or package installed; contact/activation and
retail height acceptance remain deferred. See
[field source workspace](legaia-field-source-workspace.md). Full SDK/runtime
coverage is still incomplete.

Final validation:59 retail-enabled Python tests passed with no skips in84.629s;41 Node checks and39 module syntax checks passed. Actual browser frame/pick, overlapping rows, reference/script navigation, actor restoration and scene invalidation passed with zero page/HTTP errors. The saved baseline/import hashes remained unchanged; no package or game was launched.

**Central transition assets (2026-10-02):** Decoded scene-change instructions
now appear in the Asset Browser, shared Inspector and Active/Project dependency
graphs. Imported/authored/effective entry bytes and static destination arrival
coordinates remain distinct from unknown source triggers. A dedicated transition
key invalidates stale views without reloading geometry. Fresh serializer checks
qualify authored entries; partial catalog coverage with zero decoder stops no
longer blocks otherwise supported entries. Retail discovery found 35 transitions
across Town01, Dolk2, map01 and Town0b.55 retail-enabled Python tests passed
with no skips;39 Node checks and38 syntax checks passed. Browser editing,
history, persistence, source/destination navigation and reference scopes passed.
Reopened Build changes only Town01 MAN bytes28574 (96 to128) and28576 (4 to2).
No game launched; existing transition-arrival gameplay acceptance is deferred.
See [transition asset workflow](legaia-transition-assets.md). The full SDK and
runtime objective remains incomplete.

**Reusable initial-animation presets (2026-10-02):** Versioned v2 presets
capture a verified initial clip alone or with authored position/appearance.
Frozen witness proof survives later source-actor edits; full proposed components
are validated together before one single/group Apply. Omitted components and
imported channel ownership stay intact. Inherited clip matches normalize to
absence, including a true no-op on untouched targets. Metadata-only v2 files
retain fresh source/import/hash proof and independent library identity; legacy
v1 files/scopes remain supported. Proposed/Current scene comparison, Return,
Undo/Redo and Save/Open are connected.47 focused retail-enabled Python tests
passed in57.695s, plus8 HTTP/project compatibility tests in1.293s;37 Node files
and37 syntax checks passed. Actual browser capture/transfer/single/group scene
review/Apply/history/Save passed with zero page or unexpected HTTP errors.
Independent Town0b pure-clip MAN readback changes only9471,14→13; inheritance
reproduces baseline output. The saved combined fixture changes only19122,13→14,
and19123,119→150 (X15296→2944), retaining model0102/Z1472. Reopened Build
reproduces package SHA256 `2cc94474453d5a5bd8eaddb07808c6f3dbd10d089d126f9a8e8c4cb0dbd06389`.
No game launched; existing playback/script/gameplay acceptance remains deferred.
See [animated preset workflow](legaia-animated-actor-presets.md). The full SDK
and runtime objective remains incomplete.

**Central flag-reference assets (2026-10-02):** Source-scoped flag groups
now appear in Asset Database search, a shared Inspector, and Active/Project
script dependency graphs. The Inspector shows retail/authored/effective sites,
coverage and exact-PC navigation for P1/P2 owners. A dedicated operand-state
key invalidates stale annotations without changing geometry; project flag
keys now include authored operands. Fresh Town01/Dolk2/map01 sources yielded
899 groups/2,142 sites; source browsing preserves project/saved state.
43 focused retail-enabled Python tests passed in20.085s;36 Node files and36
syntax checks passed. Browser P1/P2 exact-PC navigation, operand layers,
Undo/Redo/Save/Clear, stale-view closure and Active/Project references passed
with no page or unexpected HTTP errors. Runtime variables, story names and
unseen paths remain unresolved. See [flag asset workflow](legaia-flag-assets.md). Gameplay remains
deferred; the full SDK/runtime objective is incomplete.

**Initial animation assignment (2026-10-02):** The actor Inspector now offers
source-verified same-model clip choices, explicit Review/Apply/Clear and witness
preview. A separate ActorAnimation component preserves imported channel ownership,
Undo/Redo and Save/Open. The authored scene and assigned GLB preview keep target
identity/position; normal and draft writers compose the final MAN header once.
Effective references and unconfirmed Live candidates keep animation witnesses
separate from appearance donors and invalidate stale observations. Incompatible
appearance/preset/revert changes reject atomically. Legacy v1 templates capture position/appearance; versioned v2 presets now
include the separate initial assignment. Global/zero/unknown/partial pairings remain
unsupported; scripts, timing and gameplay suitability remain unverified.
39 focused retail-enabled Python checks passed in55.598s, plus a22-check
compatibility pass in21.572s; all34 Node files and35 syntax checks passed. Seven raw MAN/appearance compatibility checks
also passed in47.334s without skips.
Actual browser Review/Preview/Apply/Clear, assigned-frame GLB export,
Undo/Redo/Save, exact scene placement and initial/effective reference edges passed
with zero page errors; malformed/stale HTTP rejected without history changes.
Visual review repaired a clipped Review button; final layout and screenshot
passed. Fresh Town0b package readback changes only MAN offset9471,14→13,
model0102/positions/imports/saved bytes unchanged. Record12 digest and exact
retail import were reverified; clearing reproduces baseline package bytes.
Draft composition preserves the appended retail donor clip and rebases the
existing header9471→9474. Saved private fixture/package/evidence:
`local-output/sdk-20260909/actor-animation-assignment-20261002/`.
See [initial assignment workflow](legaia-initial-animation-assignment.md).
No game launched or package installed. Manual checks are queued for later;
full SDK/runtime acceptance remains incomplete and the565 checkpoint predates
this feature.

**Shared model/clip reference navigation (2026-10-02):** Asset references
now links the eight supported shared field clips to their five global models in
both Active scene and Project scopes. These are explicit reference-pinned
associations, separate from initial/effective actor assignments. Edges retain
the pinned commit, model/clip identity, decoded counts and full source locator;
strict model provenance, record mapping and bounded metadata checks reject
inconsistent evidence. Missing models remain unresolved. The browser labels
actor playback unknown and supports model-to-clip and clip-to-model navigation.
31 focused retail-enabled Python checks passed in 24.333s; all 33 Node files and 34
syntax checks passed with hashes matched to final source. Fresh Town01/Dolk2/map01
discovery verified all 8 clips and 24 source-qualified edges in 33.826s, exact edge
hashes and untouched project/cache/saved bytes. Actual browser Active/Project
HTTP, three-scene navigation and the auxiliary loop passed with zero page errors
or authoring commands; screenshot inspected. Private evidence:
`local-output/sdk-20260909/shared-clip-references-20261001/`.
No game launched; this read-only feature needs no new gameplay gate. The
565-test checkpoint predates both reference workflows; full SDK/runtime
acceptance remains incomplete.

**Project-wide asset references (2026-10-01):** Asset Details → Inspect
asset references now offers Active scene and Project scopes. Project discovery
freshly verifies all imported scenes and assembles existing decoded relationships
through detached scene/catalog views, preserving project state and caches. Shared
stable IDs retain source memberships separately from navigable catalogs, with
scene-qualified edges and deterministic cross-scene navigation. Coverage exposes
source hashes, partial-catalog limitations and explicit unavailable reasons;
recorded relationships do not establish runtime residency or reachability.
Scope/Close cancellation and stale-source guards prevent late results. Strict
HTTP shapes and bounded graphs/metadata retain the existing active response.
Twenty focused retail-enabled Python tests passed in13.948s; all33 Node files
and34 syntax checks passed with hashes matched to final source. Fresh Town01,
Dolk2 and map01 discovery checked actor/script/dialogue/animation/world-map links,
12 shared-model material edges and exact source hashes; complete project/cache
and saved bytes stayed unchanged. This final retail check took21.566s. Per-call
import-hash reuse produces an identical report to the earlier repeated-hashing
implementation. Actual browser Active/Project HTTP responses, three-scene scope,
source navigation, pending Close and stale-source rejection passed with zero
page errors; screenshot inspected. Private evidence:
`local-output/sdk-20260909/project-asset-references-20261001/`.
No game launched. This read-only feature needs no new gameplay gate. The565
checkpoint predates it; full SDK/runtime acceptance remains incomplete.

**Integrated offline checkpoint (2026-10-01):** Full retail-enabled SDK
regression passed565 Python tests in250.658s (252.001s wall time), exit0 with no
skips, on unchanged clean source `43994eb25f5125da4378f2cb970b311931745bf9`.
All33 Node test files and34 editor syntax checks passed with captured hashes
freshly matched to source. This supersedes548 and includes viewport source-wall
editing, atomic mixed actor/scenery placements and their X/Z handles, saved
scene selections and visible placement rectangle selection, alongside earlier
SDK workflows. User-owned disc identity and466714416-byte length were freshly
verified. Browser and package readback evidence remains separate from this
regression. No game launched; runtime parity, genuine Live identity, gameplay
acceptance and full16-layer SDK completion remain unproven.

Private evidence under `local-output/sdk-20260909/`:
`sdk-regression-20261001-scene-placement.log/.json` and
`node-checks-20261001-scene-placement.json`. Python log SHA256:
`4a52fe3e8f7923fc173298f8c6f38b6fa460193ccf72eb6ced78177ff27a595f`.

**Placement rectangle selection (2026-10-01):** Box select placements now
selects visible imported actor and static-decoration meshes through one
depth-tested renderer ID pass. Drag replaces the selection; Ctrl/Command adds,
and an empty rectangle clears it. Hidden entities/layers, ground, NPC drafts and
placed scenery are excluded. Results are canonical and bounded to128, with
atomic rejection preserving the previous selection. Hierarchy and focused
Inspector stay synchronized; the selection feeds existing mixed placement
review and saved scene selections. Escape, camera, resize and stale source
cancel gestures without a project command. Eleven focused Python checks passed
in3.214s; all33 Node files and34 editor syntax checks passed. Actual2×-DPI
pointer replacement/addition, single-actor focus, empty selection, both layer
filters, cancellation and fresh review handoff passed with zero page errors;
screenshot inspected. Saved bytes/history stayed unchanged. Private evidence:
`local-output/sdk-20260909/scene-placement-box-20261001/`. No game launched.
This selection-only feature introduces no new gameplay gate. Historical548
predates it; the full SDK objective remains incomplete.

**Mixed placement viewport handles (2026-10-01):** Retained Proposed
actor/static-decoration groups now expose X/Z handles. Every drag snaps to a
relative 64-unit offset, holding each displayed height and rotation; release
freshly reviews the full source-bound mixed proposal without a project command.
Current has no handles. Rejected/pending drags keep the prior verified matrices
and inputs; Restore cancels pending review and ignores late responses. Escape,
camera, preview/source/representation changes and resize cancel stale gestures.
Thirty-one focused retail-enabled Python checks passed in 18.361s, all 32 Node
files and 33 syntax checks passed. Actual 2×-DPI top-view X/Z pointer drags,
retained review, rejection, cancellation, Current matrices, Apply/Undo/Redo/Save
and fresh Escape/camera/resize checks passed with zero page errors; screenshots
inspected. Normal two-overlay MAN/MAP package passed exact full73728-byte MAP ZIP
readback and independent actor/grid decode, preserving prior actor/scenery edits,
height/rotation, 17 collision edits, floor tiers and saved selection metadata.
Private evidence: `local-output/sdk-20260909/scene-placement-drag-20261001/`.
No game launched; gameplay remains deferred. Historical548 predates this feature.
See [Mixed placement workflow](legaia-scene-placement-groups.md).

**Saved scene placement selections (2026-10-01):** Named project-local
selections now retain 1–128 imported actors, static decorations or mixed members.
Create/Rename/Replace/Delete use strict source-bound commands and one-step
Undo/Redo. Metadata validation remains portable without a disc; scenery Create,
Replace and Recall freshly verify static MAP identities. Cross-scene Recall seeds
actor, scenery or mixed placement tools without editing game overrides. Changed
reimport is blocked under the library and its history. Thirty-eight focused Python
checks passed in 2.554s, all 32 Node files and 33 syntax checks passed. Actual
Town01/Dolk2 browser Create/Rename/Delete/history, Save/Open, cross-scene mixed
recall, single-decoration replacement/recall/Undo and pending source/recall Cancel
checks passed with zero page errors; screenshot inspected. Private saved-project
copy retains the library; normal package is byte-identical before/after selection
metadata (SHA256 `1503a2fb0aa1c141927efac65285390afa876028bfd7ddc46f44dd70c02302fe`).
Private evidence: `local-output/sdk-20260909/scene-selection-sets-20261001/`.
No game launched. This feature requires no new gameplay gate; it does not establish
runtime placement parity. Historical 548 checkpoint predates it.
See [Saved scene selections](legaia-scene-selections.md).

**Mixed scene placement groups (2026-10-01):** Select scene placements combines
imported actors and static decorations in one bounded selection. Move scene
placement group reviews 2–128 targets, including at least one of each kind, with
common X/Z offsets in 64-unit steps within ±16320. Proposed/Current inspection
retains the review and holds preview height; runtime height remains unknown.
Fresh full-source validation precedes one atomic Apply/Undo/Redo operation across
actor and Environment overrides, preserving unrelated components and edits.
NPC drafts and placed scenery are excluded. Forty-seven focused Python checks
passed (43 in 23.086s, four HTTP checks in 2.912s); all 31 Node files and 32 syntax
checks passed. Actual 2×-DPI retail hierarchy selection, Proposed/Current matrices,
held height/rotation, no-op/input withdrawal, one-step Undo for both owners,
Redo/Save and pending Cancel/late-response withdrawal passed with zero page errors.
Fresh browser representation guards also passed without writes; screenshots inspected.
The normal package contains both MAN and complete 73728-byte MAP overlays: exact ZIP
readback and independent MAN/grid coordinate decoding preserved opaque bytes,
unselected scenery, shared rotations, existing collision edits and floor tiers.
The previous 548-test checkpoint predates this change and remains unchanged.
No game launched. Gameplay remains deferred. See [Mixed placement workflow](legaia-scene-placement-groups.md).

**Viewport source-wall editing (2026-10-01):** Select wall rectangle loads
verified source collision data and picks canonical X/Z cells directly in the
scene. Dragging prepares inclusive bounds without a project command; release
opens the existing review. Proposed/Current/Retail wall layers can be inspected
on the labelled Y=0 reference plane, with retained Return/Restore and explicit
atomic Apply/Undo/Redo, Save/Open and normal Build. Camera/source/representation
changes, Escape and pending cancellation withdraw stale gestures or reviews.
Twenty-one focused retail-enabled Python tests passed in10.570s, all30 Node
files and31 syntax checks passed. Real2×-DPI top/perspective browser drags,
comparison layers, no-op/input withdrawal, cancellation and exact full73728-byte
MAP ZIP readback passed with zero page errors; screenshots inspected.
No game launched. This postdates548; gameplay and full acceptance remain open.
See [Wall rectangle workflow](legaia-collision-rectangles.md).

**Integrated offline checkpoint (2026-10-01):** Full retail-enabled discovery
passed548 Python tests in247.512s, exit0 with no skips, on unchanged clean source
`80d4ae765f820551759f181d8372478a49358b72`. All29 Node test files and30 editor
syntax checks passed with captured file hashes. This supersedes514 and integrates
saved-copy discovery, wall rectangles/spatial comparison, scenery groups/drags,
actor transform preview refresh and scenery alignment/distribution with the
previous SDK workflows. The user-owned disc SHA256 and466714416-byte length were
freshly verified. Browser/package evidence remains separate; no game launched.
Full16-layer SDK, runtime parity, genuine Live identity and gameplay acceptance
remain incomplete. This checkpoint predates the viewport wall workflow above.

Private evidence: `sdk-regression-20261001-scenery-layout.log/.json` and
`node-checks-20261001-scenery-layout.json` under `local-output/sdk-20260909/`.
Python log SHA256:
`a247306827edfc8672e0133478dbf1d0fd83ebf6e24536f014a414b4c153da2a`.

**Scenery alignment and distribution (2026-10-01):** Arrange scenery group
aligns2–128 selected static decorations to an anchor on X/Z or evenly distributes
them between fixed endpoints using integer half-up rounding and stable identity
ordering. Other axes, shared transforms, Y/rotation, outside edits and Collision
are preserved. Fresh review, textured Proposed/Current comparison, retained
Return/Restore, atomic Apply/Undo/Redo, Save/Open and normal Build are connected.
Fifty-three focused retail-enabled Python tests passed in17.726s, all29 Node tests
and30 syntax checks passed. Retail browser alignment/distribution, input withdrawal,
comparison matrices, no-op Apply and pending-close cancellation passed with zero
page errors; screenshots inspected. Complete73728-byte MAP ZIP matches the saved
binding and independently decoded descriptor coordinates. No game launched.
Included in548; runtime visibility/collision/lifecycle remain deferred.
See [Scenery groups](legaia-scenery-groups.md).

**Scenery group drag and actor preview refresh (2026-10-01):** Proposed
scenery inspection now has X/Z handles with integer movement and optional
16/64/256/1024 snapping. Release obtains a fresh source-bound review; Apply
remains one explicit undoable command. Rejected and cancelled pending drags
retain or restore the verified proposal without saving. Canvas focus now prevents
scroll displacement during pointer gestures. Imported actor transforms now
invalidate preview identity while retaining cached geometry, fixing stale actor
positions after edits and resampling source height where Y is unknown.
Forty-five focused retail-enabled Python tests passed in16.686s; all28 Node tests
and29 syntax checks passed. Retail browser group drags, rejection/cancellation,
Apply/Undo/Redo/Save, individual actor/scenery drags and exact full73728-byte MAP
ZIP readback passed with zero page errors; screenshots inspected. No game
launched. Included in548; gameplay/full acceptance remain deferred.
See [Scenery groups](legaia-scenery-groups.md).

**Static scenery group placement (2026-10-01):** Ctrl/Command-click static
decorations in the hierarchy or viewport, or Shift-select a hierarchy range,
then choose Move scenery group. Source-bound review supports2–128 instances,
common integer X/Z offsets, retained Proposed/Current textured scene inspection,
one atomic Apply, Undo/Redo, Save/Open and normal Build. Shared offsets/rotations,
Y, unselected instances, Collision and imported identities remain preserved.
Full merged descriptor capacity, signed range, source/metadata/selection guards
and exact zero-offset no-op behavior are checked. Twenty-one focused retail-
enabled Python tests passed in16.060s, all28 Node tests and29 syntax checks passed.
Retail browser two-wall workflow and full73728-byte ZIP MAP readback passed;
screenshots inspected and zero page errors. No game launched; gameplay deferred.
Postdates integrated514. See [Scenery groups](legaia-scenery-groups.md).

**Spatial wall rectangle comparison (2026-10-01):** Reviewed rectangles now
show all selected bits in a top-down Retail/Current/Proposed comparison with
canonical source X/Z bounds, quadrant placement and proposed-change outlines.
Layer switching is read-only; changed inputs withdraw the map and Apply.
Twenty-two focused retail-enabled Python tests passed in17.122s, including five
new synthetic HTTP contract tests; all27 Node tests and28 syntax checks passed.
A synthetic browser fixture checked16 bits, three layer counts, coordinate
bounds, no extra requests/writes and input withdrawal; zero page errors and
screenshot inspected. This is a source-grid diagram, not a terrain/live viewport.
Postdates integrated514. No game launched. See
[Wall rectangles](legaia-collision-rectangles.md).

Post-checkpoint feature: collision rectangle authoring passed17 retail-enabled
focused Python checks in14.410s,27 Node files and28 syntax checks. Multi-cell/
quadrant preservation, merged bounds, stale/context rejection, one-command history,
retail restoration/no-ops, Save/Open and normal package readback are covered.
Browser reviewed/applied16 town01 bits with no review writes, changed/reversed-input
withdrawal, Undo/Redo/Save, stale/extra API rejection and no-op disabled; zero errors,
compact screenshot inspected. Saved package ZIP matched the complete73728-byte
expected MAP with floor tiers preserved. No game launched; owned browser/server
stopped. Postdates514; see [Wall rectangles](legaia-collision-rectangles.md).

Post-checkpoint extension: saved editable-copy discovery passed28 focused Python
checks in4.058s,26 Node files/27 syntax checks. Fresh service/read-only listings,
edited names/metadata, incomplete/foreign/malformed receipts, scan/path/mode/source
guards, API fields and normal Open validation are covered. Retail browser checked
matching/edited/incomplete records, corruption rejection, dirty guard before Open,
Dolk2 X9536 reopen, closed pending list and Refresh with unchanged source bytes,
zero page errors and inspected screenshots. No game launched; owned browser/server
stopped. Postdates514; see [Project copies](legaia-project-copies.md).

Retail-enabled discovery passed **514 Python tests in365.743 seconds**, exit0,
no skips, on unchanged clean source `7a6459e4e29ad96f858d2a8c79eab25dabbc60f2`.
All26 Node test files and27 editor syntax checks passed on that source. This
supersedes498 and integrates saved Build comparison, raw MAN normal Build and
editable project copies with the earlier SDK workflows. The user-owned retail
disc SHA256 and466714416-byte length matched the expected source. No game launched.
Private evidence: `sdk-regression-20261001-project-copy.log/.json` and
`node-checks-20261001-project-copy.json` under `local-output/sdk-20260909/`.
Python log SHA256: `cde485238587c1200c630c4cc6306f4cbf35d7ecdb4892458df9f02b1dfe7434`.
Browser/package/rendered evidence remains separate. Native runtime parity, genuine
Live identity, gameplay and full16-layer acceptance remain incomplete.

Pre-checkpoint feature evidence: editable project copies have39 focused Python checks
passing in3.628s,26 Node files/27 syntax checks passing. Tests cover dirty-source
history/file preservation, copied templates/drafts/views/selections and referenced
TIM/TMD bytes, source metadata/file drift, size/path/mode/name guards, HTTP fields
and dirty project-open rejection. Browser copied unsaved Dolk2 X9536, blocked
dirty Open before dispatch, opened after Undo, saved independent X9600 and reopened
original X9472 with identical source bytes, zero page errors and inspected images.
No game launched; test browser/server stopped. Postdates integrated498, not a
replacement full-suite/runtime checkpoint. See [Project copies](legaia-project-copies.md).

Pre-checkpoint feature evidence: raw streamed MAN normal Build has27 retail-enabled focused
Python checks passing in79.901s, plus25 Node files/26 syntax checks. Tests cover
source offset/length, exact raw placement, no-op/clear baseline byte equality,
record/chunk structure, unaudited mutation/bad locator rejection before writes,
raw donor/dialogue/P2 transition/flag composition with raw ANM, reviewed/build audit
agreement and saved artifact verification. Existing compressed/header/texture/
animation package regressions passed. Browser mixed Town01/Dolk2 Review Build
and Build agree on ten changes/two overlays/68,930 bytes with no authored/persisted
mutation, page error or Run dispatch; screenshot inspected. Broader raw numeric
families/scenes and deferred gameplay require separate evidence. This postdates
integrated498. See [Raw MAN Build](legaia-raw-MAN-normal-build.md).

Post-checkpoint feature: saved Build comparison has 15 focused retail-enabled
Python checks, 25 Node files and 26 syntax checks passing. Coverage includes
different sources, ambiguous identities, exact record/detail/frame identity,
same-ID rejection, source/receipt drift, metadata bounds, real baseline/authored
package comparison and corrupted archive rejection. Retail browser verifies
one difference/eight identical records with no authoring or persistence changes,
same-ID client guard, malformed API rejection and corrupt-file recovery. Final
screenshot inspected after spacing/status fixes. This postdates integrated 498;
future acceptance should include larger mixed-scene audits and pending-request
context changes. See [Build comparison](legaia-build-comparison.md).

**Integrated SDK checkpoint after Build-history correction (2026-10-01):**
Retail-enabled discovery passed **498 Python tests in 368.664 seconds**,
exit0, no skips, on unchanged clean source `ba77695b6e4e86210a2d921e1e5d9935c706e611`.
All24 Node test files and26 editor module syntax checks passed on that source.
This supersedes the passing475 checkpoint and includes Project Settings,
dependency/material/effective-animation references, Build review, saved Build
history and its no-op package compatibility correction. The initial497-test
run at e49e09b0 failed four equality checks and one guard-order check; its evidence
is retained, and the unchanged regressions now pass in full discovery.
The user-owned disc SHA256 and466714416-byte length matched the expected source.
No game launched. Browser/package/rendered evidence remains separate, and native
runtime parity, genuine Live identity, gameplay and the full16-layer plan remain
incomplete. Private evidence: `sdk-regression-20261001-build-history-fixed.log/.json`
and `node-checks-20261001-build-history-fixed.json` under `local-output/sdk-20260909/`.
Log SHA256: `dd9141e0657fce546357327f9750709553de66284299018ba7353a218761ac28`.


The previous failed497-test discovery is retained as evidence. The corrected
full result above supersedes the historical passing result below.

**Historical integrated offline checkpoint (2026-10-01):** Retail-enabled
Python discovery passed **475 tests in 279.577 seconds**, exit0, no skips, on
unchanged clean committed source `9084e5454bd8e191f4f4b03e01f4c82497564619`.
All **20 Node test files** and **22 editor module syntax checks** passed on that
source. This supersedes the469-test checkpoint and includes script operand files
and atomic scene bundles, all12 catalog inspector types, bare scene URI search,
reviewed animation interpolation, and normal raw/compressed animation Build.
The final browser additionally verified observed authored-state changes withdraw
both interpolation Apply and review; baseline restored with zero page errors.
Independent user-owned disc SHA256 and466714416-byte length matched prior input.
No game launched. Native runtime parity, confirmed Live actor identity, gameplay
and the complete16-layer acceptance plan remain incomplete. Private metadata:
`local-output/sdk-20260909/sdk-regression-20261001-animation-build.log/.json`;
Node/syntax source hashes and results:
`local-output/sdk-20260909/node-checks-20261001-animation-build.json`.
Log SHA256: `2ceab6a68dee7a3088ff6faac10b73310931e1917b16cc0c4dcc206c4239791e`.

## Previous integrated checkpoint


**Previous integrated offline checkpoint (2026-10-01):** Retail-enabled
Python discovery passed **469 tests in 176.301 seconds**, exit 0, no skips, on
unchanged clean committed source `d948b2a0f27e77c2b60f17b490ca7d8878389646`.
All **17 Node checks** and **19 editor module syntax checks** passed on that
source. This supersedes the 463-test checkpoint and includes asset field search,
atomic group preset Apply, detached group scene inspection and SDK asset inspector
tools. The user-owned disc SHA256 and 466714416-byte length were independently
verified. Existing browser, package and saved-project evidence remains separate;
this does not prove native runtime parity, Live actor identity, gameplay or all
16 acceptance layers. No game launched. Private command/source/result metadata:
`local-output/sdk-20260909/sdk-regression-20261001-asset-inspectors.log/.json`;
Node/syntax file hashes and results:
`local-output/sdk-20260909/node-checks-20261001-asset-inspectors.json`.
Log SHA256: `eed72436dcc91f0631446e3786abeb42a58964fa8e8bfd967c68a33967da7de4`.

## Fixtures and execution policy

P0 protects memory, provenance, source bytes and basic boot; P1 covers primary
authoring workflows; P2 covers format breadth and diagnostics; P3 covers polish
and longer performance comparisons. Pure/synthetic tests run on Windows and
Linux without game files. Retail checks require `LEGAIA_DISC_BIN`, validate its
exact SHA-256 and skip clearly if absent. BIOS-dependent runs also require a
user-controlled BIOS path. Never download or commit those inputs.

Golden fixtures contain structural counts, stable IDs, digests and expected
diagnostic categories, not disc bytes, model/texture/dialogue payloads,
screenshots, savestates or cards. Generated evidence belongs under ignored
`local-output/`. Bounded quick checks should finish in under a minute; actual
boot/audio/transitions are separate 2–10 minute manual or environment-gated
runs. Long stress/performance captures are opt-in and record build provenance.

| Layer | Priority | Required assertions | Fixture / platform / approximate budget |
|---|---|---|---|
| 1. Pure logic | P0/P1 | Stable structural IDs, coordinate inverses, semantic claim ordering, finite authored values, no imported mutation, dependency identity | Synthetic Python; Windows/Linux; <10s |
| 2. Binary readers | P0 | Truncation, integer overflow, pointer alignment, bounds, malformed ISO/PROT/CDNAME/LZS/MAN/TMD/TIM, unsupported records fail with source context | Independently generated byte fixtures; Windows/Linux; <30s |
| 3. town01 golden | P1 | Exactly 52 actors, 119 models, 52/52 references; deterministic repeated import and stable identities | Metadata-only expectations plus `LEGAIA_DISC_BIN`; <30s |
| 4. Andrew parity | P1/P2 | Compare pinned-source interpretations and independently decoded model indices/geometry topology; document disagreements rather than bless identical bugs | Optional exact pinned checkout and local disc; no production dependency; <60s |
| 5. Retail import breadth | P2 | Multiple towns/fields; bounded catalog pagination; explicit unsupported scene taxonomy; no empty-success output | Env-gated disc, scene label list; <60s bounded batch |
| 6. Generic protocol | P0 | Capability negotiation, identity mismatch, malformed requests, region and byte budgets, non-RAM rejection, timeout, response-size limit, no memory writes | Compiled handlers and fake transport; Windows/Linux; <60s |
| 7. Layout profiles | P0 | Exact serial/text identity, confidence and evidence, safe prefix/range budgets, profile hash determinism, unsupported build rejection | Synthetic profile validation; no RAM dump; <10s |
| 8. Save/restore lifecycle | P0 | Repeated restore advances/invalidates guards and witnesses, stale native rejected, loaded RAM revalidated, frame rollback rejected, soft restart invalidates session | Compiled loader fixture plus env-gated save lifecycle; <60s / manual 5min |
| 9. Overlay replacement | P0 | Same address/different bytes reject stale static and dynamic ownership; matching bytes only reenable correct image; no 0899 in accepted inventory; split growth/shrink/restat | Executable synthetic CMake fixtures; Windows/Linux; <60s |
| 10. CD/XA/audio | P0/P1 | FIFO/IRQ visibility deadlines, seek refresh, audible continuity through FMV and battle loads, distinguish nonzero samples from acceptable sound | Source contract plus oracle/retail capture; manual 5–10min |
| 11. Windows/input | P0/P1 | Hidden/default startup, normal launcher, headless bounded check, debug port1/2 isolation, physical controller continuity, timed release and soft reset | MSVC Release and two-controller/manual check; 2–5min |
| 12. Scene transitions | P1 | Boundary observations invalidate old scene epoch, no retained stale actor selection/correlation, field-battle-field and world-map transitions | Synthetic boundary sequence plus retail route; <30s / manual 10min |
| 13. Actor traversal | P0 | Null, misalignment, out-of-region, loop, duplicate, maximum nodes/bytes/requests, partial/truncated reads, mutation during traversal, epoch changes | Safe 0x9C synthetic nodes and fake guarded transport; <30s |
| 14. Serialization/build | P0/P1 | Unchanged decode/encode preserves exact bytes; edited fields only change intended semantics; opaque bytes retained; source hash mismatch and compression capacity errors; package independently validates | Synthetic MAN/LZS plus env-gated private package; <60s |
| 15. Editor workflows | P1/P2 | Import/select/pick/drag/numeric edit/clear/undo/redo/save/reopen, dirty protection, narrow layout, model object preview, stale request rejection, separate imported/authored/live values | Browser against local Python service; synthetic scene and optional retail; 2–5min |
| 16. End-to-end modified game | P1 | Build one representable actor move, launch exact new executable with package, observe visibly modified placement, revert package restores retail; record audio and transition continuity | Private disc/package/runtime outputs; manual 5–10min |

## Acceptance details

Runtime identity must include executable content, runtime build and logical
session, not merely an executable filename. Observation freshness requires
matching lifecycle, requested execution witnesses and bounded page/region
guards before and after sampling. A nonzero frame counter alone is not a
valid scene observation. Never use restored runs as performance truth until
the restore and ownership layers pass with that exact build.

Model checks separate raw geometry, object-local shape, texture coordinates,
pixel decoding, palette interpretation, skeletal assembly and animation pose.
A successful file export or nonblank preview proves only the checked layer.
Unknown record flags and opcodes stay opaque until independent evidence exists.

Build acceptance has three distinct steps: serializer tests, runtime package
validation, and an actual modified-game run. An exported project or syntactically
valid manifest is insufficient for the final step. Nonrepresentable edits must
identify the entity, property and supported encoding rather than silently round.

The lightweight checks already implemented should remain small. Add new suites
at the listed risk boundaries when the corresponding feature is substantial;
do not generate implementation-mirroring tests merely to increase test counts.

## Additional completed targeted checks

Production snapshot tests now reject missing/duplicate/truncated known sections
before mutation, preserve MDEC FIFO contents on either allocation failure, and
resume a partially supplied MDEC command after restore. Raw and compressed
round trips, reordered sections and repeated loads pass. Unknown sections skip
within their encoded bounds; an unexpected commit-contract failure terminates
instead of returning to a partially restored machine.

The real savestate caller also rejects invalid incoming resume addresses before
guest mutation through both file and blob paths. Template acceptance now covers
capture/apply/undo/redo/save/reopen and an HTTP-level regression for the exact
Create/Apply/Delete payloads. Component tests alone had missed the Delete
route's inappropriate entity requirement; the former route fails this test.

The subsequent feature pass added executable snapshot-header rejection tests
(including omitted/truncated diagnostics), default-stack Windows mod-runtime
validation, TIM/material crops with retail provenance, strict v2 field-profile
rejection cases, conservative actor-candidate tests, and browser Build & Run /
Attach / Stop / upright textured-preview checks. These do not replace the
16-layer campaign above. Keep visible placement/revert, audible continuity,
full field-transition coverage and cold-versus-restored performance as separate
acceptance gates; a single matching MAN header is insufficient for them.

The next pass also completed a production CD controller regression that fails
against the previous unconditional XA data-ready behavior. It covers nine
mode/filter/mute/coding cases and immediate/pending/active DMA scheduling paths.
A no-input cold retail movie advanced from the former 17-frame stall to 1,337
decoded frames and movie-mode exit. This is acceptance of that reproduced stall;
a further no-input run also visibly reached the title menu after transition.
Other FMVs and audible quality require their own recorded results.

Party animation controls compare all six supported clips against unchanged
pinned reference transform functions (20,845 vertex cases). Shared textures
match an independent full-VRAM fingerprint and standalone palette crops while
preserving town01's existing catalog. Retail baseline builds also pass a real
disc serializer check: clear edits or set a retail-equivalent override, rebuild
to the same manifest-only package digest, and preserve the prior authored
package. Actual visible placement/revert remains a separate runtime check.

A single idle retail save/load also completed with paired three-by-ten-second
cold/restored windows: no sustained FPS/frame-period regression, recurrent
static-owner loss, CRC churn or new audio underruns. The nonrecurrent field VM
witness remained unavailable after lifecycle reset, so the full observer
profile correctly rejected; do not count that as observer-reacquisition
acceptance. Repeat the broader transition/restore campaign only against fresh
cold evidence, with current witness and scene guards.

Visible placement/revert acceptance now passes for town01 actor0052. The
authored savepoint appears beside Vahn at X4480/Z11904; the fresh retail build
has zero overlays, removes it from that location, and reports original
X9792/Z8512. Both runs use the same exact binary. Compare the same first-dialogue
screenshots; record that the retail guarded coordinate capture followed one
dialogue advance to reacquire a required VM execution witness.

Static GLB export checks now include binary/accessor/PNG roundtrips, path and
malformed-preview rejection, two real retail exports, Khronos validation and
Blender import/render. Editor HTTP checks reject client geometry/output paths
and invalid frame selection without writing exports or modifying project data.
The browser's selected idle frame2 also exported successfully and its actual
GLB passed Khronos validation. Animation channels and retail replacement remain
separate future features; static export acceptance does not imply them.

Central scene-preview acceptance now covers 51/52 town01 instances, 28 unique
geometries and 5,920 unique triangles. The complete request hashes the disc
once and decoded in 2.145 seconds in the recorded run. Focused tests cover
unchanged imported data, transform/undo cache reuse, returned-data isolation,
source-change rejection and HTTP rejection of client geometry/scene paths.
Parent browser inspection accepted a textured NPC's front/back, mesh-body
picking, X4544 to X4845 movement, imported-position tether, undo restoration,
and Models on/off. No browser warning/error was reported during that check.
Unknown height/facing, parked overlapping instances, script visibility and
exact PSX blending remain explicit limitations. NPC assembly additionally
passed an independent 5,028-vertex reference comparison and Blender render.

The searchable asset browser was checked with a model-reference query returning
one model and its three referring actors; category filtering isolates the model,
and an actor result selects the corresponding inspector. NPC frame stepping,
manual-rate playback/pause and selected-frame export pass in the browser. The
actual exported GLB embeds frame index4 and the selected actor/ANM provenance.
Unknown NPC timing remains null. HTTP checks reject client source bindings,
geometry, paths, invalid frame types and actors outside the active scene.

Script/dialogue UI acceptance includes actor0049's seven readable segments and
23 supported instructions, with an explicit four-byte opaque tail. Actor0001
shows a stop at0x6B for unsupported opcode0x29. Instruction rows expose encoded
successors and record offsets without claiming active runtime branches. Text
substitutions remain tokens. Bounded plain-text writing now passes project,
browser and package checks described in `legaia-sdk/dialogue-authoring.md`.
Gameplay display/revert, broader opcode coverage, relocation/control editing
and story-state evaluation still require their own evidence and campaign.

Central script-resource acceptance should cover metadata-only discovery,
script/dialogue category filtering, partial-decode status, per-PC flag/transition
references, parent-script navigation, actor selection and exact segment focus
in the authoring inspector. Source/project changes must discard stale resources.
Static references alone never pass live flag or transition-route acceptance.

The content-inspection milestone passed all 83 importer tests with private
retail input enabled and six focused HTTP/project tests. The donor-assignment
helper's seven tests establish bounded encoding, donor/channel checks,
unchanged opaque bytes and compressed-growth rejection. They do not establish
editable project integration or game behavior; those remain separate gates.

Authored TIM acceptance (2026-09-10): five writer tests cover raw retail and
synthetic compressed carriers, noops, capacity, aliases, truncation and immutable
headers; project tests cover history, persistence and tampered files. Twelve
build tests passed across textures, dialogue and assignment, including combined
guarded overlays and exact baseline restoration. Browser inspection verified
imported/effective pixels, Clear, Undo, Redo and Save. HTTP checks verified six
invalid requests leave state unchanged, original download byte identity, model
pixel propagation with unchanged geometry, and offline reopen. The native file
picker and in-game texture display/revert were not exercised.

Authored asset browser acceptance (2026-09-10) covers project-wide discovery
from an inactive scene, snapshot isolation, save/reopen and history removal/
restoration. Browser checks use town0c to open town01 actor and texture edits,
open a position template, refresh resources without duplicate rows, and inspect
authored metadata separately from source provenance. Eight focused project
tests passed; no runtime launch or new serializer behavior is claimed.

Field MAP workspace acceptance (2026-09-10): five focused foundation tests
include retail town01, biased wall lookup inversion, malformed table bounds
and overlap, source metadata and unchanged disc content. Five resource/project
checks passed, including stale source rejection and private preview separation.
Browser checks cover base-wall loading, collision/trigger/region inspectors,
toggling and refresh invalidation. Four invalid HTTP requests were rejected
without changing project state. This does not validate live collision or P2
transition execution.

Trigger-to-P2 inspection (2026-09-10): targeted importer checks cover variable
headers, all-partition bounds, section overlap, aliases, gate rejection and
fresh trigger resolution. Service checks cover changed-source rejection before
decoding and after inspection, plus private response separation. Retail checks
resolve town01 fallback trigger 0 to P2 record 38; a sweep covers all 51 eligible
references. No runtime trigger execution is claimed. Future acceptance needs
live dispatch-gate evidence before treating these references as reachable edges.

Build review (2026-09-10): focused report checks cover input metadata identity,
selection/template exclusions, audited world values, padded text and texture
hashes. Fourteen existing build tests pass with private retail input; the
combined report matches six changes in one scene, and no-op/cleared packages
are byte-identical to baseline. Browser acceptance covers the generated report,
reopening it, stale status after an edit and restored freshness after undo.
These checks establish build reporting, not gameplay execution.

Saved normal Build history (2026-10-01): 19 focused retail-enabled Python
checks include actual repeated packaging/receipt determinism, saved-project
reopen, authored-input drift distinct from package integrity, read-only file
verification, audit/manifest/payload/archive tampering, duplicate ZIP members,
missing/invalid receipts, reparse/path rejection and bounded immediate scans.
The focused set also retains normal Build review and raw/compressed animation
packaging regressions. All24 Node files and26 syntax checks passed; strict browser
contracts reject false gameplay/disc-integrity claims and malformed identities.
Fresh-server browser acceptance reopens a saved real nine-change report, verifies
package files, displays older-build receipt absence and rejects malformed routes.
No authoring/Build/Run request, persisted metadata change or page error occurred.
The corrected wide report screenshot was inspected. These checks postdate the
integrated475 checkpoint. Future acceptance should cover larger mixed-scene
histories, concurrent external filesystem changes and deliberate project context
switches during pending history requests; no atomic filesystem snapshot or
gameplay acceptance is implied. See [Build history](legaia-build-history.md).

Texture runtime acceptance (2026-09-10): one cold authored TIM run and one cold
zero-overlay baseline visibly show replacement and removal of the magenta
ground palette. Both processes exit zero without restore or RAM writes.
Manual early witness requests allow the baseline to pass the unchanged v2
observer. A separate bounded startup verifies automatic readiness preparation,
with all three PCs primed and scene verification still false. Twelve focused
service/profile/readiness tests cover identity rejection, missing/current reply
handling, malformed/partial priming and no fabricated scene acceptance.

A subsequent full cold New Game independently validated automatic preparation:
town01's unchanged v2 guard accepted 90 nodes and all three current witnesses,
without manual witness requests or restore. Both owned processes exited zero;
see `legaia-sdk/automatic-witness-field-acceptance.md`.

Live following (2026-09-10): the focused browserless harness executes the real
controller source with delayed responses to check epoch chaining, after-response
cadence, no overlap, command serialization, cancellation, one state refresh on
HTTP rejection, and no transport retry. Candidate checks cover finite positions,
display conversion, epoch mismatch and the 128-entry bound. Ten observer-service
tests pass, including rejection of a revoked token/backwards frame before actor
traversal and acceptance only after a new guarded capture. These are targeted
checks, not the complete cross-scene or repeated-restore campaign.

## Source-bound animation GLB workflow

Targeted checks cover GLB accessor/timeline guards, equivalent quaternion byte
preservation, source-nearest Euler/quantization, real Blender edit/re-export,
shared contribution ownership, stale review rejection, proposed pose inspection,
Undo/Redo, Save/Open and independent normal Build bank readback. Private retail
fixtures cover compressed Town01 and raw-stream Dolk2 animation banks. Browser
checks exercise the actual dialog and history workflow without any game request.
Gameplay clip selection and retail cadence remain deferred. See
[animation GLB workflow](legaia-animation-glb.md).

## Scenery yaw milestone — 2026-10-02

Scenery yaw milestone: ten focused Python cases (no skips), Node matrix/drag/scope guards, frontend syntax, twelve actual browser checks and one actor-handle regression passed. Browser cases cover individual/shared pointer drags, history, Save/Open, Escape/resize/source cancellation, Retail layer, narrow layout and normal Build. Resize assertions count command requests after cancellation to avoid async false positives. Independent package readback verifies exact bytes171/6987 and preservation of prior Collision/offset edits. Manual gameplay remains deferred for visibility, scripts and collision acceptance. See [workflow and evidence](legaia-scenery-rotation-gizmo.md).

## Scenery group rotation — 2026-10-02

Seven focused Python cases cover all quarter turns, source yaw wrapping/high words, axis/ownership preservation, turn0 metadata no-op, source/range/capacity rejection and strict HTTP review/atomic Apply/history/stale guards. Rotation-group and existing group Node guards pass. Twelve actual browser scenarios cover no-op, qualified preview, Current/Return, Apply/history/persistence, normal Build, changed input, pending-close and source withdrawal. Browser assertions read the actual preview Environment binding rather than a nonexistent state.overrides field. Independent full MAP ZIP comparison and expanded matrix arithmetic pass; a separate540px regression checks every label/select/button bound and visual review confirms wrapping. Gameplay visibility, collision and scripts remain deferred. See [workflow](legaia-scenery-group-rotation.md).

## Source-normal direction diagnostic — 2026-10-02

Source-normal milestone:43 focused Python cases (no skips), two Node guard suites and syntax checks passed. Coverage includes primitive layouts, normal references and vectors, normal-table structural bounds, authored composition, animation/partial poses and scene cache refresh. Independent all119-model raw comparisons passed. Ten integrated browser scenarios cover static coverage, normal/surface buffer and framebuffer invariants, Retail/Authored viewing, real vector Apply/history/Save,540px wrapping, animated disablement/playback, normal Build and independent GPU pixels/picking. Vector Apply uses /api/model-vector and closes its editor; the harness tracks that mutation endpoint and waits for updated source data. Disabled-option assertions inspect the actual DOM disabled property. Independent compressed package readback verifies three new normal bytes, preserved earlier edits and exact neighboring data. Gameplay/retail lighting and animated normal transforms remain deferred. See [workflow](legaia-model-source-normals.md).
