# Replace native object geometry

Open a model's GLB mesh importer, choose a **Native triangle donor** in the
object you want to replace, select **Replace donor object geometry**, and choose
your static GLB file. Review compares Current and Proposed geometry and reports
the complete retired face set. Optionally preserve source GLB primitives as
separate groups. Apply publishes one Undo step; Save persists the authored ledger.
Normal Build serializes the resulting model through its existing carrier path.

The selected object belongs to the shared model asset. Every scene instance of
that asset receives the change; selecting a donor does not make a private model
for one actor. Other objects remain. New groups inherit that triangle donor's
packet layout/material, including missing normal, UV and color values. Source
images and arbitrary material/shader layouts are not allocated.

Object identity and existing vector arrays remain. Original vectors can still
contribute to preview bounds even after their faces retire. Existing qualified
animation transforms can pose the replacement in that object; general skinning,
retargeting and new animation channels are outside this import path. Retired face
identities remain reserved and can be restored through the existing face tools.

The incoming mesh must fit the remaining historical 512-face and 4,096-new-vector
budgets, per-object native address limits, historical group/operation/batch limits,
model-byte and carrier bounds. Complete face retirement also uses the existing
bounded removal codec. Replacement does not reclaim retired identities or vector
allocations. Unsupported source geometry or insufficient capacity rejects Review.

The API adds a strict `replace_object` boolean to mesh Review, Apply and scene
Review. It requires `new_group=true` and rejects `replace_group=true` at the same
time. Omission preserves older behavior. Object replacement produces
`legaia.model-mesh-append-review.v8`, with `allocation_mode=replace_object`,
`replace_object=true`, an exact `replaced_object.object_index`, and complete
`removed_face_ids`. Optional primitive preservation retains the geometry's
explicit section ranges. The review key binds mode and ownership; switching from
group to object replacement requires a fresh Review.

See the current [SDK status](SDK_STATUS.md) for focused checks, private retail
Build hashes and the outstanding manual gameplay acceptance queue.

## Multiple section donors and mapped objects

To retain different native materials for imported sections, choose **Map GLB
section donors**, select the sections to import, and choose each section's native
triangle donor and source UV channel. Enable **Replace all existing geometry in
mapped donor objects**, then Review and Apply. All selected sections allocate
before original geometry retires, so multiple sections may use original donors
in the same object. Sections mapped to different objects replace those objects
together. Unmapped objects remain. Skipped source sections allocate nothing.

This batch mode uses `replace_objects=true` and V2 batch Review, independently of
the single-donor `replace_object` option above. Per-section `replace_group=true`
is incompatible. Review lists the original retired face count and selected
objects; changing the mode invalidates it. Each group retains its chosen donor's
native layout and texture binding. Shared asset instances, historical budgets,
qualified pose limits and normal Build behavior remain as described above.

## Frame imported geometry

Both the single-donor importer and Map GLB section donors expose **Camera
framing** after Review. **Shared visible geometry** keeps Current and Proposed
at one common scale. **Visible geometry in this layer** frames only vertices
referenced by its rendered triangles, making replacements easier to inspect
when retired geometry leaves unused native vectors. **All stored vertices in
this layer** includes those unused rows. **Frame mesh** resets zoom without
resetting orbit. Switching layers or framing preserves the reviewed candidate;
these camera controls do not author coordinates, change native bounds or add
history entries. Other surviving objects remain part of the visible model frame.

## Position imported vertices with a native origin

Set **Native origin offset** X/Y/Z in the GLB import dialog before Review or Map
section donors. The origin is added in native model units after baked GLB node
transforms, unit scaling and `[x,-y,z]` conversion. Native Y increases downward.
Changing an offset withdraws Review and rechecks source geometry, retaining the
chosen source section and UV channel. The mapped-section dialog displays and
uses the same origin for every selected section; change it in the import dialog
before mapping. Review reports the exact chosen XYZ offset. Apply stores the
resulting native vector coordinates with the ordinary topology command/ledger.

Offsets may be fractional; positions round after translation. Each component
must be finite and within -32768..32767, and final positions must fit that range.
Rounding can collapse a triangle, which rejects Review. Offsets do not move scene
entities or change normals, UVs, colors, winding or node-transform provenance.
All instances of the shared model inherit its imported geometry. Zero preserves
older behavior. The API's optional `source_offset` is a three-number XYZ array,
bound through inventory, Review, scene Review and Apply. Different nonzero
offsets require fresh Review even if their rounded native candidates match.

## Orient imported geometry

Set **Native import rotation (degrees)** X/Y/Z before Review or Map section
donors. Angles use native model axes (Y increases downward), rotating X, then Y,
then Z with active right-handed matrices. Conversion order is baked GLB node
transform, unit scale, `[x,-y,z]`, native rotation, native origin offset, and
integer rounding. Positions rotate around the native origin; offset is added
afterward. Normal directions rotate with the mesh before Q12 conversion. UVs,
colors and oriented winding retain their existing source interpretation.

Angles may be fractional and must be finite within -360..360 degrees. Final
coordinates still must fit signed native storage; collapsed rounded triangles
reject. Changing angles withdraws Review and refreshes inventory, retaining
selected section/UV choices. Map section donors uses one common orientation
chosen in the import dialog. The optional API `source_rotation` is an XYZ array
bound through inventory, Review, scene Review and Apply. A full turn still needs
its own Review key, even if bytes match zero rotation. Zero preserves earlier
behavior. Rotation changes shared static model geometry, not actor facing,
animation channels or retail node provenance.

## Recovering original mesh inputs

After a reviewed single or mapped import, reopen **Import GLB mesh** and choose
**Retained mesh sources**. Each Current receipt offers its original GLB and an
import-settings JSON download. The settings include scale, native XYZ rotation
and origin, source scene/section/UV choices and donor/replacement options.
Historical donor IDs are evidence of that import, not automatically reusable
Current donors. Reimport requires choosing valid Current donors and Review.

The project retains hash-named originals in `Authored/Models/Sources` and binds
receipts to native ledger spans. Save/Open and later native edits preserve the
inputs. Undo removes the Current receipt; Redo restores it using retained bytes.
Missing/changed GLBs or recipes fail qualification and Build. Retained originals
are project sources, not runtime package assets. Older imports have no retained
original unless they were applied again through this workflow.
