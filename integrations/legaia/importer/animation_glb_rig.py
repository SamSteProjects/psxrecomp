"""Qualify an explicitly selected joint rig for rigid-motion extraction only."""
from .core import ImportError


def qualify_joint_rig(doc, mapping, parents, reachable, accessors, skin_index):
    from .animation_glb import _array, _object, _integer
    skins = _array(doc.get('skins'), 'rig skins', 64)
    skin_index = _integer(skin_index, 0, len(skins)-1, 'selected rig skin')
    skin = _object(skins[skin_index], 'selected rig skin')
    joints = _array(skin.get('joints'), 'skin joints', 4096)
    if not joints: raise ImportError('Selected rig skin has no joints')
    for joint in joints: _integer(joint, 0, len(doc['nodes'])-1, 'joint node')
    if len(set(joints)) != len(joints) or not set(joints) <= reachable:
        raise ImportError('Rig joints must be distinct and reachable in the selected scene')
    if not set(mapping.values()) <= set(joints):
        raise ImportError('Explicit rig mapping must choose only joints from the selected skin')
    paths = []; budget = 0
    for joint in joints:
        path = []; current = joint
        while current is not None:
            path.append(current); budget += 1
            if budget > 65536: raise ImportError('Joint rig exceeds bounded ancestry work')
            current = parents.get(current)
        paths.append(path)
    common = set(paths[0])
    for path in paths[1:]: common.intersection_update(path)
    if not common: raise ImportError('Selected skin joints have no common scene root')
    common_root = next(index for index in paths[0] if index in common)
    if 'skeleton' in skin:
        skeleton = _integer(skin['skeleton'], 0, len(doc['nodes'])-1, 'skin skeleton node')
        if skeleton not in common: raise ImportError('Skin skeleton must be an ancestor of every selected joint')
    meshes = _array(doc.get('meshes'), 'rig meshes', 4096); instances = []
    for index, node in enumerate(doc['nodes']):
        if 'skin' not in node: continue
        selected = _integer(node['skin'], 0, len(skins)-1, 'node skin index')
        if selected != skin_index: continue
        _integer(node.get('mesh'), 0, len(meshes)-1, 'skinned mesh index')
        if index in mapping.values(): raise ImportError('A mapped joint cannot also be a skinned mesh instance')
        if index in reachable: instances.append(index)
    if not instances: raise ImportError('Selected skin has no mesh instance in the selected scene')
    inverse = skin.get('inverseBindMatrices'); count = 0
    if 'inverseBindMatrices' in skin:
        _integer(inverse, 0, len(accessors.rows)-1, 'inverse bind accessor')
        count = _integer(_object(accessors.rows[inverse], 'inverse bind accessor').get('count'), len(joints), 4096, 'inverse bind matrix count')
        values = accessors.read(inverse, 'MAT4')
        if any([row[i] for i in (3,7,11,15)] != [0,0,0,1] for row in values):
            raise ImportError('Inverse bind matrices require an affine final row')
    return dict(skin_index=skin_index, joint_nodes=list(joints), mapped_joint_nodes=list(mapping.values()),
                common_root_node=common_root, skin_mesh_nodes=instances, inverse_bind_accessor=inverse,
                inverse_bind_count=count, mesh_skinning_applied=False, scope='rigid-joint-motion-only')
