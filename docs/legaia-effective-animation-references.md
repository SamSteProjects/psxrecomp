# Effective initial animation relationships

Actor Asset Details → Inspect asset references now shows imported and effective
initial animation bindings separately. The imported edge retains the actor's
recorded MAN-to-ANM association. The effective edge follows the current verified
appearance donor only when that donor's exact model and animation binding occurs
in the active scene catalog. Its evidence includes donor identity, model identity,
initial animation ID, import hash and current catalog key. Appearance donor edges
also permit navigation to the recorded donor actor.

NPC draft animation links use an authored layer and the draft's retail donor.
They do not inherit later appearance overrides on that donor. These are source
relationships for proposed content, not evidence of spawned actors, scheduling,
live playback or behavior. Missing catalog bindings remain missing, rather than
being inferred from equal channel/object counts. Derived animation coverage is
still limited to the active scene.

There is no new arbitrary clip assignment command in this feature. The current
serializer requires an observed initial donor pair. The two imported fixture
scenes have no alternative initial clip recorded for the same model. Model/clip
retargeting and previously unobserved assignments require further format and
runtime evidence. Existing donor-pair authoring remains available.

## Imported material metadata reuse

The Asset Database retains at most two copied imported material catalogs in
memory. Each is limited to eight MiB of canonical metadata and keyed by decoder
version, retail path, active scene and the entire imported document. Every
reference query still verifies imported scenes against the user-owned retail
source before cache reuse. Source changes during discovery prevent cache
installation. The cache has no pixels, is absent from saved projects, and is
discarded when the project is reopened.

Authored actor changes do not alter these imported material relationships.
Effective donor/animation edges are assembled separately on every request from
current authored state and the fresh active resource catalog. This preserves
current reference review keys while avoiding repeated unchanged material scans.

Validation evidence is private under
`local-output/sdk-20260909/effective-animation-refs-20261001/`. Synthetic checks
cover exact donor/model matching, distinct draft layers, cache copies/bounds,
source-key changes, failed verification and discovery drift. Retail checks verify
source preservation and repeated-query cache reuse with continued verification.
Twenty focused retail-enabled Python tests, all22 Node files and24 syntax checks
passed. Browser confirmed town01 actor0012 keeps its imported clip0012 while
its authored donor0040 yields effective clip0008, plus a draft retail donor clip.
One authoring command followed by Undo restored actor/authored state; saved
metadata remained unchanged and zero page errors occurred. Screenshot inspected.
These checks postdate integrated475. No game is launched; broader SDK/runtime acceptance remains
incomplete.
