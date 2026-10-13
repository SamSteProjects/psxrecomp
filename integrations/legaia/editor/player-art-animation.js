import {placementDigest} from './worldmap-placement-replay.js';
import {qualifyPlayerArtInputs,playerArtInputRecords} from './player-art-inputs.js';
import {decodeArtArchive} from './player-art-codec.js';
import {qualifyPlayerPreview} from './player-battle.js';
import {qualifyPlayerCurrent} from './player-model-review.js';
import {samplePlayerActionBytes} from './player-action-playback.js';
import {qualifyNativeTmdGeometry} from './native-tmd-preview.js';

const canonical = v => Array.isArray(v) ? v.map(canonical) : v && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])) : v;
const same = (a,b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
const hash = v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const fail = () => { throw Error('PLAYER art source, archive selection or assembly changed.'); };
const pin = 'd6e64c68ede25813d35db20980da82a1a025549b';
const bytes = value => { if (typeof value !== 'string' || value.length > 200000) fail(); return Uint8Array.from(atob(value),c=>c.charCodeAt(0)); };

export async function decodePlayerArts(value, expected, modelReport) {
  const c = value?.catalog;
  if (value?.schema_version !== 'legaia.player-art-resources.v1' || value.project_path !== expected.projectPath || value.project_source_key !== expected.sourceKey || value.layer !== 'retail' || value.read_only !== true || value.project_changed !== false || value.gameplay_verified !== false || c?.schema_version !== 'legaia.player-art-catalog.v1' || c.reference_commit !== pin || c.read_only !== true || c.project_changed !== false || c.gameplay_verified !== false || !hash(c.source_disc_sha256) || c.source_disc_sha256 !== modelReport.catalog.source_disc_sha256 || !hash(c.source_entry_sha256) || c.player_file_sha256?.length !== 4 || !c.player_file_sha256.every((h,i)=>hash(h)&&h===modelReport.catalog.models[i].source_record.sha256) || c.archives?.length !== 8 || c.streams?.length !== 87 || c.records?.length !== 109) fail();
  const archiveIds = new Set(), streamIds = new Set(), recordIds = new Set();
  for (const [i,a] of c.archives.entries()) {
    const player = Math.floor(i/2), role = i%2 ? 'base' : 'main', slot = player*3+(i%2 ? 2 : 1);
    if (a.player_index !== player || a.role !== role || a.slot_index !== slot || a.semantic_id !== `archive://legaia/player-art/894/${String(slot).padStart(4,'0')}` || a.entry_count !== (role==='base'?8:[17,18,19,1][player]) || !hash(a.slot_sha256)) fail();
    archiveIds.add(a.semantic_id);
  }
  for (const r of c.streams) {
    const a = c.archives.find(a=>a.semantic_id===r.archive_asset_id), s = r.source_record, player = r.player_index;
    if (!a || !Number.isSafeInteger(player) || player<0 || player>3 || a.player_index!==player || a.role!==r.archive_role || r.asset_kind!=='animation' || r.reference_commit!==pin || r.model_asset_id!==`asset://legaia/models/player-battle/${String(player).padStart(4,'0')}` || !Number.isSafeInteger(r.stream_index) || r.stream_index<0 || r.stream_index>=a.entry_count || r.semantic_id!==`animation://legaia/player-art/${String(player).padStart(4,'0')}/${a.role}/${String(r.stream_index).padStart(4,'0')}` || streamIds.has(r.semantic_id) || r.part_count!==[15,16,15,17][player] || !Number.isSafeInteger(r.frame_count) || r.frame_count<1 || r.frame_count>255 || r.timing!=='not_observed' || r.runtime_state!=='not_observed') fail();
    if (s?.disc?.sha256!==c.source_disc_sha256 || s.disc.serial!=='SCUS-94254' || s.iso_file!=='PROT.DAT' || s.prot_entry_index!==894 || s.entry_sha256!==c.source_entry_sha256 || s.entry_byte_length!==78*0x10800 || s.slot_index!==a.slot_index || s.slot_offset!==a.slot_index*0x10800 || s.slot_byte_length!==0x10800 || s.slot_sha256!==a.slot_sha256 || s.record_kind!=='player_art_me_stream' || s.byte_coordinate_space!=='raw_prot_entry' || !Number.isSafeInteger(s.byte_offset) || s.byte_offset<s.slot_offset+3+2*a.entry_count || !Number.isSafeInteger(s.byte_length) || s.byte_length<1 || s.byte_length>0x7fff || s.byte_offset+s.byte_length>s.slot_offset+0x10800 || s.size_word!==(s.byte_length|0x8000) || s.compressed!==true || !hash(s.sha256) || !hash(s.decoded_sha256) || s.decoded_byte_length!==2+r.part_count*r.frame_count*9) fail();
    streamIds.add(r.semantic_id);
  }
  for (let player=0;player<4;player++) {
    const records = c.records.filter(r=>r.player_index===player);
    if (records.length!==[33,35,32,9][player] || records.filter(r=>r.rate_alt_byte===255).length!==8) fail();
    for (const [i,r] of records.entries()) {
      const s=r.source_record, role=r.rate_alt_byte===255?'base':'main', id=`art-record://legaia/player-battle/${String(player).padStart(4,'0')}/${String(i).padStart(4,'0')}`;
      const eligible=c.streams.filter(v=>v.player_index===player&&v.stream_index===r.stream_source).map(v=>v.semantic_id), preferred=`animation://legaia/player-art/${String(player).padStart(4,'0')}/${role}/${String(r.stream_source).padStart(4,'0')}`;
      if (r.semantic_id!==id || recordIds.has(id) || r.asset_kind!=='player_art_record' || r.record_index!==i || r.staged_animation_id!==0x10+i || r.reference_commit!==pin || typeof r.name!=='string' || r.name.length>20 || /[^\x20-\x7e]/.test(r.name) || !Array.isArray(r.combo) || r.combo.length>10 || r.combo.some(v=>![1,2,3,4].includes(v)) || !['stream_source','entry_tag','attach_key','rate_byte','rate_alt_byte'].every(k=>Number.isSafeInteger(r[k])&&r[k]>=0&&r[k]<=255) || r.reference_archive_role!==role || r.reference_stream_id!==preferred || !same(r.eligible_stream_ids,eligible) || !eligible.includes(preferred) || r.relationship!=='static_bank_reference_runtime_resident_archive_not_observed') fail();
      if (s?.disc?.sha256!==c.source_disc_sha256 || s.disc.serial!=='SCUS-94254' || s.prot_entry_index!==863+player || s.source_entry_sha256!==c.player_file_sha256[player] || !hash(s.containing_sha256) || !Number.isSafeInteger(s.containing_size) || s.containing_size<96 || s.byte_coordinate_space!=='decoded_player_record0' || s.record_kind!=='player_art_bank_record' || s.bank_record_count!==records.length || !Number.isSafeInteger(s.bank_offset) || s.bank_offset<96 || s.byte_offset!==s.bank_offset+4+i*0xd0 || s.byte_length!==0xd0 || s.byte_offset+s.byte_length>s.containing_size || !hash(s.sha256)) fail();
      recordIds.add(id);
    }
  }
  const key = await placementDigest(new TextEncoder().encode('player-art-v1:'+c.source_disc_sha256+':'+c.source_entry_sha256+':'+c.player_file_sha256.join(':')));
  if (key!==c.source_key) fail();
  qualifyPlayerArtInputs(value);
  return structuredClone(value);
}

export function playerArtProjectRecords(report) {
  const context={projectPath:report.project_path,sourceKey:report.project_source_key,artSourceKey:report.catalog.source_key};
  return [...report.catalog.records.map(data=>({id:data.semantic_id,type:'animation',label:data.name?`PLAYER ${data.player_index} Art ${data.record_index}: ${data.name}`:`PLAYER ${data.player_index} Art Record ${data.record_index}`,source:'PLAYER Art Record · Source',data:structuredClone(data),projectPlayerArt:{...context,modelId:`asset://legaia/models/player-battle/${String(data.player_index).padStart(4,'0')}`,artRecordId:data.semantic_id,streamId:data.reference_stream_id}})),
    ...report.catalog.streams.map(data=>({id:data.semantic_id,type:'animation',label:data.name,source:'PLAYER ME Stream · Source',data:structuredClone(data),projectPlayerArt:{...context,modelId:data.model_asset_id,artRecordId:null,streamId:data.semantic_id}})),...playerArtInputRecords(report)];
}

export async function createPlayerArtSampler(value, artReport, modelReport, modelRecord, selection) {
  if (artReport.project_path!==modelReport.project_path || artReport.project_source_key!==modelReport.project_source_key) fail();
  const stream=artReport.catalog.streams.find(s=>s.semantic_id===selection.stream_id), art=selection.art_record_id===null?null:artReport.catalog.records.find(r=>r.semantic_id===selection.art_record_id);
  if (!stream || selection.art_record_id!==null&&!art || art&&!art.eligible_stream_ids.includes(stream.semantic_id) || stream.model_asset_id!==modelRecord.id || value?.schema_version!=='legaia.player-art-playback.v1' || value.project_path!==artReport.project_path || value.project_source_key!==artReport.project_source_key || value.catalog_source_key!==modelReport.catalog.source_key || value.art_source_key!==artReport.catalog.source_key || !same(value.stream,stream) || !same(value.art_record,art) || value.layer!==selection.layer || value.read_only!==true || value.project_changed!==false || value.gameplay_verified!==false || value.archive_selection!=='explicit_source_archive_not_observed_residency' || value.timing!=='not_observed') fail();
  const base=value.base_inspection;
  if (value.layer==='current') { await qualifyPlayerCurrent(base,modelReport,modelRecord); if (selection.expected_current_sha256!==base.effective_file_sha256 || value.effective_file_sha256!==base.effective_file_sha256) fail(); }
  else if (value.layer==='retail') { qualifyPlayerPreview(base,modelReport,modelRecord,selection.equipped); if (selection.expected_current_sha256!==null || value.effective_file_sha256!==modelRecord.data.source_record.sha256) fail(); }
  else fail();
  if (!same(base.assembly.equipped,selection.equipped)) fail();
  if (typeof value.source_tmd_base64!=='string' || value.source_tmd_base64.length>4*1024*1024) fail();
  const tmd=Uint8Array.from(atob(value.source_tmd_base64),c=>c.charCodeAt(0));
  if (await placementDigest(tmd)!==base.assembly.tmd_sha256 || value.layer==='current'&&value.source_tmd_base64!==base.tmd_base64) fail();
  qualifyNativeTmdGeometry(tmd,base.geometry);
  const slot=bytes(value.source_slot_base64), source=stream.source_record;
  if (slot.length!==0x10800 || await placementDigest(slot)!==source.slot_sha256) fail();
  const decoded=decodeArtArchive(slot)[stream.stream_index], claimed=bytes(value.decoded_stream_base64);
  if (!decoded || decoded.byte_offset+source.slot_offset!==source.byte_offset || decoded.byte_length!==source.byte_length || decoded.size_word!==source.size_word || await placementDigest(slot.subarray(decoded.byte_offset,decoded.byte_offset+decoded.byte_length))!==source.sha256 || !same([...decoded.decoded],[...claimed]) || claimed.length!==source.decoded_byte_length || claimed[0]!==stream.part_count || claimed[1]!==stream.frame_count || await placementDigest(claimed)!==source.decoded_sha256) fail();
  return samplePlayerActionBytes(claimed,base.geometry,base.assembly.animation_part_indices);
}

export async function qualifyPlayerArtPose(value, artReport, modelReport, modelRecord, selection, frame) {
  if (value?.schema_version!=='legaia.player-art-pose.v1' || value.frame_index!==frame || value.read_only!==true || value.project_changed!==false || value.gameplay_verified!==false) fail();
  const sampler=await createPlayerArtSampler(value.playback,artReport,modelReport,modelRecord,selection), expected=sampler.sample(frame), actual=value.geometry;
  if (!same(value.object_transforms,expected.object_transforms) || actual?.vertices?.length!==expected.geometry.vertices.length || actual.vertices.some((v,i)=>v.length!==3||v.some((n,a)=>!Number.isFinite(n)||Math.abs(n-expected.geometry.vertices[i][a])>1e-7))) fail();
  for (const k of ['min','max']) if (actual.bounds?.[k]?.length!==3 || actual.bounds[k].some((v,a)=>!Number.isFinite(v)||Math.abs(v-expected.geometry.bounds[k][a])>1e-7)) fail();
  const copy=structuredClone(actual);copy.vertices=expected.geometry.vertices;copy.bounds=expected.geometry.bounds;
  if (!same(copy,expected.geometry)) fail();
  return sampler;
}
