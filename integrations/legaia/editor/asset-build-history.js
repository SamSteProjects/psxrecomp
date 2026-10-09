import {decodeBuildHistory,decodeBuildVerification,decodeBuildVerificationForEntry} from './build-history.js';
import {CONTROLLER_BUILD_TARGETS,controllerBuildTarget} from './controller-build-navigation.js';
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const stable=value=>typeof value==='string'&&value.length<=1024&&/^[a-z][a-z0-9-]*:\/\/[^\s\x00-\x20\x7f<>"']+$/.test(value);
export function assetBuildRecords(value,entry,assetId,key,includeOwned=true){
  if(!stable(assetId)||typeof includeOwned!=='boolean')throw new Error('Unsupported asset identity or audit relationship.');
  const verified=decodeBuildVerificationForEntry(value,entry,key);
  const controller=/^script:\/\/([A-Za-z0-9_-]{1,128})\/controllers\/man-p1\/0000$/.exec(assetId);
  const controllerMatch=row=>{
    const target=Object.hasOwn(CONTROLLER_BUILD_TARGETS,row.scope)?CONTROLLER_BUILD_TARGETS[row.scope]:null,prefix=target?assetId+'/'+target[1]+'/':null;
    return !!controller&&!!target&&row.owner_id===assetId.replace('script://','scene://')&&row.scene===controller[1]&&row.field===target[2]&&row.asset_id.startsWith(prefix)&&/^[a-f0-9]{4}$/.test(row.asset_id.slice(prefix.length));
  };
  return verified.report.changes.filter(row=>row.asset_id===assetId||includeOwned&&(row.owner_id===assetId||controllerMatch(row))).map(row=>({relationship:row.asset_id===assetId?'Exact audit asset ID':row.owner_id===assetId?'Exact audit owner ID':'Qualified controller audit owner',record:row}));
}
export function openAssetBuildHistory({record,getState,current,busy,setBusy,onError,onInspectController=null,request=fetch}){
  if(busy()||!current())return null;
  const project=getState().project?.path,key=getState().build_review_source_key;
  if(!stable(record?.id)||!hash(key)||typeof project!=='string')throw new Error('Asset Build records require current project input identity.');
  const dialog=document.createElement('dialog');dialog.id='asset-build-history-dialog';
  const controller=new AbortController(),title=document.createElement('h2'),identity=document.createElement('p'),status=document.createElement('p'),select=document.createElement('select'),selectLabel=document.createElement('label'),verify=document.createElement('button'),owned=document.createElement('input'),ownedLabel=document.createElement('label'),content=document.createElement('div'),close=document.createElement('button');
  title.textContent='Asset records in saved Builds';identity.textContent=record.id;identity.style.overflowWrap='anywhere';status.setAttribute('role','status');
  select.setAttribute('aria-label','Saved Build for asset audit');selectLabel.textContent='Saved Build ';selectLabel.append(select);verify.textContent='Verify saved package';verify.disabled=true;
  const ownerLabel=record.type==='controller'?'Include qualified controller owner matches':'Include exact audit owner matches';
  owned.type='checkbox';owned.checked=true;owned.setAttribute('aria-label',ownerLabel);ownedLabel.append(owned,document.createTextNode(ownerLabel));
  Object.assign(ownedLabel.style,{display:'flex',alignItems:'center',gap:'.5rem'});Object.assign(owned.style,{width:'auto',flex:'none',margin:'0'});
  const note=document.createElement('p');note.className='field-note';note.textContent='Matches exact stable IDs and qualified controller owner bindings in emitted audit records. Controller source navigation requires current authored inputs and matching operand values. Shared source membership and native asset presence are not inferred. A missing record does not prove unused content or deletion. Package verification does not check the source disc or gameplay.';
  close.textContent='Close';close.onclick=()=>dialog.close();const actions=document.createElement('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';actions.append(verify,close);dialog.append(title,identity,status,selectLabel,ownedLabel,note,content,actions);document.body.append(dialog);dialog.showModal();
  let entries=[],verification=null,page=0;
  const fresh=()=>dialog.open&&!controller.signal.aborted&&current()&&getState().project?.path===project&&getState().build_review_source_key===key;
  const invalidate=message=>{verification=null;content.replaceChildren();status.textContent=message;verify.disabled=true;};
  const call=async(route,body)=>{
    if(!fresh())throw new Error('Asset/project inputs changed. Reopen asset Build records.');
    const response=await request(route,{method:body===undefined?'GET':'POST',headers:body===undefined?undefined:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),cache:'no-store',signal:controller.signal});
    const value=await response.json();if(!response.ok)throw new Error(value.error||'Saved Build request failed.');
    if(!fresh())throw new Error('Asset/project inputs changed. Reopen asset Build records.');return value;
  };
  const checkServer=async()=>{const latest=await call('/api/state');if(latest.project?.path!==project||latest.build_review_source_key!==key)throw new Error('Server project inputs changed. Reopen asset Build records.');};
  const render=()=>{
    if(!fresh()){invalidate('Asset/project inputs changed. Reopen asset Build records.');return;}
    content.replaceChildren();if(!verification)return;
    const entry=entries.find(row=>row.id===select.value);
    if(!entry||verification.id!==entry.id){invalidate('Choose a saved Build and verify its package.');return;}
    const rows=assetBuildRecords(verification,entry,record.id,key,owned.checked),pages=Math.max(1,Math.ceil(rows.length/128));page=Math.min(page,pages-1);
    status.textContent=`Saved package integrity verified · ${verification.matches_current_inputs?'matches current authored inputs':'different authored inputs'} · ${rows.length} matching audit records. Source disc and gameplay unverified.`;
    const provenance=document.createElement('p');provenance.className='field-note';provenance.style.overflowWrap='anywhere';provenance.textContent=`Build ${entry.id} · ${entry.build_kind} · archive SHA256 ${entry.archive_sha256} · source disc SHA256 ${entry.source_disc_sha256}`;content.append(provenance);
    if(!rows.length){const empty=document.createElement('p');empty.textContent='No matching stable ID recorded in this audit. This does not prove the asset was absent from the package or unused.';content.append(empty);return;}
    const table=document.createElement('table');table.className='build-change-table';table.style.width='100%';table.style.tableLayout='fixed';const labels=['ID relationship','Scene / field','Before','After'],heading=document.createElement('tr');heading.className='asset-build-heading';for(const label of labels){const cell=document.createElement('th');cell.textContent=label;heading.append(cell);}table.append(heading);
    for(const item of rows.slice(page*128,(page+1)*128)){
      const row=document.createElement('tr');for(const [index,value] of [item.relationship,`${item.record.scene} · ${item.record.field}`,item.record.before,item.record.after].entries()){const cell=document.createElement('td');cell.dataset.label=labels[index];cell.style.overflowWrap='anywhere';cell.textContent=typeof value==='string'?value:JSON.stringify(value);row.append(cell);}
      const details=document.createElement('details'),summary=document.createElement('summary'),data=document.createElement('pre');summary.textContent='Full emitted audit record';data.style.whiteSpace='pre-wrap';data.textContent=JSON.stringify(item.record,null,2);details.append(summary,data);row.children[1].append(details);table.append(row);
      if(item.relationship==='Qualified controller audit owner'&&typeof onInspectController==='function'){
        const inspect=document.createElement('button');inspect.textContent='Inspect controller operand';inspect.style.whiteSpace='normal';
        const target=()=>controllerBuildTarget(item.record,getState().scenes??[],getState().authored_assets??[]);
        let supported=false;try{supported=!!target();}catch{}
        inspect.disabled=!verification.matches_current_inputs||!supported;inspect.title=inspect.disabled?'Rebuild current authored inputs before navigating this operand.':item.record.asset_id;
        inspect.onclick=async()=>{if(busy()||!fresh()||!content.contains(inspect)||!verification?.matches_current_inputs)return;const proof=verification,selectedId=select.value;try{await checkServer();if(!fresh()||verification!==proof||select.value!==selectedId||!content.contains(inspect)||!proof.matches_current_inputs||!target())throw Error('Controller Build source or displayed records changed. Reopen the saved records.');dialog.close();await onInspectController(item.record);}catch(error){if(dialog.open)invalidate(error.message);onError(error);}};
        row.children[1].append(inspect);
      }
    }
    const wrap=document.createElement('div');wrap.style.overflowX='auto';wrap.append(table);content.append(wrap);
    const paging=document.createElement('div');paging.className='dialog-actions';paging.style.flexWrap='wrap';for(const [label,delta] of [['Previous records',-1],['Next records',1]]){const button=document.createElement('button');button.textContent=label;button.disabled=delta<0?page===0:page===pages-1;button.onclick=()=>{if(busy()||!content.contains(button))return;if(!fresh()){if(dialog.open)invalidate('Asset inputs or report changed. Reopen asset Build records.');return;}page+=delta;render();};paging.append(button);}const count=document.createElement('span');count.textContent=`Page ${page+1} / ${pages} · ${rows.length} records`;paging.append(count);content.append(paging);
  };
  select.onchange=()=>{verification=null;page=0;content.replaceChildren();status.textContent='Verify the selected package before viewing its recorded asset changes.';verify.disabled=busy()||!fresh()||!entries.some(row=>row.id===select.value);};
  owned.onchange=()=>{if(busy())return;page=0;render();};
  verify.onclick=async()=>{
    if(busy()||!fresh())return;const entry=entries.find(row=>row.id===select.value);if(!entry)return;
    verification=null;page=0;content.replaceChildren();verify.disabled=select.disabled=owned.disabled=true;status.textContent='Verifying receipt, audit, manifest, payload files and ZIP…';setBusy(true);
    try{const value=await call('/api/builds/verify',{id:entry.id});await checkServer();if(select.value!==entry.id)throw new Error('Saved Build selection changed during verification. Verify again.');assetBuildRecords(value,entry,record.id,key,owned.checked);verification=decodeBuildVerification(value,entry.id);render();}
    catch(error){if(dialog.open){invalidate(error.message);onError(error);}}
    finally{setBusy(false);select.disabled=owned.disabled=false;verify.disabled=!fresh()||!entries.some(row=>row.id===select.value);}
  };
  dialog.addEventListener('close',()=>{controller.abort();verification=null;dialog.remove();});
  status.textContent='Loading saved completion receipts…';select.disabled=owned.disabled=true;setBusy(true);
  const ready=(async()=>{
    try{const history=decodeBuildHistory(await call('/api/builds',{}));await checkServer();entries=history.builds.filter(row=>row.status==='completed');for(const entry of entries){const option=document.createElement('option');option.value=entry.id;option.textContent=`${entry.id} · ${entry.change_count} changes · ${entry.matches_current_inputs?'current':'different'} inputs`;select.append(option);}status.textContent=entries.length?`${entries.length} completed Builds in identity order${history.truncated?' · bounded scan, additional entries may be omitted':''}; ${history.builds.length-entries.length} invalid/incomplete entries excluded. Choose one and verify its files.`:'No completed saved Builds available in this project. Build history retains invalid/incomplete entries; a normal Build creates a completion receipt.';}
    catch(error){if(dialog.open){invalidate(error.message);onError(error);}}
    finally{setBusy(false);select.disabled=owned.disabled=false;verify.disabled=!fresh()||!entries.length;}
  })();
  return {dialog,ready};
}
