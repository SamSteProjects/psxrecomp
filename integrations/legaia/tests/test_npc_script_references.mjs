import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {decodeAssetReferences,assetReferenceRelationLabel} from '../editor/asset-references.js';
const h='a'.repeat(64),owner='authored-actor://fixture',scene='scene://fixture',donor=scene+'/actors/man-p1/0001',script='script://fixture/actors/man-p1/0001';
const proof={donor_entity_id:donor,source_record_sha256:h,reference_commit:'d6e64c68ede25813d35db20980da82a1a025549b',record_index:1,byte_offset:100,byte_length:50,byte_coordinate_space:'decoded_lzs_descriptor',authored_draft_sha256:h,script_status:'partial'};
const edge={id:h,source_id:owner,target_id:script,kind:'draft_script_donor',scene_id:scene,layer:'authored',runtime_binding:'not_asserted',source_import_sha256:h,source_catalog_key:h,npc_script_donor_evidence:proof};
const report={schema_version:'legaia.asset-references.v1',asset_id:owner,source_key:h,read_only:true,nodes:[{id:owner,kind:'actor',scene_id:scene,label:'NPC',available:true},{id:script,kind:'script',scene_id:scene,label:'Script',available:true}],incoming:[],outgoing:[edge],coverage:{verified_scene_ids:[scene],resource_scene_id:scene,unresolved_reference_count:0},limitations:[]};
decodeAssetReferences(report,owner,h);assert.match(assetReferenceRelationLabel(edge),/retail script donor/);
for(const mutate of [v=>v.outgoing[0].layer='effective',v=>v.outgoing[0].runtime_binding='confirmed',v=>v.outgoing[0].kind='draft_donor',v=>v.outgoing[0].npc_script_donor_evidence.source_record_sha256='bad',v=>v.outgoing[0].npc_script_donor_evidence.donor_entity_id='scene://other/actors/man-p1/0001',v=>v.outgoing[0].npc_script_donor_evidence.record_index=2,v=>v.outgoing[0].npc_script_donor_evidence.byte_length=4*1024*1024,v=>v.outgoing[0].npc_script_donor_evidence.reference_commit='0'.repeat(40),v=>v.outgoing[0].npc_script_donor_evidence.generated_sha256=h,v=>v.nodes[1].available=false,v=>v.outgoing.push({...v.outgoing[0],id:'b'.repeat(64)})]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeAssetReferences(bad,owner,h));}
if(process.argv[2]){
 const value=JSON.parse(readFileSync(process.argv[2],'utf8'));
 for(const [scope,reports] of [['active',value.active],['project',value.project]])for(const actual of reports){const result=decodeAssetReferences(actual,actual.asset_id,actual.source_key,scope);assert((result.incoming.concat(result.outgoing)).some(e=>e.kind==='draft_script_donor'));}
}
console.log('NPC script donor navigation: strict evidence, unavailable/live/duplicate rejection and optional actual retail reports passed.');
