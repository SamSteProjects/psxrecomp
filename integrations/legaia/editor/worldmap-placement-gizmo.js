const finite=n=>typeof n==='number'&&Number.isFinite(n);
const round=n=>{const value=Math.sign(n)*Math.floor(Math.abs(n)+.5);return value===0?0:value;};
export const sourceOffsetDirections={x:{x:1,y:0,z:0},y:{x:0,y:-1,z:0},z:{x:0,y:0,z:-1}};
export function translateOffset(values,axis,screenDelta,screenAxis,units,step=1){
  if(!['x','y','z'].includes(axis)||![screenDelta.x,screenDelta.y,screenAxis.x,screenAxis.y,units].every(finite)||units<=0||![1,16,64,128].includes(step)||!values?.offset||!['x','y','z'].every(a=>Number.isInteger(values.offset[a])&&values.offset[a]>=-32768&&values.offset[a]<=32767)||!Number.isInteger(values.yaw_units)||values.yaw_units<0||values.yaw_units>4095)throw new Error('Invalid source translation basis or encoded offsets');
  const length=screenAxis.x**2+screenAxis.y**2;if(length<16)throw new Error('Source axis is edge-on; orbit or frame the anchor');
  const delta=(screenDelta.x*screenAxis.x+screenDelta.y*screenAxis.y)/length*units;
  const value=round((values.offset[axis]+delta)/step)*step;
  if(value < -32768 || value > 32767)throw new Error('Source offset exceeds signed16 range');
  return {...values,offset:{...values.offset,[axis]:value}};
}

export function mountPlacementGizmo({host,getAxes,getContext,getValues,allowed,getStep,onBegin,onPreview,onEnd,onCancel,onError,idPrefix='world-placement'}){
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.id=idPrefix+'-gizmo';Object.assign(svg.style,{position:'absolute',inset:'0',width:'100%',height:'100%',pointerEvents:'none',overflow:'hidden'});host.append(svg);
  const groups=new Map(),events=new AbortController();let active=null;
  function cancel(reason='Translation preview cancelled'){
    if(!active)return;const previous=active;active=null;
    if(previous.target.hasPointerCapture(previous.id))previous.target.releasePointerCapture(previous.id);
    onCancel(reason);update();
  }
  function current(){return active&&allowed()&&getContext()===active.context;}
  for(const [axis,color] of [['x','#ff786a'],['y','#89eb8e'],['z','#80baff']]){
    const group=document.createElementNS(ns,'g'),line=document.createElementNS(ns,'line'),circle=document.createElementNS(ns,'circle'),label=document.createElementNS(ns,'text');group.id=idPrefix+'-axis-'+axis;circle.id=idPrefix+'-handle-'+axis;circle.setAttribute('r','7');circle.setAttribute('fill',color);circle.setAttribute('stroke','#101819');circle.setAttribute('stroke-width','2');line.setAttribute('stroke',color);line.setAttribute('stroke-width','5');label.textContent=axis.toUpperCase();label.setAttribute('fill',color);label.setAttribute('font-size','14');label.setAttribute('font-weight','bold');Object.assign(circle.style,{pointerEvents:'all',cursor:'grab',touchAction:'none'});Object.assign(line.style,{pointerEvents:'stroke',cursor:'grab',touchAction:'none'});group.append(line,circle,label);svg.append(group);groups.set(axis,{group,line,circle,label});
    group.onpointerdown=e=>{if(e.button!==0||active||!allowed())return;const basis=getAxes()[axis];if(!basis)return;e.preventDefault();e.stopPropagation();const rect=host.getBoundingClientRect();active={id:e.pointerId,target:group,axis,basis:structuredClone(basis),values:structuredClone(getValues()),context:getContext(),step:getStep(),start:{x:e.clientX-rect.left,y:e.clientY-rect.top},changed:false};group.setPointerCapture(e.pointerId);onBegin();update();};
    group.onpointermove=e=>{if(active?.id!==e.pointerId)return;e.preventDefault();if(!current()){cancel('Source, camera or viewport changed; translation cancelled');return;}const rect=host.getBoundingClientRect(),delta={x:e.clientX-rect.left-active.start.x,y:e.clientY-rect.top-active.start.y};if(Math.hypot(delta.x,delta.y)<1&&!active.changed)return;try{const values=translateOffset(active.values,active.axis,delta,{x:active.basis.end.x-active.basis.start.x,y:active.basis.end.y-active.basis.start.y},active.basis.units,active.step);if(!active.changed&&values.offset[active.axis]===active.values.offset[active.axis])return;active.changed=true;onPreview(values);update();}catch(error){onError(error.message);}};
    group.onpointerup=e=>{if(active?.id!==e.pointerId)return;e.preventDefault();e.stopPropagation();if(!current()){cancel('Source, camera or viewport changed; translation cancelled');return;}const previous=active;active=null;if(group.hasPointerCapture(e.pointerId))group.releasePointerCapture(e.pointerId);if(previous.changed)onEnd();else onCancel('No source offset change');update();};
    group.onpointercancel=()=>cancel();group.onlostpointercapture=()=>{if(active?.target===group)cancel();};
  }
  function update(){if(active&&!current()){cancel('Source, camera or viewport changed; translation cancelled');return;}const axes=getAxes(),enabled=allowed();for(const [axis,{group,line,circle,label}] of groups){const value=axes[axis];group.style.display=value?'':'none';group.style.opacity=enabled?'1':'.35';line.style.pointerEvents=enabled?'stroke':'none';circle.style.pointerEvents=enabled?'all':'none';if(!value)continue;line.setAttribute('x1',value.start.x);line.setAttribute('y1',value.start.y);line.setAttribute('x2',value.end.x);line.setAttribute('y2',value.end.y);circle.setAttribute('cx',value.end.x);circle.setAttribute('cy',value.end.y);label.setAttribute('x',value.end.x+9);label.setAttribute('y',value.end.y-9);} }
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&active){e.preventDefault();e.stopPropagation();cancel('Escape cancelled the translation preview');}},{capture:true,signal:events.signal});
  window.addEventListener('blur',()=>cancel('Focus changed; translation cancelled'),{signal:events.signal});
  svg.addEventListener('wheel',()=>cancel('Camera input changed; translation cancelled'),{signal:events.signal});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)cancel('Page hidden; translation cancelled');},{signal:events.signal});
  const observer=new ResizeObserver(()=>{if(active&&!current())cancel('Viewport resized; translation cancelled');update();});observer.observe(host);
  return {update,cancel,isActive:()=>!!active,dispose(){cancel('Translation view closed');events.abort();observer.disconnect();svg.remove();}};
}
