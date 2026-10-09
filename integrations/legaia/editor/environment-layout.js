function layoutIds(ids){
  if(!Array.isArray(ids)||ids.length<2||ids.length>128||ids.some(id=>typeof id!=='string'||!/^environment:\/\/[^/]+\/field-map\/decorations\/\d{5}$/.test(id)||Number(id.slice(-5))>16383)||new Set(ids).size!==ids.length||JSON.stringify(ids)!==JSON.stringify([...ids].sort()))throw new Error('Select 2 through 128 distinct static decorations');
  return ids;
}
export function environmentLayoutOperation(value,ids){
  layoutIds(ids);
  const kind=value?.kind,fields=kind==='scale'?'anchor,kind,percent':kind==='distribute'?'axis,kind':'anchor,axis,kind';
  if(!value||!['align','distribute','scale','mirror'].includes(kind)||Object.keys(value).sort().join()!==fields||kind!=='scale'&&!['x','z'].includes(value.axis)||kind!=='distribute'&&!ids.includes(value.anchor)||kind==='scale'&&(!Number.isSafeInteger(value.percent)||value.percent<1||value.percent>1000))throw new Error('Invalid scenery arrangement operation');
  return kind==='scale'?{kind,anchor:value.anchor,percent:value.percent}:kind==='distribute'?{kind,axis:value.axis}:{kind,axis:value.axis,anchor:value.anchor};
}
export function decodeEnvironmentLayout(value,key,scene,ids,operation){
  operation=environmentLayoutOperation(operation,ids);const hash=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
  if(value?.schema_version!=='legaia.environment-layout-review.v1'||!hash(key)||value.project_source_key!==key||value.scene_id!==scene||!hash(value.source_sha256)||!hash(value.review_key)||value.scope!=='static-decoration-instance-transform-only'||value.gameplay_verified!==false||typeof value.project_change!=='boolean'||JSON.stringify(value.entity_ids)!==JSON.stringify(ids)||JSON.stringify(environmentLayoutOperation(value.operation,ids))!==JSON.stringify(operation)||!Array.isArray(value.targets)||value.targets.length!==ids.length||!Number.isInteger(value.affected_count)||value.affected_count<0||value.affected_count>ids.length)throw new Error('Invalid or stale scenery layout review');
  for(const [index,row] of value.targets.entries()){
    if(!row||row.entity_id!==ids[index]||!row.entity_id.startsWith(`environment://${scene.replace(/^scene:\/\//,'')}/field-map/` )||!Number.isInteger(row.cell_index)||row.cell_index<0||row.cell_index>16383||!row.entity_id.endsWith(`/decorations/${String(row.cell_index).padStart(5,'0')}`)||['retail','current','proposed'].some(layer=>!row[layer]||['x','z'].some(axis=>!Number.isSafeInteger(row[layer][axis]))))throw new Error('Invalid reviewed scenery placement');
  }
  const axis=operation.axis,other=axis==='x'?'z':'x',expected=new Map();
  if(operation.kind==='scale'){
    const pivot=value.targets.find(row=>row.entity_id===operation.anchor).current;
    for(const row of value.targets){const point={};for(const a of ['x','z']){const n=BigInt(pivot[a])*100n+(BigInt(row.current[a])-BigInt(pivot[a]))*BigInt(operation.percent),coordinate=(n<0n?-1n:1n)*((n<0n?-n:n)+50n)/100n;point[a]=Number(coordinate);if(!Number.isSafeInteger(point[a]))throw Error('Scenery spacing scale exceeds safe coordinates');}expected.set(row.entity_id,point);}
  }else if(operation.kind==='mirror'){
    const pivot=BigInt(value.targets.find(row=>row.entity_id===operation.anchor).current[axis]);for(const row of value.targets){const coordinate=Number(2n*pivot-BigInt(row.current[axis]));if(!Number.isSafeInteger(coordinate))throw Error('Scenery mirror exceeds safe coordinates');expected.set(row.entity_id,coordinate);}
  }else if(operation.kind==='align'){
    const anchor=value.targets.find(row=>row.entity_id===operation.anchor).current[axis];
    for(const row of value.targets)expected.set(row.entity_id,anchor);
  }else{
    const ordered=[...value.targets].sort((a,b)=>a.current[axis]-b.current[axis]||(a.entity_id<b.entity_id?-1:a.entity_id>b.entity_id?1:0)),low=BigInt(ordered[0].current[axis]),span=BigInt(ordered.at(-1).current[axis])-low,denominator=BigInt(ordered.length-1);
    if(span<denominator)throw new Error('Scenery distribution requires enough distinct integer positions');
    for(const [index,row] of ordered.entries())expected.set(row.entity_id,Number(low+(2n*span*BigInt(index)+denominator)/(2n*denominator)));
  }
  let changed=0;
  for(const row of value.targets){if(operation.kind==='scale'?['x','z'].some(a=>row.proposed[a]!==expected.get(row.entity_id)[a]):row.proposed[axis]!==expected.get(row.entity_id)||row.proposed[other]!==row.current[other])throw new Error('Invalid scenery layout arithmetic');changed+=row.current.x!==row.proposed.x||row.current.z!==row.proposed.z;}
  if(changed!==value.affected_count)throw new Error('Invalid scenery layout change count');
  return structuredClone({...value,operation});
}

export function mountEnvironmentLayout({host,getState,getSelection,busy,setBusy,api,canReview,onInspection,onFrame=()=>{},onError=()=>{}}){
  const button=document.createElement('button');button.id='environment-layout-button';button.type='button';button.textContent='Arrange scenery group…';host.append(button);
  const strip=document.createElement('div');strip.id='environment-layout-preview';strip.hidden=true;
  const note=document.createElement('span');note.textContent='Scenery layout preview · not applied';
  const returnButton=document.createElement('button');returnButton.type='button';returnButton.textContent='Return to scenery review';
  const restoreButton=document.createElement('button');restoreButton.type='button';restoreButton.textContent='Restore scenery preview';strip.append(note,returnButton,restoreButton);host.append(strip);
  let dialog=null,report=null,context=null,controller=null,generation=0,inspecting=false,retaining=false;
  const selection=()=>[...new Set(getSelection())].sort();
  const current=()=>{const s=getState();return !!context&&s.project?.mode==='edit'&&s.scene?.id===context.scene&&s.project_copy_source_key===context.key&&JSON.stringify(selection())===JSON.stringify(context.ids)&&canReview();};
  const operation=()=>{
    const kind=dialog.querySelector('[name="kind"]').value,axis=dialog.querySelector('[name="axis"]').value;
    const anchor=dialog.querySelector('[name="anchor"]').value;return environmentLayoutOperation(kind==='scale'?{kind,anchor,percent:Number(dialog.querySelector('[name="percent"]').value)}:kind==='distribute'?{kind,axis}:{kind,axis,anchor},context.ids);
  };
  const restoreInspection=()=>{if(inspecting){inspecting=false;onInspection(null);}strip.hidden=true;note.textContent='Scenery layout preview · not applied';};
  const withdraw=()=>{generation++;if(controller){controller.abort();controller=null;setBusy(false);}report=null;restoreInspection();dialog?.querySelector('[data-result]')?.replaceChildren();};
  function restore(){context=null;withdraw();if(dialog){const old=dialog;dialog=null;if(old.open)old.close();old.remove();}refresh();}
  function refresh(){
    let eligible=false;try{layoutIds(selection());eligible=getState().project?.mode==='edit'&&canReview();}catch{}
    button.disabled=busy()||!eligible;
    returnButton.disabled=busy();restoreButton.disabled=busy()&&!controller;
    if(context&&!current()){restore();return;}
    if(!dialog?.open)return;
    let valid=false;try{operation();valid=true;}catch{}
    for(const item of dialog.querySelectorAll('input,select,[data-review],[data-apply],[data-inspect]'))item.disabled=busy();
    const kind=dialog.querySelector('[name="kind"]').value;dialog.querySelector('[name="anchor"]').disabled=busy()||kind==='distribute';dialog.querySelector('[name="axis"]').disabled=busy()||kind==='scale';dialog.querySelector('[name="axis"]').parentElement.hidden=kind==='scale';dialog.querySelector('[name="percent"]').disabled=busy()||kind!=='scale';dialog.querySelector('[name="percent"]').parentElement.hidden=kind!=='scale';
    dialog.querySelector('[data-review]').disabled=busy()||!valid||!current();
    dialog.querySelector('[data-apply]').disabled=busy()||!valid||!current()||!report?.project_change;
    for(const item of dialog.querySelectorAll('[data-inspect]'))item.disabled=busy()||!report||!current();
  }
  button.onclick=()=>{
    if(button.disabled||busy())return;restore();
    const s=getState();context={key:s.project_copy_source_key,scene:s.scene.id,ids:selection()};layoutIds(context.ids);
    dialog=document.createElement('dialog');dialog.id='environment-layout-dialog';dialog.className='project-dialog';dialog.style.width='min(800px,90vw)';dialog.style.maxHeight='90vh';dialog.style.overflowY='auto';
    dialog.innerHTML='<h2>Arrange scenery group</h2><p>Align, distribute, mirror or scale spacing between selected static decorations. Scaling changes X/Z placements around the anchor, not mesh size; integer half ties round away from world zero. Mirroring reflects placement positions, not model orientation. Apply records the group as one Undo step. In-game behavior remains unverified.</p><form><div class="dialog-actions"><label>Action<select name="kind" aria-label="Scenery arrangement action"><option value="align">Align</option><option value="distribute">Distribute</option><option value="scale">Scale spacing</option><option value="mirror">Mirror positions</option></select></label><label>Axis<select name="axis" aria-label="Scenery arrangement axis"><option value="x">X</option><option value="z">Z</option></select></label><label>Anchor<select name="anchor" aria-label="Scenery arrangement anchor"></select></label><label>Spacing percent<input name="percent" aria-label="Scenery spacing percentage" type="number" min="1" max="1000" step="1" value="100" required></label></div><button data-review type="submit">Review group</button></form><p data-status role="status"></p><div data-result style="max-height:40vh;overflow:auto"></div><div class="dialog-actions"><button data-inspect="proposed" type="button" disabled>Inspect proposed scenery</button><button data-inspect="current" type="button" disabled>Inspect current scenery</button><button data-apply type="button" disabled>Apply group</button><button data-close type="button">Cancel</button></div>';
    const activeDialog=dialog;
    const anchor=activeDialog.querySelector('[name="anchor"]');
    for(const id of context.ids){const option=document.createElement('option');option.value=id;option.textContent=id;anchor.append(option);}

    const status=text=>{if(dialog===activeDialog)activeDialog.querySelector('[data-status]').textContent=text;};
    const render=()=>{
      const output=dialog.querySelector('[data-result]');output.replaceChildren();status(`${report.targets.length} decorations reviewed · ${report.affected_count} placements change.`);
      const table=document.createElement('table'),head=document.createElement('tr');for(const text of ['Decoration','Retail X/Z','Current X/Z','Proposed X/Z']){const th=document.createElement('th');th.textContent=text;head.append(th);}table.append(head);
      for(const row of report.targets){const tr=document.createElement('tr');for(const text of [row.entity_id,...['retail','current','proposed'].map(layer=>`${row[layer].x} / ${row[layer].z}`)]){const td=document.createElement('td');td.textContent=text;tr.append(td);}table.append(tr);}output.append(table);
    };
    activeDialog.querySelector('form').oninput=()=>{withdraw();status('Arrangement changed; review again.');refresh();};
    activeDialog.querySelector('form').onsubmit=async event=>{
      event.preventDefault();if(busy()||!current()||!activeDialog.querySelector('form').reportValidity())return;
      let requested;try{requested=operation();}catch(error){status(error.message);return;}
      withdraw();const token=++generation,binding=context,requestController=new AbortController();controller=requestController;setBusy(true);refresh();
      try{
        const response=await fetch('/api/environment-layout-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:binding.scene,entity_ids:binding.ids,operation:requested}),signal:requestController.signal});
        const value=await response.json();if(!response.ok||value.error)throw new Error(value.error||'Scenery layout review failed');
        if(dialog!==activeDialog||!activeDialog.open||generation!==token||context!==binding||!current()||JSON.stringify(operation())!==JSON.stringify(requested))return;
        report=decodeEnvironmentLayout(value,binding.key,binding.scene,binding.ids,requested);render();
      }catch(error){if(error.name!=='AbortError'&&dialog===activeDialog&&activeDialog.open&&generation===token){status(error.message);onError(error.message);}}
      finally{if(controller===requestController){controller=null;setBusy(false);}refresh();}
    };
    activeDialog.querySelector('[data-apply]').onclick=async()=>{
      if(busy()||!current()||!report?.project_change||JSON.stringify(operation())!==JSON.stringify(report.operation))return;
      const reviewed=report;
      if(await api('/api/command',{type:'apply_environment_layout',entity_id:context.scene,entity_ids:context.ids,operation:reviewed.operation,review_key:reviewed.review_key}))restore();
      else{withdraw();status('Scenery layout was rejected. Review current placements again.');refresh();}
    };
    for(const item of activeDialog.querySelectorAll('[data-inspect]'))item.onclick=()=>{
      if(busy()||!report||!current()||JSON.stringify(operation())!==JSON.stringify(report.operation))return;
      inspecting=true;strip.hidden=false;retaining=true;activeDialog.close();onInspection(report,item.dataset.inspect);onFrame(report);refresh();
    };
    activeDialog.querySelector('[data-close]').onclick=()=>activeDialog.close();
    activeDialog.addEventListener('close',()=>{if(retaining){retaining=false;return;}if(dialog===activeDialog)restore();});
    document.body.append(activeDialog);activeDialog.showModal();refresh();
  };
  returnButton.onclick=()=>{if(busy()||!report||!current()||!dialog)return;restoreInspection();dialog.showModal();refresh();};
  restoreButton.onclick=()=>{if(!busy()||controller)restore();};
  return {restore,refresh};
}
