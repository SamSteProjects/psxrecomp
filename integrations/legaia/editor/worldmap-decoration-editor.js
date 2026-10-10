import {qualifyWorldDecorationSource, qualifyWorldDecorationReview, worldDecorationDraft,
  worldDecorationDonorValues} from './worldmap-decoration-state.js';
import {validValues} from './worldmap-placement-state.js';
const node = (tag, text) => { const element = document.createElement(tag); if (text) element.textContent = text; return element; };

export function mountWorldDecorationEditor({host, getContext, getState, busy, setBusy, api, onPreview, onDiscard, onApplied, onError}) {
  const panel = node('details'), summary = node('summary', 'Create World Decoration'), status = node('p');
  panel.dataset.worldDecorationEditor = ''; status.setAttribute('role', 'status');
  const inspect = node('button', 'Inspect decoration donors'), reviewButton = node('button', 'Review decoration'),
    preview = node('button', 'Preview reviewed decoration'), apply = node('button', 'Apply reviewed decoration'), discard = node('button', 'Discard decoration');
  const actions = node('div'); actions.className = 'dialog-actions'; actions.style.flexWrap = 'wrap';
  for (const button of [inspect, reviewButton, preview, apply, discard]) { button.type = 'button'; actions.append(button); }
  const fields = node('div'); Object.assign(fields.style, {display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: '8px'});
  const donor = node('select'), target = node('input'), yaw = node('input'), offsets = {};
  const addField = (label, input) => {
    const wrapper = node('label', label); input.setAttribute('aria-label', label);
    Object.assign(input.style, {display: 'block', width: '100%', maxWidth: '100%', boxSizing: 'border-box'});
    wrapper.append(input); fields.append(wrapper);
  };
  addField('World decoration donor', donor); target.type = 'number'; target.min = '0'; target.max = '16383'; target.step = '1'; addField('World decoration target cell', target);
  for (const axis of ['x','y','z']) { const input = node('input'); input.type = 'number'; input.min = '-32768'; input.max = '32767'; input.step = '1'; offsets[axis] = input; addField('World decoration offset ' + axis.toUpperCase(), input); }
  yaw.type = 'number'; yaw.min = '0'; yaw.max = '4095'; yaw.step = '1'; addField('World decoration yaw units', yaw);
  const evidence = node('pre'); evidence.className = 'diagnostic-detail';
  Object.assign(evidence.style, {whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', maxHeight: '220px', overflow: 'auto'});
  panel.append(summary, node('p', 'Create a walk decoration from a drawable Current donor. Choose a native target cell and signed cell offsets; the preview shows the resulting native seed coordinates. Review and preview leave the project unchanged. Apply creates one authored placement through shared Undo/Redo.'), fields, actions, status, evidence); host.append(panel);
  let source = null, held = null, review = null, placementId = null, displayed = false, controller = null, pendingKind = null, generation = 0;
  const contextMatches = context => {
    const now = getContext(); return !!now && !!context && now.path === context.path && now.key === context.key &&
      now.current === context.current && now.retail === context.retail;
  };
  const sourceReady = () => !!source && contextMatches(held);
  const fieldValues = () => ({offset: Object.fromEntries(['x','y','z'].map(axis => [axis, offsets[axis].value === '' ? NaN : Number(offsets[axis].value)])),
    yaw_units: yaw.value === '' ? NaN : Number(yaw.value)});
  function draft() {
    const values = fieldValues(); if (!validValues(values) || target.value === '' || donor.value === '') throw Error('Enter signed integer offsets, yaw 0–4095 and an available target cell.');
    return worldDecorationDraft(source, Number(donor.value), Number(target.value), values, undefined, placementId);
  }
  function withdrawReview() {
    review = null; if (displayed) { displayed = false; onDiscard(); }
    evidence.textContent = ''; update();
  }
  function change() { withdrawReview(); status.textContent = sourceReady() ? 'Draft changed. Review the current donor, target and offsets again.' : 'Inspect Current decoration donors first.'; }
  function donorValues() {
    if (!sourceReady() || donor.value === '') return;
    const value = worldDecorationDonorValues(source, Number(donor.value));
    for (const axis of ['x','y','z']) offsets[axis].value = String(value.offset[axis]); yaw.value = String(value.yaw_units);
    const cell = Number(donor.value), col = cell % 128, row = Math.floor(cell / 128);
    const closest = source.inventory.target_cells.reduce((best, next) => {
      const distance = n => Math.abs(n % 128 - col) + Math.abs(Math.floor(n / 128) - row);
      return best === null || distance(next) < distance(best) ? next : best;
    }, null);
    target.value = closest === null ? '' : String(closest); change();
  }
  donor.onchange = donorValues; for (const input of [target, yaw, ...Object.values(offsets)]) input.oninput = change;
  function cancel() {
    generation++; controller?.abort(); source = held = review = placementId = null; displayed = false;
    donor.replaceChildren(); evidence.textContent = ''; status.textContent = 'Switch to a qualified Current scene and inspect decoration donors.';
    if (pendingKind !== 'apply') { controller = null; if (pendingKind) setBusy(false); pendingKind = null; }
    update();
  }
  function update() {
    if (source && !contextMatches(held) && pendingKind !== 'apply') { cancel(); return; }
    const locked = !!pendingKind || busy(), available = !!getContext();
    inspect.disabled = locked || !available;
    for (const field of [donor, target, yaw, ...Object.values(offsets)]) field.disabled = locked || !sourceReady();
    let validDraft = false; if (sourceReady()) { try { draft(); validDraft = true; } catch {} }
    reviewButton.disabled = locked || !validDraft;
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
    try { await work(context, request.signal, valid); }
    catch (error) { if (error.name !== 'AbortError' && valid()) { status.textContent = error.message; onError(error); } }
    finally { if (controller === request) { controller = null; pendingKind = null; setBusy(false); update(); } }
  }
  inspect.onclick = () => {
    if (inspect.disabled) return; withdrawReview();
    return run('source', async (context, signal, valid) => {
      status.textContent = 'Checking complete Current native donor and target inventory…';
      const value = await read('/api/worldmap-placement-allocation-source', {scene: context.current.scene, source_key: context.key}, signal);
      const qualified = await qualifyWorldDecorationSource(value, context.current, context.path); if (!valid()) return;
      source = qualified; held = context; placementId = `placement://authored/${crypto.randomUUID()}`; donor.replaceChildren();
      const assets = new Set(context.current.scene_graph.assets.map(a => a.asset_id));
      for (const seed of source.inventory.donors) if (assets.has(`asset://${value.scene}/worldmap/models/${String(seed.model_pool_index).padStart(4,'0')}`)) {
        const option = node('option', `Cell ${seed.source_cell} · model ${seed.model_pool_index} · record ${seed.object_record_index}`); option.value = String(seed.source_cell); donor.append(option);
      }
      const selected = context.current.scene_graph.entities.find(e => e.entity_id === context.selectedId);
      if (selected && [...donor.options].some(o => o.value === String(selected.source_cell))) donor.value = String(selected.source_cell);
      donorValues(); status.textContent = `${donor.options.length} drawable donors · ${value.target_cells.length} available target cells · ${value.free_record_indices.length} unused native records. Draft identity ${placementId}.`;
    });
  };
  reviewButton.onclick = () => {
    if (reviewButton.disabled) return; withdrawReview();
    return run('review', async (context, signal, valid) => {
      const requests = [draft()]; status.textContent = 'Replaying complete proposed MAP allocation and retained lineage…';
      const value = await read('/api/worldmap-placement-allocation-review', {scene: context.current.scene, source_key: context.key, requests}, signal);
      const qualified = await qualifyWorldDecorationReview(value, source, requests); if (!valid()) return;
      review = qualified; const allocation = review.audit.allocations[0];
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
      displayed = true; status.textContent = 'Proposed decoration displayed; project unchanged. Apply keeps this placement as one shared history command.';
    });
  };
  apply.onclick = async () => {
    if (apply.disabled) return;
    const context = held, captured = review, request = new AbortController(); let applied = false;
    // The shared API owns the global busy lock; taking it here would refuse
    // our own command before it reaches the server.
    controller = request; pendingKind = 'apply'; update(); status.textContent = 'Applying the exact reviewed native decoration…';
    try { applied = await api('/api/command', {type: 'allocate_worldmap_placements', scene: context.current.scene,
      source_key: context.key, requests: captured.requests, review_key: captured.review_key}) === true;
      if (!applied) throw Error('Decoration Apply failed. Inspect fresh Current sources before retrying.');
    } catch (error) { status.textContent = error.message; onError(error); }
    finally {
      if (!applied && displayed) onDiscard();
      controller = null; pendingKind = null; source = held = review = placementId = null; displayed = false; setBusy(false); update();
    }
    if (applied && getState().project?.path === context.path && getState().project?.mode === 'edit') {
      try { await onApplied({scene: context.current.scene, placementId: captured.requests[0].placement_id, projectPath: context.path}); }
      catch (error) { status.textContent = 'Decoration applied, but scene refresh failed: ' + error.message; onError(error); }
    }
  };
  discard.onclick = () => { if (discard.disabled) return; withdrawReview(); status.textContent = 'Decoration Review discarded; draft fields retained, Current scene restored and project unchanged.'; };
  update(); return {update, cancel, panel};
}
