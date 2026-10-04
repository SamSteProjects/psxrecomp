"""Compose source-addressed patches before qualified model, TIM, ANM and MAN relocation."""
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
        texture = isinstance(request,dict) and request.get('kind') in ('texture-pack','texture-layout-pack','texture-addition-pack')
        texture_layout = texture and request['kind'] in ('texture-layout-pack','texture-addition-pack')
        raw_texture = isinstance(request,dict) and request.get('kind') in ('texture-layout-raw','texture-addition-raw')
        animation = isinstance(request,dict) and request.get('kind') == 'animation-bank'
        streaming = isinstance(request,dict) and request.get('kind') == 'streaming-animation-bank'
        streaming_man = isinstance(request,dict) and request.get('kind') == 'streaming-man'
        compressed_man = isinstance(request,dict) and request.get('kind') == 'compressed-man'
        raw_resource = streaming or streaming_man
        fields = ({'kind','entry_index','expected_pack_sha256','edits'} if raw_texture else
                  {'kind','entry_index','table_offset','descriptor_index','expected_pack_sha256','pack','layout_edits'} if texture_layout else
                  {'kind','entry_index','table_offset','descriptor_index','expected_pack_sha256','pack'} if texture else
                  {'kind','entry_index','table_offset','descriptor_index','source_man_sha256','candidate'} if compressed_man else
                  {'kind','entry_index','chunk_header_offset','source_man_sha256','candidate'} if streaming_man else
                  {'kind','entry_index','chunk_header_offset','expected_bank_sha256','bank'} if streaming else
                  {'kind','entry_index','table_offset','descriptor_index','expected_bank_sha256','bank'} if animation else
                  {'entry_index', 'descriptor_index', 'expected_pack_sha256', 'replacements'})
        if isinstance(request,dict) and request.get('kind') in ('texture-addition-pack','texture-addition-raw'):
            fields = fields | {'slot_additions'}
            additions=request.get('slot_additions')
            if not isinstance(additions,list) or not 1<=len(additions)<=128:
                raise ImportError('Texture addition composition requires a bounded nonempty TIM batch')
        if (not isinstance(request, dict) or set(request) != fields
                or type(request['entry_index']) is not int or type(0 if raw_texture else request['chunk_header_offset'] if raw_resource else request['descriptor_index']) is not int):
            raise ImportError('Model composition relocation request is malformed')
        if raw_texture:
            if request['entry_index'] in tables:
                raise ImportError('Raw texture composition requires one uniquely owned standalone pack')
            tables[request['entry_index']]={'texture-layout-raw'}
            identities.add((request['entry_index'],'texture-layout-raw'))
            continue
        if raw_resource:
            kinds=tables.setdefault(request['entry_index'],set())
            if request['chunk_header_offset']<0 or request['chunk_header_offset']%4 or request['kind'] in kinds or any(kind not in ('streaming-man','streaming-animation-bank') for kind in kinds):
                raise ImportError('Raw composition requires one word-aligned resource of each type per physical owner')
            kinds.add(request['kind'])
            identities.add((request['entry_index'],request['kind'],request['chunk_header_offset']))
            continue
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
    reports = [];completed=[]
    ordered=sorted(requests,key=lambda row:(row['entry_index'],row.get('table_offset',row.get('chunk_header_offset',0)),row.get('descriptor_index',0)))
    for request in ordered:
        if request.get('kind') in ('streaming-animation-bank','streaming-man'):
            from .streaming_animation_bank import remap_streaming_header
            request=dict(request,chunk_header_offset=remap_streaming_header(request['entry_index'],request['chunk_header_offset'],3 if request['kind']=='streaming-man' else 5,reports))
        if request.get('kind') == 'streaming-man':
            from .prot_rebuild import rebuild_streaming_man_entry
            working,report=rebuild_streaming_man_entry(working,sha256(working).hexdigest(),
                **{k:v for k,v in request.items() if k!='kind'},header_offset=header_offset)
        elif request.get('kind') == 'streaming-animation-bank':
            from .streaming_animation_bank import rebuild_streaming_animation_bank_entry
            working,report=rebuild_streaming_animation_bank_entry(working,sha256(working).hexdigest(),
                **{k:v for k,v in request.items() if k!='kind'},header_offset=header_offset)
        elif request.get('kind') == 'compressed-man':
            from .prot_rebuild import rebuild_man_entry
            from .core import parse_man
            if not isinstance(request['candidate'],bytes) or not 0<len(request['candidate'])<=4*1024*1024:
                raise ImportError('Compressed MAN composition candidate exceeds its byte budget')
            parse_man(request['candidate'])
            current=_archive(working);raw=current.read_entry(current.entry(request['entry_index']))
            table=parse_scene_assets(raw,request['entry_index'],request['table_offset'])
            man_rows=[d for d in table.descriptors if d.type_byte==3 and d.size]
            if len(man_rows)!=1 or man_rows[0].index!=request['descriptor_index']:
                raise ImportError('Compressed MAN composition descriptor identity changed')
            working,report=rebuild_man_entry(working,sha256(working).hexdigest(),
                **{k:v for k,v in request.items() if k not in ('kind','descriptor_index')},header_offset=header_offset)
            report['entry_index']=request['entry_index']
        elif request.get('kind') in ('texture-layout-raw','texture-addition-raw'):
            from .texture_pack_growth import rebuild_raw_texture_pack_entry
            working,report=rebuild_raw_texture_pack_entry(working,sha256(working).hexdigest(),
                **{k:v for k,v in request.items() if k!='kind'},header_offset=header_offset)
        elif request.get('kind') in ('texture-pack','texture-layout-pack','texture-addition-pack'):
            from .texture_pack_growth import rebuild_texture_pack_entry
            working,report=rebuild_texture_pack_entry(working,sha256(working).hexdigest(),
                **{k:v for k,v in request.items() if k!='kind'},header_offset=header_offset)
        elif request.get('kind') == 'animation-bank':
            from .animation_bank_growth import rebuild_animation_bank_entry
            working,report=rebuild_animation_bank_entry(working,sha256(working).hexdigest(),
                **{k:v for k,v in request.items() if k!='kind'},header_offset=header_offset)
        else:
            working, report = rebuild_model_pack_entry(working, sha256(working).hexdigest(),
                **request, header_offset=header_offset)
        reports.append(report)
        completed.append(request)
    reopened = _archive(working)
    for index,(request,report) in enumerate(zip(completed,reports)):
        if request.get('kind') in ('streaming-animation-bank','streaming-man'):
            from .streaming_animation_bank import remap_streaming_header,verify_rebuilt_streaming_animation_banks
            final_offset=remap_streaming_header(request['entry_index'],request['chunk_header_offset'],3 if request['kind']=='streaming-man' else 5,reports[index+1:])
            if request['kind']=='streaming-animation-bank':
                verify_rebuilt_streaming_animation_banks(working,[dict(request,chunk_header_offset=final_offset)])
            else:
                from .streaming_man import streaming_chunks
                raw=reopened.read_entry(reopened.entry(request['entry_index']))
                chunks,terminated=streaming_chunks(raw)
                target=next((c for c in chunks if c['header_offset']==final_offset and c['type_byte']==3),None)
                candidate=request['candidate']
                if not terminated or target is None or target['size']!=len(candidate) or raw[final_offset+4:final_offset+4+len(candidate)]!=candidate:
                    raise ImportError('Resource composition final reopened streaming MAN changed')
            continue
        entry = reopened.entry(request['entry_index'])
        span = locate_physical_span(reopened, entry.start_lba*2048)
        raw = working[span['byte_offset']:span['byte_offset']+span['byte_length']]
        if request.get('kind') in ('texture-layout-raw','texture-addition-raw'):
            from .textures import _pack_members
            _pack_members(raw,True)
            size=report['pack_audit']['proposed_byte_length']
            if sha256(raw[:size]).hexdigest()!=report['pack_audit']['proposed_sha256'] or raw[size:]!=bytes(len(raw)-size):
                raise ImportError('Resource composition final reopened raw texture allocation changed')
            continue
        table = parse_scene_assets(raw, entry.index,request.get('table_offset',0))
        descriptor = table.descriptors[request['descriptor_index']]
        offset=request.get('table_offset',0)
        end = min([offset+d.data_offset for d in table.descriptors if d.data_offset > descriptor.data_offset]+[len(raw)])
        pack,_ = decompress_lzs(raw[offset+descriptor.data_offset:end], descriptor.size)
        if request.get('kind') in ('texture-pack','texture-layout-pack','texture-addition-pack'):
            if descriptor.type_byte!=1 or pack!=request['pack']:
                raise ImportError('Resource composition final reopened texture pack changed')
            continue
        if request.get('kind')=='compressed-man':
            if descriptor.type_byte!=3 or pack!=request['candidate']:
                raise ImportError('Resource composition final reopened compressed MAN changed')
            continue
        resource_audit='bank_audit' if request.get('kind')=='animation-bank' else 'pack_audit'
        if sha256(pack).hexdigest() != report['carrier'][resource_audit]['proposed_sha256']:
            raise ImportError('Model composition final reopened pack changed')
    return working, dict(schema_version='legaia.model-pack-composition.v1', source_sha256=expected_sha256,
        patched_sha256=patched_sha256, proposed_sha256=sha256(working).hexdigest(),
        patch_count=len(prepared), patched_bytes=sum(len(payload) for _,payload in prepared),
        resources=reports, final_packs_verified=True, final_animation_banks_verified=True,final_streaming_man_verified=True,final_compressed_man_verified=True,final_texture_packs_verified=True,final_texture_layouts_verified=True,final_texture_additions_verified=any(r.get('kind') in ('texture-addition-pack','texture-addition-raw') for r in completed),growth_bytes=len(working)-len(source),
        disc_relocation_required=len(working)!=len(source), build_ready=False, gameplay_verified=False)
