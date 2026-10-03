"""Retail-qualified actor-pool bounds, separate from gameplay acceptance."""
from hashlib import sha256
import struct

from .core import ImportError

EXECUTABLE_SHA256 = '292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482'
FUNCTIONS = (
    (0x800203EC, 56, '715c2ee02cb8108ef59c5a8310b11e8348fb7fbd7c1d7dcfc1772a4778a0ea8a'),
    (0x80020454, 72, 'c729e656913f9a70fcddd9d88a322128984752f014a09391a9957a876a144dc3'),
    (0x8002049C, 8, '207819bf4ebe30789debac4affc1a07c833e14f530eef04dc87a6cf369209b43'),
    (0x80020DE0, 424, '7bfae4a45186c97b837e81300c1752077df44c829ec76bc310194bcb812a88aa'),
    (0x80024C88, 116, '6123402c96d799e6c8b6fa24301323ad99643fa0778cbd850a923926eef35429'),
    (0x8003A1E4, 888, 'e4514f0e4eb2743bf8521e958a5bdce5e923b686005ab21635b2ddbe2faecb2b'),
    (0x8003AEB0, 3416, 'fb7b106032f9fe83aea53481f855ea2cbf383fd42ae39973541738c59ba7bf05'),
)


def qualify_actor_pool(executable):
    """Derive constants only after full executable and function-span qualification."""
    if (not isinstance(executable, bytes) or len(executable) < 2048 or
            executable[:8] != b'PS-X EXE' or sha256(executable).hexdigest() != EXECUTABLE_SHA256):
        raise ImportError('NPC actor-pool evidence requires the qualified retail SCUS executable')
    base, size = struct.unpack_from('<II', executable, 0x18)
    if size > len(executable) - 2048:
        raise ImportError('NPC actor-pool executable load span exceeds source bounds')
    witnesses = []
    for address, length, expected in FUNCTIONS:
        offset = address - base
        if not 0 <= offset <= size - length or sha256(executable[2048 + offset:2048 + offset + length]).hexdigest() != expected:
            raise ImportError('NPC actor-pool retail function witness changed')
        witnesses.append(dict(address=f'0x{address:08X}', byte_length=length, sha256=expected))
    # Qualified initializer: highest free-stack index, and signed node step.
    highest = struct.unpack_from('<I', executable, 2048 + 0x800203EC - base)[0] & 0xFFFF
    step = struct.unpack_from('<h', executable, 2048 + 0x80020404 - base)[0]
    return dict(schema_version='legaia.actor-pool-source.v1', executable_sha256=EXECUTABLE_SHA256,
                node_capacity=highest + 1, node_stride=-step, functions=witnesses,
                evidence='retail_static_instruction_paths', gameplay_verified=False)


def assess_initial_placement_capacity(profile, partition_counts):
    """Reject an unavoidable lower-bound overflow, without promising headroom."""
    if (not isinstance(profile, dict) or profile.get('schema_version') != 'legaia.actor-pool-source.v1' or
            profile.get('executable_sha256') != EXECUTABLE_SHA256 or
            profile.get('node_capacity') != 143 or profile.get('node_stride') != 216):
        raise ImportError('NPC actor-pool assessment requires qualified source evidence')
    if (not isinstance(partition_counts, list) or len(partition_counts) != 3 or
            any(type(value) is not int or not 0 <= value <= 32767 for value in partition_counts)):
        raise ImportError('NPC actor-pool assessment requires complete MAN partition counts')
    # Setup allocates one anchor before records 1..N1-1 in its initial branch.
    minimum = max(1, partition_counts[1])
    if minimum > profile['node_capacity']:
        raise ImportError(f'NPC initial placement demand is at least {minimum} nodes but the retail actor pool has only 143; reduce NPC additions')
    return dict(schema_version='legaia.actor-pool-assessment.v1', source=profile,
                candidate_partition_counts=list(partition_counts),
                initial_placement_minimum_nodes=minimum,
                remaining_after_placement_lower_bound=profile['node_capacity'] - minimum,
                other_scene_and_script_demand='unverified', runtime_allocation_verified=False,
                interpretation='Lower-bound rejection only; remaining slots are not a safe additional-NPC budget.')
