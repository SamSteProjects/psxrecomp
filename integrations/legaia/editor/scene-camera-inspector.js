const axes=['x','y','z'],fields=['projection','x','y','z','distance','yaw','pitch'];
export const MIN_CAMERA_PITCH_DEGREES=.12*180/Math.PI;
const number=(value,lo,hi)=>typeof value==='number'&&Number.isFinite(value)&&value>=lo&&value<=hi;
export function sceneCameraDraft(camera){
 if(!camera||!['perspective','orthographic'].includes(camera.projection)||!number(camera.yaw,-1e12,1e12)||!number(camera.pitch,camera.projection==='perspective'?.12:0,Math.PI/2)||!number(camera.distance,20,1e8)||!camera.target||axes.some(a=>!number(camera.target[a],-1e12,1e12)))throw Error('Current camera is outside the supported display bounds.');
 let yaw=(camera.yaw*180/Math.PI)%360;if(yaw>180)yaw-=360;if(yaw< -180)yaw+=360;
 return {projection:camera.projection,...camera.target,distance:camera.distance,yaw,pitch:camera.pitch*180/Math.PI};
}
export function cameraFromSceneDraft(value){
 if(!value||Array.isArray(value)||Object.keys(value).sort().join('|')!==fields.slice().sort().join('|')||!['perspective','orthographic'].includes(value.projection)||axes.some(a=>!number(value[a],-1e12,1e12))||!number(value.distance,20,1e8)||!number(value.yaw,-360,360)||!number(value.pitch,value.projection==='perspective'?MIN_CAMERA_PITCH_DEGREES:0,90))throw Error('Use finite display coordinates, distance 20–100000000, yaw −360–360°, and a supported pitch (perspective at least '+MIN_CAMERA_PITCH_DEGREES+'°; orthographic 0–90°).');
 return {projection:value.projection,target:Object.fromEntries(axes.map(a=>[a,value[a]])),distance:value.distance,yaw:value.yaw*Math.PI/180,pitch:value.pitch===MIN_CAMERA_PITCH_DEGREES?.12:value.pitch*Math.PI/180};
}
export function parseSceneCameraDraft(value){
 const result={projection:value?.projection};
 for(const key of fields.filter(k=>k!=='projection')){const raw=value?.[key];if(typeof raw!=='string'||!/^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?$/i.test(raw.trim()))throw Error('Enter a decimal number for every camera field.');result[key]=Number(raw);}
 cameraFromSceneDraft(result);return result;
}
export function mountSceneCameraInspector({after,getCamera,getContext,isBusy,available,apply}){
 const button=document.createElement('button');button.id='scene-camera-inspector';button.textContent='Camera coordinates';after.after(button);
 const dialog=document.createElement('dialog');dialog.id='scene-camera-dialog';document.body.append(dialog);let context=null;
 dialog.innerHTML='<h2>Scene camera coordinates</h2><p>Target coordinates use the editor display space. They are not actor, guest RAM or confirmed live coordinates. Changing this camera changes the viewport only. Save it through Saved scene views to keep it in the project.</p><label>Projection<select data-camera="projection" aria-label="Camera projection"><option value="perspective">Perspective</option><option value="orthographic">Orthographic</option></select></label><div data-camera-fields></div><p data-camera-status role="status"></p><div class="dialog-actions"><button type="button" data-camera-refresh>Read current camera</button><button type="button" data-camera-apply>Set viewport camera</button><button type="button" data-camera-close>Close camera coordinates</button></div>';
 Object.assign(dialog.querySelector('.dialog-actions').style,{display:'flex',flexWrap:'wrap',gap:'8px',justifyContent:'flex-start'});
 const holder=dialog.querySelector('[data-camera-fields]');Object.assign(holder.style,{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))',gap:'8px'});
 for(const [key,label] of [['x','Target X'],['y','Target Y'],['z','Target Z'],['distance','Camera distance'],['yaw','Camera yaw degrees'],['pitch','Camera pitch degrees']]){const row=document.createElement('label');row.textContent=label;const input=document.createElement('input');input.type='text';input.inputMode='decimal';input.dataset.camera=key;input.setAttribute('aria-label',label);row.append(input);holder.append(row);}
 const status=dialog.querySelector('[data-camera-status]'),set=dialog.querySelector('[data-camera-apply]'),refresh=dialog.querySelector('[data-camera-refresh]');
 const read=()=>Object.fromEntries(fields.map(key=>[key,dialog.querySelector(`[data-camera="${key}"]`).value]));
 function update(){button.disabled=isBusy()||!available();if(!dialog.open)return;refresh.disabled=button.disabled;let error=null;try{parseSceneCameraDraft(read());}catch(e){error=e.message;}const stale=context!==getContext();set.disabled=button.disabled||stale||!!error;dialog.querySelectorAll('input,select').forEach(input=>input.disabled=button.disabled);status.textContent=stale?'Camera or scene changed. Read the current camera before setting a new view.':error??'Camera draft only; project and actor transforms are unchanged.';}
 function capture(){try{const value=sceneCameraDraft(getCamera());context=getContext();for(const key of fields)dialog.querySelector(`[data-camera="${key}"]`).value=String(value[key]);update();}catch(error){context=null;status.textContent=error.message;set.disabled=true;}}
 button.onclick=()=>{if(button.disabled)return;dialog.showModal();capture();};refresh.onclick=()=>{if(!refresh.disabled)capture();};dialog.querySelector('[data-camera-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{context=null;});
 for(const input of dialog.querySelectorAll('input,select'))input.addEventListener('input',update);
 set.onclick=()=>{if(isBusy()||!available()||context!==getContext()){update();return;}try{const next=cameraFromSceneDraft(parseSceneCameraDraft(read()));apply(next);capture();status.textContent='Viewport camera set. Project and actor transforms are unchanged.';}catch(error){status.textContent=error.message;set.disabled=true;}};
 update();return {update};
}
