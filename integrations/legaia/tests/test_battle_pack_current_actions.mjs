import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyCurrentPackPose,qualifyCurrentPackExport} from '../editor/battle-pack-current-actions.js';
import {createBattlePackPlayback} from '../editor/battle-pack-playback.js';
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let poses=0,exports=0,refusals=0;
let trackSamples=0;
for(const c of fixture.cases){
 for(const pose of c.poses){await qualifyCurrentPackPose(pose,c.inspection,fixture.report,c.record,fixture.animations,pose.clip,pose.frame_index);poses++;
  for(const edit of [v=>v.inspection.current_tmd_sha256='0'.repeat(64),v=>v.geometry.vertices[0][0]++,v=>v.object_transforms[0].translation[0]++,v=>v.geometry.triangles[0][0]++,v=>v.geometry.textures[0].status='foreign',v=>v.layer='retail',v=>v.frame_index++,v=>v.geometry.bounds.min[0]++,v=>v.project_source_key='stale']){const v=structuredClone(pose);edit(v);await assert.rejects(()=>qualifyCurrentPackPose(v,c.inspection,fixture.report,c.record,fixture.animations,pose.clip,pose.frame_index));refusals++;}
 }
 for(const value of c.exports){const selection={mode:value.mode,clip:value.clip,frame_index:value.frame_index,fps:value.fps};await qualifyCurrentPackExport(value,c.inspection,fixture.report,c.record,selection);exports++;
  if(value.mode==='clip'){
   const bytes=Buffer.from(value.glb_base64,'base64'),length=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+length)),binary=bytes.subarray(28+length),animation=doc.animations[0],original=c.poses[0].retail_playback;
   const sampler=await createBattlePackPlayback(original,fixture.report,fixture.animations,c.record,original.raw_geometry);
   function values(index){const a=doc.accessors[index],v=doc.bufferViews[a.bufferView],width={SCALAR:1,VEC3:3,VEC4:4}[a.type],at=(v.byteOffset??0)+(a.byteOffset??0),stride=v.byteStride??width*4;assert.equal(a.componentType,5126);return Array.from({length:a.count},(_,n)=>Array.from({length:width},(_,i)=>binary.readFloatLE(at+n*stride+i*4)));}
   assert.equal(animation.channels.length,value.clip.bone_count*2);
   for(let part=0;part<value.clip.bone_count;part++){
    const channels=animation.channels.filter(ch=>ch.target.node===part),tracks=Object.fromEntries(channels.map(ch=>[ch.target.path,animation.samplers[ch.sampler]]));const ts=values(tracks.translation.output),qs=values(tracks.rotation.output),times=values(tracks.translation.input);assert.equal(ts.length,value.clip.frame_count+1);assert.deepEqual(ts.at(-1),ts.at(-2));assert.deepEqual(qs.at(-1),qs.at(-2));assert.equal(tracks.rotation.interpolation,'STEP');
    for(let frame=0;frame<value.clip.frame_count;frame++){const t=sampler.channel(frame,part);assert.deepEqual(ts[frame],[t.translation[0],-t.translation[1],t.translation[2]]);assert(Math.abs(times[frame][0]-frame/value.fps)<1e-6);const [rx,ry,rz]=t.rotation_psx.map(n=>n*Math.PI/2048),sx=Math.sin(rx),cx=Math.cos(rx),sy=Math.sin(ry),cy=Math.cos(ry),sz=Math.sin(rz),cz=Math.cos(rz),[qx,qy,qz,qw]=qs[frame];for(const basis of [[1,0,0],[0,1,0],[0,0,1]]){let [x,y,z]=basis;const [vx,vy,vz]=[x,-y,z];[y,z]=[y*cx-z*sx,y*sx+z*cx];[x,z]=[x*cy+z*sy,-x*sy+z*cy];[x,y]=[x*cz-y*sz,x*sz+y*cz];const cross=[2*(qy*vz-qz*vy),2*(qz*vx-qx*vz),2*(qx*vy-qy*vx)],actual=[vx+qw*cross[0]+qy*cross[2]-qz*cross[1],vy+qw*cross[1]+qz*cross[0]-qx*cross[2],vz+qw*cross[2]+qx*cross[1]-qy*cross[0]];[x,-y,z].forEach((n,i)=>assert(Math.abs(n-actual[i])<1e-6));}trackSamples++;}
    assert(Math.abs(times.at(-1)[0]-value.clip.frame_count/value.fps)<1e-6);
   }
  }
  for(const edit of [v=>v.current_tmd_sha256='0'.repeat(64),v=>v.current_entry_sha256='0'.repeat(64),v=>v.mode='foreign',v=>v.audit.sha256='0'.repeat(64),v=>v.audit.byte_length++,v=>v.filename='../foreign.glb',v=>v.project_source_key='stale',v=>v.fps=999]){const v=structuredClone(value);edit(v);await assert.rejects(()=>qualifyCurrentPackExport(v,c.inspection,fixture.report,c.record,selection));refusals++;}
 }
}
console.log(`${poses} authored Current pack poses / ${exports} exports / ${trackSamples} literal full-clip tracks / ${refusals} altered model, source, frame, geometry and export refusals pass`);
