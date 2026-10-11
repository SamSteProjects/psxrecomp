# World Behavior Resources

Project Resources now includes Retail World object scripts and their supported source animation clips for Map01, Map02 and Map03. Choose **Project resources**, search by stable ID, source kingdom, model or resource type, then select a script or animation. Its details link to the related model and behavior resources. **Inspect source object** opens Current World geometry, selects and frames the exact recorded source object, and provides the existing bind, script and animation inspectors.

The importer resolves source placed objects against the Retail primary/fallback kind-1 MAP bind tables. Supported P0 headers identify script entries; nonzero animation selectors identify ANM record `selector - 1`. Source clip registration requires supported frame/channel bounds and exact native model object/channel counts. Unknown partitions, missing binds and unsupported clips remain explicit. Retail associations are not rewritten by Current transform or model overrides.

The SDK registers the metadata through the shared `AssetDatabase.register_resources` API on a detached request-scoped project view. This discovery does not change the project's document, Undo/Redo stacks, dirty state or source caches. The returned registration is a verified catalog record, not a persistent authored asset. Stable IDs are `script://map01/worldmap/man-p0/0000` and `animation://map01/worldmap/scene-anm/0004`, with equivalent kingdom-qualified identities for other records. Duplicate bindings share one asset identity.

`POST /api/worldmap-behavior-resources` accepts exactly `{ "source_key": "<worldmap_authoring_state_key>" }` in Edit mode. Its metadata-only v1 response retains record/slot hashes and spans, retail executable/consumer evidence, object/model relationships, inspection summaries, kingdom coverage and limitations. It contains no MAN/ANM payload. Browser qualification checks identities, provenance structure, source spans, counts, reciprocal relationships, coverage and fresh project/native keys. It does not independently re-decode the binary records; the existing source inspectors perform their separate byte qualification.

The real-disc catalog has **57 unique scripts, 59 script/object bindings, three animation assets and five animation/object bindings**. Map02 has one script record shared by three objects; counting placements as assets would inflate the inventory. Five Map03 objects have no source bind and remain unbound. No unsupported animation binding occurred in this retail catalog. Playback timing, looping, live residency/activation, script execution and writable World behavior remain unresolved. The source script graph endpoint still presents a structural identity; its independent inspection response does not imply registration in an already loaded Project Resources catalog.

Offline checks on 2026-10-10 passed 20 focused Python checks, three Node suites including 60 real-record qualifications and 22 altered source/scope refusals, and three actual kingdom HTTP/editor workflows. Each workflow navigated script to animation and back, selected the exact Current source object and opened its bind/script inspectors, with zero authoring commands or page errors. The private document/history and Save/Open baseline remained unchanged. Related model navigation and wide/400-pixel captures are recorded separately. Private evidence is under `local-output/sdk-20260909/worldmap-behavior-resources-20261010/`; no retail payload is tracked.

No package Build, native compile, game launch, runtime attachment, installation or disc export was performed. Gameplay verification remains deferred. This completes resource discovery/navigation for the evidenced source bindings; it does not complete the full SDK goal or World behavior authoring.

Focused rerun commands from the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTHONPATH=".;integrations/legaia;integrations/legaia/tests"
C:\Python314\python.exe -m unittest test_worldmap_behavior_resources test_worldmap_object_script test_project_assets test_project_assets_http -q
& "C:\Program Files\nodejs\node.exe" integrations/legaia/tests/test_worldmap_behavior_resources.mjs local-output/sdk-20260909/worldmap-behavior-resources-20261010/catalog.json
& "C:\Program Files\nodejs\node.exe" integrations/legaia/tests/test_worldmap_project_resources.mjs local-output/sdk-20260909/worldmap-resources-20261009/index.json local-output/sdk-20260909/worldmap-behavior-resources-20261010/catalog.json
& "C:\Program Files\nodejs\node.exe" integrations/legaia/tests/test_project_assets.mjs
```

The Node catalog suites require the private metadata fixtures generated from the authorized local disc; they are not checked into the repository.
