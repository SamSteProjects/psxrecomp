# Transition graph to source entry

Scene transitions and Project transitions now expose **Inspect transition entry**
on each decoded instruction row. The action opens its imported source scene when
needed, refreshes the source resources, and opens the exact transition Inspector.
From there, Compare arrival in destination scene enters the existing arrival
comparison and draft/Review/Apply workflow.

The graph action retains the project path and project-wide transition key across
navigation. The fresh record must match its stable ID, source/destination, owner,
script, partition, status, complete source-record provenance, exact reference and
Imported/Authored/Current entry layers. Object-key order does not affect comparison.
Changed project/source/Current evidence rejects; no graph snapshot is used as an
authoring request. The action is available in Edit mode with resource catalog
support. An unresolved destination can still be inspected as a source entry; its
arrival action remains unavailable under the existing Inspector rules.

This is source navigation. Arrows remain encoded references; script reachability,
trigger location, runtime dispatch and actual arrival are not established by the
graph. Opening or inspecting an entry creates no authored change or Undo step.

Native validation on 2026-10-04 started in map01, searched Project transitions for
`transition://town01/scripts/man-p2/0000/0016`, opened its fresh Town01 Inspector,
and followed the arrival comparison back to map01. The Scene transitions path
repeated the exact-entry workflow from Town01. The complete project document and
history were unchanged after the round trip. Zero authoring requests and browser
errors; graph and Inspector screenshots inspected. Eight focused Python graph
checks and Node graph/resource/source-change guards passed. No game was launched.

Private evidence: `local-output/sdk-20260909/graph-entry-workflow-20261004/proof.json`.
