import {navigableComponentReference} from './component-inspector.js';

// Navigation resolves catalog records, never decodes an ID into a file or guest address.
export function resolveComponentReference(records,id,type){
  if(!navigableComponentReference(id,type)||!Array.isArray(records))throw new Error('Unsupported component reference.');
  const matches=records.filter(row=>row?.id===id&&(type!=='entity-reference'||row.type==='actor'));
  if(matches.length>1)throw new Error('Component reference is ambiguous in this source scene.');
  return matches[0]??null;
}

export function bindComponentReferences(root,{current,busy,records,discover,open,onError}){
  for(const button of root.querySelectorAll('[data-component-reference]')){
    const id=button.dataset.componentReference,type=button.dataset.referenceType;
    let pending=false;
    button.onclick=async()=>{
      if(pending||busy()||!current()||!navigableComponentReference(id,type))return;
      pending=true;button.disabled=true;
      try{
        let record=resolveComponentReference(records(),id,type);
        if(!record){await discover();if(!current()||busy())return;record=resolveComponentReference(records(),id,type);}
        if(!current()||busy())return;
        if(!record)throw new Error('Referenced asset is unavailable in the active source scene.');
        await open(record);
      }catch(error){if(current())onError(error);}finally{pending=false;if(current())button.disabled=false;}
    };
  }
}
