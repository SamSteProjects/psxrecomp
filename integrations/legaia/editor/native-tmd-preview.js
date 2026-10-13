import {worldFaceObjects} from './worldmap-model-face-replay.js';
const ordered=v=>Array.isArray(v)?v.map(ordered):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,ordered(v[k])])):v;
const same=(a,b)=>JSON.stringify(ordered(a))===JSON.stringify(ordered(b));
export function qualifyNativeTmdGeometry(bytes,g){
 const fail=()=>{throw Error('Native TMD geometry differs from its literal object, vector or primitive bytes.');};
 const rows=worldFaceObjects(bytes),view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),vertices=[],triangles=[],colors=[],uvs=[],materialIds=[],normals=[],materials=[],objects=[];
 for(const row of rows){const i=row.object_index,at=12+i*28,vertexStart=vertices.length,triangleStart=triangles.length,vertexAt=12+view.getUint32(at,true),normalAt=12+view.getUint32(at+8,true);
  for(let n=0;n<row.vertex_count;n++)vertices.push([0,2,4].map(a=>view.getInt16(vertexAt+n*8+a,true)));
  for(const primitive of row.primitives){const m={textured:primitive.uvs!==null,...primitive.material};let mi=materials.findIndex(v=>same(v,m));if(mi<0){mi=materials.length;materials.push(m);}const count=primitive.corner_count,cs=primitive.colors??Array.from({length:primitive.gouraud?count:1},()=>[128,128,128]),ns=primitive.normal_indices?.map(n=>[0,2,4].map(a=>view.getInt16(normalAt+n*8+a,true)));
   for(const corners of count===4?[[0,1,2],[1,3,2]]:[[0,1,2]]){triangles.push(corners.map(n=>vertexStart+primitive.vertices[n]));colors.push(corners.map(n=>cs[primitive.gouraud?n:0]));uvs.push(primitive.uvs?corners.map(n=>primitive.uvs[n]):null);materialIds.push(mi);normals.push(ns?corners.map(n=>ns[primitive.gouraud?n:0]):null);}
  }
  objects.push({object_index:i,vertex_start:vertexStart,vertex_count:row.vertex_count,triangle_start:triangleStart,triangle_count:triangles.length-triangleStart,raw_object_word6:view.getUint32(at+24,true),transform:null});
 }
 const bounds={min:[0,1,2].map(a=>Math.min(...vertices.map(v=>v[a]))),max:[0,1,2].map(a=>Math.max(...vertices.map(v=>v[a])))};
 for(const [key,value]of Object.entries({vertices,triangles,triangle_colors:colors,triangle_uvs:uvs,triangle_materials:materialIds,triangle_normals:normals,materials,objects,bounds}))if(!same(g?.[key],value))fail();
 return g;
}
