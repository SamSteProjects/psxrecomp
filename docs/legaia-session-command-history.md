# Session Command History

Open **History…** beside Undo/Redo to inspect the SDK's current session records. This view is read-only and does not require a running game.

Applied records appear newest first; undone records follow in next-Redo-first order. **Previous page**, **Next page**, and **Refresh** browse up to 50 records per page. Select a record to inspect its exact stored metadata, including `before` and `after`. Stack positions identify records within the current stacks; they are not permanent command identities.

The SDK reports recorded target and owner fields. Older actor records have no explicit target; the view says **Target not recorded**. Existing records generally have no command name, timestamp, or author, so the inspector does not invent them. Collection and batch records retain their actual stored structure rather than a guessed operation description.

Undo/Redo remain the existing project commands outside this inspector. Inspection requires a source key bound to the current project document, saved metadata identity, and both stacks, plus the selected record's stack position and digest. A changed project or stack refuses the old selector and requests Refresh. The inspector provides no restore, jump, replay, or runtime-write action.

Save keeps the in-memory session history. Opening/reopening a project starts new empty history: these stacks are not persistent history or collaboration records. The inspection API does not read retained asset payloads or guest memory. Pages and individual record responses exceeding 8 MiB are explicitly refused, without silently trimming metadata.

## Offline Checks

Focused Python checks cover exact detached records, normal actor command/Undo/Redo, Save/Open, pagination, unknown target metadata, malformed selectors, and oversized-record refusal. Node checks cover strict report/detail decoding and detached metadata.

Actual private Town01 editor checks at 1440 and 400 px used 52 normal project-rename commands to exercise pagination, exact before/after inspection, stale refusal after Undo, Refresh, and return through Redo. The record list scrolls independently so selected metadata remains visible. HTTP checks refused extra fields and invalid offsets/selectors; no page errors or Run requests occurred. The prepared project document, history stacks, and saved files remained unchanged after the checks. The owned test server and browser were closed.

Evidence: `local-output/sdk-20260909/command-history-20261007/` contains the private fixture proof, browser report, screenshots, and read-only checks. No game launched, native Build, installation, or disc export occurred. Gameplay verification and the full SDK goal remain outstanding.
