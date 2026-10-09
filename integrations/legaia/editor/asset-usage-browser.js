const PAGE_SIZE=64;
export function filterAssetUsage(references,{layer='all',scene='all',search='',page=0}={}){
 if(!Array.isArray(references)||references.length>65536||!['all','retail','current'].includes(layer)||typeof scene!=='string'||typeof search!=='string'||search.length>1024||!Number.isSafeInteger(page)||page<0)throw Error('Asset usage filters require bounded recorded references.');
 const seen=new Set();
 for(const ref of references){
  if(typeof ref?.source_id!=='string'||!ref.source_id||ref.source_id.length>1024||typeof ref.scene_id!=='string'||!ref.scene_id||ref.scene_id.length>1024||typeof ref.imported!=='boolean'||typeof ref.effective!=='boolean'||!ref.imported&&!ref.effective||seen.has(ref.source_id))throw Error('Asset usage has ambiguous identities or missing layer metadata.');
  seen.add(ref.source_id);
 }
 const text=search.toLowerCase(),matching=references.filter(ref=>(layer==='all'||ref[layer==='retail'?'imported':'effective'])&&(scene==='all'||ref.scene_id===scene)&&[ref.source_id,ref.source_name??'',ref.scene_id].join(' ').toLowerCase().includes(text));
 const pages=Math.max(1,Math.ceil(matching.length/PAGE_SIZE)),index=Math.min(page,pages-1);
 return {total:references.length,matching:matching.length,page:index,pages,rows:structuredClone(matching.slice(index*PAGE_SIZE,(index+1)*PAGE_SIZE))};
}

export function mountAssetUsageBrowser(host,{references,scenes,current,busy,onActivate,onError}){
 host.dataset.assetUsageBrowser='';
 const document=host.ownerDocument,controls=document.createElement('div'),list=document.createElement('div'),status=document.createElement('p');controls.className='dialog-actions';status.className='field-note';status.setAttribute('role','status');list.dataset.assetUsageRows='';
 const layer=document.createElement('select'),scene=document.createElement('select'),search=document.createElement('input'),previous=document.createElement('button'),next=document.createElement('button');
 layer.setAttribute('aria-label','Asset usage layer');scene.setAttribute('aria-label','Asset usage source scene');search.setAttribute('aria-label','Search asset users');search.type='search';search.maxLength=1024;search.placeholder='Actor name, ID or source scene';previous.textContent='Previous users';next.textContent='Next users';
 for(const [value,label] of [['all','Retail and Current'],['retail','Retail'],['current','Current']]){const option=document.createElement('option');option.value=value;option.textContent=label;layer.append(option);}
 const sceneIds=[...new Set(references.map(ref=>ref.scene_id))];for(const id of ['all',...sceneIds]){const option=document.createElement('option');option.value=id;option.textContent=id==='all'?'All source scenes':scenes.find(row=>row.id===id)?.name??id;scene.append(option);}
 for(const control of [layer,scene,search])Object.assign(control.style,{maxWidth:'100%',minWidth:'0'});Object.assign(search.style,{flex:'1 1 180px'});
 controls.append(layer,scene,search,previous,next);host.append(controls,status,list);let page=0,pending=false,disposed=false,mounting=true;
 const fresh=()=>!disposed&&host.isConnected&&current();
 function render(){
  const report=filterAssetUsage(references,{layer:layer.value,scene:scene.value,search:search.value,page});page=report.page;const blocked=pending||busy()||!mounting&&!fresh();
  for(const control of [layer,scene,search])control.disabled=blocked;previous.disabled=blocked||page===0;next.disabled=blocked||page>=report.pages-1;
  status.textContent=`${report.matching} / ${report.total} recorded users · Page ${page+1} / ${report.pages}`;list.replaceChildren();
  for(const ref of report.rows){const button=document.createElement('button');button.type='button';button.dataset.assetUsageActor=ref.source_id;button.title=ref.source_id;const draft=['draft_initial_model_assignment','draft_initial_animation_assignment'].includes(ref.kind);button.textContent=`${ref.source_name??ref.source_id} · ${draft?'NPC draft · ':''}${ref.imported?'Retail':''}${ref.imported&&ref.effective?' + ':''}${ref.effective?'Current':''} · ${scenes.find(row=>row.id===ref.scene_id)?.name??ref.scene_id}`;Object.assign(button.style,{maxWidth:'100%',whiteSpace:'normal',overflowWrap:'anywhere',textAlign:'left'});button.disabled=blocked;
   button.onclick=async()=>{if(button.disabled||pending||busy()||!fresh()||!list.contains(button))return;pending=true;for(const item of controls.querySelectorAll('button,input,select'))item.disabled=true;for(const item of list.querySelectorAll('button'))item.disabled=true;try{await onActivate(structuredClone(ref));}catch(error){onError(error);}finally{pending=false;if(fresh())render();}};list.append(button);}
  if(!report.rows.length){const note=document.createElement('p');note.className='field-note';note.textContent='No recorded users match these filters.';list.append(note);}
 }
 for(const control of [layer,scene,search])control.oninput=control.onchange=()=>{if(pending||busy()||!fresh())return;page=0;render();};
 previous.onclick=()=>{if(previous.disabled||!fresh())return;page--;render();};next.onclick=()=>{if(next.disabled||!fresh())return;page++;render();};
 render();mounting=false;return {refresh:render,dispose(){disposed=true;for(const control of controls.querySelectorAll('button,input,select'))control.disabled=true;for(const button of list.querySelectorAll('button'))button.disabled=true;}};
}
