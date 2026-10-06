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
