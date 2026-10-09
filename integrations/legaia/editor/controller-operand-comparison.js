import {decodeControllerFlagBitSnapshot} from './controller-flag-bits.js';
import {CONTROLLER_SNAPSHOT_SCHEMAS} from './controller-workspace-snapshot.js';
import {controllerOperandSource} from './controller-operand-files.js';
import {decodeControllerSystemSelectorSnapshot} from './system-flag-selectors.js';
import {decodeControllerBranchSnapshot} from './script-branches.js';
import {decodeControllerTileSnapshot} from './controller-tile-rects.js';
import {decodeControllerFadeSnapshot} from './controller-fades.js';
import {decodeControllerTableCopySnapshot} from './controller-tables.js';
import {decodeControllerWordTripletSnapshot} from './controller-word-triplets.js';
import {decodeControllerThreeWordSnapshot} from './controller-three-words.js';
import {decodeControllerBgmSnapshot} from './controller-bgm.js';
import {decodeControllerSceneByteSnapshot} from './controller-scene-bytes.js';
import {decodeControllerFiveWordSnapshot} from './controller-five-words.js';
import {decodeControllerGlobalByteSnapshot} from './controller-global-bytes.js';
import {decodeControllerPartySelectorSnapshot} from './controller-party-selectors.js';
const families={
 ControllerFlagBits:['flag-bit','Flag Bits',decodeControllerFlagBitSnapshot],
 ControllerSystemFlags:['selector','System Flag Selectors',decodeControllerSystemSelectorSnapshot],
 ControllerBranches:['branch','Branches',decodeControllerBranchSnapshot],
 ControllerTileRects:['tile','Tile Requests',decodeControllerTileSnapshot],
 ControllerFades:['fade','Fades',decodeControllerFadeSnapshot],
 ControllerTableCopies:['table','Table Copies',decodeControllerTableCopySnapshot],
 ControllerWordTriplets:['word-triplet','Word Triplets',decodeControllerWordTripletSnapshot],
 ControllerThreeWords:['three-word','Three Words',decodeControllerThreeWordSnapshot],
 ControllerBgm:['bgm','BGM Arguments',decodeControllerBgmSnapshot],
 ControllerSceneBytes:['scene-byte','Scene-State Bytes',decodeControllerSceneByteSnapshot],
 ControllerFiveWords:['five-word','Five Words',decodeControllerFiveWordSnapshot],
 ControllerGlobalBytes:['global-byte','Global Bytes',decodeControllerGlobalByteSnapshot],
 ControllerPartySelectors:['party-selector','Party Selectors',decodeControllerPartySelectorSnapshot]
};
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
export function controllerOperandComparison(raw,owner,context){
 const source=controllerOperandSource(raw,owner,context.scriptKey),rows=[];
 for(const [family,[kind,label,decode]] of Object.entries(families)){
  const input=raw[family];
  if(input.schema_version!==CONTROLLER_SNAPSHOT_SCHEMAS[family]||input.gameplay_verified!==false||!Array.isArray(input.targets)||input.targets.length>1024||input.supported!==(input.targets.length>0))throw Error('Controller comparison family qualification changed.');
  if(!input.targets.length)continue;
  const snapshot=decode(input,owner,context);
  for(const t of snapshot.targets){
   const retail=family==='ControllerBranches'?{target_pc:t.target_pc}:t.values;
   const authored=t.authored_values??t.authored_value??null;
   const current=family==='ControllerBranches'?{target_pc:t.current_target_pc}:family==='ControllerSystemFlags'?{index:t.current_index}:t.current_values;
   if(!same(current,authored??retail))throw Error('Controller comparison Current layer differs from its authored source.');
   rows.push({family,kind,label,id:t.semantic_id,pc:t.pc,mnemonic:t.mnemonic,retail:structuredClone(retail),authored:structuredClone(authored),current:structuredClone(current),changed:!same(retail,current)});
  }
 }
 rows.sort((a,b)=>a.pc-b.pc||a.family.localeCompare(b.family));
 return {source_record_sha256:source.source_record_sha256,current_record_sha256:source.current_record_sha256,rows};
}
export function filterControllerComparison(rows,{family='',layer='all',query=''}={}){
 if(!['all','authored','changed'].includes(layer)||typeof query!=='string'||query.length>256)throw Error('Invalid controller comparison filter.');
 const tokens=query.trim().toLowerCase().split(/\s+/).filter(Boolean);
 return rows.filter(row=>(!family||row.family===family)&&(layer==='all'||layer==='authored'&&row.authored!==null||layer==='changed'&&row.changed)&&tokens.every(token=>`${row.label} ${row.id} ${row.mnemonic} ${row.pc} 0x${row.pc.toString(16).padStart(4,'0')} ${JSON.stringify(row.retail)} ${JSON.stringify(row.authored)} ${JSON.stringify(row.current)}`.toLowerCase().includes(token)));
}
export function mountControllerOperandComparison(host,{snapshots,owner,context,current,busy,controls,sourcePcs,selectSource}){
 const value=controllerOperandComparison(snapshots,owner,context),doc=host.ownerDocument,el=(tag,text)=>{const n=doc.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 const boundaries=new Set(sourcePcs);
 const section=el('details'),heading=el('summary','Controller Operand Comparison'),note=el('p','Retail values, saved authored overrides and composed Current operands. Pending drafts are excluded. These encoded values do not prove runtime behavior.'),bar=el('div'),family=el('select'),layer=el('select'),search=el('input'),status=el('p'),list=el('div'),previous=el('button','Previous Operands'),next=el('button','Next Operands');previous.type=next.type='button';
 section.dataset.controllerOperandComparison='';family.setAttribute('aria-label','Comparison Family');layer.setAttribute('aria-label','Comparison Layer');search.setAttribute('aria-label','Find Controller Operands');search.type='search';search.maxLength=256;search.placeholder='Offset, mnemonic or operand value';status.setAttribute('role','status');
 bar.style.cssText='display:flex;flex-wrap:wrap;gap:8px';for(const n of [family,layer,search])n.style.cssText='max-width:100%;min-width:0';
 for(const [id,label] of [['','All Supported Families'],...Object.entries(families).map(([id,v])=>[id,v[1]])]){const o=el('option',label);o.value=id;family.append(o);}
 for(const [id,label] of [['all','All Operands'],['authored','Authored Overrides'],['changed','Changed from Retail']]){const o=el('option',label);o.value=id;layer.append(o);}
 let disposed=false,page=0,total=0;const valid=()=>!disposed&&current()&&!busy();
 function updateState(){const stale=disposed||!current();family.disabled=layer.disabled=search.disabled=stale||busy();previous.disabled=stale||busy()||page===0;next.disabled=stale||busy()||(page+1)*64>=total;for(const b of list.querySelectorAll('button'))b.disabled=stale||busy()||b.dataset.unavailable==='true';if(stale){list.replaceChildren();status.textContent='Controller sources changed. Reopen comparison.';}}
 function render(){if(disposed||!current())return updateState();const rows=filterControllerComparison(value.rows,{family:family.value,layer:layer.value,query:search.value});total=rows.length;page=Math.min(page,Math.max(0,Math.ceil(total/64)-1));list.replaceChildren();status.textContent=`Page ${page+1} / ${Math.max(1,Math.ceil(total/64))} · ${rows.length} / ${value.rows.length} supported operands · ${value.rows.filter(r=>r.changed).length} changed · ${value.rows.filter(r=>r.authored!==null).length} authored overrides`;
  for(const row of rows.slice(page*64,(page+1)*64)){const card=el('section'),title=el('h4',`0x${row.pc.toString(16).toUpperCase().padStart(4,'0')} · ${row.mnemonic} · ${row.label}`);card.dataset.controllerComparisonPc=row.pc;card.style.cssText='border-top:1px solid #45605e;padding:8px 0;overflow-wrap:anywhere';card.append(title);
   for(const [label,v] of [['Retail',row.retail],['Authored',row.authored],['Current',row.current]]){const p=el('p'),b=el('strong',label+': '),code=el('code',v===null?'Inherits Retail':JSON.stringify(v));p.append(b,code);card.append(p);}
   const actions=el('div');actions.style.cssText='display:flex;flex-wrap:wrap;gap:8px';const source=el('button','Inspect Source'),edit=el('button','Open Editing Controls'),control=controls.find(c=>c.kind===row.kind);source.type=edit.type='button';source.dataset.unavailable=String(!boundaries.has(row.pc));edit.dataset.unavailable=String(!boundaries.has(row.pc)||!control||!control.canFocus(row.pc));source.onclick=()=>{if(valid()&&boundaries.has(row.pc))selectSource(row.pc);};edit.onclick=()=>{if(valid()&&boundaries.has(row.pc)&&control?.canFocus(row.pc)&&selectSource(row.pc,false))control.focusPc(row.pc);};actions.append(source,edit);card.append(actions);list.append(card);
  }if(!rows.length)list.append(el('p','No supported operands match these filters.'));updateState();
 }
 family.onchange=layer.onchange=search.oninput=()=>{if(valid()){page=0;render();}};previous.onclick=()=>{if(valid()&&page>0){page--;render();}};next.onclick=()=>{if(valid()&&(page+1)*64<total){page++;render();}};bar.append(family,layer,search,previous,next);section.append(heading,note,bar,status,list);host.prepend(section);render();return {updateState,dispose(){disposed=true;section.remove();}};
}
