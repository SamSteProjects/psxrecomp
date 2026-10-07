import assert from 'node:assert/strict';
import {decodeMeshAnimationCatalog} from '../editor/mesh-animation-catalog.js';
const hash='a'.repeat(64),value={schema_version:'legaia.model-mesh-animation-catalog.v1',glb_sha256:hash,byte_length:100,node_count:2,clips:[{animation_index:0,name:'Walk <source>',channel_count:1,sampler_count:1,target_nodes:[1],target_paths:['translation']}],payloads_decoded:false,sampling_qualified:false,project_changed:false};
const result=decodeMeshAnimationCatalog(value,hash,100);result.clips[0].name='Changed';assert.equal(value.clips[0].name,'Walk <source>');
let refused=0;
for(const mutate of [v=>v.glb_sha256='b'.repeat(64),v=>v.byte_length=101,v=>v.payloads_decoded=true,v=>v.sampling_qualified=true,v=>v.project_changed=true,v=>v.extra=true,v=>v.clips[0].animation_index=1,v=>v.clips[0].name=123,v=>v.clips[0].target_nodes=[true],v=>v.clips[0].target_nodes=[2],v=>v.clips[0].target_paths=['unknown'],v=>v.clips[0].channel_count=0]){const bad=structuredClone(value);mutate(bad);assert.throws(()=>decodeMeshAnimationCatalog(bad,hash,100));refused++;}
decodeMeshAnimationCatalog({...value,clips:[]},hash,100);
console.log(JSON.stringify({detached_catalog:true,empty_catalog:true,forged_refusals:refused}));
