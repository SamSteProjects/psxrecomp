# Coordinated scene animation preview

The scene animation timeline previews every eligible actor's verified initial clip together in the existing scene viewport. It is a transient editor view. It does not author a game timeline, execute scripts, observe current runtime clips or establish retail playback timing.

## Workflow

Import a verified field scene and choose Edit mode. Choose the Authored or Retail scene representation, then start scene animation preview. Preparation reports animated instances, shared tracks and actors whose animation remains static or unavailable. It does not present partial coverage as a complete live scene.

Use Play/Pause or the integer tick control to inspect poses. Preview rate is an explicit display setting from 1 to 30 frames per second, initially 10. Tracks initially sample `preview_tick % frame_count`; repeating clips is a preview convention. Per-track preview modes and source-frame phase offsets can change that sampling without changing source data. The shared sample index continues past the longest clip. The scrub range expands to retain elapsed preview samples. Frames are discrete source samples, with no invented interpolation, script scheduling, movement or transitions.

Stop + Restore returns the viewport to its canonical scene. Preview does not append Undo history, change saved authoring, produce Build changes or persist retail animation payloads. Existing authored transforms, model materials, face/UV/RGB content and texture associations remain attached to the same scene instances. A project, scene, representation, mode or source change withdraws the preview; it never resumes automatically against changed evidence. Persistent editing and other transient pose tools are blocked while this preview owns the viewport.

The Authored representation uses the effective appearance, initial animation assignment, shared channel contributions, model content and textures. Retail uses a detached projection with those authoring components cleared. It does not clear edits from the real project. To compare a new authored edit, restore the scene, make the ordinary reviewed edit and prepare a fresh preview.

## Eligible source paths

| Path | Source qualification | Limits |
| --- | --- | --- |
| Local scene actor | Verified MAN placement animation byte 1–255 selects scene ANM record `byte - 1`; actor and model locators equal the fresh import | Later scripts may replace the model, clip, visibility, position or facing |
| Authored appearance | Existing verified donor supplies an initial model/clip pair in the same scene | No arbitrary retargeting or new model/channel mappings |
| Authored initial clip | `ActorAnimation` retains an exact imported witness and source-record hash for the inherited model | Only observed compatible assignments; channel edits retain their original shared clip ownership |
| Party models | Three pinned global field model banks, using the existing idle reference clip | Equipment objects 10 and 11 are excluded; no live equipment or idle/walk switching |
| Other global models | Pinned savepoint and auxiliary model associations, using their existing loop reference clips | Activation, scale, visibility and auxiliary gameplay role remain unresolved |
| NPC draft | Its imported retail donor's model/initial clip assignment | Donor appearance/clip overrides are not copied into the draft; shared asset/channel edits can still affect it |

Zero-animation actors and unsupported, missing or malformed bindings are not given fabricated clips. They retain explicit static/unavailable reasons. Environment and terrain are outside this actor timeline. Source records that track only a leading model-object prefix preserve that exact mapping and exclude untracked trailing objects.

Actor meshes remain in retail actor-local Y-down coordinates. Existing scene matrices provide the editor's Y reflection, placement and optional source-surface height preview. The timeline replaces posed local vertices only; it must not apply object transforms twice, rotate an actor to an assumed heading or manufacture runtime elevation. Objects are independent rigid channels, not an inferred anatomical skeleton.

## Shared tracks and preservation

One track serves each existing scene geometry key, preserving each instance's exact source actor, asset and transform. Track clip identity is a stable `animation://…` source ID; labels such as `placement`, `idle` and `loop` do not distinguish source records by themselves.

All imported actors' `AnimationChannels` contributions are composed through the same shared-bank writer used by Build. Equal writes to one shared axis agree; contradictory writes are rejected. Appearance or initial-clip changes do not retarget those contributions. An actor selecting an edited record receives its effective composed pose, including contributions made by other actors sharing that record.

Full-clip model composition uses the effective TMD through every frame. Object ranges, triangles, UV/color data, material mapping and frame zero must agree with the canonical scene. A material edit can rebuild its derived material table, so texture associations come from the freshly qualified effective source rather than an old material index. Qualified raw source normals can be rotated through explicit channel evidence as described below. The timeline does not infer normals from geometry or reconstruct unsupported runtime rendering effects.

Preparation is bounded to 128 tracks, 512 instances, 100,000 vertices per frame, one million total frame vertices and 64 MiB of finite JSON. The transport allows at most 4,096 frames per clip; the current packed source decoder is stricter at 512 frames and 64 rigid channels. Budget exclusion reports a whole track as unavailable. Frames are never silently truncated. Coverage and decode failures remain visible.

## Independent offline evidence

Private metadata and the reusable read-only probe are in `local-output/sdk-20260909/scene-animation-20261002/research/`. The verified disc SHA-256 is `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`. The Andrew reference remains pinned at `d6e64c68ede25813d35db20980da82a1a025549b`.

The source probe measured imported actors, excluding environment/terrain and authored drafts:

| Scene | Scene-header actors | Party idle | Global loop | Static/unavailable animation | Shared model/clip tracks | Total frame vertices |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Dolk2 | 56 | 4 | 9 | 3 | 15 | 46,015 |
| Town01 | 39 | 2 | 1 | 10 | 22 | 67,947 |

Every eligible canonical scene frame-zero geometry matches the independently loaded full clip exactly. Local clips' first and last full-preview frames equal the single-frame loader. Direct reads of source TMD vertex tables and packed channel bytes, composed with an independent full `Rz × Ry × Rx` matrix, agree with sampled Dolk2 actor 0001 and Town01 actor 0049 poses within `1.42 × 10^-14` source units. This is analytic source-pose agreement, not bit-exact GTE rounding.

A private `translation.x + 1` contribution also agrees between composed full-clip and single-pose paths. Town01 actor 0049 and actor 0013 can make the same shared-axis contribution without changing the composed result; a contradictory contribution is rejected. Detached project imports, authored components, selection, saved digest, history and resource caches remain unchanged across reads. No user project, disc or reference source is written, and no game is launched.

Pinned evidence paths include `asset/{man_section,player_anm}.rs`, `tmd/src/mesh/{mod,vram_posed}.rs`, `web-viewer/src/field_npc.rs` and `engine-core/src/field_anim.rs`; exact blob hashes are recorded in `source-pose-proof.json`. Scene records carry no playback-rate byte. The separately pinned party reference cadence does not establish cadence for arbitrary scene or auxiliary records.

These source checks support the offline loader and its coverage limits. Browser lifecycle, authored/retail comparison and Restore acceptance are verified centrally during feature integration. Runtime clip selection, timing, story visibility, equipment, palette animation and gameplay appearance remain deferred.

## Source normal channel diagnostic (2026-10-03)

Start **Preview scene animations**, then enable **Source normal directions** inside Scene tools. The option is available only when at least one track has qualified source vectors and all frame channels. It colors those animated tracks while other actors, environment and terrain keep surface shading. Unlit, zero or unavailable corners within a qualified track are neutral gray. Scrub and Play retain the choice. Unchecking restores the surface pixels at the same sample; **Stop and Restore** clears the choice and restores the exact canonical scene. This display never authors source data or runtime state.

Canonical posed geometry keeps raw vectors in a separate `preview.normal_source` record. They remain absent from its `triangle_normals` render stream, so a renderer cannot treat them as posed directions. Optional `track.normal_pose` contains qualified unposed source geometry/vectors plus complete actor-local rigid channels. The existing `legaia.scene-animation.v1` report still accepts tracks without this optional field. Source identity, geometry keys, object ownership, triangle layout, signed16 vectors, channel bounds and coordinate systems must agree. Python preparation also replays each channel and requires exact equality with the already-qualified vertex sample. Client decoding and the parent renderer binding separately validate the retained source.

Sampling uses the same analytic Rz × Ry × Rx helper as the individual model viewer. Translation is excluded from directions, and the existing instance inverse transpose supplies display orientation and one Y reflection. Normal and vertex buffers update in place; mode toggles do not upload them. The diagnostic mask contains only qualified animation geometry keys. Ordinary vertex-only updates withdraw normal qualification. Source clips without complete channel evidence remain valid vertex playback tracks with no diagnostic.

The existing vertex and64MiB JSON limits include the optional channel payload. If optional channels would exceed the JSON budget, they are withdrawn before considering the unchanged vertex track, preserving existing playback when it still fits. A separate limit of three million frame corners bounds complete normal-channel validation across admitted tracks. Exceeding that normal limit omits the complete track's diagnostic rather than clipping frames or inventing vectors. Derived directions are calculated only for the current sample; arrays for every posed frame are not retained.

Nineteen focused Python cases pass with no skips: scene animation source/channel/sample qualification and existing scene/transform cache behavior. Three Node suites cover optional legacy/new reports, rotation/order, invalid ownership and vectors, normal budget rejection, immutable channel evidence, mode reset, renderer updates and static source-normal guards. Six actual browser checks use Town01's42 animated actors in22 qualified tracks. They prove mode/default framebuffer restoration without uploads, exact tick7 posed normals and vertices, Play without reallocation,540px reachability, exact Restore and byte-identical project files/history. Screenshots were inspected, and owned browser/server handles are terminal. Private evidence: `local-output/sdk-20260909/scene-normal-pose-20261003/parent/`.

Retail lighting, fixed-point GTE rounding, native animation timing and gameplay appearance remain unverified. This work uses stored source normal references and qualified SDK rigid poses; it does not establish those runtime behaviors.

The22 retail Town01 tracks contain zero lit source-normal triangles. Their unlit faces correctly display neutral gray, while the focused synthetic signed16 directions establish rotation behavior. The qualified report covers344199 frame corners; this is source-channel evidence and no normals are synthesized for the retail actors.

## Per-Track Preview Modes and Phase Offsets — 2026-10-09

Start scene animation preview and expand **Animation sources and unavailable instances** in Scene tools. Each qualified track offers **Preview mode** and a source-frame **Phase offset** from zero through its last frame. Changing either pauses playback and resamples the current tick; use Play explicitly to resume.

| Mode | Selected source frame |
| --- | --- |
| Loop | `(tick + offset) % frame_count` |
| Hold at last frame | `min(tick + offset, frame_count - 1)` |
| Ping-pong | Reflect `(tick + offset)` over period `2 * (frame_count - 1)`; a one-frame clip remains at zero |
| Freeze at offset | Always the selected offset frame |

The implementation reduces the tick before addition to preserve exact modular sampling through `Number.MAX_SAFE_INTEGER`. Offsets identify discrete source frames; no interpolation or retail time is inferred. Vertices and qualified normal directions sample the same frame. All instances sharing a geometry track receive its selected pose while retaining their existing transforms and materials.

Settings are temporary and are not stored in the project, Undo history or Build inputs. Stop resets them to Loop/zero and restores the canonical scene. A fresh start uses defaults. Source changes withdraw coverage; stale or busy controls cannot update the viewport. Invalid offsets restore the prior valid settings without sampling.

Nine focused Python tests, the Node scene-animation suite and two JS syntax checks passed. An independent BigInt oracle covered all modes, one-frame clips, boundary offsets and the maximum safe tick. Mounted controls passed pause, invalid input, busy/source withdrawal, reset and restart checks. In a private Dolk2 editor, all four modes matched literal source frames and every actual rendered vertex-buffer entry for 30- and 10-frame tracks, including a shared two-instance track. Desktop and 400-pixel screenshots were inspected. Browser errors, overflow and authoring/Build/Run requests were absent; complete project/history/imports stayed unchanged and Save/Open remained exact.

Evidence: `local-output/sdk-20260909/scene-track-playback-20261009/`. The initial collapsed-drawer harness failure screenshot is retained alongside the passing evidence. These checks establish editor sampling and lifecycle behavior only. Native animation scheduling and gameplay appearance remain unverified; no game or runtime attachment occurred.

## Track Instance Navigation — 2026-10-09

Expand animation source coverage during scene preview. Every track lists its exact stable scene instance IDs. Choose **Frame visible instances** to fit all visible members using the current sampled mesh bounds and existing instance transforms. Camera projection, yaw and pitch are preserved. Hidden members remain hidden and do not contribute to the fit; if no visible bounds exist, the camera stays unchanged and an explicit error explains how to restore visibility.

Choose an instance and press **Inspect instance** to select its actor in the existing hierarchy and Inspector. The hierarchy search is cleared and the selected entity is revealed. Imported actors use the ordinary selection service; authored NPC draft instances use their existing Inspector selection path. Retail comparison retains its separate viewport representation and authored Inspector values. The list derives from the qualified animation instance bindings, rather than guessing membership from model identity or animation name.

Either action pauses playback while retaining the sampled pose and exclusive transient preview ownership. Resume explicitly with Play. Navigation does not author a transform, clip, timeline or game state. Busy or stale scenes, foreign members and stopped previews refuse actions. A pending selection disables navigation and sampling controls; Stop/source withdrawal invalidates its continuation. A late old continuation cannot lock or unlock a newer session. Parent callbacks recheck entity, geometry, asset and source-actor bindings against the loaded scene.

The scene-animation, camera and placement-selection Node suites, nine existing Python tests and three JS syntax checks passed. Mounted controls verified source membership, shared-instance ordering, pause, invalid members, busy/stale refusal, in-flight Stop/restart and absent callback refusal. Actual private Authored Dolk2 and Retail Town01 workflows selected actors 0030 and 0035 from their exact shared tracks. An independent screen-projection check put all 16 rendered mesh corners inside ten-percent viewport padding at desktop and 400-pixel sizes. Hiding the selected actor reduced the fit to the other eight corners; hiding the actor layer preserved the camera on refusal. Four screenshots were inspected. Browser errors, horizontal overflow and authoring/Build/Run requests were absent; complete project documents, history and imports stayed unchanged and Save/Open was exact.

Evidence: `local-output/sdk-20260909/scene-track-navigation-20261009/`. Gameplay position, story visibility, runtime clip selection and timing remain unverified. No game or runtime attachment occurred; this workflow connects source-qualified preview coverage to existing editor inspection.

## Source-Bound Preview Recipes — 2026-10-09

Prepare a fresh source-qualified scene animation preview, set the display tick/rate and shared-track sampling modes/offsets, and choose **Save preview recipe**. The JSON file records those temporary controls plus exact scene/project/import/representation and track model/clip/geometry/instance identities. It excludes vertices, animation frames, textures and native payloads. The format is `legaia.scene-animation-preview-recipe.v1`; at most one MiB and 128 complete tracks are accepted. Absolute ticks remain safe nonnegative integers, fps is 1–30, modes are the existing four preview modes and each offset must lie within its track's source frame count.

Use **Scene animation preview recipe JSON** against a matching prepared preview to replay. All source and complete coverage bindings, schema fields, duplicate/missing tracks and settings are checked before any rendered pose or setting changes. Canonical object-field equality accepts equivalent JSON key ordering. Track array order is irrelevant to identity; instance/coverage lists retain their canonical complete ordering. Changed authored inputs, imports, scene, representation, clip/model binding, geometry counts or members refuse. Invalid files preserve the current pose and sampling settings while pausing playback. Other preview operations are disabled while a file read is pending; Stop and source withdrawal invalidate its completion. There is no automatic playback after save/load and no implicit project authoring, Undo entry or Build input change.

Recipes restore the temporary tick, fps, modes and phase offsets only. Camera, selection, visibility and normal-direction display remain separate editor settings. The same existing source-frame sampler supplies vertices and qualified normals. Source/renderer failure continues to restore the canonical scene through the existing ownership path. Restore before persistent editing, then prepare and save a new recipe against the changed source if needed.

Nine retail-enabled focused Python tests, four Node suites and two changed-module syntax checks passed. Codec and mounted controller tests cover safe-integer tick extremes, all four modes and frame/rate bounds, exact source/schema/coverage identity, detached metadata, reordered JSON keys, source/track tampering, oversized file refusal before reading, atomic invalid-file handling, paused save/load and late Stop/source-change refusal. Existing animation sampling/lifecycle and rigid/source normal suites passed.

Actual Authored Dolk2 and Retail Town01 editor checks saved real downloads, changed the preview, loaded the downloaded recipes and retained paused controls. An independent BigInt frame sampler matched every rendered Float32 vertex-buffer coordinate: 35,199 coordinates across 15 Dolk2 tracks and 48,366 across 22 Town01 tracks, before save and after replay. Foreign representation files refused without changing the rendered pose; reloading the valid recipe succeeded. Stop disabled transfer controls. Four desktop/400-pixel screenshots were inspected; expected refusal notices are retained in the screenshots. No horizontal overflow, browser errors, authoring commands or Build/Run requests occurred. Complete project/import/history and Save/Open remained exact.

Evidence: `local-output/sdk-20260909/scene-animation-recipes-20261009/` contains Node/Python logs, private recipes, browser-check JSON and screenshots. No native recomp compile, runtime attachment, game launch, installation or disc export occurred. These checks establish source-bound editor inspection replay; native timing, runtime animation selection and gameplay appearance remain unverified.
