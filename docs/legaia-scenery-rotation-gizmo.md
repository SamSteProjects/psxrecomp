# Scenery yaw handles

The scene viewport can rotate supported field scenery around its source Y axis. This edits the existing source-bound Environment component and uses the same MAP writer as numeric transform editing. It does not establish the object's runtime visibility or script-controlled resting pose.

Select a scenery object, choose **Rotate scenery Y** in **Scenery transform tool**, and drag the ring. Static decorations use an individual cell override. A placed object requires **Enable shared transform handles** in the Inspector; its yaw changes the shared MAP descriptor and therefore all its source grid uses. Individual decoration yaw overrides retain their own angle when a shared descriptor changes. Shared offsets and other inherited axes still apply.

**Scenery yaw snap** is enabled by default. **Scenery yaw snap step** offers 16, 64, 256, and 1024 source angle units. A full turn is 4096 units; yaw is wrapped into 0–4095. Snapping rounds the absolute proposed angle, rather than rounding only the drag delta. For example, an existing yaw of 64 with a quarter-turn drag lands at 1088 with step 16, but 1024 with step 1024.

During a drag, only temporary preview matrices change. Releasing the pointer applies one ordinary command and one Undo step. Escape, pointer cancellation, loss of focus, a hidden page, or a change to the source, camera, viewport size, tool, or layer cancels the preview. The numeric Inspector remains available, and the Retail layer shows the original transform separately.

After applying, review the object and any affected shared instances, use Undo/Redo as needed, and Save the project. Opening the saved project retains the authored yaw. A normal Build uses the existing source verification and Environment patch path. Gameplay verification can be deferred until a user requests a build to run; browser placement alone does not qualify collision, scripts, or rendered runtime behavior.

## Source and coordinate contract

Each field MAP descriptor is 32 bytes. Signed offset X/Y/Z occupies bytes 0/2/4; unsigned rotation X/Y/Z occupies bytes 8/10/12. Yaw writes the halfword at `record_index *32 +10`. Other axes, offsets, model selection, flags, anchors, and padding are preserved. A cell's grid word at `0x8000 + cell_index *2` uses its low nine bits to select the descriptor.

An individual static decoration edit copies the complete shared descriptor into a zero-filled, unreferenced descriptor and replaces only those low-nine owner bits. Reserved descriptor identities and spawned placed objects are not eligible for individual allocation. Subsequent edits retain the cell's authored descriptor, and allocation is regenerated deterministically against immutable source bytes during package preparation. A shared edit runs before individual overrides.

The preview's source-local rotation order is `Rz * Ry * Rx`, followed by one source-Y-to-editor-Y reflection. Positive source yaw maps local positive X toward negative Z, and local positive Z toward positive X. The gizmo's ring is expressed in source X/Z around the displayed pivot. Preview trigonometry uses floating point and does not emulate exact GTE fixed-point rounding.

## Independent offline evidence

Private proof is under `local-output/sdk-20260909/scenery-yaw-20261002/research/`. `prepare.py` copies a previously saved Town01 scenery-layout project, preserving its collision edit and authored offsets. All proposed commands operate on detached project copies; the saved browser fixture remains unchanged. No game was launched and no disc image was written.

The original MAP SHA256 is `60ecaa14978708f8696d60c12f6e98a88cdb19c2e63c7cae8f1c967a1214eb3b`. Source descriptor 194 is shared by decorations 01833 and 02089, uses model 0007, and has source yaw at byte 6218. Both cells already have offset overrides in the saved fixture. The individual 01833 quarter turn changes its allocated descriptor 5 yaw 64→1088; only byte 171 changes 0→4, leaving the counterpart and source descriptor intact. Its position remains `[5577,0,2048]` in source coordinates.

Placed object 00156 uses descriptor 218 and model 0017. Its shared yaw changes 2048→3072 at byte 6986; the encoded high byte at 6987 changes 8→12. A sequential proposal preserves the preceding individual yaw edit. A separate shared-decoration probe sets shared yaw 2112 while the individual remains 1088, independently showing that explicit cell yaw takes precedence while position and X/Z rotation are preserved.

The proof independently calculates matrices using expanded rotation products and compares them with the SDK's matrix builder. It also performs a fresh immutable-source allocation, verifies every copied descriptor byte except yaw, preserves the original descriptor and grid high flags, and checks that no bytes outside the allocated descriptor and selected grid word change. `fixture.json` records the exact entities, source record hashes, baseline/proposed matrices, and source provenance; the individual/shared JSON reports retain byte deltas and writer audits. Parent integration separately verifies actual pointer drags, Undo/Redo, Save/Open, and package bytes.

Integrated validation: ten focused Python cases (no skips), the Node rotation guard suite and frontend syntax checks passed. Twelve actual browser scenarios and an actor movement regression passed. Resize cancellation checks current canvas bounds and command-request counts, including pointer release before ResizeObserver delivery. Reopened normal Build/package readback changes exactly bytes171 (0→4) and6987 (8→12), preserving earlier Collision/offset authoring. Parent evidence is in the private `parent/` directory alongside research; no game or disc export ran.
