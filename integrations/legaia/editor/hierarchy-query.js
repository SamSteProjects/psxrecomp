import {parseAssetQuery} from './asset-search.js';
export const HIERARCHY_FIELDS=['name','id','type','component','authored','visibility'];
export function parseHierarchyQuery(query){try{return parseAssetQuery(query,HIERARCHY_FIELDS);}catch(error){throw Error(error.message.replaceAll('Asset search','Hierarchy search').replaceAll('asset search','hierarchy search'));}}
export function hierarchyMatches(record,tokens){
 const fields={name:String(record.name??'').toLowerCase(),id:String(record.id??'').toLowerCase(),type:String(record.type??'').toLowerCase(),component:(record.components??[]).join(' ').toLowerCase(),authored:String(record.authored??'unknown').toLowerCase(),visibility:String(record.visibility??'unknown').toLowerCase()};
 const all=[fields.name,fields.id,fields.component].join(' ');
 return tokens.every(token=>{const matches=(token.field?fields[token.field]:all).includes(token.text);return token.exclude?!matches:matches;});
}
export function matchingActorIds(records,tokens){const ids=records.filter(record=>record.type==='actor'&&hierarchyMatches(record,tokens)).map(record=>record.id);if(ids.length>128)throw Error('Select at most 128 matching actors. Narrow the query.');return [...new Set(ids)].sort();}
