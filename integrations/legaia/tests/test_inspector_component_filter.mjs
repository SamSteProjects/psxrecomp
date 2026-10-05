import assert from 'node:assert/strict';
import {matchesInspectorComponent} from '../editor/inspector-component-filter.js';
const row={id:'ScriptWaits',label:'Authored script waits',text:'Retail 16, authored 17'},authored=['ScriptWaits'];
assert(matchesInspectorComponent(row,{query:' SCRIPTWAITS ',authoredOnly:true},authored));assert(matchesInspectorComponent(row,{query:'17'},[]));assert(matchesInspectorComponent(row,{query:'SCRIPT WAITS'},[]));assert(!matchesInspectorComponent(row,{query:'unrelated'},authored));assert(!matchesInspectorComponent(row,{query:'',authoredOnly:true},[]));assert(matchesInspectorComponent(row,{query:''},[]));
assert(!matchesInspectorComponent({id:'RuntimeCorrelation',label:'Authored candidate',text:'ScriptWaits'}, {authoredOnly:true},authored));assert.throws(()=>matchesInspectorComponent(row,{},[null]));assert.throws(()=>matchesInspectorComponent(row,{},Array(129).fill('ScriptWaits')));
assert.deepEqual(row,{id:'ScriptWaits',label:'Authored script waits',text:'Retail 16, authored 17'});assert.deepEqual(authored,['ScriptWaits']);
console.log('Inspector search and authored-only filtering use explicit identities and leave displayed/source records unchanged.');
