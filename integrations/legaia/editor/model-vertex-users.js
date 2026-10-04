import {mountStoredReferenceUsers,validateReferenceFaceMapping,validateReferenceVector} from './model-normal-users.js';
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const integer=(v,max)=>Number.isSafeInteger(v)&&v>=0&&v<=max;
export function decodeVertexUsers(value,binding){
  if(!value||!['legaia.model-vertex-users.v1','legaia.model-vertex-users.v2','legaia.model-vertex-users.v3'].includes(value.schema_version)||value.asset_id!==binding.asset_id||value.project_source_key!==binding.source_key||value.effective_sha256!==binding.expected_sha256||!hash(value.project_source_key)||!hash(value.effective_sha256)||!hash(value.source_sha256)||value.object_index!==binding.object_index||value.vertex_index!==binding.vertex_index||!integer(value.object_index,65535)||!integer(value.vertex_index,8191)||!integer(value.model_byte_length,32*1024*1024)||value.model_byte_length<12||value.read_only!==true||value.gameplay_verified!==false||value.scope!=='qualified_stored_vertex_reference_operands_in_selected_object')throw new Error('Vertex users differ from the inspected source vector.');
  validateReferenceVector(value,'vertex');
  for(const field of ['retail_users','current_users']){
    if(!Array.isArray(value[field])||value[field].length>4096)throw new Error('Vertex users exceed the qualified reference budget.');
    const seen=new Set();
    for(const row of value[field]){
      if(!row||row.kind!=='primitive'||row.field!=='vertex_index'||row.object_index!==value.object_index||row.vertex_index!==value.vertex_index||!integer(row.primitive_index,65535)||!integer(row.group_index,65535)||!integer(row.corner_index,3)||!integer(row.byte_offset,(field==='retail_users'&&(value.schema_version.endsWith('.v2')||value.schema_version.endsWith('.v3'))?value.retail_model_byte_length:value.model_byte_length)-2)||row.byte_offset%2||![3,4].includes(row.corner_count)||row.sharing!=='vertex_corner'||!Array.isArray(row.affected_corners))throw new Error('Invalid vertex reference ownership.');
      const corners=[row.corner_index];
      if(row.corner_index>=row.corner_count||JSON.stringify(corners)!==JSON.stringify(row.affected_corners)||seen.has(row.byte_offset))throw new Error('Vertex reference corner coverage conflicts.');seen.add(row.byte_offset);
    }
  }
  validateReferenceFaceMapping(value);
  return structuredClone(value);
}

export function mountVertexUsers(options){return mountStoredReferenceUsers(options,{noun:'vertex',decode:decodeVertexUsers});}
