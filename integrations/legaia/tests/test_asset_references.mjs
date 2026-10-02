import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const code=await readFile(new URL('../editor/asset-references.js',import.meta.url),'utf8');
const {decodeAssetReferences}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const hash='a'.repeat(64),root='scene://fixture',actor=root+'/actors/0001';
const value={schema_version:'legaia.asset-references.v1',asset_id:root,source_key:hash,read_only:true,nodes:[{id:root,kind:'scene',scene_id:root,label:'Fixture',available:true},{id:actor,kind:'actor',scene_id:root,label:'Actor 0001',available:true}],incoming:[],outgoing:[{id:'b'.repeat(64),source_id:root,target_id:actor,kind:'scene_actor',scene_id:root,layer:'imported',runtime_binding:'not_asserted',source_import_sha256:hash}],coverage:{verified_scene_ids:[root],resource_scene_id:root,unresolved_reference_count:1},limitations:['Recorded source only']};
const result=decodeAssetReferences(value,root,hash);result.nodes[0].label='Detached';assert.equal(value.nodes[0].label,'Fixture');
for(const mutate of [v=>v.read_only=false,v=>v.source_key='c'.repeat(64),v=>v.nodes.push(v.nodes[0]),v=>v.outgoing[0].target_id='missing',v=>v.outgoing[0].runtime_binding='confirmed',v=>v.outgoing[0].layer='live',v=>v.outgoing[0].kind='inferred_model',v=>v.coverage.verified_scene_ids=[],v=>v.nodes[1].scene_id='scene://missing',v=>v.outgoing[0].pc=-1,v=>v.outgoing[0].layer='decoded']){const bad=structuredClone(value);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,root,hash));}
console.log('asset reference decoder: bounded source contract, detached output and invalid records passed');
