import assert from 'node:assert/strict';
import {projectAssetsContext,decodeProjectAssets,projectAssetRecords,mountProjectAssets,projectAssetVariant,qualifyProjectCatalogVariant} from '../editor/project-assets.js';

const h=letter=>letter.repeat(64),scene=index=>'scene://'+index;
const context={projectPath:'C:/private/project-assets',sourceKey:h('a'),scenes:[{id:scene('a'),name:'Town01'},{id:scene('b'),name:'Dolk2'},{id:scene('c'),name:'Unavailable'}],activeSceneId:scene('a')};
const sharedId='worldmap://legaia/menu/placements/0000',actorId=scene('a')+'/actors/man-p1/0000';
const sourceRecord=(id,kind,sceneId,sourceFact)=>({id,semantic_id:id,kind,asset_kind:kind,name:sourceFact,scene_id:sceneId,source_record:{sha256:h(sceneId.endsWith('a')?'b':sceneId.endsWith('b')?'c':'d')},binding:{owner_scene:sceneId,source_fact:sourceFact}});
const snapshot=(key=context.sourceKey)=>({
  schema_version:'legaia.project-assets.v1',source_key:key,project_path:context.projectPath,metadata_only:true,read_only:true,
  scenes:context.scenes.map((row,index)=>({...row,import_sha256:h(['b','c','d'][index]),status:['available','partial','unavailable'][index],record_count:[2,1,1][index],limitations:index?['Derived catalog is incomplete; retained source records remain qualified.']:[]})),
  assets:[
    {id:sharedId,kind:'worldmap',label:'Source landmark',scene_ids:[scene('b'),scene('a')],variants:[{scene_id:scene('b'),source_import_sha256:h('c'),source_catalog_key:h('f'),record:sourceRecord(sharedId,'worldmap',scene('b'),'Dolk2 binding')},{scene_id:scene('a'),source_import_sha256:h('b'),source_catalog_key:h('e'),record:sourceRecord(sharedId,'worldmap',scene('a'),'Town01 binding')}]},
    {id:actorId,kind:'actor',label:'Source actor',scene_ids:[scene('a')],variants:[{scene_id:scene('a'),source_import_sha256:h('b'),source_catalog_key:null,record:sourceRecord(actorId,'actor',scene('a'),'Actor source')}]},
    {id:scene('c'),kind:'scene',label:'Unavailable source scene',scene_ids:[scene('c')],variants:[{scene_id:scene('c'),source_import_sha256:h('d'),source_catalog_key:null,record:sourceRecord(scene('c'),'scene',scene('c'),'Verified base source')}]}
  ],
  coverage:{imported_scene_count:3,available_scene_count:1,partial_scene_count:1,unavailable_scene_count:1,asset_count:3,membership_count:4},limitations:['Imported project sources only; runtime activation is not evaluated.']
});

assert.deepEqual(projectAssetsContext(context),context);
for(const change of [{sourceKey:'stale'},{projectPath:null},{scenes:[context.scenes[0],context.scenes[0]]},{activeSceneId:'Town01'},{mode:'edit'}])assert.throws(()=>projectAssetsContext({...context,...change}));
const raw=snapshot(),verified=decodeProjectAssets(raw,context);verified.assets[0].variants[0].record.binding.source_fact='detached';assert.equal(raw.assets[0].variants[0].record.binding.source_fact,'Dolk2 binding');assert.equal(verified.scenes[2].record_count,1,'Unavailable derived catalogs may retain verified base memberships.');
for(const mutate of [
  value=>value.source_key=h('0'),value=>value.project_path='C:/other',value=>value.metadata_only=false,value=>value.read_only=false,
  value=>value.scenes.pop(),value=>value.scenes[0].name='Wrong source',value=>value.scenes[0].import_sha256='bad',value=>value.scenes[0].status='loaded',value=>value.scenes[2].record_count=0,
  value=>value.assets.push(structuredClone(value.assets[0])),value=>value.assets[0].kind='invented',value=>value.assets[0].scene_ids[0]=scene('c'),value=>value.assets[0].variants[0].scene_id=scene('a'),
  value=>value.assets[0].variants[0].source_import_sha256=h('b'),value=>value.assets[0].variants[0].source_catalog_key='bad',value=>value.assets[0].variants[0].record.id='conflicting',value=>value.assets[0].variants[0].record.semantic_id='conflicting',value=>value.assets[0].variants[0].record.kind='actor',value=>value.assets[0].variants[0].record.asset_kind='actor',
  value=>value.coverage.membership_count=3,value=>value.coverage.unavailable_scene_count=0,value=>value.extra=true
]){const value=snapshot();mutate(value);assert.throws(()=>decodeProjectAssets(value,context));}
const emptyContext={...context,scenes:[],activeSceneId:null},empty={...snapshot(),scenes:[],assets:[],coverage:{imported_scene_count:0,available_scene_count:0,partial_scene_count:0,unavailable_scene_count:0,asset_count:0,membership_count:0}};assert.equal(decodeProjectAssets(empty,emptyContext).assets.length,0);
const first=projectAssetRecords(raw),active=projectAssetRecords(raw,'all',scene('b')),filtered=projectAssetRecords(raw,scene('b'),scene('a'));
const activation=projectAssetVariant(active[0],context),freshCatalog=structuredClone(activation.record);
freshCatalog.catalog_limitations=['Bounded catalog'];assert(qualifyProjectCatalogVariant(activation,freshCatalog,h('f')));
assert.throws(()=>projectAssetVariant(active[0],{...context,sourceKey:h('9')}));
assert.throws(()=>projectAssetVariant({...active[0],sceneId:scene('c')},context));
assert.throws(()=>qualifyProjectCatalogVariant(activation,freshCatalog,h('e')));
assert.throws(()=>qualifyProjectCatalogVariant(activation,{...freshCatalog,scene_id:scene('a')},h('f')));
assert.throws(()=>qualifyProjectCatalogVariant(activation,{...freshCatalog,binding:{owner_scene:scene('b'),source_fact:'changed'}},h('f')));
assert.equal(first[0].sceneId,scene('a'),'Fallback chooses the stable first scene, not array or catalog order.');assert.equal(active[0].data.binding.source_fact,'Dolk2 binding');assert.equal(filtered.length,1);assert.equal(filtered[0].sceneId,scene('b'));assert.equal(filtered[0].source,'Shared across 2 imported scenes · Dolk2');assert.equal(filtered[0].projectMembership.sourceKey,context.sourceKey);assert.equal(filtered[0].projectMembership.chosenSceneId,scene('b'));assert.equal(filtered[0].projectMembership.variants.length,2);
assert.equal(projectAssetRecords(raw,'all',scene('a'),new Map([[sharedId,scene('b')]]))[0].sceneId,scene('b'));assert.equal(projectAssetRecords(raw,scene('a'),scene('a'),new Map([[sharedId,scene('b')]]))[0].sceneId,scene('a'));assert.throws(()=>projectAssetRecords(raw,scene('unknown')));
filtered[0].data.binding.source_fact='local';filtered[0].projectMembership.variants[0].record.binding.source_fact='local';assert.equal(raw.assets[0].variants[0].record.binding.source_fact,'Dolk2 binding');

class Node {
  constructor(tag){this.tagName=tag;this.children=[];this.style={};this.dataset={};this.attributes={};this.value='';this.textContent='';this.hidden=false;this.disabled=false;}
  append(...nodes){for(const node of nodes){this.children.push(node);node.parent=this;}}
  replaceChildren(...nodes){this.children=[];this.append(...nodes);}
  setAttribute(key,value){this.attributes[key]=String(value);}
  remove(){this.removed=true;if(this.parent)this.parent.children=this.parent.children.filter(node=>node!==this);}
}
const tree=node=>[node,...node.children.flatMap(tree)],input=(host,label)=>tree(host).find(node=>node.attributes['aria-label']===label),action=host=>tree(host).find(node=>node.dataset.action==='refresh-project-resources'),hasText=(host,fragment)=>tree(host).some(node=>node.textContent.includes(fragment));
const deferred=()=>{let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};};
const globals={document:globalThis.document,fetch:globalThis.fetch};globalThis.document={createElement:tag=>new Node(tag)};
try{
  let ctx=structuredClone(context),isBusy=false,control=null,queue=[],calls=[],errors=[],changes=0;
  globalThis.fetch=async(path,options)=>{calls.push({path,body:JSON.parse(options.body),signal:options.signal});const queued=queue.shift();if(queued instanceof Error)throw queued;const value=queued instanceof Promise?await queued:queued;assert.notEqual(value,undefined,'Source response must be queued');return {ok:!value?.error,text:async()=>typeof value==='string'?value:JSON.stringify(value)};};
  const settings={getContext:()=>ctx,busy:()=>isBusy,setBusy:value=>{isBusy=value;control?.updateState();},onChange:()=>{changes++;assert.ok(control,'Mount cannot notify a parent before returning its handle.');control.records();},onError:error=>errors.push(error)};
  const mount=()=>{const host=new Node('host');control=mountProjectAssets({host,...settings});return host;};
  const chooseScope=(host,value)=>{const field=input(host,'Asset database scope');field.value=value;return field.onchange();};
  const chooseFilter=(host,value)=>{const field=input(host,'Imported resource scene filter');field.value=value;return field.onchange();};
  const load=async(host,value=snapshot(ctx.sourceKey))=>{queue=[value];assert.equal(await action(host).onclick(),true);};

  let host=mount();assert.equal(changes,0);assert.equal(calls.length,0);assert.equal(control.scope(),'active');assert.equal(control.filter(),'all');assert.deepEqual(control.records(),[]);assert.equal(control.sourceReport(),null);assert.equal(action(host).hidden,true);assert.equal(chooseScope(host,'project'),true);assert.equal(calls.length,0,'Choosing project scope never writes or automatically fetches.');assert.equal(hasText(host,'Project resources are not verified'),true);assert.equal(action(host).disabled,false);await load(host);assert.equal(calls.at(-1).path,'/api/project-assets');assert.deepEqual(calls.at(-1).body,{});assert.equal(isBusy,false);assert.equal(control.records().length,3);assert.equal(hasText(host,'4 scene memberships'),true);assert.equal(hasText(host,'1 unavailable'),true);assert.equal(hasText(host,'Unavailable · unavailable · 1 records'),true);const detached=control.sourceReport();detached.assets[0].variants[0].record.name='changed';assert.notEqual(control.sourceReport().assets[0].variants[0].record.name,'changed');
  assert.equal(chooseFilter(host,scene('b')),true);assert.equal(control.filter(),scene('b'));assert.equal(control.records().length,1);assert.equal(control.records()[0].data.binding.source_fact,'Dolk2 binding');assert.equal(control.chooseVariant(sharedId,scene('a')),false,'The explicit scene filter cannot be bypassed by a membership choice.');assert.equal(chooseFilter(host,'all'),true);assert.equal(control.records()[0].sceneId,scene('a'));assert.equal(control.chooseVariant(sharedId,scene('b')),true);assert.equal(control.records()[0].sceneId,scene('b'));assert.equal(control.chooseVariant(actorId,scene('b')),false);ctx={...ctx,activeSceneId:scene('b')};control.updateState();ctx={...ctx,activeSceneId:scene('a')};control.updateState();assert.equal(control.records()[0].sceneId,scene('b'),'Explicit membership precedes the changing active scene.');assert.equal(calls.length,1);assert.equal(control.chooseVariant(sharedId,scene('a')),true);ctx={...ctx,scenes:ctx.scenes.toReversed().map(({id,name})=>({name,id}))};control.updateState();assert.ok(control.sourceReport(),'Ordering of imported scenes and object properties cannot invalidate a verified source.');assert.equal(control.records()[0].sceneId,scene('a'));isBusy=true;control.updateState();assert.equal(control.chooseVariant(sharedId,scene('b')),false);assert.equal(chooseScope(host,'active'),false);assert.equal(input(host,'Asset database scope').value,'project');isBusy=false;control.updateState();
  ctx={...ctx,sourceKey:h('9')};control.updateState();assert.equal(control.sourceReport(),null);assert.deepEqual(control.records(),[]);assert.equal(control.chooseVariant(sharedId,scene('b')),false);assert.equal(hasText(host,'Project resources are not verified'),true);await load(host);assert.equal(control.records()[0].sceneId,scene('a'),'Source changes clear per-asset preferred memberships.');assert.equal(control.records()[0].projectMembership.sourceKey,h('9'));assert.equal(chooseScope(host,'active'),true);assert.equal(control.records().length,0);assert.ok(control.sourceReport(),'Returning to active scope keeps a still-verified read-only index.');assert.equal(chooseScope(host,'project'),true);assert.equal(control.records().length,3);assert.equal(calls.length,2);control.dispose();assert.equal(host.children.length,0);assert.equal(control.chooseVariant(sharedId,scene('a')),false);assert.equal(control.sourceReport(),null);assert.deepEqual(control.records(),[]);

  ctx=structuredClone(context);control=null;host=mount();chooseScope(host,'project');await load(host);const malformed=snapshot();malformed.assets[0].variants[0].source_import_sha256=h('0');queue=[malformed];assert.equal(await action(host).onclick(),false);assert.equal(control.sourceReport(),null);assert.equal(control.records().length,0);assert.ok(errors.at(-1).message.includes('variant'));assert.equal(hasText(host,'Project resources are not verified'),true);queue=[{error:'Private import checksum changed'}];assert.equal(await action(host).onclick(),false);assert.equal(hasText(host,'Private import checksum changed'),true);queue=['{broken'];assert.equal(await action(host).onclick(),false);assert.equal(control.sourceReport(),null);assert.equal(isBusy,false);control.dispose();

  control=null;host=mount();chooseScope(host,'project');const latest=deferred();queue=[latest.promise];const reading=action(host).onclick();const latestSignal=calls.at(-1).signal;assert.equal(isBusy,true);ctx={...ctx,activeSceneId:scene('b')};control.updateState();assert.equal(latestSignal.aborted,false,'Active scene changes leave the imported-project read valid.');latest.resolve(snapshot());assert.equal(await reading,true);assert.equal(control.records()[0].sceneId,scene('b'));assert.equal(isBusy,false);control.dispose();

  ctx=structuredClone(context);control=null;host=mount();chooseScope(host,'project');const stale=deferred();queue=[stale.promise];const staleRead=action(host).onclick();const staleSignal=calls.at(-1).signal;ctx={...ctx,sourceKey:h('9')};control.updateState();assert.equal(staleSignal.aborted,true);assert.equal(isBusy,false);isBusy=true;stale.resolve(snapshot());assert.equal(await staleRead,false);assert.equal(isBusy,true,'An old request cannot release a later operation’s busy ownership.');assert.equal(control.sourceReport(),null);assert.equal(control.records().length,0);isBusy=false;control.updateState();await load(host);assert.equal(control.sourceReport().source_key,h('9'));control.dispose();

  ctx=structuredClone(context);control=null;host=mount();chooseScope(host,'project');const cancelled=deferred();queue=[cancelled.promise];const cancelledRead=action(host).onclick();const cancelledSignal=calls.at(-1).signal;assert.equal(chooseScope(host,'active'),true);assert.equal(cancelledSignal.aborted,true);assert.equal(isBusy,false);const beforeLateChanges=changes;cancelled.resolve(snapshot());assert.equal(await cancelledRead,false);assert.equal(changes,beforeLateChanges);assert.equal(control.scope(),'active');assert.equal(control.sourceReport(),null);control.dispose();

  control=null;host=mount();chooseScope(host,'project');const closed=deferred();queue=[closed.promise];const closedRead=action(host).onclick();const closedSignal=calls.at(-1).signal;control.dispose();assert.equal(closedSignal.aborted,true);assert.equal(isBusy,false);const changesAtClose=changes,errorsAtClose=errors.length;closed.resolve({error:'Late source read failure'});assert.equal(await closedRead,false);assert.equal(changes,changesAtClose);assert.equal(errors.length,errorsAtClose);assert.equal(host.children.length,0);

  control=null;host=mount();chooseScope(host,'project');const invalid=deferred();queue=[invalid.promise];const invalidRead=action(host).onclick();ctx={...ctx,sourceKey:null};control.updateState();assert.equal(calls.at(-1).signal.aborted,true);assert.equal(hasText(host,'Project source is unavailable'),true);assert.equal(input(host,'Asset database scope').disabled,true);invalid.resolve(snapshot());assert.equal(await invalidRead,false);assert.equal(control.sourceReport(),null);assert.equal(isBusy,false);control.dispose();
  ctx={...emptyContext};control=null;host=mount();chooseScope(host,'project');assert.equal(hasText(host,'No imported scenes'),true);assert.equal(action(host).disabled,true);const count=calls.length;assert.equal(await action(host).onclick(),false);assert.equal(calls.length,count);control.dispose();
}finally{for(const [key,value] of Object.entries(globals)){if(value===undefined)delete globalThis[key];else globalThis[key]=value;}}
console.log('Project asset source/coverage/variant qualification; detached memberships; explicit refresh and filtering; preferred source selection; stale/abort/disposal and busy ownership passed.');

const {assetMatchesQuery,parseAssetQuery}=await import('../editor/asset-search.js');
const sourceSearchRecord=projectAssetRecords(decodeProjectAssets(snapshot(),context),'all',scene('a')).find(record=>record.id===sharedId),sourceSearchBefore=structuredClone(sourceSearchRecord);
assert(assetMatchesQuery(sourceSearchRecord,parseAssetQuery('provenance:'+h('c'))));assert(assetMatchesQuery(sourceSearchRecord,parseAssetQuery('provenance:'+h('f'))));assert(assetMatchesQuery(sourceSearchRecord,parseAssetQuery('name:"Dolk2 binding"')));assert(!assetMatchesQuery(sourceSearchRecord,parseAssetQuery('-provenance:'+h('c'))));
assert.equal(sourceSearchRecord.sceneId,scene('a'));assert.equal(sourceSearchRecord.data.binding.source_fact,'Town01 binding');assert.deepEqual(sourceSearchRecord,sourceSearchBefore);assert.equal(projectAssetVariant(sourceSearchRecord,context).record.binding.source_fact,'Town01 binding');
console.log('Verified project variants feed provenance/name search while activation keeps the exact chosen source record.');

const npcId='authored-actor://12345678-1234-1234-1234-123456789abc',npcReport=snapshot();
const npcDraft={scene_id:scene('a'),donor_entity_id:actorId,position:{x:128,z:256},name:'Authored NPC'};
npcReport.assets.push({id:npcId,kind:'actor',label:npcDraft.name,scene_ids:[scene('a')],variants:[{scene_id:scene('a'),source_import_sha256:h('b'),source_catalog_key:null,record:{id:npcId,semantic_id:npcId,kind:'actor',asset_kind:'actor',layer:'authored',draft:true,name:npcDraft.name,scene_id:scene('a'),donor_entity_id:actorId,authored:npcDraft}}]});
npcReport.scenes[0].record_count++;npcReport.coverage.asset_count++;npcReport.coverage.membership_count++;
assert.deepEqual(decodeProjectAssets(npcReport,context),npcReport);
const npcRecord=projectAssetRecords(npcReport,scene('a')).find(row=>row.id===npcId);
assert.equal(npcRecord.data.layer,'authored');assert.equal(projectAssetVariant(npcRecord,context).source_catalog_key,null);
assert(!projectAssetRecords(npcReport,scene('b')).some(row=>row.id===npcId));
for(const change of [r=>r.layer='imported',r=>r.draft=false,r=>r.source_record={},r=>r.authored.position.x=32,r=>r.authored.scene_id=scene('b'),r=>r.authored.donor_entity_id='missing',r=>r.name='different']){
 const bad=structuredClone(npcReport);change(bad.assets.at(-1).variants[0].record);assert.throws(()=>decodeProjectAssets(bad,context));
}
const catalogNpc=structuredClone(npcReport);catalogNpc.assets.at(-1).variants[0].source_catalog_key=h('e');assert.throws(()=>decodeProjectAssets(catalogNpc,context));
console.log('Authored NPC database memberships preserve owner/donor context and reject retail provenance substitution.');

const otherAuthored=snapshot();otherAuthored.assets[0].variants.forEach(row=>row.record.layer='authored');assert.deepEqual(decodeProjectAssets(otherAuthored,context),otherAuthored,'Non-NPC authored resources keep their existing descriptor contract.');

const modelNpc=structuredClone(npcReport),modelNpcRecord=modelNpc.assets.at(-1).variants[0].record;
modelNpcRecord.model_reference={source_id:npcId,source_name:npcDraft.name,target_id:'asset://legaia/models/0',scene_id:scene('a'),kind:'draft_initial_model_assignment',imported:false,effective:true,effective_donor_id:actorId,runtime_binding:'not_asserted'};
assert.deepEqual(decodeProjectAssets(modelNpc,context),modelNpc);
for(const edit of [r=>r.effective_donor_id='other',r=>r.imported=true,r=>r.source_id='other',r=>r.runtime_binding='live']){const bad=structuredClone(modelNpc);edit(bad.assets.at(-1).variants[0].record.model_reference);assert.throws(()=>decodeProjectAssets(bad,context));}
