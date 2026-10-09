# Controller BGM Argument Authoring

The source decoder now exposes `BGM` opcode `0x35` with a little-endian u16 `encoded_id`, the following immutable `sub_op` dispatch byte and explicit unresolved host-effect semantics. The pinned Andrew step implementation reads these three operands, calls `host.bgm(text_id, sub_op)` and advances by the header plus three bytes. The SDK calls the word an encoded ID because a verified association with a specific music asset is not established.

Reference: `crates/engine-vm/src/field/step.rs` at `d6e64c68ede25813d35db20980da82a1a025549b`, blob `9c7801d1626c6f6eb8bd48f9f7c3e5851379e674`. The reference was read without changing its checkout or pin. Reference host dispatch does not prove actual playback, runtime scheduling or retail track identity.

## Native Serialization Foundation — 2026-10-09

`ControllerBgmAuthoringContext` consumes the existing dedicated verified controller record source. Stable request IDs use `script://SCENE/controllers/man-p1/0000/bgm/PC`, with a four-digit hexadecimal instruction offset. It accepts exactly `encoded_id` as an integer in 0–65535. Booleans, extra fields and foreign or unreached IDs refuse. Only reached source BGM instructions in records without decoder stops are candidates.

Independent preimage qualification checks opcode/header, extended context, instruction length, literal u16 operand, dispatch byte and encoded continuation. Patching changes only the two ID bytes, retains complete MAN and decoded control-flow layout, and returns exact byte/hash evidence in source order. A Retail-value request is a no-op. The dispatch byte is deliberately immutable; no host operation is invented or altered.

The relocated helper requires the exact original controller record at its new unique MAN location. It preserves the candidate extent and layout, refuses changed preimages, and retains original and relocated offsets in its audit. This is foundation support for an unchanged relocated controller, not a claim of composition with all existing authored controller families.

The family is not yet registered as a project component, command, editor form or normal Build writer. Existing twelve-family controller authoring stays unchanged. The next work is source-bound Review/Apply/reset and atomic project history, followed by independently qualified native package composition and the editor workflow. No gameplay verification is required to establish those offline layers; music playback and native execution still need separate acceptance.

## Source and Fixture Verification

The fresh verified-disc survey covered all 124 structural CDNAME labels. It loaded 99 bounded controller sources: 88 descriptor MANs and 11 raw streaming MANs. Ninety-six scenes expose 271 qualified BGM sites. Source refusals and decoder stops remain explicit; no opcode scan through opaque data invents extra sites. Examples: Town01 four sites, Cave01 four, raw Rikuroa2 three and raw Dolk2 one.

Every qualified target was patched to IDs 0, 1, 255, 256, 32768 and 65535. A separate literal bytearray oracle constructed the expected whole MAN using the original controller offset, opcode-derived header and source PC. All 1,626 complete byte comparisons and layout checks passed, including dispatch preservation and no-op audit behavior. Saved survey counts, unique labels, carrier totals and stop exclusions were independently rechecked. Project documents, imports and Undo/Redo history remained exact.

Forty-two focused retail-enabled Python tests passed with no skips, including ordinary/extended headers, five dispatch-byte values, seven argument boundaries, lossless compression roundtrip, two distinct operands, relocated offsets, foreign owner/PC refusal and malformed/unknown source refusal. Existing importer, branch, wait and controller flow-source tests passed. The latter also passed 36 Current/Proposed/reset receipt/scenario roundtrips; two source-flow Node suites passed separately.

Evidence: `local-output/sdk-20260909/controller-bgm-20261009/`, including `survey.json`, `python.log` and `node.json`. Source disc SHA-256: `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`. Early harness failures used an incorrect provenance key and omitted the decompressor size argument; final checks pass without weakening production validation. No extracted asset payload is committed. No Build, game, runtime attachment, native recomp compile, installation or disc export occurred. Full SDK and gameplay acceptance remain unfinished.
