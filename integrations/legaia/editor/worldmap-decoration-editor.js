import {qualifyWorldDecorationSource, qualifyWorldDecorationReview, worldDecorationDraft,
  worldDecorationDonorValues,qualifyWorldDecorationTransformReview,qualifyWorldDecorationRemovalReview,qualifyWorldDecorationCellReview,qualifyWorldDecorationModelReview,qualifyWorldDecorationGroupReview,transformWorldDecorationGroup} from './worldmap-decoration-state.js';
import {validValues} from './worldmap-placement-state.js';
const node = (tag, text) => { const element = document.createElement(tag); if (text) element.textContent = text; return element; };

export function mountWorldDecorationEditor({host, getContext, getState, busy, setBusy, api, onPreview, onDiscard, onApplied, onError,onTransformDraft=()=>{}}) {
  const panel = node('details'), summary = node('summary', 'World Decoration Authoring'), status = node('p');
  panel.dataset.worldDecorationEditor = ''; status.setAttribute('role', 'status');
  const inspect = node('button', 'Inspect decoration donors'), editSelected = node('button','Edit selected decoration'),removeReview=node('button','Review decoration removal'),reviewButton = node('button', 'Review decoration'),
    preview = node('button', 'Preview reviewed decoration'), apply = node('button', 'Apply reviewed decoration'), discard = node('button', 'Discard decoration');
  const actions = node('div'); actions.className = 'dialog-actions'; actions.style.flexWrap = 'wrap';
  const cellReview=node('button','Review decoration cell move'),modelReview=node('button','Review decoration model');
  for (const button of [inspect, editSelected,reviewButton,cellReview,modelReview,removeReview, preview, apply, discard]) { button.type = 'button'; actions.append(button); }
  const fields = node('div'); Object.assign(fields.style, {display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: '8px'});
  const donor = node('select'), target = node('input'), yaw = node('input'), offsets = {};
  const addField = (label, input) => {
    const wrapper = node('label', label); input.setAttribute('aria-label', label);
    Object.assign(input.style, {display: 'block', width: '100%', maxWidth: '100%', boxSizing: 'border-box'});
    wrapper.append(input); fields.append(wrapper);
  };
  addField('World decoration donor', donor); target.type = 'number'; target.min = '0'; target.max = '16383'; target.step = '1'; addField('World decoration target cell', target);
  const destination=node('input');destination.type='number';destination.min='0';destination.max='16383';destination.step='1';addField('World decoration new native cell',destination);
  const model=node('select');addField('World decoration replacement model',model);
  const group=node('details'),groupList=node('div'),groupFields=node('div'),groupDelta={},groupReview=node('button','Review decoration group'),groupAll=node('button','Select all decorations'),groupNone=node('button','Clear decoration group');
  group.dataset.worldDecorationGroup='';group.append(node('summary','Transform Authored Decoration Group'),node('p','Inspect decoration donors, select up to 32 retained decorations, then review a relative native XYZ/yaw delta. Use Preview, Apply and Discard above. Yaw rotates each orientation; positions do not orbit. Apply creates one history command. Select All is unavailable when there are more than 32 decorations.'),groupList,groupFields,groupAll,groupNone,groupReview);
  Object.assign(groupList.style,{maxHeight:'200px',overflow:'auto',overflowWrap:'anywhere'});
  Object.assign(groupFields.style,{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))',gap:'8px'});
  for(const axis of ['x','y','z','yaw_units']){const input=node('input');input.type='number';input.min=axis==='yaw_units'?'-4095':'-65535';input.max=axis==='yaw_units'?'4095':'65535';input.step='1';input.value='0';input.setAttribute('aria-label','Decoration group delta '+(axis==='yaw_units'?'yaw':axis.toUpperCase()));const label=node('label',axis==='yaw_units'?'Yaw delta':'Native '+axis.toUpperCase()+' delta');Object.assign(input.style,{display:'block',width:'100%',boxSizing:'border-box'});label.append(input);groupFields.append(label);groupDelta[axis]=input;}
  for(const button of [groupReview,groupAll,groupNone])button.type='button';
  for (const axis of ['x','y','z']) { const input = node('input'); input.type = 'number'; input.min = '-32768'; input.max = '32767'; input.step = '1'; offsets[axis] = input; addField('World decoration offset ' + axis.toUpperCase(), input); }
  yaw.type = 'number'; yaw.min = '0'; yaw.max = '4095'; yaw.step = '1'; addField('World decoration yaw units', yaw);
  const move=node('input');move.type='checkbox';move.id='world-decoration-translate';const moveLabel=node('label','Translate selected decoration ');moveLabel.append(move);const snap=node('select');snap.setAttribute('aria-label','Decoration translation snap');for(const step of [1,16,64,128]){const option=node('option',step+' source units');option.value=String(step);snap.append(option);}
  const rotate=node('input');rotate.type='checkbox';rotate.id='world-decoration-rotate';const rotateLabel=node('label','Rotate selected decoration yaw ');rotateLabel.append(rotate);const yawSnap=node('select');yawSnap.setAttribute('aria-label','Decoration yaw snap');for(const step of [1,16,64,256,512,1024]){const option=node('option',`${step} yaw units (${step*360/4096}°)`);option.value=String(step);yawSnap.append(option);}
  const evidence = node('pre'); evidence.className = 'diagnostic-detail';
  Object.assign(evidence.style, {whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', maxHeight: '220px', overflow: 'auto'});
  panel.append(summary, node('p', 'Create a walk decoration from a drawable Current donor, or edit the selected retained decoration’s signed offsets and yaw. Transform edits retain the same cell. Move Cell preserves UUID, record, model and encoded offsets while changing native position from the destination row, column and floor height. Review and preview leave the project unchanged. Apply uses shared Undo/Redo.'), fields,moveLabel,snap,rotateLabel,yawSnap,node('p','Choose Edit selected decoration, then translate with X/Y/Z handles or rotate with the yaw ring. This is an unreviewed display draft. Native Review and Proposed preview are required before Apply. Y and Z follow native offset directions, with one reflection into editor space. Cell moves and model assignments require unchanged offset/yaw fields; Apply those edits or restore Current offset/yaw values first. Model assignment preserves cell, record, XYZ/yaw and child models. Saved views bound to an old cell or model must be recreated.'), actions, status, evidence); host.append(panel);
  fields.before(node('p','Removal Review restores the selected record and cell, lists donor reassignments and checks that surviving decorations stay unchanged. Preview the removal before Apply.'));
  panel.append(group);
  let source = null, held = null, review = null, placementId = null, editing = false,displayed = false, controller = null, pendingKind = null, generation = 0;
  const groupIds=()=>[...groupList.querySelectorAll('input:checked')].map(i=>i.value).sort();
  const groupValues=()=>Object.fromEntries(Object.entries(groupDelta).map(([a,i])=>[a,i.value===''?NaN:Number(i.value)]));
  function groupChanged(){withdrawReview();status.textContent='Group draft changed. Review the selected identities and delta again.';}
  for(const input of Object.values(groupDelta))input.oninput=groupChanged;
  groupAll.onclick=()=>{if(groupAll.disabled)return;for(const input of groupList.querySelectorAll('input'))input.checked=true;groupChanged();};
  groupNone.onclick=()=>{if(groupNone.disabled)return;for(const input of groupList.querySelectorAll('input'))input.checked=false;groupChanged();};
  const contextMatches = context => {
    const now = getContext(); return !!now && !!context && now.path === context.path && now.key === context.key &&
      now.current === context.current && now.retail === context.retail;
  };
  const sourceReady = () => !!source && contextMatches(held);
  const fieldValues = () => ({offset: Object.fromEntries(['x','y','z'].map(axis => [axis, offsets[axis].value === '' ? NaN : Number(offsets[axis].value)])),
    yaw_units: yaw.value === '' ? NaN : Number(yaw.value)});
  function draft() {
    const values = fieldValues(); if (!validValues(values) || target.value === '' || donor.value === '') throw Error('Enter signed integer offsets, yaw 0–4095 and an available target cell.');
    if(editing){if(JSON.stringify(values)===JSON.stringify(worldDecorationDonorValues(source,Number(donor.value))))throw Error('Decoration transform is unchanged.');return {placement_id:placementId,values};}
    return worldDecorationDraft(source, Number(donor.value), Number(target.value), values, undefined, placementId);
  }
  function withdrawReview() {
    onTransformDraft(null);review = null; if (displayed) { displayed = false; onDiscard(); }
    evidence.textContent = ''; update();
  }
  function change() { withdrawReview();const draft=transformDraft();if(draft)onTransformDraft(draft);status.textContent = sourceReady() ? 'Draft changed. Review the current donor, target, offsets and yaw again.' : 'Inspect Current decoration donors first.'; }
  function transformDraft(){
    if(!editing||!sourceReady()||getContext()?.selectedId!==held.selectedId||displayed||review||!validValues(fieldValues()))return null;
    const base=worldDecorationDonorValues(source,Number(donor.value)),values=fieldValues();
    return {entityId:held.selectedId,base,values,enabled:move.checked||rotate.checked,mode:move.checked?'translate':rotate.checked?'yaw':null,step:Number(snap.value),yawStep:Number(yawSnap.value),sourceKey:held.key};
  }
  function setTransformDraft(values,restoring=false){
    if(!validValues(values)||(restoring?(!editing||!sourceReady()||pendingKind==='apply'):(pendingKind||busy()||!transformDraft())))return false;
    for(const axis of ['x','y','z'])offsets[axis].value=String(values.offset[axis]);yaw.value=String(values.yaw_units);change();return true;
  }
  move.onchange=()=>{if(move.checked)rotate.checked=false;onTransformDraft(transformDraft());update();};rotate.onchange=()=>{if(rotate.checked)move.checked=false;onTransformDraft(transformDraft());update();};snap.onchange=yawSnap.onchange=()=>{onTransformDraft(transformDraft());update();};
  function donorValues() {
    if (!sourceReady() || donor.value === '') return;
    const value = worldDecorationDonorValues(source, Number(donor.value));
    for (const axis of ['x','y','z']) offsets[axis].value = String(value.offset[axis]); yaw.value = String(value.yaw_units);
    const cell = Number(donor.value), col = cell % 128, row = Math.floor(cell / 128);
    const closest = source.inventory.target_cells.reduce((best, next) => {
      const distance = n => Math.abs(n % 128 - col) + Math.abs(Math.floor(n / 128) - row);
      return best === null || distance(next) < distance(best) ? next : best;
    }, null);
    target.value = editing ? donor.value : closest === null ? '' : String(closest);destination.value=closest===null?'':String(closest);
    model.value=String(source.inventory.donors.find(s=>s.source_cell===cell)?.model_pool_index??'');change();
  }
  donor.onchange = donorValues; for (const input of [target, destination, yaw, ...Object.values(offsets)]) input.oninput = change;
  model.onchange=change;
  function cancel() {
    move.checked=rotate.checked=false;generation++; controller?.abort(); source = held = review = placementId = null; displayed = editing = false;onTransformDraft(null);
    donor.replaceChildren();model.replaceChildren();groupList.replaceChildren(); evidence.textContent = ''; status.textContent = 'Switch to a qualified Current scene and inspect decoration donors.';
    if (pendingKind !== 'apply') { controller = null; if (pendingKind) setBusy(false); pendingKind = null; }
    update();
  }
  function update() {
    if (source && !contextMatches(held) && pendingKind !== 'apply') { cancel(); return; }
    const locked = !!pendingKind || busy(), available = !!getContext();
    const ids=groupIds(),delta=groupValues(),count=groupList.querySelectorAll('input').length;
    for(const input of [...groupList.querySelectorAll('input'),...Object.values(groupDelta)])input.disabled=locked||!sourceReady();
    groupAll.disabled=locked||!sourceReady()||count<1||count>32;groupNone.disabled=locked||!sourceReady()||!ids.length;
    groupReview.disabled=locked||!sourceReady()||ids.length<1||ids.length>32||Object.values(delta).some(n=>!Number.isInteger(n))||
      ['x','y','z'].some(a=>Math.abs(delta[a])>65535)||Math.abs(delta.yaw_units)>4095||!Object.values(delta).some(n=>n!==0)||
      (editing&&JSON.stringify(fieldValues())!==JSON.stringify(worldDecorationDonorValues(source,Number(donor.value))));
    move.disabled=rotate.disabled=locked||!transformDraft();snap.disabled=yawSnap.disabled=move.disabled;inspect.disabled = locked || !available;
    editSelected.disabled=locked||!available||!getContext()?.current.scene_graph.entities.some(e=>e.entity_id===getContext().selectedId&&e.placement_scope==='authored_spawn_seed');
    for (const field of [donor, target, yaw, ...Object.values(offsets)]) field.disabled = locked || !sourceReady();
    if(editing){donor.disabled=true;target.disabled=true;}
    destination.disabled=locked||!editing||!sourceReady();
    model.disabled=destination.disabled;
    let validDraft = false; if (sourceReady()) { try { draft(); validDraft = true; } catch {} }
    reviewButton.disabled = locked || !validDraft;
    removeReview.disabled=locked||!editing||!sourceReady();
    cellReview.disabled=locked||!editing||!sourceReady()||destination.value===''||!Number.isInteger(Number(destination.value))||
      !source?.inventory.target_cells.includes(Number(destination.value))||JSON.stringify(fieldValues())!==JSON.stringify(worldDecorationDonorValues(source,Number(donor.value)));
    modelReview.disabled=locked||!editing||!sourceReady()||model.value===''||!Number.isInteger(Number(model.value))||
      ![...model.options].some(o=>o.value===model.value)||Number(model.value)===source?.metadata.authored_allocations.find(a=>a.placement_id===placementId)?.model_pool_index||
      JSON.stringify(fieldValues())!==JSON.stringify(worldDecorationDonorValues(source,Number(donor.value)));
    preview.disabled = locked || !review || !sourceReady();
    apply.disabled = locked || !review || !displayed || !sourceReady();
    discard.disabled = locked || !source;
    if (!available && !pendingKind) status.textContent = 'Switch to Current authored scene to create a decoration.';
  }
  async function read(route, body, signal) {
    const response = await fetch(route, {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body), signal});
    const text = await response.text(); if (new TextEncoder().encode(text).length > 2 * 1024 * 1024) throw Error('Decoration source or Review exceeds its response budget.');
    const value = JSON.parse(text); if (!response.ok) throw Error(value.error || 'Decoration request failed.'); return value;
  }
  async function run(kind, work) {
    const context = getContext(), token = ++generation, request = new AbortController();
    if (!context || busy() || pendingKind) return;
    controller = request; pendingKind = kind; setBusy(true); update();
    const valid = () => controller === request && token === generation && contextMatches(context) && !request.signal.aborted;
    try { return await work(context, request.signal, valid); }
    catch (error) { if (error.name !== 'AbortError' && valid()) { status.textContent = error.message; onError(error); } }
    finally { if (controller === request) { controller = null; pendingKind = null; setBusy(false); update(); } }
  }
  function inspectDonors(edit=false) {
    if ((edit?editSelected:inspect).disabled) return;const selectedId=getContext()?.selectedId;withdrawReview();
    source=held=placementId=null;editing=false;
    return run('source', async (context, signal, valid) => {
      status.textContent = 'Checking complete Current native donor and target inventory…';
      const value = await read('/api/worldmap-placement-allocation-source', {scene: context.current.scene, source_key: context.key}, signal);
      const qualified = await qualifyWorldDecorationSource(value, context.current, context.path); if (!valid()) return;
      const selected = context.current.scene_graph.entities.find(e => e.entity_id === selectedId);
      if(edit&&selected?.placement_scope!=='authored_spawn_seed')throw Error('Select a retained Current authored decoration first.');
      source = qualified; held = {...context,selectedId}; editing=edit;placementId = edit?selected.authored_placement.placement_id:`placement://authored/${crypto.randomUUID()}`; donor.replaceChildren();
      for(const input of Object.values(groupDelta))input.value='0';
      groupList.replaceChildren();for(const row of source.metadata.authored_allocations){const input=node('input');input.type='checkbox';input.value=row.placement_id;input.setAttribute('aria-label','Group decoration '+row.placement_id);input.onchange=groupChanged;const label=node('label'),text=node('span',`Cell ${row.target_cell} · record ${row.record_index} · model ${row.model_pool_index} · ${row.placement_id.split('/').pop()}`);Object.assign(label.style,{display:'flex',alignItems:'flex-start',gap:'8px',padding:'4px 0'});Object.assign(input.style,{width:'auto',flex:'0 0 auto',margin:'4px 0'});text.style.minWidth='0';label.append(input,text);groupList.append(label);}
      const assets = new Set(context.current.scene_graph.assets.map(a => a.asset_id));
      for (const seed of source.inventory.donors) if (assets.has(`asset://${value.scene}/worldmap/models/${String(seed.model_pool_index).padStart(4,'0')}`)) {
        const option = node('option', `Cell ${seed.source_cell} · model ${seed.model_pool_index} · record ${seed.object_record_index}`); option.value = String(seed.source_cell); donor.append(option);
      }
      if (selected && [...donor.options].some(o => o.value === String(selected.source_cell))) donor.value = String(selected.source_cell);
      model.replaceChildren();
      for(const asset of context.current.scene_graph.assets){
        const index=Number(asset.asset_id.split('/').pop());
        if(!asset.asset_id.startsWith(`asset://${value.scene}/worldmap/models/`)||!Number.isInteger(index)||index<1||index>511||!asset.preview.vertices.length||!asset.preview.triangles.length)continue;
        const option=node('option',`Model ${index} · ${asset.preview.vertices.length} vertices · ${asset.preview.triangles.length} triangles`);option.value=String(index);model.append(option);
      }
      donorValues(); status.textContent = edit?`Editing retained decoration ${placementId}. Change offsets/yaw, or review a separate native cell move with unchanged encoded values.`:`${donor.options.length} drawable donors · ${value.target_cells.length} available target cells · ${value.free_record_indices.length} unused native records. Draft identity ${placementId}.`;
      return true;
    });
  }
  inspect.onclick=()=>inspectDonors(false);editSelected.onclick=()=>inspectDonors(true);
  groupReview.onclick=()=>{
    if(groupReview.disabled)return;withdrawReview();move.checked=rotate.checked=false;
    return run('group-review',async(context,signal,valid)=>{
      const ids=groupIds(),delta=groupValues();status.textContent='Checking every selected native transform and preserving unselected decorations…';
      await transformWorldDecorationGroup(source,ids,delta);
      const value=await read('/api/worldmap-decoration-group-review',{scene:context.current.scene,source_key:context.key,placement_ids:ids,delta},signal);
      const qualified=await qualifyWorldDecorationGroupReview(value,source,ids,delta);if(!valid())return;
      review=qualified;evidence.textContent=JSON.stringify({delta,placements:review.audit.placements.map(a=>({placement_id:a.placement_id,cell:a.after.target_cell,record:a.after.record_index,before:a.before.native_seed.source_position,after:a.after.native_seed.source_position})),proposed_map_sha256:review.proposed_map_sha256,review_key:review.review_key},null,2);
      status.textContent=`Group Review matches independent complete native replay for ${ids.length} decorations. Preview before Apply.`;
    });
  };
  modelReview.onclick=()=>{
    if(modelReview.disabled)return;withdrawReview();
    return run('model-review',async(context,signal,valid)=>{
      const id=placementId,index=Number(model.value);status.textContent='Checking the Current native model and preserving dependent child models…';
      const value=await read('/api/worldmap-decoration-model-review',{scene:context.current.scene,source_key:context.key,placement_id:id,model_pool_index:index},signal);
      const qualified=await qualifyWorldDecorationModelReview(value,source,id,index,context.current);if(!valid())return;
      review=qualified;evidence.textContent=JSON.stringify({placement_id:id,cell:review.audit.after.target_cell,record:review.audit.after.record_index,
        before_model:review.audit.before.model_pool_index,after_model:review.audit.after.model_pool_index,asset_id:review.asset_id,
        unchanged_native_position:review.audit.after.native_seed.source_position,retained_child_models:review.audit.retained_child_models,
        proposed_map_sha256:review.proposed_map_sha256,review_key:review.review_key},null,2);
      status.textContent='Model Review matches independent native replay. Only this decoration’s model changes; child models and transforms stay unchanged. Preview before Apply.';
    });
  };
  cellReview.onclick=()=>{
    if(cellReview.disabled)return;withdrawReview();
    return run('cell-review',async(context,signal,valid)=>{
      const id=placementId,cell=Number(destination.value);status.textContent='Replaying the native cell move and dependent donor recipes…';
      const value=await read('/api/worldmap-decoration-cell-review',{scene:context.current.scene,source_key:context.key,placement_id:id,target_cell:cell},signal);
      const qualified=await qualifyWorldDecorationCellReview(value,source,id,cell);if(!valid())return;
      review=qualified;evidence.textContent=JSON.stringify({placement_id:id,record_index:review.audit.after.record_index,
        before_cell:review.audit.before.target_cell,after_cell:review.audit.after.target_cell,
        before_position:review.audit.before.native_seed.source_position,after_position:review.audit.after.native_seed.source_position,
        before_floor_tier:review.audit.before.native_seed.source_floor_tier,after_floor_tier:review.audit.after.native_seed.source_floor_tier,
        before_terrain:review.audit.before.preserved_terrain_hex,after_terrain:review.audit.after.preserved_terrain_hex,
        rebased_donors:review.audit.rebased_donors,proposed_map_sha256:review.proposed_map_sha256,review_key:review.review_key},null,2);
      status.textContent='Cell move Review matches independent complete native replay. Encoded offsets/yaw and surviving poses are unchanged. Preview before Apply.';
    });
  };
  removeReview.onclick=()=>{
    if(removeReview.disabled)return;withdrawReview();
    return run('removal-review',async(context,signal,valid)=>{
      const id=placementId;status.textContent='Replaying removal and rebasing dependent donors without changing surviving bytes…';
      const value=await read('/api/worldmap-decoration-removal-review',{scene:context.current.scene,source_key:context.key,placement_id:id},signal);
      const qualified=await qualifyWorldDecorationRemovalReview(value,source,id);if(!valid())return;
      review=qualified;evidence.textContent=JSON.stringify({removed_placement:id,restored_cell:review.audit.removed.target_cell,
        cleared_record:review.audit.removed.record_index,rebased_donors:review.audit.rebased_donors,remaining_decorations:review.audit.remaining_allocations.length,
        proposed_map_sha256:review.proposed_map_sha256,review_key:review.review_key},null,2);
      status.textContent='Removal Review matches independent complete byte replay. Surviving seeds are unchanged. Preview the removal before Apply.';
    });
  };
  reviewButton.onclick = () => {
    if (reviewButton.disabled) return; withdrawReview();
    return run('review', async (context, signal, valid) => {
      const proposed=draft(),requests=editing?null:[proposed]; status.textContent = 'Replaying complete proposed MAP allocation and retained lineage…';
      const value = await read(editing?'/api/worldmap-decoration-transform-review':'/api/worldmap-placement-allocation-review', {scene: context.current.scene, source_key: context.key,...(editing?proposed:{requests})}, signal);
      const qualified = editing?await qualifyWorldDecorationTransformReview(value,source,placementId,proposed.values):await qualifyWorldDecorationReview(value, source, requests); if (!valid()) return;
      review = qualified; const allocation = editing?review.audit.after:review.audit.allocations[0];
      evidence.textContent = JSON.stringify({placement_id: allocation.placement_id, target_cell: allocation.target_cell,
        record_index: allocation.record_index, native_seed_position: allocation.native_seed.source_position,
        preserved_terrain_hex: allocation.preserved_terrain_hex, proposed_map_sha256: review.proposed_map_sha256,
        review_key: review.review_key}, null, 2);
      status.textContent = 'Native Review matches independent complete byte replay. Preview the reviewed decoration before Apply.';
    });
  };
  preview.onclick = () => {
    if (preview.disabled) return;
    return run('preview', async (context, signal, valid) => {
      const captured = review; status.textContent = 'Qualifying the Proposed native scene and Current model/texture assets…';
      const shown = await onPreview(context, captured, signal, valid); if (!valid() || review !== captured || shown !== true) return;
      displayed = true; status.textContent = captured.schema_version==='legaia.worldmap-decoration-group-review.v1'?`Proposed group displayed for ${captured.placement_ids.length} decorations; project unchanged. Apply creates one history command.`:captured.schema_version==='legaia.worldmap-decoration-removal-review.v1'?'Proposed removal displayed; project unchanged. Apply removes this decoration as one shared history command.':'Proposed decoration displayed; project unchanged. Apply keeps this placement as one shared history command.';
    });
  };
  apply.onclick = async () => {
    if (apply.disabled) return;
    const context = held, captured = review, request = new AbortController(); let applied = false;
    // The shared API owns the global busy lock; taking it here would refuse
    // our own command before it reaches the server.
    controller = request; pendingKind = 'apply'; update(); status.textContent = 'Applying the exact reviewed native decoration…';
    const grouping=captured.schema_version==='legaia.worldmap-decoration-group-review.v1',removing=captured.schema_version==='legaia.worldmap-decoration-removal-review.v1',relocating=captured.schema_version==='legaia.worldmap-decoration-cell-review.v1',assigning=captured.schema_version==='legaia.worldmap-decoration-model-review.v1';
    try { applied = await api('/api/command', {type: grouping?'transform_worldmap_authored_placements':removing?'remove_worldmap_authored_placement':relocating?'relocate_worldmap_authored_placement':assigning?'assign_worldmap_authored_model':captured.placement_id?'set_worldmap_authored_placement':'allocate_worldmap_placements', scene: context.current.scene,
      source_key: context.key,...(grouping?{placement_ids:captured.placement_ids,delta:captured.delta}:removing?{placement_id:captured.placement_id}:relocating?{placement_id:captured.placement_id,target_cell:captured.target_cell}:assigning?{placement_id:captured.placement_id,model_pool_index:captured.model_pool_index}:captured.placement_id?{placement_id:captured.placement_id,values:captured.values}:{requests:captured.requests}),review_key: captured.review_key}) === true;
      if (!applied) throw Error('Decoration Apply failed. Inspect fresh Current sources before retrying.');
    } catch (error) { status.textContent = error.message; onError(error); }
    finally {
      if (!applied && displayed) onDiscard();
      controller = null; pendingKind = null; source = held = review = placementId = null; displayed = editing = false; setBusy(false); update();
    }
    if (applied && getState().project?.path === context.path && getState().project?.mode === 'edit') {
      try { await onApplied({scene: context.current.scene, placementId: captured.placement_id??captured.placement_ids?.[0]??captured.requests[0].placement_id, projectPath: context.path}); }
      catch (error) { status.textContent = 'Decoration applied, but scene refresh failed: ' + error.message; onError(error); }
    }
  };
  discard.onclick = () => { if (discard.disabled) return; move.checked=rotate.checked=false;withdrawReview(); status.textContent = 'Decoration Review discarded; draft fields retained, Current scene restored and project unchanged.'; };
  update(); return {update,cancel,panel,getTransformDraft:()=>!pendingKind&&!busy()?transformDraft():null,setTransformDraft,editSelected:()=>{update();panel.open=true;return inspectDonors(true);},reviewRemoval:async()=>{
    update();panel.open=true;const selectedId=getContext()?.selectedId;
    if(await inspectDonors(true)!==true||held?.selectedId!==selectedId||getContext()?.selectedId!==selectedId)return;
    return removeReview.onclick();
  }};
}
