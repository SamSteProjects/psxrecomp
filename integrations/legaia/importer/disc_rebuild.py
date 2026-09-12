"""Streaming experimental PROT replacement into a new Mode 2 disc image."""
from hashlib import sha256
from pathlib import Path
import importlib.util
from .core import ImportError, Mode2Image, sha256_file
from .iso_relocation import collect_metadata_relocation


def _sector_codec():
    # The SDK is launched with integrations/legaia on PYTHONPATH, potentially
    # from a project directory outside the checkout. Resolve the framework tool
    # from this module rather than depending on the process working directory.
    path = Path(__file__).resolve().parents[3]/'tools'/'cd_sector.py'
    spec = importlib.util.spec_from_file_location('psxrecomp_cd_sector', path)
    if spec is None or spec.loader is None or not path.is_file():
        raise ImportError('Framework CD sector codec is unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.encode_form1, module.relocate_mode2


def write_grown_prot_disc(source_path, expected_disc_sha256: str,
                          replacement: bytes, expected_prot_sha256: str,
                          destination) -> dict:
    """Create exclusively; failed output is incomplete and never reported as valid."""
    encode_form1, relocate_mode2 = _sector_codec()
    source_path, destination = Path(source_path).resolve(), Path(destination).resolve()
    if source_path == destination or destination.exists():
        raise ImportError('Disc output must be a new path distinct from the source')
    if not isinstance(replacement, bytes) or len(replacement) % 2048:
        raise ImportError('Replacement PROT must contain whole logical sectors')
    if sha256_file(source_path) != expected_disc_sha256:
        raise ImportError('Source disc hash mismatch')
    with Mode2Image(source_path) as image:
        prot = image.find('PROT.DAT')
        if prot.size % 2048 or len(replacement) < prot.size:
            raise ImportError('PROT replacement cannot shrink or use partial sectors')
        old_count, new_count = prot.size//2048, len(replacement)//2048
        growth = new_count-old_count
        metadata, audit = collect_metadata_relocation(image, growth)
        boundary = prot.extent_lba+old_count
        first = image._raw_sector(prot.extent_lba)
        last = image._raw_sector(boundary-1)
        encode_form1(first)
        encode_form1(last)
        original_prot = sha256()
        for lba in range(prot.extent_lba, boundary):
            raw = image._raw_sector(lba)
            expected = last[16:24] if lba == boundary-1 else first[16:24]
            if raw[16:24] != expected or raw[:12] != first[:12] or raw[15] != 2:
                raise ImportError('PROT sector framing is not uniform with a terminal sector')
            original_prot.update(raw[24:2072])
        if original_prot.hexdigest() != expected_prot_sha256:
            raise ImportError('Source PROT hash mismatch')
        digest = sha256()
        written = 0
        with destination.open('xb') as output:
            def emit(raw):
                nonlocal written
                output.write(raw)
                digest.update(raw)
                written += len(raw)

            for lba in range(image.size//2352):
                if lba == prot.extent_lba:
                    for index in range(new_count):
                        template = last if index == new_count-1 else first
                        sector = template[:24]+replacement[index*2048:(index+1)*2048]+template[2072:]
                        emit(encode_form1(relocate_mode2(sector, prot.extent_lba+index)))
                if prot.extent_lba <= lba < boundary:
                    continue
                raw = image._raw_sector(lba)
                if lba in metadata:
                    raw = encode_form1(raw[:24]+metadata[lba]+raw[2072:])
                if lba >= boundary:
                    raw = relocate_mode2(raw, lba+growth)
                emit(raw)
        if written != image.size+growth*2352:
            raise ImportError('Rebuilt disc size mismatch')
    if sha256_file(source_path) != expected_disc_sha256:
        raise ImportError('Source disc changed during rebuild; output is unverified')
    with Mode2Image(destination) as reopened:
        rebuilt_prot = reopened.find('PROT.DAT')
        if rebuilt_prot.size != len(replacement):
            raise ImportError('Reopened PROT size mismatch')
        check = sha256()
        for index in range(new_count):
            check.update(reopened.user_sector(rebuilt_prot.extent_lba+index))
        if check.hexdigest() != sha256(replacement).hexdigest():
            raise ImportError('Reopened PROT payload mismatch')
    return dict(schema_version='legaia.experimental-disc-rebuild.v1',
                output_path=str(destination), output_sha256=digest.hexdigest(),
                output_bytes=written, source_sha256=expected_disc_sha256,
                metadata=audit, reopened_prot_verified=True, gameplay_verified=False)
