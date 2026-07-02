# تصميم: لوحة عمل المؤلف («مكتبي»)

**التاريخ:** 2026-07-01
**النطاق:** الإصدار الأول (v1) — المؤلف فقط، ببنية قابلة للتوسّع لاحقاً لأدوار المراجع والمحرر/الإدارة.

---

## 1. المشكلة والهدف

المستخدم المسجّل في منصة البيان لا يملك اليوم أي نقطة دخول لسير عمل المقالات. الهيدر يعرض فقط اسمه ورابط «إعدادات الحساب» (`/al-idayat`). قاعدة البيانات تدعم بالفعل دورة حياة كاملة للمقال (`articles`, `article_versions` بحالات `draft`→`submitted`→`under_review`→`accepted`/`rejected`→`published`)، لكن لا واجهة تستخدمها.

**الهدف:** بناء لوحة عمل («مكتبي») تتيح للمؤلف إنشاء مقال، تحريره عبر BuTeX، تقديمه، ومتابعة حالته — بهيكل مفتوح ونمطي يسمح لاحقاً بإضافة أدوار (مراجع، محرر/إدارة) دون إعادة بناء القشرة.

**خارج النطاق (مؤجَّل عمداً):**
- إدارة مؤلفين مشاركين (co-authors)
- دعوات المراجعين ولوحة المراجع
- لوحة محرر/إدارة (`is_admin`)
- إشعارات (push/email)
- رفع ZIP كمصدر بديل
- تجميع PDF عبر worker
- إصدارات جديدة تلقائية بعد قرار المراجعة (v2, v3…)

---

## 2. القرارات الأساسية

| # | القرار |
|---|--------|
| 1 | v1 يخدم **المؤلف فقط**. الأدوار (`author`, `reviewer`, `admin`) موجودة كحقل في إعداد التنقل من اليوم الأول، لكن v1 يفعّل `author` فقط. |
| 2 | لا صفحة/تبويب واحد ضخم — **قشرة مشتركة (`DashboardShell`) + مسارات فرعية مستقلة**، لكل قسم صفحة App Router خاصة به. |
| 3 | محرر BuTeX (`ButexDocumentEditor2`) يعيش في **مسار مستقل بملء الشاشة**، بدون `DashboardShell`، لأنه ثقيل بصرياً ويحتاج تركيزاً كاملاً. |
| 4 | قابلية التحرير محكومة بـ `article_versions.status`: `draft` = قابل للتحرير، أي حالة أخرى = مجمّدة (بدون عمود `is_editable`، حسب `database-schema.md`). |
| 5 | المخطوطة المجمّدة تُعرض عبر معاينة headless (`fromDocumentJson2` + `document2Preview` + `DocumentPreview`) — **بدون** `ButexDocumentEditor2`. `editableEquations={false}` غير كافٍ لأنه يجمّد المعادلات فقط، لا بقية المحرر. |
| 6 | `document.json` يُخزَّن في **S3 حقيقي** (ليس عمود DB، ليس تخزيناً محلياً) — يطابق القرار الموثّق مسبقاً في `database-schema.md` (`storage_prefix` فقط في DB). عميل S3 بسيط (put/get) بدون worker أو تجميع PDF. |
| 7 | لا نظام أدوار كامل في v1 — فحص صلاحية واحد بسيط (`assert_is_author`) قابل للاستبدال لاحقاً بفحص أدوار متعدد دون تغيير الراوترات. |
| 8 | لا مكتبة إدارة حالة إضافية (لا React Query) — `useState`/`useEffect` كافٍ؛ يمكن الترقية لاحقاً دون تغيير طبقة استدعاء الـ API. |

---

## 3. مسارات Frontend

```text
/maktabi                          نظرة عامة
/maktabi/maqalati                 قائمة مقالاتي
/maktabi/maqalati/jadid           إنشاء مقال جديد
/maktabi/maqalati/[id]            تفاصيل المقال
/maktabi/maqalati/[id]/tahrir     محرر BuTeX (ملء الشاشة)
```

### الحماية
- `/maktabi(.*)` تُضاف إلى `isProtectedRoute` في `frontend/src/middleware.ts` (نفس نمط `/al-idayat`).
- رابط «مكتبي» يُضاف في `frontend/src/components/auth-header.tsx` بجانب «إعدادات الحساب».

### القشرة القابلة للتوسّع

```ts
// frontend/src/lib/dashboard-config.ts
type DashboardRole = "author" | "reviewer" | "admin";

type DashboardSection = {
  id: string;
  label: string;
  href: string;
  roles: DashboardRole[];
};

export const dashboardSections: DashboardSection[] = [
  { id: "overview", label: "نظرة عامة", href: "/maktabi", roles: ["author"] },
  { id: "articles", label: "مقالاتي", href: "/maktabi/maqalati", roles: ["author"] },
  // لاحقاً: { id: "reviews", label: "مراجعاتي", href: "/maktabi/murajaati", roles: ["reviewer"] }
];
```

`DashboardShell` (layout مشترك لكل `/maktabi/**` عدا `tahrir`) يفلتر `dashboardSections` حسب أدوار المستخدم الحالي (v1: `["author"]` دائماً، ثابت — لا استدعاء API إضافي للأدوار في v1).

`/maktabi/maqalati/[id]/tahrir` له `layout.tsx` خاص به: شريط علوي فقط (رجوع، عنوان، حفظ، تقديم) — بدون القشرة.

---

## 4. محتوى الشاشات

### 4.1 `/maktabi` — نظرة عامة
- ترحيب باسم المستخدم (من Clerk)
- 3 بطاقات ملخص: عدد المسودات، قيد المراجعة، منشورة/مقبولة (مُشتقة من `GET /articles/me`، بدون endpoint إحصائي منفصل)
- زر بارز «مقال جديد» → `/maktabi/maqalati/jadid`
- آخر 3–5 مقالات (عنوان، حالة، تاريخ) + رابط «عرض الكل»
- حالة فارغة: رسالة ترحيبية + زر «ابدأ مقالك الأول»

### 4.2 `/maktabi/maqalati` — قائمة مقالاتي
- جدول/بطاقات: العنوان، الحالة، رقم الإصدار، آخر تحديث، إجراء
- فلتر بسيط: الكل / مسودات / مُقدَّمة / قيد المراجعة / منتهية (بدون بحث متقدم)
- إجراء الصف: `draft` → «تحرير» (`/tahrir`)؛ غير ذلك → «عرض» (تفاصيل، معاينة مجمّدة)
- زر ثابت أعلى القائمة: «مقال جديد»

### 4.3 `/maktabi/maqalati/jadid` — إنشاء مقال
نموذج خفيف: العنوان (مطلوب)، ملخص مختصر (اختياري). عند الحفظ:
1. `POST /api/v1/articles` ينشئ `article` + `article_version` (v1, `status=draft`, `source_type=web_editor`) + `article_authors` (المستخدم الحالي، `author_order=1`, `is_corresponding=true`) في عملية واحدة.
2. إعادة توجيه إلى `/maktabi/maqalati/{id}/tahrir`.

### 4.4 `/maktabi/maqalati/[id]` — تفاصيل المقال
- رأس: العنوان + شارة الحالة + رقم الإصدار الحالي
- شريط تقدّم نصي لحالة سير العمل
- قائمة الإصدارات (v1, v2… بالتاريخ و`change_summary`)
- معاينة `DocumentPreview` للنسخة الحالية (عند توفر `document.json`)
- إجراءات حسب الحالة:
  - `draft`: «متابعة التحرير» + «تقديم المقال» (تأكيد قبل التقديم: «لن تتمكن من تعديل المحتوى بعد التقديم»)
  - `submitted`/`under_review`: عرض فقط
  - `published`: رابط للنسخة المنشورة (عند وجودها لاحقاً)

### 4.5 `/maktabi/maqalati/[id]/tahrir` — المحرر
- الوصول مسموح فقط إذا `status === draft`؛ غير ذلك إعادة توجيه لصفحة التفاصيل
- شريط علوي: رجوع، عنوان، حفظ، تقديم
- حفظ يدوي عبر زر (بدون autosave في v1)
- تنبيه عند الخروج بتغييرات غير محفوظة
- «تقديم» يستخدم نفس منطق endpoint التقديم في صفحة التفاصيل

---

## 5. Backend

### الملفات الجديدة

| الملف | الغرض |
|-------|-------|
| `app/routers/articles.py` | راوتر جديد، `prefix="/api/v1/articles"`، بنفس نمط `users.py` (`AuthDep`, `DbDep`) |
| `app/services/article_service.py` | منطق الصلاحيات والاستعلامات |
| `app/core/s3.py` | عميل S3 بسيط: `put_json(prefix, data)` / `get_json(prefix)` فقط |
| `app/schemas/article.py` | Pydantic schemas للطلب/الاستجابة |

### تعديلات على ملفات موجودة

| الملف | التعديل |
|-------|---------|
| `app/main.py` | `app.include_router(articles.router)` |
| `app/core/config.py` | إضافة `s3_bucket`, `s3_endpoint_url`, `s3_access_key`, `s3_secret_key` (متغيرات بيئة، نفس نمط `clerk_secret_key`) |
| `requirements.txt` | إضافة `boto3` |

**لا تغيير على مخطط الجداول** — `storage_prefix` الموجود يكفي؛ فقط يُستخدم فعلياً الآن بدل أن يبقى غير مُفعَّل.

### Endpoints

| Method | المسار | الوصف | ملاحظة صلاحية/حالة |
|--------|--------|-------|----------------------|
| `GET` | `/api/v1/articles/me` | قائمة مقالات المستخدم الحالي كمؤلف | `article_authors.user_id = current_user` |
| `POST` | `/api/v1/articles` | إنشاء مقال + إصدار v1 draft + ربط مؤلف | — |
| `GET` | `/api/v1/articles/{id}` | تفاصيل مقال (بيانات + الإصدار الحالي) | 404 إن لم يكن المستخدم مؤلفاً عليه |
| `GET` | `/api/v1/articles/{id}/document` | جلب `document.json` من S3 | حسب `storage_prefix` للإصدار الحالي |
| `PUT` | `/api/v1/articles/{id}/document` | حفظ `document.json` إلى S3 | فقط إذا `status == draft`، وإلا `409` |
| `POST` | `/api/v1/articles/{id}/submit` | `draft` → `submitted`, `submitted_at=now()` | `409` إذا لم يكن `draft` |

### الصلاحية (دالة واحدة قابلة للاستبدال)

```python
def assert_is_author(db: Session, article_id: UUID, user_id: UUID) -> Article:
    article = db.get(Article, article_id)
    is_author = db.scalar(
        select(ArticleAuthor).where(
            ArticleAuthor.article_id == article_id,
            ArticleAuthor.user_id == user_id,
        )
    )
    if not article or not is_author:
        raise HTTPException(404)  # لا نكشف الوجود لغير المخوّل
    return article
```

### منطق التقديم

```python
def submit_article(db: Session, article: Article) -> ArticleVersion:
    version = current_version(article)  # ORDER BY version_number DESC LIMIT 1
    if version.status != VersionStatus.DRAFT:
        raise HTTPException(409, "المقال مُقدَّم بالفعل")
    version.status = VersionStatus.SUBMITTED
    version.submitted_at = datetime.now(timezone.utc)
    db.commit()
    return version
```

---

## 6. Frontend: طبقة استدعاء الـ API

```ts
// frontend/src/lib/api/articles.ts
listMyArticles(): Promise<ArticleSummary[]>
createArticle(input: { title: string; abstract?: string }): Promise<Article>
getArticle(id: string): Promise<ArticleDetail>
getArticleDocument(id: string): Promise<Document2Json>
saveArticleDocument(id: string, doc: Document2Json): Promise<void>
submitArticle(id: string): Promise<void>
```

دوال بسيطة تستخدم `NEXT_PUBLIC_API_URL` وتُرفق رمز Clerk في الترويسة، بنفس نمط الاستدعاءات الحالية في `frontend/src/components/settings/*`.

---

## 7. معالجة الأخطاء

| الحالة | الاستجابة |
|--------|-----------|
| مستخدم غير مؤلف على المقال | `404` (لا كشف وجود) |
| محاولة حفظ/تحرير مقال غير `draft` | `409` + رسالة عربية واضحة في الواجهة |
| تقديم مقال مُقدَّم بالفعل | `409` |
| فشل اتصال S3 | `503` + رسالة «تعذّر حفظ المخطوطة، حاول مجدداً» (بنفس نمط معالجة `OperationalError` في `users.py`) |
| فشل اتصال DB | `503` (نمط موجود بالفعل) |

---

## 8. خطة الاختبار (لاحقاً في مرحلة التنفيذ)

- Backend: اختبارات لكل endpoint (نجاح، 404 لغير المؤلف، 409 للحالة الخاطئة)
- Frontend: اختبار يدوي لتدفق: إنشاء → تحرير → حفظ → تقديم → عرض مجمّد
- لا اختبارات E2E آلية مطلوبة في v1 (خارج النطاق)

---

## 9. ما بعد v1 (للتوضيح فقط، غير مُلزم الآن)

- إضافة `reviewer` إلى `dashboard-config.ts` + مسار `/maktabi/murajaati`
- إضافة `admin` + `/maktabi/idara` (مبني على `users.is_admin`)
- استبدال `assert_is_author` بفحص أدوار متعدد
- Autosave في المحرر
- Worker تجميع PDF (خارج DB، حسب `database-schema.md` §8)
