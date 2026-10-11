// Independent native MAP replay. Spawn seeds do not evaluate scripts or visibility.
const fail = message => { throw Error(message); };
const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).sort().join(',') === [...keys].sort().join(',');
const integer = (value, low, high) => Number.isSafeInteger(value) && value >= low && value <= high;
const hash = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
const uuid = value => typeof value === 'string' && /^placement:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(value);
export const placementDigest = async bytes => Array.from(new Uint8Array(
  await crypto.subtle.digest('SHA-256', bytes)), n => n.toString(16).padStart(2, '0')).join('');
const sameBytes = (a, b) => a.length === b.length && a.every((n, i) => n === b[i]);
const canonical = value => Array.isArray(value) ? value.map(canonical) :
  value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value;
const same = (a, b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
const values = value => exact(value, ['offset', 'yaw_units']) && exact(value.offset, ['x', 'y', 'z']) &&
  Object.values(value.offset).every(n => integer(n, -32768, 32767)) && integer(value.yaw_units, 0, 4095);
function inputs(data, floor, scene) {
  if (!(data instanceof Uint8Array) || data.length !== 0x12000 || !['map01', 'map02', 'map03'].includes(scene) ||
      !Array.isArray(floor) || floor.length !== 16 || floor.some(n => !integer(n, -32768, 32767)))
    fail('World placement replay requires a complete MAP and sixteen signed floor heights.');
  return new DataView(data.buffer, data.byteOffset, data.byteLength);
}

export async function decodeWorldPlacementSeeds(data, floor, scene) {
  const view = inputs(data, floor, scene), placements = [], unresolved = [], excluded = [], recordHashes = new Map();
  for (let cell = 0; cell < 16384; cell++) {
    const word = view.getUint16(0x8000 + cell * 2, true), record = word & 511, at = record * 32;
    const model = view.getUint16(at + 16, true), flags = view.getUint16(at + 18, true), placed = !!(flags & 4);
    const decoration = !!(word & 0x1000) && record !== 0 && model !== 0 && !!(flags & 2) && !placed;
    if (!placed && !decoration) {
      if (model) excluded.push({cell_index: cell, object_record_index: record, model_pool_index: model,
        reason: 'Source walk decoration/placed gates are not satisfied'});
      continue;
    }
    const col = cell % 128, row = Math.floor(cell / 128), tier = data[0x4000 + cell] & 15;
    const position = {x: col * 128 + view.getInt16(at, true) + 64,
      y: -floor[tier] + view.getInt16(at + 2, true), z: row * 128 - view.getInt16(at + 4, true) + 64};
    const rotation = {x: view.getUint16(at + 8, true), y: view.getUint16(at + 10, true), z: view.getUint16(at + 12, true)};
    let ac = col + view.getInt8(at + 6), ar = row + view.getInt8(at + 7);
    if (!recordHashes.has(record)) recordHashes.set(record, await placementDigest(data.slice(at, at + 32)));
    const seed = {entity_id: `scene://${scene}/worldmap/placements/${cell.toString(16).padStart(4, '0')}`,
      source_cell: cell, object_record_index: record, model_pool_index: model, source_record_sha256: recordHashes.get(record),
      source_cell_sha256: await placementDigest(data.slice(0x8000 + cell * 2, 0x8002 + cell * 2)),
      source_position: position, source_rotation_psx: rotation, source_floor_tier: tier, source_cell_flags: word,
      source_record_flags: flags, source_layer: placed ? 'placed' : 'decoration', source_anchor: {col: ac, row: ar},
      placement_scope: 'source_spawn_seed', runtime_visibility: 'not_evaluated', runtime_resting_position: 'unknown'};
    const reason = placed && (ac < 0 || ac >= 128 || ar < 0 || ar >= 128) ? 'Source placed footprint anchor is outside the MAP grid' :
      placed && [1, 2, 3].includes(record) ? 'Source placed actor record uses a non-kingdom actor model pool' :
      rotation.x || rotation.z ? 'Source X/Z tilt has no qualified sparse kingdom transform' : null;
    if (reason) { unresolved.push({...seed, reason}); continue; }
    if (decoration) { ac = Math.min(127, Math.max(0, ac)); ar = Math.min(127, Math.max(0, ar)); }
    const anchorWord = view.getUint16(0x8000 + (ar * 128 + ac) * 2, true);
    seed.source_anchor = {col: ac, row: ar, cell_flags: anchorWord};
    seed.source_bind_owner = anchorWord & 0x400 ? 'init_bind' : 'subarea_unbound';
    const angle = (rotation.y & 4095) * (Math.PI * 2) / 4096, c = Math.cos(angle), s = Math.sin(angle);
    seed.source_to_world = [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, position.x, position.y, position.z, 1];
    placements.push(seed);
  }
  return {placements, unresolved, coverage: {candidate_count: placements.length + unresolved.length,
    resolved_count: placements.length, unresolved_count: unresolved.length, excluded_count: excluded.length,
    unresolved, excluded, inspected_cell_count: 16384}};
}

export async function worldPlacementInventory(data, floor, scene) {
  const view = inputs(data, floor, scene), decoded = await decodeWorldPlacementSeeds(data, floor, scene);
  const used = new Set(), anchors = new Set(), free = [], targets = [];
  for (let cell = 0; cell < 16384; cell++) used.add(view.getUint16(0x8000 + cell * 2, true) & 511);
  for (const p of [...decoded.placements, ...decoded.unresolved]) {
    const {col, row} = p.source_anchor;
    if (col >= 0 && col < 128 && row >= 0 && row < 128) anchors.add(row * 128 + col);
  }
  for (let record = 4; record < 512; record++)
    if (!used.has(record) && data.slice(record * 32, record * 32 + 32).every(n => n === 0)) free.push(record);
  for (let cell = 0; cell < 16384; cell++) {
    const word = view.getUint16(0x8000 + cell * 2, true), at = (word & 511) * 32;
    if (word & 0x1000 && view.getUint16(at + 16, true) === 0 && !(view.getUint16(at + 18, true) & 4) && !anchors.has(cell)) targets.push(cell);
  }
  return {donors: decoded.placements.filter(p => p.source_layer === 'decoration'), free_record_indices: free,
    target_cells: targets, current_placements: decoded.placements, decoded};
}

export async function allocateWorldPlacements(data, floor, scene, requests) {
  const inventory = await worldPlacementInventory(data, floor, scene);
  if (!Array.isArray(requests) || !integer(requests.length, 1, 32) || inventory.current_placements.length + requests.length > 511)
    fail('World placement allocation exceeds its clone or scene budget.');
  const donors = new Map(inventory.donors.map(p => [p.source_cell, p])), free = new Set(inventory.free_record_indices);
  const targets = new Set(inventory.target_cells), ids = new Set(), records = new Set(), cells = new Set();
  const result = data.slice(), source = inputs(data, floor, scene), view = inputs(result, floor, scene), allocations = [];
  for (const request of requests) {
    if (!exact(request, ['placement_id', 'donor_cell', 'target_cell', 'record_index', 'values',...(Object.hasOwn(request??{},'model_pool_index')?['model_pool_index']:[])]) ||
        (Object.hasOwn(request,'model_pool_index')&&!integer(request.model_pool_index,1,511)) ||
        !uuid(request.placement_id) || ids.has(request.placement_id) || !values(request.values) ||
        !integer(request.donor_cell, 0, 16383) || !integer(request.target_cell, 0, 16383) || !integer(request.record_index, 4, 511) ||
        !donors.has(request.donor_cell) || !targets.has(request.target_cell) || cells.has(request.target_cell) ||
        !free.has(request.record_index) || records.has(request.record_index)) fail('World placement clone ownership or values differ.');
    const donor = donors.get(request.donor_cell), donorAt = donor.object_record_index * 32, at = request.record_index * 32;
    const cellAt = 0x8000 + request.target_cell * 2, cellWord = source.getUint16(cellAt, true), previousAt = (cellWord & 511) * 32;
    result.set(data.slice(donorAt, donorAt + 32), at);
    result.set(data.slice(previousAt + 20, previousAt + 24), at + 20);
    for (const [i, axis] of ['x', 'y', 'z'].entries()) view.setInt16(at + i * 2, request.values.offset[axis], true);
    view.setUint16(at + 10, (source.getUint16(donorAt + 10, true) & 0xf000) | request.values.yaw_units, true);
    if(Object.hasOwn(request,'model_pool_index'))view.setUint16(at+16,request.model_pool_index,true);
    view.setUint16(cellAt, (cellWord & ~511) | request.record_index, true);
    ids.add(request.placement_id); records.add(request.record_index); cells.add(request.target_cell);
    allocations.push({placement_id: request.placement_id, donor_cell: request.donor_cell, target_cell: request.target_cell,
      record_index: request.record_index, donor_record_index: donor.object_record_index,
      donor_record_sha256: await placementDigest(data.slice(donorAt, donorAt + 32)),
      previous_cell_sha256: await placementDigest(data.slice(cellAt, cellAt + 2)),
      allocated_record_sha256: await placementDigest(result.slice(at, at + 32)), model_pool_index: view.getUint16(at+16,true),
      preserved_terrain_hex: Array.from(result.slice(at + 20, at + 24), n => n.toString(16).padStart(2, '0')).join('')});
  }
  const decoded = await decodeWorldPlacementSeeds(result, floor, scene), byCell = new Map(decoded.placements.map(p => [p.source_cell, p]));
  if (byCell.size !== inventory.current_placements.length + cells.size ||
      inventory.current_placements.some(p => !same(p, byCell.get(p.source_cell))) ||
      !same(decoded.unresolved, inventory.decoded.unresolved) || !same(decoded.coverage.excluded, inventory.decoded.coverage.excluded))
    fail('World placement replay changed original or unresolved seeds.');
  const changed = [];
  for (let i = 0; i < data.length; i++) if (data[i] !== result[i]) {
    if (!(i < 0x4000 && records.has(Math.floor(i / 32))) && !(i >= 0x8000 && cells.has(Math.floor((i - 0x8000) / 2))))
      fail('World allocation altered unrelated MAP bytes.');
    changed.push({byte_offset: i, before_byte: data[i], after_byte: result[i]});
  }
  for (const allocation of allocations) {
    if (!byCell.has(allocation.target_cell)) fail('Allocated World seed is missing.');
    allocation.native_seed = byCell.get(allocation.target_cell);
  }
  return {bytes: result, audit: {source_sha256: await placementDigest(data), proposed_sha256: await placementDigest(result),
    byte_length: result.length, allocations, changed_bytes: changed, original_placement_count: inventory.current_placements.length,
    proposed_placement_count: byCell.size, scope: 'walk-decoration-cell-allocation', gameplay_verified: false}};
}

export async function replayWorldPlacementAllocations(raw, floor, scene, binding, provenance) {
  inputs(raw, floor, scene);
  if (binding === null) return {bytes: raw.slice(), allocations: []};
  if (!exact(binding, ['schema_version', 'scene', 'source_disc_sha256', 'source_map_sha256', 'source_floor_lut_sha256', 'operations']) ||
      !['legaia.worldmap-placement-allocation-ledger.v1','legaia.worldmap-placement-allocation-ledger.v2'].includes(binding.schema_version) || binding.scene !== scene ||
      !['source_disc_sha256', 'source_map_sha256', 'source_floor_lut_sha256'].every(k => hash(binding[k]) && binding[k] === provenance?.[k]) ||
      await placementDigest(raw) !== binding.source_map_sha256 || !Array.isArray(binding.operations) || !integer(binding.operations.length, 1, 32))
    fail('World placement lineage lacks exact source identity.');
  const floorBytes = new Uint8Array(32), floorView = new DataView(floorBytes.buffer);
  floor.forEach((n, i) => floorView.setInt16(i * 2, n, true));
  if (await placementDigest(floorBytes) !== binding.source_floor_lut_sha256) fail('World placement floor heights changed.');
  let bytes = raw.slice(); const allocations = [], ids = new Set();
  for (const operation of binding.operations) {
    if (!exact(operation, ['requests', 'proposed_map_sha256']) || !hash(operation.proposed_map_sha256)) fail('World allocation operation differs.');
    if(binding.schema_version==='legaia.worldmap-placement-allocation-ledger.v1'&&operation.requests?.some(r=>Object.hasOwn(r??{},'model_pool_index')))
      fail('World model overrides require a version-two allocation ledger.');
    const result = await allocateWorldPlacements(bytes, floor, scene, operation.requests);
    if (result.audit.proposed_sha256 !== operation.proposed_map_sha256) fail('World allocation native replay hash differs.');
    for (const allocation of result.audit.allocations) {
      if (ids.has(allocation.placement_id) || ids.size >= 511) fail('World authored identity is repeated or unbounded.');
      ids.add(allocation.placement_id); allocations.push(allocation);
    }
    bytes = result.bytes;
  }
  return {bytes, allocations};
}

export async function composeWorldPlacementTransforms(raw, allocated, floor, scene, entries) {
  inputs(raw, floor, scene); inputs(allocated, floor, scene);
  if (!entries || typeof entries !== 'object' || Array.isArray(entries) || Object.keys(entries).length > 512)
    fail('World source transforms require bounded record entries.');
  const decoded = await decodeWorldPlacementSeeds(raw, floor, scene), view = inputs(raw, floor, scene), transformed = raw.slice();
  const output = inputs(transformed, floor, scene), qualified = new Map(), references = new Map();
  for (const p of decoded.placements) qualified.set(p.object_record_index, (qualified.get(p.object_record_index) ?? 0) + 1);
  for (let cell = 0; cell < 16384; cell++) { const record = view.getUint16(0x8000 + cell * 2, true) & 511; references.set(record, (references.get(record) ?? 0) + 1); }
  for (const [key, entry] of Object.entries(entries)) {
    const record = Number(key), at = record * 32;
    if (!/^\d{4}$/.test(key) || !integer(record, 0, 511) || !exact(entry, ['values', 'source_record_sha256', 'shared_record']) ||
        !values(entry.values) || typeof entry.shared_record !== 'boolean' || !hash(entry.source_record_sha256) ||
        !qualified.has(record) || qualified.get(record) !== references.get(record) || references.get(record) > 1 && !entry.shared_record ||
        await placementDigest(raw.slice(at, at + 32)) !== entry.source_record_sha256) fail('World source transform owner is unavailable or changed.');
    ['x', 'y', 'z'].forEach((axis, i) => output.setInt16(at + i * 2, entry.values.offset[axis], true));
    output.setUint16(at + 10, (view.getUint16(at + 10, true) & 0xf000) | entry.values.yaw_units, true);
  }
  const result = allocated.slice();
  for (let i = 0; i < raw.length; i++) if (raw[i] !== transformed[i]) {
    if (allocated[i] !== raw[i]) fail('World allocation conflicts with a source transform.');
    result[i] = transformed[i];
  }
  return result;
}

export function equalWorldPlacementBytes(a, b) { return sameBytes(a, b); }
