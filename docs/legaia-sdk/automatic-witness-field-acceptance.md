# Automatic witness preparation: cold field acceptance

On 2026-09-10, the production owned-launch preparation introduced in
`71a969686b477e3fe3227d4103349b2bc65608a8` was exercised through a fresh New Game
and a successful guarded town01 observation. No manual execution-witness
requests, savestate restore, guest RAM writes or authored overlays were used.

The actual runtime executable SHA-256 was
`2be69467c02937d6ccfc86a6030f9380bc5654ea6404694ea3e801a25b716fab`.
The isolated run directory was `Runs/20260910T082803Z-cf42bacc`, runtime PID
38108, process instance
`proc-c0885df3314131a3a5651049be47a575b296baf6cfa5071de6ef02578b55e79b`.
Its zero-overlay package SHA-256 was
`4d90a93bf6f4551bfd89c2997f055cf745188d1189ee563c5a17a88e83fbdce7`.

Launch readiness verified identity and reported all three required profile PCs
primed with initial status `missing`, correctly retaining `scene_verified=false`.
The first movie completed 1,337 decoded frames; normal title selection, story
and default-name confirmation reached the opening Village Elder conversation.
The final screenshot was independently inspected.

Normal attachment and observation then passed the unchanged
`legaia-na-scus94254-field-v2` guard. It reported town01, PROT base 3, mode 3,
a complete 90-node traversal and a current capture. Required witnesses were:

| PC | Status | Backend |
|---|---|---|
| 0x801CF754 | current | static-native |
| 0x801DE840 | current | static-native |
| 0x801D79E8 | current | interpreter |

The final mod status retained zero writes, overlays, sector applications and
copied bytes, with no disc guard failure. Runtime PID 38108 and isolated editor
PID 16788 both shut down gracefully with exit code zero. Main and isolated
project files, the isolated launch configuration and imported metadata retained
their pre-run hashes.

This closes the cold field acceptance gap left by the earlier startup-only
automatic probe. It does not establish restored or cross-scene Live recovery,
every actor's semantic identity, audible continuity, or authored dialogue display.
No runtime or profile code changed for this validation.

Private command evidence, identities, preparation/capture summaries and images
remain in `local-output/sdk-20260909/automatic-witness-field-qa/acceptance.json`
and its adjacent PNGs. The final `field-confirmed.png` SHA-256 is
`568280e83e4cb8dcf3c8824385b670fe1c671aea60ec5fbe21f5a39e26488e6a`.
