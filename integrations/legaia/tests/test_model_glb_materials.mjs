import assert from 'node:assert/strict';
import {decodeModelGlbBinding,decodeModelGlbReview} from '../editor/model-glb.js';

const h=x=>x.repeat(64),assetId='asset://town01/models/scene-tmd/0000';
const context={projectPath:'C:/private/material-test',sceneId:'scene://town01',mode:'edit',sourceKey:h('f')};
const binding=()=>({schema_version:'legaia.model-glb-binding.v1',asset_id:assetId,scene_id:context.sceneId,
  source_sha256:h('a'),effective_sha256:h('b'),project_source_key:context.sourceKey,
  profile:{schema_version:'legaia.model-glb-profile.v6',attributes:{material:'_LEGAIA_SOURCE_MATERIAL'},
    imported_fields:['primitive_material_words']}});
const material=(field,at,before,after)=>({kind:'primitive',object_index:0,primitive_index:0,group_index:0,
  field,byte_offset:at,before_value:before,after_value:after});
const abe=()=>({kind:'primitive_group',object_index:0,group_index:0,field:'gpu_mode',byte_offset:47,
  before_value:0x27,after_value:0x25,primitive_indices:[0,1]});
const report=()=>({schema_version:'legaia.model-glb-review.v1',asset_id:assetId,scene_id:context.sceneId,
  source_sha256:h('a'),effective_sha256:h('b'),proposed_sha256:h('c'),glb_sha256:h('d'),
  project_source_key:context.sourceKey,changes:[material('clut',54,0x8123,0x8124),material('tpage',58,0xe041,0xe051),abe()],
  pending_changes:[material('clut',54,0x8123,0x8124),material('tpage',58,0xe041,0xe051),abe()],
  quantization:{vertex_max_error:0,uv_max_error:0,color_max_error:0,normal_max_error:0,quantized_component_count:0},
  limitations:['Existing qualified CLUT, TPage and group ABE masks only.'],review_key:h('e'),project_changed:false,gameplay_verified:false});

const value=report(),before=JSON.stringify(value);
assert.equal(decodeModelGlbBinding(binding(),assetId,context).profile.schema_version,'legaia.model-glb-profile.v6');
assert.deepEqual(decodeModelGlbReview(value,binding(),assetId,context,h('d')).pending_changes,value.pending_changes);
assert.equal(JSON.stringify(value),before,'Material review remains read-only.');
for(const mutate of [
  r=>r.pending_changes[0].after_value=0x124, // CLUT reserved bit15.
  r=>r.pending_changes[1].after_value=0xe061, // Caller ABR bits.
  r=>r.pending_changes[1].after_value=0xc041, // TPage opaque bits.
  r=>r.pending_changes[1].after_value=65536,
  r=>r.pending_changes[1].after_value=0xe051+.5,
  r=>r.pending_changes[2].after_value=0x23,
  r=>r.pending_changes[2].primitive_indices=[0,0],
  r=>r.pending_changes[2].primitive_indices=[],
  r=>r.pending_changes[2].field='command',
  r=>r.pending_changes[0].field='texture',
  r=>r.pending_changes[0].corner_index=0,
  r=>r.pending_changes[1].byte_offset=54,
  r=>r.pending_changes[0].after_value=NaN,
  r=>r.project_changed=true,
]){const candidate=report();mutate(candidate);assert.throws(()=>decodeModelGlbReview(candidate,binding(),assetId,context,h('d')));}
for(const version of [1,2,3,4,5]){
  const old=binding();old.profile.schema_version=`legaia.model-glb-profile.v${version}`;
  assert.throws(()=>decodeModelGlbBinding(old,assetId,context),'SDK binding requires a fresh material-capable export.');
}
console.log('v6 GLB material review admits qualified masks and shared ABE; reserved bits, malformed aliases, stale bindings and mutation claims reject.');
