# Reviewing SDK animation exports in Blender

`integrations/legaia/tools/blender_glb_review.py` provides an offline consumer
review for complete SDK animation GLBs. It uses Blender's own glTF importer,
evaluates the clip, renders first/middle/last frames and saves an editable
`review.blend` plus `report.json`. It neither loads a game nor modifies the input.
No Blender dependency is added to the editor or runtime.

Export a complete clip from the editor with an explicit preview rate, then run
this command in the repository, substituting your Blender and GLB paths:

```powershell
& 'D:\Games\Steam\steamapps\common\Blender\blender.exe' --background --factory-startup --python-exit-code 1 --python integrations/legaia/tools/blender_glb_review.py -- 'C:\path\to\export.glb' 'C:\path\to\new-private-review-directory'
```

The output directory must be new; existing reviews are never overwritten. Keep
retail-derived GLBs, renders, Blender files and pose expectations in ignored
private output. Limits are 64 MiB for each input, 4096 source frames and two
million evaluated points. Failed reviews can retain partial private output;
only terminal exit 0 and a completed report establish success.

An optional third argument supplies a JSON object with `glb_sha256` and `samples`:
each sample contains `seconds` and source-decoded `points` in Blender coordinates.
For SDK Y-down source poses, convert `[x,y,z]` to `[x,-z,-y]`. Only vertices used
by emitted triangles belong in expectations. Both directions of nearest-point
comparison must pass within 0.002 source units. This tolerates consumer splitting
or merging duplicate vertices; it is a geometry-position check, not a topology
or material equivalence proof. Half-frame samples can independently check STEP
holds. Blender places glTF time zero at frame 0; this tool sets the review rate
before importing and preserves imported interpolation.

## September 30 evidence

Fresh source `188d1963` exported the imported Dolk2 actor0001 clip: model0133,
30 frames, ten independent rigid objects, three textures, selected rate 15 fps.
GLB SHA256 `3a09e39ab7e58009545dad66b0c58ff8731745961ed0224ffb7cc6015e11fe67`
matches the earlier editor export exactly. Blender 5.2.2 LTS imported and evaluated
61 samples: every frame, every half-frame hold and the terminal pose. Maximum
bidirectional point error was 0.0000170865 source units; 24 distinct evaluated
geometry snapshots establish motion rather than a static-only import.

The saved Blender scene reopened with ten meshes, animation actions and three
packed texture images. The first/middle/last textured renders were visually inspected. Final review
completed with exit 0; two existing focused animation-export tests also passed.
An existing-directory rerun rejected with exit 1, preserving the previous review.
Blender reported default brush-material relative-path warnings while saving;
these do not refer to the imported character's geometry or embedded textures.

Private inputs and evidence are under
`local-output/sdk-20260909/blender-clip-review-20260930/`, with accepted output in
`rendered-final/`. The initial review sampled with an incorrect one-frame offset;
the importer source established frame-zero time and the corrected full run passed.

This establishes rendered Blender consumption of this complete clip. Caller-selected
timing, retail lighting, equipment, other clips, other consumers and full scene or
gameplay parity remain unverified. Gameplay remains deferred at the user's request.
