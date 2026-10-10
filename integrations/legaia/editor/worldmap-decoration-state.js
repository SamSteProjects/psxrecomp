import {worldPlacementInventory, allocateWorldPlacements, equalWorldPlacementBytes,
  replayWorldPlacementAllocations, composeWorldPlacementTransforms} from './worldmap-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
const fail = message => { throw Error(message); };
const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).sort().join(',') === [...keys].sort().join(',');
const hash = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
const same = nativeWorldPlacementMatches;
const keys = ['schema_version','project_path','scene','source_key','source_record','current_map_sha256','current_map_base64',
  'floor_lut','authored_allocations','binding','donors','free_record_indices','target_cells','current_placements',
  'read_only','project_changed','gameplay_verified','limitations'];
const decode = text => {
  if (typeof text !== 'string' || text.length !== 98304 || !/^[A-Za-z0-9+/]+$/.test(text)) fail('Decoration source requires complete MAP bytes.');
  return Uint8Array.from(atob(text), c => c.charCodeAt(0));
};
export async function qualifyWorldDecorationSource(value, current, path) {
  const meta = current?.placement_authoring;
  if (!meta || current.representation !== 'current-source' || !exact(value, keys) ||
      value.schema_version !== 'legaia.worldmap-placement-allocation-source.v2' || value.project_path !== path ||
      value.scene !== current.scene || value.source_key !== current.project_source_key ||
      value.read_only !== true || value.project_changed !== false || value.gameplay_verified !== false ||
      !same(value.source_record, meta.source_record) || value.current_map_sha256 !== meta.current_map_sha256 ||
      value.current_map_base64 !== meta.current_map_base64 || !same(value.floor_lut, meta.floor_lut) ||
      !same(value.binding, meta.allocation_binding) || !same(value.authored_allocations, meta.authored_allocations) ||
      !Array.isArray(value.limitations) || value.limitations.some(v => typeof v !== 'string' || v.length > 4096))
    fail('Decoration source differs from the qualified Current scene.');
  const bytes = decode(value.current_map_base64), inventory = await worldPlacementInventory(bytes, value.floor_lut, value.scene);
  for (const key of ['donors','free_record_indices','target_cells','current_placements'])
    if (!same(value[key], inventory[key])) fail('Decoration donor, target or unused-record inventory differs from native MAP replay.');
  return {metadata: structuredClone(value), bytes, inventory, retailBytes: decode(meta.retail_map_base64),
    authoredRecords: structuredClone(meta.authored_records)};
}
export function worldDecorationDraft(source, donorCell, targetCell, values, newUuid = () => crypto.randomUUID(), placementId = null) {
  if (!source?.inventory.donors.some(p => p.source_cell === donorCell) || !source.inventory.target_cells.includes(targetCell) ||
      !source.inventory.free_record_indices.length) fail('Choose an available decoration donor and model-free target cell.');
  return {placement_id: placementId ?? `placement://authored/${newUuid()}`, donor_cell: donorCell, target_cell: targetCell,
    record_index: source.inventory.free_record_indices[0], values: structuredClone(values)};
}
export function worldDecorationDonorValues(source, donorCell) {
  const donor = source?.inventory.donors.find(p => p.source_cell === donorCell);
  if (!donor) fail('Choose a qualified native decoration donor.');
  const view = new DataView(source.bytes.buffer, source.bytes.byteOffset, source.bytes.byteLength), at = donor.object_record_index * 32;
  return {offset: {x: view.getInt16(at, true), y: view.getInt16(at + 2, true), z: view.getInt16(at + 4, true)},
    yaw_units: view.getUint16(at + 10, true) & 4095};
}
export async function qualifyWorldDecorationReview(value, source, requests) {
  const before = source?.metadata;
  if (!before || !exact(value, ['schema_version','project_path','scene','source_key','source_record','requests','current_map_sha256',
      'proposed_map_sha256','proposed_map_base64','audit','binding','before_binding','read_only','project_changed','gameplay_verified','build_ready','review_key']) ||
      value.schema_version !== 'legaia.worldmap-placement-allocation-review.v2' || value.project_path !== before.project_path ||
      value.scene !== before.scene || value.source_key !== before.source_key || !same(value.source_record, before.source_record) ||
      !same(value.requests, requests) || value.current_map_sha256 !== before.current_map_sha256 ||
      value.read_only !== true || value.project_changed !== false || value.gameplay_verified !== false || value.build_ready !== false ||
      !hash(value.review_key) || !same(value.before_binding, before.binding)) fail('Decoration Review lost its source, draft or read-only scope.');
  const allocated = await allocateWorldPlacements(source.bytes, before.floor_lut, before.scene, requests);
  if (value.proposed_map_sha256 !== allocated.audit.proposed_sha256 || !same(value.audit, allocated.audit) ||
      !equalWorldPlacementBytes(decode(value.proposed_map_base64), allocated.bytes)) fail('Decoration Review differs from complete independent allocation replay.');
  const binding = value.binding, prior = before.binding;
  const provenance = {...before.source_record, schema_version: 'legaia.worldmap-placement-allocation-ledger.v1'};
  if (!exact(binding, [...Object.keys(provenance), 'operations']) ||
      Object.entries(provenance).some(([k,v]) => binding[k] !== v) || !Array.isArray(binding.operations) ||
      binding.operations.length !== (prior?.operations.length ?? 0) + 1 || binding.operations.length > 32 ||
      !same(binding.operations.slice(0,-1), prior?.operations ?? []) ||
      !exact(binding.operations.at(-1), ['requests','proposed_map_sha256']) ||
      !same(binding.operations.at(-1).requests, requests) || !hash(binding.operations.at(-1).proposed_map_sha256))
    fail('Decoration Review changed existing retained allocation lineage.');
  const canonical = await replayWorldPlacementAllocations(source.retailBytes, before.floor_lut, before.scene, binding, before.source_record);
  const composed = await composeWorldPlacementTransforms(source.retailBytes, canonical.bytes, before.floor_lut, before.scene, source.authoredRecords);
  if (!equalWorldPlacementBytes(composed, allocated.bytes)) fail('Decoration Review canonical lineage conflicts with original transforms.');
  return structuredClone(value);
}
