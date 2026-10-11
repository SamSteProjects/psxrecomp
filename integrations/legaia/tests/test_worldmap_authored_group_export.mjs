import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeCurrentWorldSceneExport} from '../editor/worldmap-geometry.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const {value,report,ids} of rows){
  const held=JSON.stringify([value,report,ids]),decoded=await decodeCurrentWorldSceneExport(value,report,'selected-authored',null,ids);assert.equal(decoded.bytes.length,value.audit.byte_length);
  for(const mutate of [v=>v.placement_ids.reverse(),v=>v.entity_ids.pop(),v=>v.scope='selected-records',v=>v.representation='proposed-source',v=>v.audit.selected_entity_ids.reverse(),v=>v.audit.worldmap_source.entity_ids.pop(),v=>v.audit.worldmap_source.placement_authoring.selected_placement_ids.pop(),v=>v.audit.geometry_count++,v=>v.audit.entity_count++,v=>v.audit.worldmap_source.placement_authoring.current_map_sha256='f'.repeat(64),v=>v.audit.sha256='f'.repeat(64)]){
    const bad=structuredClone(value);mutate(bad);await assert.rejects(decodeCurrentWorldSceneExport(bad,report,'selected-authored',null,ids));refusals++;
  }
  for(const mutate of [doc=>doc.nodes[doc.scenes[0].nodes[0]].matrix[12]++,doc=>doc.extras.selected_entity_ids.pop(),doc=>doc.extras.geometry_count++,doc=>doc.scenes[0].nodes[1]=doc.scenes[0].nodes[0],doc=>doc.nodes[doc.scenes[0].nodes[0]].extras.authored_placement.record_index++]){
    const bad=structuredClone(value),original=Buffer.from(bad.glb_base64,'base64'),length=original.readUInt32LE(12),doc=JSON.parse(original.subarray(20,20+length).toString());mutate(doc);let json=Buffer.from(JSON.stringify(doc));json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);const header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);header.writeUInt32LE(20+json.length+original.length-20-length,8);header.writeUInt32LE(json.length,12);header.writeUInt32LE(0x4e4f534a,16);const bytes=Buffer.concat([header,json,original.subarray(20+length)]);bad.glb_base64=bytes.toString('base64');bad.audit.byte_length=bytes.length;bad.audit.sha256=Buffer.from(await crypto.subtle.digest('SHA-256',bytes)).toString('hex');await assert.rejects(decodeCurrentWorldSceneExport(bad,report,'selected-authored',null,ids));refusals++;
  }
  for(const bad of [[],[ids[0],ids[0]],['foreign'],[...ids].reverse()]){await assert.rejects(decodeCurrentWorldSceneExport(value,report,'selected-authored',null,bad));refusals++;}
  assert.equal(JSON.stringify([value,report,ids]),held);
}
assert.equal(rows.length,3);console.log(`Three actual Current group GLBs qualify; ${refusals} scope, membership, native-provenance and byte-hash refusals pass.`);
