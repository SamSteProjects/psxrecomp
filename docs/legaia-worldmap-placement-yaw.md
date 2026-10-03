# World source yaw rotation ring

In **World placements**, inspect a kingdom, select a source record or mesh, then
enable **Rotate source yaw**. Translation and rotation tools are mutually
exclusive. Shared records still require **Edit every cell using this shared
record**. **Frame anchor** centers the selected record origin.

Drag the yellow ring or its heading endpoint. The yaw snap menu supports 1, 16,
64, 256, 512 or 1024 encoded units; a full turn is 4096 units. The endpoint shows
the source rotation of local +X toward -Z. This is an encoded object-record yaw,
not a claim about native actor heading or runtime orientation.

The ring solves pointer coordinates on a frozen horizontal source plane using
the viewport's homogeneous projection. Perspective is retained. Consecutive
angles unwrap across the atan2 seam, offsets remain unchanged, and the resulting
absolute yaw is snapped and wrapped into 0..4095. All source instances sharing
the record preview the same yaw. Nearly edge-on, center or behind-camera input
rejects without introducing an invalid draft.

Release retains a numeric draft. Review checks source ownership and the exact
candidate; Apply alone creates one normal WorldMapPlacements command/Undo step.
Current comparison disables manipulation of a hidden draft. Re-enabling the
tool restores a valid numeric draft preview. Escape, pointercancel, lost capture,
focus/visibility loss and changed source/camera/viewport/tool/snap context cancel
the gesture and restore the preceding values, dirty state and review. Save and
history retain the existing pending-draft guard.

Persistence, normal Build and reviewed Current/Proposed GLB exports use the
existing world placement service. No new retail serializer or runtime writer is
introduced. Source cells, model selectors, anchors, flags, other rotation axes
and opaque record bytes remain preserved. Script-driven visibility, resting
positions, collision and native gameplay behavior remain unverified.

## Offline evidence — 2026-10-02

Three focused Node suites pass yaw direction/wrapping, snapping, finite bounds,
offset preservation, independent orthographic/perspective plane inversion,
translation and existing source/review/matrix guards. Two Python source-package
regression cases pass with private retail input and no skips.

Seventeen actual browser checks pass: exclusive tools and shared scope;
positive 90° and negative 180° drags; source yaw3968 wrapping to448; independent
rotation-matrix and unchanged-position checks for all57 shared instances;
Escape and resize restoration; Current comparison gating; retained review
restoration;540px controls; one reviewed Apply; Undo/Redo and Save/reload;
normal Build; stale-source withdrawal; yaw pointercancel/lost capture/blur; and
translation after tool switching. No game requests or page errors occurred in
the main proof; the cancellation regression submitted no commands. Desktop and
narrow screenshots were visually inspected.

The final fixture retains X1280/Y256/Z256 and changes yaw to448. Independent
reconstruction matches the full73728-byte MAP package payload. Against retail,
bytes15265/15267/15269 retain the prior offset edits, and yaw bytes15274/15275
change; every other byte remains exact. The package feature remains disabled by
default. No game, install or disc export ran, and the owned helper is closed.

Package SHA256: `4a953cf8acfb12105dd121b7c3f6416f9469bfa00907ef4c2999d4e9bc9de6bf`.
Candidate MAP SHA256: `4a9b87e1d2c3db757654500573474c9e854499ee4b25a1e064042692da74481f`.
Private evidence: `local-output/sdk-20260909/worldmap-placement-yaw-20261002/parent/`.
