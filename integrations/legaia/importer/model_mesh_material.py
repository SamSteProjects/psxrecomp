"""Bounded standard base-color factors; no image or PBR material allocation."""
import math
from .core import ImportError


def color_factor(doc, primitive, index):
    materials=doc.get('materials',[])
    slot=primitive.get('material')
    if not isinstance(materials,list) or len(materials)>128:
        raise ImportError('Mesh material factors exceed bounded source slots')
    material={}
    if slot is not None:
        if type(slot) is not int or not 0<=slot<len(materials) or not isinstance(materials[slot],dict):
            raise ImportError('Mesh material factor slot is missing')
        material=materials[slot]
    pbr=material.get('pbrMetallicRoughness',{})
    if not isinstance(pbr,dict) or material.get('extensions') or pbr.get('extensions'):
        raise ImportError('Material RGB baking requires standard material factors without extensions')
    factor=pbr.get('baseColorFactor',[1,1,1,1])
    if (not isinstance(factor,list) or len(factor)!=4 or any(type(v) not in (int,float)
            or not math.isfinite(v) or not 0<=v<=1 for v in factor)):
        raise ImportError('Material baseColorFactor requires four finite normalized components')
    if material.get('alphaMode','OPAQUE')!='OPAQUE' or factor[3]!=1:
        raise ImportError('Material RGB baking requires opaque alpha; native blending is not inferred')
    return dict(primitive_index=index,material_index=slot,base_color_factor=factor)
