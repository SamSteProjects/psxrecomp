"""The readonly display graph preserves image ownership and bounds every reference."""
from copy import deepcopy
from hashlib import sha256
import base64,json,shutil,subprocess,unittest
from pathlib import Path
from importer.core import ImportError
from importer.texture_png import _encode_png
from importer.texture_glb_dependencies import inspect_glb_dependencies
import test_texture_glb as glb_fixtures
import test_texture_slots_workflow as fixtures
from test_model_primitive_workflow import http_server


def graph_doc(doc):
    doc['images'] += [dict(name='Normal image',mimeType='image/png',bufferView=0),dict(name='Unused image',mimeType='image/png',bufferView=0)]
    doc['samplers']=[dict(magFilter=9728,wrapS=33071)]
    doc['textures']=[dict(source=0,sampler=0),dict(source=1),dict(source=2),dict(source=3),dict(extensions={})]
    doc['materials']=[dict(name='Wall shader',pbrMetallicRoughness=dict(baseColorTexture=dict(index=0),metallicRoughnessTexture=dict(index=1,texCoord=1),baseColorFactor=[1,0,0,1]),normalTexture=dict(index=2),doubleSided=True),dict(name='Unused emissive material',emissiveTexture=dict(index=0)),dict(name='Plain')]
    doc['meshes']=[dict(primitives=[dict(material=0),dict(material=0),dict(material=2),dict()]),dict(primitives=[])]


def fixture(change=None):
    png=_encode_png(4,1,bytes([255,0,0,255]*4))
    def mutate(doc):
        graph_doc(doc)
        if change:change(doc)
    return glb_fixtures.glb_png(png,mutate)


class GlbDependencies(unittest.TestCase):
    def test_inventory_graph_node_decoder_and_shared_unused_uri_dependencies(self):
        content=fixture();r=inspect_glb_dependencies(content)
        self.assertEqual(r['catalog']['glb_sha256'],sha256(content).hexdigest())
        self.assertEqual(r['catalog']['excluded_image_indices'],[1]);self.assertEqual([i['image_index'] for i in r['catalog']['images']],[0,2,3])
        self.assertEqual(r['primitive_count'],4);self.assertEqual(r['mesh_count'],2)
        self.assertEqual(r['texture_links'][4]['image_index'],None)
        self.assertEqual(r['materials'][0]['links'][1],dict(role='metallic_roughness',texture_index=1,texcoord=1,has_extensions=False))
        self.assertFalse(r['native_binding_inferred']);self.assertFalse(r['project_changed'])
        script="""import assert from 'node:assert/strict';import {decodeGlbDependencies,glbImageUses,loadGlbImageDependencies} from './integrations/legaia/editor/texture-glb-dependencies.js';let text='';for await(const c of process.stdin)text+=c;const r=JSON.parse(text),h=r.catalog.glb_sha256;decodeGlbDependencies(r,h);const links=glbImageUses(r,0);assert.equal(links.length,2);assert.equal(links[0].primitives.length,2);assert.equal(links[1].primitives.length,0);assert.deepEqual(glbImageUses(r,3),[]);assert.equal(glbImageUses(r,1)[0].texcoord,1);const direct=await loadGlbImageDependencies(async()=>r,'unused',h);assert.deepEqual(direct.graph,r);const calls=[],fallback=await loadGlbImageDependencies(async route=>{calls.push(route);if(route.endsWith('dependencies'))throw new Error('Invalid material reference');return r.catalog;},'unused',h);assert.deepEqual(calls,['/api/texture-glb-dependencies','/api/texture-glb-images']);assert.equal(fallback.graph,null);assert.deepEqual(fallback.catalog,r.catalog);assert.equal(fallback.issue,'Invalid material reference');const abort=new Error('Closed');abort.name='AbortError';let attempts=0;await assert.rejects(loadGlbImageDependencies(async()=>{attempts++;throw abort;},'unused',h));assert.equal(attempts,1);await assert.rejects(loadGlbImageDependencies(async()=>{throw new Error('Invalid PNG');},'unused',h));
for(const mutate of [v=>v.native_binding_inferred=true,v=>v.catalog.glb_sha256='f'.repeat(64),v=>v.texture_links[0].image_index=true,v=>v.texture_links[0].sampler_index=1,v=>v.materials[0].links[0].texture_index=5,v=>v.materials[0].links[1].role='base_color',v=>v.materials[0].shader_features.reverse(),v=>v.primitive_uses[1].primitive_index=0,v=>v.primitive_uses[0].material_index=true,v=>v.primitive_count=3]){const bad=structuredClone(r);mutate(bad);assert.throws(()=>decodeGlbDependencies(bad,h));}
"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(r),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_malformed_references_names_and_work_budget_reject(self):
        changes=(lambda d:d.update(textures={}),lambda d:d.update(materials=[{}]*257),lambda d:d['textures'][0].update(source=True),lambda d:d['textures'][0].update(source=4),lambda d:d['textures'][0].update(sampler=1),lambda d:d['textures'][0].update(extensions=[]),lambda d:d['samplers'][0].update(magFilter=True),lambda d:d['materials'][0].update(name='Bad\x00name'),lambda d:d['materials'][0].update(pbrMetallicRoughness=None),lambda d:d['materials'][0]['normalTexture'].update(index=5),lambda d:d['materials'][0]['normalTexture'].update(texCoord=True),lambda d:d['materials'][0]['normalTexture'].update(texCoord=8),lambda d:d['meshes'][0]['primitives'][0].update(material=3),lambda d:d['meshes'][0].update(primitives=[{}]*4097),lambda d:d['meshes'][1].update(primitives=[{}]*4096))
        for change in changes:
            with self.assertRaises(ImportError):inspect_glb_dependencies(fixture(change))

    def test_http_exact_input_readonly_and_no_external_fetch(self):
        helper=fixtures.TextureSlotsWorkflow();self.addCleanup(helper.doCleanups);p,*_=helper.setup_project()
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        body=dict(content_base64=base64.b64encode(fixture()).decode())
        with http_server(p) as (_,post):
            for bad in ({},dict(body,extra=1),dict(content_base64='?')):
                status,_=post('/api/texture-glb-dependencies',bad);self.assertEqual(status,400)
            status,r=post('/api/texture-glb-dependencies',body);self.assertEqual(status,200,r)
            self.assertEqual(r,inspect_glb_dependencies(fixture()))
            malformed=dict(content_base64=base64.b64encode(fixture(lambda d:d['meshes'][0]['primitives'][0].update(material=99))).decode())
            status,_=post('/api/texture-glb-dependencies',malformed);self.assertEqual(status,400)
            status,r=post('/api/texture-glb-images',malformed);self.assertEqual(status,200,r)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before);self.assertFalse((p.root/'Authored').exists())


if __name__=='__main__':unittest.main()
