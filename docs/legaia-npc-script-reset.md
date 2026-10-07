# Reviewed NPC script reset

Select an authored NPC and choose **Reset NPC-owned script edits...** in its
script ownership component. Asset Details offers the same tool. Select currently
owned families, Review, then Apply. The eight supported families are dialogue,
waits, movement, facing, flags, branches, model selectors and effect colors.

Review shows the project fields and target counts to remove. Apply removes only
the selected families in one undo step. Identity, name, position, appearance,
script donor, unselected families and other NPCs are preserved. Save/reopen
persists the result. Discard restores the currently owned selection; changing a
selection withdraws its proposal. Source changes withdraw controls until reopen.
Empty, unknown, duplicate, unordered or unowned selections are rejected.

This is a project metadata operation. Its source and proposal do not claim a
native byte preview or runtime behavior. The existing normal Build serializers
qualify the retained donor clone and remaining owned edits. Reset does not edit
retail records, write guest memory or install a package. Capability, Edit/busy,
active-scene selection and full project freshness remain guarded.

Offline acceptance (2026-10-06): 37 affected Python checks, three affected client
suites and three syntax checks passed. A private Town0b editor reset one owned
wait target and one color target together while preserving qualified facing
ownership and a second NPC. Review was immutable; empty/changed selections,
Discard, single-entry history, Undo/Redo, Save/reload and stale-source withdrawal
passed. Wide/400 px screenshots were inspected; no page errors or game requests.

A fresh normal Build independently read back both complete appended records
against retail donor bytes plus supported X/Z placement and the remaining other
NPC's color span. The retained facing owner used its qualified retail sector,
so the reset NPC's complete native record returned to donor bytes plus placement.
Integrity and current-input checks passed; Build did not change document/history.
Record hashes: `34d07d75ee059bb7881099850f20dc80aeab9c40b9023e4ed3ad4263cb9983d4`
and `7993ec53553e9fe542de9027303b8349b3a067cff03dccf9fd683defd7c8d8f3`.
This positive native proof used compressed Town0b; no new streaming reset Build
or full regression campaign was run. Runtime effects/gameplay remain unverified.

Evidence: `local-output/sdk-20260909/npc-script-reset-20261007/`. Early verification
scripts omitted the server-only freshness field and expected a public history
depth that is not exposed; retained failures are superseded by the final public
state checks and direct authoritative one-entry history assertion.
