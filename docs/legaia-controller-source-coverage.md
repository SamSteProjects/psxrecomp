# Controller Source Coverage Survey

Source survey dated 2026-10-08. This is Retail byte/decoder evidence, not runtime execution or gameplay acceptance.

The read-only survey enumerated all124 structural CDNAME block labels from the verified SCUS-94254 source disc, using the existing bounded scene range, MAN carrier and unique partition-1 record-zero reader. Descriptor-compressed and raw-streaming carriers retained their existing independent encoded/decoded parity checks. It inspected entry-reachable paths with the existing decoder and passed the dedicated controller wait qualifier over each verified record.

| Result | Blocks | Meaning |
| --- | ---: | --- |
| Fully decoded supported paths | 37 | No decoder stops on the inspected encoded paths |
| Partial controller inspection | 62 | Bounded source exists, but opaque/conflicting paths remain unresolved |
| Refused blocks | 25 | MAN/controller ownership or source qualification could not be established |
| Total structural blocks | 124 | Complete catalog enumeration, including non-scene blocks |

All99 bounded controller inspections reported zero decoded WAIT_FRAMES sites and zero qualified controller wait targets. This does **not** establish that waits are absent from the game, actor/P2 scripts, opaque controller regions, alternative external entry points or runtime scheduling. It does establish that the current dedicated controller wait serializer has no Retail target exposed by this inventory. No controller wait Review/Apply UI or Build support is claimed on this basis.

Fully decoded controller scene labels: `town01`, `izumi`, `bylon`, `suimon`, `map01`, `keikoku`, `retock`, `geremi`, `rayman`, `ropeway`, `dohaty`, `map02`, `tower`, `tunnelb`, `rayman2`, `ropeway2`, `son`, `doman`, `bubu2`, `taiku2`, `urudre1`, `urudre3`, `kor5`, `korb3`, `koin1`, `koin4`, `koin6`, `juui1`, `town0e`, `koin1b`, `edteien`, `edbylon`, `edbalden`, `eddoman`, `edson`, `other1`, `other7`.

The survey never scans for opcode bytes inside opaque material or fabricates a recovered path. Default actor/P2 wait ownership stays separate from controller ownership. The pinned Andrew step implementation supports the existing native target-word contract; it does not turn a synthetic controller wait test into real Retail coverage.

Private evidence: `local-output/sdk-20260909/controller-waits-inventory-20261008/inventory.json` retains the first64-block pass; `complete-inventory.json` retains all124 results, source disc hash, carrier kinds, entry PCs, decoder status/stop counts, refusal reasons and wait counts. The continuation rechecked the exact disc hash, total labels and first-pass label sequence before adding the remaining60 results. Counts, unique labels and absence of reported decoded/qualified waits were independently checked against the saved full inventory. No extracted byte payload was added to this report.

The next controller work should improve explicit partial source coverage or another observed operand family, while retaining the wait groundwork for a future source-qualified site. Persistent controller wait authoring remains unfinished. This survey does not reduce the full SDK goal: live scene/runtime correlation, native scheduling, playable Build/runtime validation, release parity and deferred manual gameplay verification still require their own evidence. No project authoring, Build, game, runtime attachment, native recompilation, installation or disc export ran; full SDK goal active, solo work continues.
