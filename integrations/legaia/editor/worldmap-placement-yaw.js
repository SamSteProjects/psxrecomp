const finite=value=>typeof value==='number'&&Number.isFinite(value);
const wrap=value=>((value%4096)+4096)%4096;
const nearest=value=>{const result=Math.sign(value)*Math.floor(Math.abs(value)+.5);return result===0?0:result;};
export function rotateSourceYaw(values,radians,step=1){
  if(!finite(radians)||![1,16,64,256,512,1024].includes(step)||!Number.isInteger(values?.yaw_units)||values.yaw_units<0||values.yaw_units>=4096||!values?.offset||!['x','y','z'].every(axis=>Number.isInteger(values.offset[axis])&&values.offset[axis]>=-32768&&values.offset[axis]<=32767))throw new Error('Invalid source yaw draft or snap');
  const snapped=nearest((values.yaw_units+radians*4096/(2*Math.PI))/step)*step;
  if(!Number.isSafeInteger(snapped))throw new Error('Source yaw gesture exceeds its finite angle budget');
  return {...values,offset:{...values.offset},yaw_units:wrap(snapped)};
}
// Solve the homogeneous projection on the frozen horizontal source plane.
// This preserves perspective, rather than measuring angles in a screen ellipse.
export function sourcePlaneAngle(point,plane){
  const m=plane?.matrix,p=plane?.pivot;
  if(!Array.isArray(m)||m.length!==16||!m.every(finite)||!p||![p.x,p.y,p.z,point?.x,point?.y,plane.width,plane.height,plane.radius].every(finite)||plane.width<=0||plane.height<=0||plane.radius<=0)throw new Error('Invalid projected source plane');
  const nx=2*point.x/plane.width-1,ny=1-2*point.y/plane.height;
  const cx=m[0]*p.x+m[4]*p.y+m[8]*p.z+m[12],cy=m[1]*p.x+m[5]*p.y+m[9]*p.z+m[13],cw=m[3]*p.x+m[7]*p.y+m[11]*p.z+m[15];
  const a=m[0]-nx*m[3],b=m[8]-nx*m[11],c=cx-nx*cw,d=m[1]-ny*m[3],e=m[9]-ny*m[11],f=cy-ny*cw,det=a*e-b*d;
  if(Math.abs(det)<1e-12)throw new Error('Yaw plane is edge-on; orbit or frame the anchor');
  const x=(b*f-c*e)/det,z=(c*d-a*f)/det;
  if(!finite(x)||!finite(z)||cw+m[3]*x+m[11]*z<=0||Math.hypot(x,z)<plane.radius*.05)throw new Error('Yaw pointer is too close to the origin or behind the camera');
  return Math.atan2(-z,x);
}
export function mountPlacementYaw({host,getRotation,getContext,getValues,allowed,getStep,onBegin,onPreview,onEnd,onCancel,onError}){
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg'),group=document.createElementNS(ns,'g'),ring=document.createElementNS(ns,'path'),heading=document.createElementNS(ns,'line'),handle=document.createElementNS(ns,'circle'),label=document.createElementNS(ns,'text');
  svg.id='world-placement-yaw-gizmo';group.id='world-placement-yaw-axis';ring.id='world-placement-yaw-ring';handle.id='world-placement-yaw-handle';
  Object.assign(svg.style,{position:'absolute',inset:'0',width:'100%',height:'100%',pointerEvents:'none',overflow:'hidden'});
  for(const item of [ring,heading]){item.setAttribute('stroke','#f3cf76');item.setAttribute('stroke-width',item===ring?'6':'3');item.setAttribute('fill','none');}
  handle.setAttribute('r','8');handle.setAttribute('fill','#f3cf76');handle.setAttribute('stroke','#101819');handle.setAttribute('stroke-width','2');label.textContent='YAW';label.setAttribute('fill','#f3cf76');label.setAttribute('font-size','14');label.setAttribute('font-weight','bold');
  group.append(ring,heading,handle,label);svg.append(group);host.append(svg);let active=null;
  function cancel(reason='Yaw preview cancelled'){
    if(!active)return;const previous=active;active=null;if(group.hasPointerCapture(previous.id))group.releasePointerCapture(previous.id);onCancel(reason);update();
  }
  const current=()=>active&&allowed()&&getContext()===active.context;
  const point=event=>{const rect=host.getBoundingClientRect();return {x:event.clientX-rect.left,y:event.clientY-rect.top};};
  group.onpointerdown=event=>{
    if(event.button!==0||active||!allowed())return;const basis=getRotation();if(!basis)return;
    try{const angle=sourcePlaneAngle(point(event),basis.plane);event.preventDefault();event.stopPropagation();active={id:event.pointerId,basis:structuredClone(basis),values:structuredClone(getValues()),context:getContext(),step:getStep(),previousAngle:angle,radians:0,changed:false};group.setPointerCapture(event.pointerId);onBegin();update();}catch(error){onError(error.message);}
  };
  group.onpointermove=event=>{
    if(active?.id!==event.pointerId)return;event.preventDefault();if(!current()){cancel('Source, camera or viewport changed; yaw cancelled');return;}
    try{const angle=sourcePlaneAngle(point(event),active.basis.plane);let delta=angle-active.previousAngle;if(delta>Math.PI)delta-=2*Math.PI;if(delta< -Math.PI)delta+=2*Math.PI;active.radians+=delta;active.previousAngle=angle;const values=rotateSourceYaw(active.values,active.radians,active.step);if(!active.changed&&values.yaw_units===active.values.yaw_units)return;active.changed=true;onPreview(values);update();}catch(error){onError(error.message);}
  };
  group.onpointerup=event=>{
    if(active?.id!==event.pointerId)return;event.preventDefault();event.stopPropagation();if(!current()){cancel('Source, camera or viewport changed; yaw cancelled');return;}const previous=active;active=null;if(group.hasPointerCapture(event.pointerId))group.releasePointerCapture(event.pointerId);if(previous.changed)onEnd();else onCancel('No source yaw change');update();
  };
  group.onpointercancel=()=>cancel();group.onlostpointercapture=()=>{if(active)cancel();};
  function update(){
    if(active&&!current()){cancel('Source, camera or viewport changed; yaw cancelled');return;}
    const basis=getRotation(),enabled=allowed();group.style.display=basis?'':'none';group.style.opacity=enabled?'1':'.35';ring.style.pointerEvents=enabled?'stroke':'none';handle.style.pointerEvents=enabled?'all':'none';ring.style.cursor=handle.style.cursor='grab';ring.style.touchAction=handle.style.touchAction='none';heading.style.pointerEvents=label.style.pointerEvents='none';if(!basis)return;
    ring.setAttribute('d',basis.points.map((p,index)=>`${index?'L':'M'}${p.x},${p.y}`).join(' ')+' Z');heading.setAttribute('x1',basis.center.x);heading.setAttribute('y1',basis.center.y);heading.setAttribute('x2',basis.heading.x);heading.setAttribute('y2',basis.heading.y);handle.setAttribute('cx',basis.heading.x);handle.setAttribute('cy',basis.heading.y);label.setAttribute('x',basis.heading.x+11);label.setAttribute('y',basis.heading.y-11);
  }
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&active){event.preventDefault();event.stopPropagation();cancel('Escape cancelled the yaw preview');}},true);
  window.addEventListener('blur',()=>cancel('Focus changed; yaw cancelled'));document.addEventListener('visibilitychange',()=>{if(document.hidden)cancel('Page hidden; yaw cancelled');});svg.addEventListener('wheel',()=>cancel('Camera input changed; yaw cancelled'));
  new ResizeObserver(()=>{if(active&&!current())cancel('Viewport resized; yaw cancelled');update();}).observe(host);
  return {update,cancel,isActive:()=>!!active};
}
