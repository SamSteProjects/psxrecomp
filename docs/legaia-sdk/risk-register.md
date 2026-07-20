# Legaia SDK risk register

Scales: likelihood and impact are `low`, `medium`, or `high`. Owners name the architectural layer responsible for mitigation, not a person.

| Risk | L | I | Mitigation / evidence gate | Owner |
|---|---:|---:|---|---|
| C/C++/Rust integration complexity | M | H | Keep shipped SDK code on the PSXRecomp side; use Andrew's Rust implementation as reference/parity oracle, not a runtime dependency | integration |
| CMake/Cargo build coupling | L | H | No Cargo/submodule requirement in the shipped PSXRecomp SDK; pin reference revisions in provenance | integration |
| Runtime vs clean-room disagreement | H | H | Preserve both observations as claims; PSXRecomp decides retail behavior, traces locate first divergence | provenance/runtime |
| Scene-specific overlays | H | H | Scope symbols/layouts to overlay digest/load generation; never address-only | runtime profile |
| Reused RAM addresses | H | H | Session + frame interval + scene/overlay epoch in every live locator | provenance |
| Actor slot reuse | H | H | Occupancy generations and discriminators; expire correlation on replacement | bridge |
| Dynamically allocated actors | H | H | Enumerate runtime candidates and allocation traces; do not assume MAN order | bridge |
| Indirect script dispatch | H | H | Function/read/write traces and explicit unknown claims; no proximity inference | semantics/runtime |
| Unresolved story flags | H | M | Retain bank/id/site/clean/alias evidence; contradictions allowed | Legaia importer |
| Dialogue IDs depend on scene context | H | H | Include scene/carrier/MES container in identity; require explicit control/data-flow | Legaia importer |
| Static decoder desync through text/data | H | H | Carry `clean`/text-alias status, independent byte scans and runtime validation | provenance |
| Temporary vs authored state confusion | M | H | Five state layers in schema; live is never serialized as authored | project model |
| Runtime timing sensitivity | M | H | Pause/safe-point/batched reads; observer-stall telemetry; no unbounded requests | bridge/runtime |
| Live edits overwritten by game | H | M | No writes in first slice; later transactions declare reapply/rollback policy | preview |
| Unsafe memory writes | M | H | Default read-only, profile/range allowlists, captured originals and explicit consent | preview |
| Fixed PS1 actor/script/resource limits | H | H | Target-specific preflight and capacity reports before authoring/export | build |
| Archive size restrictions | H | H | Adapt proven packer/relayout constraints with attribution; fail with report, never truncate | build/importer |
| VRAM constraints/palette collisions | H | H | Reuse targeted VRAM model and compare live VRAM; budget validator | build/render |
| Disc rebuild/ECC/sector constraints | H | H | Reuse `legaia-iso` sector-aware writer and PPF; preserve original; verify output | export |
| Proprietary data committed | M | H | Ignore rules before extraction, metadata allowlist/scanner, disc-gated tests | repository |
| Proprietary data leaked via traces/caches | M | H | Local ignored storage; metadata-only export; bounded redaction validator | bridge/repository |
| PSX generated game code distribution | M | H | Follow existing PSXRecomp policies; generated output remains ignored/local | repository |
| License incompatibility | M | H | Separate processes/artifacts; record source licenses/revisions; legal review before redistribution | project governance |
| False assumption of commercial rights | M | H | Document PolyForm Noncommercial and Sony-IP boundary; no license modifications | project governance |
| Clean-room contamination | M | H | No generated/decompiled MIPS-to-C in Rust repo; factual interfaces/provenance only | both upstreams |
| Generic PSXRecomp coupled to Legaia | M | H | Isolated integration/profile; generic protocol extensions only; no title checks | PSXRecomp |
| Clean-room runtime copied wholesale | L | H | Provider boundary and narrow DTOs; no vendoring in Phase 0 | integration |
| Upstream research changes | H | M | Record audited Andrew commit, periodically review upstream discoveries, and update local provenance/tests deliberately | integration |
| Two-upstream maintenance burden | H | H | Unidirectional dependencies, explicit compatibility matrix and upgrade procedure | project governance |
| Symbol collisions across overlays/revisions | H | H | Program + overlay digest + address + map revision as symbol key | provenance |
| Region/disc revision mismatch | M | H | Exact disc/executable hashes and profile compatibility; refuse silent fallback | import/runtime |
| Semantic ID instability after parser improvements | M | H | IDs use structural source path; aliases/claims can change independently; migration tests | project model |
| User paths embedded in shareable files | M | M | Store identities/relative refs; redact absolute paths in reports | project model |
| Large JSON/mesh performance | M | M | Metadata JSON plus content-addressed local binary caches; paging and size limits | integration |
| Protocol response stalls emulator | M | H | Existing send budgets; paging/batch caps; monitor TCP stall counters | runtime bridge |
| Existing game/release regression | L | H | Documentation-only Phase 0; future generic changes run existing regression/oracle suites | PSXRecomp |
| Editor UX pressures speculative mapping | H | H | Unknown/contradictory are first-class; confidence threshold blocks export | editor/provenance |
| Undo mutates imported/live data | M | H | Command log targets authored sparse overlays only | project model |
| Collision census mistaken for owning actor pool | H | H | Profile distinguishes linked owning nodes from the filtered 32-pointer per-frame census; no slot-index identity | runtime profile |
| Actor subclass fields conflated | H | H | Scope `.MAP` object fields separately from MAN NPCs; neutral names for `+0x50`/`+0x94` | runtime profile/provenance |
| Source overlay hash mistaken for live identity | H | H | Protocol 1.3 keeps source, exact DMA capture, registration validation and current live identities distinct and declares comparability; require an accepted canonical field-overlay model | runtime bridge |
| Mixed-epoch multi-read snapshot | M | H | Use bounded `read_regions`; reject differing frame or executable-state stamps and re-check scene-epoch signals | runtime bridge |
| Executable-region census exceeds one bounded response | M | H | Use protocol 1.2's eight-record byte-budgeted pages and token-bound cursor; treat ownership-token changes separately | runtime bridge |
| Static structural variant mistaken for loaded image | H | H | Image catalog labels structural variants honestly; require an authoritative load/capture lifecycle before accepting a retail image base | runtime/overlay build |
| Field code has no authoritative native owner | H | H | Keep overlay 0897 identity null; preserve exact source/live guards and collect authoritative image-lifecycle evidence | runtime/overlay build |
| Last execution owner mistaken for current owner after mutation | M | H | Bind exact-PC observations to watched generation; expose stale observations with `observation_current:false` and no current owner | runtime bridge |
| DMA fragment mistaken for a complete overlay | H | H | Label exact transfer spans as fragments; never group adjacent transfers or claim a whole-image identity without a traced transformation/load relationship | runtime/overlay build |

## Highest-priority validation items

1. Prove the semantic export can remain narrow and deterministic without linking clean-room code into PSXRecomp.
2. Resolve canonical loaded-image/lifecycle identity for field overlay 0897 using the generic catalog plus authoritative loader evidence so the revisioned profile can select a runtime.
3. Prove linked actor-node lifecycle and imported-to-live correlation without census/list-order assumptions.
4. Establish explicit evidence for any NPC → interaction → flag → dialogue chain before presenting it as resolved.
5. Add and test proprietary-data ignore/scanning policy before any extraction/cache command writes inside the project.

## Decision triggers

- Do not add a submodule, Cargo dependency or required Andrew subprocess unless a future, separately reviewed need overturns the current one-runtime design.
- Change the generic TCP protocol only after existing commands cannot satisfy a concrete bounded observation.
- Begin PS1 patch export only after project/authored state and capacity validation are stable.
- Seek licensing advice before any combined binary/package or commercial use.
