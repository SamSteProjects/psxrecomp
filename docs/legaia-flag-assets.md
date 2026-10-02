# Flag references in the Asset Database

Flag reference groups now use the SDK's central Asset Database, shared Inspector
and asset dependency graph. They describe encoded operands in a verified retail
script. They do not represent named story variables or current runtime values.

Refresh scene resources, select **Flag references**, and search by stable ID,
bank, selector, operation or source script. `type:flag scene:dolk2` also works in
the ordinary asset search. The Details action uses the same Inspector metadata
and capability registry across the thirteen supported catalog record types.

The flag Inspector shows the source script and owner, dispatch context, retail
selector, per-site authored/effective selectors, decoded coverage and source
provenance. Sites are paged in groups of fifty. **Inspect parent script** opens
the existing source workspace; the first, last and individual operand actions
select the exact decoded instruction PC. Both P1 actor owners and P2 script
owners are supported. Existing source-qualified flag editing remains in that
workspace, with its existing width, side-effect and unknown-path restrictions.

## Identity and layers

The stable identity remains:

```text
flag-reference://<scene>/<actors/man-p1|scripts/man-p2>/<record>/<current|extended-N>/<bank>/<retail-index>
```

Equal selectors in different scripts or dispatch contexts remain separate
groups. An authored bit changes an individual site's effective operand; it
does not rename or regroup the retail source identity. System selectors,
flag-word branches and the separate extra bank retain their recorded selector
semantics. Local indices16–31 retain unresolved width. Runtime binding and value
remain unresolved/null, including after a source edit.

Resource responses include a separate `flag_state_key`. The editor invalidates
catalog annotations and closes stale flag views after Apply, Clear or Undo,
without changing the geometry source key. Project flag discovery now includes
project/disc/import identity and authored flag operands in its state key; it no
longer identifies the authored result with an imports-only hash.

## References and coverage

Each decoded site contributes a `script_flag_reference` dependency from the
source script to its flag group. The inverse appears under Referenced by. Edges
retain source-import and resource keys, instruction PC, encoded bank/index,
operation, mnemonic, scope and dispatch target. These are retail source
relationships, even when a site's authored effective selector differs.
Active scene and Project reference scopes support the new nodes through the
existing source-scene navigation and fresh catalog verification.

The adapter consumes the existing verified script catalog and validated flag
edits. It does not decode more paths or partitions. P0/controller records,
opaque/unvisited paths, additional MAN carriers, current flag values, story
names and runtime execution remain outside this contract. Partial/unavailable
script coverage is retained. Matching indices are not merged across scenes,
scripts, world-map discovery records or captured runtime node words.

Flag assets reject more than4,096 groups or16,384 sites. The combined resource
catalog still rejects more than4,096 records. Existing graph limits remain
16,384 nodes,32,768 edges and4,096 edges per neighborhood, with project scene
and response-byte limits unchanged. Overflow rejects; it never truncates.

Fresh Town01/Dolk2/map01 discovery found446/253/200 groups covering1,249/615/278
sites respectively. Detached discovery preserved imports, selection, history, caches
and saved bytes. A real Dolk2 actor0002 context24 operand at PC14 retained its
group identity after source-qualified editing, Undo/Redo and Save/Open; the
geometry key remained unchanged. Private evidence stays under
`local-output/sdk-20260909/flag-assets-20261002/`.

Source browsing introduces no immediate gameplay verification requirement.
Story behavior and execution of authored operands retain the deferred gameplay
acceptance requirements of the existing flag editing workflow.

Final validation:43 focused retail-enabled Python tests,36 Node test files and
36 editor syntax checks passed. Actual browser P1 PC14/P2 PC45 navigation,
shared Inspector actions, authored layers, Undo/Redo/Save/Clear, stale-dialog
closure and Active/Project references passed with zero page or unexpected HTTP
errors. The screenshot was visually reviewed. No game was launched or package
installed; owned SDK/browser helpers were stopped after validation.
