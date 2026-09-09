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
