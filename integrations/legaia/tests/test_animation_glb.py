"""Numerical and malformed-file proofs for bounded rigid-channel GLB import."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.animation import decode_animation_record
from importer.animation_authoring import patch_animation_channels, replace_animation_record
from importer.animation_glb import import_animation_glb
from importer.core import ImportError
from importer.export import encode_model_glb


def record(frames):
    """Independent packer: rotations are byte ticks, opaque nibble varies."""
    body = bytearray(struct.pack('<4H', 0x100 | len(frames[0]), len(frames), 0x080C, 4))
    for fi, channels in enumerate(frames):
        for oi, (translation, rotation) in enumerate(channels):
            x, y, z = [v & 0xFFF for v in translation]
            body.extend((x & 255, y & 255, (x >> 8) | ((y >> 8) << 4),
                         z & 255, (((fi + oi) % 16) << 4) | (z >> 8), *rotation))
    return bytes(body) + bytes(8)


def quaternion(ticks, reflect=True):
    # Compose Hamilton qz*qy*qx independently of the reader's trig expression.
    def multiply(a, b):
        x, y, z, w = a; bx, by, bz, bw = b
        return [w*bx + x*bw + y*bz - z*by,
                w*by - x*bz + y*bw + z*bx,
                w*bz + x*by - y*bx + z*bw,
                w*bw - x*bx - y*by - z*bz]
    x, y, z = [v * math.pi / 256 for v in ticks]
    q = multiply(multiply([0, 0, math.sin(z), math.cos(z)],
                          [0, math.sin(y), 0, math.cos(y)]),
                 [math.sin(x), 0, 0, math.cos(x)])
    return [-q[0], q[1], -q[2], q[3]] if reflect else q


def encode(doc, payload):
    doc = deepcopy(doc)
    doc['buffers'] = [{'byteLength': len(payload)}]
    raw = json.dumps(doc, separators=(',', ':'), allow_nan=False).encode()
    raw += b' ' * (-len(raw) % 4)
    binary = payload + bytes(-len(payload) % 4)
    return struct.pack('<3I', 0x46546c67, 2, 28 + len(raw) + len(binary)) + \
        struct.pack('<2I', len(raw), 0x4e4f534a) + raw + \
        struct.pack('<2I', len(binary), 0x004e4942) + binary


def document(frames, fps=15, *, mode='STEP', terminal=True, negative=False):
    doc = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': []}],
           'nodes': [], 'bufferViews': [], 'accessors': [],
           'animations': [{'samplers': [], 'channels': []}]}
    payload = bytearray()

    def accessor(values, shape):
        offset = len(payload)
        width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[shape]
        payload.extend(b''.join(struct.pack(f'<{width}f', *value) for value in values))
        vi = len(doc['bufferViews'])
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(payload)-offset})
        ai = len(doc['accessors'])
        doc['accessors'].append({'bufferView': vi, 'componentType': 5126, 'count': len(values), 'type': shape})
        return ai

    times = [[i/fps] for i in range(len(frames) + int(terminal))]
    ti = accessor(times, 'SCALAR')
    for oi in range(len(frames[0])):
        translations = [[t[0], -t[1], t[2]] for t, _ in (frame[oi] for frame in frames)]
        rotations = [quaternion(r) for _, r in (frame[oi] for frame in frames)]
        if negative:
            rotations = [[-v for v in q] for q in rotations]
        node = {'name': f'object-{oi}', 'extras': {'source_object': {'object_index': oi}},
                'translation': translations[0], 'rotation': rotations[0]}
        doc['scenes'][0]['nodes'].append(oi); doc['nodes'].append(node)
        if terminal:
            translations.append(translations[-1]); rotations.append(rotations[-1])
        for path, values, shape in [('translation', translations, 'VEC3'), ('rotation', rotations, 'VEC4')]:
            ai = accessor(values, shape)
            samplers = doc['animations'][0]['samplers']
            si = len(samplers); samplers.append({'input': ti, 'output': ai, 'interpolation': mode})
            doc['animations'][0]['channels'].append({'sampler': si, 'target': {'node': oi, 'path': path}})
    return doc, bytes(payload)


def changed_key(doc, payload, path, frame, values, obj=0):
    channel = next(c for c in doc['animations'][0]['channels'] if c['target'] == {'node': obj, 'path': path})
    sampler = doc['animations'][0]['samplers'][channel['sampler']]
    accessor = doc['accessors'][sampler['output']]
    view = doc['bufferViews'][accessor['bufferView']]
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0) + frame*len(values)*4
    result = bytearray(payload)
    struct.pack_into(f'<{len(values)}f', result, offset, *values)
    return bytes(result)


class AnimationGlbTests(unittest.TestCase):
    def test_every_angle_byte_noop_and_negative_quaternion_keeps_opaque_source(self):
        frames = [[([i-128, 127-i, i%9], [i, (i*37)%256, (i*71)%256])] for i in range(256)]
        # Add both gimbal signs, source branches beyond 90 degrees, and wraps.
        frames += [[([0,0,0], angles)] for angles in ([51,64,13], [51,192,13], [170,115,190], [255,255,255])]
        source = record(frames)
        for negative in (False, True):
            with self.subTest(negative=negative):
                doc, payload = document(frames, fps=29.97, negative=negative)
                changed, report = import_animation_glb(source, encode(doc,payload), fps=29.97)
                self.assertEqual(changed, source)
                self.assertEqual(report['changes'], [])
                self.assertEqual(report['quantization']['preserved_rotation_channels'], len(frames))
                self.assertLess(report['maximum_angular_error_degrees'], 0.0001)

    def test_exact_edit_full_byte_coverage_source_fields_and_detached_report(self):
        frames = [[([10,-20,30], [16,32,48])], [([11,-21,31], [17,33,49])]]
        source = record(frames); doc,payload = document(frames)
        payload = changed_key(doc,payload,'translation',1,[100,200,-300])
        payload = changed_key(doc,payload,'rotation',1,quaternion([18,33,49]))
        changed,report = import_animation_glb(source,encode(doc,payload),fps=15)
        expected,audit = patch_animation_channels(source,hashlib.sha256(source).hexdigest(),
            [{'frame_index':1,'object_index':0,'translation':{'x':100,'y':-200,'z':-300},'rotation_psx':{'x':288}}])
        self.assertEqual(changed,expected);self.assertEqual(report['changes'],audit)
        self.assertEqual(replace_animation_record(source,hashlib.sha256(source).hexdigest(),changed),(changed,audit))
        self.assertEqual(changed[20] & 0xf0,source[20] & 0xf0)
        self.assertEqual(report['changed_axes'],4)
        self.assertEqual(report['candidate_sha256'],hashlib.sha256(changed).hexdigest())
        report['changes'].clear()
        self.assertEqual(len(import_animation_glb(source,encode(doc,payload),fps=15)[1]['changes']),4)

    def test_accessor_order_and_relative_offsets_do_not_imply_channel_order(self):
        frames = [[([1,2,3],[5,115,200]),([4,5,6],[240,50,17])]]
        source=record(frames);doc,payload=document(frames)
        old=deepcopy(doc['accessors']); count=len(old)
        doc['accessors']=old[::-1]
        for sampler in doc['animations'][0]['samplers']:
            sampler['input']=count-1-sampler['input'];sampler['output']=count-1-sampler['output']
        doc['animations'][0]['channels'].reverse()
        # Use a nonzero accessor offset within a larger view for the first vector.
        vector=next(a for a in doc['accessors'] if a['type']=='VEC3')
        view=doc['bufferViews'][vector['bufferView']]
        view['byteOffset']-=4;view['byteLength']+=4;vector['byteOffset']=4
        self.assertEqual(import_animation_glb(source,encode(doc,payload),fps=15)[0],source)

    def test_linear_shortest_slerp_static_components_and_terminal_hold(self):
        source=record([[([0,0,0],[0,0,0])]]*5)
        doc,payload=document([[([0,0,0],[0,0,0])],[([8,0,0],[0,0,64])]],fps=2,mode='LINEAR',terminal=False)
        # q/-q endpoints must interpolate the same shortest rotation.
        payload=changed_key(doc,payload,'rotation',1,[-v for v in quaternion([0,0,64])])
        changed,report=import_animation_glb(source,encode(doc,payload),fps=4)
        values=decode_animation_record(changed)['frames']
        self.assertEqual([f['object_transforms'][0]['translation'][0] for f in values],[0,4,8,8,8])
        self.assertEqual([f['object_transforms'][0]['rotation_psx'][2] for f in values],[0,512,1024,1024,1024])
        self.assertLess(report['maximum_angular_error_degrees'],0.0001)
        doc['animations'][0]['channels']=[c for c in doc['animations'][0]['channels'] if c['target']['path']=='rotation']
        doc['nodes'][0]['translation']=[5,-6,7]
        changed,_=import_animation_glb(source,encode(doc,payload),fps=4)
        self.assertEqual([f['object_transforms'][0]['translation'] for f in decode_animation_record(changed)['frames']],[[5,6,7]]*5)
        del doc['animations'];doc['nodes'][0]['rotation']=quaternion([0,0,32])
        changed,_=import_animation_glb(source,encode(doc,payload),fps=4)
        self.assertEqual([f['object_transforms'][0]['rotation_psx'] for f in decode_animation_record(changed)['frames']],[[0,0,512]]*5)

    def test_step_uses_exact_key_and_prior_value_between_keys(self):
        source=record([[([0,0,0],[0,0,0])]]*4)
        doc,payload=document([[([0,0,0],[0,0,0])],[([8,0,0],[0,0,64])]],fps=2,terminal=False)
        changed,_=import_animation_glb(source,encode(doc,payload),fps=4)
        self.assertEqual([f['object_transforms'][0]['translation'][0] for f in decode_animation_record(changed)['frames']],[0,0,8,8])

    def test_translation_rounding_and_raw_overflow_are_explicit(self):
        source=record([[([0,0,0],[0,0,0])]])
        doc,payload=document([[([0,0,0],[0,0,0])]])
        del doc['animations'];doc['nodes'][0]['translation']=[0.5,0.5,-0.5]
        changed,report=import_animation_glb(source,encode(doc,payload),fps=1)
        self.assertEqual(decode_animation_record(changed)['frames'][0]['object_transforms'][0]['translation'],[1,-1,-1])
        self.assertEqual(report['maximum_translation_error'],0.5)
        for value in (2047.01,-2048.01,1e20):
            doc['nodes'][0]['translation']=[value,0,0]
            with self.subTest(value=value),self.assertRaisesRegex(ImportError,'before quantization'):
                import_animation_glb(source,encode(doc,payload),fps=1)

    def test_regular_branches_gimbal_and_near_gimbal_are_source_biased(self):
        cases=[([170,115,190],[171,115,190]),([51,64,13],[53,64,13]),
               ([51,192,13],[53,192,13]),([100,63,200],[101,63,200]),
               ([255,10,30],[0,10,30])]
        for before,after in cases:
            with self.subTest(before=before):
                source=record([[([0,0,0],before)]])
                doc,payload=document([[([0,0,0],after)]])
                changed,report=import_animation_glb(source,encode(doc,payload),fps=15)
                actual=[v//16 for v in decode_animation_record(changed)['frames'][0]['object_transforms'][0]['rotation_psx']]
                self.assertLess(report['maximum_angular_error_degrees'],0.0001)
                if before[1] not in (64,192):self.assertEqual(actual,after)
                else:
                    self.assertEqual(actual[1],before[1])
                    self.assertLessEqual(abs(actual[0]-before[0]),2)
                    self.assertLessEqual(abs(actual[2]-before[2]),2)
                    sign=1 if before[1]==64 else -1
                    self.assertEqual((actual[0]-sign*actual[2])%256,(after[0]-sign*after[2])%256)
        # Arbitrary non-grid orientation must stay within the documented bound.
        source=record([[([0,0,0],[23,250,99])]])
        doc,payload=document([[([0,0,0],[24.37,251.41,100.29])]])
        changed,report=import_animation_glb(source,encode(doc,payload),fps=15)
        self.assertNotEqual(changed,source)
        self.assertLessEqual(report['maximum_angular_error_degrees'],2.2)

    def test_identity_ancestors_are_allowed_but_transformed_or_mapped_parents_reject(self):
        frames=[[([0,0,0],[0,0,0]),([0,0,0],[0,0,0])]]
        source=record(frames);doc,payload=document(frames)
        doc['nodes'].append({'name':'collection','children':[0,1],'matrix':[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]})
        doc['scenes'][0]['nodes']=[2]
        self.assertEqual(import_animation_glb(source,encode(doc,payload),fps=15)[0],source)
        invalid=[]
        changed=deepcopy(doc);del changed['nodes'][2]['matrix'];changed['nodes'][2]['translation']=[1,0,0];invalid.append(changed)
        changed=deepcopy(doc);changed['nodes'][2]['children']=[0];changed['nodes'][0]['children']=[1];invalid.append(changed)
        changed=deepcopy(doc);changed['nodes'][1]['children']=[2];invalid.append(changed)
        changed=deepcopy(doc);changed['nodes'][0]['children']=[1];invalid.append(changed)
        # Earlier-visited identity intermediates cannot conceal a mapped ancestor.
        changed=deepcopy(doc);changed['nodes'][2].pop('matrix');changed['nodes'][2]['children']=[1]
        changed['nodes'][0]['children']=[2];changed['scenes'][0]['nodes']=[0];invalid.append(changed)
        changed=deepcopy(doc);changed['nodes'][0]['extras']['source_object']['object_index']=1;invalid.append(changed)
        changed=deepcopy(doc);changed['nodes'][1]['name']='object-0';invalid.append(changed)
        for changed in invalid:
            with self.assertRaises(ImportError):import_animation_glb(source,encode(changed,payload),fps=15)

    def test_malformed_accessors_times_payloads_and_unsupported_channels_reject(self):
        source=record([[([0,0,0],[0,0,0])]]*2)
        doc,payload=document([[([0,0,0],[0,0,0])]]*2)
        mutations=[]
        def mutate(change):
            value=deepcopy(doc);change(value);mutations.append(value)
        mutate(lambda d:d['bufferViews'][0].update(byteStride=4))
        mutate(lambda d:d['bufferViews'][0].update(buffer=True))
        mutate(lambda d:d['bufferViews'][0].update(byteOffset=1))
        mutate(lambda d:d['bufferViews'][0].update(byteLength=len(payload)+1))
        mutate(lambda d:d['accessors'][0].update(sparse={}))
        mutate(lambda d:d['accessors'][0].update(componentType=5123))
        mutate(lambda d:d['accessors'][0].update(count=65537))
        mutate(lambda d:d['accessors'][0].update(byteOffset=99999))
        mutate(lambda d:d['animations'][0]['samplers'][0].update(interpolation='CUBICSPLINE'))
        mutate(lambda d:d['animations'][0]['samplers'][0].update(output=0))
        mutate(lambda d:d['animations'][0]['channels'][0]['target'].update(path='scale'))
        mutate(lambda d:d['animations'][0]['channels'][0]['target'].update(node=True))
        mutate(lambda d:d['animations'][0]['channels'].append(deepcopy(d['animations'][0]['channels'][0])))
        mutate(lambda d:d['nodes'][0].update(rotation=[0,0,0,0]))
        mutate(lambda d:d['nodes'][0].update(scale=[1,2,1]))
        mutate(lambda d:d['nodes'][0].update(matrix=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]))
        mutate(lambda d:d['nodes'][0].update(skin=0))
        mutate(lambda d:d['nodes'][0].update(weights=[]))
        mutate(lambda d:d.update(extensionsRequired=['KHR_materials_unlit']))
        mutate(lambda d:d.update(extensionsUsed=['EXT_animation_pointer']))
        mutate(lambda d:d.update(extensions={'EXT_foo':{}}))
        mutate(lambda d:d.update(extensions=None))
        mutate(lambda d:d['animations'][0].update(extensions={'EXT_foo':{}}))
        mutate(lambda d:d['animations'].append(deepcopy(d['animations'][0])))
        for invalid in mutations:
            with self.subTest(invalid=invalid),self.assertRaises(ImportError):
                import_animation_glb(source,encode(invalid,payload),fps=15)
        for times in ([0,0,1],[-1,0,1],[0,2,1],[0,1,2]):
            bad=bytearray(payload);struct.pack_into('<3f',bad,0,*times)
            with self.assertRaises(ImportError):import_animation_glb(source,encode(doc,bytes(bad)),fps=15)
        bad=bytearray(payload);struct.pack_into('<f',bad,0,float('nan'))
        with self.assertRaises(ImportError):import_animation_glb(source,encode(doc,bytes(bad)),fps=15)
        bad=changed_key(doc,payload,'rotation',0,[0,0,0,2])
        with self.assertRaises(ImportError):import_animation_glb(source,encode(doc,bad),fps=15)

    def test_glb_container_json_external_buffer_and_rate_bounds(self):
        frames=[[([0,0,0],[0,0,0])]];source=record(frames);doc,payload=document(frames);good=encode(doc,payload)
        for raw in (bytearray(good),good[:-1],good+b'\0',good[:20],b'',b'glTF'+good[4:8]+bytes(4)+good[12:]):
            with self.assertRaises(ImportError):import_animation_glb(source,raw,fps=15)
        text=json.dumps(doc).encode();text=text.replace(b'"asset":',b'"asset": {"version":"2.0"}, "asset":',1)
        text+=b' '*(-len(text)%4)
        duplicate=struct.pack('<3I',0x46546c67,2,28+len(text)+len(payload))+struct.pack('<2I',len(text),0x4e4f534a)+text+struct.pack('<2I',len(payload),0x004e4942)+payload
        with self.assertRaisesRegex(ImportError,'duplicate'):import_animation_glb(source,duplicate,fps=15)
        for fps in (True,0,121,float('nan'),float('inf'),'15'):
            with self.assertRaises(ImportError):import_animation_glb(source,good,fps=fps)
        with self.assertRaises(ImportError):import_animation_glb(bytearray(source),good,fps=15)
        too_many=record([[([0,0,0],[0,0,0])]*9]*512)
        with self.assertRaisesRegex(ImportError,'4096'):import_animation_glb(too_many,good,fps=15)
        # Rewrite the container directly: URI presence rejects even for a BIN GLB.
        doc['buffers']=[{'byteLength':len(payload),'uri':'external.bin'}]
        text=json.dumps(doc).encode();text+=b' '*(-len(text)%4)
        external=struct.pack('<3I',0x46546c67,2,28+len(text)+len(payload))+struct.pack('<2I',len(text),0x4e4f534a)+text+struct.pack('<2I',len(payload),0x004e4942)+payload
        with self.assertRaisesRegex(ImportError,'external'):import_animation_glb(source,external,fps=15)

    def test_sdk_full_model_export_mesh_material_context_roundtrips(self):
        frames=[[([i,-i,3],[i,115,17])] for i in range(30)]
        source=record(frames)
        preview={'schema_version':'legaia.model-preview.v1','coordinate_system':'retail_tmd_object_local',
                 'vertices':[[0,0,0],[1,0,0],[0,1,0]],'triangles':[[0,1,2]],
                 'triangle_colors':[[[128,128,128]]*3],'triangle_uvs':[None],'triangle_materials':[0],
                 'materials':[{'textured':False,'semi_transparent':False}],
                 'objects':[{'object_index':0,'vertex_start':0,'vertex_count':3,'triangle_start':0,'triangle_count':1}],
                 'frames':decode_animation_record(source)['frames']}
        raw,_=encode_model_glb(preview,clip_fps=15)
        self.assertEqual(import_animation_glb(source,raw,fps=15)[0],source)


if __name__=='__main__':unittest.main()
