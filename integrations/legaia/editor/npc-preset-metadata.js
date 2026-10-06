/** Portable NPC presets contain source-bound metadata only, never native payloads. */
export const NPC_PRESET_SCOPE='npc-draft-preset-v1';
export const NPC_PRESET_FILE_SCHEMA='legaia.npc-preset-file.v1';
export const NPC_DIALOGUE_PRESET_FILE_SCHEMA='legaia.npc-preset-file.v2';
export const NPC_APPEARANCE_PRESET_FILE_SCHEMA='legaia.npc-preset-file.v3';
export const NPC_WAITS_PRESET_FILE_SCHEMA='legaia.npc-preset-file.v4';
export const NPC_MOVEMENT_PRESET_FILE_SCHEMA='legaia.npc-preset-file.v5';
export const NPC_FACING_PRESET_FILE_SCHEMA='legaia.npc-preset-file.v6';
export const NPC_FLAGS_PRESET_FILE_SCHEMA='legaia.npc-preset-file.v7';
const exact=(v,keys)=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const uuid=(v,prefix)=>typeof v==='string'&&v.startsWith(prefix)&&/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/.test(v.slice(prefix.length));
const name=(v,max)=>typeof v==='string'&&v===v.trim()&&v.length>0&&v.length<=max;
export function validateNpcPresetMetadata(template){
  const source=template?.source,components=template?.components,position=components?.Transform?.position,npc=components?.NpcDraft,scene=source?.scene_id,prefix=scene+'/actors/man-p1/';
  if(!exact(template,['id','name','scope','source','components'])||template.scope!==NPC_PRESET_SCOPE||!uuid(template.id,'template://')||!name(template.name,80)||
    !exact(source,['disc_identity','scene_id','entity_id','capture_draft_id','import_sha256'])||!/^sha256:[0-9a-f]{64}$/.test(source.disc_identity)||!/^scene:\/\/[a-z0-9_]+$/.test(scene)||
    typeof source.entity_id!=='string'||!source.entity_id.startsWith(prefix)||!/^[0-9]{4}$/.test(source.entity_id.slice(prefix.length))||!uuid(source.capture_draft_id,'authored-actor://')||!/^[a-f0-9]{64}$/.test(source.import_sha256)||
    !exact(components,['Transform','NpcDraft'])||!exact(components.Transform,['position'])||!exact(position,['x','z'])||Object.values(position).some(n=>!Number.isSafeInteger(n)||n%64||n<64||n>16384)||
    (!npc||typeof npc!=='object'||Array.isArray(npc)||!Object.hasOwn(npc,'name')||!Object.hasOwn(npc,'donor_entity_id')||Object.keys(npc).some(k=>!['name','donor_entity_id','dialogue','appearance','waits','movement','facing','flags'].includes(k)))||!name(npc.name,120)||npc.donor_entity_id!==source.entity_id)throw new Error('Invalid portable NPC donor/placement preset metadata.');
  if(Object.hasOwn(npc,'dialogue')){
    const value=npc.dialogue,runs=value?.runs,prefix='script://'+npc.donor_entity_id.slice(8);
    if(!exact(value,['donor_entity_id','runs'])||value.donor_entity_id!==npc.donor_entity_id||!runs||typeof runs!=='object'||Array.isArray(runs)||Object.keys(runs).length<1||Object.keys(runs).length>1024)throw new Error('Invalid NPC preset owned dialogue.');
    let length=0;for(const [id,text] of Object.entries(runs)){if((!id.startsWith(prefix+'/')||!/^(?:dialogue\/[0-9a-f]{4}|menu\/[0-9a-f]{4}\/option\/[0-3])\/run\/[0-9a-f]{4}$/.test(id.slice(prefix.length+1)))||typeof text!=='string'||text.length>4096||/[^\x20-\x7e]|[\^|]/.test(text))throw new Error('NPC preset text is not a supported donor-owned glyph run.');length+=text.length;}if(length>65536)throw new Error('NPC preset text exceeds its span budget.');
  }
  if(Object.hasOwn(npc,'appearance')){const value=npc.appearance;if(!exact(value,['script_donor_entity_id','donor_entity_id'])||value.script_donor_entity_id!==npc.donor_entity_id||typeof value.donor_entity_id!=='string'||!value.donor_entity_id.startsWith(prefix)||!/^[0-9]{4}$/.test(value.donor_entity_id.slice(prefix.length)))throw new Error('NPC preset appearance witness differs from its script donor or scene.');}
  if(Object.hasOwn(npc,'waits')){const value=npc.waits,entries=value?.entries,prefix='script://'+npc.donor_entity_id.slice(8)+'/wait/';if(!exact(value,['donor_entity_id','entries'])||value.donor_entity_id!==npc.donor_entity_id||!entries||typeof entries!=='object'||Array.isArray(entries)||Object.keys(entries).length<1||Object.keys(entries).length>1024)throw new Error('Invalid NPC preset owned waits.');for(const [id,fields] of Object.entries(entries))if(!id.startsWith(prefix)||!/^[0-9a-f]{4}$/.test(id.slice(prefix.length))||!exact(fields,['duration_ticks'])||!Number.isInteger(fields.duration_ticks)||fields.duration_ticks<0||fields.duration_ticks>32767)throw new Error('NPC preset wait must be a donor-owned integer target.');}
  if(Object.hasOwn(npc,'movement')){
    const value=npc.movement,entries=value?.entries,prefix='script://'+npc.donor_entity_id.slice(8)+'/movement/';
    if(!exact(value,['donor_entity_id','entries'])||value.donor_entity_id!==npc.donor_entity_id||!entries||typeof entries!=='object'||Array.isArray(entries)||Object.keys(entries).length<1||Object.keys(entries).length>1024)throw new Error('Invalid NPC preset owned movement.');
    for(const [id,fields] of Object.entries(entries)){
      if(!id.startsWith(prefix)||!/^[0-9a-f]{4}$/.test(id.slice(prefix.length))||!fields||typeof fields!=='object'||Array.isArray(fields)||Object.keys(fields).length<1||Object.keys(fields).some(k=>!['x','z','move_id'].includes(k)))throw new Error('NPC preset movement must be a donor-owned typed target.');
      for(const [field,n] of Object.entries(fields))if(!Number.isInteger(n)||(field==='move_id'?(n<0||n>255):(n<64||n>16384||n%64)))throw new Error('Invalid NPC preset movement operand.');
    }
  }
  if(Object.hasOwn(npc,'facing')){
    const value=npc.facing,entries=value?.entries,prefix='script://'+npc.donor_entity_id.slice(8)+'/facing/';
    if(!exact(value,['donor_entity_id','entries'])||value.donor_entity_id!==npc.donor_entity_id||!entries||typeof entries!=='object'||Array.isArray(entries)||Object.keys(entries).length<1||Object.keys(entries).length>1024)throw new Error('Invalid NPC preset owned facing.');
    for(const [id,fields] of Object.entries(entries))if(!id.startsWith(prefix)||!/^[0-9a-f]{4}$/.test(id.slice(prefix.length))||!exact(fields,['sector'])||!Number.isInteger(fields.sector)||fields.sector<0||fields.sector>7)throw new Error('NPC preset facing must be a donor-owned integer sector from 0 to 7.');
  }
  if(Object.hasOwn(npc,'flags')){
    const value=npc.flags,entries=value?.entries,prefix='script://'+npc.donor_entity_id.slice(8)+'/flag-bit/';
    if(!exact(value,['donor_entity_id','entries'])||value.donor_entity_id!==npc.donor_entity_id||!entries||typeof entries!=='object'||Array.isArray(entries)||Object.keys(entries).length<1||Object.keys(entries).length>1024)throw new Error('Invalid NPC preset owned flags.');
    for(const [id,fields] of Object.entries(entries))if(!id.startsWith(prefix)||!/^[0-9a-f]{4}$/.test(id.slice(prefix.length))||!exact(fields,['bit'])||!Number.isInteger(fields.bit)||fields.bit<0||fields.bit>31)throw new Error('NPC preset flags must be a donor-owned integer bit from 0 to 31.');
  }
  return structuredClone(template);
}
