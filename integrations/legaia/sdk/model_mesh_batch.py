"""Atomic donor mapping for selected sections of one qualified static GLB."""
from copy import copy,deepcopy
from hashlib import sha256
from importer.model_mesh_append import inspect_append_mesh,mesh_source_offset
from importer.model_mesh_orientation import mesh_source_rotation
from importer.model_face_addition import MAX_NEW_FACES
from . import model_mesh_append
from .model_face_addition import _context,_budget
from .project import ProjectError,digest
from .scene_preview import source_key


def prepare(project,asset_id,content,mappings,expected_sha256,expected_key,*,material_colors=False,scene_index=None,uv_set=0,source_scale=1,replace_objects=False,source_offset=(0,0,0),source_rotation=(0,0,0)):
    source_offset=mesh_source_offset(source_offset);source_rotation=mesh_source_rotation(source_rotation)
    if type(replace_objects) is not bool:raise ProjectError('Object replacement choice must be boolean')
    if type(uv_set) is not int or not 0<=uv_set<=7:raise ProjectError('Choose a default source UV set from 0 through 7')
    _,effective,_,_,_,topology=_context(project,asset_id,expected_key)
    if sha256(effective).hexdigest()!=expected_sha256:
        raise ProjectError('Model changed since mesh donor mapping')
    inventory=inspect_append_mesh(content,scene_index=scene_index,source_scale=source_scale,source_offset=source_offset,source_rotation=source_rotation)
    if not isinstance(mappings,list) or not 1<=len(mappings)<=16:
        raise ProjectError('Choose 1 through 16 source GLB sections for donor mapping')
    donors={face['face_id']:face for face in topology['faces']};replaced=set()
    for index,row in enumerate(mappings):
        if (not isinstance(row,dict) or set(row) not in ({'primitive_index','donor_face_id','replace_group'},{'primitive_index','donor_face_id','replace_group','uv_set'})
                or type(row['primitive_index']) is not int or not 0<=row['primitive_index']<len(inventory['primitives'])
                or index and row['primitive_index']<=mappings[index-1]['primitive_index']
                or not isinstance(row['donor_face_id'],str) or row['donor_face_id'] not in donors
                or type(row['replace_group']) is not bool or type(row.get('uv_set',uv_set)) is not int or not 0<=row.get('uv_set',uv_set)<=7):
            raise ProjectError('Mesh donor mappings require exact source order, Current faces and boolean replacement choices')
        if replace_objects and row['replace_group']:raise ProjectError('Object replacement cannot also replace individual donor groups')
        donor=donors[row['donor_face_id']];group=(donor['object_index'],donor['group_index'])
        if group in replaced:raise ProjectError('A replaced donor group cannot supply another section in the same batch')
        if row['replace_group']:
            if any((donors[prior['donor_face_id']]['object_index'],donors[prior['donor_face_id']]['group_index'])==group for prior in mappings[:index]):
                raise ProjectError('A donor group used by another section cannot be replaced in the same batch')
            replaced.add(group)
    if sum(inventory['primitives'][row['primitive_index']]['triangle_count'] for row in mappings)>MAX_NEW_FACES:
        raise ProjectError(f'Selected GLB sections exceed the {MAX_NEW_FACES}-triangle native transaction budget')
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
            source['effective_sha256'],key,new_group=True,replace_group=row['replace_group'],primitive_index=row['primitive_index'],material_colors=material_colors,scene_index=scene_index,uv_set=row.get('uv_set',uv_set),source_scale=source_scale,source_offset=source_offset,source_rotation=source_rotation)
        candidates[binding['asset_sha256']]=candidate;view.model_overrides[asset_id]=deepcopy(binding)
        steps.append(dict(source=source,review=report))
    retirement=None
    if replace_objects:
        from . import model_face_removal
        replaced_objects=sorted({donors[row['donor_face_id']]['object_index'] for row in mappings})
        retired_ids=[face['face_id'] for face in topology['faces'] if face['object_index'] in replaced_objects]
        key=source_key(view);mesh_source=model_mesh_append.source(view,asset_id,key)
        face_source=model_face_removal.source(view,asset_id,key)
        current={face['face_id']:face for face in mesh_source['topology']['faces']}
        selections=[dict(object_index=current[identity]['object_index'],primitive_index=current[identity]['current_primitive_index']) for identity in retired_ids]
        candidate,_,removed=model_face_removal.prepare(view,asset_id,selections,mesh_source['effective_sha256'],key)
        binding=removed.pop('_binding');removed.pop('_effective')
        retirement=dict(mesh_source=mesh_source,source=face_source,review=removed)
    report=dict(schema_version='legaia.model-mesh-batch-review.v1',asset_id=asset_id,
        project_source_key=expected_key,effective_sha256=expected_sha256,source_sha256=binding['source_sha256'],
        proposed_sha256=binding['asset_sha256'],glb_sha256=inventory['glb_sha256'],mappings=deepcopy(mappings),
        selected_primitive_indices=[row['primitive_index'] for row in mappings],
        skipped_primitive_indices=[i for i in range(len(inventory['primitives'])) if i not in {row['primitive_index'] for row in mappings}],
        inventory=inventory,steps=steps,current_preview=steps[0]['review']['current_preview'],
        preview=steps[-1]['review']['preview'],topology=steps[-1]['review']['topology'],
        project_changed=False,gameplay_verified=False,
        limitations=['Selected source primitives are mapped once in source order to existing native triangle donors; skipped sections allocate no geometry.',
            'Each section creates an independent native packet group in its donor object.',
            'Each mapping may choose its source UV set; omitted choices use the batch default. Missing selected UVs retain donor values.',
            'Only explicitly selected donor groups are replaced; shared replacement ownership is rejected.',
            'Native donor layouts and texture bindings supply materials; no new images, packet families or animation channels are allocated.',
            'Review is read-only and Apply publishes the complete mapping in one Undo entry. Gameplay is unverified.'])
    if retirement:
        report.update(schema_version='legaia.model-mesh-batch-review.v2',replace_objects=True,
            replaced_object_indices=replaced_objects,removed_face_ids=retired_ids,retirement=retirement,
            proposed_sha256=binding['asset_sha256'],preview=retirement['review']['preview'],topology=retirement['review']['topology'])
        report['limitations'][3]='All original Current geometry in mapped donor objects is retired after every selected section is allocated. Newly mapped sections remain; other objects and original vector rows remain.'
    if inventory.get('source_scale',1)!=1:report['source_scale']=inventory['source_scale']
    if any(source_offset):report['source_offset']=source_offset
    if any(source_rotation):report['source_rotation']=source_rotation
    if uv_set:report['uv_set']=uv_set
    if scene_index is not None:report['selected_scene_index']=scene_index
    if material_colors:
        report['material_colors']=True
        report['limitations'].append('Opaque standard base-color factors multiply vertex RGB. Unlit donors consume the result; lit donors ignore RGB. Native texture bindings remain and source images/PBR shading are not imported.')
    report['review_key']=digest(report)
    if source_key(project)!=expected_key:raise ProjectError('Project changed during mesh donor mapping review')
    return candidate,binding,_budget(report,64*1024*1024)


def review(*args,**kwargs):return prepare(*args,**kwargs)[2]


def apply(project,*args,review_key,material_colors=False,scene_index=None,uv_set=0,source_scale=1,replace_objects=False,source_offset=(0,0,0),source_rotation=(0,0,0)):
    candidate,binding,report=prepare(project,*args,material_colors=material_colors,scene_index=scene_index,uv_set=uv_set,source_scale=source_scale,replace_objects=replace_objects,source_offset=source_offset,source_rotation=source_rotation)
    if report['review_key']!=review_key:raise ProjectError('GLB donor mappings changed after Review')
    asset_id,_,_,_,expected_key=args
    from .model_mesh_sources import attach
    binding=attach(project,asset_id,binding,args[1],dict(kind='batch',mappings=deepcopy(args[2]),replace_objects=replace_objects,material_colors=material_colors,scene_index=scene_index,uv_set=uv_set,source_scale=source_scale,source_offset=list(source_offset),source_rotation=list(source_rotation)),expected_key)
    project._publish_model_ledger(asset_id,candidate,binding,expected_key,'Mesh donor mapping')
    return report
