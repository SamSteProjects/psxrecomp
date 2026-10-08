import assert from 'node:assert/strict';
import {decodeStabilityChecks} from '../editor/sdk-stability-checks.js';
const job={schema_version:'legaia.stability-checks.v1',id:'12345678-1234-1234-1234-123456789012',status:'passed',scope:'synthetic_runtime_fixtures',runtime_binary_verified:false,gameplay_verified:false,project_modified:false,source_current:true,started_at:'2026-10-08T00:00:00Z',finished_at:'2026-10-08T00:01:00Z',sources:[{path:'runtime/source.c',sha256:'a'.repeat(64),size:10}],checks:['restore','audio','precompile'].map(id=>({id,title:id,status:'passed',exit_code:0,output:'passed'}))};
assert.deepEqual(decodeStabilityChecks(job),job);
for(const mutate of [v=>v.gameplay_verified=true,v=>v.runtime_binary_verified=true,v=>v.source_current=false,v=>v.checks[0].status='skipped',v=>v.checks[0].exit_code=1,v=>v.sources[0].path='../outside',v=>v.sources.push(v.sources[0]),v=>v.finished_at=null]){const bad=structuredClone(job);mutate(bad);assert.throws(()=>decodeStabilityChecks(bad));}
const detached=decodeStabilityChecks(job);detached.sources.length=0;assert.equal(job.sources.length,1);
console.log('Fresh synthetic scope, complete pass, source identity and detached receipt checks passed.');
