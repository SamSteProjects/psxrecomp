"""Synthetic ANM/MAN composition reaches a new physical disc without Retail bytes."""
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from importer.core import Mode2Image,ProtArchive,parse_scene_assets,decompress_lzs,parse_man,ImportError
from importer.animation_bank_growth import verify_rebuilt_animation_banks
from importer.model_pack_archive import _archive
from importer.man_actor_structure import append_actor_candidates
from importer.relocated_disc import RelocatedLogicalDisc
from importer.disc_rebuild import write_grown_prot_disc
from importer.serialization import compress_lzs
from sdk.project import ProjectService,ProjectError
from sdk.draft_build import prepare_draft_archive
from tools.cd_sector import SYNC,encode_form1,relocate_mode2
from test_animation_bank_growth import fixture as bank_fixture
from test_man_actor_structure import fixture as man_fixture
from test_model_pack_archive import archive_source
from test_relocated_disc import LogicalSource
from test_model_pack_growth import pack_source,ledger_for
from importer.model_pack_growth import grow_model_pack


class AnimationDraftExport(unittest.TestCase):
    def test_shared_owner_growth_final_readback_and_synthetic_disc(self):
        self._run()

    def test_raw_anm_before_man_synthetic_disc(self):
        self._run(streaming=True)

    def test_raw_man_before_anm_synthetic_disc(self):
        self._run(streaming=True,man_first=True)

    def test_model_anm_and_man_growth_synthetic_disc(self):
        self._run(topology=True)

    def test_model_and_man_growth_without_animation_ledger_synthetic_disc(self):
        self._run(topology=True,bank_growth=False)

    def test_prefixed_archive_model_anm_man_synthetic_disc(self):
        self._run(topology=True,header_offset=2048)

    def test_prefixed_archive_raw_anm_man_synthetic_disc(self):
        self._run(streaming=True,man_first=True,header_offset=2048)

    def _run(self,streaming=False,man_first=False,topology=False,bank_growth=True,header_offset=0):
        _,bank,expanded,_,_=bank_fixture();man=man_fixture()
        candidate,_=append_actor_candidates(man,sha256(man).hexdigest(),[
            dict(id='npc',donor_record_index=1,position=dict(x=832,z=896))])
        payloads=[compress_lzs(bank),compress_lzs(man),b'KEEP',b'opaque3',b'opaque4',b'opaque5']
        if topology:
            pack,models=pack_source();_,ledger=ledger_for(models[2],32,varied=True)
            model_request=dict(entry_index=1,descriptor_index=3,expected_pack_sha256=sha256(pack).hexdigest(),replacements=[dict(slot_index=2,ledger=ledger)])
            expected_pack,pack_audit=grow_model_pack(pack,sha256(pack).hexdigest(),model_request['replacements'])
            payloads[3]=compress_lzs(pack)
        carrier=bytearray(56);struct.pack_into('<II',carrier,0,6,0xAABBCCDD)
        for i,data in enumerate(payloads):
            kind,size=(5,len(bank)) if i==0 else (3,len(man)) if i==1 else (1,len(data))
            if topology and i==3:kind,size=2,len(pack)
            struct.pack_into('<II',carrier,8+8*i,(kind<<24)|size,len(carrier));carrier.extend(data)
        source,starts=archive_source(bytes(carrier),header_offset);table=parse_scene_assets(bytes(carrier),1)
        resource=dict(kind='animation-bank',entry_index=1,table_offset=0,descriptor_index=0,
            expected_bank_sha256=sha256(bank).hexdigest(),bank=expanded)
        native_request=dict(entry_index=1,table_offset=0,source_man_sha256=sha256(man).hexdigest(),candidate=candidate)
        if streaming:
            from test_streaming_animation_bank import chunk
            from importer.streaming_man import streaming_chunks
            from importer.streaming_animation_bank import verify_rebuilt_streaming_animation_banks
            candidate+=bytes(-len(candidate)%4)
            parts=[chunk(3,man),chunk(5,bank)] if man_first else [chunk(5,bank),chunk(3,man)]
            carrier=chunk(1,b'KEEP')+b''.join(parts)+chunk(1,b'TAILraw!')+bytes(4)
            source,starts=archive_source(carrier,header_offset)
            rows=streaming_chunks(carrier)[0]
            resource=dict(kind='streaming-animation-bank',entry_index=1,
                chunk_header_offset=next(c['header_offset'] for c in rows if c['type_byte']==5),
                expected_bank_sha256=sha256(bank).hexdigest(),bank=expanded)
            native_request=dict(entry_index=1,
                chunk_header_offset=next(c['header_offset'] for c in rows if c['type_byte']==3),
                source_man_sha256=sha256(man).hexdigest(),candidate=candidate)
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root)/'project');scene='scene://fixture'
            project.imports={scene:{'scene':{'name':'fixture'},'actors':[]}}
            project.overrides={scene:{'AnimationRecords':{'test_retained_identity':'stable'}},scene+'/actors/man-p1/0001':{'ActorAllocatedAnimation':{'record_id':'stable'}}}
            if not bank_growth:project.overrides={}
            project.actor_drafts={'npc':dict(scene_id=scene)};before=deepcopy(project.overrides)
            if topology:
                project.model_overrides={'asset://fixture/model/added':dict(format='tmd-face-addition-v1',source_scene_id=scene)}
            base=LogicalSource();view=RelocatedLogicalDisc(base,source,sha256(base.read_file(base.find('PROT.DAT'))).hexdigest());sectors=[]
            for lba in range(view.size//2352):
                raw=bytearray(2352);raw[:12]=SYNC;raw[15]=2;raw[17]=1
                raw[18]=0x89 if lba==view.prot_lba+len(source)//2048-1 else 0x08
                raw[20:24]=raw[16:20];raw[24:2072]=view.user_sector(lba)
                sectors.append(encode_form1(relocate_mode2(bytes(raw),lba)))
            disc=Path(root)/'source.bin';disc.write_bytes(b''.join(sectors));project.disc_path=str(disc)
            disc_hash=sha256(disc.read_bytes()).hexdigest();seen=[]
            def prepare(p,selected,*,defer_rebuild,scene_id,animation_growth_managed=False):
                self.assertEqual(animation_growth_managed,bank_growth);self.assertTrue(defer_rebuild);self.assertEqual(selected,'npc')
                if topology:self.assertFalse(p.model_overrides)
                seen.append(scene_id)
                return source,dict(_rebuild_request=native_request,source_disc_sha256=disc_hash,
                    _asset_patches=[dict(offset=starts[1]*2048+(4 if streaming else table.descriptors[2].data_offset),
                        expected_sha256=sha256(b'KEEP').hexdigest(),payload=b'EDIT')])
            from contextlib import ExitStack
            with ExitStack() as stack:
                stack.enter_context(patch('sdk.draft_build._prepare_draft_scene',side_effect=prepare))
                stack.enter_context(patch('sdk.draft_build._disc_context',return_value=nullcontext((None,disc_hash,None,_archive(source)))))
                stack.enter_context(patch('sdk.animation_growth.prepare_animation_growth',return_value=([resource],{'carriers':[]},[])))
                if topology:
                    stack.enter_context(patch('sdk.model_growth.prepare_model_growth',return_value=([model_request],dict(deferred_model_ids=list(project.model_overrides),carriers=[dict(entry_index=1,descriptor_index=3,carrier=dict(pack_audit=pack_audit))]))))
                result,audit=prepare_draft_archive(project,'npc')
            self.assertEqual(seen,[scene]);self.assertEqual(project.overrides,before)
            if bank_growth:self.assertTrue(audit['animation_growth']['final_archive_banks'][0]['final_bank_verified'])
            else:self.assertNotIn('animation_growth',audit)
            self.assertGreater(len(result),len(source));self.assertEqual(result[-8*2048:],source[-8*2048:])
            archive=_archive(result);raw=archive.read_entry(archive.entry(1))
            if streaming:
                rows,terminated=streaming_chunks(raw);self.assertTrue(terminated)
                anm=next(c for c in rows if c['type_byte']==5)
                man_chunk=next(c for c in rows if c['type_byte']==3)
                self.assertEqual(raw[anm['header_offset']+4:anm['header_offset']+4+anm['size']],expanded)
                emitted=raw[man_chunk['header_offset']+4:man_chunk['header_offset']+4+man_chunk['size']]
                self.assertEqual(raw[4:8],b'EDIT')
                final_resource=dict(resource,chunk_header_offset=anm['header_offset'])
                verifier=verify_rebuilt_streaming_animation_banks
            else:
                new=parse_scene_assets(raw,1)
                self.assertEqual(decompress_lzs(raw[new.descriptors[0].data_offset:],new.descriptors[0].size)[0],expanded if bank_growth else bank)
                emitted=decompress_lzs(raw[new.descriptors[1].data_offset:],new.descriptors[1].size)[0]
                self.assertEqual(raw[new.descriptors[2].data_offset:new.descriptors[2].data_offset+4],b'EDIT')
                final_resource=resource if bank_growth else dict(resource,bank=bank);verifier=verify_rebuilt_animation_banks
            self.assertEqual(emitted,candidate);self.assertEqual(len(parse_man(emitted).actors),2)
            output=Path(root)/'export.bin'
            report=write_grown_prot_disc(disc,disc_hash,result,sha256(source).hexdigest(),output)
            self.assertTrue(report['reopened_prot_verified']);self.assertEqual(sha256(disc.read_bytes()).hexdigest(),disc_hash)
            with Mode2Image(output) as image:
                reopened=ProtArchive(image,image.find('PROT.DAT'));self.assertEqual(image.read_file(image.find('PROT.DAT')),result)
                final=image.read_user(reopened.node.extent_lba,0,reopened.node.size,reopened.node.size)
                if bank_growth:self.assertEqual(verifier(final,[final_resource]),audit['animation_growth']['final_archive_banks'])
                else:self.assertTrue(verifier(final,[final_resource])[0]['final_bank_verified'])
                if topology:
                    owner=_archive(final);raw=owner.read_entry(owner.entry(1));descriptor=parse_scene_assets(raw,1).descriptors[3]
                    self.assertEqual(decompress_lzs(raw[descriptor.data_offset:],descriptor.size)[0],expected_pack)
                    self.assertTrue(audit['model_growth']['final_archive_packs'][0]['final_model_pack_verified'])
            bad=bytearray(result);descriptor_at=archive.entry(1).start_lba*2048+(anm['header_offset'] if streaming else 8)
            struct.pack_into('<I',bad,descriptor_at,(5<<24)|(len(expanded)+1))
            with self.assertRaises(ImportError):verifier(bytes(bad),[final_resource])
            if topology:return
            with patch('sdk.draft_build._prepare_draft_scene',side_effect=prepare),patch('sdk.draft_build._disc_context',return_value=nullcontext((None,'changed',None,_archive(source)))):
                with self.assertRaisesRegex(ProjectError,'disc changed'):prepare_draft_archive(project,'npc')


if __name__=='__main__':unittest.main()
