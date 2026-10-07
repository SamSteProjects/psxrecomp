# Native Animation Channel Graph

Open an animated model preview and expand **Inspect native animation channels**. Choose a rigid object, translation or rotation XYZ, and a 16/32/64/128-frame window. Earlier/Later moves the visible window without changing the inspected pose. Each axis has a distinct color and a literal native value readout.

Click the graph to choose the nearest displayed integer frame. Left/Right steps through the clip; Home/End selects the visible window endpoints. The graph and existing frame slider/transport share the current preview frame. Graph object selection also selects and frames that model object; choosing a supported object in the model selector updates the graph. The animated assembly view can show all supported objects while the graph inspects one rigid channel.

Translation is displayed in encoded object-local native units, with PSX Y pointing down. Rotation retains 0–4080 PSX units in steps of 16; 4096 is a full turn. Stepped lines join stored samples for inspection. They do not establish runtime interpolation, retail timing, joint parenting or anatomical meaning. Rotation wraps remain visible in the encoded domain rather than being silently unwrapped. Constant tracks and final partial windows preserve exact samples.

The graph consumes the current model preview data. It does not read runtime memory, request a separate source, write project commands or alter Build inputs. New clips reset its frame/object window. Missing or malformed native channels are explicitly unavailable; no graph values are synthesized from posed vertices. Existing preview provenance identifies imported, authored, reference or proposed data.

## Verification

Focused checks cover native bounds and angle grid, exact XYZ series, malformed/out-of-order frames, unavailable objects, detached window data, final partial windows, graph pointer endpoints/clamping and single-frame selection. Gameplay verification remains deferred.

Three focused Node suites passed (channel graph and existing animation GLB/blend contracts), with two changed JS module syntax checks and server AST validation. Actual 1400/400 px Town01 browser checks matched native decoded readouts and passed frame/object/keyboard/pointer synchronization and unposed reset, without page errors. A separate synthetic 150-frame controller check passed window navigation and selected-frame following. The narrow graph uses horizontal scrolling for readable labels, and transport wraps. Complete project document, Undo/Redo and file snapshots remained unchanged. All owned helpers terminated. No Build, game, runtime attachment, installation or disc export occurred. Final evidence: `local-output/sdk-20260909/animation-channel-graph-20261007/complete/`; preceding selector and layout attempts remain retained.
