"""Static assembled scene GLB, retaining shared meshes and instance provenance."""
from copy import deepcopy
import hashlib
import json
import struct
from .core import ImportError
from .export import encode_model_glb, MAX_GLB_BYTES, _vector


def select_scene_export_instance(scene, entity_id):
    """Keep one verified instance and its shared geometry, without rebasing it."""
    if not isinstance(entity_id,str) or not entity_id or len(entity_id)>512:
        raise ImportError('Choose a valid scene instance identity')
    matches=[entity for entity in scene['entities'] if entity.get('entity_id')==entity_id]
    if len(matches)!=1 or not matches[0].get('renderable'):
        raise ImportError('Selected instance is absent or has no exportable geometry')
    assets=[asset for asset in scene['assets'] if asset.get('geometry_key')==matches[0].get('geometry_key')]
    if len(assets)!=1:raise ImportError('Selected instance geometry is unavailable or ambiguous')
    return {**scene,'entities':deepcopy(matches),'assets':deepcopy(assets),
            'export_scope':'selected-instance','selected_entity_id':entity_id}


def encode_scene_glb(scene):
    if scene.get('schema') != 'legaia.scene-preview.v1' or scene.get('coordinate_system') != 'editor_field_y_up_source_units':
        raise ImportError('Scene export requires a verified scene preview')
    assets, entities = scene.get('assets'), scene.get('entities')
    if not isinstance(assets, list) or not 0<len(assets)<=128 or not isinstance(entities,list) or not 0<len(entities)<=2048:
        raise ImportError('Scene export exceeds geometry or entity bounds')
    doc={'asset':{'version':'2.0','generator':'Legaia SDK assembled scene exporter'},
         'scene':0,'scenes':[{'nodes':[]}],'nodes':[], 'meshes':[], 'materials':[],
         'accessors':[], 'bufferViews':[], 'images':[], 'textures':[], 'samplers':[],
         'extensionsUsed':['KHR_materials_unlit']}
    binary=bytearray(); templates={}; audits=[]
    for asset in assets:
        key=asset.get('geometry_key')
        if not isinstance(key,str) or key in templates:raise ImportError('Duplicate or invalid scene geometry identity')
        preview=deepcopy(asset['preview'])
        if preview.get('coordinate_system')=='actor_local_y_down_source_units':
            preview['coordinate_system']='retail_psx_actor_local_y_down'
        if asset.get('pose_kind')=='source_heightfield':
            if preview.get('coordinate_system')!='retail_field_y_down':raise ImportError('Unsupported terrain coordinates')
            preview.update(schema_version='legaia.model-preview.v1',coordinate_system='retail_tmd_object_local',
                           objects=[{'object_index':0,'vertex_start':0,'vertex_count':len(preview['vertices']),
                                     'triangle_start':0,'triangle_count':len(preview['triangles'])}])
        raw,audit=encode_model_glb(preview)
        size=struct.unpack_from('<I',raw,12)[0]; part=json.loads(raw[20:20+size]); payload=raw[28+size:]
        offsets={name:len(doc[name]) for name in ('meshes','materials','accessors','bufferViews','images','textures','samplers')}
        binary.extend(bytes(-len(binary)%4)); base=len(binary);binary.extend(payload)
        if len(binary)>MAX_GLB_BYTES:raise ImportError('Scene GLB binary exceeds export budget')
        for view in part['bufferViews']:view['byteOffset']=view.get('byteOffset',0)+base
        for accessor in part['accessors']:accessor['bufferView']+=offsets['bufferViews']
        for image in part.get('images',[]):image['bufferView']+=offsets['bufferViews']
        for texture in part.get('textures',[]):
            texture['source']+=offsets['images'];texture['sampler']+=offsets['samplers']
        for material in part['materials']:
            texture=material.get('pbrMetallicRoughness',{}).get('baseColorTexture')
            if texture:texture['index']+=offsets['textures']
        for mesh in part['meshes']:
            for primitive in mesh['primitives']:
                primitive['attributes']={name:index+offsets['accessors'] for name,index in primitive['attributes'].items()}
                primitive['material']+=offsets['materials']
        for name in offsets:doc[name].extend(part.get(name,[]))
        templates[key]=part['nodes']
        for node in templates[key]:
            if 'mesh' in node:node['mesh']+=offsets['meshes']
        audits.append({'geometry_key':key,'audit':audit})
    identifiers=set();unavailable=[]
    for entity in entities:
        identifier=entity.get('entity_id')
        if not isinstance(identifier,str) or identifier in identifiers:raise ImportError('Duplicate or invalid scene entity identity')
        identifiers.add(identifier)
        matrix=_vector(entity.get('model_to_scene'),16,'scene matrix',-1e9,1e9)
        if list(matrix[12:]) != [0,0,0,1]:raise ImportError('Scene transform must be affine')
        # Model export reflects local Y. Undo that reflection before applying
        # the editor-provided transform, which already maps into display space.
        converted=[value*(-1 if i%4==1 else 1) for i,value in enumerate(matrix)]
        node={'name':entity.get('name') or identifier,'matrix':[converted[row*4+col] for col in range(4) for row in range(4)],
              'extras':deepcopy(entity)}
        root=len(doc['nodes']);doc['nodes'].append(node);doc['scenes'][0]['nodes'].append(root)
        if entity.get('renderable'):
            children=templates.get(entity.get('geometry_key'))
            if children is None:raise ImportError('Renderable entity has no exported geometry')
            if len(doc['nodes'])+len(children)>32768:
                raise ImportError('Expanded scene hierarchy exceeds export node budget')
            node['children']=[]
            for child in children:
                node['children'].append(len(doc['nodes']));doc['nodes'].append(deepcopy(child))
        else:unavailable.append({'entity_id':identifier,'reason':entity.get('reason')})
    audit={'schema_version':'legaia.scene-export.v1','scene_id':scene.get('scene_id'),'source_key':scene.get('source_key'),
           'representation':scene.get('representation','authored'),'project_source_key':scene.get('project_source_key'),
           'export_scope':scene.get('export_scope','complete-scene'),'selected_entity_id':scene.get('selected_entity_id'),
           'entity_count':len(entities),'geometry_count':len(assets),'unavailable_entities':unavailable,
           'geometry_exports':audits,'limitations':scene.get('limits',[])+['Static source preview, not runtime state. Unavailable entities retain metadata nodes only.',
            'Source units retained; physical meter scale unknown. Meshes are shared across instances.']}
    for name in ('images','textures','samplers'):
        if not doc[name]:del doc[name]
    doc['extras']=audit;doc['buffers']=[{'byteLength':len(binary)}]
    metadata=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();metadata+=b' '*(-len(metadata)%4)
    total=28+len(metadata)+len(binary)
    if total>MAX_GLB_BYTES:raise ImportError('Scene GLB exceeds export budget')
    raw=struct.pack('<III',0x46546C67,2,total)+struct.pack('<I4s',len(metadata),b'JSON')+metadata+struct.pack('<I4s',len(binary),b'BIN\0')+binary
    return raw,{**audit,'byte_length':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
