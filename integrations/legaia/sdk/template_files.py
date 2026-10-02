"""Portable source-bound authored preset metadata; no retail payloads."""
from copy import deepcopy
import json
import uuid
from .project import ProjectError,digest

MAX_FILE_BYTES=8*1024
SCHEMA='legaia.actor-preset-file.v1'
ANIMATED_SCHEMA='legaia.actor-preset-file.v2'

def _pairs(items):
    result={}
    for key,value in items:
        if key in result:raise ProjectError('Duplicate preset JSON key')
        result[key]=value
    return result

def _constant(_):
    raise ProjectError('Nonfinite preset JSON value')

def parse(content):
    if not isinstance(content,str):raise ProjectError('Preset file must be UTF-8 JSON up to 8 KiB')
    try:size=len(content.encode('utf-8'))
    except UnicodeError as exc:raise ProjectError('Preset content must be valid UTF-8') from exc
    if size>MAX_FILE_BYTES:raise ProjectError('Preset file must be UTF-8 JSON up to 8 KiB')
    try:
        value=json.loads(content,object_pairs_hook=_pairs,parse_constant=_constant)
    except (ValueError,RecursionError) as exc:raise ProjectError('Invalid preset JSON') from exc
    if not isinstance(value,dict) or set(value)!={'schema_version','source_import_sha256','template'} or value['schema_version'] not in (SCHEMA,ANIMATED_SCHEMA):
        raise ProjectError('Unsupported preset file fields or schema')
    source_hash=value['source_import_sha256']
    if not isinstance(source_hash,str) or len(source_hash)!=64 or any(c not in '0123456789abcdef' for c in source_hash):
        raise ProjectError('Preset requires a source import SHA256')
    if not isinstance(value['template'],dict):raise ProjectError('Preset file requires template metadata')
    from .preset_animation import ANIMATED_SCOPE
    if (value['schema_version']==ANIMATED_SCHEMA)!=(value['template'].get('scope')==ANIMATED_SCOPE):
        raise ProjectError('Preset file version differs from its template scope')
    return value

def _verify_source(project,template):
    project._validate_template(template.get('id'),template)
    try:json.dumps(template,ensure_ascii=False).encode('utf-8')
    except UnicodeError as exc:raise ProjectError('Preset metadata must be valid UTF-8') from exc
    source=template['source'];document=project.imports.get(source['scene_id'])
    if not document or not any(actor['semantic_id']==source['entity_id'] for actor in document['actors']):
        raise ProjectError('Import the preset source scene and actor first')
    if not project.disc_path:raise ProjectError('Preset transfer requires the project user-owned disc')
    from importer.pipeline import _disc_context,import_scene
    with _disc_context(project.disc_path):
        if digest(import_scene(project.disc_path,document['scene']['name']))!=digest(document):
            raise ProjectError('Preset source differs from freshly verified retail import')
    if 'ActorAppearance' in template['components']:
        donor=template['components']['ActorAppearance']['donor_entity_id']
        if not any(row['donor_entity_id']==donor for row in project.appearance_options(source['entity_id'])['options']):
            raise ProjectError('Preset donor is not a verified compatible initial pair')
    if 'ActorAnimation' in template['components']:
        from .preset_animation import validate_frozen
        validate_frozen(project,template,verify_disc=True)
    return digest(document)

def export_file(project,template_id):
    if not isinstance(template_id,str) or template_id not in project.actor_templates:raise ProjectError('Choose an existing actor preset')
    template=deepcopy(project.actor_templates[template_id])
    source_hash=_verify_source(project,template)
    from .preset_animation import ANIMATED_SCOPE
    value={'schema_version':ANIMATED_SCHEMA if template['scope']==ANIMATED_SCOPE else SCHEMA,'source_import_sha256':source_hash,'template':template}
    encoded=json.dumps(value,ensure_ascii=True,indent=2)+'\n'
    parse(encoded)
    if project.actor_templates.get(template_id)!=template:raise ProjectError('Preset changed during export')
    return value

def review(project,content,name):
    value=parse(content);template=deepcopy(value['template'])
    if not isinstance(name,str) or name!=name.strip() or not 1<=len(name)<=80:raise ProjectError('Preset name must contain 1 to 80 trimmed characters')
    try:name.encode('utf-8')
    except UnicodeError as exc:raise ProjectError('Preset name must be valid UTF-8') from exc
    if len(project.actor_templates)>=128:raise ProjectError('Project supports at most 128 authored actor templates')
    if any(row['name'].casefold()==name.casefold() for row in project.actor_templates.values()):raise ProjectError('An authored template already uses that name')
    key=digest({'root':str(project.root),'disc':project.disc_path,'imports':project.imports,'templates':project.actor_templates,'file':value,'name':name})
    source_hash=_verify_source(project,template)
    if source_hash!=value['source_import_sha256']:raise ProjectError('Preset file source import differs from this project')
    template['id']='template://'+str(uuid.uuid5(uuid.NAMESPACE_URL,'legaia-preset-import:'+key));template['name']=name
    project._validate_template(template['id'],template)
    if key!=digest({'root':str(project.root),'disc':project.disc_path,'imports':project.imports,'templates':project.actor_templates,'file':value,'name':name}):raise ProjectError('Project changed during preset review')
    return {'schema_version':'legaia.actor-preset-import-review.v1','review_key':key,'template':template,
            'source_import_sha256':source_hash,'limitations':['Import adds one independent preset to the library; it changes no actor components.','Source scene/import and donor compatibility remain bound; Apply revalidates its target.','Coordinates are absolute; height may be project-only and gameplay remains unverified.']}

def apply(project,command):
    if set(command)!={'type','content','name','review_key'}:raise ProjectError('Preset import requires file, name and reviewed key only')
    report=review(project,command['content'],command['name'])
    if command['review_key']!=report['review_key']:raise ProjectError('Preset library or source changed since review')
    template=report['template'];identifier=template['id']
    if identifier in project.actor_templates:raise ProjectError('Imported preset identity already exists')
    project.actor_templates[identifier]=deepcopy(template)
    project.undo_stack.append({'target':'actor_templates','template_id':identifier,'entity_id':template['source']['entity_id'],'before':None,'after':deepcopy(template)})
    project.redo_stack.clear()
