"""Normal Build uses public synthetic model/ISO data and the real generic packer."""
from contextlib import nullcontext
from hashlib import sha256
from pathlib import Path
import json
import tomllib
import unittest
from unittest.mock import patch
import zipfile

from importer.core import Mode2Image, ProtArchive, ImportError, parse_scene_assets, decompress_lzs, _pack_ranges
from importer.relocated_disc import RelocatedLogicalDisc
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from sdk.build import build_project, _build_project
from sdk.build_relocation import prepare_build_relocation
from tools.cd_sector import SYNC, encode_form1, relocate_mode2
from test_relocated_disc import LogicalSource
import test_model_growth as growth_fixtures


class ModelGrowthNormalBuildTests(unittest.TestCase):
    def fixture(self):
        helper=growth_fixtures.ModelGrowthTests();self.addCleanup(helper.doCleanups)
        p,asset,other,pack,raw=helper.fixture()
        base=LogicalSource()
        view=RelocatedLogicalDisc(base,raw,sha256(base.read_file(base.find('PROT.DAT'))).hexdigest())
        sectors=[]
        for lba in range(view.size//2352):
            frame=bytearray(2352);frame[:12]=SYNC;frame[15]=2;frame[17]=1
            frame[18]=0x89 if lba==view.prot_lba+len(raw)//2048-1 else 0x08
            frame[20:24]=frame[16:20];frame[24:2072]=view.user_sector(lba)
            sectors.append(encode_form1(relocate_mode2(bytes(frame),lba)))
        source=p.root/'synthetic-source.bin';source.write_bytes(b''.join(sectors));p.disc_path=str(source)
        image=Mode2Image(source);self.addCleanup(image.close)
        archive=ProtArchive(image,image.find('PROT.DAT'))
        doc=p.imports[p.active_scene]
        self.enterContext(patch('sdk.build.import_scene',return_value=doc))
        self.enterContext(patch('sdk.build._disc_context',side_effect=lambda _:nullcontext((image,sha256(source.read_bytes()).hexdigest(),None,archive))))
        return p,asset,other,image,archive

    def test_normal_build_packages_shared_growth_and_source_offset_patches_once(self):
        p,asset,other,image,archive=self.fixture()
        offset=archive.node.extent_lba*2048+4*2048+10
        payload=b'PATCH';before=image.read_user(0,offset,len(payload),image.size//2352*2048)
        row=dict(scene='fixture',offset=offset,size=len(payload),payload=payload,file='assets/patch.bin',
                 sha256=sha256(payload).hexdigest(),expected_sha256=sha256(before).hexdigest())
        with patch('sdk.worldmap_placements.build',side_effect=lambda project,overlays:overlays.append(row) or []):
            review=_build_project(p,None,review_only=True)
            self.assertFalse(review['output_written']);self.assertFalse((p.root/'Builds').exists())
            result=build_project(p)
            again=build_project(p);self.assertEqual(result['sha256'],again['sha256'])
        with zipfile.ZipFile(result['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode())
            self.assertEqual(manifest['format_version'],7);self.assertNotIn('overlay',manifest)
            self.assertEqual(len(manifest['disc_relocation']),1)
            entry=manifest['disc_relocation'][0]
            self.assertEqual(set(package.namelist()),{'manifest.toml',entry['file']})
            decoded=decode_relocation_package(package.read(entry['file']),entry['sha256'])
        reopened=_archive(decoded['replacement'])
        neighbor=reopened.entry(3).start_lba*2048
        self.assertEqual(decoded['replacement'][neighbor+10:neighbor+15],payload)
        carrier=reopened.read_entry(reopened.entry(1));descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size)
        for slot,identifier in ((1,asset),(0,other)):
            start,_=_pack_ranges(pack)[slot]
            expected=p.read_model_replacement(identifier,p.model_overrides[identifier])
            self.assertEqual(pack[start:start+len(expected)],expected)
        audit=json.loads(Path(result['audit']).read_text())
        self.assertEqual(audit['model_growth']['deferred_model_ids'],sorted([asset,other]))
        self.assertTrue(audit['relocation']['composition']['final_packs_verified'])
        self.assertTrue(audit['relocation']['package']['readback_verified'])
        self.assertEqual({change['owner_id'] for change in result['report']['changes']},{asset,other})
        self.assertEqual(result['runtime_status'],'package_built_not_launched')

    def test_external_patch_maps_to_shifted_source_sector_and_rejects_iso_conflicts(self):
        p,_,_,image,archive=self.fixture()
        from sdk.model_growth import prepare_model_growth
        requests,_=prepare_model_growth(p,archive)
        movie=image.find('MOV/MOVIE.STR').extent_lba
        offset=movie*2048+2046;payload=b'ABCD'
        def overlay(at,data):
            return dict(offset=at,size=len(data),payload=data,sha256=sha256(data).hexdigest(),
                        expected_sha256=sha256(image.read_user(0,at,len(data),image.size//2352*2048)).hexdigest())
        result,audit=prepare_build_relocation(image,archive,requests,[overlay(offset,payload)])
        decoded=decode_relocation_package(result['payload'],result['sha256'])
        growth=decoded['proposed_sector_count']-decoded['source_sector_count']
        self.assertEqual(decoded['metadata'][movie+growth][-2:],b'AB')
        self.assertEqual(decoded['metadata'][movie+growth+1][:2],b'CD')
        self.assertEqual(audit['external_patched_sectors'],2)
        for changes in ([overlay(16*2048,b'X')],[overlay(offset,payload)]*2,
                        [dict(overlay(offset,payload),expected_sha256='0'*64)]):
            with self.assertRaises(ImportError):prepare_build_relocation(image,archive,requests,changes)


if __name__=='__main__':unittest.main()
