// Explicit native UV rectangles. No texture/material/address inference.
const fail=message=>{throw new Error(message);};
const int=(v,lo,hi)=>Number.isSafeInteger(v)&&v>=lo&&v<=hi;
function rectangle(v,source){
  if(!Array.isArray(v)||v.length!==4||v.some(n=>!int(n,0,255))||v[0]===v[2]||v[1]===v[3]||source&&(v[0]>v[2]||v[1]>v[3]))fail('UV rectangles require four byte endpoints and nonzero spans; source endpoints must ascend.');
  return v;
}
export function remapUVs(uvs,from,to){
  rectangle(from,true);rectangle(to,false);
  if(!Array.isArray(uvs)||![3,4].includes(uvs.length)||uvs.some(v=>!Array.isArray(v)||v.length!==2||v.some((n,a)=>!int(n,from[a],from[a+2]))))fail('Every selected UV corner must lie inside the source rectangle; clipping and wrapping are not inferred.');
  return uvs.map(v=>v.map((n,a)=>to[a]+Math.floor(((n-from[a])*(to[a+2]-to[a])*2+from[a+2]-from[a])/(2*(from[a+2]-from[a])))));
}
export function uvRectangleDrafts(source,selected,from,to,scope){
  if(!['primitive','group'].includes(scope)||!int(selected?.object_index,0,(source?.objects?.length??0)-1))fail('Select an existing primitive or packet group.');
  const object=source.objects[selected.object_index],row=object.primitives?.[selected.primitive_index];
  if(!row||row.primitive_index!==selected.primitive_index||row.uvs===null)fail('Select a textured primitive for UV retargeting.');
  const rows=scope==='primitive'?[row]:object.primitives.filter(v=>v.group_index===row.group_index&&v.uvs!==null);
  if(!rows.length||rows.length>256)fail('UV rectangle remapping accepts at most 256 textured primitives in one reviewed draft.');
  // Construct the entire result before publishing any draft. Other fields of
  // the selected draft are retained; neighboring faces use Current source data.
  return rows.map(v=>{
    const base=v.primitive_index===selected.primitive_index?structuredClone(selected):{object_index:selected.object_index,primitive_index:v.primitive_index,vertices:structuredClone(v.vertices),uvs:structuredClone(v.uvs),...(v.colors===null?{}:{colors:structuredClone(v.colors)}),...(v.normal_indices==null?{}:{normal_indices:structuredClone(v.normal_indices)})};
    base.uvs=remapUVs(v.uvs,from,to);return base;
  });
}
