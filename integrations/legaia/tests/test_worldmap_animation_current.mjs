import fs from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyWorldAnimationCurrent,replayWorldAnimationChannels} from '../editor/worldmap-animation-current.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let positives=0,refusals=0;
for(const {current,preview:v} of rows){
  await qualifyWorldAnimationCurrent(v,current,v.entity_id,v.project_path,v.frame_index);positives++;
  const changes=[v=>v.preview.geometry.vertices[0][0]+=.1,v=>v.preview.bank_sha256='0'.repeat(64),v=>v.preview.record_index++,v=>v.preview.object_transforms[0].translation[0]++,v=>v.source.current_model_geometry.vertices[0][0]++,v=>v.source.edits.push({}),v=>v.source.audit.changed_bytes.push({}),v=>v.source_key='stale',v=>v.entity_id='foreign',v=>v.representation='current-model-retail-object-animation',v=>v.gameplay_verified=true,v=>v.audits.push({})];
  if(v.binding)changes.push(v=>v.binding.source_disc_sha256='0'.repeat(64),v=>v.binding.source_bank_sha256='0'.repeat(64),v=>Object.values(v.binding.entries)[0].source_record_sha256='0'.repeat(64),v=>Object.values(v.binding.entries)[0].edits[0].translation.x--,v=>Object.values(v.binding.entries)[0].edits.push(Object.values(v.binding.entries)[0].edits[0]));
  for(const mutate of changes){const bad=structuredClone(v);mutate(bad);await assert.rejects(qualifyWorldAnimationCurrent(bad,current,v.entity_id,v.project_path,v.frame_index));refusals++;}
  const p=v.source.before.preview,bank=Uint8Array.from(atob(p.bank_base64),c=>c.charCodeAt(0));
  const replay=await replayWorldAnimationChannels(bank,p.record_index,p.record_sha256,[{frame_index:0,object_index:0,translation:{x:-2048,z:2047},rotation_psx:{z:4080}}]);
  const expected=bank.slice(),at=p.byte_offset+8;expected[at]=0;expected[at+2]=(expected[at+2]&240)|8;expected[at+3]=255;expected[at+4]=(expected[at+4]&240)|7;expected[at+7]=255;assert.deepEqual(replay.bank,expected);
  for(const edit of [{frame_index:0,object_index:0,translation:{x:2048}},{frame_index:0,object_index:0,rotation_psx:{z:1}},{frame_index:0,object_index:0,translation:{x:true}},{frame_index:512,object_index:0,translation:{x:1}}]){await assert.rejects(replayWorldAnimationChannels(bank,p.record_index,p.record_sha256,[edit]));refusals++;}
}
assert.equal(positives,5);console.log(`${positives} actual Current poses, literal full-bank packed-axis replay and ${refusals} refusals passed.`);
