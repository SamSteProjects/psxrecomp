"""Prove same-layout SDK rigid animation editing in independent Blender.

Run Blender --background --factory-startup --python-exit-code 1 --python this.py
-- INPUT.glb NEW_OUTPUT_DIRECTORY. The source is never modified. A new private
directory receives baseline/edited GLBs, saved Blender scenes and a JSON receipt.
No game is launched or software installed. The proof uses the existing Blender
installation and does not use the SDK animation importer service.

This proof edits object0/frame0 by +1 source X unit and +16 source Rx angle units
(1.40625 degrees). It validates every other exported translation/orientation and
the selected-rate STEP timing, including the terminal hold. It does not establish
retail playback cadence, runtime selection or broader retargeting compatibility.
"""
from pathlib import Path
import hashlib
import json
import math
import stat
import struct
import sys

import bpy
from mathutils import Quaternion


MAX_BYTES = 32 * 1024 * 1024


def read_glb(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('GLB exceeds 32 MiB')
    raw = path.read_bytes()
    if len(raw) < 20 or struct.unpack_from('<III', raw) != (0x46546C67, 2, len(raw)):
        raise ValueError('Invalid GLB header')
    offset, chunks = 12, {}
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise ValueError('Truncated GLB chunk')
        length, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        if kind in chunks or length % 4 or offset + length > len(raw):
            raise ValueError('Invalid GLB chunk extent')
        chunks[kind] = raw[offset:offset + length]
        offset += length
    doc = json.loads(chunks[0x4E4F534A])
    binary = chunks[0x004E4942]
    if (doc.get('asset', {}).get('version') != '2.0' or
            len(doc.get('buffers', [])) != 1 or
            any(item.get('uri') for item in doc.get('buffers', []) + doc.get('images', []))):
        raise ValueError('Choose a self-contained glTF2 GLB')
    return raw, doc, binary


def float_accessor(doc, binary, index, kind):
    accessor = doc['accessors'][index]
    if (accessor.get('componentType') != 5126 or accessor.get('type') != kind or
            accessor.get('sparse') or accessor.get('normalized')):
        raise ValueError('Proof requires ordinary float animation accessors')
    view = doc['bufferViews'][accessor['bufferView']]
    count = accessor['count']
    if type(count) is not int or not 1 <= count <= 4097 or view.get('buffer', 0) != 0:
        raise ValueError('Invalid animation accessor count/buffer')
    components = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[kind]
    width = 4 * components
    stride = view.get('byteStride', width)
    relative = accessor.get('byteOffset', 0)
    start = view.get('byteOffset', 0) + relative
    if (type(stride) is not int or stride < width or stride % 4 or
            relative + (count - 1) * stride + width > view['byteLength'] or
            start + (count - 1) * stride + width > len(binary)):
        raise ValueError('Invalid animation accessor extent')
    rows = [list(struct.unpack_from('<' + 'f' * components, binary, start + i * stride))
            for i in range(count)]
    if any(not math.isfinite(value) for row in rows for value in row):
        raise ValueError('Nonfinite animation value')
    return rows


def tracks(doc, binary, object_indices, count, fps):
    nodes = doc.get('nodes', [])
    parents = {child for node in nodes for child in node.get('children', [])}
    mapped, node_rows = {}, []
    for index, node in enumerate(nodes):
        identity = node.get('extras', {}).get('source_object', {}).get('object_index')
        if type(identity) is not int or identity not in object_indices or identity in mapped:
            raise ValueError('Re-export changed or duplicated explicit source object identity')
        if node.get('name') != f'object-{identity}' or index in parents or node.get('children'):
            raise ValueError('Re-export changed independent object names/parents')
        if node.get('matrix') or any(abs(v - 1) > 1e-6 for v in node.get('scale', [1, 1, 1])):
            raise ValueError('Re-export changed unit-scale independent TRS layout')
        mapped[identity] = index
        node_rows.append({'node_index': index, 'object_index': identity, 'name': node['name'],
                          'source_object_retained': True, 'parent': None,
                          'scale': node.get('scale', [1, 1, 1])})
    if set(mapped) != set(object_indices):
        raise ValueError('Re-export source object set differs')
    animations = doc.get('animations', [])
    if len(animations) != 1:
        raise ValueError(f'Re-export requires one clip, received {len(animations)}')
    animation = animations[0]
    by_node = {value: key for key, value in mapped.items()}
    result, rows = {}, []
    for channel in animation['channels']:
        target = channel['target']
        if target.get('node') not in by_node or target.get('path') not in ('translation', 'rotation'):
            raise ValueError('Unsupported or unmapped re-export animation target')
        key = (by_node[target['node']], target['path'])
        if key in result:
            raise ValueError('Duplicate source-object animation track')
        sampler = animation['samplers'][channel['sampler']]
        if sampler.get('interpolation', 'LINEAR') != 'STEP':
            raise ValueError('Re-export changed source STEP interpolation')
        times = float_accessor(doc, binary, sampler['input'], 'SCALAR')
        values = float_accessor(doc, binary, sampler['output'],
                                'VEC3' if key[1] == 'translation' else 'VEC4')
        if len(times) != count + 1 or len(values) != count + 1 or any(
                abs(row[0] - i / fps) > 2e-6 for i, row in enumerate(times)):
            raise ValueError('Re-export changed selected source-frame timing or terminal sample')
        result[key] = values
        rows.append({'object_index': key[0], 'path': key[1], 'interpolation': 'STEP',
                     'samples': len(times), 'first_seconds': times[0][0],
                     'last_seconds': times[-1][0]})
    if set(result) != {(index, path) for index in object_indices for path in ('translation', 'rotation')}:
        raise ValueError('Re-export omitted existing translation/rotation channels')
    return result, node_rows, sorted(rows, key=lambda row: (row['object_index'], row['path']))


def orientation_error(a, b):
    # q and -q represent the same orientation. Use vector distance after sign
    # alignment, which remains accurate near zero despite float32 export noise.
    a = [value / math.sqrt(sum(v * v for v in a)) for value in a]
    b = [value / math.sqrt(sum(v * v for v in b)) for value in b]
    sign = 1 if sum(x * y for x, y in zip(a, b)) >= 0 else -1
    distance = math.sqrt(sum((x - sign * y) ** 2 for x, y in zip(a, b)))
    return math.degrees(4 * math.asin(min(1, distance / 2)))


def compare(actual, expected):
    translation_error, rotation_error = 0, 0
    for key, values in expected.items():
        for before, after in zip(values, actual[key]):
            if key[1] == 'translation':
                translation_error = max(translation_error, *(abs(x - y) for x, y in zip(before, after)))
            else:
                rotation_error = max(rotation_error, orientation_error(before, after))
    if translation_error > 1e-4 or rotation_error > 1e-4:
        raise ValueError(f'Animation round-trip mismatch: T={translation_error}, R={rotation_error}degrees')
    return {'max_translation_error_source_units': translation_error,
            'max_orientation_error_degrees': rotation_error}


def export(path):
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', export_yup=True,
        export_extras=True, export_animations=True, export_animation_mode='ACTIONS',
        export_force_sampling=False, export_frame_range=True, export_frame_step=1,
        export_optimize_animation_size=False, export_anim_slide_to_zero=False,
        export_nla_strips=False)


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    if len(args) != 2:
        raise ValueError('Expected SDK GLB and a new private output directory')
    source, output = (Path(value).resolve() for value in args)
    raw, doc, binary = read_glb(source)
    audit = doc.get('extras', {})
    count, fps = audit.get('frame_count'), audit.get('export_fps')
    if (audit.get('schema_version') != 'legaia.model-export.v1' or not audit.get('full_clip') or
            audit.get('source_coordinate_system') != 'retail_tmd_object_local' or
            type(count) is not int or not 2 <= count <= 4096 or
            type(fps) not in (int, float) or not math.isfinite(fps) or not 1 <= fps <= 120):
        raise ValueError('Choose an SDK object-local full clip with explicit rate and at least two frames')
    identities = [node['extras']['source_object']['object_index'] for node in doc['nodes']]
    if 0 not in identities or len(identities) * count > 100000:
        raise ValueError('Missing object0 or proof channel budget exceeded')
    original, _, _ = tracks(doc, binary, identities, count, fps)
    source_hash = hashlib.sha256(raw).hexdigest()
    for ancestor in (output, *output.parents):
        if ancestor.exists():
            info = ancestor.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Private output path contains symlink/reparse ancestry')
    output.mkdir(parents=True, exist_ok=False)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.fps = round(fps)
    scene.render.fps_base = round(fps) / fps
    scene.frame_start, scene.frame_end = 0, count
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects = {obj.get('source_object', {}).get('object_index'): obj for obj in scene.objects}
    if set(objects) != set(identities) or any(obj.parent or obj.rotation_mode != 'QUATERNION'
            or any(abs(value - 1) > 1e-6 for value in obj.scale) for obj in objects.values()):
        raise ValueError('Blender import lost independent source-object TRS identity')
    baseline_path = output / 'baseline.glb'
    export(baseline_path)
    baseline_raw, baseline_doc, baseline_binary = read_glb(baseline_path)
    baseline, baseline_nodes, baseline_tracks = tracks(baseline_doc, baseline_binary, identities, count, fps)
    baseline_comparison = compare(baseline, original)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'baseline.blend'))

    scene.frame_set(0)
    obj = objects[0]
    obj.location.x += 1
    # Blender's glTF axis conversion leaves local X unchanged. SDK's Y
    # reflection negates an axial X rotation. Right multiplication therefore
    # edits source Rx alone in the verified Rz*Ry*Rx convention.
    delta = Quaternion((1, 0, 0), -2 * math.pi / 256)
    obj.rotation_quaternion = obj.rotation_quaternion @ delta
    obj.keyframe_insert(data_path='location', index=0, frame=0)
    obj.keyframe_insert(data_path='rotation_quaternion', frame=0)
    curves = []
    for layer in obj.animation_data.action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(obj.animation_data.action_slot)
            for curve in bag.fcurves:
                if curve.data_path in ('location', 'rotation_quaternion'):
                    for point in curve.keyframe_points:
                        point.interpolation = 'CONSTANT'
                    curves.append({'path': curve.data_path, 'axis': curve.array_index,
                                   'points': len(curve.keyframe_points),
                                   'first_frame': curve.keyframe_points[0].co[0],
                                   'last_frame': curve.keyframe_points[-1].co[0]})
    edited_path = output / 'edited.glb'
    export(edited_path)
    edited_raw, edited_doc, edited_binary = read_glb(edited_path)
    edited, edited_nodes, edited_tracks = tracks(edited_doc, edited_binary, identities, count, fps)
    expected = {key: [list(row) for row in values] for key, values in original.items()}
    expected[(0, 'translation')][0][0] += 1
    x, y, z, w = expected[(0, 'rotation')][0]
    quaternion = Quaternion((w, x, y, z)) @ delta
    expected[(0, 'rotation')][0] = [quaternion.x, quaternion.y, quaternion.z, quaternion.w]
    edited_comparison = compare(edited, expected)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'edited.blend'))
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise ValueError('Input GLB changed during proof')
    receipt = {'schema_version': 'legaia.blender-animation-roundtrip.v1',
        'blender': bpy.app.version_string, 'blender_build_hash': bpy.app.build_hash.decode(),
        'source_path': str(source), 'source_sha256': source_hash,
        'asset_id': audit.get('asset_semantic_id'), 'animation': audit.get('animation'),
        'frame_count': count, 'export_fps': fps, 'object_count': len(identities),
        'scene_render_fps': scene.render.fps, 'scene_render_fps_base': scene.render.fps_base,
        'baseline': {'path': str(baseline_path), 'sha256': hashlib.sha256(baseline_raw).hexdigest(),
                     'nodes': baseline_nodes, 'tracks': baseline_tracks, **baseline_comparison},
        'edited': {'path': str(edited_path), 'sha256': hashlib.sha256(edited_raw).hexdigest(),
                   'nodes': edited_nodes, 'tracks': edited_tracks, **edited_comparison},
        'edit': {'object_index': 0, 'frame_index': 0, 'translation_x_delta': 1,
                 'source_rotation_x_delta_psx': 16, 'source_rotation_x_delta_degrees': 1.40625,
                 'keyframes': curves},
        'top_level_sdk_extras_retained': bool(edited_doc.get('extras')),
        'other_channels_unchanged_within_reported_error': True,
        'input_unchanged': True, 'gameplay_verified': False,
        'limitations': ['Caller-selected FPS; no retail cadence inference.',
            'Independent object TRS only; no retargeting or allocation.',
            'Document extras are not an authoritative source binding; use the SDK JSON sidecar.']}
    with (output / 'report.json').open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False)
    print('SDK_ROUNDTRIP_RECEIPT=' + json.dumps({'report_path': str(output / 'report.json'),
        'source_sha256': source_hash, 'baseline_sha256': receipt['baseline']['sha256'],
        'edited_sha256': receipt['edited']['sha256'],
        'baseline_error': baseline_comparison, 'edited_error': edited_comparison}))


if __name__ == '__main__':
    main()
