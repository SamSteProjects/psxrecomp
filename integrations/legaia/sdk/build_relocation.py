"""Compose normal Build patches and resource growth into one runtime disc payload."""
from hashlib import sha256
from importer.core import ImportError
from importer.model_pack_composition import compose_model_pack_archive
from importer.relocated_disc import RelocatedLogicalDisc
from importer.iso_relocation import path_table_locations
from importer.disc_relocation_package import encode_relocation_package, MAX_METADATA


def prepare_build_relocation(image, archive, requests, overlays):
    node = archive.node
    if not 0 < node.size <= 256*1024*1024:
        raise ImportError('Build source PROT exceeds native package budget')
    source = image.read_user(node.extent_lba, 0, node.size, node.size)
    source_hash = sha256(source).hexdigest()
    start, stop = node.extent_lba*2048, node.extent_lba*2048+node.size
    patches, outside, ranges = [], [], []
    if len(overlays) > 4096:
        raise ImportError('Build relocation exceeds the patch budget')
    for row in overlays:
        offset, payload, size = row['offset'], row['payload'], row['size']
        if (type(offset) is not int or type(size) is not int or not isinstance(payload, bytes)
                or size != len(payload) or not size or offset < 0
                or offset+size > image.size//2352*2048):
            raise ImportError('Build relocation patch bounds or payload changed')
        original = image.read_user(0, offset, size, image.size//2352*2048)
        if sha256(original).hexdigest() != row['expected_sha256'] or sha256(payload).hexdigest() != row['sha256']:
            raise ImportError('Build relocation patch preimage or candidate hash changed')
        ranges.append((offset, offset+size))
        if start <= offset and offset+size <= stop:
            patches.append(dict(offset=offset-start, source_sha256=row['expected_sha256'], payload=payload))
        elif offset < stop and offset+size > start:
            raise ImportError('Build relocation patch straddles PROT ownership')
        else:
            outside.append((offset, payload))
    ranges.sort()
    if any(a[1] > b[0] for a,b in zip(ranges,ranges[1:])):
        raise ImportError('Build relocation patches overlap')
    proposed, composition = compose_model_pack_archive(source, source_hash, requests, patches,
                                                       header_offset=archive.header_offset)
    view = RelocatedLogicalDisc(image, proposed, source_hash)
    protected = [(16,17)]
    for table in path_table_locations(image.user_sector(16)):
        if table['size'] > 1024*1024:
            raise ImportError('Build source path table exceeds qualification budget')
        protected.append((table['lba'],table['lba']+(table['size']+2047)//2048))
    queue, seen, records = [image.root], set(), 0
    while queue:
        directory = queue.pop()
        if directory.extent_lba in seen:
            continue
        if len(seen) >= 4096 or not 0 < directory.size <= 4*1024*1024:
            raise ImportError('Build source directories exceed qualification budget')
        seen.add(directory.extent_lba)
        protected.append((directory.extent_lba,directory.extent_lba+(directory.size+2047)//2048))
        children = image._children(directory);records += len(children)
        if records > 100000:
            raise ImportError('Build source directory entries exceed qualification budget')
        queue.extend(child for child in children if child.is_dir and child.name not in ('.','..'))
    changed = {}
    for offset,payload in outside:
        at = 0
        while at < len(payload):
            lba, within = divmod(offset+at, 2048)
            mapped = lba+(view.growth_sectors if lba >= view.insertion_lba else 0)
            if mapped in view.metadata or any(start <= lba < stop for start,stop in protected):
                raise ImportError('Build patch conflicts with relocated ISO metadata')
            if lba not in changed:
                if len(changed)+len(view.metadata) >= MAX_METADATA:
                    raise ImportError('Build relocation metadata exceeds native package budget')
                raw = image._raw_sector(lba)
                if (len(raw) != 2352 or raw[15] != 2 or raw[16:20] != raw[20:24] or raw[18]&0x20):
                    raise ImportError('External Build patch requires Mode 2 Form 1 source framing')
                changed[lba] = bytearray(image.user_sector(lba))
            count = min(2048-within, len(payload)-at)
            changed[lba][within:within+count] = payload[at:at+count]
            at += count
    if len(changed)+len(view.metadata) > MAX_METADATA:
        raise ImportError('Build relocation metadata exceeds native package budget')
    for lba,sector in sorted(changed.items()):
        mapped = lba+(view.growth_sectors if lba >= view.insertion_lba else 0)
        payload = bytes(sector);view.metadata[mapped] = payload
        view.audit['metadata_sectors'].append(dict(source_lba=lba, proposed_lba=mapped,
            source_sha256=sha256(image.user_sector(lba)).hexdigest(), proposed_sha256=sha256(payload).hexdigest()))
    view.audit['metadata_sectors'].sort(key=lambda row:row['source_lba'])
    length = 96+len(proposed)+len(view.metadata)*2120
    if length > 256*1024*1024:
        raise ImportError('Build relocation exceeds native 256 MiB package budget')
    payload, package = encode_relocation_package(view)
    return dict(file='assets/disc-relocation.bin', payload=payload, sha256=package['sha256'], size=len(payload)), dict(
        schema_version='legaia.build-relocation.v1', composition=composition,
        logical_disc=view.audit, package=package, external_patched_sectors=len(changed),
        gameplay_verified=False)
