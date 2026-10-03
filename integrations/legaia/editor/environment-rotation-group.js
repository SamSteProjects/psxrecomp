import {rotateSourceXZ} from './environment-rotation-math.js';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const fail=message=>{throw new Error(message);};
function groupIds(ids){
  if(!Array.isArray(ids)||ids.length<2||ids.length>128||ids.some(id=>typeof id!=='string'||!/^environment:\/\/[^/]+\/field-map\/decorations\/\d{5}$/.test(id)||Number(id.slice(-5))>16383)||new Set(ids).size!==ids.length||!same(ids,[...ids].sort()))fail('Select 2 through 128 distinct static decorations.');
  return ids;
}
export function environmentRotationGroupOperation(value,ids){
  groupIds(ids);
  const field=value&&Object.hasOwn(value,'yaw_units')?'yaw_units':'quarter_turns',maximum=field==='yaw_units'?4095:3;
  if(!value||Object.keys(value).sort().join()!==`anchor_id,${field}`||!ids.includes(value.anchor_id)||!Number.isInteger(value[field])||value[field]<0||value[field]>maximum)fail('Choose a selected anchor and an integer source angle or quarter turns.');
  return {anchor_id:value.anchor_id,[field]:value[field]};
}
export function decodeEnvironmentRotationGroup(value,key,scene,ids,operation){
  operation=environmentRotationGroupOperation(operation,ids);
  if(typeof scene!=='string'||!/^scene:\/\/[A-Za-z0-9_-]{1,128}$/.test(scene)||value?.schema_version!=='legaia.environment-rotation-group-review.v1'||!hash(key)||value.project_source_key!==key||value.scene_id!==scene||!hash(value.source_sha256)||!hash(value.review_key)||value.scope!=='static-decoration-instance-layout-and-yaw-only'||value.gameplay_verified!==false||typeof value.project_change!=='boolean'||!same(value.entity_ids,ids)||!same(environmentRotationGroupOperation(value.operation,ids),operation)||!Array.isArray(value.targets)||value.targets.length!==ids.length||!Number.isInteger(value.affected_count)||value.affected_count<0||value.affected_count>ids.length)fail('Invalid or stale scenery rotation review.');
  for(const [index,row] of value.targets.entries()){
    if(!row||row.entity_id!==ids[index]||!row.entity_id.startsWith(`environment://${scene.slice(8)}/field-map/decorations/`)||!Number.isInteger(row.cell_index)||row.cell_index<0||row.cell_index>16383||!row.entity_id.endsWith(`/decorations/${String(row.cell_index).padStart(5,'0')}`)||['retail','current','proposed'].some(layer=>!row[layer]||!Number.isSafeInteger(row[layer].x)||!Number.isSafeInteger(row[layer].z)||!Number.isInteger(row[layer].yaw)||row[layer].yaw<0||row[layer].yaw>4095))fail('Invalid reviewed scenery position or source yaw.');
  }
  const anchor=value.targets.find(row=>row.entity_id===operation.anchor_id).current;
  const yawUnits=operation.yaw_units??operation.quarter_turns*1024;
  let changed=0;
  for(const row of value.targets){
    const rotated=rotateSourceXZ(BigInt(row.current.x)-BigInt(anchor.x),BigInt(row.current.z)-BigInt(anchor.z),yawUnits);
    const x=BigInt(anchor.x)+rotated.x,z=BigInt(anchor.z)+rotated.z,yaw=(row.current.yaw+yawUnits)%4096;
    if(BigInt(row.proposed.x)!==x||BigInt(row.proposed.z)!==z||row.proposed.yaw!==yaw)fail('Reviewed rotation differs from its quantized source X/Z arithmetic.');
    changed+=row.current.x!==row.proposed.x||row.current.z!==row.proposed.z||row.current.yaw!==row.proposed.yaw;
  }
  if(changed!==value.affected_count||yawUnits===0&&value.project_change)fail('Invalid scenery rotation change count or no-op claim.');
  return structuredClone({...value,operation});
}

export function mountEnvironmentRotationGroup({host,getState,getSelection,busy,setBusy,api,canReview,onInspection,onFrame=()=>{},onError=()=>{}}){
  const button=document.createElement('button');button.id='environment-rotation-group-button';button.type='button';button.textContent='Rotate scenery group…';host.append(button);
  const strip=document.createElement('div');strip.id='environment-rotation-group-preview';strip.hidden=true;
  const note=document.createElement('span');note.textContent='Scenery rotation preview · not applied';
  const returnButton=document.createElement('button');returnButton.type='button';returnButton.textContent='Return to rotation review';
  const restoreButton=document.createElement('button');restoreButton.type='button';restoreButton.textContent='Restore rotation preview';strip.append(note,returnButton,restoreButton);host.append(strip);
  let dialog=null,report=null,context=null,controller=null,generation=0,inspecting=false,retaining=false,applying=false;
  const selection=()=>[...new Set(getSelection())].sort();
  const current=()=>{const state=getState();return !!context&&state.project?.mode==='edit'&&state.scene?.id===context.scene&&state.project_copy_source_key===context.key&&same(selection(),context.ids)&&canReview();};
  const operation=()=>{
    const mode=dialog.querySelector('[name="rotation_mode"]').value;
    if(!['quarter','source'].includes(mode))fail('Choose a scenery rotation mode.');
    const field=mode==='source'?'yaw_units':'quarter_turns',input=dialog.querySelector(`[name="${field}"]`);
    if(!input.value.trim())fail('Enter an integer source yaw.');
    return environmentRotationGroupOperation({anchor_id:dialog.querySelector('[name="anchor"]').value,[field]:Number(input.value)},context.ids);
  };
  const restoreInspection=()=>{if(inspecting){inspecting=false;onInspection(null);}strip.hidden=true;note.textContent='Scenery rotation preview · not applied';};
  const withdraw=()=>{generation++;if(controller){controller.abort();controller=null;setBusy(false);}report=null;restoreInspection();dialog?.querySelector('[data-result]')?.replaceChildren();};
  function restore(){context=null;withdraw();if(dialog){const old=dialog;dialog=null;if(old.open)old.close();old.remove();}refresh();}
  function refresh(){
    let eligible=false;try{groupIds(selection());eligible=getState().project?.mode==='edit'&&canReview();}catch{}
    button.disabled=busy()||applying||!eligible;
    returnButton.disabled=busy()||applying;restoreButton.disabled=applying||busy()&&!controller;
    if(context&&!current()){restore();return;}
    if(!dialog?.open)return;
    let valid=false;try{operation();valid=true;}catch{}
    const blocked=busy()||applying;
    for(const control of dialog.querySelectorAll('input,select,[data-review],[data-apply],[data-inspect]'))control.disabled=blocked;
    const sourceMode=dialog.querySelector('[name="rotation_mode"]').value==='source';
    dialog.querySelector('[data-source-angle]').hidden=!sourceMode;dialog.querySelector('[name="yaw_units"]').disabled=blocked||!sourceMode;
    dialog.querySelector('[data-quarter-angle]').hidden=sourceMode;dialog.querySelector('[name="quarter_turns"]').disabled=blocked||sourceMode;
    dialog.querySelector('[data-review]').disabled=blocked||!valid||!current();
    dialog.querySelector('[data-apply]').disabled=blocked||!valid||!current()||!report?.project_change;
    for(const control of dialog.querySelectorAll('[data-inspect]'))control.disabled=blocked||!report||!current();
    dialog.querySelector('[data-close]').disabled=applying;
  }
  button.onclick=()=>{
    if(button.disabled||busy()||applying)return;restore();
    const state=getState();context={key:state.project_copy_source_key,scene:state.scene.id,ids:selection()};groupIds(context.ids);
    dialog=document.createElement('dialog');dialog.id='environment-rotation-group-dialog';dialog.className='project-dialog';dialog.style.width='min(640px,94vw)';dialog.style.maxHeight='90vh';dialog.style.overflowY='auto';
    dialog.innerHTML='<h2>Rotate scenery group</h2><p>Rotate selected scenery around an anchor on the source X/Z plane and add the angle to source yaw. Positions use deterministic integer rounding. 4096 source units equal one turn. Apply records one Undo step. In-game behavior remains unverified.</p><form><div class="dialog-actions"><label>Anchor<select name="anchor" aria-label="Scenery rotation anchor"></select></label><label>Mode<select name="rotation_mode" aria-label="Scenery group rotation mode"><option value="quarter">Quarter turns</option><option value="source">Source angle</option></select></label><label data-quarter-angle>Rotation<select name="quarter_turns" aria-label="Scenery group quarter turns"><option value="0">0° · no change</option><option value="1" selected>90° · 1 quarter turn</option><option value="2">180° · 2 quarter turns</option><option value="3">270° · 3 quarter turns</option></select></label><label data-source-angle hidden>Source yaw units<input name="yaw_units" type="number" min="0" max="4095" step="1" value="512" required aria-label="Scenery group source yaw units"></label></div><button data-review type="submit">Review rotation</button></form><p data-status role="status"></p><div data-result style="max-height:40vh;overflow:auto"></div><div class="dialog-actions"><button data-inspect="proposed" type="button" disabled>Inspect proposed rotation</button><button data-inspect="current" type="button" disabled>Inspect current rotation</button><button data-apply type="button" disabled>Apply rotation</button><button data-close type="button">Cancel</button></div>';
    const activeDialog=dialog;
    for(const row of activeDialog.querySelectorAll('.dialog-actions')){row.style.flexWrap='wrap';row.style.justifyContent='flex-start';}for(const label of activeDialog.querySelectorAll('form label')){label.style.flex='1 1 170px';label.style.minWidth='0';label.style.maxWidth='100%';}for(const select of activeDialog.querySelectorAll('select,input')){select.style.width='100%';select.style.maxWidth='100%';select.style.boxSizing='border-box';}
    for(const id of context.ids){const option=document.createElement('option');option.value=id;option.textContent=`Decoration ${id.slice(-5)}`;option.title=id;activeDialog.querySelector('[name="anchor"]').append(option);}
    const status=text=>{if(dialog===activeDialog)activeDialog.querySelector('[data-status]').textContent=text;};
    const render=()=>{
      const output=activeDialog.querySelector('[data-result]');output.replaceChildren();const units=report.operation.yaw_units??report.operation.quarter_turns*1024;status(`${report.targets.length} decorations reviewed · ${report.affected_count} positions or yaws change · ${units*360/4096}° / ${units} source units. Positions are quantized integers.`);
      const scroll=document.createElement('div');scroll.style.overflowX='auto';const table=document.createElement('table'),head=document.createElement('tr');
      for(const text of ['Decoration','Retail X / Z / yaw','Current X / Z / yaw','Proposed integer X / Z / yaw']){const cell=document.createElement('th');cell.textContent=text;head.append(cell);}table.append(head);
      for(const row of report.targets){const tr=document.createElement('tr');for(const text of [row.entity_id,...['retail','current','proposed'].map(layer=>`${row[layer].x} / ${row[layer].z} / ${row[layer].yaw} units (${row[layer].yaw*360/4096}°)` )]){const cell=document.createElement('td');cell.textContent=text;tr.append(cell);}table.append(tr);}scroll.append(table);output.append(scroll);
    };
    activeDialog.querySelector('form').oninput=()=>{withdraw();status('Rotation changed; review again.');refresh();};
    activeDialog.querySelector('form').onsubmit=async event=>{
      event.preventDefault();if(busy()||applying||!current()||!activeDialog.querySelector('form').reportValidity())return;
      let requested;try{requested=operation();}catch(error){status(error.message);return;}
      withdraw();const token=++generation,binding=context,requestController=new AbortController();controller=requestController;setBusy(true);refresh();
      try{
        const response=await fetch('/api/environment-rotation-group-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:binding.scene,entity_ids:binding.ids,operation:requested}),signal:requestController.signal});
        const value=await response.json();if(!response.ok||value.error)throw new Error(value.error||'Scenery rotation review failed.');
        if(dialog!==activeDialog||!activeDialog.open||generation!==token||context!==binding||!current()||!same(operation(),requested))return;
        report=decodeEnvironmentRotationGroup(value,binding.key,binding.scene,binding.ids,requested);render();
      }catch(error){if(error.name!=='AbortError'&&dialog===activeDialog&&activeDialog.open&&generation===token){status(error.message);onError(error.message);}}
      finally{if(controller===requestController){controller=null;setBusy(false);}refresh();}
    };
    activeDialog.querySelector('[data-apply]').onclick=async()=>{
      if(busy()||applying||!current()||!report?.project_change||!same(operation(),report.operation))return;
      const reviewed=report,binding=context;applying=true;refresh();
      try{
        const accepted=await api('/api/command',{type:'apply_environment_rotation_group',entity_id:binding.scene,entity_ids:binding.ids,operation:reviewed.operation,review_key:reviewed.review_key});
        if(dialog!==activeDialog||context!==binding)return;
        if(accepted)restore();else{withdraw();status('Scenery rotation was rejected. Review current placements again.');}
      }catch(error){if(dialog===activeDialog){withdraw();status(error.message);onError(error.message);}}
      finally{applying=false;refresh();}
    };
    for(const control of activeDialog.querySelectorAll('[data-inspect]'))control.onclick=()=>{
      if(busy()||applying||!report||!current()||!same(operation(),report.operation))return;
      inspecting=true;strip.hidden=false;retaining=true;activeDialog.close();onInspection(report,control.dataset.inspect);onFrame(report);refresh();
    };
    activeDialog.querySelector('[data-close]').onclick=()=>{if(!applying)activeDialog.close();};
    activeDialog.addEventListener('cancel',event=>{if(applying){event.preventDefault();status('Applying rotation…');}});
    activeDialog.addEventListener('close',()=>{if(retaining){retaining=false;return;}if(dialog===activeDialog)restore();});
    document.body.append(activeDialog);activeDialog.showModal();refresh();
  };
  returnButton.onclick=()=>{if(busy()||applying||!report||!current()||!dialog)return;restoreInspection();dialog.showModal();refresh();};
  restoreButton.onclick=()=>{if(!applying&&(!busy()||controller))restore();};
  refresh();return {restore,refresh};
}
