import assert from 'node:assert/strict';
import {decodeNormalUsers} from '../editor/model-normal-users.js';
const hash='a'.repeat(64),binding={asset_id:'asset://fixture/model/0',object_index:0,normal_index:0,expected_sha256:hash,source_key:hash};
const row={kind:'primitive',field:'normal_index',object_index:0,normal_index:0,primitive_index:0,group_index:0,corner_index:0,corner_count:3,byte_offset:40,sharing:'flat_all_corners',affected_corners:[0,1,2]};
const source={schema_version:'legaia.model-normal-users.v1',...binding,project_source_key:hash,effective_sha256:hash,source_sha256:hash,scene_id:'scene://fixture',model_byte_length:128,retail_coordinates:[0,-4096,0],current_coordinates:[0,-2048,0],retail_users:[row],current_users:[row],read_only:true,gameplay_verified:false,scope:'qualified_stored_normal_reference_operands_in_selected_object'};
const result=decodeNormalUsers(source,binding);result.current_users[0].affected_corners[0]=2;assert.equal(source.current_users[0].affected_corners[0],0);
for(const delta of [{read_only:false},{gameplay_verified:true},{project_source_key:'b'.repeat(64)},{normal_index:1},{current_users:[row,row]},{current_users:[{...row,affected_corners:[0]}]},{current_users:[{...row,byte_offset:41}]},{current_coordinates:[0,32768,0]}])assert.throws(()=>decodeNormalUsers({...source,...delta},binding));
console.log('Normal-user source binding, detached layers, corner coverage and read-only guards passed.');
