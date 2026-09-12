# Deferred gameplay verification

The user requested on 2026-09-12 that implementation and non-gameplay validation
continue while manual checks are saved for later. This queue does not authorize
launching or controlling the game. A passing archive or browser check does not
close a gameplay item.

New experimental exports also retain `Inputs/project.legaia.json`, imported
evidence and referenced model/TIM replacements. Open that project to recover the
exact authored inputs even after the working project changes. The export report
lists every snapshot file's SHA256 and byte count; the original retail disc is
still required. Older exports listed below predate input snapshot support.

Use **Export history** in the editor toolbar to find this project's experimental
exports and their saved input paths. **Verify saved files** checks the disc hash
and, where available, every input snapshot file against the completion report.
This does not launch the game or mark a gameplay check as passed. History lists
exports under the current project's Builds directory; separately prepared CLI
fixtures in this queue retain their explicit paths below.

For exports with retained inputs, **Open editable copy** verifies and copies those
files into a new project under ReviewCopies, then opens it. Save your current
project and use Edit mode first. Subsequent edits affect the copy; the original
export inputs stay available for reproducing the test.

The toolbar's **Export disc** action exports supported authored changes without
requiring an NPC draft. It uses the same experimental output, input snapshot and
history workflow. CLI callers may omit `--draft` for project-wide export. A
project with no authored changes is rejected; ordinary Build remains the retail
baseline workflow. Export completion still requires later gameplay acceptance.

## Streaming dialogue export probe

- Artifact: `local-output/sdk-20260909/streaming-dialogue-export-20260912/draft.bin`.
- SHA256: `cb8f9914ee04069625b066d7bf043171e5003bc7b62789fdc58065c595ec564f`; 466,714,416 bytes.
- Adjacent report and Inputs snapshot preserve one dolk2 actor0003 text override: run `script://dolk2/actors/man-p1/0003/dialogue/0017/run/0018`, replacement `SDK` plus twelve spaces in its original 15-byte capacity.
- Browser Apply/Undo restored original text and clean state. Exported disc hash, directly reopened MAN text bytes and all snapshot hashes passed independently.
- Deferred manual check: reach the corresponding actor/script branch in dolk2 and verify the changed message, subsequent messages and interaction progression. Branch execution and story prerequisites have not been established by static decoding. No gameplay run has occurred.

## Streaming placement export probe

- Artifact: `local-output/sdk-20260909/streaming-placement-export-20260912/draft.bin`.
- SHA256: `834a22c50b0bc527bd8b9327246ca8c342b34ad82548501e42a3cc47c28f36de`; 466,714,416 bytes.
- Adjacent `report.json` and `Inputs/project.legaia.json` retain the exact export and authored inputs.
- One dolk2 actor-0001 initial placement field changes: X16320 to X64, retaining Z16320. This is a boundary/serialization probe, not an added NPC or a known visible walkable destination. Its script can relocate or hide it.
- Offline verification: independent disc hash, reopened PROT, directly decoded output MAN coordinates X64/Z16320, unchanged TOC, and all snapshot hashes passed. The retail-only project importer intentionally rejects this modified disc.
- Deferred manual check: use this exact disc and an identified runtime; reach dolk2 and inspect actor/script behavior with the live observer when available. Verify scene entry and existing progression remain intact. Do not infer a runtime placement failure solely from not seeing the actor at its encoded initial position.
- Gameplay has not run. Streaming NPC additions, model/texture replacement and other unsupported authored components remain outside this export implementation.

## Ready artifact: added NPC

- Artifact: `local-output/sdk-20260909/saved-draft-export-20260911/draft.bin`.
- Report: adjacent `report.json`.
- SHA256: `f8a75661a02acd537257029a9df9e7e79ec1703b766a942a333e63c217e04f97`.
- Saved project: `local-output/sdk-20260909/actor-draft-persistence-check`.
- Draft: Candidate NPC, donor town01 actor0011, authored X3008/Z5440.
- Offline evidence: exact reopened MAN/PROT, independent output hash, matching
  CLI and browser exports. This artifact contains one draft, not the later
  separate appearance/dialogue/transition composition experiments.
- Manual steps: cold boot this specific disc with an identified runtime; reach
  town01 (Select can skip the prologue); locate the draft using the editor;
  inspect appearance, position, animation and interaction; leave and re-enter;
  check that existing actors, dialogue and scene progression still behave.
- Expected: added actor at the authored initial position, subject to its cloned
  script; no missing original actors or broken transitions. Script relocation
  coverage is incomplete, so any unexpected behavior must be captured rather
  than dismissed as a placement issue.
- Record runtime executable hash, disc hash, location, screenshots and results.

## Features needing a dedicated manual fixture

### Isolated collision fixture available (2026-09-12)

- Disc: `local-output/sdk-20260909/collision-only-export-20260912/draft.bin`.
- SHA256: `f77fb410addd646904208f184b2a1a174f73d9b7378f7fa54c28a25c90822c5d`.
- Adjacent `report.json` and reopenable `Inputs/project.legaia.json` preserve the exact inputs.
- Only authored edit: town01 row30/column30/quadrant0, unblocked to blocked,
  MAP byte20254 bit16. No NPC drafts, model, texture or animation edits.
- Locate center X3872/Z3744. Exact canonical integer bounds are
  `3840 < X <= 3904`, `3712 <= Z < 3776`. Use the editor's coordinate locator
  and Effective collision overlay to inspect the location before gameplay.
- Alternatively open collision wall editing, choose the saved cell under Applied
  wall edits, then click Locate cell in viewport. This browser flow is verified;
  the reference marker uses sampled guest Y-128 here. The grid remains a Y0
  overlay, not a runtime collision surface. Screenshot:
  `local-output/sdk-20260909/collision-terrain-locator-20260912.png`.
- Later manual check: compare approach from each accessible side against the
  unchanged retail disc, leave/re-enter and repeat. Runtime scripts, other
  blockers and floor tiers may affect accessibility; record those observations.
- Final MAP/PROT reopening, independent disc hash, all snapshot-file hashes
  and collision-only project reopen passed. No gameplay was performed.

### Combined integration fixture available (2026-09-12)

`local-output/sdk-20260909/combined-assets-export-20260912/draft.bin`, with adjacent
`report.json`, SHA256 `8e1fd5be2cc845c06aa6293964bd0b581a06d3db5d4c6a86c54d65c9bc0f805f`.
Contains the saved town01 NPC draft, model0105 first vertex-X increment,
clip0012 frame0/object0 translation X100, TIM5/raw/0 last payload byte XOR1,
decoration cell1833 Z-256 and collision row30/column30/quadrant0 toggled.
Final MAP/model/texture/animation carrier checks, MAN/PROT reopening and independent
disc hash passed. This fixture checks combined behavior; its tiny texture/model
changes are serialization probes, not a substitute for visually obvious isolated
acceptance fixtures. Use the NPC steps above, inspect shared clip users and the
wall edit, and record any regressions. No gameplay has been run on this image.

These are implemented within bounded authoring scopes but must have a current,
identified output prepared before asking the user to test them. Historical
packages must not be silently substituted.

| Feature | Manual check | Preparation still needed |
| --- | --- | --- |
| Animation channels | Confirm edited pose and motion throughout playback, shared users and scene reload. | Export a minimal current authored/baseline pair with the exact clip and axes recorded. |
| Model shape | Confirm edited mesh under animation and scene lighting, then baseline restoration. | Export a minimal model-only pair and record model identity and source/output hashes. |
| Collision wall bits | Attempt movement across the exact edited subcell boundaries; compare baseline. | Isolated collision fixture above is ready; baseline is the unchanged retail disc. |
| P2 dialogue | Trigger the edited P2 text, close it and resume normal control. | Build a minimal fixture with the owning trigger, text and expected interaction documented. |
| Transition arrival | Traverse the exact source trigger and inspect destination arrival/facing. | Build a minimal arrival-only pair; preserve destination name and record encoded values. |
| Combined draft edits | Check original actor edits plus added NPC behavior together. | The combined integration disc above is ready; isolated visible edits still need dedicated fixtures. |
| Stability and restores | Check field/cross-scene restore, controller behavior, battle/audio cases. | Use the per-fix provenance and acceptance gaps in `legaia-release-parity.md`. |

The previously user-confirmed wall gap and bounded actor49 appearance/dialogue
acceptance remain recorded in the feature matrix. Do not repeat those checks
without a changed build or a specific unresolved behavior.

## Work that continues independently

- Complete authored asset/container composition and multi-scene draft export.
- Preserve report provenance and expose completed artifacts coherently in the editor.
- Expand supported editor tools and source-backed inspection from the original SDK requirements.
- Validate commands, history, persistence, source preservation, serialization and browser behavior.
- Prepare minimal manual fixtures as their implementation reaches that boundary.
