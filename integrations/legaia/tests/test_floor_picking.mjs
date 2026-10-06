import assert from 'node:assert/strict';
import {nativeFloorSelectorAtTriangle} from '../editor/floor-picking.js';
const geometry={asset_id:'environment://fixture/field-map/ground',preview:{coordinate_system:'retail_field_y_down',cells:[{cell_index:0,vertex_start:0}],vertices:[[0,0,0],[128,0,0],[0,0,128],[128,0,128]],vertex_floor_tiers:[0,12,5,7],triangles:[[0,1,2],[1,3,2]]}},project=v=>({x:v[0],y:v[2]});
const before=structuredClone(geometry);
assert.deepEqual(nativeFloorSelectorAtTriangle(geometry,0,{x:110,y:10},project),{row:0,column:1,tier:12,vertex_index:1,display_corner:[128,0,0],edge_clamped:false});
assert.equal(nativeFloorSelectorAtTriangle(geometry,0,{x:64,y:0},project).column,0); // Deterministic exact tie.
assert.deepEqual(geometry,before); // Equal heights retain distinct tier identities.
const edge=structuredClone(geometry);edge.preview.cells[0].cell_index=16383;edge.preview.vertices=edge.preview.vertices.map(v=>[v[0]+16256,v[1],v[2]+16256]);const corner=nativeFloorSelectorAtTriangle(edge,1,{x:16383,y:16383},project);assert.equal(corner.row,127);assert.equal(corner.column,127);assert.equal(corner.tier,7);assert(corner.edge_clamped);
for(const change of [g=>g.asset_id='asset://fixture/model/0',g=>g.preview.coordinate_system='unknown',g=>g.preview.cells[0].vertex_start=1,g=>g.preview.cells[0].cell_index=1,g=>g.preview.triangles[0][0]=3,g=>g.preview.vertices.pop(),g=>g.preview.vertex_floor_tiers.pop(),g=>g.preview.vertex_floor_tiers[0]=true,g=>g.preview.vertices[0][2]=1]){const g=structuredClone(geometry);change(g);assert.throws(()=>nativeFloorSelectorAtTriangle(g,0,{x:1,y:1},project));}
for(const i of [-1,2,.5,true])assert.throws(()=>nativeFloorSelectorAtTriangle(geometry,i,{x:1,y:1},project));assert.throws(()=>nativeFloorSelectorAtTriangle(geometry,0,{x:NaN,y:1},project));assert.throws(()=>nativeFloorSelectorAtTriangle(geometry,0,{x:1,y:1},()=>null));
console.log('Visible ground triangle ownership, exact duplicate-height tier identity, nearest projected corner, edge clamping and stale/partial/foreign rejection passed.');
