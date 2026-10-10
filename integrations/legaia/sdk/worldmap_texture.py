"""Read-only native TIM-local pixels; palettes are explicit, never runtime guesses."""
import base64,re
from hashlib import sha256
from importer.textures import decode_tim
from importer.worldmap_geometry import load_worldmap_texture
from .project import ProjectError
from .worldmap_authoring import state_key

MAX_PIXELS=2097152

def inspect(project,texture_id,key,member_hash,palette_index):
    match=re.fullmatch(r'texture://(map0[123])/kingdom/([0-9]{4,5})',texture_id) if isinstance(texture_id,str) else None
    if project.mode!='edit' or not project.disc_path or key!=state_key(project) or not match or not isinstance(member_hash,str) or not re.fullmatch('[0-9a-f]{64}',member_hash) or type(palette_index) is not int or not 0<=palette_index<=32767:
        raise ProjectError('World TIM preview requires the current Edit source, native texture identity and explicit palette')
    scene=match[1];slot=int(match[2])
    if texture_id!=f'texture://{scene}/kingdom/{slot:04d}':raise ProjectError('World TIM identity is not canonical')
    tim,source,provenance=load_worldmap_texture(project.disc_path,scene,slot)
    if source['semantic_id']!=texture_id or source['decoded_member_sha256']!=member_hash:raise ProjectError('Native TIM member changed; refresh world resources')
    count=len(tim.clut.data)//((1<<tim.bpp)*2) if tim.bpp<=8 and tim.clut else 0 if tim.bpp<=8 else 1
    if palette_index>=max(1,count):raise ProjectError('Requested native TIM palette is unavailable')
    if not 0<tim.width*tim.image.height<=MAX_PIXELS:raise ProjectError('World TIM exceeds its bounded pixel preview')
    status='available' if count else 'unsupported';rgba=stp=b''
    if count:
        pixels=decode_tim(tim,palette_index);rgba=pixels['rgba'];stp=pixels['stp']
        if len(rgba)!=tim.width*tim.image.height*4 or len(stp)*4!=len(rgba):raise ProjectError('World TIM pixel coverage is incomplete')
    result=dict(schema_version='legaia.worldmap-texture.v1',texture_id=texture_id,source_key=key,project_path=str(project.root),source_record=source,source_provenance=provenance,palette_index=palette_index,palette_count=count,width=tim.width,height=tim.image.height,status=status,reason=None if count else 'Indexed TIM has no complete local CLUT; cross-TIM/runtime palette selection is not inferred.',rgba_base64=base64.b64encode(rgba).decode('ascii'),stp_base64=base64.b64encode(stp).decode('ascii'),rgba_sha256=sha256(rgba).hexdigest(),stp_sha256=sha256(stp).hexdigest(),read_only=True,project_changed=False,gameplay_verified=False)
    if project.mode!='edit' or key!=state_key(project):raise ProjectError('World TIM sources changed during preview')
    return result
