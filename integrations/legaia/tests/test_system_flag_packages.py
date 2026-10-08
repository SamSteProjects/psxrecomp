"""Opt-in complete Retail MAN/package readback for both carriers and partitions."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from importer.pipeline import import_scene,_disc_context,_bounded_scene_range
from importer.man_source import read_man_source
from importer.core import ImportError as RetailImportError
from importer.man_layout import read_man_layout
from importer.model_pack_archive import _archive
from importer.script_inspection import inspect_record
from importer.system_flag_authoring import load_system_flag_authoring_context
from sdk.project import ProjectService
from sdk.system_flags import review
from sdk.script_branches import review as branch_review
from sdk.build import build_project
from sdk.build_review import review as build_review
from sdk.build_history import verify_build
from sdk.npc_build_script import emitted_prot


def record(man,partition,index):
    row=next(r for r in read_man_layout(man)['records'] if r['partition']==partition and r['record_index']==index)
    return man[row['byte_offset']:row['byte_offset']+row['byte_length']]


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class SystemSelectorPackages(unittest.TestCase):
    def qualify(self,scene,append):
        disc=os.environ['LEGAIA_DISC_BIN']
        with tempfile.TemporaryDirectory() as directory,_disc_context(disc) as (_,_,mapping,archive):
            document=import_scene(disc,scene);p=ProjectService(Path(directory));p.import_metadata(document,disc)
            source=read_man_source(archive,*_bounded_scene_range(archive,mapping,scene),scene)
            self.assertEqual(source.kind,'descriptor_man' if scene=='town01' else 'raw_streaming_man')
            ctx=load_system_flag_authoring_context(disc,scene);self.assertEqual(ctx._man,source.payload);targets=[]
            for row in read_man_layout(source.payload)['records']:
                if row['partition'] not in (1,2):continue
                owner=f"scene://{scene}/"+('actors/man-p1/' if row['partition']==1 else 'scripts/man-p2/')+f"{row['record_index']:04d}"
                try:options=ctx.options(owner)
                except RetailImportError:continue
                targets.extend(options['targets'])
            def clone_safe(t):
                _,raw,entry=ctx._source.verified_record(t['owner_id'])
                return not any(n['mnemonic']=='SPAWN_RECORD' for n in inspect_record(raw,entry)['instructions'])
            actor=next(t for t in targets if '/actors/' in t['owner_id'] and (not append or clone_safe(t)))
            secondary=next(t for t in targets if '/scripts/man-p2/' in t['owner_id'])
            expected=bytearray(source.payload);bindings=[]
            for target,value in ((actor,4095),(secondary,0)):
                r=review(p,target['owner_id'],target['semantic_id'],{'index':value})
                p.command(dict(type='set_system_flag_selector',entity_id=target['owner_id'],operand_id=target['semantic_id'],value={'index':value},review_key=r['review_key']))
                at=target['decoded_byte_offset'];expected[at:at+2]=bytes(((source.payload[at]&0xf0)|(value>>8),value&255))
                bindings.append(dict(owner=target['owner_id'],operand=target['semantic_id'],pc=target['pc'],retail=target['values']['index'],current=value))
            if secondary['mnemonic']=='SYSFLAG_TEST':
                target_pc=secondary['pc']+4;branch=secondary['semantic_id'].replace('/system-flag/','/branch/')
                r,_=branch_review(p,secondary['owner_id'],branch,{'target_pc':target_pc})
                p.command(dict(type='set_branch',entity=secondary['owner_id'],branch_id=branch,value={'target_pc':target_pc},review_key=r['review']['review_key']))
                at=secondary['decoded_byte_offset']+2;expected[at:at+2]=((target_pc-secondary['pc']-2)&65535).to_bytes(2,'little')
            donor_index=int(actor['owner_id'].rsplit('/',1)[1]);donor_record=record(source.payload,1,donor_index)
            if append:
                donor=next(a for a in document['actors'] if a['semantic_id']==actor['owner_id'])
                position={k:donor['imported_transform']['position'][k] for k in ('x','z')}
                p.command(dict(type='create_actor_draft',donor_entity_id=actor['owner_id'],position=position,name='Selector delivery probe'))
                # Adding one P1 owner shifts global P2 indices by one. Construct
                # those reached opcode44 byte edits directly, without the writer.
                from importer.trigger_scripts import _p2_entry
                layout=read_man_layout(source.payload)
                first=sum(layout['partition_counts'][:2]);last=first+layout['partition_counts'][2]
                for span in layout['records']:
                    if span['partition'] not in (1,2):continue
                    raw=record(source.payload,span['partition'],span['record_index'])
                    entry=1+raw[0]*2+4 if span['partition']==1 else _p2_entry(raw)[0]
                    for node in inspect_record(raw,entry)['instructions']:
                        if node['mnemonic']!='SPAWN_RECORD':continue
                        old=node['operands']['global_record_index'];self.assertTrue(first<=old<last)
                        relative=node['pc']+(2 if node['target_context'] is not None else 1)
                        self.assertEqual(raw[relative],old)
                        expected[span['byte_offset']+relative]=old+1
            p.save();before=deepcopy((p._document(),p.imports,p.undo_stack,p.redo_stack));metadata=(p.root/'project.legaia.json').read_bytes()
            assessment=build_review(p);self.assertTrue(assessment['normal_build_ready'],assessment['blockers'])
            built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'))
            with zipfile.ZipFile(built['path']) as package:
                source_prot=archive.image.read_user(archive.node.extent_lba,0,archive.node.size,archive.node.size)
                delivered,delivery=emitted_prot(source_prot,archive.node.extent_lba*2048,package,audit)
                emitted=read_man_source(_archive(delivered),*_bounded_scene_range(archive,mapping,scene),scene)
            self.assertEqual(emitted.kind,source.kind)
            if not append:self.assertEqual(emitted.payload,bytes(expected))
            else:
                # Compare every original record independently after offset rebasing.
                for row in read_man_layout(source.payload)['records']:
                    actual=record(emitted.payload,row['partition'],row['record_index']);wanted=record(bytes(expected),row['partition'],row['record_index'])
                    self.assertEqual(actual,wanted,f"{scene} original partition {row['partition']} record {row['record_index']}: first differences {[i for i,(a,b) in enumerate(zip(actual,wanted)) if a!=b][:12]}")
                clone_index=read_man_layout(source.payload)['partition_counts'][1]
                self.assertEqual(record(emitted.payload,1,clone_index),donor_record)
            self.assertEqual(before,(p._document(),p.imports,p.undo_stack,p.redo_stack))
            self.assertEqual(metadata,(p.root/'project.legaia.json').read_bytes())
            self.assertEqual(ProjectService.open(p.root)._document(),p._document())
            self.assertTrue(verify_build(p,Path(built['audit']).parent.name)['matches_current_inputs'])
            if os.environ.get('LEGAIA_SYSTEM_PACKAGE_EVIDENCE'):
                dest=Path(os.environ['LEGAIA_SYSTEM_PACKAGE_EVIDENCE']);dest.mkdir(parents=True,exist_ok=True)
                (dest/f"{scene}-{'appended' if append else 'normal'}.json").write_text(json.dumps(dict(scene=scene,append=append,bindings=bindings,carrier=emitted.kind,delivery=delivery,source_man_sha256=hashlib.sha256(source.payload).hexdigest(),emitted_man_sha256=hashlib.sha256(emitted.payload).hexdigest(),package_sha256=built['sha256'],full_man_equal=not append,all_original_records_equal=append,clone_inherits_retail=append,project_imports_history_unchanged=True,save_open_matches=True,gameplay_verified=False),indent=2),encoding='utf-8')

    def test_complete_normal_compressed_and_streaming_packages(self):
        for scene in ('town01','dolk2'):
            with self.subTest(scene=scene):self.qualify(scene,False)

    def test_appended_compressed_and_streaming_packages_preserve_original_p2_and_clone(self):
        for scene in ('town01','dolk2'):
            with self.subTest(scene=scene):self.qualify(scene,True)


if __name__=='__main__':unittest.main()
