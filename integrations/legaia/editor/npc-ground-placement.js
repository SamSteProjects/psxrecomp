// Native X/Z are taken from a qualified source-heightfield vertex, not display axes.
export function npcGroundPlacement(document,hit,sceneId){
  if(typeof sceneId!=='string'||!sceneId.startsWith('scene://'))throw Error('NPC ground placement requires the active source scene.');
  const ground=`environment://${sceneId.replace('scene://','')}/field-map/ground`;
  const entity=document?.entities?.find(row=>row.entity_id===hit?.entity_id&&row.geometry_key===hit?.geometry_key&&row.renderable);
  const asset=document?.assets?.find(row=>row.geometry_key===entity?.geometry_key&&row.asset_id===ground);
  const vertex=asset?.preview?.vertices?.[hit?.vertex_index];
  if(document?.scene_id!==sceneId||!entity||entity.asset_id!==ground||entity.pose_kind!=='source_heightfield'||hit?.asset_id!==ground||!Number.isSafeInteger(hit.vertex_index)||hit.vertex_index<0||!Array.isArray(vertex)||vertex.length!==3||!vertex.every(Number.isFinite)||JSON.stringify(vertex)!==JSON.stringify(hit.decoded_model_position))throw Error('Choose a visible source-ground corner; actor and scenery vertices cannot place an NPC.');
  const position={x:vertex[0],z:vertex[2]};
  if(Object.values(position).some(value=>!Number.isInteger(value)||value<64||value>16384||value%64!==0))throw Error('This ground corner is outside the supported native NPC X/Z grid.');
  return {position,source:{entity_id:entity.entity_id,geometry_key:entity.geometry_key,vertex_index:hit.vertex_index},height:'not_authored'};
}
export function mountNpcGroundPlacement({after,getKey,available,getDocument,getSceneId,pickVertex,onError,onChange=()=>{}}){
  const toolbar=document.createElement('div');toolbar.hidden=true;toolbar.className='scene-placement-tools';toolbar.innerHTML='<p role="status">Choose a visible source-ground corner within 24 pixels. Drag to orbit; right-drag to pan. Only X/Z will be copied into the creation form.</p><button type="button">Return to NPC creation</button>';Object.assign(toolbar.style,{padding:'8px 12px',flexShrink:'0',borderBottom:'1px solid #2b3539'});after.after(toolbar);
  let session=null;
  const finish=result=>{if(!session)return;const active=session;session=null;toolbar.hidden=true;onChange();clearInterval(active.timer);active.resume(result);};
  const fresh=()=>!!session&&available()&&session.current()&&session.key===getKey();
  toolbar.querySelector('button').onclick=()=>finish(null);
  document.addEventListener('keydown',event=>{if(session&&event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();finish(null);}},true);
  return {
    bar:toolbar,
    begin(resume,{current=()=>true,returnLabel="Return to NPC creation",note="Choose a visible source-ground corner within 24 pixels. Drag to orbit; right-drag to pan. Only X/Z will be copied into the creation form."}={}){if(session||!available()||!current())throw Error('Use the current Authored scene with models enabled and other scene tools closed.');toolbar.querySelector('button').textContent=returnLabel;toolbar.querySelector('p').textContent=note;session={key:getKey(),resume,current,timer:null};session.timer=setInterval(()=>{if(!fresh()){onError(Error('Ground placement source changed. Reopen against the current Project.'));finish(null);}},250);toolbar.hidden=false;onChange();},
    active:()=>!!session,
    key:()=>session?.key,
    pick(point,key){if(!fresh()||key!==session.key){finish(null);return;}try{const hit=pickVertex(point);if(!hit)throw Error('Click within 24 pixels of a visible source-ground corner.');const result=npcGroundPlacement(getDocument(),hit,getSceneId());finish(result);}catch(error){onError(error);}},
    cancel:()=>finish(null),
  };
}
