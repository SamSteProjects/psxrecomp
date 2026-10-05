import assert from 'node:assert/strict';
import {matchesInspectorComponent} from '../editor/inspector-component-filter.js';
const row={id:'ScriptWaits',label:'Authored script waits',text:'Retail 16, authored 17'},authored=['ScriptWaits'];
assert(matchesInspectorComponent(row,{query:' SCRIPTWAITS ',authoredOnly:true},authored));assert(matchesInspectorComponent(row,{query:'17'},[]));assert(matchesInspectorComponent(row,{query:'SCRIPT WAITS'},[]));assert(!matchesInspectorComponent(row,{query:'unrelated'},authored));assert(!matchesInspectorComponent(row,{query:'',authoredOnly:true},[]));assert(matchesInspectorComponent(row,{query:''},[]));
assert(!matchesInspectorComponent({id:'RuntimeCorrelation',label:'Authored candidate',text:'ScriptWaits'}, {authoredOnly:true},authored));assert.throws(()=>matchesInspectorComponent(row,{},[null]));assert.throws(()=>matchesInspectorComponent(row,{},Array(129).fill('ScriptWaits')));
assert.deepEqual(row,{id:'ScriptWaits',label:'Authored script waits',text:'Retail 16, authored 17'});assert.deepEqual(authored,['ScriptWaits']);
console.log('Inspector search and authored-only filtering use explicit identities and leave displayed/source records unchanged.');

const categories={id:'Transform',label:'Transform',text:'X 192; Y unknown',propertyCategories:['Retail','Authored','Effective','Unresolved','Unsupported']};
assert(matchesInspectorComponent(categories,{propertyCategory:'Unresolved'},[]));assert(matchesInspectorComponent(categories,{propertyCategory:'Authored',authoredOnly:true},['Transform']));
assert(!matchesInspectorComponent(categories,{propertyCategory:'Authored',authoredOnly:true},[]));assert(!matchesInspectorComponent(categories,{propertyCategory:'Derived'},[]));assert(!matchesInspectorComponent(categories,{propertyCategory:'Unresolved',query:'model'},[]));assert(matchesInspectorComponent(categories,{propertyCategory:'Unsupported',query:'192'},[]));
assert(!matchesInspectorComponent(row,{propertyCategory:'Authored'},authored));assert(matchesInspectorComponent(row,{propertyCategory:''},authored));
assert.deepEqual(categories.propertyCategories,['Retail','Authored','Effective','Unresolved','Unsupported']);
console.log('Property-category filtering composes with search and exact authored identities; declared Authored categories do not imply overrides.');
