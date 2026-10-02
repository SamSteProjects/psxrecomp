export function wallRectangle(value){
  const fields=['row_start','row_end','column_start','column_end','quadrant','blocked'];
  if(!value||Object.keys(value).sort().join()!==fields.sort().join())throw new Error('Invalid wall rectangle fields');
  for(const [field,low,high] of [['row_start',1,127],['row_end',1,127],['column_start',0,127],['column_end',0,127]])if(!Number.isSafeInteger(value[field])||value[field]<low||value[field]>high)throw new Error('Rectangle bounds are outside the canonical grid');
  if(!(value.quadrant==='all'||Number.isInteger(value.quadrant)&&value.quadrant>=0&&value.quadrant<=3)||typeof value.blocked!=='boolean'||value.row_start>value.row_end||value.column_start>value.column_end)throw new Error('Rectangle bounds must be ordered; quadrant and blocked must be valid');
  const count=(value.row_end-value.row_start+1)*(value.column_end-value.column_start+1)*(value.quadrant==='all'?4:1);if(count>4096)throw new Error('Rectangle exceeds 4096 wall bits');return Object.fromEntries(['row_start','row_end','column_start','column_end','quadrant','blocked'].map(key=>[key,value[key]]));
}
export function decodeWallRectangle(value,key,scene,rectangle){
  const hash=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);rectangle=wallRectangle(rectangle);
  if(value?.schema_version!=='legaia.collision-rectangle-review.v1'||value.project_source_key!==key||!hash(key)||!hash(value.review_key)||!hash(value.source_sha256)||value.scene_id!==scene||value.scope!=='source-MAP-wall-bits-only'||value.gameplay_verified!==false||typeof value.project_change!=='boolean'||JSON.stringify(wallRectangle(value.rectangle))!==JSON.stringify(rectangle)||!Array.isArray(value.rows)||value.rows.length!==value.wall_bit_count||value.rows.length!==(rectangle.row_end-rectangle.row_start+1)*(rectangle.column_end-rectangle.column_start+1)*(rectangle.quadrant==='all'?4:1))throw new Error('Invalid or stale wall rectangle review');
  const seen=new Set();let changed=0;
  for(const row of value.rows){if(!row||!Number.isInteger(row.row)||row.row<rectangle.row_start||row.row>rectangle.row_end||!Number.isInteger(row.column)||row.column<rectangle.column_start||row.column>rectangle.column_end||!Number.isInteger(row.quadrant)||row.quadrant<0||row.quadrant>3||rectangle.quadrant!=='all'&&row.quadrant!==rectangle.quadrant||[row.retail,row.effective,row.proposed].some(x=>typeof x!=='boolean')||row.proposed!==rectangle.blocked||seen.has(`${row.row}/${row.column}/${row.quadrant}`))throw new Error('Invalid reviewed wall bit');seen.add(`${row.row}/${row.column}/${row.quadrant}`);changed+=row.effective!==row.proposed;}
  if(changed!==value.effective_change_count||!Number.isSafeInteger(value.authored_bit_count)||value.authored_bit_count<0||value.authored_bit_count>4096)throw new Error('Invalid rectangle totals');return structuredClone({...value,rectangle});
}
// Uses the same canonical X/Z reference plane as the source-wall scene overlay.
export function wallRectangleGeometry(review,layer='proposed'){
  if(!['retail','effective','proposed'].includes(layer))throw new Error('Invalid wall comparison layer');
  const rectangle=wallRectangle(review.rectangle),x=rectangle.column_start*128,z=(rectangle.row_start-1)*128;
  return {x,z,width:(rectangle.column_end-rectangle.column_start+1)*128,height:(rectangle.row_end-rectangle.row_start+1)*128,
    cells:review.rows.map(row=>({x:row.column*128+(row.quadrant&1)*64-x,z:(row.row-1)*128+(row.quadrant>>1)*64-z,
      blocked:row[layer],changed:row.effective!==row.proposed,row:row.row,column:row.column,quadrant:row.quadrant}))};
}
export function wallRectangleMap(review){
  const wrap=document.createElement('section'),label=document.createElement('label'),select=document.createElement('select');
  label.textContent='Spatial comparison';select.setAttribute('aria-label','Wall rectangle comparison');
  for(const [value,text] of [['proposed','Proposed'],['effective','Current'],['retail','Retail']]){const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);}
  label.append(select);const caption=document.createElement('p'),canvas=document.createElementNS('http://www.w3.org/2000/svg','svg');
  canvas.setAttribute('role','img');canvas.style.width='100%';canvas.style.height='260px';canvas.style.background='#171e29';
  const draw=()=>{
    const geometry=wallRectangleGeometry(review,select.value);canvas.replaceChildren();canvas.setAttribute('viewBox',`0 0 ${geometry.width} ${geometry.height}`);
    canvas.setAttribute('aria-label',`${select.selectedOptions[0].textContent} source wall rectangle, X increases right, Z increases down`);
    for(const cell of geometry.cells){const rect=document.createElementNS(canvas.namespaceURI,'rect');rect.setAttribute('x',cell.x);rect.setAttribute('y',cell.z);rect.setAttribute('width','64');rect.setAttribute('height','64');rect.setAttribute('fill',cell.blocked?'#dc9851':'#314359');rect.setAttribute('stroke',cell.changed?'#68f0ac':'#8c9aac');rect.setAttribute('stroke-width',cell.changed?'3':'1');
      const title=document.createElementNS(canvas.namespaceURI,'title');title.textContent=`Row ${cell.row}, column ${cell.column}, quadrant ${cell.quadrant}: ${cell.blocked?'blocked':'unblocked'}${cell.changed?' · proposed change':''}`;rect.append(title);canvas.append(rect);}
    caption.textContent=`Source overlay X ${geometry.x}–${geometry.x+geometry.width}, Z ${geometry.z}–${geometry.z+geometry.height}. X →, Z ↓. Orange blocked; blue unblocked; dark unreviewed; green outline proposed change. Reference plane only.`;
  };
  select.onchange=draw;wrap.append(label,canvas,caption);draw();return wrap;
}
export function mountWallRectangle({host,getState,busy,setBusy,api,sourceCurrent,hasDraft,closeInspector,onInspection=()=>{},onFrame=()=>{}}){
  const button=document.createElement('button');button.type='button';button.textContent='Edit wall rectangle…';host.append(button);
  const strip=document.createElement('div');strip.id='collision-rectangle-preview';strip.hidden=true;
  const note=document.createElement('span');note.textContent='Source wall preview · not applied';
  const returnButton=document.createElement('button');returnButton.type='button';returnButton.textContent='Return to wall review';
  const restoreButton=document.createElement('button');restoreButton.type='button';restoreButton.textContent='Restore wall preview';strip.append(note,returnButton,restoreButton);host.append(strip);
  let dialog=null,context=null,reviewed=null,controller=null,generation=0,inspecting=false;
  const retainedClosures=new WeakSet();
  const current=()=>{const s=getState();return !!context&&sourceCurrent()&&s.project?.mode==='edit'&&s.project_copy_source_key===context.key&&s.scene?.id===context.scene;};
  const rectangle=()=>wallRectangle({row_start:Number(dialog.querySelector('[name="row_start"]').value),row_end:Number(dialog.querySelector('[name="row_end"]').value),column_start:Number(dialog.querySelector('[name="column_start"]').value),column_end:Number(dialog.querySelector('[name="column_end"]').value),quadrant:dialog.querySelector('[name="quadrant"]').value==='all'?'all':Number(dialog.querySelector('[name="quadrant"]').value),blocked:dialog.querySelector('[name="blocked"]').checked});
  const restoreInspection=()=>{if(inspecting){inspecting=false;onInspection(null);}strip.hidden=true;note.textContent='Source wall preview · not applied';};
  const withdraw=()=>{generation++;if(controller){controller.abort();controller=null;setBusy(false);}reviewed=null;restoreInspection();dialog?.querySelector('[data-result]')?.replaceChildren();};
  function restore(){context=null;withdraw();if(dialog){const old=dialog;dialog=null;if(old.open)old.close();old.remove();}refresh();}
  function refresh(){
    button.disabled=busy()||!sourceCurrent()||getState().project?.mode!=='edit';returnButton.disabled=busy();restoreButton.disabled=busy()&&!controller;
    if(context&&!current()){restore();return;}
    if(!dialog?.open)return;
    let valid=false;try{rectangle();valid=true;}catch{}
    for(const item of dialog.querySelectorAll('input,select,[data-review],[data-apply],[data-inspect]'))item.disabled=busy();
    dialog.querySelector('[data-review]').disabled=busy()||!valid||!current();
    dialog.querySelector('[data-apply]').disabled=busy()||!valid||!current()||!reviewed?.project_change;
    for(const item of dialog.querySelectorAll('[data-inspect]'))item.disabled=busy()||!reviewed||!current();
  }
  function open(seed){
    if(busy()||!sourceCurrent()||getState().project?.mode!=='edit')return false;
    if(hasDraft()){const error=document.createElement('p');error.textContent='Apply or discard the single-cell wall change first.';host.append(error);return false;}
    const initialRectangle=wallRectangle(seed??{row_start:1,row_end:1,column_start:0,column_end:0,quadrant:'all',blocked:false});restore();
    const initial=getState();context={key:initial.project_copy_source_key,scene:initial.scene.id};
    dialog=document.createElement('dialog');dialog.id='collision-rectangle-dialog';dialog.className='project-dialog';dialog.style.width='min(800px,90vw)';dialog.style.maxHeight='90vh';dialog.style.overflowY='auto';
    const activeDialog=dialog,binding=context;
    const heading=document.createElement('h2');heading.textContent='Source wall rectangle';const description=document.createElement('p');description.textContent='Inclusive canonical grid bounds. Only wall bits change; floor tiers, other edits and runtime collision paints are separate.';const form=document.createElement('form');form.style.display='grid';form.style.gridTemplateColumns='repeat(2,minmax(0,1fr))';form.style.gap='12px';
    for(const [field,label,minimum,maximum] of [['row_start','First row',1,127],['row_end','Last row',1,127],['column_start','First column',0,127],['column_end','Last column',0,127]]){const element=document.createElement('label');element.textContent=label;const input=document.createElement('input');input.name=field;input.type='number';input.min=minimum;input.max=maximum;input.step=1;input.value=initialRectangle[field];input.required=true;input.setAttribute('aria-label',label);element.append(input);form.append(element);}
    const label=document.createElement('label');label.textContent='Quadrants';const quadrant=document.createElement('select');quadrant.name='quadrant';quadrant.setAttribute('aria-label','Rectangle quadrants');for(const [value,text] of [['all','All four'],['0','0 · low X / low Z'],['1','1 · high X / low Z'],['2','2 · low X / high Z'],['3','3 · high X / high Z']]){const option=document.createElement('option');option.value=value;option.textContent=text;quadrant.append(option);}quadrant.value=String(initialRectangle.quadrant);label.append(quadrant);form.append(label);
    const blockedLabel=document.createElement('label');blockedLabel.textContent='Blocked';blockedLabel.style.display='flex';blockedLabel.style.alignItems='center';blockedLabel.style.gap='8px';const blocked=document.createElement('input');blocked.style.width='auto';blocked.name='blocked';blocked.type='checkbox';blocked.checked=initialRectangle.blocked;blocked.setAttribute('aria-label','Rectangle blocked');blockedLabel.append(blocked);form.append(blockedLabel);
    const reviewButton=document.createElement('button');reviewButton.textContent='Review rectangle';reviewButton.dataset.review='';reviewButton.style.gridColumn='1/-1';form.append(reviewButton);
    const status=document.createElement('p');status.setAttribute('role','status');const output=document.createElement('div');output.dataset.result='';output.style.maxHeight='40vh';output.style.overflowY='auto';
    const actions=document.createElement('div');actions.className='dialog-actions';
    for(const [layer,text] of [['proposed','Inspect proposed walls'],['effective','Inspect current walls'],['retail','Inspect retail walls']]){const item=document.createElement('button');item.type='button';item.dataset.inspect=layer;item.textContent=text;item.disabled=true;item.onclick=()=>{if(busy()||!reviewed||!current()||JSON.stringify(rectangle())!==JSON.stringify(reviewed.rectangle))return;inspecting=true;note.textContent=`${layer==='effective'?'Current':layer==='retail'?'Retail':'Proposed'} source walls · ${reviewed.wall_bit_count} bits · Y=0 reference plane · not applied`;strip.hidden=false;retainedClosures.add(activeDialog);activeDialog.close();onInspection(reviewed,layer);onFrame(reviewed);refresh();};actions.append(item);}
    const apply=document.createElement('button');apply.type='button';apply.dataset.apply='';apply.textContent='Apply rectangle';apply.disabled=true;const close=document.createElement('button');close.type='button';close.dataset.close='';close.textContent='Cancel';close.onclick=()=>activeDialog.close();actions.append(apply,close);
    activeDialog.addEventListener('close',()=>{if(retainedClosures.delete(activeDialog))return;if(dialog===activeDialog)restore();});activeDialog.append(heading,description,form,status,output,actions);document.body.append(activeDialog);activeDialog.showModal();
    form.oninput=()=>{withdraw();status.textContent='Inputs changed; review again.';refresh();};
    form.onsubmit=async event=>{
      event.preventDefault();if(busy()||!current()||!form.reportValidity())return;
      let requested;try{requested=rectangle();}catch(error){status.textContent=error.message;return;}
      withdraw();const token=++generation,requestController=new AbortController();controller=requestController;setBusy(true);refresh();
      try{
        const response=await fetch('/api/collision-rectangle-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:binding.scene,rectangle:requested}),signal:requestController.signal});const value=await response.json();if(!response.ok||value.error)throw new Error(value.error||'Rectangle review failed');
        if(dialog!==activeDialog||!activeDialog.open||generation!==token||context!==binding||!current()||JSON.stringify(requested)!==JSON.stringify(rectangle()))return;
        reviewed=decodeWallRectangle(value,binding.key,binding.scene,requested);status.textContent=`${reviewed.wall_bit_count} selected wall bits · ${reviewed.effective_change_count} effective changes · ${reviewed.authored_bit_count} total authored bits. Showing all selected bits spatially and up to 64 table rows.`;output.append(wallRectangleMap(reviewed));const table=document.createElement('table');const header=document.createElement('tr');for(const text of ['Row','Column','Quadrant','Retail','Current','Proposed']){const cell=document.createElement('th');cell.textContent=text;header.append(cell);}table.append(header);for(const row of reviewed.rows.slice(0,64)){const tr=document.createElement('tr');for(const value of [row.row,row.column,row.quadrant,...[row.retail,row.effective,row.proposed].map(x=>x?'blocked':'unblocked')]){const cell=document.createElement('td');cell.textContent=value;tr.append(cell);}table.append(tr);}output.append(table);
      }catch(error){if(error.name!=='AbortError'&&dialog===activeDialog&&activeDialog.open&&generation===token)status.textContent=error.message;}
      finally{if(controller===requestController){controller=null;setBusy(false);}refresh();}
    };
    apply.onclick=async()=>{if(busy()||!reviewed?.project_change||!current()||JSON.stringify(rectangle())!==JSON.stringify(reviewed.rectangle))return;const report=reviewed;if(await api('/api/command',{type:'apply_collision_rectangle',entity_id:binding.scene,rectangle:report.rectangle,review_key:report.review_key})){restore();closeInspector();}else{withdraw();status.textContent='Wall rectangle was rejected. Review current wall bits again.';refresh();}};
    refresh();return true;
  }
  button.onclick=()=>open();returnButton.onclick=()=>{if(busy()||!reviewed||!current()||!dialog)return;restoreInspection();dialog.showModal();refresh();};restoreButton.onclick=()=>{if(!busy()||controller)restore();};
  refresh();return {open,restore,refresh};
}
