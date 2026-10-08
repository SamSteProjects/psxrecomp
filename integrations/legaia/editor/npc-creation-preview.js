export function decodeNpcCreationReview(review,request,scene){
  const canonical=value=>Array.isArray(value)?value.map(canonical):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;
  const equal=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
  const draft={scene_id:scene?.scene_id,donor_entity_id:request.donor_entity_id,name:request.name,position:request.position},command={type:'create_actor_draft',donor_entity_id:request.donor_entity_id,name:request.name,position:request.position};
  if(review?.schema_version!=='legaia.npc-creation-review.v1'||review.scene_id!==scene?.scene_id||review.project_source_key!==request.project_source_key||review.scene_preview_source_key!==scene?.source_key||review.identity_scope!=='temporary_preview_only'||review.project_changed!==false||review.gameplay_verified!==false||!equal(review.draft,draft)||!equal(review.command,command)||!/^[a-f0-9]{64}$/.test(review.review_key??'')||!/^authored-actor:\/\/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(review.preview_entity_id??''))throw Error('NPC creation review differs from its current donor/name/position/source.');
  return structuredClone(review);
}
export function decodeNpcCreationPreview(value,request,scene){
  if(value?.schema_version!=='legaia.npc-creation-scene.v1'||value.geometry_unchanged!==true||value.existing_instances_unchanged!==true||value.project_changed!==false||value.gameplay_verified!==false)throw Error('NPC creation preview has unsupported geometry or mutation claims.');
  const review=decodeNpcCreationReview(value.review,request,scene),row=value.proposed_instance,equal=(a,b)=>a&&b&&Object.keys(a).sort().join(',')===Object.keys(b).sort().join(',')&&['x','y','z'].every(axis=>a[axis]===b[axis]);
  if(scene?.schema!=='legaia.scene-preview.v1'||scene.representation!=='authored'||scene.coordinate_system!=='editor_field_y_up_source_units'||scene.entities.some(item=>item.entity_id===review.preview_entity_id)||row?.entity_id!==review.preview_entity_id||row.kind!=='actor_draft'||row.name!==request.name||row.donor_entity_id!==request.donor_entity_id||row.source_actor_id!==request.donor_entity_id||!equal(row.position,{...request.position,y:null})||!row.renderable||!scene.assets.some(asset=>asset.geometry_key===row.geometry_key)||['x','y','z'].some(axis=>!Number.isFinite(row.display_position?.[axis]))||!Array.isArray(row.model_to_scene)||row.model_to_scene.length!==16||row.model_to_scene.some(value=>!Number.isFinite(value))||[3,7,11].some((index,i)=>row.model_to_scene[index]!==row.display_position[['x','y','z'][i]]))throw Error('Prospective NPC requires a supported source-owned scene mesh and finite native translation.');
  const document=structuredClone(scene);document.entities.push(structuredClone(row));return {report:structuredClone(value),document};
}

// The candidate form owns the request; persistent creation stays with the Project command.
export function mountNpcCreationPreview({form,getRequest,current,available,isBusy,getScene,suspend,resume,onShow,onClear,onError}){
  const button=document.createElement('button');button.type='button';button.textContent='Preview NPC in scene';form.querySelector('button[type="submit"]').before(button);
  let controller=null,pending=false,generation=0,disposed=false,active=false;
  const controls=()=>form.querySelectorAll('input,button');
  const fresh=()=>!disposed&&form.isConnected&&current();
  const clear=()=>{generation++;controller?.abort();controller=null;pending=false;if(active){active=false;onClear();}refresh();};
  const refresh=()=>{if(disposed)return;button.disabled=isBusy()||pending||!fresh()||!available();if(pending)for(const control of controls())control.disabled=true;};
  const changed=()=>clear();form.addEventListener('input',changed);
  button.onclick=async()=>{refresh();if(button.disabled)return;clear();let request,scene;try{request=getRequest();scene=structuredClone(getScene());}catch(error){onError(error);return;}const key=JSON.stringify(request),epoch=++generation;controller=new AbortController();const signal=controller.signal;pending=true;refresh();
    const stillCurrent=()=>{try{return fresh()&&key===JSON.stringify(getRequest());}catch{return false;}};
    try{const post=async(route,body)=>{const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal}),value=await response.json();if(!response.ok)throw Error(value.error||'NPC scene preview failed');return value;};
      const review=await post('/api/npc-creation-review',request);if(!/^[a-f0-9]{64}$/.test(review.review_key??''))throw Error('NPC preview returned no valid review receipt.');const value=await post('/api/npc-creation-scene',{...request,review_key:review.review_key});if(value.review?.review_key!==review.review_key)throw Error('NPC preview review changed during projection.');
      if(signal.aborted||epoch!==generation||!stillCurrent()||!available())return;const result=decodeNpcCreationPreview(value,request,scene);active=true;onShow(result,stillCurrent,()=>{clear();resume();});suspend();
    }catch(error){if(!signal.aborted&&epoch===generation&&fresh())onError(error);}finally{if(epoch===generation){pending=false;controller=null;if(fresh())for(const control of controls())control.disabled=false;refresh();}}
  };
  const timer=setInterval(()=>{if(!form.isConnected){dispose();return;}if(!fresh())clear();refresh();},250);
  function dispose(){if(disposed)return;clear();disposed=true;clearInterval(timer);form.removeEventListener('input',changed);}
  return {button,clear,dispose,pending:()=>pending};
}
