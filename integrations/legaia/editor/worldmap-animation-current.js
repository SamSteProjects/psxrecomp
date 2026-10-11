import {placementDigest} from './worldmap-placement-replay.js';
import {qualifyWorldObjectAnimation,qualifyWorldAnimationPreview} from './worldmap-object-animation.js';
const fail=()=>{throw Error('Saved World animation differs from immutable source, canonical channels or Current pose.');};
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===keys.sort().join(',');
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const integer=(v,lo,hi)=>Number.isSafeInteger(v)&&v>=lo&&v<=hi;
const bytes=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));

// Replay exact packed channels; retain header, trailer, opaque bits and all neighbors.
export async function replayWorldAnimationChannels(bank,index,recordHash,edits){
  if(!(bank instanceof Uint8Array)||bank.length<4||bank.length>4194304||!Array.isArray(edits)||edits.length>4096)fail();
  const view=new DataView(bank.buffer,bank.byteOffset,bank.byteLength),count=view.getUint32(0,true);
  if(!integer(count,1,4096)||4+count*4>bank.length||!integer(index,0,count-1))fail();
  const offsets=Array.from({length:count},(_,i)=>view.getUint32(4+i*4,true));
  if(offsets[0]<4+count*4||offsets.at(-1)>=bank.length||offsets.some((n,i)=>i&&n<=offsets[i-1]))fail();
  const start=offsets[index],end=offsets[index+1]??bank.length,record=bank.slice(start,end);
  if(record.length<16||await placementDigest(record)!==recordHash)fail();
  const r=new DataView(record.buffer),header=r.getUint16(0,true),objects=header&255,frames=r.getUint16(2,true);
  if(header>>8>1||!integer(objects,1,64)||!integer(frames,1,512)||r.getUint16(4,true)!==0x80c||![2,4].includes(r.getUint16(6,true))||record.length!==16+objects*frames*8||record.slice(-8).some(n=>n))fail();
  const candidate=bank.slice(),channels=[],normalized=[],seen=new Set(),signed=n=>n&2048?n-4096:n;
  for(const edit of [...edits].sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index)){
    if(!edit||!exact(edit,['frame_index','object_index',...['translation','rotation_psx'].filter(k=>k in edit)])||!['translation','rotation_psx'].some(k=>k in edit)||!integer(edit.frame_index,0,frames-1)||!integer(edit.object_index,0,objects-1))fail();
    const key=`${edit.frame_index}:${edit.object_index}`;if(seen.has(key))fail();seen.add(key);
    const at=8+(edit.frame_index*objects+edit.object_index)*8,d=record.slice(at,at+8),values={translation:[signed(d[0]+(d[2]&15)*256),signed(d[1]+(d[2]>>4)*256),signed(d[3]+(d[4]&15)*256)],rotation_psx:[d[5]*16,d[6]*16,d[7]*16]},row={frame_index:edit.frame_index,object_index:edit.object_index};
    for(const field of ['translation','rotation_psx']){
      if(!(field in edit))continue;const axes=edit[field];
      if(!axes||Array.isArray(axes)||typeof axes!=='object'||!Object.keys(axes).length||Object.keys(axes).some(k=>!'xyz'.includes(k)||k.length!==1))fail();
      for(const axis of Object.keys(axes).sort()){
        const value=axes[axis],i='xyz'.indexOf(axis),before=values[field][i];
        if(field==='translation'?!integer(value,-2048,2047):!integer(value,0,4080)||value%16)fail();
        if(value!==before){channels.push({frame_index:edit.frame_index,object_index:edit.object_index,field:`${field}.${axis}`,before_value:before,after_value:value,channel_byte_offset:at});(row[field]??={})[axis]=value;values[field][i]=value;}
      }
    }
    if(Object.keys(row).length>2)normalized.push(row);
    const [x,y,z]=values.translation.map(n=>n&4095);
    candidate.set([x&255,y&255,(x>>8)|((y>>8)<<4),z&255,(d[4]&240)|(z>>8),...values.rotation_psx.map(n=>n/16)],start+at);
  }
  const changed=[];for(let i=0;i<bank.length;i++)if(bank[i]!==candidate[i])changed.push({byte_offset:i,before_byte:bank[i],after_byte:candidate[i]});
  return {bank:candidate,normalized,audit:{scope:'world-animation-channel-content-only',record_index:index,byte_offset:start,byte_length:end-start,source_bank_sha256:await placementDigest(bank),proposed_bank_sha256:await placementDigest(candidate),source_record_sha256:recordHash,proposed_record_sha256:await placementDigest(candidate.slice(start,end)),channels,changed_bytes:changed,gameplay_verified:false}};
}

export async function qualifyNativeWorldAnimation(native,current,id,path,frame,edits){
  if(!exact(native,['schema_version','project_path','scene','source_key','entity_id','frame_index','edits','animation_id','before','current_model_geometry','proposed_preview','audit','read_only','project_changed','gameplay_verified','build_ready','limitations','review_key']))fail();
  const before=native.before;await qualifyWorldObjectAnimation(before,current,id,path,frame);
  const entity=current.scene_graph.entities.find(e=>e.entity_id===id),geometry=current.scene_graph.assets.find(a=>a.asset_id===entity.asset_id).preview;
  const animationId=`animation://${current.scene}/worldmap/anm/${String(before.preview.record_index).padStart(4,'0')}`;
  if(native.schema_version!=='legaia.worldmap-animation-review.v1'||native.project_path!==path||native.scene!==current.scene||native.source_key!==current.project_source_key||native.entity_id!==id||native.frame_index!==frame||native.animation_id!==animationId||!same(native.edits,edits)||!same(native.current_model_geometry,geometry)||native.read_only!==true||native.project_changed!==false||native.gameplay_verified!==false||native.build_ready!==false||typeof native.review_key!=='string'||!/^[0-9a-f]{64}$/.test(native.review_key)||!Array.isArray(native.limitations)||native.limitations.some(s=>typeof s!=='string'||s.length>4096))fail();
  const bank=bytes(before.preview.bank_base64),replay=await replayWorldAnimationChannels(bank,before.preview.record_index,before.preview.record_sha256,edits);
  if(!same(native.audit,replay.audit)||native.proposed_preview.encoded_selector!==before.preview.encoded_selector)fail();
  await qualifyWorldAnimationPreview(native.proposed_preview,geometry,replay.bank,frame);
  return {before,bank,geometry,replay,animationId};
}

export async function composeWorldAnimationBinding(binding,before,current){
  let bank=bytes(before.preview.bank_base64);const audits=[];
  if(binding!==null){
    const b=binding;
    if(!exact(b,['schema_version','scene','source_disc_sha256','source_bank_sha256','entries'])||b.schema_version!=='legaia.world-animation-channels.v1'||b.scene!==current.scene||b.source_bank_sha256!==before.preview.bank_sha256||!exact(b.entries,Object.keys(b.entries??{}))||!integer(Object.keys(b.entries).length,1,4096)||b.source_disc_sha256!==current.source_record.disc_sha256)fail();
    let total=0;
    for(const index of Object.keys(b.entries).sort()){
      const entry=b.entries[index];if(!/^\d{4}$/.test(index)||Number(index)>4095||!exact(entry,['source_record_sha256','edits'])||!Array.isArray(entry.edits)||!entry.edits.length||(total+=entry.edits.length)>4096)fail();
      const replay=await replayWorldAnimationChannels(bank,Number(index),entry.source_record_sha256,entry.edits);
      if(!same(replay.normalized,entry.edits))fail();bank=replay.bank;audits.push(replay.audit);
    }
  }
  return {bank,audits};
}

export async function qualifyWorldAnimationCurrent(v,current,id,path,frame,expectedBinding=undefined){
  if(!exact(v,['schema_version','project_path','scene','source_key','entity_id','frame_index','animation_id','source','binding','preview','audits','representation','read_only','project_changed','gameplay_verified'])||v.schema_version!=='legaia.world-animation-current.v1'||v.project_path!==path||v.scene!==current.scene||v.source_key!==current.project_source_key||v.entity_id!==id||v.frame_index!==frame||v.representation!=='current-model-current-world-animation'||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false)fail();
  if(expectedBinding!==undefined&&!same(v.binding,expectedBinding))fail();
  const {before,geometry,animationId}=await qualifyNativeWorldAnimation(v.source,current,id,path,frame,[]);
  const {bank,audits}=await composeWorldAnimationBinding(v.binding,before,current);
  if(v.animation_id!==animationId||!same(v.audits,audits)||v.preview.encoded_selector!==before.preview.encoded_selector)fail();
  await qualifyWorldAnimationPreview(v.preview,geometry,bank,frame);
  return structuredClone(v);
}

export async function qualifyWorldAnimationEdit(v,held,current,id,path,frame,edits){
  if(!exact(v,['schema_version','project_path','scene','source_key','entity_id','frame_index','animation_id','edits','shared_record','source','before_binding','binding','current_preview','proposed_preview','current_bank_sha256','proposed_bank_sha256','changed_bytes','project_change','read_only','project_changed','gameplay_verified','build_ready','review_key'])||v.schema_version!=='legaia.world-animation-edit-review.v1'||v.project_path!==path||v.scene!==current.scene||v.source_key!==current.project_source_key||v.entity_id!==id||v.frame_index!==frame||!same(v.edits,edits)||v.shared_record!==true||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false||v.build_ready!==false||typeof v.review_key!=='string'||!/^[0-9a-f]{64}$/.test(v.review_key))fail();
  await qualifyWorldAnimationCurrent(held,current,id,path,frame);
  const {before,geometry,replay,animationId}=await qualifyNativeWorldAnimation(v.source,current,id,path,frame,edits);
  if(v.animation_id!==animationId||!same(before,held.source.before)||!same(v.before_binding,held.binding)||!same(v.current_preview,held.preview))fail();
  let binding=structuredClone(held.binding)??{schema_version:'legaia.world-animation-channels.v1',scene:current.scene,source_disc_sha256:current.source_record.disc_sha256,source_bank_sha256:before.preview.bank_sha256,entries:{}};
  const index=String(before.preview.record_index).padStart(4,'0');
  if(replay.normalized.length)binding.entries[index]={source_record_sha256:before.preview.record_sha256,edits:replay.normalized};else delete binding.entries[index];
  if(!Object.keys(binding.entries).length)binding=null;
  const proposed=await composeWorldAnimationBinding(binding,before,current),old=bytes(held.preview.bank_base64),changed=[];
  for(let i=0;i<old.length;i++)if(old[i]!==proposed.bank[i])changed.push({byte_offset:i,before_byte:old[i],after_byte:proposed.bank[i]});
  if(!same(v.binding,binding)||v.project_change!==!same(held.binding,binding)||v.current_bank_sha256!==held.preview.bank_sha256||v.proposed_bank_sha256!==await placementDigest(proposed.bank)||!same(v.changed_bytes,changed)||v.proposed_preview.encoded_selector!==before.preview.encoded_selector)fail();
  await qualifyWorldAnimationPreview(v.proposed_preview,geometry,proposed.bank,frame);
  return structuredClone(v);
}

export function qualifyWorldAnimationAsset(v,record){
  const p=v?.source?.before?.preview,s=record?.source_record,b=v?.source?.before?.binding?.man_source;
  if(!p||!s||record.kind!=='animation'||record.source_scene!==v.scene||record.id!==`animation://${v.scene}/worldmap/scene-anm/${String(p.record_index).padStart(4,'0')}`||(record.authored_animation_id??`animation://${v.scene}/worldmap/anm/${String(p.record_index).padStart(4,'0')}`)!==v.animation_id||p.record_sha256!==s.sha256||p.byte_offset!==s.byte_offset||p.byte_length!==s.byte_length||!same(v.source.before.animation_source,s.animation_slot)||p.frame_count!==record.frame_count||p.channel_count!==record.channel_count||b.disc_sha256!==s.disc_sha256||b.entry_index!==s.prot_entry_index||b.table_offset!==s.table_offset)fail();
  return structuredClone(record);
}
