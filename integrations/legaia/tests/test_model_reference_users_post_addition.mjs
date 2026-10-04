import assert from 'node:assert/strict';
import {decodeNormalUsers,mountNormalUsers} from '../editor/model-normal-users.js';
import {decodeVertexUsers,mountVertexUsers} from '../editor/model-vertex-users.js';
const hash='a'.repeat(64),faceId='face://authored/00000000-0000-4000-8000-000000000001';
class Element {
  constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.value='';this.textContent='';this.disabled=false;}
  append(...nodes){this.children.push(...nodes);if(this.tagName==='select'&&!this.value)this.value=nodes[0]?.value??'';}
  replaceChildren(...nodes){this.children=[];this.append(...nodes);}
  setAttribute(name,value){this[name]=value;}
}
const tree=node=>[node,...node.children.flatMap(tree)];
const saved={document:globalThis.document,fetch:globalThis.fetch};
try{
  globalThis.document={createElement:tag=>new Element(tag)};
  for(const [noun,decode,mount] of [['normal',decodeNormalUsers,mountNormalUsers],['vertex',decodeVertexUsers,mountVertexUsers]]){
    const binding={asset_id:'asset://fixture/model/0',object_index:0,[noun+'_index']:0,expected_sha256:hash,source_key:hash};
    const row={kind:'primitive',field:noun+'_index',object_index:0,[noun+'_index']:0,primitive_index:1,group_index:0,corner_index:0,corner_count:3,byte_offset:40,sharing:noun==='normal'?'flat_all_corners':'vertex_corner',affected_corners:noun==='normal'?[0,1,2]:[0]};
    const report={schema_version:`legaia.model-${noun}-users.v2`,asset_id:binding.asset_id,object_index:0,[noun+'_index']:0,project_source_key:hash,effective_sha256:hash,source_sha256:hash,scene_id:'scene://fixture',model_byte_length:128,retail_model_byte_length:104,current_face_count:3,retail_coordinates:[0,1,2],current_coordinates:[0,3,4],retail_users:[row],current_users:[{...row,byte_offset:64}],face_mapping:[{retail_index:0,current_index:0},{retail_index:1,current_index:2}],authored_faces:[{face_id:faceId,current_index:1}],read_only:true,gameplay_verified:false,scope:`qualified_stored_${noun}_reference_operands_in_selected_object`};
    const result=decode(report,binding);result.authored_faces[0].face_id='mutated';assert.equal(report.authored_faces[0].face_id,faceId);
    for(const change of [v=>delete v.face_mapping,v=>v.authored_faces=[],v=>v.authored_faces[0].current_index=0,v=>v.authored_faces[0].face_id='face://retail/0',v=>v.authored_faces.push({...v.authored_faces[0]}),v=>v.current_face_count=4,v=>v.face_mapping[1].current_index=1,v=>v.retail_model_byte_length=20,v=>v.current_users[0].primitive_index=3]){const bad=structuredClone(report);change(bad);assert.throws(()=>decode(bad,binding));}
    const host=new Element('main'),selected=[];let live=true;
    globalThis.fetch=async()=>({ok:true,json:async()=>structuredClone(report)});
    const control=mount({host,assetId:binding.asset_id,expectedSha:hash,sourceKey:hash,getSelection:()=>({object_index:0,[noun+'_index']:0}),isCurrent:()=>live,onSelect:row=>selected.push(row)});
    await tree(host).find(node=>node.dataset[noun+'Users']!==undefined).onclick();
    assert.ok(tree(host).some(node=>node.textContent.includes('Retail face none (authored)')));
    assert.ok(tree(host).some(node=>node.textContent.includes(faceId)));
    tree(host).find(node=>node.textContent==='Inspect current face 1').onclick();assert.equal(selected.at(-1).primitive_index,1);assert.equal(selected.at(-1).face_id,faceId);
    const layer=tree(host).find(node=>node.tagName==='select');layer.value='retail';layer.onchange();
    tree(host).find(node=>node.textContent==='Inspect current face 2').onclick();assert.equal(selected.at(-1).primitive_index,2);assert.equal(selected.at(-1).face_id,undefined);
    live=false;control.refresh();assert.ok(!tree(host).some(node=>node.textContent==='Inspect current face 2'));control.close();
  }
}finally{for(const [key,value] of Object.entries(saved)){if(value===undefined)delete globalThis[key];else globalThis[key]=value;}}
console.log('Added normal/vertex reference ownership, Retail gaps, authored navigation, current indices and stale withdrawal passed.');
