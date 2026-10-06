import {glbAnimationDocument} from './animation-glb-clips.js';
export function validateObjectMapping(value,count){
  if(!Array.isArray(value)||value.length!==count||count<1||count>64||new Set(value).size!==count||value.some(v=>!Number.isSafeInteger(v)||v<0||v>4095))throw new Error('Map each native object to one distinct GLB node index (0-4095).');return structuredClone(value);
}
export function withObjectMapping(binding,text,skinText=undefined){
  const value=structuredClone(binding);if(skinText!==undefined){if(skinText.trim()){if(!/^(0|[1-9][0-9]*)$/.test(skinText.trim())||Number(skinText)>63)throw Error('Choose a skin index from 0 to 63.');value.external_skin_index=Number(skinText);}else delete value.external_skin_index;}if(!text.trim())return value;
  const parts=text.trim().split(/[\s,]+/);if(parts.some(p=>!/^(0|[1-9][0-9]*)$/.test(p)))throw new Error('Object mapping requires GLB node indices separated by commas.');value.external_object_nodes=validateObjectMapping(parts.map(Number),value.object_count);return value;
}
export function objectNodeInventory(bytes){
  const doc=glbAnimationDocument(bytes),nodes=doc.nodes??[];if(!Array.isArray(nodes)||nodes.length>4096||nodes.some(n=>!n||typeof n!=='object'||Array.isArray(n)||n.name!==undefined&&typeof n.name!=='string'))throw new Error('Choose a GLB with at most 4096 named rigid nodes.');
  const skins=doc.skins??[];if(!Array.isArray(skins)||skins.length>64)throw Error('Choose a bounded GLB skin inventory');
  return nodes.map((n,i)=>`${i}: ${skins.flatMap((s,k)=>Array.isArray(s?.joints)&&s.joints.includes(i)?['[skin '+k+' joint]']:[]).join(' ')} ${Object.hasOwn(n,'skin')?'[skin mesh '+n.skin+'] ':''}${(n.name??'Unnamed node').replace(/[\x00-\x1f]/g,' ').slice(0,128)}`).join('\n');
}
export function createObjectMappingControl(){
  const label=document.createElement('label');label.textContent='External object mapping : GLB node indices in native object order (optional)';const input=document.createElement('input');input.setAttribute('aria-label','External rigid object mapping');input.placeholder='0, 1, 2 : blank uses binding or source tags';input.maxLength=512;label.append(input);
  const details=document.createElement('details'),summary=document.createElement('summary'),inventory=document.createElement('pre');summary.textContent='GLB node indices and names';Object.assign(inventory.style,{maxHeight:'200px',overflow:'auto',whiteSpace:'pre-wrap',overflowWrap:'anywhere'});inventory.textContent='Choose an edited GLB to list its nodes.';details.append(summary,inventory);const skin=document.createElement('input');skin.type='number';skin.min='0';skin.max='63';skin.placeholder='Optional skin index';skin.setAttribute('aria-label','External joint rig skin');const skinLabel=document.createElement('label');skinLabel.textContent='Joint rig skin (optional): explicit mapping extracts rigid joint motion; native geometry stays unchanged';skinLabel.append(skin);const group=document.createElement('div');group.append(label,skinLabel);let touched=false;return {input,label:group,details,inventory,skin,load:binding=>{if(!touched)skin.value=binding.external_skin_index===undefined?'':String(binding.external_skin_index);},touch:()=>{touched=true;}};
}
