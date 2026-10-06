import {glbAnimationDocument} from './animation-glb-clips.js';
export function validateObjectMapping(value,count){
  if(!Array.isArray(value)||value.length!==count||count<1||count>64||new Set(value).size!==count||value.some(v=>!Number.isSafeInteger(v)||v<0||v>4095))throw new Error('Map each native object to one distinct GLB node index (0-4095).');return structuredClone(value);
}
export function withObjectMapping(binding,text){
  const value=structuredClone(binding);if(!text.trim())return value;
  const parts=text.trim().split(/[\s,]+/);if(parts.some(p=>!/^(0|[1-9][0-9]*)$/.test(p)))throw new Error('Object mapping requires GLB node indices separated by commas.');value.external_object_nodes=validateObjectMapping(parts.map(Number),value.object_count);return value;
}
export function objectNodeInventory(bytes){
  const nodes=glbAnimationDocument(bytes).nodes??[];if(!Array.isArray(nodes)||nodes.length>4096||nodes.some(n=>!n||typeof n!=='object'||Array.isArray(n)||n.name!==undefined&&typeof n.name!=='string'))throw new Error('Choose a GLB with at most 4096 named rigid nodes.');
  return nodes.map((n,i)=>`${i}: ${(n.name??'Unnamed node').replace(/[\x00-\x1f]/g,' ').slice(0,128)}`).join('\n');
}
export function createObjectMappingControl(){
  const label=document.createElement('label');label.textContent='External object mapping : GLB node indices in native object order (optional)';const input=document.createElement('input');input.setAttribute('aria-label','External rigid object mapping');input.placeholder='0, 1, 2 : blank uses binding or source tags';input.maxLength=512;label.append(input);
  const details=document.createElement('details'),summary=document.createElement('summary'),inventory=document.createElement('pre');summary.textContent='GLB node indices and names';Object.assign(inventory.style,{maxHeight:'200px',overflow:'auto',whiteSpace:'pre-wrap',overflowWrap:'anywhere'});inventory.textContent='Choose an edited GLB to list its nodes.';details.append(summary,inventory);return {input,label,details,inventory};
}
