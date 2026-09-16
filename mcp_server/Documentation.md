# توثيق MCP — مجلة البيان

> **الغرض:** مرجع موحّد لخادم MCP (Model Context Protocol) والتفاعل مع المنصة عبر الوكلاء الذكية.  
> **آخر تحديث:** ١٣ سبتمبر ٢٠٢٦
> **الموقع:** `mcp_server/` في جذر المستودع  
> **مرجع سابق:** نُقل من `docs/afkar-al-mashrou.md` — القسم ٥.

---

## البنية الحالية (Current Architecture)

`mcp_server/` **محوّل رفيع (thin adapter)** فوق FastAPI فقط. حد التكامل
العام للمستخدمين والعملاء المتوافقين هو:

```text
https://mcp.albayan-journal.org/mcp
```

- كل أدوات MCP تستدعي `GET/POST /api/v1/...` عبر `api_client.py` مع تمرير credential المستخدم كما هو (`alb_...` أو Clerk OAuth JWT).
- **FastAPI** هو المسؤول النهائي عن: المصادقة، التفويض، منطق الأعمال، الملكية، حدود workflow، والوصول إلى قاعدة البيانات.
- **ممنوع** داخل `mcp_server/`: اتصال DB مباشر، استيراد نماذج SQLAlchemy، الوصول المباشر إلى S3، أو تكرار business logic.

```text
عميل MCP بعيد ── Streamable HTTP ──→ mcp.albayan-journal.org/mcp
                  OAuth أو alb_...              │ Bearer المستخدم
                                                ▼
                                      FastAPI الداخلي
```

العميل البعيد لا يحتاج إلى معرفة عنوان FastAPI في الحالتين: التفويض التفاعلي
عبر OAuth، أو الأتمتة المتقدمة بمفتاح شخصي `alb_...`. في الحالة الثانية يرسل
العميل المفتاح إلى عنوان MCP العام كترويسة Bearer، ويمرّره الخادم المستضاف إلى
FastAPI. التشغيل المحلي عبر stdio باقٍ فقط للمساهمين الذين يطوّرون أو يختبرون
تنفيذ `mcp_server` نفسه.

### تشغيل الخدمة المستضافة

| الإعداد | القيمة |
|---------|--------|
| Root Directory | `mcp_server` |
| Start Command | `python -m albayan_mcp --transport streamable-http --host 0.0.0.0` |
| `MCP_RESOURCE_URL` | `https://mcp.albayan-journal.org/mcp` |
| `ALBAYAN_API_URL` | `https://api.albayan-journal.org` |

لتطوير خادم MCP نفسه محليًا، انسخ `mcp_server/.env.example` إلى
`mcp_server/.env` وعدّل `ALBAYAN_API_URL` و`ALBAYAN_AGENT_TOKEN`. هذه إعدادات
داخلية للمحوّل المحلي وليست إعدادات عميل أو جزءًا من دليل `/wukala`.

---

## القدرات المنفذة حالياً (Current Implemented Capabilities)

> **التفعيل:** `NEXT_PUBLIC_MCP_ENABLED=true` (واجهة) + `MCP_ENABLED=true`
> (خلفية) + `alembic upgrade head`. يضيف `NEXT_PUBLIC_DEV_MODE=true` أسطح
> المفاتيح والربط البعيد المتقدم بها، ولا يستبدل تجربة OAuth المعتادة.

### الواجهة (Next.js)

| المكوّن / المسار | الوظيفة |
|------------------|---------|
| `AgentsNavLink` في `MainNav` | زر **«وكلاء»** في الهيدر عند تفعيل MCP |
| `McpGate` | يحمي `/wukala` وميزة MCP العامة |
| `/wukala` | أدلة الربط البعيد عبر OAuth، ومثال Cursor المتقدم بالمفتاح الشخصي |
| `DevModeGate` | يخفي أسطح المفاتيح والربط المتقدم خارج وضع التطوير |
| `/al-idayat/wukala` | إدارة مفاتيح الوكيل في وضع التطوير فقط |
| `DevModeAgentsCard` في `/al-idayat` | مدخل ثانوي لأدوات المفاتيح المتقدمة |
| `AgentTokensPanel` | إنشاء، نسخ (مرة واحدة)، تعديل التسمية، حذف |
| `frontend/src/lib/api/agent-tokens.ts` | عميل API للمفاتيح |
| `frontend/src/lib/agent-token-config.ts` | نطاقات الصلاحيات (scopes) والحد الأقصى (٥ مفاتيح) |

### الخلفية (FastAPI)

| المكوّن | الوظيفة |
|---------|---------|
| `GET/POST/PATCH/DELETE /api/v1/users/me/agent-tokens` | CRUD مفاتيح الوكيل |
| `agent_token_service.py` | إنشاء مفتاح `alb_...`، تخزين SHA-256 فقط، إلغاء، تحديث |
| `ActorDep` في `backend/app/core/actor.py` | هوية موحدة لمسارات human-or-agent الآمنة |
| `GET /api/v1/users/me` | Agent-safe: قراءة الملف الشخصي |
| `GET /api/v1/articles/me` | Agent-safe: قراءة مقالات المستخدم |
| `POST /api/v1/articles` | إنشاء مسودة وربط المستخدم المصادق مؤلفاً مراسلاً |
| `GET /api/v1/articles/{id}` | تفاصيل مقال يملكه المستخدم مع بيانات الإصدار |
| `PATCH /api/v1/articles/{id}` | تحديث title/abstract في الصف والجلسة النشطة معاً |
| `GET /api/v1/articles/{id}/draft/outline` | ملخص دلالي للمسودة مع المعرّفات الثابتة ورقم المراجعة |
| `GET /api/v1/articles/{id}/draft/blocks` | كتل Document2 القانونية للتحرير الدقيق |
| `POST /api/v1/articles/{id}/draft/commands` | تطبيق أمر Document2 واحد مع base_revision وcommand_id |
| `AuthDep` | يبقى مسار المصادقة البشري فقط لمسارات submit/review/editor/admin |

### خادم MCP

| المكوّن | الحالة |
|---------|--------|
| stdio transport | منجز |
| Streamable HTTP transport | منجز |
| `api_client.py` | تمرير Bearer إلى FastAPI، معالجة HTTP مركزية، helpers للـ object/list |
| `tools/profile.py` | أداة `get_my_profile` |
| `tools/articles.py` | القراءة وإنشاء المسودة وتفاصيلها وتحديث title/abstract |
| `tools/drafts.py` | أدوات فحص وتحرير وتجميع مراجعات المسودة غير القابلة للتعديل واسترجاع PDF |
| `schemas/document2.py` | مرآة مستقلة صارمة لاتحاد أوامر Document2 ذي ٢٩ عملية |
| `server.py` | تركيب الخادم وتسجيل الأدوات فقط |
| `call_logging.py` | وسيط واحد يراقب `tools/call` ويرسل حدثاً منقّحاً إلى FastAPI بأفضل جهد |

### قاعدة البيانات

| الجدول | الحقول الرئيسية |
|--------|-----------------|
| `agent_tokens` (migration `007_agent_tokens`) | `user_id`, `token_hash`, `label`, `scopes` (JSONB), `expires_at`, `last_used_at`, `revoked_at` |
| `mcp_call_logs` (migration `014_mcp_call_logs`) | اسم الأداة والأمر الاختياري والحالة والمدة ولقطات JSON المنقّحة ومعرّف تتبع اختياري؛ احتفاظ 90 يوماً |

### النطاقات (scopes) المعرّفة في الواجهة

> **ملاحظة (2026-08-25):** هذه نطاقات **تطبيق** تُفرض في FastAPI فقط. طبقة MCP OAuth (`server.py`) تطلب نطاقات هوية Clerk القياسية `profile` + `email` — لأن Clerk يُصدر نطاقات هوية (`openid`, `profile`, `email`, `offline_access`) وليس نطاقات تطبيق مخصّصة.

- `profile:read` — قراءة الملف الشخصي
- `articles:read` — قراءة المقالات
- `articles:draft:write` — إنشاء مراجعات المسودة ورفع أصولها وتجميعها
- `reviews:read` — قراءة تعيينات المراجعة
- `reviews:draft:write` — مسودة ملاحظات المراجعة
- `editor:read` — قراءة مقالات التحرير

---

## حد قدرات الوكيل (Agent Capability Boundary)

الوكلاء يستطيعون القراءة والعمل على جلسة المقال القابلة للمراجعة:

- `get_my_profile` → `GET /api/v1/users/me`
- `read_articles` → `GET /api/v1/articles/me`
- `create_article` و`get_article` → إنشاء مسودة مملوكة وقراءة تفاصيلها
- `update_article_metadata` → تحديث title/abstract ومزامنتهما مع الجلسة النشطة
- `get_draft_outline` و`get_draft_blocks` → فحص المسودة ومعرّفاتها الثابتة
- `apply_draft_command` → تعديل موجّه واحد ينشئ مراجعة مسودة غير قابلة للتعديل
- `compile_draft` → بدء تجميع المراجعة الحالية الموثوق، بطلب صريح فقط
- `get_compile_status` و`get_article_pdf` → متابعة التجميع وعرض PDF الحالي

القاعدة الثابتة:

> الوكيل قد يساعد في القراءة وعمليات مسودة/جلسة قابلة للمراجعة لاحقاً. الإجراءات المعتمدة والنهائية تبقى بشرية فقط.

Authoritative actions تبقى human-only داخل FastAPI، وليس فقط لأنها غير موجودة كأدوات MCP:

- تقديم المقال.
- إرسال المراجعة.
- اتخاذ قرار تحريري.
- النشر.
- إجراءات الإدارة.
- استبدال المستند كاملاً، حذف المقال، أو تجاوز حدود الجلسة والمراجعات.

لا يكفي حذف أداة MCP مثل `submit_article`. يجب أن يبقى endpoint نفسه على `AuthDep` أو اعتماد بشري صريح، وألا يستخدم `ActorDep` إلا إذا صُنّف المسار بأنه agent-safe.

---

## الربط البعيد للعملاء

الخادم المستضاف وOAuth هما المسار الافتراضي لكل عميل يدعمهما. لا تُنسخ صيغة
عميل إلى آخر؛ تختلف أسماء الحقول وبنية ملفات الإعداد:

### Cursor

```json
{
  "mcpServers": {
    "albayan": {
      "url": "https://mcp.albayan-journal.org/mcp"
    }
  }
}
```

### Google Antigravity

```json
{
  "mcpServers": {
    "albayan": {
      "serverUrl": "https://mcp.albayan-journal.org/mcp"
    }
  }
}
```

### OpenCode V2

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "albayan": {
        "type": "remote",
        "url": "https://mcp.albayan-journal.org/mcp"
      }
    }
  }
}
```

في Claude وChatGPT يُضاف العنوان من واجهة الموصلات/التطبيقات ثم يُستكمل
التفويض في المتصفح. أما العملاء الآخرون فيُستخدم توثيق العميل نفسه متى دعم
Streamable HTTP وOAuth؛ لا توجد صيغة JSON عامة تصلح للجميع.

نتائج التحقق التقني المنشور وحدوده موثقة في
[`docs/mcp-remote-interoperability-verification.md`](../docs/mcp-remote-interoperability-verification.md).

## ربط ChatGPT — سجل التحقق والدليل الكامل

> ثمرة تشخيص فعلي (٢٥ أغسطس ٢٠٢٦) انتهى بربط ناجح. كل خطوة هنا جُرّبت على الإنتاج.

### الصورة الكبيرة

```text
ChatGPT (عميل OAuth) ──1── يكتشف metadata من mcp_server
        │                   /.well-known/oauth-protected-resource/mcp
        ├─2── يسجّل نفسه تلقائياً لدى Clerk (DCR)
        ├─3── المستخدم يوافق على شاشة تفويض Clerk
        ├─4── يحصل على JWT صالح من Clerk
        ├─5── POST /mcp + Bearer JWT ──→ mcp_server (تحقق شكلي)
        └─6── mcp_server يمرر نفس JWT ──→ FastAPI (تحقق فعلي عبر aud)
```

لا حاجة لإنشاء تطبيق OAuth يدوي في Clerk — **ChatGPT هو العميل** ويسجّل نفسه عبر
Dynamic Client Registration، و**mcp_server هو المورد** (resource server) فقط.

### ١. إعدادات Clerk Dashboard

| الإعداد | القيمة | أين |
|---------|--------|-----|
| Dynamic Client Registration | **مفعّل** | OAuth Applications → إعدادات |
| JWT access tokens | **مفعّل** | OAuth Applications → إعدادات |
| شاشة الموافقة (consent) | مفعّلة (الافتراضي — لا تعطّلها) | لكل تطبيق OAuth |
| تطبيق OAuth يدوي | **غير مطلوب** | — |

بعد أول محاولة ربط ناجحة سترى في OAuth Applications عميلاً باسم «ChatGPT»
سجّله DCR تلقائياً بنطاقات `openid email offline_access profile`.

### ٢. النطاقات — لماذا نطاقات الهوية القياسية؟

طبقة MCP OAuth تستخدم **نطاقات هوية Clerk القياسية** فقط:

```text
openid  profile  email  (+ offline_access يضيفه العميل)
```

- Clerk **لا يُصدر** نطاقات تطبيق مخصّصة (مثل `profile:read`) لعملاء DCR.
- ChatGPT يطلب `openid` **دائماً** عند authorize؛ وClerk يرفض أي نطاق لم
  يُسجَّل به العميل → خطأ `invalid_scope` الشهير:
  «The OAuth 2.0 Client is not allowed to request scope 'openid'».
- لذلك `required_scopes` في `server.py` هي `["openid", "profile", "email"]` —
  وهي ما يظهر في metadata فيسجّل ChatGPT عميله بها.
- **صلاحيات التطبيق** (قراءة المقالات، الملف الشخصي…) تُفرض في FastAPI،
  لا علاقة لها بنطاقات OAuth هذه.

### ٣. متغيرات بيئة الاستضافة

**خدمة mcp_server:**

| المتغير | مثال | ملاحظة |
|---------|-------|--------|
| `MCP_RESOURCE_URL` | `https://mcp.albayan-journal.org/mcp` | **مطابقة حرفية** لعنوان مورد MCP العام |
| `CLERK_ISSUER_URL` | `https://clerk.albayan-journal.org` | يساوي `iss` في JWT |
| `ALBAYAN_API_URL` | `https://api.albayan-journal.org` | عنوان FastAPI الداخلي بالنسبة إلى محوّل MCP |

**خدمة الخلفية (FastAPI):** تحتاج إلى `MCP_ENABLED=true`. لا تستخدم نسخة
FastAPI من `MCP_RESOURCE_URL`؛ التحقق الفعلي لهوية JWT يجري عبر Clerk، بينما
ملكية عنوان مورد OAuth تخص خدمة `mcp_server`.

**خدمة الواجهة (Next.js):** `NEXT_PUBLIC_MCP_ENABLED=true` — **قبل البناء**
(المتغير يُخبز وقت `next build`؛ ضبطه بعد البناء بلا أثر حتى إعادة النشر).

### ٤. خطوات المستخدم في ChatGPT

1. افتح ChatGPT من **المتصفح** (وضع المطوّر لا يُفعَّل من تطبيق الجوال).
2. الإعدادات → **التطبيقات والموصلات** → إعدادات متقدمة → فعّل **وضع المطوّر**.
3. ارجع إلى الموصلات → **إنشاء** (Create).
4. املأ: الاسم «البيان»، وصفاً قصيراً، وعنوان خادم MCP:
   `https://mcp.albayan-journal.org/mcp`
5. (اختياري) افتح إعدادات OAuth المتقدمة وتحقق أن النطاقات المدعومة
   والـ DCR ظاهرة كما في metadata.
6. وافق على الإقرار ثم **إنشاء** → يُفتح تبويب جديد بشاشة تفويض Clerk → **السماح**.
7. عد إلى ChatGPT — الموصل جاهز، وتظهر أدوات الملف والمقالات وجلسة Document2
   التسع في قائمة الأدوات.

### ٥. دليل استكشاف الأخطاء (من التجربة الفعلية)

| العرض | التشخيص | السبب/الحل |
|-------|---------|------------|
| `POST /mcp → 401` ثم `GET /.well-known/... → 200` في سجلات الاستضافة | **طبيعي** | أول طلب بلا توكن؛ هكذا يبدأ اكتشاف OAuth |
| `curl -H "Authorization: Bearer test123"` على `/mcp` يرجع 401 | وسيط الاستضافة يحذف الترويسة أو خطأ بيئة | مع التحقق الشكلي الحالي أي توكن غير فارغ يجب أن يصل إلى طبقة التحقق |
| `oauth_authorization.failed` في سجلات Clerk بسبب `code_challenge_missing` | طلب authorize بلا PKCE | طبيعي في الاختبار اليدوي؛ ChatGPT يرسل PKCE دائماً |
| `invalid_scope … scope 'openid'` في رابط العودة إلى ChatGPT | العميل سُجّل بلا `openid` | أضف `openid` إلى `required_scopes` واحذف الموصل وأعد إنشاءه (DCR جديد) |
| الأدوات ترجع 401 من FastAPI بعد نجاح `/mcp` | التوكن لم يمر بمسار OAuth الخاص بالوكيل | راجع تحقق Clerk في `ActorDep` وسجلات المصدر والمُصدر من دون تسجيل التوكن نفسه |
| `Could not resolve host` عند curl | نطاق DNS أو الشهادة غير جاهزين | أصلح النطاق الرسمي؛ لا تنشر عنوان الاستضافة الداخلي بديلاً للمستخدمين |
| لقراءة سبب فشل authorize | سجلات Clerk → Logs → افتح الحدث | حقل `reason` في payload، أو راقب `?error=` في رابط العودة |

**نصيحة تشخيص ذهبية:** أعد محاولة الربط ثم افتح أحدث حدث
`oauth_authorization.failed` في Clerk واقرأ `reason` — أو انسخ رابط العودة
إلى ChatGPT من شريط العنوان وافحص `?error=&error_description=`.

### ٦. ملاحظة مستقبلية — تخصيص شاشة الموافقة

شاشة التفويض التي يراها المستخدم هي Account Portal الافتراضي من Clerk.
منذ يونيو ٢٠٢٦ يدعم Clerk استضافتها على نطاقنا عبر مكوّن `OAuthConsent`
(مع `appearance` للتخصيص البصري، أو مسار كامل في تطبيقنا يُضبط من
Dashboard → Paths). ليست أولوية الآن؛ الافتراضي موصى به رسمياً.

---

## القدرات المخططة المتبقية (Remaining Planned Capabilities)

أدوات مسودة Document2 والمراجعات غير القابلة للتعديل منفّذة كما يوضح القسم ٢.
يستطيع المؤلف البشري تصفح سجل المسودة واستعادة مراجعة من الواجهة، ولا توجد
أداة استعادة للوكيل. ملف PDF الحالي متاح عبر مورد مضمّن مرتبط بالمراجعة
الحالية. يظل تقديم المقال وإرسال المراجعة والقرار التحريري خارج أدوات MCP.

---

## 2. أدوات مسودة Document2 عبر MCP

أصبح عقد BuTeX 7.0.2 متاحاً للعملاء عبر أداة تحرير MCP واحدة ذات مخطط
مميّز بـ `op`. يبقى MCP محوّلاً رفيعاً؛ كل أداة أدناه تستدعي FastAPI ولا
تتصل بالعامل الخاص أو التخزين أو قاعدة البيانات مباشرة.

### 2.1 أدوات دورة حياة المسودة

| أداة MCP | مسار FastAPI | الغرض |
|----------|---------------|-------|
| `create_article(title, abstract?)` | `POST /api/v1/articles` | إنشاء مقال ومسودة أولى بلا إصدار رسمي، وربط المستخدم المصادق في `ArticleAuthor` بالترتيب الأول وبصفة المؤلف المراسل |
| `get_article(article_id)` | `GET /api/v1/articles/{id}` | قراءة title/abstract وتفاصيل الإصدار الحالي والإصدارات |
| `update_article_metadata(article_id, title?, abstract?)` | `PATCH /api/v1/articles/{id}` | تحديث title و/أو abstract لمسودة مملوكة؛ النص الفارغ يمسح الملخص |

`Article.title` و`Article.abstract` متزامنان مع بيانات `Document2.meta` في
المراجعة الحالية. يمر PATCH من بدائية إنشاء المراجعات نفسها، فيحدّث البيانات
الوصفية والمستند معاً وينشئ مراجعة غير قابلة للتعديل عند تغير المحتوى. لذلك
يجب أن يعيد العميل قراءة أحدث مراجعة قبل أمره الهيكلي التالي عند حدوث تعارض.

لا تقبل حمولات الإنشاء أو التحديث حقول authors. المؤلفون علاقات
`ArticleAuthor` ولا يديرهم الوكيل. كذلك يرفض FastAPI محاولة وكيل تمرير
`update_document_meta.authors` عبر أداة الأوامر، بينما يزامن title/abstract
الواردين عبر ذلك الأمر مع صف Article. لا توجد أدوات MCP للتقديم أو الحذف أو
إضافة المؤلفين أو حذفهم أو إعادة ترتيبهم.

تبقى أدوات المسودة نفسها قابلة للاستخدام عندما تكون حالة المقال
`revision_requested`، بحيث يستطيع الوكيل مساعدة المؤلف داخل جولة التعديل.
لا توجد أدوات لطلب التعديلات أو اختيار كشف هوية مراجع أو إعادة التقديم أو اتخاذ
قرار تحريري؛ هذه الحدود بشرية دائماً.

### 2.2 أدوات تحرير المسودة

| أداة MCP | مسار FastAPI | الغرض |
|----------|---------------|-------|
| `get_draft_outline(article_id)` | `GET /api/v1/articles/{id}/draft/outline` | فحص خفيف للمراجعة الحالية، أنواع الكتل، مقتطفاتها ومعرّفاتها الثابتة |
| `get_draft_blocks(article_id)` | `GET /api/v1/articles/{id}/draft/blocks` | قراءة كتل Document2 القانونية ومعرّفات الحقول والرموز والقوائم والجداول قبل تحرير دقيق |
| `apply_draft_command(article_id, command_id, base_revision, command)` | `POST /api/v1/articles/{id}/draft/commands` | تطبيق أمر Document2 واحد وإنشاء مراجعة غير قابلة للتعديل |
| `compile_draft(article_id)` | `POST /api/v1/articles/{id}/draft/compile` | يطلب من FastAPI تصدير المراجعة الحالية وتجميعها دون مدخلات LaTeX أو أصول أو hash من العميل |
| `get_compile_status(article_id)` | `GET /api/v1/articles/{id}/draft/compile/status` | يعرض هوية المحاولة والمراجعة وحالة النجاح أو الفشل وجاهزية PDF |
| `get_article_pdf(article_id)` | `GET /api/v1/articles/{id}/draft/pdf` | يعيد PDF الحالي كمورد MCP ثنائي مضمّن ويرفض أي معاينة لا تخص المراجعة الحالية |
| `list_article_assets(article_id)` | `GET /api/v1/articles/{id}/assets` | يسرد صور الإصدار الحالي ومعرّفاتها الثابتة |
| `get_article_asset(article_id, asset_id)` | `GET /api/v1/articles/{id}/assets/{filename}` | يعيد الصورة كمحتوى MCP قابل للعرض بعد تفويض FastAPI |
| `upload_article_asset(article_id, file)` | `POST /api/v1/articles/{id}/assets` | ينزّل ملفاً اختاره المستخدم عبر file params ثم يرسله multipart إلى FastAPI |

النتائج مقيّدة أيضاً: أدوات القراءة تعيد `revision_id` و`revision_number`
مع outline أو blocks؛ ونتيجة الأمر تعيد المستند القانوني والمراجعة الجديدة
و`affected_block_ids`. نماذج كتل
الاستجابة تثبّت حقول الهوية والبنية المعروفة وتسمح بحقول BuTeX الإضافية كي لا
تُحذف عند تطور الحزمة.

### 2.3 مخطط أمر التحرير

حقل `command` ليس JSON عشوائياً. مخطط اكتشاف MCP ينشر `oneOf` لكل العمليات
الـ٢٩ ويستخدم `op` كمميّز. تشمل العائلات: الكتل والأشكال، بيانات المقال
والمراجع، الرموز المضمّنة للنص والمعادلات والاستشهادات والإحالات، القوائم،
والجداول وصفوفها وأعمدتها.

مثال إدراج جدول في نهاية المستند:

```json
{
  "article_id": "11111111-1111-1111-1111-111111111111",
  "command_id": "22222222-2222-2222-2222-222222222222",
  "base_revision": 12,
  "command": {
    "op": "insert_table",
    "rows": [["A", "B"]],
    "columns": "ll",
    "anchor": {"end": true}
  }
}
```

مثال إدراج رمز نصي في حقل معروف:

```json
{
  "article_id": "11111111-1111-1111-1111-111111111111",
  "command_id": "33333333-3333-3333-3333-333333333333",
  "base_revision": 13,
  "command": {
    "op": "insert_inline_token",
    "field_id": "field_7",
    "token": {"kind": "text", "text": "إضافة"},
    "anchor": {"end": true}
  }
}
```

يحافظ MCP على الفرق بين الحقل المحذوف و`null` الصريح؛ لذلك يصل
`update_figure.asset_id: null` إلى FastAPI لمسح أصل الشكل. FastAPI هو من
يتحقق من الأصول ويستبدل provenance لأي كتلة منشأة، ولا يثق في
`metadata.source` القادمة من العميل.

### 2.4 سير عمل العميل

1. استخدم `get_draft_outline` للتنقل الخفيف إن لم تحتج المحتوى الكامل.
2. استخدم `get_draft_blocks` عندما تحتاج هوية field أو token أو list أو
   item أو table أو بنية المحتوى الدقيقة.
3. لا تخترع أي معرّف؛ خذه من آخر استجابة للمسودة.
4. مرّر أحدث `revision` في `base_revision`.
5. أنشئ `command_id` جديداً لكل تعديل منطقي، ولا تعِد استخدامه لحمولة أخرى.
6. استخدم أمراً موجهاً بدلاً من تصنيع مستند خام كامل.
7. عند نجاح الأمر استخدم `revision` الجديد للعملية التالية.
8. عند `revision_conflict` أعد قراءة المسودة قبل إعادة بناء المحاولة.
9. كل أمر تعديل ناجح محفوظ تلقائياً كمراجعة مسودة غير قابلة للتعديل.
10. لا تستدع `compile_draft` إلا بطلب صريح؛ فهو يجمع المراجعة الحالية
    التصدير لاحقاً. راقب `get_compile_status`، ولا تطلب PDF إلا عند
    `pdf_ready=true` و`stale=false`.
11. لا تنشئ LaTeX أو قائمة أصول أو hash للتجميع؛ FastAPI وBuTeX يملكانها.
12. اسرد الأصول قبل استرجاعها، ولا تخترع `asset_id` أو بيانات ملف.
13. يرفع `upload_article_asset` فقط ملفاً اختاره المستخدم؛ ثم يُستخدم
    `asset_id` العائد مع `insert_figure` أو `update_figure`.

لا ترسل أدوات MCP `article_id` أو credential المستخدم أو بيانات actor إلى
عامل BuTeX. هي ترسل الطلب إلى FastAPI فقط، وFastAPI يحتفظ بملكية المصادقة
والصلاحيات وprovenance والأصول والمراجعات وidempotency والحفظ.

### 2.5 الأخطاء والتعافي

إخفاق FastAPI يظهر كخطأ أداة MCP، لا كنتيجة نجاح مزيفة. نص الخطأ JSON آمن
وقابل للقراءة آلياً:

```json
{
  "status": 409,
  "code": "revision_conflict",
  "message": "وصل تعديل أحدث للمسودة؛ أعد قراءتها.",
  "current_revision": 14
}
```

يظهر `current_revision` حين يوفره FastAPI. تفاصيل التحقق الخام، والحمولات
الخام، وآثار المكدس، والتوكنات لا تُعرض للعميل ولا تُسجّل؛ لا يبقى إدارياً إلا
اللقطات المحدودة والمنقّحة الموضحة في قسم التحليلات. في تعارض المراجعة يجب أن
يعيد العميل الفحص؛ أما خطأ التحقق فيُصلح الأمر وفق المخطط المنشور قبل المحاولة.

### 2.6 الحدود المؤجلة

لا توجد أداة MCP لحذف الأصول أو استعادة مراجعة تاريخية؛ الاستعادة عملية بشرية
من واجهة سجل المسودة. تبقى تعديلات الوكيل مرئية في السجل مع provenance، ولا
يجلب FastAPI أصولاً من URL خارجي.
ينزّل MCP رابط الملف المؤقت الذي يسلّمه العميل بحدود صارمة، ولا يرسل إليه
توكن Albayan. ويبقى استبدال المستند كاملاً، تقديم المقال، حذف المقال، والطفرات
العالية الأثر خارج هذه الأدوات.

## 3. تحليلات استدعاءات MCP

يسجل وسيط SDK واحد كل طلب بروتوكول فعلي من نوع `tools/call`. لا تحتوي الأدوات
نفسها على عدادات، ولا توجد قائمة ثابتة للعمليات في الوسيط: يؤخذ اسم الأداة من
الطلب، ويؤخذ اسم أمر Document2 تلقائياً من `arguments.command.op` إن وُجد.
لذلك تظهر الأدوات والأوامر المستقبلية في الإحصاءات بلا migration.

بعد اكتمال الاستدعاء يرسل الوسيط حدثاً واحداً إلى
`POST /api/v1/mcp/call-logs` عبر عميل FastAPI المصادق نفسه. مهلة الإرسال
ثانيتان، وأي تعطل في التسجيل لا يغيّر نتيجة الأداة ولا يعيد المحاولة داخل
طلب المستخدم. لا يتصل MCP بقاعدة البيانات أو عامل BuTeX أو التخزين مباشرة.

تُنقّح لقطات الإدخال والإخراج عودية قبل الإرسال ومرة أخرى عند حد FastAPI:

- تُحجب مفاتيح credentials المحددة، مع إبقاء حقل Document2 العادي `token`.
- الحد الأقصى للعمق 12، ولأبناء المجموعة 100، وللنص المفرد 4096 محرفاً.
- حد الإدخال النهائي 32 KiB والإخراج 64 KiB؛ تستبدل اللقطة الكبيرة بغلاف
  JSON يوضح القطع والحجم الأصلي.
- لا تُحفظ الترويسات أو Bearer أو آثار المكدس. نص الخطأ الآمن لا يتجاوز
  2000 محرف.
- يحفظ `trace_id` الصالح من span الحالي للربط المستقبلي فقط؛ لا يوجد مصدر
  Langfuse أو OTLP في هذا الإصدار.

FastAPI يملك هوية `user_id` والطابع الزمني ومعرّف السجل. مسار الإدخال مخصص
لهوية agent عند تفعيل MCP. القراءة عبر المسارات الإدارية التالية فقط:

```text
GET /api/v1/admin/mcp/analytics?period=24h|7d|30d|90d
GET /api/v1/admin/mcp/calls
GET /api/v1/admin/mcp/calls/{call_id}
```

تعرض `/admin/mcp` الإجماليات والسلسلة الزمنية وترتيب الأدوات وعائلات أوامر
Document2 الست والنشاط الحديث والتفاصيل المنقّحة عند الطلب. التصنيف المركزي
في `backend/app/document2_registry.py` مطابق لاتحاد الأوامر باختبار آلي؛ وتظهر
أي عملية تاريخية أو مستقبلية غير مصنفة تحت «أوامر أخرى».

---

## سجل التحديثات

| التاريخ | التحديث |
|---------|---------|
| ٢٣/٠٨/٢٠٢٦ | إنشاء المجلد والملف؛ نقل توثيق MCP من `docs/afkar-al-mashrou.md` |
| ٢٣/٠٨/٢٠٢٦ | إضافة ملخص ما تم إنجازه (واجهة، خلفية، قاعدة بيانات) |
| ٢٥/٠٨/٢٠٢٦ | تحديث الحالة الحالية بعد Batch 1-3؛ إضافة حد قدرات الوكيل؛ ووسم التصميم القديم كتاريخي/مخطط |
| ٢٥/٠٨/٢٠٢٦ | إضافة «ربط ChatGPT — الدليل الكامل»: DCR، النطاقات، متغيرات Railway، خطوات الواجهة، واستكشاف الأخطاء من التجربة الفعلية |
| ٢٧/٠٨/٢٠٢٦ | إضافة القسم ٢: استنتاجات تحليل BuTeX (موضع الإدراج، فصل رفع/إدراج الأصول، متطلبات الحزمة، تراجع الجلسة، مسار REST/MCP) |
| ١٣/٠٩/٢٠٢٦ | توثيق أدوات جلسة Document2 الأربع واتحاد الأوامر المقيّد وسير التعافي من تعارض المراجعة |
| ١٣/٠٩/٢٠٢٦ | إضافة أدوات إنشاء المسودة وقراءة تفاصيلها وتحديث بياناتها مع مزامنة Article وDocument2 |
| ١٣/٠٩/٢٠٢٦ | إضافة التسجيل المركزي المنقّح لاستدعاءات MCP ولوحة الإدارة واحتفاظ 90 يوماً |
| ١٣/٠٩/٢٠٢٦ | إضافة حفظ وتجميع جلسة Document2 ومتابعة الحالة وعرض PDF مضمّن عبر MCP |
| ١٤/٠٩/٢٠٢٦ | إضافة سرد أصول الصور وعرضها ورفعها بمعلمات الملف الأصلية عبر MCP |
