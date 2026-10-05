# Guarded material reference reuse

Repeated active-scene and project-wide reference queries now reuse a bounded
Current material metadata census. The cache lives only in `AssetDatabase`, with
two entries and an eight MiB limit per entry. Returned metadata is detached; no
pixels or project history are cached, and no cache is written into the project.
The existing immutable Retail material cache remains separate.

A Current key covers the imported source identity and complete saved model,
texture and authored-slot bindings. Relevant binding changes require new decoding.
Before a warm entry can be reused, existing owned-content readers requalify active
model replacements, including their base bindings, and effective texture inputs,
including authored-slot source recipes. Missing, changed-size and same-size hash
changes reject. Failures within that guard evict the affected entry. An earlier
resource or Retail verification failure blocks the query before the cache is read.
Restoring identical bytes permits reuse after the ordinary fresh checks.

Cold decoding requalifies owned inputs before installing metadata, checks source
freshness and enforces both the Current and combined Retail/Current response
budgets. Cache hits also check source freshness after qualification. LRU retention
does not give a stale result permission to pass verification.

Project-wide discovery still registers resource catalogs in a detached AssetDatabase
so it cannot overwrite active editor resource records. Only source-keyed material
metadata caches are shared with that view. Every imported scene is freshly verified
before either cache is consulted; Current reuse then requalifies owned files against
the detached project snapshot. Existing scene, discovery and response budgets remain.

## Verification - 2026-10-04

Twenty-one focused material/reference/project Python checks passed with private
retail input and no skips. New checks verify detached Current results, two-entry
retention, changed binding keys, failed owned-guard eviction and re-decoding,
source drift rejection, blocked cache access after failed Retail verification,
and absence from saved project metadata.

A copied private native vell authored project verified one Current decode across
four initial model/slot queries; all queries retained fresh Retail checks. Same-size
model and TIM corruption both rejected without decoding or returning cached data;
the exact source bytes were restored afterward. Changed slot bindings required a
new census. Repeated project-wide and HTTP queries reused qualified metadata.
The styled browser retained separate Retail/Current links, authored-slot consumers
and project-scope navigation. Project document, selection and history stayed
unchanged, with zero page errors. Screenshots were inspected. Private evidence:
`local-output/sdk-20260909/current-material-cache-20261004/final/proof.json`.

The initial native run measured about4.4 seconds cold versus1.6 seconds warm for
this vell fixture. These local timings are informational, not a general performance
guarantee. An initial harness incorrectly required a TIM resource-refresh rejection
to evict a cache that had not yet been reached; that assertion was corrected while
retaining the failed attempt. No game launched, installed output changed or runtime
code was edited. Residency and appearance remain deferred gameplay acceptance.
