# Al-Bayan FastAPI to BuTeX Worker Contract

## Purpose

- This is the Al-Bayan host integration contract for its deployed BuTeX Node
  worker, whose Railway service name is `albayan-butex`.
- The existing ownership model remains unchanged:

```text
Agent -> mcp_server -> FastAPI -> private BuTeX worker
                              -> session storage and revision
```

- `mcp_server` remains a thin FastAPI client and never calls the worker.
- FastAPI owns users, articles, authorization, sessions, revisions, idempotency,
  assets, S3, commit, and submission.
- The worker owns only stateless `documentJson` normalization, outlines, and
  one-command transformations.
- FastAPI keeps one ephemeral `article_sessions` row per active article
  workbench. The row points at the current draft `article_versions` row; the
  session document and command idempotency records live in S3.

## Railway Configuration

The worker and FastAPI must run in the same Railway project and environment.
The worker needs no public domain.

Worker service:

```text
BUTEX_WORKER_TOKEN=${{shared.BUTEX_WORKER_TOKEN}}
```

FastAPI service:

```text
BUTEX_WORKER_URL=http://${{albayan-butex.RAILWAY_PRIVATE_DOMAIN}}:${{albayan-butex.PORT}}
BUTEX_WORKER_TOKEN=${{shared.BUTEX_WORKER_TOKEN}}
```

FastAPI sends these headers to every transform endpoint:

```http
Authorization: Bearer <BUTEX_WORKER_TOKEN>
Content-Type: application/json
X-Request-ID: <host request or trace ID>
```

Do not put either worker variable in Next.js public variables or `mcp_server`.
`BUTEX_WORKER_URL` is an Al-Bayan FastAPI setting; it is not read by the BuTeX
package or worker process itself.

## Private Worker HTTP API

| Method and path | Request body | Successful response |
|---|---|---|
| `GET /health` | none | `{ "ok": true, "service": "butex-document" }` |
| `POST /v1/document/normalize` | `{ "document": documentJson }` | `{ "ok": true, "document": documentJson }` |
| `POST /v1/document/outline` | `{ "document": documentJson }` | `{ "ok": true, "outline": documentOutlineEntry[] }` |
| `POST /v1/document/commands` | `{ "document": documentJson, "command": documentCommand }` | `{ "ok": true, "document": documentJson }` |

- Transform endpoints require the bearer token; `/health` does not.
- The `/health` value `service: "butex-document"` identifies the packaged
  worker process; the Railway service containing it is `albayan-butex`.
- The maximum request body is 5 MiB.
- The worker request timeout is 15 seconds.
- HTTP request bodies do not include an `action`; the route selects the action.

### Normalize

Use this once when creating a session from legacy or externally supplied JSON.
Persist the returned canonical document so later outlines and commands use stable
block IDs.

```json
{
  "document": {
    "node_type": "DocumentObject",
    "blocks": [
      { "command": "\\paragraph", "value": "Legacy paragraph" }
    ]
  }
}
```

### Outline

Input must be canonical JSON with unique block IDs. Entries remain in top-level
document order:

```json
{
  "ok": true,
  "outline": [
    {
      "id": "block_1",
      "kind": "paragraph",
      "command": "\\paragraph",
      "excerpt": "Legacy paragraph"
    }
  ]
}
```

`kind` is one of `section`, `subsection`, `subsubsection`, `paragraph`, `list`,
`table`, `figure`, `bibliography`, or `raw`. Excerpts have normalized whitespace
and are limited to 160 characters.

## Command Contract

Commands operate on top-level blocks only.

```ts
type documentCommand =
  | {
      op: 'insert_text_block';
      kind: 'section' | 'subsection' | 'subsubsection' | 'paragraph';
      text: string;
      anchor: { after_block_id: string } | { end: true };
    }
  | { op: 'replace_text_block'; block_id: string; text: string }
  | { op: 'remove_block'; block_id: string }
  | {
      op: 'insert_figure';
      asset_id: string;
      value?: string;
      caption?: string;
      label?: string;
      anchor: { after_block_id: string } | { end: true };
    };
```

Example worker request:

```json
{
  "document": {
    "node_type": "DocumentObject",
    "blocks": []
  },
  "command": {
    "op": "insert_text_block",
    "kind": "paragraph",
    "text": "New paragraph",
    "anchor": { "end": true }
  }
}
```

Rules:

- An unknown `after_block_id` is an error; it never silently appends.
- `replace_text_block` rejects formatted or structured inline content to avoid
  losing equations, citations, or formatting.
- `insert_figure.asset_id` is the host-owned stable asset identity. The worker
  does not list, upload, authorize, resolve, or fetch the asset.
- The input document is not stored or mutated outside the request. Only the
  returned canonical document may be saved by FastAPI.
- The worker response does not include revisions, command IDs, or article IDs.

## Errors

Every failure body has one shape:

```json
{
  "ok": false,
  "error": {
    "code": "block_not_found",
    "message": "Document block was not found: block_9"
  }
}
```

| Status | Meaning |
|---|---|
| `400` | malformed JSON or invalid worker request |
| `401` | missing or invalid worker bearer token |
| `404` | unknown worker route |
| `413` | request body exceeds 5 MiB |
| `422` | valid protocol request with an invalid document or command |
| `500` | unexpected worker failure |

Expected `422` codes include `invalid_document`, `invalid_command`,
`missing_block_id`, `duplicate_block_id`, `anchor_not_found`, `block_not_found`,
`block_kind_mismatch`, and `unsupported_inline_content`.

FastAPI should preserve expected worker error codes for its caller, map an
unreachable or invalid worker response to `502`, and map a worker timeout to
`504`. Never log the bearer token or full document body.

## FastAPI Session Command API

The public host endpoint is separate from the private worker endpoint. A
recommended host request is:

```http
POST /api/v1/articles/{article_id}/session/commands
Content-Type: application/json
```

```json
{
  "command_id": "a client-generated UUID",
  "base_revision": 12,
  "command": {
    "op": "replace_text_block",
    "block_id": "block_4",
    "text": "Replacement text"
  }
}
```

`command_id` and `base_revision` are mandatory host fields. FastAPI does not
forward them to the worker.

For each session command, FastAPI must:

1. Authenticate and authorize the actor.
2. Return the previous result when `command_id` was already completed.
3. Load the active `article_sessions` row and `session/document.json`.
4. Reject a stale `base_revision` with the host's revision-conflict response.
5. Call the worker with only `{ "document": current_document, "command": command }`.
6. Require HTTP `200`, `ok: true`, and a valid returned `documentJson`.
7. Save the returned document with compare-and-swap revision handling on the
   `article_sessions.revision` value.
8. Record `command_id` in S3, increment the session revision, and return the
   new revision.

The worker returns the whole next document but no affected IDs. If MCP needs
`affected_block_ids`, FastAPI can use the command's `block_id` or compare the
top-level IDs before and after an insertion.

## MCP Mapping

Recommended first tools:

| MCP tool | FastAPI behavior |
|---|---|
| `get_session_outline` | load the session and call worker `/outline` |
| `get_session_blocks` | load and select canonical blocks in FastAPI |
| `apply_session_command` | validate revision/idempotency and call worker `/commands` |
| `list_article_assets` | use the existing host asset inventory; no worker call |

Do not expose the private worker URL or token to MCP. Do not add direct MCP tools
for whole-document replacement, commit, submission, shared undo/redo, or asset
upload until the host explicitly designs those permissions.

## Host Implementation Checklist

- Add a small private worker client module inside the FastAPI backend.
- Add typed request/response validation at the client boundary.
- Normalize and persist legacy session documents before returning an outline.
- Replace old host documentation examples using `upsert_block` with the four
  implemented command operations above.
- Implement the ephemeral `article_sessions` row and S3 command-id handling
  before exposing write tools.
- Run the private-network checks in `test/CLI_manual_tests/smoke_test.md`.
- Keep editor polling/SSE pointed at FastAPI; the browser never calls the worker.
