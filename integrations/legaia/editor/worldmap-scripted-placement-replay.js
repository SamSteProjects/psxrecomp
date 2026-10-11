// Independent native init-anchor/bind replay. Scripts and visibility are not evaluated.
import {placementDigest as digest, worldPlacementInventory, decodeWorldPlacementSeeds} from './worldmap-placement-replay.js';
const fail = message => {throw Error(message);};
const exact = (v, keys) => v && typeof v === 'object' && !Array.isArray(v) &&
  Object.keys(v).sort().join(',') === [...keys].sort().join(',');
const integer = (v, lo, hi) => Number.isSafeInteger(v) && v >= lo && v <= hi;
const hash = v => typeof v === 'string' && /^[0-9a-f]{64}$/.test(v);
const uuid = v => typeof v === 'string' && /^placement:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(v);
const hex = bytes => Array.from(bytes, n => n.toString(16).padStart(2, '0')).join('');
const view = bytes => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
function tables(block) {
  if (!(block instanceof Uint8Array) || block.length !== 8192) fail('Bind replay requires a complete native table block.');
  const v = view(block), result = [], spans = [];
  for (let kind = 0; kind < 4; kind++) {
    const at = v.getInt16(kind * 4 + 2, true), count = v.getInt16(kind * 4 + 4, true), stride = kind === 3 ? 8 : 4, end = at + count * stride;
    if (at < 0 || count < 0 || count && at < 18 || end > block.length ||
        count && spans.some(([lo, hi]) => at < hi && lo < end)) fail('Native bind table bounds or owners differ.');
    if (count) spans.push([at, end]);
    result.push({at, rows: Array.from({length: count}, (_, i) => block.slice(at + i * stride, at + (i + 1) * stride))});
  }
  return {tables: result, spans};
}
export function worldMapTriggerTables(block) {return tables(block);}
function layout(man) {
  if (!(man instanceof Uint8Array) || !integer(man.length, 43, 4194304)) fail('Bind replay needs a bounded MAN.');
  const v = view(man), counts = [0, 1, 2].map(i => v.getInt16(34 + i * 2, true)), total = counts.reduce((a, b) => a + b, 0), base = 43 + 3 * total;
  if (counts.some(n => n < 0) || total > 8192 || base > man.length) fail('MAN record ownership exceeds its budget.');
  const u24 = at => {if (!integer(at, 0, man.length - 3)) fail('MAN offset is truncated.'); return man[at] + man[at + 1] * 256 + man[at + 2] * 65536;};
  const starts = Array.from({length: total}, (_, i) => base + u24(43 + i * 3));
  if (starts.some(at => at >= man.length)) fail('MAN record crosses its source.');
  const sections = []; let cursor = base + u24(40);
  for (let i = 0; i < 6; i++) {const end = cursor + 3 + u24(cursor); if (end > man.length) fail('MAN section crosses its source.'); sections.push([cursor, end]); cursor = end;}
  return {starts, counts, sections};
}
export function worldManRecordSpans(man) {
  const l=layout(man);let flat=0;const rows=[];
  for(let partition=0;partition<3;partition++)for(let index=0;index<l.counts[partition];index++){
    const at=l.starts[flat++],end=Math.min(man.length,...l.starts.filter(n=>n>at),...l.sections.map(s=>s[0]).filter(n=>n>at));
    if(l.starts.filter(n=>n===at).length!==1||!integer(end-at,1,65536)||l.sections.some(([lo,hi])=>at<hi&&lo<end))fail('MAN record spans have ambiguous native owners.');
    rows.push({partition,index,at,length:end-at});
  }
  return rows;
}
async function header(man, l, flat) {
  if (!integer(flat, 0, l.starts.length - 1)) fail('Bind has an invalid flat MAN index.');
  const at = l.starts[flat], end = Math.min(man.length, ...l.starts.filter(n => n > at), ...l.sections.map(s => s[0]).filter(n => n > at));
  if (l.starts.filter(n => n === at).length !== 1 || !integer(end - at, 1, 65536) || l.sections.some(([lo, hi]) => at < hi && lo < end)) fail('MAN bind record has ambiguous ownership.');
  if (flat >= l.counts[0]) fail('Scripted donor requires a partition-zero MAN header.');
  const length = 2 + 2 * man[at]; if (at + length > end) fail('Scripted donor header crosses its record.');
  return {index: flat, sha256: await digest(man.slice(at, end)), selector: man[at + length - 1]};
}
function lookup(primary, fallback, x, z) {
  for (const [name, t] of [['primary', primary], ['fallback', fallback]])
    for (let i = 0; i < t.rows.length; i++) if (t.rows[i][0] === x && t.rows[i][1] === z) return {name, index: i, row: t.rows[i]};
  return null;
}
const scriptId = (scene, index) => `script://${scene}/worldmap/man-p0/${String(index).padStart(4, '0')}`;
const changes = (a, b) => Array.from(a, (n, i) => n === b[i] ? null : {byte_offset: i, before_byte: n, after_byte: b[i]}).filter(Boolean);
function seedEqual(a, b) {
  if (Array.isArray(b)) return Array.isArray(a) && a.length === b.length && b.every((n, i) => typeof n === 'number' ? Number.isFinite(a[i]) && Math.abs(a[i] - n) <= 1e-12 : seedEqual(a[i], n));
  if (b && typeof b === 'object') return a && Object.keys(a).sort().join(',') === Object.keys(b).sort().join(',') && Object.keys(b).every(k => seedEqual(a[k], b[k]));
  return a === b;
}
async function coverage(before, after, floor, scene, newCells) {
  const a = await decodeWorldPlacementSeeds(before, floor, scene), b = await decodeWorldPlacementSeeds(after, floor, scene), indexed = new Map(b.placements.map(s => [s.source_cell, s]));
  if (indexed.size !== a.placements.length + newCells.size || a.placements.some(s => !seedEqual(indexed.get(s.source_cell), s)) ||
      !seedEqual(b.unresolved, a.unresolved) || !seedEqual(b.coverage.excluded, a.coverage.excluded) ||
      [...newCells].some(c => !indexed.has(c) || indexed.get(c).source_layer !== 'placed' || indexed.get(c).source_bind_owner !== 'init_bind')) fail('Scripted replay changed original native coverage.');
  return {indexed, count: a.placements.length};
}

export async function allocateScriptedWorldPlacements(data, fallback, man, floor, scene, requests, relocationOffset, allowModelOverride=false) {
  const inv = await worldPlacementInventory(data, floor, scene), l = layout(man);
  if (!Array.isArray(requests) || !integer(requests.length, 1, 32) || inv.current_placements.length + requests.length > 511 ||
      !integer(relocationOffset, 18, 8191) || relocationOffset % 2) fail('Scripted replay exceeds its operation or relocation budget.');
  const primary = tables(data.slice(65536)), backup = tables(fallback).tables[1], t = primary.tables[1];
  const donors = new Map(inv.current_placements.filter(s => s.source_layer === 'placed' && s.source_bind_owner === 'init_bind' && s.model_pool_index).map(s => [s.source_cell, s]));
  const targets = new Set(inv.target_cells), free = new Set(inv.free_record_indices), ids = new Set(), records = new Set(), cells = new Set(), newCells = new Set();
  const result = data.slice(), v = view(result), source = view(data), allocations = [], bindRequests = [];
  for (const r of requests) {
    if (!exact(r, ['placement_id', 'donor_cell', 'target_cell', 'record_index', 'values', 'shared_script', ...(allowModelOverride&&Object.hasOwn(r??{},'model_pool_index')?['model_pool_index']:[])]) || r.shared_script !== true ||
        (Object.hasOwn(r,'model_pool_index')&&!integer(r.model_pool_index,1,511))||!uuid(r.placement_id) || ids.has(r.placement_id) || !integer(r.donor_cell, 0, 16383) || !integer(r.target_cell, 0, 16383) || !integer(r.record_index, 4, 511) ||
        !donors.has(r.donor_cell) || !targets.has(r.target_cell) || !free.has(r.record_index) || records.has(r.record_index) ||
        !exact(r.values, ['offset', 'yaw_units']) || !exact(r.values.offset, ['x', 'y', 'z']) || Object.values(r.values.offset).some(n => !integer(n, -32768, 32767)) || !integer(r.values.yaw_units, 0, 4095)) fail('Scripted request ownership or values differ.');
    const donor = donors.get(r.donor_cell), donorAt = donor.object_record_index * 32, at = r.record_index * 32;
    const col = r.target_cell % 128 + source.getInt8(donorAt + 6), row = Math.floor(r.target_cell / 128) + source.getInt8(donorAt + 7), anchor = row * 128 + col;
    if (!integer(col, 0, 127) || !integer(row, 0, 127) || !targets.has(anchor) || cells.has(anchor) || cells.has(r.target_cell) || source.getUint16(32768 + 2 * anchor, true) & 1024) fail('Scripted anchor is occupied or outside the grid.');
    const hit = lookup(t, backup, donor.source_anchor.col, donor.source_anchor.row);
    if (!hit || hit.name !== 'primary' || lookup(t, backup, col, row)) fail('Scripted donor or destination bind differs.');
    const h = await header(man, l, hit.row[2]), bindId = r.placement_id.replace('placement://', 'bind://');
    const cellAt = 32768 + 2 * r.target_cell, word = source.getUint16(cellAt, true), previousAt = (word & 511) * 32;
    result.set(data.slice(donorAt, donorAt + 32), at); result.set(data.slice(previousAt + 20, previousAt + 24), at + 20);
    ['x', 'y', 'z'].forEach((axis, i) => v.setInt16(at + 2 * i, r.values.offset[axis], true));
    v.setUint16(at + 10, (source.getUint16(donorAt + 10, true) & 61440) | r.values.yaw_units, true);
    if(Object.hasOwn(r,'model_pool_index'))v.setUint16(at+16,r.model_pool_index,true);
    v.setUint16(cellAt, (word & ~511) | r.record_index, true); v.setUint16(32768 + 2 * anchor, v.getUint16(32768 + 2 * anchor, true) | 1024, true);
    allocations.push({placement_id: r.placement_id, bind_id: bindId, donor_cell: r.donor_cell, target_cell: r.target_cell, anchor_cell: anchor, record_index: r.record_index,
      donor_record_sha256: await digest(data.slice(donorAt, donorAt + 32)), allocated_record_sha256: await digest(result.slice(at, at + 32)), shared_script: true, script_id: scriptId(scene, h.index)});
    bindRequests.push({bindId, donor: hit.index, x: col, z: row});
    ids.add(r.placement_id); records.add(r.record_index); cells.add(anchor); cells.add(r.target_cell); newCells.add(r.target_cell);
  }
  const preBind = result.slice(), start = relocationOffset + 4 * t.rows.length, end = start + 4 * requests.length;
  if (!t.rows.length || end > 8192 || t.rows.length + requests.length > 32767 || primary.spans.some(([lo, hi]) => relocationOffset < hi && lo < end) ||
      data.slice(65536 + relocationOffset, 65536 + end).some(n => n !== 0)) fail('Scripted table relocation lacks zero unowned capacity.');
  const used = new Set([...t.rows, ...backup.rows].map(r => `${r[0]},${r[1]}`)), bindAllocations = [];
  t.rows.forEach((r, i) => result.set(r, 65536 + relocationOffset + 4 * i));
  v.setInt16(65542, relocationOffset, true); v.setInt16(65544, t.rows.length + requests.length, true);
  for (const [i, r] of bindRequests.entries()) {
    const donor = t.rows[r.donor], hit = lookup(t, backup, donor[0], donor[1]);
    if (used.has(`${r.x},${r.z}`) || hit.name !== 'primary' || hit.index !== r.donor) fail('Scripted bind does not own an effective original donor.');
    const h = await header(man, l, donor[2]), at = 65536 + start + 4 * i, payload = Uint8Array.of(r.x, r.z, donor[2], donor[3]);
    result.set(payload, at); used.add(`${r.x},${r.z}`);
    bindAllocations.push({bind_id: r.bindId, donor_index: r.donor, record_index: t.rows.length + i, byte_offset: at, byte_length: 4,
      before_hex: '00000000', after_hex: hex(payload), donor_sha256: await digest(donor), flat_man_record_index: donor[2], gate_byte: donor[3],
      script_id: scriptId(scene, h.index), man_record_sha256: h.sha256, encoded_animation_selector: h.selector});
  }
  const afterTables = tables(result.slice(65536)).tables;
  for (let k = 0; k < 4; k++) if (afterTables[k].at !== (k === 1 ? relocationOffset : primary.tables[k].at) ||
      !seedEqual(afterTables[k].rows.map(hex).slice(0, primary.tables[k].rows.length), primary.tables[k].rows.map(hex)) ||
      k !== 1 && afterTables[k].rows.length !== primary.tables[k].rows.length) fail('Scripted bind changed original table owners.');
  const decoded = await coverage(data, result, floor, scene, newCells);
  allocations.forEach(a => {a.native_seed = decoded.indexed.get(a.target_cell);});
  const bindAudit = {scope: 'primary-kind-1-bind-row-allocation', scene, source_sha256: await digest(preBind), proposed_sha256: await digest(result),
    fallback_sha256: await digest(fallback), man_sha256: await digest(man), original_row_count: t.rows.length, proposed_row_count: afterTables[1].rows.length,
    original_table_offset: t.at, proposed_table_offset: relocationOffset,
    relocation: {byte_offset: 65536 + relocationOffset, byte_length: 4 * t.rows.length, before_hex: '00'.repeat(4 * t.rows.length), after_hex: t.rows.map(hex).join(''), original_bytes_preserved: true},
    allocations: bindAllocations, changed_bytes: changes(preBind, result), gameplay_verified: false, placement_allocated: false};
  return {bytes: result, audit: {scope: 'scripted-world-placement-allocation', source_sha256: await digest(data), proposed_sha256: await digest(result),
    allocations, bind_allocation: bindAudit, changed_bytes: changes(data, result), original_placement_count: decoded.count, proposed_placement_count: decoded.indexed.size,
    gameplay_verified: false, runtime_pool_demand: 'not_evaluated', opaque_zero_runtime_ownership: 'not_verified'}};
}

export async function replayScriptedWorldPlacements(base, fallback, man, floor, binding, provenance) {
  const keys = ['scene', 'source_disc_sha256', 'source_map_sha256', 'source_floor_lut_sha256', 'source_man_sha256', 'fallback_sha256'];
  if (!exact(binding, [...keys, 'schema_version', 'base_map_sha256', 'operations']) || !['legaia.worldmap-scripted-placement-ledger.v1','legaia.worldmap-scripted-placement-ledger.v2'].includes(binding.schema_version) ||
      !keys.every(k => k === 'scene' ? binding[k] === provenance?.[k] : hash(binding[k]) && binding[k] === provenance?.[k]) ||
      !hash(binding.base_map_sha256) || await digest(base) !== binding.base_map_sha256 || await digest(fallback) !== binding.fallback_sha256 ||
      !Array.isArray(binding.operations) || !integer(binding.operations.length, 1, 32)) fail('Scripted retained lineage source identity differs.');
  let bytes = base.slice(); const audits = [], ids = new Set(), records = new Set();
  for (const operation of binding.operations) {
    if (!exact(operation, ['requests', 'relocation_offset', 'proposed_map_sha256']) || !hash(operation.proposed_map_sha256)) fail('Scripted operation schema differs.');
    const result = await allocateScriptedWorldPlacements(bytes, fallback, man, floor, binding.scene, operation.requests, operation.relocation_offset,binding.schema_version==='legaia.worldmap-scripted-placement-ledger.v2');
    if (result.audit.proposed_sha256 !== operation.proposed_map_sha256) fail('Scripted retained operation checksum differs.');
    for (const a of result.audit.allocations) {
      if (ids.has(a.placement_id) || records.has(a.record_index) || ids.size >= 32) fail('Scripted retained lineage repeats identity or exceeds its budget.');
      ids.add(a.placement_id); records.add(a.record_index);
    }
    bytes = result.bytes; audits.push(result.audit);
  }
  return {bytes, audits};
}

export async function mergeScriptedWorldCurrent(base, allocated, current, floor, scene, audits) {
  if ([base, allocated, current].some(b => !(b instanceof Uint8Array) || b.length !== 73728)) fail('Scripted merge needs complete MAPs.');
  const a = tables(base.slice(65536)).tables[1], b = tables(current.slice(65536)).tables[1];
  if (a.at !== b.at || !seedEqual(a.rows.map(hex), b.rows.map(hex))) fail('Current bind ownership changed after retention.');
  const owned = new Set(), newCells = new Set(), result = allocated.slice();
  for (const audit of audits) {
    for (const p of audit.allocations) {
      for (let i = p.record_index * 32; i < p.record_index * 32 + 32; i++) owned.add(i);
      for (const cell of [p.target_cell, p.anchor_cell]) {owned.add(32768 + cell * 2); owned.add(32769 + cell * 2);}
      newCells.add(p.target_cell);
    }
    const bind = audit.bind_allocation, at = 65536 + bind.proposed_table_offset;
    for (let i = at; i < at + 4 * bind.proposed_row_count; i++) owned.add(i);
    for (let i = 65542; i < 65546; i++) owned.add(i);
  }
  for (let i = 0; i < base.length; i++) if (base[i] !== current[i]) {
    if (owned.has(i) && current[i] !== allocated[i]) fail('Current edit conflicts with retained scripted ownership.');
    result[i] = current[i];
  }
  tables(result.slice(65536)); await coverage(current, result, floor, scene, newCells);
  return result;
}
