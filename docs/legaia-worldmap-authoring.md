# World-map landmark menu authoring

The editor supports source-qualified edits to the existing global landmark menu
in `SCUS_942.54`. It compares Retail, Current and reviewed Proposed values,
retains duplicate source records, saves ordinary project commands, and packages
the changes through normal Build. This is an offline encoded-data workflow;
drawing, travel, discovery activation and gameplay remain unverified.

## Editor workflow

1. Import a scene from the supported user-owned retail disc and use **Edit**
   mode. Open **World-map landmarks** beside the resource tools, or open a
   world-map placement from the asset database.
2. Choose a source placement record. The form shows Retail, Authored and Current
   values. Select an existing landmark name and exact CDNAME destination
   definition; edit the discovery index and encoded X/Y within the bounds below.
3. Choose **Review menu values**. Review shows changed fields, executable byte
   offsets and the Proposed values. The 2D diagram offers Retail, Current and
   reviewed Proposed markers on an encoded 0–255 plane, with Y downward under
   the reference pixel interpretation. It is not a geographical or 3D scene
   preview. Coincident markers retain separate source IDs and have individual
   record-selection buttons; duplicate names never merge the editable rows.
4. Choose **Apply reviewed menu values**. Apply rechecks the source, authored
   state, candidate hashes and review key before creating a history entry.
   Changing an input invalidates its review. Stale context requires reopening;
   no-op reviews cannot create commands.
5. **Review reset to Retail**, followed by Apply, clears only the selected row's
   override. Other authored rows remain. **Discard menu draft** restores Current
   form values without changing applied edits. Apply or discard the pending row
   before switching rows, closing, using history, saving or building.
6. Use ordinary **Undo**, **Redo**, **Save** and project **Open**. Then use normal
   **Build review** and **Build**. A Build-report change opens its source placement
   in the same landmark workspace. **Inspect Current destination source** opens
   the scene catalog at the exact CDNAME label; it does not assert import support
   or a successful transition.

## Source and editable fields

The supported executable loads at `0x80010000`. Its placement table begins at
file `0x64298`, RAM `0x80073A98`, and contains exactly 20 source rows. Each
six-byte little-endian `<BBHBB` row is:

| Byte offset | Stored field | Authoring constraint |
| --- | --- | --- |
| 0 | Name index, u8 | Existing name index 0–15 |
| 1 | Encoded discovery byte, u8 | Form index 32–287; writer stores index minus 32 |
| 2–3 | Destination ID, u16 | Exact existing numeric CDNAME definition |
| 4 | Encoded X, u8 | Integer 0–255 |
| 5 | Encoded Y, u8 | Integer 0–255 |

Terminator row 20 starts at file `0x64310`, RAM `0x80073B10`; its first byte is
`0xFF`. Preserve its complete six bytes and the two padding bytes at `0x64316`.
The 16 names, each with a 32-byte source slot, begin at file `0x64318`, RAM
`0x80073B18`. Rows, stable IDs and order cannot be added, removed or renamed;
the name strings cannot be rewritten. Changing a row's name index selects an
existing source string.

The public authoring loader requires the verified retail disc, executable
header/load address and fixed hashes of the executing consumer windows. Name
and discovery consumers have retail static evidence: the walker stops at the
terminator, checks byte 1 plus 32, and deduplicates against the last emitted
name. The bitmap query uses `0x80085758 + (index >> 3)` and the MSB-first mask
`0x80 >> (index & 7)`. No current flag values or named story events are inferred.
The executing walker has no 64-row cap or name-range guard; the editor's bounds
protect the source layout.

Destination labels are exact CDNAME numeric associations. A travel consumer has
not been proved. X/Y retain the pinned reference's menu-pixel interpretation;
their executing draw consumers have not been proved. These fields are editable
wire values, without claims about physical coordinates or gameplay behavior.

The global owner is `worldmap://legaia/menu`. Its `WorldMapMenu` component stores
`source_executable_sha256`, `source_disc_sha256` and `entries` keyed by
`worldmap://legaia/menu/placements/NNNN`. Each entry contains `name_index`,
`discovery_flag_index`, `destination_scene_id` and `menu_position: {x, y}`.
Imported scene metadata remains separate. CDNAME definitions are read from the
same verified disc when qualifying the source and candidate.

## Build and evidence

Normal Build emits `assets/worldmap-menu.bin`, a 126-byte SCUS table overlay:
20 rows plus the unchanged terminator. Its `disc_user` location is bound to the
SCUS ISO extent and file offset. Header, executable code, names, padding and all
unrequested bytes remain exact. Build independently encodes the requested
`<BBHBB` values, checks the row audit and changed bytes, reconstructs the complete
executable from the overlay, and verifies readback and the original preimage
hash before packaging. The Build audit retains field offsets and source-row
navigation. The completion status is `package_built_not_launched`.

**Experimental Export disc is unsupported while this global component is
authored.** It rejects the project rather than silently omitting the landmark
changes. Use normal Build for this workflow.

Private retail research, source-window hashes and integration evidence are under
`local-output/sdk-20260909/worldmap-authoring-20261002/`. The read-only Andrew
reference remains pinned at `d6e64c68ede25813d35db20980da82a1a025549b`.
The executable SHA256 is
`292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482`.
Package/readback checks do not establish runtime or gameplay acceptance.

Offline validation for this milestone: 36 selected Python cases passed with the
private retail disc enabled and no skips; two Node suites and 16 actual browser
workflows passed with zero page/HTTP errors or game-launch requests. The browser
package independently reconstructs the entire executable with only 0x6429C
changed 96 to 97, and its scene import matches a fresh retail import. A mixed
field-placement/landmark Build retains both overlays. This is package acceptance;
runtime drawing/travel and gameplay remain in the deferred queue.
