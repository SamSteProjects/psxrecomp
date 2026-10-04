# Source NPC candidates in normal Build

Experimental parent export now propagates the parsed native PROT header location
through MAN batch rebuilding. Both primary and 2048-byte-prefixed headers are
supported by that orchestration. Synthetic physical-disc reopen verifies prefixed
compressed model/ANM/MAN composition and raw ANM/MAN composition with exact final
payloads. This layout check does not establish Retail gameplay acceptance.

**2026-10-04 — experimental model composition:** Experimental archive export
now uses qualified model-growth requests too. Those requests own every authored
member in a relocating pack, while scene preparation serializes the MAN and
remaining model edits. Original-address patches compose before model/ANM growth;
MAN rebuild follows, and final model hashes are read back afterward. A selected
single-scene export includes topology instead of entering the fixed-layout shortcut.

Retail read-only Town01 preparation verifies eight NPCs, retained ANM/shared
axes/allocated initial assignment and added-face model bytes together without
writing a Retail disc. Synthetic discs reopen exact model/MAN output both with
and without ANM allocation. Arbitrary model donor mapping, runtime spawning and
interactive rendering remain separate acceptance work.

**2026-10-04 — model growth composition:** Normal Build prepares qualified model
relocation requests first, then passes their authored model IDs to NPC scene
preparation. That handoff excludes only those models from the scene's fixed-layout
model serializer; the parent delivers and verifies them. Same-scene delegated IDs
appear in each NPC draft audit as `managed_model_ids`. Remaining model edits stay
in the ordinary serializer. Empty/default handoff suppresses nothing; unknown,
duplicate, malformed or over-budget IDs reject. The handoff is internal Build
orchestration, not an editor setting or HTTP upload.

Retail Town01 normal package readback passes eight NPC additions, retained ANM
allocation/shared axes/initial assignment and a model face addition together.
Synthetic composition also verifies MAN, ANM and TMD pack growth in one table,
with exact payload readback and preserved neighboring patches. Runtime spawning,
model rendering and animation suitability remain deferred gameplay checks.

**2026-10-04 — compressed capacity growth:** Normal Build now relocates a
qualified compressed MAN when its candidate cannot fit the original consumed
stream, rather than rejecting the batch. Eight-donor Retail Town01 batches pass
read-only review and exact format-7 package readback, alone and with retained ANM
allocation, shared axes and an allocated initial selector. Gameplay remains deferred.

**2026-10-04:** Retail dolk2 normal Build package readback passes both NPC-only
raw growth and combined NPC/retained-animation growth, shared channel edits,
allocated initial assignment and placement. Inclusive read-only Review Build also
passes the combined case. Native synthetic composition covers both chunk orders,
duplicate rejection and opaque header overlap rejection. The editor v2 review
scope is now `qualified_man_source_candidates`. Gameplay remains deferred.

Saved donor-based NPC drafts can enter **Review Build** and **Build** when their
scene uses a qualified compressed or raw streaming MAN carrier. Compressed
candidates that fit their consumed source stream use fixed-span overlays; larger
candidates use a source-qualified relocation package. This is source packaging support;
native allocation, spawning, scheduling and opaque script paths remain unverified. Normal Build also qualifies the [retail actor-pool lower bound](legaia-npc-actor-pool.md) and rejects unavoidable initial-placement overflow before compression; other consumers and safe headroom remain unknown.

Review includes all supported authored inputs. Its v2 result counts requested
NPC candidates, keeps excluded count at zero and reports failed serialization
as a blocker. A successful review writes no package and does not launch a game.
**Build reviewed inputs** binds the action to the reviewed authored snapshot.
The generated feature is disabled by default and identifies source NPC candidates.

For fixed-span compressed delivery, the serializer appends immutable retail donor records, applies supported existing
actor and partition-two edits after rebasing, and preserves the donor's scripts
except for intended initial placement. A bounded optimal LZS fallback may fit a
candidate when greedy compression cannot. Exactly two source-hashed overlay claims
update the original consumed MAN stream and its four-byte descriptor size word.
Any unused part of that stream retains original bytes. Carrier size, descriptor
pointers, neighboring payloads, TOC and ISO layout remain unchanged. Supported
model, animation, MAP and texture overlays still use the normal Build pipeline.

Raw streaming candidates use a source-bound MAN relocation request and a format-7
package. One MAN and one ANM growth request can share a physical carrier. The
composer applies original-address patches first, replays completed native header
relocations, preserves opaque chunks and reads back the exact final MAN/ANM bytes.
Compressed candidates exceeding the consumed source stream use the native
MAN encoder with descriptor-pointer relocation when its source slot must grow,
then whole-sector PROT owner relocation. Original table/descriptor identity,
decoded source hash, bounded native candidate and final exact payload are required.
A compressed MAN and ANM request can share one table in either descriptor order.
The qualified slot may admit a larger stream without physical growth; the package
still uses verified relocated-disc delivery. Multiple distinct tables in one
physical owner remain unsupported. Experimental growth export stays separate.
Passing source checks does not prove that copied scripts initialize a new NPC
correctly, refer to appropriate story state or permit valid runtime identity.

## Offline evidence — 2026-10-02

Town01 donor11 plus one draft and existing placement/facing edits passes source
composition and normal package readback. Partition counts change from
`[36,53,39]` to `[36,54,39]`; decoded MAN grows from45,338 to45,917 bytes.
Greedy output needs25,259 bytes; bounded optimal output uses24,856 within the
original24,894-byte stream. The new record53 retains retail donor scripts, and
reached decoded SPAWN_RECORD operands are independently checked after rebasing.
Only the original stream and descriptor size word change in the physical carrier.

Eleven focused Python checks pass with private source input and no skips. Legacy
and v2 Node review guards pass. Four actual browser scenarios verify inclusive
read-only review,540px layout, reviewed package creation and unchanged authored
files with no game requests or page errors. Private evidence is retained under
`local-output/sdk-20260909/npc-normal-build-20261002/`.

Manual acceptance remains queued: install the disabled candidate feature when
ready, verify the new NPC appears at the intended position, then check collision,
dialogue, scripts, transitions and save/reload behavior. No game was launched or
disc exported during this milestone.
