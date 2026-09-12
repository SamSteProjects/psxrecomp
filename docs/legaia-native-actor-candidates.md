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

The source-bound inspection completed for all52 town01 donors without a rejected
candidate. Required container growth ranged from24 to1492 bytes. Every response
retained read-only status and false build readiness; this checks candidate
construction, not gameplay or complete script coverage.

The donor11 compressed candidate was25259 bytes against24894 bytes of slot
capacity; the original re-encoded to24891 bytes. Buffer growth of368 bytes
roundtripped with four descriptor offsets moved and following payload preserved.
However the containing entry2 starts at LBA239 and reads118 sectors; entry3 starts
at LBA240 and overlaps117 of them. `prot_layout.inspect_entry_footprint` exposes
these overlaps and the exact source TOC words.

Physical allocation is now resolved separately from those read windows. The
town01 table found through entry2 belongs to physical entry4, LBA243..354,
with the table at offset0. Candidate encoding uses that exact227328-byte span;
donor11 produces a229376-byte sector-rounded candidate (one additional sector).
The emitted scene descriptors and decoded MAN are checked again after encoding.

Pinned `rando/src/disc.rs::grow_prot_entries` demonstrates consecutive-start
allocation and cumulative downstream TOC shifts. Its disc writer,
`iso/src/relayout.rs::grow_prot_dat`, also relocates following physical sectors,
updates MSF addresses, regenerates sector checksums and renumbers ISO references.
This is reference evidence, not an accepted SDK writer: the implementation uses
fixed path-table LBAs18..21, and its directory-record loop visibly patches the
little-endian extent/size fields only. SDK integration must verify both endian
copies and derive table locations from the PVD before relying on this approach.
No candidate archive or disc has been written by this inspection workflow.

`importer/prot_rebuild.py` now rebuilds a logical archive in memory from a
source-hashed, sector-aligned physical replacement. It preserves neighboring
payloads and relocates every subsequent raw TOC start, including the end sentinel
omitted by read-window validation. A retail entry4 growth check preserved the
entire following payload and shifted1229 starts by one sector. This utility does
not yet emit a disc or integrate with project Build; disc relocation remains required.

`rebuild_man_entry` composes MAN encoding, sector padding and logical archive
relocation, then reopens the archive with the production parser and requires exact
decoded MAN equality. A retail donor11 append passed this complete in-memory path
with one sector growth and1229 relocated starts. This validates serialized logical
archive content, not runtime scheduling or a playable disc image.

## Remaining integration work

Experimental disc output is now available through `disc_rebuild.write_grown_prot_disc`.
The private donor11 image reopens with the expected MAN; all44 non-PROT file hashes
match the source,139219 unaffected sectors preserve payload/protection bytes, and
59215 regenerated sectors pass internal parity verification. The writer preserves
PROT's distinct terminal subheader and updates ISO metadata in both endian forms.
This is not gameplay acceptance or project Build integration.

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
