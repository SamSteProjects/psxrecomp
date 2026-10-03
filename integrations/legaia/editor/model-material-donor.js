// A source binding is a draft convenience, not a new runtime dependency.
const fail=message=>{throw new Error(message);};
const exact=(value,keys)=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join('|')===[...keys].sort().join('|');
export function decodeMaterialDonorModels(value,context){
  if(!exact(value,['schema_version','scene_id','project_source_key','models','project_changed'])||value.schema_version!=='legaia.model-material-donor-models.v1'||value.scene_id!==context.sceneId||value.project_source_key!==context.sourceKey||value.project_changed!==false||!Array.isArray(value.models)||value.models.length>2048)fail('Material binding catalog does not match the current scene source.');
  const seen=new Set();
  for(const row of value.models){if(!exact(row,['asset_id','label'])||typeof row.asset_id!=='string'||!/^asset:\/\/.{1,504}$/.test(row.asset_id)||typeof row.label!=='string'||row.label.length<1||row.label.length>512||seen.has(row.asset_id))fail('Material binding catalog contains an invalid or duplicate model.');seen.add(row.asset_id);}
  return structuredClone(value.models);
}
// Call only with a source snapshot qualified by decodeModelMaterialSource.
export function materialDonorRows(source){
  return source.objects.flatMap(object=>object.groups.flatMap(group=>group.primitives.filter(row=>row.textured&&[4,8,16].includes(row.texture_bpp)).map(row=>({object_index:object.object_index,group_index:group.group_index,primitive_index:row.primitive_index,byte_offset:row.byte_offset,values:materialDonorValues(row)}))));
}
export function materialDonorValues(row){
  const ranges={page_column:15,page_row:1,clut_column:63,clut_row:511};
  if(row?.textured!==true||![4,8,16].includes(row.texture_bpp))fail('Choose a source-qualified textured primitive.');
  const values={texture_bpp:row.texture_bpp};
  for(const field of ['page_column','page_row',...(row.texture_bpp===16?[]:['clut_column','clut_row'])]){const value=row[field];if(!Number.isInteger(value)||value<0||value>ranges[field])fail('Source binding has an invalid VRAM coordinate.');values[field]=value;}
  return values;
}
export function materialDonorGroupEdits(source,objectIndex,groupIndex,donorRow){
  const values=materialDonorValues(donorRow),object=source.objects.find(row=>row.object_index===objectIndex),group=object?.groups.find(row=>row.group_index===groupIndex);
  if(!group)fail('Choose a qualified target packet group.');
  return group.primitives.filter(row=>row.textured).map(row=>({kind:'primitive',object_index:objectIndex,primitive_index:row.primitive_index,values:Object.fromEntries(Object.entries(values).filter(([field,value])=>row[field]!==value))}));
}
