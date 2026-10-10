"""Reviewed atomic field-scene ingestion using the existing qualified importer."""
from copy import deepcopy
from pathlib import Path
import re
from .project import ProjectError, canonical, digest
from importer.pipeline import import_scene


def source_key(project):
    return digest(dict(root=str(project.root),mode=project.mode,document=project._document(),
                       selected=project.selected,undo=project.undo_stack,redo=project.redo_stack))


def _prepare(project,disc,scenes,key):
    if project.mode!='edit' or key!=source_key(project):raise ProjectError('Scene group import requires the same current Edit project')
    if not isinstance(disc,str) or not disc.strip() or len(disc)>32768:raise ProjectError('Scene group import requires a local disc path')
    if not isinstance(scenes,list) or not 1<=len(scenes)<=16 or any(not isinstance(s,str) or not re.fullmatch('[a-z0-9_]{1,64}',s) for s in scenes) or scenes!=sorted(set(scenes)):raise ProjectError('Scene group import requires 1..16 canonical unique scene names')
    if len(set(project.imports)|{'scene://'+s for s in scenes})>64:raise ProjectError('Scene group import exceeds 64 project scenes')
    staged=deepcopy(project);rows=[];disc_path=str(Path(disc).resolve())
    for scene in scenes:
        metadata=import_scene(disc_path,scene)
        if metadata['scene']['semantic_id']!='scene://'+scene or metadata['scene']['name']!=scene:raise ProjectError('Imported scene identity differs from the selected group')
        previous=staged.imports.get('scene://'+scene)
        staged.import_metadata(metadata,disc_path)
        rows.append(dict(scene=scene,scene_id='scene://'+scene,metadata_sha256=digest(metadata),
                         disc_identity=metadata['source']['disc_identity'],actor_count=len(metadata['actors']),
                         model_count=len(metadata['assets'].get('models',[])),
                         status='new' if previous is None else 'unchanged' if previous==metadata else 'replaced'))
    if project.imports:
        staged.active_scene=project.active_scene;staged.selected=project.selected
    else:
        staged.active_scene='scene://'+scenes[0]
        actors=staged.imports[staged.active_scene]['actors'];staged.selected=actors[0]['semantic_id'] if actors else None
    if len(canonical(staged.imports))>32*1024*1024:raise ProjectError('Scene group imports exceed the 32 MiB metadata budget')
    if source_key(project)!=key:raise ProjectError('Project changed during scene group qualification')
    result=dict(schema_version='legaia.scene-import-batch-review.v1',source_key=key,project_path=str(project.root),
                disc_path=disc_path,scenes=list(scenes),rows=rows,active_scene=staged.active_scene,
                selection=staged.selected,no_op=project.imports==staged.imports and project.disc_path==staged.disc_path,
                project_changed=False,gameplay_verified=False)
    result['review_key']=digest(result)
    return result,staged


def review(project,disc,scenes,key):return _prepare(project,disc,scenes,key)[0]


def apply(project,body):
    if not isinstance(body,dict) or set(body)!={'disc','scenes','source_key','review_key'}:raise ProjectError('Scene group import accepts only the exact reviewed source group')
    result,staged=_prepare(project,body['disc'],body['scenes'],body['source_key'])
    if body['review_key']!=result['review_key']:raise ProjectError('Scene group import changed; review again')
    if result['no_op']:return
    project.imports=staged.imports;project.assets=staged.assets;project.disc_path=staged.disc_path
    project.active_scene=staged.active_scene;project.selected=staged.selected;project._live_correlation=None
