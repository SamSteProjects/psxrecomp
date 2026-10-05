export function scenePlacementGroupDelta(value){
  if(!value||Object.keys(value).sort().join()!=='x,z'||['x','z'].some(axis=>!Number.isSafeInteger(value[axis])||Math.abs(value[axis])>16320||value[axis]%64))throw new Error('Placement offsets must be multiples of 64 from -16320 through 16320');
  return {x:value.x,z:value.z};
}
function placementIds(ids,scene){
  const match=/^scene:\/\/([^/]+)$/.exec(scene||'');
  if(!match||!Array.isArray(ids)||ids.length<2||ids.length>128||new Set(ids).size!==ids.length||JSON.stringify(ids)!==JSON.stringify([...ids].sort()))throw new Error('Select 2 through 128 distinct placements in the active scene');
  let actors=0,decorations=0;
  for(const id of ids){
    if(typeof id!=='string')throw new Error('Invalid placement selection');
    const actor=/^scene:\/\/([^/]+)\/actors\/man-p[12]\/\d{4}$/.exec(id);
    const decoration=/^environment:\/\/([^/]+)\/field-map\/decorations\/(\d{5})$/.exec(id);
    if(actor&&actor[1]===match[1])actors++;
    else if(decoration&&decoration[1]===match[1]&&Number(decoration[2])<=16383)decorations++;
    else throw new Error('Select imported actors and static decorations from the active scene');
  }
  if(!actors||!decorations)throw new Error('Select at least one imported actor and one static decoration');
  return ids;
}
export function decodeScenePlacementGroup(value,key,scene,ids,delta){
  placementIds(ids,scene);delta=scenePlacementGroupDelta(delta);const hash=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
  if(value?.schema_version!=='legaia.scene-placement-group-review.v1'||!hash(key)||value.project_source_key!==key||value.scene_id!==scene||!hash(value.source_sha256)||!hash(value.review_key)||value.scope!=='imported-actor-and-static-decoration-xz-only'||value.gameplay_verified!==false||typeof value.project_change!=='boolean'||JSON.stringify(value.entity_ids)!==JSON.stringify(ids)||JSON.stringify(scenePlacementGroupDelta(value.delta))!==JSON.stringify(delta)||!Array.isArray(value.targets)||value.targets.length!==ids.length||!Number.isInteger(value.affected_count)||value.affected_count<0||value.affected_count>ids.length)throw new Error('Invalid or stale scene placement group review');
  let changed=0;
  for(const [index,row] of value.targets.entries()){
    const isActor=ids[index].startsWith('scene://');
    if(!row||row.entity_id!==ids[index]||row.kind!==(isActor?'actor':'decoration')||(!isActor&&(!Number.isInteger(row.cell_index)||row.cell_index<0||row.cell_index>16383||!row.entity_id.endsWith(`/decorations/${String(row.cell_index).padStart(5,'0')}`)))||(isActor&&Object.hasOwn(row,'cell_index'))||['retail','current','proposed'].some(layer=>!row[layer]||Object.keys(row[layer]).sort().join()!=='x,z'||['x','z'].some(axis=>!Number.isSafeInteger(row[layer][axis])))||['x','z'].some(axis=>!Number.isSafeInteger(row.current[axis]+delta[axis])||row.proposed[axis]!==row.current[axis]+delta[axis]))throw new Error('Invalid reviewed scene placement');
    changed+=row.current.x!==row.proposed.x||row.current.z!==row.proposed.z;
  }
  if(changed!==value.affected_count)throw new Error('Invalid scene placement group change count');
  return structuredClone({...value,delta});
}

export function mixedLayoutPositions(targets,operation){
  const fields=operation?.kind==='scale'?['anchor_entity_id','kind','percent']:operation?.kind==='reset'?['kind']:operation?.kind==='rotate'?['anchor_entity_id','kind','quarter_turns']:operation?.kind==='align'?['anchor_entity_id','axis','kind']:['axis','kind'];
  if(!operation||Object.keys(operation).sort().join()!==fields.join()||!['align','distribute','reset','rotate','scale'].includes(operation.kind)||['align','distribute'].includes(operation.kind)&&!['x','z'].includes(operation.axis)||operation.kind==='rotate'&&(!Number.isInteger(operation.quarter_turns)||![-1,1,2].includes(operation.quarter_turns)))throw new Error('Choose exact mixed placement operation fields.');
  if(operation.kind==='scale'&&(!Number.isInteger(operation.percent)||operation.percent<1||operation.percent>1000))throw new Error('Mixed scale requires an integer percentage from 1 through 1000.');
  const result=targets.map(row=>({entity_id:row.entity_id,position:{...row.current}})),axis=operation.axis;
  if(operation.kind==='reset'){for(const [i,row] of result.entries())row.position={...targets[i].retail};}
  else if(operation.kind==='scale'){
    const anchor=targets.find(row=>row.entity_id===operation.anchor_entity_id);
    if(!anchor||targets.some(row=>['x','z'].some(a=>!Number.isSafeInteger(row.current[a]))))throw new Error('Mixed scale requires integer Current X/Z coordinates.');
    for(const row of result)for(const a of ['x','z']){const step=row.entity_id.startsWith('scene://')?64:1,n=anchor.current[a]*100+(row.position[a]-anchor.current[a])*operation.percent,denominator=100*step;if(!Number.isSafeInteger(n)||!Number.isSafeInteger(Math.abs(n)+denominator/2))throw new Error('Mixed scale exceeds safe arithmetic.');row.position[a]=Math.sign(n)*Math.floor((Math.abs(n)+denominator/2)/denominator)*step;}
  }
  else if(operation.kind==='rotate'){
    const anchor=targets.find(row=>row.entity_id===operation.anchor_entity_id);
    if(!anchor||targets.some(row=>['x','z'].some(a=>!Number.isSafeInteger(row.current[a]))))throw new Error('Mixed rotation requires integer Current X/Z coordinates.');
    const {x:px,z:pz}=anchor.current;
    for(const row of result){const dx=row.position.x-px,dz=row.position.z-pz;if(!Number.isSafeInteger(dx)||!Number.isSafeInteger(dz))throw new Error('Mixed rotation exceeds safe arithmetic.');const [x,z]=operation.quarter_turns===1?[-dz,dx]:operation.quarter_turns===-1?[dz,-dx]:[-dx,-dz],step=row.entity_id.startsWith('scene://')?64:1;for(const [a,n] of [['x',px+x],['z',pz+z]]){if(!Number.isSafeInteger(n)||!Number.isSafeInteger(Math.abs(n)+Math.floor(step/2)))throw new Error('Mixed rotation exceeds safe arithmetic.');row.position[a]=Math.sign(n)*Math.floor((Math.abs(n)+Math.floor(step/2))/step)*step;}}
    if(result.some(row=>['x','z'].some(a=>!Number.isSafeInteger(row.position[a]))))throw new Error('Mixed rotation exceeds safe coordinates.');
  }
  else if(operation.kind==='align'){const anchor=targets.find(row=>row.entity_id===operation.anchor_entity_id);if(!anchor||!Number.isSafeInteger(anchor.current[axis])||anchor.current[axis]%64)throw new Error('Selected mixed anchor must lie on the 64-unit actor grid.');for(const row of result)row.position[axis]=anchor.current[axis];}
  else{if(targets.some(row=>!Number.isSafeInteger(row.current[axis])||row.current[axis]%64))throw new Error('Mixed distribution requires selected coordinates on the 64-unit actor grid.');const ordered=[...result].sort((a,b)=>a.position[axis]-b.position[axis]||a.entity_id.localeCompare(b.entity_id)),low=ordered[0].position[axis]/64,span=ordered.at(-1).position[axis]/64-low,intervals=ordered.length-1;if(span<intervals)throw new Error('Mixed distribution needs one 64-unit interval per gap.');for(const [i,row] of ordered.entries())row.position[axis]=(low+Math.floor((2*span*i+intervals)/(2*intervals)))*64;}
  for(const row of result)if(row.entity_id.startsWith('scene://')&&(row.position.x<64||row.position.x>16384||row.position.z<64||row.position.z>16384||row.position.x%64||row.position.z%64))throw new Error('Mixed layout exceeds actor source-grid bounds.');return result;
}
export function decodeScenePlacementLayout(value,key,scene,ids,operation,expectedResetAxes=null){
  if(value?.schema_version!=='legaia.scene-placement-layout-review.v1'||JSON.stringify(value.operation)!==JSON.stringify(operation)||JSON.stringify(scenePlacementGroupDelta(value.delta))!==JSON.stringify({x:0,z:0}))throw new Error('Mixed layout operation differs from requested review.');
  decodeScenePlacementGroup({...value,schema_version:'legaia.scene-placement-group-review.v1',affected_count:0,project_change:false,targets:value.targets?.map(row=>({...row,proposed:{...row.current}}))},key,scene,ids,{x:0,z:0});
  const expected=mixedLayoutPositions(value.targets,operation);let changed=0;
  for(const [i,row] of value.targets.entries()){if(JSON.stringify(row.proposed)!==JSON.stringify(expected[i].position))throw new Error('Mixed layout positions differ from exact native arithmetic.');changed+=row.current.x!==row.proposed.x||row.current.z!==row.proposed.z;}
  let metadataChange=false;
  if(operation.kind==='reset'){
    const actorIds=ids.filter(id=>id.startsWith('scene://')),axes=value.reset_actor_axes;
    if(!axes||!expectedResetAxes||JSON.stringify(Object.keys(axes).sort())!==JSON.stringify(actorIds)||JSON.stringify(Object.keys(expectedResetAxes).sort())!==JSON.stringify(actorIds)||actorIds.some(id=>!Array.isArray(axes[id])||JSON.stringify(axes[id])!==JSON.stringify(expectedResetAxes[id])||axes[id].some(a=>!['x','z'].includes(a))||new Set(axes[id]).size!==axes[id].length))throw new Error('Retail reset differs from the Current authored actor axes.');
    metadataChange=actorIds.some(id=>axes[id].length>0);
  }
  if(value.affected_count!==changed||value.project_change!==(changed>0||metadataChange))throw new Error('Mixed layout change count differs from exact proposal.');return structuredClone(value);
}

export function offsetScenePlacementGroup(report,axis,amount){
  if(!['x','z'].includes(axis)||!Number.isSafeInteger(amount)||amount%64)throw new Error('Placement drag requires an X or Z offset in multiples of 64');
  const reviewed=decodeScenePlacementGroup(report,report?.project_source_key,report?.scene_id,report?.entity_ids,report?.delta);
  const delta=scenePlacementGroupDelta({...reviewed.delta,[axis]:reviewed.delta[axis]+amount});
  if(reviewed.targets.some(row=>!Number.isSafeInteger(row.proposed[axis]+amount)))throw new Error('Placement drag exceeds safe coordinates');
  return {entity_ids:[...reviewed.entity_ids],delta};
}

export function mountScenePlacementGroup({host,getState,getSelection,busy,setBusy,api,canReview,onInspection,onFrame=()=>{},onError=()=>{}}){
  const button=document.createElement('button');button.id='scene-placement-group-button';button.type='button';button.textContent='Move scene placement group…';host.append(button);
  const strip=document.createElement('div');strip.id='scene-placement-group-preview';strip.hidden=true;
  const note=document.createElement('span');note.textContent='Placement preview · proposal height held · runtime unknown · not applied';
  const returnButton=document.createElement('button');returnButton.type='button';returnButton.textContent='Return to placement review';
  const restoreButton=document.createElement('button');restoreButton.type='button';restoreButton.textContent='Restore placement preview';strip.append(note,returnButton,restoreButton);host.append(strip);
  let dialog=null,report=null,context=null,controller=null,generation=0,inspecting=false,inspectionLayer=null,retaining=false,renderReport=null,statusReport=null;
  const selection=()=>[...new Set(getSelection())].sort();
  const current=()=>{const s=getState();return !!context&&s.project?.mode==='edit'&&s.scene?.id===context.scene&&s.project_copy_source_key===context.key&&JSON.stringify(selection())===JSON.stringify(context.ids)&&canReview();};
  const delta=()=>{
    const values={};for(const axis of ['x','z']){const text=dialog.querySelector(`[name="${axis}"]`).value;if(!text.trim())throw new Error('Enter both placement offsets');values[axis]=Number(text);}return scenePlacementGroupDelta(values);
  };
  const request=()=>{const mode=dialog.querySelector('[name="layout-mode"]').value;if(mode==='offset')return {delta:delta()};if(mode==='reset')return {operation:{kind:'reset'}};if(mode==='scale'){const text=dialog.querySelector('[name="layout-percent"]').value,percent=Number(text);if(!text.trim()||!Number.isInteger(percent)||percent<1||percent>1000)throw new Error('Enter an integer spacing percentage from 1 through 1000.');return {operation:{kind:'scale',anchor_entity_id:dialog.querySelector('[name="layout-anchor"]').value,percent}};}if(mode.startsWith('rotate_'))return {operation:{kind:'rotate',anchor_entity_id:dialog.querySelector('[name="layout-anchor"]').value,quarter_turns:Number(mode.split('_')[1])}};const [kind,axis]=mode.split('_');return {operation:{kind,axis,...(kind==='align'?{anchor_entity_id:dialog.querySelector('[name="layout-anchor"]').value}:{})}};};
  const decode=(value,binding,requested)=>requested.operation?decodeScenePlacementLayout(value,binding.key,binding.scene,binding.ids,requested.operation,requested.operation.kind==='reset'?Object.fromEntries(binding.ids.filter(id=>id.startsWith('scene://')).map(id=>{const actor=getState().scene.entities.find(e=>e.id===id);if(!actor)throw new Error('Reset actor is absent from Current scene.');const position=actor.components.Transform.authored?.position??{};return [id,['x','z'].filter(a=>Object.hasOwn(position,a))];})):null):decodeScenePlacementGroup(value,binding.key,binding.scene,binding.ids,requested.delta);
  const restoreInspection=()=>{if(inspecting){inspecting=false;inspectionLayer=null;onInspection(null);}strip.hidden=true;note.textContent='Placement preview · proposal height held · runtime unknown · not applied';};
  const withdraw=()=>{generation++;if(controller){controller.abort();controller=null;setBusy(false);}report=null;restoreInspection();dialog?.querySelector('[data-result]')?.replaceChildren();};
  function restore(){context=null;withdraw();if(dialog){const old=dialog;dialog=null;if(old.open)old.close();old.remove();}refresh();}
  function refresh(){
    let eligible=false;try{placementIds(selection(),getState().scene?.id);eligible=getState().project?.mode==='edit'&&canReview();}catch{}
    button.disabled=busy()||!eligible;
    returnButton.disabled=busy();restoreButton.disabled=busy()&&!controller;
    if(context&&!current()){restore();return;}
    if(!dialog?.open)return;
    let valid=false;try{request();valid=true;}catch{}
    for(const item of dialog.querySelectorAll('input,select,[data-review],[data-apply],[data-inspect]'))item.disabled=busy();
    const mode=dialog.querySelector('[name="layout-mode"]').value,layout=mode!=='offset';for(const input of dialog.querySelectorAll('input[name="x"],input[name="z"]')){input.parentElement.hidden=layout;input.disabled=busy()||layout;}
    dialog.querySelector('[name="layout-anchor"]').parentElement.hidden=!(mode.startsWith('align_')||mode.startsWith('rotate_')||mode==='scale');
    const percent=dialog.querySelector('[name="layout-percent"]');percent.parentElement.hidden=mode!=='scale';percent.disabled=busy()||mode!=='scale';
    dialog.querySelector('[data-review]').disabled=busy()||!valid||!current();
    dialog.querySelector('[data-apply]').disabled=busy()||!valid||!current()||!report?.project_change;
    for(const item of dialog.querySelectorAll('[data-inspect]'))item.disabled=busy()||!report||!current();
  }
  button.onclick=()=>{
    if(button.disabled||busy())return;restore();
    const s=getState();context={key:s.project_copy_source_key,scene:s.scene.id,ids:selection()};placementIds(context.ids,context.scene);
    dialog=document.createElement('dialog');dialog.id='scene-placement-group-dialog';dialog.className='project-dialog';dialog.style.width='min(800px,90vw)';dialog.style.maxHeight='90vh';dialog.style.overflowY='auto';
    dialog.innerHTML='<h2>Move scene placement group</h2><p>Review X/Z offsets for selected imported actors and static decorations. Apply records the group as one Undo step. Alignment uses a selected actor or decoration anchor on the 64-unit actor grid. Distribution preserves grid endpoints with nearest spacing and stable identity ties. Reset X/Z to Retail restores source positions and clears selected actor X/Z overrides, preserving height, facing and other components. Position rotation uses the selected anchor, including decorations between actor grid points: +90 maps relative (X,Z) to (-Z,X), then rounds final actor coordinates to 64 units and leaves scenery at native integer precision. Half steps round away from zero. The selected anchor stays fixed. Spacing scale uses 1–1000 percent around the selected anchor, rounding final actor coordinates to 64 units and decoration coordinates to 1 unit. Half steps round away from zero. The selected anchor stays fixed, including decorations between actor grid points. Height, facing and object rotations stay unchanged. Proposal height is held; runtime behavior remains unknown.</p><form><label>Operation<select name="layout-mode" aria-label="Mixed placement operation"><option value="offset">Shared offset</option><option value="align_x">Align X to selected anchor</option><option value="align_z">Align Z to selected anchor</option><option value="distribute_x">Distribute X on grid</option><option value="distribute_z">Distribute Z on grid</option><option value="scale">Scale spacing at native precision</option><option value="reset">Reset X/Z to Retail</option><option value="rotate_1">Rotate positions +90° in X/Z</option><option value="rotate_-1">Rotate positions -90° in X/Z</option><option value="rotate_2">Rotate positions 180° in X/Z</option></select></label><label hidden>Anchor<select name="layout-anchor" aria-label="Mixed placement layout anchor"></select></label><label hidden>Spacing percent<input name="layout-percent" type="number" min="1" max="1000" step="1" value="100" aria-label="Mixed placement spacing percent"></label><div class="dialog-actions"><label>X offset<input name="x" type="number" step="64" min="-16320" max="16320" value="0" required aria-label="Scene placement group X offset"></label><label>Z offset<input name="z" type="number" step="64" min="-16320" max="16320" value="0" required aria-label="Scene placement group Z offset"></label></div><button data-review type="submit">Review group</button></form><p data-status role="status"></p><div data-result style="max-height:40vh;overflow:auto"></div><div class="dialog-actions"><button data-inspect="proposed" type="button" disabled>Inspect proposed placements</button><button data-inspect="current" type="button" disabled>Inspect current placements</button><button data-apply type="button" disabled>Apply group</button><button data-close type="button">Cancel</button></div>';
    const activeDialog=dialog;for(const id of context.ids){const option=document.createElement('option');option.value=id;option.textContent=id;dialog.querySelector('[name="layout-anchor"]').append(option);}
    const status=text=>{if(dialog===activeDialog)activeDialog.querySelector('[data-status]').textContent=text;};
    const render=()=>{
      const output=dialog.querySelector('[data-result]');output.replaceChildren();status(`${report.targets.length} placements reviewed · ${report.affected_count} placements change${report.operation?.kind==='reset'?' / '+Object.values(report.reset_actor_axes).reduce((n,axes)=>n+axes.length,0)+' authored actor axes clear':''}.`);
      const table=document.createElement('table'),head=document.createElement('tr');table.style.width='100%';table.style.fontSize='.85em';for(const text of ['Placement','Retail X/Z','Current X/Z','Proposed X/Z']){const th=document.createElement('th');th.textContent=text;th.style.padding='8px';th.style.textAlign='left';head.append(th);}table.append(head);
      for(const row of report.targets){const tr=document.createElement('tr');for(const text of [row.entity_id,...['retail','current','proposed'].map(layer=>`${row[layer].x} / ${row[layer].z}`)]){const td=document.createElement('td');td.textContent=text;td.style.padding='8px';td.style.overflowWrap='anywhere';tr.append(td);}table.append(tr);}output.append(table);
    };
    renderReport=render;statusReport=status;
    activeDialog.querySelector('form').oninput=()=>{withdraw();status('Placement operation changed; review again.');refresh();};
    activeDialog.querySelector('form').onsubmit=async event=>{
      event.preventDefault();if(busy()||!current()||(!request().operation&&!activeDialog.querySelector('form').reportValidity()))return;
      let requested;try{requested=request();}catch(error){status(error.message);return;}
      withdraw();const token=++generation,binding=context,requestController=new AbortController();controller=requestController;setBusy(true);refresh();
      try{
        const response=await fetch(requested.operation?'/api/scene-placement-layout-review':'/api/scene-placement-group-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:binding.scene,entity_ids:binding.ids,...requested}),signal:requestController.signal});
        const value=await response.json();if(!response.ok||value.error)throw new Error(value.error||'Scene placement group review failed');
        if(dialog!==activeDialog||!activeDialog.open||generation!==token||context!==binding||!current()||JSON.stringify(request())!==JSON.stringify(requested))return;
        report=decode(value,binding,requested);render();
      }catch(error){if(error.name!=='AbortError'&&dialog===activeDialog&&activeDialog.open&&generation===token){status(error.message);onError(error.message);}}
      finally{if(controller===requestController){controller=null;setBusy(false);}refresh();}
    };
    activeDialog.querySelector('[data-apply]').onclick=async()=>{
      if(busy()||!current()||!report?.project_change||JSON.stringify(request())!==JSON.stringify(report.operation?{operation:report.operation}:{delta:report.delta}))return;
      const reviewed=report;
      if(await api('/api/command',{type:reviewed.operation?'apply_scene_placement_layout':'apply_scene_placement_group',entity_id:context.scene,entity_ids:context.ids,...(reviewed.operation?{operation:reviewed.operation}:{delta:reviewed.delta}),review_key:reviewed.review_key}))restore();
      else{withdraw();status('Scene placement group was rejected. Review current placements again.');refresh();}
    };
    for(const item of activeDialog.querySelectorAll('[data-inspect]'))item.onclick=()=>{
      if(busy()||!report||!current()||JSON.stringify(request())!==JSON.stringify(report.operation?{operation:report.operation}:{delta:report.delta}))return;
      inspecting=true;inspectionLayer=item.dataset.inspect;note.textContent=item.dataset.inspect==='proposed'?(report.operation?'Proposed placement layout · height and rotation held · runtime unknown · not applied':'Proposed placements · X/Z handles snap 64 · height held · runtime unknown · not applied'):'Current placements · runtime unknown';strip.hidden=false;retaining=true;activeDialog.close();onInspection(report,item.dataset.inspect);onFrame(report);refresh();
    };
    activeDialog.querySelector('[data-close]').onclick=()=>activeDialog.close();
    activeDialog.addEventListener('close',()=>{if(retaining){retaining=false;return;}if(dialog===activeDialog)restore();});
    document.body.append(activeDialog);activeDialog.showModal();refresh();
  };
  returnButton.onclick=()=>{if(busy()||!report||!current()||!dialog)return;restoreInspection();dialog.showModal();refresh();};
  restoreButton.onclick=()=>{if(!busy()||controller)restore();};
  async function moveProposal(axis,amount,expectedReviewKey){
    if(busy()||!current()||!inspecting||inspectionLayer!=='proposed'||!report||report.operation||report.review_key!==expectedReviewKey||amount===0)return false;
    let requested;try{requested=offsetScenePlacementGroup(report,axis,amount);}catch(error){note.textContent=`Drag rejected: ${error.message}`;onError(error.message);return false;}
    const reviewed=report,binding=context,activeDialog=dialog,token=++generation,requestController=new AbortController();controller=requestController;
    setBusy(true);note.textContent='Reviewing dragged placement offset…';refresh();
    try{
      const response=await fetch('/api/scene-placement-group-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:binding.scene,...requested}),signal:requestController.signal});
      const value=await response.json();if(!response.ok||value.error)throw new Error(value.error||'Scene placement group review failed');
      if(dialog!==activeDialog||generation!==token||context!==binding||!current()||!inspecting||inspectionLayer!=='proposed'||report!==reviewed)return false;
      const fresh=decodeScenePlacementGroup(value,binding.key,binding.scene,binding.ids,requested.delta);
      report=fresh;for(const name of ['x','z'])activeDialog.querySelector(`[name="${name}"]`).value=String(fresh.delta[name]);
      renderReport();note.textContent='Proposed placements · X/Z handles snap 64 · height held · runtime unknown · not applied';onInspection(fresh,'proposed');return true;
    }catch(error){
      if(error.name!=='AbortError'&&dialog===activeDialog&&generation===token&&context===binding&&current()&&inspecting&&inspectionLayer==='proposed'&&report===reviewed){note.textContent=`Drag rejected: ${error.message}`;statusReport(error.message);onError(error.message);}
      return false;
    }finally{if(controller===requestController){controller=null;setBusy(false);}refresh();}
  }
  return {restore,refresh,moveProposal};
}
