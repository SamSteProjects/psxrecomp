// Display-only framing. Native bounds and unused vector rows remain source facts.
const finiteVector=v=>Array.isArray(v)&&v.length===3&&v.every(n=>typeof n==='number'&&Number.isFinite(n));
export function modelPreviewFrame(current,proposed,layer='proposed',mode='comparison'){
  if(!['current','proposed'].includes(layer)||!['comparison','visible','stored'].includes(mode))throw new Error('Choose a supported model comparison frame.');
  const previews=mode==='comparison'?[current,proposed]:[layer==='current'?current:proposed];
  const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];let pointCount=0;
  for(const preview of previews){
    if(!Array.isArray(preview?.vertices)||preview.vertices.length>100000||!Array.isArray(preview.triangles)||preview.triangles.length>100000)throw new Error('Model camera geometry is missing or exceeds preview limits.');
    const indices=new Set();
    if(mode==='stored')for(let i=0;i<preview.vertices.length;i++)indices.add(i);
    else for(const triangle of preview.triangles){
      if(!Array.isArray(triangle)||triangle.length!==3||triangle.some(i=>!Number.isSafeInteger(i)||i<0||i>=preview.vertices.length))throw new Error('Model camera triangle references an unavailable vertex.');
      for(const i of triangle)indices.add(i);
    }
    for(const i of indices){const vertex=preview.vertices[i];if(!finiteVector(vertex))throw new Error('Model camera vertex is not finite XYZ.');for(let a=0;a<3;a++){min[a]=Math.min(min[a],vertex[a]);max[a]=Math.max(max[a],vertex[a]);}pointCount++;}
  }
  if(!pointCount)return {bounds:{min:[0,0,0],max:[0,0,0]},center:[0,0,0],radius:1,empty:true};
  return {bounds:{min,max},center:min.map((v,i)=>(v+max[i])/2),radius:Math.max(1,Math.hypot(...max.map((v,i)=>v-min[i]))/2),empty:false};
}

export function modelFrameControls(host,onChange){
  const label=document.createElement('label');label.textContent='Camera framing';
  const select=document.createElement('select');select.dataset.frameMode='true';select.setAttribute('aria-label','Model camera framing');
  for(const [value,text] of [['comparison','Shared visible geometry'],['visible','Visible geometry in this layer'],['stored','All stored vertices in this layer']]){const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);}
  const button=document.createElement('button');button.type='button';button.dataset.frameMesh='true';button.textContent='Frame mesh';
  const note=document.createElement('p');note.textContent='Visible framing ignores unused and retired vertex rows. Shared framing keeps Current and Proposed at the same scale. Camera controls do not change the model.';
  label.append(select);host.querySelector('canvas').before(label,button);host.append(note);
  select.onchange=button.onclick=onChange;
  return {select,button,frame:(current,proposed,layer)=>modelPreviewFrame(current,proposed,layer,select.value),setDisabled:v=>{select.disabled=button.disabled=v;}};
}
