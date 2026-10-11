import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldAnimationGlb} from '../editor/worldmap-animation-glb.js';
import {decodeAnimationSourceLibrary,decodeAnimationSourceComparison,navigateAnimationSource} from '../editor/animation-source-library.js';
const r=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),v=r.review,request={scene:v.scene,source_key:v.source_key,entity_id:v.entity_id,frame_index:v.frame_index,glb_base64:r.glb_base64,binding:v.binding,shared_record:true,animation_index:v.animation_index,object_nodes:v.object_nodes};
const qualified=await qualifyWorldAnimationGlb(v,r.held,r.current,v.entity_id,v.project_path,request);assert.equal(qualified.native.proposed_preview.record_sha256,v.candidate_record_sha256);let refusals=0;
for(const mutate of [v=>v.glb_sha256='0'.repeat(64),v=>v.source_key='stale',v=>v.entity_id='foreign',v=>v.binding.fps++,v=>v.animation_index=1,v=>v.object_nodes=[0,1],v=>v.shared_record=false,v=>v.analysis.candidate_sha256='0'.repeat(64),v=>v.native_review.proposed_preview.geometry.vertices[0][0]++,v=>v.native_review.edits=[]]){
 const bad=structuredClone(v);mutate(bad);await assert.rejects(qualifyWorldAnimationGlb(bad,r.held,r.current,v.entity_id,v.project_path,request));refusals++;
}
const library=decodeAnimationSourceLibrary(r.library,r.library.project_path),record=library.imports[0];assert.equal(record.kind,'world');decodeAnimationSourceComparison(r.comparison,library,record);assert.throws(()=>decodeAnimationSourceComparison({...r.comparison,active_in_native_bank:false},library,record));
let opened=0,switched=0;const state={project:{path:library.project_path,mode:'edit'},scene:{id:'scene://town01'}};
await navigateAnimationSource({record,catalog:library,getState:()=>state,readLibrary:async()=>library,changeScene:async()=>{switched++;return true;},openWorld:async row=>{assert.equal(row.target_id,record.target_id);opened++;return true;}});assert.equal(opened,1);assert.equal(switched,0);
await assert.rejects(navigateAnimationSource({record,catalog:library,getState:()=>state,readLibrary:async()=>library,changeScene:async()=>true}));
console.log(`Native World GLB candidate qualification, ${refusals} altered file/context/pose refusals, retained library comparison and field-scene-preserving navigation passed.`);
