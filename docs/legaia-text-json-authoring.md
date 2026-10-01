# Source-bound dialogue and menu text files

Open a supported actor or partition-two script's **Script and dialogue**
Inspector in Edit mode. Apply or discard existing form drafts first. Use
**Download text JSON**, edit the file outside the editor, then use
**Inspect text JSON file**. Review the before/proposed/effective text for each
changed run and explicitly **Apply text file**. Close leaves the project alone.
All file changes form one Undo step. Save/Open and Build use the existing
Dialogue component and source-preserving MAN serializer.

The UTF-8 JSON schema is `legaia.text-runs.v1`. Keep every exported run and all
fields. Edit only each run's `text`: a printable ASCII string supplies an
override; `null` clears it and inherits retail. An empty string becomes spaces.
Do not change `run_id`, `byte_length`, `retail_text`, owner, MAN hash or authored
state hash. Order may change but the complete collection must remain unique.
Controls/substitutions are outside editable runs. Caret, newlines, non-ASCII,
longer text, relocation and branch/control editing remain unsupported.

The file is bound to the verified retail MAN and the owner's current text
overrides. After those overrides change, download a fresh file and carry your
edits forward. Other component edits do not invalidate the text snapshot;
imports preserve them. Unsupported or unresolved saved runs block export.
No-op files create no history entry and cannot be applied from the preview.

Files are capped at1MiB. Unknown fields, duplicate JSON keys/runs, non-finite
values, missing runs, stale source/state, changed immutable metadata and invalid
glyph spans are rejected before any project/history mutation. Import is Edit
mode only. Closing during a pending read withdraws the preview. The file input
is disabled during inspection to avoid overlapping reads. The import rechecks
bindings even after a successful preview.

## Evidence — 2026-09-30

Six focused text/project tests passed (including two new text-file tests),
plus existing Node operand checks and editor syntax. Tests cover preview/no-op,
atomic multi-run history, null clearing, unrelated Transform preservation,
Save/Open, stale files, metadata/capacity/type mismatches, duplicates, malformed
JSON, oversized files and mode rejection.

Retail town01 actor0001 exported30 supported menu runs. A file changed two
labels while retaining the prior override. Browser export/no-op/preview,
immutable-field rejection, a larger-than32KiB HTTP request, Apply/Undo/Redo/Save
and stale import rejection passed with no page errors. Oversized and closed
pending-read checks sent no preview/import request and left state unchanged.
The final preview screenshot and article bounds were inspected.

Private project/evidence: `local-output/sdk-20260909/text-json-project-20260930/`.
The saved project reopened with three authored runs. Independent ZIP/LZS
package readback matched the expected MAN exactly. Package SHA256:
`86a89fd5deff5ce9bbf113fce26c864085481604831bfd9b32a731db8c975bd4`.
The current392-test full-suite checkpoint predates this workflow. No game was
launched. Source-menu reachability, font/layout and selection behavior remain
unverified; this file workflow does not execute script or pager controls.


Fresh regression update:397 retail-enabled Python discovery tests passed in
164.669s, with no skips, against unchanged source`e1b88c22` on2026-09-30.
This supersedes the older392-test checkpoint noted above and includes the menu
and text-file services. Browser/package/gameplay evidence remains separate.
