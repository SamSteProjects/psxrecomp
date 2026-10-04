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

// Qualified GLB material selection owns the face identities; explicit byte
// rectangles own this UV transformation. Construct and validate before publish.
export function uvSelectionDrafts(source,selection,from,to,existing=[]){
  if(selection?.asset_id!==source.asset_id||selection.project_source_key!==source.project_source_key||selection.effective_sha256!==source.effective_sha256||selection.can_stage!==true||!Array.isArray(selection.faces)||!selection.faces.length||selection.faces.length>256)fail('UV face selection is stale, ambiguous or exceeds its budget.');
  const next=new Map(existing.map(row=>[`${row.object_index}:${row.primitive_index}`,structuredClone(row)])),owned=new Set();
  for(const face of selection.faces){const obj=source.objects[face.object_index],row=obj?.primitives[face.primitive_index],key=`${face.object_index}:${face.primitive_index}`;if(!row||row.primitive_index!==face.primitive_index||row.group_index!==face.group_index||row.uvs===null||face.textured!==true||face.material_indices?.length!==1||face.material_indices[0]!==selection.material_index||owned.has(key))fail('UV face selection does not own complete Current textured faces.');owned.add(key);
    const draft=next.get(key)??{object_index:face.object_index,primitive_index:face.primitive_index,vertices:structuredClone(row.vertices),...(row.colors===null?{}:{colors:structuredClone(row.colors)}),...(row.normal_indices==null?{}:{normal_indices:structuredClone(row.normal_indices)})};draft.uvs=remapUVs(row.uvs,from,to);next.set(key,draft);
  }
  if(next.size>256)fail('UV face selection exceeds the combined 256-entry draft budget.');
  return [...next.values()].sort((a,b)=>a.object_index-b.object_index||a.primitive_index-b.primitive_index);
}
