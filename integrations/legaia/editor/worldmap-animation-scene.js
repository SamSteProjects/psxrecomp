import {decodeWorldmapBehaviorResources} from './worldmap-behavior-resources.js';
import {qualifyWorldAnimationCurrent,qualifyWorldAnimationAsset} from './worldmap-animation-current.js';
import {createWorldAnimationSampler,mountWorldAnimationPlayback} from './worldmap-animation-playback.js';
const fail=()=>{throw Error('World scene animation differs from complete Current instances, source clips or saved channels.');};
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&same(Object.keys(v).sort(),keys.sort());

// Current is independently admitted by the World viewport before this plan is used.
export async function qualifyWorldAnimationScene(value,current,path,key,binding=undefined){
  if(!exact(value,['schema_version','project_path','scene','source_key','current','resources','members','absent','unsupported_bindings','coverage','representation','read_only','project_changed','gameplay_verified','timing','looping','runtime_state'])||value.schema_version!=='legaia.world-animation-scene.v1'||value.project_path!==path||value.scene!==current?.scene||value.source_key!==key||current.project_source_key!==key||value.representation!=='current-world-animation-scene-plan'||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||value.timing!=='unresolved'||value.looping!=='unresolved'||value.runtime_state!=='not_observed'||!same(value.current,current)||!Array.isArray(value.members)||value.members.length>32||new TextEncoder().encode(JSON.stringify(value)).length>160*1024*1024)fail();
  const resources=decodeWorldmapBehaviorResources(value.resources,{project:{path},worldmap_authoring_state_key:key}),records=resources.assets.filter(r=>r.kind==='animation'&&r.source_scene===value.scene),entities=new Map(current.scene_graph.entities.map(e=>[e.entity_id,e])),assets=new Map(current.scene_graph.assets.map(a=>[a.asset_id,a])),expected=new Map(),absent=[];
  for(const record of records)for(const b of record.bindings){
    if(expected.has(b.entity_id)||absent.some(e=>e.entity_id===b.entity_id))fail();
    const e=entities.get(b.entity_id);
    if(!e){absent.push({entity_id:b.entity_id,animation_asset_id:record.id,reason:'absent_from_current_scene'});continue;}
    if(e.asset_id!==b.model_asset_id||!assets.has(e.asset_id))fail();expected.set(b.entity_id,record);
  }
  absent.sort((a,b)=>a.entity_id.localeCompare(b.entity_id));
  const kingdom=resources.kingdoms.find(r=>r.scene===value.scene),coverage={compatible_source_instances:expected.size+absent.length,current_instances:expected.size,absent_instances:absent.length,source_only_clips:records.filter(r=>!r.bindings.length).length};
  if(!same(value.coverage,coverage)||!same(value.absent,absent)||!same(value.unsupported_bindings,kingdom.unsupported_animation_bindings)||!same(value.members.map(r=>r.entity_id),[...expected.keys()].sort()))fail();
  const samples=[];let bank=null;
  for(const member of value.members){
    if(!exact(member,['entity_id','animation_asset_id','current']))fail();
    const record=expected.get(member.entity_id);if(!record||member.animation_asset_id!==record.id)fail();
    const v=await qualifyWorldAnimationCurrent(member.current,current,member.entity_id,path,0,binding);qualifyWorldAnimationAsset(v,record);
    if(bank!==null&&bank!==v.preview.bank_sha256)fail();bank=v.preview.bank_sha256;
    const entity=entities.get(member.entity_id),source=assets.get(entity.asset_id).preview,sampler=await createWorldAnimationSampler(v.preview,source);
    samples.push({entity_id:member.entity_id,animation_asset_id:member.animation_asset_id,sampler});
  }
  return {metadata:structuredClone(value),samples};
}

// Pose independent instances on a clone of the admitted viewport scene. Shorter clips hold their last frame.
export function sampleWorldAnimationScene(plan,view,frame){
  if(!plan||!Array.isArray(plan.samples)||plan.samples.length>32||!Number.isSafeInteger(frame)||frame<0||frame>511||!view||!Array.isArray(view.assets)||!Array.isArray(view.entities))fail();
  const next=structuredClone(view),seen=new Set();
  for(const member of plan.samples){
    if(seen.has(member.entity_id))fail();seen.add(member.entity_id);
    const entity=next.entities.find(e=>e.entity_id===member.entity_id),original=view.entities.find(e=>e.entity_id===member.entity_id),asset=next.assets.find(a=>a.geometry_key===entity?.geometry_key),receipt=plan.metadata.members.find(m=>m.entity_id===member.entity_id)?.current;
    if(!entity||!original||!asset||asset.preview?.posed===true||!receipt||!same(asset.preview,receipt.source.current_model_geometry))fail();
    const key=entity.geometry_key+'#world-scene-animation/'+member.entity_id,geometry=member.sampler.sample(Math.min(frame,member.sampler.frameCount-1)).geometry;
    if(next.assets.some(a=>a.geometry_key===key))fail();
    next.assets.push({...asset,geometry_key:key,preview:geometry});entity.geometry_key=key;
  }
  if(next.assets.length>128||next.entities.length>2048)fail();
  return next;
}

export function mountWorldAnimationScene({host,getContext,busy,setBusy,onPose,onReturn,onError,update}){
  const box=document.createElement('details'),summary=document.createElement('summary'),prepare=document.createElement('button'),restore=document.createElement('button'),status=document.createElement('p');
  box.dataset.worldAnimationScene='';Object.assign(box.style,{width:'100%',maxWidth:'100%',boxSizing:'border-box'});summary.textContent='World Scene Animation Preview';prepare.type=restore.type='button';prepare.textContent='Inspect Current scene animations';restore.textContent='Return from scene animation preview';status.textContent='Preview compatible Retail source instances together with saved Current channels. Display timing and shared starts are editor choices; runtime activation remains unknown.';box.append(summary,prepare,restore,status);host.append(box);
  let captured=null,pending=null,disposed=false,shown=false;
  const fresh=()=>!disposed&&captured&&getContext()?.report===captured.report&&getContext()?.key===captured.key&&getContext()?.allowed;
  const playback=mountWorldAnimationPlayback({host:box,current:fresh,busy,onError,update,onFrame:v=>{onPose(v.geometry);shown=true;status.textContent=`Current scene display frame ${v.frame_index}; compatible source instances sampled together. Shorter clips hold their last frame. Native timing, looping and activation remain unknown.`;refresh();update();}});
  function refresh(){prepare.disabled=disposed||busy()||!getContext()?.allowed||!!pending;restore.disabled=disposed||busy()||!shown;playback.update();}
  function reset(){pending?.abort();if(pending){pending=null;setBusy(false);}playback.clear();if(shown){shown=false;onReturn();}captured=null;refresh();}
  prepare.onclick=async()=>{
    if(prepare.disabled)return;reset();captured=getContext();const controller=new AbortController();pending=controller;setBusy(true);refresh();update();let ready=false;
    try{const response=await fetch('/api/worldmap-animation-scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene:captured.report.scene,source_key:captured.key}),signal:controller.signal}),raw=await response.text();if(pending!==controller||!fresh())return;if(new TextEncoder().encode(raw).length>160*1024*1024)fail();const v=JSON.parse(raw);if(!response.ok)throw Error(v.error||'World scene animation inspection failed.');const plan=await qualifyWorldAnimationScene(v,captured.report,captured.path,captured.key,captured.binding);if(pending!==controller||!fresh())return;
      if(!plan.samples.length){status.textContent='No compatible Retail source animation instances are present in this Current scene.';return;}
      const view=structuredClone(captured.view),frames=Math.max(...plan.samples.map(s=>s.sampler.frameCount));playback.set({frameCount:frames,initialFrame:0,sample:frame=>({frame_index:frame,geometry:sampleWorldAnimationScene(plan,view,frame)})});status.textContent=`${plan.samples.length} compatible Current instances qualified; ${plan.metadata.coverage.source_only_clips} unbound clips excluded. No runtime activation is inferred.`;ready=true;
    }catch(e){if(e.name!=='AbortError'&&pending===controller&&fresh()){status.textContent=e.message;onError(e);}}
    finally{if(pending===controller){pending=null;setBusy(false);refresh();if(ready)playback.seek(0);update();}}
  };
  restore.onclick=()=>{if(restore.disabled)return;reset();status.textContent='Current scene geometry restored; no project change.';update();};
  refresh();return {reset,update(){if(captured&&!fresh()&&!pending)reset();refresh();},dispose(){disposed=true;reset();playback.dispose();box.remove();}};
}
