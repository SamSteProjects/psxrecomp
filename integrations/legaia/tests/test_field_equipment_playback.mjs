import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createFieldEquipmentPlaybackSampler} from '../editor/field-equipment-playback.js';
import {sampledWorldFrame} from '../editor/worldmap-animation-playback.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let poses=0,vertices=0,refusals=0;
for(const item of cases){
 const {context,value,frames}=item,sampler=await createFieldEquipmentPlaybackSampler(value,context);
 assert.equal(sampler.frameCount,value.frame_count);assert.equal(sampler.initialFrame,context.frameIndex);
 for(const native of frames){const sampled=sampler.sample(native.frame_index);assert.deepEqual(sampled.object_transforms,native.object_transforms);assert.equal(sampled.geometry.vertices.length,native.vertices.length);for(let i=0;i<native.vertices.length;i++)for(let k=0;k<3;k++)assert(Math.abs(sampled.geometry.vertices[i][k]-native.vertices[i][k])<=1e-7);assert.deepEqual(sampled.geometry.textures,value.preview.base_geometry.textures);assert.deepEqual(sampled.geometry.equipment_variant,value.preview.geometry.equipment_variant);assert.equal(sampled.geometry.frame_index,native.frame_index);assert.equal(sampled.geometry.triangle_normals,undefined);poses++;vertices+=native.vertices.length;}
 for(const frame of [-1,sampler.frameCount,NaN,.5]){assert.throws(()=>sampler.sample(frame));refusals++;}
 // Cached sampling owns copies: later caller mutations cannot alter the source.
 const held=sampler.sample(0);value.preview.base_geometry.vertices[0][0]+=7;value.record_base64='';assert.deepEqual(sampler.sample(0).geometry.vertices,held.geometry.vertices);
}
const fresh=JSON.parse(fs.readFileSync(process.argv[2],'utf8'))[0];
for(const mutate of [
 v=>v.bank_sha256='0'.repeat(64),v=>v.record_sha256='0'.repeat(64),
 v=>{const b=Buffer.from(v.record_base64,'base64');b[8]^=1;v.record_base64=b.toString('base64');},
 v=>v.source_record.record_index++,v=>v.source_record.byte_offset++,v=>v.channel_count=12,
 v=>v.frame_count++,v=>v.active_object_indices[0]=1,v=>v.preview.animation.association.record_index++,
 v=>v.preview.geometry.object_transforms[0].opaque_nibble^=1,v=>v.preview.geometry.equipment_variant.selected_equipment_byte=1,
 v=>v.timing='verified_native_30fps',v=>v.looping='verified_loop',v=>v.project_changed=true,v=>v.display_fps=30
]){const v=structuredClone(fresh.value);mutate(v);await assert.rejects(()=>createFieldEquipmentPlaybackSampler(v,fresh.context));refusals++;}
for(const patch of [{frameIndex:-1},{frameIndex:999},{equipmentByte:1},{modelLayer:'current'},{clipId:'walk'},{sourceKey:'stale'}]){await assert.rejects(()=>createFieldEquipmentPlaybackSampler(fresh.value,{...fresh.context,...patch}));refusals++;}
assert.equal(sampledWorldFrame(0,30,12,1000),12);assert.equal(sampledWorldFrame(0,30,60,1000),29);
for(const fps of [0,61,.5,NaN]){assert.throws(()=>sampledWorldFrame(0,30,fps,1000));refusals++;}
console.log(`${cases.length} Field Equipment clips, ${poses} native poses / ${vertices} vertices and ${refusals} source/index/rate refusals passed`);
