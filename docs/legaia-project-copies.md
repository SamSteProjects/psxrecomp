# Editable project copies

## Find and reopen saved copies

The Copy project panel also lists copies from the current project's
`ProjectCopies/` folder. Discovery works after restarting the editor. **Refresh
saved copies** rereads the list. Entries show the current saved name and whether
saved `project.legaia.json` bytes match the creation receipt or changed afterward.
An edited copy remains a normal editable project. These labels do not verify
current imported/model/texture files: normal validation runs on **Open saved copy**.
Creation receipts are local provenance records, not signed integrity certificates.

Missing/invalid receipts or unreadable metadata produce an explicit unavailable
row with no Open action. Save or Undo source changes before opening a listed copy.
Listing reads bounded metadata only, creates no projects and rewrites no files.
It scans at most4096 immediate directory entries, then shows up to64 matching
identities in lexicographic order with truncation indicated. This is not date or
recency order. Per-document metadata is limited to8 MiB; response size to2 MiB.
Copies whose source/destination paths differ from their creation records are
unavailable through this list; ordinary Open project remains separate.

**Discovery verification — 2026-10-01:** Twenty-eight focused retail-enabled Python
checks passed in4.058s, all26 Node files and27 syntax checks passed. New checks
cover fresh-service discovery, edited names/metadata, read-only behavior, malformed
or partial records, path/size/scan/mode/source guards, API whitelists and current
input validation on Open. Browser found matching/edited/incomplete copies from
disk, reopened Dolk2 X9536 with empty history, rejected a corrupted import, blocked
dirty Open before dispatch, withdrew a closed pending list and refreshed normally.
Original saved bytes/authored state were preserved, zero page errors, screenshots
inspected; owned browser/server stopped. No game launched. Private evidence:
`local-output/sdk-20260909/project-copy-history-20261001/`. This extension postdates
the integrated514 checkpoint; full SDK/runtime acceptance remains open.

## Create a copy

In Edit mode, choose **Copy project…** beside Settings. Review the captured input
count and size, enter a name, and choose **Create editable copy**. The copy captures
current authoring metadata, including unsaved changes. It does not Save the source
or replace its Undo/Redo history. The original remains the active project.

Copies use fresh project-local folders:
`ProjectCopies/project-<32-hex-UUID>/`. There is no arbitrary destination field.
The copy retains imported scene evidence, authored changes, NPC drafts, templates,
saved views/selections, active scene and referenced authored TIM/TMD files. The
retail disc path remains a reference; the disc itself, generated Build/export
outputs, runtime configuration, live samples and Undo/Redo history are excluded.
Unreferenced authored files are excluded as well. Model validation can require
reading the referenced retail disc; this operation does not launch a game.

Each input is hashed after writing. The service reopens the copied project through
normal validation and compares its full metadata to the captured document, then
recaptures the source to check for drift. Only after those checks does it write
`copy-report.json`. The report records creation-time provenance; editing the copy
can subsequently change its inputs. It is not an immutable export archive.

**Open copy** uses the ordinary project-open workflow. If the source is dirty,
Save or Undo its changes first. The created copy retains the inputs captured
before that Save/Undo. Alternatively, keep the displayed path and open it later.
The new project starts saved, with empty Undo/Redo history. Subsequent changes and
Save affect the copy independently.

Review binds full metadata and actual referenced file bytes. Changed names,
templates, views, active scene, overrides or file contents require a new review.
The service rejects Live mode, invalid names, extra API fields and symlink/reparse
output paths. Limits are 64 imported scenes, 512 captured files, 64 MiB per file
and 256 MiB total. Names allow 1–120 trimmed Unicode scalar characters; control
characters and lone surrogates reject. A failed/interrupted copy can leave a
partial folder without a completion report; it is retained for inspection.

## Verification — 2026-10-01

Thirty-nine focused Python checks passed in 3.628 seconds with retail gates
enabled, covering copy/history independence, project settings, export snapshots,
HTTP routes, model payloads, drafts, saved views/selections and byte/path/context
guards. All 26 Node test files and 27 editor syntax checks passed. A synthetic
model-source fixture independently exercises TMD payload copying; it is not a
claim of new retail model compatibility.

The retail-backed browser copied an unsaved Dolk2 actor0011 X9536 edit from a
project saved at X9472. Source bytes/history/dirty state remained unchanged;
opening was blocked before dispatch while dirty. After Undo, the copy opened
with X9536 and an empty history, then edited/saved independently at X9600.
Reopening the original restored X9472 with identical saved bytes. Unicode names,
API field guards and zero page errors were verified; screenshots were inspected.
Owned test browser/server stopped. No game launched or controlled.

Private evidence: `local-output/sdk-20260909/project-copy-20261001/`, including
Python/Node logs, browser checks, copied project and screenshots. Initial fixture
assertions used an incorrect override shape and a one-actor selection; corrected
tests passed without weakening production validators. This feature postdates
the integrated 498-test checkpoint. Full SDK/runtime acceptance remains open.

A subsequent integrated pass on clean committed source `7a6459e4` passed514
Python tests in365.743s with no skips,26 Node test files and27 editor syntax checks.
This includes project copies; it does not add gameplay or native runtime acceptance.

## Retained mesh and texture sources - 2026-10-06

Editable copies and saved export input snapshots now include original GLBs
referenced by Current model import receipts. Hash-named files under
`Authored/Models/Sources` are qualified and copied with the native TMD and ledger.
Shared originals appear once in the captured inventory. Retained texture PNGs
and GLBs are also accepted by the editor copy inventory and saved-copy discovery.
The existing 512-file/256-MiB copy limits include these inputs.

Open the copied project, choose **Import GLB mesh > Retained mesh sources**, and
download the same original GLBs and settings. Missing or changed sources reject
copy review/creation before a completed copy is published. Unreferenced files
and inputs reachable only through excluded Undo/Redo history are not copied.
Review and Copy still preserve the original project's metadata, dirty state and
history. Retained original inputs remain project sources, not runtime Build
assets. Older snapshots created without mesh sources are not repaired implicitly.

The same capture routine serves export input snapshots and editable recovery
copies. Synthetic snapshot/recovery checks do not generate a retail disc export.
