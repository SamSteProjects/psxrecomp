import {controllerOwnerComponents,controllerAssetSourceHash} from './controller-owner-inspector.js';
import {CONTROLLER_SNAPSHOT_SCHEMAS} from './controller-workspace-snapshot.js';
import {parseHierarchyQuery} from './hierarchy-query.js';
export function hierarchyControllerRecord(record,schema){
 const result={id:record.id,name:record.label,type:'controller',components:[],attached:[],authored:'unknown',visibility:'unknown'};
 try{
  if(record.type!=='controller'||typeof record.sceneId!=='string'||!/^scene:\/\/[A-Za-z0-9_-]{1,128}$/.test(record.sceneId)||record.id!==record.sceneId.replace('scene://','script://')+'/controllers/man-p1/0000')return result;
  controllerAssetSourceHash(record);
  const components=record.authoredRecord?controllerOwnerComponents(record.authoredRecord,record.sceneId):{};
  result.components=Object.keys(components).flatMap(id=>[id,...(typeof schema?.components?.[id]?.label==='string'?[schema.components[id].label]:[])]);
  result.attached=[...result.components];
  result.authored=Object.keys(components).length?'true':'false';
 }catch{/* Incoherent source metadata stays unknown rather than inheriting a false authored state. */}
 return result;
}
export function hierarchyNeedsControllerResources(query,schema){
 let tokens;try{tokens=parseHierarchyQuery(query);}catch{return false;}
 if(tokens.some(token=>token.field==='type'&&(token.exclude?'controller'.includes(token.text):!'controller'.includes(token.text))||token.field==='visibility'&&(token.exclude?'unknown'.includes(token.text):!'unknown'.includes(token.text))))return false;
 const labels=['scene entry controller',...Object.keys(CONTROLLER_SNAPSHOT_SCHEMAS).flatMap(id=>[id.toLowerCase(),String(schema?.components?.[id]?.label??'').toLowerCase()])].filter(Boolean);
 return tokens.some(token=>!token.exclude&&(token.field==='type'?'controller'.includes(token.text):token.field==='authored'?['true','false'].some(value=>value.includes(token.text)):['component','attached'].includes(token.field)?labels.some(label=>label.includes(token.text)):token.field==='name'?'scene entry controller'.includes(token.text):(token.field===null||token.field==='id')&&(token.text.startsWith('script://')||token.text.includes('/controllers')||token.field===null&&labels.some(label=>label.includes(token.text)))));
}
