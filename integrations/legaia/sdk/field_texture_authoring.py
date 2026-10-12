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



def resources(project,expected_project_path,expected_source_key):
    from .battle_character_resources import _fresh
    from importer.pipeline import _disc_context
    from importer.field_texture_authoring import load_field_texture_authoring_context,LIMITATIONS
    from importer.texture_catalog import _metadata
    _fresh(project,expected_project_path,expected_source_key)
    with _disc_context(project.disc_path):
        ctx=load_field_texture_authoring_context(project.disc_path);assets=[]
        for tim,source in ctx._catalog.textures:
            row=_metadata(ctx._catalog,tim,source);row.update(name=f'Shared Field TIM {source["pack_slot"]}',scope='global_field_party',limitations=list(LIMITATIONS),original_sha256=sha256(ctx.original_tim(source['semantic_id'])).hexdigest());assets.append(row)
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.field-texture-resources.v1',project_path=str(project.root),project_source_key=expected_source_key,assets=assets,disc_sha256=ctx._digest,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def _snapshot(project,asset_id,expected_project_path,expected_source_key):
    from .battle_character_resources import _fresh
    _fresh(project,expected_project_path,expected_source_key)
    ctx=context(project,asset_id);original=ctx.original_tim(asset_id);binding=project.texture_overrides.get(asset_id);current=project.read_texture_replacement(binding) if binding else original;ctx.validate_replacement(asset_id,current)
    return ctx,original,current


def inspect(project,asset_id,palette_index,expected_project_path,expected_source_key):
    from .battle_character_resources import _fresh
    from importer.textures import parse_tim,decode_tim
    from base64 import b64encode
    ctx,original,current=_snapshot(project,asset_id,expected_project_path,expected_source_key);source=project.texture_palette_source(asset_id,palette_index);pixels=decode_tim(parse_tim(current),palette_index);_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.field-texture-inspection.v1',project_path=str(project.root),project_source_key=expected_source_key,source_record=ctx._source(asset_id),palette=source,current_tim_base64=b64encode(current).decode(),rgba_base64=b64encode(pixels['rgba']).decode(),width=pixels['width'],height=pixels['height'],layer='current',read_only=True,project_changed=False,gameplay_verified=False)


def review(project,asset_id,palette_index,entry_index,word,expected_current_sha256,expected_project_path,expected_source_key):
    from .battle_character_resources import _fresh
    from .project import digest
    from importer.texture_authoring import patch_tim_palette_word,texture_payload_changes
    from base64 import b64encode
    if project.mode!='edit':raise ProjectError('Shared field palette authoring requires Edit mode')
    ctx,original,current=_snapshot(project,asset_id,expected_project_path,expected_source_key)
    candidate=patch_tim_palette_word(current,expected_current_sha256,palette_index,entry_index,word)
    edits={i:project.read_texture_replacement(b) for i,b in project.texture_overrides.items() if owns(i)};edits[asset_id]=candidate;ctx.patch(edits)
    result=dict(schema_version='legaia.field-texture-review.v1',project_path=str(project.root),project_source_key=expected_source_key,asset_id=asset_id,palette_index=palette_index,entry_index=entry_index,word=word,source_sha256=sha256(original).hexdigest(),current_sha256=sha256(current).hexdigest(),candidate_sha256=sha256(candidate).hexdigest(),candidate_tim_base64=b64encode(candidate).decode(),changes=texture_payload_changes(current,candidate),layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    result['review_key']=digest(result);_fresh(project,expected_project_path,expected_source_key);return result


def apply(project,review_key,**args):
    from base64 import b64decode
    result=review(project,**args)
    if result['review_key']!=review_key:raise ProjectError('Shared field palette Apply requires its exact fresh Review')
    if result['current_sha256']==result['candidate_sha256']:raise ProjectError('Shared field palette Apply has no native change')
    project.set_texture_replacement(args['asset_id'],b64decode(result['candidate_tim_base64']))
    return dict(schema_version='legaia.field-texture-apply.v1',history_steps=1,project_changed=True,gameplay_verified=False)



def compose_catalog(project,catalog):
    """Copy a qualified field catalog and replay saved source-bound replacements."""
    from copy import deepcopy
    from importer.pipeline import _disc_context
    from importer.textures import parse_tim
    if catalog.scene!='global-field-party':raise ProjectError('Shared TIM composition requires its qualified global catalog')
    bindings={i:deepcopy(b) for i,b in project.texture_overrides.items() if owns(i)}
    if not bindings:return catalog,bindings
    result=deepcopy(catalog);replacements={}
    with _disc_context(project.disc_path):
        ctx=context(project,next(iter(bindings)))
        if ctx._digest!=catalog.disc_sha256:raise ProjectError('Shared TIM catalog and replacement disc differ')
        for identifier,binding in bindings.items():
            validate(project,binding,identifier)
            if binding['source_disc_sha256']!=ctx._digest or binding['source_sha256']!=sha256(ctx.original_tim(identifier)).hexdigest():raise ProjectError('Shared Current TIM original source changed')
            content=project.read_texture_replacement(binding);ctx.validate_replacement(identifier,content);replacements[identifier]=parse_tim(content)
    result.textures=[(replacements.get(source['semantic_id'],tim),source) for tim,source in result.textures]
    return result,bindings



def download(project,asset_id,layer,expected_current_sha256,expected_project_path,expected_source_key):
    from .battle_character_resources import _fresh
    from base64 import b64encode
    if layer not in ('retail','current'):raise ProjectError('Choose Retail or Current shared TIM')
    ctx,original,current=_snapshot(project,asset_id,expected_project_path,expected_source_key)
    if sha256(current).hexdigest()!=expected_current_sha256:raise ProjectError('Shared TIM changed; inspect again')
    content=original if layer=='retail' else current;_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.field-texture-download.v1',project_path=str(project.root),project_source_key=expected_source_key,asset_id=asset_id,layer=layer,sha256=sha256(content).hexdigest(),byte_length=len(content),filename=f'shared-field-{asset_id[-1]}-{layer}.tim',tim_base64=b64encode(content).decode(),read_only=True,project_changed=False,gameplay_verified=False)


def review_file(project,asset_id,palette_index,tim_base64,expected_current_sha256,expected_project_path,expected_source_key):
    from .battle_character_resources import _fresh
    from .project import digest
    from importer.texture_authoring import texture_payload_changes
    from base64 import b64decode,b64encode
    if project.mode!='edit':raise ProjectError('Shared TIM replacement requires Edit mode')
    if not isinstance(tim_base64,str) or not 1<=len(tim_base64)<=1400000:raise ProjectError('Shared TIM file must be at most 1 MiB')
    try:candidate=b64decode(tim_base64,validate=True)
    except (ValueError,TypeError) as e:raise ProjectError('Shared TIM requires exact base64 bytes') from e
    if not 1<=len(candidate)<=1024*1024:raise ProjectError('Shared TIM file must be at most 1 MiB')
    ctx,original,current=_snapshot(project,asset_id,expected_project_path,expected_source_key)
    if sha256(current).hexdigest()!=expected_current_sha256:raise ProjectError('Shared TIM changed; inspect again')
    project.texture_palette_source(asset_id,palette_index);ctx.validate_replacement(asset_id,candidate)
    edits={i:project.read_texture_replacement(b) for i,b in project.texture_overrides.items() if owns(i)};edits[asset_id]=candidate;ctx.patch(edits)
    result=dict(schema_version='legaia.field-texture-file-review.v1',project_path=str(project.root),project_source_key=expected_source_key,asset_id=asset_id,palette_index=palette_index,input_sha256=sha256(candidate).hexdigest(),input_byte_length=len(candidate),source_sha256=sha256(original).hexdigest(),current_sha256=sha256(current).hexdigest(),candidate_sha256=sha256(candidate).hexdigest(),candidate_tim_base64=b64encode(candidate).decode(),changes=texture_payload_changes(current,candidate),layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    result['review_key']=digest(result);_fresh(project,expected_project_path,expected_source_key);return result


def apply_file(project,review_key,**args):
    from base64 import b64decode
    result=review_file(project,**args)
    if result['review_key']!=review_key:raise ProjectError('Shared TIM replacement Apply requires its exact fresh Review')
    if result['current_sha256']==result['candidate_sha256']:raise ProjectError('Shared TIM replacement has no native change')
    project.set_texture_replacement(args['asset_id'],b64decode(result['candidate_tim_base64']))
    return dict(schema_version='legaia.field-texture-apply.v1',history_steps=1,project_changed=True,gameplay_verified=False)
