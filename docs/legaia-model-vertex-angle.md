# Custom-angle vertex group rotation

In Move model geometry, choose Selected vertex group, then Custom angle under
Turn. Enter degrees from -360 through 360 and choose Rotate group X, Y or Z.
Origin, Group bounds center and Explicit source XYZ pivots are available. The editor reports the
actual quantized angle; Apply commits the draft as one normal project change.

Degrees round to the nearest 1/4096 turn, with signed half ties away from zero,
then wrap to native angle units 0..4095. A shared Q30 quarter-sine table supplies
all axes. The browser uses BigInt products, and Python uses integer products.
Bounds centers retain half-word precision until one final signed half-away
round to native signed16 coordinates. Existing quarter-turn tools retain their
behavior; custom cardinal angles agree with them exactly.

This edits selected object-local vertex words. Normals, primitive references,
padding, unselected rows and other objects remain fixed. It does not change
actor placement or pose, and does not claim to reproduce GTE instruction
rounding. Rounded arbitrary-angle edits need not invert exactly with the
opposite angle; Undo restores the exact previous bytes.

Local drafts require explicit Apply. Current and Retail comparison, movement
scene inspection, single/all-instance previews and return/restore preserve the
draft. Source hashes, exact operation fields, qualified object ownership,
bounded unique indices and signed16 overflow rejection remain enforced. A zero
turn or a rotation whose rounded coordinates do not change adds no history.
Invalid or overflowing edits reject atomically.

## Offline acceptance, 2026-10-07

Fourteen focused Python tests and five client suites passed, with two changed
client syntax checks. Coverage includes cardinal compatibility on all axes and
pivots, literal 45-degree words, retained native bytes, zero angles, bad inputs,
stale hashes, exact HTTP fields, read-only reviews and one-step history.

The actual Town01 Current model rotated indices `[0,1,2]` around Y by 45 degrees
about their bounds center. The browser exercised invalid/zero degrees, local
draft locks, Current/Retail/Draft layers, single/all-instance scene inspection,
return/restore, Apply and Undo/Redo without page errors. A scene caption error
found by the first private attempt was repaired; that failed evidence is retained.
Save/Open preserved the final native bytes. Wide and 400 px layouts were
inspected; the narrow draft left the SDK document unchanged and had no
horizontal dialog overflow.

Independent trigonometry applied directly to the starting native words matched
the output exactly. Only seven byte offsets changed, all inside the selected XYZ
words. Normal private Build `618b66e0863449cf` was independently decompressed
from both directory and ZIP outputs: the entire containing model section matched
the expected native section. ZIP integrity and package SHA-256 were verified.

Current model SHA-256:
`a01c93c5d9f0910dd313e37bd677f1c32050c2b689604c23fd6d30b5b86e0ee8`.
Package SHA-256:
`ae64c5c2cb9efdea8ffb5cab79a6a284c4b2d9eeda9e60fecec1a13742572ab1`.

Private evidence stays in
`local-output/sdk-20260909/vertex-angle-rotation-20261007/`.
No full regression campaign was repeated. Gameplay verification remains
deferred; development stays solo and the full SDK goal stays active.

## Explicit Source Rotation Pivot

Selected vertex group rotation now offers **Explicit source XYZ** under **Pivot**. Enter three signed16 object-local source coordinates (-32768 through 32767), choose a quarter turn or Custom angle, then Rotate group X/Y/Z. Source positive Y points down. The pivot does not represent an actor or scene position. Draft/Current/Retail layers, single/all-instance scene comparison, explicit Apply/Discard, Undo/Redo and Save/Open use the existing rotation workflow. Pivot controls lock while a draft is pending.

The existing `pivot` field accepts either `origin`, `center` or an exact three-integer XYZ array for both rotation operations. Scaling and rotation share bounded pivot validation and doubled-coordinate pivot calculation in each language. Custom angles retain their existing Q30/BigInt arithmetic and 1/4096-turn quantization; quarter turns agree exactly at cardinal angles. All output words round nearest with ties away from zero. Invalid arrays, booleans, fractional/out-of-range coordinates, stale sources and coordinate overflow refuse the entire change. Only selected XYZ words change. Normals, padding, topology, unselected rows, other objects, allocated row ownership and imported evidence remain fixed. No actor heading, skeleton pivot or runtime rotation field is inferred.

Offline checks passed on 2026-10-08: 23 focused Python cases and three Node suites passed, along with JavaScript syntax and Python AST checks. Added tests compare entire native models against independently literal expected quarter-turn and 45-degree results around (10,-20,30); cover X/Y/Z cardinal parity, malformed arrays, overflow, extreme-pivot zero-angle no-op, history and allocated-row ownership. Existing rotation, angle and scale regressions passed after the shared pivot refactor.

A private native Town01 browser check staged/discarded a quarter turn and applied a custom Y45-degree rotation for object0 vertices0/1/2 around (10,-20,30). Local draft/Discard, invalid-angle refusal, source layers, single/all-instance scene Review/Return, one Apply, Undo/Redo and Save/independent Open passed. Desktop and 400 px captures were inspected without horizontal overflow or browser page errors. An independent floating-point 45-degree calculation matched this fixture's entire native model; nine changed byte offsets belonged only to the selected XYZ spans. This fixture comparison complements the literal-word/cardinal tests and does not claim exhaustive equivalence to integer angle arithmetic for every input.

A private data-package Build passed full containing-section readback from directory and ZIP, with package SHA-256 `c0c5f73e833642caeb6bc931f8cfe20208a291cfe08ec2e4bd9486acaf773e01`. Final Undo/Save restored the original project document, model and imported evidence with one legitimate Redo entry. Evidence: `local-output/sdk-20260909/vertex-explicit-rotation-pivot-20261008/` (`native-proof.json`, `cleanup.json`, `edit.json`, browser log, screenshots and private package). No game, runtime attachment, native recompilation, installation or disc export ran. Gameplay lighting/appearance remains deferred; the full SDK goal is active and solo work continues.

Rotation pivots can also copy an exact Current object-local vertex. See [Current Vertex Pivot](legaia-model-vertex-axis-scale.md#current-vertex-pivot) for the shared controls, source guards and offline evidence.
