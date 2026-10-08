# NPC Arrival References

Asset References now connects an authored NPC to each qualified named transition in its Retail script donor. Active-scene and Project reports retain separate Retail bytes, partial or complete clone-owned arrival fields, effective Current bytes and a static X/Z/facing reference. The inverse transition view identifies independent NPC users. Arrival coordinates describe player destination entry; they do not position the NPC.

The relation kind is `npc_script_transition_arrival`. Each relation carries a fresh native instruction layout, source record hash, donor identity, exact operand offset and destination identity. The backend independently reads donor bytes before binding qualified source options; the client validates the same typed ownership and native instruction contract before displaying or navigating. An imported donor actor's own overrides cannot leak into a clone. Unmatched owned entries remain unresolved in coverage diagnostics.

From NPC Asset Details, choose **Inspect asset references**, filter to **Authored**, and search for **arrival**. Current coordinates and bytes appear beside the unchanged Retail source. **Inspect retail donor instruction** opens the actual donor's exact source PC. It does not claim to inspect generated clone allocation. Active/Project scope, forward/inverse exploration and complete report downloads use the existing bounded reference workflow.

This work also fixes NPC Asset Details failing before opening: its expanded server descriptor exceeded the old 16-action ceiling. The component contract now permits up to32 unique actions, still refusing duplicates and larger lists. The asset registry now includes Current Script, Transition Arrivals and System Selectors with existing donor/capability guards. No guest writes or native execution are implied.

## Offline Checks — 2026-10-08

Private Map02 donor0002 PC53 supplies a real named transition. Retail entry31/30/0 remains independent of three clones: full0/255/7, partial direction255 inheriting31/30, and fully inherited31/30/0. The donor actor separately overrides direction3. Forward/inverse and Project graph agreement, immutable inspection, native offset/forged-source refusal, Clear, Undo/Redo and Save/Open passed in one focused Retail Python workflow. Nine existing Python cases also passed; the initial regression run skipped its Retail case, then that case was rerun explicitly with Retail enabled and passed.

Seven Node suites passed: the arrival graph, four existing reference suites, actual server NPC inspector descriptor integration and component inspector. Four Python AST and six JavaScript syntax checks passed. A fresh private browser workflow passed NPC Details, authored arrival filters, Project scope, complete report download, exact donor PC53 navigation, unchanged document/history/imports/dirty state and Save/Open. Wide and400px captures were inspected with zero page errors and no horizontal overflow. Helpers closed.

Evidence is retained privately under `local-output/sdk-20260909/npc-arrival-references-20261008/`; final UI evidence is `browser-qualified-final/`. Earlier selection/timing/assertion harness failures and the genuine Asset Details contract failure remain retained separately. `checks-receipt.json` records command outputs; `final-source-hashes.json` records checked source identities.

Reachability is `not_evaluated`; runtime binding is `not_asserted`. Unknown route activation, streaming delivery and gameplay remain unverified. This checkpoint performed no native Build, game launch, runtime attachment, installation or disc export. It advances the full SDK goal without marking it complete.
