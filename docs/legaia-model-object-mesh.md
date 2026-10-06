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
