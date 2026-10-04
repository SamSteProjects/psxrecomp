"""One reviewed mesh import publishes vector and face allocation atomically."""
from hashlib import sha256
from uuid import UUID
from importer.model_mesh_append import decode_append_mesh
from importer.model_face_ledger import append_vector_ledger,append_face_ledger,append_group_ledger,append_removal_ledger
from importer.model_primitives import inspect_model_primitives
from importer.assets import decode_tmd
from .model_face_addition import _context,_budget,FORMAT
from .scene_preview import source_key
from .project import ProjectError,digest


def source(project,asset_id,expected_key):
    from .model_group_allocation import source as group_source
    from importer.model_face_removal import _groups
    from importer.model_primitives import _qualified_model
    report=group_source(project,asset_id,expected_key)
    _,_,base,_,_,audit=_context(project,asset_id,expected_key)
    next_indices=[0]*len(report['objects'])
    for owner,*_ in _groups(base,_qualified_model(base)[0]):next_indices[owner]+=1
    for row in audit.get('allocated_groups',[]):
        next_indices[row['object_index']]=max(next_indices[row['object_index']],row['origin_group_index']+1)
    report['next_group_origin_indices']=next_indices
    if source_key(project)!=expected_key:raise ProjectError('Project changed during mesh append inspection')
    return report

LIMITATIONS=[
    'Imports static standard GLB POSITION and triangle lists, strips or fans into the selected donor object in native source units.',
    'Reflects Y and reverses triangle winding; rounds positions to signed integer native coordinates.',
    'GLB NORMAL directions are normalized, reflected in Y and converted to Q12 stored normals for lit packets. Flat donors require equal corner normals.',
    'Mesh UVs map to the Current UV region of the selected native texture binding, using texel centers and clamped crop edges. Wrapping outside 0..1 is unsupported.',
    'Unlit packets import mesh colors. Textured RGB maps linear modulation to neutral 128; untextured RGB converts linear glTF colors to display-referred byte RGB. Flat donors require equal corner colors.',
    'Packet flags/materials are inherited. Missing attributes retain donor values. Vertex alpha other than 1 is not representable in baked RGB; lit packets ignore mesh colors.',
    'Other GLB display attributes, materials and images are not imported. No external resources are fetched.',
    'Apply object transforms before export. One scene, one mesh node and no skinning, morph targets or animation.',
    'Appends geometry; it does not replace retained faces or create native objects or packet groups. Gameplay remains unverified.',
]


def prepare(project,asset_id,content,donor_face_id,expected_sha256,expected_key,*,new_group=False,replace_group=False):
    if type(new_group) is not bool or type(replace_group) is not bool:
        raise ProjectError('Mesh packet-group choice must be boolean')
    if replace_group and not new_group:
        raise ProjectError('Mesh group replacement requires an independent new group')
    original,effective,base,base_binding,ledger,topology=_context(project,asset_id,expected_key)
    if sha256(effective).hexdigest()!=expected_sha256:
        raise ProjectError('Model changed since mesh append inspection')
    if not isinstance(donor_face_id,str):raise ProjectError('Mesh append requires a stable donor identity')
    donor=next((face for face in topology['faces'] if face['face_id']==donor_face_id),None)
    if donor is None:raise ProjectError('Mesh append donor is absent from Current topology')
    objects=inspect_model_primitives(effective,include_normal_references=True)['objects']
    obj=objects[donor['object_index']]
    row=obj['primitives'][donor['current_primitive_index']]
    if row['corner_count']!=3:raise ProjectError('Select a native triangle donor for a triangle mesh')
    geometry=decode_append_mesh(content)
    normals=[];references=[];imported_faces=0
    for directions in geometry['triangle_normals']:
        if row['normal_indices'] is None or directions is None:
            references.append(None);continue
        if not row['gouraud'] and directions[1:]!=[directions[0],directions[0]]:
            raise ProjectError('Flat triangle donor cannot represent different corner normals; select a Gouraud donor')
        indices=[]
        for direction in directions if row['gouraud'] else directions[:1]:
            if direction not in normals:normals.append(direction)
            indices.append(obj['normal_count']+normals.index(direction))
        references.append(indices);imported_faces+=1
    if row['normal_indices'] is None and any(directions is not None for directions in geometry['triangle_normals']):
        geometry['ignored_attributes']=sorted(geometry['ignored_attributes']+['NORMAL'])
    normal_import=dict(mode=('gouraud' if row['gouraud'] else 'flat') if imported_faces else 'inherited',
        first_normal_index=obj['normal_count'],vectors=normals,references=references,imported_face_count=imported_faces)
    uv_region=None;uv_values=[];uv_faces=0;uv_error=0.0
    if row['uvs'] is not None:
        points=[point for owner in objects for packet in owner['primitives']
                if packet['uvs'] is not None and all(packet['material'][key]==row['material'][key] for key in ('clut','tpage'))
                for point in packet['uvs']]
        origin=[min(point[axis] for point in points) for axis in range(2)]
        size=[max(point[axis] for point in points)-origin[axis]+1 for axis in range(2)]
        uv_region=dict(origin=origin,width=size[0],height=size[1],clut=row['material']['clut'],tpage=row['material']['tpage'])
    for points in geometry['triangle_uvs']:
        if uv_region is None or points is None:uv_values.append(None);continue
        converted=[]
        for point in points:
            pair=[]
            for axis,dimension in enumerate(('width','height')):
                if not 0<=point[axis]<=1:raise ProjectError('Mesh UVs must remain within 0..1; texture wrapping is not imported')
                raw=point[axis]*uv_region[dimension]+uv_region['origin'][axis]-.5
                low=uv_region['origin'][axis];high=low+uv_region[dimension]-1
                value=round(min(high,max(low,raw)));uv_error=max(uv_error,abs(raw-value));pair.append(value)
            converted.append(pair)
        uv_values.append(converted);uv_faces+=1
    if uv_region is None and any(points is not None for points in geometry['triangle_uvs']):
        geometry['ignored_attributes']=sorted(geometry['ignored_attributes']+['TEXCOORD_0'])
    uv_import=dict(region=uv_region,values=uv_values,imported_face_count=uv_faces,uv_max_error=uv_error)
    color_values=[];color_faces=0;color_error=0.0
    for points in geometry['triangle_colors']:
        if row['colors'] is None or points is None:color_values.append(None);continue
        converted=[]
        for point in points:
            if any(not 0<=value<=1 for value in point):raise ProjectError('Mesh colors must remain in the normalized 0..1 range')
            if len(point)==4 and point[3]!=1:raise ProjectError('Native baked RGB cannot import per-corner alpha; use opaque vertex colors')
            rgb=[]
            for value in point[:3]:
                raw=value*128 if row['uvs'] is not None else (12.92*value if value<=.0031308 else 1.055*value**(1/2.4)-.055)*255
                rounded=round(min(255,max(0,raw)));color_error=max(color_error,abs(raw-rounded));rgb.append(rounded)
            converted.append(rgb)
        if not row['gouraud'] and converted[1:]!=[converted[0],converted[0]]:
            raise ProjectError('Flat triangle donor cannot represent different corner colors; select an unlit Gouraud donor')
        color_values.append(converted if row['gouraud'] else converted[:1]);color_faces+=1
    if row['colors'] is None and any(points is not None for points in geometry['triangle_colors']):
        geometry['ignored_attributes']=sorted(geometry['ignored_attributes']+['COLOR_0'])
    color_import=dict(mode=('textured_modulation' if row['uvs'] is not None else 'untextured_srgb') if color_faces else 'inherited',
        values=color_values,imported_face_count=color_faces,color_max_error=color_error)
    allocations=[dict(object_index=donor['object_index'],kind='vertices',vectors=geometry['vertices'])]
    if normals:allocations.append(dict(object_index=donor['object_index'],kind='normals',vectors=normals))
    _,updated,_=append_vector_ledger(base,ledger,allocations)
    additions=[]
    for index,triangle in enumerate(geometry['triangles']):
        identity=bytearray(sha256((expected_sha256+geometry['glb_sha256']+donor_face_id+'/'+str(index)).encode('utf-8')).digest()[:16])
        identity[6]=(identity[6]&15)|64;identity[8]=(identity[8]&63)|128
        fields=dict(vertices=[obj['vertex_count']+value for value in triangle])
        if references[index] is not None:fields['normal_indices']=references[index]
        if uv_values[index] is not None:fields['uvs']=uv_values[index]
        if color_values[index] is not None:fields['colors']=color_values[index]
        additions.append(dict(face_id='face://authored/'+str(UUID(bytes=bytes(identity))),donor_face_id=donor_face_id,
            fields=fields))
    group_requests=None
    if new_group:
        identity=bytearray(sha256((expected_sha256+geometry['glb_sha256']+donor_face_id+'/group').encode('utf-8')).digest()[:16])
        identity[6]=(identity[6]&15)|64;identity[8]=(identity[8]&63)|128
        group_requests=[dict(group_id='group://authored/'+str(UUID(bytes=bytes(identity))),donor_face_id=donor_face_id,faces=additions)]
        candidate,updated,audit=append_group_ledger(base,updated,group_requests)
    else:
        candidate,updated,audit=append_face_ledger(base,updated,additions)
    removed=[]
    if replace_group:
        removed=[face['face_id'] for face in topology['faces'] if face['object_index']==donor['object_index']
            and face['group_index']==row['group_index']]
        candidate,updated,audit=append_removal_ledger(base,updated,removed)
    binding=dict(format=FORMAT,source_scene_id=project.active_scene,source_sha256=sha256(original).hexdigest(),
        asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),base_binding=base_binding,ledger=updated)
    report=dict(schema_version='legaia.model-mesh-append-review.v4',asset_id=asset_id,
        source_sha256=binding['source_sha256'],effective_sha256=expected_sha256,proposed_sha256=binding['asset_sha256'],
        project_source_key=expected_key,donor_face_id=donor_face_id,object_index=donor['object_index'],
        first_vertex_index=obj['vertex_count'],geometry=geometry,normal_import=normal_import,uv_import=uv_import,color_import=color_import,allocations=allocations,additions=additions,topology=audit,
        current_preview=decode_tmd(effective),preview=decode_tmd(candidate),limitations=list(LIMITATIONS),
        project_changed=False,gameplay_verified=False)
    report['review_key']=digest(dict(asset_id=asset_id,source_key=expected_key,effective_sha256=expected_sha256,
        glb_sha256=geometry['glb_sha256'],donor_face_id=donor_face_id,proposed_sha256=binding['asset_sha256'],
        allocations=allocations,additions=additions))
    if new_group:
        report.update(schema_version='legaia.model-mesh-append-review.v5',allocation_mode='new_group',group_requests=group_requests)
        report['limitations'][-1]='Appends geometry in one independent native packet group in the donor object; retained faces and groups remain. No native object or animation channel is created. Gameplay remains unverified.'
        report['review_key']=digest(dict(base_review_key=report['review_key'],allocation_mode='new_group',group_requests=group_requests))
    if replace_group:
        report.update(schema_version='legaia.model-mesh-append-review.v6',allocation_mode='replace_group',
            removed_face_ids=removed,replaced_group=dict(object_index=donor['object_index'],group_index=row['group_index']))
        report['limitations'][-1]='Replaces the complete Current donor packet group with a new native group. Retired faces remain reserved and restorable in ledger history; original vector rows remain. No native object, image or animation channel is created. Gameplay remains unverified.'
        report['review_key']=digest(dict(base_review_key=report['review_key'],allocation_mode='replace_group',removed_face_ids=removed,replaced_group=report['replaced_group']))
    if source_key(project)!=expected_key:raise ProjectError('Project changed during mesh append review')
    return candidate,binding,_budget(report,64*1024*1024)


def review(*args,**kwargs):return prepare(*args,**kwargs)[2]
