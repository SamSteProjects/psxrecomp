import {renderComponentProperties,renderComponentActions,bindComponentActions} from './component-inspector.js';

const TYPES={model:'AssetModel',texture:'AssetTexture',animation:'AssetAnimation',script:'AssetScript',dialogue:'AssetDialogue',collision:'AssetCollision',trigger:'AssetTrigger',region:'AssetRegion'};
const ACTION_TYPES={'inspect-asset-model':['model'],'inspect-asset-texture':['texture'],'inspect-asset-animation':['animation'],'inspect-asset-script':['script','dialogue'],'inspect-asset-field':['collision','trigger','region']};
export function assetInspectorDefinition(schema,record){
  const expected=TYPES[record?.type];if(!expected)return null;
  if(schema?.asset_inspectors?.[record.type]!==expected)throw new Error('Unsupported asset inspector descriptor');
  return expected;
}
export function assetInspectorRegistry(record,activate){
  return Object.fromEntries(Object.entries(ACTION_TYPES).filter(([,types])=>types.includes(record.type)).map(([id])=>[id,{run:()=>activate(record)}]));
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
