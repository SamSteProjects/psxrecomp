import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {decodeMeshSources,qualifyMeshSourceDownload,openMeshSources} from '../editor/model-mesh-sources.js';
const asset='asset://town01/models/scene-tmd/0009',key='a'.repeat(64),bytes=Buffer.alloc(32,17);
const record={schema_version:'legaia.model-mesh-source.v1',asset_id:asset,glb_sha256:createHash('sha256').update(bytes).digest('hex'),byte_length:bytes.length,first_operation:0,operation_count:2,operations_sha256:'b'.repeat(64),input_sha256:'c'.repeat(64),proposed_sha256:'d'.repeat(64),receipt_key:'e'.repeat(64),recipe:{kind:'single',material_colors:false,scene_index:null,uv_set:0,source_scale:1,source_offset:[0,0,0],source_rotation:[0,0,0],donor_face_id:'face://fixture/0',new_group:true,replace_group:false,replace_object:false,preserve_primitives:false,primitive_index:null}};
const value=()=>({schema_version:'legaia.model-mesh-sources.v1',asset_id:asset,project_source_key:key,imports:[structuredClone(record)],project_changed:false,selected:structuredClone(record),content_base64:bytes.toString('base64')});
const original=value(),decoded=decodeMeshSources(original,asset,key);decoded.imports[0].recipe.source_offset[0]=99;assert.equal(original.imports[0].recipe.source_offset[0],0);
for(const change of [v=>v.project_changed=true,v=>v.imports.push(v.imports[0]),v=>v.imports[0].operation_count=0,v=>v.imports[0].first_operation=-1,v=>v.imports[0].input_sha256='bad',v=>v.imports[0].recipe.extra=true]){const changed=value();change(changed);assert.throws(()=>decodeMeshSources(changed,asset,key));}
const result=await qualifyMeshSourceDownload(value(),asset,key,record,()=>true);assert.deepEqual(Buffer.from(result.bytes),bytes);result.record.recipe.source_offset[0]=88;assert.equal(record.recipe.source_offset[0],0);
for(const change of [v=>v.selected.recipe.source_scale=2,v=>v.imports[0].recipe.source_scale=2,v=>v.selected.receipt_key='f'.repeat(64),v=>v.content_base64=Buffer.alloc(32,18).toString('base64'),v=>v.content_base64+='AAAA',v=>v.content_base64='invalid!']){const changed=value();change(changed);await assert.rejects(qualifyMeshSourceDownload(changed,asset,key,record,()=>true));}
let checks=0;await assert.rejects(qualifyMeshSourceDownload(value(),asset,key,record,()=>++checks===1),'Context change during hashing must reject publication.');
class Node{constructor(){this.children=[];this.style={};this.removed=false;this.disabled=false;}get isConnected(){return !this.removed;}append(...nodes){this.children.push(...nodes);}showModal(){this.open=true;}close(){this.open=false;this.onclose?.();}remove(){this.removed=true;}click(){this.onclick?.();}}
const oldDocument=globalThis.document,oldFetch=globalThis.fetch,oldCreate=URL.createObjectURL,oldRevoke=URL.revokeObjectURL;
const nodes=[],requests=[],downloads=[],blobs=[];let finish,signal;
globalThis.document={body:new Node(),createElement:tag=>{const node=new Node();node.tag=tag;if(tag==='a')node.click=()=>downloads.push(node.download);nodes.push(node);return node;}};
try{
 globalThis.fetch=(_route,request)=>{signal=request.signal;return new Promise(resolve=>finish=resolve);};
 const pending=openMeshSources({assetId:asset,key,current:()=>true,onError:()=>assert.fail('Closed read reported an error.')});
 const closed=nodes.find(n=>n.tag==='dialog');closed.close();assert.equal(signal.aborted,true);finish({ok:true,json:async()=>value()});assert.equal(await pending,closed);assert.equal(closed.removed,true);
 nodes.length=0;let active=true;globalThis.fetch=async()=>({ok:true,json:async()=>{active=false;return value();}});const stale=await openMeshSources({assetId:asset,key,current:()=>active,onError:()=>assert.fail('A superseded read notified a later context.')});assert.match(nodes.find(n=>n.role==='status').textContent,/context changed/);stale.close();
 nodes.length=0;globalThis.fetch=async(route,request)=>{requests.push({route,body:JSON.parse(request.body)});return {ok:true,json:async()=>value()};};
 URL.createObjectURL=blob=>{blobs.push(blob);return 'blob:fixture';};URL.revokeObjectURL=()=>{};
 const dialog=await openMeshSources({assetId:asset,key,current:()=>true,onError:error=>assert.fail(error.message)});
 for(const label of ['Download import settings JSON','Download import receipt','Download original GLB'])await nodes.find(n=>n.textContent===label).onclick();
 assert.equal(requests.filter(r=>r.route==='/api/model-mesh-source-download').length,3,'Every artifact must qualify the native receipt and original bytes again.');
 assert.equal(JSON.parse(await blobs[0].text()).kind,'single');assert.deepEqual(JSON.parse(await blobs[1].text()),record);assert.deepEqual(Buffer.from(await blobs[2].arrayBuffer()),bytes);
 assert.deepEqual(downloads,[`${record.receipt_key}.settings.json`,`${record.receipt_key}.receipt.json`,`${record.glb_sha256}.glb`]);
 let resolveDownload,downloadSignal,pendingCalls=0;globalThis.fetch=(_route,request)=>{pendingCalls++;downloadSignal=request.signal;return new Promise(resolve=>resolveDownload=resolve);};
 const delayed=nodes.find(n=>n.textContent==='Download import settings JSON').onclick();await nodes.find(n=>n.textContent==='Download import receipt').onclick();assert.equal(pendingCalls,1,'Concurrent artifact reads must be ignored.');dialog.close();assert.equal(downloadSignal.aborted,true);resolveDownload({ok:true,json:async()=>value()});await delayed;assert.equal(downloads.length,3);
}finally{globalThis.document=oldDocument;globalThis.fetch=oldFetch;URL.createObjectURL=oldCreate;URL.revokeObjectURL=oldRevoke;}
console.log('Mesh settings/receipt/GLB downloads requalify exact records and hashes; detached snapshots, stale hash-time context, duplicate spans and close/abort reject.');
