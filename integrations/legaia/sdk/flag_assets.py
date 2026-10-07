"""Derived flag assets retain source groups, never shared runtime variables."""
from copy import deepcopy
import re

from importer.core import ImportError as RetailImportError, validate_metadata_only
from .flags import build_flag_index
from .project import ProjectError

MAX_FLAG_ASSETS = 4096
MAX_FLAG_REFERENCES = 16384
MAX_SOURCE_BYTES = 4 * 1024 * 1024
_SCRIPT = re.compile(r"script://([a-z0-9_]+)/((actors/man-p1)|(scripts/man-p2))/(\d{4})")
_SCOPES = {
    "local": "dispatch_context_local_flags", "global": "host_global_flags",
    "context": "dispatch_context_flags", "system": "system_bank_encoded_selector",
    "extra": "host_extra_flags",
}
_COVERAGE = {"script_count", "partial_script_count", "unavailable_script_count"}
_GROUP_FIELDS = {
    "id", "script_id", "script_name", "owner_id", "partition", "script_status",
    "source_record", "bank", "index", "scope", "extended_target", "runtime_binding",
    "runtime_value", "references",
}
_ASSET_FIELDS = _GROUP_FIELDS | {
    "semantic_id", "asset_kind", "read_only", "grouping_layer", "name",
    "reference_count", "authored_reference_count", "coverage", "limitations",
}
_REFERENCE_FIELDS = {
    "pc", "byte_offset", "mnemonic", "bank", "operation", "index", "scope",
    "extended_target", "context_resolution", "index_semantics", "status", "runtime_value",
    "retail_index", "authored_index", "effective_index", "flag_operand_id",
}
_WRAPPER_FIELDS = {"kind", "layer", "scene_id"}


def _reject(reason):
    raise ProjectError("Invalid flag asset: " + reason)


def _integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def _text(value, maximum=8192):
    return isinstance(value, str) and 0 < len(value) <= maximum


def _metadata(value):
    try:
        validate_metadata_only(value)
    except (RetailImportError, AttributeError) as exc:
        raise ProjectError("Invalid flag asset metadata: " + str(exc)) from exc
    # Generic metadata validation permits hex/text fields; this adapter does not.
    if isinstance(value, dict):
        forbidden = {"text", "raw_hex", "encoded_hex", "tokens", "scene_name_bytes_hex", "rgba", "stp"}
        if any(not isinstance(key, str) or key.lower() in forbidden for key in value):
            _reject("contains payload fields")
        for child in value.values():
            _metadata(child)
    elif isinstance(value, list):
        for child in value:
            _metadata(child)


def _coverage(value):
    if not isinstance(value, dict) or set(value) != _COVERAGE:
        _reject("coverage shape")
    if any(not _integer(value[key], 0, 1024) for key in _COVERAGE):
        _reject("coverage bounds")
    if value['partial_script_count'] + value['unavailable_script_count'] > value['script_count']:
        _reject("coverage counts")


def validate_flag_asset(record):
    """Validate adapter or registered metadata and return it without mutation."""
    if not isinstance(record, dict) or not _ASSET_FIELDS <= set(record) or set(record) - _ASSET_FIELDS - _WRAPPER_FIELDS:
        _reject("record shape")
    if (record['asset_kind'] != 'flag' or record['read_only'] is not True or
            record['grouping_layer'] != 'retail' or record['runtime_binding'] != 'unresolved' or
            record['runtime_value'] is not None):
        _reject("runtime identity or asset kind")
    script = _SCRIPT.fullmatch(record['script_id']) if isinstance(record['script_id'], str) else None
    if script is None:
        _reject("source script identity")
    scene, path, _, _, index_text = script.groups()
    partition = 1 if path == 'actors/man-p1' else 2
    owner = record['script_id'].replace('script://', 'scene://', 1)
    if (record['owner_id'] != owner or type(record['partition']) is not int or record['partition'] != partition or
            not _text(record['script_name']) or not _text(record['name'])):
        _reject("source owner or label")
    if (record.get('kind', 'flag') != 'flag' or record.get('layer', 'derived') != 'derived' or
            record.get('scene_id', 'scene://' + scene) != 'scene://' + scene):
        _reject("registered identity")
    bank, target, index = record['bank'], record['extended_target'], record['index']
    if not isinstance(bank, str) or bank not in _SCOPES or record['scope'] != _SCOPES[bank]:
        _reject("flag bank or scope")
    if not _integer(index, 0, 65535 if bank == 'system' else 31):
        _reject("encoded selector bounds")
    if target is not None and not _integer(target, 0, 255):
        _reject("extended target bounds")
    context = 'current' if target is None else f'extended-{target}'
    identity = record['script_id'].replace('script://', 'flag-reference://', 1) + f'/{context}/{bank}/{index}'
    if record['id'] != identity or record['semantic_id'] != identity:
        _reject("source group identity")
    if record['script_status'] not in ('decoded_supported_paths', 'partial'):
        _reject("source script status")
    source = record['source_record']
    if (not isinstance(source, dict) or source.get('partition') != partition or
            type(source.get('partition')) is not int or source.get('record_index') != int(index_text) or
            type(source.get('record_index')) is not int or
            not _integer(source.get('byte_offset'), 0, MAX_SOURCE_BYTES) or
            not _integer(source.get('byte_length'), 1, MAX_SOURCE_BYTES) or
            source['byte_offset'] + source['byte_length'] > MAX_SOURCE_BYTES or
            not _text(source.get('byte_coordinate_space'), 128) or
            not isinstance(source.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', source['sha256'])):
        _reject("source locator or hash")
    references = record['references']
    if not isinstance(references, list) or not 1 <= len(references) <= MAX_FLAG_REFERENCES:
        _reject("reference count bounds")
    seen, authored_count = set(), 0
    for ref in references:
        if not isinstance(ref, dict) or set(ref) not in (_REFERENCE_FIELDS,_REFERENCE_FIELDS|{'authored_qualification'}):
            _reject("reference shape")
        pc = ref['pc']
        if (not _integer(pc, 0, MAX_SOURCE_BYTES) or pc >= source['byte_length'] or pc in seen or
                type(ref['byte_offset']) is not int or ref['byte_offset'] != source['byte_offset'] + pc):
            _reject("reference source PC")
        seen.add(pc)
        if (ref['bank'] != bank or type(ref['index']) is not int or ref['index'] != index or
                type(ref['retail_index']) is not int or ref['retail_index'] != index or
                ref['scope'] != _SCOPES[bank] or ref['extended_target'] != target or
                type(ref['extended_target']) is not type(target) or ref['runtime_value'] is not None):
            _reject("reference differs from retail group")
        if (ref['context_resolution'] != ('current_script_context' if target is None else 'extended_target_unresolved') or
                ref['index_semantics'] != ('encoded_selector_not_resolved_runtime_bit' if bank == 'system' else 'operand_masked_to_five_bits') or
                ref['status'] != ('bank_width_unresolved' if bank == 'local' and index >= 16 else 'encoded_reference')):
            _reject("reference semantics")
        mnemonic, operation = ref['mnemonic'], ref['operation']
        prefix = {'local': 'LFLAG', 'global': 'GFLAG', 'context': 'CFLAG', 'system': 'SYSFLAG'}.get(bank)
        ordinary = operation in ('set', 'clear', 'test') and prefix is not None and mnemonic == prefix + '_' + operation.upper()
        branch = operation == 'test' and ((mnemonic == 'FLAG_WORD_BRANCH' and bank in ('local', 'global', 'context')) or
                                         (mnemonic == 'COND_JMP' and bank == 'extra'))
        if not ordinary and not branch:
            _reject("reference mnemonic or operation")
        editable = ordinary and bank in ('local', 'global', 'context')
        operand_id = record['script_id'] + f'/flag-bit/{pc:04x}' if editable else None
        if ref['flag_operand_id'] != operand_id:
            _reject("flag operand identity")
        authored = ref['authored_index']
        qualified='authored_qualification' in ref
        if qualified:
            from .flag_qualification import validate
            validate(ref['authored_qualification'],record['owner_id'],operand_id,source['sha256'],pc,mnemonic,target,index,authored)
        if authored is not None:
            if not editable or not _integer(authored, 0, 31):
                _reject("authored selector")
            if (record['script_status'] != 'decoded_supported_paths' and not qualified or
                    bank == 'local' and (index >= 16 or authored >= 16) or
                    mnemonic == 'CFLAG_SET' and (index == 8 or authored == 8) or
                    mnemonic == 'CFLAG_CLEAR' and (index == 10 or authored == 10)):
                _reject("unsupported authored width or context side effect")
            authored_count += 1
        if type(ref['effective_index']) is not int or ref['effective_index'] != (index if authored is None else authored):
            _reject("effective selector differs from authored layer")
    if (type(record['reference_count']) is not int or record['reference_count'] != len(references) or
            type(record['authored_reference_count']) is not int or record['authored_reference_count'] != authored_count):
        _reject("reference layer counts")
    _coverage(record['coverage'])
    if (not isinstance(record['limitations'], list) or len(record['limitations']) > 256 or
            any(not _text(row) for row in record['limitations'])):
        _reject("limitations")
    _metadata(record)
    return record


def build_flag_assets(catalog, authored=None,qualifications=None):
    """Adapt an existing decoder catalog; no decoding or source reads occur here."""
    if not isinstance(catalog, dict) or not isinstance(catalog.get('assets'), list):
        _reject("catalog shape")
    assets = catalog['assets']
    if any(not isinstance(asset, dict) for asset in assets):
        _reject("catalog record shape")
    if not any('flag_references' in asset for asset in assets):
        return []
    if len(assets) > 8192:
        _reject("source catalog count bounds")
    scripts = [asset for asset in assets if asset.get('asset_kind') == 'script']
    if not isinstance(catalog.get('scene'), str) or not re.fullmatch('[a-z0-9_]+', catalog['scene']):
        _reject("catalog scene identity")
    _coverage({key: catalog.get(key) for key in _COVERAGE})
    if catalog['script_count'] != len(scripts):
        _reject("catalog script count")
    required = {'semantic_id', 'name', 'source_record', 'status', 'flag_references'}
    reference_count = 0
    for script in scripts:
        if not required <= set(script) or not isinstance(script['flag_references'], list):
            _reject("script flag contract")
        identifier = script['semantic_id']
        parsed = _SCRIPT.fullmatch(identifier) if isinstance(identifier, str) else None
        owner = script.get('owner_semantic_id') or script.get('actor_semantic_id')
        if (parsed is None or parsed.group(1) != catalog['scene'] or
                owner != identifier.replace('script://', 'scene://', 1) or
                not _text(script['name']) or not isinstance(script['source_record'], dict) or
                script['status'] not in ('decoded_supported_paths', 'partial', 'unavailable')):
            _reject("script owner contract")
        reference_count += len(script['flag_references'])
        if reference_count > MAX_FLAG_REFERENCES:
            _reject("asset or reference count exceeds discovery bounds")
    if (catalog['partial_script_count'] != sum(script['status'] == 'partial' for script in scripts) or
            catalog['unavailable_script_count'] != sum(script['status'] == 'unavailable' for script in scripts)):
        _reject("catalog script coverage")
    try:
        index = build_flag_index(catalog, authored,qualifications)
    except (KeyError, TypeError, IndexError, AttributeError, RetailImportError) as exc:
        raise ProjectError("Invalid flag asset catalog: " + str(exc)) from exc
    groups = index['groups']
    if len(groups) > MAX_FLAG_ASSETS or index['reference_count'] > MAX_FLAG_REFERENCES:
        _reject("asset or reference count exceeds discovery bounds")
    records, seen = [], set()
    for group in groups:
        record = deepcopy(group)
        target = record['extended_target']
        context = 'current script context' if target is None else f'unresolved extended target {target}'
        record.update(semantic_id=group['id'], asset_kind='flag', read_only=True, grouping_layer='retail',
                      name=f"{group['bank'].title()} {group['index']} · {context} · {group['script_name']}",
                      reference_count=len(group['references']),
                      authored_reference_count=sum(ref['authored_index'] is not None for ref in group['references']),
                      coverage=deepcopy(index['coverage']), limitations=list(index['limitations']))
        validate_flag_asset(record)
        if record['id'] in seen or not record['script_id'].startswith('script://' + catalog['scene'] + '/'):
            _reject("duplicate or foreign catalog identity")
        seen.add(record['id'])
        record['references'].sort(key=lambda ref: ref['pc'])
        records.append(record)
    return sorted(records, key=lambda record: record['id'])
