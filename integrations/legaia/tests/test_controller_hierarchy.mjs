import assert from 'node:assert/strict';
import {hierarchyControllerRecord,hierarchyNeedsControllerResources} from '../editor/controller-hierarchy.js';
import {CONTROLLER_BUILD_TARGETS} from '../editor/controller-build-navigation.js';
import {hierarchyMatches,parseHierarchyQuery,matchingActorIds} from '../editor/hierarchy-query.js';
const scene='scene://fixture',id='script://fixture/controllers/man-p1/0000',hash='a'.repeat(64),schema={components:{}};
for(const [family,kind] of Object.values(CONTROLLER_BUILD_TARGETS)){
 schema.components[family]={label:'Authored '+family};const record={id,type:'controller',label:'Scene Entry Controller',sceneId:scene,data:{source_record:{sha256:hash}},authoredRecord:{id,kind:'controller',scene_id:scene,authored:{[family]:{source_record_sha256:hash,entries:{[id+'/'+kind+'/0005']:{value:7}}}}}},before=JSON.stringify(record);
 const row=hierarchyControllerRecord(record,schema);assert.equal(row.authored,'true');assert.equal(row.visibility,'unknown');assert(hierarchyMatches(row,parseHierarchyQuery('type:controller authored:true component:'+family)));assert(hierarchyMatches(row,parseHierarchyQuery('component:"Authored '+family+'"')));assert.deepEqual(matchingActorIds([row],[]),[]);assert.equal(JSON.stringify(record),before);row.components.length=0;assert(hierarchyControllerRecord(record,schema).components.length);
 for(const changed of [{id:'foreign'},{sceneId:'scene://foreign'},{data:{source_record:{sha256:'b'.repeat(64)}}},{authoredRecord:{...record.authoredRecord,kind:'actor'}}])assert.equal(hierarchyControllerRecord({...record,...changed},schema).authored,'unknown');
 const imported={...record,authoredRecord:undefined};assert.equal(hierarchyControllerRecord(imported,schema).authored,'false');assert(hierarchyMatches(hierarchyControllerRecord(imported,schema),parseHierarchyQuery('authored:false')));
 assert(hierarchyNeedsControllerResources('component:'+family,schema));
}
for(const query of ['type:controller','type:cont authored:true','authored:false','name:"Scene Entry Controller"','script://fixture/controllers','id:script://fixture','/controllers/'])assert(hierarchyNeedsControllerResources(query,schema),query);
for(const query of ['','type:actor','type:actor component:ControllerPartySelectors','-type:controller authored:true','-component:ControllerPartySelectors','type:controller visibility:shown','name:Vahn','component:Transform','component:','"unfinished'])assert.equal(hierarchyNeedsControllerResources(query,schema),false,query);
console.log('Eleven-family controller hierarchy authorship/component queries preserve source uncertainty, actor selection boundaries and bounded catalog discovery.');
