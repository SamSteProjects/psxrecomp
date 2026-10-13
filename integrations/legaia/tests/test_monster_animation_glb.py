import base64,json,os,struct,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_archive import resources
from sdk.monster_export import export
from sdk.monster_motion_authoring import inspect
from sdk.monster_motion_glb import review
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterAnimationGlbTests(unittest.TestCase):
 def test_export_roundtrip_and_literal_existing_frame_track_edit(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();fresh=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));catalog=resources(p,**fresh)['catalog'];held=deepcopy((p._document(),p.undo_stack));cases=[]
   for identifier in (10,62,63):
    model=f'asset://legaia/models/monster-archive/{identifier:04d}';clip=next(c for c in catalog['animations'] if c['model_asset_id']==model and c['preview_supported']);context=dict(fresh,asset_id=model,catalog_source_key=catalog['source_key']);inspection=inspect(p,**context,animation_id=clip['semantic_id'],frame_index=0,part_index=0);e=export(p,**context,mode='full-clip',animation_id=clip['semantic_id'],frame_index=None,fps=24,texture_layer='current');content=base64.b64decode(e['glb_base64']);args=dict(context,animation_id=clip['semantic_id'],expected_current_block_sha256=inspection['current_block_sha256'],glb_base64=e['glb_base64'],fps=24,animation_index=None,object_node_indices=None);roundtrip=review(p,**args);self.assertEqual(roundtrip['source_motion_base64'],roundtrip['candidate_motion_base64'])
    doc,raw=_read_glb(content);raw=bytearray(raw);animation=doc['animations'][0];channel=next(c for c in animation['channels'] if c['target']==dict(node=0,path='translation'));a=doc['accessors'][animation['samplers'][channel['sampler']]['output']];v=doc['bufferViews'][a['bufferView']];start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
    for index in range(a['count']):at=start+index*stride;struct.pack_into('<f',raw,at,struct.unpack_from('<f',raw,at)[0]+1)
    for key in ('min','max'):
     if key in a:a[key][0]+=1
    edited=_write_glb(doc,raw);plan=review(p,**dict(args,glb_base64=base64.b64encode(edited).decode()));source=base64.b64decode(plan['source_motion_base64']);expected=bytearray(source)
    for index in range(clip['frame_count']):
     at=2+index*clip['part_count']*9;x=source[at]|(source[at+2]&15)<<8;x=x-4096 if x&2048 else x;value=(x+1)&4095;expected[at]=value&255;expected[at+2]=(source[at+2]&240)|(value>>8)
    self.assertEqual(base64.b64decode(plan['candidate_motion_base64']),bytes(expected));self.assertEqual(len(plan['analysis']['edits']),clip['frame_count'])
    with self.assertRaises(ProjectError):review(p,**dict(args,fps=0))
    with self.assertRaises(ProjectError):review(p,**dict(args,expected_current_block_sha256='0'*64))
    cases.append(dict(inspection=inspection,review=plan,input_glb_base64=base64.b64encode(edited).decode()))
   self.assertEqual((p._document(),p.undo_stack),held)
   if os.getenv('LEGAIA_MONSTER_GLB_CASES'):Path(os.environ['LEGAIA_MONSTER_GLB_CASES']).write_text(json.dumps(dict(cases=cases,exact_roundtrips=True,literal_native_track_changes=True,history_unchanged=True,gameplay_verified=False)),encoding='utf-8')
