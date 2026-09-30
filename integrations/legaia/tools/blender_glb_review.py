"""Review an SDK GLB in independent Blender, without loading a game or retail disc.

Run Blender --background --factory-startup --python-exit-code 1 --python this.py
-- exported.glb NEW_OUTPUT_DIRECTORY [expected-poses.json]. Outputs are private.
The optional expectations contain source-decoded points in Blender coordinates,
bound to the input SHA256, with samples [{seconds, points}]. No retail timing or
lighting equivalence is inferred. Input files are never modified.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import sys

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


def distance_to(points, targets):
    tree = KDTree(len(targets))
    for index, point in enumerate(targets):
        tree.insert(Vector(point), index)
    tree.balance()
    return max(tree.find(Vector(point))[2] for point in points)


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    if len(args) not in (2, 3):
        raise ValueError('Expected GLB, new output directory and optional pose expectations')
    source, output = Path(args[0]).resolve(), Path(args[1]).resolve()
    if source.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('GLB exceeds the SDK 64 MiB limit')
    raw = source.read_bytes()
    if len(raw) < 20 or struct.unpack_from('<III', raw) != (0x46546C67, 2, len(raw)):
        raise ValueError('Invalid GLB header')
    size, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4E4F534A or size > len(raw) - 20:
        raise ValueError('Missing GLB JSON chunk')
    document = json.loads(raw[20:20 + size])
    if document.get('asset', {}).get('version') != '2.0' or any(
            item.get('uri') for item in document.get('buffers', []) + document.get('images', [])):
        raise ValueError('Choose a self-contained glTF 2.0 GLB with embedded resources')
    audit = document.get('extras', {})
    fps, count = audit.get('export_fps'), audit.get('frame_count')
    if (audit.get('schema_version') != 'legaia.model-export.v1' or not audit.get('full_clip') or type(count) is not int or not 1 <= count <= 4096
            or type(fps) not in (int, float) or not math.isfinite(fps) or not 1 <= fps <= 120):
        raise ValueError('Choose a complete SDK animation export with explicit rate')
    digest = hashlib.sha256(raw).hexdigest()
    if len(args) == 3 and Path(args[2]).stat().st_size > 64 * 1024 * 1024:
        raise ValueError('Expected pose input exceeds 64 MiB')
    expected = json.loads(Path(args[2]).read_text(encoding='utf-8')) if len(args) == 3 else None
    if expected is not None:
        if not isinstance(expected, dict) or expected.get('glb_sha256') != digest:
            raise ValueError('Pose expectations belong to another GLB')
        samples = expected.get('samples')
        if not isinstance(samples, list) or not 1 <= len(samples) <= 8192:
            raise ValueError('Invalid expectation sample count')
        for sample in samples:
            points, seconds = sample.get('points'), sample.get('seconds')
            if (type(seconds) not in (int, float) or not math.isfinite(seconds)
                    or not 0 <= seconds <= count / fps or not isinstance(points, list)
                    or not 1 <= len(points) <= 100000 or any(
                        not isinstance(p, list) or len(p) != 3 or any(
                            type(v) not in (int, float) or not math.isfinite(v) for v in p) for p in points)):
                raise ValueError('Invalid expected pose')
    else:
        samples = [{'seconds': frame / fps} for frame in range(count + 1)]
    # A new directory is required; a rerun cannot overwrite a previous review.
    output.mkdir(parents=True, exist_ok=False)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.render.fps_base = 1
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes or not bpy.data.actions:
        raise ValueError('Blender imported no animated mesh')
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.render.fps_base = 1
    scene.frame_start, scene.frame_end = 0, math.ceil(count / fps * 30)

    def pose(seconds):
        frame = seconds * 30
        scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
        depsgraph = bpy.context.evaluated_depsgraph_get()
        return [list(obj.matrix_world @ vertex.co) for original in meshes
                for obj in [original.evaluated_get(depsgraph)] for vertex in obj.data.vertices]

    if sum(len(s.get('points', [])) for s in samples) > 2000000:
        raise ValueError('Expected poses exceed the two-million-point review budget')
    if sum(len(obj.data.vertices) for obj in meshes) * len(samples) > 2000000:
        raise ValueError('Evaluated poses exceed the two-million-point review budget')
    results, bounds = [], []
    for sample in samples:
        points = pose(sample['seconds'])
        if not points or any(not math.isfinite(v) for point in points for v in point):
            raise ValueError('Blender evaluated empty or nonfinite geometry')
        bounds.extend(points)
        error = None
        if expected is not None:
            error = max(distance_to(points, sample['points']), distance_to(sample['points'], points))
            if error > 0.002:
                raise ValueError(f"Blender pose mismatch at {sample['seconds']} seconds: {error}")
        results.append({'seconds': sample['seconds'], 'vertices': len(points), 'max_point_error': error,
                        'geometry_sha256': hashlib.sha256(json.dumps(points).encode()).hexdigest()})
    low = Vector([min(p[i] for p in bounds) for i in range(3)])
    high = Vector([max(p[i] for p in bounds) for i in range(3)])
    center, radius = (low + high) / 2, max((high - low).length / 2, 1)
    bpy.ops.object.camera_add(location=center + Vector((1.8, -2.8, 1.4)) * radius)
    camera = bpy.context.object
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = radius * 2.6
    scene.camera = camera
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.world.color = (0.06, 0.06, 0.06)
    scene.view_settings.view_transform = 'Standard'
    # Studio lights also make non-unlit consumer materials inspectable.
    for offset, energy in [((2, -3, 4), 1000), ((-3, -1, 2), 500)]:
        bpy.ops.object.light_add(type='SUN', location=center + Vector(offset) * radius)
        light = bpy.context.object
        light.rotation_euler = (center - light.location).to_track_quat('-Z', 'Y').to_euler()
        light.data.energy = energy / 500
    rendered = []
    for index in sorted(set((0, count // 2, count - 1))):
        pose(index / fps)
        path = output / f'frame-{index:04d}.png'
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path))
    scene.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'review.blend'))
    report = {'source': str(source), 'sha256': digest, 'blender': bpy.app.version_string,
              'asset_id': audit.get('asset_semantic_id'), 'frame_count': count,
              'export_fps': fps, 'mesh_objects': len(meshes), 'samples': results,
              'expected_pose_comparison': expected is not None, 'renders': rendered,
              'limits': ['Caller-selected timing; no retail cadence or lighting equivalence',
                         'One imported GLB; no gameplay or full scene parity acceptance']}
    (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValueError('Input changed during review')


if __name__ == '__main__':
    main()
