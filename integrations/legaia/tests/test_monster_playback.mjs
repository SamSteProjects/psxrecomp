import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyMonsterPreview} from '../editor/monster-archive.js';
import {createMonsterPlaybackSampler} from '../editor/monster-playback.js';
import {sampledWorldFrame} from '../editor/worldmap-animation-playback.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let vertices=0;
for(const v of cases.poses){const report=cases.report,record={id:v.clip.model_asset_id},base=await qualifyMonsterPreview(v.base_preview,report,record),sampler=await createMonsterPlaybackSampler(v,report,record,base,'retail');assert.equal(sampler.frameCount,v.clip.frame_count);assert.equal(sampler.initialFrame,v.frame_index);const sampled=sampler.sample(v.frame_index);for(let i=0;i<v.geometry.vertices.length;i++){for(let a=0;a<3;a++)assert(Math.abs(sampled.geometry.vertices[i][a]-v.geometry.vertices[i][a])<1e-7);vertices++;}assert.deepEqual(sampled.geometry.textures,v.geometry.textures);assert.throws(()=>sampler.sample(-1));assert.throws(()=>sampler.sample(v.clip.frame_count));const changed=structuredClone(v);changed.source_motion_base64=Buffer.from('changed').toString('base64');await assert.rejects(createMonsterPlaybackSampler(changed,report,record,base,'retail'));}
const saved=JSON.parse(fs.readFileSync(process.argv[3],'utf8')).pose,b=saved.base_preview,report={project_path:saved.project_path,project_source_key:saved.project_source_key,catalog:{source_key:saved.catalog_source_key,models:[b.record],textures:[b.texture_record],animations:[saved.clip]}},record={id:saved.clip.model_asset_id},base=await qualifyMonsterPreview(b,report,record,'current'),current=await createMonsterPlaybackSampler(saved,report,record,base,'current'),posed=current.sample(saved.frame_index).geometry;
assert.equal(posed.vertices.length,saved.geometry.vertices.length);
for(let i=0;i<posed.vertices.length;i++){assert.equal(posed.vertices[i].length,3);for(let a=0;a<3;a++){assert(Number.isFinite(posed.vertices[i][a]));assert(Math.abs(posed.vertices[i][a]-saved.geometry.vertices[i][a])<1e-7);}}
for(const k of ['min','max'])for(let a=0;a<3;a++)assert(Math.abs(posed.bounds[k][a]-saved.geometry.bounds[k][a])<1e-7);
assert.deepEqual(posed.textures,saved.geometry.textures);
// Local playback must retain its qualified snapshot rather than reread caller
// geometry or return mutable buffers that can corrupt subsequent frames.
const held=current.sample(saved.frame_index),first=held.geometry.vertices[0][0];
base.vertices[0][0]+=100;held.geometry.vertices[0][0]+=200;
assert.equal(current.sample(saved.frame_index).geometry.vertices[0][0],first);
const freshBase=await qualifyMonsterPreview(b,report,record,'current');
for(const alter of [v=>v.project_path+='-foreign',v=>v.frame_index=-1,v=>v.source_motion_base64=Buffer.from('changed').toString('base64')]){
 const v=structuredClone(saved);alter(v);await assert.rejects(createMonsterPlaybackSampler(v,report,record,freshBase,'current'));
}
assert.equal(sampledWorldFrame(0,30,12,0),0);assert.equal(sampledWorldFrame(0,30,12,1000),12);assert.equal(sampledWorldFrame(28,30,12,1000),29);assert.throws(()=>sampledWorldFrame(0,30,0,100));console.log(`Six Retail poses / ${vertices} vertices and saved Current playback match native sampling; source/index/rate refusals pass`);
