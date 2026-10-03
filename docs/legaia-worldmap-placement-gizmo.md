# World source placement translation handles

In **World placements**, inspect a kingdom, select a record or click a source
mesh, and enable **Translate source record**. For a shared record, explicitly
check **Edit every cell using this shared record** first. **Frame anchor** centers
the selected source instance's record origin; **Frame record** still fits every
affected instance.

Drag the colored X/Y/Z line or endpoint. The snap menu offers 1, 16, 64 or 128
source units. These handles edit signed16 record offsets, not absolute positions.
Source X moves viewport +X, source Y moves viewport -Y, and source Z moves
viewport -Z. Yaw is preserved. The Inspector and every instance sharing the
record update together in a temporary preview.

Releasing retains the numeric draft. **Review transform** qualifies the exact
source proposal; **Apply reviewed transform** alone records one normal authoring
command and one Undo step. Unreviewed drafts cannot be exported as Proposed.
Choosing Current hides the draft and disables translation until its preview is
restored. Discard returns to applied source values. Save/history remain blocked
while a draft is pending.

Escape cancels the current drag without closing the inspector. Pointer
cancellation, lost capture, focus loss, hidden page, source/mode changes, camera
input, changed snap/tool and viewport layout changes also cancel the gesture.
Cancellation restores the preceding numeric draft, comparison state, dirty flag
and review. Source invalidation withdraws the inspector. The projected axis and
source-unit scale are frozen for each drag; nearly edge-on axes require orbiting
or framing, and signed16 overflow rejects the attempted update.

These are qualified source spawn seeds. They do not prove native visibility,
resting position, scripted initialization or collision. No game is launched by
the tool. Normal persistence, Build and Current/Proposed GLB exports use the
existing source-bound WorldMapPlacements service.

## Offline evidence — 2026-10-02

Two Node suites pass source-direction, independent matrix arithmetic, projected
delta, signed absolute snapping, bounds and ownership checks. Fourteen Python
regression cases pass with private retail input and no skips. Fifteen actual
browser checks pass: explicit shared-scope gating; nonzero X/Y/Z pointer drags
against independent arithmetic for all 57 affected instances; Escape, focus,
resize and reviewed-draft restoration; 540px controls; exactly one reviewed
Apply; stale-source withdrawal; pointercancel and lost capture restoration;
Undo/Redo with Save/reload; and normal Build. No game requests or page errors
occurred in the passing runs. Screenshots were inspected at desktop and 540px.

The Apply/reopen proof also exposed and fixed a dialog-close race: cancellation
now clears the global busy flag only when the dialog owns the cancelled request,
so it cannot unlock another command while that command is still running.

The final private fixture has map01 record0477 offsets X1280/Y256/Z256 and
yaw1536. Independent reconstruction and complete 73728-byte package readback
agree exactly. Only retail MAP bytes15265,15267,15269 and15275 differ. The source
cells, anchors, selectors, flags, other record bytes and source identity remain
exact; the feature is disabled by default.

Package SHA256: `d15d8464e9486a9463dac0b5653e1005aadd9fa942c13e11ebf95fee8d28b6b7`.
Candidate MAP SHA256: `c50f59209004bfdde04ad531363d670cb84abfbe77026646b1a11f5256dc0be3`.
Private evidence: `local-output/sdk-20260909/worldmap-placement-gizmo-20261002/parent/`.
The owned helper and browser processes are closed. Gameplay remains deferred.
