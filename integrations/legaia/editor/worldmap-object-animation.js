import {mountWorldAnimationEditor} from './worldmap-animation-editor.js';
import {qualifyWorldObjectBind} from './worldmap-object-bind.js';
import {placementDigest} from './worldmap-placement-replay.js';
import {rigidFrameNormals} from './source-normal-view.js';
const fail=()=>{throw Error('World animation differs from source bytes, Current geometry or preview scope.');};
const bytes=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
const matches=(a,b)=>typeof b==='number'?Number.isFinite(a)&&Math.abs(a-b)<=1e-8:
  Array.isArray(b)?Array.isArray(a)&&a.length===b.length&&b.every((v,i)=>matches(a[i],v)):
  b&&typeof b==='object'?a&&Object.keys(a).sort().join(',')===Object.keys(b).sort().join(',')&&Object.keys(b).every(k=>matches(a[k],b[k])):a===b;
export async function qualifyWorldObjectAnimation(v,current,id,path,frame){
  if(!v||Object.keys(v).sort().join(',')!==['schema_version','project_path','scene','source_key','entity_id','model_asset_id','model_source','binding','animation_source','preview','representation','read_only','project_changed','gameplay_verified'].sort().join(','))fail();
  await qualifyWorldObjectBind(v.binding,current,id,path);
  if(v.schema_version!=='legaia.worldmap-object-animation.v1'||v.project_path!==path||v.scene!==current.scene||v.source_key!==current.project_source_key||v.entity_id!==id||v.representation!=='current-model-retail-object-animation'||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false)fail();
  const entity=current.scene_graph.entities.find(e=>e.entity_id===id),asset=current.scene_graph.assets.find(a=>a.asset_id===entity?.asset_id),p=v.preview;
  if(!asset||v.model_asset_id!==asset.asset_id||!matches(v.model_source,asset.source_record)||p.encoded_selector!==v.binding.bind.encoded_animation_selector||!Number.isInteger(p.encoded_selector)||p.encoded_selector<1)fail();
  if(p.bank_sha256!==v.animation_source.decoded_sha256||bytes(p.bank_base64).length!==v.animation_source.decoded_byte_length||v.animation_source.slot_index!==4||v.animation_source.descriptor_type!==5)fail();
  await qualifyWorldAnimationPreview(p,asset.preview,bytes(p.bank_base64),frame);
  return structuredClone(v);
}

// The caller supplies independently reconstructed bank bytes and raw Current geometry.
export async function qualifyWorldAnimationPreview(p,source,expected,frame){
  const bank=bytes(p.bank_base64),view=new DataView(bank.buffer);
  if(!(expected instanceof Uint8Array)||bank.length!==expected.length||bank.some((n,i)=>n!==expected[i]))fail();
  if(bank.length<4||bank.length>4194304||await placementDigest(bank)!==p.bank_sha256)fail();
  const count=view.getUint32(0,true);if(count<1||count>4096||4+count*4>bank.length||count!==p.bank_record_count)fail();
  const offsets=Array.from({length:count},(_,i)=>view.getUint32(4+i*4,true));if(offsets[0]<4+count*4||offsets.at(-1)>=bank.length||offsets.some((n,i)=>i&&n<=offsets[i-1]))fail();
  const index=p.encoded_selector-1,at=offsets[index],end=offsets[index+1]??bank.length;
  if(index>=count||p.record_index!==index||p.byte_offset!==at||p.byte_length!==end-at)fail();
  const record=bank.slice(at,end),r=new DataView(record.buffer),a=r.getUint16(0,true),channels=a&255,frames=r.getUint16(2,true);
  if(record.length<16||a>>8>1||r.getUint16(4,true)!==0x80c||![2,4].includes(r.getUint16(6,true))||channels<1||channels>64||frames<1||frames>512||record.length!==16+channels*frames*8||record.slice(-8).some(n=>n)||channels!==source.objects.length||channels!==p.channel_count||frames!==p.frame_count||p.frame_index!==frame||!Number.isInteger(frame)||frame<0||frame>=frames)fail();
  if(await placementDigest(record)!==p.record_sha256||!matches(Array.from(bytes(p.record_base64)),Array.from(record)))fail();
  const transforms=Array.from({length:channels},(_,i)=>{const pos=8+(frame*channels+i)*8,d=record.slice(pos,pos+8),signed=n=>n&2048?n-4096:n;return {object_index:i,translation:[signed(d[0]+(d[2]&15)*256),signed(d[1]+(d[2]>>4)*256),signed(d[3]+(d[4]&15)*256)],rotation_psx:[d[5]*16,d[6]*16,d[7]*16],opaque_nibble:d[4]>>4};});
  if(!matches(p.object_transforms,transforms))fail();
  const vertices=new Array(source.vertices.length),rotate=(v,t)=>{const [rx,ry,rz]=t.rotation_psx.map(n=>n*Math.PI*2/4096);let [x,y,z]=v;[y,z]=[y*Math.cos(rx)-z*Math.sin(rx),y*Math.sin(rx)+z*Math.cos(rx)];[x,z]=[x*Math.cos(ry)+z*Math.sin(ry),-x*Math.sin(ry)+z*Math.cos(ry)];return [x*Math.cos(rz)-y*Math.sin(rz)+t.translation[0],x*Math.sin(rz)+y*Math.cos(rz)+t.translation[1],z+t.translation[2]];};
  for(let i=0;i<channels;i++){const o=source.objects[i];if(o.object_index!==i||!Number.isInteger(o.vertex_start)||!Number.isInteger(o.vertex_count)||o.vertex_start<0||o.vertex_count<0||o.vertex_start+o.vertex_count>vertices.length)fail();for(let j=o.vertex_start;j<o.vertex_start+o.vertex_count;j++){if(vertices[j]!==undefined)fail();vertices[j]=rotate(source.vertices[j],transforms[i]);}}
  if(vertices.includes(undefined))fail();
  const bounds={min:[0,1,2].map(i=>Math.min(...vertices.map(v=>v[i]))),max:[0,1,2].map(i=>Math.max(...vertices.map(v=>v[i])))};
  const geometry={...structuredClone(source),vertices,bounds,posed:true,coordinate_system:'retail_psx_actor_local_y_down'};
  if(source.triangle_normals!==undefined)Object.assign(geometry,rigidFrameNormals(source,{posed:true,coordinate_system:'retail_psx_actor_local_y_down',object_transforms:transforms}));
  delete geometry.frames;
  if(!matches(p.geometry,geometry)||p.normal_pose!==(source.triangle_normals===undefined?'unavailable':'rigid_rotation_only')||p.association!=='retail_object_header_scene_anm_record_plus_one'||p.timing!=='unresolved'||p.looping!=='unresolved'||p.runtime_state!=='not_observed'||p.rounding!=='analytic_preview_not_fixed_point_gte')fail();
  return structuredClone(p);
}

export function mountWorldObjectAnimation({host,binding,currentReport,entityId,path,current,busy,setBusy,onPose,onReturn,onError,update,api,onApplied,getBinding}){
  const box=document.createElement('div');box.dataset.worldObjectAnimation='';host.append(box);
  const title=document.createElement('h4');title.textContent='World Animation Preview';box.append(title);
  const frame=document.createElement('input');frame.type='number';frame.min='0';frame.max='511';frame.step='1';frame.value='0';frame.setAttribute('aria-label','World source animation frame');box.append(frame);
  const preview=document.createElement('button');preview.type='button';preview.textContent='Preview source animation frame';box.append(preview);
  const currentPreview=document.createElement('button');currentPreview.type='button';currentPreview.textContent='Preview Current animation frame';box.append(currentPreview);
  const restore=document.createElement('button');restore.type='button';restore.textContent='Return to Current geometry';box.append(restore);
  const status=document.createElement('p');status.textContent='Compare Retail or saved Current animation with the Current model. ANM records may be shared; timing and live state are unknown.';box.append(status);
  let disposed=false,pending=null,shown=false,editTool=null;
  const refresh=()=>{frame.disabled=preview.disabled=currentPreview.disabled=disposed||!current()||busy();restore.disabled=disposed||!current()||busy()||!shown;editTool?.update();};
  const show=async(authored,expected=null)=>{if(disposed||!current()||busy())return;editTool?.cancel();const n=Number(frame.value);if(frame.value.trim()===''||!Number.isInteger(n)||n<0||n>511){status.textContent='Choose a whole source frame 0..511.';return;}const controller=new AbortController();pending=controller;setBusy(true);refresh();update();
    const valid=()=>!disposed&&current()&&pending===controller;
    try{const response=await fetch(authored?'/api/worldmap-object-animation-current':'/api/worldmap-object-animation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene:currentReport.scene,source_key:binding.source_key,entity_id:entityId,frame_index:n}),signal:controller.signal}),text=await response.text();if(!valid())return;if(new TextEncoder().encode(text).length>(authored?160:40)*1024*1024)fail();const v=JSON.parse(text);if(!response.ok)throw Error(v.error||'Source animation preview failed.');const qualified=authored?await (await import('./worldmap-animation-current.js')).qualifyWorldAnimationCurrent(v,currentReport,entityId,path,n,getBinding()):await qualifyWorldObjectAnimation(v,currentReport,entityId,path,n);if(!valid())return;if(expected)(await import('./worldmap-animation-current.js')).qualifyWorldAnimationAsset(qualified,expected);onPose(qualified.preview.geometry);shown=true;frame.max=String(v.preview.frame_count-1);status.textContent=`${authored?'Current':'Retail'} frame ${n} / ${v.preview.frame_count-1} · ${v.preview.channel_count} rigid channels. Current placement retained; no project change or live animation.`;return true;
    }catch(error){if(error.name!=='AbortError'&&valid()){status.textContent=error.message;onError(error);}}
    finally{if(pending===controller){pending=null;setBusy(false);refresh();update();}}
  };
  preview.onclick=()=>show(false);currentPreview.onclick=()=>show(true);
  restore.onclick=()=>{if(restore.disabled)return;editTool?.cancel();onReturn();shown=false;status.textContent='Current geometry restored; no project change.';refresh();update();};
  editTool=mountWorldAnimationEditor({host:box,currentReport,entityId,path,current,busy,setBusy,api,onApplied,getBinding,onError,update,onPose:geometry=>{onPose(geometry);shown=true;},onReturn:()=>{onReturn();shown=false;},onInspect:()=>{if(shown){onReturn();shown=false;}}});
  refresh();return {dispose(){disposed=true;editTool?.dispose();pending?.abort();if(pending){pending=null;setBusy(false);}if(shown)onReturn();box.remove();},update:refresh,openAsset:async record=>{frame.value='0';return await show(true,record);}};
}
