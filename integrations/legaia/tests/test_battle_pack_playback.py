import base64
from copy import deepcopy
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import tempfile
import unittest

from importer.assets import decode_tmd
from importer.battle_pack_animation import decode_catalogue
from importer.battle_character_catalog import decode_catalog
from importer.pipeline import _disc_context
from sdk.battle_pack_playback import playback
from sdk.battle_character_resources import resources, animations, preview
from sdk.project import ProjectService, ProjectError
from sdk.project_assets import source_key
from test_model_primitive_workflow import http_server


def literal_transforms(stream, frame, parts):
    rows=[]
    for part in range(parts):
        d=stream[8+(frame*parts+part)*8:16+(frame*parts+part)*8]
        xyz=[d[0]|((d[2]&15)<<8),d[1]|((d[2]&240)<<4),d[3]|((d[4]&15)<<8)]
        rows.append(dict(object_index=part,translation=[n-4096 if n&2048 else n for n in xyz],
                         rotation_psx=[n<<4 for n in d[5:8]],opaque_nibble=d[4]>>4))
    return rows


def matrix_pose(raw, transforms):
    vertices=[None]*len(raw['vertices'])
    for obj,t in zip(raw['objects'],transforms):
        rx,ry,rz=[v*math.tau/4096 for v in t['rotation_psx']]
        sx,cx,sy,cy,sz,cz=math.sin(rx),math.cos(rx),math.sin(ry),math.cos(ry),math.sin(rz),math.cos(rz)
        matrix=[[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],
                [sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],[-sy,cy*sx,cy*cx]]
        for at in range(obj['vertex_start'],obj['vertex_start']+obj['vertex_count']):
            vertices[at]=[sum(matrix[axis][i]*raw['vertices'][at][i] for i in range(3))+t['translation'][axis] for axis in range(3)]
    return vertices


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class BattlePackPlaybackTests(unittest.TestCase):
    def test_all_27_complete_streams_literal_first_last_poses_and_read_only_state(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
            context=dict(expected_project_path=str(p.root),expected_source_key=source_key(p))
            report=resources(p,**context);animation_report=animations(p,**context)
            # Load the complete native entries once for independent corpus checks.
            with _disc_context(p.disc_path) as (_,disc,_,archive):
                model_entry=archive.read_entry(archive.entry(1204));models=decode_catalog(model_entry,disc)
                catalog,bank=decode_catalogue(archive.read_entry(archive.entry(1203)),disc)
            cases=[];held=deepcopy((p._document(),p.undo_stack,p.redo_stack));total=0
            raw_models={}
            for model in models['models'][:3]:
                raw_models[model['semantic_id']]=preview(p,**context,asset_id=model['semantic_id'],catalog_source_key=models['source_key'],palette_index=0)['preview']
            for clip in catalog['clips'][:27]:
                model=next(m for m in models['models'] if m['semantic_id']==clip['model_asset_id'])
                args=dict(context,model_id=model['semantic_id'],model_source_key=models['source_key'],animation_id=clip['semantic_id'],animation_source_key=catalog['source_key'])
                value=playback(p,**args);source=clip['source_record'];stream=bank[source['byte_offset']:source['byte_offset']+source['byte_length']]
                self.assertEqual(base64.b64decode(value['source_motion_base64']),stream)
                self.assertEqual(base64.b64decode(value['source_bank_base64']),bank)
                at=model['source_record']['byte_offset'];tmd=model_entry[at:at+model['source_record']['byte_length']]
                self.assertEqual(base64.b64decode(value['source_model_base64']),tmd)
                self.assertEqual(sha256(stream).hexdigest(),source['sha256'])
                raw=raw_models[model['semantic_id']];literal=decode_tmd(tmd);self.assertEqual(literal['vertices'],raw['vertices'])
                poses=[]
                for frame in (0,clip['frame_count']-1):
                    transforms=literal_transforms(stream,frame,clip['bone_count']);vertices=matrix_pose(literal,transforms)
                    if frame==0:
                        self.assertEqual(value['object_transforms'],transforms)
                        for row,expected in zip(value['geometry']['vertices'],vertices):
                            for a,b in zip(row,expected):self.assertAlmostEqual(a,b,delta=1e-7)
                    poses.append(dict(frame_index=frame,object_transforms=transforms,vertices=vertices));total+=len(vertices)
                cases.append(dict(record=dict(id=model['semantic_id'],type='model',data=model),raw=raw,value=value,first=poses[0],last=poses[1]))
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            output=os.getenv('LEGAIA_BATTLE_PACK_PLAYBACK_CASES')
            if output:Path(output).write_text(json.dumps(dict(report=report,animations=animation_report,cases=cases,complete_source_streams=27,first_last_poses=54,vertices=total,independent_matrix_oracle=True,document_history_unchanged=True,gameplay_verified=False)),encoding='utf-8')

    def test_matching_sources_unmatched_rigs_and_exact_http_fields(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();context=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));m=resources(p,**context);a=animations(p,**context)
            args=dict(context,model_id=m['catalog']['models'][0]['semantic_id'],model_source_key=m['catalog']['source_key'],animation_id=a['catalog']['clips'][0]['semantic_id'],animation_source_key=a['catalog']['source_key']);held=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with http_server(p) as (_,post):
                status,value=post('/api/battle-pack-playback',args);self.assertEqual(status,200,value)
                for change in (dict(model_id=True),dict(animation_id=True),dict(model_source_key=False),dict(animation_source_key='0'*64),dict(expected_source_key='0'*64),dict(model_id=m['catalog']['models'][1]['semantic_id']),dict(animation_id=a['catalog']['clips'][27]['semantic_id']),dict(frame_index=0),dict(fps=12)):
                    self.assertEqual(post('/api/battle-pack-playback',dict(args,**change))[0],400,change)
            for clip in a['catalog']['clips'][27:]:
                with self.assertRaises(ProjectError):playback(p,**dict(args,animation_id=clip['semantic_id']))
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
