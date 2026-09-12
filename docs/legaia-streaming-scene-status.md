# Streaming scene SDK coverage

Verified offline against the user-owned USA disc on 2026-09-12. These results
describe source import and reference previews, not gameplay acceptance.

| Scene | Imported actors | Resolved model references | Validated animation bindings | Terrain cells |
|---|---:|---:|---:|---:|
| dolk2 | 72 | 72 | 56 | 2,054 |
| rikuroa | 28 | 28 | 11 | 5,682 |
| rayman | 91 | 91 | 72 | 1,254 |
| station | 20 | 20 | 15 | 6,258 |
| balden2 | 66 | 66 | 48 | 759 |

Animation bindings count scene-model actors with a nonzero initial animation
ID and matching channel/object counts. Shared character poses and static models
are separate; a binding count is not a rendered-instance count.

Dolk2 has also passed an integrated browser preview: 432 of 441 entities render,
including terrain, scenery and 63 actors. Its nine remaining actor markers use
shared multipart models F3/F4 with no established pose association. Their model
references are resolved; displaying unassembled object-local geometry would not
establish the correct scene pose.

The current reader supports one explicit model pack and one type-5 animation
bank in the verified streaming MAN carrier. Station's bank requires the extended
entry footprint, clipped to scene ownership. Balden2's model pack uses a five-entry
asset directory. Both now resolve offline. Integrated previews return 304/306
renderable entities for Station and 149/155 for Balden2, with no terrain,
environment or animation-source exception.

Browser review found missing textures on Station models 0001/0012 at VRAM
(640, 0). Their typed TIM pack members use the observed opaque flag 0x80000008;
supporting that variant restores the texture page. The formerly gray surfaces
now display sky textures on large dome meshes. Temporary per-object and per-model visibility controls now support scene
inspection; geometry scale/positions remain intact.
Balden2's room geometry is visible. Runtime parity remains unverified for both.

Equal-span streaming export now supports existing actor positions, bounded
plain dialogue runs, encoded transition entries (including partition-2 owners),
and scene MAP scenery/collision edits. Exported placement and dialogue disc
probes are preserved in the gameplay queue. The resource catalog and P2 script
inspector share verified raw-MAN coordinates, without fictitious compressed
source fields. NPC additions, model/texture replacements and payload growth in
streaming containers still require implementation. All runtime visibility,
script-driven relocation, palette state and gameplay behavior remain deferred
to the [gameplay verification queue](legaia-gameplay-verification-queue.md).

Private evidence:

- `local-output/sdk-20260909/streaming-scene-coverage-20260912.json`
- `local-output/sdk-20260909/streaming-dolk2-actors-browser-20260912.png`
- `local-output/sdk-20260909/streaming-dolk2-models-20260912/project.legaia.json`

The source disc SHA256 is
`e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.
No source payloads are included in this report.
