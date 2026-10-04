import assert from 'node:assert/strict';
import {decodeResizeSource,decodeResizeReview,openTextureResizeEditor} from '../editor/texture-resize.js';
const hash=c=>c.repeat(64),asset='texture://fixture/1/raw/0',context={projectPath:'C:/private/resize',sceneId:'scene://fixture',mode:'edit',sourceKey:hash('f')};
const current={bpp:4,x:0,y:0,width:4,height:1,width_words:1};
const source={schema_version:'legaia.texture-resize-source.v1',asset_id:asset,project_source_key:context.sourceKey,retail_sha256:hash('b'),effective_sha256:hash('b'),current_layout:current,byte_length:66,palette_count:1,read_only:true,project_changed:false};
const request={asset_id:asset,expected_sha256:hash('b'),source_key:context.sourceKey,width:4,height:2,fill_value:7,accept_potential_overlap:false};
const report={schema_version:'legaia.texture-resize-review.v1',asset_id:asset,project_source_key:context.sourceKey,retail_sha256:hash('b'),effective_sha256:hash('b'),proposed_sha256:hash('c'),width:4,height:2,fill_value:7,resize_mode:'crop-fill',current_layout:current,proposed_layout:{...current,height:2},allocation:{source_sha256:hash('b'),proposed_sha256:hash('c'),source_byte_length:66,proposed_byte_length:68,before:{width:4,height:1,width_words:1},after:{width:4,height:2,width_words:1},bpp:4,image_origin:{x:0,y:0},changed:true,layout_changed:true,scope:'TIM-image-allocation-fixed-mode-and-VRAM-origin',gameplay_verified:false},footprint:{schema_version:'legaia.texture-footprint.v1',examined_upload_count:3,potential_overlap_count:1,rows:[{asset_id:asset+'-neighbor',kind:'image',boot_upload_index:null,rectangle:{x:0,y:1,width_words:1,height:1},added_overlap_words:1}],rows_truncated:false,coverage:'known-static-scene-and-boot-uploads',runtime_residency_verified:false},accept_potential_overlap:false,can_apply:false,project_changed:false,gameplay_verified:false,review_key:hash('d')};
assert.deepEqual(decodeResizeSource(source,asset,context),source);
assert.deepEqual(decodeResizeReview(report,request,source),report);
for(const bad of [{...source,current_layout:{...current,width:'4'}},{...source,effective_sha256:'bad'},{...source,read_only:false}])assert.throws(()=>decodeResizeSource(bad,asset,context));
for(const bad of [{...report,can_apply:true},{...report,fill_value:8},{...report,resize_mode:'linear'},{...report,resize_mode:'nearest'},{...report,project_changed:true},{...report,allocation:{...report.allocation,proposed_byte_length:70}},{...report,footprint:{...report.footprint,potential_overlap_count:2}},{...report,footprint:{...report.footprint,rows:[{...report.footprint.rows[0],added_overlap_words:2}]}}])assert.throws(()=>decodeResizeReview(bad,request,source));
class Node{
  constructor(tag){this.tag=tag;this.children=[];this.style={};this.attributes={};this.textContent='';this._value='';this.open=false;this.checked=false;}
  set value(v){this._value=String(v);}
  get value(){return this._value;}
  append(...nodes){for(const node of nodes){this.children.push(node);node.parent=this;}}
  prepend(...nodes){this.children.unshift(...nodes);for(const node of nodes)node.parent=this;}
  replaceChildren(...nodes){this.children=[];this.append(...nodes);}
  setAttribute(k,v){this.attributes[k]=v;}
  showModal(){this.open=true;}
  close(){this.open=false;this.onclose?.();}
  remove(){this.removed=true;this.open=false;if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);}
}
const tree=n=>[n,...n.children.flatMap(tree)],button=(control,text)=>tree(control.dialog).find(n=>n.tag==='button'&&n.textContent===text),input=(control,label)=>tree(control.dialog).find(n=>n.attributes['aria-label']===label);
const previous={document:globalThis.document,fetch:globalThis.fetch};globalThis.document={body:new Node('body'),createElement:tag=>new Node(tag)};
const deferred=()=>{let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};};
let ctx=structuredClone(context),busy=false,queue=[],calls=[],applied=[];
globalThis.fetch=async(route,options)=>{calls.push({route,body:JSON.parse(options.body),signal:options.signal});const value=await queue.shift();assert(value,'Queue a source response');return {ok:true,text:async()=>JSON.stringify(value)};};
const open=async()=>{queue.push(source);return openTextureResizeEditor({assetId:asset,paletteIndex:0,getContext:()=>ctx,busy:()=>busy,setBusy:v=>busy=v,onApplied:state=>applied.push(state)});};
try{
  let control=await open();input(control,'Height in pixels').value=2;input(control,'Encoded fill value').value=7;input(control,'Height in pixels').oninput();queue.push(report);await button(control,'Review resize').onclick();assert(button(control,'Apply reviewed resize').disabled);assert(!button(control,'Inspect resized pixels').disabled);
  input(control,'Accept listed potential overlap').checked=true;input(control,'Accept listed potential overlap').oninput();assert(button(control,'Inspect resized pixels').disabled);assert(button(control,'Apply reviewed resize').disabled);
  const accepted={...report,accept_potential_overlap:true,can_apply:true,review_key:hash('e')};queue.push(accepted);await button(control,'Review resize').onclick();assert(!button(control,'Apply reviewed resize').disabled);
  input(control,'Encoded fill value').value=8;input(control,'Encoded fill value').oninput();assert(button(control,'Apply reviewed resize').disabled);assert(button(control,'Inspect resized pixels').disabled);
  input(control,'Encoded fill value').value=7;input(control,'Encoded fill value').oninput();queue.push(accepted);await button(control,'Review resize').onclick();
  queue.push({project:{path:context.projectPath,mode:'edit'},scene:{id:context.sceneId},resize_report:{...accepted,project_changed:true}});await button(control,'Apply reviewed resize').onclick();assert.equal(applied.length,1);assert(control.dialog.removed);assert(!busy);
  control=await open();ctx={...ctx,sourceKey:hash('a')};control.update();assert(button(control,'Review resize').disabled);assert(button(control,'Apply reviewed resize').disabled);control.dispose();ctx=structuredClone(context);
  control=await open();input(control,'Height in pixels').value=2;input(control,'Encoded fill value').value=7;input(control,'Height in pixels').oninput();const pending=deferred();queue.push(pending.promise);const work=button(control,'Review resize').onclick();assert(busy);control.dispose();assert(!busy);assert(calls.at(-1).signal.aborted);pending.resolve(report);await work;assert(control.dialog.removed);assert.equal(applied.length,1);
  control=await open();input(control,'Height in pixels').value=2;input(control,'Encoded fill value').value=7;input(control,'Height in pixels').oninput();queue.push(report);await button(control,'Review resize').onclick();
  const method=input(control,'Resize method');method.value='nearest';method.onchange();assert.equal(input(control,'Encoded fill value').value,'0');assert(input(control,'Encoded fill value').disabled);assert(button(control,'Inspect resized pixels').disabled);
  const scaled={...report,fill_value:0,resize_mode:'nearest'};queue.push(scaled);await button(control,'Review resize').onclick();assert.equal(calls.at(-1).body.resize_mode,'nearest');assert.equal(calls.at(-1).body.fill_value,0);assert(!button(control,'Inspect resized pixels').disabled);control.dispose();
  // Disposing an idle editor cannot release somebody else's busy state.
  control=await open();busy=true;control.dispose();assert(busy);busy=false;
}finally{globalThis.document=previous.document;globalThis.fetch=previous.fetch;}
