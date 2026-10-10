# World Source Instance Isolation and Group Framing

In **World ground**, choose **World viewport instance scope**:

- **All source instances** displays the qualified loaded scene.
- **Selected instance only** isolates the hierarchy/viewport selection.
- **Selected asset instances** displays every qualified instance sharing the selected geometry asset, including the selected instance.

**Frame visible instances** computes the camera target and distance from the transformed bounds of the visible instances in the current Retail or Current layer. It preserves orbit orientation. An empty display leaves the camera unchanged and explains that there are no visible instances to frame. **Frame selected** retains its existing single-instance behavior; **Frame ground** retains its ground framing behavior.

**Inspect all source asset instances** is available in model Details in **Project resources**, and in **World ground** → **Browse world resources**. It re-reads the native kingdom and verifies the model's exact source record, geometry counts and complete instance membership before switching to Retail, retaining the first canonical hierarchy selection, isolating the complete asset group and framing it. Ground is also a geometry asset with one source instance.

The selected source entity remains the Inspector target. Hierarchy selection changes update isolation; viewport picking uses the same hidden-instance set as rendering. Hierarchy search controls its list without trimming the asset group. Turning off **Source model placements** hides source model instances; it can make an isolated model group empty. Ground stays governed by its own selected/group scope.

These are local display choices, not authored visibility or spawning changes. Display isolation does not alter export scope or native scene data. Existing scene/ground/selected export choices retain their separate meanings. Reloading or withdrawing source inspection resets the display scope to All; switching Retail/Current retains it and frames the displayed layer when requested. Runtime visibility and resting positions remain unknown.

## Offline Evidence — 2026-10-09

The pure display helper validates at most 129 geometry assets and 513 source entities, unique identities, qualified asset ownership and source roles. It returns detached visible IDs and hidden sets without modifying scene objects. One focused Node suite verifies single/shared-asset/ground scopes, model visibility, immutability and nine invalid scope/ownership variants. Four JavaScript syntax checks and the server AST check pass.

Actual browser workflows instrument the real SceneRenderer draw list and transformed bounds, rather than counting only helper output. The three kingdoms qualify model groups containing 126, 138 and 109 source instances respectively. Exact memberships, single-instance isolation and hierarchy/Inspector synchronization pass. Nonmatching hierarchy search preserves full group membership. Empty visibility leaves the camera unchanged. Camera target and distance match the visible transformed bounds exactly. Retail/Current switches retain group membership and scope. Both resource-browser handoffs pass, along with existing resource metadata download, TIM consumer/Back navigation and field/active-scope isolation.

Desktop/400px layouts and group/single-instance viewport output were inspected; no page errors occurred. Private evidence is retained under `local-output/sdk-20260909/worldmap-view-scope-20261009/`. All fixture files, imports, authored inputs, field scene, selection and history remain unchanged. No Apply, Build, game or runtime attachment occurred. This is source-scene inspection; manual gameplay verification remains deferred and the full SDK goal remains active.
