import fs from 'node:fs';import assert from 'node:assert/strict';
import {worldmapResourceProjectRecords,qualifyWorldmapProjectResource} from '../editor/worldmap-project-resources.js';
import {projectAssetRecords,projectAssetsContext,mountProjectAssets} from '../editor/project-assets.js';
import {assetMatchesQuery,parseAssetQuery} from '../editor/asset-search.js';
const index=JSON.parse(fs.readFileSync(process.argv[2])),state={project:{path:index.project_path,mode:'edit'},worldmap_authoring_state_key:index.source_key,project_assets_source_key:'b'.repeat(64)},rows=worldmapResourceProjectRecords(index,state.project_assets_source_key),held=structuredClone(index);
assert.equal(rows.length,index.coverage.asset_count);assert.ok(rows.every(r=>r.sceneId===null&&!r.projectMembership&&!r.projectGlobal));
for(const row of rows){const target=qualifyWorldmapProjectResource(row,index,state);assert.equal(target.record.id,row.id);assert.equal(target.root.source_scene,row.data.source_scene);assert.ok(assetMatchesQuery(row,parseAssetQuery('type:'+row.type+' scene:'+row.data.source_scene)));}
rows[0].data.name='detached';assert.deepEqual(index,held);
const model=worldmapResourceProjectRecords(index,state.project_assets_source_key).find(r=>r.data.resource_role==='native_placed_model');
for(const mutate of [r=>r.sceneId='scene://town01',r=>r.type='actor',r=>r.data.source_instance_ids=[],r=>r.projectWorldResource.sourceKey='0'.repeat(64),r=>r.projectWorldResource.projectSourceKey='0'.repeat(64)]){const bad=structuredClone(model);mutate(bad);assert.throws(()=>qualifyWorldmapProjectResource(bad,index,state));}
for(const changes of [{project:{path:'foreign',mode:'edit'}},{project:{...state.project,mode:'live'}},{worldmap_authoring_state_key:'0'.repeat(64)},{project_assets_source_key:'0'.repeat(64)}])assert.throws(()=>qualifyWorldmapProjectResource(model,index,{...state,...changes}));
const scene='scene://town01',report={source_key:state.project_assets_source_key,scenes:[{id:scene,name:'Town01'}],assets:[],globalWorldResources:index};assert.equal(projectAssetRecords(report).length,index.coverage.asset_count);assert.equal(projectAssetRecords(report,'global-worldmap').length,index.coverage.asset_count);assert.equal(projectAssetRecords(report,scene).length,0);
assert.deepEqual(projectAssetsContext({projectPath:index.project_path,sourceKey:state.project_assets_source_key,worldResourceKey:index.source_key,scenes:[]}).worldResourceKey,index.source_key);
console.log('Actual global resources retain null field membership, separate source keys, source-qualified targets, search and filters; nine stale/forged handoffs refused.');

// Empty disc-backed projects discover global records without inventing field memberships.
class Node {constructor(tag){this.tagName=tag;this.children=[];this.style={};this.dataset={};this.attributes={};this.value='';this.textContent='';}append(...nodes){for(const n of nodes){this.children.push(n);n.parent=this;}}replaceChildren(...nodes){this.children=[];this.append(...nodes);}setAttribute(k,v){this.attributes[k]=String(v);}remove(){if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);}}
const tree=n=>[n,...n.children.flatMap(tree)],saved={document:globalThis.document,fetch:globalThis.fetch};
try{
 globalThis.document={createElement:t=>new Node(t)};let context={projectPath:index.project_path,sourceKey:state.project_assets_source_key,worldResourceKey:index.source_key,scenes:[],activeSceneId:null},busy=false,control,tasks=[],calls=[];
 const empty={schema_version:'legaia.project-assets.v1',source_key:context.sourceKey,project_path:context.projectPath,metadata_only:true,read_only:true,scenes:[],assets:[],coverage:{imported_scene_count:0,available_scene_count:0,partial_scene_count:0,unavailable_scene_count:0,asset_count:0,membership_count:0},limitations:[]},queue=[empty,index];
 globalThis.fetch=async(path,options)=>{calls.push({path,body:JSON.parse(options.body)});const value=queue.shift();assert.ok(value);return {ok:true,text:async()=>JSON.stringify(value)};};
 const host=new Node('div');control=mountProjectAssets({host,getContext:()=>context,busy:()=>busy,setBusy:v=>{busy=v;control?.updateState();},globalResources:()=>true,schedule:f=>tasks.push(f)});
 const scope=tree(host).find(n=>n.attributes['aria-label']==='Asset database scope');scope.value='project';scope.onchange();assert.equal(tasks.length,1);await tasks.shift()();assert.equal(busy,false);assert.equal(control.records().length,index.coverage.asset_count);assert.deepEqual(calls,[{path:'/api/project-assets',body:{}},{path:'/api/worldmap-resources',body:{source_key:index.source_key}}]);
 assert.equal(control.sourceReport().coverage.membership_count,0);assert.ok(control.records().every(r=>r.sceneId===null));context={...context,worldResourceKey:'0'.repeat(64)};control.updateState();assert.equal(control.sourceReport(),null);assert.deepEqual(control.records(),[]);control.dispose();
}finally{for(const [k,v] of Object.entries(saved)){if(v===undefined)delete globalThis[k];else globalThis[k]=v;}}
console.log('Empty-project mounted discovery uses separate exact requests, retains zero memberships and withdraws changed world-source results.');
