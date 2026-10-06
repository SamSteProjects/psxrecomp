# Selected script operand layers

In **Script and dialogue**, select a decoded instruction from the source instruction table or source-flow graph. The selected-instruction inspector under **Source flow and branch destinations** compares that boundary across three distinct layers:

- **Retail**: the immutable imported instruction or atomic message segment.
- **Current**: applied project script operands and branch choices, composed by existing qualified SDK writers.
- **Reviewed Proposed**: the currently accepted branch review over Current. Other pending form drafts are not included.

The table shows the instruction, encoded dispatch context and length, decoded operand fields, and encoded successors. Message boundaries show decoded text and their continuation. Expand **Selected encoded bytes and differences** for each layer's exact bytes and byte changes by record PC. This is static inspection; it does not run a VM or observe the game.

**Boundary not decoded** means that layer's inspected path did not decode this original boundary. Its retained bytes are not classified as deleted, and execution remains unknown. **Inspection unavailable** and **Not reviewed** stay explicit. Decoder stops and opaque regions remain in the surrounding flow workspace. Proposed values withdraw on draft changes, Discard, source/state invalidation, failed Apply or close.

Apply other operand edits to inspect them in Current; branch changes require Review before appearing in Proposed. Actual byte delivery can then be inspected with [Retail versus saved Build](legaia-source-build-script.md). The selected view introduces no command, authored state, runtime write or serializer.

## Offline acceptance, 2026-10-06

An actual private Town01 source script (`man-p2/0000`, PC `0x000F`) shows Retail RGB `[255,255,255]`/intensity `65` beside Current RGB `[254,255,255]`/intensity `66`, with exactly two changed encoded bytes. A Town01 actor branch (`man-p1/0002`, PC `0x001F`) shows the accepted Proposed target separately; its source/current delta is `-17` and reviewed delta `-21`, with one encoded-byte change. The UI review is not applied.

Actual browser asset entry, source/current inspection, branch Review, Discard and close passed, as did wide/narrow layouts and source/history preservation. Focused Node checks cover detached instruction/message values, exact bytes, unavailable/unvisited paths, ambiguous boundaries and changed source shape; the existing branch workflow regression remains green. Private evidence is in `local-output/sdk-20260909/script-node-layers-20261006/`. No game, Build, installation or full-disc export ran.
