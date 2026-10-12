"""Immutable PLAYER native candidates/GLB inputs with one project history step."""
from copy import deepcopy
from hashlib import sha256
import re
from .project import ProjectError,atomic_write
from importer.player_battle import table


def _path(project,kind,key):
    if kind not in ('Candidates','Inputs') or not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key):raise ProjectError('Invalid PLAYER retained content identity')
    path=project.root/'Authored'/'PLAYER'/kind/(key+('.bin' if kind=='Candidates' else '.glb'))
    if not path.resolve().is_relative_to(project.root.resolve()):raise ProjectError('PLAYER retained content escapes project root')
    return path


def _read(project,kind,key,length):
    path=_path(project,kind,key)
    if not path.is_file() or path.stat().st_size!=length:raise ProjectError('PLAYER retained file is missing or changed size')
    content=path.read_bytes()
    if sha256(content).hexdigest()!=key:raise ProjectError('PLAYER retained file hash changed')
    return content


def _retain(project,kind,content):
    key=sha256(content).hexdigest();path=_path(project,kind,key)
    if path.exists():_read(project,kind,key,len(content))
    else:atomic_write(path,content)
    _read(project,kind,key,len(content));return key


def validate(project,values):
    if not isinstance(values,dict) or len(values)>4:raise ProjectError('PLAYER overrides require at most four native file owners')
    sizes={}
    for identifier,b in values.items():
        if not re.fullmatch('asset://legaia/models/player-battle/000[0-3]',identifier) or not isinstance(b,dict) or set(b)!={'schema_version','asset_id','source_record','current_sha256','byte_length','inputs'} or b['schema_version']!='legaia.player-model-override.v1' or b['asset_id']!=identifier:raise ProjectError('PLAYER override ownership changed')
        source=b['source_record'];slot=int(identifier[-1])
        if not isinstance(source,dict):raise ProjectError('PLAYER retail source metadata changed')
        if source.get('prot_entry_index')!=863+slot or source.get('record_kind')!='adjacent_toc_bounded_player_file' or not re.fullmatch('[a-f0-9]{64}',source.get('sha256','')) or b['byte_length']!=source.get('byte_length') or not 32768<b['byte_length']<=4*1024*1024 or not isinstance(b['inputs'],list) or not 1<=len(b['inputs'])<=16:raise ProjectError('PLAYER override differs from its source footprint')
        current=_read(project,'Candidates',b['current_sha256'],b['byte_length']);table(current)
        for i in b['inputs']:
            if not isinstance(i,dict) or set(i)!={'sha256','byte_length','binding','review_key','base_sha256','proposed_sha256'} or not isinstance(i['byte_length'],int) or not 28<=i['byte_length']<=4*1024*1024 or not isinstance(i['binding'],dict) or any(not isinstance(i[k],str) or not re.fullmatch('[a-f0-9]{64}',i[k]) for k in ('review_key','base_sha256','proposed_sha256')) or i['binding'].get('asset_id')!=identifier:raise ProjectError('PLAYER retained input binding changed')
            _read(project,'Inputs',i['sha256'],i['byte_length'])
            if i['sha256'] in sizes and sizes[i['sha256']]!=i['byte_length']:raise ProjectError('PLAYER retained input length conflicts')
            sizes[i['sha256']]=i['byte_length']
        if b['inputs'][0]['base_sha256']!=source['sha256'] or any(i['base_sha256']!=b['inputs'][n-1]['proposed_sha256'] for n,i in enumerate(b['inputs']) if n) or b['inputs'][-1]['proposed_sha256']!=b['current_sha256']:raise ProjectError('PLAYER override input chain changed')
    if sum(sizes.values())>64*1024*1024:raise ProjectError('PLAYER retained inputs exceed 64 MiB')
    return deepcopy(values)


def effective(project,record,retail):
    binding=project.player_model_overrides.get(record['semantic_id'])
    if binding is None:return retail
    validate(project,{record['semantic_id']:binding})
    if binding['source_record']!=record['source_record'] or sha256(retail).hexdigest()!=binding['source_record']['sha256']:raise ProjectError('PLAYER override retail source changed')
    from importer.player_model_authoring import import_player_model
    from importer.core import ImportError as RetailImportError
    cursor=retail
    for i in binding['inputs']:
        if sha256(cursor).hexdigest()!=i['base_sha256']:raise ProjectError('PLAYER Current replay source changed')
        try:cursor,_=import_player_model(cursor,i['binding']['native_binding'],_read(project,'Inputs',i['sha256'],i['byte_length']))
        except (RetailImportError,KeyError) as e:raise ProjectError('PLAYER retained source cannot reproduce Current') from e
        if sha256(cursor).hexdigest()!=i['proposed_sha256']:raise ProjectError('PLAYER Current differs from retained input replay')
    current=_read(project,'Candidates',binding['current_sha256'],binding['byte_length'])
    if cursor!=current:raise ProjectError('PLAYER Current bytes differ from their complete retained input chain')
    return current


def publish(project,record,base,proposed,input_bytes,binding,review_key):
    if project.mode!='edit' or not isinstance(input_bytes,bytes) or not 28<=len(input_bytes)<=4*1024*1024:raise ProjectError('PLAYER Apply requires Edit mode and a bounded retained GLB')
    before=deepcopy(project.player_model_overrides);old=before.get(record['semantic_id']);base_sha=sha256(base).hexdigest()
    if base_sha!=(old['current_sha256'] if old else record['source_record']['sha256']):raise ProjectError('PLAYER Current model changed before Apply')
    if proposed==base:raise ProjectError('PLAYER Apply has no quantized changes')
    candidate_hash=_retain(project,'Candidates',proposed);input_hash=_retain(project,'Inputs',input_bytes)
    value=dict(schema_version='legaia.player-model-override.v1',asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),current_sha256=candidate_hash,byte_length=len(proposed),inputs=deepcopy(old['inputs']) if old else [])
    value['inputs'].append(dict(sha256=input_hash,byte_length=len(input_bytes),binding=deepcopy(binding),review_key=review_key,base_sha256=base_sha,proposed_sha256=candidate_hash));after=deepcopy(before);after[record['semantic_id']]=value;validate(project,after)
    project.player_model_overrides=after;project.undo_stack.append(dict(target='player_model_overrides',before=before,after=deepcopy(after),label='PLAYER native model import'));project.redo_stack.clear();return deepcopy(value)
