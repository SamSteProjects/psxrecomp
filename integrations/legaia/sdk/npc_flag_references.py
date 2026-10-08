"""NPC-owned encoded flag usages; source groups never become runtime variables."""
from copy import deepcopy
from .project import ProjectError


def binding(draft, donor_proof, record, reference, script,qualified=None):
    if record['owner_id'] != draft['donor_entity_id'] or record['source_record'] != script['source_record']:
        raise ProjectError('NPC flag usage differs from its retail donor record')
    sites = [row for row in script.get('flag_references', []) if row.get('pc') == reference['pc']]
    fields = ('bank', 'index', 'scope', 'extended_target', 'operation', 'mnemonic', 'byte_offset')
    if len(sites) != 1 or any(sites[0].get(field) != reference[field] for field in fields):
        raise ProjectError('NPC flag usage differs from its unique decoded donor instruction')
    operand = reference['flag_operand_id']
    system = reference['bank'] == 'system'
    field = 'index' if system else 'bit'
    authored = draft.get('system_flags' if system else 'flags', {}).get('entries', {}).get(operand)
    bit = authored.get(field) if isinstance(authored, dict) else None
    if authored is not None:
        bank, mnemonic = reference['bank'], reference['mnemonic']
        if (not isinstance(authored, dict) or set(authored) != {field} or type(bit) is not int or not 0 <= bit <= (4095 if system else 31)
                or operand is None or qualified is None
                or system and reference['extended_target'] is not None
                or bank == 'local' and (reference['retail_index'] >= 16 or bit >= 16)
                or mnemonic == 'CFLAG_SET' and (reference['retail_index'] == 8 or bit == 8)
                or mnemonic == 'CFLAG_CLEAR' and (reference['retail_index'] == 10 or bit == 10)):
            raise ProjectError('NPC flag usage has unsupported authored bit ownership')
        if (qualified['source_record_sha256'] != donor_proof['source_record_sha256']
                or qualified['pc'] != reference['pc'] or qualified['mnemonic'] != reference['mnemonic']
                or qualified['target_context'] != reference['extended_target']
                or type(qualified['target_context']) is not type(reference['extended_target'])
                or qualified['values'][field] != reference['retail_index']
                or qualified['semantic_id'] != operand or bit > qualified['maximum']):
            raise ProjectError('NPC flag authoring qualification differs from its decoded donor instruction')
    result = dict(donor=deepcopy(donor_proof), operand_id=operand,
                retail_index=reference['retail_index'], authored_index=bit,
                effective_index=reference['retail_index'] if bit is None else bit,
                authored_operand_qualified=authored is not None)
    if system and authored is not None:
        from .flag_qualification import from_target, validate
        result['native_operand_qualification'] = validate(from_target(qualified, authored),
            draft['donor_entity_id'], operand, donor_proof['source_record_sha256'], reference['pc'],
            reference['mnemonic'], reference['extended_target'], reference['retail_index'], bit)
    return result
