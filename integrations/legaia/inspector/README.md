# Legaia Trace inspector

Read-only browser surface for metadata emitted by the PSXRecomp-side `town01` importer. It accepts `legaia.scene-import.v1` JSON through a local file picker or drag/drop, then shows actor records, an X/Z placement projection, imported transforms, model references, source spans, provenance claims, confidence and unresolved fields.

The selected JSON is parsed in browser memory. The inspector has no upload endpoint, storage, PSXRecomp connection, runtime writes, authoring controls or asset rendering. Its built-in data is explicitly synthetic and contains no retail content.

## Run locally

```powershell
npm ci --ignore-scripts
npm run dev
```

Open the local URL, choose **Open import**, and select the JSON produced by:

```powershell
python ..\tools\legaia_import.py --disc "C:\path\to\Legend of Legaia.bin" --scene town01 --output "C:\local-output\imported-town01.json"
```

Validate with `npm test`. Building or hosting the inspector never includes a user import; user-selected metadata stays in the current browser tab.
