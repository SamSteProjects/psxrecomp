import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodePresetFileExport} from '../editor/preset-files.js';
import {decodeNpcScriptComparison} from '../editor/npc-script-comparison.js';
if(process.argv.length<5)throw new Error('Provide a fresh Retail v11 preset and both qualified saved-package comparison fixtures.');
const value=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
assert.equal(value.schema_version,'legaia.npc-preset-file.v11');
assert.deepEqual(decodePresetFileExport(value,value.template),value);
const first=Object.keys(value.template.components.NpcDraft.system_flags.entries)[0];
for(const mutate of [v=>v.schema_version='legaia.npc-preset-file.v1',v=>v.template.components.NpcDraft.system_flags.entries[first].index=true,v=>v.template.components.NpcDraft.system_flags.entries[first].index=4096,v=>v.template.components.NpcDraft.system_flags.donor_entity_id='foreign',v=>v.template.components.NpcDraft.system_flags.entries[first].extra=1]){
  const bad=structuredClone(value);mutate(bad);assert.throws(()=>decodePresetFileExport(bad,bad.template));
}
console.log('NPC system-selector v11 preset bytes, typed bounds, ownership and downgrade refusal passed.');
for(const path of process.argv.slice(3)){
  const {comparison,state,entry,entity_id}=JSON.parse(fs.readFileSync(path,'utf8'));
  decodeNpcScriptComparison(comparison,entity_id,state,entry);
  for(const value of [true,-1,4096]){
    const bad=structuredClone(state),key=Object.keys(bad.actor_drafts[entity_id].system_flags.entries)[0];
    bad.actor_drafts[entity_id].system_flags.entries[key].index=value;
    assert.throws(()=>decodeNpcScriptComparison(comparison,entity_id,bad,entry));
  }
  const bad=structuredClone(comparison);bad.authored_spans[0].after_hex='0000';
  assert.throws(()=>decodeNpcScriptComparison(bad,entity_id,state,entry));
}
console.log('Fresh Retail NPC package comparisons and malformed selector refusal passed.');
