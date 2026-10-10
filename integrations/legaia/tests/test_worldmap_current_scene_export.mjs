import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeCurrentWorldSceneExport} from '../editor/worldmap-geometry.js';
import {placementDigest} from '../editor/worldmap-placement-replay.js';
const primary=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),coauthors=process.argv[3]?JSON.parse(fs.readFileSync(process.argv[3],'utf8')):[],rows=[...primary,...coauthors];let positives=0,refusals=0;
async function forge(value,mutate){
 const bytes=Buffer.from(value.glb_base64,'base64'),size=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+size));mutate(doc);
 const text=Buffer.from(JSON.stringify(doc)),padded=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]),tail=bytes.subarray(20+size),result=Buffer.alloc(20+padded.length+tail.length);
 bytes.copy(result,0,0,20);result.writeUInt32LE(result.length,8);result.writeUInt32LE(padded.length,12);padded.copy(result,20);tail.copy(result,20+padded.length);
 const changed=structuredClone(value);changed.glb_base64=result.toString('base64');changed.audit.byte_length=result.length;changed.audit.sha256=await placementDigest(result);return changed;
}
for(const row of rows){
 for(const value of row.exports){const decoded=await decodeCurrentWorldSceneExport(value,row.current,value.scope,value.entity_id);assert.equal(decoded.bytes.length,value.audit.byte_length);positives++;}
 const selected=row.exports.find(v=>v.scope==='selected');
 for(const mutate of [v=>v.schema_version='foreign',v=>v.review_key='0'.repeat(64),v=>v.audit.representation='retail-source',v=>v.audit.worldmap_source.placement_authoring.authored_records={},v=>v.audit.worldmap_source.metrics.entity_count++,v=>v.audit.entity_count++,v=>v.audit.worldmap_source.placement_authoring.source_map_sha256='0'.repeat(64),v=>v.audit.sha256='0'.repeat(64)]){
  const bad=structuredClone(selected);mutate(bad);await assert.rejects(decodeCurrentWorldSceneExport(bad,row.current,'selected',selected.entity_id));refusals++;
 }
 for(const mutate of [d=>d.nodes[d.scenes[0].nodes[0]].matrix[12]++,d=>d.nodes[d.scenes[0].nodes[0]].extras.entity_id='foreign',d=>d.nodes[d.scenes[0].nodes[0]].extras.source_position.y++,d=>d.scenes[0].nodes=[],d=>d.scenes[0].nodes.push(d.scenes[0].nodes[0]),d=>d.extras.worldmap_source.placement_authoring.source_map_sha256='0'.repeat(64)]){
  const bad=await forge(selected,mutate);await assert.rejects(decodeCurrentWorldSceneExport(bad,row.current,'selected',selected.entity_id));refusals++;
 }
}
assert.equal(primary.length,6);if(process.argv[3])assert.equal(coauthors.length,3);assert.equal(positives,rows.length*3);console.log(`${positives} actual Current v1/v2 full/ground/selected GLBs and ${refusals} altered metadata or rehashed GLB claims passed.`);
