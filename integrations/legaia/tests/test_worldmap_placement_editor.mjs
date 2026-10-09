import {worldPlacementComparison} from '../editor/worldmap-placement-state.js';
import assert from 'node:assert/strict';
import {decodeWorldPlacements,placementSceneView,worldPlacementTarget,worldPlacementLayers} from '../editor/worldmap-placement-editor.js';
const key='a'.repeat(64),sha='b'.repeat(64),id='scene://map01/worldmap/placements/0064';
const values={offset:{x:4,y:8,z:12},yaw_units:64};
const report={schema_version:'legaia.worldmap-placement-authoring.v1',scene:'map01',source_key:key,gameplay_verified:false,project_changed:false,current_map_sha256:sha,source_record:{scene:'map01',source_disc_sha256:sha,source_map_sha256:sha,source_floor_lut_sha256:sha},limitations:[],records:[{record_id:'0005',object_record_index:5,source_record_sha256:sha,retail_values:values,current_values:values,authored_values:null,writable:true,source_cell_count:1,placements:[{entity_id:id,object_record_index:5,source_cell:100,source_record_sha256:sha}]}]};
assert.deepEqual(decodeWorldPlacements(report,'map01',key),report);
for(const mutate of [r=>r.gameplay_verified=true,r=>r.source_key='f'.repeat(64),r=>r.records[0].current_values.offset.x=32768,r=>r.records[0].source_cell_count=0,r=>r.records.push(structuredClone(r.records[0])),r=>r.records[0].placements[0].entity_id='scene://map02/worldmap/placements/0064']){const r=structuredClone(report);mutate(r);assert.throws(()=>decodeWorldPlacements(r,'map01',key));}
const proposed={offset:{x:132,y:24,z:76},yaw_units:1024};report.review={review_key:sha,record_id:'0005',candidate_map_sha256:sha,shared_record:false,no_op:false,values:proposed,proposed_values:proposed,changed_bytes:[{byte_offset:160,before_byte:4,after_byte:132}],affected_source_entities:[id]};assert(decodeWorldPlacements(report,'map01',key));
const base={assets:[],entities:[{entity_id:id,object_record_index:5,source_record_sha256:sha,source_position:{x:1000,y:200,z:3000},placement_scope:'source_spawn_seed'}]};const current=placementSceneView(base,report),preview=placementSceneView(base,report,true);assert.deepEqual(current.entities[0].authored_source_position,{x:1000,y:200,z:3000});assert.deepEqual(preview.entities[0].authored_source_position,{x:1128,y:216,z:2936});assert.equal(preview.entities[0].model_to_scene[7],-216);assert(Math.abs(preview.entities[0].model_to_scene[2]-1)<1e-12);assert(Math.abs(preview.entities[0].model_to_scene[8]+1)<1e-12);
for(const mutate of [r=>r.review.changed_bytes[0].byte_offset=167,r=>r.review.affected_source_entities=[],r=>r.review.candidate_map_sha256='bad']){const r=structuredClone(report);mutate(r);assert.throws(()=>decodeWorldPlacements(r,'map01',key));}
console.log('World placement source bounds, shared review ownership and independent matrix arithmetic passed');

const target={scene:'map01',sourceKey:key,recordIndex:5,sourceRecordHash:sha,entityId:id};
const owned=worldPlacementTarget(report,target);assert.deepEqual(owned,report.records[0]);owned.current_values.offset.x=100;assert.equal(report.records[0].current_values.offset.x,4);
for(const patch of [{scene:'map02'},{sourceKey:'c'.repeat(64)},{sourceRecordHash:'c'.repeat(64)},{recordIndex:6},{recordIndex:5.5},{entityId:id+'-other'}])assert.throws(()=>worldPlacementTarget(report,{...target,...patch}));
const duplicated=structuredClone(report);duplicated.records.push(structuredClone(report.records[0]));assert.throws(()=>worldPlacementTarget(duplicated,target));
const shared=structuredClone(report),second='scene://map01/worldmap/placements/0065';shared.records[0].source_cell_count=2;shared.records[0].placements.push({...shared.records[0].placements[0],entity_id:second,source_cell:101});assert.equal(worldPlacementTarget(shared,{...target,entityId:second}).placements[1].entity_id,second);
console.log('Exact world placement navigation owner, shared member, detached return and changed-source refusal passed');

const layers=worldPlacementLayers(report.records[0],{review:report.review,draft:proposed});assert.deepEqual(layers.retail,values);assert.deepEqual(layers.current,values);assert.equal(layers.authored,null);assert.deepEqual(layers.reviewed,proposed);assert.deepEqual(layers.draft,proposed);layers.retail.offset.x=123;assert.equal(report.records[0].retail_values.offset.x,4);
assert.equal(worldPlacementLayers(report.records[0]).reviewed,null);assert.equal(worldPlacementLayers(report.records[0]).draft,null);
for(const options of [{review:{...report.review,record_id:'0006'}},{draft:{...proposed,yaw_units:4096}}])assert.throws(()=>worldPlacementLayers(report.records[0],options));
console.log('Retail/Current/Authored/Reviewed/Draft layers retain missing overrides, exact values and record ownership');

const authoredRecord=structuredClone(report.records[0]);authoredRecord.authored_values=proposed;authoredRecord.current_values=proposed;const authoredLayers=worldPlacementLayers(authoredRecord);assert.deepEqual(authoredLayers.authored,proposed);assert.deepEqual(authoredLayers.current,proposed);assert.deepEqual(authoredLayers.retail,values);

const geometry={scene:'map01',project_source_key:key,source_record:{map_sha256:sha,floor_lut_sha256:sha,disc_sha256:sha}},beforeBase=JSON.stringify(base);assert.deepEqual(worldPlacementComparison(base,geometry,report).entities[0].authored_source_position,{x:1000,y:200,z:3000});assert.equal(JSON.stringify(base),beforeBase);
for(const change of [g=>g.scene='map02',g=>g.project_source_key='c'.repeat(64),g=>g.source_record.disc_sha256='c'.repeat(64),g=>g.source_record.map_sha256='c'.repeat(64),g=>g.source_record.floor_lut_sha256='c'.repeat(64)]){const changed=structuredClone(geometry);change(changed);assert.throws(()=>worldPlacementComparison(base,changed,report));}
console.log('Retail/Current comparison requires matching kingdom, state key, disc, MAP and floor sources');
