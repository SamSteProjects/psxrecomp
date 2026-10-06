export const validMeshRotation=value=>Array.isArray(value)&&value.length===3&&value.every(n=>typeof n==='number'&&Number.isFinite(n)&&n>=-360&&n<=360);
export function meshRotationMatches(value,requested){
  const actual=value&&Object.hasOwn(value,'source_rotation')?value.source_rotation:[0,0,0];
  return validMeshRotation(requested)&&validMeshRotation(actual)&&actual.every((n,i)=>n===requested[i]);
}
export function meshRotationControls(initial=[0,0,0]){
  if(!validMeshRotation(initial))throw new Error('Invalid native mesh rotation.');
  const host=document.createElement('fieldset'),legend=document.createElement('legend');legend.textContent='Native import rotation (degrees)';host.append(legend);
  const inputs=['x','y','z'].map((axis,i)=>{const label=document.createElement('label');label.textContent=axis.toUpperCase();const input=document.createElement('input');input.type='number';input.min='-360';input.max='360';input.step='any';input.value=String(initial[i]);input.dataset['sourceRotation'+axis.toUpperCase()]='true';input.setAttribute('aria-label',`Native mesh rotation ${axis.toUpperCase()}`);label.append(input);host.append(label);return input;});
  const note=document.createElement('p');note.textContent='Rotate about native X, then Y, then Z after GLB conversion, before origin offset. Native Y increases downward. Normal directions rotate with geometry; actor facing and animation channels stay separate.';host.append(note);
  return {host,inputs,values:()=>inputs.map(input=>input.valueAsNumber),setDisabled:value=>{for(const input of inputs)input.disabled=value;}};
}
