import assert from 'node:assert/strict';
import {decodeNpcPresetReview,decodeNpcPresetScene,NPC_PRESET_SCOPE} from '../editor/npc-presets.js';
const hash='a'.repeat(64),scene='scene://fixture',donor=scene+'/actors/001',id='authored-actor://12345678-1234-5234-8234-123456789abc';
const template={id:'template://12345678-1234-4234-8234-123456789abc',name:'Guard',scope:NPC_PRESET_SCOPE,source:{scene_id:scene,entity_id:donor},components:{Transform:{position:{x:128,z:512}},NpcDraft:{name:'Original',donor_entity_id:donor}}};
const state={scene:{id:scene},project_copy_source_key:hash,scene_preview_source_key:hash,actor_templates:[{...template,application:{available:false}}],actor_drafts:{}};
const request={template_id:template.id,name:'New guard',position:{x:192,z:576},expected_source_key:hash};
const report={schema_version:'legaia.npc-preset-review.v1',project_source_key:hash,scene_preview_source_key:hash,scene_id:scene,request,template,entity_id:id,draft:{scene_id:scene,donor_entity_id:donor,name:request.name,position:request.position},review_key:hash,gameplay_verified:false,limitations:['Runtime unverified.']};
assert.deepEqual(decodeNpcPresetReview(report,request,state),report);
for(const bad of [{...report,draft:{...report.draft,donor_entity_id:'wrong'}},{...report,request:{...request,name:'Other'}},{...report,project_source_key:'b'.repeat(64)},{...report,gameplay_verified:true},{...report,template:{...template,name:'Changed'}}])assert.throws(()=>decodeNpcPresetReview(bad,request,state));
const base={schema:'legaia.scene-preview.v1',source_key:hash,scene_id:scene,entities:[{entity_id:donor,kind:'actor'}],assets:[],position_to_display:{x:1,y:-1,z:1}};
const row={entity_id:id,kind:'actor_draft',donor_entity_id:donor,source_actor_id:donor,name:request.name,authored_position:request.position,position:{...request.position,y:null},preview_position:{...request.position,y:20},display_position:{...request.position,y:-20},preview_height_status:'source_surface',model_to_scene:[1,0,0,192,0,1,0,-20,0,0,1,576,0,0,0,1],renderable:false};
const response={schema_version:'legaia.npc-preset-scene.v1',review:report,scene:{...base,representation:'authored',entities:[...base.entities,row]}};
assert.deepEqual(decodeNpcPresetScene(response,report,base),response.scene);
for(const change of [{donor_entity_id:'wrong'},{authored_position:{x:256,z:576}},{display_position:{x:192,y:20,z:576}},{model_to_scene:Array(16).fill(0)}])assert.throws(()=>decodeNpcPresetScene({...response,scene:{...response.scene,entities:[...base.entities,{...row,...change}]}},report,base));
assert.throws(()=>decodeNpcPresetScene({...response,scene:{...response.scene,entities:[{...base.entities[0],name:'changed'},row]}},report,base));
console.log('NPC preset source, donor, requested placement and detached scene checks pass.');

const ownedTemplate=structuredClone(template),ownedDialogue={donor_entity_id:donor,runs:{'script://fixture/actors/001/dialogue/0005/run/0006':'Yo'}};ownedTemplate.components.NpcDraft.dialogue=ownedDialogue;
const ownedState={...state,actor_templates:[{...ownedTemplate,application:{available:false}}]},ownedReport={...report,template:ownedTemplate,draft:{...report.draft,dialogue:ownedDialogue}};
assert.deepEqual(decodeNpcPresetReview(ownedReport,request,ownedState),ownedReport);
for(const mutate of [v=>delete v.draft.dialogue,v=>v.draft.dialogue.runs['script://fixture/actors/001/dialogue/0005/run/0006']='Wrong',v=>v.draft.dialogue.donor_entity_id='wrong']){const v=structuredClone(ownedReport);mutate(v);assert.throws(()=>decodeNpcPresetReview(v,request,ownedState));}
console.log('NPC instance review retains exact frozen own-dialogue metadata and rejects loss or substitution.');
