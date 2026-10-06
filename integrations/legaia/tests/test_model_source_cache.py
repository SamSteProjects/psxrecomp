"""Fresh disc verification precedes every bounded immutable source-cache read."""
from contextlib import contextmanager
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import unittest
from sdk.model_sources import ModelSourceService
from sdk.project import ProjectError

class ModelSourceCacheTests(unittest.TestCase):
    def fixture(self):
        document=dict(scene=dict(name='fixture'),assets=dict(models=[dict(semantic_id=f'model://{i}',asset_kind='tmd_model') for i in range(3)]))
        project=SimpleNamespace(imports={'scene://fixture':document},disc_path='source.bin')
        service=ModelSourceService();checks=[]
        @contextmanager
        def verify(path):checks.append(path);yield (None,'a'*64,None,None)
        self.enterContext(patch('importer.pipeline._disc_context',side_effect=verify))
        scene=self.enterContext(patch('importer.pipeline.import_scene',side_effect=lambda *args:deepcopy(document)))
        model=self.enterContext(patch('importer.assets.load_model_source',side_effect=lambda path,asset:asset['semantic_id'].encode()))
        return project,service,checks,scene,model

    def test_cached_derivations_still_enter_verified_context_each_time(self):
        p,s,checks,scene,model=self.fixture();held=deepcopy(p.imports)
        first=s.read(p,'model://0','scene://fixture')
        self.assertIs(first,s.read(p,'model://0','scene://fixture'))
        self.assertEqual(s.read(p,'model://1','scene://fixture'),b'model://1')
        self.assertEqual(len(checks),3);self.assertEqual(scene.call_count,1);self.assertEqual(model.call_count,2)
        self.assertEqual(p.imports,held);self.assertEqual(s.statistics()['cache_hits'],1)
        p.imports['scene://fixture']['changed']=True
        self.assertEqual(s.read(p,'model://0','scene://fixture'),first);self.assertEqual(scene.call_count,2);self.assertEqual(model.call_count,3)
        with patch('importer.pipeline.import_scene',return_value={}):
            p.imports['scene://fixture']['changed']=False
            with self.assertRaisesRegex(ProjectError,'imported evidence'):s.read(p,'model://0','scene://fixture')
        self.assertEqual(s.statistics()['cached_bytes'],0)

    def test_disc_failure_or_exit_drift_cannot_publish_or_serve_cached_bytes(self):
        p,s,checks,scene,model=self.fixture();s.read(p,'model://0','scene://fixture')
        @contextmanager
        def rejected(path):raise ProjectError('changed disc hash');yield
        with patch('importer.pipeline._disc_context',side_effect=rejected):
            with self.assertRaisesRegex(ProjectError,'disc hash'):s.read(p,'model://0','scene://fixture')
        self.assertEqual(s.statistics()['cached_models'],0)
        @contextmanager
        def drift(path):yield (None,'a'*64,None,None);raise ProjectError('changed disc stamp')
        with patch('importer.pipeline._disc_context',side_effect=drift):
            with self.assertRaisesRegex(ProjectError,'disc stamp'):s.read(p,'model://0','scene://fixture')
        self.assertEqual(s.statistics()['qualified_scenes'],0);self.assertEqual(s.statistics()['cached_models'],0)
        s.read(p,'model://0','scene://fixture');self.assertEqual(model.call_count,3)

    def test_model_count_bytes_lru_and_context_drift(self):
        p,s,checks,scene,model=self.fixture();s.MAX_MODELS=1;s.MAX_BYTES=10
        s.read(p,'model://0','scene://fixture');s.read(p,'model://1','scene://fixture')
        self.assertEqual(s.statistics()['cached_bytes'],9);self.assertEqual(s.statistics()['cached_models'],1)
        s.read(p,'model://0','scene://fixture');self.assertEqual(model.call_count,3)
        s.MAX_BYTES=1;s.clear();s.read(p,'model://0','scene://fixture');self.assertEqual(s.statistics()['cached_models'],0)
        def drift(*args):p.disc_path='other.bin';return b'model'
        with patch('importer.assets.load_model_source',side_effect=drift):
            with self.assertRaisesRegex(ProjectError,'context changed'):s.read(p,'model://0','scene://fixture')
        self.assertEqual(s.statistics()['cached_models'],0)

    def test_project_staging_deepcopy_uses_fresh_independent_service(self):
        p,s,checks,scene,model=self.fixture();p._model_source_service=s
        s.read(p,'model://0','scene://fixture');clone=deepcopy(p)
        copied=clone._model_source_service;self.assertIsNot(copied.lock,s.lock)
        self.assertEqual(copied.statistics()['cached_models'],0)
        copied.read(clone,'model://0','scene://fixture')
        self.assertEqual(s.statistics()['cached_models'],1);self.assertEqual(model.call_count,2)

    def test_real_hash_rejects_same_size_same_mtime_disc_mutation(self):
        from hashlib import sha256
        from pathlib import Path
        import os,tempfile
        from importer.core import ImportError
        document=dict(scene=dict(name='fixture'),assets=dict(models=[dict(semantic_id='model://0')]))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fixture.bin';original=b'original';path.write_bytes(original)
            p=SimpleNamespace(imports={'scene://fixture':document},disc_path=str(path));service=ModelSourceService()
            image=SimpleNamespace(path=path,find=lambda name:None,read_file=lambda node:b'fixture')
            @contextmanager
            def opened(*args):yield image
            with patch('importer.pipeline.Mode2Image',side_effect=opened),patch('importer.pipeline.SUPPORTED_DISC_SHA256',sha256(original).hexdigest()),patch('importer.pipeline.parse_cdname',return_value={0:'fixture'}),patch('importer.pipeline.ProtArchive',return_value=None),patch('importer.pipeline.import_scene',return_value=document) as scene,patch('importer.assets.load_model_source',return_value=b'qualified native') as model:
                self.assertEqual(service.read(p,'model://0','scene://fixture'),b'qualified native')
                self.assertEqual(service.read(p,'model://0','scene://fixture'),b'qualified native')
                saved=path.stat();path.write_bytes(b'modified');os.utime(path,ns=(saved.st_atime_ns,saved.st_mtime_ns))
                self.assertEqual(path.stat().st_size,saved.st_size);self.assertEqual(path.stat().st_mtime_ns,saved.st_mtime_ns)
                with self.assertRaisesRegex(ImportError,'unsupported disc build'):service.read(p,'model://0','scene://fixture')
                self.assertEqual((scene.call_count,model.call_count),(1,1));self.assertEqual(service.statistics()['cached_models'],0)
                path.write_bytes(original);service.read(p,'model://0','scene://fixture');self.assertEqual((scene.call_count,model.call_count),(2,2))

if __name__=='__main__':unittest.main()
