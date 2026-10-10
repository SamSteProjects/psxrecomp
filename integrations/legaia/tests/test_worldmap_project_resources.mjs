import fs from 'node:fs';import assert from 'node:assert/strict';
import {worldmapResourceProjectRecords,qualifyWorldmapProjectResource} from '../editor/worldmap-project-resources.js';
import {projectAssetRecords,projectAssetsContext} from '../editor/project-assets.js';
import {assetMatchesQuery,parseAssetQuery} from '../editor/asset-search.js';
const index=JSON.parse(fs.readFileSync(process.argv[2])),state={project:{path:index.project_path,mode:'edit'},worldmap_authoring_state_key:index.source_key,project_assets_source_key:'b'.repeat(64)},rows=worldmapResourceProjectRecords(index,state.project_assets_source_key),held=structuredClone(index);
assert.equal(rows.length,215);assert.ok(rows.every(r=>r.sceneId===null&&!r.projectMembership&&!r.projectGlobal));
for(const row of rows){const target=qualifyWorldmapProjectResource(row,index,state);assert.equal(target.record.id,row.id);assert.equal(target.root.source_scene,row.data.source_scene);assert.ok(assetMatchesQuery(row,parseAssetQuery('type:'+row.type+' scene:'+row.data.source_scene)));}
rows[0].data.name='detached';assert.deepEqual(index,held);
const model=worldmapResourceProjectRecords(index,state.project_assets_source_key).find(r=>r.type==='model');
for(const mutate of [r=>r.sceneId='scene://town01',r=>r.type='actor',r=>r.data.source_instance_ids=[],r=>r.projectWorldResource.sourceKey='0'.repeat(64),r=>r.projectWorldResource.projectSourceKey='0'.repeat(64)]){const bad=structuredClone(model);mutate(bad);assert.throws(()=>qualifyWorldmapProjectResource(bad,index,state));}
for(const changes of [{project:{path:'foreign',mode:'edit'}},{project:{...state.project,mode:'live'}},{worldmap_authoring_state_key:'0'.repeat(64)},{project_assets_source_key:'0'.repeat(64)}])assert.throws(()=>qualifyWorldmapProjectResource(model,index,{...state,...changes}));
const scene='scene://town01',report={source_key:state.project_assets_source_key,scenes:[{id:scene,name:'Town01'}],assets:[],globalWorldResources:index};assert.equal(projectAssetRecords(report).length,215);assert.equal(projectAssetRecords(report,'global-worldmap').length,215);assert.equal(projectAssetRecords(report,scene).length,0);
assert.deepEqual(projectAssetsContext({projectPath:index.project_path,sourceKey:state.project_assets_source_key,worldResourceKey:index.source_key,scenes:[]}).worldResourceKey,index.source_key);
console.log('Actual 215 global resources retain null field membership, separate source keys, source-qualified targets, search and filters; nine stale/forged handoffs refused.');
