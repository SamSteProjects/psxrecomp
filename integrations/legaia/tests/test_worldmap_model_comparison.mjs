import fs from 'node:fs';
import assert from 'node:assert/strict';
import {worldModelComparisonGeometry,qualifyWorldModelComparison} from '../editor/worldmap-model-comparison.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2]));
for(const item of rows){
 const source={...item.source,tmd:new Uint8Array(Buffer.from(item.source.tmd_base64,'base64'))},candidate=new Uint8Array(Buffer.from(item.expected_base64,'base64'));
 assert.deepEqual(worldModelComparisonGeometry(source,source.tmd),item.current_geometry);
 assert.deepEqual(worldModelComparisonGeometry(source,candidate),item.proposed_geometry);
 const receipt={request:{asset_id:item.name,source_key:'key'},review_key:'review',proposed_sha256:'candidate'};source.metadata.tmd_sha256='current';
 const value={schema_version:'legaia.worldmap-model-comparison.v1',project_path:'project',asset_id:item.name,source_key:'key',review_key:'review',current_sha256:'current',proposed_sha256:'candidate',current:item.current_geometry,proposed:item.proposed_geometry,coordinate_system:'retail_tmd_object_local_y_down',read_only:true,project_changed:false,gameplay_verified:false},options={source,candidate,receipt,path:'project'},held=structuredClone(value);
 const qualified=qualifyWorldModelComparison(value,options);qualified.current.vertices[0][0]++;assert.deepEqual(value,held);
 for(const mutate of [v=>v.extra=true,v=>v.project_path='foreign',v=>v.asset_id='foreign',v=>v.source_key='stale',v=>v.review_key='stale',v=>v.current_sha256='stale',v=>v.proposed_sha256='stale',v=>v.current.vertices[0][0]++,v=>v.proposed.vertices[0][1]++,v=>v.proposed.triangles[0][0]++,v=>v.current.triangles=[],v=>v.coordinate_system='y_up',v=>v.read_only=false,v=>v.project_changed=true,v=>v.gameplay_verified=true]){const bad=structuredClone(value);mutate(bad);assert.throws(()=>qualifyWorldModelComparison(bad,options));}
}
assert(rows.length);console.log(rows.length+' native/synthetic comparison pairs: exact independent vertices and packet topology, detached results and fifteen forged ownership/geometry claims each passed.');
