import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createCurrentPackPlayback} from '../editor/battle-pack-current-actions.js';
import {battlePackChannelTrack} from '../editor/battle-pack-timeline.js';
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let frames=0,vertices=0,tracks=0,refusals=0;
const multiply=(a,b)=>a.map(row=>b[0].map((_,j)=>row.reduce((sum,n,k)=>sum+n*b[k][j],0)));
for(const c of fixture.cases){
 const before=JSON.stringify(c),first=c.poses[0],sampler=await createCurrentPackPlayback(first,c.inspection,fixture.report,c.record,fixture.animations,first.clip),stream=sampler.byteStream(),signed=n=>n>=2048?n-4096:n;
 assert.equal(sampler.currentTmdHash,c.inspection.current_tmd_sha256);assert.equal(sampler.currentEntryHash,c.inspection.current_entry_sha256);
 for(let frame=0;frame<sampler.frameCount;frame++){
  const sampled=sampler.sample(frame);assert.equal(sampled.frame_index,frame);
  for(let part=0;part<first.clip.bone_count;part++){
   const at=8+(frame*first.clip.bone_count+part)*8,translation=[signed(stream[at]+(stream[at+2]&15)*256),signed(stream[at+1]+(stream[at+2]>>4)*256),signed(stream[at+3]+(stream[at+4]&15)*256)],rotations=[stream[at+5],stream[at+6],stream[at+7]].map(n=>n*Math.PI/128),[x,y,z]=rotations,rx=[[1,0,0],[0,Math.cos(x),-Math.sin(x)],[0,Math.sin(x),Math.cos(x)]],ry=[[Math.cos(y),0,Math.sin(y)],[0,1,0],[-Math.sin(y),0,Math.cos(y)]],rz=[[Math.cos(z),-Math.sin(z),0],[Math.sin(z),Math.cos(z),0],[0,0,1]],matrix=multiply(multiply(rz,ry),rx),object=c.inspection.geometry.objects[part];
   for(let vertex=object.vertex_start;vertex<object.vertex_start+object.vertex_count;vertex++){
    const expected=matrix.map((row,a)=>row.reduce((sum,n,k)=>sum+n*c.inspection.geometry.vertices[vertex][k],translation[a]));
    expected.forEach((n,a)=>assert(Math.abs(n-sampled.geometry.vertices[vertex][a])<1e-7));vertices++;
   }
  }
  for(const key of ['objects','triangles','materials','triangle_materials','triangle_uvs','triangle_colors','textures'])assert.deepEqual(sampled.geometry[key],c.inspection.geometry[key]);
  assert.equal(sampled.geometry.triangle_normals,undefined);assert.equal(sampled.geometry.normal_preview,undefined);frames++;
 }
 for(let part=0;part<first.clip.bone_count;part++)for(const field of ['translation','rotation_psx'])for(const axis of ['x','y','z']){const track=await battlePackChannelTrack(sampler,part,field,axis);assert.equal(track.samples.length,sampler.frameCount);tracks++;}
 const original=sampler.sample(0);sampler.sample(0).geometry.vertices[0][0]+=100;sampler.byteStream().fill(0);sampler.channel(0,0).translation.fill(123);assert.deepEqual(sampler.sample(0),original);
 for(const frame of [-1,sampler.frameCount,0.5,true,NaN,Infinity,'0']){assert.throws(()=>sampler.sample(frame));refusals++;}
 for(const change of [v=>v.geometry.vertices[0][0]++,v=>v.inspection.current_entry_sha256='0'.repeat(64),v=>v.retail_playback.source_motion_sha256='0'.repeat(64),v=>v.clip.model_asset_id='foreign']){const v=structuredClone(first);change(v);await assert.rejects(()=>createCurrentPackPlayback(v,c.inspection,fixture.report,c.record,fixture.animations,first.clip));refusals++;}
 assert.equal(JSON.stringify(c),before);
}
console.log(`${frames} cached Current frames / ${vertices} independent native vertex samples / ${tracks} channel tracks / ${refusals} refusals pass; inputs and returned samples remain isolated`);
