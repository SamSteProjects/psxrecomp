# Whole inspected script flow

The existing branch-flow diagram now offers Whole inspected flow under Script
graph scope, alongside Selected neighborhood. Earlier graph page and Later
graph page traverse all reached decoded boundaries in the selected layer in
record-PC order, 24 boundaries per page. Dialogue segments retain their encoded
continuation edges.

Each page shows outgoing edges and a bounded set of outside-page endpoints.
Click a decoded outside-page endpoint to inspect it and open its graph page.
Instruction boxes retain keyboard Enter/Space navigation. Shared Current and
Reviewed Proposed edges are merged; changed Proposed edges remain dashed and
colored. Retail uses the existing separate source layer. Selecting a branch or
instruction follows the corresponding graph page; source/layer refresh clamps
the page to the available report.

At most 40 boxes render on one page. Additional outgoing edges are counted
explicitly as omissions. A target outside the page differs from an undecoded
target: only qualified decoded targets navigate to another page. Decoder stop
reasons remain visible where supplied. Retained unvisited source rows stay in
the existing Whole-record source flow overview. Opaque bytes are never decoded
or recovered by this view.

This is encoded control-flow visualization. It does not evaluate conditions,
flags, scheduler state, story activation, external resumes or runtime execution.
Existing source qualification, Current-layer availability and review/Apply
guards remain unchanged. Graph browsing edits no project data.

## Offline acceptance, 2026-10-07

Four focused client suites and the changed module's syntax check passed.
Coverage includes complete paging without duplicates, exact Current/Proposed
edge identity, parallel/self/dialogue edges, outside-page targets, explicit
display omissions, malformed boundaries, 8192-node bounds and immutable inputs.
Existing branch review/Apply, stale/late-response, source overview and selected
operand-layer checks remain green.

Actual Town01 Actor 0010 supplies 156 decoded boundaries across seven pages.
Its unresolved source stops keep Current inspection unavailable; the Retail
diagram retains that restriction. The browser passed next/previous paging,
decoded off-page navigation, keyboard instruction inspection and source refresh.
A separately qualified Actor 0002 passed Current/Reviewed Proposed edge
comparison and discard withdrawal. Close removed the inspector. Wide and 400 px
layouts were inspected without horizontal dialog overflow or page errors.

Project document/history/saved bytes and Build input key stayed exact. Reopening
the private project retained the same document. The first private browser check
used an incorrect dialog selector; its failed evidence is retained with the
corrected check. No native serializer or runtime code changed, and no new Build
or full campaign was needed for this read-only editor feature.

Private evidence: `local-output/sdk-20260909/script-whole-flow-20261007/`.
No game launch, runtime attachment, install or disc export occurred. Development
stays solo; gameplay verification stays deferred and the full SDK goal is active.
