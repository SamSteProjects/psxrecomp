import {placementDigest} from './worldmap-placement-replay.js';
import {qualifyNativeTmdGeometry} from './native-tmd-preview.js';
import {SceneRenderer} from './scene-renderer.js';
import {modelPreviewFrame} from './model-preview-frame.js';

const ordered = v => Array.isArray(v) ? v.map(ordered) : v && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map(k => [k, ordered(v[k])])) : v;
const same = (a, b) => JSON.stringify(ordered(a)) === JSON.stringify(ordered(b));
const fail = () => { throw Error('Sideband source, geometry or native page pixels changed.'); };
const hash = v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const pin = 'd6e64c68ede25813d35db20980da82a1a025549b';
const bytes = (s, limit = 1024 * 1024) => {
  if (typeof s !== 'string' || s.length > limit) fail();
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

export async function sourcePngPixels(data, width, height) {
  if (data.length < 57 || ![137,80,78,71,13,10,26,10].every((v,i) => data[i] === v)) fail();
  const view = new DataView(data.buffer,data.byteOffset,data.byteLength), parts = []; let at = 8, header = false, ended = false;
  const crc = raw => { let value = 0xffffffff; for (const b of raw) { value ^= b; for (let i=0;i<8;i++) value = (value >>> 1) ^ ((value & 1) ? 0xedb88320 : 0); } return (value ^ 0xffffffff) >>> 0; };
  while (at + 12 <= data.length) {
    const length = view.getUint32(at), end = at + 12 + length;
    if (end > data.length || crc(data.subarray(at+4,end-4)) !== view.getUint32(end-4)) fail();
    const type = String.fromCharCode(...data.subarray(at+4,at+8)), payload = data.subarray(at+8,end-4);
    if (!header) {
      if (type !== 'IHDR' || length !== 13 || view.getUint32(at+8) !== width || view.getUint32(at+12) !== height || !same([...payload.subarray(8)],[8,6,0,0,0])) fail();
      header = true;
    } else if (type === 'IDAT' && !ended) parts.push(payload);
    else if (type === 'IEND' && length === 0 && parts.length && end === data.length) ended = true;
    else fail();
    at = end;
  }
  if (!ended || at !== data.length) fail();
  const expected = (width*4+1)*height, reader = new Blob(parts).stream().pipeThrough(new DecompressionStream('deflate')).getReader(), chunks = []; let count = 0;
  try { for (;;) { const {done,value} = await reader.read(); if (done) break; count += value.length; if (count > expected) fail(); chunks.push(value); } } finally { await reader.cancel(); }
  if (count !== expected) fail();
  const raw = new Uint8Array(expected); at = 0; for (const chunk of chunks) { raw.set(chunk,at); at += chunk.length; }
  const rgba = new Uint8Array(width*height*4);
  for (let y=0;y<height;y++) { const row = y*(width*4+1); if (raw[row] !== 0) fail(); rgba.set(raw.subarray(row+1,row+1+width*4),y*width*4); }
  return rgba;
}

function sourceGlbPositions(data, geometry, audit) {
  const view = new DataView(data.buffer,data.byteOffset,data.byteLength);
  if (data.length < 28 || view.getUint32(0,true) !== 0x46546c67 || view.getUint32(4,true) !== 2 || view.getUint32(8,true) !== data.length || view.getUint32(16,true) !== 0x4e4f534a) fail();
  const size = view.getUint32(12,true), binAt = 20+size;
  if (size < 2 || binAt+8 > data.length || view.getUint32(binAt+4,true) !== 0x004e4942 || binAt+8+view.getUint32(binAt,true) !== data.length) fail();
  const doc = JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data.subarray(20,binAt))), binary = data.subarray(binAt+8);
  const embedded = Object.fromEntries(Object.entries(audit).filter(([k]) => !['sha256','byte_length'].includes(k)));
  if (doc.asset?.version !== '2.0' || !same(doc.extras,embedded) || doc.animations || doc.skins || doc.images || doc.textures || !Array.isArray(doc.nodes) || doc.nodes.length > 256 || !Array.isArray(doc.meshes) || doc.meshes.length > 256 || !Array.isArray(doc.accessors) || doc.accessors.length > 4096 || !Array.isArray(doc.bufferViews) || doc.bufferViews.length > 4096 || doc.buffers?.length !== 1 || doc.buffers[0].uri || doc.buffers[0].byteLength !== binary.length) fail();
  const seen = new Set();
  for (const node of doc.nodes) {
    const object = node.extras?.source_object, index = object?.object_index;
    if (!Number.isSafeInteger(index) || seen.has(index) || !same(object,geometry.objects[index]) || ['matrix','translation','rotation','scale','children','skin','weights','extensions'].some(k=>Object.hasOwn(node,k))) fail();
    seen.add(index);
    const mesh = doc.meshes[node.mesh]; if (!mesh || !Array.isArray(mesh.primitives) || ['weights','extensions'].some(k=>Object.hasOwn(mesh,k))) fail();
    const materials = new Set();
    for (const p of mesh.primitives) {
      if (p.mode !== 4 || p.indices !== undefined || !Number.isSafeInteger(p.material) || materials.has(p.material) || ['targets','extensions'].some(k=>Object.hasOwn(p,k))) fail(); materials.add(p.material);
      const expected = [];
      for (let t=object.triangle_start;t<object.triangle_start+object.triangle_count;t++) if (geometry.triangle_materials[t] === p.material) for (const corner of [0,2,1]) { const [x,y,z] = geometry.vertices[geometry.triangles[t][corner]]; expected.push([x,-y,z]); }
      const a = doc.accessors[p.attributes?.POSITION], b = doc.bufferViews[a?.bufferView];
      if (!a || !b || a.componentType !== 5126 || a.type !== 'VEC3' || a.count !== expected.length || a.sparse || a.normalized || b.buffer !== 0 || b.byteStride || !Number.isSafeInteger(b.byteOffset) || b.byteOffset < 0 || b.byteLength !== a.count*12 || b.byteOffset+b.byteLength > binary.length || (a.byteOffset ?? 0) !== 0) fail();
      const positions = new DataView(binary.buffer,binary.byteOffset+b.byteOffset,b.byteLength);
      for (let i=0;i<a.count;i++) for (let axis=0;axis<3;axis++) if (positions.getFloat32(i*12+axis*4,true) !== expected[i][axis]) fail();
    }
    const expectedMaterials = new Set(geometry.triangle_materials.slice(object.triangle_start,object.triangle_start+object.triangle_count));
    if (!same([...materials].sort((a,b)=>a-b),[...expectedMaterials].sort((a,b)=>a-b))) fail();
  }
  if (seen.size !== geometry.objects.length) fail();
}

export async function qualifySidebandExport(value, report, record, kind, palette) {
  if (value?.schema_version !== 'legaia.battle-sideband-export.v1' || value.export_kind !== kind || !['glb','png','stp'].includes(kind) || value.read_only !== true || value.project_changed !== false || value.gameplay_verified !== false || value.inspection?.palette_index !== palette) fail();
  const geometry = await qualifySidebandPreview(value.inspection,report,record), source = record.source_record, stem = `sideband-${source.prot_entry_index}-slot-${source.slot_index}`;
  const name = kind === 'glb' ? stem+'-object-local.glb' : stem+`-palette-${palette}`+(kind === 'stp' ? '-stp' : '')+'.png';
  const data = bytes(value.file_base64,8*1024*1024);
  if (value.filename !== name || !Number.isSafeInteger(value.byte_length) || value.byte_length !== data.length || data.length > 6*1024*1024 || value.sha256 !== await placementDigest(data)) fail();
  const audit = value.audit;
  if (kind === 'glb') {
    if (record.asset_kind !== 'tmd_model' || audit?.schema_version !== 'legaia.model-export.v1' || audit.asset_semantic_id !== record.semantic_id || !same(audit.source_record,source) || audit.reference_commit !== pin || audit.representation !== 'retail_battle_sideband_object_local' || audit.posed !== false || audit.frame_index !== null || audit.animation !== null || audit.object_transforms !== null || audit.texture_count !== 0 || audit.object_count !== geometry.objects.length || audit.triangle_count !== geometry.triangles.length || audit.source_coordinate_system !== 'retail_tmd_object_local' || audit.coordinate_conversion !== '[x,-y,z]; reverse triangle winding' || audit.sha256 !== value.sha256 || audit.byte_length !== data.length) fail();
    sourceGlbPositions(data,geometry,audit);
  } else {
    if (record.asset_kind !== 'texture' || !same(audit,{width:geometry.width,height:geometry.height,pixel_format:'RGBA8',adapter:'source_CLUT_page_pixels_not_native_TIM',mask_convention:kind === 'stp' ? 'white_set_bit_black_clear_bit' : null})) fail();
    const pixels = await sourcePngPixels(data,geometry.width,geometry.height), rgba = bytes(geometry.rgba_base64), stp = bytes(geometry.stp_base64);
    for (let i=0;i<pixels.length;i++) { const expected = kind === 'png' ? rgba[i] : i%4 === 3 ? 255 : stp[i>>2]*255; if (pixels[i] !== expected) fail(); }
  }
  return data;
}

const mounted = new WeakMap();
export function updateSidebandResource(dialog) { mounted.get(dialog)?.update(); }

export function showSidebandResource({dialog, record, getReport, current, busy, setBusy, onError}) {
  mounted.get(dialog)?.dispose();
  const report = getReport();
  if (!report || !same(sidebandProjectRecords(report).find(r => r.id === record.id), record)) fail();
  const node = (tag, text) => { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; return e; };
  dialog.replaceChildren();
  const heading = node('div'), close = node('button','×'); heading.className = 'dialog-heading';
  close.type = 'button'; close.setAttribute('aria-label','Close Source Inspector'); close.onclick = () => dialog.close();
  heading.append(node('h2',record.label),close);
  const inspect = node('button',record.type === 'model' ? 'Inspect Source Model' : 'Inspect Source Page'); inspect.type = 'button';
  const palette = node('select'), object = node('select'), canvas = node('canvas'), status = node('p');
  palette.setAttribute('aria-label','Source Page Palette'); object.setAttribute('aria-label','Source Model Object');
  palette.hidden = record.type !== 'texture'; object.hidden = true;
  for (let i = 0; i < (record.data.palette_count ?? 0); i++) { const o = node('option',`Palette ${i}`); o.value = String(i); palette.append(o); }
  for (const select of [palette,object]) Object.assign(select.style,{width:'100%',boxSizing:'border-box'});
  Object.assign(canvas.style,{width:'100%',height:'320px',background:'#101a20',display:'none'});
  canvas.hidden = true; canvas.dataset.sidebandPreview = ''; canvas.dataset.ready = 'false';
  const details = node('details'), pre = node('pre',JSON.stringify(record.data,null,2));
  Object.assign(pre.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}); details.append(node('summary','Source Provenance'),pre);
  const downloads = node('div'), exportButtons = [];
  Object.assign(downloads.style,{display:'flex',flexWrap:'wrap',gap:'6px'});
  for (const [kind,label] of record.type === 'model' ? [['glb','Download Source Model GLB']] : [['png','Download Source Page PNG'],['stp','Download Source Page STP Mask']]) {
    const button = node('button',label); button.type = 'button'; button.disabled = true;
    button.onclick = () => download(kind); exportButtons.push(button); downloads.append(button);
  }
  dialog.append(heading,node('p',record.type === 'model' ? 'Object-local source geometry. Assembly, animation and texture association are unresolved.' : 'Native source CLUT and indexed page. Runtime upload, residency and STP forcing are unresolved.'),inspect,palette,object,canvas,status,downloads,details);
  let disposed = false, pending = null, ownsBusy = false, generation = 0, value = null, renderer = null, loadedObject = null, drag = null;
  const view = {yaw:.55,pitch:-.18,zoom:1};
  const valid = () => !disposed && dialog.open && current() && same(getReport(),report);
  const release = () => { if (ownsBusy) { ownsBusy = false; setBusy(false); } };
  function clear() {
    generation++; pending?.abort(); pending = null; value = null; drag = null;
    renderer?.load({assets:[],entities:[]}); loadedObject = null;
    canvas.hidden = true; canvas.style.display = 'none'; canvas.dataset.ready = 'false'; object.hidden = true;
  }
  function update() {
    if (disposed) return;
    if (!valid()) { clear(); status.textContent = 'Source changed; refresh project resources before inspecting again.'; release(); }
    const blocked = !valid() || busy() || !!pending;
    inspect.disabled = palette.disabled = object.disabled = blocked;
    for (const button of exportButtons) button.disabled = blocked || !value;
  }
  function draw() {
    if (!valid() || !value || record.type !== 'model' || !renderer) return;
    const selected = object.value === 'all' ? null : value.objects[Number(object.value)];
    const start = selected?.triangle_start ?? 0, end = selected ? start + selected.triangle_count : value.triangles.length;
    const geometry = {...value};
    for (const key of ['triangles','triangle_colors','triangle_uvs','triangle_materials','triangle_normals']) geometry[key] = value[key].slice(start,end);
    if (loadedObject !== object.value) {
      const errors = renderer.load({assets:[{geometry_key:'sideband-model',preview:geometry}],entities:[{entity_id:'sideband-model',geometry_key:'sideband-model',renderable:true,model_to_scene:[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]}]});
      if (errors.length) throw Error(errors.join('; ')); loadedObject = object.value;
    }
    const frame = modelPreviewFrame(geometry,geometry,'current','visible'), rect = canvas.getBoundingClientRect();
    const c = Math.cos(view.yaw), s = Math.sin(view.yaw), cp = Math.cos(view.pitch), sp = Math.sin(view.pitch);
    renderer.draw({width:rect.width,height:rect.height,positions:new Map(),grid:false,camera:{target:{x:frame.center[0],y:-frame.center[1],z:frame.center[2]},distance:frame.radius*4/view.zoom*.9/1.3},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}});
    canvas.dataset.ready = 'true';
  }
  const redraw = () => { try { draw(); } catch (error) { clear(); status.textContent = error.message; onError(error); } };
  inspect.onclick = async () => {
    if (inspect.disabled || !valid() || busy() || pending) return;
    clear(); const ticket = generation, controller = new AbortController(), selectedPalette = record.type === 'texture' ? Number(palette.value) : 0;
    pending = controller; ownsBusy = true; setBusy(true); update();
    try {
      const response = await fetch('/api/battle-sideband-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_project_path:report.project_path,expected_source_key:report.project_source_key,asset_id:record.id,catalog_source_key:report.catalog.source_key,palette_index:selectedPalette}),signal:controller.signal});
      const text = await response.text(); if (text.length > 2 * 1024 * 1024) fail();
      const receipt = JSON.parse(text); if (!response.ok) throw Error(receipt.error || 'Source inspection failed');
      if (receipt.palette_index !== selectedPalette) fail();
      const qualified = await qualifySidebandPreview(receipt,report,record.data);
      if (!valid() || generation !== ticket || record.type === 'texture' && Number(palette.value) !== selectedPalette) return;
      value = qualified; canvas.hidden = false; canvas.style.display = 'block';
      if (record.type === 'model') {
        object.replaceChildren(); const all = node('option','All Object-Local Groups'); all.value = 'all'; object.append(all);
        for (const row of value.objects) { const option = node('option',`Object ${row.object_index}`); option.value = String(row.object_index); object.append(option); }
        object.hidden = false; renderer ??= new SceneRenderer(canvas); draw();
        status.textContent = `${value.objects.length} objects · ${value.vertices.length} vertices · ${value.triangles.length} triangles · Source Only. Drag to orbit; scroll to zoom.`;
      } else {
        canvas.width = value.width; canvas.height = value.height; canvas.style.height = 'auto'; canvas.style.imageRendering = 'pixelated';
        canvas.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(bytes(value.rgba_base64)),value.width,value.height),0,0);
        canvas.dataset.ready = 'true'; status.textContent = `${value.width} × ${value.height} · Palette ${selectedPalette} · Source Words And STP`;
      }
    } catch (error) {
      if (generation === ticket && error.name !== 'AbortError' && valid()) { clear(); status.textContent = error.message; onError(error); }
    } finally {
      if (pending === controller) pending = null; release(); update();
    }
  };
  async function download(kind) {
    if (!value || !valid() || busy() || pending) return;
    const held = value, ticket = generation, controller = new AbortController(), selectedPalette = record.type === 'texture' ? Number(palette.value) : 0;
    pending = controller; ownsBusy = true; setBusy(true); update();
    try {
      const response = await fetch('/api/battle-sideband-export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_project_path:report.project_path,expected_source_key:report.project_source_key,asset_id:record.id,catalog_source_key:report.catalog.source_key,palette_index:selectedPalette,export_kind:kind}),signal:controller.signal});
      const text = await response.text(); if (text.length > 8*1024*1024) fail();
      const receipt = JSON.parse(text); if (!response.ok) throw Error(receipt.error || 'Source export failed');
      const file = await qualifySidebandExport(receipt,report,record.data,kind,selectedPalette);
      if (!valid() || generation !== ticket || value !== held || record.type === 'texture' && Number(palette.value) !== selectedPalette) return;
      const url = URL.createObjectURL(new Blob([file],{type:kind === 'glb' ? 'model/gltf-binary' : 'image/png'})), link = node('a');
      link.href = url; link.download = receipt.filename; link.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
      status.textContent = `Downloaded ${receipt.filename} · Source Only`;
    } catch (error) {
      if (error.name !== 'AbortError' && valid() && generation === ticket) { status.textContent = error.message; onError(error); }
    } finally { if (pending === controller) pending = null; release(); update(); }
  }
  palette.onchange = () => { if (!busy() && valid()) { clear(); status.textContent = 'Inspect the selected source palette.'; update(); } };
  object.onchange = redraw;
  canvas.onpointerdown = e => { if (record.type === 'model' && value && valid() && !busy()) { drag = {x:e.clientX,y:e.clientY}; canvas.setPointerCapture(e.pointerId); } };
  canvas.onpointermove = e => { if (!drag || !valid() || busy()) return; view.yaw += (e.clientX-drag.x)*.01; view.pitch = Math.max(-1.4,Math.min(1.4,view.pitch+(e.clientY-drag.y)*.01)); drag = {x:e.clientX,y:e.clientY}; redraw(); };
  canvas.onpointerup = canvas.onpointercancel = () => { drag = null; };
  canvas.addEventListener('wheel',e => { if (record.type !== 'model' || !value || !valid() || busy()) return; e.preventDefault(); view.zoom = Math.max(.25,Math.min(5,view.zoom*Math.exp(-e.deltaY*.001))); redraw(); },{passive:false});
  const observer = new ResizeObserver(redraw); observer.observe(canvas);
  function dispose() { if (disposed) return; disposed = true; clear(); renderer?.dispose(); renderer = null; observer.disconnect(); dialog.removeEventListener('close',dispose); release(); if (mounted.get(dialog)?.dispose === dispose) mounted.delete(dialog); }
  dialog.addEventListener('close',dispose); mounted.set(dialog,{update,dispose});
  if (!dialog.open) dialog.showModal(); update();
}
