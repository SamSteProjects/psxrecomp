import assert from 'node:assert/strict';
import {decodeWallPattern,captureWallPattern,transformWallPattern,wallPatternDraft,repeatWallPattern} from '../editor/wall-pattern.js';
const rectangle={row_start:15,row_end:15,column_start:20,column_end:21,quadrant:'all',blocked:'current'},edits=[{row:15,column:20,quadrant:0,blocked:true},{row:15,column:20,quadrant:1,blocked:false},{row:15,column:21,quadrant:2,blocked:'retail'}];
const held=structuredClone({rectangle,edits}),pattern=captureWallPattern(rectangle,edits);
assert.deepEqual(pattern,{schema_version:'legaia.wall-pattern.v1',width_subcells:4,height_subcells:2,cells:[{x:0,z:0,blocked:true},{x:1,z:0,blocked:false},{x:2,z:1,blocked:'retail'}]});
assert.deepEqual(wallPatternDraft(pattern,15,20),{rectangle,cell_edits:edits});
assert.deepEqual(transformWallPattern(pattern,1).cells,[{x:1,z:0,blocked:true},{x:1,z:1,blocked:false},{x:0,z:2,blocked:'retail'}]);
assert.deepEqual(wallPatternDraft(transformWallPattern(pattern,1),40,50),{rectangle:{row_start:40,row_end:41,column_start:50,column_end:50,quadrant:'all',blocked:'current'},cell_edits:[{row:40,column:50,quadrant:1,blocked:true},{row:40,column:50,quadrant:3,blocked:false},{row:41,column:50,quadrant:0,blocked:'retail'}]});
assert.deepEqual(transformWallPattern(transformWallPattern(pattern,2),2),pattern);
assert.deepEqual(transformWallPattern(transformWallPattern(pattern,0,true),0,true),pattern);
assert.deepEqual(transformWallPattern(transformWallPattern(pattern,0,false,true),0,false,true),pattern);
assert.deepEqual(transformWallPattern(pattern,0,true).cells,[{x:2,z:0,blocked:false},{x:3,z:0,blocked:true},{x:1,z:1,blocked:'retail'}]);
assert.equal(captureWallPattern({...rectangle,blocked:true},[edits[1]]).cells.length,8);assert.equal(captureWallPattern({...rectangle,blocked:'retail'},[]).cells.filter(c=>c.blocked==='retail').length,8);
assert.equal(captureWallPattern({...rectangle,quadrant:0,blocked:true},[]).cells.length,2);
for(const change of [v=>v.extra=true,v=>v.width_subcells=3,v=>v.height_subcells=258,v=>v.cells=[],v=>v.cells.push(v.cells[0]),v=>v.cells[0].x=4,v=>v.cells[0].blocked='current',v=>v.cells[0].extra=true]){const v=structuredClone(pattern);change(v);assert.throws(()=>decodeWallPattern(v));}
for(const coords of [[0,20],[1,-1],[127,20],[15,128],[true,1]])assert.throws(()=>wallPatternDraft(transformWallPattern(pattern,1),...coords));
assert.throws(()=>captureWallPattern(rectangle,[]));assert.throws(()=>captureWallPattern(rectangle,[{...edits[0],row:16}]));assert.throws(()=>transformWallPattern(pattern,4));assert.throws(()=>transformWallPattern(pattern,0,1));
assert.deepEqual({rectangle,edits},held);const decoded=decodeWallPattern(pattern);decoded.cells[0].blocked=false;assert.equal(pattern.cells[0].blocked,true);
console.log('Portable wall patterns preserve operations, exact quadrant transforms, uniform fills, detached input and bounded destination staging.');

const singleQuadrant=captureWallPattern({row_start:1,row_end:64,column_start:0,column_end:63,quadrant:0,blocked:true},[]);assert.equal(singleQuadrant.cells.length,4096);assert.equal(wallPatternDraft(singleQuadrant,1,0).rectangle.quadrant,0);assert.equal(wallPatternDraft(transformWallPattern(singleQuadrant,1),1,0).rectangle.quadrant,1);
assert.throws(()=>wallPatternDraft({...pattern,width_subcells:256,height_subcells:256},1,0));
console.log('Patterns preserve the existing 4096-bit single-quadrant selection budget through rotation.');

const serialized=JSON.stringify(singleQuadrant,null,2);assert(Buffer.byteLength(serialized,'utf8')<=512*1024);assert.deepEqual(decodeWallPattern(JSON.parse(serialized)),singleQuadrant);console.log('Maximum 4096-operation download round-trips within the file budget.');

const repeatInput=structuredClone(pattern),repeated=repeatWallPattern(pattern,2,3,1,2);
assert.equal(repeated.width_subcells,10);assert.equal(repeated.height_subcells,14);assert.equal(repeated.cells.length,18);
for(let z=0;z<3;z++)for(let x=0;x<2;x++)for(const cell of pattern.cells)assert(repeated.cells.some(c=>c.x===cell.x+6*x&&c.z===cell.z+6*z&&c.blocked===cell.blocked));
const repeatDraft=wallPatternDraft(repeated,10,20);assert.equal(repeatDraft.rectangle.row_end,16);assert.equal(repeatDraft.rectangle.column_end,24);assert.equal(repeatDraft.cell_edits.length,18);assert(!repeatDraft.cell_edits.some(c=>c.column===22));assert(!repeatDraft.cell_edits.some(c=>c.row===11||c.row===12));
assert.deepEqual(pattern,repeatInput);assert.deepEqual(repeatWallPattern(pattern),pattern);
for(const args of [[0,1],[1,true],[2,1,-1],[2,1,1.5],[128,1],[1,128],[2,2,127,126]])assert.throws(()=>repeatWallPattern(pattern,...args));
assert.throws(()=>repeatWallPattern(singleQuadrant,2,1));
const sparse=decodeWallPattern({schema_version:'legaia.wall-pattern.v1',width_subcells:2,height_subcells:2,cells:[{x:0,z:0,blocked:true}]});
assert.throws(()=>repeatWallPattern(sparse,2,2,100,100)); // Extent budget applies even to four authored operations.
assert.throws(()=>wallPatternDraft(repeated,122,124));
assert.deepEqual(transformWallPattern(repeatWallPattern(pattern,2,3,1,2),1),repeatWallPattern(transformWallPattern(pattern,1),3,2,2,1));
console.log('Repeated patterns preserve all operations and quadrant parity, leave gaps untouched, and reject count, extent, operation and destination overflow.');
