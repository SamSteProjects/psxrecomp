import {renderComponentProperties,renderComponentDetails,renderComponentActions,bindComponentActions} from './component-inspector.js';
const kinds={ControllerSystemFlags:'system-flag',ControllerBranches:'branch',ControllerTileRects:'tile-rect',ControllerFades:'fade',ControllerTableCopies:'table-copy',ControllerWordTriplets:'word-triplet',ControllerThreeWords:'three-word',ControllerSceneBytes:'scene-byte',ControllerFiveWords:'five-word',ControllerGlobalBytes:'global-byte',ControllerPartySelectors:'party-selector',ControllerFlagBits:'flag-bit'};
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
export function controllerOwnerComponents(record,sceneId){
 if(record?.kind!=='controller'||typeof sceneId!=='string'||!/^scene:\/\/[A-Za-z0-9_-]{1,128}$/.test(sceneId)||record.scene_id!==sceneId||record.id!==sceneId.replace('scene://','script://')+'/controllers/man-p1/0000'||!record.authored||Array.isArray(record.authored)||typeof record.authored!=='object')throw Error('Choose an authored controller in its owning scene.');
 const components={};let sourceHash=null;
 for(const [family,value] of Object.entries(record.authored)){
  const entries=value?.entries;
  if(!Object.hasOwn(kinds,family)||!hash(value?.source_record_sha256)||!entries||typeof entries!=='object'||Array.isArray(entries)||Object.keys(entries).length>1024||sourceHash!==null&&sourceHash!==value.source_record_sha256)throw Error('Authored controller component source is invalid.');
  sourceHash=value.source_record_sha256;const ids=Object.keys(entries);
  for(const id of ids){const prefix=record.id+'/'+kinds[family]+'/';if(!id.startsWith(prefix)||!/^[a-f0-9]{4}$/.test(id.slice(prefix.length))||!entries[id]||typeof entries[id]!=='object'||Array.isArray(entries[id]))throw Error('Authored controller operand has foreign ownership.');}
  if(ids.length)components[family]={source_record_sha256:sourceHash,authored_instruction_count:ids.length,first_pc:Math.min(...ids.map(id=>parseInt(id.slice(-4),16))),entries:structuredClone(entries)};
 }
 return components;
}
export function controllerAssetSourceHash(record){
 const components=record.authoredRecord?controllerOwnerComponents(record.authoredRecord,record.sceneId):{},authored=Object.values(components)[0]?.source_record_sha256,source=record.data?.source_record?.sha256;
 if(source!==undefined&&!hash(source)||authored&&source&&authored!==source||!hash(source??authored))throw Error('Controller asset source changed. Refresh resources.');
 return source??authored;
}
export function mountControllerOwnerInspector(host,{record,schema,capabilities,current,editable,busy,onInspect,onError=()=>{}}){
 if(!record.authoredRecord)return null;
 const components=controllerOwnerComponents(record.authoredRecord,record.sceneId);if(!Object.keys(components).length)return null;
 const section=document.createElement('section');section.dataset.controllerOwnerInspector='';const heading=document.createElement('h3');heading.textContent='Authored Controller Components';section.append(heading);
 const actions={'inspect-controller-component':{requiresEdit:true,run:({componentId})=>onInspect(componentId,components[componentId].first_pc)}};
 for(const [id,value] of Object.entries(components)){
  if(!schema?.components?.[id])throw Error('Controller component Inspector metadata is unavailable.');
  const part=document.createElement('section');part.className='component';const title=document.createElement('h4');title.textContent=schema.components[id].label;part.append(title);const content=document.createElement('div');content.innerHTML=renderComponentProperties(schema,id,value,false,true)+renderComponentActions(schema,id,value,capabilities,actions,editable())+renderComponentDetails(schema,id,value);part.append(content);section.append(part);
 }
 host.append(section);bindComponentActions(section,actions,{current,editable,busy,onError});return section;
}
