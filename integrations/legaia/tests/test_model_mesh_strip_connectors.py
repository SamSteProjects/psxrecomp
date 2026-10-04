"""Strip connectors preserve source parity through the existing native workflow."""
from copy import deepcopy
from pathlib import Path
import json,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from sdk import model_mesh_append
from sdk.project import ProjectService
from sdk.build import build_project
import test_model_mesh_append as fixtures

POSITIONS=[[0,0,0],[100,0,0],[0,100,0],[200,0,0],[200,100,0],[300,0,0]]

def connected():return fixtures.glb(positions=POSITIONS,indices=[0,1,2,2,3,3,4,5],mode=5)

class StripConnectorTests(unittest.TestCase):
    def test_original_parity_budget_and_real_collapse(self):
        result=decode_append_mesh(connected())
        explicit=decode_append_mesh(fixtures.glb(positions=POSITIONS,indices=[0,1,2,4,3,5]))
        for key in ('vertices','triangles','triangle_normals','triangle_uvs','triangle_colors'):
            self.assertEqual(result[key],explicit[key])
        self.assertEqual(inspect_append_mesh(connected())['triangle_count'],2)
        one=fixtures.glb(indices=[0]*200+[0,1,2],mode=5)
        self.assertEqual(len(decode_append_mesh(one)['triangles']),1)
        for content in (fixtures.glb(indices=[0]*16385,mode=5),fixtures.glb(indices=[0,0,0],mode=5),
                        fixtures.glb(indices=[0,1,2,2,9,9],mode=5),fixtures.glb(indices=[0,0,0]),
                        fixtures.glb(positions=[[0,0,0],[.1,0,0],[0,.1,0]],indices=[0,1,2],mode=5)):
            with self.assertRaises(ImportError):decode_append_mesh(content)

    def test_review_history_save_open_and_exact_normal_build(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups);p,asset,donor=helper.fixture()
        source=model_mesh_append.source(p,asset,'a'*64);before=deepcopy(p._document());content=connected()
        candidate,_,report=model_mesh_append.prepare(p,asset,content,donor,source['effective_sha256'],'a'*64)
        self.assertEqual(p._document(),before);self.assertEqual(len(report['geometry']['triangles']),2)
        p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key'])
        p.undo();self.assertEqual(p._document(),before);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            entry=tomllib.loads(package.read('manifest.toml').decode())['disc_relocation'][0]
            archive=_archive(decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)
