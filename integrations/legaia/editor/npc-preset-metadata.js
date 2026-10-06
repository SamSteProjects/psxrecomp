/** Portable NPC presets contain source-bound metadata only, never native payloads. */
export const NPC_PRESET_SCOPE='npc-draft-preset-v1';
export const NPC_PRESET_FILE_SCHEMA='legaia.npc-preset-file.v1';
const exact=(v,keys)=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const uuid=(v,prefix)=>typeof v==='string'&&v.startsWith(prefix)&&/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/.test(v.slice(prefix.length));
const name=(v,max)=>typeof v==='string'&&v===v.trim()&&v.length>0&&v.length<=max;
export function validateNpcPresetMetadata(template){
  const source=template?.source,components=template?.components,position=components?.Transform?.position,npc=components?.NpcDraft,scene=source?.scene_id,prefix=scene+'/actors/man-p1/';
  if(!exact(template,['id','name','scope','source','components'])||template.scope!==NPC_PRESET_SCOPE||!uuid(template.id,'template://')||!name(template.name,80)||
    !exact(source,['disc_identity','scene_id','entity_id','capture_draft_id','import_sha256'])||!/^sha256:[0-9a-f]{64}$/.test(source.disc_identity)||!/^scene:\/\/[a-z0-9_]+$/.test(scene)||
    typeof source.entity_id!=='string'||!source.entity_id.startsWith(prefix)||!/^[0-9]{4}$/.test(source.entity_id.slice(prefix.length))||!uuid(source.capture_draft_id,'authored-actor://')||!/^[a-f0-9]{64}$/.test(source.import_sha256)||
    !exact(components,['Transform','NpcDraft'])||!exact(components.Transform,['position'])||!exact(position,['x','z'])||Object.values(position).some(n=>!Number.isSafeInteger(n)||n%64||n<64||n>16384)||
    !exact(npc,['name','donor_entity_id'])||!name(npc.name,120)||npc.donor_entity_id!==source.entity_id)throw new Error('Invalid portable NPC donor/placement preset metadata.');
  return structuredClone(template);
}
