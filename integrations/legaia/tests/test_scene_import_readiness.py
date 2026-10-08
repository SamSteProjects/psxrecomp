"""Catalog readiness agrees with actual Import without inventing resolved assets."""
from pathlib import Path
from unittest.mock import patch
import os,unittest
from importer import pipeline
from importer.core import ImportError

class SceneImportReadiness(unittest.TestCase):
    def test_invalid_probe_refuses_before_disc_access(self):
        for kwargs in [dict(offset=True),dict(offset=65537),dict(limit=True),dict(prefix=None)]:
            with self.assertRaises(ImportError):pipeline.list_scenes('missing.bin',**kwargs)

    @unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
    def test_real_import_resolution_and_partial_page(self):
        disc=os.environ['LEGAIA_DISC_BIN'];report=pipeline.list_scenes(disc,prefix='taiku',limit=16)
        self.assertEqual(report['schema_version'],'legaia.scene-catalog.v2')
        self.assertEqual([s['name'] for s in report['scenes']],['taiku','taiku2'])
        for row in report['scenes']:
            metadata=pipeline.import_scene(disc,row['name'])
            models=metadata['assets']['models']
            self.assertEqual(row['scene_model_count'],sum(m['model_pool']=='scene_tmd' for m in models))
            self.assertEqual(row['global_model_count'],5)
            self.assertEqual(row['unresolved_actor_model_count'],sum(a['model_reference']['resolution_status']!='resolved' for a in metadata['actors']))
        self.assertEqual(report['scenes'][0]['unresolved_actor_model_count'],0)
        self.assertEqual(report['scenes'][1]['unresolved_actor_model_count'],6)
        first=pipeline.list_scenes(disc,prefix='taiku',limit=1)
        last=pipeline.list_scenes(disc,prefix='taiku',offset=first['next_offset'],limit=1)
        self.assertEqual(first['scenes']+last['scenes'],report['scenes']);self.assertIsNone(last['next_offset'])
        original=pipeline._scene_metadata
        def refuse(digest,archive,start,end,scene,source):
            if scene=='taiku2':raise ImportError('fixture native model slot refuses')
            return original(digest,archive,start,end,scene,source)
        with patch.object(pipeline,'_scene_metadata',side_effect=refuse):
            partial=pipeline.list_scenes(disc,prefix='taiku',limit=16)
        row=partial['scenes'][1]
        self.assertEqual(row['placement_status'],'supported');self.assertEqual(row['import_status'],'unsupported')
        self.assertEqual(row['import_reason'],'fixture native model slot refuses');self.assertIsNone(row['scene_model_count'])
        self.assertEqual(partial['scenes'][0],report['scenes'][0])
        self.assertEqual(pipeline.list_scenes(disc,prefix='taiku',offset=100,limit=16)['scanned_blocks'],0)

if __name__=='__main__':unittest.main()
