"""Bounded World-native ledger operation families; complete replay remains required."""
from .core import ImportError
from .model_face_ledger import SCHEMA, CONTENT_SCHEMA, VECTOR_SCHEMA

FACE_FORMAT = 'world-tmd-face-addition-v1'


def validate_face_ledger(ledger):
    if not isinstance(ledger,dict) or ledger.get('schema_version') not in (SCHEMA,CONTENT_SCHEMA,VECTOR_SCHEMA):
        raise ImportError('World face binding requires a supported native addition ledger')
    member='batches' if ledger['schema_version']==SCHEMA else 'operations'
    operations=ledger.get(member)
    if (not isinstance(operations,list) or not operations or
            any(not isinstance(op,dict) or (member=='operations' and op.get('kind') not in ('add_faces','edit_content','allocate_vectors')) for op in operations)
            or member=='operations' and not any(op.get('kind')=='add_faces' for op in operations)):
        raise ImportError('World face binding requires additions and supported content/vector operations')


GROUP_FORMAT = 'world-tmd-group-allocation-v1'
OBJECT_FORMAT = 'world-tmd-object-allocation-v1'


def validate_group_ledger(ledger):
    from .model_face_ledger import GROUP_SCHEMA
    if (not isinstance(ledger,dict) or ledger.get('schema_version')!=GROUP_SCHEMA
            or not isinstance(ledger.get('operations'),list) or not ledger['operations']
            or not any(isinstance(op,dict) and op.get('kind')=='allocate_groups' for op in ledger['operations'])
            or any(not isinstance(op,dict) or op.get('kind') not in
                ('add_faces','edit_content','allocate_vectors','allocate_groups') for op in ledger['operations'])):
        raise ImportError('World group binding requires group allocation and supported native operations')


def validate_object_ledger(ledger):
    from .model_face_ledger import OBJECT_SCHEMA
    if (not isinstance(ledger,dict) or ledger.get('schema_version')!=OBJECT_SCHEMA
            or not isinstance(ledger.get('operations'),list) or not ledger['operations']
            or not any(isinstance(op,dict) and op.get('kind')=='allocate_objects' for op in ledger['operations'])
            or any(not isinstance(op,dict) or op.get('kind') not in
                ('add_faces','edit_content','allocate_vectors','allocate_groups','allocate_objects') for op in ledger['operations'])):
        raise ImportError('World object binding requires object allocation and supported native operations')
