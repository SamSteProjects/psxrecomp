"""Compose V7 native geometry with evidenced pose channels and explicit unposed objects."""
from copy import deepcopy
from hashlib import sha256
from .core import ImportError
from .assets import decode_tmd
from .model_primitives import _qualified_model
from .model_face_ledger import _operations
from .animation import pose_vertices,_bounds


def preview_object_model(preview,replacement,binding):
    _qualified_model(replacement);shape=decode_tmd(replacement)
    if binding.get('asset_sha256')!=sha256(replacement).hexdigest() or binding.get('byte_length')!=len(replacement):
        raise ImportError('Object allocation preview differs from its qualified binding')
    operations=_operations(binding['ledger']);previous=preview.get('authored_shape',{})
    if not operations or operations[-1]['proposed_sha256']!=binding['asset_sha256']:
        raise ImportError('Object preview differs from the ledger operation chain')
    old_operations=[]
    if previous.get('format')=='tmd-face-addition-v1':
        old=previous['ledger'];old_operations=_operations(old)
        if (any(old[key]!=binding['ledger'][key] for key in ('source_sha256','source_byte_length'))
                or old_operations!=operations[:len(old_operations)]
                or previous.get('asset_sha256')!=(old_operations[-1]['proposed_sha256'] if old_operations else old['source_sha256'])):
            raise ImportError('Object preview is not a continuation of its Current ledger')
    clone_count=sum(len(op['requests']) for op in operations if op['kind']=='allocate_objects')
    old_clone_count=sum(len(op['requests']) for op in old_operations if op['kind']=='allocate_objects')
    old_native_count=len(shape['objects'])-clone_count+old_clone_count
    if old_native_count<1 or len(preview['objects'])>old_native_count:
        raise ImportError('Object preview changed its preceding native object ownership')
    growth=[0]*len(shape['objects'])
    for op in operations[len(old_operations):]:
        if op['kind']=='allocate_vectors':
            for request in op['requests']:
                if request['kind']=='vertices':growth[request['object_index']]+=len(request['vectors'])
    count=0
    for owner,obj in enumerate(preview['objects']):
        if (obj['object_index']!=owner or obj['vertex_start']!=count
                or shape['objects'][owner]['vertex_count']!=obj['vertex_count']+growth[owner]):
            raise ImportError('Object preview changed an existing object vertex/channel layout')
        count+=obj['vertex_count']
    if count!=len(preview['vertices']):raise ImportError('Object preview source has incomplete vector ownership')
    result=deepcopy(preview);result['objects']=deepcopy(shape['objects'])
    for key in ('vertices','triangles','triangle_colors','triangle_uvs','triangle_materials','triangle_normals','materials','normal_preview'):
        result[key]=deepcopy(shape[key])
    transforms=result.get('pose',{}).get('object_transforms')
    frames=result.get('frames',[])
    if result.get('posed') and transforms is None and not frames:
        raise ImportError('Object preview requires explicit source pose transforms')
    def compose(values):
        if not isinstance(values,list) or len(values)>min(len(preview['objects']),len(shape['objects'])-clone_count):
            raise ImportError('Object preview cannot infer pose channels for new native objects')
        if result.get('posed') and not values:
            raise ImportError('Object preview has no evidenced source pose channels')
        owners=shape['objects'][:len(values)];prefix=sum(obj['vertex_count'] for obj in owners)
        return pose_vertices(shape['vertices'][:prefix],owners,values)+deepcopy(shape['vertices'][prefix:])
    if transforms is not None:result['vertices']=compose(transforms)
    for frame in frames:
        frame['vertices']=compose(frame['object_transforms']);frame['bounds']=_bounds(frame['vertices'])
    known=len(transforms) if transforms is not None else len(frames[0]['object_transforms']) if frames else 0
    if any(len(frame['object_transforms'])!=known for frame in frames):
        raise ImportError('Object preview frames changed the evidenced pose channel prefix')
    result['unposed_object_indices']=list(range(known,len(shape['objects'])))
    result['pose_scope']='verified_existing_channels_with_explicit_unposed_native_objects' if known else 'unposed_native_objects'
    result['bounds']=_bounds(result['vertices']);result['textures']=[]
    result.pop('texture_catalog',None);result.pop('texture_scope',None)
    result['representation']='authored-shape';result['authored_shape']=deepcopy(binding)
    return result
