// SDK source-ground ownership; no height-to-tier inference or wall-grid bias.
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const finite=v=>typeof v==='number'&&Number.isFinite(v);
export function nativeFloorSelectorAtTriangle(geometry,triangleIndex,point,projectVertex){
 const g=geometry?.preview;
 if(!g||typeof geometry.asset_id!=='string'||!/^environment:\/\/[^/]+\/field-map\/ground$/.test(geometry.asset_id)||g.coordinate_system!=='retail_field_y_down'||!Array.isArray(g.cells)||!g.cells.length||g.cells.length>16384||!Array.isArray(g.vertices)||g.vertices.length!==4*g.cells.length||!Array.isArray(g.triangles)||g.triangles.length!==2*g.cells.length||!Array.isArray(g.vertex_floor_tiers)||g.vertex_floor_tiers.length!==g.vertices.length||!integer(triangleIndex,0,g.triangles.length-1)||!finite(point?.x)||!finite(point?.y)||typeof projectVertex!=='function')throw Error('Floor pick requires a Current source-ground triangle with exact selector metadata.');
 const index=Math.floor(triangleIndex/2),cell=g.cells[index],base=4*index;
 if(!cell||!integer(cell.cell_index,0,16383)||cell.vertex_start!==base||JSON.stringify(g.triangles[2*index])!==JSON.stringify([base,base+1,base+2])||JSON.stringify(g.triangles[2*index+1])!==JSON.stringify([base+1,base+3,base+2]))throw Error('Floor pick triangle does not belong to a complete source cell.');
 const column=cell.cell_index%128,row=Math.floor(cell.cell_index/128),corners=[[0,0],[1,0],[0,1],[1,1]];
 for(let i=0;i<4;i++){const v=g.vertices[base+i],[dx,dz]=corners[i];if(!Array.isArray(v)||v.length!==3||!v.every(finite)||v[0]!==128*(column+dx)||v[2]!==128*(row+dz)||!integer(g.vertex_floor_tiers[base+i],0,15))throw Error('Floor pick corner coordinates or selector tier differ from source ownership.');}
 const candidates=g.triangles[triangleIndex].map(vertexIndex=>{const projected=projectVertex([...g.vertices[vertexIndex]]);if(!finite(projected?.x)||!finite(projected?.y))throw Error('Floor corners cannot be projected in the current camera.');const [dx,dz]=corners[vertexIndex-base];return {row:Math.min(row+dz,127),column:Math.min(column+dx,127),tier:g.vertex_floor_tiers[vertexIndex],vertex_index:vertexIndex,display_corner:[...g.vertices[vertexIndex]],edge_clamped:row+dz>127||column+dx>127,distance:(projected.x-point.x)**2+(projected.y-point.y)**2};}).sort((a,b)=>a.distance-b.distance||a.row-b.row||a.column-b.column||a.vertex_index-b.vertex_index);
 const result=candidates[0];delete result.distance;return result;
}
