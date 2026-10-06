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

const appearanceTemplate=structuredClone(ownedTemplate);appearanceTemplate.components.NpcDraft.appearance={script_donor_entity_id:donor,donor_entity_id:scene+'/actors/002'};
const appearanceState={...state,actor_templates:[appearanceTemplate]},appearanceReport={...ownedReport,template:appearanceTemplate,draft:{...ownedReport.draft,appearance:appearanceTemplate.components.NpcDraft.appearance}};
assert.deepEqual(decodeNpcPresetReview(appearanceReport,request,appearanceState),appearanceReport);assert.throws(()=>decodeNpcPresetReview({...appearanceReport,draft:ownedReport.draft},request,appearanceState));
console.log('NPC instance review retains independent appearance witness as well as script/text binding.');

const waitingTemplate=structuredClone(appearanceTemplate);waitingTemplate.components.NpcDraft.waits={donor_entity_id:donor,entries:{'script://fixture/actors/001/wait/0065':{duration_ticks:11}}};const waitingState={...state,actor_templates:[waitingTemplate]},waitingReport={...appearanceReport,template:waitingTemplate,draft:{...appearanceReport.draft,waits:waitingTemplate.components.NpcDraft.waits}};
assert.deepEqual(decodeNpcPresetReview(waitingReport,request,waitingState),waitingReport);const omitted=structuredClone(waitingReport);delete omitted.draft.waits;assert.throws(()=>decodeNpcPresetReview(omitted,request,waitingState));
console.log('NPC instance review retains exact frozen wait binding with independent appearance and dialogue.');

const movingTemplate=structuredClone(waitingTemplate);movingTemplate.components.NpcDraft.movement={donor_entity_id:donor,entries:{'script://fixture/actors/001/movement/0027':{x:3200}}};const movingState={...state,actor_templates:[movingTemplate]},movingReport={...waitingReport,template:movingTemplate,draft:{...waitingReport.draft,movement:movingTemplate.components.NpcDraft.movement}};
assert.deepEqual(decodeNpcPresetReview(movingReport,request,movingState),movingReport);const lostMovement=structuredClone(movingReport);delete lostMovement.draft.movement;assert.throws(()=>decodeNpcPresetReview(lostMovement,request,movingState));const changedMovement=structuredClone(movingReport);changedMovement.draft.movement.entries['script://fixture/actors/001/movement/0027'].x=64;assert.throws(()=>decodeNpcPresetReview(changedMovement,request,movingState));
console.log('NPC placement review retains exact frozen movement with text, appearance and waits.');

const facingTemplate=structuredClone(movingTemplate);facingTemplate.components.NpcDraft.facing={donor_entity_id:donor,entries:{'script://fixture/actors/001/facing/0027':{sector:7}}};const facingState={...state,actor_templates:[facingTemplate]},facingReport={...movingReport,template:facingTemplate,draft:{...movingReport.draft,facing:facingTemplate.components.NpcDraft.facing}};
assert.deepEqual(decodeNpcPresetReview(facingReport,request,facingState),facingReport);const lostFacing=structuredClone(facingReport);delete lostFacing.draft.facing;assert.throws(()=>decodeNpcPresetReview(lostFacing,request,facingState));const changedFacing=structuredClone(facingReport);changedFacing.draft.facing.entries['script://fixture/actors/001/facing/0027'].sector=0;assert.throws(()=>decodeNpcPresetReview(changedFacing,request,facingState));
console.log('NPC placement review retains exact frozen facing with all prior families.');

const flaggedTemplate=structuredClone(facingTemplate);flaggedTemplate.components.NpcDraft.flags={donor_entity_id:flaggedTemplate.components.NpcDraft.donor_entity_id,entries:{'script://town01/actors/man-p1/0012/flag-bit/000c':{bit:3}}};const flaggedState={...state,actor_templates:[flaggedTemplate]},flaggedReport={...facingReport,template:flaggedTemplate,draft:{...facingReport.draft,flags:flaggedTemplate.components.NpcDraft.flags}};
assert.deepEqual(decodeNpcPresetReview(flaggedReport,request,flaggedState),flaggedReport);assert.throws(()=>decodeNpcPresetReview({...flaggedReport,draft:facingReport.draft},request,flaggedState));const changedFlags=structuredClone(flaggedReport);changedFlags.draft.flags.entries['script://town01/actors/man-p1/0012/flag-bit/000c'].bit=0;assert.throws(()=>decodeNpcPresetReview(changedFlags,request,flaggedState));
console.log('NPC placement retains exact frozen flag binding with all five prior families.');
