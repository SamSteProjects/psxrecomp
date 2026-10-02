import {componentDefinition,renderComponentProperties,renderComponentActions,bindComponentActions} from './component-inspector.js';
export function projectNameCommand(schema,settings,value){
  const definition=componentDefinition(schema,'ProjectSettings'),property=definition.properties.find(row=>row.id==='name'),bounds=property?.authoring;
  if(property?.type!=='string'||bounds?.set_command!=='rename_project'||bounds.minimum_length!==1||bounds.maximum_length!==120||typeof settings?.review_key!=='string'||!/^[0-9a-f]{64}$/.test(settings.review_key))throw new Error('Unsupported project name contract.');
  if(typeof value!=='string'||/[\x00-\x1f\x7f\ud800-\udfff]/u.test(value)||Array.from(value.trim()).length<1||Array.from(value.trim()).length>120)throw new Error('Project name requires 1–120 valid Unicode characters without controls.');
  return {type:'rename_project',name:value.trim(),review_key:settings.review_key};
}
export function mountProjectSettings({after,getState,busy,api,onError}){
  const button=document.createElement('button');button.id='project-settings-button';button.textContent='Settings…';button.disabled=true;after.after(button);
  button.onclick=()=>{
    const state=getState();if(busy()||!state?.capabilities?.project_settings)return;
    const settings=structuredClone(state.project_settings),schema=state.inspector_schema,key=JSON.stringify([settings,schema,state.capabilities.project_settings]),dialog=document.createElement('dialog');dialog.id='project-settings-dialog';dialog.className='project-dialog';
    const current=()=>dialog.open&&key===JSON.stringify([getState().project_settings,getState().inspector_schema,getState().capabilities?.project_settings]),editable=()=>getState().project?.mode==='edit';
    const title=document.createElement('h2');title.textContent=componentDefinition(schema,'ProjectSettings').label;const properties=document.createElement('div');properties.innerHTML=renderComponentProperties(schema,'ProjectSettings',settings);
    const form=document.createElement('form');form.hidden=true;const label=document.createElement('label');label.textContent='New project name';const input=document.createElement('input');input.required=true;input.value=settings.name;input.maxLength=240;input.setAttribute('aria-label','New project name');label.append(input);const submit=document.createElement('button');submit.type='submit';submit.textContent='Apply project name';form.append(label,submit);
    const actions=document.createElement('div'),error=document.createElement('p');error.className='dialog-error';error.setAttribute('role','alert');const registry={'rename-project':{requiresEdit:true,run:()=>{form.hidden=false;input.focus();}}};actions.innerHTML=renderComponentActions(schema,'ProjectSettings',settings,state.capabilities,registry,editable());
    bindComponentActions(actions,registry,{current,editable,busy,onError:exc=>error.textContent=exc.message});
    form.onsubmit=async event=>{event.preventDefault();if(busy())return;if(!current()||!editable()){error.textContent='Project settings changed. Reopen Settings.';return;}try{const command=projectNameCommand(schema,settings,input.value);if(await api('/api/command',command))dialog.close();else error.textContent='Project rename failed. Reopen Settings to inspect the current name.';}catch(exc){error.textContent=exc.message;}};
    const close=document.createElement('button');close.type='button';close.textContent='Close';close.onclick=()=>dialog.close();dialog.addEventListener('close',()=>dialog.remove());dialog.append(title,properties,actions,form,error,close);document.body.append(dialog);dialog.showModal();
  };
}
