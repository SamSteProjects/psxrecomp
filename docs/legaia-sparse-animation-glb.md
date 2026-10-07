# Sparse Animation GLB Import

The imported-actor and retained-clip GLB editors accept sparse FLOAT animation accessors through their existing **Review**, **Preview**, and **Apply** actions. No conversion to dense GLB is required before uploading a file. Clip selection, external rigid-object mapping, joint-rig qualification, sampling controls, original-input retention, and current-source binding still apply.

Sparse input timestamps, translation outputs, rotation outputs, and cubic tangent/value rows are resolved before existing animation validation and sampling. A supplied dense base is copied and its sparse elements replaced; an absent base initializes to zero. Sparse indices use unsigned byte, short, or int components, must increase strictly, and must stay within the accessor count. Counts, offsets, spans, alignment, embedded-buffer ownership, and finite FLOAT values are checked. Sparse buffer views cannot declare a vertex stride or target. A base-less accessor cannot declare `byteOffset`.

The shared reader also accepts sparse FLOAT matrix elements used by the external-rig inverse-bind validator. Existing affine and rig-ownership validation remains responsible for qualifying those matrices; inverse binds are not applied as retargeting compensation.

These rules follow the primary [glTF 2.0 sparse accessor specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#sparse-accessors). The 32 MiB GLB bound, 65,536 accessor-element bound, and one-million resolved FLOAT-component bound remain. Sparse replacement counts cannot exceed their accessor counts. Unselected clips are not newly sampled or assigned semantic meaning.

The decoder preserves unchanged native angle bytes and opaque source fields. This is interchange support for existing rigid motion, not native skeletal skinning, arbitrary retargeting, a new gameplay timing model, or expanded retail animation capacity. Normal Build capacity and shared-ownership checks remain in force.

## Offline Verification

Seven new focused synthetic cases cover all three sparse index widths, explicit/implicit bases, exact unchanged source bytes, independently packed translation/rotation edits, cubic equivalence, invalid index ordering/ranges, malformed spans/types/views, nonfinite values, zero initialization, component bounds/cache accounting, and sparse matrices. Related existing animation, rig, hierarchy, matrix, and numeric-bound checks exercise the shared reader.

All 49 focused Python checks passed with no skips. Actual private imported-actor and retained-clip editor workflows at 1400/700 px passed named-clip selection, explicit joint mapping, Review/Preview/Return/Apply, changed-selection refusal, and exact original GLB/binding recovery. Each Apply created one history entry; Undo/Redo, Save/Open and a reopened project copy retained the expected authored metadata and inputs. Normal Build `1d2f919a5c71394a` delivered a relocation-backed native animation bank matching the composed project byte-for-byte (SHA-256 `b478a4e572459b837ae2be01b1eb94c160cec9aad4b1952c602e1123a356009d`). No page errors or Run requests occurred, the reference project stayed unchanged, and owned helpers terminated. No game launch, installation, or disc export occurred.

Private workflow evidence is stored under `local-output/sdk-20260909/animation-glb-sparse-20261007/`. The evidence remains local because the GLBs and native output may contain retail-derived content. Gameplay acceptance remains separate.
