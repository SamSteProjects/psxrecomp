import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {decodeScriptedWorldSceneExport} from '../editor/worldmap-geometry.js';
const cases=JSON.parse(readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of cases){
 const {result,current,scope,entity_id}=row,held=structuredClone(row);
 assert((await decodeScriptedWorldSceneExport(result,current,scope,entity_id)).bytes.length>20);
 for(const change of [v=>v.representation='retail-source',v=>v.source_key='0'.repeat(64),v=>v.entity_id='foreign',v=>v.audit.worldmap_source.placement_authoring.current_man_sha256='0'.repeat(64),v=>v.audit.worldmap_source.placement_authoring.scripted_binding.extra=true,v=>v.audit.worldmap_source.placement_authoring.authored_scripted_placements[0].script_id='foreign',v=>v.audit.worldmap_source.placement_authoring.ground_layer='current',v=>v.audit.worldmap_source.placement_authoring.gameplay_verified=true,v=>v.audit.worldmap_source.metrics.entity_count++,v=>v.audit.worldmap_source.coverage.resolved_count++,v=>v.audit.sha256='0'.repeat(64),v=>v.project_changed=true]){
  const bad=structuredClone(result);change(bad);await assert.rejects(()=>decodeScriptedWorldSceneExport(bad,current,scope,entity_id));refusals++;
 }
 // A self-consistent binary hash cannot substitute another UUID or transform.
 for(const mutate of [node=>node.extras.entity_id='foreign',node=>node.matrix[12]++]){
  const bad=structuredClone(result),bytes=Buffer.from(bad.glb_base64,'base64'),oldLength=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+oldLength));mutate(doc.nodes[doc.scenes[0].nodes[0]]);
  const json=Buffer.from(JSON.stringify(doc)),padded=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]),tail=bytes.subarray(20+oldLength),header=Buffer.from(bytes.subarray(0,20));header.writeUInt32LE(20+padded.length+tail.length,8);header.writeUInt32LE(padded.length,12);const raw=Buffer.concat([header,padded,tail]);bad.glb_base64=raw.toString('base64');bad.audit.byte_length=raw.length;bad.audit.sha256=Buffer.from(await crypto.subtle.digest('SHA-256',raw)).toString('hex');await assert.rejects(()=>decodeScriptedWorldSceneExport(bad,current,scope,entity_id));refusals++;
 }
 assert.deepEqual(row,held);console.log(row.scene,scope,'Current scripted export admitted');
}
const proof={cases:cases.length,refusals,inputs_unchanged:true,gameplay_verified:false};if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(proof);
