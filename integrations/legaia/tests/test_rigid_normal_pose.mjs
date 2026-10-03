import assert from 'node:assert/strict';
import {rigidFrameNormals,qualifySourceNormals,sourceNormalMatrix} from '../editor/source-normal-view.js';
import {SceneRenderer} from '../editor/scene-renderer.js';
const near=(a,b)=>a.forEach((v,i)=>assert.ok(Math.abs(v-b[i])<1e-8,`${v} != ${b[i]}`));
const source={posed:false,vertices:[[0,0,0],[1,0,0],[0,1,0],[4,0,0],[5,0,0],[4,1,0]],triangles:[[0,1,2],[3,4,5]],triangle_normals:[[[4096,0,0],[0,4096,0],[0,0,0]],null],objects:[{object_index:0,vertex_start:0,vertex_count:3,triangle_start:0,triangle_count:1},{object_index:1,vertex_start:3,vertex_count:3,triangle_start:1,triangle_count:1}],normal_preview:{status:'source_unposed',coordinate_system:'retail_tmd_object_local'},frames:[{}]};
const frame={posed:true,coordinate_system:'retail_psx_actor_local_y_down',object_transforms:[{object_index:0,rotation_psx:[1024,1024,1024],translation:[100,-200,300]},{object_index:1,rotation_psx:[0,0,0],translation:[0,0,0]}]};
const snapshot=JSON.stringify({source,frame}),posed=rigidFrameNormals(source,frame);
// Independent quarter-turn axes: X -> -Z; Y -> +Y after Rx, Ry, Rz.
near(posed.triangle_normals[0][0],[0,0,-4096]);near(posed.triangle_normals[0][1],[0,4096,0]);near(posed.triangle_normals[0][2],[0,0,0]);assert.equal(posed.triangle_normals[1],null);
assert.equal(qualifySourceNormals({...posed,triangles:source.triangles}),true);
assert.equal(qualifySourceNormals({...posed,triangles:source.triangles,posed:false}),false);
assert.equal(qualifySourceNormals({...posed,triangles:source.triangles,frames:[{}]}),false);
assert.equal(JSON.stringify({source,frame}),snapshot);
const untranslated=structuredClone(frame);untranslated.object_transforms.forEach(c=>c.translation=[0,0,0]);assert.deepEqual(rigidFrameNormals(source,untranslated).triangle_normals,posed.triangle_normals);
const identity=structuredClone(frame);identity.object_transforms.forEach(c=>c.rotation_psx=[0,0,0]);assert.deepEqual(rigidFrameNormals(source,identity).triangle_normals,source.triangle_normals);
const yDown=sourceNormalMatrix([1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]);near([0,1,2].map(r=>posed.triangle_normals[0][1].reduce((sum,v,c)=>sum+yDown[r*3+c]*v,0)),[0,-4096,0]);
for(const mutate of [s=>s.posed=true,s=>s.objects.pop(),s=>s.objects[1].object_index=0,s=>s.objects[1].vertex_start=2,s=>s.objects[1].triangle_start=0,s=>s.objects[1].triangle_count=0,s=>s.triangles[0][1]=3,s=>s.triangle_normals[0][0][0]=1.5]){const bad=structuredClone(source);mutate(bad);assert.throws(()=>rigidFrameNormals(bad,frame));}
for(const mutate of [f=>f.posed=false,f=>f.coordinate_system='unknown',f=>f.object_transforms[0].object_index=2,f=>f.object_transforms[0].rotation_psx[0]=4096,f=>f.object_transforms[0].rotation_psx[0]=NaN,f=>f.object_transforms[0].rotation_psx[0]=.5,f=>f.object_transforms[0].translation[0]=Infinity]){const bad=structuredClone(frame);mutate(bad);assert.throws(()=>rigidFrameNormals(source,bad));}
for(const mutate of [p=>p.normal_preview.transform='other',p=>p.normal_preview.coordinate_system='other',p=>p.triangle_normals[0][0][0]=Infinity,p=>p.triangle_normals[0][0]=[60000,0,0]]){const bad=structuredClone({...posed,triangles:source.triangles});mutate(bad);assert.throws(()=>qualifySourceNormals(bad));}
// Renderer updates both streams in-place, with complete validation before writes.
const calls=[],gl={ARRAY_BUFFER:1,DYNAMIC_DRAW:2,bindBuffer:()=>{},bufferSubData:(_,__,data)=>calls.push([...data]),createBuffer:()=>{throw new Error('Unexpected allocation');}};
const batch={buffer:1,normalBuffer:2,data:new Float32Array(6*8),vertexIndices:[0,1,2,3,4,5],normalCorners:[[0,0],[0,1],[0,2],[1,0],[1,1],[1,2]]};
const mesh={vertexCount:6,triangles:source.triangles,batches:[batch]},renderer={meshes:new Map([['test',mesh]]),gl,scene:{assets:[{geometry_key:'test',preview:source}]}};
const update=(vertices,normals)=>SceneRenderer.prototype.updateVertices.call(renderer,'test',vertices,normals);
const payload={...posed,triangles:source.triangles};assert.equal(update(source.vertices,payload),true);assert.equal(mesh.normalQualified,true);assert.equal(calls.length,2);near(calls[1].slice(0,3),[0,0,-4096]);assert.deepEqual(calls[1].slice(6),new Array(12).fill(0));
const before=[...batch.data],count=calls.length;assert.throws(()=>update(source.vertices,{...payload,triangles:[[0,2,1],[3,4,5]]}));assert.deepEqual([...batch.data],before);assert.equal(calls.length,count);
assert.throws(()=>update([[NaN,0,0],...source.vertices.slice(1)],payload));assert.equal(calls.length,count);
assert.throws(()=>update(source.vertices,{...source,frames:undefined}));assert.equal(calls.length,count);
assert.equal(update(source.vertices),true);assert.equal(mesh.normalQualified,false);assert.equal(calls.length,count+1);
assert.equal(renderer.scene.assets[0].preview.normal_preview,undefined);assert.equal(qualifySourceNormals(renderer.scene.assets[0].preview),false);
console.log('Rigid normals: rotation order, translation exclusion, neutral corners, one Y reflection, channel/span guards, immutable sources and validated in-place renderer updates passed.');
