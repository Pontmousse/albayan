# Round 2 — Al-Bayan persistence and consumer audit (2026-10-25)

Base: `develop`. Companion BuTeX extraction: `migration/document-round2-shared-math-20261025`. This round does **not** rename `Document2`, change worker routes, deploy, or migrate saved data.

## Source consumer inventory

| Boundary | Current references to preserve | Later scheduled round |
| --- | --- | --- |
| Frontend editor/preview | `@drghaliasri/butex/react-document2`, `react-document2-preview`, `document2`, and UI CSS selectors | Round 5 |
| Frontend persistence | `Document2Json` in editor, autosave, history, and read-only revisions; BuTeX npm manifest + lock remain pinned | Round 5 |
| Backend | `backend/app/services/butex_worker_client.py` uses `/v1/document2/*` and the existing authenticated, stateless worker | Round 4 |
| Normal MCP and API | `backend/app/schemas/document2.py`, `mcp_server/src/albayan_mcp/schemas/document2.py`, typed command operations, document validation | Round 6 |
| Equations | Burhan projection, `MathObject` conversion, worker math diagnostics, MathJax; mathematical semantics unchanged | Preserve all rounds |
| Infrastructure | Railway **development** worker/Backend/Dev MCP; no source or environment changes in Round 2 | Integration gates only |

## Persisted data is not a source-code naming convention

- `article_draft_service.revision_storage_key` writes to `articles/{article_id}/draft/revisions/{revision_id}/document.json`; formal published versions have their own immutable `document.json` snapshots.
- PostgreSQL stores revision metadata/hashes and current revision pointers. The S3 JSON body is an immutable structured `DocumentObject`, not a mutable BuTeX worker session.
- Preserve `node_type: "DocumentObject"`, nested `MathObject`/raw math, `meta`, `references`, `blocks`, `math_objects`, optional `source_side`/`source_owner`, field/token IDs, assets, provenance and captions exactly. The generation suffix exists in TypeScript, Python, HTTP paths and commands; it does not warrant rewriting historical records.
- The added `backend/tests/test_draft_revisions.py::test_round2_preserves_structured_math_wire_json_in_immutable_revision` exercises the existing write/read path with nested mathematical provenance, immutable key, and canonical document hash; it does not alter the application implementation.

## Baseline and review gates

Developer MCP on 2026-10-25 reported successful `document-math-roundtrip` (2/2) and `document-normalization` (2/2), plus an old worker contract for `/v1/document2/*` and package 7.4.3. Railway reports its development worker online; its build commit is not independently attested by the worker. The wider equation `document2-roundtrip` suite revealed pre-existing unsupported `\\text` and `cases` cases, unrelated to this extraction.

Candidate CI must pass the new persistence test and existing revision/worker/MCP tests. A live after-extraction comparison requires a separately authorized development deployment; these diagnostics currently evidence **baseline**, not newly built branch behavior. Frozen 145-case acceptance is deferred to Round 7. Do not merge or publish before explicit owner approval.
