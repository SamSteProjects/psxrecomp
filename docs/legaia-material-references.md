# Imported material source references

Asset Details → Inspect asset references now links imported model material groups
to recorded texture source candidates. A successful link carries the material
index, raw texture page, CLUT, inclusive UV crop, imported model SHA256 and
static-address evidence. It appears in model Dependencies and texture Referenced
by. Available source TIMs open their existing provenance inspector. Shared party
or boot sources outside the active navigable catalog remain visible and disabled.

The decoder resolves each sampled VRAM word from recorded source uploads. Only
`address_match` produces edges. Missing, ambiguous and unsupported results remain
in the model's Imported material address results; unavailable models also have
an explicit reason. Identical overlapping source uploads may contribute multiple
candidate IDs. Unique word values are not proof of a unique upload owner, runtime
residency, animated palette state or scheduling. Only supported decoded primitive
material groups are covered.

The service verifies the imported scene sources first and uses the same TIM,
field-party and boot upload interpretation as model previews. Discovery is limited
to 512 active scene models, 256 recorded material groups per model, sampling for
the first 32 material indexes and eight million sampled texels per query. Remaining
work is reported unsupported rather than becoming invented links. Sources outside
the active model/material catalog are not covered by this view.

These relationships describe imported models and texture candidates. Authored
shape/pixel replacements are not silently substituted. The existing initial and
effective actor-to-model references remain separate. Queries return metadata
without pixel blobs and do not change authoring state, history, saves or guest RAM.

Validation on 2026-10-01: 23 retail-enabled Python tests passed, covering source
verification, graph adaptation, payload-free matches, missing/conflicting uploads,
cross-TIM palettes, field-party resources and actual town01 address matches. All
22 Node test files and 24 module syntax checks passed, including rejection of
invalid material evidence and diagnostics. Retail browser demonstrated model
`asset://dolk2/models/scene-tmd/0133` material groups1/2/3 link to
`texture://dolk2/69/0/19` and open its provenance inspector, with zero page
errors/authoring commands and unchanged authored content/history. The reverse
texture Referenced by view also contains the recorded model relationships. Screenshot
inspected. Browser evidence is private under
`local-output/sdk-20260909/material-references-20261001/`. These checks postdate
integrated475 and do not establish gameplay or complete SDK/runtime acceptance.
