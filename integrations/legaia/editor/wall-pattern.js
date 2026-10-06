// Portable authored wall operations; no retail bytes or native write authority.
const fail=message=>{throw Error(message);};
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const operation=v=>typeof v==='boolean'||v==='retail';
export function decodeWallPattern(value){
  if(!value||Object.keys(value).sort().join(',')!=='cells,height_subcells,schema_version,width_subcells'||value.schema_version!=='legaia.wall-pattern.v1'||!integer(value.width_subcells,2,256)||!integer(value.height_subcells,2,256)||value.width_subcells%2||value.height_subcells%2||!Array.isArray(value.cells)||!value.cells.length||value.cells.length>4096)fail('Wall pattern requires bounded even subcell dimensions and authored operations.');
  const seen=new Set(),cells=value.cells.map(cell=>{if(!cell||Object.keys(cell).sort().join(',')!=='blocked,x,z'||!integer(cell.x,0,value.width_subcells-1)||!integer(cell.z,0,value.height_subcells-1)||!operation(cell.blocked)||seen.has(`${cell.x}/${cell.z}`))fail('Invalid, duplicate or out-of-bounds wall pattern operation.');seen.add(`${cell.x}/${cell.z}`);return {x:cell.x,z:cell.z,blocked:cell.blocked};}).sort((a,b)=>a.z-b.z||a.x-b.x);
  return {schema_version:value.schema_version,width_subcells:value.width_subcells,height_subcells:value.height_subcells,cells};
}
export function captureWallPattern(rectangle,edits=[]){
  const r=rectangle;
  if(!r||Object.keys(r).sort().join(',')!=='blocked,column_end,column_start,quadrant,row_end,row_start'||!integer(r.row_start,1,127)||!integer(r.row_end,r.row_start,127)||!integer(r.column_start,0,127)||!integer(r.column_end,r.column_start,127)||!(r.quadrant==='all'||integer(r.quadrant,0,3))||!(operation(r.blocked)||r.blocked==='current'))fail('Wall pattern requires canonical source rectangle bounds.');
  const width=2*(r.column_end-r.column_start+1),height=2*(r.row_end-r.row_start+1),cells=new Map();
  if((r.row_end-r.row_start+1)*(r.column_end-r.column_start+1)*(r.quadrant==='all'?4:1)>4096)fail('Pattern source selection exceeds 4096 wall bits.');
  if(r.blocked!=='current')for(let row=r.row_start;row<=r.row_end;row++)for(let column=r.column_start;column<=r.column_end;column++)for(const q of r.quadrant==='all'?[0,1,2,3]:[r.quadrant]){const x=2*(column-r.column_start)+(q&1),z=2*(row-r.row_start)+(q>>1);cells.set(`${x}/${z}`,{x,z,blocked:r.blocked});}
  if(!Array.isArray(edits)||edits.length>4096)fail('Wall pattern edit budget exceeded.');const seen=new Set();
  for(const e of edits){if(!e||Object.keys(e).sort().join(',')!=='blocked,column,quadrant,row'||!integer(e.row,r.row_start,r.row_end)||!integer(e.column,r.column_start,r.column_end)||!integer(e.quadrant,0,3)||r.quadrant!=='all'&&e.quadrant!==r.quadrant||!operation(e.blocked)||seen.has(`${e.row}/${e.column}/${e.quadrant}`))fail('Wall pattern edit escapes or duplicates the source selection.');seen.add(`${e.row}/${e.column}/${e.quadrant}`);const x=2*(e.column-r.column_start)+(e.quadrant&1),z=2*(e.row-r.row_start)+(e.quadrant>>1);cells.set(`${x}/${z}`,{x,z,blocked:e.blocked});}
  return decodeWallPattern({schema_version:'legaia.wall-pattern.v1',width_subcells:width,height_subcells:height,cells:[...cells.values()]});
}
export function transformWallPattern(input,quarterTurns=0,mirrorX=false,mirrorZ=false){
  const pattern=decodeWallPattern(input);if(!integer(quarterTurns,0,3)||typeof mirrorX!=='boolean'||typeof mirrorZ!=='boolean')fail('Invalid wall pattern rotation or mirror choice.');
  let width=pattern.width_subcells,height=pattern.height_subcells,cells=pattern.cells.map(c=>({...c,x:mirrorX?width-1-c.x:c.x,z:mirrorZ?height-1-c.z:c.z}));
  for(let turn=0;turn<quarterTurns;turn++){cells=cells.map(c=>({...c,x:height-1-c.z,z:c.x}));[width,height]=[height,width];}
  return decodeWallPattern({...pattern,width_subcells:width,height_subcells:height,cells});
}
export function wallPatternDraft(input,row,column){
  const pattern=decodeWallPattern(input),rowEnd=row+pattern.height_subcells/2-1,columnEnd=column+pattern.width_subcells/2-1;
  if(!integer(row,1,127)||!integer(column,0,127)||rowEnd>127||columnEnd>127)fail('Wall pattern placement escapes the canonical source grid.');
  const cell_edits=pattern.cells.map(c=>({row:row+(c.z>>1),column:column+(c.x>>1),quadrant:(c.x&1)+2*(c.z&1),blocked:c.blocked})).sort((a,b)=>a.row-b.row||a.column-b.column||a.quadrant-b.quadrant);
  const quadrants=new Set(cell_edits.map(c=>c.quadrant)),quadrant=quadrants.size===1?cell_edits[0].quadrant:'all';
  if(pattern.width_subcells*pattern.height_subcells/(quadrant==='all'?1:4)>4096)fail('Pattern extent exceeds the selected quadrant review budget.');
  return {rectangle:{row_start:row,row_end:rowEnd,column_start:column,column_end:columnEnd,quadrant,blocked:'current'},cell_edits};
}
