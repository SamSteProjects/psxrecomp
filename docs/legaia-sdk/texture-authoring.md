# Authored TIM replacement

Format evidence uses Andrew's unchanged reference revision
`d6e64c68ede25813d35db20980da82a1a025549b`: `crates/tim/src/lib.rs`
(blob `99607f6265e223153cc47678bff1d65d59b0ea54`) and
`crates/prot/src/timpack.rs` (blob `f90c89f1aba8adf012395a6d752cef49a41d4960`).
Standalone pack offsets convert from words with a four-byte base; descriptor
pack offsets use their existing decoder convention. The writable path rejects
ambiguous members instead of sorting or deduplicating them into new identities.

Texture replacement keeps imported provenance and authored content separate.
The editor accepts a user-selected TIM file with the same source layout and
provides an original TIM download for external editing. Imported and effective
preview layers remain distinct. A replacement supplies actual image and palette
data; changing format, dimensions, VRAM rectangles or CLUT layout is unsupported.

Project metadata stores `texture_overrides`, mapping a structural texture ID to
`asset_sha256`, `byte_length`, `format` and `source_scene_id`. The authored file
lives at `Authored/Textures/<sha256>.tim` beneath the project. Input is bounded
to 1 MiB per file and 128 references per project. Content hashes and lengths
are checked on use, save and offline reopen. Paths are derived from validated
hashes and must resolve within the project. No client source locator or output
path is accepted.

Apply and Clear participate in Undo/Redo and dirty tracking. Clearing or undoing
a replacement retains the content file for history and recovery. The project
format omits the collection when empty, preserving existing baseline build
identity. Imported documents and the retail image are not modified.

Model and scene previews use effective scene TIM data while retaining retail
source locators. Shared party banks are separate and are not replaced through
scene texture IDs. Preview matching still does not reconstruct runtime upload
order, conditional resources, palette animation or PSX blend behavior.

The build combines compatible replacements within each source carrier, checks
exact source hashes and boundaries, and emits private guarded disc overlays.
Compressed carriers must fit their original allocation. Unsupported growth or
overlapping overlays fails before publication. No relocation is inferred.

Playable texture appearance and restoration require explicit runtime evidence;
successful image preview and package decoding do not establish that acceptance.
