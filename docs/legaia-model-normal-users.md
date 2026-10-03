# Stored normal reference navigation

Open an unposed imported or authored model, choose **Edit model vectors**, select an existing object, choose **Normals**, then **Find faces using this normal**. The read-only lookup shows separate **Current** and **Retail** layers. Each row identifies the stored reference word by byte offset and describes its corner ownership: one flat operand serves every face corner, while a Gouraud operand belongs to one corner. Unlit packets do not create normal users.

**Inspect current face** opens the existing face editor at that object and primitive. A Retail row can identify a face whose current reference changed. The action inspects the current face; it does not restore or edit normal references. Stored normal coordinates, reference ownership, runtime use and retail lighting are separate facts.

The server qualifies the complete retail and effective model layouts and permitted replacement bytes before reading references. The request must match both the inspected effective model hash and current project source key. A final source-key check rejects changes during inspection. The browser validates detached metadata, signed coordinates, reference bounds and flat/Gouraud corner coverage. Changing the selected vector or closing aborts and withdraws the result; late replies cannot repopulate the inspector. Metadata is bounded to4096 operands per layer and4MiB; the UI explicitly shows at most128 rows.

Nine focused Python cases and the Node metadata/source guards pass. Seven actual browser checks pass, including a540px screenshot, source face navigation and closing with a fetched response withheld. The private Town01 model0009 object1 normal1 fixture retains prior material/reference/rescaling edits. Retail references normal1 at byte2940; Current references normal2 there, leaving normal1 with zero Current users. Independent raw primitive-packet reads match the complete report for both layers. Every project file hash and history record stays exact, and no authoring command, Build or game request runs.

Proof and inspected screenshot: `local-output/sdk-20260909/model-normal-users-20261003/parent/`. Owned helpers are closed. Gameplay visibility and native lighting are unverified; this feature requires no immediate gameplay check.

## Reference lookup with face removal

Existing face-removal overrides now support read-only reference lookup. Current faces show their retained Retail owners; the Retail layer marks removed faces with no Current identity. Stored-word offsets remain specific to the displayed layer. Face-editor navigation and reference retargeting remain guarded for this topology binding. Source/model hash and selection-lifetime guards still apply.
