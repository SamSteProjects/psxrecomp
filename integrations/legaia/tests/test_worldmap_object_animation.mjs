import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldObjectAnimation} from '../editor/worldmap-object-animation.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let count=0,refusals=0;
for(const row of rows){
  for(const v of row.previews){await qualifyWorldObjectAnimation(v,row.current,v.entity_id,v.project_path,v.preview.frame_index);count++;}
  const v=row.previews[0];
  for(const mutate of [v=>v.preview.frame_index++,v=>v.preview.record_index++,v=>v.preview.byte_offset++,v=>v.preview.channel_count++,v=>v.preview.object_transforms[0].translation[0]++,v=>v.preview.geometry.vertices[0][0]+=.1,v=>v.preview.geometry.triangles[0][0]++,v=>v.preview.normal_pose='not_transformed',v=>v.preview.runtime_state='active',v=>v.preview.timing='30fps',v=>v.preview.bank_sha256='0'.repeat(64),v=>v.binding.bind.encoded_animation_selector++,v=>v.model_asset_id='foreign',v=>v.project_changed=true,v=>v.gameplay_verified=true]){
    const bad=structuredClone(v);mutate(bad);await assert.rejects(qualifyWorldObjectAnimation(bad,row.current,v.entity_id,v.project_path,v.preview.frame_index));refusals++;
  }
}
assert.equal(count,10);console.log(`${count} source first/last poses and ${refusals} altered scope/geometry refusals passed.`);
