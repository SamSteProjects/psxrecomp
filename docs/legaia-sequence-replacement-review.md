# Native Sequence Replacement Review

Open a native audio asset's Details, choose **Inspect sequence events**, then **Edit sequence operands… → Review replacement MIDI…**. Choose a complete supported format-0 MIDI. The SDK constructs a native candidate from fresh Current audio and the browser independently checks its decoded header/events against the upload. The panel shows changed event/tick counts, native carrier/SEQ sizes, candidate hash, preserved opaque tail, added alignment and an encoded note timeline.

This is a read-only prerequisite for general native sequence replacement. It does not apply the candidate, retain a replacement input, create history or deliver a Build. The existing matching-layout MIDI operand Review/Apply remains available independently. Writable replacement integration and runtime playback qualification remain unfinished.

## Supported Candidate Generation

The complete format-0 parser permits bounded metrical PPQN, seven channel-event families, positive tempo events and a complete ending. Initial tempo and time-signature anchors describe the native header. Timing, event insertion/removal and initial header values can change. Initial time signature requires numerator 1–255, denominator power 0–7, and the supported interchange values 24/8. Mid-track time signatures, unsupported metadata, system/SysEx messages, incomplete tracks and unknown Current native events refuse rather than losing data.

The native writer preserves the Current header variant/version. Changed tracks use explicit native channel statuses and canonical delta VLQs; therefore even one timing edit can increase the sequence size when Current used running status. A logically unchanged upload preserves every Current byte, including its running-status encoding.

Complete Current opaque SEQ tails are retained as exact bytes. Sound-pack sequence sizes stay four-byte aligned; zero to three explicitly reported alignment bytes are inserted before the retained tail after the encoded ending. The writer does not infer that existing opaque tail bytes are disposable padding. Bank/sample chunks and the physical carrier suffix remain byte-exact. Standalone SEQ carriers need no added chunk alignment. Full entry/sequence bounds, native header/event readback and source hashes qualify the candidate.

## Freshness and Remaining Integration

`/api/audio-sequence-replacement-review` accepts exactly `asset_id`, `expected_entry_sha256`, `expected_authoring_key` and `midi_base64`. It requires fresh Edit mode, validates strict upload bounds and reconstructs Current through the existing native composition service. Its typed response separates the original retail source from the candidate audit/report and explicitly states read-only, unretained, unchanged project and unobserved runtime. Browser validation checks exact fields, extents, preservation claims and complete MIDI-to-native event agreement. Closing the panel or changing project context withdraws the candidate and aborts owned requests; the parent editor owns the child panel.

Next integration: retained replacement recipes with independent replay, source-qualified replacement commands, one-step Undo/Redo and Save/Open, composition with bank/sample/operand families, complete native Build readback and eventually manual playback. Candidate generation alone does not prove any of those outcomes.

## Offline Evidence

Four focused Python cases cover byte-exact unchanged running status, independently declared changed timing/inserted events/headers in both native header variants, complete sound-pack bank/sample/tail preservation, unsupported metadata/partial inputs and source-hash refusal, including native source drift at the final publication recheck. Three Node suites cover the replacement contract/independent MIDI readback plus existing operand-import and MIDI-export behavior. Three JS syntax and four Python AST checks passed.

Actual private Town01 Asset Database → sequence inspector → operand editor → replacement review passed changed/no-op/changed uploads. An independently constructed complete native entry matched the timing candidate; bank/sample/carrier suffix bytes stayed exact, and stale sources/invalid uploads refused. The browser verified unchanged candidate hashes, independently agreed with all candidate events, showed a 400 px timeline without overflow, reported no page errors and made no command/Build/Run request. Complete project document/history/files stayed unchanged and owned helpers terminated. Evidence: `local-output/sdk-20260909/sequence-replacement-review-20261007/qualified/`; the first passing timing-only proof is retained in its parent. No native Build or game ran. This evidence does not establish writable delivery or playback.
