// Native ownership, independent of material batching and display highlighting.
const int=(n,a,b)=>Number.isSafeInteger(n)&&n>=a&&n<=b;
// Poses change positions, not native connectivity. Require a complete object
// prefix and exact Current corner indices before navigating out of the scene.
export function nativeSceneFaceAtTriangle(geometry,source,triangleIndex){
 const preview=geometry?.preview;
 if(geometry?.asset_id!==source?.asset_id||preview?.semantic_id!==source?.asset_id||!['retail_tmd_object_local','retail_psx_actor_local_y_down','actor_local_y_down_source_units'].includes(preview.coordinate_system)||!Array.isArray(preview.objects)||!preview.objects.length||preview.objects.length>source.objects.length||!Array.isArray(preview.triangles)||preview.triangles.length>100000||!Array.isArray(preview.vertices)||preview.vertices.length>100000||!int(triangleIndex,0,preview.triangles.length-1))throw new Error('Scene face picking requires qualified Current native geometry.');
 let vertex=0,triangle=0,found=null;
 for(const [o,shown] of preview.objects.entries()){
  const obj=source.objects[o];if(shown.object_index!==o||shown.vertex_start!==vertex||shown.vertex_count!==obj.vertex_count||shown.triangle_start!==triangle)throw new Error('Scene object differs from Current native ownership.');
  const start=triangle;
  for(const [p,row] of obj.primitives.entries()){
   if(row.primitive_index!==p||![3,4].includes(row.corner_count)||!Array.isArray(row.vertices)||row.vertices.length!==row.corner_count||row.vertices.some(v=>!int(v,0,obj.vertex_count-1)))throw new Error('Scene face has unsupported native corner ownership.');
   for(const corners of row.corner_count===4?[[0,1,2],[1,3,2]]:[[0,1,2]]){
    const actual=preview.triangles[triangle],expected=corners.map(c=>vertex+row.vertices[c]);
    if(!Array.isArray(actual)||actual.length!==3||actual.some((v,i)=>v!==expected[i]))throw new Error('Scene triangulation differs from Current native faces.');
    if(triangle===triangleIndex)found={object_index:o,primitive_index:p};triangle++;
   }
  }
  if(shown.triangle_count!==triangle-start)throw new Error('Scene object has incomplete native faces.');vertex+=obj.vertex_count;
 }
 if(vertex!==preview.vertices.length||triangle!==preview.triangles.length||!found)throw new Error('Scene triangle has no complete native face ownership.');return found;
}
export function nativeModelFaceAtTriangle(preview,source,triangleIndex){
 if(preview?.semantic_id!==source.asset_id||preview.posed===true||preview.coordinate_system!=='retail_tmd_object_local'||!Array.isArray(preview.objects)||preview.objects.length!==source.objects.length||!Array.isArray(preview.triangles)||preview.triangles.length>100000||!int(triangleIndex,0,preview.triangles.length-1))throw new Error('Face picking requires qualified unposed native geometry.');
 let total=0,found=null;for(const [o,obj] of source.objects.entries()){const shown=preview.objects[o];if(shown.object_index!==o||shown.triangle_start!==total||shown.vertex_count!==obj.vertex_count)throw new Error('Picked model object differs from Current ownership.');let count=0;for(const [p,row] of obj.primitives.entries()){if(row.primitive_index!==p||![3,4].includes(row.corner_count))throw new Error('Picked face has unsupported native corner ownership.');const n=row.corner_count-2;if(triangleIndex>=total+count&&triangleIndex<total+count+n)found={object_index:o,primitive_index:p};count+=n;}if(shown.triangle_count!==count)throw new Error('Picked model triangulation differs from native faces.');total+=count;}if(total!==preview.triangles.length||!found)throw new Error('Picked triangle has no complete native face ownership.');return found;
}

export function nativeModelFaceTriangles(preview,source,objectIndex,primitiveIndex){
 if(!int(objectIndex,0,source.objects.length-1)||!int(primitiveIndex,0,(source.objects[objectIndex]?.primitives.length??0)-1))throw new Error('Choose an existing native face for the outline.');
 const obj=source.objects[objectIndex],face=obj.primitives[primitiveIndex];if(![3,4].includes(face.corner_count))throw new Error('Face outline requires a native triangle or quad.');let start=preview.objects?.[objectIndex]?.triangle_start;for(let p=0;p<primitiveIndex;p++)start+=obj.primitives[p].corner_count-2;
 const result=Array.from({length:face.corner_count-2},(_,i)=>start+i);for(const t of result){const found=nativeModelFaceAtTriangle(preview,source,t);if(found.object_index!==objectIndex||found.primitive_index!==primitiveIndex)throw new Error('Outlined triangle differs from native face ownership.');}return result;
}
