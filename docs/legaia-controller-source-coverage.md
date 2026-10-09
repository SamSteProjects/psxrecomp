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


## Retail Party Controller Decoding — 2026-10-08

Follow-up source coverage now recognizes MENU_CTRL outer nibble0 and2 as `PARTY_LEADER_REQUEST` and `PARTY_VIEW_SWAP_REQUEST`. Each consumes one sub-op byte after its ordinary/extended dispatch header and advances to the next encoded boundary. The raw sub-op and masked low-three-bit party selector are retained, with `runtime_party_identity_unresolved` and effects not evaluated. These are read-only inspection forms; no party editor, live party observation or new writer is introduced.

The pinned Andrew `crates/engine-vm/src/field/step/menu_ctrl.rs` blob `e28dd4040ca323de43609a11cf7e3cf272936c1c` and `crates/asset/src/field_disasm/decode_subops.rs` blob `c1264426abbee33b96c57e249ece8cfc430a0fe9` independently specify the widths, masked selector and continuation. Pin remains `d6e64c68ede25813d35db20980da82a1a025549b`. Executing Retail PROT[897], load0x801CE818, SHA256 `216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b`, corroborates the continuations: outer0 table target0x801E0C70 adds2 to adjusted PC and returns through0x801E3624; outer2 target0x801E0EB8 routes all inspected paths through0x801DF098, which adds2 and returns through0x801E3628. Both mask the sub-op with7. Existing extended dispatch header handling supplies the additional context byte. Runtime source/global party identity is not inferred from these stores.

The stop survey identified MENU_CTRL0x20 as the most frequent unsupported form (22 original stops). With the two new forms, a fresh source-hash-bound readback over all99 previously bounded controllers matched170 decoded party-control widths/raw spans and exact successors. Cave01, Dream and Station changed from partial to decoded supported paths; **current coverage is40 decoded supported /59 partial /25 refused, out of124 structural blocks**. The earlier37/62 survey above remains the pre-change baseline. Other unknown MENU_CTRL/effect forms continue to stop rather than being skipped.

Offline checks passed:41 focused Python cases ran,39 passed and two optional Retail cases skipped; two Python AST and diff checks passed. Synthetic ordinary/extended headers cover all16 low selector forms for both nibbles, truncation, record-relative PCs and unchanged unsupported neighbors. Actual Cave01 inspector showed the newly decoded PC0x0040 leader request and its PC0x0042 continuation at wide/400-pixel sizes. Both captures were inspected; there were zero authoring commands, page errors or document overflow, and the complete project/import/history state remained unchanged.

Private evidence: `local-output/sdk-20260909/controller-decoder-stops-20261008/` holds original stops, hash-bound native words, all99-controller readback and browser checks. No Build, game, runtime attachment, native recompilation, installation or disc export ran. Native party activation, live state and gameplay remain unverified. Full SDK goal active; solo work continues.
