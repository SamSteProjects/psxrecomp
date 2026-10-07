import assert from 'node:assert/strict';
import {animationChannelAuthoringTarget,validateImportedChannelHandoff,validateRetainedChannelHandoff} from '../editor/animation-channel-authoring.js';
const entity='scene://town01/actors/man-p1/0011',asset='asset://town01/models/scene-tmd/0011';
const frames=Array.from({length:3},(_,i)=>({frame_index:i,object_transforms:[{object_index:0,translation:[i,0,0],rotation_psx:[0,0,16]}]}));
const animation={representation:'imported',clip_id:'scene-header',actor_semantic_id:entity,semantic_id:'animation://town01/scene-anm/0012',asset_semantic_id:asset,frame_count:3,bone_count:1};
const preview={frames,animation},binding={semantic_id:animation.semantic_id,asset_semantic_id:asset,frame_count:3,bone_count:1};
const target=animationChannelAuthoringTarget(preview,entity,2,0);assert.equal(target.kind,'imported');assert.equal(target.initial.frame,2);validateImportedChannelHandoff(target.initial,binding);
for(const bad of [{...binding,frame_count:2},{...binding,semantic_id:'other'},{...binding,asset_semantic_id:'other'},{...binding,bone_count:2}])assert.throws(()=>validateImportedChannelHandoff(target.initial,bad));
for(const representation of ['file_preview','allocation_preview','allocated_record_edit_preview','allocated_initial_assignment','reference'])assert.throws(()=>animationChannelAuthoringTarget({frames,animation:{...animation,representation}},entity,1,0));
assert.throws(()=>animationChannelAuthoringTarget(preview,'scene://town01/actors/man-p1/0012',1,0));assert.throws(()=>animationChannelAuthoringTarget(preview,entity,3,0));assert.throws(()=>animationChannelAuthoringTarget(preview,entity,1,1));
const id='11111111-1111-4111-8111-111111111111',row={entity_id:entity,animation_id:'animation://town01/authored-record/'+id,record_id:id,record_sha256:'a'.repeat(64),donor_asset_id:asset,frame_count:3,object_count:1};
const retained={frames,animation:{...animation,representation:'allocated_record',clip_id:'allocated-record',semantic_id:row.animation_id,saved_record:row,source_record:{record_id:id,record_sha256:row.record_sha256}}};
const saved=animationChannelAuthoringTarget(retained,entity,2,0);assert.equal(saved.kind,'retained');saved.row.record_sha256='b'.repeat(64);assert.equal(row.record_sha256,'a'.repeat(64));
for(const changes of [{record_sha256:'b'.repeat(64)},{record_id:'other'},{frame_count:2},{object_count:2},{donor_asset_id:'other'}])assert.throws(()=>animationChannelAuthoringTarget({frames,animation:{...retained.animation,saved_record:{...row,...changes}}},entity,1,0));
console.log('Imported/retained channel handoff ownership, frame bounds, source witness and detached targets passed');

const current=animationChannelAuthoringTarget(retained,entity,2,0),context={sceneId:"scene://town01",sourceKey:"c".repeat(64)},library={schema_version:"legaia.animation-record-library.v1",scene_id:context.sceneId,project_source_key:context.sourceKey,records:[row]};assert.deepEqual(validateRetainedChannelHandoff(current,library,context),row);for(const bad of [{...library,project_source_key:"d".repeat(64)},{...library,scene_id:"scene://other"},{...library,records:[]},{...library,records:[{...row,active:true}]},{...library,records:[{...row,record_sha256:"d".repeat(64)}]}])assert.throws(()=>validateRetainedChannelHandoff(current,bad,context));
