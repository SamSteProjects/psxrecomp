"""Fixed-width native VAB parameters, without sample/layout allocation.

Widths and offsets follow pinned VAB header/ProgAtr/VagAtr structures. Ranges
are encoded integer ranges, not claims about audible effects or engine enums.
"""
from hashlib import sha256
from .core import ImportError
from .audio_bank import inspect_bank, bank_from_entry

MAX_EDITS = 256
# (record-relative offset, width, signed). Counts and reserved words are absent.
HEADER_FIELDS = {'master_volume': (24,1,False), 'pan': (25,1,False),
                 'attributes1': (26,1,False), 'attributes2': (27,1,False)}
PROGRAM_FIELDS = {'volume': (1,1,False), 'priority': (2,1,False),
                  'mode': (3,1,False), 'pan': (4,1,False), 'attributes': (6,2,False)}
TONE_FIELDS = {'priority': (0,1,False), 'mode': (1,1,False), 'volume': (2,1,False),
               'pan': (3,1,False), 'center': (4,1,False), 'shift': (5,1,False),
               'minimum_key': (6,1,False), 'maximum_key': (7,1,False),
               'vibrato_width': (8,1,False), 'vibrato_time': (9,1,False),
               'portamento_width': (10,1,False), 'portamento_time': (11,1,False),
               'pitch_bend_down': (12,1,False), 'pitch_bend_up': (13,1,False),
               'adsr1': (16,2,False), 'adsr2': (18,2,False),
               'program_operand': (20,2,True), 'sample_operand': (22,2,True)}
FIELDS = {'header': HEADER_FIELDS, 'program': PROGRAM_FIELDS, 'tone': TONE_FIELDS}


def _hash(body):
    return sha256(body).hexdigest()


def _structure(report):
    return (report['header'], report['sections'], report['bank_size_bytes'],
            [(r['slot'],r['offset'],r['tone_count']) for r in report['programs']],
            [(r['page'],r['index'],r['offset']) for r in report['tones']],
            report['samples'], report['sample_table_spacer'],
            report['sample_table_unused_nonzero'], report['consumed_sample_end'],
            report['remaining_bank_bytes'])


def _target(report, edit):
    if not isinstance(edit, dict) or not isinstance(edit.get('section'), str) or edit['section'] not in FIELDS:
        raise ImportError('Choose a VAB header, program slot or packed tone record')
    section = edit['section']
    identities = {'header': [], 'program': ['slot'], 'tone': ['page','index']}[section]
    if set(edit) != {'section','field','value',*identities} or not isinstance(edit['field'], str) or edit['field'] not in FIELDS[section]:
        raise ImportError('VAB edits require exact source identities and a supported parameter field')
    for key in identities:
        maximum = 127 if key == 'slot' else report['header']['program_count']-1 if key == 'page' else 15
        if type(edit[key]) is not int or not 0 <= edit[key] <= maximum:
            raise ImportError('VAB source slot/page/index is outside its native table')
    base = (0 if section == 'header' else 32+edit['slot']*16 if section == 'program'
            else 2080+edit['page']*512+edit['index']*32)
    relative, width, signed = FIELDS[section][edit['field']]
    minimum, maximum = (-32768,32767) if signed else (0,(1 << (width*8))-1)
    if type(edit['value']) is not int or not minimum <= edit['value'] <= maximum:
        raise ImportError('VAB parameter exceeds its encoded integer width')
    return base+relative, width, signed


def replace_bank_parameters(original, current, *, expected_source_sha256,
                            expected_current_sha256, edits):
    """Edit existing scalar fields; never allocate slots, tones or samples."""
    source, effective = inspect_bank(original), inspect_bank(current)
    if _hash(original) != expected_source_sha256 or _hash(current) != expected_current_sha256:
        raise ImportError('VAB source or Current hash differs from reviewed bytes')
    if len(original) != len(current) or _structure(source) != _structure(effective):
        raise ImportError('Current VAB must preserve source layout, counts and sample ownership')
    allowed = bytearray(len(original))
    for base, fields in [(0,HEADER_FIELDS), *[(32+i*16,PROGRAM_FIELDS) for i in range(128)],
                         *[(2080+i*32,TONE_FIELDS) for i in range(source['header']['program_count']*16)]]:
        for relative, width, _ in fields.values():
            allowed[base+relative:base+relative+width] = b'\1'*width
    if any(a != b and not allowed[i] for i,(a,b) in enumerate(zip(original,current))):
        raise ImportError('Current VAB changed bytes outside qualified parameter fields')
    if not isinstance(edits,list) or not 1 <= len(edits) <= MAX_EDITS:
        raise ImportError('VAB authoring requires one to 256 explicit parameter edits')
    output, seen, audit = bytearray(current), set(), []
    for edit in edits:
        position, width, signed = _target(source,edit)
        if position in seen:
            raise ImportError('Choose unique VAB source parameter fields')
        seen.add(position)
        output[position:position+width] = edit['value'].to_bytes(width,'little',signed=signed)
        audit.append({**edit, 'bank_byte_offset':position, 'byte_length':width, 'signed':signed,
                      'source_value':int.from_bytes(original[position:position+width],'little',signed=signed),
                      'before_value':int.from_bytes(current[position:position+width],'little',signed=signed),
                      'after_value':edit['value']})
    output = bytes(output)
    if _structure(inspect_bank(output)) != _structure(source):
        raise ImportError('Authored VAB failed layout/sample readback')
    return output, dict(source_sha256=_hash(original),before_sha256=_hash(current),after_sha256=_hash(output),
                        edits=audit,changed_bank_byte_offsets=[i for i,(a,b) in enumerate(zip(current,output)) if a!=b])


def replace_audio_bank_parameters(original, current, *, expected_source_sha256,
                                  expected_current_sha256, edits):
    """Serialize a complete qualified standalone, leading or split VAB carrier.

    This domain codec requires nonbank bytes to remain original. SDK composition
    with SEQ edits must validate each family independently before merging spans.
    """
    bank, pieces, kind = bank_from_entry(original)
    effective, current_pieces, current_kind = bank_from_entry(current)
    if _hash(original) != expected_source_sha256 or _hash(current) != expected_current_sha256:
        raise ImportError('VAB carrier source or Current hash changed')
    if len(original)!=len(current) or pieces!=current_pieces or kind!=current_kind:
        raise ImportError('Current VAB carrier changed physical piece ownership')
    allowed = bytearray(len(original))
    for piece in pieces:
        offset, size = piece['entry_offset'], piece['size_bytes']
        allowed[offset:offset+size] = b'\1'*size
    if any(a!=b and not allowed[i] for i,(a,b) in enumerate(zip(original,current))):
        raise ImportError('Current VAB carrier changed nonbank chunks or physical padding')
    replacement, audit = replace_bank_parameters(bank,effective,
        expected_source_sha256=_hash(bank),expected_current_sha256=_hash(effective),edits=edits)
    output = bytearray(current)
    for piece in pieces:
        entry, offset, size = piece['entry_offset'], piece['bank_offset'], piece['size_bytes']
        output[entry:entry+size] = replacement[offset:offset+size]
    output = bytes(output)
    reopened, reopened_pieces, reopened_kind = bank_from_entry(output)
    if reopened!=replacement or reopened_pieces!=pieces or reopened_kind!=kind:
        raise ImportError('Authored VAB carrier failed native piece readback')
    changed=[]
    for bank_offset in audit['changed_bank_byte_offsets']:
        matches=[p for p in pieces if p['bank_offset']<=bank_offset<p['bank_offset']+p['size_bytes']]
        if len(matches)!=1:raise ImportError('VAB changed byte has no unique physical owner')
        piece=matches[0];changed.append(piece['entry_offset']+bank_offset-piece['bank_offset'])
    return output,dict(source_entry_sha256=_hash(original),before_entry_sha256=_hash(current),
                       after_entry_sha256=_hash(output),carrier=kind,pieces=pieces,
                       changed_entry_byte_offsets=sorted(changed),bank=audit)
