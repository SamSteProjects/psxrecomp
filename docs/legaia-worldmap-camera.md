# Numeric World Camera Inspector

Choose **World ground** → a kingdom → **Inspect kingdom** → **Camera coordinates**. The shared camera inspector exposes target X/Y/Z, distance, yaw/pitch in degrees, and Perspective/Orthographic projection. **Set viewport camera** changes only the editor display. Use **Saved world views** to retain the resulting camera in the project.

Target coordinates are editor display coordinates: source X/Z are retained, and native Y-down coordinates are reflected once for display. Camera targets do not identify an actor position, guest address, or observed runtime transform. The World viewport retains its existing orientation/basis; numeric controls do not convert it into the field viewport's basis.

Decimal and scientific notation are supported. Empty values, hexadecimal, nonfinite numbers and out-of-range values are refused. World targets are bounded to ±100,000,000, distance to 10–1,000,000, and entered yaw to ±360 degrees. Perspective pitch spans 0.05 radians (about 2.86479 degrees) through 90 degrees; Orthographic permits 0–90 degrees. The exact minimum is retained through degree conversion. Displayed yaw is normalized to ±180 degrees.

Changing the camera, source kingdom, project source key or displayed placement layer invalidates an open draft. **Read current camera** refreshes it. Source withdrawal closes the inspector. Existing field camera defaults remain independent: target ±1e12, distance 20–1e8, and perspective minimum 0.12 radians.

## Offline Checks — 2026-10-10

Two focused Node suites verify existing field behavior and World bounds, exact minimum pitch, projection/degree conversion, detached state and invalid decimal/profile refusal. Two JavaScript syntax checks pass.

Actual browser workflows use all three native kingdoms. Numeric targets/distance/angles match the real World renderer camera exactly, including Orthographic pitch zero and the Perspective minimum. Invalid entries leave the camera unchanged. A changed camera invalidates the draft; Read current restores availability. Saved-view Replace/Recall and Save/Open retain exact numeric cameras; reopening and recalling map01 confirms renderer restoration. Changing the kingdom closes the inspector. The active field scene and selection remain unchanged.

An additional actual field inspector workflow confirms the unchanged distance-20 and 0.12-radian minimums and rejects the smaller World limits. Desktop and 400px World dialogs were inspected without clipping; no page errors occurred. Private evidence: `local-output/sdk-20260909/worldmap-camera-20261009/`. Only explicitly replaced saved-view metadata changes; the full project document excluding saved views, imported/authored inputs, authored Build identity and all other fixture files remain unchanged. No Build, game, runtime attachment, installation or disc export ran. Gameplay verification remains deferred; the full SDK goal remains active.
