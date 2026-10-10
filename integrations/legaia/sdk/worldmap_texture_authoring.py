"""Kingdom texture bindings reuse project TIM history without field ownership."""
import re
from hashlib import sha256
from .project import ProjectError

OWNERS = {f'worldmap://{scene}/textures': scene for scene in ('map01','map02','map03')}

def scene_for(identifier):
    match = re.fullmatch(r'texture://(map0[123])/kingdom/([0-9]{4,5})', identifier) if isinstance(identifier,str) else None
    if match and identifier == f'texture://{match[1]}/kingdom/{int(match[2]):04d}':
        return match[1]
    return None

def validate(project,binding,identifier=None):
    source = binding.get('source_scene_id') if isinstance(binding,dict) else None
    scene = OWNERS.get(source) if isinstance(source,str) else None
    if (scene is None or binding.get('format') != 'tim' or
            any(not isinstance(binding.get(k),str) or not re.fullmatch('[0-9a-f]{64}',binding[k])
                for k in ('source_disc_sha256','source_sha256')) or
            identifier is not None and scene_for(identifier) != scene):
        raise ProjectError('World TIM binding requires canonical kingdom and immutable Retail hashes')
    identities = {doc['source']['disc_identity'] for doc in project.imports.values()}
    if identities and identities != {'sha256:'+binding['source_disc_sha256']}:
        raise ProjectError('World TIM binding differs from the imported disc')
    return scene

def context(project,identifier):
    scene = scene_for(identifier)
    if not scene or not project.disc_path:
        raise ProjectError('World TIM authoring requires a canonical native texture and source disc')
    from importer.worldmap_texture_authoring import load_worldmap_texture_authoring_context
    result = load_worldmap_texture_authoring_context(project.disc_path,scene)
    original = result.original_tim(identifier)
    disc_hash = result._source(identifier)['disc']['sha256']
    identities = {doc['source']['disc_identity'] for doc in project.imports.values()}
    if identities and identities != {'sha256:'+disc_hash}:
        raise ProjectError('World TIM source differs from the imported disc')
    binding = project.texture_overrides.get(identifier)
    if binding:
        validate(project,binding,identifier)
        if binding['source_disc_sha256'] != disc_hash or binding['source_sha256'] != sha256(original).hexdigest():
            raise ProjectError('World TIM immutable source changed; refresh the project')
    return result
