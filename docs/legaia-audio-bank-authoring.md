# Native VAB parameter codec groundwork

The native VAB parameter serializer is implemented and qualified. It is **not yet connected to SDK project commands, editor editing controls or Build**. The bank inspector and source sample audition remain the available bank workflows. Development stays solo; gameplay verification remains deferred.

`importer/audio_bank_authoring.py` supports 27 existing scalar parameter fields:

| Source record | Parameters | Encoded range |
| --- | --- | --- |
| Header | Master volume, pan, attributes1, attributes2 | u8: 0–255 |
| Program slot | Volume, priority, mode, pan | u8: 0–255 |
| Program slot | Attributes | Little-endian u16: 0–65535 |
| Packed tone record | Priority, mode, volume, pan, center, shift, minimum/maximum key, vibrato width/time, portamento width/time, pitch bend down/up | u8: 0–255 |
| Packed tone record | ADSR1, ADSR2 | Little-endian u16: 0–65535 |
| Packed tone record | Program and sample operands | Little-endian signed16: −32768–32767 |

These are encoded native widths. They do not establish valid runtime enums, instrument assignment, note/sample selection, playable pitch, envelope interpretation or audible effects. In particular, program slots and packed tone pages remain separate identities, and a signed sample operand is not automatically a resolved waveform assignment. Counts, slot/page allocation, sample replacement and interpreted ADSR editing are outside this codec.

The format evidence is pinned Andrew reference `d6e64c68ede25813d35db20980da82a1a025549b`, `crates/vab/src/lib.rs`: explicit header byte reads and ProgAtr/VagAtr scalar reads establish offsets and endian widths. The current reference checkout is not advanced or modified, and reference code is not shipped as a dependency. Existing source bank qualification owns header/table bounds and sample spans; new header and vibrato/portamento scalar offsets were checked directly against the pinned parser.

`replace_bank_parameters` accepts immutable Retail/Current bank bytes, their reviewed hashes and one to 256 explicit edits. An edit identifies exactly its `section`, `field`, `value`, and either a program `slot` or packed tone `page`/`index` where applicable. It never accepts client-provided offsets. Unique field ownership, integer types and widths are checked before returning bytes. Boolean values, unknown/reserved/count fields, bad slots/pages/indices, duplicate fields and stale hashes reject atomically.

Current may contain earlier qualified parameter edits. Everything outside those scalar spans stays byte-identical, including reserved header/record bytes, program tone counts, sample-size table/spacer, sample bodies and trailing data. Source and output are independently inspected to preserve layout, declared counts and sample ownership. The audit reports exact bank offsets, widths, signedness, source/Current/Proposed integers, hashes and changed byte positions.

`replace_audio_bank_parameters` maps the qualified bank back into standalone VAB, leading contiguous VAB chunk or split header/sample carriers. It preserves native piece ownership, chunk declarations, physical entry length, nonbank tails and any sequence data. It reassembles the bank from the output for exact readback. This domain codec requires nonbank Current bytes to remain Retail; future SDK composition with SEQ edits must qualify the two families independently and merge their audited disjoint spans.

Verification on 2026-10-06: all nine focused Python checks passed without skips/errors/failures. Every one of the 202 qualified retail banks passed a combined edit of all 27 parameters and exact restoration of the complete physical entry. Independent literal offsets and `struct.pack_into` encodings produced expected banks/carriers; tests did not reuse the serializer field registry. Fixtures cover all three carrier shapes, sparse slot versus packed-page identity, unsigned/signed extremes, reserved/sample/padding preservation, composed Current/no-op, unsupported allocation/count fields, stale hashes and incomplete carriers. The 16 unavailable source banks remain outside authoring. Private evidence: `local-output/sdk-20260909/audio-bank-authoring-codec-20261006/focused.log`.

A separate source-qualified inventory recorded the raw ranges of all 27 fields across 202 banks, 25,856 fixed program slots and 17,264 packed tone records. All 202 qualified retail carriers use split VAB header/sample chunks; standalone/leading-contiguous delivery is covered by structural fixtures, not claimed as retail coverage. Ranges include unused slots/records and do not define runtime validity limits. Private evidence: `source-field-ranges.json` and `ranges.log` in the same directory. The bank inspector's stale limitation text was also corrected to recognize existing bounded waveform/sample audition workflows; its Node contract and a focused preservation check passed.

Next integration must preserve existing SEQ editing while adding bank operand metadata, source-qualified atomic commands/history, Save/Open and copy validation, Retail/Current/Proposed controls and native Build audits. Because a bank and sequence can share one raw PROT entry, Build must emit one composed entry overlay from independently qualified disjoint family changes, rather than overlapping bank and sequence overlays. Both fixed-span and relocated PROT packages need independent full-entry readback before claiming native delivery. No game, runtime attachment, installation or full-disc export was used for this codec qualification.
