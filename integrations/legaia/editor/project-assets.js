// A read-only project index with distinct imported and authored records. Each selected record keeps one scene's source binding.
import {createAssetResourceDiscovery} from './asset-resource-discovery.js';
const MAX_METADATA_BYTES=32*1024*1024;
const kinds=new Set(['audio','scene','actor','model','texture','animation','script','dialogue','flag','transition','collision','trigger','region','worldmap']);
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const text=(value,max=8192)=>typeof value==='string'&&value.length>0&&value.length<=max;
const sceneId=value=>typeof value==='string'&&value.startsWith('scene://')&&value.length>8&&value.length<=1024&&!/[\x00-\x20\x7f-\uffff]/.test(value);
const clone=value=>structuredClone(value);
const fail=message=>{throw new Error(message);};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const notes=value=>Array.isArray(value)&&value.length<=256&&value.every(line=>text(line));

export function projectAssetsContext(value){
  const keys=['projectPath','sourceKey','scenes'];
  if(!object(value)||!keys.every(key=>Object.hasOwn(value,key))||Object.keys(value).some(key=>!keys.includes(key)&&key!=='activeSceneId')||!text(value.projectPath,32768)||!hash(value.sourceKey)||!Array.isArray(value.scenes)||value.scenes.length>64||Object.hasOwn(value,'activeSceneId')&&value.activeSceneId!==null&&!sceneId(value.activeSceneId))fail('Project assets require the current project, source key and imported scene identities.');
  const ids=new Set();for(const row of value.scenes){if(!exact(row,['id','name'])||!sceneId(row.id)||!text(row.name,256)||ids.has(row.id))fail('Imported project scene identities are invalid or duplicated.');ids.add(row.id);}
  return clone(value);
}
function sourceIdentity(context){return {projectPath:context.projectPath,sourceKey:context.sourceKey,scenes:context.scenes.map(({id,name})=>({id,name})).sort((a,b)=>a.id.localeCompare(b.id))};}

export function decodeProjectAssets(value,context){
  context=projectAssetsContext(context);
  const keys=['schema_version','source_key','project_path','metadata_only','read_only','scenes','assets','coverage','limitations'];
  if(!exact(value,keys)||value.schema_version!=='legaia.project-assets.v1'||value.source_key!==context.sourceKey||value.project_path!==context.projectPath||value.metadata_only!==true||value.read_only!==true||!Array.isArray(value.scenes)||value.scenes.length>64||!Array.isArray(value.assets)||value.assets.length>16384||!notes(value.limitations))fail('Project asset sources changed or returned invalid metadata.');
  if(new TextEncoder().encode(JSON.stringify(value)).byteLength>MAX_METADATA_BYTES)fail('Project asset metadata exceeds the 32 MiB budget.');
  const scenes=new Map(),counts=new Map(),expected=new Map(context.scenes.map(row=>[row.id,row.name]));
  for(const row of value.scenes){
    if(!exact(row,['id','name','import_sha256','status','record_count','limitations'])||!sceneId(row.id)||scenes.has(row.id)||expected.get(row.id)!==row.name||!hash(row.import_sha256)||!['available','partial','unavailable'].includes(row.status)||!integer(row.record_count,0,16384)||!notes(row.limitations))fail('Project asset scene coverage differs from its imported source.');
    scenes.set(row.id,row);counts.set(row.id,0);
  }
  if(scenes.size!==expected.size)fail('Project assets omit an imported scene coverage record.');
  const identities=new Set(),assetsById=new Map(value.assets.map(row=>[row?.id,row]));let memberships=0;
  for(const asset of value.assets){
    if(!exact(asset,['id','kind','label','scene_ids','variants'])||!text(asset.id,1024)||identities.has(asset.id)||!kinds.has(asset.kind)||!text(asset.label,4096)||!Array.isArray(asset.scene_ids)||!integer(asset.scene_ids.length,1,64)||new Set(asset.scene_ids).size!==asset.scene_ids.length||asset.scene_ids.some(id=>!scenes.has(id))||!Array.isArray(asset.variants)||asset.variants.length!==asset.scene_ids.length)fail('Project asset identity, kind or scene memberships conflict.');
    const variantScenes=new Set();
    for(const variant of asset.variants){
      if(!exact(variant,['scene_id','source_import_sha256','source_catalog_key','record'])||!asset.scene_ids.includes(variant.scene_id)||variantScenes.has(variant.scene_id)||variant.source_import_sha256!==scenes.get(variant.scene_id)?.import_sha256||!(variant.source_catalog_key===null||hash(variant.source_catalog_key))||!object(variant.record)||variant.record.id!==asset.id||variant.record.semantic_id!==asset.id||variant.record.kind!==asset.kind||variant.record.asset_kind!==asset.kind)fail('Project asset variant differs from its scene import or source record identity.');
      const record=variant.record;
      if(asset.id.startsWith('authored-actor://')||asset.kind==='actor'&&(Object.hasOwn(record,'draft')||record.layer==='authored')){
        const draft=record.authored;
        if(asset.kind!=='actor'||asset.variants.length!==1||!/^authored-actor:\/\/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(asset.id)||record.layer!=='authored'||record.draft!==true||variant.source_catalog_key!==null||Object.hasOwn(record,'source_record')||record.scene_id!==variant.scene_id||!exact(draft,['scene_id','donor_entity_id','position','name'])||draft.scene_id!==variant.scene_id||draft.donor_entity_id!==record.donor_entity_id||draft.name!==record.name||!text(draft.name,120)||!exact(draft.position,['x','z'])||['x','z'].some(axis=>!integer(draft.position[axis],64,16384)||draft.position[axis]%64))fail('Authored NPC project asset differs from its project identity, scene or native placement.');
        const model=record.model_reference;
        if(model!==undefined&&model!==null&&(model.source_id!==asset.id||model.source_name!==record.name||model.scene_id!==variant.scene_id||model.kind!=='draft_initial_model_assignment'||model.imported!==false||model.effective!==true||model.effective_donor_id!==draft.donor_entity_id||model.runtime_binding!=='not_asserted'||typeof model.target_id!=='string'||!model.target_id.startsWith('asset://')))fail('NPC project model reference differs from its recorded donor assignment.');
        const donor=assetsById.get(draft.donor_entity_id);
        if(donor?.kind!=='actor'||!Array.isArray(donor.variants)||!donor.variants.some(row=>row.scene_id===variant.scene_id&&row.record.layer!=='authored'&&!Object.hasOwn(row.record,'draft')))fail('Authored NPC project asset donor is absent from its imported scene.');
      }
      variantScenes.add(variant.scene_id);counts.set(variant.scene_id,counts.get(variant.scene_id)+1);memberships++;if(memberships>65536)fail('Project asset scene memberships exceed their bounded budget.');
    }
    identities.add(asset.id);
  }
  for(const [id,scene] of scenes)if(scene.record_count!==counts.get(id))fail('Scene coverage counts differ from the retained asset memberships.');
  const coverage={imported_scene_count:scenes.size,available_scene_count:value.scenes.filter(row=>row.status==='available').length,partial_scene_count:value.scenes.filter(row=>row.status==='partial').length,unavailable_scene_count:value.scenes.filter(row=>row.status==='unavailable').length,asset_count:value.assets.length,membership_count:memberships};
  if(!exact(value.coverage,Object.keys(coverage))||Object.entries(coverage).some(([key,count])=>value.coverage[key]!==count))fail('Project asset coverage totals differ from the verified records.');
  return clone(value);
}

/** Shared IDs retain every membership; data always comes from one complete variant. */
export function projectAssetRecords(report,filter='all',activeSceneId=null,preferredScenes=new Map()){
  if(filter!=='all'&&!report.scenes.some(row=>row.id===filter))fail('Choose an imported source scene for project resource filtering.');
  const scenes=new Map(report.scenes.map(row=>[row.id,row]));
  return report.assets.filter(asset=>filter==='all'||asset.scene_ids.includes(filter)).map(asset=>{
    const preferred=preferredScenes.get(asset.id),chosenId=filter!=='all'?filter:asset.scene_ids.includes(preferred)?preferred:asset.scene_ids.includes(activeSceneId)?activeSceneId:[...asset.scene_ids].sort()[0],variant=asset.variants.find(row=>row.scene_id===chosenId);
    const source=asset.scene_ids.length>1?`Shared across ${asset.scene_ids.length} imported scenes · ${scenes.get(chosenId).name}`:scenes.get(chosenId).name;
    return {id:asset.id,type:asset.kind,label:asset.label,source,sceneId:chosenId,data:clone(variant.record),projectMembership:{scene_ids:clone(asset.scene_ids),variants:clone(asset.variants),chosenSceneId:chosenId,sourceKey:report.source_key}};
  });
}

// Source activation uses one retained variant, never an ID-prefix membership guess.
export function projectAssetVariant(record,context){
  context=projectAssetsContext(context);
  const membership=record?.projectMembership,variant=membership?.variants?.find(row=>row.scene_id===record.sceneId);
  if(!membership||membership.sourceKey!==context.sourceKey||membership.chosenSceneId!==record.sceneId||!membership.scene_ids?.includes(record.sceneId)||!context.scenes.some(scene=>scene.id===record.sceneId)||!variant||variant.record?.id!==record.id||variant.record?.kind!==record.type)fail('Project asset source changed. Refresh project resources before opening this asset.');
  return clone(variant);
}
const ordered=value=>Array.isArray(value)?value.map(ordered):object(value)?Object.fromEntries(Object.keys(value).sort().map(key=>[key,ordered(value[key])])):value;
export function qualifyProjectCatalogVariant(variant,record,catalogKey){
  if(!hash(variant?.source_catalog_key)||variant.source_catalog_key!==catalogKey||!object(record)||record.scene_id!==variant.scene_id||record.semantic_id!==variant.record?.id||record.asset_kind!==variant.record?.kind)fail('Selected project membership differs from the refreshed scene catalog. Refresh project resources.');
  const normalized=clone(record);delete normalized.catalog_limitations;
  const id=normalized.semantic_id,kind=normalized.asset_kind;
  let name=normalized.name;if(!name||name.length>256||/[\x00-\x1f\x7f]/.test(name))name=kind[0].toUpperCase()+kind.slice(1)+' '+id.split('/').at(-1).slice(0,240);
  Object.assign(normalized,{id,semantic_id:id,kind,asset_kind:kind,name});
  if(!same(ordered(normalized),ordered(variant.record)))fail('Selected project source metadata changed. Refresh project resources before opening its inspector.');
  return true;
}

function element(tag,label){const node=document.createElement(tag);if(label!==undefined)node.textContent=label;return node;}
export function mountProjectAssets({host,getContext,busy,setBusy,onChange=()=>{},onError=()=>{},getUnavailableReason=()=>null,schedule}){
  if(!host||[getContext,busy,setBusy,onChange,onError,getUnavailableReason].some(callback=>typeof callback!=='function'))fail('Project asset controls require source and lifecycle callbacks.');
  const section=element('section');section.className='asset-scope project-assets-scope';section.dataset.projectAssets='';Object.assign(section.style,{gridColumn:'1 / -1',minWidth:'0'});
  const controls=element('div');Object.assign(controls.style,{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(min(100%,180px),1fr))',gap:'7px',minWidth:'0'});
  const scopeLabel=element('label','Asset database scope'),scopeInput=element('select');scopeInput.setAttribute('aria-label','Asset database scope');for(const [value,label] of [['active','Active scene resources'],['project','Project resources']]){const option=element('option',label);option.value=value;scopeInput.append(option);}scopeInput.value='active';scopeLabel.append(scopeInput);
  const filterLabel=element('label','Source scene'),filterInput=element('select');filterInput.setAttribute('aria-label','Imported resource scene filter');filterLabel.append(filterInput);const refresh=element('button','Refresh project resources');refresh.type='button';refresh.dataset.action='refresh-project-resources';
  for(const select of [scopeInput,filterInput])Object.assign(select.style,{width:'100%',minWidth:'0'});Object.assign(refresh.style,{whiteSpace:'normal',textAlign:'left'});controls.append(scopeLabel,filterLabel,refresh);
  const status=element('p');status.className='field-note';status.dataset.projectAssetCoverage='';status.setAttribute('role','status');const error=element('p');error.className='dialog-error';error.setAttribute('role','alert');const coverage=element('details'),summary=element('summary','Imported scene coverage and limits'),sceneRows=element('div');coverage.append(summary,sceneRows);section.append(controls,status,error,coverage);host.append(section);
  let scopeValue='active',filterValue='all',context=null,identity=null,report=null,controller=null,busyOwner=null,generation=0,disposed=false,pending=false,updating=false,mounting=true;
  const preferredScenes=new Map();
  const discovery=createAssetResourceDiscovery({getContext:()=>({key:identity===null?null:JSON.stringify(identity),eligible:!disposed&&scopeValue==='project'&&!!context?.scenes.length&&!error.textContent,busy:busy()!==false,loaded:report!==null,pending}),load:refreshReport,schedule,onError});
  const capture=()=>{try{return projectAssetsContext(getContext());}catch{return null;}};
  const fresh=()=>{const value=capture();return !disposed&&value!==null&&identity!==null&&same(identity,sourceIdentity(value));};
  const notify=()=>{if(!disposed&&!mounting)onChange();};
  const release=token=>{if(busyOwner===token){busyOwner=null;setBusy(false);}};
  function invalidate(){generation++;controller?.abort();controller=null;pending=false;report=null;preferredScenes.clear();sceneRows.replaceChildren();if(busyOwner)release(busyOwner);}
  function renderFilters(){
    filterInput.replaceChildren();const all=element('option','All imported scenes');all.value='all';filterInput.append(all);for(const scene of context?.scenes??[]){const option=element('option',scene.name);option.value=scene.id;filterInput.append(option);}if(filterValue!=='all'&&!context?.scenes.some(scene=>scene.id===filterValue))filterValue='all';filterInput.value=filterValue;
  }
  function renderCoverage(){
    filterLabel.hidden=refresh.hidden=coverage.hidden=scopeValue!=='project';
    status.hidden=scopeValue!=='project'&&context!==null;
    if(context===null){const reason=getUnavailableReason();status.textContent=typeof reason==='string'&&reason.length<=8192?reason:'Project source is unavailable.';return;}
    if(scopeValue!=='project'){status.textContent='Choose Project resources to discover imported project inventory.';return;}
    if(pending){status.textContent=`Verifying resources across ${context?.scenes.length??0} imported scenes…`;return;}
    if(!report){status.textContent=!context?'Project source is unavailable.':!context.scenes.length?'No imported scenes. Import scenes before refreshing project resources.':error.textContent?`Project resources are not verified. Refresh to retry ${context.scenes.length} imported scenes.`:`Project resources are not verified. Discovery will load ${context.scenes.length} imported scenes when the editor is ready.`;return;}
    const counts=report.coverage,filtered=filterValue==='all'?counts.asset_count:report.assets.filter(asset=>asset.scene_ids.includes(filterValue)).length;
    status.textContent=`${filtered} scoped / ${counts.asset_count} project identities · ${counts.membership_count} scene memberships · ${counts.available_scene_count} available / ${counts.partial_scene_count} partial / ${counts.unavailable_scene_count} unavailable of ${counts.imported_scene_count} imported scenes.`;
  }
  function renderScenes(){
    sceneRows.replaceChildren();if(!report)return;
    for(const scene of report.scenes){const item=element('details'),heading=element('summary',`${scene.name} · ${scene.status} · ${scene.record_count} records`);item.append(heading);const identity=element('p',`${scene.id} · import SHA-256 ${scene.import_sha256}`);identity.style.overflowWrap='anywhere';item.append(identity);for(const line of scene.limitations)item.append(element('p',line));sceneRows.append(item);}for(const line of report.limitations)sceneRows.append(element('p',line));
  }
  function updateState(){
    if(disposed||updating)return;updating=true;let changed=false;
    try{const next=capture(),nextIdentity=next===null?null:sourceIdentity(next);if(!same(identity,nextIdentity)){invalidate();identity=nextIdentity;context=next;error.textContent='';renderFilters();changed=true;}else if(context?.activeSceneId!==next?.activeSceneId){context=next;if(scopeValue==='project'&&report)changed=true;}else context=next;
      const blocked=context===null||busy()!==false;scopeInput.disabled=context===null||busy()!==false&&busyOwner===null;filterInput.disabled=blocked||scopeValue!=='project';refresh.disabled=blocked||scopeValue!=='project'||!context?.scenes.length;renderCoverage();
    }finally{updating=false;}
    if(changed)notify();
    discovery.request();
  }
  async function refreshReport(){
    updateState();if(disposed||scopeValue!=='project'||!fresh()||busy()!==false||pending||!context.scenes.length)return false;
    const ticket=++generation,expected=clone(context),token={};report=null;sceneRows.replaceChildren();pending=true;controller=new AbortController();const signal=controller.signal;busyOwner=token;setBusy(true);error.textContent='';notify();updateState();const valid=()=>fresh()&&generation===ticket&&!signal.aborted&&scopeValue==='project';
    try{const response=await fetch('/api/project-assets',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',signal});const raw=await response.text();if(new TextEncoder().encode(raw).byteLength>MAX_METADATA_BYTES)fail('Project asset metadata exceeds the 32 MiB budget.');const value=JSON.parse(raw);if(!response.ok||value?.error)fail(typeof value?.error==='string'?value.error:'Project resource verification failed.');if(!valid())return false;report=decodeProjectAssets(value,expected);renderScenes();notify();return true;}catch(value){if(valid()&&value?.name!=='AbortError'){report=null;sceneRows.replaceChildren();error.textContent=value?.message??String(value);onError(value instanceof Error?value:new Error(String(value)));notify();}return false;}finally{if(generation===ticket){controller=null;pending=false;}release(token);if(!disposed)updateState();}
  }
  scopeInput.onchange=()=>{if(disposed||!['active','project'].includes(scopeInput.value))return false;if(busy()!==false&&busyOwner===null){scopeInput.value=scopeValue;return false;}const next=scopeInput.value;if(next===scopeValue)return true;scopeValue=next;if(pending)invalidate();error.textContent='';updateState();notify();discovery.request(true);return true;};
  filterInput.onchange=()=>{if(disposed||scopeValue!=='project'||busy()!==false||!fresh()||filterInput.value!=='all'&&!context.scenes.some(scene=>scene.id===filterInput.value)){filterInput.value=filterValue;return false;}filterValue=filterInput.value;renderCoverage();notify();return true;};refresh.onclick=()=>refresh.disabled?false:refreshReport();
  function records(){updateState();return scopeValue==='project'&&report&&fresh()?projectAssetRecords(report,filterValue,context.activeSceneId??null,preferredScenes):[];}
  function chooseVariant(assetId,sceneId){updateState();if(disposed||scopeValue!=='project'||!report||!fresh()||busy()!==false||pending||filterValue!=='all'&&filterValue!==sceneId)return false;const asset=report.assets.find(row=>row.id===assetId);if(!asset?.scene_ids.includes(sceneId))return false;preferredScenes.set(assetId,sceneId);notify();return true;}
  function revealSource(sceneId){updateState();if(disposed||scopeValue!=='project'||!fresh()||busy()!==false||pending||!context.scenes.some(scene=>scene.id===sceneId))return false;if(filterValue!=='all'&&filterValue!==sceneId){filterValue=sceneId;filterInput.value=sceneId;renderCoverage();notify();}return true;}
  function sourceReport(){updateState();return report&&fresh()?clone(report):null;}
  function dispose(){if(disposed)return;disposed=true;discovery.dispose();invalidate();section.remove();}
  updateState();mounting=false;return {scope:()=>scopeValue,filter:()=>filterValue,chooseVariant,revealSource,records,sourceReport,updateState,dispose};
}
