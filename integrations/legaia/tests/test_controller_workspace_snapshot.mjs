import assert from 'node:assert/strict';
import {CONTROLLER_SNAPSHOT_SCHEMAS,decodeControllerWorkspaceSnapshot,controllerSnapshotRequest} from '../editor/controller-workspace-snapshot.js';
const owner='scene://fixture/controllers/man-p1/0000',key='a'.repeat(64);
const raw=()=>({schema_version:'legaia.controller-workspace-snapshot.v1',owner_id:owner,state_key:key,source_record_sha256:'b'.repeat(64),current_record_sha256:'c'.repeat(64),read_only:true,project_changed:false,gameplay_verified:false,families:Object.fromEntries(Object.entries(CONTROLLER_SNAPSHOT_SCHEMAS).map(([family,schema])=>[family,{schema_version:schema,owner_id:owner,state_key:key,source_record_sha256:'b'.repeat(64),current_record_sha256:'c'.repeat(64),gameplay_verified:false}]))});
const detached=decodeControllerWorkspaceSnapshot(raw(),owner,key);detached.ControllerGlobalBytes.state_key='changed';assert.equal(raw().families.ControllerGlobalBytes.state_key,key);
for(const change of [r=>r.owner_id='foreign',r=>r.state_key='f'.repeat(64),r=>r.read_only=false,r=>r.project_changed=true,r=>r.gameplay_verified=true,r=>delete r.families.ControllerFades,r=>r.families.Extra={},r=>r.families.ControllerFades.schema_version='foreign',r=>r.families.ControllerFades.current_record_sha256='f'.repeat(64),r=>r.families.ControllerGlobalBytes.owner_id='foreign',r=>r.families.ControllerGlobalBytes.source_record_sha256='f'.repeat(64)]){const r=raw();change(r);assert.throws(()=>decodeControllerWorkspaceSnapshot(r,owner,key));}
let requests=[];globalThis.fetch=async(route,options)=>{requests.push({route,options});return {ok:true,json:async()=>({fresh:true})};};
const initial=raw().families.ControllerGlobalBytes,options={method:'POST',body:JSON.stringify({entity:owner})},route='/api/controller-global-bytes';
const response=await controllerSnapshotRequest(route,options,initial,route);assert.deepEqual(await response.json(),initial);assert.equal(requests.length,0);const value=await response.json();value.state_key='changed';assert.equal((await response.json()).state_key,key);
assert.deepEqual(await (await controllerSnapshotRequest('/api/controller-global-byte-review',options,initial,route)).json(),{fresh:true});assert.equal(requests.length,1);
await controllerSnapshotRequest(route,options,null,route);assert.equal(requests.length,2);
for(const body of [{entity:'foreign'},{entity:owner,extra:true}])await assert.rejects(()=>controllerSnapshotRequest(route,{...options,body:JSON.stringify(body)},initial,route));
const abort=new AbortController();abort.abort();await assert.rejects(()=>controllerSnapshotRequest(route,{...options,signal:abort.signal},initial,route),{name:'AbortError'});
console.log('Combined family binding, detached preloads, legacy requests, uncached Review and aborted/foreign preload guards passed.');
