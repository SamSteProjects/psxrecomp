import base64,json,math,os,tempfile,unittest,struct
from pathlib import Path
from copy import deepcopy
from importer.monster_archive import block
from importer.pipeline import _disc_context
from importer.texture_png import decode_png
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.monster_archive import resources,preview
from test_model_primitive_workflow import http_server
from test_importer_export import parse_glb
from test_animation_clip_export import values

def assert_source_positions(test,doc,binary,geometry,data,clip,mode,frame_index):
 checked=0
 for node in doc['nodes']:
  if 'mesh' not in node:continue
  obj=node['extras']['source_object'];start=obj['triangle_start'];end=start+obj['triangle_count'];part=obj['object_index'];translation=[0,0,0];matrix=[[1,0,0],[0,1,0],[0,0,1]]
  if mode=='stored-pose':
   at=clip['source_record']['byte_offset']+2+(frame_index*clip['part_count']+part)*9;packed=int.from_bytes(data[at:at+9],'little');v=[((packed>>low)&255)+((packed>>high)&15)*256 for low,high in ((0,16),(8,20),(24,40),(32,44),(48,64),(56,68))];translation=[n-4096 if n>=2048 else n for n in v[:3]];rx,ry,rz=[n*math.pi/2048 for n in v[3:]];sx,cx,sy,cy,sz,cz=math.sin(rx),math.cos(rx),math.sin(ry),math.cos(ry),math.sin(rz),math.cos(rz);matrix=[[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],[sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],[-sy,cy*sx,cy*cx]]
  for primitive in doc['meshes'][node['mesh']]['primitives']:
   expected=[]
   for triangle in range(start,end):
    if geometry['triangle_materials'][triangle]!=primitive['material']:continue
    for corner in (0,2,1):
     source=geometry['vertices'][geometry['triangles'][triangle][corner]];point=[sum(matrix[a][k]*source[k] for k in range(3))+translation[a] for a in range(3)];expected.append((point[0],-point[1],point[2]))
   actual=values(doc,binary,primitive['attributes']['POSITION']);test.assertEqual(len(actual),len(expected))
   for point,wanted in zip(actual,expected):
    for axis,value in enumerate(point):test.assertAlmostEqual(value,wanted[axis],delta=0.001)
   checked+=len(expected)
 return checked

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterExportTests(unittest.TestCase):
 def test_source_images_all_clip_tracks_and_read_only_modes(self):
  disc=os.environ['LEGAIA_DISC_BIN']
  with _disc_context(disc) as (_,_,_,archive):archive_bytes=archive.read_entry(archive.entry(867))
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=disc;p.save();ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));report=resources(p,**ctx);before=deepcopy((p._document(),p.undo_stack));receipts=[];samples=0;pixels=0
   with http_server(p) as (_,post):
    for identifier,rate in ((10,23.5),(62,30),(63,12)):
     clip=next(c for c in report['catalog']['animations'] if c['monster_id']==identifier and c['entry_index']==0);base=preview(p,**ctx,asset_id=clip['model_asset_id'],catalog_source_key=report['catalog']['source_key']);data,_=block(archive_bytes,identifier)
     for mode in ('object-local','stored-pose','full-clip'):
      body=dict(ctx,asset_id=clip['model_asset_id'],catalog_source_key=report['catalog']['source_key'],mode=mode,animation_id=None if mode=='object-local' else clip['semantic_id'],frame_index=clip['frame_count']-1 if mode=='stored-pose' else None,fps=rate if mode=='full-clip' else None)
      status,v=post('/api/monster-export',body);self.assertEqual(status,200,v);doc,binary=parse_glb(base64.b64decode(v['glb_base64']));self.assertNotIn('skins',doc);assert_source_positions(self,doc,binary,base['geometry'],data,clip,mode,body['frame_index'])
      for material in doc['materials']:
       image=material['pbrMetallicRoughness'].get('baseColorTexture')
       if image is None:continue
       index=int(material['name'].split('-')[-1]);crop=base['geometry']['textures'][index];view=doc['bufferViews'][doc['images'][image['index']]['bufferView']];png=decode_png(binary[view['byteOffset']:view['byteOffset']+view['byteLength']]);self.assertEqual(png['rgba'],base64.b64decode(crop['rgba_base64']));pixels+=png['width']*png['height'];self.assertEqual(material['extras']['source_pool_association']['pool_sha256'],base['texture_record']['source_record']['sha256'])
      if mode=='full-clip':
       animation=doc['animations'][0];self.assertEqual(len(animation['channels']),clip['part_count']*2)
       for part in range(clip['part_count']):
        tracks={c['target']['path']:animation['samplers'][c['sampler']] for c in animation['channels'] if c['target']['node']==part};ts=values(doc,binary,tracks['translation']['output']);qs=values(doc,binary,tracks['rotation']['output']);times=values(doc,binary,tracks['translation']['input']);self.assertEqual(ts[-1],ts[-2]);self.assertEqual(qs[-1],qs[-2]);self.assertEqual(tracks['rotation']['interpolation'],'STEP')
        for frame in range(clip['frame_count']):
         at=clip['source_record']['byte_offset']+2+(frame*clip['part_count']+part)*9;packed=int.from_bytes(data[at:at+9],'little');v0=[((packed>>low)&255)+((packed>>high)&15)*256 for low,high in ((0,16),(8,20),(24,40),(32,44),(48,64),(56,68))];translation=[n-4096 if n>=2048 else n for n in v0[:3]];self.assertEqual(ts[frame],(translation[0],-translation[1],translation[2]));self.assertAlmostEqual(times[frame][0],frame/rate,places=6)
         rx,ry,rz=[n*math.pi/2048 for n in v0[3:]]
         for source in ((1,0,0),(0,1,0),(0,0,1)):
          x,y,z=source;y,z=y*math.cos(rx)-z*math.sin(rx),y*math.sin(rx)+z*math.cos(rx);x,z=x*math.cos(ry)+z*math.sin(ry),-x*math.sin(ry)+z*math.cos(ry);x,y=x*math.cos(rz)-y*math.sin(rz),x*math.sin(rz)+y*math.cos(rz);qx,qy,qz,qw=qs[frame];vx,vy,vz=source[0],-source[1],source[2];cx,cy,cz=2*(qy*vz-qz*vy),2*(qz*vx-qx*vz),2*(qx*vy-qy*vx);actual=[vx+qw*cx+qy*cz-qz*cy,vy+qw*cy+qz*cx-qx*cz,vz+qw*cz+qx*cy-qy*cx]
          for actual_axis,expected_axis in zip(actual,(x,-y,z)):self.assertAlmostEqual(actual_axis,expected_axis,places=6)
         samples+=1
        self.assertAlmostEqual(times[-1][0],clip['frame_count']/rate,places=6)
      else:self.assertNotIn('animations',doc)
      receipts.append(dict(choice={k:body[k] for k in ('mode','animation_id','frame_index','fps')},value=v))
    for change in (dict(fps=True),dict(fps=0),dict(fps=121),dict(frame_index=0),dict(expected_source_key='0'*64),dict(extra=True)):
     self.assertEqual(post('/api/monster-export',dict(body,**change))[0],400)
   self.assertEqual((p._document(),p.undo_stack),before)
   if os.getenv('LEGAIA_MONSTER_EXPORT_CASES'):Path(os.environ['LEGAIA_MONSTER_EXPORT_CASES']).write_text(json.dumps(dict(report=report,receipts=receipts,source_track_samples=samples,source_png_pixels=pixels,unchanged=True,gameplay_verified=False)),encoding='utf-8')
