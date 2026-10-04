"""Read-only embedded PNG extraction; no GLB shader or native binding inference."""
from hashlib import sha256
import base64
from .animation_glb import _read_glb
from .texture_png import decode_png,MAX_PNG_BYTES
from .core import ImportError


def _name(value):
    if value is not None and (not isinstance(value,str) or len(value)>256 or any(ord(c)<32 for c in value)):
        raise ImportError('GLB image names must be bounded display text')
    return value


def _images(content):
    doc,binary=_read_glb(content)
    images,views=doc.get('images'),doc.get('bufferViews',[])
    if not isinstance(images,list) or not 1<=len(images)<=64 or not isinstance(views,list) or len(views)>16384:
        raise ImportError('GLB PNG extraction requires 1 through 64 image slots')
    rows=[];excluded=[];payloads={};qualified={}
    for index,image in enumerate(images):
        if not isinstance(image,dict):raise ImportError('GLB image slot is malformed')
        name=_name(image.get('name'))
        if image.get('mimeType')!='image/png' or 'uri' in image or 'extensions' in image:
            excluded.append(index);continue
        slot=image.get('bufferView')
        if type(slot) is not int or not 0<=slot<len(views):raise ImportError('Embedded PNG buffer view is unavailable')
        view=views[slot]
        if not isinstance(view,dict) or type(view.get('buffer')) is not int or view['buffer']!=0 or any(key in view for key in ('byteStride','extensions')):
            raise ImportError('Embedded PNG must own a plain embedded buffer view')
        offset,length=view.get('byteOffset',0),view.get('byteLength')
        if type(offset) is not int or type(length) is not int or not 0<=offset or not 33<=length<=MAX_PNG_BYTES or offset+length>len(binary):
            raise ImportError('Embedded PNG byte range exceeds its bounded source')
        identity=(offset,length)
        if identity not in qualified:
            payload=binary[offset:offset+length];png=decode_png(payload)
            qualified[identity]=dict(png_sha256=sha256(payload).hexdigest(),width=png['width'],height=png['height'])
        info=qualified[identity];payloads[index]=identity
        rows.append(dict(image_index=index,name=name,byte_length=length,**info))
    catalog=dict(schema_version='legaia.texture-glb-images.v1',glb_sha256=sha256(content).hexdigest(),
                 image_count=len(images),images=rows,excluded_image_indices=excluded,read_only=True,project_changed=False)
    return catalog,binary,payloads


def inspect_glb_pngs(content):return _images(content)[0]


def extract_glb_png(content,image_index,glb_sha256,png_sha256):
    catalog,binary,payloads=_images(content)
    if type(image_index) is not int or image_index not in payloads or glb_sha256!=catalog['glb_sha256']:
        raise ImportError('GLB file or embedded PNG selection changed after inspection')
    row=next(row for row in catalog['images'] if row['image_index']==image_index)
    if png_sha256!=row['png_sha256']:raise ImportError('Embedded PNG bytes changed after inspection')
    offset,length=payloads[image_index]
    return dict(schema_version='legaia.texture-glb-image.v1',glb_sha256=catalog['glb_sha256'],image=row,
                png_base64=base64.b64encode(binary[offset:offset+length]).decode(),read_only=True,project_changed=False)
