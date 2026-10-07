import {exact,equal,hash,integer} from './audio-sample-contract.js';

export function decodeWavRemoval(v,key,receipt){
 if(!exact(v,['schema_version','authoring_key','receipt_key','wav_sha256','source_file_deleted','native_content_changed','registered_bytes_released','review_key'])||v.schema_version!=='legaia.audio-sample-source-removal.v1'||v.authoring_key!==key||v.receipt_key!==receipt.receipt_key||v.wav_sha256!==receipt.wav_sha256||v.source_file_deleted!==false||v.native_content_changed!==false||![0,receipt.byte_length].includes(v.registered_bytes_released)||!hash(v.review_key))throw Error('WAV registration removal differs from its reviewed input.');
 return structuredClone(v);
}
export async function decodeWavRecovery(v,key,receipt){
 if(!exact(v,['schema_version','authoring_key','imports','historical_inputs','project_changed','runtime_state','selected','wav_base64'])||v.schema_version!=='legaia.audio-sample-sources.v1'||v.authoring_key!==key||v.historical_inputs!==true||v.project_changed!==false||v.runtime_state!=='not_observed'||!Array.isArray(v.imports)||v.imports.length>32||v.imports.filter(r=>equal(r,receipt)).length!==1||!equal(v.selected,receipt)||typeof v.wav_base64!=='string'||v.wav_base64.length>1398104||!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(v.wav_base64))throw Error('WAV recovery differs from Current retained input.');
 const raw=atob(v.wav_base64);if(raw.length!==receipt.byte_length||btoa(raw)!==v.wav_base64)throw Error('Retained WAV extent changed.');
 const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0)),sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');if(sha!==receipt.wav_sha256)throw Error('Retained WAV content hash changed.');
 inspectInputWav(bytes,receipt);return bytes;
}
// Independently verify RIFF extents and declared PCM fields without normalizing bytes.
export function inspectInputWav(bytes,receipt){
 if(!(bytes instanceof Uint8Array)||!integer(bytes.length,44,1048576))throw Error('Invalid retained WAV size.');
 const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),text=at=>String.fromCharCode(...bytes.subarray(at,at+4));
 if(text(0)!=='RIFF'||text(8)!=='WAVE'||view.getUint32(4,true)!==bytes.length-8)throw Error('Invalid retained RIFF extent.');
 let cursor=12,format=null,data=null;while(cursor<bytes.length){if(cursor+8>bytes.length)throw Error('Incomplete retained WAV chunk.');const name=text(cursor),size=view.getUint32(cursor+4,true),start=cursor+8,end=start+size,padded=end+(size%2);if(padded>bytes.length)throw Error('Retained WAV chunk exceeds its extent.');if(name==='fmt '){if(format||![16,18].includes(size))throw Error('Invalid retained PCM format chunk.');format=start;if(size===18&&view.getUint16(start+16,true)!==0)throw Error('Unsupported retained PCM extension.');}else if(name==='data'){if(data)throw Error('Duplicate retained PCM data.');data={start,size};}cursor=padded;}
 if(format===null||!data||view.getUint16(format,true)!==1||view.getUint16(format+2,true)!==1||view.getUint16(format+14,true)!==16||view.getUint16(format+12,true)!==2||view.getUint32(format+4,true)!==receipt.input_wav_rate||view.getUint32(format+8,true)!==receipt.input_wav_rate*2||data.size!==receipt.decoded_frames*2)throw Error('Retained WAV PCM fields differ from the receipt.');
 return {frames:data.size/2,rate:receipt.input_wav_rate};
}
