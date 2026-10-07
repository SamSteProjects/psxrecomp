const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function mirrorObjectWords(object,{axis,pivot}){
 if(!['x','y','z'].includes(axis)||!['origin','center'].includes(pivot)||!Array.isArray(object?.vertices)||object.vertices.length<1||object.vertices.length>8192||!Array.isArray(object.normals)||object.normals.length>8192)throw Error('Choose object vectors, axis and origin or center pivot.');
 const a='xyz'.indexOf(axis),rows=kind=>Array.from(object[kind],row=>{if(!Array.isArray(row)||row.length!==3||[0,1,2].some(i=>!Number.isSafeInteger(row[i])||row[i]< -32768||row[i]>32767))throw Error('Object mirror requires signed16 XYZ.');return [...row];}),vertices=rows('vertices'),normals=rows('normals'),center=pivot==='origin'?0:Math.min(...vertices.map(v=>v[a]))+Math.max(...vertices.map(v=>v[a]));
 for(const [rows,c] of [[vertices,center],[normals,0]])for(const row of rows){row[a]=c-row[a];if(row[a]< -32768||row[a]>32767)throw Error('Object mirror exceeds signed16 bounds.');}
 return {vertices,normals};
}
export function qualifyObjectMirror(report,object,values){
 const expected=mirrorObjectWords(object,values),before=report.current_preview,after=report.preview,owner=before?.objects?.[report.object_index],a='xyz'.indexOf(values.axis),keys=['triangles','triangle_colors','triangle_uvs','triangle_normals'];
 if(!equal(report.values,values)||!equal(report.object_mirror_words?.current,{vertices:object.vertices,normals:object.normals})||!equal(report.object_mirror_words?.proposed,expected)||!owner||!Number.isSafeInteger(owner.triangle_start)||!Number.isSafeInteger(owner.triangle_count)||owner.triangle_start<0||owner.triangle_count<0||owner.triangle_start+owner.triangle_count>before.triangles.length||!Array.isArray(before.triangle_materials)||before.triangle_materials.length!==before.triangles.length||!equal(before.triangle_materials,after.triangle_materials)||keys.some(k=>!Array.isArray(before[k])||!Array.isArray(after[k])||before[k].length!==before.triangles.length||after[k].length!==before[k].length))throw Error('Object mirror differs from inspected words or preview ownership.');
 for(let i=0;i<before.triangles.length;i++){
  if(i<owner.triangle_start||i>=owner.triangle_start+owner.triangle_count){if(keys.some(k=>!equal(before[k][i],after[k][i])))throw Error('Object mirror changed another object.');continue;}
  if(![[0,2,1],[2,1,0],[1,0,2]].some(order=>keys.every(k=>{const row=before[k][i];if(row===null)return after[k][i]===null;if(!Array.isArray(row)||row.length!==3)return false;return equal(after[k][i],order.map(c=>k==='triangle_normals'?row[c].map((v,index)=>index===a?-v:v):row[c]));})))throw Error('Object mirror winding or corner attributes differ from Current.');
 }
 if(!Array.isArray(report.changes_from_current)||report.changes_from_current.some(row=>row.object_index!==report.object_index||!['vertex','normal','primitive'].includes(row.kind)||row.kind==='primitive'&&!['vertex_index','normal_index','uv','color'].includes(row.field)))throw Error('Object mirror changed unsupported native fields.');
 return expected;
}
