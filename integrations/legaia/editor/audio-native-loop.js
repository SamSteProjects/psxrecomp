// Supported native ADPCM arithmetic with continuous predictor history at a loop.
// No Gaussian interpolation, driver pitch, voice registers or live mix.
import {encodedPcmLoop} from './audio-pcm-loop.js';
import {decodeSampleWave,exact,equal,hash} from './audio-sample-contract.js';
import {simulateEnvelope,ENVELOPE_RATE,MAX_ENVELOPE_FRAMES} from './audio-envelope.js';
import {PREVIEW_RATES} from './audio-audition.js';
const coefficients=[[0,0],[60,0],[115,-52],[98,-55],[122,-60]],integer=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
export function nativeLoopQualified(wave){return Boolean(encodedPcmLoop(wave,wave.decoded_frames))&&!wave.markers.some(m=>m.encoded_shift>12)&&wave.source_size_bytes<=65536;}
export function decodeNativeLoop(raw,frameCount){
 if(!(raw instanceof Uint8Array)||raw.length<16||raw.length>65536||!integer(frameCount,1,240001))throw Error('Native ADPCM loop requires bounded source bytes and output frames.');
 let sourceFrames=0,loopStart=null,end=null;
 for(let at=0;at+16<=raw.length;at+=16){
  const header=raw[at],flags=raw[at+1];if((header>>4)>4||(header&15)>12||flags&~7)throw Error('Native ADPCM loop has unsupported predictor, shift or flag bits.');
  if(flags&4)loopStart=at;sourceFrames+=28;
  if(flags&1){if(!(flags&2)||loopStart===null)throw Error('Native ADPCM sample has no explicit repeated loop.');end=at;break;}
 }
 if(end===null)throw Error('Native ADPCM sample has no complete bounded end/repeat block.');
 const bytes=new Uint8Array(frameCount*2),output=new DataView(bytes.buffer);let previous=0,older=0,at=0,count=0,wraps=0;
 while(count<frameCount){
  const header=raw[at],flags=raw[at+1],[first,second]=coefficients[header>>4],shift=header&15;
  // The source is prequalified above. Neither predictor history is reset at END.
  for(let b=at+2;b<at+16&&count<frameCount;b++)for(const nibble of [raw[b]&15,raw[b]>>4]){
   if(count>=frameCount)break;const signed=nibble<8?nibble:nibble-16,prediction=(previous*first+older*second+32)>>6;
   const value=Math.max(-32768,Math.min(32767,(signed<<(12-shift))+prediction));output.setInt16(count++*2,value,true);older=previous;previous=value;
  }
  if(count%28)break;
  if(flags&1){at=loopStart;wraps++;}else at+=16;
 }
 return {bytes,sourceFrames,loop:{startFrame:loopStart/16*28,endFrame:sourceFrames},wraps};
}
export async function decodeNativeSample(value,context,bank,sample,layer,sha,currentEntryHash,waveform,pcm){
 const keys=['schema_version','asset_id','sample_index','authoring_key','layer','source_record','current_entry_sha256','sample_sha256','waveform','format','adpcm_base64','project_changed','runtime_state'];
 if(!exact(value,keys)||value.schema_version!=='legaia.audio-sample-adpcm.v1'||value.asset_id!==context.assetId||value.sample_index!==sample.index||value.authoring_key!==context.authoringKey||!['retail','current'].includes(layer)||value.layer!==layer||!equal(value.source_record,bank.source_record)||!hash(currentEntryHash)||value.current_entry_sha256!==currentEntryHash||value.sample_sha256!==sha||value.format!=='psx-spu-adpcm-blocks'||typeof value.adpcm_base64!=='string'||value.adpcm_base64.length>87384||value.project_changed!==false||value.runtime_state!=='not_observed')throw Error('Native ADPCM preview differs from its selected source layer.');
 const wave=decodeSampleWave(value.waveform,bank,sample,sha);if(!equal(wave,waveform)||!nativeLoopQualified(wave)||!(pcm instanceof Uint8Array)||pcm.length!==wave.decoded_frames*2||!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value.adpcm_base64))throw Error('Native ADPCM loop differs from its qualified waveform.');
 const text=atob(value.adpcm_base64);if(text.length!==wave.source_size_bytes||btoa(text)!==value.adpcm_base64)throw Error('Native ADPCM extent differs from its complete source sample.');
 const raw=Uint8Array.from(text,c=>c.charCodeAt(0)),digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),b=>b.toString(16).padStart(2,'0')).join('');if(digest!==sha)throw Error('Native ADPCM byte hash differs from the qualified sample.');
 const decoded=decodeNativeLoop(raw,wave.decoded_frames);if(!equal(decoded.loop,encodedPcmLoop(wave,wave.decoded_frames))||decoded.bytes.some((b,i)=>b!==pcm[i]))throw Error('Native ADPCM first pass differs from the verified PCM prefix.');
 return raw;
}
export function renderNativeEnvelope(raw,rate,adsr1,adsr2,window={}){
 if(!PREVIEW_RATES.includes(rate))throw Error('Choose an explicit supported native ADPCM preview rate.');
 const model=simulateEnvelope(adsr1,adsr2,window),required=Math.ceil(model.frameCount*rate/ENVELOPE_RATE)+1;
 if(model.frameCount>MAX_ENVELOPE_FRAMES)throw Error('Native envelope exceeds its bounded window.');
 const decoded=decodeNativeLoop(raw,required),input=new DataView(decoded.bytes.buffer),bytes=new Uint8Array(model.frameCount*2),output=new DataView(bytes.buffer);
 for(let i=0;i<model.frameCount;i++){
  const numerator=i*rate,at=Math.floor(numerator/ENVELOPE_RATE),fraction=(numerator%ENVELOPE_RATE)/ENVELOPE_RATE,a=input.getInt16(at*2,true),b=input.getInt16((at+1)*2,true);
  output.setInt16(i*2,Math.trunc((a+(b-a)*fraction)*model.levels[i]/32768),true);
 }
 return {bytes,model,sourceRate:rate,outputRate:ENVELOPE_RATE,nativeLoop:decoded.loop};
}
