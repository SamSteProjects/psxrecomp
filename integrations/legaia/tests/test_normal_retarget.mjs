import assert from 'node:assert/strict';
import {validateNormalRetarget} from '../editor/normal-retarget.js';
const owner={kind:'primitive',field:'normal_index',object_index:1,primitive_index:4,group_index:0,corner_index:0,byte_offset:132};
const users={asset_id:'asset://fixture/models/1',object_index:1,normal_index:2,effective_sha256:'a'.repeat(64),current_users:[owner]};
const report={operation:'normal_references',asset_id:users.asset_id,object_index:1,effective_sha256:users.effective_sha256,proposed_sha256:'b'.repeat(64),project_changed:false,changes_from_current:[{...owner,before_value:2,after_value:3}]};
validateNormalRetarget(report,users,3);
for(const mutate of [v=>v.object_index=2,v=>v.project_changed=true,v=>v.changes_from_current=[],v=>v.changes_from_current[0].byte_offset=134,v=>v.changes_from_current[0].after_value=1,v=>v.changes_from_current[0].before_value=0,v=>v.changes_from_current[0].axis='x',v=>v.changes_from_current.push(v.changes_from_current[0]),v=>v.proposed_sha256=users.effective_sha256]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>validateNormalRetarget(bad,users,3));}
assert.throws(()=>validateNormalRetarget(report,users,2));const empty={...users,current_users:[]};validateNormalRetarget({...report,changes_from_current:[],proposed_sha256:users.effective_sha256},empty,3);
console.log('Normal retarget exact Current-user ownership, values, no-op and hash guards passed.');
