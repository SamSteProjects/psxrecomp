# Custom-angle vertex group rotation

In Move model geometry, choose Selected vertex group, then Custom angle under
Turn. Enter degrees from -360 through 360 and choose Rotate group X, Y or Z.
Origin and Group bounds center pivots remain available. The editor reports the
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
