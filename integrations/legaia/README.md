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
