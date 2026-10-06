import {MAX_PREVIEW_ENTITIES} from './scene-limits.js';
// Source-address dependencies from one verified scene preview, not runtime use.
export function textureSceneUsage(preview,textureId){
  if(!preview||typeof textureId!=='string'||!Array.isArray(preview.assets)||!Array.isArray(preview.entities)||preview.assets.length>128||preview.entities.length>MAX_PREVIEW_ENTITIES)throw new Error('Invalid or oversized scene usage source');
  const matches=[],candidates=[];let unresolved=0,textured=0;
  for(const asset of preview.assets){
    const rows=[],partial=[];
    for(const texture of asset.preview?.textures??[]){
      const material=asset.preview?.materials?.[texture.material_index];
      if(material?.textured===false||texture.reason==='material is untextured')continue;
      textured++;
      if(texture.status!=='address_match')unresolved++;
      if(!Array.isArray(texture.source_ids)||!texture.source_ids.includes(textureId))continue;
      const row={material_index:texture.material_index,status:texture.status,source_ids:[...texture.source_ids],reason:texture.reason??null};
      if(texture.status==='address_match')rows.push(row);else partial.push(row);
    }
    const instances=preview.entities.filter(entity=>entity.geometry_key===asset.geometry_key&&entity.renderable).map(entity=>({id:entity.entity_id,kind:entity.kind??'actor',asset_id:entity.asset_id}));
    if(rows.length)matches.push({asset_id:asset.asset_id,geometry_key:asset.geometry_key,materials:rows,instances});
    if(partial.length)candidates.push({asset_id:asset.asset_id,geometry_key:asset.geometry_key,materials:partial,instances});
  }
  return {texture_id:textureId,scene_id:preview.scene_id,source_key:preview.source_key,representation:preview.representation,
    matches,candidates,textured_material_count:textured,unresolved_material_count:unresolved,
    matching_instance_count:new Set(matches.flatMap(group=>group.instances.map(instance=>instance.id))).size,
    unavailable_instance_count:preview.entities.filter(entity=>!entity.renderable).length};
}
