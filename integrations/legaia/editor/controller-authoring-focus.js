// Navigation uses qualified editor targets; it never decodes bytes or authors commands.
export function controllerAuthoringFocus({current,busy,targets,source,select}){
 const target=pc=>Number.isSafeInteger(pc)&&pc>=0&&pc<=65535&&current()&&!busy()?(targets()??[]).find(t=>t.pc===pc):null;
 return {canFocus:pc=>!!target(pc),focusPc(pc){const row=target(pc);if(!row)return false;
  if(source.value!==row.semantic_id)select(row);
  source.scrollIntoView?.({block:'center'});source.focus?.({preventScroll:true});return true;
 }};
}
