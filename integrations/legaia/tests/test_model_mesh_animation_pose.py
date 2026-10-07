"""Explicit animation snapshots feed the existing native mesh geometry path."""
from copy import deepcopy
import struct,unittest
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from importer.core import ImportError
import test_model_mesh_append as mesh
import test_model_mesh_skin as skin
import test_model_mesh_morph as morph
import test_model_mesh_append_normals as normal_fixtures
from sdk import model_mesh_append,model_face_addition
from sdk.model_mesh_sources import read_source
from sdk.model_mesh_sources import validate as validate_retained
from sdk.project import ProjectError,digest

def animated(content,tracks,change=None):
    doc,binary=_read_glb(content);binary=bytearray(binary)
    def add(rows,shape):
        binary.extend(b'\0'*(-len(binary)%4));at=len(binary);width=len(rows[0]);binary.extend(b''.join(struct.pack('<'+str(width)+'f',*r) for r in rows));view=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=at,byteLength=len(binary)-at));index=len(doc['accessors']);doc['accessors'].append(dict(bufferView=view,componentType=5126,count=len(rows),type=shape));return index
    samplers=[];channels=[]
    for node,path,mode,values in tracks:
        times=add([[0],[1]],'SCALAR');output=add(values,'SCALAR' if path=='weights' else 'VEC4' if path=='rotation' else 'VEC3');channels.append(dict(sampler=len(samplers),target=dict(node=node,path=path)));samplers.append(dict(input=times,output=output,interpolation=mode))
    doc['animations']=[dict(channels=channels,samplers=samplers)];doc['buffers'][0]['byteLength']=len(binary)
    if change:change(doc,binary)
    return _write_glb(doc,binary)

def pose(time=.5,index=0):return dict(animation_index=index,time_seconds=time)

class MeshAnimationPose(unittest.TestCase):
    def test_native_review_apply_original_retention_and_history(self):
        helper=normal_fixtures.MeshAppendNormalTests();self.addCleanup(helper.doCleanups);p,asset,donor=helper.fixture(0x14);source=model_face_addition.source(p,asset,'a'*64);original,_,base,*_=model_face_addition._context(p,asset,'a'*64)
        content=animated(mesh.glb(normals=[[0,1,0]]*4),[(0,'translation','LINEAR',[[0,0,0],[10,20,30]])]);before=deepcopy(p._document());depth=len(p.undo_stack)
        actual,_,report=model_mesh_append.prepare(p,asset,content,donor,source['effective_sha256'],'a'*64,animation_pose=pose())
        literal=mesh.glb(positions=[[5,10,15],[105,10,15],[5,110,15],[105,110,15]],normals=[[0,1,0]]*4)
        expected,_,oracle=model_mesh_append.prepare(p,asset,literal,donor,source['effective_sha256'],'a'*64)
        self.assertEqual(actual,expected);self.assertEqual(report['normal_import'],oracle['normal_import']);self.assertEqual(p._document(),before)
        with self.assertRaises(ProjectError):p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key'],animation_pose=pose(.25))
        self.assertEqual(p._document(),before)
        p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key'],animation_pose=pose())
        record=p.model_overrides[asset]['mesh_imports'][-1];self.assertEqual(read_source(p,record),content);self.assertEqual(record['recipe']['animation_pose'],pose());self.assertEqual(len(p.undo_stack),depth+1)
        binding=p.model_overrides[asset];held=deepcopy(p._document());validate_retained(p,asset,binding,base,original,digest(p.imports[binding['source_scene_id']]));self.assertEqual(p._document(),held)
        p.undo();self.assertEqual(p._document(),before);p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),actual)
    def test_linear_trs_literal_geometry_and_immutable_source(self):
        content=animated(mesh.glb(),[(0,'translation','LINEAR',[[0,0,0],[10,20,30]]),(0,'rotation','LINEAR',[[0,0,0,1],[0,0,1,0]]),(0,'scale','LINEAR',[[1,1,1],[3,3,3]])]);held=bytes(content)
        with self.assertRaisesRegex(ImportError,'animated'):decode_append_mesh(content)
        r=decode_append_mesh(content,animation_pose=pose());self.assertEqual(content,held)
        self.assertEqual(r['vertices'],[[5,-10,15],[-195,-10,15],[5,-210,15],[-195,-210,15]])
        self.assertEqual(r['static_scope']['sampled_animation']['time_seconds'],.5)
        self.assertEqual(len(r['static_scope']['sampled_animation']['sampled_channels']),3)
        self.assertEqual(inspect_append_mesh(content,animation_pose=pose())['static_scope'],r['static_scope'])
    def test_skin_joint_animation_matches_independent_declared_pose(self):
        content=animated(skin.skin_glb(normals=[[1,1,0]]*4),[(1,'translation','LINEAR',[[20,0,0],[40,0,0]])]);r=decode_append_mesh(content,animation_pose=pose())
        static=decode_append_mesh(skin.skin_glb(lambda d,b:d['nodes'][1].update(translation=[30,0,0]),normals=[[1,1,0]]*4))
        for key in ['vertices','triangles','triangle_normals','triangle_colors','triangle_uvs']:self.assertEqual(r[key],static[key])
        self.assertEqual(r['vertices'],[[13,-5,0],[16,-160,0],[219,-15,0],[222,-220,0]])
    def test_morph_animation_bakes_before_skin(self):
        source=morph.morph_glb(skin=True);doc,_=_read_glb(source);count=len(doc['meshes'][0]['primitives'][0]['targets']);values=[[0]]*count+[[1]]*count
        content=animated(source,[(0,'weights','LINEAR',values)]);r=decode_append_mesh(content,animation_pose=pose())
        static=decode_append_mesh(morph.morph_glb(lambda d,b,a:d['nodes'][0].update(weights=[.5]*count),skin=True))
        for key in ['vertices','triangles','triangle_normals']:self.assertEqual(r[key],static[key])
    def test_step_cubic_and_endpoint_clamping(self):
        base=decode_append_mesh(mesh.glb())['vertices']
        for mode,values,delta in [('STEP',[[0,0,0],[10,0,0]],0),('CUBICSPLINE',[[0,0,0],[0,0,0],[0,0,0],[0,0,0],[10,0,0],[0,0,0]],5)]:
            content=animated(mesh.glb(),[(0,'translation',mode,values)])
            for time,offset in [(0,0),(.5,delta),(2,10)]:self.assertEqual(decode_append_mesh(content,animation_pose=pose(time))['vertices'],[[x+offset,y,z] for x,y,z in base])
    def test_scope_excludes_unselected_clip_payload_and_tracks(self):
        def exclude(d,b):
            d['nodes'].append({'mesh':0});d['scenes'].append({'nodes':[1]});d['animations'][0]['samplers'].append(dict(input=999,output=999));d['animations'][0]['channels'].append(dict(sampler=1,target=dict(node=1,path='translation')))
        content=animated(mesh.glb(),[(0,'translation','LINEAR',[[0,0,0],[10,0,0]])],exclude);r=decode_append_mesh(content,animation_pose=pose(),scene_index=0)
        self.assertEqual(r['static_scope']['sampled_animation']['excluded_channels'],[dict(node_index=1,path='translation')])
        self.assertEqual(r['static_scope']['selected_nodes'],[0])
    def test_malformed_pose_and_track_refusals(self):
        content=animated(mesh.glb(),[(0,'translation','LINEAR',[[0,0,0],[10,0,0]])])
        for p in [dict(animation_index=True,time_seconds=0),pose(float('nan')),pose(-1),pose(3601),pose(index=1),dict(animation_index=0,time_seconds=0,extra=True)]:
            with self.assertRaises(ImportError):decode_append_mesh(content,animation_pose=p)
        mutations=[lambda d,b:d['animations'][0]['channels'].append(deepcopy(d['animations'][0]['channels'][0])),lambda d,b:d['animations'][0]['samplers'][0].update(interpolation='BAD'),lambda d,b:d['nodes'][0].update(matrix=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]),lambda d,b:d['animations'][0]['channels'][0]['target'].update(path='weights'),lambda d,b:d['accessors'][-1].update(count=1)]
        for change in mutations:
            forged=animated(mesh.glb(),[(0,'translation','LINEAR',[[0,0,0],[10,0,0]])],change)
            with self.assertRaises(ImportError):decode_append_mesh(forged,animation_pose=pose())
