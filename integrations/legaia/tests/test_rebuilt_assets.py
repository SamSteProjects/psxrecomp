"""Final asset verification follows relocated entry identities, not old offsets."""
from hashlib import sha256
import struct
import unittest
from sdk.map_build import verify_rebuilt_maps
from sdk.project import ProjectError
from importer.prot_rebuild import replace_physical_entry


class RebuiltAssets(unittest.TestCase):
    def test_descriptor_location_supersedes_stale_carrier_offset(self):
        raw=bytearray(2048*10)
        struct.pack_into('<ii',raw,4,5,1)
        struct.pack_into('<5I',raw,16,1,2,3,4,0)
        table=2048
        struct.pack_into('<I',raw,table,6)
        for index in range(6):
            kind=5 if index==2 else 3 if index==1 else 1
            struct.pack_into('<II',raw,table+8+index*8,(kind<<24)|3,56 if index==0 else 100+index*10)
        raw[table+120:table+123]=b'ANM'
        raw[table+80:table+83]=b'old'
        audit=dict(map_entry_index=0,relative_offset=80,byte_length=3,
                   result_sha256=sha256(b'ANM').hexdigest(),
                   descriptor_binding=dict(table_offset=0,index=2,type=5))
        verify_rebuilt_maps(bytes(raw),[audit])
        self.assertTrue(audit['reopened_payload_verified'])
        bad=dict(audit,descriptor_binding=dict(table_offset=0,index=2,type=4))
        with self.assertRaisesRegex(ProjectError,'descriptor'):
            verify_rebuilt_maps(bytes(raw),[bad])
        self.assertNotIn('reopened_payload_verified',bad)

    def test_relocated_carrier_and_corruption(self):
        source=bytearray(2048)+bytearray(b'A'*2048+b'B'*2048+b'C'*(2048*8))
        struct.pack_into('<ii',source,4,5,1)
        struct.pack_into('<5I',source,16,1,2,3,4,0)
        source=bytes(source)
        rebuilt,_=replace_physical_entry(source,sha256(source).hexdigest(),0,b'X'*4096)
        audit=dict(map_entry_index=1,relative_offset=17,byte_length=23,result_sha256=sha256(b'B'*23).hexdigest())
        verify_rebuilt_maps(rebuilt,[audit])
        self.assertTrue(audit['reopened_payload_verified'])
        self.assertNotIn('reopened_map_verified',audit)
        bad=bytearray(rebuilt);bad[3*2048+17]^=1
        with self.assertRaisesRegex(ProjectError,'differs'):
            verify_rebuilt_maps(bytes(bad),[audit])
        self.assertNotIn('reopened_payload_verified',audit)


if __name__=='__main__':
    unittest.main()
