import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {decodeImageConversion,decodeSourceRetention,decodeRetainedInputs} from '../editor/texture-image-conversion.js';
const hash=v=>v.repeat(64),options={bpp:16,image_x:640,image_y:32,clut_x:0,clut_y:0,stp_mode:'opaque'};
const bytes=Buffer.alloc(28);bytes.writeUInt32LE(16,0);bytes.writeUInt32LE(2,4);bytes.writeUInt32LE(20,8);bytes.writeUInt16LE(640,12);bytes.writeUInt16LE(32,14);bytes.writeUInt16LE(4,16);bytes.writeUInt16LE(1,18);bytes.writeUInt16LE(31,20);bytes.writeUInt16LE(31,22);bytes.writeUInt16LE(31,24);bytes.writeUInt16LE(31,26);
const request={asset_id:'texture://fixture/1/raw/0',source_key:hash('a'),options};
const input={sceneId:'scene://fixture',pngSha256:hash('b'),pngSize:100,stpSha256:null};
const report={schema_version:'legaia.texture-image-conversion.v1',png_sha256:input.pngSha256,png_byte_length:100,stp_png_sha256:null,options,width:4,height:1,proposed_sha256:createHash('sha256').update(bytes).digest('hex'),byte_length:28,palette_count:0,quantization:{color_max_error:0,color_rms_error:0,quantized_pixel_count:0,visible_pixel_count:4,transparent_pixel_count:0,distinct_requested_words:1,palette_representative_count:0,used_palette_entries:0,forced_black_stp_pixels:0,forced_transparent_stp_pixels:0},native_readback_verified:true,alpha_stp_classes_verified:true,project_changed:false,gameplay_verified:false,limitations:['Explicit native draft.']};
const value={report,asset_id:request.asset_id,project_source_key:request.source_key,source_scene_id:input.sceneId,content_base64:bytes.toString('base64')};
assert.equal((await decodeImageConversion(value,request,input)).sha256,report.proposed_sha256);
for(const bad of [{...value,project_source_key:'stale'},{...value,asset_id:'other'},{...value,extra:true},{...value,report:{...report,png_sha256:hash('c')}},{...value,report:{...report,proposed_sha256:hash('c')}},{...value,report:{...report,palette_count:1}},{...value,report:{...report,quantization:{...report.quantization,color_rms_error:NaN}}},{...value,report:{...report,quantization:{...report.quantization,visible_pixel_count:3}}},{...value,report:{...report,project_changed:true}}])await assert.rejects(decodeImageConversion(bad,request,input));
for(const at of [0,4,8,12,14,16,18]){
  const malformed=Buffer.from(bytes);malformed[at]^=1;
  const replaced={...value,content_base64:malformed.toString('base64'),report:{...report,proposed_sha256:createHash('sha256').update(malformed).digest('hex')}};
  await assert.rejects(decodeImageConversion(replaced,request,input));
}
console.log('PNG draft source/context/hash, diagnostics and independently checked native header qualification passed.');

const draft=await decodeImageConversion(value,request,input),retentionRequest={...request,expected_sha256:draft.sha256},source={format:'png-tim-source-v1',png_sha256:input.pngSha256,png_byte_length:input.pngSize,stp_png_sha256:null,stp_png_byte_length:null,options,conversion_report:report};
const retained={schema_version:'legaia.texture-slot-source-retention.v1',asset_id:request.asset_id,project_source_key:request.source_key,effective_sha256:draft.sha256,source,native_bytes_changed:false,changed:true,can_apply:true,project_changed:false,gameplay_verified:false,review_key:hash('c')};
assert.deepEqual(decodeSourceRetention(retained,retentionRequest,draft,{...input,stpSize:null}),retained);
for(const bad of [{...retained,native_bytes_changed:true},{...retained,effective_sha256:hash('d')},{...retained,source:{...source,png_byte_length:99}},{...retained,source:{...source,conversion_report:{...report,byte_length:29}}},{...retained,changed:false}])assert.throws(()=>decodeSourceRetention(bad,retentionRequest,draft,{...input,stpSize:null}));
console.log('Retention source/recipe/native hash, metadata-only status and Apply qualification passed.');

const retainedPng=Buffer.alloc(100),pngHash=createHash('sha256').update(retainedPng).digest('hex'),retainedReport={...report,png_sha256:pngHash},retainedSource={...source,png_sha256:pngHash,conversion_report:retainedReport},download={asset_id:request.asset_id,project_source_key:request.source_key,effective_sha256:draft.sha256,source:retainedSource,png_base64:retainedPng.toString('base64'),stp_png_base64:null,read_only:true,project_changed:false};
const retainedContext={sourceKey:request.source_key,sceneId:input.sceneId};
assert.deepEqual((await decodeRetainedInputs(download,request.asset_id,retainedContext,draft.sha256,value.content_base64,retainedSource)).png,Uint8Array.from(retainedPng));
assert.deepEqual((await decodeRetainedInputs({...download,source:Object.fromEntries(Object.entries(retainedSource).reverse())},request.asset_id,retainedContext,draft.sha256,value.content_base64,retainedSource)).options,options);
for(const bad of [{...download,project_source_key:'stale'},{...download,effective_sha256:hash('d')},{...download,asset_id:'other'},{...download,project_changed:true},{...download,extra:true},{...download,png_base64:Buffer.alloc(99).toString('base64')},{...download,png_base64:Buffer.alloc(100,1).toString('base64')},{...download,stp_png_base64:'AAAA'},{...download,source:{...retainedSource,png_byte_length:99}}])await assert.rejects(decodeRetainedInputs(bad,request.asset_id,retainedContext,draft.sha256,value.content_base64,retainedSource));
await assert.rejects(decodeRetainedInputs(download,request.asset_id,retainedContext,draft.sha256,Buffer.alloc(28).toString('base64'),retainedSource));
console.log('Retained input load context, exact PNG/native hashes, recipe equality and saved key order qualification passed.');

const missingPlaneReceipt={...retainedSource,stp_png_sha256:pngHash,stp_png_byte_length:retainedPng.length,conversion_report:{...retainedReport,stp_png_sha256:pngHash}};
await assert.rejects(decodeRetainedInputs({...download,source:missingPlaneReceipt},request.asset_id,retainedContext,draft.sha256,value.content_base64,missingPlaneReceipt));

const glbBytes=Buffer.alloc(28,7),glbHash=createHash('sha256').update(glbBytes).digest('hex'),selection={content_base64:glbBytes.toString('base64'),image_index:0,glb_sha256:glbHash,png_sha256:pngHash},glbReceipt={glb_sha256:glbHash,png_sha256:pngHash,image_index:0,name:'Embedded source',glb_byte_length:28};
const glbSource={...retainedSource,glb_source:glbReceipt},glbDownload={...download,source:glbSource,glb_base64:selection.content_base64};
const loadedGlb=await decodeRetainedInputs(glbDownload,request.asset_id,retainedContext,draft.sha256,value.content_base64,glbSource);assert.deepEqual(loadedGlb.glbSource,selection);
const glbRequest={...request,png_base64:download.png_base64,stp_png_base64:null,glb_source:selection},glbInput={...input,pngSha256:pngHash,glbReceipt};
const glbDraft=await decodeImageConversion({...value,report:retainedReport},glbRequest,glbInput);assert.deepEqual(glbDraft.conversionSource.glb_source,selection);
const glbRetention={...retained,source:glbSource};assert.deepEqual(decodeSourceRetention(glbRetention,{...glbRequest,expected_sha256:draft.sha256},glbDraft,{...glbInput,stpSize:null}),glbRetention);
for(const bad of [{...glbDownload,glb_base64:null},{...glbDownload,glb_base64:Buffer.alloc(28,8).toString('base64')},{...glbDownload,glb_base64:Buffer.alloc(27,7).toString('base64')},{...glbDownload,source:{...glbSource,glb_source:{...glbReceipt,image_index:true}}}])await assert.rejects(decodeRetainedInputs(bad,request.asset_id,retainedContext,draft.sha256,value.content_base64,bad.source));
for(const receipt of [{...glbReceipt,image_index:1},{...glbReceipt,glb_sha256:hash('f')},{...glbReceipt,png_sha256:hash('f')},{...glbReceipt,name:'Other'}])assert.throws(()=>decodeSourceRetention({...glbRetention,source:{...glbSource,glb_source:receipt}},{...glbRequest,expected_sha256:draft.sha256},glbDraft,{...glbInput,stpSize:null}));
console.log('GLB conversion lineage, retained file hash/length, metadata receipt and selected image guards passed.');
