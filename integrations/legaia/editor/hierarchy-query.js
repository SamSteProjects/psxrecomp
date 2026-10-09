import {parseAssetQuery} from './asset-search.js';
export const HIERARCHY_FIELDS=['name','id','type','component','attached','authored','visibility','model','retail_model','current_model','animation','retail_animation','current_animation'];
export function hierarchyActorBindings(components){
 const identity=(value,prefix)=>typeof value==='string'&&value.startsWith(prefix)?[value]:[];
 const retail_model=identity(components?.ActorAppearance?.imported?.asset_id,'asset://'),current_model=identity(components?.ActorAppearance?.effective?.asset_id,'asset://');
 const retail_animation=identity(components?.ActorAnimation?.imported?.animation_asset_id,'animation://'),current_animation=identity(components?.ActorAnimation?.effective?.animation_asset_id,'animation://');
 return {retail_model,current_model,model:[...new Set([...retail_model,...current_model])],retail_animation,current_animation,animation:[...new Set([...retail_animation,...current_animation])]};
}
export function hierarchyAttachedComponents(components,schema){
 if(!components||typeof components!=='object'||Array.isArray(components))return [];
 return Object.keys(components).flatMap(id=>[id,...(typeof schema?.components?.[id]?.label==='string'?[schema.components[id].label]:[])]);
}
export function parseHierarchyQuery(query){try{return parseAssetQuery(query,HIERARCHY_FIELDS);}catch(error){throw Error(error.message.replaceAll('Asset search','Hierarchy search').replaceAll('asset search','hierarchy search'));}}
export function hierarchyAssetBindingQuery(record,layer){
 if(!['retail','current'].includes(layer)||!['model','animation'].includes(record?.type)||typeof record.id!=='string'||record.id.length>1024||!record.id.startsWith(record.type==='model'?'asset://':'animation://')||/[\u0000-\u001f\u007f]/.test(record.id))throw Error('Actor binding navigation requires a recorded model or clip identity and a Retail/Current layer.');
 const query=`type:actor ${layer}_${record.type}:${JSON.stringify(record.id)}`;parseHierarchyQuery(query);return query;
}
export function hierarchyMatches(record,tokens){
 const fields={name:String(record.name??'').toLowerCase(),id:String(record.id??'').toLowerCase(),type:String(record.type??'').toLowerCase(),component:(record.components??[]).join(' ').toLowerCase(),attached:(record.attached??[]).join(' ').toLowerCase(),authored:String(record.authored??'unknown').toLowerCase(),visibility:String(record.visibility??'unknown').toLowerCase()};
 for(const field of ['model','retail_model','current_model','animation','retail_animation','current_animation'])fields[field]=(record[field]??[]).join(' ').toLowerCase();
 const all=[fields.name,fields.id,fields.component].join(' ');
 return tokens.every(token=>{const exact=['model','retail_model','current_model','animation','retail_animation','current_animation'].includes(token.field)&&/^(asset|animation):\/\//.test(token.text);
  const matches=exact?(record[token.field]??[]).some(id=>id.toLowerCase()===token.text):(token.field?fields[token.field]:all).includes(token.text);return token.exclude?!matches:matches;});
}
export function matchingActorIds(records,tokens){const ids=records.filter(record=>record.type==='actor'&&hierarchyMatches(record,tokens)).map(record=>record.id);if(ids.length>128)throw Error('Select at most 128 matching actors. Narrow the query.');return [...new Set(ids)].sort();}
