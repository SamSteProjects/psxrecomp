import assert from 'node:assert/strict';
import {glbAnimationChoices,populateGlbClipSelect,selectedGlbClipIndex} from '../editor/animation-glb-clips.js';
function glb(doc){const raw=JSON.stringify(doc),json=new TextEncoder().encode(raw+' '.repeat((4-raw.length%4)%4)),bytes=new Uint8Array(28+json.length),view=new DataView(bytes.buffer);view.setUint32(0,0x46546c67,true);view.setUint32(4,2,true);view.setUint32(8,bytes.length,true);view.setUint32(12,json.length,true);view.setUint32(16,0x4e4f534a,true);bytes.set(json,20);view.setUint32(24+json.length,0x004e4942,true);return bytes;}
assert.deepEqual(glbAnimationChoices(glb({})),[]);
const choices=glbAnimationChoices(glb({animations:[{name:'Idle'},{name:'<Wave>\npose'},{}]}));
assert.deepEqual(choices,[{index:0,label:'0 · Idle'},{index:1,label:'1 · <Wave> pose'},{index:2,label:'2 · Unnamed clip'}]);
for(const value of [{animations:Array(65).fill({})},{animations:[null]},{animations:[{name:7}]},{animations:{}}])assert.throws(()=>glbAnimationChoices(glb(value)));
const bad=glb({});new DataView(bad.buffer).setUint32(8,1,true);assert.throws(()=>glbAnimationChoices(bad));
const previous=globalThis.document;globalThis.document={createElement:()=>({})};
try{const select={children:[],value:'',append(node){this.children.push(node);},replaceChildren(){this.children=[];}};populateGlbClipSelect(select,choices);assert.equal(select.children.length,4);assert.throws(()=>selectedGlbClipIndex(select,choices));select.value='1';assert.equal(selectedGlbClipIndex(select,choices),1);select.value='99';assert.throws(()=>selectedGlbClipIndex(select,choices));populateGlbClipSelect(select,choices.slice(0,1));assert.equal(selectedGlbClipIndex(select,choices.slice(0,1)),null);populateGlbClipSelect(select,[]);assert.equal(select.children[0].textContent,'Static node transforms · no animation');}
finally{globalThis.document=previous;}
console.log('GLB named clip metadata, bounded catalog, safe text and explicit selection checks passed.');
