# Executable catalog pagination

Protocol 1.2 adds the native `executable_catalog` capability. The command has
three views: `images`, `ranges`, and `registrations`.

```json
{"cmd":"executable_catalog","view":"registrations","cursor":0,"limit":8}
```

The first page returns `catalog_token`, `ownership_token`, `returned`,
`has_more`, and `next_cursor`. Every continuation request must send the same
`catalog_token`. A structural catalog change returns `catalog_changed`; clients
must restart rather than combine revisions.

## Bounds

- limits from 1 through 8 are accepted;
- a larger or non-positive limit is rejected;
- serialization uses a 60,000-byte record budget inside the 65,536-byte
  response buffer;
- a single record that cannot fit returns `catalog record exceeds response
  budget`;
- records are never truncated or silently dropped; and
- one request produces one newline-delimited JSON response.

Eight is deliberately conservative for the worst currently serializable
registration record, including optional identities, predicates, range lists,
JSON punctuation, and the terminal paging fields. The legacy
`executable_regions` command remains available but now uses the same conservative
maximum.

## Tokens

The 64-bit hexadecimal **catalog token** is derived from the main executable's
stable source identity and the loader's structural registration metadata. It
changes when registrations, grouping, ranges, backends, or source ownership
change. Mutable validation state and unrelated RAM do not participate.

The 256-bit hexadecimal **ownership token** is derived from authoritative
watched generations for pages intersecting exact dispatch-registration ranges,
the main-text divergence bitmap, and loader registration state. It may change
between pages without invalidating structural paging; the client reports this
as unstable ownership. It does not include every watched page or the mutable
data portion of the canonical main image.

`tools/debug_client.py executable-catalog <view> [limit]` reconnects for each
page because the native server serves one command per connection. It enforces
the token and total, rejects repeated or non-advancing cursors, caps page count,
and returns both a compact summary and full JSON.
