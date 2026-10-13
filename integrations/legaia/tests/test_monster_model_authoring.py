import base64,json,os,struct,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_archive import resources
from sdk.monster_model_authoring import export,review,snapshot
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.model_primitives import _qualified_model


def shifted_glb(content):
 doc,raw=_read_glb(content);raw=bytearray(raw);seen=set()
 for mesh in doc['meshes']:
  for primitive in mesh['primitives']:
   index=primitive['attributes']['POSITION']
   if index in seen:continue
   seen.add(index);a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];at=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
   for n in range(a['count']):
    pos=at+n*stride;struct.pack_into('<f',raw,pos,struct.unpack_from('<f',raw,pos)[0]+1)
   for key in ('min','max'):
    if key in a:a[key][0]+=1
 return _write_glb(doc,raw)


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterModelAuthoringTests(unittest.TestCase):
 def test_current_texture_composes_and_stales_previous_model_export(self):
  from sdk.monster_palettes import inspect,review as palette_review,apply as palette_apply
  from importer import monster_model_authoring as native
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();fresh=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));catalog=resources(p,**fresh)['catalog'];context=dict(fresh,asset_id='asset://legaia/models/monster-archive/0063',catalog_source_key=catalog['source_key']);old=export(p,**context)
   texture=dict(fresh,asset_id='texture://legaia/monster-archive/0063/pool',palette_index=0);observed=inspect(p,**texture);args=dict(texture,entry_index=1,word=observed['preview']['words'][1]^1,expected_current_sha256=observed['current_pool_sha256']);plan=palette_review(p,**args);palette_apply(p,review_key=plan['review_key'],**args)
   with self.assertRaises(ProjectError):review(p,**context,binding=old['binding'],glb_base64=old['glb_base64'])
   context['expected_source_key']=source_key(p);current=export(p,**context);self.assertIsNotNone(current['palette_binding']);self.assertNotEqual(current['source_pool_base64'],current['retail_pool_base64']);edited=shifted_glb(base64.b64decode(current['glb_base64']));held=deepcopy((p._document(),p.undo_stack));record,texture,original,body,_,_=snapshot(p,**context);candidate,_=native.convert(body,record,texture,current['binding'],edited)
   at=record['source_record']['byte_offset'];end=at+record['source_record']['byte_length'];self.assertEqual(candidate[:at],body[:at]);self.assertEqual(candidate[end:],body[end:]);self.assertNotEqual(candidate[end:],original[end:]);self.assertEqual((p._document(),p.undo_stack),held)
 def test_tagged_export_edit_projection_capacity_and_stale_refusal(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();fresh=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));catalog=resources(p,**fresh)['catalog'];held=deepcopy((p._document(),p.undo_stack));cases=[]
   for identifier in (10,62,63):
    context=dict(fresh,asset_id=f'asset://legaia/models/monster-archive/{identifier:04d}',catalog_source_key=catalog['source_key']);exported=export(p,**context);content=base64.b64decode(exported['glb_base64']);roundtrip=review(p,**context,binding=exported['binding'],glb_base64=exported['glb_base64']);self.assertEqual(roundtrip['projection']['changes'],[])
    edited=shifted_glb(content);plan=review(p,**context,binding=exported['binding'],glb_base64=base64.b64encode(edited).decode());original=base64.b64decode(plan['current_tmd_base64']);expected=bytearray(original);_,vectors=_qualified_model(original)
    for start,_,_,kind,count in vectors:
     if kind!='vertex':continue
     for n in range(count):
      at=start+n*8;struct.pack_into('<h',expected,at,struct.unpack_from('<h',expected,at)[0]+1)
    self.assertEqual(base64.b64decode(plan['candidate_tmd_base64']),bytes(expected));self.assertEqual(plan['projection']['candidate_tmd_sha256'],sha256(expected).hexdigest());self.assertEqual(plan['persistence'],'not_applied')
    altered=deepcopy(exported['binding']);altered['current_block_sha256']='0'*64
    with self.assertRaises(ProjectError):review(p,**context,binding=altered,glb_base64=base64.b64encode(edited).decode())
    cases.append(dict(export=exported,review=plan,input_glb_base64=base64.b64encode(edited).decode()))
   self.assertEqual((p._document(),p.undo_stack),held)
   if os.getenv('LEGAIA_MONSTER_MODEL_CASES'):Path(os.environ['LEGAIA_MONSTER_MODEL_CASES']).write_text(json.dumps(dict(cases=cases,document_unchanged=True,history_unchanged=True,gameplay_verified=False)),encoding='utf-8')
