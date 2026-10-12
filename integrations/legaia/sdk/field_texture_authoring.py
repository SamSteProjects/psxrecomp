"""Explicit global ownership for shared field-party TIM overrides."""
import re
from hashlib import sha256
from .project import ProjectError

OWNER='field-party://textures'

def owns(identifier):
    return isinstance(identifier,str) and re.fullmatch(r'texture://legaia/field-party/874/2/[0-7]',identifier) is not None

def validate(project,binding,identifier=None):
    if (not isinstance(binding,dict) or binding.get('source_scene_id')!=OWNER or binding.get('format')!='tim' or identifier is not None and not owns(identifier)
        or any(not isinstance(binding.get(k),str) or not re.fullmatch('[a-f0-9]{64}',binding[k]) for k in ('source_disc_sha256','source_sha256'))):raise ProjectError('Shared field TIM binding requires canonical bank ownership and immutable Retail hashes')
    identities={d['source']['disc_identity'] for d in project.imports.values()}
    if identities and identities!={'sha256:'+binding['source_disc_sha256']}:raise ProjectError('Shared field TIM binding differs from imported disc')

def context(project,identifier):
    if not owns(identifier) or not project.disc_path:raise ProjectError('Shared field TIM requires a canonical bank identity and source disc')
    from importer.field_texture_authoring import load_field_texture_authoring_context
    result=load_field_texture_authoring_context(project.disc_path)
    original=result.original_tim(identifier);disc=result._source(identifier)['disc']['sha256']
    identities={d['source']['disc_identity'] for d in project.imports.values()}
    if identities and identities!={'sha256:'+disc}:raise ProjectError('Shared field TIM source differs from imported disc')
    binding=project.texture_overrides.get(identifier)
    if binding:
        validate(project,binding,identifier)
        if binding['source_disc_sha256']!=disc or binding['source_sha256']!=sha256(original).hexdigest():raise ProjectError('Shared field TIM Retail identity changed')
    return result
