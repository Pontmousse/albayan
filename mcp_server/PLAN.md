Yes. Here is the implementation plan I would hand to the Al-Bayan development team.

The goal is to make the MCP layer **modular, thin, scalable, and safe for long-term article-writing workflows** without overengineering the current two-tool stage.

# Al-Bayan MCP refactor plan

# Batch 1: Backend Auth Boundary

## 1. Establish the architectural rule first

Keep this as the permanent architecture:

```text
AI client
   │
   ▼
Al-Bayan MCP server
   │
   │ translates MCP tools → ordinary API calls
   ▼
Al-Bayan FastAPI
   │
   ├── authentication
   ├── authorization
   ├── business rules
   ├── ownership checks
   └── workflow restrictions
   │
   ▼
PostgreSQL / S3 / BuTeX document state
```

The MCP server must remain a **thin protocol adapter**.

Do not let `mcp_server/`:

```text
- connect directly to PostgreSQL
- import SQLAlchemy models
- access S3 directly
- duplicate article/review/editor business logic
- decide ownership rules
- perform human-only workflow transitions
```

FastAPI remains the source of truth.

---

# 2. Simplify the agent authorization model

For now, stop building the MCP architecture around many fine-grained scopes such as:

```text
profile:read
articles:read
paragraph:write
equation:write
figure:write
...
```

Instead use this simpler model:

```text
authenticated agent
        │
        ▼
acts on behalf of one Al-Bayan user
```

The important question becomes:

> Is this API operation safe for an agent?

not:

> Does this token have `equation:write` versus `paragraph:write`?

Keep the existing scopes data model if removing it would create unnecessary migrations or churn. It may become useful later for third-party integrations, read-only agents, organizations, etc.

But **do not expand the scope system right now**.

---

# 3. Define two backend authorization classes

Every operation should conceptually belong to one of two classes.

### Agent-safe

Both a logged-in human and their authenticated agent may perform it.

Examples:

```text
read own profile
read own articles
read article metadata
read working document/session
edit session text
insert paragraph
edit paragraph
insert equation
edit equation
upload figure
insert figure
change caption
request preview compilation
```

### Human-only

Only the human through the normal Al-Bayan application may perform it.

Examples:

```text
save/finalize authoritative draft
submit article
submit review
make editorial decision
accept
reject
publish
assign reviewers
administrative actions
```

This must be enforced **inside FastAPI**.

Not merely by omitting MCP tools.

For example:

```text
MCP has no submit_article tool
```

is good, but insufficient.

Also ensure:

```http
POST /articles/{id}/submit
```

does **not accept agent authentication at all**.

That creates a real security boundary.

---

# 4. Refactor backend authentication into reusable dependencies

Right now `/users/me` contains special logic for deciding between agent authentication and Clerk authentication.

Do not repeat that block manually in every future endpoint.

Create a reusable backend dependency/helper with semantics approximately like:

```text
current_actor()
```

or:

```text
current_human_or_agent_user()
```

It should:

```text
1. inspect the credential
2. if it is an Al-Bayan agent token:
      authenticate agent
      resolve its user
3. otherwise:
      authenticate normal Clerk user
4. return one consistent application-level identity
```

Potential conceptual result:

```python
Actor(
    user_id=...,
    auth_method="human" | "agent",
)
```

Then agent-safe endpoints can use:

```python
actor: ActorDep
```

rather than duplicating authentication logic.

Human-only endpoints should continue using:

```python
auth: AuthDep
```

or an explicit:

```python
HumanAuthDep
```

This distinction should be extremely obvious in code review.

---

# 5. Refactor `GET /api/v1/users/me`

Move its current special MCP handling into the shared actor dependency.

Then the endpoint should become simple again:

```python
@router.get("/me")
def get_me(actor: ActorDep, db: DbDep):
    ...
```

No endpoint-specific Bearer parsing.

---

# 6. Make `GET /api/v1/articles/me` agent-safe

This is the first additional endpoint needed for the new MCP tool.

Currently it is tied to normal Clerk authentication.

Refactor it to use the shared human-or-agent actor.

Conceptually:

```text
GET /api/v1/articles/me

human → allowed
agent → allowed
```

Ownership should still be resolved using the authenticated user's `user_id`.

Do not expose other article mutation endpoints to agent auth yet.

---

# 7. Keep human-only article endpoints unchanged

Do not casually migrate every article endpoint to the new actor dependency.

For example, leave operations such as:

```text
submit
final save
delete authoritative content if sensitive
workflow transitions
```

under human authentication unless the team explicitly classifies them as agent-safe.

The migration rule is:

> Only change an existing endpoint when an MCP capability genuinely needs it.

Do not globally make the whole API agent-accessible.

---

# 25. Add backend authentication tests

Test the new actor dependency independently.

At minimum:

```text
valid Clerk user → human actor

valid alb_ agent token → agent actor

invalid alb_ token → rejected

agent resolves correct user

human-only dependency rejects agent
```

---

# 26. Add endpoint tests for `/articles/me`

Verify:

```text
human Clerk authentication → succeeds

agent authentication → succeeds

agent sees only its user's articles

invalid agent → rejected
```

If scopes remain in the existing schema but are not actively used, tests should reflect the new intended policy.

---

# 27. Add explicit human-only security tests

This is extremely important.

Pick representative protected actions, for example:

```text
submit article
submit review
editorial decision
```

and test:

```text
human → potentially allowed subject to normal rules

agent token → rejected
```

This prevents future developers or agents from accidentally widening agent permissions.

---

# Batch 2: MCP Foundation Refactor

# 8. Remove the MCP server's custom Bearer `ContextVar`

Currently the MCP package has its own:

```python
_current_bearer
set_current_bearer()
get_bearer_token()
```

Remove this request-local authentication mechanism.

The MCP SDK already maintains authenticated request context and exposes the current `AccessToken`.

Use the SDK's request-local token for Streamable HTTP.

Conceptually:

```python
access_token = get_access_token()
```

For local `stdio`, fall back to:

```text
ALBAYAN_AGENT_TOKEN
```

The MCP package should have one function approximately like:

```python
def get_backend_bearer_token() -> str:
    token = MCP request token if available
    otherwise ALBAYAN_AGENT_TOKEN

    if neither exists:
        raise authentication error

    return token
```

This removes duplicate request-context infrastructure.

---

# 9. Simplify `token_verifier.py`

Keep it minimal.

Its responsibility should be limited to the MCP transport authentication boundary.

It should not also secretly pass state into `api_client.py`.

Remove:

```text
token_verifier
   ↓
set_current_bearer()
   ↓
ContextVar
   ↓
api_client
```

The API client should independently retrieve the current authenticated MCP token from the SDK context.

---

# 10. Centralize ALL MCP → FastAPI HTTP behavior

Refactor `api_client.py` around one internal primitive:

```python
async def api_request(
    method,
    path,
    *,
    json=None,
    params=None,
    headers=None,
):
```

This function owns:

```text
ALBAYAN_API_URL
Bearer forwarding
timeouts
HTTP status handling
JSON decoding
204 handling
common API errors
```

Every MCP tool should use this layer.

No MCP tool should manually instantiate `httpx`.

---

# 11. Add typed convenience wrappers

On top of `api_request`, provide functions such as:

```python
api_get_object(...)
api_get_list(...)

api_post_object(...)
api_post_list(...)

api_patch_object(...)
api_put_object(...)

api_delete(...)
```

They should validate expected response shapes.

Example:

```python
api_get_object()
```

expects:

```json
{
  "id": "...",
  "name": "..."
}
```

while:

```python
api_get_list()
```

expects:

```json
[
  {...},
  {...}
]
```

This solves the current limitation where `api_get()` only accepts dictionaries.

---

# 12. Prepare non-JSON helpers separately

Do not force every future API operation into JSON.

Eventually BuTeX/article functionality will need:

```text
images
PDFs
binary assets
multipart uploads
possibly streamed data
```

So leave room for functions such as:

```python
api_get_bytes(...)
api_upload_file(...)
api_get_text(...)
```

But implement them only when needed.

Do not overbuild them now.

---

# 13. Keep `api_client.py` domain-agnostic

Do not put functions like:

```python
get_articles()
get_profile()
insert_equation()
```

inside `api_client.py`.

Its job is only:

```text
HTTP communication with FastAPI
```

Domain logic belongs in MCP tool modules.

---

# 14. Create a dedicated `tools/` package now

Change the package structure toward:

```text
mcp_server/
└── src/
    └── albayan_mcp/
        ├── __init__.py
        ├── __main__.py
        ├── server.py
        ├── settings.py
        ├── api_client.py
        ├── token_verifier.py
        │
        └── tools/
            ├── __init__.py
            ├── profile.py
            └── articles.py
```

This is important for long-term maintainability.

---

# 15. Make `server.py` composition-only

`server.py` should stop becoming the place where every tool implementation lives.

Its responsibility should be roughly:

```python
def create_server():
    server = MCPServer(...)

    register_profile_tools(server)
    register_article_tools(server)

    return server
```

That is all.

Add an architectural comment explaining:

> Tool implementations belong under `tools/`. Keep `server.py` limited to server configuration and registration.

---

# 16. Move `get_my_profile` to `tools/profile.py`

Create:

```python
def register_profile_tools(server):
    ...
```

Inside it register:

```text
get_my_profile
```

The tool should call:

```python
api_get_object("/api/v1/users/me")
```

---

# 17. Return structured MCP output

Stop doing:

```python
json.dumps(...)
```

Use Pydantic models or structured Python return types.

For example:

```python
class ProfileResult(BaseModel):
    id: str
    email: str
    full_name: str | None
    affiliation: str | None
```

Then:

```python
async def get_my_profile() -> ProfileResult:
```

This gives MCP clients proper output schemas.

---

# 19. Add MCP result models

For now they can live near their tool modules.

Example:

```text
tools/profile.py
    ProfileResult

tools/articles.py
    ArticleSummaryResult
```

If they become numerous later, introduce:

```text
schemas/
```

or:

```text
models/
```

Do not create another abstraction layer prematurely.

---

# 20. Do not create the entire future folder hierarchy yet

Eventually I expect:

```text
tools/
├── author/
├── reviewer/
├── editor/
└── writing/
```

But do not create empty packages simply because they might exist one day.

Start with:

```text
tools/profile.py
tools/articles.py
```

Then split when a domain becomes substantial.

---

# Batch 3: First New MCP Capability

# 18. Add `read_articles`

Create in:

```text
tools/articles.py
```

a tool such as:

```text
read_articles
```

or:

```text
get_my_articles
```

The development team can choose the final naming convention.

It should call:

```http
GET /api/v1/articles/me
```

through:

```python
api_get_list(...)
```

Return structured article summaries.

Use the backend's current article summary shape:

```text
id
title
status
version_number
updated_at
submitted_at
```

---

# 24. Add MCP-specific tests now

Create:

```text
mcp_server/tests/
```

Use the MCP SDK's in-memory client.

Do not launch real HTTP ports for ordinary tool tests.

Test at minimum:

```text
server exposes get_my_profile

server exposes read_articles

get_my_profile returns structured output

read_articles returns structured output

read_articles handles zero articles

API object helper accepts object

API object helper rejects list

API list helper accepts list

API list helper rejects object

stdio uses ALBAYAN_AGENT_TOKEN

HTTP path uses MCP request token

missing credentials produces a clean error
```

---

# Batch 4: Documentation And Future Guardrails

# 21. Plan the future writing hierarchy

When BuTeX integration becomes significant, evolve toward something like:

```text
tools/
└── writing/
    ├── document.py
    ├── paragraphs.py
    ├── sections.py
    ├── equations.py
    ├── figures.py
    ├── citations.py
    └── assets.py
```

Potential MCP tools later:

```text
read_document
insert_paragraph
edit_paragraph
delete_paragraph

insert_section
rename_section

insert_equation
edit_equation

upload_figure
insert_figure
edit_figure_caption

insert_citation
edit_reference
```

The exact BuTeX-level API should be designed only after carefully studying its document model.

---

# 22. Do not let MCP manipulate BuTeX storage directly

When writing tools arrive, avoid:

```text
MCP
 ↓
S3 document.json
```

Instead:

```text
MCP tool
   ↓
FastAPI writing/session endpoint
   ↓
document/session service
   ↓
BuTeX document state
```

The backend remains responsible for document validity and ownership.

---

# 23. Introduce a working-session layer before serious AI writing

The long-term writing architecture should distinguish:

```text
authoritative saved article
```

from:

```text
AI/human working session
```

The agent should modify the **working session**.

The human reviews it.

Then the human explicitly performs the authoritative save through the website.

Conceptually:

```text
AI + human
    ↓
session/document.json
    ↓
human reviews
    ↓
Save
    ↓
authoritative document.json
```

This is particularly important given your rule that final saving/submission stays human-only.

---

# 28. Document the agent-safe boundary centrally

Add a section to:

```text
mcp_server/Documentation.md
```

called something like:

```text
Agent Capability Boundary
```

State clearly:

> Agents may assist with reading and reversible working-document operations. Authoritative workflow transitions remain human-only.

Document examples.

This should be treated as an architectural invariant.

---

# 29. Add code comments for future agents

In critical areas, add concise architectural comments.

Especially around:

```text
server.py
backend actor authentication
human-only endpoints
api_client.py
future writing/session boundary
```

For example:

```python
# MCP tools must call FastAPI rather than database/storage directly.
# FastAPI remains the source of truth for ownership and workflow rules.
```

And:

```python
# This endpoint accepts human and agent actors because it is read-only.
# Do not use ActorDep on submission/publication endpoints.
```

These comments matter because future coding agents may otherwise "simplify" the architecture in dangerous ways.

---

# 30. Update outdated MCP documentation

The current MCP documentation contains older planning text that can contradict the current implementation state.

Separate the document into something like:

```text
1. Current architecture
2. Current implemented capabilities
3. Security invariants
4. Planned architecture
5. Historical design notes
```

Clearly mark historical text.

Future agents should never have to guess whether something is implemented.

---

# 31. Do not add more MCP tools in this refactor

For this implementation cycle, stop at:

```text
get_my_profile
read_articles
```

The purpose of this change is to make the foundation correct.

After this refactor, adding tool #3 should feel trivial.

That will be the proof that the architecture worked.

---

# Target result

After this work, the MCP package should roughly look like:

```text
mcp_server/
├── pyproject.toml
├── .env.example
├── Documentation.md
├── tests/
│   ├── test_api_client.py
│   ├── test_profile_tools.py
│   └── test_article_tools.py
│
└── src/albayan_mcp/
    ├── __init__.py
    ├── __main__.py
    ├── server.py
    ├── settings.py
    ├── api_client.py
    ├── token_verifier.py
    │
    └── tools/
        ├── __init__.py
        ├── profile.py
        └── articles.py
```

And backend authentication should conceptually become:

```text
                 FastAPIgood, please now
                    │
        ┌───────────┴───────────┐
        │                       │
   ActorDep                HumanAuthDep
        │                       │
 human OR agent              human only
        │                       │
        ▼                       ▼
 read/work/session        submit/publish/
 operations               decisions/etc.
```

The core rule for the whole implementation should be:

> **MCP is an AI-facing interface to Al-Bayan, not a second application backend. Agents may work on behalf of users only through explicitly agent-safe FastAPI operations. Human-authoritative actions remain inaccessible to agent credentials.**

That is the architecture I would build everything else on.
