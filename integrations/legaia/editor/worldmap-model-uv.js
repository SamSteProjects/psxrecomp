import {worldModelContentFields,worldModelContentAudit} from './worldmap-model-content.js';
import {worldModelPacketAttributes} from './worldmap-model-materials.js';
import {uvTextureCrop} from './model-uv-workspace.js';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function worldModelUvFace(source,objectIndex,primitiveIndex){
 if(source?.metadata.layer!=='current'||!Number.isSafeInteger(objectIndex)||objectIndex<0||!Number.isSafeInteger(primitiveIndex)||primitiveIndex<0)throw Error('Inspect a Current native face for UV editing.');
 const fields=worldModelContentFields(source.tmd),faces=new Map();
 for(const f of fields){if(f.kind!=='primitive'||f.field!=='vertex_index')continue;const key=f.object_index+':'+f.primitive_index;if(!faces.has(key))faces.set(key,{object_index:f.object_index,primitive_index:f.primitive_index,corners:0});faces.get(key).corners++;}
 let start=0,target=null;for(const face of faces.values()){if(face.object_index===objectIndex&&face.primitive_index===primitiveIndex){target=face;break;}start+=face.corners-2;}
 if(!target)throw Error('UV face is outside the native primitive tables.');const selected=fields.filter(f=>f.kind==='primitive'&&f.object_index===objectIndex&&f.primitive_index===primitiveIndex&&f.field==='uv');if(!selected.length)return null;
 const current=[],byte_offsets=[];for(let c=0;c<target.corners;c++){const pair=['u','v'].map(axis=>selected.find(f=>f.corner_index===c&&f.axis===axis));if(pair.some(f=>!f)||selected.length!==target.corners*2)throw Error('Native UV corner coverage differs.');current.push(pair.map(f=>f.value));byte_offsets.push(pair.map(f=>f.byte_offset));}
 return {object_index:objectIndex,primitive_index:primitiveIndex,current,byte_offsets,triangle_indices:Array.from({length:target.corners-2},(_,i)=>start+i)};
}
export function worldModelUvCandidate(source,objectIndex,primitiveIndex,rows){
 const face=worldModelUvFace(source,objectIndex,primitiveIndex);if(!face||!Array.isArray(rows)||rows.length!==face.current.length||rows.some(row=>!Array.isArray(row)||row.length!==2||row.some(v=>!Number.isSafeInteger(v)||v<0||v>255)))throw Error('UV edits require every existing native corner and byte-valued U/V.');
 const bytes=source.tmd.slice();for(const [c,pair] of rows.entries())for(let axis=0;axis<2;axis++)bytes[face.byte_offsets[c][axis]]=pair[axis];worldModelContentAudit(source.tmd,bytes);return bytes;
}
export function worldModelUvTexture(source,face,context){
 if(!context)return {status:'unavailable',reason:'Preview Current or reviewed model to qualify its Current static crop.'};if(context.source_key!==source.metadata.request?.source_key||context.source_sha256!==source.metadata.tmd_sha256)throw Error('UV texture belongs to another Current model.');const preview=context.preview,attrs=worldModelPacketAttributes(source,source.tmd);
 if(['triangle_uvs','triangle_materials','materials'].some(key=>!same(preview?.[key],attrs[key])))throw Error('UV texture differs from complete native UV/material ownership.');const fresh=worldModelUvFace(source,face.object_index,face.primitive_index);if(!same(face,fresh))throw Error('UV face differs from the inspected Current corners.');const material=attrs.triangle_materials[face.triangle_indices[0]];if(face.triangle_indices.some(i=>attrs.triangle_materials[i]!==material))throw Error('Native UV face has conflicting materials.');return uvTextureCrop(preview,material);
}
