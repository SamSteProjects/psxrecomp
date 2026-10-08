"""Real raw-MAN source arguments and independent NPC model arguments reach Build."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json,os,shutil,tempfile,unittest,zipfile
from importer.animation_operand_authoring import load_animation_operand_authoring_context
from importer.man_actor_structure import append_actor_candidates
from importer.man_layout import read_man_layout
from importer.pipeline import import_scene,_disc_context,_bounded_scene_range
from importer.man_source import read_man_source
from importer.model_pack_archive import _archive
from sdk.project import ProjectService
from sdk.script_animation_operands import review
from sdk.npc_animation_operands import review as npc_review
from sdk.build import build_project
from sdk.build_history import verify_build
from sdk.npc_build_script import emitted_prot

OWNER='scene://rikuroa/actors/man-p1/0007'

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class StreamingAnimationOperands(unittest.TestCase):
    def test_fixed_span_p1_p2_source_arguments(self):self.run_build(False)
    def test_growing_raw_carrier_independent_model_argument_clones(self):self.run_build(True)

    def run_build(self,clones):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'rikuroa'),os.environ['LEGAIA_DISC_BIN'])
            c=load_animation_operand_authoring_context(p.disc_path,'rikuroa')
            target=c.options(OWNER)['targets'][0];self.assertEqual(target['mnemonic'],'SET_MODEL_ANIMATION')
            ids=[];clone_values=[dict(model_id=1,animation_frame=2,tween_frames=3),dict(model_id=16777215,animation_frame=65535,tween_frames=65535)]
            if clones:
                for i,values in enumerate(clone_values):
                    p.command(dict(type='create_actor_draft',donor_entity_id=OWNER,name=f'Raw argument clone {i}',position=dict(x=128+i*128,z=256)))
                    identity=next(name for name in p.actor_drafts if name not in ids);ids.append(identity)
                    request=dict(entity_id=identity,entries={target['semantic_id']:values});proposal=npc_review(p,request)
                    p.command(dict(type='set_actor_draft_animation_operands',**request,review_key=proposal['review_key']))
                requests=[dict(id=name,donor_record_index=7,position=p.actor_drafts[name]['position']) for name in ids]
                candidate,allocation=append_actor_candidates(c._man,sha256(c._man).hexdigest(),requests)
            else:candidate,allocation=c._man,None
            expected=bytearray(candidate);layout=read_man_layout(candidate)
            def literal(record,selected,values):
                fields=[('model_id',3),('animation_frame',2),('tween_frames',2)] if selected['mnemonic']=='SET_MODEL_ANIMATION' else [('animation_operand',1)]
                at=record['byte_offset']+selected['pc']+selected['instruction_length']-sum(width for _,width in fields)
                for field,width in fields:expected[at:at+width]=values[field].to_bytes(width,'little');at+=width
            if clones:
                for name,values in zip(ids,clone_values):
                    row=next(row for row in allocation['drafts'] if row['draft_id']==name)
                    literal(next(r for r in layout['records'] if r['partition']==1 and r['record_index']==row['record_index']),target,values)
            for owner,mnemonic in [(OWNER,'SET_MODEL_ANIMATION'),('scene://rikuroa/actors/man-p1/0001','EFFECT_ANIMATION_TRIGGER'),('scene://rikuroa/scripts/man-p2/0053','SET_MODEL_ANIMATION')]:
                selected=next(t for t in c.options(owner)['targets'] if t['mnemonic']==mnemonic);values={key:value^1 for key,value in selected['values'].items()}
                assessed,_=review(p,owner,selected['semantic_id'],values)
                p.command(dict(type='apply_script_animation_operands',entity_id=owner,animation_operand_id=selected['semantic_id'],values=values,review_key=assessed['review']['review_key']))
                partition=1 if '/actors/' in owner else 2;index=int(owner.split('/')[-1])
                literal(next(r for r in layout['records'] if r['partition']==partition and r['record_index']==index),selected,values)
            if clones:expected.extend(bytes((-len(expected))%4))
            p.save();before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports))
            output=build_project(p);audit=json.loads(Path(output['audit']).read_text(encoding='utf-8'))
            with zipfile.ZipFile(output['path']) as package,_disc_context(p.disc_path) as (_,_,mapping,archive):
                original=read_man_source(archive,*_bounded_scene_range(archive,mapping,'rikuroa'),'rikuroa');self.assertEqual(original.kind,'raw_streaming_man')
                source_prot=archive.image.read_user(archive.node.extent_lba,0,archive.node.size,archive.node.size)
                prot,delivery=emitted_prot(source_prot,archive.node.extent_lba*2048,package,audit);made=_archive(prot)
                emitted=read_man_source(made,*_bounded_scene_range(made,mapping,'rikuroa'),'rikuroa')
                self.assertEqual(emitted.payload,bytes(expected));self.assertEqual(emitted.kind,'raw_streaming_man')
                # The original record bank and every unrelated archive entry remain literal.
                old=archive.read_entry(archive.entry(original.entry_index));new=made.read_entry(made.entry(original.entry_index))
                header=original.chunk_header_offset;self.assertEqual(emitted.chunk_header_offset,header)
                self.assertEqual(old[:header],new[:header]);self.assertEqual(int.from_bytes(new[header:header+4],'little'),(3<<24)|len(expected))
                tail=old[original.payload_offset+len(original.payload):];after=new[emitted.payload_offset+len(emitted.payload):]
                self.assertEqual(tail,after[:len(tail)]);self.assertFalse(any(after[len(tail):]))
                target_entry=archive.entry(original.entry_index);start=target_entry.start_lba*2048;end=start+target_entry.indexed_size_sectors*2048
                unrelated=0;aliases=[];extended_footprints=[]
                for entry in archive.entries:
                    at=entry.start_lba*2048;stop=at+entry.indexed_size_sectors*2048
                    if at<end and start<stop:aliases.append(entry.index);continue
                    old_entry=archive.read_entry(entry,extended=False);new_entry=made.read_entry(made.entry(entry.index),extended=False)
                    self.assertEqual(old_entry,new_entry[:len(old_entry)],f'Original indexed payload changed: entry {entry.index}')
                    extra=len(new_entry)-len(old_entry);self.assertGreaterEqual(extra,0)
                    if extra:
                        self.assertTrue(clones);self.assertLessEqual(extra,((len(expected)-len(c._man)+2047)//2048)*2048)
                        extended_footprints.append(dict(entry_index=entry.index,additional_indexed_bytes=extra))
                    unrelated+=1
                self.assertGreater(unrelated,0)
                members=[row['file'] for row in audit['overlays']]
                if audit.get('relocation_payload'):members.append(audit['relocation_payload']['file'])
                for member in members:self.assertEqual(package.read(member),(Path(output['package_directory'])/member).read_bytes())
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.imports));verify_build(p,Path(output['audit']).parent.name)
            if clones:
                from sdk.npc_script_compare import compare
                for name in ids:self.assertEqual([row['category'] for row in compare(p,name,Path(output['audit']).parent.name)['authored_spans']],['own_animation_operand']*3)
            if os.environ.get('LEGAIA_STREAMING_ARGUMENT_EVIDENCE'):
                root=Path(os.environ['LEGAIA_STREAMING_ARGUMENT_EVIDENCE']);root.mkdir(parents=True,exist_ok=True)
                build_id=Path(output['audit']).parent.name;build_root=root/build_id;build_root.mkdir(exist_ok=True)
                retained=build_root/f'run-{len(list(build_root.glob("run-*")))+1}';shutil.copytree(p.root,retained)
                reopened=ProjectService.open(retained);verify_build(reopened,build_id)
                (root/('clones.json' if clones else 'source.json')).write_text(json.dumps(dict(build_id=build_id,package_sha256=output['sha256'],complete_literal_man_equal=True,carrier_prefix_suffix_equal=True,chunk_size_verified=True,original_unrelated_indexed_payloads_preserved=unrelated,extended_indexed_footprints=extended_footprints,carrier_alias_entry_indices=aliases,directory_zip_equal=True,saved_artifacts_verified=True,delivery=delivery,final_man_sha256=sha256(emitted.payload).hexdigest(),retained_fixture=str(retained),gameplay_verified=False),indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':unittest.main()
