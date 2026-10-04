"""A selected static scene excludes unrelated activity without posing a mesh."""
from copy import deepcopy
from pathlib import Path
import base64,json,shutil,subprocess,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from sdk import model_mesh_append,model_mesh_batch
from sdk.project import ProjectService
from sdk.build import build_project
import test_model_mesh_append as fixtures
from test_model_primitive_workflow import http_server


def mixed(doc):
    doc['nodes']=[dict(mesh=0,translation=[40,20,10]),dict(children=[0]),
                  dict(mesh=0,skin=0),dict()]
    doc['scenes']=[dict(name='Animated',nodes=[2]),dict(name='Static',nodes=[1])]
    doc['skins']=[dict(joints=[3])]
    time=len(doc['accessors']);doc['accessors'].append(dict(bufferView=0,componentType=5126,count=1,type='SCALAR',min=[0],max=[0]))
    output=len(doc['accessors']);doc['accessors'].append(dict(bufferView=0,componentType=5126,count=1,type='VEC3'))
    doc['animations']=[dict(channels=[dict(sampler=0,target=dict(node=2,path='translation'))],
                            samplers=[dict(input=time,output=output)])]


class MeshStaticSelectionTests(unittest.TestCase):
    def test_selected_nodes_and_ancestors_reject_activity_but_other_scene_is_excluded(self):
        with self.assertRaisesRegex(ImportError,'node 2 is animated'):
            decode_append_mesh(fixtures.glb(mixed))
        geometry=decode_append_mesh(fixtures.glb(mixed),scene_index=1)
        expected=dict(selected_nodes=[1,0],animated_nodes=[2],animation_count=1,skin_count=1)
        self.assertEqual(geometry['static_scope'],expected)
        self.assertEqual(inspect_append_mesh(fixtures.glb(mixed),scene_index=1)['static_scope'],expected)
        self.assertEqual(geometry['vertices'][0],[40,-20,10])
        for node in (0,1):
            def selected(doc):mixed(doc);doc['animations'][0]['channels'][0]['target']['node']=node
            with self.assertRaisesRegex(ImportError,f'node {node} is animated'):
                inspect_append_mesh(fixtures.glb(selected),scene_index=1)
        def selected_skin(doc):mixed(doc);doc['nodes'][0]['skin']=0
        with self.assertRaisesRegex(ImportError,'unskinned'):
            decode_append_mesh(fixtures.glb(selected_skin),scene_index=1)
        def skin_only(doc):mixed(doc);doc.pop('animations')
        self.assertEqual(decode_append_mesh(fixtures.glb(skin_only),scene_index=1)['static_scope']['animated_nodes'],[])
        self.assertNotIn('static_scope',decode_append_mesh(fixtures.glb()))
        def empty(doc):mixed(doc);doc['scenes'].append(dict(nodes=[]))
        self.assertEqual(inspect_append_mesh(fixtures.glb(empty),scene_index=2)['static_scope']['selected_nodes'],[])

    def test_ambiguous_or_unbounded_activity_rejects_before_native_publication(self):
        changes=[lambda d:d.update(animations=True),lambda d:d.update(skins=[None]),
                 lambda d:d.update(animations=d['animations']*65),
                 lambda d:d['animations'][0].update(channels=d['animations'][0]['channels']*257),
                 lambda d:d['animations'][0].update(extensions={}),
                 lambda d:d['animations'][0]['channels'][0].update(sampler=True),
                 lambda d:d['animations'][0]['channels'][0].update(extensions={}),
                 lambda d:d['animations'][0]['channels'][0]['target'].update(node=True),
                 lambda d:d['animations'][0]['channels'][0]['target'].update(node=4),
                 lambda d:d['animations'][0]['channels'][0]['target'].pop('node'),
                 lambda d:d['animations'][0]['channels'][0]['target'].update(path='pointer'),
                 lambda d:d['animations'][0]['channels'][0]['target'].update(extensions={})]
        for change in changes:
            def mutate(doc):mixed(doc);change(doc)
            with self.assertRaises(ImportError):inspect_append_mesh(fixtures.glb(mutate),scene_index=1)

    def test_http_atomic_history_save_open_build_and_browser_scope_qualification(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        source=model_mesh_append.source(p,asset,'a'*64)
        def sections(doc):mixed(doc);doc['meshes'][0]['primitives'].append(deepcopy(doc['meshes'][0]['primitives'][0]))
        content=fixtures.glb(sections)
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        files=set((p.root/'Authored'/'Models').iterdir())
        candidate,_,report=model_mesh_batch.prepare(p,*args,scene_index=1)
        def other_target(doc):sections(doc);doc['animations'][0]['channels'][0]['target']['node']=3
        changed_content=fixtures.glb(other_target)
        changed_candidate,_,changed=model_mesh_batch.prepare(p,asset,changed_content,mappings,source['effective_sha256'],'a'*64,scene_index=1)
        self.assertEqual(changed_candidate,candidate)
        self.assertNotEqual(changed['review_key'],report['review_key'])
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,
                      expected_sha256=source['effective_sha256'],source_key='a'*64,scene_index=1)
            status,review=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,review)
            status,_=post('/api/model-mesh-batch',dict(body,content_base64=base64.b64encode(changed_content).decode(),review_key=review['review_key']))
            self.assertEqual(status,400);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,_=post('/api/model-mesh-batch',dict(body,scene_index=0,review_key=review['review_key']))
            self.assertEqual(status,400);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,result=post('/api/model-mesh-batch',dict(body,review_key=review['review_key']))
            self.assertEqual(status,200,result)
        self.assertEqual(len(p.undo_stack),len(before[1])+1)
        p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            entry=tomllib.loads(package.read('manifest.toml').decode())['disc_relocation'][0]
            archive=_archive(decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)
        script="""import {decodeMeshBatchReview} from './integrations/legaia/editor/model-mesh-batch.js';
import assert from 'node:assert/strict';let input='';for await(const c of process.stdin)input+=c;
const {source,report}=JSON.parse(input);decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings,false,1);
for(const mutate of [r=>r.inventory.static_scope.selected_nodes=[1],r=>r.inventory.static_scope.animated_nodes=[0,2],r=>r.inventory.static_scope.animation_count=true,r=>r.steps[0].review.geometry.static_scope.skin_count=2,r=>r.steps[0].review.geometry.static_scope.selected_nodes=[1]]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshBatchReview(bad,source,report.glb_sha256,report.mappings,false,1));}"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)
