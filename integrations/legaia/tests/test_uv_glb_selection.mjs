import assert from 'node:assert/strict';
import {uvSelectionDrafts} from '../editor/uv-rectangle.js';
import {primitiveGlbSelectionSource} from '../editor/model-glb-material-selection.js';
const row=(i,g=0)=>({primitive_index:i,group_index:g,flags:0x20,vertices:[0,1,2],uvs:[[0,0],[255,255],[128,64]],colors:[[10,20,30]],normal_indices:null});
const source={asset_id:'asset://fixture/model/0',project_source_key:'a'.repeat(64),effective_sha256:'b'.repeat(64),objects:[{primitives:[row(0),row(1,1)]},{primitives:[row(0)]}]};
const face=(o,i,g=0)=>({object_index:o,primitive_index:i,group_index:g,textured:true,material_indices:[2]});
const selection={...source,can_stage:true,material_index:2,faces:[face(0,0),face(1,0)]};
const existing=[{object_index:0,primitive_index:0,vertices:[2,1,0],uvs:[[1,1],[1,1],[1,1]],colors:[[99,20,30]]},{object_index:0,primitive_index:1,vertices:[1,0,2],uvs:[[1,2],[3,4],[5,6]],colors:[[33,44,55]]}],before=structuredClone({source,selection,existing});
const result=uvSelectionDrafts(source,selection,[0,0,255,255],[16,32,80,160],existing);
assert.equal(result.length,3);assert.deepEqual(result[0].vertices,existing[0].vertices);assert.deepEqual(result[0].colors,existing[0].colors);assert.deepEqual(result[0].uvs,[[16,32],[80,160],[48,64]]);assert.deepEqual(result[1],existing[1]);assert.deepEqual(result[2].uvs,result[0].uvs);assert.deepEqual(result[2].vertices,[0,1,2]);assert.deepEqual({source,selection,existing},before);
for(const change of [s=>s.project_source_key='c'.repeat(64),s=>s.effective_sha256='c'.repeat(64),s=>s.can_stage=false,s=>s.faces[0].group_index=1,s=>s.faces[0].material_indices=[2,3],s=>s.faces.push(s.faces[0])]){const bad=structuredClone(selection);change(bad);assert.throws(()=>uvSelectionDrafts(source,bad,[0,0,255,255],[0,0,128,128],existing));}
assert.throws(()=>uvSelectionDrafts(source,selection,[0,0,100,100],[0,0,255,255],existing));assert.deepEqual({source,selection,existing},before);
const adapted=primitiveGlbSelectionSource(source,{sourceKey:source.project_source_key,sceneId:'scene://fixture'});assert.equal(adapted.scene_id,'scene://fixture');assert.deepEqual(adapted.objects[0].groups[1].primitives,[{primitive_index:1,textured:true}]);assert.equal(adapted.objects[1].groups[0].flags,0x20);assert.throws(()=>primitiveGlbSelectionSource(source,{sourceKey:'stale',sceneId:'scene://fixture'}));
console.log('Qualified UV face set, cross-object identities, existing drafts and atomic rejection passed.');
