import assert from 'node:assert/strict';
import {decodeBuildComparison} from '../editor/build-history.js';
const left='a'.repeat(16),right='b'.repeat(16),key='c'.repeat(64),value={schema_version:'legaia.build-comparison.v1',left_id:left,right_id:right,project_source_key:key,source_disc_sha256:'d'.repeat(64),integrity:'both_packages_verified',gameplay_verified:false,source_disc_integrity:'not_checked',comparison_scope:'saved_audit_records_only',unchanged_change_count:0,difference_count:1,differences:[{identity:{scene:'town01',owner_id:'actor',asset_id:'actor',field:'x',scope:'placement'},status:'only_right_audit',left:null,right:{before:0,after:64}}]};
assert.equal(decodeBuildComparison(value,left,right,key).difference_count,1);
for(const mutate of [v=>v.project_source_key='e'.repeat(64),v=>v.gameplay_verified=true,v=>v.integrity='unchecked',v=>v.comparison_scope='runtime',v=>v.difference_count=2,v=>v.differences[0].left={},v=>v.differences[0].right=null]){const bad=structuredClone(value);mutate(bad);assert.throws(()=>decodeBuildComparison(bad,left,right,key));}
console.log('Saved Build comparison scope, integrity and stale contracts passed');
