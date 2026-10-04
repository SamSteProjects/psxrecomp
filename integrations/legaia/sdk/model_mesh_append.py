"""One reviewed mesh import publishes vector and face allocation atomically."""
from hashlib import sha256
from uuid import UUID
from importer.model_mesh_append import decode_append_mesh
from importer.model_face_ledger import append_vector_ledger,append_face_ledger
from importer.model_primitives import inspect_model_primitives
from importer.assets import decode_tmd
from .model_face_addition import _context,_budget,FORMAT
from .scene_preview import source_key
from .project import ProjectError,digest

LIMITATIONS=[
    'Imports static standard GLB POSITION and triangle lists into the selected donor object in native source units.',
    'Reflects Y and reverses triangle winding; rounds positions to signed integer native coordinates.',
    'UVs, baked RGB, normal references, packet flags and material bindings are inherited from the selected native triangle donor.',
    'Validated GLB display attributes, materials and images are not imported. No external resources are fetched.',
    'Apply object transforms before export. One scene, one mesh node and no skinning, morph targets or animation.',
    'Appends geometry; it does not replace retained faces or create native objects or packet groups. Gameplay remains unverified.',
]


def prepare(project,asset_id,content,donor_face_id,expected_sha256,expected_key):
    original,effective,base,base_binding,ledger,topology=_context(project,asset_id,expected_key)
    if sha256(effective).hexdigest()!=expected_sha256:
        raise ProjectError('Model changed since mesh append inspection')
    if not isinstance(donor_face_id,str):raise ProjectError('Mesh append requires a stable donor identity')
    donor=next((face for face in topology['faces'] if face['face_id']==donor_face_id),None)
    if donor is None:raise ProjectError('Mesh append donor is absent from Current topology')
    obj=inspect_model_primitives(effective,include_normal_references=True)['objects'][donor['object_index']]
    row=obj['primitives'][donor['current_primitive_index']]
    if row['corner_count']!=3:raise ProjectError('Select a native triangle donor for a triangle mesh')
    geometry=decode_append_mesh(content)
    allocations=[dict(object_index=donor['object_index'],kind='vertices',vectors=geometry['vertices'])]
    _,updated,_=append_vector_ledger(base,ledger,allocations)
    additions=[]
    for index,triangle in enumerate(geometry['triangles']):
        identity=bytearray(sha256((expected_sha256+geometry['glb_sha256']+donor_face_id+'/'+str(index)).encode('utf-8')).digest()[:16])
        identity[6]=(identity[6]&15)|64;identity[8]=(identity[8]&63)|128
        additions.append(dict(face_id='face://authored/'+str(UUID(bytes=bytes(identity))),donor_face_id=donor_face_id,
            fields=dict(vertices=[obj['vertex_count']+value for value in triangle])))
    candidate,updated,audit=append_face_ledger(base,updated,additions)
    binding=dict(format=FORMAT,source_scene_id=project.active_scene,source_sha256=sha256(original).hexdigest(),
        asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),base_binding=base_binding,ledger=updated)
    report=dict(schema_version='legaia.model-mesh-append-review.v1',asset_id=asset_id,
        source_sha256=binding['source_sha256'],effective_sha256=expected_sha256,proposed_sha256=binding['asset_sha256'],
        project_source_key=expected_key,donor_face_id=donor_face_id,object_index=donor['object_index'],
        first_vertex_index=obj['vertex_count'],geometry=geometry,allocations=allocations,additions=additions,topology=audit,
        current_preview=decode_tmd(effective),preview=decode_tmd(candidate),limitations=list(LIMITATIONS),
        project_changed=False,gameplay_verified=False)
    report['review_key']=digest(dict(asset_id=asset_id,source_key=expected_key,effective_sha256=expected_sha256,
        glb_sha256=geometry['glb_sha256'],donor_face_id=donor_face_id,proposed_sha256=binding['asset_sha256'],
        allocations=allocations,additions=additions))
    if source_key(project)!=expected_key:raise ProjectError('Project changed during mesh append review')
    return candidate,binding,_budget(report,64*1024*1024)


def review(*args):return prepare(*args)[2]
