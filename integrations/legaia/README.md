# Legaia Trace SDK

Local scene import and project authoring around PSXRecomp. Requires Python 3.11+
and a user-owned North American SCUS-94254 Mode 2/2352 disc image for retail import.
No runtime dependency on Andrew's repository and no retail assets are included.

From the framework repository root:

```powershell
python integrations/legaia/tools/legaia_editor.py --project local-output/my-legaia-project
```

Open the printed loopback URL. Import the disc with scene `town01` or another
supported scene. Select an actor in the hierarchy or viewport, edit an authored
coordinate in the inspector or drag an X/Z handle, then Save. Undo/redo affects
authored values. Opening the same project restores edits and checks imported
evidence digests. Keep project output under ignored `local-output/`.

The viewport distinguishes placement markers from decoded model previews.
Retail height and initial facing remain unknown when not established by the
placement record. Build exports a private `.psxmod` for supported X/Z placement
edits. The retail encoding accepts multiples of 64 from 64 through 16384;
height edits and unsupported properties fail explicitly. Recompressed MAN data
must fit its original verified span. Import the package in the runtime mod
manager and enable its Authored actor placements feature to play with it.
The builder preserves the stock disc and reports an audit beside the package.
Export and successful boot do not prove a particular actor survives later
script-driven placement changes; verify the resulting scene in the game.

The read-only runtime adapter accepts `--runtime-port` (default 4370). Runtime
discovery must negotiate the required identity and observation guard protocol;
field observation reports unavailable unless the profile's execution witnesses
and scene guards actually match the running game.
No editor route writes live RAM. See the repository's `docs/FEATURE_MATRIX.md`
for exact subsystem status and `docs/legaia-release-parity.md` for runtime checks.

## Inspecting and exporting animation

Select an actor, then use **Preview imported scene animation** for its supported
MAN assignment, or **Preview reference animation** for a supported shared-model
clip. Scrub the clip in the model dialog. **Inspect animation in scene** isolates
that actor's preview geometry and adds a scene frame slider, play/pause, and a
chosen preview rate. **Restore scene pose** removes the temporary inspection;
these controls do not author actor positions or animation channels.

**Export GLB** retains its single-frame/static-model behavior. For a complete
loaded clip, set **Export fps** and choose **Export full clip GLB**. The private
file is written beneath the project's `Exports` directory. It contains
independent rigid-object translation/rotation tracks with step interpolation,
embedded supported textures, and source provenance. Untracked trailing objects
remain excluded. The final decoded frame is held for one selected frame interval;
the receiving application controls looping. Export fps is a user choice, not
verified retail cadence. Source units remain unchanged apart from the documented
Y-axis conversion; no physical-meter scale or anatomical skin hierarchy is inferred.

As of 2026-09-12, a browser-exported 30-frame actor clip passed Khronos glTF
validation with zero errors/warnings and imported through glTF-Transform 4.5.0
with all 20 channels intact. This establishes file conformance and independent
import, not rendered playback acceptance in Blender/Unity or gameplay parity.

## Inspecting runtime positions

Use Check runtime, enter Live mode, then Observe actors. Runtime positions toggles
cyan markers for accepted sampled nodes, including nodes behind scenery. These
are captured coordinates, not confirmed NPC identities or live replacement meshes.
Follow live refreshes observations through the existing guarded observer.

Observed nodes lists captured XYZ and position-read frame intervals independently
of imported actor matches. Filter by node ID, coordinates, or candidate ID; Frame
node moves only the editor camera. Inspect candidate opens the entity inspector,
which keeps imported, authored and observed values separate and distinguishes
position-read timing from later binding evidence. Refresh captured list uses the
latest sample already held by the editor; Observe actors obtains a new sample.

Enable Pick runtime node and click a cyan marker to inspect nearby sampled nodes,
including overlapping hits. This path was verified in-browser with 31 stacked nodes.
Turn picking off for normal scene-mesh selection. Alt-click is an additional
shortcut; modifier-based browser acceptance remains pending.
Markers are suppressed outside Live mode or when accepted epoch evidence is lost.
No runtime position control writes game RAM or modifies authored transforms.

### Export an assembled scene

After the scene preview finishes loading, choose **Export scene GLB** in the viewport toolbar. The export uses the selected authored or retail representation and includes temporarily hidden instances. Restore any temporary animation inspection pose first. Files are saved with unique names in the project Exports folder. Shared geometry, instance transforms and source provenance are preserved; unavailable instances remain metadata-only nodes. This is a static source-preview export, not captured gameplay, exact PSX lighting/blending, or a physically scaled scene. External rendered consumer acceptance remains pending.

Use **Export selected GLB** to export one selected actor, NPC draft, scenery instance or ground surface with its scene placement retained. The selected representation still applies. Unsupported instances without geometry cannot be exported individually.


## Compare script movement targets

Select an actor and open **Inspect script and dialogue**, then expand **Instruction
paths**. Choose the retail or authored **Script target layer**, enter a **Reference Y** and
choose **Show targets in scene**. The viewport labels each source instruction's
PC and X/Z; **Top (X/Z)** helps compare placement. **Frame script targets** restores
the overview and **Clear script targets** removes the overlay.

The same controls appear for supported partition-2 script reports. The reference
height is supplied by you because these instructions do not establish Y. Parked
targets and unresolved actor contexts remain explicit. Markers do not change the
project, prove branch execution, or represent current NPC positions. Changes to
the project/scene source invalidate the overlay. At most 256 targets are shown;
larger reports retain individual instruction locators.

Choose an instruction in the overlay toolbar and click **Inspect target** to
reopen its verified source report at that offset. Alternatively enable **Pick
script target** and click a marker or its label. Dragging still controls the
camera, but actor transform handles are inactive in this picking mode. If targets
overlap, choose the instruction explicitly from the selector. Clear removes the
overlay and restores ordinary viewport selection.


## Author script movement targets

Open **Inspect script and dialogue** and find **Script movement targets** below
the source report. Supported instructions expose retail, authored and effective
X/Z. Enter exact 64-unit coordinates from 64 through 16384, then **Apply movement**.
Use **Discard movement draft** for unapplied input, **Clear movement override**
to restore the retail target, and the script toolbar for Undo/Redo and Save.

Build packages these edits for supported descriptor MAN scenes such as town01.
Experimental **Export disc** also supports streaming scenes and appended NPCs.
Gameplay behavior is unverified. The instruction table displays retail source
coordinates; the viewport offers retail and authored effective target layers.
Authored preview requires a complete verified movement report with no unresolved
overrides. Y, executed branches and
runtime actor identity remain unresolved.


## Move placed scenery

Select a placed scenery object in the authored viewport, then choose **Enable
shared move handles** in its Inspector. Drag X or Z to edit the shared placement
record; every use of that record receives the change. The Inspector lists related
instances and the source reference count. Undo restores the edit. Enable the
handles again after the project changes. Decoration handles continue to create
individual overrides. Runtime visibility and gameplay behavior remain unverified.


Hierarchy search also matches authored change types such as **Script movement**,
**Transitions**, **Dialogue**, and **Position**. Hover an actor's authored badge to
see its changed components, then select the actor to inspect the corresponding
retail and authored values.


Shape OBJ imports preserve source vertex order and oriented triangle topology.
Equivalent face reordering, cyclic corner order and relative vertex indices are
accepted. Reversed winding, missing/duplicate triangles and changed vertex counts
are rejected. Only vertex positions are imported; source materials and normals
remain unchanged.


In **Author animation channels**, copy a verified retail or effective channel,
select another frame of the same rigid object, and choose **Paste channel into
draft**. Paste fills translation and rotation axes; **Apply channel override**
creates the project edit. Discard removes unapplied input. Clipboard contents
last only for the current dialog and do not retarget between objects. Shared
clip users are affected when the override is applied and built.


To repeat a copied animation channel, enter **First target frame** and **Last
target frame**, then **Apply copied channel to frame range**. Both endpoints are
included. This replaces the selected object's six values in those frames as one
Undo step, retaining other frames and objects. It repeats a pose without
interpolation; shared-clip effects still apply.


## Animation record interchange

Open **Author animation channels**, choose **Download retail animation record**,
then select a replacement `.anm`/`.bin` and click **Import animation record**.
The record must retain source length, frame/object counts and opaque bytes.
Only existing translation/rotation channel values are writable. Import replaces
this actor's contribution; a retail-identical record clears it. Other shared
contributors remain, and conflicting values reject. Undo restores the prior
contribution; Save persists a successful import. This is a raw game record,
not a general Blender/Unity animation import format.


**Download effective animation record** exports the composed shared clip with
applied contributions. **Download retail animation record** keeps the original
bytes. Both retain the same source binding; effective export can include other
actors' shared-clip contributions. Importing that file assigns its differences
from retail to the selected actor, subject to conflict checks.


For readable values, choose **Editable channel JSON (.json)** in **Animation
interchange format** before downloading or importing. The document contains
`legaia.animation-channels.v1`, the retail `source_record_sha256`, unchanged
`frame_count`/`object_count`, and every channel's zero-based `frame_index` and
`object_index`. Each channel requires complete `translation` and `rotation_psx`
XYZ objects. Translation uses signed 12-bit source units (-2048..2047); rotation
uses 0..4080 in steps of 16. No unit conversion, resampling or retargeting occurs.
Effective JSON contains composed values but retains the retail source hash.
Missing/duplicate channels or keys, incomplete axes, changed layout, stale source
hashes and out-of-range values reject before a project command is applied.
The interchange budget is 4096 channels and 4 MiB. Save preserves the resulting
ordinary channel overrides; reopening does not require the imported JSON file.


**Preview animation file** checks the selected file without applying a command.
It reports proposed differences from retail, whether import would replace or
clear this actor's contribution, and validates composition with other shared-clip
contributors. The Inspector shows up to 256 axis rows with a total count.
Preview does not save or change Undo history. Import remains a separate action
and revalidates the current file and project; a preview is not runtime acceptance.


**Inspect file animation** opens the selected file as a proposed clip in the
model viewer without importing it. Scrub or play its frames, or choose **Inspect
animation in scene** to isolate the proposed pose on the selected actor. The
scene labels it **Proposed file · not applied**; **Restore scene pose** restores
the assembled project preview. This inspection changes no project overrides or
history. It previews composed shared contributions on one instance; other clip
users are not simultaneously animated. Import the file before exporting an
applied animation. Diagnostic offsets can visibly separate rigid objects and do
not establish a suitable animation or verified runtime cadence.


While inspecting a proposed file in the scene, **Return to animation file**
restores the scene and reopens the original file form with its selection and
format intact. You can then import explicitly. Returning requires the same
actor/project context and unchanged file selection; otherwise reopen authoring
and select the file again. Ordinary imported/applied clip inspection does not
show this action.


## Model vertex and normal JSON

The model viewer offers **Download source JSON** and **Download authored JSON**.
Choose an edited `.json` in the shape file input and use **Apply shape**. JSON
retains `legaia.model-shape.v1`, the retail `source_sha256`, original coordinate
convention, and every ordered object with complete vertex/normal arrays. Values
are signed16 source words; the tool performs no normal normalization or unit
conversion. Authored download keeps the retail binding and includes current
edited vectors. Import replaces the complete shape through ordinary model
history/persistence; missing objects/vectors and stale hashes reject. Topology,
materials and padding remain unchanged. OBJ still edits positions only.


Model build-report rows retain the before/after TMD hashes and an expandable
vertex/normal axis audit. It identifies each changed object, vector, axis and
source-word value. The viewer shows up to256 scalar rows per model; the complete
build audit retains all changes. These are emitted package changes, not merely
unsaved editor intentions.


Click a model identity in the build report to open its authored model preview.
The source and authored hashes must still match the report. If the shape changed
or was cleared after the build, rebuild before using this link to inspect it.


The current WebGL model/scene preview uses decoded colors and textures, without
normal-based lighting. Normal-only JSON edits can therefore package correctly
without changing the browser image. Use the scalar build audit to verify changed
normal words; runtime lighting acceptance remains a separate deferred check.
