import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateNpcPresetMetadata} from '../editor/npc-preset-metadata.js';
import {decodePresetFileExport,decodePresetImportReview} from '../editor/preset-files.js';
import {decodeNpcPresetReview} from '../editor/npc-presets.js';
if(!process.argv[2])throw new Error('Provide fresh Retail arrival preset transfer and instance fixtures.');
const {file,transfer,request,proposal,state}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
assert.equal(file.schema_version,'legaia.npc-preset-file.v12');
assert.deepEqual(decodePresetFileExport(file,file.template),file);
assert.deepEqual(decodePresetImportReview(transfer,JSON.stringify(file),transfer.template.name),transfer);
assert.deepEqual(decodeNpcPresetReview(proposal,request,state),proposal);
const key=Object.keys(file.template.components.NpcDraft.transitions.entries)[0];
for(const fields of [{direction_encoded:true},{entry_x_encoded:-1},{entry_z_encoded:256},{direction_encoded:1.5},{destination:'town01'},{}]){
  const bad=structuredClone(file);bad.template.components.NpcDraft.transitions.entries[key]=fields;
  assert.throws(()=>decodePresetFileExport(bad,bad.template));
}
for(const mutate of [v=>v.schema_version='legaia.npc-preset-file.v11',v=>v.template.components.NpcDraft.transitions.donor_entity_id='foreign',v=>v.template.components.NpcDraft.transitions.entries={'script://map02/actors/man-p1/0003/transition/0035':{direction_encoded:1}}]){
  const bad=structuredClone(file);mutate(bad);assert.throws(()=>decodePresetFileExport(bad,bad.template));
}
for(const mutate of [v=>delete v.draft.transitions,v=>v.draft.transitions.entries[key].direction_encoded=3]){
  const bad=structuredClone(proposal);mutate(bad);assert.throws(()=>decodeNpcPresetReview(bad,request,state));
}
const partial=structuredClone(file.template);partial.components.NpcDraft.transitions.entries[key]={direction_encoded:255};
assert.deepEqual(validateNpcPresetMetadata(partial),partial);
const copy=validateNpcPresetMetadata(file.template);copy.components.NpcDraft.transitions.entries[key].direction_encoded=3;
assert.equal(file.template.components.NpcDraft.transitions.entries[key].direction_encoded,7);
console.log('Fresh Retail v12 arrival preset export/import/instance decoders, byte bounds, ownership, downgrade, loss and detached metadata checks passed.');
