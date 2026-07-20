# Executable lifecycle protocol

Protocol 1.3 adds the native capability `executable_image_lifecycle` and the
`executable_lifecycle` command. Protocol 1.2 clients remain valid because the
revision is additive.

## Request

```json
{"cmd":"executable_lifecycle","view":"instances","cursor":0,"limit":8}
```

Views are `instances`, `owners`, `owner`, and `events`. The hard page maximum is eight
records and the existing 65,536-byte response ceiling applies. Continuation
requests must repeat `lifecycle_token`; a changed token returns
`lifecycle_changed` rather than a mixed catalog. The client also rejects
repeated cursors and excessive page counts.

`instances` is ordered by creation. It reports exact capture spans, capture and
current-live identities, active/superseded state, lifecycle generation,
predecessor/successor links, and deliberately null whole-image fields where the
runtime lacks evidence.

`owners` is ordered by guest address. `owner` accepts one bounded `addr` and
returns at most one exact record without traversing a changing table. They
report the exact PC, last observed
backend, current-generation status, reason, image-instance relationship, and
native-registration relationship. `current_execution_owner` is null after a
watched write until dispatch observes the backend again.

`events` is ordered by sequence. Events are `created`, `superseded`,
`owner-acquired`, and `owner-changed`. The response reports the oldest and
latest retained event sequence. A cursor older than the bounded ring fails with
`lifecycle event cursor evicted`.

No view returns executable bytes, RAM payloads, host paths, or source paths.
Full-span SHA-256 work occurs only when an instance page is requested; normal
`read_regions` polling does not traverse lifecycle records or recompute these
hashes.
