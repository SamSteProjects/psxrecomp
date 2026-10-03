import assert from 'node:assert/strict';
import {decodeMaterialDonorModels,materialDonorValues,materialDonorRows,materialDonorGroupEdits} from '../editor/model-material-donor.js';
const context={sceneId:'scene://town01',sourceKey:'a'.repeat(64)},model={asset_id:'asset://global/models/0001',label:'Imported model'},catalog={schema_version:'legaia.model-material-donor-models.v1',scene_id:context.sceneId,project_source_key:context.sourceKey,models:[model],project_changed:false};
const decoded=decodeMaterialDonorModels(catalog,context);decoded[0].label='changed';assert.equal(model.label,'Imported model');
for(const change of [{project_changed:true},{scene_id:'scene://other'},{project_source_key:'b'.repeat(64)},{models:[model,model]},{models:[{...model,extra:true}]},{models:Array(2049).fill(model)}])assert.throws(()=>decodeMaterialDonorModels({...catalog,...change},context));
const row={textured:true,texture_bpp:4,page_column:7,page_row:1,clut_column:12,clut_row:93,source_blend_mode:3,uvs:[[1,2]],semi_transparent:true};
assert.deepEqual(materialDonorValues(row),{texture_bpp:4,page_column:7,page_row:1,clut_column:12,clut_row:93});assert.deepEqual(materialDonorValues({...row,texture_bpp:16}),{texture_bpp:16,page_column:7,page_row:1});
for(const change of [{textured:false},{texture_bpp:null},{page_column:16},{clut_row:512},{page_row:true}])assert.throws(()=>materialDonorValues({...row,...change}));
const source={objects:[{object_index:2,groups:[{group_index:4,primitives:[{...row,primitive_index:9,byte_offset:128},{...row,texture_bpp:null},{...row,textured:false}]}]}]};
assert.deepEqual(materialDonorRows(source),[{object_index:2,group_index:4,primitive_index:9,byte_offset:128,values:materialDonorValues(row)}]);
console.log('Material source catalog and indexed/direct binding draft guards passed.');

const target={objects:[{object_index:2,groups:[{group_index:4,primitives:[{...row,primitive_index:9,page_column:1},{...row,primitive_index:10},{...row,textured:false,primitive_index:11}]}]}]};
const before=structuredClone(target);assert.deepEqual(materialDonorGroupEdits(target,2,4,row),[{kind:'primitive',object_index:2,primitive_index:9,values:{page_column:7}},{kind:'primitive',object_index:2,primitive_index:10,values:{}}]);assert.deepEqual(target,before);assert.throws(()=>materialDonorGroupEdits(target,2,5,row));assert(materialDonorGroupEdits(target,2,4,{...row,texture_bpp:16}).every(edit=>!Object.keys(edit.values).some(key=>key.startsWith('clut_'))));
console.log('Group binding drafts preserve source and omit untextured rows/direct CLUT fields.');
