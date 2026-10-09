# Inspecting source world-map walk ground

The editor's **World ground** button opens the read-only **World-map source scene** dialog. Choose a **World kingdom** (`map01`, `map02`, or `map03`) and select **Inspect kingdom**. The viewport uses the same SceneRenderer as the field editor. Drag to orbit, use the wheel to zoom, and use **Frame ground**, **Top view**, and **Wireframe** to inspect the surface. Expand **Source provenance and limitations** for the qualified source spans and coverage.

This displays the source walk-visible ground heightfield for Drake, Sebucus, and Karisto. It does not import another scene, write authored overrides, change project history, start the game, or replace the current field scene. Source changes withdraw the stale inspection. World-map landmark menu X/Y bytes are not interpreted as 3D positions.

## Qualified geometry source

AndrewAltimit's read-only reference commit `d6e64c68ede25813d35db20980da82a1a025549b` supplies the world walk carrier selection and ground conventions. The SDK independently reads the user-owned retail disc. Each kingdom uses the complete `0x12000`-byte MAP immediately before its asset bundle, plus slot 2's MAN floor-height lookup table and slot 0's TIM_LIST atlas data.

| Kingdom | MAP PROT entry | Equivalent asset-table views | Visible cells | Vertices | Triangles |
|---|---:|---|---:|---:|---:|
| map01 | 83 | entry 85 + 6144 bytes = entry 86 + 0 | 16,251 | 65,004 | 32,502 |
| map02 | 242 | entry 244 + 2048 bytes = entry 245 + 0 | 16,381 | 65,524 | 32,762 |
| map03 | 389 | entry 391 + 6144 bytes = entry 392 + 0 | 16,374 | 65,496 | 32,748 |

The overlapping PROT views must resolve the same physical table and identical decoded source slots. The bare table view is the canonical locator. Seven descriptors retain their source types and stream boundaries; slot 2 provides the sixteen signed floor heights at MAN bytes 2 through 33. The source MAP has 128 by 128 cells. A cell's `0x1000` bit selects this surface, its low nine bits select the 32-byte object record, and corner height tiers select the MAN floor table. Each displayed cell contributes four vertices and two triangles. Raw geometry uses retail Y-down axes; only the renderer flips Y for display.

Texture selectors come from each selected source object record's atlas tile, page, and CLUT words. TIM_LIST member offsets are word offsets multiplied by four. The SDK qualifies bounded TIM images and their static address associations rather than inventing an atlas. Source material associations are available for 23 of 23 map01 materials, 17 of 18 map02 materials, and 15 of 16 map03 materials. Missing associations remain explicit. Static address agreement does not establish runtime upload order or VRAM residency.

## Independent retail evidence

Private evidence under `local-output/sdk-20260909/worldmap-geometry-20261002/retail/` independently walks all three MAPs and bundle tables. It records disc, MAP, compressed stream, and decoded MAN/TIM_LIST hashes and span boundaries. Independently generated ordered vertices, triangle indices, source UV coordinates, and every visible cell's record/tile/page/CLUT selector match the SDK output exactly. The probe writes metadata and hashes; it does not export an ISO/BIN or extract a broad payload tree.

For map01, the exact MAP SHA256 is `d29209df2b99b54182fdd029515bb89b7ca8fd47ac8bee2e128332608e925ea4`. Its source floor table is `[1,48,96,128,192,240,288,336,384,432,480,528,576,624,672,720]`; source ground bounds are `[0,-576,0]` through `[16384,-1,16256]`.

The current surface is a reference heightfield. It does not reproduce the complete retail ground emitter, per-story object placement, script visibility, collision deformation, ocean animation, special world overlay mesh semantics, or the separate overview resource. Landmark TMDs, decorations, and live actor placement are separate consumers and are not guessed into this viewport. Source geometry inspection does not establish full world-map rendering parity. No game was launched for this evidence; visual gameplay acceptance remains deferred.

Source model seeds now share this viewport. Use **Source model placements**, the
source entity hierarchy and **Frame selected** to inspect their immutable XYZ.
See [sparse placements](legaia-worldmap-placements.md) for provenance, model
texture coverage and the limits on runtime visibility and resting transforms.

The inspection now supports [source scene and selected-entity GLB export](legaia-worldmap-export.md) with the same geometry, transforms and confidence limits.


## Source Hierarchy Search — 2026-10-09

The source scene hierarchy now filters its recorded entities by case-insensitive
plain terms or exact `model:`, `record:` and `cell:` unsigned indices. `id:`,
`asset:` and `scope:` terms search their recorded identity fields. Terms combine
with AND; searches are bounded to 512 characters and 16 terms. Duplicate/missing
identities and a selected ID outside the qualified source view refuse. Numeric
filters reject malformed or oversized values without replacing the prior options.
These fields describe source model pools, object records and cell indices; they
are not semantic object names, runtime identities or authoring assignments.

A selected entity stays in the hierarchy when it does not match, labelled selected
outside filter. Match counts distinguish this retained row from search matches.
Filtering preserves the selected stable ID, Inspector and rendered scene; it does
not hide meshes or alter geometry/export scope. Mesh picking can retain its selected
entity outside the filter. Busy or stale source contexts do not apply search events.
Kingdom/source withdrawal and close clear the display filter.

Four Node suites and two JS syntax checks passed. Focused checks cover field and
identity matching, detached labels, exact preserved selection, query limits and
foreign/duplicate refusal. Actual muted editor workflows loaded fresh SDK source
geometry for map01/map02/map03: 302/273/237 entities including ground. Model, record
and cell results matched independent filtering of every source report; selection
and Inspector text stayed exact, including no-match filters and Frame selected.
Invalid filters retained the prior selection/options; clearing restored every row.
Close/reopen cleared the filter. Desktop/400px screenshots were inspected. Zero page
errors or command/Build/Run/Save/scene/selection/export requests occurred. Project,
imports, history and saved fixture files stayed exact. Private evidence:
`local-output/sdk-20260909/worldmap-hierarchy-search-20261009/`.
The browser harness first exhausted Chromium response-body inspection cache for a
large geometry response; bounded API route capture qualified the same response
before the final pass. No game, runtime attachment or native Build ran. Source spawn
seeds do not establish runtime resting positions or visibility; full SDK goal active.


## Shared Source Inspector — 2026-10-09

World source entities now render through the shared component inspector using the
SDK `WorldSourcePlacement` descriptor. The descriptor owns labels, property paths,
read-only state badges and limits notes. Entity/model identities, placement scope,
source XYZ, cell/object/model indices and source record hash are separate fields.
Decoded spawn-seed coordinates remain Derived; runtime visibility and resting
position remain Unresolved. Missing ground-only fields retain explicit unavailable
labels. No component actions, authoring adapters or runtime writes are registered.
The raw entity evidence remains unchanged in a disclosure, with the existing raw
Inspector identity preserved for source inspection. An older schema without the
new component can still expose the raw evidence.

Seventeen Python schema checks, three Node inspector/world geometry/hierarchy suites
and frontend syntax passed. Actual muted map01/map02/map03 workflows verified exact
XYZ against each source report, two Unresolved runtime badges and no edit controls.
Hierarchy filtering retained selection and raw Inspector text; close cleared content.
Desktop and 400px layouts were inspected. Zero page errors or command/Build/Run/Save/
scene/selection/export requests occurred; project/imports/history and saved fixture
files stayed exact. Private evidence:
`local-output/sdk-20260909/worldmap-component-inspector-20261009/`.
No game, runtime attachment or native Build ran. These remain source spawn seeds;
runtime resting transforms and visibility require further evidence. Full SDK goal active.

## Placement Inspector Handoff — 2026-10-09

Select a source model seed in World ground and choose **Inspect placement record**. The source dialog hands the selected stable entity to World placements, reloads qualified geometry and placement metadata, selects its exact owning record, and frames that seed. Source XYZ remains decoded read-only metadata; destination number fields contain Current record offsets and yaw, not absolute seed coordinates.

Ownership requires the same Edit project, source key, kingdom, source record index/hash and placement entity. Exactly one fresh owner must qualify. Missing/changed ownership closes the destination instead of leaving a different default record selected. Busy state, existing placement dialogs/drafts, changed project/mode/source and withdrawn capability refuse navigation. Replaced Inspector buttons cannot navigate even if the new Inspector selects the same entity. Ground exposes no placement action. Shared records still require explicit all-cell consent; navigation grants none automatically. Review, typed Apply, retained provenance and undo remain owned by the existing placement workflow. Discard restores Current values and clears the old Reviewed status.

Targeted evidence: 17 inspector-schema Python checks; placement and shared-component Node suites; three JavaScript syntax checks. Actual private retail source workflows for map01/map02/map03 qualified records 0414/0461/0490 with 1/55/31 source cells respectively. Each selected exact entity/hash/record/anchor and Current values, then reviewed a changed byte and discarded. Detached-button refusal and ground action absence passed. Desktop and 400px views were inspected. Project document, imports, history and all saved fixture bytes remained exact; zero browser errors or mutation requests occurred.

Private evidence: `local-output/sdk-20260909/worldmap-placement-handoff-20261009/`. No extracted assets or fixtures are tracked. No game, runtime attachment, native Build, install or disc export occurred. Apply/package/gameplay were not rerun for this navigation change. Runtime visibility and resting positions remain unresolved; full SDK goal remains active.

## Shared Record Inspector — 2026-10-09

World placements now lists **Affected source entity** members of the selected qualified record. Options identify each source cell and its coordinates in the displayed Current/Proposed/unreviewed preview. The source-scope summary separates qualified seeds from the complete source cell count; incomplete coverage remains unwritable. Selecting a member frames its anchor and preserves offsets, shared-record consent, pending drafts and same-record Review. Viewport selection within that same record also retains its draft; selecting another record remains refused until Apply or Discard. Anchor identity participates in the transform gesture context.

Expand **Retail, Current, Authored and Proposed record values** for SDK component metadata showing Retail, Current, Authored override, Reviewed proposal and Unreviewed preview draft separately. Absent authored/review/draft values display Not present rather than inheriting another layer. Offset fields remain native record values, not absolute seed XYZ. Reviewed proposals and drafts are labelled Editor state and do not become persistent authored values until the existing typed Apply. This read-only comparison registers no commands or actions. Source withdrawal, kingdom change and close clear members and comparison content.

Focused validation: 18 Python inspector-schema checks, four Node suites (placement/layers, shared component renderer, translation and yaw), JavaScript syntax and actual map01/map02/map03 browser workflows. Fresh source reports supplied exact member lists for records with 1/55/31 source cells. All Retail/Current/Authored/Reviewed/Draft values were checked independently against metadata or staged inputs. Selecting each record's last member preserved exact Review and shared consent; Discard retained that anchor and removed proposal values. Desktop and 400px expanded comparisons were visually inspected. All project/import/history documents and fixture bytes stayed exact; zero page errors or mutation requests occurred. Persistent authored-layer separation is covered with a detached Node fixture, while browser fixtures had no authored placement override.

Private evidence: `local-output/sdk-20260909/worldmap-shared-record-inspector-20261009/`. No game, runtime attachment, native Build, Apply, install or disc export occurred. Source-preview coordinates do not establish gameplay resting transforms or visibility. The full SDK goal remains active and gameplay acceptance stays deferred.

## Retail and Current Viewport Comparison — 2026-10-09

In World ground, inspect a kingdom and choose **World placement layer** → **Current authored seeds**. The editor freshly reads the existing source-qualified placement API and verifies matching kingdom, project source key, disc, MAP and floor hashes before changing the scene. The same pure placement decoder and transform adapter now serve this viewport and World placements, with original exports retained for existing consumers. The editor server explicitly serves the new shared module.

Retail source seeds remain the initial layer. Switching to Current applies persistent record offsets and yaw to the same qualified source instances; imported source XYZ remains unchanged in the shared Inspector. **Displayed placement layer** and **Displayed seed X/Y/Z** show the active native coordinate representation separately. Ground geometry stays Retail. Selection, hierarchy filter, identities and camera are retained; framing/picking use the displayed scene. Returning to Retail restores exact source matrices. Unreviewed placement-dialog drafts are not Current authored state and are not included here. Unknown runtime visibility/resting fields remain Unresolved.

Failed source comparison retains the prior scene and resets the layer selector. Project/mode/source/session changes and late requests cannot publish an old comparison. Close, kingdom change or reinspection discard cached placement metadata. Current layer requires the supported placement capability. Source exports remain available only in Retail view; Current scene export remains in World placements, avoiding an export that differs from this displayed layer. Switching a layer cancels an outstanding source export.

Focused checks: 18 Python inspector-schema tests; four Node suites for placement qualification/layers, world geometry, hierarchy and shared Inspector; three module syntax checks. Actual browser fixtures were fresh private copies of the existing retail-imported reference, with supported authored offset changes (+32 X, +16 Y, +64 Z) and +512 yaw units applied through existing SDK Review/command ownership in each kingdom before browsing. No native Build was required. For all three kingdoms, browser checks independently computed native Current positions and yaw matrices, preserved Retail source coordinates/ground/filter/selection/camera, refused source export in Current and restored the exact Retail scene. A deliberately mismatched MAP hash response was refused atomically before the valid retry. Wide/400px Inspector views were inspected. The initial browser startup exposed a missing explicit shared-module server route; it was added and fresh workflows passed.

During browsing, fixture documents/imports/history/files stayed unchanged; the original reference project files also stayed exact. Zero page errors or browser command/Build/Run/Save/scene/selection/export requests occurred. Private evidence: `local-output/sdk-20260909/worldmap-retail-current-comparison-20261009/`, including preserved initial route-failure log. Authored commands were applied only to isolated fixture copies. No game launch, runtime attachment, native Build, installation or disc export occurred. This is authored source comparison, not gameplay coordinate/visibility acceptance; full SDK goal remains active.
