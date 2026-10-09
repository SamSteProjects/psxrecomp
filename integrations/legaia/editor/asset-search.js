// Search recorded asset metadata without inferring confidence or runtime identity.
export const ASSET_SEARCH_FIELDS=['name','id','type','scene','model','animation','confidence','provenance'];
export function parseAssetQuery(query,fields=ASSET_SEARCH_FIELDS){
  if(!Array.isArray(fields)||!fields.length||fields.length>32||fields.some(field=>typeof field!=='string'||!/^[_a-z]+$/.test(field))||new Set(fields).size!==fields.length)throw Error('Invalid search field vocabulary.');
  if(typeof query!=='string'||query.length>2048)throw new Error('Asset search is limited to 2048 characters.');
  const tokens=[];let token='',quoted=false,escaped=false,started=false,literal=false;
  const finish=()=>{if(!started)return;let value=token,exclude=false;if(!literal&&value.startsWith('-')){exclude=true;value=value.slice(1);}if(!value)throw new Error('An exclusion needs a search term.');
    let field=null;const colon=value.indexOf(':');if(!literal&&colon>0&&value.slice(colon+1,colon+3)!=='//'){const prefix=value.slice(0,colon).toLowerCase();if(fields.includes(prefix)){field=prefix;value=value.slice(colon+1);}else if(!value.includes('://'))throw new Error(`Unknown asset search field: ${prefix}.`);}
    if(!value)throw new Error('A field filter needs a value.');tokens.push({field,text:value.toLowerCase(),exclude});if(tokens.length>32)throw new Error('Asset search is limited to 32 terms.');token='';started=false;literal=false;};
  for(const char of query){if(escaped){token+=char;escaped=false;started=true;}else if(char==='\\'&&quoted){escaped=true;}else if(char==='"'){if(!started)literal=true;quoted=!quoted;started=true;}else if(/\s/.test(char)&&!quoted)finish();else{token+=char;started=true;}}
  if(quoted||escaped)throw new Error('Close the quoted asset search phrase.');finish();return tokens;
}
function values(value){return value===undefined||value===null?'':typeof value==='string'?value:JSON.stringify(value);}
export function assetSearchIndex(record){
  const data=record.data??{},variants=record.projectMembership?.variants??[],sources=[data,...variants.map(variant=>variant.record)],confidences=[],models=[],animations=[];
  const visit=(value,key='')=>{if(value===null||value===undefined)return;if(key==='confidence'&&typeof value==='string')confidences.push(value);
    if(typeof value==='string'){if(value.startsWith('asset://')&&value.includes('/models/'))models.push(value);if(value.startsWith('animation://'))animations.push(value);return;}
    if(Array.isArray(value)){for(const item of value)visit(item,key);}else if(typeof value==='object'){for(const [name,item] of Object.entries(value))visit(item,name);}};
  visit(record);if(record.type==='model')models.push(record.id);
  const fields={name:[record.label,...sources.map(source=>source?.name)],id:[record.id],type:[record.type,data.asset_kind],scene:[record.sceneId,record.source,record.authoredRecord?.source_scene,...sources.map(source=>source?.source_record?.prot_entry_name),...(record.projectMembership?.scene_ids??[])],model:models,animation:animations,confidence:confidences,
    provenance:[...sources.flatMap(source=>[source?.source_record,source?.claims,source?.components?.RetailMetadata]),record.authoredRecord?.source_record,
      ...variants.map(({scene_id,source_import_sha256,source_catalog_key})=>({scene_id,source_import_sha256,source_catalog_key}))]};
  return Object.fromEntries([['all',values(record).toLowerCase()],...Object.entries(fields).map(([key,items])=>[key,items.map(values).join(' ').toLowerCase()])]);
}
export function assetMatchesQuery(record,tokens){const index=assetSearchIndex(record);return tokens.every(token=>{const match=index[token.field??'all'].includes(token.text);return token.exclude?!match:match;});}
