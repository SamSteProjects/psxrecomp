import {triggerScriptEditable} from './trigger-scripts.js';
import {decodeAssetReferences} from './asset-references.js';
import {renderComponentProperties,renderComponentActions,bindComponentActions} from './component-inspector.js';

const TYPES={actor:'AssetActor',scene:'AssetScene',template:'AssetTemplate',worldmap:'AssetWorldmap',model:'AssetModel',texture:'AssetTexture',animation:'AssetAnimation',script:'AssetScript',dialogue:'AssetDialogue',flag:'AssetFlag',transition:'AssetTransition',collision:'AssetCollision',trigger:'AssetTrigger',region:'AssetRegion'};
const ACTION_TYPES={'select-asset-actor':['actor'],'inspect-npc-donor-model':['actor'],'inspect-npc-donor-script':['actor'],'inspect-npc-build-script':['actor'],'edit-npc-dialogue':['actor'],'edit-npc-waits':['actor'],'edit-npc-appearance':['actor'],'open-asset-scene':['scene'],'open-asset-template':['template'],'open-asset-worldmap':['worldmap'],'inspect-landmark-destination':['worldmap'],'inspect-asset-model':['model'],'inspect-asset-texture':['texture'],'inspect-asset-animation':['animation'],'inspect-asset-script':['script','dialogue'],'inspect-asset-flag':['flag'],'inspect-asset-transition':['transition'],'inspect-asset-field':['collision','trigger','region'],'inspect-asset-region-bounds':['region'],'inspect-asset-trigger-cells':['trigger'],'inspect-asset-trigger-scripts':['trigger'],'inspect-asset-trigger-group':['trigger']};
export function assetInspectorDefinition(schema,record){
  if(record?.type==='actor'&&Object.hasOwn(record.authoredRecord??{},'draft')){
    const authored=record.authoredRecord,value=authored.authored;
    if(authored.draft!==true||authored.kind!=='actor'||authored.id!==record.id||!/^authored-actor:\/\/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(record.id)||authored.scene_id!==record.sceneId||value?.scene_id!==authored.scene_id||value?.donor_entity_id!==authored.donor_entity_id||value?.name!==authored.name||['x','z'].some(axis=>!Number.isSafeInteger(value?.position?.[axis])||value.position[axis]%64||value.position[axis]<64||value.position[axis]>16384))throw new Error('NPC draft asset differs from its authored SDK record');
    if(schema?.authored_asset_inspectors?.npc_draft!=='AssetNpcDraft')throw new Error('Unsupported NPC draft asset inspector descriptor');
    npcDonorModel(record);return 'AssetNpcDraft';
  }
  const expected=TYPES[record?.type];if(!expected)return null;
  if(schema?.asset_inspectors?.[record.type]!==expected)throw new Error('Unsupported asset inspector descriptor');
  return expected;
}
export function npcDonorModel(record){
  const authored=record?.authoredRecord,ref=authored?.model_reference;
  if(authored?.draft!==true||!ref)return null;
  if(ref.source_id!==record.id||ref.source_name!==authored.name||ref.scene_id!==record.sceneId||ref.kind!=='draft_initial_model_assignment'||ref.imported!==false||ref.effective!==true||ref.effective_donor_id!==(authored.authored?.appearance?.donor_entity_id??authored.donor_entity_id)||ref.runtime_binding!=='not_asserted'||typeof ref.target_id!=='string'||!ref.target_id.startsWith('asset://'))throw new Error('NPC recorded donor model differs from its SDK assignment.');
  return ref.target_id;
}
export function npcDonorScript(record){
  const authored=record?.authoredRecord,draft=authored?.authored;if(authored?.draft!==true)return null;
  if(record.type!=='actor'||authored.id!==record.id||authored.kind!=='actor'||authored.scene_id!==record.sceneId||draft?.scene_id!==record.sceneId||draft?.name!==authored.name||draft?.donor_entity_id!==authored.donor_entity_id||typeof authored.donor_entity_id!=='string'||!authored.donor_entity_id.startsWith(record.sceneId+'/actors/man-p1/'))throw new Error('NPC retail donor script binding differs from its authored SDK record.');
  return authored.donor_entity_id;
}
export function assetInspectorRegistry(record,activate){
  return Object.fromEntries(Object.entries(ACTION_TYPES).filter(([id,types])=>types.includes(record.type)&&(id!=='inspect-npc-donor-model'||npcDonorModel(record)!==null)&&(!['inspect-npc-donor-script','inspect-npc-build-script','edit-npc-dialogue','edit-npc-waits','edit-npc-appearance'].includes(id)||npcDonorScript(record)!==null)&&(id!=='inspect-asset-trigger-group'||record.data?.table_source==='primary'&&[0,1].includes(record.data?.table_kind))&&(id!=='inspect-asset-trigger-scripts'||triggerScriptEditable(record))).map(([id])=>[id,{run:()=>activate(record,id)}]));
}
export function mountAssetInspector(host,{schema,record,capabilities,current,busy,activate,onError}){
  const id=assetInspectorDefinition(schema,record);if(!id)return false;
  const registry=assetInspectorRegistry(record,activate),definition=schema.components[id];
  const heading=document.createElement('h3');heading.textContent=definition.label;host.append(heading);
  const properties=document.createElement('div');properties.innerHTML=renderComponentProperties(schema,id,record);host.append(properties);
  const actions=document.createElement('div');actions.className='dialog-actions';actions.innerHTML=renderComponentActions(schema,id,record,capabilities,registry,false);host.append(actions);
  bindComponentActions(actions,registry,{current,editable:()=>false,busy,onError});
  return true;
}

// The graph qualifies source targets; this adapter only presents SDK layers.
export function triggerBindingSummary(report){
  const retail=report.outgoing.find(edge=>edge.kind==='field_trigger_script_reference');
  const authored=report.outgoing.find(edge=>edge.kind==='effective_field_trigger_script_reference');
  const nodes=new Map(report.nodes.map(node=>[node.id,node]));
  const target=edge=>edge?nodes.get(edge.target_id):null;
  return {retail:target(retail),authored:target(authored),current:target(authored??retail)};
}
export function mountTriggerBindingInspector(host,{record,getState,current,busy,onInspect,request=fetch}){
  if(record.type!=='trigger'||record.data?.table_kind!==1||record.data?.encoded?.gate!==1||record.sceneId!==getState().scene?.id||!getState().capabilities?.asset_references)return null;
  const key=getState().asset_reference_source_key,controller=new AbortController(),section=document.createElement('section');section.dataset.triggerBindingInspector='';
  const heading=document.createElement('h4');heading.textContent='Script binding';const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Verifying source targets…';const content=document.createElement('div');section.append(heading,status,content);host.append(section);
  let disposed=false;
  const fresh=()=>!disposed&&current()&&key===getState().asset_reference_source_key&&getState().capabilities?.asset_references===true;
  const dispose=()=>{disposed=true;controller.abort();};
  const ready=(async()=>{try{
    const response=await request('/api/asset-references',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id}),signal:controller.signal}),value=await response.json();
    if(!fresh())return;if(!response.ok||value.error)throw new Error(value.error??'Trigger reference verification failed.');
    const layers=triggerBindingSummary(decodeAssetReferences(value,record.id,key));
    for(const [layer,label] of [['retail','Retail'],['authored','Authored'],['current','Current']]){
      const row=document.createElement('div');row.className='property';row.dataset.triggerBindingLayer=layer;const title=document.createElement('span');title.textContent=label;const target=layers[layer],identity=document.createElement('code');identity.textContent=target?.id??(layer==='authored'?'None · inherit':'Unresolved source target');row.append(title,identity);content.append(row);
      if(target){const button=document.createElement('button');button.type='button';button.textContent=`Inspect ${label} script`;button.dataset.triggerBindingTarget=target.id;button.disabled=!target.available;button.onclick=async()=>{if(!fresh()){status.textContent='Project sources changed. Reopen this Inspector.';return;}if(busy()||!target.available)return;try{await onInspect(target);}catch(error){status.textContent=error.message;}};content.append(button);}
    }
    status.textContent='Source binding only. Activation, execution and gameplay reachability are not established.';
  }catch(error){if(!controller.signal.aborted&&fresh()){content.replaceChildren();status.textContent=error.message;}}})();
  return {dispose,ready};
}
