import fs from 'node:fs';
import assert from 'node:assert/strict';
import {qualifySidebandExport} from '../editor/battle-sideband.js';
import {placementDigest} from '../editor/worldmap-placement-replay.js';

const c = JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let checks = 0, refusals = 0;
for (const value of c.cases) {
  const record = value.inspection.record, palette = value.inspection.palette_index;
  await qualifySidebandExport(value,c.report,record,value.export_kind,palette); checks++;
  for (const change of [v=>v.filename='../foreign', v=>v.sha256='0'.repeat(64), v=>v.byte_length++,
    v=>v.inspection.project_source_key='stale', v=>v.inspection.record.source_record.byte_offset++,
    v=>v.inspection.palette_index++, v=>v.export_kind='unknown', v=>v.read_only=false]) {
    const changed = structuredClone(value); change(changed);
    await assert.rejects(() => qualifySidebandExport(changed,c.report,record,value.export_kind,palette)); refusals++;
  }
  const forged = structuredClone(value), data = Uint8Array.from(Buffer.from(forged.file_base64,'base64'));
  if (value.export_kind === 'glb') {
    const view = new DataView(data.buffer), n = view.getUint32(12,true), doc = JSON.parse(new TextDecoder().decode(data.subarray(20,20+n)));
    const primitive = doc.meshes.find(m=>m.primitives.length).primitives[0], accessor = doc.accessors[primitive.attributes.POSITION], buffer = doc.bufferViews[accessor.bufferView];
    const at = 20+n+8+buffer.byteOffset; view.setFloat32(at,view.getFloat32(at,true)+1,true);
  } else data[data.length-1] ^= 1;
  forged.file_base64 = Buffer.from(data).toString('base64'); forged.sha256 = await placementDigest(data);
  if (forged.export_kind === 'glb') forged.audit.sha256 = forged.sha256;
  await assert.rejects(() => qualifySidebandExport(forged,c.report,record,value.export_kind,palette)); refusals++;
}
console.log(`${checks} source GLB/PNG/STP exports qualify; ${refusals} source, filename, pixels, rehashed positions and CRC alterations refuse`);
