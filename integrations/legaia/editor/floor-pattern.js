// Portable authored floor operations. Never copies retail grid bytes or carries Apply authority.
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const fail=message=>{throw Error(message);};
function lut(value){if(!Array.isArray(value)||value.length!==16||value.some(v=>!integer(v,-32768,32767)))fail('Floor pattern requires sixteen signed MAN height values.');return [...value];}
export function decodeFloorPattern(value){
 if(!value||Object.keys(value).sort().join(',')!=='cells,height,height_lut,schema_version,width'||value.schema_version!=='legaia.floor-pattern.v1'||!integer(value.width,1,128)||!integer(value.height,1,128)||value.width*value.height>4096||!Array.isArray(value.cells)||!value.cells.length||value.cells.length>4096)fail('Floor pattern requires a bounded selector extent and authored operations.');
 const heights=lut(value.height_lut),seen=new Set(),cells=value.cells.map(c=>{if(!c||Object.keys(c).sort().join(',')!=='tier,x,z'||!integer(c.x,0,value.width-1)||!integer(c.z,0,value.height-1)||!(integer(c.tier,0,15)||c.tier==='retail')||seen.has(`${c.x}/${c.z}`))fail('Floor pattern has an invalid, duplicate or out-of-bounds operation.');seen.add(`${c.x}/${c.z}`);return {x:c.x,z:c.z,tier:c.tier};}).sort((a,b)=>a.z-b.z||a.x-b.x);
 return {schema_version:'legaia.floor-pattern.v1',width:value.width,height:value.height,height_lut:heights,cells};
}
export function captureFloorPattern(rectangle,edits,heightLut){
 const r=rectangle;if(!r||Object.keys(r).sort().join(',')!=='column_end,column_start,row_end,row_start,tier'||['row_start','row_end','column_start','column_end'].some(k=>!integer(r[k],0,127))||r.row_start>r.row_end||r.column_start>r.column_end||!(integer(r.tier,0,15)||['retail','current'].includes(r.tier)))fail('Floor pattern requires exact native bounds and a supported operation.');
 const width=r.column_end-r.column_start+1,height=r.row_end-r.row_start+1;if(width*height>4096||!Array.isArray(edits)||edits.length>4096)fail('Floor pattern exceeds 4096 selectors.');
 const cells=new Map(),seen=new Set();if(r.tier!=='current')for(let z=0;z<height;z++)for(let x=0;x<width;x++)cells.set(`${x}/${z}`,{x,z,tier:r.tier});
 for(const e of edits){if(!e||Object.keys(e).sort().join(',')!=='column,row,tier'||!integer(e.row,r.row_start,r.row_end)||!integer(e.column,r.column_start,r.column_end)||!(integer(e.tier,0,15)||e.tier==='retail')||seen.has(`${e.row}/${e.column}`))fail('Floor pattern edits escape or duplicate the source rectangle.');seen.add(`${e.row}/${e.column}`);const x=e.column-r.column_start,z=e.row-r.row_start;cells.set(`${x}/${z}`,{x,z,tier:e.tier});}
 return decodeFloorPattern({schema_version:'legaia.floor-pattern.v1',width,height,height_lut:heightLut,cells:[...cells.values()]});
}
export function transformFloorPattern(input,turns=0,mirrorX=false,mirrorZ=false){
 const p=decodeFloorPattern(input);if(!integer(turns,0,3)||typeof mirrorX!=='boolean'||typeof mirrorZ!=='boolean')fail('Invalid floor pattern transform.');let width=p.width,height=p.height,cells=p.cells.map(c=>({...c,x:mirrorX?width-1-c.x:c.x,z:mirrorZ?height-1-c.z:c.z}));
 for(let turn=0;turn<turns;turn++){cells=cells.map(c=>({...c,x:height-1-c.z,z:c.x}));[width,height]=[height,width];}return decodeFloorPattern({...p,width,height,cells});
}
export function floorPatternDraft(input,row,column,heightLut){
 const p=decodeFloorPattern(input),heights=lut(heightLut);if(!integer(row,0,127)||!integer(column,0,127)||row+p.height>128||column+p.width>128)fail('Floor pattern destination escapes native rows/columns 0..127.');
 for(const tier of new Set(p.cells.map(c=>c.tier).filter(t=>t!=='retail')))if(p.height_lut[tier]!==heights[tier])fail(`Tier ${tier} has a different destination MAN height; no selectors staged.`);
 return {rectangle:{row_start:row,row_end:row+p.height-1,column_start:column,column_end:column+p.width-1,tier:'current'},cell_edits:p.cells.map(c=>({row:row+c.z,column:column+c.x,tier:c.tier}))};
}
export function repeatFloorPattern(input,columns=1,rows=1,gapColumns=0,gapRows=0){
 const p=decodeFloorPattern(input);if(!integer(columns,1,128)||!integer(rows,1,128)||!integer(gapColumns,0,127)||!integer(gapRows,0,127))fail('Floor pattern repeat counts and gaps must be bounded integers.');
 const width=columns*p.width+(columns-1)*gapColumns,height=rows*p.height+(rows-1)*gapRows;if(width>128||height>128||width*height>4096||p.cells.length*columns*rows>4096)fail('Repeated floor pattern exceeds the native grid or 4096-selector review budget.');const cells=[];
 for(let z=0;z<rows;z++)for(let x=0;x<columns;x++)for(const c of p.cells)cells.push({...c,x:c.x+x*(p.width+gapColumns),z:c.z+z*(p.height+gapRows)});return decodeFloorPattern({...p,width,height,cells});
}
