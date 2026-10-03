import assert from 'node:assert/strict';
import {sourceNormalMatrix,sourceNormalColor,sourceNormalDirection,qualifySourceNormals} from '../editor/source-normal-view.js';
const identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const close=(a,b)=>{assert.equal(a.length,b.length);a.forEach((v,i)=>assert.ok(Math.abs(v-b[i])<1e-12,`${v} != ${b[i]}`));};
close(sourceNormalMatrix(identity),[1,0,0,0,1,0,0,0,1]);
close(sourceNormalColor([4096,0,0],sourceNormalMatrix(identity)),[1,.5,.5]);
const reflection=[1,0,0,12,0,-1,0,34,0,0,1,56,0,0,0,1];
close(sourceNormalColor([0,4096,0],sourceNormalMatrix(reflection)),[.5,0,.5]);
const yaw=[0,0,1,0,0,-1,0,0,-1,0,0,0,0,0,0,1];
close(sourceNormalColor([4096,0,0],sourceNormalMatrix(yaw)),[.5,.5,0]);
const scale=[2,0,0,0,0,4,0,0,0,0,8,0,0,0,0,1];
close(sourceNormalMatrix(scale),[.5,0,0,0,.25,0,0,0,.125]);
const length=Math.sqrt(.25+.0625+.015625);
close(sourceNormalColor([1,1,1],sourceNormalMatrix(scale)),[.5+.25/length,.5+.125/length,.5+.0625/length]);
assert.equal(sourceNormalMatrix([1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1]),null);
for(const [raw,matrix,status] of [[null,sourceNormalMatrix(identity),'unavailable'],[[0,0,0],sourceNormalMatrix(identity),'zero'],[[1,0,0],null,'singular']]){
  assert.equal(sourceNormalDirection(raw,matrix).status,status);close(sourceNormalColor(raw,matrix),[.5,.5,.5]);
}
const preview={posed:false,triangles:[[0,1,2]],triangle_normals:[[[1,0,0],[0,1,0],[0,0,1]]],normal_preview:{coordinate_system:'retail_tmd_object_local',status:'source_unposed'}};
assert.equal(qualifySourceNormals(preview),true);
assert.equal(qualifySourceNormals({...preview,triangle_normals:[null]}),true);
for(const delta of [{posed:true},{frames:[{}]}])assert.equal(qualifySourceNormals({...preview,...delta}),false);
for(const delta of [{normal_preview:{status:'other',coordinate_system:'retail_tmd_object_local'}},{triangle_normals:[]},{triangle_normals:[[[32768,0,0],[0,1,0],[0,0,1]]]},{triangle_normals:[[[1.5,0,0],[0,1,0],[0,0,1]]]},{triangle_normals:[[[1,0,0]]]}])assert.throws(()=>qualifySourceNormals({...preview,...delta}));
for(const bad of [[],identity.map((v,i)=>i===2?NaN:v),identity.map((v,i)=>i===15?0:v)])assert.throws(()=>sourceNormalMatrix(bad));
assert.equal(qualifySourceNormals({triangles:preview.triangles}),false);
console.log('Source normal direction: inverse transpose, one Y reflection, yaw, nonuniform scale, singular/zero/unavailable and static qualification guards passed.');
