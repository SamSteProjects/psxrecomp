"""VAB parameter byte ownership and native carrier roundtrip; no playback."""
import os
import struct
import unittest
from hashlib import sha256
from importer.core import ImportError
from importer.audio_bank import bank_from_entry, inspect_bank
from importer.audio_catalog import load_audio_asset_catalog
from importer.audio_bank_authoring import replace_bank_parameters, replace_audio_bank_parameters
from importer.pipeline import _disc_context
from test_audio_bank import source_bank
from test_audio_catalog import chunk, seq


def digest(body):return sha256(body).hexdigest()


def patch(body,edits,current=None):
    current=body if current is None else current
    return replace_bank_parameters(body,current,expected_source_sha256=digest(body),
                                   expected_current_sha256=digest(current),edits=edits)


# Independent expected offsets and packing codes, not the serializer registry.
PARAMETERS=[('header','master_volume',24,'B'),('header','pan',25,'B'),
    ('header','attributes1',26,'B'),('header','attributes2',27,'B'),
    ('program','volume',1,'B'),('program','priority',2,'B'),('program','mode',3,'B'),
    ('program','pan',4,'B'),('program','attributes',6,'H'),
    ('tone','priority',0,'B'),('tone','mode',1,'B'),('tone','volume',2,'B'),
    ('tone','pan',3,'B'),('tone','center',4,'B'),('tone','shift',5,'B'),
    ('tone','minimum_key',6,'B'),('tone','maximum_key',7,'B'),
    ('tone','vibrato_width',8,'B'),('tone','vibrato_time',9,'B'),
    ('tone','portamento_width',10,'B'),('tone','portamento_time',11,'B'),
    ('tone','pitch_bend_down',12,'B'),('tone','pitch_bend_up',13,'B'),
    ('tone','adsr1',16,'H'),('tone','adsr2',18,'H'),
    ('tone','program_operand',20,'h'),('tone','sample_operand',22,'h')]


def edits_and_expected(bank,slot=12,page=0,index=0):
    edits=[];restore=[];expected=bytearray(bank)
    for section,field,relative,code in PARAMETERS:
        identity=({'slot':slot} if section=='program' else {'page':page,'index':index} if section=='tone' else {})
        base=32+slot*16 if section=='program' else 2080+page*512+index*32 if section=='tone' else 0
        before=struct.unpack_from('<'+code,bank,base+relative)[0]
        after=before-1 if before==({'B':255,'H':65535,'h':32767}[code]) else before+1
        edits.append(dict(section=section,field=field,value=after,**identity))
        restore.append(dict(section=section,field=field,value=before,**identity))
        struct.pack_into('<'+code,expected,base+relative,after)
    return edits,bytes(expected),restore


class BankParameters(unittest.TestCase):
    def test_all_27_scalar_fields_preserve_opaque_bytes_and_source_shapes(self):
        body=bytearray(source_bank());body[37]=0xa5;body[40:48]=bytes(range(8));body[2094:2096]=b'\xaa\xbb';body[2104:2112]=bytes(range(8))
        body=bytes(body)+b'bank trailing padding'
        edits,expected,restore=edits_and_expected(body)
        output,audit=patch(body,edits)
        self.assertEqual(output,expected);self.assertEqual(len(audit['edits']),27)
        self.assertEqual(inspect_bank(output)['samples'],inspect_bank(body)['samples'])
        self.assertEqual(inspect_bank(output)['used_program_slots'],[12])
        current_again,_=patch(body,edits,output);self.assertEqual(current_again,output)
        restored,_=patch(body,restore,output);self.assertEqual(restored,body)
        self.assertEqual(audit['changed_bank_byte_offsets'],[i for i,(a,b) in enumerate(zip(body,output)) if a!=b])

    def test_unsigned_and_signed_widths_are_encoded_not_invented_runtime_ranges(self):
        body=source_bank()
        for section,field,identity,valid,invalid in (
            ('header','master_volume',{},[0,255],[-1,256,True,1.5]),
            ('program','attributes',{'slot':127},[0,65535],[-1,65536,False]),
            ('tone','sample_operand',{'page':0,'index':15},[-32768,32767],[-32769,32768,True])):
            for value in valid:patch(body,[dict(section=section,field=field,value=value,**identity)])
            for value in invalid:
                with self.assertRaises(ImportError):patch(body,[dict(section=section,field=field,value=value,**identity)])

    def test_exact_source_identities_and_stale_hashes_reject_atomically(self):
        body=source_bank();edit=dict(section='program',slot=12,field='volume',value=100)
        invalid=[[],[edit]*2,[edit]*257,[dict(**edit,offset=32)],[dict(section='program',slot=True,field='volume',value=1)],
                 [dict(section='program',slot=128,field='volume',value=1)],
                 [dict(section='tone',page=1,index=0,field='pan',value=1)],
                 [dict(section='tone',page=0,index=16,field='pan',value=1)],
                 [dict(section='header',field='program_count',value=1)],
                 [dict(section='program',slot=12,field='tone_count',value=2)],
                 [dict(section='tone',page=0,index=0,field='reserved1',value=2)]]
        for edits in invalid:
            with self.assertRaises(ImportError):patch(body,edits)
        for source_hash,current_hash in (('f'*64,digest(body)),(digest(body),'f'*64)):
            with self.assertRaises(ImportError):replace_bank_parameters(body,body,
                expected_source_sha256=source_hash,expected_current_sha256=current_hash,edits=[edit])
        for position in (28,37,40,2094,2104,2592,3104):
            current=bytearray(body);current[position]^=1
            with self.assertRaises(ImportError):patch(body,[edit],bytes(current))
        self.assertEqual(body,source_bank())

    def test_all_native_carrier_shapes_keep_chunk_headers_samples_sequence_and_padding(self):
        body=source_bank();edits,expected,_=edits_and_expected(body)
        cases=[(body+b'pad',[(0,0,len(body))]),
               (chunk(0,body)+b'opaque tail',[(0,4,len(body))]),
               (chunk(0,body[:3104])+chunk(1,body[3104:])+chunk(2,seq())+b'pad',[(0,4,3104),(3104,3112,16)])]
        for carrier,pieces in cases:
            actual,audit=replace_audio_bank_parameters(carrier,carrier,expected_source_sha256=digest(carrier),
                                                      expected_current_sha256=digest(carrier),edits=edits)
            independent=bytearray(carrier)
            for bank_at,entry_at,size in pieces:independent[entry_at:entry_at+size]=expected[bank_at:bank_at+size]
            self.assertEqual(actual,bytes(independent))
            self.assertEqual(bank_from_entry(actual)[0],expected)
            self.assertEqual(audit['changed_entry_byte_offsets'],[i for i,(a,b) in enumerate(zip(carrier,actual)) if a!=b])
            current=bytearray(actual);current[-1]^=1
            with self.assertRaises(ImportError):replace_audio_bank_parameters(carrier,bytes(current),
                expected_source_sha256=digest(carrier),expected_current_sha256=digest(current),edits=edits)
        # A valid header alone cannot borrow fixed tables or sample bodies.
        with self.assertRaises(ImportError):replace_audio_bank_parameters(body[:32],body[:32],
            expected_source_sha256=digest(body[:32]),expected_current_sha256=digest(body[:32]),edits=edits)

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
    def test_all_202_retail_banks_exact_27_field_edit_and_restore(self):
        disc=os.environ['LEGAIA_DISC_BIN'];catalog=load_audio_asset_catalog(disc,'town01');count=0
        with _disc_context(disc) as (image,_,_,archive):
            for row in catalog['assets']:
                if row['bank_inspection']['status']!='available':continue
                index=row['source_record']['prot_entry_index'];start,end=archive.toc[index+2:index+4]
                carrier=image.read_user(archive.node.extent_lba,start*2048,(end-start)*2048,archive.node.size)
                bank,pieces,_=bank_from_entry(carrier);source=inspect_bank(bank)
                slot=source['used_program_slots'][0];tone=next((t for t in source['tones'] if t['sample_index'] is not None),source['tones'][0])
                edits,expected,restore=edits_and_expected(bank,slot,tone['page'],tone['index'])
                output,_=replace_audio_bank_parameters(carrier,carrier,
                    expected_source_sha256=digest(carrier),expected_current_sha256=digest(carrier),edits=edits)
                native=bytearray(carrier)
                for piece in pieces:
                    at,offset,size=piece['entry_offset'],piece['bank_offset'],piece['size_bytes']
                    native[at:at+size]=expected[offset:offset+size]
                self.assertEqual(output,bytes(native),row['semantic_id'])
                restored,_=replace_audio_bank_parameters(carrier,output,
                    expected_source_sha256=digest(carrier),expected_current_sha256=digest(output),edits=restore)
                self.assertEqual(restored,carrier,row['semantic_id']);count+=1
        self.assertEqual(count,202)


if __name__=='__main__':unittest.main()
