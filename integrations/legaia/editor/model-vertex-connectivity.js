// Current preview connectivity, not spatial proximity or runtime mesh ownership.
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const fail=message=>{throw new Error(message);};
function owner(preview,index,indices){
  if(!integer(index,0,65535)||!Array.isArray(preview?.objects)||preview.objects.length>65536||!Array.isArray(preview.vertices)||preview.vertices.length>100000)fail('Vertex selection requires a bounded Current model preview.');
  const object=preview.objects[index];
  if(!object||object.object_index!==index||!integer(object.vertex_start,0,preview.vertices.length)||!integer(object.vertex_count,1,preview.vertices.length-object.vertex_start))fail('Vertex selection requires an existing Current object table.');
  if(!Array.isArray(indices)||!indices.length||indices.length>4096||indices.some(i=>!integer(i,0,object.vertex_count-1))||new Set(indices).size!==indices.length)fail('Choose 1..4096 unique object-local vertex indices.');
  return object;
}
export function invertVertexGroup(preview,index,indices){
  const object=owner(preview,index,indices),selected=new Set(indices),result=[];
  for(let i=0;i<object.vertex_count;i++)if(!selected.has(i)){if(result.length===4096)fail('Inverted group exceeds 4096 vertices; selection was retained.');result.push(i);}
  return result;
}
export function linkedVertexGroup(preview,index,indices){
  const object=owner(preview,index,indices);
  if(!Array.isArray(preview.triangles)||preview.triangles.length>262144||!integer(object.triangle_start,0,preview.triangles.length)||!integer(object.triangle_count,0,preview.triangles.length-object.triangle_start))fail('Current object triangle ranges are unavailable or exceed selection bounds.');
  const adjacency=new Map(),start=object.vertex_start,end=start+object.vertex_count;
  for(let i=object.triangle_start;i<object.triangle_start+object.triangle_count;i++){
    const triangle=preview.triangles[i];if(!Array.isArray(triangle)||triangle.length!==3||triangle.some(v=>!integer(v,start,end-1)))fail('Current triangle references escape the selected object; selection was retained.');
    const local=triangle.map(v=>v-start);for(const vertex of local){if(!adjacency.has(vertex))adjacency.set(vertex,new Set());for(const neighbor of local)adjacency.get(vertex).add(neighbor);}
  }
  const selected=new Set(indices),queue=indices.slice();
  for(let head=0;head<queue.length;head++)for(const neighbor of adjacency.get(queue[head])??[]){if(selected.has(neighbor))continue;if(selected.size===4096)fail('Connected group exceeds 4096 vertices; selection was retained.');selected.add(neighbor);queue.push(neighbor);}
  return [...selected].sort((a,b)=>a-b);
}
