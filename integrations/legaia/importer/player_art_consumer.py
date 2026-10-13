"""Immutable retail ME instruction witnesses, separate from playable acceptance."""
import struct
from hashlib import sha256
from .core import ImportError
from .actor_runtime_capacity import EXECUTABLE_SHA256

FUNCTIONS = ((0x8002A9CC, 2240, '4846568647c9d13fdf55938ca4832679c2674dc611898267ccac55fe8da42acd'),
             (0x8002B28C, 328, '708ff5d29efa7afa0ae55a29ee44cda7c07e9842aa881b46e3c13b4ee69130ef'))


def qualify(executable):
    if not isinstance(executable,bytes) or len(executable)<2048 or executable[:8]!=b'PS-X EXE' or sha256(executable).hexdigest()!=EXECUTABLE_SHA256:
        raise ImportError('PLAYER art consumer evidence requires the exact retail executable')
    base,size=struct.unpack_from('<II',executable,0x18)
    if size>len(executable)-2048:raise ImportError('Art consumer load span exceeds its executable')
    witnesses=[]
    for address,length,digest in FUNCTIONS:
        at=address-base
        if not 0<=at<=size-length or sha256(executable[2048+at:2048+at+length]).hexdigest()!=digest:
            raise ImportError('Art consumer function instruction witness changed')
        witnesses.append(dict(address=f'0x{address:08X}',byte_length=length,sha256=digest))
    return dict(schema_version='legaia.player-art-consumer-source.v1',executable_sha256=EXECUTABLE_SHA256,
                functions=witnesses,evidence='retail_instruction_witnesses_with_bounded_offline_consumer_oracle',
                constraints=['Preserve each original ME size word and body offset.',
                             'Preserve original decoded parts, frames and byte count.',
                             'Every encoded stream must fit its original declared body.',
                             'Source and destination spans require complete bounded replay.'],
                allocation='not_supported',resident_archive='not_observed',timing='not_observed',gameplay_verified=False)
