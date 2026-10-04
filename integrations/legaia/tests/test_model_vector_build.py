"""A qualified V5 vector-allocation binding survives existing project consumers and normal Build.

The fixture installs the internal binding; this does not test a vector-allocation UI
or project command, which are not implemented yet.
"""
from copy import deepcopy
from hashlib import sha256
import tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import parse_scene_assets,decompress_lzs,_pack_ranges
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_face_ledger import append_vector_ledger,append_face_ledger,replay_face_ledger
from sdk.model_face_addition import base_content
from sdk.project import ProjectService
from sdk.build import build_project
import test_model_growth_normal_build as fixtures


class VectorBuildTests(unittest.TestCase):
    def test_v5_binding_new_vector_face_content_history_save_open_and_build(self):
        helper=fixtures.ModelGrowthNormalBuildTests();self.addCleanup(helper.doCleanups)
        p,asset,*_=helper.fixture()
        binding=deepcopy(p.model_overrides[asset])
        original=p._model_source(asset,p.active_scene)
        base=base_content(p,asset,original,binding)
        _,audit=replay_face_ledger(base,binding['ledger'])
        import struct
        from importer.model_primitives import inspect_model_primitives
        current=p.read_model_replacement(asset,binding)
        nv=struct.unpack_from('<I',current,16)[0]
        requests=[dict(object_index=0,kind=kind,vectors=[[100,200,300],[400,500,600]]) for kind in ('vertices','normals')]
        current,ledger,audit=append_vector_ledger(base,binding['ledger'],requests)
        donor=audit['faces'][0]
        corners=inspect_model_primitives(current)['objects'][0]['primitives'][0]['corner_count']
        request=dict(face_id='face://authored/00000000-0000-4000-8000-000000000099',
            donor_face_id=donor['face_id'],fields=dict(vertices=[nv,nv+1,0,1][:corners]))
        restored,ledger,audit=append_face_ledger(base,ledger,[request])
        self.assertEqual(audit['allocated_vector_count'],4)
        self.assertEqual(inspect_model_primitives(restored)['objects'][0]['primitives'][-1]['vertices'],[nv,nv+1,0,1][:corners])
        binding.update(ledger=ledger,asset_sha256=sha256(restored).hexdigest(),byte_length=len(restored))
        (p.root/'Authored'/'Models'/(binding['asset_sha256']+'.tmd')).write_bytes(restored)
        p.model_overrides[asset]=binding
        self.assertEqual(p.read_model_replacement(asset,binding),restored)
        p.set_model_vector(asset,0,'vertices',nv+1,[71,19,-3],sha256(restored).hexdigest())
        final=p.read_model_replacement(asset,p.model_overrides[asset])
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v5')
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),restored)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),final)
        p.save();saved=deepcopy(p.model_overrides[asset])
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.model_overrides[asset],saved)
            self.assertEqual(reopened.read_model_replacement(asset,saved),final)
        build=build_project(p)
        with zipfile.ZipFile(build['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode())
            entry=manifest['disc_relocation'][0]
            decoded=decode_relocation_package(package.read(entry['file']),entry['sha256'])
        archive=_archive(decoded['replacement']);carrier=archive.read_entry(archive.entry(1))
        descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size)
        start,_=_pack_ranges(pack)[1]
        self.assertEqual(pack[start:start+len(final)],final)
        self.assertEqual(p.model_overrides[asset],saved)


if __name__=='__main__':unittest.main()
