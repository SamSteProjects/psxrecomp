"""Exact audited payload inventory shared by saved verification and private runs."""
import re
from .project import ProjectError

MAX_RELOCATION = 256*1024*1024


def package_inventory(manifest, overlays, relocation=None):
    expected, planned = {}, []
    if not isinstance(overlays,list) or len(overlays)>4096:
        raise ProjectError('Saved overlay inventory is invalid')
    for overlay in overlays:
        name=overlay.get('file')
        if (not isinstance(name,str) or not re.fullmatch(r'assets/[A-Za-z0-9_.-]+',name) or name in expected
                or not _hash(overlay.get('sha256')) or not _hash(overlay.get('expected_sha256'))
                or type(overlay.get('size')) is not int or not 0<overlay['size']<=64*1024*1024
                or type(overlay.get('offset')) is not int or overlay['offset']<0):
            raise ProjectError('Saved overlay inventory is invalid')
        expected[name]=(overlay['sha256'],overlay['size'])
        planned.append(dict(feature='placements',target='disc_user',offset=overlay['offset'],file=name,
                            sha256=overlay['sha256'],expected_sha256=overlay['expected_sha256']))
    if relocation is None:
        if manifest.get('overlay',[])!=planned or manifest.get('disc_relocation',[]):
            raise ProjectError('Manifest payload inventory differs from audit')
        return expected
    if (not isinstance(relocation,dict) or set(relocation)!={'file','sha256','size'}
            or not isinstance(relocation['file'],str) or not re.fullmatch(r'assets/[A-Za-z0-9_.-]+',relocation['file'])
            or not _hash(relocation['sha256']) or type(relocation['size']) is not int
            or not 96<=relocation['size']<=MAX_RELOCATION):
        raise ProjectError('Saved relocation inventory is invalid')
    declaration=dict(feature='placements',file=relocation['file'],sha256=relocation['sha256'])
    if (manifest.get('format_version')!=7 or manifest.get('disc_relocation')!=[declaration]
            or manifest.get('overlay',[]) or any(manifest.get(channel) for channel in
                ('write','patch','derived_disc','sparse_write','byte_patch'))):
        raise ProjectError('Manifest relocation inventory differs from audit')
    return {relocation['file']:(relocation['sha256'],relocation['size'])}


def _hash(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None
