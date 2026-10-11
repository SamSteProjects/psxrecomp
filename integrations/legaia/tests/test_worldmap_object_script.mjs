import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldObjectScript} from '../editor/worldmap-object-script.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let count=0,refusals=0;
for(const row of rows){
  for(const v of row.scripts){await qualifyWorldObjectScript(v,row.current,v.entity_id,v.project_path);count++;}
  const v=row.scripts.find(v=>v.inspection.graph.instructions.length);
  for(const mutate of [v=>v.extra=true,v=>v.inspection.entry_pc++,v=>v.inspection.record_index++,v=>v.inspection.graph.instructions[0].byte_offset++,v=>v.inspection.graph.instructions[0].raw_hex='00',v=>v.inspection.graph.instructions[0].opcode++,v=>v.inspection.graph.instructions.shift(),v=>v.inspection.runtime_execution='active',v=>v.inspection.asset_registration='registered',v=>v.consumer.script_pc_store='0x80000000',v=>v.consumer.function.sha256='0'.repeat(64),v=>v.project_changed=true,v=>v.gameplay_verified=true]){
    const bad=structuredClone(v);mutate(bad);await assert.rejects(qualifyWorldObjectScript(bad,row.current,v.entity_id,v.project_path));refusals++;
  }
}
assert.equal(count,59);console.log(`${count} byte-qualified source graphs and ${refusals} altered source/scope refusals passed.`);
