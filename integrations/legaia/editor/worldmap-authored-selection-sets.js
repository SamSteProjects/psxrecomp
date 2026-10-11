import {qualifyScriptedWorldSelectionReview} from './worldmap-scripted-selection-state.js';
import {qualifyAuthoredWorldSelectionReview} from './worldmap-authored-selection-state.js';
const node=(tag,text)=>{const e=document.createElement(tag);if(text)e.textContent=text;return e;};
export function mountAuthoredWorldSelectionSets({host,getState,getSource,getIds,current,busy,api,recall,onError,request=fetch,scripted=false}){
  const panel=node('details'),summary=node('summary'),select=node('select'),name=node('input'),tools=node('div'),status=node('p'),buttons={};
  const domain=scripted?'scripted':'authored',metadata=()=>scripted?getSource():getSource()?.metadata;
  if(scripted)panel.dataset.worldScriptedGroups='';else panel.dataset.worldAuthoredGroups='';select.setAttribute('aria-label',scripted?'Saved scripted group':'Saved authored decoration group');name.setAttribute('aria-label',scripted?'Scripted group name':'Authored decoration group name');name.maxLength=80;name.placeholder='Group name';
  for(const input of [select,name])Object.assign(input.style,{display:'block',width:'100%',maxWidth:'100%',minWidth:'0',boxSizing:'border-box'});
  tools.className='dialog-actions';Object.assign(tools.style,{flexWrap:'wrap',justifyContent:'flex-start'});status.setAttribute('role','status');
  for(const [key,label] of [['create','Save authored group'],['update','Replace authored group members'],['rename','Rename authored group'],['recall','Recall authored group'],['delete','Delete authored group']]){const button=node('button',scripted?label.replace('authored','scripted'):label);button.type='button';buttons[key]=button;tools.append(button);}
  panel.append(summary,node('p',scripted?'Groups retain saved scripted UUID, native record and shared script identities. Recall clears deltas and selects Current members. Removed or mismatched owners refuse.': 'Inspect Current decoration donors first. Groups save UUID membership, not transforms or camera views. Recall clears relative delta drafts and selects the retained decorations at their current positions. Moved or reassigned members remain in the group; deleted members refuse recall.'),select,name,tools,status);host.append(panel);
  let pending=false,generation=0,controller=null,signature=null;
  const rows=()=> (getState().worldmap_selection_sets??[]).filter(row=>row.schema_version===`legaia.worldmap-${domain}-selection.v1`&&row.scene===metadata()?.scene);
  const chosen=()=>rows().find(row=>row.id===select.value);
  const scope=()=>JSON.stringify([getState().project?.path,metadata()?.source_key,metadata()?.scene,getIds().slice().sort()]);
  const usable=()=>panel.isConnected&&current()&&!busy();
  function update(){
    const saved=rows(),key=JSON.stringify(saved),old=select.value;
    if(signature!==key){signature=key;select.replaceChildren();for(const row of saved){const option=node('option',`${row.name} · ${row.placement_ids.length} ${scripted?'scripted objects':'decorations'}`);option.value=row.id;select.append(option);}if(saved.some(row=>row.id===old))select.value=old;}
    summary.textContent=`Saved ${scripted?'Scripted':'Authored Decoration'} Groups (${saved.length})`;
    const locked=pending||!usable(),row=chosen(),ids=getIds();select.disabled=name.disabled=locked;
    const valid=ids.length>0&&ids.length<=32&&new Set(ids).size===ids.length;
    buttons.create.disabled=locked||!valid||!name.value.trim()||(getState().worldmap_selection_sets??[]).length>=128;
    buttons.update.disabled=locked||!row||!valid;buttons.rename.disabled=locked||!row||!name.value.trim();buttons.delete.disabled=buttons.recall.disabled=locked||!row;
  }
  async function command(kind){
    update();if(buttons[kind].disabled||!usable())return;
    const saved=chosen(),source=getSource(),token=++generation,beforeIds=new Set(rows().map(r=>r.id)),ids=getIds().slice().sort();
    const body=kind==='create'?{type:`create_worldmap_${domain}_selection_set`,scene:(scripted?source:source.metadata).scene,source_key:(scripted?source:source.metadata).source_key,placement_ids:ids,name:name.value}:
      {type:kind==='update'?`update_worldmap_${domain}_selection_set`:kind+'_worldmap_selection_set',selection_set_id:saved.id,review_key:saved.review_key,
        ...(kind==='rename'?{name:name.value}:kind==='update'?{source_key:(scripted?source:source.metadata).source_key,placement_ids:ids}:{})};
    pending=true;update();
    try{if(await api('/api/command',body)!==true)throw Error('Authored group metadata command failed. Refresh before retrying.');
      if(token!==generation)return;update();if(kind==='create'){const added=rows().find(r=>!beforeIds.has(r.id));if(added)select.value=added.id;}
      status.textContent='Authored group metadata updated; native scene unchanged.';
    }catch(error){if(token===generation){status.textContent=error.message;onError(error);}}
    finally{pending=false;update();}
  }
  for(const kind of ['create','update','rename','delete'])buttons[kind].onclick=()=>command(kind);
  buttons.recall.onclick=async()=>{
    update();if(buttons.recall.disabled||!usable())return;
    const saved=structuredClone(chosen()),source=getSource(),captured=scope(),token=++generation,active=new AbortController();controller?.abort();controller=active;pending=true;update();
    status.textContent='Checking saved authored group ownership…';
    const valid=()=>token===generation&&!active.signal.aborted&&usable()&&source===getSource()&&scope()===captured&&chosen()?.review_key===saved.review_key&&chosen()?.id===saved.id;
    const fresh=()=>{if(valid())return true;if(token===generation&&!active.signal.aborted&&current())status.textContent='Recall canceled because the group, source or active selection changed.';return false;};
    try{
      const response=await request('/api/worldmap-selection-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({selection_set_id:saved.id,review_key:saved.review_key,source_key:(scripted?source:source.metadata).source_key}),signal:active.signal});
      const text=await response.text();if(!fresh())return;if(new TextEncoder().encode(text).length>128*1024)throw Error('Authored group Review exceeds its metadata budget.');
      const value=JSON.parse(text);if(!response.ok)throw Error(value.error||'Authored group recall failed.');
      const ids=await (scripted?qualifyScriptedWorldSelectionReview:qualifyAuthoredWorldSelectionReview)(value,saved,source);if(!fresh())return;
      recall(ids);status.textContent=`Recalled ${ids.length} ${scripted?'scripted objects':'authored decorations'}; native transforms unchanged.`;
    }catch(error){if(valid()&&error.name!=='AbortError'){status.textContent=error.message;onError(error);}}
    finally{if(controller===active)controller=null;pending=false;update();}
  };
  select.onchange=()=>{name.value=chosen()?.name??'';update();};name.oninput=update;
  update();return {update,cancel:()=>{generation++;controller?.abort();controller=null;update();}};
}
