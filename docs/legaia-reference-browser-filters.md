# Reference browser filtering

The Asset Database reference browser offers **Recorded reference layer**,
**Reference direction** and **Search recorded references** alongside the existing
active/project scope control. Layer choices map exactly to recorded `imported`,
`decoded`, `authored` and `effective` edges. Derived source and Effective/Current
are display labels; filtering never invents inheritance, new relationships or
runtime use.

Search matches case-insensitive whitespace-separated terms against the neighbor's
stable ID, label and type, the relationship label, and recorded edge provenance.
Every term must match. Scene IDs, source hashes and material evidence can be found
this way. The limit is512 characters and32 terms; this is plain-text matching,
not a regular-expression or Asset Database field-filter parser.

Visible/total relationship counts appear for the report and each visible direction.
An empty filtered result differs from a direction with no recorded relationships.
Coverage, unresolved counts, provenance and material diagnostics retain the full
accepted report; filters affect relationship rows only. Search and layer/direction
changes use that accepted snapshot locally without another request. Scope changes
requalify the report and retain the filters. Inputs are disabled while loading;
closed/superseded replies and stale source contexts retain existing rejection.

Filtered target buttons keep their exact qualified identity and ordinary source
navigation checks. They open the target asset Inspector; they do not automatically
launch its specialized editor. Close now sits beside the dialog title, above long
reference lists. Controls use a responsive grid with a full-width search field.

## Verification - 2026-10-04

Focused reference JavaScript checks passed, including exact layers/directions,
case-insensitive terms, stable IDs and recorded hashes, detached rows, no-match
results and input limits. Existing source/proof/project navigation checks passed.

A copied native vell authored project verified All, Effective/Current and Derived
source results, outgoing direction, authored-slot ID search, visible/total counts,
no-match recovery, retained filters across active-to-project scope and navigation
to the selected authored slot's Inspector. Filter changes made no extra reference
requests. Project document, SDK selection and history remained unchanged, with zero
page errors. Desktop and narrow screenshots were inspected. The first harness
incorrectly waited for a texture preview after a reference link; it was corrected
to verify the actual asset Inspector destination, preserving the failed attempt.
Private evidence:
`local-output/sdk-20260909/reference-filters-20261004/final/proof.json`.

No SDK serializer, build or runtime code changed. No game launched or installed
output changed. Recorded links remain source evidence rather than residency,
execution, activation or gameplay reachability.
