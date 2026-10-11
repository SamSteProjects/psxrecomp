"""Retail placed-object selector to kingdom type-5 ANM, never runtime state."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256

from .animation import animation_record_ranges, decode_animation_record, pose_vertices, _bounds
from .core import ImportError


def resolve_object_animation(bind, bank, geometry, frame_index):
    if type(frame_index) is not int or not 0 <= frame_index < 512:
        raise ImportError('World object animation frame must be an integer0..511')
    selector = bind.get('encoded_animation_selector')
    if bind.get('status') != 'resolved_source_header' or type(selector) is not int or selector == 0:
        raise ImportError('World object has no evidenced nonzero animation selector')
    if not 1 <= selector <= 255:
        raise ImportError('World object animation selector must be a native byte')
    ranges = animation_record_ranges(bank)
    index = selector-1
    if index >= len(ranges):
        raise ImportError('World object animation selector exceeds the kingdom ANM bank')
    start, end = ranges[index]
    record = bank[start:end]
    clip = decode_animation_record(record)
    if clip['bone_count'] != len(geometry['objects']):
        raise ImportError('World placed-object animation channels must match every TMD object')
    if frame_index >= clip['frame_count']:
        raise ImportError('World object animation frame exceeds the source clip')
    transforms = clip['frames'][frame_index]['object_transforms']
    vertices = pose_vertices(geometry['vertices'],geometry['objects'],transforms)
    posed = deepcopy(geometry)
    if 'triangle_normals' in geometry:
        normals = geometry['triangle_normals']
        if len(normals) != len(geometry['triangles']):
            raise ImportError('World animation normal layout differs from its source triangles')
        seen = set()
        for obj, transform in zip(geometry['objects'], transforms):
            triangle_start,count = obj['triangle_start'],obj['triangle_count']
            if not 0 <= triangle_start <= triangle_start+count <= len(normals):
                raise ImportError('World animation normal object span exceeds its source')
            for t in range(triangle_start,triangle_start+count):
                if t in seen:
                    raise ImportError('World animation normal object spans overlap')
                seen.add(t)
                if any(not obj['vertex_start'] <= v < obj['vertex_start']+obj['vertex_count'] for v in geometry['triangles'][t]):
                    raise ImportError('World animation triangle crosses its rigid object')
                if normals[t] is not None:
                    posed['triangle_normals'][t] = pose_vertices(normals[t],
                        [dict(object_index=0,vertex_start=0,vertex_count=3)],
                        [dict(object_index=0,translation=[0,0,0],rotation_psx=transform['rotation_psx'])])
        if len(seen) != len(normals):
            raise ImportError('World animation leaves normals without an object owner')
        posed['normal_preview'] = dict(geometry['normal_preview'],status='source_rigid_pose',
            coordinate_system='retail_psx_actor_local_y_down',transform='sdk_analytic_rz_ry_rx')
    posed.update(vertices=vertices,bounds=_bounds(vertices),posed=True,
                 coordinate_system='retail_psx_actor_local_y_down')
    return dict(encoded_selector=selector,record_index=index,byte_offset=start,
        byte_length=end-start,record_sha256=sha256(record).hexdigest(),
        record_base64=b64encode(record).decode('ascii'),bank_base64=b64encode(bank).decode('ascii'),bank_sha256=sha256(bank).hexdigest(),
        bank_record_count=len(ranges),frame_count=clip['frame_count'],
        channel_count=clip['bone_count'],frame_index=frame_index,
        object_transforms=deepcopy(transforms),geometry=posed,
        association='retail_object_header_scene_anm_record_plus_one',
        timing='unresolved',looping='unresolved',runtime_state='not_observed',
        normal_pose='rigid_rotation_only' if 'triangle_normals' in geometry else 'unavailable',rounding='analytic_preview_not_fixed_point_gte')
