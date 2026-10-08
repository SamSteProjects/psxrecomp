"""Independent source-bound flag authoring proof, not general script coverage."""
from copy import deepcopy
import re
from .project import ProjectError


def from_target(target,values):
    system=target['mnemonic'].startswith('SYSFLAG_')
    field='index' if system else 'bit'
    return dict(schema_version='legaia.system-flag-operand-qualification.v1' if system else 'legaia.flag-operand-qualification.v1',owner_id=target['owner_id'],
                operand_id=target['semantic_id'],source_record_sha256=target['source_record_sha256'],
                pc=target['pc'],mnemonic=target['mnemonic'],extended_target=target['target_context'],
                retail_index=target['values'][field],authored_index=values[field],maximum=target['maximum'])


def validate(value,owner,operand,source_hash,pc,mnemonic,target,retail,authored):
    keys={'schema_version','owner_id','operand_id','source_record_sha256','pc','mnemonic','extended_target','retail_index','authored_index','maximum'}
    system=isinstance(mnemonic,str) and mnemonic.startswith('SYSFLAG_')
    maximum=4095 if system else 15 if isinstance(mnemonic,str) and mnemonic.startswith('LFLAG_') else 31
    family='system-flag' if system else 'flag-bit'
    schema='legaia.system-flag-operand-qualification.v1' if system else 'legaia.flag-operand-qualification.v1'
    if (not isinstance(value,dict) or set(value)!=keys or value['schema_version']!=schema
            or not isinstance(owner,str) or re.fullmatch(r'scene://[a-z0-9_]+/(actors/man-p1|scripts/man-p2)/[0-9]{4}',owner) is None
            or value['owner_id']!=owner or value['operand_id']!=operand or operand!='script://'+owner[8:]+f'/{family}/{pc:04x}'
            or value['source_record_sha256']!=source_hash or not isinstance(source_hash,str) or re.fullmatch('[a-f0-9]{64}',source_hash) is None
            or type(value['pc']) is not int or value['pc']!=pc or not 0<=pc<=65535
            or value['mnemonic']!=mnemonic or mnemonic not in tuple(f'{bank}_{op}' for bank in ('LFLAG','GFLAG','CFLAG','SYSFLAG') for op in ('SET','CLEAR','TEST'))
            or system and target is not None
            or value['extended_target']!=target or type(value['extended_target']) is not type(target)
            or target is not None and (type(target) is not int or not 0<=target<=255)
            or type(value['retail_index']) is not int or value['retail_index']!=retail or not 0<=retail<=maximum
            or type(value['authored_index']) is not int or value['authored_index']!=authored or not 0<=authored<=maximum
            or type(value['maximum']) is not int or value['maximum']!=maximum
            or mnemonic=='CFLAG_SET' and (retail==8 or authored==8)
            or mnemonic=='CFLAG_CLEAR' and (retail==10 or authored==10)):
        raise ProjectError('Flag native operand qualification differs from its source or authored binding')
    return deepcopy(value)
