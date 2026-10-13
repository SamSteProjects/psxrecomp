import {placementDigest} from './worldmap-placement-replay.js';
import {qualifyNativeTmdGeometry} from './native-tmd-preview.js';

const ordered = v => Array.isArray(v) ? v.map(ordered) : v && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map(k => [k, ordered(v[k])])) : v;
const same = (a, b) => JSON.stringify(ordered(a)) === JSON.stringify(ordered(b));
const fail = () => { throw Error('Sideband source, geometry or native page pixels changed.'); };
const hash = v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const pin = 'd6e64c68ede25813d35db20980da82a1a025549b';
const bytes = s => {
  if (typeof s !== 'string' || s.length > 1024 * 1024) fail();
  return Uint8Array.from(atob(s), c => c.charCodeAt(0));
};

export async function decodeSidebandResources(value, expected) {
  const c = value?.catalog;
  if (value?.schema_version !== 'legaia.battle-sideband-resources.v1' || value.project_path !== expected.projectPath || value.project_source_key !== expected.sourceKey || value.layer !== 'retail' || value.read_only !== true || value.project_changed !== false || value.gameplay_verified !== false || c?.schema_version !== 'legaia.battle-sideband-catalog.v1' || c.reference_commit !== pin || !hash(c.source_disc_sha256) || c.read_only !== true || c.project_changed !== false || c.gameplay_verified !== false || !Array.isArray(c.banks) || c.banks.length !== 2 || !Array.isArray(c.slots) || c.slots.length !== 181 || !Array.isArray(c.models) || !Array.isArray(c.textures) || c.models.length + c.textures.length > 181) fail();
  const banks = new Map();
  for (let i = 0; i < 2; i++) {
    const b = c.banks[i], count = [103,78][i], entry = [893,894][i];
    if (b.prot_entry_index !== entry || b.slot_count !== count || b.byte_length !== count * 0x10800 || !hash(b.sha256)) fail();
    banks.set(entry, b);
  }
  function source(s) {
    const b = banks.get(s?.prot_entry_index);
    if (!b || s.disc?.sha256 !== c.source_disc_sha256 || s.disc.serial !== 'SCUS-94254' || s.iso_file !== 'PROT.DAT' || s.entry_sha256 !== b.sha256 || s.entry_byte_length !== b.byte_length || !Number.isSafeInteger(s.slot_index) || s.slot_index < 0 || s.slot_index >= b.slot_count || s.slot_offset !== s.slot_index * 0x10800 || s.slot_byte_length !== 0x10800 || !hash(s.slot_sha256) || s.byte_coordinate_space !== 'raw_prot_entry') fail();
    return s;
  }
  const slots = new Map();
  for (let i = 0; i < c.slots.length; i++) {
    const r = c.slots[i], s = source(r.source_record), entry = i < 103 ? 893 : 894, index = i < 103 ? i : i - 103;
    if (r.prot_entry_index !== entry || r.slot_index !== index || s.prot_entry_index !== entry || s.slot_index !== index || !['texture','actor_record','opaque'].includes(r.kind)) fail();
    slots.set(`${entry}/${index}`, r);
  }
  const ids = new Set();
  for (const r of [...c.models,...c.textures]) {
    const s = source(r.source_record), row = slots.get(`${s.prot_entry_index}/${s.slot_index}`);
    if (r.reference_commit !== pin || r.preview_supported !== true || typeof r.name !== 'string' || !r.name.length || r.name.length > 256 || /[\x00-\x1f\x7f]/.test(r.name) || !hash(s.sha256) || !Number.isSafeInteger(s.byte_offset) || !Number.isSafeInteger(s.byte_length) || s.byte_length < 12 || s.byte_offset < s.slot_offset || s.byte_offset + s.byte_length > s.slot_offset + 0x10800 || ids.has(r.semantic_id) || row.asset_id !== r.semantic_id || Object.entries(row.source_record).some(([k,v]) => !same(s[k],v))) fail();
    if (c.models.includes(r)) {
      const summary = r.preview_summary;
      if (r.asset_kind !== 'tmd_model' || row.kind !== 'actor_record' || row.preview_supported !== true || s.record_kind !== 'sideband_actor_tmd' || r.semantic_id !== `asset://legaia/models/battle-sideband/${s.prot_entry_index}/${String(s.slot_index).padStart(4,'0')}` || !Number.isSafeInteger(r.source_model_offset) || r.source_model_offset < 0x4c || !Number.isSafeInteger(r.source_texture_pool_offset) || r.source_model_offset >= r.source_texture_pool_offset || r.source_texture_pool_offset >= 0x10800 || s.byte_offset !== s.slot_offset + r.source_model_offset || r.references_beyond_texture_pool !== (s.byte_length > r.source_texture_pool_offset - r.source_model_offset) || !summary || !Number.isSafeInteger(summary.objects) || summary.objects < 1 || summary.objects > 256 || !['vertices','triangles'].every(k => Number.isSafeInteger(summary[k]) && summary[k] >= 0 && summary[k] <= 100000)) fail();
    } else {
      const rows = r.mode === 1 ? 2 : 1, width = r.mode === 0 ? 256 : 512;
      if (r.asset_kind !== 'texture' || row.kind !== 'texture' || s.record_kind !== 'sideband_clut_page' || r.semantic_id !== `texture://legaia/battle-sideband/${s.prot_entry_index}/${String(s.slot_index).padStart(4,'0')}` || ![0,1,2].includes(r.mode) || r.width !== width || r.height !== 256 || r.bpp !== 4 || r.clut_rows !== rows || r.palette_count !== rows * 16 || r.image_offset !== 4 + rows * 512 || r.image_byte_length !== width * 128 || s.byte_offset !== s.slot_offset || s.byte_length !== r.image_offset + r.image_byte_length) fail();
    }
    ids.add(r.semantic_id);
  }
  if (c.slots.some(r => r.asset_id && !ids.has(r.asset_id))) fail();
  const key = await placementDigest(new TextEncoder().encode('battle-sideband-v1:' + c.source_disc_sha256 + ':' + c.banks.map(b => b.sha256).join(':')));
  if (key !== c.source_key) fail();
  return structuredClone(value);
}

export function sidebandProjectRecords(report) {
  return [...report.catalog.models,...report.catalog.textures].map(data => ({id:data.semantic_id, type:data.asset_kind === 'tmd_model' ? 'model' : 'texture', label:data.name, source:`Battle Sideband · PROT ${data.source_record.prot_entry_index} · Retail`, data:structuredClone(data), projectSideband:{projectPath:report.project_path, sourceKey:report.project_source_key, catalogSourceKey:report.catalog.source_key}}));
}

export async function qualifySidebandPreview(value, report, record) {
  const source = record?.source_record;
  if (value?.schema_version !== 'legaia.battle-sideband-preview.v1' || value.project_path !== report.project_path || value.project_source_key !== report.project_source_key || value.catalog_source_key !== report.catalog.source_key || !same(value.record, record) || value.layer !== 'retail' || value.read_only !== true || value.project_changed !== false || value.gameplay_verified !== false) fail();
  const slot = bytes(value.source_slot_base64);
  if (slot.length !== 0x10800 || await placementDigest(slot) !== source.slot_sha256) fail();
  const offset = source.byte_offset - source.slot_offset;
  if (!Number.isSafeInteger(offset) || offset < 0 || source.byte_length < 1 || offset + source.byte_length > slot.length) fail();
  const body = slot.slice(offset, offset + source.byte_length);
  if (await placementDigest(body) !== source.sha256) fail();
  const g = value.preview;
  if (record.asset_kind === 'tmd_model') {
    if (value.palette_index !== 0 || g?.schema_version !== 'legaia.model-preview.v1' || g.posed !== false || g.coordinate_system !== 'retail_tmd_object_local' || g.semantic_id !== record.semantic_id || !same(g.source_record, source) || g.representation !== 'retail_battle_sideband_object_local' || g.texture_association !== 'unresolved_source_geometry_only' || g.reference_commit !== record.reference_commit || ['textures','frames','animation','skins'].some(k => Object.hasOwn(g,k))) fail();
    qualifyNativeTmdGeometry(body, g);
    if (!same(record.preview_summary, {objects:g.objects.length, vertices:g.vertices.length, triangles:g.triangles.length})) fail();
  } else if (record.asset_kind === 'texture') {
    const p = value.palette_index, view = new DataView(body.buffer, body.byteOffset, body.byteLength);
    if (!Number.isSafeInteger(p) || p < 0 || p >= record.palette_count || g.palette_index !== p || g.width !== record.width || g.height !== 256 || g.stp_forcing !== 'not_applied_source_words_only' || view.getUint32(0, true) !== record.mode) fail();
    const words = Array.from({length:16}, (_, i) => view.getUint16(4 + p * 32 + i * 2, true));
    if (!same(g.words, words)) fail();
    const rgba = bytes(g.rgba_base64), stp = bytes(g.stp_base64), image = body.subarray(record.image_offset);
    if (rgba.length !== record.width * 256 * 4 || stp.length !== record.width * 256 || image.length * 2 !== stp.length) fail();
    for (let pixel = 0; pixel < stp.length; pixel++) {
      const word = words[(image[pixel >> 1] >> ((pixel & 1) * 4)) & 15];
      for (let axis = 0; axis < 3; axis++) {
        const n = (word >> (axis * 5)) & 31;
        if (rgba[pixel * 4 + axis] !== ((n << 3) | (n >> 2))) fail();
      }
      if (rgba[pixel * 4 + 3] !== (word === 0 ? 0 : 255) || stp[pixel] !== ((word >> 15) & 1)) fail();
    }
  } else fail();
  return structuredClone(g);
}
