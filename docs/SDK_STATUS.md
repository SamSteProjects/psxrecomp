# Legaia SDK status — 2026-10-03

**Asset-reference instruction navigation (2026-10-03):** Dependency and Referenced by rows now offer Inspect reference instruction for decoded script→dialogue, flag, transition and named-scene relationships. The action uses the edge's structural P1/P2 owner and PC, refreshes its source catalog after ordinary scene navigation, and verifies owner/partition/index/extent/source key and any recorded hash before opening disassembly at the exact boundary. Unimported destinations do not prevent inspection of their imported source script. Busy, stale, closed and late-response guards remain in force. Runtime actor/model identity, execution and reachability remain unasserted.

Validation: 25 focused Python cases pass with private Retail source and no skips; four Node suites and both editor module syntax checks pass. The new suite covers P1/P2 source qualification, drift, unavailable/mismatched owners, source-only targets and exactly-once/stale/busy/close/late-response navigation. An outdated flag fixture now uses qualified ordinary SYSFLAG selectors and explicitly checks that unsupported extended dispatch stops before later references. Eight actual browser checks cover outgoing/incoming P1 flag sites, atomic dialogue PC15, P2 SCENE_CHANGE PC22 with an unimported destination, 540px Project controls, Town01→Dolk2 PC14 navigation, stale-key rejection and unchanged project bytes/authored state/history. Cross-scene navigation marks only the ordinary Active scene setting unsaved; returning restores the prior dirty state. Independent native MAN pointer/opcode checks confirm all four inspected source sites at decoded offsets4771/4774/28565/7466. Private proof: `local-output/sdk-20260909/asset-reference-instructions-20261003/parent/`. Screenshot inspected; owned helpers closed. No authoring, Save, Build, Run, installation or full-disc export occurred in the browser workflow. No immediate gameplay verification is required. See [reference-site navigation](legaia-asset-references.md#inspect-the-reference-instruction).

**Whole-record script flow overview (2026-10-03):** Actor and partition-2 disassembly now summarize verified entry reachability, cyclic components, encoded exits, undecoded targets and decoder stops, with paged source navigation. The branch workspace compares separate Retail, Current and reviewed Proposed overviews. Current/Proposed reports retain independently redecoded original anchors that a branch leaves unvisited; reached-path arrays keep their existing meaning. Missing or undecoded entries leave reachability unknown. Links open collapsed disassembly before focusing the exact row, and discarding a branch withdraws Proposed flow and its review status. Encoded reachability and closed cycles do not establish story activation, execution or nontermination. General control-flow authoring/live execution remain unfinished.

Validation: 47 focused Python cases pass with private Retail source and no skips, including branch history, Build/readback and HTTP regressions; both source-overview and branch Node suites pass. The overview suite covers an 8192-node cycle, dialogue boundaries, preserved unvisited anchors, unknown entries, malformed domains, pagination and disposal. Eight actual browser checks pass without page errors: Retail/Current cycle navigation, reviewed Proposed unvisited anchors, discard, 540px containment, unchanged files/overrides/history, unknown exits and paging. Independent per-node transitive reachability/mutual membership matches all three recorded graphs: Town01 actor0002 has 5 boundaries/one cycle; actor0011 Proposed retains 49 boundaries/two cycles and unvisited PCs 55, 57, 63. Private proof: `local-output/sdk-20260909/script-flow-overview-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. Browser inspection submitted no command, Build, Save or Run; no game, installation or full-disc export ran. This read-only feature requires no immediate gameplay verification. See [source-flow overview](legaia-script-flow-overview.md).

**Selective model face restoration (2026-10-03):** The removal dialog now offers restoration using listed removed Retail indices. Restored packets recover Retail face fields with current vector tables; retained groups keep their current settings and fully absent groups recover Retail settings. Preview and reviewed Apply preserve unrelated typed edits. Partial restoration retains the remaining removal binding; restoring all removals transitions to the ordinary typed format or clears the override when byte-exact Retail. Each Apply is one undoable command. This restores existing Retail packets only; general new-face allocation/addition remains unfinished.

Validation:13 focused Python cases and the expanded topology Node suite pass. Tests cover dropped groups, partial/cumulative recovery, retained vector/material fields, removed-owner rejection, all-restored typed/clear transitions and history. Six actual private-retail browser checks verify native Retail-index domain, independently reconstructed188→190 triangle review, wrong-hash rejection without state mutation,540px Apply to `tmd-content-v3`, exact Undo/Redo format/bytes and Save/reload/Build. Complete candidate/carrier readback preserves Current vectors and retained packet fields and every decoded neighbor within154547 source bytes. Package SHA256 `d7bed311677f882ae97792d3544155ab425ddb695a11fc740bd090d211d76d68`. Private proof: `local-output/sdk-20260909/model-face-restoration-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran; native restored-face appearance remains deferred.

**GLB interchange after face removal (2026-10-03):** The model GLB workflow now exports the qualified Current topology with a v2 binding that names every removed Retail face. Profiles are regenerated from Current bytes; Review qualifies typed edits against the original Retail removal binding. V2 reviews retain the complete removal audit and reject missing, conflicting or pending removal identities. Reviewed Apply preserves the normal model override, cumulative removals and prior typed edits. Count allocation/addition and arbitrary replacement remain unfinished.

Validation:27 focused Python cases pass with private Retail source and no skips; the expanded GLB Node suite verifies binding identities, complete removal audits and existing review/lifecycle guards. Six actual private-retail browser checks cover exact no-op Current export, selected-file vertex review, reduced proposed-model inspection/Return,540px Apply, exact Undo/Redo and Save/reload/Build. Independent candidate/carrier readback proves only byte3196 changes for object1 vertex1 X126→128, retaining188 triangles, material/normal/UV/color data and every decoded neighbor within154547 source bytes. Package SHA256 `036b2732b290e954c578de666d3f9b9b7fd8e30e8310f45efd61f4deaa186d8a`. Private proof: `local-output/sdk-20260909/model-removal-glb-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran; native appearance/shared-instance behavior remains deferred.

**Material editing after face removal (2026-10-03):** The native material Inspector now uses exact retained Retail group and face owners for comparisons and Reset. The versioned catalog handles compacted packets and fully dropped groups. CLUT/page/depth and shared group ABE drafts edit Current source words; complete candidate review audits actual Retail ownership and preserves the removal binding and unrelated normal/vertex edits. Removed faces/groups cannot become Current edit targets. GLB interchange after removal is now supported as described above. General topology allocation/addition remains unfinished.

Validation:18 focused Python cases pass with private Retail source and no skips, plus material workflow/mapping and donor Node suites. Seven actual private-retail browser checks cover native ownership, mapped Retail reset, independently patched CLUT/page/ABE review, all-instance scene proposal,540px Apply, exact Undo/Redo and Save/reload/Build. Full candidate/carrier readback proves only bytes2895/2898/2902 change, retaining188 triangles, vector/UV/color/normal data and every decoded neighbor within154547 source bytes. Package SHA256 `9458a47b0aa62d030a5c62eb017157c2adc8ffe889895b35c0b2b530dbf40150`. Private proof: `local-output/sdk-20260909/model-removal-materials-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran; native palette/VRAM/blend appearance remains deferred.

**Reference retargeting after face removal (2026-10-03):** Object-wide vertex and normal retargeting now remains available with a removal binding. Preview qualifies every matching Current operand against the reference lookup; the final candidate is independently audited against actual Retail ownership. Reviewed Apply preserves removed Retail identities, vector tables, native Current packet counts/layout and other edits. Removed faces are never retargeted. Material editing is now supported as described above. GLB interchange after removal is now supported as described above. General topology allocation/addition remains unfinished.

Validation:13 focused Python cases and both exact-user retarget Node suites pass. Seven private-retail browser checks cover normal4→3 across three retained words, vertex5→6 across one retained word, Current/Proposed toggles,540px reviewed Apply, exact Undo/Redo for both operations and cumulative Save/reload/Build. Whole-candidate and compressed-carrier readback matches independent raw-word patches at bytes2908/2916/2964/2988, retaining188 triangles and every decoded neighbor within154547 source bytes. Package SHA256 `5dfcc1ffed7111883201e380d28eff5fdcbc328fbfbdf22962de9101aed99ac9`. Private proof: `local-output/sdk-20260909/model-removal-retarget-20261003/parent/`. Narrow screenshots inspected; owned helpers closed. No game, installation or full-disc export ran. Native appearance and shared-instance behavior remain deferred.

**Retained-face editing after removal (2026-10-03):** The face Inspector now supports compacted Current packet identities with exact retained Retail owners. Reset to Retail copies the mapped face, and existing vertex/UV/RGB/normal-reference drafts use Current packet offsets. Preview audits the complete candidate against actual Retail ownership; reviewed Apply retains cumulative removal identities. Vertex/normal user navigation is restored for retained faces. Object-wide retargeting is now supported as described above. The material editor now supports this binding as described above. GLB interchange now preserves removal bindings; general allocation/addition is unfinished.

Validation:14 focused Python cases pass with private Retail source and no skips; the expanded primitive Node suite passes v1/v2/v3 mappings, draft/audit/hash and removed-owner rejection. Six private-retail browser checks verify native Current0→Retail1 inspection, mapped Reset, independent UV proposal bytes,540px reviewed Apply, exact Undo/Redo and Save/reload/Build. Full compressed-carrier readback proves only byte2896 changes (corner0 U0→17), retaining188 triangles, the removed quad, vectors/materials/normals/opaque bytes and every decoded neighbor within154547 source bytes. Package SHA256 `f6f3bee2fbada9ba1d5f76b19e645ce18a4ec51baaf586fe56d6f1b74c77b911`. Private proof: `local-output/sdk-20260909/model-retained-faces-20261003/parent/`. An additional actual browser API check verifies all-instance scene proposal with188 triangles, the reviewed hash and unchanged project bytes; the scene handoff retains removal metadata. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran; native UV appearance remains deferred.

**Reference inspection after face removal (2026-10-03):** Vertex/normal user lookup now qualifies the complete removal binding and reports exact Retail-to-Current face identities. Compacted Current indices display their retained Retail owners; removed Retail faces explicitly have no Current face. The lookup is restored in the vector Inspector. Retained-face editing/navigation now consume this mapping as described above. Object-wide reference retargeting is now supported as described above.

Validation:12 focused Python cases and both reference-decoder Node suites pass. Five private-retail browser checks cover removed-face labeling, retained vertex9 users with shifted identities, matching normal endpoint mapping,540px access and unchanged project files/overrides. No browser errors occurred. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/model-reference-faces-20261003/parent/`. No authoring, Build, game, installation or disc export ran; no immediate gameplay verification is required for this read-only inspector feature.

**Vector and file editing after face removal (2026-10-03):** Existing removal bindings now survive vertex/normal edits, object translation/rotation/scale, normal-length adjustment and same-layout TMD/OBJ/JSON imports. Candidates are audited against actual Retail ownership and retain the exact removed Retail face identities. Reference lookup now displays qualified Current-to-Retail identities as described above. Retained-face editing/navigation now consume the mapping. Reference retargeting is now supported; material editing is now supported; GLB interchange now preserves removal bindings. General topology allocation remains unfinished. See [supported editing after removal](legaia-model-face-removal.md#editing-after-removal).

Validation:11 focused Python cases and two Node suites pass. Six private-retail browser checks verify enabled vector controls, reduced-topology object preview, reviewed vector Apply, exact Undo/Redo, Save/reload and normal Build. Independent readback confirms only model byte3188 changes for object1 vertex0 X126→143, retaining188 triangles and all materials, normals, opaque bytes and decoded neighbors within154547 source carrier bytes. Package SHA256 `f21d1fd224cbf19bba111a1b7398bf00da59e0b7af1767d3afcc4f45b7ed084b`. Private proof: `local-output/sdk-20260909/model-topology-vectors-20261003/parent/`. The540px screenshot was inspected and owned helpers closed. No game, installation or full-disc export ran; native appearance remains deferred.

**Count-changing model face removal (2026-10-03):** The model viewer now reviews and removes whole existing triangles/quads, compacts retained packet groups inside the source allocation and updates native primitive counts. A versioned binding preserves cumulative Retail identities independently of Current dense indices. Object and vector-table identities remain fixed; supported poses refresh face ranges without changing vertex channels. Apply requires the reviewed candidate hash. Undo/Redo, Save/Open, Clear, further removal and normal Build are connected. Vector and same-layout file edits are now supported as described above; material editing is now supported; GLB interchange now preserves removal bindings; retained-face editing is now supported. Arbitrary replacement/allocation remains unfinished. See [face-removal workflow and limitations](legaia-model-face-removal.md).

Validation:12 focused Python cases pass with private retail source and no skips; face-removal and rigid-normal Node suites pass. Eight actual private-retail browser workflows verify review/domain/hash guards, Current/Proposed,540px Apply, exact Undo/Redo, Save/reload and Build. Additional checks cover cumulative Current-to-Retail mapping, Clear/Undo, fresh capability and closed preview resources with unchanged project files/history. Independent full-model/carrier readback proves Town01 model0009 object1 quad removal,190→188 triangles, unchanged vector tables/object identity and every decoded neighbor within154547 source bytes. Package SHA256 `c6bcc7a8ccd981960b07cbb8482c0699e8179ce161a66594a8a841120d5a138c`. Private proof: `local-output/sdk-20260909/model-face-removal-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran; native appearance and shared-instance effects are deferred.

**Component reference navigation (2026-10-03):** The entity Inspector now opens exact Asset Database records from supported model, initial-animation and donor-actor reference properties. Imported/Authored/Effective layers retain separate values and accessible reference names. Navigation resolves the active source scene independently of Project browser filters; the opened metadata Inspector keeps its normal tool actions. Missing, ambiguous, stale and busy navigation fails explicitly. See [component reference workflow](legaia-component-references.md).

Validation: three focused Node suites pass. Five actual private-retail browser workflows verify exact model details and viewer activation, native Enter,540px access and unchanged selection/project/saved bytes. An additional two-scene proof filters the browser to Dolk2 while Town01 remains active: the absent Town01 model reference still opens its enabled Inspector, and the Imported Clip opens the native animation-binding Inspector. Narrow screenshot inspected. Private proof: `local-output/sdk-20260909/component-references-20261003/parent/`. Owned helpers closed. No gameplay verification is needed for this feature; no game, Build, installation or disc export ran. Full runtime correlation and scene parity remain unfinished.

**Object-wide vertex-reference retargeting (2026-10-03):** The vector Inspector now finds Current/Retail faces using an existing vertex and navigates to their exact current face. Retargeting changes every matching stored corner within its object to another existing vertex. Preview verifies complete Current-user ownership and offers Current/Proposed geometry; Apply requires the reviewed candidate hash. Coordinates, stored normals, counts, packet layout, material edits, padding and other objects remain fixed. Faces may collapse. See [vertex users and retargeting](legaia-model-vertex-retarget.md).

Validation:19 focused Python cases pass with private retail source and no skips, plus five Node decoder/retarget/primitive suites. Ten actual private-retail browser checks pass through lookup/navigation, target/review guards, independent whole-model preview, Current/Proposed,540px controls, rejected proposal, Apply, Undo/Redo, Save/reload and normal Build. Complete compressed-carrier readback matches Town01 model0009 object1 vertex0→9, with only byte2912 additionally changed and decoded neighbors preserved within154547 source bytes. Package SHA256 `37c6b64a03abcf663ac64c00462153ca87a8cb5eaf2f870b274427a2942dedc7`. Private proof: `local-output/sdk-20260909/vertex-retarget-20261003/parent/`. Screenshot inspected; owned helpers closed. No game, installation or full-disc export ran. Gameplay acceptance stays deferred; general count-changing topology remains unfinished.

**Asset database keyboard navigation (2026-10-03):** Asset cards now have one Tab entry, Up/Down result browsing, Left/Right Open/Details actions and Home/End boundaries. Project PageUp/PageDown retain the action while moving across result pages. Stable asset/action focus survives redraw and temporary busy controls. Rendered scope tracking prevents focus transfer across changed projects/scenes/scopes; search and external controls keep focus. Parent busy handling now refreshes the Tab entry after project-resource discovery enables its buttons. See [asset keyboard browsing](legaia-asset-keyboard.md).

Validation: focused asset-navigation and existing hierarchy Node suites pass, along with editor syntax and diff checks. Eight actual private-retail browser checks pass for native Details activation, stable redraw/busy focus, search/empty behavior, paging1614 retained results across13 pages, scope reset and540px access. Project files, history and selection remain exact; no authoring, Save, Build or Run request occurs. Desktop/narrow screenshots were inspected and owned helpers are closed. Private proof: `local-output/sdk-20260909/asset-keyboard-20261003/parent/`. No immediate gameplay verification is required; source coverage and runtime-use limits remain unchanged.

**Scene animation normal-channel inspection (2026-10-03):** Supported scene tracks now carry optional raw normal evidence and complete rigid channels. The timeline offers **Source normal directions** for those tracks during scrub and Play. Unsupported actors and environment retain surface shading. Canonical posed scenes retain raw vectors in a separate `normal_source` field, never as a qualified render stream. Preparation verifies that every channel reproduces its vertex sample; Restore clears the mode and restores the exact scene. See [scene normal channels](legaia-scene-animation.md#source-normal-channel-diagnostic-2026-10-03).

Validation:19 focused Python cases and three Node suites pass with no skips. Six actual private-retail browser checks pass for Town01's42 animated actors in22 qualified tracks: mode/default pixel restoration, tick7 direction/vertex agreement, Play without geometry/texture allocation,540px reachability, exact Stop/Restore and unchanged project files/history. These22 retail tracks contain no lit source-normal triangles and correctly appear neutral; lit rotation behavior is covered by the focused synthetic vectors. Desktop/narrow screenshots were inspected. Optional normal validation is bounded to three million frame corners within the existing64MiB report; exceeding it omits the diagnostic, retaining vertex playback. Private proof: `local-output/sdk-20260909/scene-normal-pose-20261003/parent/`. Owned helpers are closed. No authoring, Build, game, installation or disc export ran; native GTE lighting and gameplay appearance remain deferred.

**Animated source-normal directions (2026-10-03):** The individual model viewer now rotates qualified stored normal directions through the supported frame's independent rigid object channels. Scrub and Play update vertex and normal buffers in place; surface shading remains the default. Every object, vertex span and triangle owner must match the frame, and unknown poses retain surface shading. This is analytic SDK Rz × Ry × Rx direction visualization, not retail GTE lighting. Static posed and assembled-scene diagnostics without qualified channels remain unavailable. See [source normal directions](legaia-model-source-normals.md#supported-rigid-frame-directions-2026-10-03).

Validation: three focused Node suites pass, including rigid rotation/order/translation/ownership guards, stale metadata withdrawal and existing scene animation behavior. Eight actual private-retail browser checks pass for mode restoration without uploads, in-place scrub, Play, object slicing,540px controls, unknown-pose fallback, static compatibility and byte-exact project files. Independent Python pose math matches1488 private test directions across10 objects at frames0/1/14 with zero error. The real Vahn idle model has zero lit source-normal triangles and remains neutral; colorful screenshots use explicit private direction-only test data. Owned browser/server handles are terminal. Private proof: `local-output/sdk-20260909/rigid-normal-pose-20261003/parent/`. No authoring, Build, game, installation or disc export ran. Native appearance remains deferred.

**Object-wide normal-reference retargeting (2026-10-03):** The vector Inspector now retargets every qualified Current use of the selected normal within its object to another existing normal. Preview binds the complete Current-user ownership report, shows exact reference-word changes and offers Current/Proposed source-direction comparison. Apply requires the reviewed candidate hash and records one existing model replacement command. Coordinates, geometry, other references, padding and inherited material edits remain intact. See [normal retargeting](legaia-model-normal-retarget.md).

Validation:10 focused Python cases and both Node retarget/primitive suites pass with no skips. Nine actual private-retail browser checks pass through target/review guards, independent whole-model preview, Current/Proposed,540px controls, rejected mismatched proposal, one Apply, exact Undo/Redo, Save/reload and normal Build. A final read-only preview verifies the finished labels and narrow layout. Complete model/carrier readback matches Town01 model0009 object1 normal3→4: only bytes2940/2988 additionally change, decoded neighbors remain exact within154547 source bytes. Package SHA256 `31c7e714c2f90c3ba82496970558cb3371df67fbe87609cae9cb6f7e4b401b3f`. Private proof: `local-output/sdk-20260909/normal-retarget-20261003/parent/`. Owned helpers are closed. No game, installation or full-disc export ran; native lighting remains deferred.

**Precompile multi-configuration acceptance (2026-10-03):** The existing synthetic static-overlay fixture now builds and executes both Release and Debug for every inventory/body variant when using a multi-configuration generator. Shared generated sources must reach both configurations after growth, shrinkage, body-only changes, split/monolithic switching, empty output and regrowth. Single-configuration behavior remains unchanged. See [release parity evidence](legaia-release-parity.md#ninja-multi-config-acceptance-2026-10-03).

Validation: Ninja Multi-Config1.13.2, CMake4.2.3 and MSYS2 UCRT GCC16.1.0 pass both focused tests in12.745s with no skips: nine recipes times two configurations,18 executable sum checks, final no-change builds and sparse numeric filename ownership. A restricted invocation failed before configuration while starting the Winget Ninja executable; the approved retry passes. GNU Make is not installed and its coverage remains open. Private logs/tool/source identities: `local-output/sdk-20260909/precompile-ninja-multi-20261003/parent/`. No runtime implementation, game executable, installed mod, retail payload or gameplay acceptance changed; no game ran.

**Collapsible scene tools and viewport space (2026-10-03):** Existing secondary scene controls now live in a closed-by-default Scene tools drawer. Nodes move intact, retaining their handlers and drafts. The open drawer scrolls within available height, reserving180px for the scene where space permits. Runtime notices, field-map notes, proposed-scene restore controls, active actor-group controls and script-target controls stay outside. The viewport panel now has a zero minimum height, fixing expansion below the workspace. See [scene tools](legaia-scene-tool-drawer.md).

Validation: six actual private-retail browser checks pass with no page errors. The desktop scene area is640px collapsed and279px expanded; at540px it is389px collapsed and at least175px in the open-drawer check. Existing snap settings survive collapse/reopen. Project files, history and selection remain exact; no authoring, Build or game request ran. The existing narrow Hierarchy & assets tab exposes the keyboard hierarchy, correcting the prior Scene-tab-only limitation note. Desktop and narrow screenshots were visually inspected; the hierarchy Node suite still passes. Private proof: `local-output/sdk-20260909/scene-tool-drawer-20261003/parent/`. Owned helpers are closed.

**Hierarchy keyboard browsing and stable focus (2026-10-03):** The rendered SDK hierarchy now has one Tab entry. Arrow Up/Down and Home/End move focus across visible actor, draft, environment and resource rows without changing selection. Native Enter/Space retain existing row actions. Same-scene rebuilds restore the focused stable ID; filtering falls back safely and does not steal focus from search. Empty lists remain reachable; scene/context changes do not transplant old focus. See [hierarchy keyboard workflow](legaia-hierarchy-keyboard.md).

Validation: focused Node checks pass for roving focus, boundary keys, filtered/empty lists, context changes, modifiers and native selection keys. Seven actual private-retail browser checks pass with no page errors, including one Tab entry, mixed row browsing without requests, Enter selection through the existing API, rerender focus, search/empty behavior and exact project files/history. The original check covered desktop focus after resize and observed the hidden sidebar in the540px Scene tab. The later scene-tools proof verifies keyboard access through the existing Hierarchy & assets tab. No authoring, Build or game request ran. Private proof: `local-output/sdk-20260909/hierarchy-keyboard-20261003/parent/`. Owned helpers are closed.

**Face/normal Inspector navigation (2026-10-03):** Lit face controls now inspect their Current stored normal directly: one flat reference or the selected Gouraud corner. The vector Inspector opens the exact object and normal index, and its existing normal-user lookup returns to the source face. Any face draft blocks navigation until Apply or explicit Discard. Vector drafts withdraw reference results; explicit Discard now refreshes lookup availability. Post-Apply close handling distinguishes intentional navigation from background model refresh. See [normal navigation](legaia-face-normal-references.md#current-normal-navigation).

Validation: the expanded Node primitive suite passes for flat/Gouraud target ownership, detached bindings, UV-draft rejection, busy and stale-source guards. Seven actual private-retail browser checks pass with no page errors: initially clean state, UV/reference draft guards,540px controls, exact object1 normal3 navigation, vector draft withdrawal/discard, return to primitive1 and unchanged project files/history. No authoring, Build or game requests ran. Private proof: `local-output/sdk-20260909/face-normal-navigation-20261003/parent/`. Owned helpers are closed. Native lighting and runtime appearance remain deferred.

**Native face normal-reference editing (2026-10-03):** The existing face editor now selects existing object normals directly, with one shared operand for flat faces and per-corner operands for Gouraud faces. Unlit packets expose no normal editor. V2 source metadata and exact reference-word audit guards preserve counts, geometry, normal coordinates, materials, padding and prior edits. Source normal directions are available in Current/Proposed comparisons; the object extraction now slices normal metadata alongside its triangles. Existing reviewed Apply, Undo/Redo, persistence and normal Build carry the edits. See [face normal references](legaia-face-normal-references.md).

Validation:21 focused Python cases pass with private source and no skips; the Node primitive workflow and new V2 source/audit guards pass. Eight actual browser checks pass, including domain/shared ownership, independently matched preview, Current/Proposed source directions,540px layout, Apply, exact Undo/Redo, Save/reload and Build. Complete model/carrier readback matches: Town01 model0009 object1 primitive1 changes normal2 to3 at byte2940, adding only one changed byte to the inherited authored fixture; decoded neighbors and154547-byte compressed capacity remain exact. Package SHA256 `9a784f6398809281b8fca293aef9c800cd56381273d217b036e29943a7e92075`. Private proof: `local-output/sdk-20260909/model-primitive-normals-20261003/parent/`. Owned helpers are closed. No game, install or full-disc export ran; native appearance remains deferred.

**Stored normal reference navigation (2026-10-03):** The vector Inspector now finds qualified faces using a selected stored normal, with separate Current/Retail references, exact source-word offsets and flat/Gouraud corner ownership. Inspect current face opens the existing face editor at the source object and primitive. Requests bind the inspected model hash and project source key; selection changes and closing withdraw results. This is read-only source navigation. See [normal reference navigation](legaia-model-normal-users.md).

Validation: nine focused Python cases and the Node source/DTO guards pass. Seven actual browser checks pass with no page errors: exact private-retail report, distinct Current/Retail layers,540px layout, face navigation, selection invalidation, pending-response cleanup and unchanged files/history. Town01 model0009 object1 normal1 has one Retail operand at byte2940 and zero Current operands after its earlier reference edit. Independent raw packet reads match both layers. No command, Build or game requests ran; owned helpers are closed. Private proof: `local-output/sdk-20260909/model-normal-users-20261003/parent/`. Runtime visibility and native lighting remain deferred.

**Object-level stored-normal rescaling (2026-10-03):** The vector Inspector now rescales an existing object's nonzero normals to an explicit encoded length1..32767, with exact integer midpoint rounding and zero-vector retention. The client previews the same arithmetic with BigInt. Qualified Current/Proposed object previews, explicit Apply, history, persistence and normal Build reuse existing replacement infrastructure. Geometry, normal references, padding, material edits and other objects stay separate. An object-preview bug retaining full-model triangle normals after triangle slicing is also fixed. See [normal rescaling](legaia-model-normal-length.md).

Validation: eight focused Python checks and normal-length/source-direction Node suites pass. Eight actual browser checks pass with no page errors or game requests, including source domain guards, exact proposal, Current/Proposed,540px layout, one Apply, history, Save/reload and Build. Independent80-digit decimal construction matches the whole candidate:11 normals,14 coordinate words and19 bytes change; full compressed carrier readback preserves decoded neighbors and prior edits within154547 source bytes. Package SHA256 `509fe8cac4fe103973a10c2f19ddee0fa0275130b9aac710d6feda2729dd8f42`. Private proof: `local-output/sdk-20260909/model-normal-length-20261003/parent/`. Owned helpers are closed; no game, install or disc export ran. Native lighting acceptance remains deferred.

**Restore selected source walls to retail (2026-10-03):** Wall rectangles now offer Set wall bits or Restore retail walls. Restoration uses each selected quadrant's own source value, preserving mixed blocked/unblocked cells, outside overrides and floor tiers. Existing Review, Proposed/Return, one Apply, Undo/Redo, Save/Open and normal Build handle the operation; changing the choice withdraws prior review, and no-op restoration disables Apply. See [wall rectangle workflow](legaia-collision-rectangles.md#retail-restoration-evidence-2026-10-03).

Validation: five focused Python cases pass with private retail source and no skips; wall rectangle/viewport Node suites pass. Eight actual browser checks pass with no page errors or game requests, including mixed-bit review, retained comparison,540px controls, Apply, exact history, Save/reload, no-op and Build. Independent complete73,728-byte MAP readback returns the selected area to retail and changes only byte32767's retained outside wall bit; every floor nibble stays exact. Package SHA256 `143ca9497ec65065a56765605cedc07ff4e7f782335019c1880399ebeaf8b036`. Private proof: `local-output/sdk-20260909/wall-retail-restore-20261003/parent/`. Owned helpers are closed; no game, install or disc export ran. Native movement acceptance remains deferred.

**Shared NPC capacity gate for growth candidates (2026-10-03):** Compressed and raw-streaming appended-NPC preparation now uses the same retail executable qualification and initial-placement lower-bound assessor as normal Build. Candidate counts are checked before archive repacking; existing-only edits retain their prior compatibility. Per-scene growth audits and Review NPC output retain qualified pool evidence. A stale review limitation claiming normal Build rejects every draft is corrected.

Validation:17 focused Python cases passed with private source and no skips, including distinct Town01/Dolk2 growth rejection before either repacker, unchanged project files/history, valid rebuilt archive readback with retained donor clones/facing edits, normal Build regression and review/HTTP/multi-scene guards. After the review metadata addition, all six review cases pass, including detached pool evidence. Both Node review suites and five existing-only streaming/export snapshot regressions pass. No game, full-disc export or install ran. Complete native demand and gameplay acceptance remain deferred. See [shared growth gate](legaia-npc-actor-pool.md#shared-growth-candidate-gate-2026-10-03).

**Shared actor-pool consumers (2026-10-03):** Build audit metadata now qualifies nine complete retail functions and records six setup allocation sites, including scenery, two unconditional later allocation attempts and a conditional setup object. Review Build explains that intervening script execution prevents treating those attempts as an additive capacity budget. The existing proved initial-placement rejection remains unchanged. See [qualified shared consumers](legaia-npc-actor-pool.md#shared-consumers-qualified-on-2026-10-03).

Validation: six focused Python checks pass with private retail source and no skips, including a fresh normal Build and complete carrier readback; Node review guards pass. The packaged audit retains all six semantic sites after private-path filtering. No browser, game or export ran for this follow-up. Scenery lookup, script allocation/release and native scene completion remain deferred.

**Retail NPC actor-pool lower bound (2026-10-03):** Normal Review Build/Build now qualify the complete SCUS executable and initially seven retail function spans, derive the143-slot/216-byte actor pool, and reject unavoidable initial-placement overflow before MAN encoding. Source setup evidence establishes the anchor plus partition-1 loop; successful audit metadata keeps other scenery/channel/script demand unknown. Candidate features stay disabled and runtime allocation/gameplay unverified. See [pool check and evidence](legaia-npc-actor-pool.md).

Validation: six focused private-enabled Python checks and existing Node review guards pass. A bounded instruction harness executes the actual pool initializer/pop/failure path:143 distinct slots, then zero without memory changes. Six browser checks prove a normal one-draft package plus a real91-draft Town01 blocker (minimum144 nodes), disabled reviewed Build, unchanged authoring and540px layout. Independent full carrier readback preserves the earlier candidate MAN and fixed-span ownership. Package SHA256 `e8907db2b03619303d72cf3e09fbe2ac82bff7815534733d15c9337a00443c06`. Private proof: `local-output/sdk-20260909/npc-runtime-source-20261003/`. Helpers are closed; no game, install or disc export ran. Full runtime demand/acceptance remain deferred.

**Packet-group texture-binding copy (2026-10-02):** The source-binding picker now fills all textured primitives in a qualified target group in one draft action, with explicit target count. Other group/object drafts, group ABE, untextured rows, target UVs/geometry and source-owned bits remain separate. The complete resulting batch validates before draft replacement; over-budget groups reject atomically. Review, Proposed/Return, one Apply, history, persistence and Build reuse the existing material workflow. See [group copy](legaia-material-binding-picker.md#packet-group-copy-evidence-2026-10-02).

Validation: focused donor/material Node guards and seven actual browser workflows pass. Fresh effective-model hashes verify Undo/Redo. Independent complete TMD construction and packaged carrier readback match:14 target primitives,13 changed rows,26 CLUT/TPage word changes and39 additional bytes, preserving earlier edits and decoded neighbors. Package SHA256 `f1e9c622f00bf4b07fbee0ef1926ecd83872e8430125c94ebda325effcfd39c0`. Private proof: `local-output/sdk-20260909/material-group-binding-20261002/parent/`. Helpers are closed; no game, install or disc export ran. Native appearance/residency acceptance remains deferred.

**Imported model texture-binding picker (2026-10-02):** The material editor now browses active-scene AssetDB models and qualifies their Current source primitive bindings. Explicit Copy fills page/depth/indexed CLUT draft controls while retaining target UVs, geometry and blend flags. Review/Apply, Proposed/Return, history, persistence and normal Build reuse the existing source material command. See [binding picker](legaia-material-binding-picker.md).

Validation: three catalog Python cases, donor Node guards and the existing material lifecycle suite pass. Seven actual browser checks pass through one Apply and Build; a separate visual follow-up verifies UTF-8 labels and540px layout. Independent complete TMD construction/readback proves Current-to-Proposed bytes1102/1103/1106 only, retaining prior ABE byte1095; the entire carrier's neighboring decoded bytes stay unchanged. Package SHA256 `a952ee4f6443068d63f8ddc5b6f636aa31168d3625851d01fcc6a14d0e8a89a3`. Private proof: `local-output/sdk-20260909/material-binding-picker-20261002/parent/`. Helpers are closed. No game, install or disc export ran; UV suitability, live residency, palette animation and native blend appearance remain deferred.

**Assigned actor animation GLB interchange (2026-10-02):** Qualified appearance/initial-clip assignments now export and preview the assigned existing rigid pose. V2 sidecars bind the selected actor, imported clip contribution owner and inherited model witness; the export/review names ownership before Apply. Changes use the owner's existing AnimationChannels command, preserving the selected actor's original clip edits and assignments. Fresh witness/source checks and existing shared-axis conflict guards remain in force; unassigned v1 sidecars remain compatible. See [assigned GLB workflow](legaia-assigned-animation-glb.md).

Validation: four distinct private-retail Python workflow cases and the v1/v2 Node guard suite pass with no skips. Eight actual browser workflows pass through owner-labelled review, retained pose Return,540px controls, explicit Apply, Undo/Redo, Save/reload and normal Build. Independent complete ANM/MAN readback matches: town0b actor0019 retains clip0013 edits; witness0049 owns the clip0012 GLB change. Only ANM bytes8880/10336 and MAN byte9471 differ from retail. Package SHA256 `2d9eaec92f5076624af50f568c6494cd2f01b4b3b27b7f39becb60f2b3ad0aa7`. Private proof: `local-output/sdk-20260909/assigned-animation-glb-20261002/parent/`. No game, install or disc export ran, and helpers are closed. Native clip selection/timing and shared-user gameplay remain deferred.

**World source yaw rotation ring (2026-10-02):** World placements now offers an exclusive source-yaw ring with encoded-unit snapping, perspective-correct frozen-plane pointer conversion, continuous angle unwrapping and 0..4095 wrapping. Shared-record confirmation remains explicit. Temporary previews preserve positions and update every affected instance; Review and Apply use the existing source-qualified command, Undo, persistence, Build and export path. Current comparison gates hidden drafts and cancellation restores prior values/review. See [source yaw ring](legaia-worldmap-placement-yaw.md).

Validation: three focused Node suites and two private-retail Python source/package regressions pass with no skips. Seventeen browser checks pass, including both turn directions, wrapping, independent matrices and unchanged positions for all57 shared instances, cancellation, tool switching,540px controls, one Apply, Undo/Redo, Save/reload, normal Build and stale-source withdrawal. Independent full MAP readback matches X1280/Y256/Z256/yaw448; prior offsets persist and only the two yaw bytes additionally change. Package SHA256 `4a953cf8acfb12105dd121b7c3f6416f9469bfa00907ef4c2999d4e9bc9de6bf`. Private proof: `local-output/sdk-20260909/worldmap-placement-yaw-20261002/parent/`. No game, install or disc export ran; helpers are closed. Native runtime behavior remains deferred.

**World source viewport translation handles (2026-10-02):** World placements now offers source X/Y/Z pointer handles, 1/16/64/128-unit snapping and Frame anchor. Explicit shared scope is required. All affected instances and numeric offsets preview together; release retains a draft, Review qualifies it, and Apply alone records one command/Undo step. Cancellation restores prior draft/review state, and source/camera/layout changes invalidate frozen gestures. A dialog-close race was fixed so cancellation cannot clear another command's busy state. See [translation handles](legaia-worldmap-placement-gizmo.md).

Validation: two focused Node suites and fourteen Python regression cases pass with private input and no skips. Fifteen browser checks pass, including nonzero source/display X/Y/Z movement for all57 shared instances, cancellation, 540px layout, source invalidation, one Apply, Undo/Redo, Save/reload and normal Build. Independent complete MAP readback agrees exactly: record0477 is X1280/Y256/Z256/yaw1536, and only four retail source bytes differ. Package SHA256 `d15d8464e9486a9463dac0b5653e1005aadd9fa942c13e11ebf95fee8d28b6b7`. Private proof: `local-output/sdk-20260909/worldmap-placement-gizmo-20261002/parent/`. No game, install or disc export ran; owned helpers are closed. Native behavior and gameplay verification remain deferred.

**Current/Proposed world placement GLB export (2026-10-02):** World placements now downloads complete qualified kingdom scenes with applied record transforms or an exact reviewed proposal. Exports retain retail geometry, shared meshes, textures and ground, add source/current/exported MAP identities and per-instance retail/exported transform provenance, and preserve unknown runtime visibility/resting state. Proposal export does not Apply, Save or Build. The browser verifies representation, review identity, MAP hashes and binary digest, and rejects late or stale downloads. Existing World ground exports stay retail-source. See [authored world export](legaia-worldmap-placement-export.md).

Validation: six focused Python cases pass with private input and no skips, including unchanged legacy source exports. Independent all-three-kingdom MAP construction verifies every exported translation, yaw and record hash; geometry/image binaries remain identical to retail exports. Node guards validate actual private artifacts. Seven browser scenarios pass with no commands, game requests or page errors; Current and Proposed downloads match independent artifacts byte-for-byte, each with302 entities and57 changed source seeds. Saved project/import/Build files remain exact. The Current MAP hash matches the previously verified Build payload. Private proof: `local-output/sdk-20260909/worldmap-placement-export-20261002/`. No game, install or disc export ran.

**World source placement authoring (2026-10-02):** The World placements viewport now edits qualified shared object-record offsets and yaw for all three walk kingdoms. Source record selection and mesh picking, effective coordinates, shared-record scope, Current/Proposed comparison, frame/orbit, reviewed atomic Apply, Undo/Redo, Save/Open, Authored assets and normal Build are connected. Exact field masks preserve cells, anchors, model references, flags, other axes and opaque bytes. Disjoint MAP overlays compose; conflicting writes reject. Source spawn seeds remain separate from script-evaluated resting positions and visibility. See [world placement workflow](legaia-worldmap-placement-authoring.md).

Validation:17 focused Python cases pass with private source input and no skips, including all-three-kingdom source/package readback and ordinary Build regressions. Node source/review guards and independent transform arithmetic pass. Eight actual browser scenarios verify pending selection and Save/history guards, explicit shared scope, Proposed GPU pixels/matrices,540px controls, history/persistence, normal Build and actual GPU mesh selection. Independent browser-package readback matches all73,728 MAP bytes and changes only bytes15265/15275 against retail; shared record0477 affects57 seeds. No page errors, game requests, installs or disc exports ran. Private proof: `local-output/sdk-20260909/worldmap-placement-authoring-20261002/`. Gameplay acceptance remains deferred.

**Source NPC candidates in normal Build (2026-10-02):** Saved donor drafts now enter inclusive v2 Build review and normal package generation for qualified compressed MAN scenes whose complete candidate fits the original consumed stream. Two source-hashed overlays update that stream and its descriptor size word; carrier size, pointers, neighboring payloads, TOC and disc layout stay unchanged. Supported existing actor/P2 edits compose after append, while other asset overlays retain the normal pipeline. Streaming or oversized additions remain rejected. Packages identify source candidates and keep their feature disabled by default. Native allocation, spawning, scheduling and opaque script behavior remain unverified. See [NPC Build boundaries](legaia-npc-build-candidates.md).

Validation: eleven focused Python checks and sixteen ordinary Build regressions pass with private retail input and no skips; legacy and v2 Node review guards pass. Independent Town01 package readback verifies donor scripts, reached spawn-reference rebasing, existing placement/facing composition and counts `[36,53,39]` to `[36,54,39]`. Optimal LZS uses24,856 bytes within the original24,894-byte stream; decoded MAN grows45,338 to45,917 bytes. Four actual browser scenarios verify inclusive read-only review,540px controls, reviewed Build and unchanged authored/import files with no game requests or page errors. No game, install or disc export ran. Private proof: `local-output/sdk-20260909/npc-normal-build-20261002/`. This supersedes earlier blanket normal-Build draft rejection statements; broader gameplay acceptance remains deferred.

**World-map source GLB export (2026-10-02):** World ground inspection now connects to private GLB downloads for all resolved source placements plus terrain, terrain alone when the placement layer is hidden, or one selected source entity. Shared meshes, source transforms, embedded matched textures and source provenance use the existing scene exporter. Fresh source checks bind exports to the imported disc and current project; late responses after closing or changing sources cannot trigger downloads. Exported placement seeds retain unknown runtime resting positions and visibility. Exports create private artifacts without authored commands or Build/disc output. See [world-source export](legaia-worldmap-export.md).

Validation: 16 focused Python cases passed with private retail input and no skips; three Node guard suites and frontend syntax checks passed. Independent all-three-kingdom readback verifies source world corners, reflected winding, shared meshes, UVs, stored colors, embedded PNG pixels and provenance. Nine actual browser scenarios pass, including five downloaded artifacts, ground-only visibility scope, selected seed scope, 540px controls, cancelled late responses and stale-source withdrawal. Downloaded geometry binaries and normalized metadata match the independent exports. Blender 5.2.2 LTS imports the complete map01 scene with 302 entity roots, 303 mesh objects, 67 materials and 60 images; all local triangles match, and maximum world-coordinate float error is 0.0009765625 source unit. Saved project/import/Build files remain unchanged; no game, authoring command or disc export ran. Private proof: `local-output/sdk-20260909/worldmap-glb-20261002/`.

**Scenery group source-angle rotation (2026-10-02):** The existing anchor rotation workflow now accepts every integer source yaw delta from 0 through 4095, alongside its compatible quarter-turn controls. A frozen Q30 quarter-wave table and signed integer nearest-half-away rounding produce reviewed X/Z positions; cardinal turns remain exact. The editor independently checks the same arithmetic before accepting a report. Review, retained Proposed/Current inspection, atomic Apply, Undo/Redo, Save/Open and normal Build preserve source Y, other rotation axes, shared descriptors and unrelated components. Rounded positions can change distances slightly; this authoring convention does not establish retail GTE rounding or gameplay acceptance. See [group rotation workflow](legaia-scenery-group-rotation.md).

Validation: 19 focused Python cases passed with no skips; two Node guard suites and frontend syntax checks passed. All 4096 angles match between Python integers and JavaScript BigInt for six signed displacement pairs, with identical frozen tables. Twelve actual browser scenarios verify custom angle review, invalid-input rejection, retained Proposed/Current comparison, history, Save/reload, normal Build, cancellation and stale-state withdrawal; the 540px layout was visually inspected. Independent renderer matrices and reopened full 73,728-byte MAP package readback match the reviewed 45° proposal. Only bytes 171/256/260/267 change against the prior authored fixture; source Y, other axes, shared records, prior Collision and retail MAP remain intact. No game or disc export ran. Private proof: `local-output/sdk-20260909/scenery-group-angle-20261002/`.

The SDK is functional for supported offline authoring workflows, but the full editor and runtime parity objective is incomplete. Gameplay verification is deferred at the user's request. No new game launch is needed to review the work below.

**Source-normal model diagnostic (2026-10-02):** The static Model shading control now offers source-normal direction colors alongside the default textures/stored colors. Checked raw per-corner TMD normals follow flat/Gouraud references and quad triangulation; unlit or invalid references remain unavailable, and zero/singular directions display gray. One inverse-transpose display transform includes the Y reflection. Existing normal-vector/reference authoring is visible through Retail/Authored comparison, history, Save/Open and normal Build. Animated poses explicitly disable the diagnostic; assembled posed scene geometry does not retain static normal metadata. This visualizes source directions without reconstructing retail lighting.

Validation: 43 focused Python cases passed with private retail input (no skips), two Node guard suites and frontend syntax checks passed. Independent raw decoding matches all119 Town01 models:404lit and14,321unlit triangles, with no invalid or zero corners. Ten actual browser scenarios verify zero uploads on mode flips, exact default framebuffer restoration, normal-vector Apply/history/persistence,540px wrapping, animation playback/disablement and normal Build. Actual WebGL pixels independently prove Y reflection and unchanged picking with no GL errors. Package readback adds only bytes3332/3333/3335 to the previous authored model, preserving its material/reference edits, vector padding, decoded neighbors and154,547-byte compressed capacity. No game or disc export ran. See [source-normal workflow](legaia-model-source-normals.md). Private proof: `local-output/sdk-20260909/model-source-normals-20261002/`.

**Scenery group quarter-turn rotation (2026-10-02):** Selected static decorations can rotate their source X/Z layout around a selected anchor by 90°, 180° or 270°, with the same delta added to each source yaw. Exact integer arithmetic preserves distances and the anchor position. Qualified Review, retained Proposed/Current scene comparison, atomic Apply, Undo/Redo, Save/Open and normal Build are connected. Shared source descriptors and unrelated overrides remain intact. This edits source yaw while retaining X/Z rotation axes; it is not arbitrary three-axis rigid rotation.

Validation: seven focused Python cases passed (no skips), two Node guard suites and frontend syntax checks passed. Twelve integrated browser scenarios plus a bounded 540px control-layout regression passed. Independent expanded matrices match the actual Proposed renderer transforms; reopened full 73,728-byte MAP packages match independent source construction. Only bytes171/256/260/261/267 change against the saved Collision/offset fixture. Source MAP and prior Collision remain unchanged; no game or disc export ran. Gameplay visibility, script transforms and collision acceptance remain deferred. See [group rotation workflow](legaia-scenery-group-rotation.md). Private proof: `local-output/sdk-20260909/scenery-group-yaw-20261002/`.

**Scenery viewport yaw handles (2026-10-02):** Rotate scenery Y previews source-bound transforms without project writes during a drag. Individual static decorations retain cell ownership; placed scenery requires explicit shared-transform enable. Absolute-angle snapping, Undo/Redo, Save/Open and normal Build use the existing Environment command/writer. Resize, Escape and stale-source changes cancel previews; actor movement remains available. Preview uses source `Rz * Ry * Rx` and one display Y reflection.

Validation: ten focused Python cases passed with the private retail disc (no skips), the Node rotation guard suite and frontend syntax checks passed, and twelve integrated browser checks plus an actor-handle regression passed. Independent package readback changes only yaw bytes171 (0→4) and6987 (8→12), preserving prior Collision, offsets, grid ownership and other axes. No game was launched or disc output written. Runtime visibility, scripts and collision acceptance remain deferred. See [scenery yaw workflow](legaia-scenery-rotation-gizmo.md). Private proof: `local-output/sdk-20260909/scenery-yaw-20261002/`.

**Source-bound GLB material editing (2026-10-02):** Fresh profile v6 adds
`_LEGAIA_SOURCE_MATERIAL` for full stored CLUT/TPage words and shared group ABE.
Exact integer primitive aliases and whole-group transparency aliases must agree.
Qualified masks preserve reserved CLUT bits, source ABR, other mode bits, row
commands and allocation. Untextured CLUT/TPage retain -1; group ABE remains
editable. Existing source positions, UV/RGB, normals and references compose;
legacy profiles retain their earlier field permissions. Review/Proposed
inspection/Apply/history/Save/Build use the normal model replacement workflow.
Shader assignments and texture images are separate; static associations may
remain partial. Retail blend/appearance acceptance remains deferred. See
[material GLB workflow](legaia-model-glb-materials.md).

Validation: 44 focused Python cases passed with the private retail disc (no
skips), two Node guard suites and frontend syntax checks. Actual Blender 5.2.2
no-op roundtrips are byte-exact; independent CLUT/group ABE, TPage and untextured
sentinel proofs change only bytes131/138, byte142 and byte299 respectively.
Twelve integrated browser checks cover fresh exports, no-op, reviewed source
fields, Proposed/Return, 540px layout, Apply/history/Save/stale withdrawal and
normal Build. Reopened package readback retains prior normal-reference/XYZ
bytes2940/3332 and adds only material bytes131/138, preserving neighboring data
and the 154,547-byte compressed capacity. No game was launched and no disc output written.
Private proof: `local-output/sdk-20260909/model-glb-materials-20261002/`.

**World-map source placement inspection (2026-10-02):** **World ground** now
opens a source scene with 301/272/236 sparse model placements in map01/map02/map03.
The hierarchy, mesh picking, Frame selected and Source model placements toggle
expose stable entity IDs, MAP cells, record hashes, dictionary slots and source
XYZ. Column-major source yaw/translation becomes a row-major renderer transform
with one display Y flip. The ground asset and source coordinates remain unchanged.
This is read-only; source changes withdraw geometry and pending-close cancels reads.
Runtime visibility, script-adjusted resting positions and animation remain
unverified. Model textures are partially resolved and missing associations stay
explicit. See [placement workflow](legaia-worldmap-placements.md).

Validation: eleven focused Python cases passed with the private retail disc
(no skips), plus ground and placement Node guards and frontend syntax checks.
Independent raw-source comparisons match every seed position, rotation, record
hash, model slot, loaded model topology and source-member hash in all kingdoms;
ground geometry remains unchanged. Nine integrated browser checks cover actual
rendering, hierarchy/coordinates, mesh picking, toggles, camera controls, 540px
layout, source withdrawal, pending-close and exact saved project/Build file hashes.
No game was launched or disc output written. Private proof:
`local-output/sdk-20260909/worldmap-placements-20261002/`.

**World-map walk-ground workspace (2026-10-02):** The editor's **World ground**
resource action now opens source-backed textured 3D ground for map01, map02 and
map03 through the shared scene renderer. The importer qualifies the overlapping
kingdom carriers, exact 0x12000 MAP footprint, slot-2 MAN floor LUT and slot-0
TIM atlas. Orbit/zoom, Frame ground, Top view, Wireframe and source details are
read-only; source changes withdraw retained geometry and closing pending reads
releases controls. Imported field selection, authored state, history and Build
files remain unchanged. Source Y-down coordinates flip only at the renderer.
Overview/MAPDSIP, script-managed resting transforms, sky/fog and runtime parity remain pending.
See [world-ground workflow](legaia-worldmap-geometry.md).

Validation: six focused Python cases passed with the private retail disc (no
skips), plus Node source/geometry/texture guards and frontend syntax checks.
Independent readback matches every ordered vertex, triangle, UV and visible-cell
selector in all three kingdoms. Visible cells are 16,251/16,381/16,374; source
texture coverage is 23/23, 17/18 and 15/16. Missing palettes stay explicit, without
fallback textures. Eight browser checks cover actual three-kingdom rendering,
camera controls, 540px layout, stale withdrawal, pending-close and unchanged
project files. No game was launched, no disc output written. Private proof:
`local-output/sdk-20260909/worldmap-geometry-20261002/`.

**Source-bound GLB normal-reference editing (2026-10-02):** Fresh profile v5
adds `_LEGAIA_SOURCE_NORMAL_INDEX` for selecting an existing normal within the
source object. Immutable corners retain packet ownership; flat references and
all raw XYZ aliases must agree. Unlit index -1 and XYZ sentinel remain explicit.
Changed references use `tmd-content-v3`; older content versions keep normal
references immutable. Review/Apply/history/Save/Open and normal Build compose
reference changes with earlier authored normal words. Material inspection,
source-bound JSON/TMD review and object transforms preserve the new references.
Counts, allocation, padding and unrelated source bytes remain fixed. Retail
lighting and gameplay parity remain deferred. See
[normal-reference workflow](legaia-model-glb-normal-references.md).

Validation: 42 focused Python tests passed with the private retail disc (no
skips), plus Node workflow and frontend syntax checks. Twelve integrated browser
checks cover actual Blender review/no-op, proposed inspection, Apply/history/
Save, 540px layout, stale rejection and Build. Independent flat/Gouraud rewiring
changes only byte2940/byte4284 respectively, retaining the earlier normal edit.
Integrated Build retains bytes2940 and3332, unchanged neighbors and the original
154,547-byte compressed capacity. Legacy content downgrades reject the changed
reference. No game was launched. Private proof:
`local-output/sdk-20260909/model-glb-normal-references-20261002/`.

**Source-bound GLB normal editing (2026-10-02):** Fresh model profile v4 adds
`_LEGAIA_SOURCE_NORMAL` raw signed-i16 XYZ for existing lit packet normal owners.
Shared flat/Gouraud aliases must agree after rounding. Retail axes remain
[x,y,z], without POSITION's Y flip or normalization; unlit corners retain the
out-of-domain [32768,32768,32768] sentinel. Display NORMAL is ignored. Normal
references, padding, allocation and unrelated bytes remain unchanged. Review,
Apply, undo/redo, Save/Open and normal Build use the existing model replacement
workflow. Legacy v1-v3 codec behavior remains; SDK editing requires a fresh v4
export. Retail normal-based lighting and gameplay acceptance remain pending.
See [normal workflow](legaia-model-glb-normals.md).

Validation: 27 focused Python tests passed with the private retail disc (no
skips), plus Node workflow and frontend syntax checks. Twelve browser checks
cover actual Blender no-op/edit review, proposed geometry, Apply/history/Save,
540px layout, stale rejection and normal Build. Independent Blender 5.2.2
readback changes only byte3332 for a shared flat normal and byte4640 for a
Gouraud normal. Integrated Build preserves all decoded neighbors and the
154,547-byte compressed capacity. No game was launched. Private proof:
`local-output/sdk-20260909/model-glb-normals-20261002/`.

**NPC facing composition and output review (2026-10-02):** Source script facing
edits now compose with appended NPC drafts in compressed and streaming MAN
carriers. Original record ownership is re-resolved after append; only the facing
nibble changes, upper flags remain intact, and donor clones retain retail facing.
The editor's **Review NPC output** prepares an in-memory archive and reports
source identities, relocated fields and allocation limits without writing a
package/disc, changing history or launching the game. Normal Build still rejects
NPC drafts; gameplay, scheduling and general allocation remain unverified.
See [draft facing workflow](legaia-draft-facing.md).

Validation: 16 focused Python tests passed with the private retail disc (no
skips), plus Node metadata guards and frontend syntax checks. Six integrated
browser checks cover actual two-scene review, exact metadata, 540px layout,
stale-input withdrawal, pending-close handling and unchanged saved files.
Independent Town0b/Dolk2 readback verifies four/one facing-byte changes, each
rebased by three bytes after append; donor copies and unrelated bytes are retained.
Private proof: `local-output/sdk-20260909/draft-facing-20261002/`.

**Source-bound GLB face rewiring (2026-10-02):** Model profile v3 adds existing
polygon vertex references to the external mesh workflow. Immutable source corner
IDs retain face ownership; qualified vertex IDs may select existing vertices in
the same object. Seam/quad reference and coordinate aliases must agree. Review
shows exact source/current/proposed references before ordinary Apply/history/
persistence/Build. Object, vector, polygon and packet capacities stay fixed;
new objects/polygons, normal tables and material allocation remain pending.
Legacy v1/v2 codec behavior is retained; SDK authoring requires a fresh v3 export.
See [face workflow](legaia-model-glb-faces.md).

Validation: 22 focused Python cases passed with the private retail disc (no
skips), plus the Node workflow and frontend syntax checks. Twelve browser checks
cover exact reference Review, regenerated proposed geometry, no-op and stale
rejection, 540px layout, Apply/history/Save and normal Build. Actual Blender 5.2.2
updates both aliases of one quad corner, vertex 17 to 0; independent readback
changes only byte434 (136 to 0). Build retains earlier RGB/material bytes300,
1095 and1102, all decoded neighbors and the 118,461-byte compressed capacity.
No game was launched; gameplay appearance and general allocation remain pending.
Private proof: `local-output/sdk-20260909/model-glb-faces-20261002/`.

**Raw RGB model GLB editing (2026-10-02):** The existing external model workflow
now imports qualified baked RGB through `_LEGAIA_SOURCE_RGB` in the raw 0..255
byte domain. Profile v2 binds each flat/shared or Gouraud/corner color to its
source packet; duplicate aliases must agree, and packets without stored RGB
retain explicit -1 sentinels. Review exposes exact fields and rounding error
before ordinary Apply/history/persistence/Build. Display `COLOR_0`, shader colors,
normals, references, material words and allocation remain outside this lane.
Fresh exports use v2; the codec retains legacy v1 positions/UV behavior. Existing
bindings require a fresh export for SDK Apply. See [RGB workflow](legaia-model-glb-rgb.md).

Validation: 18 focused Python cases passed with the private retail disc (no
skips), plus the Node workflow and frontend syntax checks. Twelve browser checks
cover no-op, exact RGB Review, proposed model, 540px layout, file invalidation,
Apply, Undo/Redo, Save, Build and stale-source rejection. Actual Blender 5.2.2
round trips flat and Gouraud edits exactly. The saved Dolk2 Build adds only byte
300 (24 to 25) to the two existing material bytes, preserving decoded neighbors
and the 118,461-byte compressed capacity. No game was launched; runtime lighting
and appearance remain deferred. Private proof: `local-output/sdk-20260909/model-glb-rgb-20261002/`.

**Coordinated scene animation (2026-10-02):** The central viewport now previews
eligible actors together with Play/Pause, integer scrubbing, an explicit preview
rate and exact Stop/Restore. Retail and Authored projections retain their source
identity, placements, material/texture associations and separate shared channel
contributions. Sampling is transient; persistent editing is blocked until Restore.
Dolk2 covers 69/72 actors in 15 tracks; Town01 source proof covers 42/52 in 22.
Static/unavailable actors stay explicit. Six Python tests, the Node lifecycle
suite and integrated browser checks pass, with no game launched. Effective-channel
frame zero matches the independently composed bank; Retail stays distinct.
Retail timing, scheduling and current live animation remain unverified. See
[timeline workflow](legaia-scene-animation.md).

**Source-qualified model materials (2026-10-02):** The model inspector now edits
existing CLUT/page/depth bindings and shared packet-group ABE with exact masks,
source/current Review, proposed model/posed-scene inspection and explicit Apply.
Ordinary Undo/Redo, Save/Open and Build retain versioned material overrides.
Source ABR stays read-only because traced retail paths supply caller blend state.
Twenty-two focused Python tests, three Node suites and six integrated browser
checks pass. The actual Dolk2 proof changes only bytes 1095 and 1102; Build readback
preserves the 118,461-byte compressed capacity and every decoded neighboring byte.
Geometry and a fresh GLB round-trip stay exact. Gameplay blending/residency and
general material allocation remain pending. See [workflow](legaia-model-materials.md).

**Source-bound texture PNG editing (2026-10-02):** Imported textures now support
current PNG + binding + separate STP export, external image editing, exact
source/current Review, Current/Proposed pixel and scene inspection, and explicit
Apply through normal texture history, Save/Open and Build. Existing palette mode
retains words; deterministic rebuild changes only the selected CLUT row. Shared
indices, color error and forced black/transparent STP changes are reported.
Dimensions, bit depth, VRAM rectangles and source capacities remain fixed.

Validation: 12 focused Python cases, the Node workflow suite, both frontend
syntax checks and 11 integrated browser checks passed. Independent Pillow 12.1
proofs cover both palettes of a retail Dolk2 TIM, exact nibble/word edits,
transparent/opaque-black semantics and deterministic color reduction. The saved
Town01 browser Build contains the exact reviewed 33,312-byte TIM with unchanged
other CLUT rows and neighboring source bytes. Scene preview changes 26 materials
across 10 instances while preserving geometry/placements; Return restores the
scene and retains exact Files. Review-only, stale/no-op, history, persistence and
540px checks passed, with zero page/HTTP errors or game-launch requests. Large
unique-color images may be CPU-intensive; gameplay and live blending remain
deferred. See [workflow and limits](legaia-texture-png.md); private evidence is
under `local-output/sdk-20260909/texture-png-20261002/`.

**Source-bound model GLB editing (2026-10-02):** Imported models now support
Export current model + binding → external mesh edit → Review → Inspect proposed
model → Apply → Undo/Redo → Save/Open → normal Build. Explicit source vertex
and corner attributes retain identities across Blender splits and quad
triangulation. This imports existing positions and UV bytes; effective RGB,
normals, face references, material words, images and opaque bytes are preserved.
Topology allocation and arbitrary mesh/material replacement remain pending.

Validation: 14 focused Python tests, the Node workflow suite, both frontend
syntax checks and 12 integrated browser checks passed. Actual Blender 5.2.2
round-tripped a fresh SDK export exactly; its edit changed only vertex 27 X and
primitive 50/corner 2 U of Dolk2 model 0133. The saved browser Build independently
reproduces those two fields and unchanged neighboring decoded bytes within the
118,461-byte compressed source span. Review/preview are read only; stale/no-op
Apply guards, history, persistence and 540px layout passed. Page/HTTP errors and
game-launch requests were zero. Gameplay appearance remains deferred.
See [workflow and limits](legaia-model-glb.md); private evidence is under
`local-output/sdk-20260909/model-glb-20261002/`.

**Imported project Asset Database (2026-10-02):** The primary asset browser now
offers explicit project discovery, source-scene filtering, searches across all
retained memberships, and pages of 128 rows. Shared IDs retain complete per-scene
variants; Details selects one source membership before opening existing tools.
Cross-scene derived inspection refreshes and compares that source catalog first.
Discovery uses detached views and does not change imports, authored state,
selection, history, saved files or active caches. Navigation retains the index;
source or authored changes invalidate it and require a new refresh.

The Town01/Dolk2/map01 source audit returns 3,637 unique identities and 3,703
memberships, with all three inventories explicitly partial. Counts do not imply
complete format coverage, runtime residency, actor spawning or gameplay parity.
See [project asset workflow and limits](legaia-project-assets.md). Private
evidence is under `local-output/sdk-20260909/project-assets-20261002/`.

Validation: 18 selected Python tests, two Node suites, both changed-module syntax
checks and 19 integrated browser checks passed. Source discovery preserves
populated caches and saved files; exact P2 owner/PC focus and canonical tool
handoffs passed. A private edit followed by Undo verifies invalidation and stale
action rejection without Save/Build. Controls and the source inspector fit
540px. Page/HTTP errors and game-launch requests were zero.

**Source-qualified global landmark authoring (2026-10-02):** The world-map
workspace edits the 20 existing SCUS menu records with separate Retail,
Authored, Current and reviewed Proposed values. Existing name/discovery,
CDNAME destination and encoded X/Y fields have a duplicate-safe 2D diagram,
exact byte review, Apply/reset, Undo/Redo and Save/Open. Authored asset links and
normal Build reports reopen the source row. Normal Build emits a guarded
126-byte SCUS data overlay, with independent whole-executable reconstruction;
field placement composition retains both overlays and unchanged imports.
Experimental Export disc rejects this global component explicitly.

Name and discovery consumers are now qualified by retail static analysis.
Destination and X/Y meanings remain reference interpretations; drawing,
travel, discovery activation and gameplay are not verified. The table has 20
rows, terminator row 20 and two padding bytes before 16 immutable name slots.
See [landmark authoring workflow and evidence](legaia-worldmap-authoring.md).

Validation: 36 selected Python tests passed with the private retail disc and no
skips; two Node suites, both changed-module syntax checks and 16 browser
workflows passed. Browser page/HTTP errors and game-launch requests were zero.
The saved browser package independently reconstructs the executable with only
file byte 0x6429C changed 96-to97 (row 0 X), while fresh scene imports still match.
Review exposes field changes, byte offsets and the candidate hash; draft gates,
reset/history/persistence, 540px layout and Build-to-source navigation passed.
Private proof is in `local-output/sdk-20260909/worldmap-authoring-20261002/`.
The full SDK and gameplay acceptance remain incomplete.

**Source-qualified field branch authoring (2026-10-02):** The script workspace
now links a selectable source-flow diagram to disassembly and reviews existing
JMP, conditional, bounding-box, flag-word and ordinary system-flag destinations.
Retail, authored, current and proposed edges remain separate; encoded conditions
are not evaluated. Targets must be original instruction or atomic MES starts
through PC32767. Reviewed Apply/reset uses ordinary Undo/Redo and Save/Open;
normal Build, streaming export, appended-record composition and operand files/
bundles retain record layout and independently qualify changed flow. Other
authored operands survive branches that make source nodes unvisited.

Retail handler validation also corrects three existing decoder interpretations:
camera apply and FIELD43/44 continue, and flag-word targets use relative offsets.
Ordinary SYSFLAG forms cover50..7F; extended forms stop with an explicit reason.
The pinned Andrew reference remains unchanged. Town01 now has619 decoded dialogue
segments and1339 flag references; Dolk2 has629 segments and744 references.
See [field branch workflow and evidence](legaia-script-branches.md).

Validation:88 integrated Python regression cases passed with the private retail
disc and no skips, including compressed Town01 and raw Dolk2 normal packages.
Three HTTP cases reject18 malformed/foreign requests and stale Apply without
changing evidence or history. Four Node suites and15 browser workflows passed;
browser page/HTTP errors and game-launch requests were zero. The browser's
reviewed Town01 package independently reads back with only byte4791 changed
(PC31 target15-to11); its saved imports still match a fresh source import.
Dolk2 PC28 target63-to9 changes only bytes7481/7482. Real Town01 donor append
preserves that branch at rebased byte4794 in the prepared MAN; full rebuilt-disc
acceptance is deferred. Current/Proposed navigation, multiple pending choices,
reviewed Apply/reset, Undo/Redo, Save, no-op/stale gates, narrow layout and exact
Build-to-source navigation were checked. Private evidence remains in
`local-output/sdk-20260909/script-branches-20261002/`. Runtime branch activation,
story behavior and termination remain deferred; the full SDK remains incomplete.

**Model faces, UVs and baked colors (2026-10-02):** The model viewer now
provides a source-bound primitive editor with separate Retail, Current and
Proposed values. Existing face connections, UV byte pairs and stored RGB words
can be authored across all 24 supported flags. Preview uses paired textured
views with a shared camera; a reviewed proposal can be inspected across supported
scene instances while retaining their existing poses and placement. Apply checks
current model, scene and candidate hashes. Undo/Redo, Save/Open, authored TMD
export and normal Build use a versioned `tmd-content-v1` binding; legacy
`tmd-shape` bindings retain strict XYZ-only validation. Vector/whole-object/JSON
edits preserve authored primitives. Pose composition now refreshes face/color/UV
arrays, and proposed scene textures recrop from candidate UVs. Normal Build audit
links reopen the exact source primitive. Object/group counts, capacities, normal
references, material bindings and opaque bytes remain source-owned. Arbitrary
new mesh allocation and runtime lighting/culling acceptance remain unfinished.
See [model content workflow](legaia-model-content.md).

Validation: 31 selected Python cases passed with the private retail disc enabled
and zero skips; 3 Node suites and 2 changed-module syntax checks passed. Sixteen
actual browser workflows passed with zero page/HTTP errors and zero game-launch
requests, including normal Build review/package/source navigation. Reviewed,
scene, Build and narrow-layout captures were inspected. Town01 model0000 changes
exactly source bytes48/52/62/64; independent package readback verifies the complete
304116-byte decoded container, 154518 encoded bytes within the 154547-byte source
capacity, and unchanged unused encoded tail. Imported metadata is unchanged and
Save/Open retains the exact versioned binding. Vahn idle retains its verified
12-to-10 object prefix and frame coordinates. Gameplay appearance/lighting/culling
remain deferred; no game was launched or package installed. Private evidence is
under `local-output/sdk-20260909/model-primitives-20261002/`.

**Visual transition graph workspace (2026-10-02):** Scene and Project
transitions now open a selectable node/arrow diagram, scene list, search,
imported-only filter, direct-reference focus, zoom/pan/Fit and paginated source
instructions. Parallel instructions remain independent records; arrow badges
group only equal source/destination pairs. Retail, Authored and Effective entry
bytes stay separate. Source-script navigation selects the exact owner and PC;
imported destinations use ordinary scene selection. Coverage, unavailable
catalogs and unresolved names remain explicit. Project-only freshness changes,
stale responses and pending-close/reopen cleanup and old-request isolation invalidate retained controls. The
canvas draws at most 80 scenes and 160 pairs; every matching instruction remains
accessible in 20-row pages. No gameplay route or story reachability is inferred.
See [transition graph workflow](legaia-project-transitions.md).

Validation: 26 selected retail-enabled Python cases passed with zero skips;
6 Node suites and 3 changed-module syntax checks passed. Thirteen actual browser
workflow checks passed with zero page/HTTP errors, zero authoring commands and
zero game-launch requests. The four-scene Town01/Dolk2/Town0b/map01 fixture has
17 nodes, 18 grouped pairs and 35 instructions from 319 scripts (195 partial,
zero unavailable). Graph, narrow-layout and entry-layer captures were inspected;
long arrows avoid intervening scene boxes and badges remain selectable above
crossing lines. Imported metadata and the saved project are unchanged. This
source-reference workspace is accepted offline; gameplay/runtime verification
remains deferred for the wider SDK. No game was launched or package installed.

**Reviewed primary trigger cells (2026-10-02):** Existing primary MAP kind-0
teleport and kind-1 binding rows now have an Edit trigger cell action. Retail,
Authored, Current and Proposed X/Z cells remain separate, with outline and scene
comparison, per-row retail reset, one-step Undo/Redo and Save/Open. Fresh source
and review keys qualify the complete retained binding; stable row identity stays
independent of coordinates. Only two lookup-coordinate bytes are writable.
Destinations, record/gate payloads, row order, footprints, elevation and all other
MAP bytes remain unchanged. A separate trigger key invalidates annotations
without reloading geometry. Normal Build composes triggers, regions, scenery and
collision walls in one exact MAP overlay, independently binding every trigger
byte to the requested cells. Build report links reopen the source resource.
Fallback rows remain read-only; unknown gates keep their unresolved behavior.
Moving a row can change first-match shadowing. Height, contact, activation and
playable behavior remain deferred. See [trigger cell workflow](legaia-trigger-cells.md).

Validation:50 selected retail-enabled Python cases verified without skips,
including the12 affected/neighbor cases rerun after repairs;6 Node suites and3
changed-module syntax checks passed. Thirteen actual browser workflow checks
passed with zero page/HTTP errors and zero game-launch requests. Visually
inspected review and viewport captures are readable. The retained Town01
kind-0/0000 fixture changes only MAP65554 from30 to31, preserving destination
bytes146/132. Fresh disc-span, ZIP and imported-metadata readbacks agree. The
package is built, not installed or played; full SDK/runtime scope remains incomplete.

**Source-facing instruction authoring and object-index correction (2026-10-02):**
The actor Inspector now opens source-qualified facing controls for simple
CAM_CFG and nonparked NPC_RUN instructions. Retail, Authored and Effective
sectors remain separate; drafts have a numeric compass preview, Apply/Clear,
Undo/Redo and Save/Open. Source-bound operand JSON and scene bundles include
ScriptFacing. Normal Build composes the exact low-nibble writes with other MAN
edits and checks the full byte audit and compressed capacity. Retail dispatch,
LUT reads and actor-facing stores were verified statically before implementation.
The shared Inspector also renders additional registered components through their
schema. Gate-0 object references now preserve unresolved flat MAN indices;
gate-1 remains explicitly P2-local. Initial/live actor heading, branch selection,
experimental NPC append export and gameplay acceptance remain unresolved.
See [source-facing workflow](legaia-script-facing.md).

Validation:56 focused retail-enabled Python tests passed without skips in70.133s;
7 Node checks and3 changed-module syntax checks passed. Nine actual browser
workflow checks passed with zero page/HTTP errors and zero game-launch requests;
a real P2 report independently validates/renders31 controls with explicit
extended-context uncertainty. Retained Town0b actor0019 packaging changes only
MAN byte9479 from0x81 to0x85, preserving the upper flag. Imports remain unchanged.
The package is not installed or played; full SDK/runtime scope is incomplete.

**Reviewed field region bounds (2026-10-02):** Primary MAP regions now have
an Edit region bounds action, four strict corner inputs, separate Retail /
Authored / Current / Proposed layers, and outline/viewport comparison. Apply
and per-row retail reset use one undo step; inherited/no-op values normalize
without dirtying the project. Source-qualified effective annotations leave the
imported spatial envelope intact, and a separate region key invalidates views
without reloading geometry. Save/Open and normal Build preserve the region
type, padding, source order and all bytes outside audited corners. Region edits
compose with scenery and collision walls in one MAP overlay. Browser review,
frame, comparison, Apply, history, persistence and scene cleanup passed with
zero page/HTTP errors and zero game-launch requests. The retained Town01
fixture changes only MAP byte66692 from58 to59; its package is built but not
installed or played. Height, activation and movement acceptance remain deferred.
See [region bounds workflow](legaia-region-bounds.md). The full SDK/runtime
objective remains incomplete.

Region milestone validation:54 retail-enabled Python tests passed with no skips in74.565s;42 Node checks and40 module syntax checks passed. Actual browser comparison passed10 workflow checks with zero page/HTTP errors and zero run requests. Independent package readback confirms one byte changes; imported scene hashes remain unchanged. No game launched or package installed.

**Field source cells and script links (2026-10-02):** Verified trigger and
region rows now appear in the scene hierarchy and shared Inspector, with
viewport outlines, framing and explicit source-cell picking. Trigger dispatch
uses `world >> 7`; region lookup uses `(world - 64) >> 7`, preserving the
64-unit difference. Display Y=0 remains an inspection plane with unknown
height. Coincident rows retain separate source identities. Gate-1 rows link to
unique bounded P2 scripts in Active/Project reference graphs with both record
hashes; object binds, unknown gates and missing/aliased targets stay unresolved.
Town01 supplies 99 trigger cells,14 region bounds and 51 eligible script links.
Read-only HTTP, source qualification, browser navigation/picking and stale-scene
cleanup passed. No game launched or package installed; contact/activation and
retail height acceptance remain deferred. See
[field source workspace](legaia-field-source-workspace.md). Full SDK/runtime
coverage is still incomplete.

Final validation:59 retail-enabled Python tests passed with no skips in84.629s;41 Node checks and39 module syntax checks passed. Actual browser frame/pick, overlapping rows, reference/script navigation, actor restoration and scene invalidation passed with zero page/HTTP errors. The saved baseline/import hashes remained unchanged; no package or game was launched.

**Central transition assets (2026-10-02):** Decoded scene-change instructions
now appear in the Asset Browser, shared Inspector and Active/Project dependency
graphs. Imported/authored/effective entry bytes and static destination arrival
coordinates remain distinct from unknown source triggers. A dedicated transition
key invalidates stale views without reloading geometry. Fresh serializer checks
qualify authored entries; partial catalog coverage with zero decoder stops no
longer blocks otherwise supported entries. Retail discovery found 35 transitions
across Town01, Dolk2, map01 and Town0b.55 retail-enabled Python tests passed
with no skips;39 Node checks and38 syntax checks passed. Browser editing,
history, persistence, source/destination navigation and reference scopes passed.
Reopened Build changes only Town01 MAN bytes28574 (96 to128) and28576 (4 to2).
No game launched; existing transition-arrival gameplay acceptance is deferred.
See [transition asset workflow](legaia-transition-assets.md). The full SDK and
runtime objective remains incomplete.

**Reusable initial-animation presets (2026-10-02):** Versioned v2 presets
capture a verified initial clip alone or with authored position/appearance.
Frozen witness proof survives later source-actor edits; full proposed components
are validated together before one single/group Apply. Omitted components and
imported channel ownership stay intact. Inherited clip matches normalize to
absence, including a true no-op on untouched targets. Metadata-only v2 files
retain fresh source/import/hash proof and independent library identity; legacy
v1 files/scopes remain supported. Proposed/Current scene comparison, Return,
Undo/Redo and Save/Open are connected.47 focused retail-enabled Python tests
passed in57.695s, plus8 HTTP/project compatibility tests in1.293s;37 Node files
and37 syntax checks passed. Actual browser capture/transfer/single/group scene
review/Apply/history/Save passed with zero page or unexpected HTTP errors.
Independent Town0b pure-clip MAN readback changes only9471,14→13; inheritance
reproduces baseline output. The saved combined fixture changes only19122,13→14,
and19123,119→150 (X15296→2944), retaining model0102/Z1472. Reopened Build
reproduces package SHA256 `2cc94474453d5a5bd8eaddb07808c6f3dbd10d089d126f9a8e8c4cb0dbd06389`.
No game launched; existing playback/script/gameplay acceptance remains deferred.
See [animated preset workflow](legaia-animated-actor-presets.md). The full SDK
and runtime objective remains incomplete.

**Central flag-reference assets (2026-10-02):** Source-scoped flag groups
now appear in Asset Database search, a shared Inspector, and Active/Project
script dependency graphs. The Inspector shows retail/authored/effective sites,
coverage and exact-PC navigation for P1/P2 owners. A dedicated operand-state
key invalidates stale annotations without changing geometry; project flag
keys now include authored operands. Fresh Town01/Dolk2/map01 sources yielded
899 groups/2,142 sites; source browsing preserves project/saved state.
43 focused retail-enabled Python tests passed in20.085s;36 Node files and36
syntax checks passed. Browser P1/P2 exact-PC navigation, operand layers,
Undo/Redo/Save/Clear, stale-view closure and Active/Project references passed
with no page or unexpected HTTP errors. Runtime variables, story names and
unseen paths remain unresolved. See [flag asset workflow](legaia-flag-assets.md). Gameplay remains
deferred; the full SDK/runtime objective is incomplete.

**Initial animation assignment (2026-10-02):** The actor Inspector now offers
source-verified same-model clip choices, explicit Review/Apply/Clear and witness
preview. A separate ActorAnimation component preserves imported channel ownership,
Undo/Redo and Save/Open. The authored scene and assigned GLB preview keep target
identity/position; normal and draft writers compose the final MAN header once.
Effective references and unconfirmed Live candidates keep animation witnesses
separate from appearance donors and invalidate stale observations. Incompatible
appearance/preset/revert changes reject atomically. Legacy v1 templates capture position/appearance; versioned v2 presets now
include the separate initial assignment. Global/zero/unknown/partial pairings remain
unsupported; scripts, timing and gameplay suitability remain unverified.
39 focused retail-enabled Python checks passed in55.598s, plus a22-check
compatibility pass in21.572s; all34 Node files and35 syntax checks passed. Seven raw MAN/appearance compatibility checks
also passed in47.334s without skips.
Actual browser Review/Preview/Apply/Clear, assigned-frame GLB export,
Undo/Redo/Save, exact scene placement and initial/effective reference edges passed
with zero page errors; malformed/stale HTTP rejected without history changes.
Visual review repaired a clipped Review button; final layout and screenshot
passed. Fresh Town0b package readback changes only MAN offset9471,14→13,
model0102/positions/imports/saved bytes unchanged. Record12 digest and exact
retail import were reverified; clearing reproduces baseline package bytes.
Draft composition preserves the appended retail donor clip and rebases the
existing header9471→9474. Saved private fixture/package/evidence:
`local-output/sdk-20260909/actor-animation-assignment-20261002/`.
See [initial assignment workflow](legaia-initial-animation-assignment.md).
No game launched or package installed. Manual checks are queued for later;
full SDK/runtime acceptance remains incomplete and the565 checkpoint predates
this feature.

**Shared model/clip reference navigation (2026-10-02):** Asset references
now links the eight supported shared field clips to their five global models in
both Active scene and Project scopes. These are explicit reference-pinned
associations, separate from initial/effective actor assignments. Edges retain
the pinned commit, model/clip identity, decoded counts and full source locator;
strict model provenance, record mapping and bounded metadata checks reject
inconsistent evidence. Missing models remain unresolved. The browser labels
actor playback unknown and supports model-to-clip and clip-to-model navigation.
31 focused retail-enabled Python checks passed in 24.333s; all 33 Node files and 34
syntax checks passed with hashes matched to final source. Fresh Town01/Dolk2/map01
discovery verified all 8 clips and 24 source-qualified edges in 33.826s, exact edge
hashes and untouched project/cache/saved bytes. Actual browser Active/Project
HTTP, three-scene navigation and the auxiliary loop passed with zero page errors
or authoring commands; screenshot inspected. Private evidence:
`local-output/sdk-20260909/shared-clip-references-20261001/`.
No game launched; this read-only feature needs no new gameplay gate. The
565-test checkpoint predates both reference workflows; full SDK/runtime
acceptance remains incomplete.

**Project-wide asset references (2026-10-01):** Asset Details → Inspect
asset references now offers Active scene and Project scopes. Project discovery
freshly verifies all imported scenes and assembles existing decoded relationships
through detached scene/catalog views, preserving project state and caches. Shared
stable IDs retain source memberships separately from navigable catalogs, with
scene-qualified edges and deterministic cross-scene navigation. Coverage exposes
source hashes, partial-catalog limitations and explicit unavailable reasons;
recorded relationships do not establish runtime residency or reachability.
Scope/Close cancellation and stale-source guards prevent late results. Strict
HTTP shapes and bounded graphs/metadata retain the existing active response.
Twenty focused retail-enabled Python tests passed in13.948s; all33 Node files
and34 syntax checks passed with hashes matched to final source. Fresh Town01,
Dolk2 and map01 discovery checked actor/script/dialogue/animation/world-map links,
12 shared-model material edges and exact source hashes; complete project/cache
and saved bytes stayed unchanged. This final retail check took21.566s. Per-call
import-hash reuse produces an identical report to the earlier repeated-hashing
implementation. Actual browser Active/Project HTTP responses, three-scene scope,
source navigation, pending Close and stale-source rejection passed with zero
page errors; screenshot inspected. Private evidence:
`local-output/sdk-20260909/project-asset-references-20261001/`.
No game launched. This read-only feature needs no new gameplay gate. The565
checkpoint predates it; full SDK/runtime acceptance remains incomplete.

**Integrated offline checkpoint (2026-10-01):** Full retail-enabled SDK
regression passed565 Python tests in250.658s (252.001s wall time), exit0 with no
skips, on unchanged clean source `43994eb25f5125da4378f2cb970b311931745bf9`.
All33 Node test files and34 editor syntax checks passed with captured hashes
freshly matched to source. This supersedes548 and includes viewport source-wall
editing, atomic mixed actor/scenery placements and their X/Z handles, saved
scene selections and visible placement rectangle selection, alongside earlier
SDK workflows. User-owned disc identity and466714416-byte length were freshly
verified. Browser and package readback evidence remains separate from this
regression. No game launched; runtime parity, genuine Live identity, gameplay
acceptance and full16-layer SDK completion remain unproven.

Private evidence under `local-output/sdk-20260909/`:
`sdk-regression-20261001-scene-placement.log/.json` and
`node-checks-20261001-scene-placement.json`. Python log SHA256:
`4a52fe3e8f7923fc173298f8c6f38b6fa460193ccf72eb6ced78177ff27a595f`.

**Placement rectangle selection (2026-10-01):** Box select placements now
selects visible imported actor and static-decoration meshes through one
depth-tested renderer ID pass. Drag replaces the selection; Ctrl/Command adds,
and an empty rectangle clears it. Hidden entities/layers, ground, NPC drafts and
placed scenery are excluded. Results are canonical and bounded to128, with
atomic rejection preserving the previous selection. Hierarchy and focused
Inspector stay synchronized; the selection feeds existing mixed placement
review and saved scene selections. Escape, camera, resize and stale source
cancel gestures without a project command. Eleven focused Python checks passed
in3.214s; all33 Node files and34 editor syntax checks passed. Actual2×-DPI
pointer replacement/addition, single-actor focus, empty selection, both layer
filters, cancellation and fresh review handoff passed with zero page errors;
screenshot inspected. Saved bytes/history stayed unchanged. Private evidence:
`local-output/sdk-20260909/scene-placement-box-20261001/`. No game launched.
This selection-only feature introduces no new gameplay gate. Historical548
predates it; the full SDK objective remains incomplete.

**Mixed placement viewport handles (2026-10-01):** Retained Proposed
actor/static-decoration groups now expose X/Z handles. Every drag snaps to a
relative 64-unit offset, holding each displayed height and rotation; release
freshly reviews the full source-bound mixed proposal without a project command.
Current has no handles. Rejected/pending drags keep the prior verified matrices
and inputs; Restore cancels pending review and ignores late responses. Escape,
camera, preview/source/representation changes and resize cancel stale gestures.
Thirty-one focused retail-enabled Python checks passed in 18.361s, all 32 Node
files and 33 syntax checks passed. Actual 2×-DPI top-view X/Z pointer drags,
retained review, rejection, cancellation, Current matrices, Apply/Undo/Redo/Save
and fresh Escape/camera/resize checks passed with zero page errors; screenshots
inspected. Normal two-overlay MAN/MAP package passed exact full73728-byte MAP ZIP
readback and independent actor/grid decode, preserving prior actor/scenery edits,
height/rotation, 17 collision edits, floor tiers and saved selection metadata.
Private evidence: `local-output/sdk-20260909/scene-placement-drag-20261001/`.
No game launched; gameplay remains deferred. Historical548 predates this feature.
See [Mixed placement workflow](legaia-scene-placement-groups.md).

**Saved scene placement selections (2026-10-01):** Named project-local
selections now retain 1–128 imported actors, static decorations or mixed members.
Create/Rename/Replace/Delete use strict source-bound commands and one-step
Undo/Redo. Metadata validation remains portable without a disc; scenery Create,
Replace and Recall freshly verify static MAP identities. Cross-scene Recall seeds
actor, scenery or mixed placement tools without editing game overrides. Changed
reimport is blocked under the library and its history. Thirty-eight focused Python
checks passed in 2.554s, all 32 Node files and 33 syntax checks passed. Actual
Town01/Dolk2 browser Create/Rename/Delete/history, Save/Open, cross-scene mixed
recall, single-decoration replacement/recall/Undo and pending source/recall Cancel
checks passed with zero page errors; screenshot inspected. Private saved-project
copy retains the library; normal package is byte-identical before/after selection
metadata (SHA256 `1503a2fb0aa1c141927efac65285390afa876028bfd7ddc46f44dd70c02302fe`).
Private evidence: `local-output/sdk-20260909/scene-selection-sets-20261001/`.
No game launched. This feature requires no new gameplay gate; it does not establish
runtime placement parity. Historical 548 checkpoint predates it.
See [Saved scene selections](legaia-scene-selections.md).

**Mixed scene placement groups (2026-10-01):** Select scene placements combines
imported actors and static decorations in one bounded selection. Move scene
placement group reviews 2–128 targets, including at least one of each kind, with
common X/Z offsets in 64-unit steps within ±16320. Proposed/Current inspection
retains the review and holds preview height; runtime height remains unknown.
Fresh full-source validation precedes one atomic Apply/Undo/Redo operation across
actor and Environment overrides, preserving unrelated components and edits.
NPC drafts and placed scenery are excluded. Forty-seven focused Python checks
passed (43 in 23.086s, four HTTP checks in 2.912s); all 31 Node files and 32 syntax
checks passed. Actual 2×-DPI retail hierarchy selection, Proposed/Current matrices,
held height/rotation, no-op/input withdrawal, one-step Undo for both owners,
Redo/Save and pending Cancel/late-response withdrawal passed with zero page errors.
Fresh browser representation guards also passed without writes; screenshots inspected.
The normal package contains both MAN and complete 73728-byte MAP overlays: exact ZIP
readback and independent MAN/grid coordinate decoding preserved opaque bytes,
unselected scenery, shared rotations, existing collision edits and floor tiers.
The previous 548-test checkpoint predates this change and remains unchanged.
No game launched. Gameplay remains deferred. See [Mixed placement workflow](legaia-scene-placement-groups.md).

**Viewport source-wall editing (2026-10-01):** Select wall rectangle loads
verified source collision data and picks canonical X/Z cells directly in the
scene. Dragging prepares inclusive bounds without a project command; release
opens the existing review. Proposed/Current/Retail wall layers can be inspected
on the labelled Y=0 reference plane, with retained Return/Restore and explicit
atomic Apply/Undo/Redo, Save/Open and normal Build. Camera/source/representation
changes, Escape and pending cancellation withdraw stale gestures or reviews.
Twenty-one focused retail-enabled Python tests passed in10.570s, all30 Node
files and31 syntax checks passed. Real2×-DPI top/perspective browser drags,
comparison layers, no-op/input withdrawal, cancellation and exact full73728-byte
MAP ZIP readback passed with zero page errors; screenshots inspected.
No game launched. This postdates548; gameplay and full acceptance remain open.
See [Wall rectangle workflow](legaia-collision-rectangles.md).

**Integrated offline checkpoint (2026-10-01):** Full retail-enabled discovery
passed548 Python tests in247.512s, exit0 with no skips, on unchanged clean source
`80d4ae765f820551759f181d8372478a49358b72`. All29 Node test files and30 editor
syntax checks passed with captured file hashes. This supersedes514 and integrates
saved-copy discovery, wall rectangles/spatial comparison, scenery groups/drags,
actor transform preview refresh and scenery alignment/distribution with the
previous SDK workflows. The user-owned disc SHA256 and466714416-byte length were
freshly verified. Browser/package evidence remains separate; no game launched.
Full16-layer SDK, runtime parity, genuine Live identity and gameplay acceptance
remain incomplete. This checkpoint predates the viewport wall workflow above.

Private evidence: `sdk-regression-20261001-scenery-layout.log/.json` and
`node-checks-20261001-scenery-layout.json` under `local-output/sdk-20260909/`.
Python log SHA256:
`a247306827edfc8672e0133478dbf1d0fd83ebf6e24536f014a414b4c153da2a`.

**Scenery alignment and distribution (2026-10-01):** Arrange scenery group
aligns2–128 selected static decorations to an anchor on X/Z or evenly distributes
them between fixed endpoints using integer half-up rounding and stable identity
ordering. Other axes, shared transforms, Y/rotation, outside edits and Collision
are preserved. Fresh review, textured Proposed/Current comparison, retained
Return/Restore, atomic Apply/Undo/Redo, Save/Open and normal Build are connected.
Fifty-three focused retail-enabled Python tests passed in17.726s, all29 Node tests
and30 syntax checks passed. Retail browser alignment/distribution, input withdrawal,
comparison matrices, no-op Apply and pending-close cancellation passed with zero
page errors; screenshots inspected. Complete73728-byte MAP ZIP matches the saved
binding and independently decoded descriptor coordinates. No game launched.
Included in548; runtime visibility/collision/lifecycle remain deferred.
See [Scenery groups](legaia-scenery-groups.md).

**Scenery group drag and actor preview refresh (2026-10-01):** Proposed
scenery inspection now has X/Z handles with integer movement and optional
16/64/256/1024 snapping. Release obtains a fresh source-bound review; Apply
remains one explicit undoable command. Rejected and cancelled pending drags
retain or restore the verified proposal without saving. Canvas focus now prevents
scroll displacement during pointer gestures. Imported actor transforms now
invalidate preview identity while retaining cached geometry, fixing stale actor
positions after edits and resampling source height where Y is unknown.
Forty-five focused retail-enabled Python tests passed in16.686s; all28 Node tests
and29 syntax checks passed. Retail browser group drags, rejection/cancellation,
Apply/Undo/Redo/Save, individual actor/scenery drags and exact full73728-byte MAP
ZIP readback passed with zero page errors; screenshots inspected. No game
launched. Included in548; gameplay/full acceptance remain deferred.
See [Scenery groups](legaia-scenery-groups.md).

**Static scenery group placement (2026-10-01):** Ctrl/Command-click static
decorations in the hierarchy or viewport, or Shift-select a hierarchy range,
then choose Move scenery group. Source-bound review supports2–128 instances,
common integer X/Z offsets, retained Proposed/Current textured scene inspection,
one atomic Apply, Undo/Redo, Save/Open and normal Build. Shared offsets/rotations,
Y, unselected instances, Collision and imported identities remain preserved.
Full merged descriptor capacity, signed range, source/metadata/selection guards
and exact zero-offset no-op behavior are checked. Twenty-one focused retail-
enabled Python tests passed in16.060s, all28 Node tests and29 syntax checks passed.
Retail browser two-wall workflow and full73728-byte ZIP MAP readback passed;
screenshots inspected and zero page errors. No game launched; gameplay deferred.
Postdates integrated514. See [Scenery groups](legaia-scenery-groups.md).

**Spatial wall rectangle comparison (2026-10-01):** Reviewed rectangles now
show all selected bits in a top-down Retail/Current/Proposed comparison with
canonical source X/Z bounds, quadrant placement and proposed-change outlines.
Layer switching is read-only; changed inputs withdraw the map and Apply.
Twenty-two focused retail-enabled Python tests passed in17.122s, including five
new synthetic HTTP contract tests; all27 Node tests and28 syntax checks passed.
A synthetic browser fixture checked16 bits, three layer counts, coordinate
bounds, no extra requests/writes and input withdrawal; zero page errors and
screenshot inspected. This is a source-grid diagram, not a terrain/live viewport.
Postdates integrated514. No game launched. See
[Wall rectangles](legaia-collision-rectangles.md).

**Rectangular source wall editing (2026-10-01):** Collision tools now review
inclusive grid rectangles and apply one atomic wall override, preserving floor
bits, outside edits and unrelated components. Fresh source/review guards, bounds,
merged4096 limit, no-op and Undo/Save/Open support are connected. Seventeen focused
Python checks,27 Node files/28 syntax checks passed. Browser reviewed/applied16
town01 bits, verified history/Save/stale/no-op guards, zero errors and inspected
compact dialog. Normal package ZIP matches the expected complete73728-byte MAP
with floor tiers preserved. No game launched; runtime collision paints/gameplay
remain deferred. Postdates514. See [Wall rectangles](legaia-collision-rectangles.md).

**Saved editable copy discovery (2026-10-01):** Copy project now lists bounded
project-local creation records after restart, shows current saved names/metadata
changes, labels partial records and reopens through normal validation and the
dirty-source guard. Listing does not claim current input integrity. Twenty-eight
focused Python checks,26 Node files/27 syntax checks passed. Browser verifies
three states, corrupted-import rejection, dirty guard, reopened Dolk2 X9536,
pending-close withdrawal and Refresh with unchanged source bytes, zero errors
and inspected screenshots. No game launched; postdates514. See
[Project copies](legaia-project-copies.md).

**Latest integrated offline checkpoint (2026-10-01):** Retail-enabled discovery
passed **514 Python tests in 365.743 seconds**, exit0, no skips, on unchanged
clean source `7a6459e4e29ad96f858d2a8c79eab25dabbc60f2`. All26 Node test files
and27 editor syntax checks passed on that same source. This supersedes498 and
includes saved Build comparison, raw MAN normal Build and editable project copies.
The private retail disc SHA256 and466714416-byte length matched the expected
source. No game launched. Browser/rendered evidence remains separate; runtime
parity, genuine Live identity, gameplay and the full16-layer plan remain open.
Private logs: `sdk-regression-20261001-project-copy.log/.json` and
`node-checks-20261001-project-copy.json` under `local-output/sdk-20260909/`.
Python log SHA256: `cde485238587c1200c630c4cc6306f4cbf35d7ecdb4892458df9f02b1dfe7434`.

**Editable project copies (2026-10-01):** Copy project captures unsaved authoring
inputs into a fresh project-local folder, including referenced TIM/TMD files,
drafts, templates and saved views/selections. Hash readback, normal reopen and
source drift checks precede the completion report. Source files, dirty state and
Undo history are preserved; Open copy requires Save/Undo first when dirty.
Thirty-nine focused Python checks, all26 Node files and27 syntax checks passed.
Browser verified unsaved Dolk2 X9536, independent copy Save at X9600 and original
X9472 recovery with unchanged source bytes and zero errors; screenshots inspected.
No game launched. Postdates integrated498. See [Project copies](legaia-project-copies.md).

**Normal Build for raw streamed MAN (2026-10-01):** The typed source handoff now
routes raw MAN through existing audited placement/header/script composition,
preserving size, structural chunks, record layout and opaque bytes. Raw output is
explicitly uncompressed; raw validation and LZS round trips remain distinct.
Dolk2 placement, donor appearance, dialogue, P2 transition and flag changes
compose with a separate raw ANM bank. Twenty-seven retail-enabled Python checks,
25 Node files and26 syntax checks passed. Browser Review Build/Build agreed on
ten mixed Town01/Dolk2 changes, two overlays/68,930 bytes; authored/persisted data
unchanged, zero errors, screenshot inspected. No game launched; NPC drafts still
block normal Build. Postdates integrated498. See [Raw MAN Build](legaia-raw-MAN-normal-build.md).

**Saved Build audit comparison (2026-10-01):** Build history verifies two saved
packages and compares exact audit identities/records, including animation frame/
object and detailed deltas. Missing records do not imply deletion or runtime values.
Different retail sources, ambiguous identities, corruption and stale context reject.
Fifteen focused retail-enabled Python checks, all 25 Node files and 26 syntax checks
passed. Browser compared one changed Town01 record with eight identical records,
blocked identical IDs, rejected/restored corrupt bytes, and preserved all authored/
saved metadata with zero errors. Corrected spacing/status labels; final screenshot
inspected. No game launched. Postdates integrated 498. See
[Build comparison](legaia-build-comparison.md).

**Historical integrated SDK checkpoint after Build-history correction (2026-10-01):**
Retail-enabled discovery passed **498 Python tests in 368.664 seconds**,
exit0, no skips, on unchanged clean source `ba77695b6e4e86210a2d921e1e5d9935c706e611`.
All24 Node test files and26 editor module syntax checks passed on that source.
This supersedes the passing475 checkpoint and includes Project Settings,
dependency/material/effective-animation references, Build review, saved Build
history and its no-op package compatibility correction. The initial497-test
run at e49e09b0 failed four equality checks and one guard-order check; its evidence
is retained, and the unchanged regressions now pass in full discovery.
The user-owned disc SHA256 and466714416-byte length matched the expected source.
No game launched. Browser/package/rendered evidence remains separate, and native
runtime parity, genuine Live identity, gameplay and the full16-layer plan remain
incomplete. Private evidence: `sdk-regression-20261001-build-history-fixed.log/.json`
and `node-checks-20261001-build-history-fixed.json` under `local-output/sdk-20260909/`.
Log SHA256: `dd9141e0657fce546357327f9750709553de66284299018ba7353a218761ac28`.


**Build-history compatibility correction (2026-10-01):** Integrated discovery
at e49e09b0 ran497 tests but found four no-op package-equality failures and one
stale-source guard-order error. Content-derived package identity is restored;
separate immutable input receipts retain distinct authored snapshots. All29
focused regression checks passed, plus six history checks including conflicting
input-receipt rejection. The failed run is retained as evidence, not presented
as integrated acceptance. The integrated result above verifies this correction.

**Saved normal Build history (2026-10-01):** Successful Builds retain deterministic
completion receipts; Build history reopens reports after server restart. Input
match, package integrity and gameplay status remain separate. Verify saved files
checks receipt/audit/manifest, package payloads and exact ZIP contents. Older
folders without receipts show unavailable input match/integrity. Bounded scans
and path guards reject invalid coverage or redirected files. Nineteen focused
retail-enabled Python checks, all24 Node files and26 syntax checks passed.
Fresh-server browser reopened a real nine-change report and verified the package;
legacy labels/malformed request rejection passed, authored/persisted data unchanged,
zero page errors. Corrected clipped report columns and inspected the final view.
Postdates integrated475; no game launched. See [Build history](legaia-build-history.md).


**Read-only normal Build review (2026-10-01):** Review Build reuses the actual
serializer and manifest/file guards on detached authored inputs without creating
outputs. Retained NPC drafts remain explicit blockers; existing overrides are
assessed with the exclusion clearly recorded. Ready reviews can dispatch a Build
with browser/server input-identity guards. Five retail-enabled Python checks,
all23 Node files and25 syntax checks passed. Review audit/manifest/report matched
actual Build; normal raw/compressed animation packaging still passed. Browser
proved four retained draft blockers, nine existing changes, no review outputs,
stale dispatch rejection, Undo restoration and matching package creation in a
separate no-draft fixture. Zero page errors; saved metadata/authored content
unchanged; screenshots inspected; no game launched. Postdates integrated475.
See [Build review](legaia-build-review.md).

**Effective animation references and imported material reuse (2026-10-01):**
Actor reference views now distinguish initial retail clip bindings, effective
bindings from exact verified appearance donors, and authored draft donor clips.
Appearance donor relationships also navigate to imported actors. Missing bindings
remain unknown; equal counts do not create new combinations. Asset Database
material metadata is bounded to two eight-MiB entries, keyed by imported source,
scene, path and decoder version. Queries still verify retail sources before reuse
and assemble current authored relationships separately. Cache data is copied,
never persisted, and contains no pixels. Twenty focused retail-enabled Python
checks, all22 Node files and24 syntax checks passed; repeated retail query reused
material metadata while still verifying source. Browser proved separate retail/
effective links after one donor assignment, authored draft clips, current review
keys and Undo restoration; persisted metadata unchanged, zero page errors.
Screenshot inspected. Postdates integrated475; no game launched. See
[Effective animation relationships](legaia-effective-animation-references.md).

**Imported material source navigation (2026-10-01):** Model Dependencies and
texture Referenced by now include successful static UV/texture-page/CLUT address
matches with source hashes and material indexes. Missing/conflicting/unsupported
materials remain explicit diagnostics; shared and boot sources outside the active
navigable catalog remain disabled. Metadata has no pixel payloads. Relationships
describe candidate word providers, not unique upload ownership or runtime material
use; authored replacements remain separate. Twenty-three retail-enabled Python
tests, all22 Node files and24 syntax checks passed. Retail browser showed three
Dolk2 material groups linking to TIM69/0/19, opened its provenance and verified
the reverse texture Referenced by view, with zero
errors/authoring commands and unchanged authored content/history. Screenshot
inspected. Postdates integrated475; no game launched. See [Material references](legaia-material-references.md).

**Asset reference navigation (2026-10-01):** Asset Details exposes Dependencies
and Referenced by for verified imported membership/model assignments and active
script, dialogue, animation, field-table and landmark source relationships.
Authored draft donors and effective model assignments retain separate evidence
layers; unavailable destination scenes cannot be navigated. Runtime use,
script model pools, trigger dispatch and live animation state remain
unresolved. Fourteen focused Python checks, all22 Node test files and24 module
syntax checks passed. Browser verified actor/script and cross-scene navigation, stale-view rejection,
closed-request withdrawal, unchanged authored content/history and zero errors
or authoring commands; screenshot inspected. This feature postdates integrated475; full SDK/runtime
acceptance remains incomplete. See [Asset references](legaia-asset-references.md).

**Project settings inspector (2026-10-01):** Settings now uses SDK
property/action metadata for name, folder, retail source identity, scene count,
active scene and mode. Source/path values remain read-only. A validated rename
command supports dirty tracking, one Undo/Redo, Save/Open, no-op and stale-name
rejection without modifying imported content or authored assets. Browser proved
one quoted Unicode rename, persistence/history, stale-form withdrawal and zero
page errors; screenshot inspected and baseline restored. Independent reopen
retained four drafts and normal no-draft builds preserved every game-data
payload. The Unicode probe exposed invalid surrogate escapes in package TOML;
manifest names now emit literal UTF-8 with valid escaping. Fourteen focused
Python checks, all21 Node files and23 syntax checks passed. No game launched;
checks postdate integrated475. See [Project settings](legaia-project-settings.md).

**Latest integrated offline checkpoint (2026-10-01):** Retail-enabled
Python discovery passed **475 tests in 279.577 seconds**, exit0, no skips, on
unchanged clean committed source `9084e5454bd8e191f4f4b03e01f4c82497564619`.
All **20 Node test files** and **22 editor module syntax checks** passed on that
source. This supersedes the469-test checkpoint and includes script operand files
and atomic scene bundles, all12 catalog inspector types, bare scene URI search,
reviewed animation interpolation, and normal raw/compressed animation Build.
The final browser additionally verified observed authored-state changes withdraw
both interpolation Apply and review; baseline restored with zero page errors.
Independent user-owned disc SHA256 and466714416-byte length matched prior input.
No game launched. Native runtime parity, confirmed Live actor identity, gameplay
and the complete16-layer acceptance plan remain incomplete. Private metadata:
`local-output/sdk-20260909/sdk-regression-20261001-animation-build.log/.json`;
Node/syntax source hashes and results:
`local-output/sdk-20260909/node-checks-20261001-animation-build.json`.
Log SHA256: `2ceab6a68dee7a3088ff6faac10b73310931e1917b16cc0c4dcc206c4239791e`.

**Reviewed animation interpolation and raw ANM Build (2026-10-01):**
The animation channel editor now blends a copied verified pose into the selected
effective pose across an existing frame range. Read-only review precedes one
Undo/Redo command; unrelated channels remain. Translation rounds to integers and
per-axis shortest-path rotation to16-unit PSX increments, with explicit tie rules.
Actual retail verification exposed normal Build assuming all ANM banks were
compressed. Normal Build now reuses the source-preserving patch service for raw
and compressed banks with preimage/carrier checks. Thirteen focused Python
checks passed with retail input, including both normal Build layouts and existing
streaming composition; all20 Node files and22 editor syntax checks passed.
Retail browser passed review, stale-range rejection, Apply/Save/Undo/Redo and zero
errors. Independent reopened package matched all114764 bank bytes, preserved
other payloads and four drafts. Screenshots inspected; baseline restored.
No game launched or disc installed. Gameplay remains deferred; this postdates
integrated469. See [animation interpolation](legaia-animation-interpolation.md).

**Asset navigation inspectors (2026-10-01):** Actors, imported scenes,
actor presets and world-map landmarks now use the shared SDK read-only property
and registered-action contract, bringing supported catalog inspector types to12.
Navigation retains original source and authored provenance; landmarks expose
menu coordinates and discovery indices without claiming live state or gameplay
reachability. Source/catalog/schema/capability, busy and closed guards apply.
Fixed bare `scene://` searches being misread as `scene:` filters; explicit field
filters remain supported. Eleven focused Python checks, all19 Node test files
and21 editor syntax checks passed. Retail browser verified all four new panels,
actor selection, cross-scene navigation, preset library and landmark menu/source
catalog navigation, zero author commands/errors and unchanged authored state.
Screenshot inspected. Private evidence:
`local-output/sdk-20260909/navigation-inspectors-20261001/`.
No game launched. These checks postdate the integrated469 checkpoint; gameplay
and the full SDK objective remain incomplete.

**Scene script operand bundles (2026-10-01):** The asset tools now export
and review authored numeric operands across actors and partition-two script
owners in the active scene. All owners stage before one atomic Apply/Undo/Redo;
actual shared-byte conflicts, invalid owners and changed review contexts reject.
Five focused Python checks, all 19 Node test files and 21 editor syntax checks
passed. Retail browser verified two owners/four entries, export, read-only review,
Save/Undo/Redo, invalid/stale/closed guards and zero page errors. Independent
reopen retained four drafts; detached no-draft normal builds changed only MAN
bytes 4808/4811/4816/28557, with all other content payloads unchanged. Screenshot
inspected and baseline restored. No game launched or disc installed; gameplay
remains deferred. This postdates the integrated 469-test checkpoint. See
[scene operand bundles](legaia-script-operand-bundles.md).

**Script file review refinement (2026-10-01):** File controls now bind to
the script owner's authored-state snapshot. An owner edit observed during review
withdraws Apply in the UI; the server's existing stale-key rejection remains.
Reviews show a readable operand/instruction/current/proposed table, with complete
source-bound details collapsed. All 18 Node checks and 20 editor syntax checks
passed. Final retail browser checked one-command flag/model-selector/move imports,
actual partition-two asset-to-script navigation, P2 Apply/Save/Undo/Redo, stale
review withdrawal and a closed pending response, zero page errors. Baseline
restored; screenshot inspected. Independent Save/Open retained four drafts.
Detached no-draft builds matched the complete 45338-byte MAN: mixed actor edits
changed only4808/4811/4816; the P2 flag changed only28557. Raw record-table/opcode
checks established offsets independently; every other content payload was
unchanged. Private evidence:
`local-output/sdk-20260909/script-operand-files-advanced-20261001/`.
No game launched or disc installed. Gameplay remains deferred; these checks
postdate the integrated469-test checkpoint.

**Script operand JSON workflow (2026-10-01):** The script inspector now
exports authored movement, flag, wait, model-selector and transition operand
metadata. A bounded source/owner-bound file review stages every entry through
existing verified commands; one atomic Apply supports Undo/Redo and Save/Open.
Supplied entries replace their authored fields; other entries/components remain.
Duplicate/nonfinite/extra/oversized files, wrong source/owner and stale reviews
reject without partial edits. No instruction bytes, dialogue, control-flow layout
or runtime state are transferred. Nineteen focused Python checks, all 18 Node
checks and 20 editor syntax checks passed. Retail browser verified export,
read-only review, Apply/Save/Undo/Redo, wrong-owner rejection and restored baseline,
zero page errors. Screenshot inspected. Independent reopen retained all four
NPC drafts; a detached no-draft normal Build matched the complete 45338-byte MAN
with only offset4811 changed for owner0003's selector240→239. Other content
payloads were unchanged. Package SHA256:
`e440d265be2a20a7008801e89c60eb1de8adc586ef3cac470e6ad22dc4aad53e`.
Normal Build still rejects drafts. Private evidence:
`local-output/sdk-20260909/script-operand-files-20261001/`. This postdates the
469-test integrated checkpoint; execution/gameplay remains deferred. No game
launched or disc installed. See [operand files](legaia-script-operand-files.md).

**Previous integrated offline checkpoint (2026-10-01):** Retail-enabled
Python discovery passed **469 tests in 176.301 seconds**, exit 0, no skips, on
unchanged clean committed source `d948b2a0f27e77c2b60f17b490ca7d8878389646`.
All **17 Node checks** and **19 editor module syntax checks** passed on that
source. This supersedes the 463-test checkpoint and includes asset field search,
atomic group preset Apply, detached group scene inspection and SDK asset inspector
tools. The user-owned disc SHA256 and 466714416-byte length were independently
verified. Existing browser, package and saved-project evidence remains separate;
this does not prove native runtime parity, Live actor identity, gameplay or all
16 acceptance layers. No game launched. Private command/source/result metadata:
`local-output/sdk-20260909/sdk-regression-20261001-asset-inspectors.log/.json`;
Node/syntax file hashes and results:
`local-output/sdk-20260909/node-checks-20261001-asset-inspectors.json`.
Log SHA256: `eed72436dcc91f0631446e3786abeb42a58964fa8e8bfd967c68a33967da7de4`.

**SDK asset inspector tools (2026-10-01):** Asset Details now uses the
same SDK property/action contract as actor inspectors for eight catalog types:
models, textures, animations, scripts, dialogue, collision, triggers and regions.
SDK metadata supplies labels, read-only stable identity/source properties and
capability-bound tools; explicit type-specific handlers open the existing
verified workspaces. Details is now a consistent entry point, while asset-card
shortcuts remain. Changed source/catalog record/schema/capability, busy state and
closed dialogs block dispatch. Duplicate authored-open buttons are removed for
these types; authored details and source provenance remain separate. These are
inspector tool groups, not invented or persisted entity components. Eleven
focused Python checks, all 17 Node checks and 19 editor syntax checks passed.
Retail browser opened all eight Details panels through actual browser buttons,
loaded model/texture previews and opened the resource tools; busy/closed guards,
unchanged actors, zero author commands and zero page errors passed. Screenshot
inspected. Evidence: `local-output/sdk-20260909/asset-inspector-20261001/`.
This postdates the integrated 463-test checkpoint. Specialized editing forms,
other asset types, runtime identity and gameplay still need further work.
No game launched.

**Group preset scene inspection (2026-10-01):** The extension adds read-only Current/Proposed comparison in the assembled
3D scene for position, appearance and combined group presets. Return retains the
review for atomic Apply; Restore, changed selection and a closed pending request
discard it. Preview preserves the camera and unknown guest Y, and writes no
actor components. Markers and framing now use the active proposal's display
coordinates, matching its rendered meshes. Twelve focused Python checks, all 16 Node checks and 18 editor module syntax
checks passed. The final scene screenshot was inspected. All three scopes also passed the production
decoder against freshly verified retail-source scene responses. The retail browser
checked two changed actors, Current/Proposed/Return, Restore, late-response and
selection guards, Apply/Save/Undo/Redo, matching marker coordinates and unchanged
camera, with zero page errors. Independent normal Build readback matched the
entire 45338-byte MAN with only five expected donor/position bytes changed; all
other package payloads were preserved. Normal Build proof used a detached view
without drafts; projects containing drafts remain rejected. Private evidence:
`local-output/sdk-20260909/preset-batch-scene-20261001/`. These changes postdate
the integrated 463-test checkpoint. Gameplay and
runtime parity remain pending; no game was launched.

**Actor group presets (2026-10-01):** Position, appearance and combined
presets now review all 2–128 selected imported actors before one atomic Apply /
Undo/Redo command. Fresh source/target/donor compatibility, canonical membership,
stale-key rejection and no-op groups reuse existing commands on a detached
staging view. Absolute axes and possible overlaps are explicit; unrelated data
and unknown Y remain preserved. Eleven focused Python tests, all 15 Node checks
and 18 editor syntax checks passed. Retail browser group review/Apply/Save/Undo/
Redo passed without preview writes or page errors; screenshot inspected.
Independent Save/Open retained all four NPC drafts. A detached no-draft normal
Build package matched the complete 45338-byte town01 MAN with exactly target 0012
X changed from 3008 to 2944 at offset 8498. Package SHA256:
`a59e32eaf00f07971a0f36eb83ff10529eea908d34dd98404f07042bc6cf6567`.
Normal Build still rejects drafts; no game launched or disc installed. This
postdates the 463-test checkpoint; gameplay remains deferred. See
[group presets](legaia-actor-group-presets.md).

**Asset browser field search (2026-10-01):** Search now supports name,
stable ID, type, scene, model reference, recorded confidence and provenance
filters, quoted phrases and exclusions. Unknown fields and malformed/oversized
queries show errors without broadening results. Existing category and resource
scope remain; recorded confidence and model matches do not establish aggregate
certainty or runtime use. All 14 Node checks and 17 editor syntax checks passed.
Retail-source browser verified field combinations, imported/authored model users
against the SDK reference graph, phrases/exclusions, provenance, URI IDs, errors,
reset and actor navigation without authoring commands or actor changes, zero
errors. Screenshots inspected; narrow-panel controls now wrap. This postdates
the 463-test checkpoint. No game launched. See [asset search](legaia-asset-search.md).

**Historical integrated offline checkpoint (2026-10-01, 463 tests):** The retail-enabled SDK
Python discovery suite passed **463 tests in 264.543 seconds**, exit 0, no skips,
on unchanged committed source `2ca0a1a4fa0044f55e9b0dc6d6c217b9e061f578`.
This supersedes the 457-test checkpoint and includes the later SDK animation/preset
inspector actions and saved scene views. All **13 Node checks** and **16 editor
module syntax checks** passed separately on the same source. The disc SHA-256
was independently verified against the recorded retail source. Browser, package,
saved-project and rendered acceptance retain their separate evidence; this suite
does not establish native runtime parity, Live actor identity or deferred gameplay.
No game was launched. Private command/source/result metadata and log:
`local-output/sdk-20260909/sdk-regression-20261001-scene-views.log/.json`;
Node/syntax hashes/results: `local-output/sdk-20260909/node-checks-20261001-scene-views.json`.
Log SHA-256: `5509fa89b90dd8f040c80c33bc7f75cb02cd7cf0e38ac100361772f009d16111`.

**Saved scene views (2026-10-01):** Named project-local camera bookmarks
retain projection, target/orbit/distance, authored/retail representation and scene
layers, bound to the imported scene hash. Recall supports cross-scene navigation
without actor edits or a history command; metadata create/rename/update/delete
support Undo/Redo and Save/Open. Stale source/review, invalid cameras and changed
source beneath saved views/history reject. Live and active proposal inspections
disable capture/recall. Camera targets are editor display coordinates, not proof
of retail height or runtime identity. Fourteen focused Python/HTTP checks and
Node validation/syntax passed. Retail-source browser checked exact display
recall, cross-scene navigation, rename/delete/Undo and unchanged actors, zero
page errors; screenshot inspected and button wrapping corrected. This postdates
the 457-test checkpoint. No game launched. See
[saved scene views](legaia-saved-scene-views.md).

**Historical runtime review comparison (2026-09-30):** Saved node reviews
now support a baseline/comparison table, coordinate sample differences, status
and text filters, complete decoded evidence, return navigation and metadata
export. Declared scene/epoch/profile mismatches reject; matching node keys remain
unconfirmed because v1 has no process or object-lifetime identity. Missing axes
and numeric overflow retain unknown deltas; file-only keys do not imply spawning
or removal. Node checks and synthetic browser comparison/filter/download/return,
context rejection and closed-read withdrawal passed, zero page errors or authoring
requests. Project/camera/runtime state was unchanged. Screenshot inspected. This
postdates the 441-test checkpoint; no real runtime capture or game launch occurred.
See [saved runtime reviews](legaia-runtime-node-review.md).

**SDK animation and preset actions (2026-09-30):** Four more actor tools
now consume SDK action descriptors and registered handlers: imported scene
animation preview, Edit-only channel authoring, eligible reference animation
preview and the preset library. The SDK supplies reference-clip eligibility as
detached view metadata without modifying imported components. Unsupported actions
are omitted; source/selection/busy/Edit guards remain in dispatch. Eight focused
Python/HTTP checks and Node action eligibility checks passed. Retail-source
browser opened all four existing tools, checked unsupported/busy guards and
confirmed no actor changes or authoring commands, zero errors; screenshot
inspected. Specialized tool forms and asset actions still use their existing
adapters. This postdates the457-test checkpoint. No game launched. See
[inspector contract](legaia-inspector-schema.md).

**Historical integrated offline checkpoint (2026-09-30, 457 tests):** The retail-enabled SDK
Python discovery suite passed **457 tests in 178.185 seconds**, exit0, no skips,
against unchanged committed source `3c8d8f46af7063f2993d49fe74ec02e6a0005639`.
This supersedes the 441-test checkpoint and includes the later draft repetition,
project transition discovery, SDK inspector services, combined actor preset
review/projection and preset file transfer/source protection. All12 Node checks
and10 module syntax checks passed separately on the same source, including the
inspector registry, model-user selection, historical review comparison and
combined preset scene guards. Browser, package, saved-project and rendered
acceptance retain their independent evidence. This does not establish native
runtime parity, real Live actor identity or deferred gameplay. No game launched.
Private command/source/result/hash metadata and log:
`local-output/sdk-20260909/sdk-regression-20260930-preset-files.log/.json`;
Node/syntax metadata: `local-output/sdk-20260909/node-checks-20260930-preset-files.json`.
Log SHA256: `d5095cd0f752881ce0fcd7212c6cfa09e5361719362b62356c20906759734732`.

**Actor preset file transfer (2026-09-30):** Position, appearance and
combined presets can export metadata-only JSON and import into a project with
the same freshly verified source import. Name/source/donor/schema review precedes
one independent library entry and Undo/Redo; actors remain unchanged. Duplicate
names, changed sources, stale reviews, extra/payload fields and bounded JSON
reject. Saved preset libraries now block changed-source reimport after reopen.
Nineteen focused Python/HTTP checks and retail-source browser export/review/import/history,
no-preview writes, size/closed-response rejection passed, zero errors; screenshot
inspected. Independent cross-project retail Save/reopen/re-export passed with
preserved components/hash and no actor/import edits. This postdates the 441-test
checkpoint. No game launched. See [preset files](legaia-actor-preset-files.md).

**Combined preset scene comparison (2026-09-30):** The combined preset
review can now inspect proposed position and initial donor appearance together
in the assembled scene. A freshly verified detached project projection preserves
current overrides/history. Proposed/Current retains the camera; Return reopens
the review for one Apply/Undo, while Restore discards the retained dialog.
Placement/display/matrix/authored-layer and donor/owner/unrelated-geometry checks
bind the scene response. Scene components, preset or selection changes withdraw
it, and scene export requires restoration. Fourteen focused Python tests and Node
preset/appearance projection checks passed. Retail-source browser comparison,
no-preview writes, camera, Return/Apply/Undo, Restore, closed delayed-response withdrawal and stale-target rejection
passed with zero page errors; screenshot inspected. This postdates the 441-test
checkpoint. No game launched; gameplay remains deferred. See
[combined actor presets](legaia-combined-actor-presets.md).

**Combined actor presets (2026-09-30):** Authored templates can capture
position axes and a verified appearance donor together. A source/target-bound
read-only review shows imported/authored/effective/proposed positions and donor;
Apply updates both components atomically in one Undo/Redo entry, retaining other
axes/components. Thirteen focused tests and retail browser capture/review/history/
Save/reload/stale rejection passed; screenshot inspected, zero page errors.
Independent disk reopen retained the preset and target edits. A detached no-draft
Build view matched every expected MAN byte, retaining earlier menus, selector,
placements and appearances; package SHA256:
`a59e32eaf00f07971a0f36eb83ff10529eea908d34dd98404f07042bc6cf6567`.
Normal Build rejects projects containing NPC drafts. Full experimental archive
readback also retained all four drafts and preset edits, SHA256:
`2f9437b5a0eda2ed4ae9eaf8bf810a6f2f9c0936942e1caae8c3c0a818e43381`.
No disc installed or game launched. Gameplay remains deferred; this feature
postdates the441-test checkpoint. See [combined actor presets](legaia-combined-actor-presets.md).

**Select effective model users (2026-09-30):** Model asset details now offer
scene-qualified selection of2–128 effective imported actor users for the existing
viewport/group tools. Retail-only assignments and NPC drafts remain separate.
Fresh SDK references, scene owners and effective assets are checked before
selection; changed or ambiguous usage rejects. No component/history command is
issued by selection. Node checks and retail browser exact membership for model0112
(actors0005/0011/0012), Dolk2-to-town01 navigation and stale-review rejection
passed, zero page errors. Screenshot inspected. A footer obstruction found during
the cross-scene check was fixed by reserving asset-list space and scrolling the
library tools. These are initial assignments; runtime script replacements remain
unobserved. No game launched. See [model-user selection](legaia-model-user-selection.md).

**SDK-driven component inspector (2026-09-30):** Project state now exposes
a versioned property contract for Transform, ModelRenderer, Animation,
ActorAppearance, RuntimeCorrelation and RetailMetadata. The editor consumes it
for layered number/reference controls, read-only properties and evidence details;
unregistered components receive escaped read-only SDK details. Transform commands
use a bounded registry adapter and ordinary ProjectService validation/history.
SDK authoring limits remain distinct from retail Build encoding, with unresolved
retail Y and project-only authored height explicit. Busy/Edit/selection/source
checks guard controls. Nine focused Python tests and Node renderer/command/
fallback/layer/detail checks passed. Retail browser X edit/Undo and project-only Y Build
issues passed, zero page errors. Retail layered appearance Clear/Undo preserved
imported/effective pairs; runtime unconfirmed state and provenance details passed,
zero errors, screenshot inspected. Six donor/model/script/candidate action buttons
now consume SDK action metadata and registered handlers, with capability/condition
filtering and Edit/busy/stale dispatch guards. Retail registered Clear/Undo and
loaded source-script inspection passed. Specialized forms, animation/template
actions and asset inspectors retain existing adapters; migration is incomplete.
This feature postdates the441-test checkpoint. No game launched. See
[inspector property contract](legaia-inspector-schema.md).

**Project-wide transitions (2026-09-30):** Project transitions now merges
source-qualified decoded scene-change references across1–64 imported scenes,
with separate source coverage, unavailable reasons and imported destinations.
Inspect source script navigates across scenes to its instruction; imported
destinations retain the existing scene navigation. Imported/authored/effective
entry operands remain separate. Five focused tests passed, including self-edge,
merged identity, unavailable source, no-write and stale-state checks. Retail
HTTP/browser discovery found3 references across town01/Dolk2,180 scripts,
88 partial,0 unavailable; cross-scene source navigation and strict request shape
passed with zero page errors. Screenshot inspected. This feature postdates the
441-test checkpoint. These references do not establish reachable gameplay routes,
complete exits or runtime scene connections. No game launched. See
[project transition guide](legaia-project-transitions.md).

**NPC draft repetition (2026-09-30):** Repeat draft previews a named series
of donor-bound NPC copies with a count and X/Z grid spacing. Proposed/Current
scene comparison and Return retain the review; Apply adds the copies in one
Undo/Redo entry. Eleven focused Python tests and Node projection checks passed.
Retail-source browser checks confirmed three copies at X2944/3008/3072, Z5440,
unchanged existing scene/assets, preserved donor pairs, no preview writes,
retained camera, Apply/Undo/Redo, Save/reload, atomic bounds and stale-source
rejection, and zero page errors. Screenshot inspected; independent disk reopen
retained all four drafts. Independent experimental PROT reopen decoded the final
MAN and verified four appended records' exact positions, initial model105 /
animation13 and script bytes equal to donor0011. Archive SHA256:
`b386fb186853a10e445030c3b7f3dc09d2dde1d3faa817acdc6fb6b7f711b262`.
This feature **postdates the 441-test integrated checkpoint**. Normal Build
rejects projects containing NPC drafts; experimental export retains its existing gates. Runtime spawning,
scheduling, collision and visibility remain unverified. No disc installed or game
launched. See [NPC repetition guide](legaia-npc-draft-repetition.md). Private
browser/disk/archive evidence: `local-output/sdk-20260909/draft-repeat-20260930/`.

**Historical integrated source checkpoint (2026-09-30, 441 tests):** the retail-enabled SDK discovery
suite passed **441 Python tests in 177.315 seconds**, exit0, no skips, against
unchanged committed source `e76b05fb1775802057e41c33a5a1e4e36301a093`. This includes
group donor appearance and its detached scene projection, actor alignment/
distribution, saved actor selections and all prior Python SDK services. It
supersedes the425-test source checkpoint below. All eight Node checks (font,
texture usage, script operands, rectangle picking, saved runtime review, actor
group scene/selection, group appearance scene and saved actor selection recall)
and five editor/renderer/group module syntax checks passed separately on the same
unchanged source. Browser/package/disk/rendered evidence remains independent;
this checkpoint does not establish deferred gameplay or native runtime parity.
No game launched. Private exact-command/source/result/hash metadata and log:
`local-output/sdk-20260909/sdk-regression-20260930-saved-selections.log/.json`.
Node evidence: `local-output/sdk-20260909/node-checks-20260930-saved-selections.json`.
Log SHA256: `d095c9718e9cb0269f99a5eeccf1f05b265051dee98984abdee197af6decbed2`.

**Saved actor selections (2026-09-30):** the viewport tool row now saves named
source-bound imported actor groups for later editing. Create, Rename, Replace
members and Delete use project commands/Undo/Redo; Save/Open retains UUID identity,
scene import hash and sorted actor IDs. Recall can navigate to another imported
scene and seed the existing placement/appearance/component tools. It changes no
actor component or command history. Stale reviews reject and refresh displayed
state; changed imports are blocked under selections or their history. Fifteen
focused Python tests passed in1.318s, plus Node recall binding checks. Retail
browser create/rename/history/member replacement/delete/Save/reload, Dolk2-to-town01
recall, placement-dialog seeding and stale rename checks passed, zero page errors.
A clipped Recall button found in the first browser run was fixed with a wrapping
dialog layout; final screenshot inspected. Independent retail disk reopen verified
saved membership/import identity and unchanged build/scene input keys. These are
editor selections, not game parenting/prefabs. No gameplay check is required for
selection metadata; authored game edits retain their existing deferred checks.
Its Python services are included in the441-test checkpoint above. No game launched.

**Actor group alignment/distribution (2026-09-30):** **Actor group placements**
now offers Align X/Z to a selected anchor and Distribute along X/Z, alongside
offsets. Alignment preserves its anchor; distribution preserves coordinate
endpoints and sorts ties by stable source ID. Interior coordinates round to the
nearest retail64-unit grid (ties upward), with adjacent gaps differing by at most
64. Insufficient span rejects before mutation. Retail/Authored/Effective/Proposed
review, no-write scene comparison/Return/Restore, atomic Apply/Undo, Save/Open and
existing Build serialization are connected. Only changed axis values are authored;
height, facing, source and unrelated components remain unchanged. Ten focused
Python tests, existing Node group checks and two retail browser workflows passed;
zero page errors. Town01 actor0013 distribution Z changed2880 to3648 while endpoint
actors0012/0011 remained1856/5440. Independent ZIP/LZS MAN readback matched every
expected byte, retaining donor assignments, earlier placements, three menus and
selector240. Screenshots inspected. No game launched or package installed; the
441-test full checkpoint includes its Python services. See
[group placement guide](legaia-actor-group-offset.md). Gameplay remains deferred.

**Actor group appearance scene comparison (2026-09-30):** reviewed donor
assignments now offer **Inspect group appearance in scene** before Apply.
A detached SDK projection resolves the verified initial model/animation pair at
both actors' existing placements. Proposed/Current switches preserve the camera;
Return retains the donor review, Restore discards the comparison, and export
requires restoration. Source or placement/group changes withdraw the comparison;
closed delayed responses cannot attach. Seventeen focused retail-enabled Python
tests passed in 7.010s, no skips; the new Node projection checks passed. Town01
actor0011/0012 browser comparison verified changed geometry, unchanged positions,
transforms and unrelated geometry/texture content, no inspection writes, retained
Return/Apply/Undo, Restore, source withdrawal and delayed-response discard. Zero
page errors; comparison screenshots inspected. Shared pose geometry may identify
a different first source actor after deduplication; only that attribution is
ignored when comparing unaffected geometry, retaining model/animation evidence.
No game launched or package installed. This feature postdates the425-test full
checkpoint; its Python services are now included in441. Private evidence: `local-output/sdk-20260909/group-appearance-scene-20260930/`.

**Actor group donor appearance (2026-09-30):** selected imported actors now
share a donor-backed initial model/animation assignment through Group appearance.
Discovery intersects freshly verified compatible pairs across every actor; source,
object-count and initial-animation restrictions remain explicit. Preview separates
Retail/Authored/Effective/Proposed data without writes. Apply revalidates the whole
group before one command/Undo entry, preserving other components. Sixteen focused
retail-enabled tests passed in 7.005s, no skips. Town01 actor0011/0012 had12 common
donors; browser discovery/preview/Apply/Undo/Redo/Save and stale last-member rejection
passed, zero page errors. Actor0001/0002 correctly had no supported pair. Screenshot
inspected. Independent saved-project/package MAN readback matched exact donor
assignments and retained positions, three menus and selector240. No game launched
or package installed. Its Python services are included in the441-test full checkpoint; see
[group appearance guide](legaia-actor-group-appearance.md). Gameplay is queued.

**Historical integrated source checkpoint (2026-09-30):** the retail-enabled SDK discovery
suite passed **425 Python tests in 172.910 seconds**, exit 0, no skips, against
unchanged `55f5db15ec610db8642e1e995c29a0b4c6855730`. This includes actor group component
review/revert and all earlier Python services, superseding the 421-test checkpoint
and historical lower counts below. All six Node checks and editor/group/renderer
syntax passed separately against the same source, including box/range guards.
Browser/package/rendered checks retain their independent evidence; this run does
not establish gameplay or runtime parity. No game launched. Private log/metadata:
`local-output/sdk-20260909/sdk-regression-20260930-group-components.log/.json`.
Log SHA256: `69e0a61d32f73d1b313b00b543b0199f8787519991430e17eff44e23c31be60c`.

**Actor group component review/revert (2026-09-30):** selected imported actor
groups now offer Review group components, showing each actor's authored settings
or retail inheritance. A source-bound review includes every selected actor,
including inherited members; Revert validates the whole group before removing
only the chosen component, with one Undo entry. Other components and imported
provenance are preserved. Fifteen focused group/component/history tests passed
in 1.771s with no skips. Retail town01 three-actor browser review, atomic Revert/
Undo, unrelated-component preservation, stale inherited-member rejection and
closed pending-response checks passed with zero page errors; screenshot inspected.
A private fixture was saved during preparation; no game or package installation.
The 425-test source checkpoint includes this backend addition; browser evidence
remains separate. See
[component review guide](legaia-authored-component-review.md).

**Actor box and hierarchy range selection (2026-09-30):** Box select actors
now draws a marquee and gathers visible mesh IDs from one depth-tested render,
read in bounded strips. Shift-click selects a range in the filtered hierarchy;
Ctrl/Command adds boxes or ranges to the existing group. Replace/add operations
retain the 128-actor bound. Escape preserves selection; source/camera changes
reject a pending box, and proposal inspection disables these selection tools.
Node range/merge and rectangle/high-DPI/strip/restoration checks passed. Actual
2x-DPI town01 browser ranges, exact mesh ID boxes, hidden actor exclusion,
reverse/add/empty boxes, Escape, source withdrawal and exact placement-review
seeding passed without selection-service or authoring requests/page errors.
Screenshots inspected; no Save or game launch. These UI checks are separate
from the earlier 421-test Python checkpoint. See
[group placement guide](legaia-actor-group-offset.md).

**Viewport/hierarchy actor group selection (2026-09-30):** Ctrl/Command-click
now toggles imported actors into a bounded 128-actor group, with cyan scene and
hierarchy highlights, Frame actor group, Clear group and Review group offset.
Review seeds the existing placement dialog; normal clicks retain focused-actor
inspection. Group selection is transient and sends no selection or authoring
requests. Single-actor handles are suppressed while any group is selected.
Node membership/bounds/immutability checks and real town01 hierarchy/visible-mesh
Ctrl-click, filtering, framing, seeded review, +64 X proposal drag, atomic Apply
and project-restoring Undo passed. Client source/mode guards were checked with
injected state changes; actual Live remains unavailable without a checked runtime.
Screenshot inspected; no game launched or project saved. These UI checks are
separate from the earlier 421-test Python checkpoint. See
[group placement guide](legaia-actor-group-offset.md).

**Actor group proposal drag handles (2026-09-30):** Proposed mode now offers
X/Z handles for the selected actor group, snapping relative movement to 64 units.
Release revalidates the whole proposal without authoring; Return shows the updated
offsets/table, and Apply remains one atomic command. Escape restores the prior
proposal, bounds failures reject the whole move, and Current authored mode has
no group handles. Node offset/immutability/bounds checks and actual retail town01
browser pointer drags (+256 X, +64 Z), cancellation, no-write preview, Return,
one-command Apply and project-restoring Undo passed with zero page errors.
Screenshot inspected. This UI addition was checked separately after the 421-test
Python checkpoint; no new full-suite result is claimed. No game launched. See
[group placement guide](legaia-actor-group-offset.md).

**Actor group 3D proposal comparison (2026-09-30):** reviewed group offsets
now inspect in the assembled viewport, with Proposed/Current authored layers,
Frame group, Return retaining the draft and Restore. Only proposed transforms
change; source terrain preview heights are recalculated, with unknown runtime
elevation explicit. Single-entity handles are disabled; group handles are described
above. GLB export requires Restore.
26 focused tests in 1.301s/no skips and Node guards passed. Retail town01 exact
actor transforms, unchanged geometry/unrelated transforms, camera comparison,
Return/Restore and source withdrawal passed with zero authoring requests/page
errors; screenshots inspected. Separate Return Apply/Undo and export rejection
passed. No game launched. The 421-test source checkpoint includes this addition; browser evidence remains separate. See
[group placement guide](legaia-actor-group-offset.md).

**Actor group placement offsets (2026-09-30):** the editor toolbar now
previews and applies X/Z offsets to 2–128 imported active-scene actors. Retail,
Authored, Effective and Proposed positions stay separate. All source-grid/bounds
checks complete before one atomic command and one Undo entry. History protects
all group actors during reimport; stale source/project/actor states and replay
are rejected. 23 focused retail-enabled tests passed in 9.731s, no skips. Retail
town01 browser preview/no-write/bounds/Apply/Undo/Redo/Save and closed pending
response checks passed with zero page errors. Independent saved-project/package
MAN readback matched the four placement bytes while retaining prior menu and
selector edits. Screenshots inspected; no game launched or package installed.
The 421-test source checkpoint includes this feature; browser/package evidence remains separate. See the
[group placement guide](legaia-actor-group-offset.md).

**Authored component review (2026-09-30):** Authored Assets details now
show component-level review and source-bound Revert actions for actors, P2
scripts and scenes. Removing one component preserves the others and imported
evidence; Undo/Redo and Save/Open retain normal behavior. Stale reviewed values,
source/project identities and replay are rejected before mutation. 25 focused
tests passed in 1.334s with no skips. Retail town01 browser review/revert/history/
Save and stale rejection passed; independent disk reopen retained the selector
and three unrelated menu edits. Screenshot inspected, no page errors. No game
launched. The 421-test source checkpoint includes this feature; browser/package evidence remains separate. See the
[component review guide](legaia-authored-component-review.md).

**Script model-selector authoring (2026-09-30):** reached SET_ACTOR_MODEL
signed16 operands now use source-qualified commands, separate retail/authored/
effective layers, draft dispatch display, exact instruction-field navigation,
Undo/Redo, persistence, descriptor Build and experimental streaming/append output.
Runtime model-pool bases, actual assets and restaging remain unresolved; the
viewport does not execute the opcode. 34 focused retail-enabled tests passed in
35.413s with no skips, including five selector tests covering P2 ownership and
rebased extended actor-context rejection. Node binding/editor syntax and Dolk2 browser workflows passed; screenshots
inspected. Town01 package readback matched the exact MAN, retaining three menu
edits; Dolk2 rebuilt PROT contained the exact candidate. The 421-test source checkpoint
includes this feature; browser/package evidence remains separate. No game launched; gameplay deferred. See the
[model-selector guide](legaia-script-model-selectors.md).

**Project-wide text search (2026-09-30):** the same text search panel now
covers all imported scenes, retains scene coverage/reasons and opens the owning
scene before focusing the exact edit field. Discovery uses detached views and
checks imported/source and all dialogue-override identities. Retail town01/Dolk2
found645 supported runs across180 scripts (88 partial). Eleven focused tests and
editor syntax passed. Browser layer/scene search, cross-scene/return navigation,
stale aggregate and held-response close/reopen guards passed with unchanged
text/history and zero authoring requests/page errors. Screenshot inspected.
Explicit navigation changes Active scene; discovery leaves it unchanged.
Unknown/unvisited text remains excluded. The 405-test checkpoint includes this feature; gameplay remains deferred. See [text search guide](legaia-scene-text-search.md).

**Scene text search (2026-09-30):** source-qualified dialogue/menu runs
are searchable by text, owner and retail/effective/authored layers, with pages
and exact actor/partition-two edit-field navigation. Retail town01 discovery
found267 supported runs across91 scripts (60 partial), including eight P2 runs.
Nine focused Python tests and editor syntax passed. Browser filtering, paging,
field navigation, stale text-state and closed pending-response guards passed
with unchanged project state, zero authoring requests and page errors. Screenshot
inspected. Unknown/unvisited bytes and unsupported dialogue remain excluded;
coverage is explicit. The 405-test checkpoint includes this feature; gameplay deferred.
See the [scene text search guide](legaia-scene-text-search.md).

**Retail glyph preview (2026-09-30):** supported dialogue/menu forms show
Retail, Effective and padded unapplied Draft glyph stencils and source advances.
Nine focused Python tests, JavaScript font checks and editor syntax passed.
Retail browser pixel/advance readback, invalid drafts, Discard, held-response
close/reopen and malformed request rejection passed with unchanged project
state, zero authoring requests and page errors. Screenshot inspected. Controls,
substitutions, boxes, wrapping, pager behavior and runtime tint are not simulated.
The 405-test checkpoint includes this feature; gameplay remains deferred. See the
[glyph preview guide](legaia-text-glyph-preview.md).


## Ready for offline review

- Scene workspace: source-based textured scenes, hierarchy selection, inspector, orthographic/top views, coordinate locator, authored/retail layers, and actor/decorative/shared-scenery X/Z handles. Shared scenery browser checks moved three instances while preserving366 unrelated instances and verified Undo on both axes.
- Script movement: verified MOVE_TO/NPC_RUN X/Z authoring, source/effective values, history and persistence, viewport targets with source-instruction navigation, and descriptor/streaming experimental output composition. Y, executed branches and actor identity remain unknown where evidence does not establish them.
- Script flags and waits: source-qualified flag SET/CLEAR/TEST bit operands and WAIT_FRAMES targets have Inspector Apply/Clear/Discard, ordinary history and persistence, audited Build output and experimental append composition. Flag discovery shows separate retail/authored/effective indices with immutable retail grouping. Wait targets use host ticks0..32767; special context flags, larger wait targets and unresolved control flow remain unavailable. Story semantics, actual timing and runtime values are unverified.
- Animation: supported rigid clips can be previewed and exported. Channel edits and same-object retail/effective copy across frames/ranges use Apply/Undo/Discard. Existing-layout raw-record and readable channel-JSON download/import support retail/effective values. Raw-record checks pass shared-conflict, clear, persistence and package readback checks. Browser checks cover late responses, invalid selections and cross-object rejection. Shared clip users are explicitly listed. Proposed files can be inspected without applying them in both the model and scene viewers, restored, and returned to the same file form for explicit import.
- Model shapes: a diagnostic wireframe overlay displays all decoded triangle edges in the model viewer, including hidden edges. Focused WebGL and retail browser checks cover toggle, buffer reuse, vertex updates, picking and no project writes. Direct vector Inspector editing, per-vector retail reset, inspected-vertex camera location and exact-vector audit navigation are connected with focused browser checks. Existing-layout TMD, ordered-vertex OBJ and source-bound vertex/normal JSON replacements preserve source primitive/material data. Model build reports show scalar audits and navigate only to hash-matching authored previews. Normal-only edits are not visualized as lighting: the WebGL shader uses colors/textures without normal-based lighting. Equivalent oriented face order and relative indices passed exact roundtrip and isolated vertex edits on119 town01 models. A saved OBJ project passed Undo/Redo, reopen and package build.
- Textures: indexed scene palette-word and pixel-index editing, retail/effective JSON downloads and source-bound complete palette/pixel JSON imports are connected to texture Undo/Redo, Save/Open and Build. All96 town01 indexed textures round-tripped exactly. Source layout and other packed pixels are preserved; gameplay appearance remains unverified.
- Output: supported edits compose into private packages or experimental disc exports. Input snapshots, hashes and reopened archive checks support later review. Package descriptions list emitted edit families; output collisions are rejected instead of silently replacing existing builds.

**Scene proposal comparison (2026-09-30):** model-transform, model-file and
texture proposals can switch between Proposed (not applied) and Current authored
scene while retaining the proposal and camera framing. Exact layer/restore and
unchanged project checks passed in retail browser runs for shared model0074
(11 instances), a JSON model-file proposal, and texture29 (19 geometries,
31 materials, 58 instances). Texture checks also verified unchanged camera and
withdrawal on a stale scene source. These are browser checks, separate from the
390-test Python checkpoint; game appearance and retail visibility remain deferred.

**Animation scene comparison (2026-09-30):** supported animation inspections now
switch between the inspected animation and Current authored scene, retaining the
selected frame and camera. Switching layers pauses playback; the current layer
disables scrubbing, playback and rate controls. Returning restores the inspected
frame and slider together. A retail actor0011 JSON proposal (15 frames) passed
exact layer/placement/base checks, playback pause, Return retaining the file,
Restore, stale-source withdrawal and unchanged project state, with zero authoring
requests or page errors. Screenshot inspected. This is separate browser evidence;
retail animation timing, playback and gameplay visibility remain deferred.

**Independent animation consumer review (2026-09-30):** Blender 5.2.2 rendered
and evaluated a fresh complete Dolk2 actor0001 GLB (30 frames, ten rigid objects,
three embedded textures). All61 source-decoded samples, including half-frame STEP
holds and terminal pose, matched within0.000018 source units;24 distinct geometry
snapshots establish motion. First/middle/last renders were visually inspected.
The saved Blender scene reopened with all meshes, animation actions and three
packed textures. A reusable offline review tool and [consumer review guide](legaia-glb-consumer-review.md)
are available. Acceptance is specific to this clip; wider clips/consumers, retail
cadence, lighting and gameplay remain unverified. No game was launched.

**Indexed texture rectangle copy (2026-09-30):** copy an existing 4/8-bpp
image region to another location in the same texture, with draft pixels and
source/destination bounds before Apply. Overlaps read the immutable pre-copy
indices; packed neighbors, palettes, headers and VRAM layout stay unchanged.
Retail texture29 browser checks passed draft/no-write, bounds and stale-hash
rejection, no-op/no-history, Apply, Undo/Redo, Discard, Save/reopen and Build.
Independent package readback matched all pixels/palettes and the saved33312-byte
TIM; three indices/image bytes changed, zero palette words.24 retail-enabled
focused tests passed with no skips. This feature is included in the 405-test source checkpoint; browser
and package evidence remain separate. Gameplay appearance remains deferred.

**Renderer newline preservation fix (2026-09-30):** the plain-glyph
writer now excludes byte0x7C (`|`), which the pinned font renderer uses as a
newline even though MES emits it as a Glyph event. Source newline bytes split
editable runs and remain unchanged; form/API/text-file/Build writes reject new
pipe characters. Legacy saved projects open without rewriting their files;
invalid pipe edits have an unavailable effective value and can be cleared or
replaced. Clear/Undo and file-based null clearing retain normal history.
58 focused retail-enabled tests passed in29.566s with no skips, plus Node binding
checks and editor syntax. Retail browser rejection and legacy Inspector/Clear/
Undo passed with no page errors; legacy Build rejection created no output.
Synthetic dialogue/menu checks prove newline-byte preservation. The town01
52-actor read-only scan found no reached newline glyphs and no offered run
containing pipe; it is not wider retail preservation evidence. This fix follows
the397-test source checkpoint. No game launched; layout/gameplay remain deferred.

**Source-bound text JSON workflow (2026-09-30):** the script Inspector
exports supported dialogue/menu runs and previews external JSON before Apply.
Only each run's `text` is editable; null inherits retail. The file retains the
complete supported collection, verified MAN identity and current text-override
binding. All changes validate before one Undo entry; unrelated components stay
unchanged. Six focused text/project tests and editor/operand JavaScript checks
passed. Retail browser export/no-op/preview/immutable-field/stale-import,
two-run Apply/Undo/Redo/Save, oversized-file and closed pending-read guards
passed. Independent saved-project/package readback matched all three authored
label runs, including the prior override. Final preview screenshot and layout
bounds inspected. The 405-test source checkpoint includes this workflow; browser/package evidence remains separate.
See the [text-file guide](legaia-text-json-authoring.md). No game was launched;
menu reachability and display/selection remain deferred.

**Menu instruction-to-label navigation (2026-09-30):** decoded picker
choices now show separate retail/authored/effective glyph-run text and links to
the exact label forms. Owner, option, PCs, targets, capacity and source tokens
must match before a link is created. Duplicate or mismatched metadata is rejected.
The retail actor0001 browser exposed all30 supported label links, focused the
exact field and retained an unapplied draft. Stale source and withdrawn report
navigation were rejected; project/camera/service remained unchanged, with zero
authoring requests or page errors. Pure JavaScript checks cover multiple runs,
partition-two owners, detachment, bounds and ambiguity. Screenshot inspected.
This is separate browser/JavaScript evidence; gameplay remains deferred.

**Menu-label authoring (2026-09-30):** source-qualified plain-glyph runs
inside decoded two-, three- and four-option pickers now use the existing
Dialogue component and Apply/Clear/Discard, Undo/Redo, Save/Open and Build paths.
The Inspector identifies picker PC, option number, source capacity and encoded
choice target. Equal-span edits preserve jump entries, continuation bytes,
control/substitution tokens and record boundaries. Ordinary dialogue retains its
no-stop gate; conflicting or aliased menu spans remain unavailable. 54 focused
retail-enabled dialogue/script/resource tests passed in29.896s with no skips,
plus editor syntax and a retail browser workflow. A saved town01 actor0001
label package independently decoded to exactly the expected MAN. This is included in the 405-test source checkpoint; browser/package evidence remains separate. Menu story
reachability, glyph layout and runtime selection are unverified. See the
[menu-label guide](legaia-menu-label-authoring.md). No game was launched.

**Saved runtime node review (2026-09-30):** the Observed nodes panel can
export decoded metadata and reopen it later in Edit mode as a historical,
read-only Inspector. Positions/capture frames, uncertain fields, evidence and
unconfirmed candidate IDs are retained; raw prefixes and guard tokens are
excluded. Saved files never set Live state/correlation or change project/camera.
Serializer and synthetic browser download/reopen/filter/stale/file-read guards
passed with zero authoring requests or page errors. All17 fields from the actual
profile decoder on a synthetic prefix were accepted. See the [review guide](legaia-runtime-node-review.md).
No real runtime capture was performed; capture/gameplay acceptance remains deferred.

## Validation scope

The retail-enabled SDK discovery suite passed **421 tests in 172.966 seconds**,
exit code 0, with no skips, against unchanged committed source
`be7a5e42686119b2290643556a9827775cfb21c7`. This supersedes the 405-test
checkpoint at `cc41ded0` and includes model-selector authoring, authored component
review/revert, grouped placement commands/history and detached 3D proposal views,
along with earlier text/font/search services. Log and exact command, source,
result and hash metadata:
`local-output/sdk-20260909/sdk-regression-20260930-group-inspection.log/.json`.
Log SHA256: `4256992f5d0a3e1767a60056fbb625ce5c70b292f54373b7294743d3c7f2ef98`.
All five Node checks (font, texture usage, script operands, saved runtime review,
actor group scene coordinates) and editor/group-module syntax passed separately.
Browser workflows retain their independent pixel/render/navigation evidence;
a green suite does not establish gameplay, runtime parity or broader rendered
acceptance. Historical checkpoints below retain their dated evidence.

Recent private evidence lives under `local-output/sdk-20260909/`, including `sdk-suite-recheck-20260912.log`, `shared-scenery-multiple-check.json`, `shared-scenery-multiple-z-check.json`, `obj-equivalent-retail-20260912/report.json`, `animation-channel-copy-check.json`, `animation-effective-copy-check.json`, and `animation-copy-request-order-check.json`. These files are local evidence, not redistributable fixtures.

## Deferred gameplay

Use [the verification queue](legaia-gameplay-verification-queue.md) for saved input projects, exact artifacts and manual checks. NPC append/spawn behavior, script execution, animation playback, modified collision and visual behavior require their stated checks. Successful serialization does not establish gameplay acceptance. The user's wall-gap confirmation is bounded to that prior edit.

## Major unfinished work

- Arbitrary model topology/material replacement, general animation import and retargeting.
- Complete script/control-flow authoring, unknown records and scheduling behavior.
- Confirmed runtime actor identity and complete Unity-style live scene parity.
- Complete world-map behavior and unresolved MAPDSIP coverage.
- Remaining release/runtime acceptance, including the latest audio-lock build and deferred lifecycle/performance checks.
- Wider rendered animation acceptance beyond the reviewed Dolk2 clip, other consumers and broader scene parity.

See [feature coverage](FEATURE_MATRIX.md), [release parity](legaia-release-parity.md), [architecture](ARCHITECTURE.md), and [test plan](TEST_PLAN.md). The goal remains active; this report does not claim all offline work is exhausted.


Recent model interchange addition: source-bound complete vertex/normal JSON is
connected to model downloads, Apply shape, Undo/Redo and Save/Open. All119 town01
models round-tripped exactly. A retail normal-only model0009 probe preserved all
other TMD bytes and passed independent package-member readback. Browser checks
cover model0000 vertex upload, authored JSON download and Undo; they do not prove
runtime normal lighting. Saved probes are listed in the gameplay queue.

September 30 viewport authoring connection: enable **Wireframe overlay** and
Shift-click a projected vertex in an unposed model to open its exact object,
index and source XYZ in the vector Inspector. Selection does not apply changes.
Plain clicks and orbit drags do not select. Picking includes hidden vertices;
posed/proposed animation geometry, pending shape files and Live mode cannot
use this authoring shortcut. Retail browser checks verified the selected vector
and no submitted edits; projection checks cover center, behind-camera and
offscreen points.

Whole-object shape authoring: the vector Inspector now offers **Translate all
vertices in this object** with explicit integer XYZ offsets in source units.
It preserves normals, other objects and topology; validates every resulting
signed16 coordinate and the inspected model hash before applying one undoable
replacement. Zero offsets submit no change. Retail service checks proved all
vertices, preservation and exact Undo/Redo; browser checks proved Apply/readback/
Undo and disabled zero/overflow offsets. Gameplay remains deferred.

Script workspace addition: **Find a decoded instruction path** accepts a selected
start and destination and shows one shortest encoded-successor route, with
condition labels and clickable instruction steps. Cycles terminate; unknown
targets are reported as boundaries. No-path results do not establish gameplay
unreachability. Queries do not execute scripts or alter project state. Synthetic
browser checks cover branching, cycles, same-node queries and undecoded targets;
a retail actor-script path was checked edge-by-edge against its decoded report.
General control-flow authoring and live execution remain incomplete.

Script operand authoring now includes the one-byte **NPC_RUN encoded move
selector** (0–255), with retail/authored/effective values, Apply/Clear/Discard,
Undo/Redo, Save/Open and existing audited Build composition. X/Z and depth stay
unchanged when only the selector is edited. Selector behavior is unresolved;
no animation or speed meaning is assigned. Seven focused tests passed (four
separate retail streaming tests skipped without their environment input). A
saved town01 probe changed selector 13 to 14, and independent package ZIP
readback found exactly one changed MAN byte. Browser Apply/Undo passed.

EXEC_MOVE operand authoring: fixed-width encoded move selectors now share the
ScriptMovement workflow with NPC_RUN. EXEC_MOVE exposes only its move-selector
byte, with no invented X/Z or scene marker. Source-verified field offsets drive
Build audits and appended-record rebasing. Eight focused tests passed, including
all256 selector bytes with ordinary/extended headers and rejection of X/Z edits.
Retail actor0003 PC0x12 selector9->10 passed Save/Open, Undo/Redo, browser
Apply11/Undo10 and independent ZIP decode with exactly MAN byte4816 changed.
This addition follows the352-test checkpoint and has focused checks; runtime
move-table identity and behavior remain unverified.

Indexed scene texture palette authoring: **Edit selected palette** exposes
retail/effective words, RGB5/STP bit interpretation, explicit Apply, retail
reset and draft Discard. Entry changes lock while a draft is pending. Edits
are bound to the inspected effective TIM hash and use ordinary texture
replacement Undo/Redo, Save/Open and Build. Four focused synthetic/build tests
passed (one retail test skipped without its environment input); a separate
retail workflow and browser Apply/readback/Undo passed. Actual ZIP member
readback proved the saved entry change affected only TIM byte22. Other palette
entries, image data and headers are preserved. Shared/conditional banks and
runtime palette/blend behavior remain outside the accepted authoring scope.

Indexed texture pixel authoring: Shift-click the bitmap to inspect a pixel
and edit its encoded palette index. Retail/effective values and the inspected
palette colour word remain explicit. Apply/reset/Discard uses source-hash-bound
texture replacement history, persistence and Build. Four-bpp edits preserve the
other nibble; eight-bpp edits preserve neighboring pixels. Five focused tests
passed (one environment-gated retail test skipped), with exhaustive index
values at row/packed-byte boundaries. Separate retail checks passed authored
palette preservation, stale rejection, Undo/Redo, Save/Open, Build and exact
ZIP member readback. Browser Shift-click, range rejection, Discard, Apply and
Undo passed after correcting fractional canvas-edge rounding. Runtime residency
and visible/material/palette behavior remain deferred.

Indexed texture interchange: retail/effective JSON downloads and source-bound
JSON replacement now expose complete ordered CLUT words and pixel-index rows.
Existing TIM headers, bit depth, dimensions and array counts remain fixed;
duplicate keys, stale source hashes, unsupported formats and invalid values
reject before replacement. Effective JSON retains the retail source hash.
All96 indexed town01 scene textures round-tripped exactly; seven focused tests
passed (one environment-gated retail test skipped). Separate retail/browser
checks passed combined palette/pixel import, Undo/Redo, Save/Open, download/
upload and actual ZIP member readback. Existing TIM upload remains available;
file reads now reject changed texture/file contexts before submitting. No
quantization, resizing, shared-bank authoring or runtime acceptance is claimed.

Texture-file proposal preview: selected TIM/JSON files render without applying,
with palette-word, pixel-index and image-byte counts against both retail and
current authored data. Details are capped at256 changes while counts remain
complete. Return retains the file for explicit Apply. Source/layout validation
and changed-context guards precede display; Build capacity and runtime appearance
remain separate gates. Nine focused tests passed with one environment-gated
retail test skipped. Separate retail service and browser checks proved preview
leaves state/history/authored files unchanged, and Apply/Undo restores the exact
previous texture. Screenshot inspected; game not launched.

Texture Build reports now retain bounded palette-word/pixel-index/image-byte
audits with complete change counts. Changed pixel links open the effective
texture pixel editor only when its replacement hash matches the report;
older reports without payload details remain readable. Synthetic report tests
and a retail package readback verified the combined palette/pixel diagnostic
at TIM bytes22/544. This reports emitted payload edits, not runtime residency.
Browser checks passed report details, unchanged project state during pixel
navigation, and stale replacement hash rejection after a later edit.

Indexed texture rectangle fill: the editor previews an unapplied rectangle
using an existing encoded palette index, validates complete image bounds and
uses an inspected effective TIM hash. Apply creates one ordinary texture
replacement command; no-op fills create no history entry. Four-bit packed
neighbors, outside pixels and all palette words are preserved. Nine focused
tests passed with one retail environment-gated test skipped. Separate retail
checks passed stale rejection, Undo/Redo, Save/Open and actual ZIP readback;
browser draft/no-command, edge rejection, Discard, Apply and Undo passed.
This edits indices for every palette using the image; resizing, quantization,
shared-bank authoring and runtime appearance remain outside verified scope.

Project-wide flag references: imported scenes are freshly verified and scanned
without changing authored state or active selection. Scene/script-qualified
operand groups remain separate even when encoded bank/index values match;
partial/unavailable coverage stays explicit. Browser search includes scene
names, and source-instruction links navigate to the matching scene/script.
A three-scene town01/Dolk2/map01 retail probe found2142 references in899groups
across230scripts (128partial). Service state stayed unchanged. Browser coverage,
search and cross-scene instruction navigation passed with unchanged command
history; scene navigation uses the existing saved-view dirty tracking. Discovery
is bounded to64imported scenes,32768groups and262144references. Current runtime
values, shared variable identity and story names remain unresolved.

Scene texture dependency inspection: **Inspect scene texture uses** derives
static image/CLUT source contributors from the current verified scene preview,
keeps partial candidates separate from address matches, reports unresolved
materials/unavailable instances, and offers model/instance/material search plus
viewport Locate actions. Source keys guard navigation; inspection adds no
project edits/history. Focused Node checks cover shared/draft instances, CLUT
contributors, unresolved candidates, untextured exclusion, detached results and
bounds. Retail browser checks passed actor0005 navigation for texture25, and
texture29 fanout of31material matches/19geometries/58instances, scenery Locate,
empty search and stale-source rejection. Screenshot inspected. This addition
follows the365-test Python checkpoint; runtime residency/conditional visibility
and cross-scene dependencies remain unverified.

Model object quarter-turn authoring: rotate existing object vertices and normals
around their source-local origin by−90°, +90° or180° on source X/Y/Z. Exact
signed permutations preserve vector lengths, padding, topology and other objects;
signed16 overflow and stale effective hashes reject atomically. The vector draft
must be applied/discarded first. Three focused tests passed, including inverse/
four-turn restoration, all axes and invalid ranges. Separate multipart retail
checks passed object1 vertex/normal transforms, other-object preservation, stale
rejection, Undo/Redo, Save/Open and independent decompression of the actual ZIP
member. Browser draft guard, Discard, Apply, readback and exact Undo passed.
This addition follows the365-test checkpoint; gameplay shape/lighting/animation
compatibility remains deferred. Browser lighting does not use normal vectors.


Flag operand authoring foundation (2026-09-30): source-qualified ScriptFlags
commands preserve separate retail/authored/effective values, support Undo/Redo,
clear offline and Save/Open, and validate reached L/G/C flag SET/CLEAR/TEST
operands against immutable source records. Upper operand bits and dispatch/layout
remain unchanged; local width and context side-effect cases are unavailable.
Fourteen focused tests passed. Retail town01 actor0002 CFLAG_SET bit2-to3 changed
only decoded MAN byte4772; project history and reopening passed. Private project:
local-output/sdk-20260909/flag-authoring-project-20260930. Editor Apply and Build
composition remain pending. Build explicitly rejects ScriptFlags instead of
silently dropping them. This is foundation work, not a completed authoring
workflow or gameplay acceptance; the365-test checkpoint predates it.


Flag output integration (2026-09-30): ordinary Build now emits source-qualified
flag operands with independent audit checks for source/hash/owner/offset, upper
bits, requested bit, overlaps and unaudited changes. Build reports distinguish
flag.bit from raw operand bytes and name the source instruction. Experimental
compressed and raw-streaming exports rebase existing owners after NPC append;
flag changes participate in scene export audits. Thirteen selected tests passed
with the private retail disc and no skips (27.267s); sixteen focused project,
serializer and merge tests also passed. Retail ZIP readback changed only MAN
byte4772. Compressed town01 append reopened bit3 at rebased byte4775; raw dolk2
append composed bit24-to25 with dialogue and transition edits. Private package:
local-output/sdk-20260909/flag-authoring-project-20260930/Builds/flag-output-verified,
SHA256 adeeb217b679908845e4e9e260e31b3d22cccceb3fc0f63ab33fd502459c99bf.
Earlier foundation notes describing Build rejection are superseded by this
integration. Editor Apply remains pending; story meaning, execution, runtime
values and gameplay acceptance remain unverified. No game launched or package
installed. The365-test checkpoint predates this addition.


Flag operand Inspector (2026-09-30): supported source-qualified L/G/C flag
SET/CLEAR/TEST operands now expose retail, authored and effective bit indices
through script inspection APIs and editor forms. Apply/Clear use ordinary project
commands; Discard retains authored state. Numeric bounds and special context
SET8/CLEAR10 checks disable Apply; unapplied drafts block project history/save
controls. Unsupported scripts retain read-only reports and clearable unresolved
overrides. Failed refresh removes authoring controls. Flag Build report navigation
opens the source instruction. Six focused retail HTTP/project/merge tests passed;
HTTP checks include unexpected fields, invalid values and special context bits.
Browser checks passed layers, special-bit guard, pending draft guard, Discard,
Apply, Undo, Clear and restoration with no page errors; screenshot inspected.
Private evidence: flag-authoring-project-20260930/flag-browser-check.json and
flag-editor.png under local-output/sdk-20260909. Earlier pending-Apply notes are
superseded. Supported operand editing is connected through project persistence
and output; wider flag/control-flow authoring and gameplay acceptance remain
incomplete. No game launched. Temporary browser/server stopped.


Authored flag reference layers (2026-09-30): scene/project flag browsers now show
retail, authored and effective operands for source-qualified flag edits. Groups
keep their retail identity/index; matching effective indices never merge scripts,
scenes or unresolved contexts. Search includes effective operands. Authored
annotations pass the source serializer first; missing/stale source or unmatched
catalog identities reject, and project-wide discovery rejects state changes
during collection. No runtime values or execution are inferred. Twelve focused
flag/reference/project tests passed. Retail scene/project discovery retained
1249references with one authored operand (town01 actor0002 CFLAG_SET2-to3).
Browser layer display, retail grouping and exact instruction navigation passed
without page errors; screenshot inspected. Private evidence:
local-output/sdk-20260909/flag-authoring-project-20260930/flag-reference-browser-check.json
and flag-reference-layers.png. No edits/history were created by discovery;
temporary browser/server stopped. Gameplay remains deferred. The365-test
checkpoint predates this work.


In progress — script wait authoring (2026-09-30): WAIT_FRAMES inspection now
exposes its u16 target as duration_ticks, host_frame_delta units, signed16
accumulator width and explicitly unknown seconds/execution. Source-qualified
wait serialization changes only the two-byte target and preserves dispatch,
control layout and opaque bytes; source owners rebase after actor append.
Authored targets are restricted to0..32767 because the pinned reference uses a
signed16 saturating accumulator; larger retail targets remain unavailable.
Thirty-eight retail-enabled wait/inspection/catalog tests passed in2.226s.
Retail town01 has four eligible actor waits; actor0044 PC0x019F16-to17 changed
only decoded MAN byte24483. Dolk2 has no eligible actor waits under these source
coverage rules. Private evidence: local-output/sdk-20260909/wait-authoring-20260930/town01-wait-check.json.
Project commands, Inspector Apply and output composition remain pending; this is
serializer groundwork, not a finished editor workflow or gameplay acceptance.
Reference checkout HEAD has advanced to574ee5f603ed3ca9bd95c796711e595d9c2ad8a8;
WAIT handler evidence was read directly with git show from the unchanged SDK pin
d6e64c68ede25813d35db20980da82a1a025549b, step.rs opcode0x4A.
No reference checkout mutation or game launch occurred. The365-test checkpoint
predates this addition.


Wait project/output integration (2026-09-30): ScriptWaits commands now preserve
retail/authored/effective ticks, ordinary Undo/Redo, Clear, authored summaries
and Save/Open. Ordinary Build independently checks exact two-byte spans, requested
values, source identity and overlap/unaudited bytes. Reports expose wait.duration_ticks
and source instruction IDs. Experimental compressed/raw-streaming exporters
compose/rebase waits and include them in scene audits; new wait coverage in the
raw-streaming route has not yet received a retail wait probe. Fifteen selected
retail-enabled tests passed in27.113s without skips. A focused merge check also
passed after adding explicit high-byte and second-byte overlap cases. Retail
town01 actor0044 wait16-to17 composed with actor0002 flag2-to3; saved project,
Undo/Redo, package ZIP/decompression and appended archive readbacks passed.
The two changed decoded MAN offsets were4772 and24483; append rebased the wait
to24486. Private project: local-output/sdk-20260909/wait-authoring-project-20260930.
Package under Builds/89f66b995f838276 has SHA256
148ab35c0b9146cab17359b9a870ab054c95aa98c415a7b26be199992da50971.
Earlier pending project/output notes are superseded. Inspector Apply is next;
seconds, execution, actual timing behavior and gameplay acceptance remain
unverified. No game launched or package installed. The365-test checkpoint
predates this work.


Wait target Inspector (2026-09-30): source-qualified WAIT_FRAMES forms now show
retail, authored and effective host ticks with Apply, Clear and Discard. Targets
remain0..32767; seconds and actual timing/execution are unresolved. Ordinary
script Undo/Redo and Save obey pending draft guards. Actor, partition-two and
trigger script routes expose authoring metadata without suppressing read-only
inspection when authoring is unavailable. HTTP commands reject extra fields,
invalid tick values and malformed identities. Build report links can open the
source wait instruction. Six targeted retail-enabled HTTP/project/merge/serializer
tests passed in7.768s. Browser layer/bounds/pending-draft/Discard/Apply/Clear/Undo
checks passed and restored the saved17-tick diagnostic; zero page errors and
screenshot inspected. Initial copied browser assertion had an encoding mismatch;
corrected test text, no application change required. Evidence retained under
local-output/sdk-20260909/wait-authoring-project-20260930/wait-browser-check.json
and wait-editor.png. Earlier pending-Apply notes are superseded. Supported wait
editing is connected through project and output; wider script/control-flow and
runtime timing acceptance remain incomplete. Temporary browser/server stopped;
no game launched or package installed. The365-test checkpoint predates this work.


Instruction operand navigation (2026-09-30): decoded instruction rows now display
retail/authored/effective values for verified movement, flag and wait targets,
with Open operand editor links that focus the matching form. Encoded source
operands and graph successors remain retail evidence. A reusable client metadata
adapter requires exact PC/mnemonic/context/retail values and consistent effective
layers; mismatches, duplicate PCs and oversized metadata withdraw links. It does
not simulate execution or mutate reports. Focused Node checks passed flags,
coordinate/selector movement, waits, bounds, ambiguity, context/value rejection
and source detachment. Retail browser flag/wait rows and exact input focus passed
with no project/history changes or page errors; screenshots inspected. Evidence:
local-output/sdk-20260909/wait-authoring-project-20260930/instruction-operands-browser-check.json
and instruction-flag-layers.png/instruction-wait-layers.png. Temporary browser
and server stopped; no game launch. This JavaScript addition follows the383-test
Python checkpoint and retains separate browser validation.


Model object uniform scaling (2026-09-30): Scale whole object in the vector
Inspector edits source-local vertices by an integer percent1..1000, with positive
uniform scaling, nearest-integer rounding and halves away from zero. Normals,
vector padding, topology/materials and other objects remain unchanged. Signed16
overflow, stale inspected hashes, invalid percentages/objects and pending vector
drafts reject before applying.100% is a no-op without history. Ordinary model
replacement supplies Undo/Redo, Save/Open and Build. Five focused scale/rotation/
JSON tests passed. Retail model0009 object1 at150% composed with its existing
rotation/normal override; normal/other-object preservation, history, reopening
and actual ZIP carrier decompression matched the replacement. Browser invalid/
draft guards, Discard,125% Apply, readback and exact Undo passed, no page errors;
screenshot inspected. Initial readback harness selected a scene-specific carrier;
corrected to the recorded shared model carrier, without rebuilding/replacing it.
Private project: local-output/sdk-20260909/model-scale-project-20260930; package
under Builds/e7728cba624de600 has SHA256
9d16d794517133d474921f7e001f9dd1929cc43f51df2ff8c33aca89f09aa3cb.
No game or package installation. Gameplay shape/animation/collision compatibility
remains deferred. The383-test checkpoint predates this addition.


Object-transform previews (2026-09-30): implemented before Apply in the model
vector Inspector for translation, rotation and scale. Source-bound proposed/current
geometry comparison, shared framing and draft/stale-response guards passed focused
model and retail browser checks without history or authored-file changes. Gameplay
acceptance remains deferred; the383-test checkpoint predates this feature.


Scene shape proposal inspection (2026-09-30): implemented for supported renderable
instances using their verified existing pose and scene placement. One-instance
isolation, Return to vector inputs and exact Restore passed focused and retail
browser checks without authored changes. Gameplay acceptance remains deferred;
383-test checkpoint predates this addition.


Model replacement file scene inspection (2026-09-30): TMD/OBJ/JSON proposals
can be inspected before Apply on a verified instance and pose, with exact Restore
and Return retaining the selected file. Retail browser/file-size/hash/state checks
passed without authored changes. Gameplay acceptance remains deferred;383-test
checkpoint predates this addition.


Shared model proposal impact (2026-09-30): all supported scene instances can be
previewed before Apply for transforms or replacement files, with distinct source
poses, preserved placements and explicit unavailable counts. Retail model0074
all11 placements, Restore/Return and unchanged state passed. Focused multi-pose
and browser checks passed; gameplay acceptance remains deferred.


Texture proposal scene inspection (2026-09-30): TIM/JSON proposals can be previewed
through the static image/CLUT material decoder before Apply, retaining geometry
and placement. Retail texture29 changed31 materials/19 geometries/58 instances;
Return/Restore, late-response withdrawal, unchanged project/authored-file hashes
and TIM readback passed.23 retail-enabled focused tests passed. Runtime texture
residency/gameplay appearance remain unverified;383-test checkpoint predates feature.

## External animation authoring — 2026-10-02

**Source-bound GLB animation authoring (2026-10-02):** An imported actor's
current effective rigid clip exports with a separate binding JSON. External GLB
translation/rotation edits receive an exact source-axis and quantization review,
proposed animation inspection and revalidated Apply through normal animation
commands. Unchanged axes retain their existing ownership; other shared-clip
contributors are not adopted. Stale exports, ownership-only changes, conflicts
and unsupported layouts reject. Undo/Redo, Save/Open and normal Build retain the
existing record and capacity checks. Counts, skinning, general retargeting and
retail timing/runtime acceptance remain unfinished. See
[animation GLB workflow](legaia-animation-glb.md).
