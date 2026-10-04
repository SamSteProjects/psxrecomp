# Reviewed model UV rectangle retargeting

Open a model in Edit mode, choose **Edit faces, UVs and colors**, select a
textured primitive and expand **Retarget a UV rectangle**. Choose inclusive
Source and Target U/V endpoints in native byte coordinates (0–255). Source
endpoints must ascend and both rectangles must have nonzero spans. Reversed
target endpoints mirror that axis. Mapping rounds to the nearest byte, with
half ties toward the larger value. This is a coordinate mapping rather than
an image resampler.

Choose the selected primitive or every textured primitive in its packet group,
then **Copy remapped UVs into draft**. Every selected Current corner must lie
inside the source rectangle. No clipping, wrapping, texture address, image size
or material assignment is inferred. More than 256 textured faces rejects the
whole operation; untextured neighbors are excluded. Copy always maps Current
source UVs, replacing earlier UV drafts. The selected vertex/RGB/normal-reference
draft is retained; other group faces retain all their Current non-UV fields.

Use **Preview faces** for the exact source-qualified byte audit and Current /
Proposed model views. **Inspect proposed faces in scene** and **Return to face
editor** preserve the reviewed batch. Changing a rectangle choice or scope
withdraws the old review. Copy again to change the face draft, then Preview.
**Apply reviewed faces** applies the batch as one ordinary model replacement.
All consumers of that model share the edit. Save, reopen, Undo/Redo and normal
Build use the existing project path. Discard or Reset clears neighboring UV
batch drafts; Reset copies Retail values into the selected primitive only.

Retargeting does not resize TIMs or rewrite CLUT/TPage/ABE. Use Resize image and
the source material editor for those separate explicit choices. Runtime
texture windows, VRAM residency, palette animation and final visual suitability
remain deferred gameplay checks. General imported image/material assignment,
new TIM slots and automatic atlas allocation remain unfinished.

## Offline evidence

Two Node guard/lifecycle suites and 17 focused Python cases passed. The private
Town01 fixture remapped object 0 / group 0 of model `scene-tmd/0009`: five faces,
27 changed UV bytes, candidate SHA256
`5066c91047b78013af5c260db03ee1544cf02a562d596ed01d956f91ff1be87d`.
Independent byte construction, reviewed scene Return, one Apply, Undo/Redo,
Save/reopen and exact normal Build carrier readback passed. Neighboring decoded
bytes and source compressed capacity remain unchanged. Visual inspection passed.
Evidence: `local-output/sdk-20260909/model-uv-rectangle-20261004/parent/`.
The proof browser and server closed; game launches: zero. Gameplay suitability
is deferred.
