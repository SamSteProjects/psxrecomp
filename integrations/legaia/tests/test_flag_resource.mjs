import assert from 'node:assert/strict';
import {decodeFlagResource,flagResourceNavigationAllowed,openFlagResource} from '../editor/flag-resource.js';

function resource({bank='local',index=2,target=null,partition=1,mnemonic=null,authored=3}={}){
  const route=partition===1?'actors/man-p1':'scripts/man-p2',script=`script://fixture/${route}/0001`,context=target===null?'current':`extended-${target}`;
  const scope={local:'dispatch_context_local_flags',global:'host_global_flags',context:'dispatch_context_flags',system:'system_bank_encoded_selector',extra:'host_extra_flags'}[bank];
  mnemonic??={local:'LFLAG_SET',global:'GFLAG_TEST',context:'CFLAG_CLEAR',system:'SYSFLAG_TEST',extra:'COND_JMP'}[bank];
  const authorable=/^(LFLAG|GFLAG|CFLAG)_/.test(mnemonic),operation=mnemonic==='FLAG_WORD_BRANCH'||mnemonic==='COND_JMP'?'test':mnemonic.split('_')[1].toLowerCase();
  const references=[5,9].map((pc,i)=>({pc,byte_offset:128+pc,mnemonic,bank,operation,index,scope,extended_target:target,context_resolution:target===null?'current_script_context':'extended_target_unresolved',index_semantics:bank==='system'?'encoded_selector_not_resolved_runtime_bit':'operand_masked_to_five_bits',status:bank==='local'&&index>=16?'bank_width_unresolved':'encoded_reference',runtime_value:null,retail_index:index,authored_index:i===0&&authorable?authored:null,effective_index:i===0&&authorable?(authored??index):index,flag_operand_id:authorable?`${script}/flag-bit/${pc.toString(16).padStart(4,'0')}`:null}));
  const id=script.replace('script://','flag-reference://')+`/${context}/${bank}/${index}`;
  return {semantic_id:id,asset_kind:'flag',id,script_id:script,script_name:'Fixture source script',owner_id:'scene://'+script.slice(9),partition,script_status:'decoded_supported_paths',source_record:{synthetic:true,partition,record_index:1,byte_offset:128,byte_length:32,sha256:'a'.repeat(64),additional_provenance:{carrier:'synthetic source',evidence:['fixture']}},bank,index,scope,extended_target:target,runtime_binding:'unresolved',runtime_value:null,grouping_layer:'retail',read_only:true,references,reference_count:2,authored_reference_count:references.filter(row=>row.authored_index!==null).length,coverage:{script_count:4,partial_script_count:1,unavailable_script_count:1},limitations:['Source-qualified operands; no runtime variable binding.','Unknown and unvisited paths remain outside coverage.']};
}
const source=resource(),before=structuredClone(source),decoded=decodeFlagResource(source);
decoded.references[0].effective_index=99;decoded.source_record.additional_provenance.evidence.push('detached');decoded.coverage.partial_script_count=0;decoded.limitations.pop();assert.deepEqual(source,before);
for(const options of [{bank:'global',partition:2,target:255},{bank:'context',target:0},{bank:'system',index:0x8301,target:5},{bank:'extra',index:31},{bank:'local',index:19,mnemonic:'FLAG_WORD_BRANCH'},{bank:'context',mnemonic:'FLAG_WORD_BRANCH'}])decodeFlagResource(resource(options));
const minimalProvenance=resource();minimalProvenance.source_record={synthetic:true};decodeFlagResource(minimalProvenance);
const extendedMetadata=resource();extendedMetadata.catalog_limitations=['Metadata inherited from the source catalog.'];assert.deepEqual(decodeFlagResource(extendedMetadata).catalog_limitations,extendedMetadata.catalog_limitations);
const supported=resource({authored:null});supported.script_status='decoded_supported_paths';supported.coverage={script_count:1,partial_script_count:0,unavailable_script_count:0};assert.equal(decodeFlagResource(supported).script_status,'decoded_supported_paths');
const partial=resource({authored:null});partial.script_status='partial';assert.equal(decodeFlagResource(partial).script_status,'partial');
for(const mutate of [
  data=>data.runtime_value=1,data=>data.runtime_binding='confirmed',data=>data.read_only=false,data=>data.grouping_layer='effective',data=>data.asset_kind='variable',data=>data.semantic_id=data.id='flag://global/2',data=>data.id+='-other',data=>data.script_id='script://other/actors/man-p1/0001',data=>data.script_id=[data.script_id],data=>data.owner_id='scene://fixture/actors/man-p1/0002',data=>data.partition=2,data=>data.extended_target=256,data=>data.index=32,data=>data.scope='universal_story_flag',data=>data.script_status='unavailable',data=>data.script_status='partial',data=>data.source_record.byte_length=9,data=>data.source_record.byte_offset=129,data=>data.source_record.record_index=2,data=>data.source_record.sha256='invalid',data=>data.source_record.prot_entry_name='other',data=>data.source_record.payload=[1,2],data=>data.source_record.byte_length=65537,data=>data.references=[],data=>data.reference_count=3,data=>data.authored_reference_count=0,data=>data.references[0].runtime_value=false,data=>data.references[0].runtime_binding='known',data=>data.references[0].pc=9,data=>data.references[0].pc=-1,data=>data.references[0].byte_offset+=1,data=>data.references[0].bank='global',data=>data.references[0].index=3,data=>data.references[0].retail_index=3,data=>data.references[0].authored_index=true,data=>data.references[0].effective_index=2,data=>data.references[0].flag_operand_id+='/other',data=>data.references[0].operation='clear',data=>data.references[0].context_resolution='resolved_actor',data=>data.references[0].index_semantics='runtime_global_bit',data=>data.references[0].status='confirmed',data=>data.references[0].mnemonic='GFLAG_SET',data=>data.references[0].mnemonic=['LFLAG_SET'],data=>data.references[0].scope='host_global_flags',data=>data.references[0].extended_target=7,data=>data.coverage.unavailable_script_count=4,data=>data.coverage.script_count=1025,data=>data.limitations=[1],data=>data.source_record.circular=data
]){const malformed=structuredClone(source);mutate(malformed);assert.throws(()=>decodeFlagResource(malformed));}
for(const data of [resource({bank:'local',index:16}),resource({bank:'local',authored:16}),resource({bank:'context',index:8,mnemonic:'CFLAG_SET'}),resource({bank:'context',authored:8,mnemonic:'CFLAG_SET'}),resource({bank:'context',index:10,mnemonic:'CFLAG_CLEAR'}),resource({bank:'context',authored:10,mnemonic:'CFLAG_CLEAR'})])assert.throws(()=>decodeFlagResource(data));
for(const options of [{bank:'local',index:16},{bank:'context',index:8,mnemonic:'CFLAG_SET'},{bank:'context',index:10,mnemonic:'CFLAG_CLEAR'}])decodeFlagResource(resource({...options,authored:null}));
const inconsistentCoverage=structuredClone(partial);inconsistentCoverage.coverage.partial_script_count=0;assert.throws(()=>decodeFlagResource(inconsistentCoverage));
const system=resource({bank:'system',index:65536});assert.throws(()=>decodeFlagResource(system));
const branch=resource({mnemonic:'FLAG_WORD_BRANCH'});branch.references[0].authored_index=3;branch.references[0].effective_index=3;branch.authored_reference_count=1;assert.throws(()=>decodeFlagResource(branch));
const tooMany=resource();tooMany.references=Array.from({length:16385},()=>tooMany.references[0]);tooMany.reference_count=tooMany.references.length;assert.throws(()=>decodeFlagResource(tooMany));

const metadata=decodeFlagResource(source),gates={current:true,busy:false,canInspect:true};
for(const pc of [null,5,9])assert.equal(flagResourceNavigationAllowed(metadata,pc,gates),true);
for(const pc of [undefined,0,-1,8,65536,'5',{},true])assert.equal(flagResourceNavigationAllowed(metadata,pc,gates),false);
for(const changes of [{current:false},{busy:true},{canInspect:false},{open:false},{pending:true},{current:1},{busy:undefined}])assert.equal(flagResourceNavigationAllowed(metadata,5,{...gates,...changes}),false);
assert.equal(flagResourceNavigationAllowed(metadata,5),false);assert.equal(flagResourceNavigationAllowed(null,null,gates),false);

// A small DOM double verifies dispatch and closed-dialog late-result handling offline.
class Node {
  constructor(tag){this.tagName=tag;this.children=[];this.style={};this.attributes={};this.listeners={};this.open=false;this.textContent='';}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;}
  setAttribute(key,value){this.attributes[key]=value;}
  addEventListener(type,callback){this.listeners[type]=callback;}
  showModal(){this.open=true;}
  close(){this.open=false;this.listeners.close?.();}
  remove(){this.removed=true;}
}
const previousDocument=globalThis.document;globalThis.document={createElement:tag=>new Node(tag),body:new Node('body')};
const descendants=node=>[node,...node.children.flatMap(descendants)],button=(dialog,label)=>descendants(dialog).find(node=>node.tagName==='button'&&node.textContent===label);
const record={id:source.id,type:'flag',label:'Local flag reference 2',source:'fixture',sceneId:'scene://fixture',data:source};
let current=true,busy=false,canInspect=true,calls=[],errors=[];
const settings={record,current:()=>current,busy:()=>busy,canInspect:()=>canInspect,onInspect:pc=>{calls.push(pc);return true;},onError:error=>errors.push(error)};
try{
  let dialog=openFlagResource(settings);assert.ok(dialog.open);assert.ok(descendants(dialog).some(node=>node.textContent.includes('4 scripts · 1 partial · 1 unavailable')));assert.ok(descendants(dialog).some(node=>node.textContent==='Unavailable · source binding unresolved'));
  current=false;await button(dialog,'Inspect 0x0005').onclick();assert.deepEqual(calls,[]);current=true;busy=true;await button(dialog,'Inspect first operand').onclick();assert.deepEqual(calls,[]);busy=false;canInspect=false;await button(dialog,'Inspect parent script').onclick();assert.deepEqual(calls,[]);canInspect=true;
  await button(dialog,'Inspect last operand').onclick();assert.deepEqual(calls,[9]);assert.equal(dialog.open,false);assert.equal(dialog.removed,true);
  dialog=openFlagResource(settings);await button(dialog,'Inspect parent script').onclick();assert.deepEqual(calls,[9,null]);
  let finish;dialog=openFlagResource({...settings,onInspect:pc=>{calls.push(pc);return new Promise(resolve=>{finish=resolve;});}});const exact=button(dialog,'Inspect 0x0005'),first=button(dialog,'Inspect first operand');const pending=exact.onclick();assert.equal(first.disabled,true);await first.onclick();assert.deepEqual(calls,[9,null,5]);dialog.close();finish(true);assert.equal(await pending,false);assert.equal(dialog.removed,true);assert.equal(errors.length,0);
  dialog=openFlagResource({...settings,onInspect:()=>false});assert.equal(await button(dialog,'Inspect first operand').onclick(),false);assert.equal(dialog.open,true);dialog.close();
  current=false;assert.equal(openFlagResource(settings),null);current=true;busy=true;assert.equal(openFlagResource(settings),null);busy=false;
  assert.equal(openFlagResource({...settings,record:{...record,sceneId:'scene://other'}}),null);assert.equal(errors.length,1);assert.deepEqual(source,before);
}finally{if(previousDocument===undefined)delete globalThis.document;else globalThis.document=previousDocument;}
console.log('Flag resource source identity, operand layers, bounded detached metadata, coverage, navigation guards and closed-dialog late results passed.');
