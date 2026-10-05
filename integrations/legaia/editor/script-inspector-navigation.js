// Component identities select UI sections, never decode source records or infer execution.
const sections=Object.freeze({ScriptMovement:'movement-authoring',ScriptFlags:'flag-authoring',ScriptWaits:'wait-authoring',ScriptModelSelectors:'modelSelector-authoring',ScriptFacing:'facing-authoring',ScriptBranches:'script-branch-authoring',Dialogue:'dialogue-authoring-note',Transitions:'transition-authoring'});
export function focusScriptInspectorFamily(root,componentId){
  if(typeof componentId!=='string'||!Object.hasOwn(sections,componentId)||typeof root?.querySelector!=='function')return false;
  const section=root.querySelector('.'+sections[componentId]);if(!section)return false;
  section.tabIndex=-1;section.scrollIntoView({block:'start'});section.focus({preventScroll:true});return true;
}
