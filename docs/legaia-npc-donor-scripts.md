# Inspect an authored NPC retail donor script

Select an NPC draft in the Hierarchy and choose **Inspect retail donor script...**.
Alternatively, search its stable ID in the Asset Database, open Asset Details,
and choose **Inspect retail donor script**. The draft must belong to the active
imported scene; the project retail disc must be available.

This workspace reads the retail donor record through the existing source-verified
MAN script decoder. It preserves the selected NPC and changes no authored state.
Dialogue cards retain structural source identities. Instruction search, the flow
overview, successor links and decoded path tools use the shared script Inspector.
Its instruction table includes dialogue markers alongside decoded instructions.
Search/navigation controls are read only; no authoring forms are mounted.

Source, raw bytes and decoder limits remain inspectable. Opaque regions and stops
are explicit. Encoded paths do not establish execution or gameplay reachability.
Offsets refer to the imported donor record. Native allocation can rebase code and
references; this is not an inspection of generated NPC code or a runtime binding.
Imported donor source is separate from project edits to that donor.

The SDK response is bound to the complete current project source key, active
scene, draft identity/name/position/donor, source owner and original record span.
A project change during verification rejects the response. Closing aborts pending
work and removes the dialog. Generated/live claims and authored reports reject
before rendering. Existing Build inputs and source provenance remain unchanged.

## Offline evidence - 2026-10-05

Twenty focused Python checks and three Node contracts pass. The private retail
browser verified both Inspector entries, exact SDK response, instruction selection,
retained NPC selection and the inspected 540px layout. Source donor0012 exposes25
instructions and16 dialogue segments; its verified record SHA-256 is
`5063e5eb8bfd400fba142b0eabee28f50c46b900aa319ebdf86fd0b4eea73a65`.
Evidence lives in `local-output/sdk-20260909/npc-donor-script-20261005/`. Project,
history, normal Build input identity and preexisting files are unchanged. No game
launch or authoring command occurred; generated-code and gameplay acceptance
remain separate.
