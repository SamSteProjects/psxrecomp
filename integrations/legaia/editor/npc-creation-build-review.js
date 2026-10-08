import {decodeNpcCreationReview} from '/npc-creation-preview.js';
import {decodeBuildReview} from '/build-review.js';

export function decodeNpcCreationBuildReview(value,request,context){
  if(value?.schema_version!=='legaia.npc-creation-build-review.v1'||value.read_only!==true||value.project_changed!==false||value.output_written!==false||value.gameplay_verified!==false||value.assessment_scope!=='complete_supported_project_with_one_prospective_npc'||value.existing_npc_draft_count!==context.existing_npc_draft_count||!Number.isSafeInteger(value.proposed_npc_draft_count)||value.proposed_npc_draft_count!==context.existing_npc_draft_count+1||value.proposed_npc_draft_count>128||!/^[a-f0-9]{64}$/.test(value.prospective_build_source_key??''))throw Error('Prospective NPC Build review has stale coverage or unsupported mutation claims.');
  decodeNpcCreationReview(value.review,request,context);
  const build=decodeBuildReview(value.build_review,value.prospective_build_source_key);
  if(build.schema_version!=='legaia.build-review.v2'||build.included_npc_draft_count!==value.proposed_npc_draft_count)throw Error('Prospective NPC is missing from the complete Build assessment.');
  return structuredClone(value);
}

export function mountNpcCreationBuildReview({form,current,getRequest,getContext,available,isBusy,setBusy,onError}){
  const button=document.createElement('button'),content=document.createElement('section');button.type='button';button.textContent='Review Build with proposed NPC';content.setAttribute('aria-label','Proposed NPC Build readiness');content.hidden=true;form.querySelector('button[type="submit"]').before(button,content);
  let controller=null,pending=false,generation=0,disposed=false;
  const fresh=()=>!disposed&&form.isConnected&&current();
  const refresh=()=>{if(!disposed)button.disabled=pending||isBusy()||!fresh()||!available();};
  const release=()=>{if(pending){pending=false;setBusy(false);if(fresh())for(const control of form.querySelectorAll('input,button'))control.disabled=false;}};
  const clear=()=>{generation++;controller?.abort();controller=null;release();content.replaceChildren();content.hidden=true;refresh();};
  const changed=()=>clear();form.addEventListener('input',changed);
  button.onclick=async()=>{refresh();if(button.disabled)return;clear();let request,context;try{request=getRequest();context=structuredClone(getContext());}catch(error){onError(error);return;}const error=form.querySelector('.dialog-error');if(error)error.textContent='';const key=JSON.stringify([request,context]),epoch=++generation;controller=new AbortController();const signal=controller.signal;pending=true;for(const control of form.querySelectorAll('input,button'))control.disabled=true;setBusy(true);content.hidden=false;content.textContent='Reviewing all supported authored content with one prospective NPC; no package will be written.';
    const stillCurrent=()=>{try{return fresh()&&key===JSON.stringify([getRequest(),getContext()]);}catch{return false;}};
    try{const response=await fetch('/api/npc-creation-build-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),signal}),raw=await response.json();if(signal.aborted||epoch!==generation||!stillCurrent())return;if(!response.ok)throw Error(raw.error||'Prospective NPC Build review failed');const value=decodeNpcCreationBuildReview(raw,request,context),build=value.build_review;content.replaceChildren();const status=document.createElement('p');status.setAttribute('role','status');status.textContent=build.normal_build_ready?'Proposed inputs passed source serialization and package-fit review. NPC not created; package not written; gameplay unverified.':`Proposed project Build is blocked (${build.blockers.length} blocker(s)). NPC not created; package not written.`;content.append(status);
      const scope=document.createElement('p');scope.textContent=`${value.existing_npc_draft_count} existing NPC draft(s) + 1 prospective NPC. ${build.assessment?'All supported authored inputs were assessed.':'Serialization stopped at a blocker; later inputs are not claimed to have passed.'} Create and review the saved project again before Build.`;content.append(scope);
      for(const row of build.blockers){const note=document.createElement('p');note.className='dialog-error';note.textContent=row.message;content.append(note);}const limits=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Build review scope and limitations';limits.append(summary);for(const text of build.limitations){const p=document.createElement('p');p.textContent=text;limits.append(p);}content.append(limits);
    }catch(error){if(!signal.aborted&&epoch===generation&&fresh()){content.textContent=error.message;onError(error);}}finally{if(epoch===generation){release();controller=null;refresh();}}
  };
  const timer=setInterval(()=>{if(!form.isConnected){dispose();return;}if(!fresh())clear();refresh();},250);
  function dispose(){if(disposed)return;clear();disposed=true;clearInterval(timer);form.removeEventListener('input',changed);}
  return {button,clear,dispose,pending:()=>pending};
}
