// Native model coordinates, after GLB node transforms, scale and Y reflection.
export const validMeshOffset=value=>Array.isArray(value)&&value.length===3&&value.every(n=>typeof n==='number'&&Number.isFinite(n)&&n>=-32768&&n<=32767);
export function meshOffsetMatches(value,requested){
  const actual=value&&Object.hasOwn(value,'source_offset')?value.source_offset:[0,0,0];
  return validMeshOffset(requested)&&validMeshOffset(actual)&&actual.every((n,i)=>n===requested[i]);
}
export function meshOriginControls(initial=[0,0,0]){
  if(!validMeshOffset(initial))throw new Error('Invalid native mesh origin offset.');
  const host=document.createElement('fieldset'),legend=document.createElement('legend');legend.textContent='Native origin offset';host.append(legend);
  const inputs=['x','y','z'].map((axis,i)=>{const label=document.createElement('label');label.textContent=axis.toUpperCase();const input=document.createElement('input');input.type='number';input.min='-32768';input.max='32767';input.step='any';input.value=String(initial[i]);input.dataset['sourceOffset'+axis.toUpperCase()]='true';input.setAttribute('aria-label',`Native mesh offset ${axis.toUpperCase()}`);label.append(input);host.append(label);return input;});
  const note=document.createElement('p');note.textContent='Added in native model units after scaling and GLB coordinate conversion. Native Y increases downward. This moves imported vertices within the shared model; actor placement stays separate.';host.append(note);
  return {host,inputs,values:()=>inputs.map(input=>input.valueAsNumber),setDisabled:value=>{for(const input of inputs)input.disabled=value;}};
}
