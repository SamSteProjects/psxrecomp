import assert from 'node:assert/strict';
import {assetEvidenceContext,assetRecordDownload,mountAssetRecordDownload} from '../editor/asset-record-export.js';
const state={asset_reference_source_key:'a'.repeat(64),project_assets_source_key:'b'.repeat(64),build_review_source_key:'c'.repeat(64),project:{path:'C:/private/project',name:'Evidence'},scene:{id:'scene://fixture'},authored_assets:[{id:'asset://fixture/model',authored:{x:1}}]};
const record={id:'asset://fixture/model',type:'model',label:'<b>Source</b>',data:{source_record:{sha256:'d'.repeat(64)},opaque:[0,255]},sceneId:undefined,authoredRecord:{authored:{delta:2}},projectMembership:{variants:[{scene_id:'scene://fixture'},{scene_id:'scene://other'}]}};
const context=assetEvidenceContext(state),file=assetRecordDownload(record,context),report=JSON.parse(file.text);
assert.deepEqual(report.record,JSON.parse(JSON.stringify(record)));assert.deepEqual(report.source_context,context);assert.equal(report.read_only,true);assert.equal(file.filename,'legaia-asset-model-aaaaaaaaaaaaaaaa.json');assert(file.text.endsWith('\n'));
assert.match(report.limitations.join(' '),/Gameplay remains unverified/);
for(const invalid of [{...record,type:'unknown'},{...record,id:'asset://bad <x>'},{...record,data:{number:NaN}},{...record,data:{n:Infinity}},{...record,data:{n:1n}},{...record,data:{n:()=>1}},{...record,data:{date:new Date()}},{...record,data:{array:[undefined]}}])assert.throws(()=>assetRecordDownload(invalid,context));
const circular={};circular.self=circular;assert.throws(()=>assetRecordDownload({...record,data:circular},context));
assert.throws(()=>assetRecordDownload({...record,data:{value:'é'.repeat(17*1024*1024)}},context),/32 MiB/);
assert.throws(()=>assetEvidenceContext({...state,asset_reference_source_key:null}));
// Exercise the production click adapter without a browser or project mutation.
let clicked=0,requests=0,revoked=0,current=true,busy=false,latest=state,resolveRequest;
globalThis.document={createElement:tag=>({tag,dataset:{},setAttribute(){},remove(){},click(){clicked++;}}),body:{append(){}}};
globalThis.URL.createObjectURL=()=> 'blob:evidence';globalThis.URL.revokeObjectURL=()=>{revoked++;};
const originalTimer=globalThis.setTimeout;globalThis.setTimeout=callback=>{callback();return 1;};
const host={children:[],append(...children){this.children.push(...children);}},errors=[];
const options={record,getState:()=>state,current:()=>current,busy:()=>busy,onError:e=>errors.push(e.message),request:async()=>{requests++;return {ok:true,json:async()=>latest};}};
try{
 const button=mountAssetRecordDownload(host,options);busy=true;await button.onclick();assert.equal(requests,0);busy=false;
 await button.onclick();assert.equal(clicked,1);assert.equal(revoked,1);assert.equal(button.disabled,false);
 latest={...state,asset_reference_source_key:'f'.repeat(64)};await button.onclick();assert.equal(clicked,1);assert.equal(button.disabled,true);assert.match(errors.at(-1),/Reopen/);
 latest=state;current=false;await button.onclick();assert.equal(requests,2);assert.equal(clicked,1);
 current=true;const delayed=mountAssetRecordDownload(host,{...options,request:()=>new Promise(resolve=>resolveRequest=resolve)});
 const pending=delayed.onclick();assert.equal(delayed.disabled,true);await delayed.onclick();current=false;resolveRequest({ok:true,json:async()=>state});await pending;assert.equal(clicked,1);assert.equal(delayed.disabled,true);
}finally{globalThis.setTimeout=originalTimer;}
console.log('Asset record evidence completeness, bounded metadata, busy/pending and local/server stale-source guards passed.');
