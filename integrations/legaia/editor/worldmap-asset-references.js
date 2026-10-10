import {decodeWorldmapAssets,worldmapProjectRecords} from './worldmap-assets.js';
import {createReferenceTrail} from './asset-references.js';

const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const relations={owns_native_source_record:'Owns native source record',owns_source_seed:'Owns source seed'};
export function qualifyGlobalAssetReferenceRecord(record,graph){
  const selected=graph.assets.find(n=>n.id===record?.id);
  if(!selected||record.type!=='worldmap'||record.sceneId!==null&&record.sceneId!==undefined||record.projectGlobal?.sourceKey!==graph.source_key||!same(selected,record.data))throw Error('Selected global asset changed. Refresh project resources.');
  return record;
}
export function decodeGlobalAssetReferences(value,assetId,context){
  const keys=['schema_version','asset_id','source_key','read_only','global_worldmap_index','incoming','outgoing'];
  if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==keys.length||keys.some(k=>!Object.hasOwn(value,k))||value.schema_version!=='legaia.global-asset-references.v1'||value.asset_id!==assetId||value.source_key!==context.sourceKey||value.read_only!==true)throw Error('Global reference identity or source changed.');
  const graph=decodeWorldmapAssets(value.global_worldmap_index,context);
  if(!graph.assets.some(n=>n.id===assetId)||!same(value.incoming,graph.references.filter(e=>e.target_id===assetId))||!same(value.outgoing,graph.references.filter(e=>e.source_id===assetId)))throw Error('Global reference neighborhood differs from its complete ownership graph.');
  if(new TextEncoder().encode(JSON.stringify(value)).byteLength>32*1024*1024)throw Error('Global reference report exceeds 32 MiB.');
  return structuredClone(value);
}
export function filterGlobalAssetReferences(report,{direction='all',query=''}={}){
  if(!['all','incoming','outgoing'].includes(direction)||typeof query!=='string'||query.length>512)throw Error('Global reference filters exceed their supported bounds.');
  const terms=query.trim().toLowerCase().split(/\s+/).filter(Boolean);if(terms.length>32)throw Error('Reference search is limited to 32 terms.');
  const nodes=new Map(report.global_worldmap_index.assets.map(n=>[n.id,n]));
  const rows=(name,target)=>direction!=='all'&&direction!==name?[]:report[name].filter(edge=>{
    const node=nodes.get(edge[target]);const text=[node.id,node.name,node.resource_role,node.source_scene,relations[edge.kind],JSON.stringify(edge)].join(' ').toLowerCase();return terms.every(term=>text.includes(term));
  });
  return structuredClone({incoming:rows('incoming','source_id'),outgoing:rows('outgoing','target_id')});
}
export function globalAssetReferenceDownload(value,assetId,context){
  const report=decodeGlobalAssetReferences(value,assetId,context),name=assetId.replace(/[^a-z0-9_-]/gi,'_').slice(-100);
  const text=JSON.stringify(report,null,2)+'\n';if(new TextEncoder().encode(text).byteLength>32*1024*1024)throw Error('Global reference download exceeds 32 MiB.');
  return {filename:`legaia-references-global-${name}-${context.sourceKey.slice(0,12)}.json`,text};
}

// Global source ownership has no imported-scene scope or field navigation.
export function openGlobalAssetReferences({record,index,getState,busy,onNavigate,onError=()=>{},request=fetch}){
  const state=getState();if(busy()||!state.capabilities?.asset_references||!state.capabilities?.worldmap_placements)return;
  const context={sourceKey:state.project_assets_source_key,projectPath:state.project?.path},graph=decodeWorldmapAssets(index,context);
  qualifyGlobalAssetReferenceRecord(record,graph);
  const graphSnapshot=JSON.stringify(graph),trail=createReferenceTrail(record),dialog=document.createElement('dialog');dialog.id='asset-references-dialog';dialog.className='project-dialog';
  let controller=null,generation=0,accepted=null,loading=false,saving=false;
  const current=()=>dialog.isConnected&&dialog.open&&getState().project_assets_source_key===context.sourceKey&&getState().project?.path===context.projectPath&&getState().capabilities?.asset_references===true&&getState().capabilities?.worldmap_placements===true;
  const valid=()=>current()&&!loading&&!saving&&!busy()&&accepted?.asset_id===trail.current().id;
  const title=document.createElement('h2'),close=document.createElement('button'),heading=document.createElement('div');heading.className='dialog-heading';close.textContent='Close';close.onclick=()=>dialog.close();heading.append(title,close);
  const note=document.createElement('p');note.textContent='Global world-map sources · Derived ownership only. Imported field-scene membership, runtime residency and gameplay reachability remain separate.';
  const history=document.createElement('nav');history.className='dialog-actions';history.setAttribute('aria-label','Reference exploration history');const back=document.createElement('button'),forward=document.createElement('button'),path=document.createElement('p');back.textContent='Back in references';forward.textContent='Forward in references';path.dataset.referenceTrail='';path.style.overflowWrap='anywhere';history.append(back,forward);
  const tools=document.createElement('div');tools.className='reference-filters';const directionLabel=document.createElement('label'),direction=document.createElement('select');directionLabel.textContent='Reference direction';direction.setAttribute('aria-label','Reference direction');for(const [value,text] of [['all','Both directions'],['outgoing','Dependencies'],['incoming','Referenced by']]){const option=document.createElement('option');option.value=value;option.textContent=text;direction.append(option);}directionLabel.append(direction);
  const searchLabel=document.createElement('label'),search=document.createElement('input');search.type='search';search.maxLength=512;search.setAttribute('aria-label','Search recorded references');search.placeholder='Labels, IDs, roles, kingdoms or hashes';searchLabel.textContent='Search recorded references';searchLabel.append(search);tools.append(directionLabel,searchLabel);
  const save=document.createElement('button'),status=document.createElement('p'),counts=document.createElement('p'),content=document.createElement('div');save.textContent='Save full reference report';save.title='Save the selected neighborhood and complete qualified ownership graph. Filters do not trim the file.';status.setAttribute('role','status');counts.setAttribute('role','status');counts.dataset.referenceFilterCount='';
  const trace=document.createElement('button');trace.textContent='Trace global relationships…';
  dialog.append(heading,note,history,path,tools,save,trace,status,counts,content);document.body.append(dialog);dialog.showModal();
  dialog.addEventListener('close',()=>{generation++;controller?.abort();accepted=null;dialog.remove();});
  const controls=()=>{const locked=!valid(),historyLocked=!current()||loading||saving||busy();back.disabled=historyLocked||!trail.canBack();forward.disabled=historyLocked||!trail.canForward();save.disabled=trace.disabled=locked;direction.disabled=search.disabled=locked;title.textContent=`Asset references · ${trail.current().label}`;path.textContent=`Recent reference trail ${trail.position()+1}/${trail.entries().length} (up to 32): ${trail.entries().map(n=>n.label).join(' → ')} · ${trail.current().id}`;};
  trace.onclick=async()=>{if(!valid()||!dialog.contains(trace))return;const report=accepted,revision=generation,selected=worldmapProjectRecords(report.global_worldmap_index).find(n=>n.id===trail.current().id);try{const {openGlobalReferenceTrace}=await import('./worldmap-reference-trace.js');if(!valid()||accepted!==report||generation!==revision||!dialog.contains(trace))return;openGlobalReferenceTrace({record:selected,index:report.global_worldmap_index,getState,busy,request,onError,onNavigate:async node=>{if(!valid()||accepted!==report||generation!==revision)throw Error('Global reference exploration changed. Reopen references.');dialog.close();await onNavigate(node);}});}catch(error){if(current())status.textContent=error.message;}};
  const render=()=>{
    content.replaceChildren();counts.textContent='';controls();if(!current()){status.textContent='Project sources changed. Reopen asset references.';return;}if(!accepted)return;
    const report=accepted,filterKey=JSON.stringify([direction.value,search.value]);let filtered;
    try{filtered=filterGlobalAssetReferences(report,{direction:direction.value,query:search.value});search.setAttribute('aria-invalid','false');}catch(error){search.setAttribute('aria-invalid','true');status.textContent=error.message;return;}
    const nodes=new Map(worldmapProjectRecords(report.global_worldmap_index).map(n=>[n.id,n]));
    const rowCurrent=element=>valid()&&accepted===report&&content.contains(element)&&filterKey===JSON.stringify([direction.value,search.value]);
    status.textContent=`Recorded ownership · ${report.global_worldmap_index.coverage.asset_count} global assets / ${report.global_worldmap_index.coverage.reference_count} links across three kingdoms. Complete native ownership is recorded per owner; excluded source cells do not grant authoring permission.`;
    for(const [label,name,target] of [['Dependencies','outgoing','target_id'],['Referenced by','incoming','source_id']]){
      if(direction.value!=='all'&&direction.value!==name)continue;const section=document.createElement('section'),heading=document.createElement('h3');section.dataset.referenceDirection=name;heading.textContent=`${label} (${filtered[name].length}/${report[name].length})`;section.append(heading);
      if(!filtered[name].length){const empty=document.createElement('p');empty.textContent=report[name].length?'No matches for these filters.':'No recorded relationships in this coverage.';section.append(empty);}
      for(const edge of filtered[name]){
        const node=nodes.get(edge[target]),row=document.createElement('div'),open=document.createElement('button'),explore=document.createElement('button'),description=document.createElement('p');row.dataset.globalReferenceTarget=node.id;open.textContent=node.label;open.title=node.id;open.dataset.referenceTarget=node.id;explore.textContent='Explore references';explore.dataset.exploreReferenceTarget=node.id;
        open.onclick=async()=>{if(!rowCurrent(open))return;dialog.close();try{await onNavigate(node);}catch(error){onError(error);}};
        explore.onclick=()=>{if(!rowCurrent(explore))return;if(trail.visit(node)){direction.value='all';search.value='';void load();}};
        description.textContent=`${relations[edge.kind]} · Derived source · ${node.data.source_scene} · ${node.data.resource_role.replaceAll('_',' ')}`;description.style.overflowWrap='anywhere';
        const evidence=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Recorded provenance';pre.className='diagnostic-detail';pre.textContent=JSON.stringify(edge,null,2);evidence.append(summary,pre);row.append(open,description,explore,evidence);section.append(row);
      }
      content.append(section);
    }
    counts.textContent=`Showing ${filtered.incoming.length+filtered.outgoing.length} of ${report.incoming.length+report.outgoing.length} recorded relationships. Filters affect rows only; saved evidence retains the full graph.`;
  };
  const load=async()=>{
    const revision=++generation;controller?.abort();const active=new AbortController();controller=active;const selected=trail.current();accepted=null;loading=true;content.replaceChildren();counts.textContent='';status.textContent='Verifying global source references…';controls();
    try{const response=await request('/api/asset-references',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:selected.id,scope:'global',source_key:context.sourceKey}),signal:active.signal}),value=await response.json();
      if(active.signal.aborted||revision!==generation||!dialog.open||trail.current().id!==selected.id)return;if(!current())throw Error('Project sources changed. Reopen asset references.');if(!response.ok||value.error)throw Error(value.error||'Global reference verification failed.');
      const report=decodeGlobalAssetReferences(value,selected.id,context);if(JSON.stringify(report.global_worldmap_index)!==graphSnapshot)throw Error('Global ownership sources changed. Refresh project resources.');accepted=report;render();
    }catch(error){if(error.name!=='AbortError'&&revision===generation&&dialog.open&&!active.signal.aborted)status.textContent=error.message;}finally{if(revision===generation&&dialog.open){loading=false;controls();}}
  };
  const move=offset=>{if(!current()||loading||saving||busy()||offset<0&&!trail.canBack()||offset>0&&!trail.canForward())return;trail.move(trail.position()+offset);direction.value='all';search.value='';void load();};back.onclick=()=>move(-1);forward.onclick=()=>move(1);direction.onchange=render;search.oninput=render;
  save.onclick=async()=>{
    if(!valid()||!dialog.contains(save))return;const report=accepted,revision=generation,identifier=trail.current().id;saving=true;controls();
    try{const response=await request('/api/state'),value=await response.json();if(!current()||revision!==generation||accepted!==report||trail.current().id!==identifier)return;if(busy()||!response.ok||value.error||value.project_assets_source_key!==context.sourceKey||value.project?.path!==context.projectPath)throw Error('Project sources changed before saving references. Reopen asset references.');
      const file=globalAssetReferenceDownload(report,identifier,context),url=URL.createObjectURL(new Blob([file.text],{type:'application/json;charset=utf-8'})),link=document.createElement('a');link.href=url;link.download=file.filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent='Saved full global reference report. Project state unchanged.';
    }catch(error){if(current()&&revision===generation)status.textContent=error.message;}finally{saving=false;if(dialog.open)controls();}
  };
  void load();return dialog;
}
