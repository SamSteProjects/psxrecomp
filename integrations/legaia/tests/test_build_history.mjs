import assert from 'node:assert/strict';
import {decodeBuildHistory,decodeBuildVerification,decodeBuildVerificationForEntry} from '../editor/build-history.js';
const id='a'.repeat(16),hash='b'.repeat(64),value={builds:[{id,status:'completed',gameplay_verified:false,integrity:'not_checked',matches_current_inputs:true,archive_sha256:hash,source_disc_sha256:hash,build_kind:'retail',change_count:0,archive_path:'private.psxmod'}],truncated:false,coverage:'project_Builds_only_identity_order'};
const detached=decodeBuildHistory(value);detached.builds[0].id='c'.repeat(16);assert.equal(value.builds[0].id,id);
for(const mutate of [v=>v.builds[0].gameplay_verified=true,v=>v.builds[0].integrity='verified',v=>v.builds.push(v.builds[0]),v=>v.coverage='newest',v=>v.builds[0].id='../escape',v=>v.builds[0].matches_current_inputs=null]){const v=structuredClone(value);mutate(v);assert.throws(()=>decodeBuildHistory(v));}
const verified={id,integrity:'verified',gameplay_verified:false,matches_current_inputs:true,source_disc_integrity:'not_checked',runtime_status:'package_built_not_launched',scope:'receipt_audit_manifest_package_source_files_and_ZIP_members',report:{schema_version:'legaia.build-report.v1',changes:[],change_count:0,overlay_bytes:0,validation:{live_runtime:'not_run'}}};
assert.equal(decodeBuildVerification(verified,id).integrity,'verified');
for(const mutate of [v=>v.id='c'.repeat(16),v=>v.gameplay_verified=true,v=>v.source_disc_integrity='verified',v=>v.report.change_count=1,v=>v.runtime_status='running']){const v=structuredClone(verified);mutate(v);assert.throws(()=>decodeBuildVerification(v,id));}
const bound={...verified,receipt:{authored_state_key:hash,archive_sha256:hash,source_disc_sha256:hash,build_kind:'retail'}};
assert.equal(decodeBuildVerificationForEntry(bound,value.builds[0],hash).matches_current_inputs,true);
assert.equal(decodeBuildVerificationForEntry({...bound,matches_current_inputs:false},value.builds[0],'0'.repeat(64)).matches_current_inputs,false);
for(const mutate of [v=>v.receipt.archive_sha256='0'.repeat(64),v=>v.receipt.source_disc_sha256='0'.repeat(64),v=>v.receipt.build_kind='authored',v=>v.receipt.authored_state_key='0'.repeat(64),v=>delete v.receipt]){const bad=structuredClone(bound);mutate(bad);assert.throws(()=>decodeBuildVerificationForEntry(bad,value.builds[0],hash));}
assert.throws(()=>decodeBuildVerificationForEntry(bound,{...value.builds[0],change_count:1},hash));assert.throws(()=>decodeBuildVerificationForEntry(bound,value.builds[0],null));
console.log('Saved Build integrity/coverage and selected receipt/current-input binding contracts passed');
