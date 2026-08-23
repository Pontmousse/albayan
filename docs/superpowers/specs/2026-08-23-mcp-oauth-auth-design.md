# تصميم: MCP Server — مصادقة موحّدة (API Key + Clerk OAuth) و Streamable HTTP

**التاريخ:** 2026-08-23  
**النطاق:** طبقة مصادقة موحّدة في FastAPI، خادم MCP (`mcp_server/`) بـ stdio + **Streamable HTTP**، أداة تجريبية `get_my_profile`.  
**مرجع:** `mcp_server/Documentation.md` — الجلسة المشتركة والأدوات المستقبلية خارج هذا النطاق.

---

## 1. المشكلة والهدف

المستخدمون يريدون ربط وكلاء ذكية (Cursor، Claude، ChatGPT) بمنصة البيان. اليوم:

- مفاتيح الوكيل `alb_...` موجودة (فرع `cursor/agents-mcp-ui-f6d8`) لكن **لا middleware** يقبلها على الـ API.
- لا يوجد `mcp_server/`.
- OAuth عبر Clerk مطلوب كطريقة ثانية للمستخدمين النهائيين — بدون نسخ مفاتيح يدوياً.

**الهدف:**

1. **لا نلغي API Keys** — تبقى للمطورين والسكربتات.
2. **نضيف Clerk OAuth** (Public Client + PKCE) لعملاء AI البعيدة.
3. **نوحّد المصادقة** إلى `AuthPrincipal` واحد (`user_id` + `scopes`) قبل أي أداة MCP.
4. **ننشر** `mcp_server/` كحاوية منفصلة على Railway (Streamable HTTP) مع stdio محلياً.

**خارج النطاق (مؤجَّل):**

- طبقة الجلسة المشتركة (`session/document.json`)
- أدوات كتابة (`update_session_from_text`)
- Dynamic Client Registration (DCR) — تسجيل يدوي في Clerk بالمرحلة الأولى
- OAuth 2.1 consent screen مخصص داخل المنصة
- `mcp_audit_log` (جدول مقترح لاحقاً)

---

## 2. القرارات المعتمدة (من النقاش)

| # | القرار |
|---|--------|
| 1 | **عملاء:** stdio (Cursor + `alb_`) **و** Streamable HTTP (Claude/ChatGPT + OAuth) — معاً من البداية |
| 2 | **نشر:** كود في `mcp_server/`، **حاوية منفصلة** على Railway (`mcp.albayan-journal.org`) |
| 3 | **نقل HTTP:** **Streamable HTTP** فقط — لا HTTP+SSE القديم (2024-11-05) |
| 4 | **نطاقات OAuth:** ثابتة — `profile:read` + `articles:read` فقط (قراءة) |
| 5 | **نطاقات API Key:** مرنة من جدول `agent_tokens` (كما اليوم) |
| 6 | **معمارية:** `mcp_server/` **thin adapter** فوق FastAPI فقط — يمرّر `Bearer` إلى `/api/v1/...`؛ **لا DB ولا business logic** داخل MCP |
| 7 | **مصادقة/تفويض:** FastAPI فقط (`resolve_principal` + scopes) |
| 8 | **أداة تجريبية:** `get_my_profile` فقط في المرحلة الأولى |

---

## 3. البنية العامة

```text
┌─────────────────┐     stdio (محلي)      ┌──────────────────┐
│  Cursor         │ ──────────────────────►│                  │
└─────────────────┘                       │   mcp_server/    │
                                          │   (Python MCP    │
┌─────────────────┐  Streamable HTTP     │    SDK v2)       │
│ Claude/ChatGPT  │ ─────────────────────►│                  │
└─────────────────┘  + OAuth Bearer       └────────┬─────────┘
                                                   │ Bearer (كما هو)
                                                   ▼
                                          ┌──────────────────┐
                                          │  FastAPI         │
                                          │  resolve_principal│
                                          │  ├─ alb_ → DB    │
                                          │  └─ JWT → Clerk  │
                                          └────────┬─────────┘
                                                   ▼
                                          PostgreSQL + Clerk API
```

### النشر

| الخدمة | URL | النقل |
|--------|-----|-------|
| FastAPI | `api.albayan-journal.org` | REST (موجود) |
| MCP | `mcp.albayan-journal.org/mcp` | **Streamable HTTP** |
| تطوير محلي | `localhost` | stdio |

### Streamable HTTP — لماذا وليس «HTTP عام»

- **Streamable HTTP** (مواصفة MCP 2025-03-26+) يستبدل HTTP+SSE القديم (endpoint مزدوج).
- نقطة نهاية واحدة `/mcp` — `POST` لرسائل JSON-RPC؛ الرد إما `application/json` أو `text/event-stream` للتدفق.
- متوافق مع OAuth (401 + اكتشاف RFC 9728 على نفس المسار).
- Python SDK v2: `streamable_http_app()` / `mcp run --transport streamable-http`.

**تحديات وحلولها:**

| التحدي | الحل |
|--------|------|
| بروكسي Railway يخزّن SSE | تعطيل buffering لمسار `/mcp` |
| إصدارات مواصفة MCP | تثبيت `mcp>=2,<3`؛ SDK v2 يدعم 2025 و2026 |
| JWT OAuth ≠ JWT متصفح | OAuth app منفصل في Clerk؛ `authorized_parties` منفصلة |
| عملاء قدامى (HTTP+SSE) | لا ندعمهم — نستهدف Claude/ChatGPT الحديثة |

### قواعد `mcp_server/` (إلزامية)

| مسموح | ممنوع |
|-------|--------|
| بروتوكول MCP (stdio / Streamable HTTP) | اتصال PostgreSQL أو SQLAlchemy |
| OAuth metadata (RFC 9728) — HTTP فقط | تكرار `resolve_principal` أو التحقق من `alb_` |
| `httpx` → `GET/POST /api/v1/...` | استيراد `app.models` أو `app.services` |
| تمرير `Authorization: Bearer` كما ورد من العميل | قرارات تفويض (scopes) — تلك في FastAPI |

---

## 4. `AuthPrincipal` — الطبقة الموحّدة

```python
@dataclass(frozen=True)
class AuthPrincipal:
    user_id: uuid.UUID
    clerk_id: str
    scopes: frozenset[str]
    auth_method: Literal["api_key", "oauth", "session"]
    token_id: uuid.UUID | None = None  # عند api_key فقط
```

**مبدأ:** أدوات MCP ومسارات API تستهلك `user_id` + `scopes` — لا `auth_method`.

### مسارات المصادقة

| المصدر | الكشف | التحقق | النطاقات |
|--------|-------|--------|----------|
| API Key | `Bearer alb_...` | SHA-256 → `agent_tokens` (غير ملغى، غير منتهٍ) | من عمود `scopes` |
| OAuth | `Bearer <jwt>` (لا `alb_`) | Clerk JWT + audience OAuth app | ثابتة: `profile:read`, `articles:read` |
| جلسة متصفح | Clerk JWT (المسار الحالي) | `get_auth_context` دون تغيير سلوك | كامل (لا يتغير) |

### `resolve_principal` — موقع الملف

`backend/app/core/agent_auth.py`

```python
def resolve_principal(
    authorization: str | None,
    db: Session,
    *,
    allow_session: bool = True,
) -> AuthPrincipal:
    ...
```

- يُستدعى من dependency جديد `AgentAuthDep` لمسارات تدعم الوكلاء.
- مسارات الواجهة الحالية تبقى على `AuthDep` (Clerk session) دون كسر.
- `GET /api/v1/users/me` يقبل **أيّاً من:** `AuthDep` (متصفح) **أو** `AgentAuthDep` (وكيل).

### التحقق من النطاق

```python
def require_scope(principal: AuthPrincipal, scope: str) -> None:
    if scope not in principal.scopes:
        raise HTTPException(status_code=403, detail="صلاحية غير كافية.")
```

---

## 5. Streamable HTTP + OAuth (Clerk)

### اكتشاف OAuth — على `mcp-server` فقط

```
GET /.well-known/oauth-protected-resource
```

```json
{
  "resource": "https://mcp.albayan-journal.org/mcp",
  "authorization_servers": ["https://<clerk-issuer>"],
  "scopes_supported": ["profile:read", "articles:read"],
  "bearer_methods_supported": ["header"]
}
```

طلب `POST /mcp` **بدون** `Authorization`:

```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer resource_metadata="https://mcp.albayan-journal.org/.well-known/oauth-protected-resource"
```

### تدفق OAuth

1. العميل (Claude) يتلقى 401 → يجلب Protected Resource Metadata.
2. يكتشف Clerk كـ Authorization Server (RFC 8414).
3. PKCE flow → `access_token` (Clerk JWT).
4. `POST /mcp` + `Authorization: Bearer <jwt>`.
5. `mcp-server` يمرّر نفس التوكن إلى FastAPI.

### إعداد Clerk (يدوي — المرحلة ١)

1. إنشاء **OAuth Application** (Public Client) في Clerk Dashboard.
2. تسجيل Redirect URIs حسب العملاء المستهدفة (Claude Desktop `localhost`، إلخ).
3. متغيرات بيئة:

| المتغير | الغرض |
|---------|--------|
| `CLERK_SECRET_KEY` | تحقق JWT (موجود) |
| `CLERK_OAUTH_CLIENT_ID` | OAuth app للـ MCP |
| `CLERK_ISSUER_URL` | issuer لـ metadata |
| `MCP_RESOURCE_URL` | `https://mcp.albayan-journal.org/mcp` |
| `MCP_OAUTH_SCOPES` | `profile:read,articles:read` (ثابت) |

**لا DCR** في المرحلة الأولى — العميل يُسجَّل يدوياً في Clerk.

### stdio — بدون OAuth

```json
{
  "mcpServers": {
    "albayan": {
      "command": "python",
      "args": ["-m", "albayan_mcp"],
      "env": {
        "ALBAYAN_API_URL": "https://api.albayan-journal.org",
        "ALBAYAN_AGENT_TOKEN": "alb_..."
      }
    }
  }
}
```

---

## 6. هيكل `mcp_server/`

```text
mcp_server/
├── pyproject.toml              # mcp>=2,<3 · httpx · uvicorn
├── Dockerfile
└── src/albayan_mcp/
    ├── __init__.py
    ├── __main__.py             # --transport stdio|streamable-http
    ├── server.py               # FastMCP + تسجيل الأدوات
    ├── tools/
    │   └── profile.py          # get_my_profile
    ├── api_client.py           # httpx → FastAPI مع Bearer
    └── oauth_metadata.py       # RFC 9728 endpoints (HTTP فقط)
```

### تشغيل

| الوضع | الأمر | الاستعمال |
|-------|-------|-----------|
| stdio | `python -m albayan_mcp` | Cursor محلي |
| Streamable HTTP | `python -m albayan_mcp --transport streamable-http` | Railway |

أو: `uvicorn albayan_mcp.http_app:app` حيث `http_app` يجمع Streamable HTTP + metadata routes.

### أداة `get_my_profile`

| الحقل | القيمة |
|-------|--------|
| الاسم | `get_my_profile` |
| النطاق المطلوب | `profile:read` |
| يستدعي | `GET {ALBAYAN_API_URL}/api/v1/users/me` |
| يمرّر | `Authorization: Bearer <نفس توكن العميل>` |

**الإرجاع:** JSON مبسّط (الاسم، البريد، الجهة، `user_id`) — بدون بيانات حساسة إضافية.

### `api_client.py`

```python
async def api_get(path: str, token: str) -> dict:
    async with httpx.AsyncClient(base_url=settings.api_url) as client:
        r = await client.get(path, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json()
```

التوكن يأتي من سياق الطلب الحالي (stdio: من `ALBAYAN_AGENT_TOKEN`؛ HTTP: من header العميل).

---

## 7. تغييرات FastAPI (الخطوة ٥)

### ملفات جديدة/معدّلة

| الملف | التغيير |
|-------|---------|
| `backend/app/core/agent_auth.py` | `AuthPrincipal`, `resolve_principal`, `require_scope` |
| `backend/app/core/deps.py` | `agent_auth_principal()` dependency |
| `backend/app/routers/users.py` | `GET /users/me` يقبل `AgentAuthDep` + `profile:read` |
| `backend/app/main.py` | لا تغيير CORS جوهري |

### دمج فرع الوكلاء

يجب دمج/إعادة استخدام من `cursor/agents-mcp-ui-f6d8`:

- `agent_tokens` model + migration `007`
- `agent_token_service.py`
- routers/schemas للمفاتيح

### تحديث `last_used_at`

عند نجاح `resolve_principal` لـ `api_key` → تحديث `agent_tokens.last_used_at`.

### الأمان

- مفتاح ملغى / منتهٍ → 401
- نطاق ناقص → 403
- `DEV_MODE` يبقى يحكم **إدارة المفاتيح** فقط — قبول المفاتيح على API يعمل عند تفعيل MCP (ليس مقيداً بـ dev mode للمصادقة نفسها؛ قرار: **مصادقة الوكيل متاحة عند `DEV_MODE=true` في المرحلة الأولى** لتجنب تعريض إنتاج مبكراً).

---

## 8. معالجة الأخطاء

| الحالة | MCP (HTTP) | FastAPI | الأداة |
|--------|------------|---------|--------|
| بدون توكن | 401 + WWW-Authenticate | 401 | رسالة «يلزم مصادقة» |
| توكن غير صالح | 401 | 401 | نفس المعنى |
| نطاق ناقص | — | 403 | «صلاحية غير كافية» |
| API غير متاح | 502 | 503 | «الخدمة غير متاحة» |

---

## 9. الاختبار

### Backend

```bash
# بمفتاح alb_ (بعد إنشائه من /al-idayat/wukala)
curl -H "Authorization: Bearer alb_..." http://localhost:8000/api/v1/users/me
```

اختبارات pytest:

- `resolve_principal` مع مفتاح صالح / ملغى / نطاق خاطئ
- `GET /users/me` بـ `alb_` + `profile:read` → 200
- `GET /users/me` بـ `alb_` بدون `profile:read` → 403

### MCP stdio

1. `ALBAYAN_AGENT_TOKEN=alb_... python -m albayan_mcp`
2. في Cursor: «ما هو ملفي الشخصي في البيان؟»
3. يجب أن تُستدعى `get_my_profile` وتُرجع البيانات.

### MCP Streamable HTTP (محلي)

```bash
ALBAYAN_API_URL=http://localhost:8000 python -m albayan_mcp --transport streamable-http --port 8080
curl -X POST http://localhost:8080/mcp -H "Authorization: Bearer alb_..." ...
```

### OAuth (يدوي)

1. ربط Claude بـ `https://mcp.albayan-journal.org/mcp`
2. إكمال تسجيل الدخول Clerk
3. «أعطني ملفي الشخصي»

---

## 10. خارطة التنفيذ

| المرحلة | المحتوى | الأولوية |
|---------|---------|----------|
| **0** | دمج `agent_tokens` من فرع الوكلاء | P0 |
| **1** | `agent_auth.py` + `GET /users/me` للوكلاء | P0 — **الخطوة ٥** |
| **2** | `mcp_server/` stdio + `get_my_profile` | P0 — **الخطوة ٦** |
| **3** | Streamable HTTP + OAuth metadata | P1 |
| **4** | نشر Railway + إعداد Clerk OAuth app | P1 |
| **5** | `list_my_articles` (نطاق `articles:read`) | P2 |

---

## 11. متغيرات البيئة — ملخص

### FastAPI

```
DEV_MODE=true
CLERK_SECRET_KEY=sk_...
```

### mcp-server (stdio)

```
ALBAYAN_API_URL=http://localhost:8000
ALBAYAN_AGENT_TOKEN=alb_...
```

### mcp-server (Streamable HTTP / Railway)

```
ALBAYAN_API_URL=https://api.albayan-journal.org
CLERK_SECRET_KEY=sk_...
CLERK_ISSUER_URL=https://...
MCP_RESOURCE_URL=https://mcp.albayan-journal.org/mcp
PORT=8080
```

---

## 12. الخلاصة

| جاهز | مطلوب في هذا التصميم |
|------|----------------------|
| Clerk JWT للمتصفح | `resolve_principal` موحّد |
| `agent_tokens` (فرع dev) | middleware + دمج الفرع |
| توثيق MCP | `mcp_server/` + Streamable HTTP |
| | OAuth metadata (RFC 9728) |
| | `get_my_profile` |

**الجملة المرجعية:** لا نستبدل مصادقة API Key؛ نضيف Clerk OAuth كطريقة ثانية أمام نفس طبقة التفويض، ونوحّد الطريقتين إلى `user_id` واحد قبل تنفيذ أي أداة — عبر **Streamable HTTP** للعملاء البعيدة و **stdio** للمطورين.
