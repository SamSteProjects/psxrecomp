import {glbAnimationDocument} from './animation-glb-clips.js';

export function validateModelObjectMapping(value,count){
  if(!Number.isSafeInteger(count)||count<1||count>1024||!Array.isArray(value)||value.length!==count||new Set(value).size!==count||value.some(v=>!Number.isSafeInteger(v)||v<0||v>=1024))throw new Error('Map every native model object to one distinct GLB node index (0-1023).');
  return structuredClone(value);
}
export function withModelObjectMapping(binding,text){
  const value=structuredClone(binding);if(!text.trim())return value;
  if(text.length>6144)throw new Error('Model object mapping exceeds its text budget.');
  const parts=text.trim().split(/[\s,]+/);if(parts.some(p=>!/^(0|[1-9][0-9]*)$/.test(p)))throw new Error('Model object mapping requires GLB node indices separated by commas.');
  value.external_object_nodes=validateModelObjectMapping(parts.map(Number),Array.isArray(value.profile?.objects)?value.profile.objects.length:NaN);return value;
}
export function modelNodeInventory(bytes){
  const nodes=glbAnimationDocument(bytes).nodes??[];
  if(!Array.isArray(nodes)||nodes.length>1024||nodes.some(n=>!n||typeof n!=='object'||Array.isArray(n)||n.name!==undefined&&typeof n.name!=='string'))throw new Error('Choose a model GLB with at most 1024 nodes.');
  return nodes.map((node,index)=>`${index}: ${(node.name??'Unnamed node').replace(/[\x00-\x1f]/g,' ').slice(0,128)}${Object.hasOwn(node,'mesh')?' · mesh '+node.mesh:' · group or empty object'}`).join('\n');
}
export function createModelMappingControl(){
  const label=document.createElement('label');label.textContent='External model mapping: GLB node indices in native object order (optional)';
  const input=document.createElement('input');input.setAttribute('aria-label','External model object mapping');input.placeholder='0, 1, 2: blank uses binding or source tags';input.maxLength=6144;Object.assign(input.style,{width:'100%',minWidth:'0'});label.append(input);
  const details=document.createElement('details'),summary=document.createElement('summary'),inventory=document.createElement('pre');summary.textContent='GLB node indices and names';Object.assign(inventory.style,{maxHeight:'200px',overflow:'auto',whiteSpace:'pre-wrap',overflowWrap:'anywhere'});inventory.textContent='Choose an edited GLB to list its nodes.';details.append(summary,inventory);return {input,label,details,inventory};
}
