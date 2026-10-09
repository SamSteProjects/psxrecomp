import assert from 'node:assert/strict';
import {controllerAuthoringFocus} from '../editor/controller-authoring-focus.js';
let fresh=true,busy=false,selected=[],scrolls=0,focuses=0;
const source={value:'one',scrollIntoView(options){assert.equal(options.block,'center');scrolls++;},focus(options){assert.equal(options.preventScroll,true);focuses++;}},targets=[{pc:5,semantic_id:'one'},{pc:39,semantic_id:'two'}];
const control=controllerAuthoringFocus({current:()=>fresh,busy:()=>busy,targets:()=>targets,source,select:t=>{selected.push(t.semantic_id);source.value=t.semantic_id;}});
assert(control.canFocus(5));assert(control.focusPc(5));assert.deepEqual(selected,[]);assert.equal(scrolls,1);assert.equal(focuses,1);
assert(control.focusPc(39));assert.equal(source.value,'two');assert.deepEqual(selected,['two']);
for(const pc of [-1,65536,5.5,'5',null,6]){assert.equal(control.canFocus(pc),false);assert.equal(control.focusPc(pc),false);}
busy=true;assert.equal(control.focusPc(5),false);busy=false;fresh=false;assert.equal(control.canFocus(5),false);assert.equal(control.focusPc(5),false);
assert.deepEqual(selected,['two']);assert.equal(scrolls,2);assert.equal(focuses,2);
console.log('Qualified controller navigation preserves same-source drafts and refuses missing, malformed, busy and stale targets.');
