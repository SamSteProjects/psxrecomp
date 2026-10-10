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
