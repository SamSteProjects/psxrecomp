"""Reviewed component presets for existing imported actors, composed atomically."""
from copy import deepcopy,copy
from .project import ProjectError,digest
from .preset_animation import COMBINED_SCOPES, compose

def state_key(project,template,entity_id):
    return digest({'root':str(project.root),'disc':project.disc_path,'imports':project.imports,
                   'template':template,'entity_id':entity_id,'overrides':project.overrides.get(entity_id),
                   'mode':project.mode,'scene_id':project.active_scene})

def preview(project,template_id,entity_id):
    if project.mode!='edit':raise ProjectError('Actor preset review requires Edit mode')
    if not isinstance(template_id,str) or not isinstance(entity_id,str):raise ProjectError('Preset and target identities must be strings')
    template=project.actor_templates.get(template_id)
    if template is None or template['scope'] not in COMBINED_SCOPES:raise ProjectError('Choose a combined or animation actor preset')
    project._validate_template(template_id,template)
    actor=project._actor(entity_id);key=state_key(project,template,entity_id)
    if not any(a['semantic_id']==entity_id for a in project.imports.get(project.active_scene,{}).get('actors',[])):
        raise ProjectError('Actor preset review requires a target in the active scene')
    option=None
    if 'ActorAppearance' in template['components']:
        donor=template['components']['ActorAppearance']['donor_entity_id']
        option=next((row for row in project.appearance_options(entity_id)['options'] if row['donor_entity_id']==donor),None)
        if option is None:raise ProjectError('Preset donor is not a verified compatible initial pair')
    from .template_files import _verify_source
    source_hash=(_verify_source(project,template) if template['scope']=='authored-actor-preset-v2'
                 else digest(project.imports[template['source']['scene_id']]))
    before=deepcopy(project.overrides.get(entity_id))
    after,animation=compose(project,entity_id,template['components'],verify_disc=True)
    donor=(after or {}).get('ActorAppearance',{}).get('donor_entity_id')
    imported=deepcopy(actor['imported_transform']['position'])
    layers=dict(imported_position=imported,authored_position=deepcopy((before or {}).get('Transform',{}).get('position',{})),
                effective_position=dict(imported,**(before or {}).get('Transform',{}).get('position',{})),
                proposed_position=dict(imported,**(after or {}).get('Transform',{}).get('position',{})),
                authored_donor=(before or {}).get('ActorAppearance',{}).get('donor_entity_id'),proposed_donor=donor)
    if project.actor_templates.get(template_id)!=template or key!=state_key(project,project.actor_templates.get(template_id),entity_id):raise ProjectError('Preset or target changed during review')
    return dict(schema_version='legaia.actor-preset-review.v1',template_id=template_id,entity_id=entity_id,
                scope=template['scope'],source_import_sha256=source_hash,animation=animation,
                review_key=key,before=before,after=after,layers=layers,appearance=deepcopy(option),changed=before!=after,
                build_issues=project._placement_issues((after or {}).get('Transform',{})),
                limitations=['Saved axes are absolute; untouched axes and unrelated components remain unchanged.',
                             'Captured initial clip is verified against the complete proposed appearance before any change applies.',
                             'Initial MAN header only; scripts, cadence, visibility, collision and gameplay compatibility remain unverified.',
                             'AnimationChannels retain their imported clip ownership and are not retargeted.'])

def apply(project,command):
    if set(command)!={'type','template_id','entity_id','review_key'}:raise ProjectError('Actor preset requires its reviewed target and key only')
    report=preview(project,command['template_id'],command['entity_id'])
    if command['review_key']!=report['review_key']:raise ProjectError('Preset or target changed since review')
    if not report['changed']:return
    if report['after'] is None:project.overrides.pop(report['entity_id'],None)
    else:project.overrides[report['entity_id']]=deepcopy(report['after'])
    project.undo_stack.append({'entity_id':report['entity_id'],'before':report['before'],'after':deepcopy(report['after'])})
    project.redo_stack.clear()

def proposal_view(project,report):
    """Verify and detach both components; inspection never authors the project."""
    if preview(project,report['template_id'],report['entity_id'])!=report:
        raise ProjectError('Preset or target changed since review')
    if not any(actor['semantic_id']==report['entity_id'] for actor in project.imports.get(project.active_scene,{}).get('actors',[])):
        raise ProjectError('Preset scene inspection requires a target in the active scene')
    view=copy(project);view.overrides=deepcopy(project.overrides)
    if report['after'] is None:view.overrides.pop(report['entity_id'],None)
    else:view.overrides[report['entity_id']]=deepcopy(report['after'])
    return view
