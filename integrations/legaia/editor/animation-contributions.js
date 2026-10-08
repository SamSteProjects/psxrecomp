const integer=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
export function inspectAnimationContributions(record,entities,sceneId){
 const data=record?.data,hash=data?.source_record?.record_sha256;
 if(typeof sceneId!=='string'||!sceneId.startsWith('scene://')||record?.type!=='animation'||typeof record.id!=='string'||!record.id.startsWith('animation://'+sceneId.slice(8)+'/scene-anm/')||!integer(data?.frame_count,1,4096)||!integer(data?.bone_count,1,1024)||typeof hash!=='string'||!/^([a-f0-9]{64})$/.test(hash)||!Array.isArray(entities)||entities.length>512)throw Error('Stored contribution inspection requires a bounded native clip and source hash.');
 const cells=new Map(),owners=new Set();let count=0;
 for(const entity of entities){
  const binding=entity?.components?.Animation?.authored_channels;if(!binding||binding.animation_id!==record.id)continue;
  if(typeof entity.id!=='string'||!entity.id.startsWith(sceneId+'/actors/')||owners.has(entity.id)||entity.components?.ActorAnimation?.imported?.animation_asset_id!==record.id||binding.source_record_sha256!==hash||!Array.isArray(binding.edits)||binding.edits.length>4096)throw Error('Stored contribution differs from its imported clip owner or source.');
  owners.add(entity.id);const seen=new Set();
  for(const edit of binding.edits){
   if(!edit||Object.keys(edit).some(k=>!['frame_index','object_index','translation','rotation_psx'].includes(k))||!integer(edit.frame_index,0,data.frame_count-1)||!integer(edit.object_index,0,data.bone_count-1)||seen.has(edit.frame_index+':'+edit.object_index))throw Error('Stored channel selection differs from the native clip.');
   seen.add(edit.frame_index+':'+edit.object_index);let axes=0;
   for(const field of ['translation','rotation_psx'])if(Object.hasOwn(edit,field)){
    const values=edit[field];if(!values||typeof values!=='object'||Array.isArray(values)||!Object.keys(values).length||Object.keys(values).some(k=>!['x','y','z'].includes(k)))throw Error('Stored channel axes are invalid.');
    for(const [axis,value] of Object.entries(values)){
     if(field==='translation'?!integer(value,-2048,2047):!integer(value,0,4080)||value%16)throw Error('Stored channel value exceeds native encoding.');
     if(++count>65536)throw Error('Stored contribution axis budget exceeded.');axes++;
     const key=JSON.stringify([edit.frame_index,edit.object_index,field,axis]);let cell=cells.get(key);if(!cell){cell={frame_index:edit.frame_index,object_index:edit.object_index,field,axis,values:new Map()};cells.set(key,cell);}let ids=cell.values.get(value);if(!ids){ids=[];cell.values.set(value,ids);}ids.push(entity.id);
    }
   }
   if(!axes)throw Error('Stored channel edit has no axes.');
  }
 }
 const rows=[...cells.values()].sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index||a.field.localeCompare(b.field)||a.axis.localeCompare(b.axis)).map(cell=>({...cell,values:[...cell.values].sort((a,b)=>a[0]-b[0]).map(([value,ids])=>({value,owners:ids.sort()})),conflict:cell.values.size>1}));
 return {asset_id:record.id,source_record_sha256:hash,owners:[...owners].sort(),axis_count:rows.length,contribution_count:count,conflict_count:rows.filter(row=>row.conflict).length,rows};
}

export function mountAnimationContributions(host,{record,getContext,current,busy,onSelect,onError}){
 const doc=host.ownerDocument,button=doc.createElement('button');button.type='button';button.textContent='Inspect stored channel contributions…';host.append(button);let disposed=false,dialog=null,timer=null,generation=0;
 const snapshot=()=>{if(disposed||busy()||!current())return null;const c=getContext();if(!c)return null;const report=inspectAnimationContributions(record,c.entities,c.sceneId);return {report,key:JSON.stringify([c.projectPath,c.sceneId,c.sourceKey,report])};};
 function close(){generation++;clearInterval(timer);timer=null;dialog?.remove();dialog=null;}
 function synchronize(){button.disabled=true;try{button.disabled=!snapshot();}catch(error){button.title=error.message;}}
 button.onclick=()=>{if(button.disabled||dialog)return;try{
  const held=snapshot();if(!held)return;const token=++generation;dialog=doc.createElement('dialog');dialog.id='animation-contributions-dialog';Object.assign(dialog.style,{width:'min(800px,calc(100vw - 32px))',maxWidth:'calc(100vw - 32px)',maxHeight:'calc(100vh - 32px)',overflow:'auto'});
  const el=(tag,text)=>{const n=doc.createElement(tag);if(text!==undefined)n.textContent=text;return n;},heading=el('h2','Stored animation channel contributions'),status=el('p'),note=el('p','Stored authored axes only. Equal values share a channel; conflicting values require resolution through existing authoring validation. This is not a native byte, playback or runtime assignment report.'),back=el('button','Previous contributions'),next=el('button','Next contributions'),label=el('span'),results=el('div'),done=el('button','Close contributions');const entries=held.report.rows.flatMap(cell=>cell.values.flatMap(group=>group.owners.map(owner=>({cell,value:group.value,owner}))));let page=0,working=false;
  const fresh=()=>{try{return !!dialog&&token===generation&&snapshot()?.key===held.key;}catch{return false;}};
  const render=()=>{results.replaceChildren();const r=held.report;status.textContent=`${r.owners.length} owners · ${r.axis_count} axes · ${r.contribution_count} contributions · ${r.conflict_count} conflicting axes`;label.textContent=`Page ${page+1} / ${Math.max(1,Math.ceil(entries.length/128))}`;back.disabled=page===0;next.disabled=(page+1)*128>=entries.length;
   for(const {cell,value,owner} of entries.slice(page*128,(page+1)*128)){const section=el('section');section.append(el('h3',`Frame ${cell.frame_index}, object ${cell.object_index} · ${cell.field}.${cell.axis}${cell.conflict?' · conflict':''}`),el('p','Stored value: '+value));const choose=el('button','Inspect contributor '+owner.split('/').at(-1));choose.title=owner;choose.onclick=async()=>{if(working||!fresh())return;working=true;dialog.querySelectorAll('button').forEach(b=>b.disabled=b!==done);try{if(await onSelect(owner,fresh)&&fresh())close();}catch(error){if(dialog&&token===generation)onError(error);}finally{working=false;if(dialog&&token===generation){if(fresh())render();else{status.textContent='Source or stored contributions changed. Close and inspect again.';dialog.querySelectorAll('button').forEach(b=>b.disabled=b!==done);}}}};section.append(choose);results.append(section);}

  };back.onclick=()=>{if(fresh()&&!working){page--;render();}};next.onclick=()=>{if(fresh()&&!working){page++;render();}};done.onclick=close;dialog.addEventListener('close',()=>{if(token===generation)close();},{once:true});dialog.append(heading,note,status,back,next,label,results,done);doc.body.append(dialog);render();dialog.showModal();timer=setInterval(()=>{if(dialog&&!busy()&&!fresh()){status.textContent='Source or stored contributions changed. Close and inspect again.';dialog.querySelectorAll('button').forEach(b=>b.disabled=b!==done);}},300);
 }catch(error){onError(error);}};
 synchronize();return {synchronize,dispose(){disposed=true;close();button.disabled=true;}};
}
