import assert from 'node:assert/strict';
import {parseAssetQuery,assetSearchIndex,assetMatchesQuery} from '../editor/asset-search.js';
const record={id:'scene://town01/actors/man-p1/0012',type:'actor',label:'Actor 12',source:'town01',sceneId:'scene://town01',data:{components:{ModelRenderer:{asset_id:'asset://town01/models/scene-tmd/0112'},RetailMetadata:{claims:[{confidence:'confirmed',notes:'speculative text is not confidence',evidence:[{source:'AndrewAltimit',kind:'parser_span'}]}],source_record:{iso_file:'PROT.DAT',prot_entry_name:'town01'}}}}};
const before=structuredClone(record),match=q=>assetMatchesQuery(record,parseAssetQuery(q));
for(const query of [record.id,'actor 12','name:"Actor 12" type:actor','id:scene://town01/actors/man-p1/0012','scene:town01 model:asset://town01/models/scene-tmd/0112','confidence:confirmed provenance:AndrewAltimit','-type:model -name:"Actor 13"','TYPE:ACTOR'])assert(match(query),query);
for(const query of ['name:"Actor 1 2"','type:model','model:0113','confidence:speculative','provenance:actor','-confidence:confirmed','id:0112'])assert(!match(query),query);
assert.equal(assetSearchIndex(record).confidence,'confirmed');assert.deepEqual(record,before);
assert.deepEqual(parseAssetQuery(record.id),[{field:null,text:record.id,exclude:false}]);assert.deepEqual(parseAssetQuery('-'+record.id),[{field:null,text:record.id,exclude:true}]);assert.deepEqual(parseAssetQuery('scene:scene://town01'),[{field:'scene',text:'scene://town01',exclude:false}]);
assert.deepEqual(parseAssetQuery(''),[]);assert.deepEqual(parseAssetQuery('"unknown:value"'),[{field:null,text:'unknown:value',exclude:false}]);assert.deepEqual(parseAssetQuery('asset://town01/models/0112'),[{field:null,text:'asset://town01/models/0112',exclude:false}]);
assert.deepEqual(parseAssetQuery('name:"say \\"hi\\""'),[{field:'name',text:'say "hi"',exclude:false}]);
for(const query of ['name:','"unclosed','-','unknown:value','x'.repeat(2049),Array(33).fill('word').join(' ')])assert.throws(()=>parseAssetQuery(query),undefined,query);
assert(!assetMatchesQuery({id:'asset',data:{}},parseAssetQuery('confidence:unknown')));assert(assetMatchesQuery({id:'asset',data:{}},parseAssetQuery('-confidence:confirmed')));
const shared={...record,sceneId:'scene://town01',projectMembership:{scene_ids:['scene://town01','scene://map01']}};
assert(assetMatchesQuery(shared,parseAssetQuery('scene:map01')));assert(!assetMatchesQuery(shared,parseAssetQuery('-scene:map01')));
console.log('Asset field, phrase, URI, exclusion, recorded confidence, provenance, bounds and immutable-record checks passed.');

const variants={...record,projectMembership:{scene_ids:['scene://town01','scene://map01'],chosenSceneId:'scene://town01',variants:[
 {scene_id:'scene://town01',source_import_sha256:'a'.repeat(64),source_catalog_key:'b'.repeat(64),record:{name:'Town binding',source_record:{prot_entry_name:'town_alias',offset:123},claims:[{confidence:'confirmed',evidence:[{source:'Town evidence'}]}]}},
 {scene_id:'scene://map01',source_import_sha256:'c'.repeat(64),source_catalog_key:'d'.repeat(64),record:{name:'Other binding',source_record:{prot_entry_name:'map_alias',offset:456},claims:[{confidence:'inferred',evidence:[{source:'Other evidence'}]}],components:{RetailMetadata:{source_record:{iso_file:'OTHER.DAT'}}}}}
]}};const variantsBefore=structuredClone(variants);
for(const query of ['provenance:'+ 'c'.repeat(64),'provenance:'+ 'd'.repeat(64),'name:"Other binding"','scene:map_alias','provenance:"Other evidence"','provenance:OTHER.DAT','confidence:inferred'])assert(assetMatchesQuery(variants,parseAssetQuery(query)),query);
for(const query of ['-provenance:'+ 'c'.repeat(64),'-name:"Other binding"','provenance:'+ 'e'.repeat(64),'provenance:invented','name:"Other evidence"'])assert(!assetMatchesQuery(variants,parseAssetQuery(query)),query);
assert.deepEqual(variants,variantsBefore);assert.equal(variants.data,record.data);assert.equal(variants.projectMembership.chosenSceneId,'scene://town01');
console.log('Project field search covers retained membership names, source aliases, import/catalog hashes and provenance without merging or activating source variants.');

const retailClip='animation://town01/scene-anm/0012',currentClip='animation://town01/authored-record/example';
const bound={...record,data:{...record.data,components:{...record.data.components,ActorAnimation:{imported:{animation_asset_id:retailClip},effective:{animation_asset_id:currentClip}}}}};
const boundBefore=structuredClone(bound);
for(const query of ['type:actor animation:'+retailClip,'animation:'+currentClip,'animation:authored-record -animation:0013'])assert(assetMatchesQuery(bound,parseAssetQuery(query)),query);
for(const query of ['animation:0013','-animation:'+retailClip,'animation:speculative','animation:scene://town01'])assert(!assetMatchesQuery(bound,parseAssetQuery(query)),query);
assert(assetMatchesQuery({id:currentClip,type:'animation',data:{}},parseAssetQuery('animation:'+currentClip)));
assert(!assetMatchesQuery({id:'unresolved',type:'actor',data:{components:{ActorAnimation:{imported:{animation_asset_id:null},effective:{initial_animation_id:12}}}}},parseAssetQuery('animation:12')));
const projectBinding={...record,projectMembership:{chosenSceneId:'scene://town01',variants:[{scene_id:'scene://other',record:{components:{ActorAnimation:{effective:{animation_asset_id:'animation://other/scene-anm/0001'}}}}}]}};
const projectBefore=structuredClone(projectBinding);assert(assetMatchesQuery(projectBinding,parseAssetQuery('animation:animation://other/scene-anm/0001')));assert(!assetMatchesQuery(projectBinding,parseAssetQuery('-animation:animation://other/scene-anm/0001')));
assert.deepEqual(bound,boundBefore);assert.deepEqual(projectBinding,projectBefore);
console.log('Animation field search covers Retail/Current bindings, clip identities and retained Project variants without inventing unresolved clips or changing source membership.');
