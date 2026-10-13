import {placementDigest} from './worldmap-placement-replay.js';
const ordered=v=>Array.isArray(v)?v.map(ordered):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,ordered(v[k])])):v;
const same=(a,b)=>JSON.stringify(ordered(a))===JSON.stringify(ordered(b)),fail=()=>{throw Error('Monster Current motion ledger changed.');};
const decode=s=>{if(typeof s!=='string'||s.length>200000)fail();return Uint8Array.from(atob(s),c=>c.charCodeAt(0));};
export function nativeMonsterChannels(raw,at){const n=[raw[at]|(raw[at+2]&15)<<8,raw[at+1]|(raw[at+2]>>4)<<8,raw[at+3]|(raw[at+5]&15)<<8,raw[at+4]|(raw[at+5]>>4)<<8,raw[at+6]|(raw[at+8]&15)<<8,raw[at+7]|(raw[at+8]>>4)<<8];return {translation:n.slice(0,3).map(v=>v&2048?v-4096:v),rotation_psx:n.slice(3)};}
export function packedMonsterChannels(t,r){const [x,y,z]=t.map(n=>n&4095),[rx,ry,rz]=r;return [x&255,y&255,x>>8|(y>>8)<<4,z&255,rx&255,z>>8|(rx>>8)<<4,ry&255,rz&255,ry>>8|(rz>>8)<<4];}
export async function qualifyMonsterMotionBytes(v,clip){
 const current=decode(v.source_motion_base64),retail=decode(v.retail_motion_base64??v.source_motion_base64),b=v.motion_binding,expected=new Uint8Array(retail);
 if(retail.length!==clip.source_record.byte_length||current.length!==retail.length||await placementDigest(retail)!==clip.source_record.sha256||retail[0]!==clip.part_count||retail[1]!==clip.frame_count)fail();
 if(b){if(b.schema_version!=='legaia.monster-motion-override.v1'||b.asset_id!==clip.semantic_id||!same(b.source_record,clip.source_record)||!Array.isArray(b.edits)||b.edits.length<1||b.edits.length>clip.frame_count*clip.part_count)fail();let previous=-1;
  for(const e of b.edits){const f=e.frame_index,p=e.part_index,k=f*clip.part_count+p;if(!Number.isSafeInteger(f)||f<0||f>=clip.frame_count||!Number.isSafeInteger(p)||p<0||p>=clip.part_count||k<=previous)fail();for(const [a,lo,hi] of [[e.translation,-2048,2047],[e.rotation_psx,0,4095]])if(!Array.isArray(a)||a.length!==3||a.some(n=>!Number.isSafeInteger(n)||n<lo||n>hi))fail();const at=2+k*9;if(same(nativeMonsterChannels(retail,at),{translation:e.translation,rotation_psx:e.rotation_psx}))fail();expected.set(packedMonsterChannels(e.translation,e.rotation_psx),at);previous=k;}
  if(await placementDigest(expected)!==b.current_motion_sha256)fail();
 }
 if(!same([...expected],[...current]))fail();return current;
}

export async function qualifyMonsterMotionEntry(v,clip){
 const decodeEntry=s=>{if(typeof s!=='string'||s.length>900000)fail();return Uint8Array.from(atob(s),c=>c.charCodeAt(0));},current=decodeEntry(v.source_entry_base64),retail=decodeEntry(v.retail_entry_base64??v.source_entry_base64),expected=new Uint8Array(retail),stream=await qualifyMonsterMotionBytes(v,clip),at=clip.source_record.byte_offset-clip.source_record.entry_offset;
 if(retail.length!==clip.source_record.entry_end-clip.source_record.entry_offset||current.length!==retail.length||await placementDigest(retail)!==clip.source_record.entry_sha256||at<0||at+stream.length>retail.length)fail();expected.set(stream,at);
 if(!same([...current],[...expected])||await placementDigest(expected)!==(v.motion_binding?.current_entry_sha256??clip.source_record.entry_sha256))fail();return current;
}
