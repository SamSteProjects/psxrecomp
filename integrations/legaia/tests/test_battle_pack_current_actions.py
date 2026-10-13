"""Authored pack geometry must drive Current reference poses and all exports."""
import base64,json,os,struct,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.battle_character_resources import resources,animations
from sdk import battle_pack_model_authoring as models
from sdk import battle_pack_current_actions as actions
from test_monster_model_authoring import shifted_glb
from test_model_primitive_workflow import http_server
from test_importer_export import parse_glb


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class CurrentPackActionsTests(unittest.TestCase):
 def test_three_authored_models_reference_frames_exports_and_atomic_guards(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
   source=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));catalog=resources(p,**source)['catalog'];an=animations(p,**source)
   def ctx(i):return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=catalog['models'][i]['semantic_id'],catalog_source_key=catalog['source_key'])
   for i in range(3):
    export=models.export(p,**ctx(i));args=dict(ctx(i),binding=export['binding'],glb_base64=base64.b64encode(shifted_glb(base64.b64decode(export['glb_base64']))).decode(),expected_current_entry_sha256=export['current_entry_sha256'])
    plan=models.review(p,**args);models.apply(p,review_key=plan['review_key'],**args)
   held=deepcopy((p._document(),p.undo_stack,p.redo_stack));cases=[]
   with http_server(p) as (_,post):
    for i in range(3):
     current=models.current(p,**ctx(i));clip=an['catalog']['clips'][i*9];selection=dict(ctx(i),expected_current_tmd_sha256=current['current_tmd_sha256'],expected_current_entry_sha256=current['current_entry_sha256'],animation_id=clip['semantic_id'],animation_source_key=an['catalog']['source_key'])
     poses=[]
     for frame in (0,clip['frame_count']-1):
      status,value=post('/api/battle-pack-current-pose',dict(selection,frame_index=frame));self.assertEqual(status,200,value)
      self.assertEqual(value['inspection'],current);self.assertNotEqual(value['geometry']['vertices'],value['retail_playback']['geometry']['vertices'])
      for key in ('objects','triangles','triangle_colors','triangle_uvs','materials','textures'):self.assertEqual(value['geometry'][key],current['geometry'][key])
      for obj,transform in zip(current['geometry']['objects'],value['object_transforms']):
       # Independent homogeneous rotations, not the SDK pose helper.
       import math
       rx,ry,rz=[n*math.pi/2048 for n in transform['rotation_psx']]
       sx,cx,sy,cy,sz,cz=math.sin(rx),math.cos(rx),math.sin(ry),math.cos(ry),math.sin(rz),math.cos(rz)
       matrix=((cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx),(sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx),(-sy,cy*sx,cy*cx))
       for j in range(obj['vertex_start'],obj['vertex_start']+obj['vertex_count']):
        v=current['geometry']['vertices'][j]
        for axis in range(3):self.assertAlmostEqual(value['geometry']['vertices'][j][axis],sum(matrix[axis][a]*v[a] for a in range(3))+transform['translation'][axis],delta=1e-7)
      poses.append(value)
     exports=[]
     for mode in ('object-local','pose','clip'):
      args=dict(selection,mode=mode,frame_index=clip['frame_count']-1 if mode=='pose' else None,fps=23.5 if mode=='clip' else None)
      if mode=='object-local':args.update(animation_id=None,animation_source_key=None)
      status,value=post('/api/battle-pack-current-export',args);self.assertEqual(status,200,value)
      doc,binary=parse_glb(base64.b64decode(value['glb_base64']));g=poses[-1]['geometry'] if mode=='pose' else current['geometry']
      self.assertEqual(len(doc.get('animations',[])),1 if mode=='clip' else 0)
      for node in doc['nodes']:
       if 'mesh' not in node:continue
       obj=node['extras']['source_object']
       for primitive in doc['meshes'][node['mesh']]['primitives']:
        a=doc['accessors'][primitive['attributes']['POSITION']];view=doc['bufferViews'][a['bufferView']];at=view.get('byteOffset',0)+a.get('byteOffset',0)
        actual=list(struct.iter_unpack('<3f',binary[at:at+a['count']*12]));expected=[]
        for t in range(obj['triangle_start'],obj['triangle_start']+obj['triangle_count']):
         if g['triangle_materials'][t]!=primitive['material']:continue
         for corner in (0,2,1):x,y,z=g['vertices'][g['triangles'][t][corner]];expected.append((x,-y,z))
        self.assertEqual(len(actual),len(expected))
        for v,target in zip(actual,expected):
         for a,b in zip(v,target):self.assertAlmostEqual(a,b,delta=0.0003)
      exports.append(value)
     for changed in ({'frame_index':True},{'frame_index':999},{'extra':True},{'expected_current_tmd_sha256':'0'*64},{'expected_current_entry_sha256':'0'*64},{'animation_source_key':'0'*64},{'animation_id':an['catalog']['clips'][27]['semantic_id']}):
      self.assertEqual(post('/api/battle-pack-current-pose',dict(selection,frame_index=0,**changed) if 'frame_index' not in changed else dict(selection,**changed))[0],400)
     cases.append(dict(inspection=current,record=dict(id=ctx(i)['asset_id'],type='model',data=catalog['models'][i]),poses=poses,exports=exports))
   self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
   if os.getenv('LEGAIA_CURRENT_PACK_CASES'):
    Path(os.environ['LEGAIA_CURRENT_PACK_CASES']).write_text(json.dumps(dict(report=dict(project_path=str(p.root),project_source_key=source_key(p),catalog=catalog),animations=dict(an,project_source_key=source_key(p)),cases=cases)),encoding='utf-8')


if __name__=='__main__':unittest.main()
