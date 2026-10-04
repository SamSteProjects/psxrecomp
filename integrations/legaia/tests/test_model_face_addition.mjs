import assert from 'node:assert/strict';
import {decodeFaceAdditionSource,faceAdditionRequest,decodeFaceAdditionReview,openModelFaceAddition} from '../editor/model-face-addition.js';
const key='a'.repeat(64),next='b'.repeat(64),asset='asset://fixture/model/0',id=`face://source/${key}/0/0`,newId='face://authored/00000000-0000-4000-8000-000000000001';
const face={face_id:id,origin:'source',object_index:0,group_index:0,source_primitive_index:0,current_primitive_index:0};
const preview={vertices:[[0,0,0],[1,0,0],[0,1,0]],objects:[{object_index:0,vertex_start:0,vertex_count:3,triangle_start:0,triangle_count:1}],triangles:[[0,1,2]]};
const source={schema_version:'legaia.model-face-addition-source.v1',asset_id:asset,project_source_key:key,source_sha256:key,effective_sha256:key,project_changed:false,gameplay_verified:false,objects:[{object_index:0,vertex_count:3,normal_count:0,primitives:[{primitive_index:0,group_index:0,flags:0x20,corner_count:3,vertices:[0,1,2],uvs:[[1,2],[3,4],[5,6]],colors:[[7,8,9]],normal_indices:null}]}],topology:{source_sha256:key,proposed_sha256:key,batch_count:0,authored_face_count:0,faces:[face]},preview};
const texts={vertices:'2,1,0',uvs:'1,2;3,4;5,6',colors:'7,8,9',normal_indices:''};
const request=faceAdditionRequest(source,id,texts,newId);assert.deepEqual(request.fields,{vertices:[2,1,0],uvs:[[1,2],[3,4],[5,6]],colors:[[7,8,9]]});
const detached=decodeFaceAdditionSource(source,asset,key);detached.objects.pop();assert.equal(source.objects.length,1);
for(const change of [s=>s.asset_id='wrong',s=>s.objects[0].primitives[0].vertices[0]=3,s=>s.objects[0].primitives[0].uvs[0][1]=256,s=>s.topology.faces.push(face),s=>s.topology.faces[0].face_id='wrong',s=>s.topology.faces[0].group_index=1,s=>s.topology.authored_face_count=1,s=>s.gameplay_verified=true]){const bad=structuredClone(source);change(bad);assert.throws(()=>decodeFaceAdditionSource(bad,asset,key));}
for(const bad of [{...texts,vertices:'0,1'},{...texts,vertices:'0,1,-1'},{...texts,uvs:'1,2;3,4;5,256'},{...texts,colors:'1,2'},{...texts,vertices:'0,1,NaN'}])assert.throws(()=>faceAdditionRequest(source,id,bad,newId));
const review={schema_version:'legaia.model-face-addition-review.v1',asset_id:asset,source_sha256:key,effective_sha256:key,project_source_key:key,proposed_sha256:next,requests:[request],project_changed:false,gameplay_verified:false,current_preview:structuredClone(preview),preview:{...structuredClone(preview),objects:[{...preview.objects[0],triangle_count:2}],triangles:[[0,1,2],[2,1,0]]},topology:{source_sha256:key,proposed_sha256:next,batch_count:1,authored_face_count:1,faces:[face,{face_id:newId,origin:'authored',object_index:0,group_index:0,current_primitive_index:1,donor_face_id:id}]}};
decodeFaceAdditionReview(review,source,request);
for(const change of [r=>r.requests[0].fields.vertices[0]=0,r=>r.preview.vertices[0][0]=7,r=>r.preview.objects[0].triangle_count=1,r=>r.topology.faces[0].current_primitive_index=1,r=>r.topology.faces[1].donor_face_id='wrong',r=>r.project_source_key=next,r=>r.topology.faces.push(face)]){const bad=structuredClone(review);change(bad);assert.throws(()=>decodeFaceAdditionReview(bad,source,request));}
console.log('Face addition source ownership, typed domains, detached metadata, exact request review, vector/count/identity remapping checks pass');
class Element{
  constructor(){this.children=[];this.nodes=new Map();this.style={};this.value='';}
  append(...nodes){this.children.push(...nodes);}setAttribute(){}addEventListener(){}
  querySelector(key){if(!this.nodes.has(key))this.nodes.set(key,new Element());return this.nodes.get(key);}
  showModal(){this.open=true;}close(){this.open=false;}remove(){this.removed=true;}
}
const body=new Element();globalThis.document={body,createElement:()=>new Element()};
let context={assetId:asset,sourceKey:key,mode:'edit'},busy=false,calls=[],errors=[],resolve;
const options={assetId:asset,getContext:()=>context,busy:()=>busy,setBusy:v=>{busy=v;calls.push(v);},onApplied:()=>assert.fail('Unexpected Apply'),onError:e=>errors.push(e.message)};
globalThis.fetch=()=>new Promise(r=>resolve=r);
let pending=openModelFaceAddition(options);body.children.at(-1).close();resolve({ok:true,json:async()=>source});
assert.equal(await pending,null);assert.deepEqual(calls,[true,false]);assert.equal(body.children.at(-1).removed,true);
calls=[];pending=openModelFaceAddition(options);context={...context,sourceKey:next};resolve({ok:true,json:async()=>source});assert.equal(await pending,null);assert.deepEqual(calls,[true,false]);
context={...context,sourceKey:key};busy=true;assert.equal(await openModelFaceAddition(options),null);busy=false;context={...context,mode:'live'};assert.equal(await openModelFaceAddition(options),null);context={...context,mode:'edit'};
globalThis.fetch=async()=>({ok:true,json:async()=>({...source,asset_id:'wrong'})});const tool=await openModelFaceAddition(options);assert.equal(errors.length,1);assert.equal(tool.dialog.querySelector('[data-apply]').disabled,true);tool.dispose();
console.log('Close-before-close-event, late/stale response, owned busy release, mode and error guards pass');

const deletedAuthored={...structuredClone(source),topology:{...structuredClone(source.topology),batch_count:1,authored_face_count:1,removed_face_ids:[newId]}};
decodeFaceAdditionSource(deletedAuthored,asset,key);assert.throws(()=>faceAdditionRequest(deletedAuthored,id,texts,newId));
const survivingAuthored={...structuredClone(source),topology:{...structuredClone(source.topology),batch_count:1,authored_face_count:1,removed_face_ids:[id],faces:[{face_id:newId,origin:'authored',object_index:0,group_index:0,current_primitive_index:0,donor_face_id:id}]}};
decodeFaceAdditionSource(survivingAuthored,asset,key);
for(const change of [v=>v.topology.removed_face_ids=[],v=>v.topology.removed_face_ids.push(id),v=>v.topology.authored_face_count=2]){const bad=structuredClone(survivingAuthored);change(bad);assert.throws(()=>decodeFaceAdditionSource(bad,asset,key));}
console.log('Deleted donors and historical authored budgets qualify; deleted ID reuse and forged history reject.');
