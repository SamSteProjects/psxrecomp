"""Current native face selection is an exact GLB roundtrip plus independent corner ownership."""
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import base64,json,shutil,struct,subprocess,tempfile,unittest
from unittest.mock import patch
from importer.assets import decode_tmd
from importer.core import ImportError
from importer.texture_png import _encode_png
from importer.model_glb import export_model_glb
from importer.model_materials import patch_model_materials
from sdk import model_glb,model_materials,model_glb_material_selection as selection
from sdk.project import ProjectService,ProjectError
from sdk.scene_preview import source_key
from test_model_primitives import synthetic
from test_model_glb_normals import rewrite
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server

ASSET='asset://fixture/model/0'


def add_image_links(content,split=False):
    def change(doc,binary):
        png=_encode_png(4,1,bytes([255,0,0,255]*4));binary.extend(b'\0'*(-len(binary)%4));at=len(binary);binary.extend(png)
        view=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=at,byteLength=len(png)))
        doc['images']=[dict(name='Binding image',mimeType='image/png',bufferView=view)]
        doc['textures']=[dict(source=0)];doc['materials']=[dict(name='Target material',pbrMetallicRoughness=dict(baseColorTexture=dict(index=0)))]
        for mesh in doc['meshes']:
            for primitive in mesh['primitives']:primitive['material']=0
        if split:
            primitive=doc['meshes'][0]['primitives'][0]
            if 'indices' not in primitive:
                count=doc['accessors'][primitive['attributes']['POSITION']]['count'];binary.extend(b'\0'*(-len(binary)%4));at=len(binary);binary.extend(struct.pack('<'+'H'*count,*range(count)))
                view=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=at,byteLength=count*2,target=34963))
                primitive['indices']=len(doc['accessors']);doc['accessors'].append(dict(bufferView=view,byteOffset=0,componentType=5123,count=count,type='SCALAR'))
            old=doc['accessors'][primitive['indices']]
            component={5121:1,5123:2,5125:4}[old['componentType']]
            first=deepcopy(old);first['count']=3;second=deepcopy(old);second['count']-=3;second['byteOffset']=second.get('byteOffset',0)+3*component
            i=len(doc['accessors']);doc['accessors'] += [first,second]
            original=deepcopy(primitive);primitive['indices']=i;original['indices']=i+1;original['material']=1
            doc['meshes'][0]['primitives'].append(original);doc['materials'].append(deepcopy(doc['materials'][0]))
    return rewrite(content,change)


class GlbMaterialSelection(unittest.TestCase):
    def setup_project(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        disc=root/'fixture.bin';disc.write_bytes(b'Independent synthetic disc transport')
        p=ProjectService(root/'project');p.import_metadata(synthetic_scene(),str(disc));p.save()
        native=synthetic(((0x22,),),count=2)
        for item in (patch.object(ProjectService,'_model_source',return_value=native),patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()),patch('importer.assets.load_model_preview',side_effect=lambda *_:decode_tmd(native)),patch('sdk.model_glb._texture_preview',side_effect=lambda p,a,v:deepcopy(v))):
            item.start();self.addCleanup(item.stop)
        glb,binding,_=model_glb.export_model(p,ASSET)
        return p,native,add_image_links(glb),binding

    def test_real_codec_roundtrip_corner_faces_node_draft_masks_and_readonly(self):
        p,native,content,binding=self.setup_project();before=deepcopy((p._document(),p.undo_stack,p.redo_stack));key=source_key(p)
        links=selection.links(p,ASSET,content,binding,key);r=selection.faces(p,ASSET,content,binding,key,0,'base_color',0)
        self.assertTrue(r['can_stage']);self.assertEqual(r['face_count'],2)
        self.assertEqual(r['faces'],[dict(object_index=0,group_index=0,primitive_index=i,textured=True,triangle_count=2,material_indices=[0]) for i in range(2)])
        source=model_materials.snapshot(p,ASSET)
        script="""import assert from 'node:assert/strict';import {decodeGlbMaterialLinks,decodeGlbMaterialFaces,glbMaterialFaceEdits,primitiveGlbSelectionSource} from './integrations/legaia/editor/model-glb-material-selection.js';import {validateModelMaterialEdits} from './integrations/legaia/editor/model-materials.js';let raw='';for await(const c of process.stdin)raw+=c;const {links,r,source,primitive_source}=JSON.parse(raw),choice={material_index:0,role:'base_color',image_index:0};decodeGlbMaterialLinks(links,source,r.glb_sha256);decodeGlbMaterialFaces(r,source,links,choice);const adapter=primitiveGlbSelectionSource(primitive_source,{sceneId:source.scene_id,sourceKey:source.project_source_key});decodeGlbMaterialLinks(links,adapter,r.glb_sha256);decodeGlbMaterialFaces(r,adapter,links,choice);const existing=[{kind:'group',object_index:0,group_index:0,values:{semi_transparent:false}}],edits=glbMaterialFaceEdits(source,r,{page_column:5,page_row:1,texture_bpp:16},existing);assert.equal(edits.length,3);assert.deepEqual(edits[0],existing[0]);validateModelMaterialEdits(source,edits);assert.deepEqual(existing,[{kind:'group',object_index:0,group_index:0,values:{semi_transparent:false}}]);for(const mutate of [v=>v.project_source_key='f'.repeat(64),v=>v.face_count=1,v=>v.faces[0].group_index=1,v=>v.faces[0].triangle_count=1,v=>v.faces[1].primitive_index=0,v=>v.faces[0].material_indices=[0,1],v=>v.can_stage=false,v=>v.effective_sha256='f'.repeat(64)]){const bad=structuredClone(r);mutate(bad);assert.throws(()=>decodeGlbMaterialFaces(bad,source,links,choice));}const subset={...r,faces:[r.faces[0]],face_count:1},other={kind:'primitive',object_index:0,primitive_index:1,values:{clut_column:7}},prior=[other,{kind:'primitive',object_index:0,primitive_index:0,values:{clut_column:6,clut_row:8}},...existing],kept=glbMaterialFaceEdits(source,subset,{page_column:5,page_row:1,texture_bpp:16},prior);assert.deepEqual(kept.find(e=>e.kind==='primitive'&&e.primitive_index===1),other);assert(!Object.hasOwn(kept.find(e=>e.kind==='primitive'&&e.primitive_index===0).values,'clut_column'));assert.equal(prior[1].values.clut_column,6);validateModelMaterialEdits(source,kept);console.log(JSON.stringify(edits));"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(links=links,r=r,source=source,primitive_source=p.model_primitive_source(ASSET))),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3]);self.assertEqual(result.returncode,0,result.stderr)
        edits=json.loads(result.stdout);candidate,audit=patch_model_materials(native,sha256(native).hexdigest(),edits)
        self.assertNotEqual(candidate,native);self.assertTrue(all(c.get('field') in ('tpage','gpu_mode') for c in audit))
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)

    def test_split_native_quad_and_stale_or_changed_model_cannot_stage(self):
        p,native,content,binding=self.setup_project();key=source_key(p)
        base,_=export_model_glb(native,decode_tmd(native));split=add_image_links(base,True)
        r=selection.faces(p,ASSET,split,binding,key,0,'base_color',0);self.assertEqual(r['face_count'],1);self.assertEqual(r['ambiguous_face_count'],1);self.assertFalse(r['can_stage'])
        for args in ((0,'normal',0),(0,'base_color',1),(True,'base_color',0)):
            with self.assertRaises(ProjectError):selection.faces(p,ASSET,content,binding,key,*args)
        with self.assertRaises(ProjectError):selection.links(p,ASSET,content,binding,'stale')
        with self.assertRaises(ProjectError):selection.links(p,ASSET,content,dict(binding,effective_sha256='f'*64),key)
        def edit(doc,binary):
            primitive=doc['meshes'][0]['primitives'][0];a=doc['accessors'][primitive['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']];at=v.get('byteOffset',0)+a.get('byteOffset',0);struct.pack_into('<f',binary,at,struct.unpack_from('<f',binary,at)[0]+1)
        # One alias edit rejects in the native importer before it can authorize face selection.
        with self.assertRaises((ProjectError,ImportError)):selection.links(p,ASSET,rewrite(content,edit),binding,key)

    def test_http_exact_routes_readonly_and_face_qualification(self):
        p,native,content,binding=self.setup_project();before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        body=dict(asset_id=ASSET,content_base64=base64.b64encode(content).decode(),binding=binding,source_key=source_key(p))
        with http_server(p) as (_,post):
            for bad in (dict(body,extra=True),dict(body,content_base64='?'),dict(body,source_key='stale'),dict(body,binding={})):
                status,_=post('/api/model-glb-material-links',bad);self.assertEqual(status,400)
            status,r=post('/api/model-glb-material-links',body);self.assertEqual(status,200,r)
            status,r=post('/api/model-glb-material-faces',dict(body,material_index=0,role='base_color',image_index=0));self.assertEqual(status,200,r);self.assertEqual(r['face_count'],2)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)


if __name__=='__main__':unittest.main()
