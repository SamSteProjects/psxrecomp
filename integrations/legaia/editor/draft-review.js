const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const integer=(value,max)=>Number.isSafeInteger(value)&&value>=0&&value<=max;
const fail=message=>{throw new Error(message);};
function node(tag,text){const value=document.createElement(tag);if(text!==undefined)value.textContent=text;return value;}
export function decodeDraftOutputReview(value,key){
  if(!value||value.schema_version!=='legaia.draft-output-review.v1'||value.project_source_key!==key||!hash(key)||!['source_disc_sha256','source_prot_sha256','result_prot_sha256'].every(name=>hash(value[name]))||!integer(value.archive_bytes,256*1024*1024)||!integer(value.draft_count,128)||value.draft_count===0||!Array.isArray(value.scenes)||!value.scenes.length||value.scenes.length>128||value.experimental!==true||value.normal_build_ready!==false||value.output_written!==false||value.gameplay_verified!==false||!Array.isArray(value.limitations)||value.limitations.length>32||value.limitations.some(line=>typeof line!=='string'||line.length>2048))fail('NPC review differs from the current source or its experimental limits.');
  const scenes=new Set();let count=0;
  for(const scene of value.scenes){
    if(typeof scene.scene_id!=='string'||!/^scene:\/\/[A-Za-z0-9_-]+$/.test(scene.scene_id)||scenes.has(scene.scene_id)||!integer(scene.draft_count,128)||!hash(scene.final_man_sha256)||!Array.isArray(scene.facing_changes)||scene.facing_changes.length>1024)fail('NPC review scene ownership or facing coverage is invalid.');
    scenes.add(scene.scene_id);count+=scene.draft_count;
    const fields=new Set();
    for(const row of scene.facing_changes){
      if(typeof row.owner_id!=='string'||!row.owner_id.startsWith(scene.scene_id+'/')||typeof row.facing_id!=='string'||!row.facing_id.startsWith('script://'+row.owner_id.slice(8)+'/facing/')||!integer(row.pc,65535)||!integer(row.decoded_byte_offset,4*1024*1024)||!integer(row.source_decoded_byte_offset,4*1024*1024)||!integer(row.before_byte,255)||!integer(row.after_byte,255)||!integer(row.after_sector,7)||(row.before_byte&240)!==(row.after_byte&240)||(row.after_byte&15)!==row.after_sector||!hash(row.source_record_sha256)||!hash(row.appended_man_sha256)||fields.has(row.decoded_byte_offset))fail('NPC facing audit has conflicting ownership, source bytes or sector flags.');
      fields.add(row.decoded_byte_offset);
    }
  }
  if(count!==value.draft_count)fail('NPC review draft totals differ from its scene coverage.');
  return structuredClone(value);
}

export function mountDraftOutputReview({after,getState,busy,setBusy,onError=()=>{}}){
  const button=node('button','Review NPC output');button.id='draft-output-review';button.type='button';after.after(button);
  let session=null;
  function updateState(){const state=getState();button.disabled=busy()||state.project?.mode!=='edit'||state.capabilities?.draft_output_review!==true||!hash(state.build_review_source_key);if(session&&!session.current()){const previous=session;session=null;previous.withdraw();}}
  button.onclick=()=>{
    updateState();if(button.disabled)return;
    const state=getState(),key=state.build_review_source_key,path=state.project.path;
    const dialog=node('dialog');dialog.id='draft-output-dialog';dialog.className='project-dialog';Object.assign(dialog.style,{width:'min(620px,94vw)',maxHeight:'92vh',overflowY:'auto',boxSizing:'border-box'});
    const heading=node('div');heading.className='dialog-heading';const close=node('button','Close');close.type='button';close.dataset.action='close';heading.append(node('h2','Serialized NPC candidate review'),close);
    const status=node('p','Qualifying saved drafts and all supported authored inputs…'),content=node('div');dialog.append(heading,status,content);document.body.append(dialog);dialog.showModal();
    const controller=new AbortController();let pending=true;const current=()=>dialog.open&&getState().project?.path===path&&getState().project?.mode==='edit'&&getState().build_review_source_key===key;
    const release=()=>{if(pending){pending=false;setBusy(false);updateState();}};
    const owned={current,withdraw:()=>{controller.abort();content.replaceChildren();status.textContent='Project inputs or mode changed. Close and review the current NPC output again.';release();}};session=owned;
    close.onclick=()=>dialog.close();dialog.addEventListener('close',()=>{if(session===owned)session=null;controller.abort();release();dialog.remove();},{once:true});setBusy(true);
    (async()=>{try{
      const response=await fetch('/api/draft-output-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source_key:key}),signal:controller.signal});
      const text=await response.text();if(!current()||controller.signal.aborted)return;if(new TextEncoder().encode(text).length>4*1024*1024)fail('NPC review exceeds its metadata budget.');const raw=JSON.parse(text);if(!response.ok||raw.error)fail(raw.error||'NPC serialization review failed');const report=decodeDraftOutputReview(raw,key);
      status.textContent=`${report.draft_count} saved NPC candidate(s) · ${report.scenes.length} scene(s) · ${report.archive_bytes.toLocaleString()} logical archive bytes. No disc or package written. Gameplay unverified.`;
      for(const scene of report.scenes){
        content.append(node('h3',`${scene.scene_id} · ${scene.draft_count} candidate(s)`));
        content.append(node('p',`${scene.facing_changes.length} source facing field(s) after record relocation`));
        for(const row of scene.facing_changes){const line=node('p',`${row.owner_id} · PC ${row.pc} · sector ${row.before_sector} → ${row.after_sector} · source byte ${row.source_decoded_byte_offset} → candidate byte ${row.decoded_byte_offset}`);line.style.overflowWrap='anywhere';content.append(line);}
      }
      for(const line of report.limitations){const p=node('p',line);p.className='field-note';content.append(p);}
      const details=node('details'),pre=node('pre',JSON.stringify(report,null,2));pre.className='diagnostic-detail';Object.assign(pre.style,{maxHeight:'360px',overflow:'auto'});details.append(node('summary','Complete source and allocation metadata'),pre);content.append(details);
    }catch(error){if(error.name!=='AbortError'&&current()){status.textContent=error.message;onError(error);}}finally{release();}})();
  };
  updateState();return {button,updateState};
}
