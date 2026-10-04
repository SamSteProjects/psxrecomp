"""A standard GLB appends native topology with one reviewed history command."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import base64,json,struct,tomllib,unittest,zipfile,shutil,subprocess
from urllib.request import urlopen
from unittest.mock import patch
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_mesh_append import decode_append_mesh
from sdk import model_mesh_append,model_face_addition
from sdk.project import ProjectService,ProjectError
from sdk.build import build_project
import test_model_growth_normal_build as build_fixtures
from test_model_primitive_workflow import http_server


def glb(changes=None,positions=None,normals=None,uvs=None,colors=None,color_component=5126):
    positions=positions or [[0,0,0],[100,0,0],[0,100,0],[100,100,0]]
    binary=b''.join(struct.pack('<3f',*row) for row in positions)+struct.pack('<6H',0,1,2,1,3,2)
    doc=dict(asset={'version':'2.0'},scene=0,scenes=[{'nodes':[0]}],nodes=[{'mesh':0}],
        meshes=[{'primitives':[{'attributes':{'POSITION':0},'indices':1,'mode':4}]}],
        buffers=[{'byteLength':len(binary)}],bufferViews=[{'buffer':0,'byteOffset':0,'byteLength':len(positions)*12},
        {'buffer':0,'byteOffset':len(positions)*12,'byteLength':12}],
        accessors=[{'bufferView':0,'componentType':5126,'count':len(positions),'type':'VEC3'},
                   {'bufferView':1,'componentType':5123,'count':6,'type':'SCALAR'}])
    if normals is not None:
        offset=len(binary);binary+=b''.join(struct.pack('<3f',*row) for row in normals)
        doc['buffers'][0]['byteLength']=len(binary)
        doc['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=len(normals)*12))
        doc['accessors'].append(dict(bufferView=2,componentType=5126,count=len(normals),type='VEC3'))
        doc['meshes'][0]['primitives'][0]['attributes']['NORMAL']=2
    if uvs is not None:
        offset=len(binary);binary+=b''.join(struct.pack('<2f',*row) for row in uvs)
        view=len(doc['bufferViews']);accessor=len(doc['accessors'])
        doc['buffers'][0]['byteLength']=len(binary)
        doc['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=len(uvs)*8))
        doc['accessors'].append(dict(bufferView=view,componentType=5126,count=len(uvs),type='VEC2'))
        doc['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']=accessor
    if colors is not None:
        offset=len(binary);width=len(colors[0]);fmt={5126:'f',5121:'B',5123:'H'}[color_component]
        binary+=b''.join(struct.pack('<'+str(width)+fmt,*row) for row in colors)
        view=len(doc['bufferViews']);accessor=len(doc['accessors'])
        doc['buffers'][0]['byteLength']=len(binary)
        doc['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=len(binary)-offset))
        doc['accessors'].append(dict(bufferView=view,componentType=color_component,count=len(colors),type='VEC'+str(width),normalized=color_component!=5126))
        doc['meshes'][0]['primitives'][0]['attributes']['COLOR_0']=accessor
    if changes:changes(doc)
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*(-len(encoded)%4)
    binary+=b'\0'*(-len(binary)%4)
    return struct.pack('<3I',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<2I',len(encoded),0x4e4f534a)+encoded+struct.pack('<2I',len(binary),0x004e4942)+binary


class MeshAppendTests(unittest.TestCase):
    def fixture(self):
        helper=build_fixtures.ModelGrowthNormalBuildTests();self.addCleanup(helper.doCleanups)
        p,_,asset,*_=helper.fixture()
        self.enterContext(patch('sdk.model_mesh_append.source_key',return_value='a'*64))
        donor=model_face_addition.source(p,asset,'a'*64)['topology']['faces'][0]['face_id']
        return p,asset,donor

    def test_standard_geometry_axes_shared_vertices_and_input_rejection(self):
        report=decode_append_mesh(glb())
        self.assertEqual(report['vertices'],[[0,0,0],[0,-100,0],[100,0,0],[100,-100,0]])
        self.assertEqual(report['triangles'],[[0,1,2],[2,1,3]])
        self.assertEqual(report['ignored_attributes'],[]);self.assertEqual(report['vertex_max_error'],0)
        nonindexed=decode_append_mesh(glb(lambda d:d['meshes'][0]['primitives'][0].pop('indices'),positions=[[0,0,0],[100,0,0],[0,100,0]]))
        self.assertEqual(nonindexed['triangles'],[[0,1,2]]);self.assertEqual(len(nonindexed['vertices']),3)
        report=decode_append_mesh(glb(normals=[[0,1,0]]*4))
        self.assertEqual(report['ignored_attributes'],[])
        self.assertEqual(report['triangle_normals'],[[[0,-4096,0]]*3]*2)
        with self.assertRaises(ImportError):decode_append_mesh(glb(normals=[[0,0,0]]*4))
        for mutation in (lambda d:d['nodes'][0].update(translation=[1,0,0]),lambda d:d['scenes'][0].update(nodes=[False]),
            lambda d:d['nodes'][0].update(children=[]),lambda d:d.update(animations=[{}]),
            lambda d:d['meshes'][0]['primitives'][0].update(mode=5),lambda d:d['meshes'][0]['primitives'][0]['attributes'].update(JOINTS_0=0),
            lambda d:d['bufferViews'][0].update(buffer=False),lambda d:d['accessors'][1].update(count=5),
            lambda d:d['accessors'][0].update(count=2)):
            with self.assertRaises(ImportError):decode_append_mesh(glb(mutation))
        for positions in ([[0,0,0],[.2,0,0],[0,.2,0],[1,1,0]],[[40000,0,0],[100,0,0],[0,100,0],[100,100,0]]):
            with self.assertRaises(ImportError):decode_append_mesh(glb(positions=positions))

    def test_one_command_undo_save_reopen_and_normal_build(self):
        p,asset,donor=self.fixture();content=glb();before=p.read_model_replacement(asset,p.model_overrides[asset])
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        report=model_mesh_append.review(p,asset,content,donor,sha256(before).hexdigest(),'a'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        with self.assertRaises(ProjectError):p.apply_model_mesh_append(asset,content,donor,sha256(before).hexdigest(),'a'*64,'0'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        p.apply_model_mesh_append(asset,content,donor,sha256(before).hexdigest(),'a'*64,report['review_key'])
        final=p.read_model_replacement(asset,p.model_overrides[asset]);self.assertNotEqual(final,before)
        self.assertEqual(len(p.undo_stack),len(state[1])+1)
        self.assertEqual([op['kind'] for op in p.model_overrides[asset]['ledger']['operations']],['allocate_vectors','add_faces'])
        inspection=p.model_primitive_source(asset);self.assertEqual(inspection['vector_growth'][0]['vertices'],4)
        new=inspection['objects'][0]['primitives'][-2:]
        for row,old in zip(new,[inspection['objects'][0]['primitives'][0]]*2):
            for field in ('uvs','colors','normal_indices','material'):self.assertEqual(row[field],old[field])
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),final)
        p.save();saved=deepcopy(p.model_overrides[asset])
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,saved),final)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            replacement=decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement']
        archive=_archive(replacement);carrier=archive.read_entry(archive.entry(1))
        d=parse_scene_assets(carrier,1).descriptors[1];pack,_=decompress_lzs(carrier[d.data_offset:],d.size)
        start,_=_pack_ranges(pack)[0];self.assertEqual(pack[start:start+len(final)],final)

    def test_actual_reviews_qualify_browser_geometry_and_ownership(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        p,asset,donor=self.fixture();content=glb();reports=[]
        for iteration in range(2):
            source=model_face_addition.source(p,asset,'a'*64)
            report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
            reports.append(dict(source=source,report=report,donor=donor))
            p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key'])
            donor=report['additions'][0]['face_id']
        script="""import {decodeMeshAppendReview} from './integrations/legaia/editor/model-mesh-append.js';
import assert from 'node:assert/strict';
let input='';for await(const chunk of process.stdin)input+=chunk;
for(const {source,report,donor} of JSON.parse(input)){
 const hash=report.geometry.glb_sha256;
 decodeMeshAppendReview(report,source,donor,hash);
 for(const mutate of [r=>r.geometry.glb_sha256='0'.repeat(64),r=>r.review_key='bad',r=>r.geometry.vertices[0][0]++,r=>r.preview.vertices[0][0]++,r=>r.preview.triangles.at(-1)[0]++,r=>r.preview.triangle_uvs.at(-1)[0][0]++,r=>r.additions[0].donor_face_id='missing',r=>r.topology.faces[0].current_primitive_index++,r=>r.topology.allocated_vector_count++]){
  const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshAppendReview(bad,source,donor,hash));
 }
}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(reports),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_HTTP_changed_file_donor_and_stale_source_reject_without_history(self):
        p,asset,donor=self.fixture();current=p.read_model_replacement(asset,p.model_overrides[asset])
        body=dict(asset_id=asset,donor_face_id=donor,expected_sha256=sha256(current).hexdigest(),source_key='a'*64,content_base64=base64.b64encode(glb()).decode())
        with http_server(p) as (server,post),patch.object(server,'state',return_value={'applied':True}):
            with urlopen(f'http://127.0.0.1:{server.server_address[1]}/model-mesh-append.js',timeout=5) as response:
                self.assertEqual(response.status,200);self.assertIn(b'openModelMeshAppend',response.read())
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            status,report=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            for changes in (dict(source_key='0'*64),dict(expected_sha256='0'*64),dict(donor_face_id='absent'),dict(extra=True),dict(content_base64='!')):
                self.assertEqual(post('/api/model-mesh-append-preview',{**body,**changes})[0],400)
                self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            altered=base64.b64encode(glb(lambda d:d.update(extras={'name':'changed'}))).decode()
            self.assertEqual(post('/api/model-mesh-append',{**body,'content_base64':altered,'review_key':report['review_key']})[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':report['review_key']})[0],200)
            state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':report['review_key']})[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)


if __name__=='__main__':unittest.main()
