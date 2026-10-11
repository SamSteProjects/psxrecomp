import fs from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyWorldAnimationScene,sampleWorldAnimationScene} from '../editor/worldmap-animation-scene.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let members=0,refusals=0;
for(const v of rows){
  const held=structuredClone(v),plan=await qualifyWorldAnimationScene(v,v.current,v.project_path,v.source_key,v.members[0]?.current.binding);
  assert.equal(plan.samples.length,v.coverage.current_instances);members+=plan.samples.length;assert.deepEqual(v,held);
  const view={assets:v.current.scene_graph.assets.map(a=>({...a,geometry_key:a.asset_id})),entities:v.current.scene_graph.entities.map(e=>({...e,geometry_key:e.asset_id,model_to_scene:e.source_to_world}))},base=structuredClone(view);
  for(const frame of [0,1,511]){
    const next=sampleWorldAnimationScene(plan,view,frame);
    assert.equal(next.assets.length,view.assets.length+plan.samples.length);assert.deepEqual(view,base);
    for(const entity of next.entities){const original=view.entities.find(e=>e.entity_id===entity.entity_id),s=plan.samples.find(m=>m.entity_id===entity.entity_id);assert.deepEqual({...entity,geometry_key:original.geometry_key},original);if(s){const geometry=next.assets.find(a=>a.geometry_key===entity.geometry_key).preview;assert.deepEqual(geometry,s.sampler.sample(Math.min(frame,s.sampler.frameCount-1)).geometry);}else assert.deepEqual(entity,original);}
  }
  assert.throws(()=>sampleWorldAnimationScene(plan,view,-1));assert.throws(()=>sampleWorldAnimationScene(plan,view,512));assert.throws(()=>sampleWorldAnimationScene(plan,view,.5));
  const foreign=structuredClone(view);foreign.assets.find(a=>a.asset_id===v.current.scene_graph.entities.find(e=>e.entity_id===plan.samples[0].entity_id).asset_id).preview.vertices[0][0]++;assert.throws(()=>sampleWorldAnimationScene(plan,foreign,0));
  for(const mutate of [v=>v.members.pop(),v=>v.members.push(v.members[0]),v=>v.members[0].animation_asset_id='foreign',v=>v.members[0].current.preview.record_sha256='0'.repeat(64),v=>v.members[0].current.preview.geometry.vertices[0][0]++,v=>v.coverage.source_only_clips++,v=>v.absent.push({}),v=>v.unsupported_bindings.push({}),v=>v.current.scene_graph.entities[0].source_position=[1,2,3],v=>v.source_key='0'.repeat(64),v=>v.runtime_state='active',v=>v.timing='30fps']){
    const bad=structuredClone(v);mutate(bad);await assert.rejects(qualifyWorldAnimationScene(bad,v.current,v.project_path,v.source_key,v.members[0]?.current.binding));refusals++;
  }
}
assert.equal(rows.length,3);assert.equal(members,5);
console.log(`3 complete kingdom plans, ${members} qualified Current samplers and ${refusals} ownership/coverage/source refusals passed.`);
