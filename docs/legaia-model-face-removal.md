# Count-changing model face removal

Open a model in Edit mode and choose **Remove model faces**. Select its object and enter comma-separated **Current face indices**, starting at0. Each index identifies a whole stored triangle or quad; a quad removes two preview triangles. **Preview face removal** shows Current and Proposed geometry with the same camera. **Apply reviewed face removal** requires that exact proposal hash and unchanged project/model source. Duplicate, missing and stale selections reject. Changing the draft invalidates review.

This is count-changing topology authoring. Remaining packets are compacted within the existing model allocation, object primitive counts and group counts are rewritten, and empty groups are omitted. The explicit terminator remains. Object identities, vertex/normal table locations and counts, source vector bytes and model record size stay fixed. Retained packet padding and group footers survive; bytes outside the newly encoded primitive streams retain the canonical Retail baseline. Prior typed edits on retained faces and vectors survive. Edits belonging to a removed face are discarded with that face. Stored normals are not recomputed, and the model's shared instances can all be affected.

The versioned `tmd-face-removal-v1` binding records removed **Retail** identities separately from Current dense indices. A later removal maps its Current indices back to the surviving Retail identities. Qualification reconstructs a complete existing-layout source model, checks its supported typed edits, then independently reproduces the count-changing candidate. Unowned descriptors, padding, footers, table changes, discarded bytes and malformed references reject. The4096-removal budget is cumulative. Source metadata is bounded to4MiB and review geometry to64MiB.

Apply records one normal model-override command. Undo/Redo, Save/Open, authored downloads, further removals, Clear and normal Build are supported. Posed previews retain the same object/vertex channels and refresh face ranges; the existing omitted-equipment object prefix remains authoritative. Vector and normal editing, object transforms, normal-length adjustment and same-layout TMD/OBJ/JSON imports retain this topology override. The retained-face editor now uses qualified Current-to-Retail mapping. The material editor now uses retained Retail group/face mapping. GLB export/import now preserves the qualified Current topology and removal binding. General geometry allocation, face addition, arbitrary replacement remain unfinished. These workflows do not complete general topology allocation support.

Source evidence is AndrewAltimit's unchanged pin `d6e64c68ede25813d35db20980da82a1a025549b`, `docs/formats/tmd.md`, including renderer `FUN_8002735C`, group-count traversal and the object table's summed primitive count. The reference was read without changing that checkout. Retail source bytes and an independently constructed candidate provide the source/carrier evidence; reference documentation does not establish gameplay acceptance.

Twelve focused Python checks pass with private retail source and no skips, including all24 packet families, cumulative identities, empty groups/objects, malformed source ownership, retained typed edits, unchanged posed/frame vertices and existing face-authoring regression. The face-removal and rigid-normal Node suites pass. Eight actual private-retail browser workflows pass through reviewed Apply, Current/Proposed,540px controls, exact Undo/Redo, Save/reload and Build. Additional browser checks verify cumulative source mapping, Clear/Undo and a final fresh-capability preview with closed renderer resources and unchanged files/history. The narrow screenshot was inspected. An initial busy-state refresh defect was fixed before acceptance.

Town01 model0009 object1 Current face0 is a quad: the model changes from190 to188 triangles. The complete candidate matches an independent source-layout encoder. Separate compressed Build readback matches the entire model and preserves every decoded neighboring asset within the154547-byte carrier capacity. Vector tables, padding and object identities remain exact. Package SHA256: `c6bcc7a8ccd981960b07cbb8482c0699e8179ce161a66594a8a841120d5a138c`.

Private fixture, proof and screenshot: `local-output/sdk-20260909/model-face-removal-20261003/parent/`. Owned helpers are closed. No game, installation or full-disc export ran. Native appearance, culling, shared-instance effects and gameplay behavior remain deferred in the [gameplay queue](legaia-gameplay-verification-queue.md).

## Editing after removal

Vertex and normal tables retain their Retail object/index identities. Use **Vectors** to edit their signed coordinates or preview object translation, quarter-turn rotation, scaling and normal-length adjustment. Apply preserves the removal binding and its exact removed Retail identities. Undo/Redo and Save/Open preserve both edits together. Vertex/normal reference lookup is available for this binding and shows both Retail and compacted Current face identities. Removed Retail references are labeled explicitly and have no Current face. Retained faces now navigate to the native face editor. Object-wide vertex/normal retargeting is now available and affects only qualified Current reference words.

TMD imports must preserve the qualified Current packet layout and removal set. OBJ imports must preserve Current oriented triangles; JSON imports use ordered Retail vector capacities and the Retail source hash. Every final candidate is audited against actual Retail ownership, including retained packet fields and opaque bytes. Uploading the original full-topology TMD over a removal binding rejects; Clear the override to restore Retail first.

The private Town01 model0009 proof retains the removed object1 quad and changes vertex0 X126 to143. Browser Apply, Undo/Redo, Save/reload and Build pass; independent readback matches the whole candidate and every decoded carrier neighbor. Native appearance and shared-instance effects still require later gameplay verification.

## Editing retained faces

Open **Edit faces, UVs and colors** after removal, or follow a retained vertex/normal user. Metadata shows the selected Current primitive and its Retail face owner. **Reset draft to Retail** uses that retained Retail face, including its original normal references; it does not restore removed faces. **Discard draft** returns to Current values. Preview and reviewed Apply preserve the removal binding. Existing local vertex, UV byte, baked RGB and stored normal-reference fields retain their native domains. Removed Retail faces have no Current navigation target.

The private Town01 proof changes retained object1 Current0 / Retail1 corner0 U0→17. Apply, Undo/Redo, Save/reload and normal Build pass, with one independently verified model byte and all compressed neighbors preserved. Runtime texture appearance is deferred.

## Retargeting retained references

Use **Vectors**, select an inspected vertex or normal, expand its retarget tool and choose another existing index. Preview must account for every matching Current reference word before Apply is enabled. Removed faces retain their Retail identities and are not edited. The final candidate is audited against actual Retail source ownership, preserving the removal binding and unrelated typed edits. Undo/Redo and Save/Open keep the edits together. Vertex retargeting can collapse faces; normal directions are an SDK diagnostic, not native lighting acceptance.

The private Town01 proof retargets object1 normal4→3 (three words), then vertex5→6 (one word). Browser Apply and cumulative Build match independently patched bytes with the removed quad and carrier neighbors preserved. Native appearance remains deferred.

## Editing materials after removal

**Edit source material bindings** uses Current group/face indices and shows their Retail owners. Retail comparisons and **Reset selected draft to Retail** use these owners even when earlier groups were removed entirely. Texture page/depth, indexed CLUT coordinates and group semitransparency keep their source masks and domains. Group ABE affects every retained member of the selected Current group. Removed faces/groups cannot be selected or restored through material editing.

Review qualifies the complete candidate against actual Retail ownership, including inherited vertex/normal edits and cumulative removal identities. Reviewed Apply, Undo/Redo, Save/Open, model/scene proposals and normal Build retain the binding. Empty source objects show no retained material rows. The private Town01 proof changes Current0 / Retail1 CLUT column9→10, page column10→11 and Current group0 ABE across ten retained faces, with exactly three bytes changed and every decoded carrier neighbor preserved. Native palette residency and blend appearance still require later gameplay verification.

## GLB interchange after removal

**Edit model through GLB** exports the unposed Current model, including its reduced face layout and prior typed edits. The v2 binding JSON names the removed Retail faces and the profile binds exact Current packet/vector ownership. Keep this sidecar with the export. Review regenerates the profile from verified Current bytes and audits the complete candidate against actual Retail ownership plus the unchanged removal set. Changing the source model or removal set makes the sidecar stale and requires a fresh export.

The existing position, source vertex/corner, raw RGB, stored normal/reference and source material attributes use the same qualified Current layout. No new packet/object/vector allocation is admitted. Review distinguishes retained removed-face metadata from pending typed edits; a GLB cannot restore a removed face or silently remove another one. Proposed model inspection/Return, reviewed Apply, Undo/Redo, Save/Open and normal Build preserve the removal binding. The existing128KiB sidecar and32MiB GLB budgets still apply.

The private Town01 proof edits retained object1 vertex1 X126→128 through its Current GLB alias, matching one independently patched model byte. It preserves the removed quad, prior reference/material edits and every decoded compressed neighbor. Native appearance remains deferred.

## Restoring removed Retail faces

Open **Remove model faces**, choose **Restore removed Retail faces**, then select the object and enter indices from its listed removed Retail faces. These are original Retail indices, not compacted Current indices. Retained faces reject. Preview shows the Current and restored model with the same camera; reviewed Apply requires its exact candidate hash. Changing operation, object or selection invalidates the review.

Restoration recreates each selected Retail packet's fields. Current vector/normal tables and other retained packets keep their edits. A retained group keeps its current ABE setting, which also applies to newly restored members; an entirely absent group returns with Retail settings. Per-face edits discarded when that face was removed are not recovered; Undo to the earlier history state is required for those discarded values. No new vertices, normals, packet templates or allocation are introduced.

Partial restoration keeps the remaining sorted removal identities. Restoring all removals moves to the normal typed model format, or removes the override if the result is exactly Retail. Undo/Redo preserves the before/after formats and bytes; Save/Open and normal Build use the ordinary paths. The private Town01 proof restores object1 Retail quad0 while retaining cumulative vector, reference, UV and material edits, returning188→190 triangles with independently reconstructed whole-model and compressed-neighbor readback. Native appearance remains deferred.
