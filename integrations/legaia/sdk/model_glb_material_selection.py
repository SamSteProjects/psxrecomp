"""Readonly GLB display-material use mapped through freshly qualified native corners."""
from hashlib import sha256
from importer.animation_glb import _read_glb
from importer.model_glb import _Accessors,CORNER_ID,_integer,source_object_identity
from importer.model_primitives import inspect_model_primitives
from importer.texture_glb_dependencies import inspect_glb_dependencies
from .project import ProjectError,digest
from .scene_preview import source_key
from .model_glb import _prepare


def _qualified(project,asset_id,content,binding,expected_source_key):
    if project.mode!='edit' or not expected_source_key or source_key(project)!=expected_source_key:
        raise ProjectError('GLB material selection requires the current Edit source')
    current,report=_prepare(project,asset_id,content,binding)
    if report['pending_changes'] or sha256(current).hexdigest()!=binding['effective_sha256']:
        raise ProjectError('Apply GLB model changes and export a fresh binding before selecting material faces')
    graph=inspect_glb_dependencies(content)
    result=dict(asset_id=asset_id,scene_id=project.active_scene,project_source_key=expected_source_key,
        effective_sha256=binding['effective_sha256'],glb_sha256=sha256(content).hexdigest(),binding_sha256=digest(binding),
        native_roundtrip_verified=True,read_only=True,project_changed=False)
    if source_key(project)!=expected_source_key:raise ProjectError('Model changed during GLB material qualification')
    return current,graph,result


def links(project,asset_id,content,binding,expected_source_key):
    _,graph,result=_qualified(project,asset_id,content,binding,expected_source_key)
    return dict(result,schema_version='legaia.model-glb-material-links.v1',graph=graph)


def _face_rows(current,content,material_index,object_node_indices=None):
    doc,binary=_read_glb(content);reader=_Accessors(doc,binary);inspection=inspect_model_primitives(current)
    owners={};triangles={}
    explicit={node:obj for obj,node in enumerate(object_node_indices)} if object_node_indices is not None else None
    for node_index,node in enumerate(doc['nodes']):
        if 'mesh' not in node:continue
        # Source identities, mesh ownership, accessor aliases and topology have already
        # passed the existing complete native GLB importer in _qualified.
        object_index=explicit[node_index] if explicit is not None else source_object_identity(node,len(inspection['objects']))
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            corners=reader.read(primitive['attributes'].get(CORNER_ID),1,'source corner IDs')
            indices=[r[0] for r in reader.read(primitive['indices'],1,'indices',True)] if 'indices' in primitive else list(range(len(corners)))
            if len(indices)%3:raise ProjectError('GLB material selection has incomplete triangles')
            for at in range(0,len(indices),3):
                faces=set()
                for index in indices[at:at+3]:
                    _integer(index,0,len(corners)-1,'triangle index');corner=corners[index][0]
                    if corner!=int(corner):raise ProjectError('GLB source corner must be an integer')
                    faces.add(int(corner)//4)
                if len(faces)!=1:raise ProjectError('A GLB triangle crosses native face ownership')
                key=(object_index,faces.pop());owners.setdefault(key,set()).add(primitive.get('material'));triangles[key]=triangles.get(key,0)+1
    rows=[]
    for (obj,face),materials in sorted(owners.items()):
        if material_index not in materials:continue
        row=inspection['objects'][obj]['primitives'][face]
        if triangles[obj,face]!=row['corner_count']-2:raise ProjectError('GLB material face lacks its complete native triangles')
        if len(rows)>=4096:raise ProjectError('GLB material selection exceeds 4096 native faces')
        rows.append(dict(object_index=obj,group_index=row['group_index'],primitive_index=face,textured=row['uvs'] is not None,
            triangle_count=triangles[obj,face],material_indices=sorted(materials,key=lambda m:-1 if m is None else m)))
    return rows


def faces(project,asset_id,content,binding,expected_source_key,material_index,role,image_index):
    current,graph,result=_qualified(project,asset_id,content,binding,expected_source_key)
    if type(material_index) is not int or not 0<=material_index<len(graph['materials']) or type(image_index) is not int:
        raise ProjectError('Choose an exact qualified GLB material and image')
    material=graph['materials'][material_index]
    link=next((l for l in material['links'] if l['role']==role),None)
    if link is None or graph['texture_links'][link['texture_index']]['image_index']!=image_index or not any(i['image_index']==image_index for i in graph['catalog']['images']):
        raise ProjectError('Material channel does not reference this qualified embedded PNG')
    rows=_face_rows(current,content,material_index,binding.get('external_object_nodes'))
    conflicts=sum(r['material_indices']!=[material_index] for r in rows);untextured=sum(not r['textured'] for r in rows)
    result.update(schema_version='legaia.model-glb-material-faces.v1',material_index=material_index,role=role,image_index=image_index,
        texture_index=link['texture_index'],texcoord=link['texcoord'],faces=rows,face_count=len(rows),
        ambiguous_face_count=conflicts,untextured_face_count=untextured,
        can_stage=0<len(rows)<=256 and not conflicts and not untextured,
        limitations=['Native texture page and palette are a separate explicit choice; GLB shader/UV/sampler settings are not imported.',
            'A native quad is indivisible: differing GLB material assignments on its two triangles reject staging.',
            'Untextured native faces require a packet allocation workflow and cannot receive page-binding drafts.',
            'The existing material editor permits at most 256 pending face/group entries per Apply.',
            'These are Current native indices qualified by the fresh SDK export binding; geometry and runtime state are unchanged.'])
    result['selection_key']=digest(result)
    if source_key(project)!=expected_source_key:raise ProjectError('Model changed during native face selection')
    return result
