"""Source-bound saved World ANM channels; immutable records remain separate."""
from copy import deepcopy
from hashlib import sha256
import re
from importer.pipeline import _disc_context,_bounded_scene_range
from importer.worldmap_geometry import KINGDOM_BASES,_kingdom_table,_slot
from importer.worldmap_animation_authoring import patch_world_animation_bank
from importer.core import ImportError
from .project import ProjectError

COMPONENT='WorldAnimationChannels'
SCHEMA='legaia.world-animation-channels.v1'
HASH=re.compile(r'[0-9a-f]{64}')


def owner(scene):
    if not isinstance(scene,str) or scene not in KINGDOM_BASES:raise ProjectError('World animation owner requires a supported kingdom')
    return f'worldmap://{scene}/animation-channels'


def load_bank(project,scene):
    owner(scene)
    if not project.disc_path or not project.imports:raise ProjectError('World animation requires imported retail disc evidence')
    with _disc_context(project.disc_path) as (_,disc_hash,mapping,archive):
        if {d['source']['disc_identity'] for d in project.imports.values()}!={'sha256:'+disc_hash}:
            raise ProjectError('World animation disc differs from imported provenance')
        start,end=_bounded_scene_range(archive,mapping,scene);base=KINGDOM_BASES[scene]
        if start!=base-2 or not start<=base<base+1<end:raise ProjectError('World animation carrier differs from its kingdom')
        _,_,_,bundle,carrier=_kingdom_table(archive,base);bank,source=_slot(bundle,carrier,4)
    if source['descriptor_type']!=5:raise ProjectError('World animation requires a native type-5 bank')
    return bank,source,disc_hash


def normalize(audit):
    channels={}
    for row in audit['channels']:
        field,axis=row['field'].split('.');key=(row['frame_index'],row['object_index'])
        entry=channels.setdefault(key,dict(frame_index=key[0],object_index=key[1]))
        entry.setdefault(field,{})[axis]=row['after_value']
    return [channels[key] for key in sorted(channels)]


def validate(project,identifier,value):
    if (not isinstance(value,dict) or set(value)!={'schema_version','scene','source_disc_sha256','source_bank_sha256','entries'}
            or value['schema_version']!=SCHEMA or identifier!=owner(value['scene'])
            or any(not isinstance(value[k],str) or not HASH.fullmatch(value[k]) for k in ('source_disc_sha256','source_bank_sha256'))
            or not isinstance(value['entries'],dict) or not 1<=len(value['entries'])<=4096):
        raise ProjectError('World animation binding requires exact source-owned bounded entries')
    if {d['source']['disc_identity'] for d in project.imports.values()}!={'sha256:'+value['source_disc_sha256']}:
        raise ProjectError('World animation binding has a foreign imported disc')
    count=0
    for index,entry in value['entries'].items():
        if (not isinstance(index,str) or not re.fullmatch(r'[0-9]{4}',index) or int(index)>4095
                or not isinstance(entry,dict) or set(entry)!={'source_record_sha256','edits'}
                or not isinstance(entry['source_record_sha256'],str) or not HASH.fullmatch(entry['source_record_sha256'])
                or not isinstance(entry['edits'],list) or not entry['edits']):
            raise ProjectError('World animation entry requires immutable record identity and changed channels')
        count+=len(entry['edits'])
    if count>4096:raise ProjectError('World animation binding exceeds the channel edit budget')
    return deepcopy(value)


def compose(project,scene,bank,disc_hash):
    components=project.overrides.get(owner(scene))
    if components is None:return bank,[]
    if not isinstance(components,dict) or set(components)!={COMPONENT}:raise ProjectError('World animation owner accepts only its dedicated component')
    binding=validate(project,owner(scene),components[COMPONENT])
    if binding['source_disc_sha256']!=disc_hash or binding['source_bank_sha256']!=sha256(bank).hexdigest():
        raise ProjectError('World animation bank changed from its saved source')
    candidate=bank;audits=[]
    for index,entry in sorted(binding['entries'].items()):
        try:candidate,audit=patch_world_animation_bank(candidate,sha256(candidate).hexdigest(),int(index),entry['source_record_sha256'],entry['edits'])
        except ImportError as exc:raise ProjectError(str(exc)) from exc
        if normalize(audit)!=entry['edits']:raise ProjectError('World animation entries must contain canonical changed axes')
        audits.append(audit)
    return candidate,audits


def verify(project,scene):
    bank,source,disc_hash=load_bank(project,scene)
    current,audits=compose(project,scene,bank,disc_hash)
    return bank,current,source,disc_hash,audits
