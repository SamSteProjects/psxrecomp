import assert from 'node:assert/strict';
import {scaleObjectWords,qualifyObjectAxisScale} from '../editor/model-object-axis-scale.js';
const object={vertices:[[0,0,0],[1,0,0],[0,1,0]],normals:[[1000,1000,0],[0,0,0]]},before=structuredClone(object),values={percents:[200,100,100],pivot:'center'},proposed=scaleObjectWords(object,values);
assert.deepEqual(proposed,{vertices:[[-1,0,0],[2,0,0],[-1,1,0]],normals:[[632,1265,0],[0,0,0]]});assert.deepEqual(object,before);assert.deepEqual(scaleObjectWords(object,{percents:[100,100,100],pivot:'center'}),object);
assert.deepEqual(scaleObjectWords({...object,normals:[]},values).normals,[]);
for(const bad of [{percents:[true,100,100]},{percents:[0,100,100]},{percents:[1001,100,100]},{percents:[100,100]},{percents:new Array(3)},{pivot:'bad'}])assert.throws(()=>scaleObjectWords(object,{...values,...bad}));
assert.throws(()=>scaleObjectWords({...object,normals:[[32767,32767,32767]]},{percents:[1,1000,1000],pivot:'origin'}));assert.throws(()=>scaleObjectWords({...object,vertices:[[32767,0,0]]},{...values,pivot:'origin'}));
const report={values,object_index:0,object_axis_scale_words:{current:object,proposed},current_preview:{triangles:[[0,1,2]]},preview:{triangles:[[0,1,2]]},changes_from_current:[{kind:'vertex',object_index:0},{kind:'normal',object_index:0}]};assert.deepEqual(qualifyObjectAxisScale(report,object,values),proposed);
for(const mutate of [r=>r.values.pivot='origin',r=>r.object_axis_scale_words.proposed.normals[0][0]++,r=>r.object_axis_scale_words.current.vertices[0][0]++,r=>r.preview.triangles=[],r=>r.changes_from_current[0].kind='material',r=>r.changes_from_current[0].object_index=1]){const forged=structuredClone(report);mutate(forged);assert.throws(()=>qualifyObjectAxisScale(forged,object,values));}
console.log('Object scale pivot, inverse transpose literal words, zero/uniform normals, overflow, immutable inputs and proposal guards passed.');
