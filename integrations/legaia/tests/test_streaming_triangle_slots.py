"""Explicit model slots admit triangles; incidental scans retain their heuristic."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json,os,struct,tempfile,unittest,zipfile
from importer.core import ImportError,_tmd_extent,scan_tmds,_pack_ranges,decompress_lzs
from importer.assets import decode_tmd,load_model_source,load_model_preview
from importer.model_pack_growth import _qualified_pack
from importer.pipeline import import_scene,_disc_context
from sdk.project import ProjectService
from sdk.script_animation_operands import options,review
from sdk.build import build_project
from sdk.npc_build_script import emitted_prot
from sdk.build_history import verify_build
from importer.model_pack_archive import _archive
from test_importer_assets import model

class TriangleSlots(unittest.TestCase):
    def test_explicit_triangle_and_conservative_scan(self):
        triangle=bytearray(model()[:-8]);struct.pack_into('<I',triangle,16,3);triangle=bytes(triangle)
        self.assertEqual(_tmd_extent(triangle,0),(len(triangle),1))
        self.assertEqual(decode_tmd(triangle)['triangles'],[[0,1,2]])
        self.assertEqual(scan_tmds(triangle),())
        self.assertEqual(len(scan_tmds(model())),1)
        pack=struct.pack('<III',2,3,(12+len(triangle))//4)+triangle+model()
        self.assertEqual(len(_qualified_pack(pack)),2)
        for offset,value in [(12,0),(28,2),(24,0x100000)]:
            bad=bytearray(pack);struct.pack_into('<I',bad,offset,value)
            with self.assertRaises(ImportError):_qualified_pack(bytes(bad))

    @unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
    def test_taiku_import_save_preview_and_native_argument_build(self):
        disc=os.environ['LEGAIA_DISC_BIN'];metadata=import_scene(disc,'taiku')
        self.assertEqual(metadata,import_scene(disc,'taiku'))
        models=[m for m in metadata['assets']['models'] if m['model_pool']=='scene_tmd']
        self.assertEqual([m['normalized_pool_index'] for m in models],list(range(126)))
        self.assertEqual([m['source_record']['byte_offset'] for m in models[:3]],[508,608,708])
        for asset in models[:3]:
            source=load_model_source(disc,asset);preview=load_model_preview(disc,asset)
            self.assertEqual(len(source),100);self.assertEqual(len(preview['vertices']),3)
            self.assertEqual(preview['triangles'],[[0,2,1]])
            self.assertEqual(scan_tmds(source),())
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(metadata,disc)
            owner='scene://taiku/actors/man-p1/0001'
            target=next(t for t in options(p,owner)['targets'] if t['mnemonic']=='EFFECT_ANIMATION_TRIGGER')
            values={'animation_operand':target['values']['animation_operand']^1}
            proposal,_=review(p,owner,target['semantic_id'],values)
            p.command(dict(type='apply_script_animation_operands',entity_id=owner,animation_operand_id=target['semantic_id'],values=values,review_key=proposal['review']['review_key']))
            p.save();self.assertEqual(ProjectService.open(p.root)._document(),p._document())
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports))
            output=build_project(p);audit=json.loads(Path(output['audit']).read_text())
            with zipfile.ZipFile(output['path']) as package,_disc_context(disc) as (_,_,_,archive):
                prot=archive.image.read_user(archive.node.extent_lba,0,archive.node.size,archive.node.size)
                made,delivery=emitted_prot(prot,archive.node.extent_lba*2048,package,audit);built=_archive(made)
                source=models[0]['source_record'];index=source['prot_entry_index']
                original=archive.read_entry(archive.entry(index),extended=True)
                final=built.read_entry(built.entry(index),extended=True)
                self.assertEqual(final,original)
                body,_=decompress_lzs(original[source['compressed_stream_offset']:],source['containing_size'])
                self.assertEqual(len(_qualified_pack(body)),126)
                ranges=_pack_ranges(body)
                for slot,asset in enumerate(models):
                    a,b=ranges[slot];payload=load_model_source(disc,asset)
                    self.assertEqual(body[a:a+len(payload)],payload)
                    self.assertLessEqual(a+len(payload),b)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack,p.imports),before)
            build_id=Path(output['audit']).parent.name
            verify_build(p,build_id)
            evidence=os.environ.get('LEGAIA_TRIANGLE_SLOT_EVIDENCE')
            if evidence:
                Path(evidence).write_text(json.dumps(dict(scene='taiku',scene_slots=126,triangle_slots=[0,1,2],native_slot_offsets=[508,608,708],deterministic_import=True,saved_reopened=True,complete_model_carrier_unchanged=True,all_slot_payloads_matched=True,project_immutable=True,build_id=build_id,build_sha256=sha256(Path(output['path']).read_bytes()).hexdigest(),game_launched=False),indent=2)+'\n')

if __name__=='__main__':unittest.main()
