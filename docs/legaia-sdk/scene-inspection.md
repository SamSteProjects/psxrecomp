# Assembled scene inspection

Import town01 into a project and allow the scene preview to finish loading.
The viewport combines actors, placed environment objects, field decorations,
and a textured ground surface. The hierarchy includes these environment
instances alongside the project's actors.

Select scenery directly in the viewport or search its name in the hierarchy.
The inspector shows its source transform and model. A dashed gold box marks
the selected mesh bounds; Frame object centers the camera on it. The box is
an inspection overlay, not collision geometry.

Actors, Scenery, and Ground buttons control viewport visibility. Frame all
uses the visible layers. Hidden geometry cannot intercept mesh picking.
The preview badge reports loaded and visible mesh counts separately.
Visibility controls do not change project or runtime data.

Repeated scenery can share one MAP descriptor. The Shared placement record
section lists the imported instances using that descriptor; choosing another
instance selects and frames it. The count covers imported scene instances,
not every possible runtime or grid reference. Source offsets and rotations
belong to the shared descriptor. Environment transform authoring and
independent instance overrides are not yet implemented.

## Verified workflows

On 2026-09-10, an isolated town01 editor loaded 261 instances with 260 meshes:
52 actors (51 renderable), 46 placed objects, 162 decorations and one ground
surface. Directly clicking house137 selected its environment identity. Hiding
Scenery and clicking the same point selected the ground. Hiding all three
layers left the editor grid. The selected house's bounds and label disappeared
with its layer. Switching between the two decoration194 instances updated
the hierarchy, inspector transform, camera and selection bounds.

town0c also resolved and decoded 162 decorations in a source-catalog check.
This does not establish town0c browser parity. The specific case of an actor
marker occluded by scenery has not been independently reproduced after the
mesh-first picking change.

## Fidelity limits

Mesh pool selection follows the pinned reference's largest scene-entry
heuristic, which is exposed as inferred evidence. Prop animation uses its
initial source frame; scripts and runtime visibility are not evaluated.
Actor heights and headings retain their existing unresolved conventions.
Ground uses the source floor-LUT heightfield; it is not a complete recreation
of the retail ground emitter. Complete scene parity, animated palettes,
exact PSX blending, world-map assembly and scenery editing remain unfinished.

Scene responses can finish after their browser tab closes. Connection and
timeout failures during response writes close that connection without a
second HTTP error response. This does not cancel an already-running operation.
