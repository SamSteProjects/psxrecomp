from copy import deepcopy
from hashlib import sha256
import json,struct,unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.model_face_addition import source,review
from importer.model_json import export_shape_json
from importer.model_pack_archive import _archive,rebuild_model_pack_entry
from importer.core import parse_scene_assets,decompress_lzs,_pack_ranges
from sdk.model_growth import prepare_model_growth
import test_model_growth as growth_fixtures


class PostAdditionProjectTests(unittest.TestCase):
    def fixture(self):
        helper=growth_fixtures.ModelGrowthTests();self.addCleanup(helper.doCleanups)
        return helper.fixture()

    def test_vector_face_object_and_further_addition_survive_history_save_and_pack_rebuild(self):
        p,asset,other,pack,raw=self.fixture()
        original_binding=deepcopy(p.model_overrides[asset]);current=p.read_model_replacement(asset,original_binding)
        stable=source(p,asset,'a'*64)['topology']['faces']
        p.set_model_vector(asset,0,'vertices',0,[17,23,-5],sha256(current).hexdigest())
        vector_bytes=p.read_model_replacement(asset,p.model_overrides[asset]);self.assertEqual(p.model_overrides[asset]['base_binding'],original_binding['base_binding'])
        self.assertEqual(source(p,asset,'a'*64)['topology']['faces'],stable)
        inspection=p.model_primitive_source(asset);self.assertEqual(inspection['schema_version'],'legaia.model-primitives.v4');self.assertEqual(sum(len(rows) for rows in inspection['authored_faces']),1);added=next(row for row in stable if row['origin']=='authored')
        edits=[dict(object_index=added['object_index'],primitive_index=added['current_primitive_index'],vertices=[0,1,2,4],uvs=[[1,2],[3,4],[5,6],[7,8]],colors=[[41,52,63]])]
        preview=p.preview_model_primitives(asset,edits,sha256(vector_bytes).hexdigest(),'a'*64)
        p.set_model_primitives(asset,edits,sha256(vector_bytes).hexdigest(),'a'*64,preview['proposed_sha256'])
        faces=p.read_model_replacement(asset,p.model_overrides[asset])
        from importer.model_materials import patch_model_materials
        material,_=patch_model_materials(faces,sha256(faces).hexdigest(),[dict(kind='primitive',object_index=added['object_index'],primitive_index=added['current_primitive_index'],values={'clut_column':7})])
        p.set_model_replacement(asset,material)
        p.set_model_vector(asset,0,'normals',0,[4095,1,-1],sha256(material).hexdigest())
        faces=p.read_model_replacement(asset,p.model_overrides[asset])
        p.translate_model_object(asset,0,[1,-2,3],sha256(faces).hexdigest())
        translated=p.read_model_replacement(asset,p.model_overrides[asset])
        requests=[dict(face_id='face://authored/00000000-0000-4000-8000-000000000002',donor_face_id=added['face_id'],fields={'vertices':[4,3,2,1]})]
        proposal=review(p,asset,requests,sha256(translated).hexdigest(),'a'*64)
        p.apply_model_face_additions(asset,requests,sha256(translated).hexdigest(),'a'*64,proposal['proposed_sha256'])
        final=p.read_model_replacement(asset,p.model_overrides[asset]);saved=deepcopy(p.model_overrides[asset])
        self.assertEqual(saved['ledger']['schema_version'],'legaia.model-face-addition-ledger.v2')
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),translated)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),final)
        from sdk.export_snapshot import capture_export_inputs
        _,files=capture_export_inputs(p)
        self.assertEqual(files['Authored/Models/'+saved['asset_sha256']+'.tmd'],final)
        self.assertIn('Authored/Models/'+saved['base_binding']['asset_sha256']+'.tmd',files)
        p.save()
        original=p._model_source
        with patch.object(ProjectService,'_model_source',side_effect=original):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.model_overrides[asset],saved)
            self.assertEqual(reopened.read_model_replacement(asset,saved),final)
        requests,audit=prepare_model_growth(p,_archive(raw))
        rebuilt,_=rebuild_model_pack_entry(raw,sha256(raw).hexdigest(),**requests[0])
        archive=_archive(rebuilt);carrier=archive.read_entry(archive.entry(1));d=parse_scene_assets(carrier,1).descriptors[1]
        proposed,_=decompress_lzs(carrier[d.data_offset:],d.size);start,_=_pack_ranges(proposed)[1]
        self.assertEqual(proposed[start:start+len(final)],final)

    def test_current_JSON_source_and_noop_reject_stale_or_opaque_edits_transactionally(self):
        p,asset,_,_,_=self.fixture();current=p.read_model_replacement(asset,p.model_overrides[asset])
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        p.set_model_replacement(asset,current);self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        document=json.loads(export_shape_json(current));document['objects'][0]['vertices'][0]=[2,3,4]
        candidate,report=p._prepare_model_file(asset,json.dumps(document).encode(),'json')
        self.assertEqual(report['comparison'],'current_addition_topology');p.set_model_replacement(asset,candidate)
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        with self.assertRaises(ProjectError):p.set_model_vector(asset,0,'vertices',0,[1,2,3],sha256(current).hexdigest())
        bad=bytearray(candidate);bad[0]^=1
        with self.assertRaises(ProjectError):p.set_model_replacement(asset,bytes(bad))
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)


if __name__=='__main__':unittest.main()
