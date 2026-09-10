# Same-scene restore and Live recovery

The 2026-09-10 cold zero-overlay run tested one save and one load in town01,
followed by normal dialogue input and a fresh guarded Live capture. The runtime
executable SHA-256 was
`2be69467c02937d6ccfc86a6030f9380bc5654ea6404694ea3e801a25b716fab`.
Private run: `Runs/20260910T084049Z-82a816e2`, runtime PID 46144, editor PID
33356. Initial automatic witness preparation and cold observation accepted
town01, PROT base 3, mode 3, with a complete 90-node chain.

Save/load each ran exactly once in private slot 11. Completion required a new
generation, pending zero, success, and matching operation/slot; acknowledgment
alone was insufficient. Save/load completion receipts took 79.3/58.4 ms.
The saved file SHA-256 was
`f913654b31364e1029c856b16e4f34f49be76432131d6d72995d98e7ab413eac`.

The first post-load evidence parser mishandled `observation: null`. Its response
was not retained before that private harness error, and the immediate screenshot
was not taken. Neither runtime operation was retried. The retained pre-input
capture is delayed by 51.9 seconds: it rejects the old epoch and a fresh capture
rejects the missing VM-dispatch witness. The other two required witnesses had
already re-executed. The misleadingly named private `immediate-restored.png`
is this delayed capture, not immediate evidence.

One normal Cross input advanced the dialogue. A new guarded observation was
accepted approximately 3.1 seconds later, with all 90 nodes and three current
witnesses: 0x801CF754 and 0x801DE840 static-native, 0x801D79E8 interpreter.
The accepted epoch differed from the cold epoch. No witness was copied from
pre-restore state, and no profile or runtime code was changed for this check.
Cold and recovered screenshots were independently inspected.

Separate settled windows measured:

| Measure | Cold | Restored |
|---|---:|---:|
| Window seconds | 10.145 | 10.200 |
| FPS | 60.130 | 59.999 |
| Frame-period p95, ms | 16.6902 | 16.6897 |
| Static hits/second | 5048.9 | 5069.9 |
| Static rehashes / CRC misses added | 0 / 0 | 0 / 0 |
| Audio underruns / overflow drops added | 0 / 0 | 0 / 0 |

Each condition has one roughly ten-second window, not a repeated statistical
benchmark. The restored condition is the next dialogue page in the same idle
scene. The evidence supports no sustained slowdown in this case and guarded
Live recovery after genuine VM execution. It does not prove immediate complete
reacquisition, repeated/cross-scene restores, battle/world-map performance, or
audible quality.

The browser subsequently exercised opt-in Live following against this restored
process; those captures are separate from the performance windows. Private
evidence remains in `local-output/sdk-20260909/restore-live-qa/summary.json`,
the detailed acceptance report, PNGs, and logs. Protected project files remained
unchanged. Runtime PID 46144 and editor PID 33356 both exited zero; their
listeners were absent afterward and main editor PID 42672 remained on port
4388. Cleanup results are retained with that evidence.
