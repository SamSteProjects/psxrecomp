import assert from 'node:assert/strict';
import {focusScriptInspectorFamily,scriptInspectorFamilies,mountScriptFamilyNavigation} from '../editor/script-inspector-navigation.js';
for(const [id,selector] of [['ScriptMovement','.movement-authoring'],['ScriptFlags','.flag-authoring'],['ScriptWaits','.wait-authoring'],['ScriptModelSelectors','.modelSelector-authoring'],['ScriptFacing','.facing-authoring'],['ScriptBranches','.script-branch-authoring'],['Dialogue','.dialogue-authoring-note'],['Transitions','.transition-authoring']]){
  const calls=[],section={scrollIntoView:options=>calls.push(['scroll',options]),focus:options=>calls.push(['focus',options])};
  assert.equal(focusScriptInspectorFamily({querySelector:value=>{assert.equal(value,selector);return section;}},id),true);assert.equal(section.tabIndex,-1);assert.deepEqual(calls,[['scroll',{block:'start'}],['focus',{preventScroll:true}]]);
}
for(const id of ['Unknown','__proto__','constructor','ScriptWaits input',null,{}])assert.equal(focusScriptInspectorFamily({querySelector:()=>{throw new Error('Unexpected selector');}},id),false);
assert.equal(focusScriptInspectorFamily({querySelector:()=>null},'ScriptWaits'),false);assert.equal(focusScriptInspectorFamily(null,'ScriptWaits'),false);
console.log('Script Inspector family focus is bounded to registered UI sections and rejects missing/unknown targets.');
assert.deepEqual(scriptInspectorFamilies(null),[]);
const selectors=new Set(['.flag-authoring','.transition-authoring']);
assert.deepEqual(scriptInspectorFamilies({querySelector:s=>selectors.has(s)}),[{id:'Transitions',label:'Transitions'},{id:'ScriptFlags',label:'Flags'}]);
const calls=[],nodes=[];let stale=false,working=false;
const section={scrollIntoView:()=>calls.push('scroll'),focus:()=>calls.push('focus')};
const root={querySelector:s=>s==='.flag-authoring'?section:null,ownerDocument:{createElement:tag=>{const node={tag,children:[],dataset:{},setAttribute(){},append(n){this.children.push(n);}};nodes.push(node);return node;}},prepend:n=>calls.push(n)};
const nav=mountScriptFamilyNavigation(root,{current:()=>!stale,busy:()=>working});assert.equal(nav.children.length,2);const button=nav.children[1];assert.equal(button.dataset.scriptFamily,'ScriptFlags');calls.length=0;assert.equal(button.onclick(),true);assert.deepEqual(calls,['scroll','focus']);working=true;calls.length=0;assert.equal(button.onclick(),false);stale=true;working=false;assert.equal(button.onclick(),false);assert.deepEqual(calls,[]);
assert.throws(()=>mountScriptFamilyNavigation(root,{}));assert.equal(mountScriptFamilyNavigation({querySelector:()=>null},{current:()=>true,busy:()=>false}),null);
console.log('Script family links reflect existing sections and reject busy or stale inspection actions.');
