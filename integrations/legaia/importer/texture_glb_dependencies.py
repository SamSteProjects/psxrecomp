"""Bounded glTF image-use graph; display materials never establish native authority."""
from .animation_glb import _read_glb
from .texture_glb import inspect_glb_pngs,_name
from .core import ImportError

MAX_PRIMITIVES=4096


def _array(doc,key,maximum):
    value=doc.get(key,[])
    if not isinstance(value,list) or len(value)>maximum or any(not isinstance(row,dict) for row in value):
        raise ImportError('GLB dependency '+key+' must be a bounded object array')
    return value


def _index(value,size,label,nullable=False):
    if nullable and value is None:return None
    if type(value) is not int or not 0<=value<size:
        raise ImportError('GLB dependency '+label+' is outside its source array')
    return value


def inspect_glb_dependencies(content):
    doc,_=_read_glb(content);catalog=inspect_glb_pngs(content)
    textures=_array(doc,'textures',256);materials=_array(doc,'materials',256)
    samplers=_array(doc,'samplers',256);meshes=_array(doc,'meshes',1024)
    for row in samplers:
        for key,allowed in (('magFilter',(9728,9729)),('minFilter',(9728,9729,9984,9985,9986,9987)),('wrapS',(33071,33648,10497)),('wrapT',(33071,33648,10497))):
            if key in row and (type(row[key]) is not int or row[key] not in allowed):
                raise ImportError('GLB sampler '+key+' is malformed')
    texture_links=[]
    for i,row in enumerate(textures):
        image=_index(row.get('source'),catalog['image_count'],'texture image',nullable='source' not in row)
        sampler=_index(row.get('sampler'),len(samplers),'texture sampler',nullable='sampler' not in row)
        if 'extensions' in row and not isinstance(row['extensions'],dict):raise ImportError('GLB texture extensions are malformed')
        texture_links.append(dict(texture_index=i,image_index=image,sampler_index=sampler,has_extensions='extensions' in row))
    material_rows=[]
    for i,row in enumerate(materials):
        pbr=row.get('pbrMetallicRoughness',{})
        if not isinstance(pbr,dict):raise ImportError('GLB metallic/roughness material must be an object')
        if 'extensions' in row and not isinstance(row['extensions'],dict):raise ImportError('GLB material extensions are malformed')
        links=[]
        for role,owner,key in (('base_color',pbr,'baseColorTexture'),('metallic_roughness',pbr,'metallicRoughnessTexture'),('normal',row,'normalTexture'),('occlusion',row,'occlusionTexture'),('emissive',row,'emissiveTexture')):
            if key not in owner:continue
            link=owner[key]
            if not isinstance(link,dict):raise ImportError('GLB material texture link must be an object')
            texture=_index(link.get('index'),len(textures),'material texture')
            uv=link.get('texCoord',0)
            if type(uv) is not int or not 0<=uv<=7:raise ImportError('GLB material UV set exceeds the dependency report bounds')
            if 'extensions' in link and not isinstance(link['extensions'],dict):raise ImportError('GLB texture-link extensions are malformed')
            links.append(dict(role=role,texture_index=texture,texcoord=uv,has_extensions='extensions' in link))
        features=[]
        for key in ('baseColorFactor','metallicFactor','roughnessFactor'):
            if key in pbr:features.append(key)
        for key in ('emissiveFactor','alphaMode','alphaCutoff','doubleSided','extensions'):
            if key in row:features.append(key)
        material_rows.append(dict(material_index=i,name=_name(row.get('name')),links=links,shader_features=features))
    primitive_uses=[]
    for mesh_index,mesh in enumerate(meshes):
        primitives=_array(mesh,'primitives',MAX_PRIMITIVES)
        if len(primitive_uses)+len(primitives)>MAX_PRIMITIVES:raise ImportError('GLB image-use graph exceeds 4096 mesh primitives')
        for primitive_index,primitive in enumerate(primitives):
            material=_index(primitive.get('material'),len(materials),'primitive material',nullable='material' not in primitive)
            primitive_uses.append(dict(mesh_index=mesh_index,primitive_index=primitive_index,material_index=material))
    return dict(schema_version='legaia.texture-glb-dependencies.v1',catalog=catalog,
        texture_links=texture_links,materials=material_rows,primitive_uses=primitive_uses,
        mesh_count=len(meshes),sampler_count=len(samplers),primitive_count=len(primitive_uses),
        read_only=True,project_changed=False,native_binding_inferred=False,
        limitations=[
            'Only standard material texture links are reported; extension-owned image references are unresolved.',
            'URI and unsupported image slots are not read or downloaded.',
            'Material factors, UV sets, samplers and shaders do not establish native TPage, CLUT, UV or blend bindings.',
            'Mesh/primitive indices describe this GLB only; source native face identities require separate qualification.',
            'Selecting an image converts its pixels only; material binding remains an explicit reviewed native edit.'])
