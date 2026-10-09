import {decodeAssetReferences,assetReferenceNavigationNode} from './asset-references.js';
const RELATIONS=new Set(['static_material_texture_source','effective_material_texture_source']);
export function materialBindingRows(value,{assetId,sourceKey,type}){
 if(!['model','texture'].includes(type))throw Error('Material bindings require a model or texture asset.');
 const report=decodeAssetReferences(value,assetId,sourceKey,'project'),nodes=new Map(report.nodes.map(node=>[node.id,node]));
 const root=nodes.get(assetId);if(!root||root.kind!==type)throw Error('Material binding root differs from the selected asset.');
 const rows=(type==='model'?report.outgoing:report.incoming).filter(edge=>RELATIONS.has(edge.kind)).map(edge=>{
  const target=nodes.get(edge[type==='model'?'target_id':'source_id']);
  if(target.kind!==(type==='model'?'texture':'model'))throw Error('Material binding counterpart has a conflicting asset type.');
  return {id:edge.id,layer:edge.kind==='static_material_texture_source'?'retail':'current',sceneId:edge.scene_id,materialIndex:edge.material_evidence.material_index,target:assetReferenceNavigationNode(target,edge,'project'),evidence:structuredClone(edge)};
 });
 return {rows,coverage:structuredClone(report.coverage),limitations:[...report.limitations]};
}
export function mountMaterialBindings(host,{record,getState,current,busy,onInspect,onError=()=>{},request=fetch}){
 if(!['model','texture'].includes(record.type)||!getState().capabilities?.asset_references)return null;
 const key=getState().asset_reference_source_key,controller=new AbortController(),section=host.ownerDocument.createElement('section'),document=host.ownerDocument;
 section.dataset.materialBindings='';let disposed=false,pending=false,result=null,page=0;
 const fresh=()=>!disposed&&section.isConnected&&current()&&key===getState().asset_reference_source_key&&getState().capabilities?.asset_references===true;
 const heading=document.createElement('h4');heading.textContent='Recorded material bindings';const note=document.createElement('p');note.textContent='Static TIM address matches from SDK evidence. Retail and separately decoded Current remain distinct; missing matches do not prove absence of users or runtime texture residency.';
 const controls=document.createElement('div');controls.className='dialog-actions';const layer=document.createElement('select');layer.setAttribute('aria-label','Material binding layer');for(const [value,label] of [['all','Retail and Current'],['retail','Retail source matches'],['current','Current source matches']]){const option=document.createElement('option');option.value=value;option.textContent=label;layer.append(option);}
 const previous=document.createElement('button'),next=document.createElement('button');previous.textContent='Previous bindings';next.textContent='Next bindings';previous.type=next.type='button';controls.append(layer,previous,next);
 const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Verifying project material sources…';const list=document.createElement('div');list.dataset.materialBindingRows='';section.append(heading,note,controls,status,list);host.append(section);
 const lock=()=>{for(const input of controls.children)input.disabled=true;for(const button of list.querySelectorAll('button'))button.disabled=true;};lock();
 const render=()=>{
  list.replaceChildren();if(!result)return;const rows=result.rows.filter(row=>layer.value==='all'||row.layer===layer.value),pages=Math.max(1,Math.ceil(rows.length/64));page=Math.min(page,pages-1);const blocked=pending||busy()||!fresh();layer.disabled=blocked;previous.disabled=blocked||page===0;next.disabled=blocked||page>=pages-1;
  status.textContent=`${rows.length} / ${result.rows.length} recorded material matches · Page ${page+1} / ${pages} · ${result.coverage.scenes.filter(row=>row.status==='available').length} / ${result.coverage.scenes.length} source catalogs available`;
  for(const row of rows.slice(page*64,(page+1)*64)){
   const item=document.createElement('div'),button=document.createElement('button');item.dataset.materialBindingEdge=row.id;button.type='button';button.title=row.target.id;button.textContent=`${row.layer==='retail'?'Retail':'Current'} · Material ${row.materialIndex} · ${row.target.label} · ${row.sceneId}`;Object.assign(button.style,{maxWidth:'100%',whiteSpace:'normal',overflowWrap:'anywhere',textAlign:'left'});button.disabled=blocked||!row.target.available;
   button.onclick=async()=>{if(button.disabled||pending||busy()||!fresh()||!list.contains(button)||layer.value!=='all'&&layer.value!==row.layer)return;pending=true;lock();try{await onInspect(structuredClone(row.target));}catch(error){onError(error);}finally{pending=false;if(fresh())render();}};
   const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Recorded material provenance';pre.className='diagnostic-detail';pre.textContent=JSON.stringify(row.evidence,null,2);details.append(summary,pre);item.append(button,details);list.append(item);
  }
  if(!rows.length){const empty=document.createElement('p');empty.textContent='No recorded material matches in this layer and coverage.';list.append(empty);}
 };
 layer.onchange=()=>{if(pending||busy()||!fresh())return;page=0;render();};previous.onclick=()=>{if(previous.disabled||busy()||!fresh())return;page--;render();};next.onclick=()=>{if(next.disabled||busy()||!fresh())return;page++;render();};
 const ready=(async()=>{try{const response=await request('/api/asset-references',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id,scope:'project'}),signal:controller.signal}),value=await response.json();if(!fresh())return;if(!response.ok||value.error)throw Error(value.error??'Material source verification failed.');result=materialBindingRows(value,{assetId:record.id,sourceKey:key,type:record.type});render();}catch(error){if(!controller.signal.aborted&&fresh()){lock();status.textContent=error.message;}}})();
 return {ready,dispose(){disposed=true;controller.abort();lock();}};
}
