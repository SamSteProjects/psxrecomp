import {renderComponentProperties,renderComponentDetails,renderComponentActions,bindComponentActions} from './component-inspector.js';
import {focusScriptInspectorFamily} from './script-inspector-navigation.js';
import {openScriptComponentReset} from './script-component-reset.js';

const families=['Dialogue','Transitions','ScriptMovement','ScriptFlags','ScriptWaits','ScriptModelSelectors','ScriptFacing','ScriptBranches'];
export function scriptOwnerComponents(record,sceneId){
  if(record?.kind!=='script'||typeof record.id!=='string'||!/^scene:\/\/[A-Za-z0-9_-]{1,128}\/scripts\/man-p2\/[0-9]{4}$/.test(record.id)||record.scene_id!==sceneId||!record.id.startsWith(sceneId+'/scripts/man-p2/'))throw new Error('Choose a source script owner in the active scene');
  const components={};
  for(const family of families){
    const value=record.authored?.[family],field=family==='Dialogue'?'runs':'entries',entries=value?.[field];
    if(entries===undefined)continue;
    if(!entries||typeof entries!=='object'||Array.isArray(entries)||Object.keys(entries).length>1024)throw new Error('Invalid authored script component collection');
    const count=Object.keys(entries).length;if(!count)continue;
    const copy=JSON.parse(JSON.stringify(entries));
    components[family]=family==='Dialogue'?{authored:{runs:copy},authored_run_count:count}:{entries:copy,authored_instruction_count:count};
  }
  return components;
}

export function mountScriptOwnerInspector(host,{owner,getState,current,editable,busy,api,onReset,onError}){
  const state=getState(),record=state.authored_assets?.find(row=>row.id===owner);
  const section=document.createElement('section');section.className='script-owner-inspector';
  const heading=document.createElement('h3');heading.textContent='Authored script components';section.append(heading);
  const components=record?scriptOwnerComponents(record,state.scene?.id):{};
  if(!Object.keys(components).length){const note=document.createElement('p');note.className='field-note';note.textContent='This source owner has no authored script components. Supported source editors below retain their separate retail and effective values.';section.append(note);}
  const entity={id:owner,components},actions={
    'inspect-script':{run:({componentId})=>focusScriptInspectorFamily(host,componentId)},
    'reset-script-component':{requiresEdit:true,run:({componentId})=>openScriptComponentReset({entity,component:componentId,getState,current,editable,busy,api,onReset,onError})}
  };
  for(const [id,value] of Object.entries(components)){
    const part=document.createElement('section');part.className='component';const title=document.createElement('h4');title.textContent=state.inspector_schema.components[id].label;part.append(title);
    const content=document.createElement('div');content.innerHTML=renderComponentProperties(state.inspector_schema,id,value,false,true)+renderComponentActions(state.inspector_schema,id,value,state.capabilities,actions,editable())+renderComponentDetails(state.inspector_schema,id,value);part.append(content);section.append(part);
  }
  host.prepend(section);bindComponentActions(section,actions,{current,editable,busy,onError});return section;
}
