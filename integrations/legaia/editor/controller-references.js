import {decodeControllerFlagQualification} from './flag-qualification.js';
// Ownership describes the Retail record, never scheduling or live execution.
const exact=(value,keys)=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
export function validateControllerSourceEvidence(p,scene){
 const s=p?.source_record,name=scene?.slice(8);
 if(!exact(p,['source_record','entry_pc','local_count','reference_commit','relationship','execution'])||!exact(s,['disc_identity','iso_file','prot_entry','prot_entry_name','record_kind','record_index','byte_coordinate_space','byte_offset','byte_length','containing_decoded_size','sha256'])||!scene?.startsWith('scene://')||p.relationship!=='retail_scene_entry_record'||p.execution!=='not_asserted'||p.reference_commit!=='d6e64c68ede25813d35db20980da82a1a025549b'||typeof s.disc_identity!=='string'||!s.disc_identity.startsWith('sha256:')||!hash(s.disc_identity.slice(7))||s.iso_file!=='PROT.DAT'||s.prot_entry_name!==name||!integer(s.prot_entry,0,65535)||s.record_kind!=='man_partition_1_scene_controller'||s.record_index!==0||s.byte_coordinate_space!=='decoded_man_payload'||!integer(s.containing_decoded_size,1,4*1024*1024)||!integer(s.byte_offset,0,s.containing_decoded_size-1)||!integer(s.byte_length,1,Math.min(65536,s.containing_decoded_size-s.byte_offset))||!hash(s.sha256)||!integer(p.local_count,0,255)||!integer(p.entry_pc,5,s.byte_length-1)||p.entry_pc!==1+p.local_count*2+4)throw Error('Invalid Retail controller source evidence.');
 return structuredClone(p);
}
export function validateControllerReference(edge,nodes){
 const p=validateControllerSourceEvidence(edge.controller_source_evidence,edge.scene_id),name=edge.scene_id.slice(8),source=nodes.get(edge.source_id),target=nodes.get(edge.target_id);
 if(!exact(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','source_catalog_key','controller_source_evidence'])||edge.kind!=='scene_entry_controller_source'||edge.layer!=='decoded'||edge.runtime_binding!=='not_asserted'||!hash(edge.source_catalog_key)||edge.source_id!==edge.scene_id||edge.target_id!==`script://${name}/controllers/man-p1/0000`||source?.kind!=='scene'||target?.kind!=='controller'||source.scene_id!==edge.scene_id||target.scene_id!==edge.scene_id||source.available!==true||target.available!==true)throw Error('Invalid Retail scene/controller ownership reference.');
 return p;
}
export function validateControllerFlagReference(edge,nodes){
 const p=validateControllerSourceEvidence(edge.controller_source_evidence,edge.scene_id),f=edge.flag_reference_evidence,source=nodes.get(edge.source_id),target=nodes.get(edge.target_id);
 const scopes={local:'dispatch_context_local_flags',context:'dispatch_context_flags',global:'host_global_flags',system:'system_bank_encoded_selector',extra:'host_extra_flags'},prefix={local:'LFLAG',context:'CFLAG',global:'GFLAG',system:'SYSFLAG'}[f?.bank];
 if(!exact(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','source_catalog_key','pc','controller_source_evidence','flag_reference_evidence'])||!exact(f,['bank','index','scope','extended_target','grouping_layer','operation','mnemonic'])||edge.kind!=='controller_flag_reference'||edge.layer!=='decoded'||edge.runtime_binding!=='not_asserted'||!hash(edge.source_catalog_key)||edge.source_id!==`script://${edge.scene_id.slice(8)}/controllers/man-p1/0000`||source?.kind!=='controller'||target?.kind!=='flag'||source.scene_id!==edge.scene_id||target.scene_id!==edge.scene_id||source.available!==true||target.available!==true||!integer(edge.pc,p.entry_pc,p.source_record.byte_length-1)||!Object.hasOwn(scopes,f.bank)||f.scope!==scopes[f.bank]||!integer(f.index,0,f.bank==='system'?65535:31)||f.grouping_layer!=='retail'||!(f.extended_target===null||integer(f.extended_target,0,255))||edge.target_id!==edge.source_id.replace('script://','flag-reference://')+`/${f.extended_target===null?'current':'extended-'+f.extended_target}/${f.bank}/${f.index}`||!(prefix&&['set','clear','test'].includes(f.operation)&&f.mnemonic===prefix+'_'+f.operation.toUpperCase()||f.operation==='test'&&(f.mnemonic==='FLAG_WORD_BRANCH'&&['local','global','context'].includes(f.bank)||f.mnemonic==='COND_JMP'&&f.bank==='extra')))throw Error('Invalid read-only controller flag reference.');
 return p;
}

export function validateEffectiveControllerFlagReference(edge,nodes){
 const b=edge.flag_binding_evidence,f=edge.flag_reference_evidence;
 if(!exact(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','source_catalog_key','pc','controller_source_evidence','flag_reference_evidence','flag_binding_evidence'])||edge.kind!=='effective_controller_flag_reference'||edge.layer!=='effective'||!exact(b,['operand_id','retail_index','effective_index','source_record_sha256','component_sha256','native_operand_qualification']))throw Error('Invalid Current controller flag relationship.');
 const retail={...edge,kind:'controller_flag_reference',layer:'decoded'};delete retail.flag_binding_evidence;
 const p=validateControllerFlagReference(retail,nodes);
 if(f.bank!=='system'||f.extended_target!==null||!integer(f.index,0,4095)||b.retail_index!==f.index||b.source_record_sha256!==p.source_record.sha256||!hash(b.component_sha256))throw Error('Current controller flag differs from Retail source ownership.');
 decodeControllerFlagQualification(b.native_operand_qualification,{owner_id:edge.source_id.replace('script://','scene://'),operand_id:b.operand_id,source_record_sha256:b.source_record_sha256,pc:edge.pc,mnemonic:f.mnemonic,extended_target:f.extended_target,retail_index:b.retail_index,authored_index:b.effective_index});
 return p;
}
