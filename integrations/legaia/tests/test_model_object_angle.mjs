import assert from 'node:assert/strict';
import {rotateObjectWords,qualifyObjectAngle} from '../editor/model-object-angle.js';
const obj={vertices:[[0,0,0],[1,0,0],[0,1,0]],normals:[[1000,0,0],[0,0,0]]},before=structuredClone(obj);
assert.deepEqual(rotateObjectWords(obj,{axis:'z',angle_units:1024,pivot:'center'}),{vertices:[[1,0,0],[1,1,0],[0,0,0]],normals:[[0,1000,0],[0,0,0]]});
const values={axis:'y',angle_units:512,pivot:'origin'},proposed=rotateObjectWords(obj,values);assert.deepEqual(proposed.normals,[[707,0,-707],[0,0,0]]);assert.deepEqual(rotateObjectWords(obj,{...values,angle_units:0}),obj);assert.deepEqual(obj,before);
assert.deepEqual(rotateObjectWords({...obj,normals:[]},values).normals,[]);
for(const bad of [{axis:'bad'},{angle_units:true},{angle_units:4096},{pivot:'bad'}])assert.throws(()=>rotateObjectWords(obj,{...values,...bad}));
for(const vertices of [[],new Array(3),[[0,,0]],[[32767,0,32767]]])assert.throws(()=>rotateObjectWords({...obj,vertices},values));
assert.throws(()=>rotateObjectWords({...obj,normals:[[-32768,0,0]]},{...values,angle_units:2048}));
const report={values,object_index:0,object_rotation_words:{current:obj,proposed},current_preview:{triangles:[[0,1,2]]},preview:{triangles:[[0,1,2]]},changes_from_current:[{kind:'vertex',object_index:0},{kind:'normal',object_index:0}]};assert.deepEqual(qualifyObjectAngle(report,obj,values),proposed);
for(const mutate of [r=>r.values.pivot='center',r=>r.object_rotation_words.proposed.normals[0][0]++,r=>r.object_rotation_words.current.vertices[0][0]++,r=>r.preview.triangles=[],r=>r.changes_from_current[0].kind='material',r=>r.changes_from_current[0].object_index=1]){const forged=structuredClone(report);mutate(forged);assert.throws(()=>qualifyObjectAngle(forged,obj,values));}
console.log('Object angle exact pivot words, normal direction, immutable rows, overflow and forged proposal guards passed.');
