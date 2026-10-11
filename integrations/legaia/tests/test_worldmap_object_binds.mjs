import fs from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyWorldObjectBind} from '../editor/worldmap-object-bind.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let count=0,absent=0,refusals=0;
for(const row of rows){
  for(const v of row.binds){await qualifyWorldObjectBind(v,row.current,v.entity_id,v.project_path);count++;if(v.bind.status==='no_source_bind')absent++;}
  const v=row.binds.find(v=>v.bind.status==='resolved_source_header');
  for(const mutate of [v=>v.bind.encoded_animation_selector++,v=>v.bind.man_record.flat_record_index++,v=>v.bind.man_record.partition++,v=>v.bind.man_record.byte_offset++,v=>v.bind.man_record.header.local_count++,v=>v.bind.trigger.encoded.gate++,v=>v.bind.status='live',v=>v.bind.animation_clip='resolved',v=>v.bind.runtime_activation='active',v=>v.project_changed=true,v=>v.gameplay_verified=true,v=>v.placement.anchor.col++]){
    const bad=structuredClone(v);mutate(bad);await assert.rejects(qualifyWorldObjectBind(bad,row.current,v.entity_id,v.project_path));refusals++;
  }
  const missing=row.binds.find(v=>v.bind.status==='no_source_bind');
  if(missing)for(const mutate of [v=>v.bind.status='resolved_source_header',v=>v.bind.encoded_animation_selector=0,v=>v.bind.man_record={},v=>v.bind.trigger={}]){
    const bad=structuredClone(missing);mutate(bad);await assert.rejects(qualifyWorldObjectBind(bad,row.current,missing.entity_id,missing.project_path));refusals++;
  }
}
assert.equal(count,64);assert.equal(absent,5);
console.log(`${count} source binds, ${absent} explicit absences and ${refusals} altered scope/header refusals passed.`);
