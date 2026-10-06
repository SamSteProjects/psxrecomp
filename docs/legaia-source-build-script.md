# Retail versus saved Build scripts

Open an imported actor or standalone script in **Script and dialogue**, then choose **Find matching Builds**, select a completion receipt and choose **Compare delivered script**. If there is no matching receipt, Save and Build the current project first. Inspection does not launch or install the game.

The comparison reads the actual native MAN from the saved package's relocated PROT or qualified fixed-span overlays. It resolves the imported partition and record ordinal, qualifies the source disc and package integrity, and requires the receipt to match current project inputs. Draft NPCs retain their separate donor/generated script workflow.

The editor shows changed bytes by record PC and paired decoded paths. Actor header changes are included. Record-relative PCs remain distinct from decoded MAN offsets, which can shift when records are allocated. The view displays at most 256 byte differences and 512 decoded PCs; the local JSON download retains the full bounded record, hashes, decoder stops and opaque regions. Retail and emitted records remain separate.

Aliased owners, overlapping sections, missing owners, changed record lengths/entry layouts, stale input receipts and changed packages reject comparison. This is read-only delivery evidence; it does not prove execution, story state, effect targets or gameplay behavior.

## Offline acceptance, 2026-10-06

An actual private Town01 source script comparison used saved Build `0b3aea8180ed5767`. Its emitted record SHA256 is `97fc68f29f8bce703a84abc34b14c6410d9b9227fa88759521b7e74640ef7223`; package SHA256 is `a397f445e3fc290d89f4f0583a638c92ccae2d9ceb2aa7ee72846d54d66d341c`. The record exactly matches the independently decoded color-edit Build acceptance from the preceding checkpoint. Two delivered differences appear at record PCs `0x0011` and `0x0014`; decoded RGB/intensity retain retail and generated values separately.

The actual editor asset entry, receipt selection, comparison, exact download, wide/narrow layout and malformed/stale client contracts passed. An unchanged imported Town01 actor (`man-p1/0001`, 1169 bytes) also compares successfully, retaining its partial decoding and zero record differences. HTTP rejects extra fields, wrong-scene owners, invalid Build IDs and changed authored inputs. Imported data, overrides and history remain unchanged. Four focused Python checks and three existing Node inspector/operand checks pass. Structural checks cover both owner partitions, exact bytes, missing records, aliases and section overlap; existing saved-NPC PROT overlay qualification checks remain applicable. Private evidence is in `local-output/sdk-20260909/source-build-script-20261006/`. No game or new Build was needed for this inspection feature.

Reference evidence remains pinned at Andrew revision `d6e64c68ede25813d35db20980da82a1a025549b`: `crates/asset/src/man_section.rs` supplies partition/count/offset structure. Existing importer script decoding supplies supported instruction paths and explicit unknowns. The reference is read-only evidence, not a runtime dependency.
