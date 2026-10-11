const fail=()=>{throw Error('Saved World animation asset differs from its source clip or project binding.');};
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===keys.sort().join(',');
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));

export function qualifyWorldAnimationAuthoredAsset(record,binding){
  const authored=record.authoredRecord,r=record.data,source=authored?.source_record,entry=authored?.authored?.WorldAnimationChannels,index=String(r?.source_record?.record_index).padStart(4,'0');
  if(!record.projectWorldBehaviorResource||record.type!=='animation'||r?.kind!=='animation'||!['shared_rigid_channels','source_metadata_only','native_channel_content'].includes(r.authoring)||authored?.kind!=='animation'||authored.id!==r.authored_animation_id||authored.scene_id!==null||authored.source_scene!==r.source_scene||!exact(authored.authored,['WorldAnimationChannels'])||!exact(source,['source_disc_sha256','source_bank_sha256','source_record_sha256','record_index'])||source.source_disc_sha256!==r.source_record.disc_sha256||source.source_bank_sha256!==r.source_record.animation_slot.decoded_sha256||source.source_record_sha256!==r.source_record.sha256||source.record_index!==r.source_record.record_index||!exact(binding,['schema_version','scene','source_disc_sha256','source_bank_sha256','entries'])||binding.schema_version!=='legaia.world-animation-channels.v1'||binding.scene!==r.source_scene||binding.source_disc_sha256!==source.source_disc_sha256||binding.source_bank_sha256!==source.source_bank_sha256||!same(binding.entries?.[index],entry)||!exact(entry,['source_record_sha256','edits'])||entry.source_record_sha256!==source.source_record_sha256||!Array.isArray(entry.edits)||entry.edits.length<1||entry.edits.length>4096)fail();
  let last=-1;
  for(const edit of entry.edits){
    if(!exact(edit,['frame_index','object_index',...['translation','rotation_psx'].filter(k=>k in edit)])||!['translation','rotation_psx'].some(k=>k in edit)||!Number.isSafeInteger(edit.frame_index)||edit.frame_index<0||edit.frame_index>=r.frame_count||!Number.isSafeInteger(edit.object_index)||edit.object_index<0||edit.object_index>=r.channel_count||edit.frame_index*r.channel_count+edit.object_index<=last)fail();
    last=edit.frame_index*r.channel_count+edit.object_index;
    for(const field of ['translation','rotation_psx'])if(field in edit){const axes=edit[field];if(!axes||typeof axes!=='object'||Array.isArray(axes)||!Object.keys(axes).length||Object.keys(axes).some(k=>!'xyz'.includes(k)||k.length!==1))fail();for(const v of Object.values(axes))if(!Number.isSafeInteger(v)||(field==='translation'?v < -2048||v > 2047:v<0||v>4080||v%16))fail();}
  }
  return structuredClone(entry);
}

// Retain the registered Retail identity; attach saved metadata through its explicit authored alias.
export function mergeWorldAnimationAuthoredAssets(records,authoredAssets,bindings){
  const result=records.map(r=>({...r})),seen=new Set();
  for(const authored of authoredAssets??[]){
    if(authored.kind!=='animation'||!authored.authored?.WorldAnimationChannels)continue;
    if(seen.has(authored.id))fail();seen.add(authored.id);
    const candidates=result.filter(r=>r.projectWorldBehaviorResource&&r.data?.authored_animation_id===authored.id);
    if(candidates.length>1)fail();if(!candidates.length)continue;
    const record=candidates[0],binding=bindings?.[`worldmap://${record.data.source_scene}/animation-channels`]?.WorldAnimationChannels;
    record.authoredRecord=structuredClone(authored);qualifyWorldAnimationAuthoredAsset(record,binding);
    record.authored=structuredClone(authored.authored);record.changes=[...(authored.changes??[])];
  }
  return result;
}
