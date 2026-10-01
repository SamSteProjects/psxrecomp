# Asset browser search

Search the asset browser with ordinary words or field filters:

- `name:"Actor 0012" type:actor` finds that structural actor name.
- `type:model scene:town01 confidence:confirmed` narrows model records by source and recorded claim confidence.
- `model:asset://town01/models/scene-tmd/0112` finds recorded model references as well as that model record.
- `provenance:AndrewAltimit -scene:town01` searches source/evidence metadata while excluding a source scene.
- `id:asset://town01/models/scene-tmd/0112` searches stable identity.

Combine terms with spaces: every positive term must match, and every negative
term must be absent. Double quotes keep a phrase together; a leading `-` excludes
a word or field value. Quoted literal tokens can contain colons without being
interpreted as field filters. Bare stable-ID URIs remain normal text searches.

Supported fields are `name`, `id`, `type`, `scene`, `model`, `confidence` and
`provenance`. Matching uses case-insensitive substrings within those fields.
`scene` includes recorded source scene/context; `type` includes catalog type and
decoded asset kind. Model searches include recorded imported, authored and donor
references, without proving runtime use. Confidence searches individual recorded
claim values, not a combined certainty score for the record. Missing confidence
has no invented label: a positive filter cannot match it; an exclusion can retain
it. Provenance searches source records, claims and evidence metadata.

Unknown field prefixes, missing values, unclosed quotes, more than 32 terms or
more than 2048 characters show a search error and no results. Correcting the
query restores results. Category filters still apply. Resources remain limited
to the refreshed active scene; models and authored records retain existing
project-wide scope. Search does not decode new resources or modify project data.

Validation on 2026-10-01: all 14 Node checks and all 17 editor module syntax
checks passed. Retail-source browser verified field combinations, model-reference
actors against the SDK reference graph, phrases/exclusions, provenance, invalid
syntax, stable-ID URI searches, reset and actor navigation with no authoring
commands or actor changes and zero page errors. Screenshots were inspected;
narrow asset controls now wrap inside the panel. This feature postdates the
463-test integrated Python checkpoint. No game launched.
