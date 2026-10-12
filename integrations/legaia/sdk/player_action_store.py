"""Project-owned typed PLAYER action ledgers and immutable Retail sources."""
from copy import deepcopy
from hashlib import sha256
from functools import lru_cache
import json
import re
from importer.player_battle import actions
from importer.player_animation_authoring import patch_player_action
from importer.core import ImportError as RetailImportError
from .project import ProjectError,atomic_write,canonical


def _path(project,key):
    if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key):raise ProjectError('Invalid PLAYER action source identity')
    path=project.root/'Authored'/'PLAYER'/'ActionSources'/(key+'.bin')
    if not path.resolve().is_relative_to(project.root.resolve()):raise ProjectError('PLAYER action source escapes project root')
    return path


def retain(project,raw):
    key=sha256(raw).hexdigest();path=_path(project,key)
    if path.exists():
        if path.read_bytes()!=raw:raise ProjectError('PLAYER action source cache changed')
    else:atomic_write(path,raw)


def _compose(raw,identifier,ledger):
    slot=int(identifier[-1]);clips,_=actions(raw,slot,'0'*64);cursor=raw;reports=[]
    for key,value in sorted(ledger.items()):
        index=int(key)
        if value['source_action_sha256']!=clips[index]['source_record']['sha256']:raise ProjectError('PLAYER authored action differs from its Retail stream')
        cursor,report=patch_player_action(cursor,sha256(cursor).hexdigest(),slot,index,value['source_action_sha256'],value['edits'])
        reports.append(report)
    return cursor,reports


@lru_cache(maxsize=8)
def _cached_compose(raw,identifier,ledger_json):
    return _compose(raw,identifier,json.loads(ledger_json))


def compose(raw,identifier,binding):
    ledger=binding['actions']
    # Cache only small numeric ledgers. Every caller still verifies source
    # bytes/hash and ownership; both complete bytes and typed inputs key replay.
    if sum(len(v['edits']) for v in ledger.values())<=64:
        current,reports=_cached_compose(raw,identifier,canonical(ledger))
    else:current,reports=_compose(raw,identifier,ledger)
    return current,deepcopy(reports)


def validate(project,values,*,replays=None):
    if not isinstance(values,dict) or len(values)>4:raise ProjectError('PLAYER actions require at most four file owners')
    input_bytes=0
    for identifier,b in values.items():
        if (not isinstance(identifier,str) or not re.fullmatch('asset://legaia/models/player-battle/000[0-3]',identifier)
                or not isinstance(b,dict) or set(b)!={'schema_version','asset_id','source_record','actions','current_sha256'}
                or b['schema_version']!='legaia.player-action-override.v1' or b['asset_id']!=identifier):raise ProjectError('PLAYER action ownership changed')
        source=b['source_record']
        if (not isinstance(source,dict) or source.get('prot_entry_index')!=863+int(identifier[-1])
                or source.get('record_kind')!='adjacent_toc_bounded_player_file'
                or type(source.get('byte_length')) is not int or not 32768<source['byte_length']<=4*1024*1024):raise ProjectError('PLAYER action source footprint changed')
        path=_path(project,source.get('sha256'))
        if not path.is_file() or path.stat().st_size!=source['byte_length']:raise ProjectError('PLAYER action source cache missing or changed size')
        raw=path.read_bytes()
        if sha256(raw).hexdigest()!=source['sha256']:raise ProjectError('PLAYER action source cache hash changed')
        if not isinstance(b['actions'],dict) or not 1<=len(b['actions'])<=12:raise ProjectError('PLAYER action ledger must own existing action slots')
        for key,value in b['actions'].items():
            if (not isinstance(key,str) or not re.fullmatch('000[0-9]|001[01]',key) or not isinstance(value,dict)
                    or set(value)-{'source_action_sha256','edits','glb_import'} or not {'source_action_sha256','edits'}<=set(value) or not isinstance(value['edits'],list)
                    or not value['edits'] or len(value['edits'])>4096):raise ProjectError('PLAYER action ledger requires bounded typed channel edits')
            if 'glb_import' in value:
                from .player_action_glb import validate_input
                validate_input(project,raw,int(identifier[-1]),int(key),value['glb_import'])
                input_bytes+=value['glb_import']['glb_byte_length']+value['glb_import']['source_file_byte_length']
                if input_bytes>64*1024*1024:raise ProjectError('PLAYER retained motion inputs exceed the 64 MiB project budget')
        try:current,reports=compose(raw,identifier,b)
        except (RetailImportError,KeyError,TypeError,ValueError) as e:raise ProjectError('PLAYER action ledger cannot reproduce its native Current file') from e
        if sha256(current).hexdigest()!=b['current_sha256'] or current==raw:raise ProjectError('PLAYER action Current hash changed or has no native edits')
        if any(not report['channels'] for report in reports):raise ProjectError('PLAYER action ledger contains an unmodified action owner')
        if replays is not None:replays[identifier]=(current,reports)
    return deepcopy(values)


def effective(project,record,retail):
    b=getattr(project,'player_action_overrides',{}).get(record['semantic_id'])
    if b is None:return retail,[]
    replays={};validate(project,{record['semantic_id']:b},replays=replays)
    if b['source_record']!=record['source_record'] or sha256(retail).hexdigest()!=b['source_record']['sha256']:raise ProjectError('PLAYER action Retail source changed')
    return replays[record['semantic_id']]


def publish(project,record,retail,value):
    if project.mode!='edit':raise ProjectError('PLAYER action Apply requires Edit mode')
    retain(project,retail);before=deepcopy(project.player_action_overrides);after=deepcopy(before)
    if value is None:after.pop(record['semantic_id'],None)
    else:after[record['semantic_id']]=deepcopy(value)
    validate(project,after)
    if after==before:raise ProjectError('PLAYER action Apply has no native changes')
    project.player_action_overrides=after;project.undo_stack.append(dict(target='player_action_overrides',before=before,after=deepcopy(after),label='PLAYER action channels'));project.redo_stack.clear()
