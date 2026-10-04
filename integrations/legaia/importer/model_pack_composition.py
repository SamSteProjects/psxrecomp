"""Compose source-addressed patches before qualified model and ANM relocation."""
from hashlib import sha256

from .core import ImportError, parse_scene_assets, decompress_lzs
from .model_pack_archive import _archive, rebuild_model_pack_entry
from .prot_layout import locate_physical_span


def compose_model_pack_archive(source, expected_sha256, requests, patches=(), *, header_offset=0):
    """Patches use original PROT-relative offsets and exact equal-length preimages.

    Relocation follows patch composition, so old offsets are never used against
    a grown archive. Selected packs must still match their qualified source hash.
    No ISO metadata or physical disc is written by this transform.
    """
    if not isinstance(source, bytes) or sha256(source).hexdigest() != expected_sha256:
        raise ImportError('Model composition archive source hash changed')
    archive = _archive(source)
    if type(header_offset) is not int or header_offset not in (0, 2048) or archive.header_offset != header_offset:
        raise ImportError('Model composition archive header changed')
    if not isinstance(requests, (list, tuple)) or not 1 <= len(requests) <= 32:
        raise ImportError('Model composition requires a bounded relocation batch')
    identities = set();tables = {}
    for request in requests:
        animation = isinstance(request,dict) and request.get('kind') == 'animation-bank'
        fields = ({'kind','entry_index','table_offset','descriptor_index','expected_bank_sha256','bank'} if animation else
                  {'entry_index', 'descriptor_index', 'expected_pack_sha256', 'replacements'})
        if (not isinstance(request, dict) or set(request) != fields
                or type(request['entry_index']) is not int or type(request['descriptor_index']) is not int):
            raise ImportError('Model composition relocation request is malformed')
        table_offset = request.get('table_offset',0)
        if type(table_offset) is not int or table_offset<0:
            raise ImportError('Resource composition table locator is malformed')
        tables.setdefault(request['entry_index'],set()).add(table_offset)
        if len(tables[request['entry_index']])>1:
            raise ImportError('Resource composition cannot relocate multiple distinct tables in one physical owner')
        identity = (request['entry_index'],table_offset,request['descriptor_index'])
        if identity in identities:
            raise ImportError('Model composition duplicates a resource request')
        identities.add(identity)
    if not isinstance(patches, (list, tuple)) or len(patches) > 4096:
        raise ImportError('Model composition patches exceed the batch budget')
    header_end = header_offset + archive.toc[0]*2048
    prepared = []
    for patch in patches:
        if (not isinstance(patch, dict) or set(patch) != {'offset', 'source_sha256', 'payload'}
                or type(patch['offset']) is not int or not isinstance(patch['payload'], bytes)
                or not patch['payload'] or not header_end <= patch['offset'] < len(source)
                or patch['offset']+len(patch['payload']) > len(source)):
            raise ImportError('Model composition patch bounds or envelope changed')
        start, payload = patch['offset'], patch['payload']
        if sha256(source[start:start+len(payload)]).hexdigest() != patch['source_sha256']:
            raise ImportError('Model composition patch preimage changed')
        prepared.append((start, payload))
    prepared.sort(key=lambda row:row[0])
    if any(a+len(payload)>b for (a,payload),(b,_) in zip(prepared, prepared[1:])):
        raise ImportError('Model composition patches overlap')
    working = bytearray(source)
    for start,payload in prepared:
        working[start:start+len(payload)] = payload
    working = bytes(working)
    patched_sha256 = sha256(working).hexdigest()
    reports = []
    ordered=sorted(requests,key=lambda row:(row['entry_index'],row.get('table_offset',0),row['descriptor_index']))
    for request in ordered:
        if request.get('kind') == 'animation-bank':
            from .animation_bank_growth import rebuild_animation_bank_entry
            working,report=rebuild_animation_bank_entry(working,sha256(working).hexdigest(),
                **{k:v for k,v in request.items() if k!='kind'},header_offset=header_offset)
        else:
            working, report = rebuild_model_pack_entry(working, sha256(working).hexdigest(),
                **request, header_offset=header_offset)
        reports.append(report)
    reopened = _archive(working)
    for request,report in zip(ordered,reports):
        entry = reopened.entry(request['entry_index'])
        span = locate_physical_span(reopened, entry.start_lba*2048)
        raw = working[span['byte_offset']:span['byte_offset']+span['byte_length']]
        table = parse_scene_assets(raw, entry.index,request.get('table_offset',0))
        descriptor = table.descriptors[request['descriptor_index']]
        offset=request.get('table_offset',0)
        end = min([offset+d.data_offset for d in table.descriptors if d.data_offset > descriptor.data_offset]+[len(raw)])
        pack,_ = decompress_lzs(raw[offset+descriptor.data_offset:end], descriptor.size)
        resource_audit='bank_audit' if request.get('kind')=='animation-bank' else 'pack_audit'
        if sha256(pack).hexdigest() != report['carrier'][resource_audit]['proposed_sha256']:
            raise ImportError('Model composition final reopened pack changed')
    return working, dict(schema_version='legaia.model-pack-composition.v1', source_sha256=expected_sha256,
        patched_sha256=patched_sha256, proposed_sha256=sha256(working).hexdigest(),
        patch_count=len(prepared), patched_bytes=sum(len(payload) for _,payload in prepared),
        resources=reports, final_packs_verified=True, final_animation_banks_verified=True,growth_bytes=len(working)-len(source),
        disc_relocation_required=len(working)!=len(source), build_ready=False, gameplay_verified=False)
