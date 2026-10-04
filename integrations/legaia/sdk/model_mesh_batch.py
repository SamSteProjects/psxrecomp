"""Atomic donor mapping for all sections of one qualified static GLB."""
from copy import copy,deepcopy
from hashlib import sha256
from importer.model_mesh_append import inspect_append_mesh
from . import model_mesh_append
from .model_face_addition import _context,_budget
from .project import ProjectError,digest
from .scene_preview import source_key


def prepare(project,asset_id,content,mappings,expected_sha256,expected_key,*,material_colors=False,scene_index=None,uv_set=0):
    if type(uv_set) is not int or not 0<=uv_set<=7:raise ProjectError('Choose a default source UV set from 0 through 7')
    _,effective,_,_,_,topology=_context(project,asset_id,expected_key)
    if sha256(effective).hexdigest()!=expected_sha256:
        raise ProjectError('Model changed since mesh donor mapping')
    inventory=inspect_append_mesh(content,scene_index=scene_index)
    if not isinstance(mappings,list) or not 1<=len(mappings)<=16 or len(mappings)!=len(inventory['primitives']):
        raise ProjectError('Map every GLB primitive exactly once, within the 16-section batch budget')
    donors={face['face_id']:face for face in topology['faces']};replaced=set()
    for index,row in enumerate(mappings):
        if (not isinstance(row,dict) or set(row) not in ({'primitive_index','donor_face_id','replace_group'},{'primitive_index','donor_face_id','replace_group','uv_set'})
                or type(row['primitive_index']) is not int or row['primitive_index']!=index
                or not isinstance(row['donor_face_id'],str) or row['donor_face_id'] not in donors
                or type(row['replace_group']) is not bool or type(row.get('uv_set',uv_set)) is not int or not 0<=row.get('uv_set',uv_set)<=7):
            raise ProjectError('Mesh donor mappings require exact source order, Current faces and boolean replacement choices')
        donor=donors[row['donor_face_id']];group=(donor['object_index'],donor['group_index'])
        if group in replaced:raise ProjectError('A replaced donor group cannot supply another section in the same batch')
        if row['replace_group']:
            if any((donors[prior['donor_face_id']]['object_index'],donors[prior['donor_face_id']]['group_index'])==group for prior in mappings[:index]):
                raise ProjectError('A donor group used by another section cannot be replaced in the same batch')
            replaced.add(group)
    # A detached overlay view keeps intermediate native candidates in memory.
    # It has no command/history or disk publication path.
    view=copy(project);view.model_overrides=deepcopy(project.model_overrides)
    candidates={};read=project.read_model_replacement
    def read_candidate(asset,binding):
        candidate=candidates.get(binding.get('asset_sha256'))
        return candidate if asset==asset_id and candidate is not None else read(asset,binding)
    view.read_model_replacement=read_candidate
    steps=[]
    for row in mappings:
        key=source_key(view);source=model_mesh_append.source(view,asset_id,key)
        candidate,binding,report=model_mesh_append.prepare(view,asset_id,content,row['donor_face_id'],
            source['effective_sha256'],key,new_group=True,replace_group=row['replace_group'],primitive_index=row['primitive_index'],material_colors=material_colors,scene_index=scene_index,uv_set=row.get('uv_set',uv_set))
        candidates[binding['asset_sha256']]=candidate;view.model_overrides[asset_id]=deepcopy(binding)
        steps.append(dict(source=source,review=report))
    report=dict(schema_version='legaia.model-mesh-batch-review.v1',asset_id=asset_id,
        project_source_key=expected_key,effective_sha256=expected_sha256,source_sha256=binding['source_sha256'],
        proposed_sha256=binding['asset_sha256'],glb_sha256=inventory['glb_sha256'],mappings=deepcopy(mappings),
        inventory=inventory,steps=steps,current_preview=steps[0]['review']['current_preview'],
        preview=steps[-1]['review']['preview'],topology=steps[-1]['review']['topology'],
        project_changed=False,gameplay_verified=False,
        limitations=['All source primitives are mapped in source order to existing native triangle donors.',
            'Each section creates an independent native packet group in its donor object.',
            'Each mapping may choose its source UV set; omitted choices use the batch default. Missing selected UVs retain donor values.',
            'Only explicitly selected donor groups are replaced; shared replacement ownership is rejected.',
            'Native donor layouts and texture bindings supply materials; no new images, packet families or animation channels are allocated.',
            'Review is read-only and Apply publishes the complete mapping in one Undo entry. Gameplay is unverified.'])
    if uv_set:report['uv_set']=uv_set
    if scene_index is not None:report['selected_scene_index']=scene_index
    if material_colors:
        report['material_colors']=True
        report['limitations'].append('Opaque standard base-color factors multiply vertex RGB. Unlit donors consume the result; lit donors ignore RGB. Native texture bindings remain and source images/PBR shading are not imported.')
    report['review_key']=digest(report)
    if source_key(project)!=expected_key:raise ProjectError('Project changed during mesh donor mapping review')
    return candidate,binding,_budget(report,64*1024*1024)


def review(*args,**kwargs):return prepare(*args,**kwargs)[2]


def apply(project,*args,review_key,material_colors=False,scene_index=None,uv_set=0):
    candidate,binding,report=prepare(project,*args,material_colors=material_colors,scene_index=scene_index,uv_set=uv_set)
    if report['review_key']!=review_key:raise ProjectError('GLB donor mappings changed after Review')
    asset_id,_,_,_,expected_key=args
    project._publish_model_ledger(asset_id,candidate,binding,expected_key,'Mesh donor mapping')
    return report
