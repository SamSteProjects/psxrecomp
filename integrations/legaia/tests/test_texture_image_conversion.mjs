import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {decodeImageConversion} from '../editor/texture-image-conversion.js';
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
