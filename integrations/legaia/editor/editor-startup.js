// Owns initial module/state loading only. Recovery is explicit and read-only.
export function createEditorStartup({load,onState,loadTimeoutMs=45000,connectionTimeoutMs=30000}){
 if(typeof load!=='function'||typeof onState!=='function'||![loadTimeoutMs,connectionTimeoutMs].every(n=>Number.isSafeInteger(n)&&n>0&&n<=120000))throw Error('Invalid editor startup configuration.');
 let module=null,generation=0,controller=null,disposed=false,working=false,connecting=false,state={phase:'idle',message:'Loading editor workspace…',canRetry:false};
 const publish=next=>{state=next;if(!disposed)onState({...state});};
 function deadline(promise,ms,message,signal){return new Promise((resolve,reject)=>{const abort=()=>reject(Error(message)),timer=setTimeout(()=>{controller.abort();},ms);signal.addEventListener('abort',abort,{once:true});Promise.resolve(promise).then(resolve,reject).finally(()=>{clearTimeout(timer);signal.removeEventListener('abort',abort);});signal.addEventListener('abort',()=>clearTimeout(timer),{once:true});});}
 async function start(){
  if(disposed||working||connecting||state.phase==='ready'||state.phase==='failed'&&!state.canRetry)return false;
  working=true;const owned=++generation;controller=new AbortController();const signal=controller.signal,owns=()=>!disposed&&owned===generation&&!signal.aborted;
  try{
   if(!module){publish({phase:'loading',message:'Loading editor workspace…',canRetry:false});module=await deadline(load(),loadTimeoutMs,'The editor took too long to load. Reload the editor to try again.',signal);if(!owns())return false;if(typeof module?.initializeEditor!=='function'){module=null;throw Error('Editor startup is unavailable. Reload the editor.');}}
   publish({phase:'connecting',message:'Connecting to local project service…',canRetry:false});connecting=true;
   const connection=Promise.resolve().then(()=>{if(!owns())throw Error('Startup was cancelled.');return module.initializeEditor({signal});});const settled=()=>{connecting=false;if(!disposed&&owned===generation&&state.phase==='failed')publish({...state,canRetry:true});};connection.then(settled,settled);
   const ok=await deadline(connection,connectionTimeoutMs,'The local project service took too long to respond. Retry the connection.',signal);
   if(!owns())return false;if(ok!==true)throw Error('The local project state could not be loaded. Retry the connection.');
   publish({phase:'ready',message:'Editor ready.',canRetry:false});return true;
  }catch(error){if(!disposed&&owned===generation)publish({phase:'failed',message:String(error?.message??error).slice(0,2048),canRetry:!!module&&!connecting});return false;}
  finally{if(owned===generation)working=false;}
 }
 return {start,get state(){return {...state};},dispose(){disposed=true;generation++;controller?.abort();}};
}

export function mountEditorStartup({root,background,load=()=>import('/editor.js'),reload=()=>location.reload(),...budgets}){
 const status=root.querySelector('[data-startup-status]'),retry=root.querySelector('[data-startup-retry]'),refresh=root.querySelector('[data-startup-reload]');
 const fallback=root.querySelector('[data-startup-fallback]');if(fallback)fallback.hidden=true;
 const view=createEditorStartup({load,...budgets,onState:state=>{root.hidden=state.phase==='ready';for(const element of background)element.inert=state.phase!=='ready';status.textContent=state.message;retry.hidden=state.phase!=='failed'||!state.canRetry;retry.disabled=!state.canRetry;refresh.hidden=state.phase!=='failed';}});
 retry.onclick=()=>view.start();refresh.onclick=()=>{if(view.state.phase==='failed')reload();};return view;
}

if(typeof document!=='undefined'&&document.getElementById('editor-startup')){
 const view=mountEditorStartup({root:document.getElementById('editor-startup'),background:[...document.querySelectorAll('[data-startup-background]')]});
 window.addEventListener('pagehide',()=>view.dispose(),{once:true});view.start();
}
