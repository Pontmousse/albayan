# Al-Bayan FastAPI to BuTeX 7.0.2 Worker Contract

## Purpose and ownership

The deployed Railway worker service is `albayan-butex`:

```text
Agent -> mcp_server -> FastAPI -> private BuTeX worker
                              -> session storage and revision
```

`mcp_server` is a thin FastAPI client and never calls the worker directly.
FastAPI owns users, articles, permissions, sessions, revisions, idempotency,
assets, storage, save/commit, and submission. The worker is stateless and owns
only Document2 normalization, outlines, and one-command transformations.

## Railway configuration

The worker and FastAPI run in the same Railway project and environment. The
worker needs no public domain.

Worker service:

```text
BUTEX_WORKER_TOKEN=${{shared.BUTEX_WORKER_TOKEN}}
```

FastAPI service:

```text
BUTEX_WORKER_URL=http://${{albayan-butex.RAILWAY_PRIVATE_DOMAIN}}:${{albayan-butex.PORT}}
BUTEX_WORKER_TOKEN=${{shared.BUTEX_WORKER_TOKEN}}
```

Every transform request uses:

```http
Authorization: Bearer <BUTEX_WORKER_TOKEN>
Content-Type: application/json
X-Request-ID: <host request or trace ID>
```

Neither variable belongs in Next.js public variables or `mcp_server`.

## Private worker HTTP API

- `GET /health` returns `{ "ok": true, "service": "butex-document2" }`.
- `POST /v1/document2/normalize` accepts `{ "document": Document2Json }`.
- `POST /v1/document2/outline` accepts `{ "document": Document2Json }`.
- `POST /v1/document2/commands` accepts
  `{ "document": Document2Json, "command": Document2Command }`.

Transform routes require the bearer token; health does not. Bodies are limited
to 5 MiB and requests time out after 15 seconds. The route selects the action;
HTTP bodies do not contain an `action` field.

Normalize legacy or external JSON once when opening a session and persist the
returned canonical document. Outlines require unique canonical block IDs and
return top-level entries in document order. Kinds are `section`, `subsection`,
`subsubsection`, `paragraph`, `list`, `table`, `figure`, `bibliography`, or `raw`.

## Canonical identities and provenance

Text-bearing fields carry an identity sidecar:

```ts
type InlineIds = {
  field_id: string;
  tokens: Array<{
    id: string;
    kind: 'text' | 'math' | 'cite' | 'ref';
    start: number;
    end: number;
  }>;
};
```

Text blocks use `inline_ids`; list items use stable `id` and `inline_ids`; table
cells use `cell_inline_ids` parallel to `rows`. Offsets are JavaScript string
offsets. FastAPI never constructs or repairs these sidecars.

Every block may contain `metadata: { source: 'agent' | 'user' }`, recording its
creator rather than its latest editor. For `insert_text_block`, `insert_figure`,
`insert_bibliography`, `insert_list`, and `insert_table`, FastAPI overwrites
caller metadata from the authenticated actor: agent credentials produce
`agent`; browser credentials produce `user`.

## Command contract

Block anchors are exactly one of `{ before_block_id }`, `{ after_block_id }`, or
`{ end: true }`. Inline anchors use `before_token_id`, `after_token_id`,
`start: true`, or `end: true`. Item anchors use `before_item_id`,
`after_item_id`, or `end: true`. Reference anchors use `before_reference_key`,
`after_reference_key`, or `end: true`.

### Blocks and figures

```text
insert_text_block: kind, text, block anchor, optional metadata
replace_text_block: block_id, text
remove_block: block_id
move_block: block_id, block anchor
insert_figure: asset_id, optional value/caption/label/metadata, block anchor
update_figure: block_id plus asset_id and/or value
update_float_meta: block_id plus centered/caption_enabled/caption/label_enabled/label
insert_bibliography: block anchor, optional metadata
```

`update_figure.asset_id: null` clears only the host identity and must remain an
explicit null on the wire. `value: ""` clears only the include value. FastAPI
authorizes every non-null asset supplied to `insert_figure` or `update_figure`
before dispatch.

### Article metadata and references

```text
update_document_meta: one or more of title, authors, abstract, partial date
insert_reference: key, optional bibliographic fields, reference anchor
update_reference: reference_key plus one or more bibliographic fields
remove_reference: reference_key
move_reference: reference_key, reference anchor
```

Hijri dates use day 1-30, years 1400-1500, and BuTeX's twelve Arabic month
identifiers. Reference fields are `key`, `authors`, `title`, `year`, `venue`,
`url`, and `field_separator` (`","` or `"،"`). The worker NFC-normalizes
keys and enforces their shared namespace with figure, table, and equation labels.
Removing or renaming a reference does not rewrite citation tokens.

### Inline tokens

```ts
type InlineTokenInput =
  | { kind: 'text'; text: string; style?: {
      bold?: true; italic?: true; underline?: true
    } }
  | { kind: 'math'; source: string; math_object: MathObjectJson }
  | { kind: 'cite'; keys: string[] }
  | { kind: 'ref'; keys: string[]; ref_command: 'ref' | 'eqref' };
```

`insert_inline_token`, `replace_inline_token`, and `remove_inline_token` carry
`field_id`; replacement/removal carry `token_id`; insertion carries an inline
anchor. Math supplies exactly one complete delimited source and a matching
structured `MathObject`. The worker never parses raw equation LaTeX into an AST.

Whole-field replacement is rejected for styled or structured content. Citation
and reference token arrays retain at least one non-empty key.

### Lists

```text
insert_list: ordered, non-empty items[], block anchor, optional metadata
insert_list_item: list_id, text, item anchor
replace_list_item: list_id, item_id, text
remove_list_item: list_id, item_id
move_list_item: list_id, item_id, item anchor
```

List lookup is recursive and every list retains at least one item.

### Tables

```text
insert_table: non-empty rectangular rows[][], columns, block anchor,
              optional caption/label/metadata
replace_table_cell: table_id, row_index, column_index, text
insert_table_row: table_id, index, values[]
remove_table_row: table_id, index
move_table_row: table_id, from_index, to_index
insert_table_column: table_id, index, values[], columns
remove_table_column: table_id, index, columns
move_table_column: table_id, from_index, to_index, columns
```

Indexes are zero-based. Tables retain at least one row and column. Column shape
commands provide the complete resulting non-empty LaTeX `columns` specification.

### Host and worker request example

The public host request is:

```json
{
  "command_id": "62ca7688-7f10-4d35-8ef8-71fd77d6b3b8",
  "base_revision": 12,
  "command": {
    "op": "insert_text_block",
    "kind": "paragraph",
    "text": "New paragraph",
    "anchor": { "before_block_id": "block_4" },
    "metadata": { "source": "user" }
  }
}
```

For an authenticated agent, FastAPI dispatches only:

```json
{
  "document": { "node_type": "DocumentObject", "blocks": [] },
  "command": {
    "op": "insert_text_block",
    "kind": "paragraph",
    "text": "New paragraph",
    "anchor": { "before_block_id": "block_4" },
    "metadata": { "source": "agent" }
  }
}
```

`command_id`, `base_revision`, actor data, article IDs, and session IDs never go
to the worker.

## Errors

Worker failures have one shape:

```json
{
  "ok": false,
  "error": {
    "code": "block_not_found",
    "message": "Document block was not found"
  }
}
```

- `400`: malformed JSON or request.
- `401`: missing or invalid worker token.
- `404`: unknown worker route.
- `413`: request over 5 MiB.
- `422`: invalid document or command semantics.
- `500`: unexpected worker failure.

Expected command codes include `invalid_document`, `invalid_command`,
`invalid_anchor`, `anchor_not_found`, `block_not_found`,
`block_kind_mismatch`, `field_not_found`, `token_not_found`, `list_not_found`,
`item_not_found`, `table_not_found`, `invalid_table_shape`,
`index_out_of_range`, `minimum_structure`, `invalid_inline_token`,
`math_object_mismatch`, `unsupported_inline_content`, `reference_not_found`,
`invalid_key`, `duplicate_key`, and `bibliography_exists`.

FastAPI preserves expected worker statuses and codes, maps unreachable or
invalid responses to `502`, and maps timeouts to `504`. Never log the token or a
complete document body.

## FastAPI session command API

The public route is:

```http
POST /api/v1/articles/{article_id}/session/commands
```

FastAPI authenticates the actor, replays an already completed matching
`command_id`, loads the canonical session document, rejects stale revisions,
adds host provenance, validates figure assets, dispatches one command, performs
compare-and-swap persistence, records the result, and increments the revision.

Repeated command IDs return the stored response only when the submitted command
and base revision hash match. Indexes and anchors are never retried against a
newer revision.

`affected_block_ids` returns direct `block_id`, `list_id`, or `table_id`
targets, resolves an inline `field_id` to its containing block, and detects a
new top-level ID after insertion. Metadata and reference commands return `[]`.

## Verification

Run the contract tests from the repository root:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m unittest \
  backend.tests.test_document2_command_schemas \
  backend.tests.test_article_sessions \
  backend.tests.test_butex_worker_client \
  backend.tests.test_butex_real_worker_integration
```

The integration test starts the installed BuTeX HTTP CLI on loopback and skips
with an explicit reason when Node, frontend dependencies, or loopback sockets
are unavailable.

For a Railway private-network smoke check, open a shell in FastAPI and run:

```bash
curl --fail --silent "$BUTEX_WORKER_URL/health"
curl --fail --silent \
  -H "Authorization: Bearer $BUTEX_WORKER_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"document":{"node_type":"DocumentObject","blocks":[]}}' \
  "$BUTEX_WORKER_URL/v1/document2/normalize"
```

Finally, apply a command through the public session endpoint and verify that the
revision increments once, a command record is persisted, and retrying the same
`command_id` returns the original result.
