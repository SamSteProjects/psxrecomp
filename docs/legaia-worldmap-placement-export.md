# Exporting Current and Proposed world placements

The **World placements** editor offers **Export Current scene GLB** and
**Export Proposed scene GLB**. Both include the complete qualified kingdom source
scene: terrain, resolved model instances, shared meshes and matched embedded
textures. These are private artifacts in the project `Exports` directory.

Current uses applied `WorldMapPlacements` record bindings, including unsaved
authored changes. Proposed requires a successful transform review and binds the
artifact to that exact review key. It composes the proposed record with other
applied world placement records without Apply, history, Save or Build writes.
Unreviewed input cannot be exported as Proposed. Choosing Current explicitly
excludes the pending proposal.

The GLB records its representation, source key, retail MAP identity, current and
exported MAP hashes, authored record bindings, proposal/review identity and the
number of changed source entities. Each instance retains its retail transform
and record identity alongside its exported transform and record hash. Positions
and yaw use the same qualified MAP patch construction as normal Build. The
renderer/exporter reflects source Y once; model geometry, materials, textures
and ground remain retail source assets. Other authoring component families are
not silently interpreted as world placement overrides.

The existing **World ground** exports remain explicitly retail-source exports.
Current/Proposed are source spawn seeds, with script-driven visibility, native
resting positions, collision and gameplay behavior still unverified.

The browser validates file name, binary structure/hash and Current/Proposed
provenance before downloading. Closing a pending operation or changing source
state prevents a late download; the already requested private artifact may have
been created. No operation launches a game.

## Offline evidence — 2026-10-02

Six focused Python cases pass with private retail input and no skips, including
the original source export regressions. Current/Proposed exports for all three
kingdoms preserve the exact retail mesh/image binary, mesh definitions and image
descriptors. Independent MAP reconstruction verifies every instance translation,
yaw and exported record hash. Stale proposals and drift before artifact writes
reject without output. Node guards use actual private artifacts to verify
representation, proposal, MAP hashes, bounds, file identity and binary digest.

Seven actual browser scenarios pass: Current download, unreviewed Proposed
rejection, reviewed Proposed download without Apply,540px controls, cancelled
late response, stale-source withdrawal and unchanged saved project/import/Build
files. No authoring commands, game requests or page errors occurred. Downloaded
Current and Proposed GLBs match independent exports byte-for-byte. Both contain
302 entities and57 transformed source seeds. The Current MAP hash matches the
previous independently reopened Build payload. Private evidence is retained under
`local-output/sdk-20260909/worldmap-placement-export-20261002/`.
