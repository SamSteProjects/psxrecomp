export function decodeModelResolution(value,sceneId,key){
 const fail=()=>{throw Error('Model resolution source or native slot evidence changed.');},int=(n,max)=>Number.isInteger(n)&&n>=0&&n<=max,hash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
 if(value?.schema_version!=='legaia.model-resolution.v1'||value.scene_id!==sceneId||value.source_key!==key||!hash(key)||!hash(value.source_import_sha256)||!/^sha256:[a-f0-9]{64}$/.test(value.disc_identity)||value.read_only!==true||value.runtime_binding!=='not_asserted'||value.gameplay_verified!==false||value.coverage!=='initial_model_references_only'||!Array.isArray(value.rows)||value.rows.length>8192)fail();
 const counts=value.counts;if(!counts||Object.keys(counts).sort().join(',')!=='current_unresolved,global_special,npc_drafts,retail_unresolved,scene_tmd,source_actors'||Object.values(counts).some(n=>!int(n,8192))||counts.source_actors+counts.npc_drafts>8192||counts.npc_drafts>128||counts.retail_unresolved>counts.source_actors||counts.current_unresolved>counts.source_actors+counts.npc_drafts)fail();
 const seen=new Set();let retail=0,current=0;
 const qualify=layer=>{
  const index=layer?.model_index,pool=index>=240?'global_special':'scene_tmd',slot=index>=240?index-240:index,source=layer?.source_record;
  if(!int(index,255)||layer.model_pool!==pool||layer.slot_index!==slot||!source||!int(source.record_index,8192)||!source.record_index||layer.source_actor_id!==sceneId+'/actors/man-p1/'+String(source.record_index).padStart(4,'0')||source.record_kind!=='man_partition_1_actor_placement'||source.byte_coordinate_space!=='decoded_man_payload'||source.disc?.sha256!==value.disc_identity.slice(7)||source.disc.serial!=='SCUS-94254'||source.iso_file!=='PROT.DAT'||source.prot_entry_name!==sceneId.slice(8)||!int(source.byte_offset,0xffffffff)||!int(source.byte_length,4*1024*1024)||!source.byte_length||!int(source.containing_decoded_size,4*1024*1024)||source.byte_offset+source.byte_length>source.containing_decoded_size)fail();
  const expected=pool==='scene_tmd'?'asset://'+sceneId.slice(8)+'/models/scene-tmd/'+String(slot).padStart(4,'0'):'asset://legaia/models/global-special/'+index.toString(16).padStart(4,'0');
  if(layer.status==='unresolved'){if(layer.asset_id!==null||slot<counts[pool])fail();}
  else if(layer.status!=='resolved'||layer.asset_id!==expected||slot>=counts[pool])fail();
 };
 for(const row of value.rows){
  if(seen.has(row.entity_id)||!['actor','npc'].includes(row.kind)||typeof row.entity_id!=='string'||(row.kind==='actor'?!row.entity_id.startsWith(sceneId+'/actors/man-p1/'):!/^authored-actor:\/\/[a-f0-9-]{36}$/.test(row.entity_id)))fail();seen.add(row.entity_id);
  if(row.kind==='npc'){if(row.retail!==null)fail();}else{qualify(row.retail);if(row.retail.source_actor_id!==row.entity_id)fail();}
  qualify(row.current);const a=row.retail?.status==='unresolved',b=row.current.status==='unresolved';if(!a&&!b)fail();retail+=Number(a);current+=Number(b);
 }
 if(retail!==counts.retail_unresolved||current!==counts.current_unresolved||value.rows.length>counts.source_actors+counts.npc_drafts)fail();return structuredClone(value);
}

export function modelResolutionPlacementIds(value,scene,key){
 const report=decodeModelResolution(value,scene,key);
 if(!report.rows.length||report.rows.length>128)throw Error('Select affected placements requires a complete group of 1–128 entities.');
 return report.rows.map(row=>row.entity_id).sort();
}

export async function openModelResolution({getState,busy,onSelect,onSelectGroup=null,onInspectSource=null,onError=()=>{}}){
 const state=getState(),scene=state.scene?.id,key=state.asset_reference_source_key;if(!scene||busy())return;
 const dialog=document.createElement('dialog');dialog.id='model-resolution-dialog';dialog.style.maxWidth='min(760px, calc(100vw - 32px))';
 const heading=document.createElement('h2');heading.textContent='Initial Model Resolution';const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();
 const note=document.createElement('p');note.textContent='Unresolved Retail and Current initial references. Scripts may change runtime models; identity, activation and gameplay remain unverified.';
 const status=document.createElement('p'),content=document.createElement('div');status.setAttribute('role','status');status.textContent='Verifying native scene model references...';dialog.append(heading,close,note,status,content);document.body.append(dialog);dialog.showModal();
 const controller=new AbortController(),fresh=()=>dialog.open&&getState().scene?.id===scene&&getState().asset_reference_source_key===key;let accepted=null;
 const timer=setInterval(()=>{if(!fresh()){accepted=null;content.replaceChildren();status.textContent='Project sources changed. Reopen model resolution.';}},250);
 dialog.addEventListener('close',()=>{clearInterval(timer);controller.abort();accepted=null;dialog.remove();},{once:true});
 try{
  const response=await fetch('/api/model-resolution',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene_id:scene,expected_source_key:key}),signal:controller.signal}),value=await response.json();if(!response.ok||value.error)throw Error(value.error||'Model resolution failed');if(!fresh())return;
  accepted=decodeModelResolution(value,scene,key);status.textContent=`${accepted.counts.retail_unresolved} unresolved Retail references; ${accepted.counts.current_unresolved} unresolved Current references; ${accepted.rows.length} affected entities.`;
  if(!accepted.rows.length)content.textContent='No unresolved initial model references in this scene.';
  if(onSelectGroup&&accepted.rows.length){const group=document.createElement('button');group.type='button';group.textContent='Select All Affected Placements';group.disabled=accepted.rows.length>128;group.title=group.disabled?'The complete group exceeds 128 placements; no partial group is selected.':accepted.rows.length+' affected placements, including hidden members';group.onclick=async()=>{if(group.disabled||!accepted||!fresh()||busy())return;try{const ids=modelResolutionPlacementIds(accepted,scene,key);dialog.close();await onSelectGroup(ids,scene,key);}catch(error){onError(error);}};content.append(group);}
  for(const row of accepted.rows){
   const section=document.createElement('section');section.style.overflowWrap='anywhere';const title=document.createElement('h3');title.textContent=row.entity_id;section.append(title);if(row.kind==='npc'){const note=document.createElement('p');note.textContent='Source script navigation opens the model donor editor. NPC authored script edits remain independent.';section.append(note);}
   for(const [label,layer] of [['Retail',row.retail],['Current',row.current]]){const p=document.createElement('p');p.textContent=layer?`${label}: encoded index ${layer.model_index}; ${layer.model_pool} slot ${layer.slot_index}; ${layer.status}; ${layer.source_actor_id}`:`${label}: no imported NPC instance`;section.append(p);if(layer){const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent=label+' native source record';pre.textContent=JSON.stringify(layer.source_record,null,2);pre.style.whiteSpace='pre-wrap';details.append(summary,pre);section.append(details);if(onInspectSource){const inspect=document.createElement('button');inspect.textContent='Inspect '+label+' source script';inspect.onclick=async()=>{if(!accepted||!fresh()||busy())return;const source=structuredClone(layer);dialog.close();try{await onInspectSource(source,row.kind);}catch(error){onError(error);}};section.append(inspect);}}}
   const select=document.createElement('button');select.textContent='Select affected '+(row.kind==='npc'?'NPC':'actor');select.onclick=async()=>{if(!accepted||!fresh()||busy())return;dialog.close();try{await onSelect(structuredClone(row));}catch(error){onError(error);}};section.append(select);content.append(section);
  }
 }catch(error){if(dialog.open&&error.name!=='AbortError'){status.textContent=error.message;onError(error);}}
}
