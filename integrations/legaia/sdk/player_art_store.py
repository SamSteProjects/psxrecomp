"""Project-owned numeric art ledgers and exact original-body package overlays."""
from copy import deepcopy
from hashlib import sha256
from importer.pipeline import _disc_context
from importer.player_art_animation import discover
from importer.player_art_consumer import qualify
from importer.player_art_authoring import compose
from importer.core import ImportError as NativeError
from .project import ProjectError
from .battle_character_resources import _disc


def context(project):
    if not project.disc_path:raise ProjectError('PLAYER art ownership requires a disc-backed project')
    try:
        with _disc_context(project.disc_path) as (image, disc, _, archive):
            profile=qualify(image.read_file(image.find('SCUS_942.54')))
            catalog=discover(project.disc_path);_disc(project,catalog)
            raw=archive.read_entry(archive.entry(894))
            if sha256(raw).hexdigest()!=catalog['source_entry_sha256']:
                raise ProjectError('PLAYER art source entry changed')
    except NativeError as error:raise ProjectError(str(error)) from error
    return raw,catalog,profile


def composed_slots(raw,catalog,values):
    if not isinstance(values,dict) or len(values)>87:
        raise ProjectError('PLAYER art owners exceed the original stream catalogue')
    streams={r['semantic_id']:r for r in catalog['streams']}
    if any(identifier not in streams for identifier in values):
        raise ProjectError('PLAYER art owner is absent from the source catalogue')
    result={}
    for archive in catalog['archives']:
        owned={k:v for k,v in values.items() if streams[k]['archive_asset_id']==archive['semantic_id']}
        if not owned:continue
        at=archive['slot_index']*0x10800;original=raw[at:at+0x10800]
        try:result[archive['semantic_id']]=compose(original,catalog,archive['semantic_id'],owned)
        except (NativeError,KeyError,TypeError,ValueError) as error:
            raise ProjectError('PLAYER art owner cannot replay its complete source slot') from error
    return result


def validate(project,values):
    if not isinstance(values,dict) or len(values)>87:raise ProjectError('PLAYER art owner collection changed')
    if not values:return {}
    raw,catalog,_=context(project);composed_slots(raw,catalog,values)
    return deepcopy(values)


def prepare(project,archive,disc_hash):
    values=getattr(project,'player_art_overrides',{})
    if not isinstance(values,dict) or len(values)>87:raise ProjectError('PLAYER art Build ownership collection changed')
    if not values:return [],[]
    raw,catalog,profile=context(project)
    if catalog['source_disc_sha256']!=disc_hash:raise ProjectError('Art Build source disc changed')
    slots=composed_slots(raw,catalog,values);entry=archive.entry(894)
    overlays=[];changes=[]
    for stream in catalog['streams']:
        owner=values.get(stream['semantic_id'])
        if owner is None:continue
        source=stream['source_record'];at=source['byte_offset'];size=source['byte_length']
        slot=slots[stream['archive_asset_id']];local=at-source['slot_offset'];payload=slot[local:local+size]
        if sha256(payload).hexdigest()!=owner['current_body_sha256']:raise ProjectError('Art Build body replay changed')
        offset=(archive.node.extent_lba+entry.start_lba)*archive.SECTOR+at
        overlays.append(dict(scene='player-art-archives',offset=offset,size=size,
                             file=f'assets/player-art-{stream["player_index"]}-{stream["archive_role"]}-{stream["stream_index"]}.bin',
                             payload=payload,sha256=sha256(payload).hexdigest(),expected_sha256=source['sha256'],
                             source_kind='fixed_span_player_art_me_body',source_record=deepcopy(source),
                             consumer_profile=profile,art_decoded_before_sha256=source['decoded_sha256'],
                             art_decoded_after_sha256=owner['decoded_sha256']))
        changes.append(dict(scene='player-art-archives',semantic_id=stream['semantic_id'],field='art.native_part_frames',
                            scope='player-art-existing-body-and-decoded-counts-only',byte_offset=at,byte_length=size,
                            before_sha256=source['sha256'],after_sha256=owner['current_body_sha256'],
                            edited_part_frames=len(owner['edits'])))
    return overlays,changes
