"use client";

import { ChangeEvent, DragEvent, useMemo, useRef, useState } from "react";

type Confidence =
  | "confirmed"
  | "strongly_inferred"
  | "tentative"
  | "unknown"
  | "contradictory";

type Claim = {
  property: string;
  value: unknown;
  confidence: Confidence;
  evidence: Array<{ kind?: string; locator?: string; observation?: string }>;
  source: Record<string, unknown>;
  notes: string;
};

type Actor = {
  semantic_id: string;
  source_record: {
    iso_file: string;
    prot_entry_index: number;
    prot_entry_name?: string;
    record_kind: string;
    record_index: number;
    byte_offset: number;
    byte_length: number;
    byte_coordinate_space: string;
    scene_bundle?: {
      kind?: string;
      man_descriptor_index?: number;
      decoded_size?: number;
    };
  };
  imported_transform: {
    position: { x: number; y: number | null; z: number };
    rotation: unknown;
    coordinate_system?: string;
    placement_tile?: { x: number; z: number };
  };
  model_reference: {
    source_entry?: number | null;
    model_index: number;
    normalized_pool_index?: number;
    model_pool: string;
    asset_semantic_id?: string | null;
    referenced_asset_record: string | null;
    resolution_status: string;
  };
  placement_fields?: { animation_id?: number; local_count?: number };
  claims: Claim[];
  unresolved: string[];
};

type ModelAsset = {
  semantic_id: string;
  asset_kind: string;
  scope: string;
  model_pool: string;
  encoded_model_index: number;
  normalized_pool_index: number;
  source_record: {
    prot_entry_index: number;
    record_kind: string;
    byte_offset: number;
    byte_length: number;
    byte_coordinate_space: string;
    containing_size: number;
    container_section?: number;
    pack_slot?: number;
    object_count?: number;
  };
  claims: Claim[];
  dependencies: unknown[];
  aliases: unknown[];
  unresolved: string[];
};

type ImportDocument = {
  schema_version: string;
  importer_version: string;
  source: {
    disc_build: string;
    disc_identity: string;
    scene_name: string;
    reference_repositories?: Array<{ repository: string; commit: string; role?: string }>;
  };
  scene: {
    semantic_id: string;
    name: string;
    man_partition_counts?: number[];
    source?: { bundle_entry?: number };
  };
  actors: Actor[];
  assets?: { models: ModelAsset[] };
  diagnostics: Array<Record<string, unknown>>;
  unresolved: string[];
};

const confidenceOrder: Confidence[] = [
  "contradictory",
  "unknown",
  "tentative",
  "strongly_inferred",
  "confirmed",
];

const SAMPLE_IMPORT: ImportDocument = {
  schema_version: "legaia.scene-import.v2",
  importer_version: "0.2.0",
  source: {
    disc_build: "Synthetic metadata preview — no retail data",
    disc_identity: `sha256:${"0".repeat(64)}`,
    scene_name: "town01",
    reference_repositories: [
      {
        repository: "AndrewAltimit/legend-of-legaia-re",
        commit: "d6e64c68ede25813d35db20980da82a1a025549b",
        role: "development_reference_and_parity_oracle",
      },
    ],
  },
  scene: {
    semantic_id: "scene://town01",
    name: "town01",
    man_partition_counts: [2, 4, 1],
    source: { bundle_entry: 3 },
  },
  actors: [
    makeSampleActor(1, 448, 704, 4, "scene_tmd", "confirmed"),
    makeSampleActor(2, 960, 576, 11, "scene_tmd", "unknown"),
    makeSampleActor(3, 704, 1088, 241, "global_special", "confirmed"),
  ],
  assets: {
    models: [makeSampleModelAsset(4, "scene_tmd"), makeSampleModelAsset(11, "scene_tmd"), makeSampleModelAsset(241, "global_special")],
  },
  diagnostics: [],
  unresolved: [
    "actor facing/rotation before script execution",
    "vertical placement coordinate",
  ],
};

function modelAssetId(modelIndex: number, pool: string) {
  return pool === "global_special"
    ? `asset://legaia/models/global-special/${modelIndex.toString(16).padStart(4, "0")}`
    : `asset://town01/models/scene-tmd/${modelIndex.toString().padStart(4, "0")}`;
}

function makeSampleModelAsset(modelIndex: number, pool: string): ModelAsset {
  const normalized = pool === "global_special" ? modelIndex - 0xf0 : modelIndex;
  const semanticId = modelAssetId(modelIndex, pool);
  const source = {
    prot_entry_index: pool === "global_special" ? 874 : 4,
    record_kind: pool === "global_special" ? "decoded_tmd_pack_slot" : "decoded_lzs_section",
    byte_offset: normalized * 96,
    byte_length: 72,
    byte_coordinate_space: "decoded_lzs_section",
    containing_size: 4096,
    container_section: 0,
    pack_slot: pool === "global_special" ? normalized : undefined,
    object_count: 1,
  };
  return {
    semantic_id: semanticId,
    asset_kind: "tmd_model",
    scope: pool === "global_special" ? "global" : "scene",
    model_pool: pool,
    encoded_model_index: modelIndex,
    normalized_pool_index: normalized,
    source_record: source,
    claims: [sampleClaim("semantic_id", semanticId, "confirmed", "Synthetic structural pool identity.")],
    dependencies: [],
    aliases: [],
    unresolved: ["character or object identity", "animation and texture bindings"],
  };
}

function makeSampleActor(
  index: number,
  x: number,
  z: number,
  modelIndex: number,
  pool: string,
  modelAssetConfidence: Confidence,
): Actor {
  const source = {
    iso_file: "PROT.DAT",
    prot_entry_index: 3,
    prot_entry_name: "town01",
    record_kind: "man_partition_1_actor_placement",
    record_index: index,
    byte_offset: 128 + index * 24,
    byte_length: 24,
    byte_coordinate_space: "decoded_man_payload",
    scene_bundle: {
      kind: "scene_asset_table",
      man_descriptor_index: 1,
      decoded_size: 4096,
    },
  };
  return {
    semantic_id: `scene://town01/actors/man-p1/${String(index).padStart(4, "0")}`,
    source_record: source,
    imported_transform: {
      position: { x, y: null, z },
      rotation: null,
      coordinate_system: "retail_field_world_units",
      placement_tile: { x: Math.floor(x / 128), z: Math.floor(z / 128) },
    },
    model_reference: {
      source_entry: pool === "global_special" ? 874 : 4,
      model_index: modelIndex,
      normalized_pool_index: pool === "global_special" ? modelIndex - 0xf0 : modelIndex,
      model_pool: pool,
      asset_semantic_id: modelAssetId(modelIndex, pool),
      referenced_asset_record: modelAssetId(modelIndex, pool),
      resolution_status: "resolved",
    },
    placement_fields: { animation_id: index % 2, local_count: index - 1 },
    claims: [
      sampleClaim("source_record", source, "confirmed", "Synthetic structural parser span."),
      sampleClaim(
        "imported_transform.position",
        { x, y: null, z },
        "confirmed",
        "Synthetic placement coordinates using the documented X/Z conversion.",
      ),
      sampleClaim(
        "imported_transform.rotation",
        null,
        "unknown",
        "The placement header does not contain a confirmed facing field.",
      ),
      sampleClaim(
        "model_reference.model_index",
        { index: modelIndex, pool },
        "confirmed",
        "Synthetic model-pool selector metadata.",
      ),
      sampleClaim(
        "model_reference.referenced_asset_record",
        modelAssetId(modelIndex, pool),
        modelAssetConfidence,
        "Synthetic preview claim for structural asset identity rendering.",
      ),
    ],
    unresolved: [
      "imported_transform.position.y",
      "imported_transform.rotation",
    ],
  };
}

function sampleClaim(property: string, value: unknown, confidence: Confidence, notes: string): Claim {
  return {
    property,
    value,
    confidence,
    evidence: [{ kind: "synthetic_fixture", locator: "inspector/sample", observation: notes }],
    source: { fixture: true },
    notes,
  };
}

function isImportDocument(value: unknown): value is ImportDocument {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<ImportDocument>;
  return (
    (candidate.schema_version === "legaia.scene-import.v1" || candidate.schema_version === "legaia.scene-import.v2") &&
    candidate.scene?.name === "town01" &&
    Array.isArray(candidate.actors) &&
    candidate.actors.every(
      (actor) =>
        typeof actor?.semantic_id === "string" &&
        actor.semantic_id.startsWith("scene://town01/actors/") &&
        typeof actor.source_record?.record_index === "number" &&
        typeof actor.imported_transform?.position?.x === "number" &&
        typeof actor.imported_transform?.position?.z === "number" &&
        Array.isArray(actor.claims),
    ) &&
    (candidate.schema_version === "legaia.scene-import.v1" || Array.isArray(candidate.assets?.models))
  );
}

function shortHash(identity: string) {
  const value = identity.replace("sha256:", "");
  return `${value.slice(0, 10)}…${value.slice(-6)}`;
}

function recordLabel(actor: Actor) {
  return `P1 / ${String(actor.source_record.record_index).padStart(4, "0")}`;
}

function formatValue(value: unknown) {
  if (value === null || value === undefined) return "unresolved";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value, null, 2);
}

export default function Home() {
  const [document, setDocument] = useState<ImportDocument>(SAMPLE_IMPORT);
  const [selectedId, setSelectedId] = useState(SAMPLE_IMPORT.actors[0].semantic_id);
  const [query, setQuery] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState<Confidence | "all">("all");
  const [sourceName, setSourceName] = useState("Synthetic preview");
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const selected =
    document.actors.find((actor) => actor.semantic_id === selectedId) ?? document.actors[0];
  const selectedModelAsset = document.assets?.models.find(
    (asset) => asset.semantic_id === selected?.model_reference.asset_semantic_id,
  );

  const filteredActors = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return document.actors.filter((actor) => {
      const matchesQuery =
        !normalized ||
        actor.semantic_id.toLowerCase().includes(normalized) ||
        recordLabel(actor).toLowerCase().includes(normalized) ||
        String(actor.model_reference.model_index).includes(normalized);
      const matchesConfidence =
        confidenceFilter === "all" ||
        actor.claims.some((item) => item.confidence === confidenceFilter);
      return matchesQuery && matchesConfidence;
    });
  }, [confidenceFilter, document.actors, query]);

  const claimCounts = useMemo(() => {
    const counts = Object.fromEntries(confidenceOrder.map((value) => [value, 0])) as Record<
      Confidence,
      number
    >;
    document.actors.forEach((actor) => actor.claims.forEach((item) => counts[item.confidence]++));
    return counts;
  }, [document.actors]);

  const plotBounds = useMemo(() => {
    const xs = document.actors.map((actor) => actor.imported_transform.position.x);
    const zs = document.actors.map((actor) => actor.imported_transform.position.z);
    return {
      minX: Math.min(...xs),
      maxX: Math.max(...xs),
      minZ: Math.min(...zs),
      maxZ: Math.max(...zs),
    };
  }, [document.actors]);

  async function loadFile(file: File) {
    setError(null);
    if (!file.name.toLowerCase().endsWith(".json")) {
      setError("Choose the metadata-only JSON produced by legaia-import.");
      return;
    }
    try {
      const parsed: unknown = JSON.parse(await file.text());
      if (!isImportDocument(parsed)) {
        throw new Error("Expected schema legaia.scene-import.v1 or v2 for scene town01.");
      }
      setDocument(parsed);
      setSelectedId(parsed.actors[0]?.semantic_id ?? "");
      setSourceName(file.name);
      setQuery("");
      setConfidenceFilter("all");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The JSON could not be read.");
    }
  }

  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) void loadFile(file);
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0];
    if (file) void loadFile(file);
  }

  function resetSample() {
    setDocument(SAMPLE_IMPORT);
    setSelectedId(SAMPLE_IMPORT.actors[0].semantic_id);
    setSourceName("Synthetic preview");
    setQuery("");
    setConfidenceFilter("all");
    setError(null);
  }

  const reference = document.source.reference_repositories?.[0];

  return (
    <main className="workbench">
      <header className="topbar">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">L</span>
          <div>
            <p className="eyebrow">PSXRecomp integration</p>
            <h1>Legaia Trace</h1>
          </div>
        </div>
        <div className="topbar-state">
          <span className="state-dot" /> Read-only
          <span className="topbar-divider" /> Local JSON only
        </div>
        <div className="file-actions">
          <button className="ghost-button" type="button" onClick={resetSample}>
            Reset preview
          </button>
          <button className="primary-button" type="button" onClick={() => fileInput.current?.click()}>
            Open import
          </button>
          <input
            ref={fileInput}
            className="visually-hidden"
            type="file"
            accept="application/json,.json"
            onChange={handleFile}
          />
        </div>
      </header>

      <section className="source-strip" aria-label="Import source">
        <div className="source-primary">
          <span className="source-kicker">Loaded snapshot</span>
          <strong>{sourceName}</strong>
          <span className={sourceName === "Synthetic preview" ? "fixture-pill" : "verified-pill"}>
            {sourceName === "Synthetic preview" ? "synthetic" : "imported"}
          </span>
        </div>
        <dl className="source-facts">
          <div><dt>Scene</dt><dd>{document.scene.name}</dd></div>
          <div><dt>Actors</dt><dd>{document.actors.length}</dd></div>
          <div><dt>Schema</dt><dd>{document.schema_version.replace("legaia.", "")}</dd></div>
          <div><dt>Disc</dt><dd>{shortHash(document.source.disc_identity)}</dd></div>
          <div><dt>Reference</dt><dd>{reference?.commit.slice(0, 9) ?? "not listed"}</dd></div>
        </dl>
      </section>

      {error && <div className="error-banner" role="alert"><strong>Import rejected.</strong> {error}</div>}

      <div className="workspace-grid">
        <aside className="actor-panel panel">
          <div className="panel-heading">
            <div><p className="eyebrow">Scene index</p><h2>Actor records</h2></div>
            <span className="count-badge">{filteredActors.length}/{document.actors.length}</span>
          </div>
          <label className="search-field">
            <span className="visually-hidden">Search actors</span>
            <span aria-hidden="true">⌕</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Record or model index"
            />
          </label>
          <div className="filter-row" aria-label="Confidence filter">
            {(["all", "confirmed", "unknown", "contradictory"] as const).map((value) => (
              <button
                type="button"
                key={value}
                className={confidenceFilter === value ? "filter-chip active" : "filter-chip"}
                onClick={() => setConfidenceFilter(value)}
              >
                {value === "all" ? "All" : value.replace("_", " ")}
              </button>
            ))}
          </div>
          <nav className="actor-list" aria-label="Actor records">
            {filteredActors.map((actor) => {
              const unknown = actor.claims.filter((item) => item.confidence === "unknown").length;
              return (
                <button
                  type="button"
                  key={actor.semantic_id}
                  className={actor.semantic_id === selected?.semantic_id ? "actor-row selected" : "actor-row"}
                  onClick={() => setSelectedId(actor.semantic_id)}
                >
                  <span className="record-index">{String(actor.source_record.record_index).padStart(2, "0")}</span>
                  <span className="actor-row-copy">
                    <strong>{recordLabel(actor)}</strong>
                    <small>model {actor.model_reference.model_index} · {actor.model_reference.model_pool}</small>
                  </span>
                  {unknown > 0 && <span className="unknown-count" title={`${unknown} unknown claims`}>{unknown}?</span>}
                </button>
              );
            })}
            {filteredActors.length === 0 && <p className="empty-list">No records match this view.</p>}
          </nav>
          <div
            className={dragActive ? "drop-zone active" : "drop-zone"}
            onDragEnter={(event) => { event.preventDefault(); setDragActive(true); }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
          >
            <strong>Drop importer JSON</strong>
            <span>Parsed in this browser. Nothing is uploaded.</span>
          </div>
        </aside>

        <section className="scene-column">
          <div className="scene-panel panel">
            <div className="panel-heading scene-heading">
              <div><p className="eyebrow">Placement projection</p><h2>{document.scene.semantic_id}</h2></div>
              <div className="axis-key"><span className="axis-x">X</span><span className="axis-z">Z</span></div>
            </div>
            <div className="plot-frame">
              <div className="plot-grid" aria-label="Actor X and Z placement map">
                <span className="north-label">− Z</span>
                {document.actors.map((actor) => {
                  const { x, z } = actor.imported_transform.position;
                  const left = 10 + ((x - plotBounds.minX) / Math.max(plotBounds.maxX - plotBounds.minX, 1)) * 80;
                  const top = 10 + ((z - plotBounds.minZ) / Math.max(plotBounds.maxZ - plotBounds.minZ, 1)) * 80;
                  const isSelected = actor.semantic_id === selected?.semantic_id;
                  return (
                    <button
                      type="button"
                      key={actor.semantic_id}
                      className={isSelected ? "plot-point selected" : "plot-point"}
                      style={{ left: `${left}%`, top: `${top}%` }}
                      onClick={() => setSelectedId(actor.semantic_id)}
                      aria-label={`${recordLabel(actor)}, X ${x}, Z ${z}`}
                    >
                      <span>{actor.source_record.record_index}</span>
                    </button>
                  );
                })}
                <div className="plot-origin"><span>0</span></div>
              </div>
              <p className="plot-caption">
                Structural placement view only — no retail geometry, collision, or textures are loaded.
              </p>
            </div>
          </div>

          <div className="confidence-panel panel">
            <div className="panel-heading compact">
              <div><p className="eyebrow">Evidence posture</p><h2>Claim confidence</h2></div>
              <span className="mono-note">{document.actors.reduce((sum, actor) => sum + actor.claims.length, 0)} claims</span>
            </div>
            <div className="confidence-bars">
              {confidenceOrder.map((value) => {
                const total = Math.max(document.actors.reduce((sum, actor) => sum + actor.claims.length, 0), 1);
                return (
                  <div className="confidence-row" key={value}>
                    <span className={`confidence-dot ${value}`} />
                    <span>{value.replace("_", " ")}</span>
                    <div className="bar-track"><i className={value} style={{ width: `${(claimCounts[value] / total) * 100}%` }} /></div>
                    <strong>{claimCounts[value]}</strong>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <aside className="inspector-panel panel">
          {selected ? (
            <>
              <div className="inspector-header">
                <p className="eyebrow">Selected source entity</p>
                <h2>{recordLabel(selected)}</h2>
                <code>{selected.semantic_id}</code>
              </div>

              <InspectorSection title="Imported transform" badge="confirmed">
                <div className="coordinate-grid">
                  {(["x", "y", "z"] as const).map((axis) => (
                    <div key={axis} className={selected.imported_transform.position[axis] === null ? "coordinate unresolved" : "coordinate"}>
                      <span>{axis.toUpperCase()}</span>
                      <strong>{selected.imported_transform.position[axis] ?? "—"}</strong>
                    </div>
                  ))}
                </div>
                <KeyValue label="Rotation" value={selected.imported_transform.rotation ?? "unknown"} muted />
                <KeyValue label="Coordinates" value={selected.imported_transform.coordinate_system ?? "not declared"} />
              </InspectorSection>

              <InspectorSection title="Model reference" badge="mixed">
                <div className="model-index-card">
                  <span>Pool index</span><strong>{selected.model_reference.model_index}</strong>
                </div>
                <KeyValue label="Pool" value={selected.model_reference.model_pool} />
                <KeyValue label="Normalized slot" value={selected.model_reference.normalized_pool_index ?? selected.model_reference.model_index} />
                <KeyValue label="Resolution" value={selected.model_reference.resolution_status} />
                <KeyValue label="Asset semantic ID" value={selected.model_reference.asset_semantic_id ?? selected.model_reference.referenced_asset_record ?? "unknown"} muted />
                {selectedModelAsset && (
                  <>
                    <KeyValue label="Asset PROT entry" value={selectedModelAsset.source_record.prot_entry_index} />
                    <KeyValue label="Asset source kind" value={selectedModelAsset.source_record.record_kind} />
                    <KeyValue label="Asset source span" value={`0x${selectedModelAsset.source_record.byte_offset.toString(16).toUpperCase()} + ${selectedModelAsset.source_record.byte_length}`} />
                    <KeyValue label="Asset coordinates" value={selectedModelAsset.source_record.byte_coordinate_space} />
                    <KeyValue label="Asset unresolved" value={selectedModelAsset.unresolved.join("; ")} muted />
                  </>
                )}
              </InspectorSection>

              <InspectorSection title="Source record" badge="confirmed">
                <KeyValue label="ISO file" value={selected.source_record.iso_file} />
                <KeyValue label="PROT entry" value={selected.source_record.prot_entry_index} />
                <KeyValue label="MAN record" value={selected.source_record.record_index} />
                <KeyValue label="Decoded span" value={`0x${selected.source_record.byte_offset.toString(16).toUpperCase()} + ${selected.source_record.byte_length}`} />
                <KeyValue label="Coordinate space" value={selected.source_record.byte_coordinate_space} />
              </InspectorSection>

              <InspectorSection title="Claims" badge={`${selected.claims.length}`}>
                <div className="claim-list">
                  {selected.claims.map((item, index) => (
                    <details className="claim-card" key={`${item.property}-${index}`} open={index === 0}>
                      <summary>
                        <span className={`confidence-dot ${item.confidence}`} />
                        <span><strong>{item.property}</strong><small>{item.confidence.replace("_", " ")}</small></span>
                        <span className="disclosure">＋</span>
                      </summary>
                      <div className="claim-body">
                        <pre>{formatValue(item.value)}</pre>
                        <p>{item.notes || "No notes supplied."}</p>
                        {item.evidence.map((evidence, evidenceIndex) => (
                          <div className="evidence-line" key={evidenceIndex}>
                            <span>{evidence.kind ?? "evidence"}</span>
                            <code>{evidence.locator ?? evidence.observation ?? "no locator"}</code>
                          </div>
                        ))}
                      </div>
                    </details>
                  ))}
                </div>
              </InspectorSection>

              <InspectorSection title="Unresolved" badge={`${selected.unresolved.length}`}>
                <ul className="unresolved-list">
                  {selected.unresolved.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </InspectorSection>
            </>
          ) : (
            <div className="empty-inspector"><p>No actor records are present in this import.</p></div>
          )}
        </aside>
      </div>

      <footer>
        <span>Importer {document.importer_version}</span>
        <span>Metadata-only inspection</span>
        <span>No PSXRecomp connection</span>
      </footer>
    </main>
  );
}

function InspectorSection({
  title,
  badge,
  children,
}: {
  title: string;
  badge: string;
  children: React.ReactNode;
}) {
  return (
    <section className="inspector-section">
      <div className="section-title"><h3>{title}</h3><span>{badge}</span></div>
      {children}
    </section>
  );
}

function KeyValue({ label, value, muted = false }: { label: string; value: unknown; muted?: boolean }) {
  return (
    <div className={muted ? "key-value muted" : "key-value"}>
      <span>{label}</span><code>{String(value)}</code>
    </div>
  );
}
