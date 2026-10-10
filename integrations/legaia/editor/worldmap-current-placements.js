import {placementDigest, decodeWorldPlacementSeeds, replayWorldPlacementAllocations,
  composeWorldPlacementTransforms, equalWorldPlacementBytes} from './worldmap-placement-replay.js';
import {currentWorldModelView, qualifyCurrentWorldModels} from './worldmap-current-models.js';

const fail = message => { throw Error(message); };
const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).sort().join(',') === [...keys].sort().join(',');
const canonical = value => Array.isArray(value) ? value.map(canonical) :
  value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value;
const same = (a, b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
const matrixMatches = (a, b) => Array.isArray(a) && Array.isArray(b) && a.length === 16 && b.length === 16 &&
  a.every((n, i) => Number.isFinite(n) && Math.abs(n - b[i]) <= 1e-12);
export function nativeWorldPlacementMatches(a, b, key = '') {
  if (key === 'source_to_world' || key === 'retail_source_to_world') return b === null ? a === null : matrixMatches(a, b);
  if (Array.isArray(b)) return Array.isArray(a) && a.length === b.length && b.every((v, i) => nativeWorldPlacementMatches(a[i], v));
  if (b && typeof b === 'object') return a && typeof a === 'object' && !Array.isArray(a) &&
    same(Object.keys(a).sort(), Object.keys(b).sort()) && Object.keys(b).every(k => nativeWorldPlacementMatches(a[k], b[k], k));
  return a === b;
}
function mapBytes(value) {
  if (typeof value !== 'string' || value.length !== 98304 || !/^[A-Za-z0-9+/]+$/.test(value))
    fail('Current World scene requires complete native MAP byte receipts.');
  return Uint8Array.from(atob(value), c => c.charCodeAt(0));
}
function seedMatches(entity, seed) {
  if (!seed) return false;
  return Object.entries(seed).every(([key, value]) => key === 'source_to_world' ? matrixMatches(entity[key], value) : same(entity[key], value));
}

// Proposed receipts enter only through the separate Current/Review-bound adapter.
export async function qualifyCurrentWorldPlacements(retail, current, options) {
  const scene = retail?.scene, meta = current?.placement_authoring, graph = current?.scene_graph;
  if (current?.representation !== 'current-source' || current.placement_layer !== 'current' || current.allocation_proposal !== null ||
      current.scene !== scene || current.project_source_key !== retail.project_source_key ||
      !exact(meta, ['schema_version', 'scene', 'source_key', 'source_record', 'source_map_sha256', 'current_map_sha256',
        'exported_map_sha256', 'retail_map_base64', 'current_map_base64', 'exported_map_base64', 'floor_lut', 'authored_records',
        'allocation_binding', 'authored_allocations', 'changed_source_entity_count', 'authored_entity_count',
        'read_only', 'project_changed', 'gameplay_verified']) ||
      meta.schema_version !== 'legaia.worldmap-placement-scene.v1' || meta.scene !== scene ||
      meta.source_key !== retail.project_source_key || meta.read_only !== true || meta.project_changed !== false || meta.gameplay_verified !== false ||
      !exact(meta.source_record, ['scene', 'source_disc_sha256', 'source_map_sha256', 'source_floor_lut_sha256']) ||
      meta.source_record.scene !== scene || meta.source_record.source_disc_sha256 !== retail.source_record.disc_sha256 ||
      meta.source_record.source_map_sha256 !== retail.source_record.map_sha256 || meta.source_map_sha256 !== retail.source_record.map_sha256 ||
      meta.source_record.source_floor_lut_sha256 !== retail.source_record.floor_lut_sha256 || !same(meta.floor_lut, retail.floor_height_lut) ||
      !Array.isArray(graph?.entities) || graph.entities.length > 512 || !Array.isArray(meta.authored_allocations) ||
      meta.authored_allocations.length > 511) fail('Current World placements lost their exact source identity or scope.');
  const raw = mapBytes(meta.retail_map_base64), currentBytes = mapBytes(meta.current_map_base64), exportedBytes = mapBytes(meta.exported_map_base64);
  const floorBytes = new Uint8Array(32), floorView = new DataView(floorBytes.buffer);
  if (!Array.isArray(meta.floor_lut) || meta.floor_lut.length !== 16 ||
      meta.floor_lut.some(n => !Number.isSafeInteger(n) || n < -32768 || n > 32767)) fail('Current World floor LUT is invalid.');
  meta.floor_lut.forEach((n, i) => floorView.setInt16(i * 2, n, true));
  if (await placementDigest(raw) !== meta.source_map_sha256 || await placementDigest(floorBytes) !== meta.source_record.source_floor_lut_sha256 ||
      await placementDigest(currentBytes) !== meta.current_map_sha256 || await placementDigest(exportedBytes) !== meta.exported_map_sha256 ||
      !equalWorldPlacementBytes(currentBytes, exportedBytes)) fail('Current World native byte layer hashes differ.');
  const replay = await replayWorldPlacementAllocations(raw, meta.floor_lut, scene, meta.allocation_binding, meta.source_record);
  const composed = await composeWorldPlacementTransforms(raw, replay.bytes, meta.floor_lut, scene, meta.authored_records);
  if (!equalWorldPlacementBytes(composed, currentBytes) || !nativeWorldPlacementMatches(replay.allocations, meta.authored_allocations) ||
      meta.authored_entity_count !== replay.allocations.length) fail('Current World allocation receipt differs from independent complete MAP replay.');
  const original = await decodeWorldPlacementSeeds(raw, meta.floor_lut, scene);
  const decoded = await decodeWorldPlacementSeeds(composed, meta.floor_lut, scene);
  const retailSeeds = new Map(original.placements.map(p => [p.entity_id, p]));
  const seeds = new Map(decoded.placements.map(p => [p.entity_id, p]));
  const originals = retail.scene_graph.entities, expected = [];
  let changed = 0;
  for (const entity of originals) {
    if (entity.placement_scope === 'source_ground') { expected.push(structuredClone(entity)); continue; }
    const before = retailSeeds.get(entity.entity_id), after = seeds.get(entity.entity_id);
    if (!seedMatches(entity, before) || !after) fail('Retail World graph differs from literal native seed ownership.');
    if (!matrixMatches(before.source_to_world, after.source_to_world)) changed++;
    const recordId = String(entity.object_record_index).padStart(4, '0');
    expected.push({...structuredClone(entity), retail_source_position: structuredClone(before.source_position),
      retail_source_to_world: [...before.source_to_world], source_position: after.source_position,
      source_to_world: after.source_to_world, source_rotation_psx: after.source_rotation_psx,
      authored_source_transform: {record_id: recordId, retail_record_sha256: before.source_record_sha256,
        exported_record_sha256: after.source_record_sha256, values: meta.authored_records[recordId]?.values ?? null}});
  }
  for (const allocation of replay.allocations) {
    const seed = seeds.get(allocation.native_seed.entity_id);
    if (!seedMatches(allocation.native_seed, seed)) fail('Current World allocation seed differs from composed native bytes.');
    expected.push({...seed, entity_id: `scene://${scene}/worldmap/authored-placements/${allocation.placement_id.split('/').pop()}`,
      native_entity_id: seed.entity_id, asset_id: `asset://${scene}/worldmap/models/${String(seed.model_pool_index).padStart(4, '0')}`,
      renderable: true, placement_scope: 'authored_spawn_seed', retail_source_position: null, retail_source_to_world: null,
      authored_placement: allocation});
  }
  if (changed !== meta.changed_source_entity_count || graph.entities.length !== expected.length)
    fail('Current World scene count or changed source coverage differs.');
  for (let i = 0; i < expected.length; i++) {
    const a = structuredClone(graph.entities[i]), b = structuredClone(expected[i]);
    for (const key of ['source_to_world', 'retail_source_to_world']) {
      if (b[key] !== undefined && b[key] !== null) {
        if (!matrixMatches(a[key], b[key])) fail('Current World scene transform differs from native coordinates.');
        a[key] = b[key];
      }
    }
    // Audit matrices are checked above against canonical replay, with exact integer fields.
    if (!nativeWorldPlacementMatches(a, b)) fail('Current World scene entity lost its original or authored native identity.');
  }
  const assets = new Map(graph.assets.map(a => [a.asset_id, a])), drawn = expected.reduce((count, e) => {
    const triangles = assets.get(e.asset_id)?.preview?.triangles;
    if (!Array.isArray(triangles)) fail('Current World seed has no qualified model asset.');
    return count + triangles.length;
  }, 0);
  const expectedCoverage = {...retail.scene_graph.coverage, candidate_count: retail.scene_graph.coverage.candidate_count + replay.allocations.length,
    resolved_count: expected.length - 1, rendered_count: expected.length - 1};
  const limitations = [...retail.scene_graph.limitations,
    'Authored decorations use native source seeds; collision, script behavior and live visibility remain unevaluated.'];
  if (drawn > 200000 || graph.metrics.entity_count !== expected.length || graph.metrics.drawn_triangle_count !== drawn ||
      !same(graph.coverage, expectedCoverage) || !same(graph.limitations, limitations)) fail('Current World scene coverage or metrics differ.');
  const modelAuthored = Object.entries(options.bindings ?? {}).some(([id, b]) =>
    id.startsWith(`asset://${scene}/worldmap/models/`) && b.asset_sha256 !== b.source_sha256);
  if (current.authored_geometry !== !!(modelAuthored || changed || replay.allocations.length)) fail('Current World authored layer claim differs.');
  // Qualify unchanged asset ownership and Current model/texture geometry with the
  // existing strict parser. Only independently checked placement data is detached.
  const normalized = structuredClone(current);
  for (const key of ['placement_layer', 'placement_authoring', 'allocation_proposal']) delete normalized[key];
  normalized.authored_geometry = modelAuthored;
  normalized.scene_graph.entities = structuredClone(originals);
  normalized.scene_graph.coverage = structuredClone(retail.scene_graph.coverage);
  normalized.scene_graph.limitations = structuredClone(retail.scene_graph.limitations);
  normalized.scene_graph.metrics.entity_count = originals.length;
  normalized.scene_graph.metrics.drawn_triangle_count = originals.reduce((n, e) => n + assets.get(e.asset_id).preview.triangles.length, 0);
  const qualified = options.sources ? await qualifyCurrentWorldModels(retail, normalized, options) :
    await currentWorldModelView(retail, normalized, options);
  return {assets: qualified.assets, entities: expected.map(entity => {
    const matrix = [];
    for (let row = 0; row < 4; row++) for (let col = 0; col < 4; col++) matrix.push(entity.source_to_world[col * 4 + row] * (row === 1 ? -1 : 1));
    return {...entity, geometry_key: entity.asset_id, model_to_scene: matrix,
      authored_source_position: entity.source_position, preview_layer: 'Current authored seeds'};
  })};
}

export async function qualifyProposedWorldPlacements(retail, current, proposed, review, options) {
  await qualifyCurrentWorldPlacements(retail, current, options);
  const before = current.placement_authoring, after = proposed?.placement_authoring;
  if (!review || proposed?.representation !== 'proposed-source' ||
      !same(proposed.allocation_proposal, {requests: review.requests, review_key: review.review_key}) ||
      review.source_key !== current.project_source_key || review.current_map_sha256 !== before.current_map_sha256 ||
      !after || after.current_map_sha256 !== before.current_map_sha256 ||
      after.current_map_base64 !== before.current_map_base64 || after.retail_map_base64 !== before.retail_map_base64 ||
      after.exported_map_sha256 !== review.proposed_map_sha256 || after.exported_map_base64 !== review.proposed_map_base64 ||
      !same(after.authored_records, before.authored_records) || !same(after.allocation_binding, review.binding) ||
      !same(review.before_binding, before.allocation_binding) ||
      !Array.isArray(review.binding?.operations) || review.binding.operations.length !== (before.allocation_binding?.operations.length ?? 0) + 1 ||
      !same(review.binding.operations.slice(0,-1), before.allocation_binding?.operations ?? []) ||
      !same(review.binding.operations.at(-1).requests, review.requests) ||
      !same(proposed.scene_graph?.assets, current.scene_graph.assets) ||
      !same(proposed.model_authoring, current.model_authoring) || !same(proposed.texture_authoring, current.texture_authoring))
    fail('Proposed World placements differ from the qualified Current scene and reviewed allocation.');
  const currentView = structuredClone(proposed);
  currentView.representation = 'current-source'; currentView.allocation_proposal = null;
  currentView.placement_authoring.current_map_sha256 = after.exported_map_sha256;
  currentView.placement_authoring.current_map_base64 = after.exported_map_base64;
  const view = await qualifyCurrentWorldPlacements(retail, currentView, options);
  return {...view, entities: view.entities.map(entity => ({...entity, preview_layer: 'Proposed authored seeds'}))};
}

export async function qualifyProposedWorldPlacementEdit(retail, current, proposed, review, options) {
  await qualifyCurrentWorldPlacements(retail,current,options);
  const before=current.placement_authoring,after=proposed?.placement_authoring;
  if (review?.schema_version !== 'legaia.worldmap-decoration-transform-review.v1' || proposed?.representation !== 'proposed-source' ||
      proposed.allocation_proposal !== null || !same(proposed.allocation_edit_proposal,{placement_id:review.placement_id,values:review.values,review_key:review.review_key}) ||
      review.source_key !== current.project_source_key || review.current_map_sha256 !== before.current_map_sha256 ||
      !same(review.before_binding,before.allocation_binding) || !after ||
      after.current_map_base64 !== before.current_map_base64 || after.current_map_sha256 !== before.current_map_sha256 ||
      after.exported_map_base64 !== review.proposed_map_base64 || after.exported_map_sha256 !== review.proposed_map_sha256 ||
      !same(after.authored_records,before.authored_records) || !same(after.allocation_binding,review.binding) ||
      !same(proposed.scene_graph?.assets,current.scene_graph.assets) || !same(proposed.model_authoring,current.model_authoring) ||
      !same(proposed.texture_authoring,current.texture_authoring)) fail('Proposed decoration transform differs from qualified Current and reviewed recipe.');
  const revised=structuredClone(review.before_binding);let matches=0;
  for(const op of revised.operations)for(const request of op.requests)if(request.placement_id===review.placement_id){request.values=structuredClone(review.values);matches++;}
  for(let i=0;i<revised.operations.length;i++)revised.operations[i].proposed_map_sha256=review.binding?.operations?.[i]?.proposed_map_sha256;
  if(matches!==1||!same(revised,review.binding))fail('Decoration transform changed another request or native identity.');
  const normalized=structuredClone(proposed);delete normalized.allocation_edit_proposal;
  normalized.representation='current-source';normalized.placement_authoring.current_map_base64=after.exported_map_base64;
  normalized.placement_authoring.current_map_sha256=after.exported_map_sha256;
  const view=await qualifyCurrentWorldPlacements(retail,normalized,options);
  return {...view,entities:view.entities.map(entity=>({...entity,preview_layer:'Proposed authored seeds'}))};
}

export async function qualifyProposedWorldPlacementRemoval(retail,current,proposed,review,options){
  await qualifyCurrentWorldPlacements(retail,current,options);
  const before=current.placement_authoring,after=proposed?.placement_authoring;
  if(review?.schema_version!=='legaia.worldmap-decoration-removal-review.v1'||proposed?.representation!=='proposed-source'||proposed.allocation_proposal!==null||
      !same(proposed.allocation_remove_proposal,{placement_id:review.placement_id,review_key:review.review_key})||review.source_key!==current.project_source_key||
      review.current_map_sha256!==before.current_map_sha256||!same(review.before_binding,before.allocation_binding)||!after||
      after.current_map_base64!==before.current_map_base64||after.current_map_sha256!==before.current_map_sha256||
      after.exported_map_base64!==review.proposed_map_base64||after.exported_map_sha256!==review.proposed_map_sha256||
      !same(after.authored_records,before.authored_records)||!same(after.allocation_binding,review.binding)||
      !same(after.authored_allocations,review.audit.remaining_allocations)||!same(proposed.scene_graph?.assets,current.scene_graph.assets)||
      !same(proposed.model_authoring,current.model_authoring)||!same(proposed.texture_authoring,current.texture_authoring))fail('Proposed removal differs from qualified Current and reviewed native receipt.');
  let expected=structuredClone(before.allocation_binding);
  const matches=expected?.operations.flatMap(op=>op.requests).filter(r=>r.placement_id===review.placement_id)??[];
  if(matches.length!==1)fail('Proposed removal has no unique retained Current owner.');
  const selected=matches[0];
  for(const op of expected.operations){
    for(const request of op.requests)if(request.placement_id!==selected.placement_id&&request.donor_cell===selected.target_cell)request.donor_cell=selected.donor_cell;
    op.requests=op.requests.filter(r=>r.placement_id!==selected.placement_id);
  }
  expected.operations=expected.operations.filter(op=>op.requests.length);
  if(!expected.operations.length)expected=null;
  else for(let i=0;i<expected.operations.length;i++)expected.operations[i].proposed_map_sha256=review.binding?.operations?.[i]?.proposed_map_sha256;
  if(!same(expected,review.binding))fail('Proposed removal changed unrelated requests or donor lineage.');
  const literal=mapBytes(before.current_map_base64),retailBytes=mapBytes(before.retail_map_base64),at=selected.record_index*32,cellAt=0x8000+selected.target_cell*2;
  literal.set(retailBytes.subarray(at,at+32),at);literal.set(retailBytes.subarray(cellAt,cellAt+2),cellAt);
  if(!equalWorldPlacementBytes(literal,mapBytes(after.exported_map_base64)))fail('Proposed removal changed surviving native bytes.');
  const normalized=structuredClone(proposed);delete normalized.allocation_remove_proposal;normalized.representation='current-source';
  normalized.placement_authoring.current_map_base64=after.exported_map_base64;normalized.placement_authoring.current_map_sha256=after.exported_map_sha256;
  const view=await qualifyCurrentWorldPlacements(retail,normalized,options);
  return {...view,entities:view.entities.map(entity=>({...entity,preview_layer:'Proposed authored seeds'}))};
}
