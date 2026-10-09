import assert from 'node:assert/strict';
import {assetBuildRecords} from '../editor/asset-build-history.js';
const asset='asset://fixture/models/0000',key='a'.repeat(64),id='b'.repeat(16),archive='c'.repeat(64),disc='d'.repeat(64);
const direct=Array.from({length:301},(_,index)=>({asset_id:asset,owner_id:asset,scene:'fixture',field:'model.shape',scope:'qualified-model',before:'e'.repeat(64),after:'f'.repeat(64),coordinate_changes:[{index,before:1,after:2}]}));
const changes=[...direct,{asset_id:'script://fixture/run/1',owner_id:asset,scene:'fixture',field:'dialogue.text',scope:'source',before:'old',after:'new'},{asset_id:'asset://other/models/1',owner_id:'scene://other/actor/1',scene:'other',field:'position.x',scope:'initial',before:64,after:128}];
const entry={id,status:'completed',archive_sha256:archive,source_disc_sha256:disc,build_kind:'authored',change_count:changes.length};
const value={id,integrity:'verified',gameplay_verified:false,matches_current_inputs:true,source_disc_integrity:'not_checked',runtime_status:'package_built_not_launched',scope:'receipt_audit_manifest_package_source_files_and_ZIP_members',receipt:{authored_state_key:key,archive_sha256:archive,source_disc_sha256:disc,build_kind:'authored'},report:{schema_version:'legaia.build-report.v1',change_count:changes.length,changes,overlay_bytes:1,validation:{live_runtime:'not_run'}}};
assert.equal(assetBuildRecords(value,entry,asset,key).length,302);assert.equal(assetBuildRecords(value,entry,asset,key,false).length,301);
assert.equal(assetBuildRecords(value,entry,asset,key).at(-1).relationship,'Exact audit owner ID');assert.equal(assetBuildRecords(value,entry,asset,key)[0].relationship,'Exact audit asset ID');
assert.deepEqual(assetBuildRecords(value,entry,asset,key)[0].record.coordinate_changes,direct[0].coordinate_changes);
const detached=assetBuildRecords(value,entry,asset,key);detached[0].record.coordinate_changes[0].after=9;assert.equal(value.report.changes[0].coordinate_changes[0].after,2);
assert.equal(assetBuildRecords(value,entry,'asset://not-recorded/model',key).length,0);
assert.equal(assetBuildRecords({...value,matches_current_inputs:false},entry,asset,'0'.repeat(64)).length,302);
for(const mutate of [v=>v.receipt.archive_sha256='0'.repeat(64),v=>v.receipt.source_disc_sha256='0'.repeat(64),v=>v.receipt.build_kind='retail',v=>v.receipt.authored_state_key='0'.repeat(64),v=>delete v.receipt,v=>v.gameplay_verified=true,v=>v.report.change_count++,v=>v.report.changes[0].asset_id=0]){const bad=structuredClone(value);mutate(bad);assert.throws(()=>assetBuildRecords(bad,entry,asset,key));}
assert.throws(()=>assetBuildRecords(value,{...entry,change_count:1},asset,key));assert.throws(()=>assetBuildRecords(value,entry,'../escape',key));assert.throws(()=>assetBuildRecords(value,entry,asset,key,null));
for(const invalid of [{...entry,id:'../escape'},{...entry,archive_sha256:'invalid'},{...entry,source_disc_sha256:'invalid'},{...entry,change_count:-1},{...entry,build_kind:'unknown'}])assert.throws(()=>assetBuildRecords(value,invalid,asset,key));
console.log('Asset Build exact asset/owner matching, full ledgers, detached data, receipt/current-input binding and no-record semantics passed.');

const controller='script://fixture/controllers/man-p1/0000',owner=controller.replace('script://','scene://');
const {CONTROLLER_BUILD_TARGETS}=await import('../editor/controller-build-navigation.js');
const operands=Object.entries(CONTROLLER_BUILD_TARGETS).map(([scope,[component,kind,field]])=>({asset_id:controller+'/'+kind+'/0005',owner_id:owner,scene:'fixture',field,scope,before:0,after:1}));
const bad=operands[0],foreign=[{...bad,owner_id:owner+'extra'},{...bad,scene:'other'},{...bad,scope:'unsupported'},{...bad,field:'other'},{...bad,asset_id:controller+'/foreign/0005'},{...bad,asset_id:bad.asset_id+'extra'}];
const controllerValue=structuredClone(value);controllerValue.report.changes=[...operands,...foreign];controllerValue.report.change_count=controllerValue.report.changes.length;const controllerEntry={...entry,change_count:controllerValue.report.change_count};
const rows=assetBuildRecords(controllerValue,controllerEntry,controller,key);assert.equal(rows.length,11);assert(rows.every(row=>row.relationship==='Qualified controller audit owner'));assert.deepEqual(rows.map(row=>row.record),operands);assert.equal(assetBuildRecords(controllerValue,controllerEntry,controller,key,false).length,0);assert.equal(assetBuildRecords(controllerValue,controllerEntry,controller.replace('/controllers/','/other/'),key).length,0);
assert.equal(assetBuildRecords({...controllerValue,matches_current_inputs:false},controllerEntry,controller,'0'.repeat(64)).length,11);
console.log('All eleven controller audit owner mappings require exact scene, owner, scope, field and operand identity; stale packages remain inspectable as history.');
