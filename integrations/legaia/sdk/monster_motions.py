"""Canonical Retail-relative monster frame ownership and composed slot replay."""
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError
from importer.monster_motion_authoring import patch
from importer.monster_motion import frame
from importer.core import ImportError as NativeError


def current_clip(data,clip):
    value=deepcopy(clip);source=value['source_record'];at=source['byte_offset'];end=at+source['byte_length']
    source['sha256']=sha256(data[at:end]).hexdigest();source['entry_sha256']=sha256(data[source['entry_offset']:source['entry_end']]).hexdigest()
    return value


def compose(original,catalog,monster_id,values,current=None,project=None):
    result=bytearray(original if current is None else current)
    for identifier,binding in sorted(values.items()):
        clip=next((c for c in catalog['animations'] if c['semantic_id']==identifier),None)
        if clip is None:raise ProjectError('Monster motion owner is absent from its source')
        if clip['monster_id']!=monster_id:continue
        keys={'schema_version','asset_id','source_record','edits','current_motion_sha256','current_entry_sha256'}
        if not isinstance(binding,dict) or set(binding) not in (keys,keys|{'glb_import'}) or binding['schema_version']!='legaia.monster-motion-override.v1' or binding['asset_id']!=identifier or binding['source_record']!=clip['source_record'] or not clip['preview_supported'] or not isinstance(binding['edits'],list) or not 1<=len(binding['edits'])<=clip['part_count']*clip['frame_count']:raise ProjectError('Monster motion ownership changed')
        if 'glb_import' in binding:
            from .monster_motion_glb import validate_input
            if project is None:raise ProjectError('Monster GLB replay requires its owning project')
            validate_input(project,original,clip,binding['glb_import'])
        cursor=original;previous=(-1,-1)
        for edit in binding['edits']:
            if not isinstance(edit,dict) or set(edit)!={'frame_index','part_index','translation','rotation_psx'}:raise ProjectError('Monster motion ledger requires complete typed frame channels')
            pair=(edit['frame_index'],edit['part_index'])
            if any(type(n) is not int for n in pair) or pair<=previous:raise ProjectError('Monster motion ledger is duplicated or noncanonical')
            try:
                transforms,_=frame(original,clip,edit['frame_index']);part=edit['part_index']
                if not 0<=part<clip['part_count'] or transforms[part]['translation']==edit['translation'] and transforms[part]['rotation_psx']==edit['rotation_psx']:raise NativeError('Monster ledger contains an invalid or unchanged Retail part')
                cursor,_=patch(cursor,current_clip(cursor,clip),**edit)
            except (NativeError,TypeError,ValueError) as e:raise ProjectError('Monster motion ledger cannot replay') from e
            previous=pair
        source=clip['source_record'];at=source['byte_offset'];end=at+source['byte_length'];derived=current_clip(cursor,clip)
        if binding['current_motion_sha256']!=derived['source_record']['sha256'] or binding['current_entry_sha256']!=derived['source_record']['entry_sha256']:raise ProjectError('Monster Current motion replay hashes changed')
        result[at:end]=cursor[at:end]
    return bytes(result)


def validate(project,values):
    from importer.pipeline import _disc_context
    from importer.monster_archive import decode_catalog,block
    from .battle_character_resources import _disc
    if not isinstance(values,dict) or len(values)>1811:raise ProjectError('Monster motion owner count exceeds source bounds')
    if not values:return {}
    retained={}
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        raw=archive.read_entry(archive.entry(867));catalog=decode_catalog(raw,disc);_disc(project,catalog)
        slots=set()
        for identifier in values:
            clip=next((c for c in catalog['animations'] if c['semantic_id']==identifier),None)
            if clip is None:raise ProjectError('Monster motion owner is unqualified')
            slots.add(clip['monster_id'])
            receipt=values[identifier].get('glb_import') if isinstance(values[identifier],dict) else None
            if receipt:
                if not isinstance(receipt,dict):raise ProjectError('Monster retained motion receipt changed')
                for kind in ('glb','source_motion'):
                    size=receipt.get(kind+'_byte_length');key=receipt.get(kind+'_sha256')
                    if type(size) is not int or size<1 or not isinstance(key,str):raise ProjectError('Monster retained motion input size changed')
                    retained[(kind,key)]=size
        if sum(retained.values())>64*1024*1024:raise ProjectError('Monster active motion inputs exceed 64 MiB')
        for identifier in slots:original,_=block(raw,identifier);compose(original,catalog,identifier,values,project=project)
    return deepcopy(values)
