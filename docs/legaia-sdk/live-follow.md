# Following runtime actors

Use **Attach** for an owned run, enter **Live** mode, then choose **Follow live**
in the Runtime controls. Following is explicit and is not saved with the project.
The editor requests one bounded actor observation at a time, waiting two seconds
after each response before the next request.

Every subsequent capture supplies the last accepted epoch ID. The observer
checks its guard before traversing actors. Restore, scene changes, stale guards,
backwards frame counters and unavailable transport stop following; the editor
does not silently attach again or retry a rejected capture. Entering Edit mode,
changing project or scene, stopping the run, or hiding/leaving the page also
stops following. After rejection or transport loss, check the runtime before
resuming. Manual Stop can be resumed explicitly with **Follow live**.

Each explicit start establishes a fresh, fully guarded actor capture. It does
not reuse a cached browser epoch: a cancelled request may have completed on the
server after its response was discarded. Subsequent polls chain the new epoch.
This allows explicit restart without silently retrying a rejected capture.

The selected actor's observed candidate positions appear separately from its
authored placement. They are sampled, read-only candidates, not confirmed
identity bindings. Imported data, authored transforms and model placement stay
unchanged. Candidate markers are unavailable when the observation is rejected
or no matching epoch is accepted.

Following is not a guest execution controller or a runtime edit. Its capture
latency depends on the existing bounded traversal and binding checks, so it is
not a fixed-rate animation preview. It does not make missing entry witnesses
current; after a lifecycle reset, the required instructions must execute again.

Browser acceptance against one restored town01 run covered repeated captures,
the selected actor0052 candidate marker, manual Stop, unchanged capture state
four seconds after Stop, restart after cancelling a capture, and Edit-mode
cancellation. Runtime-stop acceptance also cleared observations and disabled
Live/follow controls, with no browser console errors. The restart check exposed
and corrected cached-epoch reuse.
Private controller checks are rerunnable with Node using
`local-output/sdk-20260909/test_editor_follow_live.cjs`; they cover failure,
serialization, cancellation and marker eligibility without simulating visuals.
