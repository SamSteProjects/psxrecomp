# Retail and Current material references

The Asset Database reference browser now preserves **Retail static material to
texture address match** links and displays separate **Current static material to
texture address match** links after relevant saved model or texture edits.
An authored TIM slot can therefore show which Current models reference its
address region. Both active-scene and project-wide reference queries support
forward model dependencies and inverse texture consumers. Navigating a recorded
link retains the existing source-scene availability checks.

Current discovery reads qualified saved model replacements and the effective
scene texture catalog, including authored slots. It decodes actual Current
materials and UV crop bounds, then uses the existing pixel-free static material
association routine. Missing, ambiguous and unsupported results create no link;
identical overlapping providers may create multiple source links. The browser
offers separate Retail and Current material diagnostics for model roots. When
there are no relevant edits, Current inherits Retail and no duplicate Current
census is produced. Imported-only cached results remain detached and unchanged.

`effective_material_texture_source` edges use layer `effective` and retain the
verified scene/catalog/import identity, Retail model hash, Current model hash,
material index, texture page, CLUT, UV bounds and a hash of the authored material
state. Existing `static_material_texture_source` edges remain source decoded;
their semantic evidence survives edits even though fresh catalog keys and edge
IDs can change. `runtime_binding` remains `not_asserted`.

The reference freshness key now includes model overrides, texture overrides and
authored texture additions. Those edits invalidate an open reference view just
as entity edits do. Discovery checks source freshness before and after decoding.
The editor validates Current proof fields and requires model diagnostics to agree
with link hashes. Material evidence cannot qualify a different relationship.

Existing discovery limits remain: at most 512 scene models, 256 decoded material
groups per model, links for supported groups below index32, an eight-million-texel
sampling budget per layer, and eight MiB combined material metadata. Project-wide
queries retain their 32 MiB discovery and eight MiB response budgets. Current
sampling is separate from the immutable Retail cache; no new persistent cache,
project file or history entry is created by reference inspection.

## Verification - 2026-10-04

Twenty focused Python checks passed with private retail input and no skips,
covering active/project graphs, immutable imported caching, separate Current
projection, source drift, inverse links and freshness of all three asset binding
types. JavaScript checks passed for Current layers, source/native/binding hashes,
strict proof fields and diagnostic/hash agreement, alongside existing reference
and project navigation checks.

A fresh private native vell project added a 256 by 256 direct-color TIM slot and
assigned it through the existing reviewed material command to Model0000. Retail
links retained their semantic evidence; Current links found the new slot. Inverse
and project-wide queries, Save/Open and Undo/Redo passed. The styled editor showed
both model link layers and the authored slot's Current consumer in project scope.
Inspection changed neither project document, SDK selection nor history, with zero
page errors. Desktop and narrow screenshots were inspected. Initial private
harness attempts were corrected for nested primitive groups and revisioned
catalog/edge identities; failed attempts remain preserved. Accepted evidence:
`local-output/sdk-20260909/effective-material-references-20261004/accepted/proof.json`.

No serializer or runtime code changed. No game launched or installed output was
modified. Static associations do not prove live upload ownership, residency,
palette animation, hardware blending or final appearance; gameplay stays deferred.
