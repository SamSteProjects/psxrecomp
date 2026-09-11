# Native actor candidates

Native actor creation is a development prototype. It is not connected to project
Build and does not establish that an added record will spawn or behave correctly.
Existing NPC coordinates must not be moved merely because interior geometry is
absent from the viewport.

## Current pipeline

`importer.man_actor_structure.append_actor_candidate` takes immutable decoded MAN
bytes, their SHA-256, and an existing partition-1 donor index. It appends a donor
record, grows the offset table, preserves existing partition-local indices, and
rewrites reached opcode `0x44` operands. The result and audit remain in memory.

The lower-level `append_actor_donor` produces the structural candidate before
operand rewriting. Its source-bound donor selection rejects system record zero,
invalid indices, and aliased records. `append_actor_structure` accepts a raw record
for structural experiments; it is not a validated authored actor definition.

`script_reindex.spawn_index_map` verifies that old/new partition-2 records have
identical bytes before mapping their global indices. `reindex_spawn_operands`
changes only decoded instruction operands, preserving opaque bytes. Partial
coverage never implies that all references were found. `inspect_spawn_reindex`
inventories partition-1 and partition-2 paths; partition zero remains excluded.

`man_container.encode_man_candidate` verifies original container and MAN hashes,
compresses the candidate, updates its decoded-size descriptor, and optionally
grows the buffer while relocating following descriptor offsets. Growth is opt-in.
An unchanged MAN retains its original compressed representation. This is a buffer
operation, not a PROT archive writer.

## Evidence and constraints

Pinned reference: AndrewAltimit/legend-of-legaia-re
`d6e64c68ede25813d35db20980da82a1a025549b`.

- `engine-vm/src/field/step.rs`: opcode44 stores a global index rebased by
  partition0 + partition1 counts to address a partition2 script context.
  Appending a partition1 actor shifts these indices even if scripts keep their bytes.
- `engine-vm/src/field/step/camera.rs` and `man_field_scripts/records.rs`:
  script-local absolute PCs must be distinguished from MAN file addresses.
  Do not apply a global byte delta to every apparent absolute operand.
- `engine-vm/src/field/step/actor_ctrl.rs`: acquire forms have a read/advance
  boundary inconsistency requiring retail verification; those forms remain opaque.
- `asset/src/scene_asset_table.rs`: descriptor high byte is type, low24 is
  decoded size. This does not describe outer archive allocation ownership.
- `prot/src/archive.rs`: the sliding TOC formulas produce overlapping read
  windows. Our parser agrees; entries are not independently resizable files.

Retail town01 checks: a donor append produces actor53. The reached rewrite
inventory found references in P1[0], P1[10], and P2[6]. Donor11 needs three
operand changes; donor10 needs four because its cloned script also references P2.
These are observed decoded references, not an exhaustive runtime dependency list.

The donor11 compressed candidate was25259 bytes against24894 bytes of slot
capacity; the original re-encoded to24891 bytes. Buffer growth of368 bytes
roundtripped with four descriptor offsets moved and following payload preserved.
However the containing entry2 starts at LBA239 and reads118 sectors; entry3 starts
at LBA240 and overlaps117 of them. `prot_layout.inspect_entry_footprint` exposes
these overlaps and the exact source TOC words.

## Remaining integration work

1. Establish every affected global reference family, including partition0 and
   opaque/external script paths. Preserve story gates and dispatch ownership.
2. Establish how a new actor is scheduled and how its model, animation, script,
   flags and collision dependencies are initialized.
3. Rebuild shared archive references and outer sizes without corrupting overlapping
   read windows, embedded references, or neighboring scene data.
4. Add actor templates, project commands, undo/persistence, preview and Build
   integration using stable authored identities and immutable retail provenance.
5. Verify the generated build interactively with the user's authorization.

Candidate audits retain `build_ready: false`; no current coverage count, roundtrip
or synthetic test changes that status.

## Focused checks

Run from the repository root with `PYTHONPATH=integrations/legaia`:

```powershell
C:\Python314\python.exe -m unittest discover -s integrations/legaia/tests -p test_man_actor_structure.py
C:\Python314\python.exe -m unittest discover -s integrations/legaia/tests -p test_script_reindex.py
C:\Python314\python.exe -m unittest discover -s integrations/legaia/tests -p test_man_container.py
```

Fixtures are synthetic; no retail payload is stored in these tests.
