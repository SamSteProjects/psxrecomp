import assert from 'node:assert/strict';
import {normalAngleUnits,rotateStoredNormals,qualifyNormalRotation} from '../editor/model-normal-rotation.js';
const words=[[1000,0,0],[0,0,0],[-4096,0,0]],before=structuredClone(words);
assert.deepEqual(rotateStoredNormals(words,'y',512),[[707,0,-707],[0,0,0],[-2896,0,2896]]);assert.deepEqual(words,before);
assert.deepEqual(rotateStoredNormals(words,'z',1024),[[0,1000,0],[0,0,0],[0,-4096,0]]);
assert.deepEqual(rotateStoredNormals(words,'x',0),words);
assert.equal(normalAngleUnits(45),512);assert.equal(normalAngleUnits(-90),3072);assert.equal(normalAngleUnits(360),0);assert.equal(normalAngleUnits(-360),0);
for(const value of [NaN,Infinity,'45',null,361,-361])assert.throws(()=>normalAngleUnits(value));
for(const [rows,axis,angle] of [[[],'x',0],[words,'w',512],[words,'y',4096],[words,'y',true],[[[32767,32767,0]],'z',512],[Array(1),'y',512],[[[0,0]],'y',512]])assert.throws(()=>rotateStoredNormals(rows,axis,angle));
const values={axis:'y',angle_units:512},report={object_index:0,values,normal_rotation_words:{current:words,proposed:rotateStoredNormals(words,'y',512)},preview:{vertices:[[0,0,0]],triangles:[]},current_preview:{vertices:[[0,0,0]],triangles:[]},changes_from_current:[{kind:'normal',object_index:0}]};
assert.deepEqual(qualifyNormalRotation(report,words,values),report.normal_rotation_words.proposed);
for(const change of [r=>r.values.angle_units=513,r=>r.normal_rotation_words.current[0][0]++,r=>r.normal_rotation_words.proposed[0][2]++,r=>r.preview.vertices[0][0]++,r=>r.changes_from_current[0].kind='vertex',r=>r.changes_from_current[0].object_index=1]){const bad=structuredClone(report);change(bad);assert.throws(()=>qualifyNormalRotation(bad,words,values));}
console.log('Stored normal rotation: native cardinal/custom words, zero preservation, bounded angle/rows, overflow, immutable source, exact local review and no geometry changes passed.');
