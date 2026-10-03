import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {decodeWorldmapExport} from '../editor/worldmap-geometry.js';

if(!globalThis.crypto)Object.defineProperty(globalThis,'crypto',{value:webcrypto,configurable:true});
const key='a'.repeat(64),scene='map01',filename=`scene-${'b'.repeat(32)}.glb`;
const selected='scene://map01/worldmap/placements/0081';
const json=Buffer.from(JSON.stringify({asset:{version:'2.0'}}).padEnd(32)),bytes=Buffer.alloc(20+json.length);
bytes.writeUInt32LE(0x46546c67,0);bytes.writeUInt32LE(2,4);bytes.writeUInt32LE(bytes.length,8);
bytes.writeUInt32LE(json.length,12);bytes.writeUInt32LE(0x4e4f534a,16);json.copy(bytes,20);
const sha=buffer=>createHash('sha256').update(buffer).digest('hex');
const response=(scope='ground',entity_id=null)=>({schema_version:'legaia.worldmap-export.v1',scene,
  project_source_key:key,scope,entity_id,path:`C:/private/exports/${filename}`,filename,
  glb_base64:bytes.toString('base64'),gameplay_verified:false,project_changed:false,
  audit:{schema_version:'legaia.scene-export.v1',scene_id:'scene://map01',source_key:key,
    project_source_key:key,export_scope:scope,selected_entity_id:entity_id,byte_length:bytes.length,
    sha256:sha(bytes),worldmap_source:{scene,scope,entity_id,source_record:{map_sha256:key},
      coverage:{resolved_count:1},metrics:{entity_count:2},limitations:['Source spawn seeds; runtime visibility unverified.']}}});

for(const [scope,id] of [['ground',null],['source-scene',null],['selected',selected]]){
  const value=response(scope,id),before=JSON.stringify(value),decoded=await decodeWorldmapExport(value,scene,key,scope,id);
  assert.deepEqual(Buffer.from(decoded.bytes),bytes);
  assert.equal(JSON.stringify(value),before,'Export verification never changes ordinary metadata.');
}

// Header corruption carries an updated audit hash: byte integrity alone must
// not authorize a foreign format, wrong GLB version or truncated container.
for(const [at,word] of [[0,0],[4,1],[8,bytes.length+4],[12,3],[16,0]]){
  const invalid=response(),corrupted=Buffer.from(bytes);corrupted.writeUInt32LE(word,at);
  invalid.glb_base64=corrupted.toString('base64');invalid.audit.sha256=sha(corrupted);
  await assert.rejects(()=>decodeWorldmapExport(invalid,scene,key,'ground'));
}
for(const mutate of [
  r=>r.glb_base64='%%%=',r=>r.glb_base64=bytes.toString('base64').slice(1),
  r=>r.audit.sha256='c'.repeat(64),r=>r.audit.byte_length++,
  r=>r.filename='../scene-'+filename,r=>r.path='C:/private/another.glb',
  r=>r.scope='source-scene',r=>r.entity_id=selected,r=>r.scene='map02',
  r=>r.project_source_key='c'.repeat(64),r=>r.audit.source_key='c'.repeat(64),
  r=>r.audit.project_source_key='c'.repeat(64),r=>r.audit.export_scope='selected',
  r=>r.audit.selected_entity_id=selected,r=>r.audit.scene_id='scene://map02',
  r=>r.audit.worldmap_source.scope='selected',r=>r.audit.worldmap_source.entity_id=selected,
  r=>r.audit.worldmap_source.scene='map03',r=>r.audit.worldmap_source.coverage=null,
  r=>r.audit.worldmap_source.limitations=[null],r=>r.project_changed=true,r=>r.gameplay_verified=true,
]){const invalid=response();mutate(invalid);await assert.rejects(()=>decodeWorldmapExport(invalid,scene,key,'ground'));}
await assert.rejects(()=>decodeWorldmapExport(response('selected',selected),scene,key,'selected',selected.replace('0081','0082')));
await assert.rejects(()=>decodeWorldmapExport(response('selected',selected.replace('map01','map02')),scene,key,'selected',selected.replace('map01','map02')));
console.log('World GLB export verifies immutable bytes, all scopes, source/selection audits and independently corrupted headers/hashes.');
