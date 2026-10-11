// Complete-byte/audit cross-language proof; pass a private collected fixture file.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {replayScriptedWorldPlacements as replay, mergeScriptedWorldCurrent as merge,
  allocateScriptedWorldPlacements as allocate} from '../editor/worldmap-scripted-placement-replay.js';
const decode=s=>new Uint8Array(Buffer.from(s,'base64'));
function matching(a,b,key='') {
  if (key==='source_to_world') {assert.equal(a.length,16);a.forEach((v,i)=>assert.ok(Math.abs(v-b[i])<=1e-12));return;}
  if(Array.isArray(b)){assert.equal(a.length,b.length);b.forEach((v,i)=>matching(a[i],v));return;}
  if(b&&typeof b==='object'){assert.deepEqual(Object.keys(a).sort(),Object.keys(b).sort());Object.keys(b).forEach(k=>matching(a[k],b[k],k));return;}
  assert.deepEqual(a,b);
}
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const c of cases){
  const base=decode(c.base),fallback=decode(c.fallback),man=decode(c.man),normal=decode(c.normal),scene=c.binding.scene;
  const held=JSON.stringify(c),result=await replay(base,fallback,man,c.floor,c.binding,c.provenance);
  assert.deepEqual(result.bytes,decode(c.allocated));matching(result.audits,c.audits);
  assert.deepEqual(await merge(base,result.bytes,normal,c.floor,scene,result.audits),decode(c.merged));
  assert.equal(JSON.stringify(c),held);
  for(const key of ['base_map_sha256','fallback_sha256','source_man_sha256','source_disc_sha256']){
    const bad=structuredClone(c.binding);bad[key]='0'.repeat(64);
    await assert.rejects(()=>replay(base,fallback,man,c.floor,bad,c.provenance));refusals++;
  }
  const checksum=structuredClone(c.binding);checksum.operations[0].proposed_map_sha256='0'.repeat(64);
  await assert.rejects(()=>replay(base,fallback,man,c.floor,checksum,c.provenance));refusals++;
  const operation=c.binding.operations[0],request=operation.requests[0];
  for(const patch of [{shared_script:false},{shared_script:1},{record_index:true},{record_index:request.record_index+512},{target_cell:true},{donor_cell:-1},{extra:1}]){
    const requests=structuredClone(operation.requests);Object.assign(requests[0],patch);
    await assert.rejects(()=>allocate(base,fallback,man,c.floor,scene,requests,operation.relocation_offset));refusals++;
  }
  for(const offset of [true,17,19,8192,operation.relocation_offset]){
    const bytes=base.slice();if(offset===operation.relocation_offset)bytes[65536+offset]=1;
    await assert.rejects(()=>allocate(bytes,fallback,man,c.floor,scene,operation.requests,offset));refusals++;
  }
  for(const offset of [request.record_index*32,32768+request.target_cell*2,65542]){
    const bytes=normal.slice();bytes[offset]^=1;
    await assert.rejects(()=>merge(base,result.bytes,bytes,c.floor,scene,result.audits));refusals++;
  }
  for(const values of [{offset:{x:true,y:0,z:0},yaw_units:0},{offset:{x:32768,y:0,z:0},yaw_units:0},{offset:{x:0,y:0,z:0},yaw_units:4096}]){
    const requests=structuredClone(operation.requests);requests[0].values=values;
    await assert.rejects(()=>allocate(base,fallback,man,c.floor,scene,requests,operation.relocation_offset));refusals++;
  }
  for(const tier of [[],[true,...c.floor.slice(1)]]){
    await assert.rejects(()=>allocate(base,fallback,man,tier,scene,operation.requests,operation.relocation_offset));refusals++;
  }
  const badMan=man.slice();new DataView(badMan.buffer).setInt16(34,-1,true);
  await assert.rejects(()=>allocate(base,fallback,badMan,c.floor,scene,operation.requests,operation.relocation_offset));refusals++;
  const shadow=fallback.slice(),sv=new DataView(shadow.buffer),anchor=result.audits[0].allocations[0].anchor_cell;
  // Replace the private fallback block with one literal occupied destination.
  shadow.fill(0);sv.setInt16(6,32,true);sv.setInt16(8,1,true);shadow.set([anchor%128,Math.floor(anchor/128),0,131],32);
  await assert.rejects(()=>allocate(base,shadow,man,c.floor,scene,operation.requests,operation.relocation_offset));refusals++;
  const repeated=structuredClone(operation.requests);repeated.push(structuredClone(repeated[0]));
  await assert.rejects(()=>allocate(base,fallback,man,c.floor,scene,repeated,operation.relocation_offset));refusals++;
  assert.deepEqual(base,decode(c.base));assert.deepEqual(fallback,decode(c.fallback));assert.deepEqual(man,decode(c.man));assert.deepEqual(normal,decode(c.normal));
  console.log(c.name,'complete replay/audit/merge passes');
}
const proof={cases:cases.length,refusals,complete_bytes_audits_and_merges_match:true,
  input_sha256:createHash('sha256').update(fs.readFileSync(process.argv[2])).digest('hex'),browser_rendered:false,gameplay_verified:false};
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');
console.log(JSON.stringify(proof));
