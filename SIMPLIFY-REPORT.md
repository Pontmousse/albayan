# تقرير تبسيط — مراجِع / محرر / إدارة

مراجعة فقط على التغييرات المحلية (معدّل + غير متتبَّع). **لم يُغيَّر أي ملف أثناء إعداد هذا التقرير.**

---

## أولوية عالية

| # | ماذا | أين |
|---|------|-----|
| 1 | **كود ميت:** `assert_is_reviewer` غير مستدعى؛ `_NOT_FOUND` و `_FORBIDDEN` متطابقان | `review_service.py` |
| 2 | **`_asset_response` منسوخة 3 مرات** (articles / editor / reviews) — نفس sanitization + S3 + Response | راوترات الخلفية |
| 3 | **جلب blob الأصول مكرر 3 مرات** في الواجهة بنفس المنطق | `api/articles.ts`, `editor.ts`, `reviews.ts` |
| 4 | **لفّافات فارغة** `_admin_user` / `_current_user` = مجرد `return current_user(...)` | `admin.py`, `articles.py` |
| 5 | **جلب قوائم مزدوج:** الـ shell يستدعي `listMyAssignments` + `listEditorArticles`، ثم صفحات maktabi تعيد نفس الطلبات | `dashboard-shell.tsx` + `page.tsx` / قوائم |

---

## أولوية متوسطة

| # | ماذا | أين |
|---|------|-----|
| 6 | منطق «أحدث مراجعة لإصدار» مكرر بين الراوتر والـ service | `reviews.py` ↔ `review_service.py` |
| 7 | `count_submitted_reviews_for_version` تكرار لـ `submitted_reviews_for_version` → يكفي `len(...)` | `editor_service.py` |
| 8 | نوع `ReviewerAssignmentStatus` مكرر حرفيًا | `api/admin.ts` و `api/reviews.ts` |
| 9 | `PENDING_EDITOR` ≡ `ACTIVE_STATUSES` + cast ضعيف للنوع | `maktabi/(lawha)/page.tsx` |
| 10 | `undefined` ثم `?? null` للمستند + try متداخل صامت؛ بعد الحفظ/التسليم يُعاد جلب JSON من S3 بلا داعٍ | صفحات `murajaati/[id]` و `tahriri/[id]` |
| 11 | تحميل تفصيلي متسلسل (metadata ثم document) بدل `Promise.all` | نفس صفحات التفصيل |
| 12 | قائمة المقالات الإدارية تحمّل علاقات ثقيلة ثم تصفّي الحالة في Python | `admin_article_service.list_articles` |
| 13 | بعد كل إجراء إداري يُعاد `listAdminUsers` كاملًا | `admin/maqalat/[id]` |

---

## أولوية منخفضة / اختياري

- توحيد `formError`/`formOk` في رسالة واحدة `{ type, text }`؛ إزالة cast قرار القبول/الرفض.
- خريطة دور→href بدل ternary مزدوج في `daawa/[token]`.
- تحديث تعليق `useButexImageResolver` (المعامل صار `scopeId` عامًا).
- استخراج مشترك خفيف لـ `AdminShell` ≈ `DashboardShell`، وقطع UI مشتركة للقوائم/التفصيل (`StatusFilterTabs`, `DetailHeader`) — أكبر من «تنظيف سريع».

---

## ما يبقى كما هو (لا تلمسه في جولة تبسيط)

- استخراج `deps.current_user` نفسه مفيد.
- `ConfirmDialog`, `DocumentFrozenPreview`, `StatusBadge` مستخدمة جيدًا.
- `review_service` و `editor_service` مجالات منفصلة — لا تدمجهما.
- تعيين المراجع `ACCEPTED` فورًا متسق؛ فرع `INVITED` توافق لصفوف قديمة.
- لا polling ولا N+1 واضح في مسارات الـ list (يوجد `selectinload`).

---

## ترتيب مقترح للتنفيذ

1. حذف الميت + لفّافات `current_user`
2. مساعد أصول واحد (خلفية + واجهة)
3. توحيد `_review_for_version` و `len(submitted_...)`
4. نوع الحالة المشترك + ثوابت الحالة في الصفحة الرئيسية
5. مشاركة/كاش قوائم الـ shell مع الصفحات
6. ثم تحسينات الأداء (parallel fetch، عدم إعادة document، تصفية SQL للإدارة)
