# Review Unsaved Project Changes

Open **Changes…** near Save to review project metadata against this session's last successful Save/Open snapshot. Select a record to see its exact **Saved** and **Current** values. Missing values are explicitly distinct from stored JSON `null`. Collection records are grouped by their actual stable owner keys; other document fields are compared as complete values. Source references can be compared, but retail payloads, retained asset payload bytes, generated output, live state, and unapplied tool drafts are not part of this metadata comparison.

The view lists Added, Removed, and Modified records, with 50 per page. Refresh reloads the current comparison; controls and record buttons wait for pending requests. Long owner IDs wrap on narrow displays. **Save reviewed changes** saves all current project metadata, including records on other pages, through the normal validated atomic Save path. It does not selectively apply a record, revert edits, replace imported provenance, or write runtime memory.

Inspection binds to the project path, exact current document digest, saved snapshot identity, record section/owner, and exact saved/current record digest. Reviewed Save checks that the complete current document and saved baseline still match the review before writing. If another command or Save changes that state, Refresh is required. Existing save validation still checks retained inputs and authored collections. The baseline is the in-memory last Save/Open snapshot, not a fresh comparison with externally modified project files.

Save replaces the saved snapshot and keeps Undo/Redo history. Undo after Save therefore exposes a new saved/current difference and marks the project dirty; Redo back to the saved document clears it. Opening a project starts with a clean snapshot. A new unsaved project explicitly has no saved snapshot. The snapshot is session-only and adds no fields to `project.legaia.json` or native Build formats.

The comparison refuses more than 16,384 records, invalid page offsets, mismatched selectors, and pages/details above 8 MiB rather than trimming data. Canonical JSON comparisons retain type distinctions. Retained model and animation source collections now also participate in the editor's unsaved-section labels; they previously affected the overall dirty flag without being named.

## Offline Verification

Six focused Python cases cover exact detached saved/current metadata, ordinary actor edits and reviewed Save, stale refusal without writing, retained-source dirty labels, pagination, missing/null values, type distinctions, snapshot identity, size limits, and Save/Open/history behavior. Related project/history checks and strict Node decoders exercise integration and forged response refusal.

Actual private Town01 editor checks exercise saved/current inspection at desktop and 400 px widths, stale Save refusal without modifying the saved file, Refresh and successful reviewed Save, clean-state review, and exact Undo/Redo against the newly saved baseline. Original imported metadata and retained files remain unchanged. No native Build, game, installation, or disc export is needed for this project workflow; gameplay verification and the broad SDK goal remain deferred.

Evidence is retained privately in `local-output/sdk-20260909/project-changes-20261007/`, including prior attempts. Only the successful final proof qualifies the final implementation. The session-history inspector also receives the long-ID wrapping correction and its own private browser regression.
