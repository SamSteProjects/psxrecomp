// Component identities select UI sections, never decode source records or infer execution.
const sections=Object.freeze({ScriptMovement:'movement-authoring',ScriptFlags:'flag-authoring',ScriptSystemFlags:'system-selector-authoring',ScriptWaits:'wait-authoring',ScriptAnimationOperands:'animation-operands-authoring',ScriptEffectColors:'effectColor-authoring',ScriptModelSelectors:'modelSelector-authoring',ScriptFacing:'facing-authoring',ScriptBranches:'script-branch-authoring',Dialogue:'dialogue-authoring-note',Transitions:'transition-authoring'});
const labels=Object.freeze({Dialogue:'Dialogue',Transitions:'Transitions',ScriptMovement:'Movement',ScriptFlags:'Flags',ScriptSystemFlags:'System selectors',ScriptWaits:'Waits',ScriptAnimationOperands:'Animation Arguments',ScriptEffectColors:'Effect colors',ScriptModelSelectors:'Model selectors',ScriptFacing:'Facing',ScriptBranches:'Branches'});
export function scriptInspectorFamilies(root){
  if(typeof root?.querySelector!=='function')return [];
  return Object.entries(labels).filter(([id])=>root.querySelector('.'+sections[id])).map(([id,label])=>({id,label}));
}
// Links reflect existing SDK tool sections, not a second source decoder or authored component list.
export function mountScriptFamilyNavigation(root,{current,busy}){
  if(typeof current!=='function'||typeof busy!=='function')throw new Error('Script navigation requires lifecycle guards');
  const families=scriptInspectorFamilies(root);if(!families.length)return null;
  const nav=root.ownerDocument.createElement('nav');nav.className='script-family-navigation';nav.setAttribute('aria-label','Inspect script families');
  const label=root.ownerDocument.createElement('span');label.textContent='Inspect script families';nav.append(label);
  for(const {id,label} of families){
    const button=root.ownerDocument.createElement('button');button.type='button';button.textContent=label;button.dataset.scriptFamily=id;button.disabled=Boolean(busy());
    button.onclick=()=>{if(!current()||busy())return false;return focusScriptInspectorFamily(root,id);};nav.append(button);
  }
  root.prepend(nav);return nav;
}
export function focusScriptInspectorFamily(root,componentId){
  if(typeof componentId!=='string'||!Object.hasOwn(sections,componentId)||typeof root?.querySelector!=='function')return false;
  const section=root.querySelector('.'+sections[componentId]);if(!section)return false;
  section.tabIndex=-1;section.scrollIntoView({block:'start'});section.focus({preventScroll:true});return true;
}
