"""Freshly reviewed atomic preset application to imported actor groups."""
from copy import copy, deepcopy
from .project import ProjectError, digest

def _key(project,template,ids):
    return digest(dict(root=str(project.root),disc=project.disc_path,imports=project.imports,scene_id=project.active_scene,template=template,targets={key:project.overrides.get(key) for key in ids}))

def review(project,template_id,actor_ids):
    if project.mode!='edit':raise ProjectError('Group presets require Edit mode')
    if not isinstance(template_id,str) or template_id not in project.actor_templates:raise ProjectError('Choose an existing actor preset')
    if not project.disc_path:raise ProjectError('Group presets require the project user-owned disc')
    document=project.imports.get(project.active_scene)
    allowed={actor['semantic_id']:actor for actor in document['actors']} if document else {}
    if (not isinstance(actor_ids,list) or not 2<=len(actor_ids)<=128 or any(not isinstance(key,str) or key not in allowed for key in actor_ids) or len(set(actor_ids))!=len(actor_ids)):
        raise ProjectError('Group presets require 2 through 128 distinct imported actors in the active scene')
    ids=sorted(actor_ids);template=deepcopy(project.actor_templates[template_id]);key=_key(project,template,ids)
    from importer.pipeline import _disc_context
    from .template_files import _verify_source
    from .resources import _verify
    staged=copy(project);staged.overrides=deepcopy(project.overrides);staged.undo_stack=[];staged.redo_stack=[]
    targets=[]
    with _disc_context(project.disc_path):
        source_hash=_verify_source(project,template)
        _verify(project,document)
        for identifier in ids:
            before=deepcopy(project.overrides.get(identifier))
            command=dict(type='apply_actor_template',template_id=template_id,entity_id=identifier)
            if template['scope']=='authored-actor-preset-v1':
                from .actor_presets import preview
                command['review_key']=preview(staged,template_id,identifier)['review_key']
            staged.command(command)
            after=deepcopy(staged.overrides.get(identifier));imported=deepcopy(allowed[identifier]['imported_transform']['position'])
            authored=deepcopy((before or {}).get('Transform',{}).get('position',{}));proposed=deepcopy((after or {}).get('Transform',{}).get('position',{}))
            targets.append(dict(entity_id=identifier,before=before,after=after,changed=before!=after,
                imported_position=imported,authored_position=authored,effective_position={**imported,**authored},proposed_position={**imported,**proposed},
                authored_donor=(before or {}).get('ActorAppearance',{}).get('donor_entity_id'),proposed_donor=(after or {}).get('ActorAppearance',{}).get('donor_entity_id'),
                build_issues=project._placement_issues((after or {}).get('Transform',{}))))
    if project.actor_templates.get(template_id)!=template or key!=_key(project,template,ids):raise ProjectError('Preset or group changed during review')
    return dict(schema_version='legaia.actor-preset-batch.v1',scene_id=project.active_scene,template_id=template_id,scope=template['scope'],source_scene_id=template['source']['scene_id'],source_import_sha256=source_hash,review_key=key,targets=targets,changed_count=sum(row['changed'] for row in targets),
        limitations=['Saved position axes are absolute for every target; shared coordinates can overlap actors. Untouched axes and unrelated components remain unchanged.',
                    'All targets must pass existing source/donor compatibility before any changes apply.',
                    'Retail Y, facing, runtime identity, collision, scripts and gameplay remain unverified.'])

def apply(project,command):
    if set(command)!={'type','template_id','actor_ids','review_key'}:raise ProjectError('Group preset requires preset, actor IDs and reviewed key only')
    report=review(project,command['template_id'],command['actor_ids'])
    if command['review_key']!=report['review_key']:raise ProjectError('Preset or group changed since review; review again')
    if not report['changed_count']:return
    before={row['entity_id']:deepcopy(row['before']) for row in report['targets']}
    after={row['entity_id']:deepcopy(row['after']) for row in report['targets']}
    for identifier,value in after.items():
        if value is None:project.overrides.pop(identifier,None)
        else:project.overrides[identifier]=deepcopy(value)
    template=project.actor_templates[report['template_id']];sources=[template['source']['entity_id']]
    if 'ActorAppearance' in template['components']:sources.append(template['components']['ActorAppearance']['donor_entity_id'])
    project.undo_stack.append(dict(target='entity_overrides',entity_ids=sorted(after),source_entity_ids=sorted(set(sources)),before=before,after=after))
    project.redo_stack.clear()
