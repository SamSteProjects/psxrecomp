import {assetEvidenceContext,assetRecordDownload} from './asset-record-export.js';
const MAX_BYTES=8*1024*1024,MAX_ROWS=512;
const scope=c=>{if(typeof c?.project_path!=='string'||!c.project_path||typeof c.project_assets_source_key!=='string'||!/^[a-f0-9]{64}$/.test(c.project_assets_source_key))throw Error('Project asset comparison source is unavailable.');return JSON.stringify([c.project_path,c.project_assets_source_key]);};
const size=v=>new TextEncoder().encode(JSON.stringify(v)).byteLength;
function snapshot(record,context){const report=JSON.parse(assetRecordDownload(record,context).text);if(size(report)>MAX_BYTES)throw Error('Pinned asset metadata exceeds 8 MiB.');scope(report.source_context);return report;}
export function compareAssetMetadata(pinned,current){
 pinned=snapshot(pinned.record,pinned.source_context);current=snapshot(current.record,current.source_context);
 if(scope(pinned.source_context)!==scope(current.source_context))throw Error('Pinned metadata belongs to different or changed project inputs.');
 if(size([pinned,current])>MAX_BYTES)throw Error('Asset comparison exceeds 8 MiB.');
 const rows=[],own=(v,k)=>Object.hasOwn(v,k),object=v=>v!==null&&typeof v==='object',pathKey=k=>String(k).replaceAll('~','~0').replaceAll('/','~1');
 function visit(a,b,path,hasA=true,hasB=true,depth=0){
  if(depth>64)throw Error('Asset comparison exceeds metadata depth.');
  if(hasA&&hasB&&object(a)&&object(b)&&Array.isArray(a)===Array.isArray(b)){
   const keys=Array.isArray(a)?Array.from({length:Math.max(a.length,b.length)},(_,i)=>String(i)):[...new Set([...Object.keys(a),...Object.keys(b)])].sort();
   if(keys.length){for(const k of keys)visit(a[k],b[k],path+'/'+pathKey(k),own(a,k),own(b,k),depth+1);return;}
  }
  if(rows.length>=MAX_ROWS)throw Error('Asset comparison exceeds 512 fields. Narrow the source record or save its metadata evidence.');
  rows.push({path,state:!hasA?'only-current':!hasB?'only-pinned':JSON.stringify(a)===JSON.stringify(b)?'same':'changed',pinned_present:hasA,current_present:hasB,pinned:hasA?a:null,current:hasB?b:null});
 }
 visit(pinned.record,current.record,'');
 const report={schema_version:'legaia.asset-metadata-comparison.v1',read_only:true,pinned:structuredClone(pinned),current:structuredClone(current),rows,difference_count:rows.filter(r=>r.state!=='same').length,limitations:['Recorded SDK metadata comparison only; differences do not prove native byte changes, runtime use or gameplay behavior.','Missing fields remain distinct from explicit null. Arrays retain recorded order; field paths use JSON Pointer escaping.']};
 if(size(report)>MAX_BYTES)throw Error('Asset comparison evidence exceeds 8 MiB.');return report;
}
export function createAssetMetadataPin(){
 let held=null,revision=0;
 return {get revision(){return revision;},clear(){held=null;revision++;},read(context){if(held&&scope(held.source_context)!==scope(context)){held=null;revision++;}return held?structuredClone(held):null;},pin(record,context){held=snapshot(record,context);revision++;return structuredClone(held);},compare(record,context){const pinned=this.read(context);if(!pinned)throw Error('Pin current metadata before comparing.');return compareAssetMetadata(pinned,snapshot(record,context));}};
}
export function mountAssetMetadataComparison(host,{record,getState,current,busy,pin,onError,request=fetch}){
 const context=assetEvidenceContext(getState()),stamp=JSON.stringify(context);scope(context);snapshot(record,context);
 const pinButton=document.createElement('button'),compare=document.createElement('button'),clear=document.createElement('button'),status=document.createElement('p');pinButton.textContent='Pin metadata';compare.textContent='Compare pinned metadata';clear.textContent='Clear pinned metadata';pinButton.dataset.assetMetadataPin='';compare.dataset.assetMetadataCompare='';clear.dataset.assetMetadataClear='';status.className='field-note';status.setAttribute('role','status');host.append(pinButton,compare,clear,status);let pending=false;
 const fresh=()=>{try{return current()&&stamp===JSON.stringify(assetEvidenceContext(getState()));}catch{return false;}};
 const currentPin=()=>{try{return pin.read(assetEvidenceContext(getState()));}catch{pin.clear();return null;}};
 function update(){const held=currentPin();compare.disabled=pending||!held;clear.disabled=pending||!held;pinButton.disabled=pending;status.textContent=held?'Pinned: '+(held.record.label??held.record.id):'No pinned asset metadata.';}
 async function qualify(){if(!fresh())throw Error('Asset metadata changed. Reopen details.');const response=await request('/api/state',{cache:'no-store'});if(!response.ok)throw Error('Could not verify current asset inputs.');const latest=await response.json();if(!fresh()||stamp!==JSON.stringify(assetEvidenceContext(latest)))throw Error('Asset metadata changed. Reopen details.');}
 async function run(action){if(busy()||pending)return;pending=true;update();try{await qualify();action();}catch(error){onError(error);status.textContent=error.message;}finally{pending=false;pinButton.disabled=!fresh();const held=currentPin();compare.disabled=!fresh()||!held;clear.disabled=!fresh()||!held;}}
 pinButton.onclick=()=>run(()=>{pin.pin(record,context);update();});
 clear.onclick=()=>{if(busy()||pending||!fresh())return;pin.clear();update();};
 compare.onclick=()=>run(()=>{
  const report=pin.compare(record,context),revision=pin.revision,dialog=document.createElement('dialog');dialog.id='asset-metadata-comparison';dialog.className='project-dialog';
  const heading=document.createElement('h2');heading.textContent='Asset metadata comparison';const note=document.createElement('p');note.textContent=`${report.difference_count} differing fields of ${report.rows.length}. Pinned: ${report.pinned.record.label??report.pinned.record.id}. Current: ${report.current.record.label??report.current.record.id}. Recorded metadata only; runtime use is not asserted.`;
  const label=document.createElement('label'),equal=document.createElement('input');equal.type='checkbox';equal.setAttribute('aria-label','Show equal metadata fields');label.append(equal,' Show equal fields');
  const list=document.createElement('div');list.dataset.comparisonRows='';const display=v=>{const text=JSON.stringify(v);return text.length>2000?text.slice(0,2000)+'… (full value in evidence)':text;};
  function render(){list.replaceChildren();for(const row of report.rows.filter(r=>equal.checked||r.state!=='same')){const entry=document.createElement('section');entry.className='asset-comparison-row';const title=document.createElement('strong');title.textContent=(row.path||'/')+' · '+row.state;entry.append(title);for(const [key,present] of [['pinned',row.pinned_present],['current',row.current_present]]){const item=document.createElement('pre');item.className='diagnostic-detail';item.textContent=key+': '+(present?display(row[key]):'(missing)');entry.append(item);}list.append(entry);}if(!list.children.length){const p=document.createElement('p');p.textContent='No differing recorded fields.';list.append(p);}}equal.onchange=render;
  const save=document.createElement('button'),close=document.createElement('button'),message=document.createElement('p');save.textContent='Save comparison evidence…';close.textContent='Close comparison';close.onclick=()=>dialog.close();message.setAttribute('role','status');save.onclick=async()=>{if(busy()||save.disabled)return;save.disabled=true;try{await qualify();if(!dialog.open||revision!==pin.revision||!pin.read(context))throw Error('Pinned comparison changed. Reopen comparison.');const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json'})),a=document.createElement('a');try{a.href=url;a.download='legaia-asset-comparison-'+context.project_assets_source_key.slice(0,16)+'.json';document.body.append(a);a.click();}finally{a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}message.textContent='Saved recorded metadata comparison.';save.disabled=false;}catch(error){message.textContent=error.message;onError(error);}};
  const actions=document.createElement('div');actions.className='dialog-actions';actions.append(save,close);dialog.append(heading,note,label,actions,message,list);dialog.addEventListener('close',()=>dialog.remove());document.body.append(dialog);render();dialog.showModal();
 });update();return {refresh:update};
}
