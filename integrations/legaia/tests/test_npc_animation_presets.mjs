import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateNpcPresetMetadata} from '../editor/npc-preset-metadata.js';
import {decodePresetFileExport,decodePresetImportReview} from '../editor/preset-files.js';
import {decodeNpcPresetReview} from '../editor/npc-presets.js';
if(!process.argv[2])throw new Error('Provide fresh Retail animation argument preset transfer and instance fixtures.');
const {file,transfer,request,proposal,state}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
assert.equal(file.schema_version,'legaia.npc-preset-file.v13');
assert.deepEqual(decodePresetFileExport(file,file.template),file);
assert.deepEqual(decodePresetImportReview(transfer,JSON.stringify(file),transfer.template.name),transfer);
assert.deepEqual(decodeNpcPresetReview(proposal,request,state),proposal);
const key=Object.keys(file.template.components.NpcDraft.animation_operands.entries)[0];
for(const fields of [{animation_operand:true},{animation_operand:-1},{animation_operand:256},{animation_operand:1.5},{model_id:16777216,animation_frame:0,tween_frames:0},{}]){
  const bad=structuredClone(file);bad.template.components.NpcDraft.animation_operands.entries[key]=fields;
  assert.throws(()=>decodePresetFileExport(bad,bad.template));
}
for(const mutate of [v=>v.schema_version='legaia.npc-preset-file.v12',v=>v.template.components.NpcDraft.animation_operands.donor_entity_id='foreign',v=>v.template.components.NpcDraft.animation_operands.entries={'script://map02/actors/man-p1/0002/animation-operands/000e':{animation_operand:1}}]){
  const bad=structuredClone(file);mutate(bad);assert.throws(()=>decodePresetFileExport(bad,bad.template));
}
for(const mutate of [v=>delete v.draft.animation_operands,v=>v.draft.animation_operands.entries[key].animation_operand=3]){
  const bad=structuredClone(proposal);mutate(bad);assert.throws(()=>decodeNpcPresetReview(bad,request,state));
}
const partial=structuredClone(file.template);partial.components.NpcDraft.animation_operands.entries[key]={animation_operand:255};
assert.deepEqual(validateNpcPresetMetadata(partial),partial);
const copy=validateNpcPresetMetadata(file.template);copy.components.NpcDraft.animation_operands.entries[key].animation_operand=3;
assert.equal(file.template.components.NpcDraft.animation_operands.entries[key].animation_operand,255);
console.log('Fresh Retail v13 animation argument preset export/import/instance decoders, byte bounds, ownership, downgrade, loss and detached metadata checks passed.');

const model=structuredClone(file.template);model.components.NpcDraft.animation_operands.entries[key]={model_id:16777215,animation_frame:65535,tween_frames:0};assert.deepEqual(validateNpcPresetMetadata(model),model);
for(const change of [{model_id:16777216},{animation_frame:65536},{tween_frames:-1},{model_id:true},{extra:1}]){const bad=structuredClone(model);Object.assign(bad.components.NpcDraft.animation_operands.entries[key],change);assert.throws(()=>validateNpcPresetMetadata(bad));}
console.log('Metadata-only model/frame/tween native-width bounds passed; source qualification remains an SDK gate.');
const combined=structuredClone(file);combined.template.components.NpcDraft.transitions={donor_entity_id:combined.template.source.entity_id,entries:{['script://'+combined.template.source.entity_id.slice(8)+'/transition/001f']:{direction_encoded:7}}};
assert.deepEqual(decodePresetFileExport(combined,combined.template),combined);
const downgraded=structuredClone(combined);downgraded.schema_version='legaia.npc-preset-file.v12';assert.throws(()=>decodePresetFileExport(downgraded,downgraded.template));
const payload=structuredClone(file.template);payload.components.NpcDraft.animation_operands.raw_hex='3430ff';assert.throws(()=>validateNpcPresetMetadata(payload));
console.log('Animation v13 takes precedence over retained arrival metadata and refuses raw payload fields.');
