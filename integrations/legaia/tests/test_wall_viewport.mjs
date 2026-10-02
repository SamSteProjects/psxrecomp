import assert from 'node:assert/strict';
import {wallCellAt,wallDragRectangle,wallSelectionGeometry} from '../editor/wall-viewport.js';

for(const [x,z,expected] of [
  [Number.MIN_VALUE,0,{row:1,column:0,quadrant:0}],
  [0.5,0,{row:1,column:0,quadrant:0}],
  [64,63.5,{row:1,column:0,quadrant:0}],
  [64.001,63.5,{row:1,column:0,quadrant:1}],
  [64,64,{row:1,column:0,quadrant:2}],
  [128,64,{row:1,column:0,quadrant:3}],
  [128,128,{row:2,column:0,quadrant:1}],
  [128.001,128,{row:2,column:1,quadrant:0}],
  [16384,16255.5,{row:127,column:127,quadrant:3}],
])assert.deepEqual(wallCellAt({x,z}),expected);
for(const point of [null,{}, {x:0,z:0},{x:-0.5,z:0},{x:16384.01,z:0},{x:1,z:-0.01},{x:1,z:16256},
  {x:NaN,z:0},{x:Infinity,z:0},{x:1,z:-Infinity},{x:'64',z:0},{x:1,z:null}])assert.equal(wallCellAt(point),null);

const start=wallCellAt({x:2816,z:2047.5}),end=wallCellAt({x:2560.5,z:1792});
const rectangle={row_start:15,row_end:16,column_start:20,column_end:21,quadrant:'all',blocked:true};
assert.deepEqual(wallDragRectangle(start,end),rectangle);
assert.deepEqual(wallDragRectangle(end,start),rectangle);
assert.deepEqual(wallDragRectangle(start,end,{quadrant:2,blocked:false}),{...rectangle,quadrant:2,blocked:false});
assert.deepEqual(wallSelectionGeometry(rectangle),{x_min:2560,x_max:2816,z_min:1792,z_max:2048});
assert.deepEqual(wallSelectionGeometry({...rectangle,quadrant:2}),wallSelectionGeometry(rectangle));
const first={row:1,column:0,quadrant:0},limit={row:32,column:31,quadrant:3};
assert.equal(wallDragRectangle(first,limit).row_end,32);
assert.throws(()=>wallDragRectangle(first,{...limit,column:32}),/4096/);
assert.equal(wallDragRectangle(first,{row:64,column:63,quadrant:3},{quadrant:0}).row_end,64);
assert.throws(()=>wallDragRectangle(first,{row:65,column:63,quadrant:3},{quadrant:0}),/4096/);
for(const cell of [null,{...first,row:0},{...first,row:128},{...first,row:1.5},{...first,column:-1},{...first,column:128},{...first,quadrant:4},{...first,quadrant:true}]){
  assert.throws(()=>wallDragRectangle(cell,first));assert.throws(()=>wallDragRectangle(first,cell));
}
for(const options of [{quadrant:4},{quadrant:true},{blocked:1}])assert.throws(()=>wallDragRectangle(first,first,options));
assert.throws(()=>wallSelectionGeometry({...rectangle,row_start:0}));
assert.deepEqual(first,{row:1,column:0,quadrant:0});
assert.deepEqual(start,{row:16,column:21,quadrant:3});
console.log('Source wall viewport mapping, biased boundaries, drag direction and bounded selection geometry passed.');
