import assert from 'node:assert/strict';
import {validateNpcPresetMetadata,NPC_PRESET_SCOPE,NPC_PRESET_FILE_SCHEMA} from '../editor/npc-preset-metadata.js';
import {decodePresetFileExport,decodePresetImportReview} from '../editor/preset-files.js';
const hash='a'.repeat(64),template={id:'template://12345678-1234-4234-8234-123456789abc',name:'NPC guard',scope:NPC_PRESET_SCOPE,source:{disc_identity:'sha256:'+hash,scene_id:'scene://town01',entity_id:'scene://town01/actors/man-p1/0012',capture_draft_id:'authored-actor://12345678-1234-4234-8234-123456789abc',import_sha256:hash},components:{Transform:{position:{x:128,z:512}},NpcDraft:{name:'Guard default',donor_entity_id:'scene://town01/actors/man-p1/0012'}}};
const file={schema_version:NPC_PRESET_FILE_SCHEMA,source_import_sha256:hash,template};
assert.deepEqual(validateNpcPresetMetadata(template),template);assert.deepEqual(decodePresetFileExport(file,template),file);
const report={schema_version:'legaia.actor-preset-import-review.v1',review_key:hash,source_import_sha256:hash,template:{...template,id:'template://87654321-1234-4234-8234-123456789abc',name:'Transferred guard'},limitations:['Adds a library preset only.']};
assert.deepEqual(decodePresetImportReview(report,JSON.stringify(file),'Transferred guard'),report);
for(const edit of [v=>v.source.import_sha256='wrong',v=>v.source.capture_draft_id='missing',v=>v.components.Transform.position.y=0,v=>v.components.Transform.position.x=32,v=>v.components.NpcDraft.donor_entity_id='wrong',v=>v.components.NpcDraft.script='payload']){const bad=structuredClone(template);edit(bad);assert.throws(()=>validateNpcPresetMetadata(bad));}
for(const edit of [v=>v.schema_version='legaia.actor-preset-file.v1',v=>v.source_import_sha256='b'.repeat(64),v=>v.payload='private']){const bad=structuredClone(file);edit(bad);assert.throws(()=>decodePresetFileExport(bad,template));}
const bad=structuredClone(report);bad.template.components.NpcDraft.name='Changed';assert.throws(()=>decodePresetImportReview(bad,JSON.stringify(file),'Transferred guard'));
console.log('NPC preset file schema, source hashes, metadata-only shape and reviewed transfer checks pass.');

const owned=structuredClone(template),run='script://town01/actors/man-p1/0012/dialogue/0048/run/0049';owned.components.NpcDraft.dialogue={donor_entity_id:owned.source.entity_id,runs:{[run]:'SDK resident'}};
const ownedFile={schema_version:'legaia.npc-preset-file.v2',source_import_sha256:hash,template:owned},ownedReport={...report,template:{...owned,id:report.template.id,name:report.template.name}};
assert.deepEqual(decodePresetFileExport(ownedFile,owned),ownedFile);assert.deepEqual(decodePresetImportReview(ownedReport,JSON.stringify(ownedFile)+' '.repeat(9000),'Transferred guard'),ownedReport);
assert.throws(()=>decodePresetFileExport({...ownedFile,schema_version:NPC_PRESET_FILE_SCHEMA},owned));assert.throws(()=>decodePresetImportReview(report,JSON.stringify(file)+' '.repeat(9000),'Transferred guard'));
for(const mutate of [v=>v.components.NpcDraft.dialogue.donor_entity_id='wrong',v=>v.components.NpcDraft.dialogue.runs[run]='|',v=>v.components.NpcDraft.dialogue.payload='native',v=>v.components.NpcDraft.dialogue.runs={'script://town01/actors/man-p1/0049/dialogue/0048/run/0049':'Wrong'}]){const v=structuredClone(owned);mutate(v);assert.throws(()=>validateNpcPresetMetadata(v));}
const detached=validateNpcPresetMetadata(owned);detached.components.NpcDraft.dialogue.runs[run]='Independent';assert.equal(owned.components.NpcDraft.dialogue.runs[run],'SDK resident');
console.log('NPC own dialogue metadata, v2 transfer, retained v1 bounds and forged donor/control rejection pass.');

const custom=structuredClone(owned);custom.components.NpcDraft.appearance={script_donor_entity_id:custom.source.entity_id,donor_entity_id:'scene://town01/actors/man-p1/0040'};
const customFile={schema_version:'legaia.npc-preset-file.v3',source_import_sha256:hash,template:custom},customReport={...report,template:{...custom,id:report.template.id,name:report.template.name}};
assert.deepEqual(decodePresetFileExport(customFile,custom),customFile);assert.deepEqual(decodePresetImportReview(customReport,JSON.stringify(customFile),'Transferred guard'),customReport);assert.throws(()=>decodePresetFileExport({...customFile,schema_version:'legaia.npc-preset-file.v2'},custom));
const forged=structuredClone(custom);forged.components.NpcDraft.appearance.script_donor_entity_id='wrong';assert.throws(()=>validateNpcPresetMetadata(forged));
console.log('NPC preset v3 retains independent appearance and own dialogue; wrong script witness and older format reject.');

const waiting=structuredClone(custom),wait='script://town01/actors/man-p1/0012/wait/0065';waiting.components.NpcDraft.waits={donor_entity_id:waiting.source.entity_id,entries:{[wait]:{duration_ticks:11}}};
const waitFile={schema_version:'legaia.npc-preset-file.v4',source_import_sha256:hash,template:waiting},waitReport={...report,template:{...waiting,id:report.template.id,name:report.template.name}};
assert.deepEqual(decodePresetFileExport(waitFile,waiting),waitFile);assert.deepEqual(decodePresetImportReview(waitReport,JSON.stringify(waitFile),'Transferred guard'),waitReport);assert.throws(()=>decodePresetFileExport({...waitFile,schema_version:'legaia.npc-preset-file.v3'},waiting));
for(const mutate of [v=>v.components.NpcDraft.waits.donor_entity_id='wrong',v=>v.components.NpcDraft.waits.entries[wait].duration_ticks=true,v=>v.components.NpcDraft.waits.entries[wait].duration_ticks=32768,v=>v.components.NpcDraft.waits.entries[wait].seconds=1,v=>v.components.NpcDraft.waits.entries={'script://town01/actors/man-p1/0040/wait/0065':{duration_ticks:1}}]){const v=structuredClone(waiting);mutate(v);assert.throws(()=>validateNpcPresetMetadata(v));}
console.log('NPC preset v4 retains own wait targets with dialogue/appearance and rejects forged ownership/types/older format.');
