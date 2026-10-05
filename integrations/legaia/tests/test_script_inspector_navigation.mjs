import assert from 'node:assert/strict';
import {focusScriptInspectorFamily} from '../editor/script-inspector-navigation.js';
for(const [id,selector] of [['ScriptMovement','.movement-authoring'],['ScriptFlags','.flag-authoring'],['ScriptWaits','.wait-authoring'],['ScriptModelSelectors','.modelSelector-authoring'],['ScriptFacing','.facing-authoring'],['ScriptBranches','.script-branch-authoring']]){
  const calls=[],section={scrollIntoView:options=>calls.push(['scroll',options]),focus:options=>calls.push(['focus',options])};
  assert.equal(focusScriptInspectorFamily({querySelector:value=>{assert.equal(value,selector);return section;}},id),true);assert.equal(section.tabIndex,-1);assert.deepEqual(calls,[['scroll',{block:'start'}],['focus',{preventScroll:true}]]);
}
for(const id of ['Dialogue','__proto__','constructor','ScriptWaits input',null,{}])assert.equal(focusScriptInspectorFamily({querySelector:()=>{throw new Error('Unexpected selector');}},id),false);
assert.equal(focusScriptInspectorFamily({querySelector:()=>null},'ScriptWaits'),false);assert.equal(focusScriptInspectorFamily(null,'ScriptWaits'),false);
console.log('Script Inspector family focus is bounded to registered UI sections and rejects missing/unknown targets.');
