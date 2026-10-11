import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldFootprint} from '../editor/worldmap-footprint.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let count=0,refusals=0;
for(const row of rows){
  const held=JSON.stringify(row);
  for(const report of row.footprints){
    const result=await qualifyWorldFootprint(report,row.current,report.entity_id,report.project_path);
    assert.deepEqual(result,report);count++;
  }
  const report=row.footprints[0];
  for(const mutate of [v=>v.offset.x++,v=>v.centre.z++,v=>v.encoded.sub_anchor.x++,v=>v.anchor.cell_flags^=0x400,
    v=>v.correction=!v.correction,v=>v.record_sha256='0'.repeat(64),v=>v.extents='known',v=>v.runtime_collision='verified',
    v=>v.scope='live-collision',v=>v.gameplay_verified=true,v=>v.project_changed=true,v=>v.extra=true]){
    const bad=structuredClone(report);mutate(bad);await assert.rejects(qualifyWorldFootprint(bad,row.current,report.entity_id,report.project_path));refusals++;
  }
  await assert.rejects(qualifyWorldFootprint(report,row.current,`scene://${row.current.scene}/worldmap/ground`,report.project_path));refusals++;
  assert.equal(JSON.stringify(row),held);
}
assert.equal(rows.length,3);assert.equal(count,64);
console.log(`${count} native placed footprint calculations and ${refusals} altered/scope refusals passed.`);
