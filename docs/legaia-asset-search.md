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
query restores results. Category filters still apply. Active scope searches the
refreshed scene; [imported project scope](legaia-project-assets.md) searches the
explicitly refreshed project index. A `scene:` match includes every retained
source membership of a shared ID, even when another membership is selected in
Details. The source-scene selector restricts the displayed inventory and fixes
its variant. Search does not decode new resources or modify project data.

Validation on 2026-10-01: all 14 Node checks and all 17 editor module syntax
checks passed. Retail-source browser verified field combinations, model-reference
actors against the SDK reference graph, phrases/exclusions, provenance, invalid
syntax, stable-ID URI searches, reset and actor navigation with no authoring
commands or actor changes and zero page errors. Screenshots were inspected;
narrow asset controls now wrap inside the panel. This feature postdates the
463-test integrated Python checkpoint. No game launched.


URI correction — 2026-10-01: a pasted `scene://town01/actors/man-p1/0004`
now remains a literal stable-ID search, even though `scene` is a registered
filter name. Excluded URI tokens behave the same way. Explicit
`scene:scene://town01` and `id:scene://...` remain field filters. The actual retail
actor/scene Details workflow exposed the failure and passed after the parser
correction; focused URI/exclusion/field checks passed.

## Retained membership provenance

In imported project scope, `name:` covers each retained variant's recorded name and
`scene:` covers its source-entry aliases. `provenance:` covers all retained source
records, claims, RetailMetadata and explicit membership import SHA256/catalog bindings.
For example, `id:worldmap://legaia/menu/placements/0000 provenance:<source SHA256>` can
find the shared placement by a verified source membership other than the chosen one.
Replace the placeholder with the recorded hash; no new decoding occurs during search.
Exclusions use the same coverage, so `-provenance:<hash>` removes matching shared records.

A search match never changes the source variant. Details continues to show the chosen
membership; choose **Imported source membership** to change it explicitly. Search terms
match the asset's retained metadata and can occur in different memberships. They do not
establish a joined binding, runtime residency, confidence for every property or gameplay
reachability. Active-scope records without project memberships behave as before.

The 2026-10-05 browser proof reproduces the old hash miss and finds the asset by Map01
provenance while retaining Dolk2 in real Details. Node and eight project-source Python
checks pass; project/history/files and scene/selection stay unchanged. Private evidence:
`local-output/sdk-20260909/project-provenance-search-20261005/`.
No game, authoring, Save, Build or Run was requested by this search workflow.
