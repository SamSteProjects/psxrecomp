import fs from 'node:fs';import assert from 'node:assert/strict';
import {decodeWorldmapBehaviorResources,worldmapBehaviorProjectRecords,qualifyWorldmapBehaviorResource} from '../editor/worldmap-behavior-resources.js';
import {assetMatchesQuery,parseAssetQuery} from '../editor/asset-search.js';
const v=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),state={project:{path:v.project_path,mode:'edit'},worldmap_authoring_state_key:v.source_key,project_assets_source_key:'a'.repeat(64)},decoded=decodeWorldmapBehaviorResources(v,state),rows=worldmapBehaviorProjectRecords(decoded,state.project_assets_source_key),animations=rows.filter(r=>r.type==='animation');
assert.equal(animations.length,38);assert.equal(animations.filter(r=>!r.data.bindings.length).length,35);
assert.equal(v.kingdoms.reduce((n,k)=>n+k.animation_bank.record_count,0),47);assert.equal(v.kingdoms.reduce((n,k)=>n+k.unsupported_animation_records.length,0),9);
for(const r of animations){assert.equal(qualifyWorldmapBehaviorResource(r,v,state).record.id,r.id);assert(assetMatchesQuery(r,parseAssetQuery(r.data.authored_animation_id)));assert(assetMatchesQuery(r,parseAssetQuery('id:'+r.data.authored_animation_id)));assert(assetMatchesQuery(r,parseAssetQuery('type:animation scene:'+r.data.source_scene)));}
const first=v.assets.find(r=>r.kind==='animation');
const mutations=[x=>x.assets.find(r=>r.id===first.id).authored_animation_id='animation://map01/worldmap/anm/4095',x=>x.assets.find(r=>r.id===first.id).source_record.animation_slot.decoded_sha256='0'.repeat(64),x=>x.kingdoms[0].animation_bank.record_count++,x=>x.kingdoms[0].unsupported_animation_records.pop(),x=>x.kingdoms[0].unsupported_animation_records[0].byte_offset++,x=>x.kingdoms[0].unsupported_animation_records[0].record_index=x.assets.find(r=>r.kind==='animation'&&r.source_scene==='map01').source_record.record_index,x=>x.assets.splice(x.assets.findIndex(r=>r.kind==='animation'&&!r.bindings.length),1),x=>x.assets.find(r=>r.kind==='animation').timing='30fps',x=>x.assets.find(r=>r.kind==='animation').authoring='live',x=>x.assets.find(r=>r.kind==='animation').source_instance_ids=['foreign'],x=>x.kingdoms[0].animation_bank.source.descriptor_type=3,x=>x.source_key='0'.repeat(64),x=>x.assets.find(r=>r.kind==='animation'&&!r.bindings.length).authoring='shared_rigid_channels'];
for(const [index,mutate] of mutations.entries()){const bad=structuredClone(v);mutate(bad);assert.throws(()=>decodeWorldmapBehaviorResources(bad,state),undefined,`Mutation ${index}`);}
console.log('38 animation registrations, 35 unreferenced clips, complete 47-record/9-diagnostic coverage and 13 refusals passed.');

if(process.argv[3]){
 const {qualifyWorldAnimationAsset}=await import('../editor/worldmap-animation-current.js');let positive=0,negative=0;
 for(const {preview:p} of JSON.parse(fs.readFileSync(process.argv[3],'utf8'))){const row=v.assets.find(r=>r.kind==='animation'&&r.authored_animation_id===p.animation_id);assert(row);qualifyWorldAnimationAsset(p,row);positive++;
 for(const mutate of [r=>r.source_record.sha256='0'.repeat(64),r=>r.source_record.disc_sha256='0'.repeat(64),r=>r.source_record.byte_offset++,r=>r.source_record.prot_entry_index++,r=>r.authored_animation_id='foreign',r=>r.channel_count++,r=>r.frame_count++,r=>r.id='foreign']){const bad=structuredClone(row);mutate(bad);assert.throws(()=>qualifyWorldAnimationAsset(p,bad));negative++;}}
 assert.equal(positive,5);console.log(`${positive} actual asset-to-Current source bridges and ${negative} foreign source/alias refusals passed.`);
}
