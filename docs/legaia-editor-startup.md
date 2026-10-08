# Editor Startup Recovery

The editor now separates loading its modules from connecting to the local project service. The workspace remains inert until both complete. A small startup view shows the active phase and provides explicit recovery if loading fails.

Module loading has a 45-second default deadline. The initial read-only `GET /api/state` has a separate 30-second deadline and AbortSignal. Timeout or failure shows the actual bounded error. A connection failure offers **Retry connection** and **Reload editor**; failed module loading offers Reload. A static Reload link remains usable if the bootstrap script itself cannot load.

There is no automatic retry, reload, project opening, runtime connection or game launch. Retry reuses the loaded editor module and requests only initial project state. It is enabled after the prior connection attempt settles, preserving the existing API busy gate. A cancelled response cannot publish state after JSON decoding, and late module completion after a timeout cannot initiate the state request. Page departure disposes startup ownership.

The main editor now exports `initializeEditor` instead of initiating state loading while the rest of its services are still mounting. The bootstrap calls that entry after the complete module is available. Successful startup hides the recovery view and releases workspace interaction. This changes no project schema, authored data, native Build inputs or runtime protocol.

## Verification

The focused Node suite covers module/state phases, explicit serialized retry, both deadlines, cancellation, late-reply ownership, invalid configuration, interaction gating and recovery controls. Four existing HTTP template/appearance regression cases, both affected JS syntax checks and the server AST passed.

Private browser evidence under `local-output/sdk-20260909/editor-reload-20261007/qualified-fallback/` passed six scenarios: healthy startup plus three full-page reloads; state HTTP failure and explicit retry without reimporting the editor; held state request timeout/cancellation and retry; dependency failure and explicit reload; module timeout followed by late completion without state publication and explicit reload; and a missing bootstrap script recovered through the static link. Fault deadlines were shortened in the browser fixture to 500 ms for module loading and 2 seconds for connection; healthy loads used the production defaults. Wide and 400-pixel recovery views were visually inspected. Complete project document/history/files/native Build key stayed unchanged and Open matched. No unexpected page errors or command/Build/Run requests occurred; helpers terminated.

The earlier spontaneous reload stall did not reproduce in the instrumented baseline diagnostic (`diagnostic/`, before this change). Its root cause remains unproven. This milestone establishes observable, bounded startup recovery and repeated healthy reloads; it does not claim to have fixed that unknown cause. The initial browser harness also expected a desktop-only resource button to remain visible at 400 pixels; that failure is retained under `startup/`, with the corrected readiness check in later evidence.

No native Build or game ran. Gameplay, general runtime identity and the rest of the SDK goal remain unfinished; solo development continues.
