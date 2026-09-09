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
placement record. A project coordinate edit is not yet a playable game patch.

The read-only runtime adapter accepts `--runtime-port` (default 4370). Runtime
discovery must negotiate the required identity and observation guard protocol;
the current runtime may report unavailable until that protocol is ported.
No editor route writes live RAM. See the repository's `docs/FEATURE_MATRIX.md`
for exact subsystem status and `docs/legaia-release-parity.md` for runtime checks.
