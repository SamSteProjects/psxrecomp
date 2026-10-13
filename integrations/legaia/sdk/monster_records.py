"""Canonical sparse Retail-relative ownership for known stored header fields."""
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError
from importer.monster_record_authoring import patch,header_values
from importer.core import ImportError as NativeError


def compose(original,catalog,monster_id,values,current=None):
    if not isinstance(values,dict) or len(values)>512 or any(not isinstance(k,str) for k in values):raise ProjectError('Monster stored record owners exceed source bounds')
    result=original if current is None else current
    if not isinstance(result,bytes) or len(result)!=len(original):raise ProjectError('Monster stored record composition requires an unchanged slot extent')
    for identifier,binding in sorted(values.items()):
        record=next((r for r in catalog['records'] if r['semantic_id']==identifier),None)
        if record is None:raise ProjectError('Monster stored record owner is absent from its source')
        if record['monster_id']!=monster_id:continue
        keys={'schema_version','asset_id','source_record','edits','current_header_sha256'}
        if not isinstance(binding,dict) or set(binding)!=keys or binding['schema_version']!='legaia.monster-record-override.v1' or binding['asset_id']!=identifier or binding['source_record']!=record['source_record'] or not isinstance(binding['edits'],list) or not 1<=len(binding['edits'])<=12:
            raise ProjectError('Monster stored record ownership changed')
        edits={};previous='';retail=header_values(original)
        for row in binding['edits']:
            if not isinstance(row,dict) or set(row)!={'field','value'} or not isinstance(row['field'],str) or row['field']<=previous or row['field'] in edits or row['field'] not in retail or row['value']==retail[row['field']]:
                raise ProjectError('Monster stored record ledger is duplicated, unchanged or noncanonical')
            edits[row['field']]=row['value'];previous=row['field']
        try:
            baseline,_=patch(original,original,record,edits);candidate,_=patch(original,result,record,edits)
        except NativeError as e:raise ProjectError(str(e)) from e
        if sha256(baseline[:0x4c]).hexdigest()!=binding['current_header_sha256'] or candidate[:0x4c]!=baseline[:0x4c]:
            raise ProjectError('Monster Current stored header differs from its complete native replay')
        result=candidate
    return result


def validate(project,values):
    from importer.pipeline import _disc_context
    from importer.monster_archive import decode_catalog,block
    from .battle_character_resources import _disc
    if not isinstance(values,dict) or len(values)>512:raise ProjectError('Monster stored record owner count exceeds source bounds')
    if not values:return {}
    with _disc_context(project.disc_path) as (_,disc,_,archive):
        raw=archive.read_entry(archive.entry(867));catalog=decode_catalog(raw,disc);_disc(project,catalog)
        for identifier in values:
            record=next((r for r in catalog['records'] if r['semantic_id']==identifier),None)
            if record is None:raise ProjectError('Monster stored record owner is unqualified')
            original,_=block(raw,record['monster_id']);compose(original,catalog,record['monster_id'],values)
    return deepcopy(values)
