"""Reviewed combined position/appearance presets for existing imported actors."""
from copy import deepcopy
from .project import ProjectError,digest

def state_key(project,template,entity_id):
    return digest({'root':str(project.root),'disc':project.disc_path,'imports':project.imports,
                   'template':template,'entity_id':entity_id,'overrides':project.overrides.get(entity_id)})

def preview(project,template_id,entity_id):
    if not isinstance(template_id,str) or not isinstance(entity_id,str):raise ProjectError('Preset and target identities must be strings')
    template=project.actor_templates.get(template_id)
    if template is None or template['scope']!='authored-actor-preset-v1':raise ProjectError('Choose a combined actor preset')
    project._validate_template(template_id,template)
    actor=project._actor(entity_id);key=state_key(project,template,entity_id)
    donor=template['components']['ActorAppearance']['donor_entity_id']
    if donor not in {row['donor_entity_id'] for row in project.appearance_options(entity_id)['options']}:
        raise ProjectError('Preset donor is not a verified compatible initial pair')
    before=deepcopy(project.overrides.get(entity_id));after=deepcopy(before or {})
    after.setdefault('Transform',{}).setdefault('position',{}).update(template['components']['Transform']['position'])
    after['ActorAppearance']=deepcopy(template['components']['ActorAppearance'])
    imported=deepcopy(actor['imported_transform']['position'])
    layers=dict(imported_position=imported,authored_position=deepcopy((before or {}).get('Transform',{}).get('position',{})),
                effective_position=dict(imported,**(before or {}).get('Transform',{}).get('position',{})),
                proposed_position=dict(imported,**after['Transform']['position']),
                authored_donor=(before or {}).get('ActorAppearance',{}).get('donor_entity_id'),proposed_donor=donor)
    if project.actor_templates.get(template_id)!=template or key!=state_key(project,project.actor_templates.get(template_id),entity_id):raise ProjectError('Preset or target changed during review')
    return dict(schema_version='legaia.actor-preset-review.v1',template_id=template_id,entity_id=entity_id,
                review_key=key,before=before,after=after,layers=layers,changed=before!=after,
                build_issues=project._placement_issues(after['Transform']),
                limitations=['Saved axes are absolute; untouched axes and unrelated components remain unchanged.',
                             'Initial donor pair only; scripts, visibility, collision and gameplay compatibility remain unverified.'])

def apply(project,command):
    if set(command)!={'type','template_id','entity_id','review_key'}:raise ProjectError('Combined preset requires its reviewed target and key only')
    report=preview(project,command['template_id'],command['entity_id'])
    if command['review_key']!=report['review_key']:raise ProjectError('Preset or target changed since review')
    if not report['changed']:return
    project.overrides[report['entity_id']]=deepcopy(report['after'])
    project.undo_stack.append({'entity_id':report['entity_id'],'before':report['before'],'after':deepcopy(report['after'])})
    project.redo_stack.clear()
