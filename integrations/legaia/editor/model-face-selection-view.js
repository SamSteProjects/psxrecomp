// Display-only native face ownership. Never returned as an authored model draft.
const fail=m=>{throw new Error(m);},int=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
export function nativeFaceSelectionTriangles(preview,source,selection){
  if(selection?.asset_id!==source.asset_id||selection.project_source_key!==source.project_source_key||selection.effective_sha256!==source.effective_sha256||selection.can_stage!==true||!Array.isArray(selection.faces)||!selection.faces.length||selection.faces.length>256)fail('GLB face highlight requires a fresh complete native selection.');
  if(!Array.isArray(preview.objects)||preview.objects.length!==source.objects.length||!Array.isArray(preview.triangles)||preview.triangles.length>100000||!Array.isArray(preview.vertices)||preview.vertices.length>100000)fail('Native highlight preview layout differs from Current.');
  const ownership=new Map();let total=0;
  for(const [o,obj] of source.objects.entries()){const shown=preview.objects[o];if(shown.object_index!==o||shown.vertex_count!==obj.vertex_count||shown.triangle_start!==total)fail('Native highlight object ownership differs from Current.');let count=0;for(const [i,row] of obj.primitives.entries()){if(row.primitive_index!==i||![3,4].includes(row.corner_count))fail('Native highlight face ownership is malformed.');ownership.set(`${o}:${i}`,Array.from({length:row.corner_count-2},(_,n)=>total+count+n));count+=row.corner_count-2;}if(count!==shown.triangle_count)fail('Native highlight triangulation differs from Current face counts.');total+=count;}
  if(total!==preview.triangles.length)fail('Native highlight has unowned triangles.');
  const triangles=[],owned=new Set();
  for(const f of selection.faces){const row=source.objects[f.object_index]?.primitives[f.primitive_index],key=`${f.object_index}:${f.primitive_index}`;if(!row||row.group_index!==f.group_index||row.uvs===null||f.textured!==true||f.triangle_count!==row.corner_count-2||f.material_indices?.length!==1||f.material_indices[0]!==selection.material_index||owned.has(key))fail('Native highlight selection has stale or ambiguous face ownership.');owned.add(key);triangles.push(...ownership.get(key));}
  return triangles.sort((a,b)=>a-b);
}
export function faceSelectionView(preview,source,selection){
  const selected=nativeFaceSelectionTriangles(preview,source,selection),geometry=structuredClone(preview),material=geometry.materials.length;
  geometry.materials.push({textured:false,semi_transparent:false,clut:null,tpage:null,blend:{enabled:false,mode:0,texel_gate:'all_fragments',evidence:'editor_selection_display_only'}});
  const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
  for(const i of selected){const triangle=geometry.triangles[i];if(!Array.isArray(triangle)||triangle.length!==3||triangle.some(v=>!int(v,0,geometry.vertices.length-1)))fail('Native highlight has invalid preview vertex references.');geometry.triangle_materials[i]=material;geometry.triangle_uvs[i]=null;geometry.triangle_colors[i]=[[255,220,40],[255,220,40],[255,220,40]];for(const v of triangle){const point=geometry.vertices[v];if(!Array.isArray(point)||point.length!==3||point.some(n=>!Number.isFinite(n)))fail('Native highlight has invalid preview coordinates.');for(let a=0;a<3;a++){min[a]=Math.min(min[a],point[a]);max[a]=Math.max(max[a],point[a]);}}}
  return {geometry,selected_triangles:selected,bounds:{min,max},face_count:selection.faces.length};
}
