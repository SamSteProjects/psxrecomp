# Saved hierarchy inspection state

Use a hierarchy search and collapse any groups, then open **Scene tools → Saved scene views** and **Save current view**. New views retain the query and group folds together with the existing camera, representation, layers, grid and source-bound visibility. **Recall scene view** restores them as one editor display operation. **Replace with current view**, Rename/Delete, project Save/Open and existing Undo/Redo remain available.

Search still uses the existing typed hierarchy grammar: name, id, type, component, authored and visibility fields; quoted phrases, AND terms and exclusions. Both client and SDK reject malformed phrases, unknown fields, empty field/exclusion terms, more than 32 terms or more than 2048 UTF-16 characters. Collapsed groups are canonical supported identities, not row indexes. Search temporarily expands matching groups; clearing a recalled query reveals its saved folds. Matching rows are evaluated from the current scene records, not saved as an implicit selection or visibility edit.

Capture requires the current project/scene hierarchy scope. Existing scene/import/review-key guards protect Save/Replace/Recall. Invalid queries cannot be saved. Old views without hierarchy metadata retain their existing recall behavior and do not overwrite the current search/folds. This optional editor metadata does not change the project format version, actor positions, scene visibility, model filters, runtime coordinates or game data.

Accepted offline on 2026-10-07: 16 focused Python tests, four Node suites, three JavaScript syntax checks and Python AST checks passed. New checks qualify server/client grammar agreement (including Unicode length and whitespace), canonical fold metadata, detached capture/recall, stale scope, legacy compatibility, source/review guards, atomic rejection and complete metadata history/persistence with native input keys held.

Actual private Town01 editor saved a collapsed Actors group with `type:actor id:0049`, changed the inspection state, recalled the single matching actor, cleared search to confirm the restored fold and rejected an invalid query without a command. Saved project reload/recall passed. Only the new scene-view record changed; imports, native Build input key and every non-project file stayed exact. Full-document one-step Undo/Redo and Save/Open passed. Actual wide/400 px hierarchy and final visible-dialog captures were inspected with no page errors or game launches. A separate read-only visual pass preserved document/history/native keys.

Private evidence: `local-output/sdk-20260909/hierarchy-view-20261007/`. The initial browser attempt stopped at a hidden narrow-layout hierarchy panel; the corrected attempt selects the existing workspace tabs. An early dialog screenshot taken before asynchronous opening is superseded by the explicit visible-dialog captures. Those proof corrections are retained. No native Build was needed for this metadata-only feature; no runtime change, game launch/attachment, installation or disc export occurred. This is focused editor acceptance, not a full regression campaign or native gameplay/coordinate validation. Solo development and the full SDK goal remain active.

## Reveal selected placement groups

**Reveal selection** clears hierarchy search and expands every group containing a
member of the current mixed, actor or scenery selection. It keeps keyboard focus on
the active member when that member belongs to the group; otherwise it focuses the
first selected stable ID. It does not invoke a row's selection action or change the
viewport selection. Unrelated group folds remain collapsed. Individual selections
continue to use the same action.

The helper accepts 1–128 unique bounded identities and qualifies every row before
expanding groups. Missing, duplicate, disabled or oversized requests refuse. Folding
and search remain editor presentation; saving the resulting hierarchy state still
requires the existing Saved scene views command. On narrow screens, open the
**Hierarchy & assets** workspace tab to use this action.

Offline checks passed (2026-10-07): two focused Node suites and two JavaScript syntax
checks. The actual Town01 editor revealed 19 selected group members across collapsed
actor/environment groups after clearing a hiding search. Active focus, the complete
viewport selection and an unrelated collapsed trigger group were preserved. Wide
and 400 px hierarchy views were inspected; no page errors occurred. Project document,
history and saved file sizes/timestamps stayed unchanged. No native Build, game launch
or installation occurred; gameplay remains deferred. Private evidence:
`local-output/sdk-20260909/hierarchy-group-reveal-20261007/`
(`browser.json`, `readonly.json`, wide/narrow screenshots). Earlier probes assumed
project-resource refresh populated the scene hierarchy and omitted the narrow
workspace-tab switch; their logs/screenshots are preserved. The final probe loads
active-scene resources and uses the Hierarchy & assets tab.
