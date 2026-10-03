# Coordinated scene animation preview

The scene animation timeline previews every eligible actor's verified initial clip together in the existing scene viewport. It is a transient editor view. It does not author a game timeline, execute scripts, observe current runtime clips or establish retail playback timing.

## Workflow

Import a verified field scene and choose Edit mode. Choose the Authored or Retail scene representation, then start scene animation preview. Preparation reports animated instances, shared tracks and actors whose animation remains static or unavailable. It does not present partial coverage as a complete live scene.

Use Play/Pause or the integer tick control to inspect poses. Preview rate is an explicit display setting from 1 to 30 frames per second, initially 10. Every track samples `preview_tick % frame_count`; repeating all clips is a preview convention. The shared sample index continues past the longest clip so different clip lengths loop independently. The scrub range expands to retain elapsed preview samples. Frames are discrete source samples, with no invented interpolation, script scheduling, movement or transitions.

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

Full-clip model composition uses the effective TMD through every frame. Object ranges, triangles, UV/color data, material mapping and frame zero must agree with the canonical scene. A material edit can rebuild its derived material table, so texture associations come from the freshly qualified effective source rather than an old material index. Source normals and unsupported runtime rendering effects are not inferred by the timeline.

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
