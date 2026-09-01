# تدقيق ظهور النصوص غير العربية في الواجهة

تاريخ التدقيق: 1 سبتمبر 2026.

## النطاق

- يشمل `frontend/src` فقط.
- يستثني صفحة `/wukala` ومكوّناتها، بناءً على القرار بأن تعرض أسماء مزودي الذكاء الاصطناعي والمحتوى التقني.
- لا يعدّ محتوى المستخدمين، عناوين المقالات، أسماء الأشخاص، عناوين البريد، أسماء الملفات، أو أسماء التطبيقات الخارجية نصوص واجهة يجب ترجمتها.
- هذه وثيقة جرد فقط؛ لم تُعدّل العناصر الواردة أدناه أثناء التدقيق.

## نصوص ثابتة مؤكدة

### `See JSON`

يظهر الزر الإنجليزي في وضع التطوير في موضعين:

- [`frontend/src/app/maktabi/maqalati/[id]/tahrir/page.tsx`](../frontend/src/app/maktabi/maqalati/%5Bid%5D/tahrir/page.tsx)
- [`frontend/src/components/dashboard/exported-tex-dev-panel.tsx`](../frontend/src/components/dashboard/exported-tex-dev-panel.tsx)

### حرف `v` قبل رقم الإصدار

يظهر للمستخدم بصيغ مثل `الإصدار v2` أو `v2` في:

- [`frontend/src/app/admin/maqalat/[id]/page.tsx`](../frontend/src/app/admin/maqalat/%5Bid%5D/page.tsx)
- [`frontend/src/app/admin/maqalat/page.tsx`](../frontend/src/app/admin/maqalat/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/maqalati/[id]/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/maqalati/%5Bid%5D/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/maqalati/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/maqalati/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/murajaati/[assignmentId]/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/murajaati/%5BassignmentId%5D/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/murajaati/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/murajaati/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/tahriri/[id]/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/tahriri/%5Bid%5D/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/tahriri/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/tahriri/page.tsx)

### أمثلة البريد الإلكتروني

تظهر أمثلة لاتينية داخل حقول الإدخال:

- `name@example.com` في [`frontend/src/app/admin/maqalat/[id]/page.tsx`](../frontend/src/app/admin/maqalat/%5Bid%5D/page.tsx)
- `person@example.com` في [`frontend/src/app/admin/mustakhdimin/page.tsx`](../frontend/src/app/admin/mustakhdimin/page.tsx)

### مصطلحات تقنية داخل نص عربي

المصطلحات التالية ظاهرة عمدًا داخل جمل عربية، لكنها تظل أحرفًا لاتينية:

- `Creative Commons` في:
  - [`frontend/src/app/al-siyasat-wal-shurut/page.tsx`](../frontend/src/app/al-siyasat-wal-shurut/page.tsx)
  - [`frontend/src/app/siyasat-an-nashr/page.tsx`](../frontend/src/app/siyasat-an-nashr/page.tsx)
- `PDF` و`PNG` و`APA` و`IEEE` في [`frontend/src/app/irshadat-al-mualifin/page.tsx`](../frontend/src/app/irshadat-al-mualifin/page.tsx).
- `TeX` و`JSON` في لوحات التطوير:
  - [`frontend/src/components/dashboard/exported-tex-dev-panel.tsx`](../frontend/src/components/dashboard/exported-tex-dev-panel.tsx)
  - [`frontend/src/components/dashboard/document-json-dev-dialog.tsx`](../frontend/src/components/dashboard/document-json-dev-dialog.tsx)
- `OAuth` و`OpenID` و`client_id` و`redirect_uri` و`ChatGPT` في:
  - [`frontend/src/components/oauth/oauth-consent-form.tsx`](../frontend/src/components/oauth/oauth-consent-form.tsx)
  - [`frontend/src/lib/oauth-consent.ts`](../frontend/src/lib/oauth-consent.ts)
- `MCP` في [`frontend/src/components/settings/dev-mode-agents-card.tsx`](../frontend/src/components/settings/dev-mode-agents-card.tsx).
- `Cursor` و`Claude Desktop` خارج `/wukala` في [`frontend/src/components/settings/agent-tokens-panel.tsx`](../frontend/src/components/settings/agent-tokens-panel.tsx).

### عارض JSON في وضع التطوير

يعرض عارض JSON كلمات وقيمًا تقنية إنجليزية:

- `Array(n)`
- `Object(n)`
- `null`
- `true`
- `false`

المصدر: [`frontend/src/components/dashboard/document-json-dev-dialog.tsx`](../frontend/src/components/dashboard/document-json-dev-dialog.tsx).

### اسم ملف التنزيل

ملف المعاينة يُنزّل باسم `compiled.pdf` من [`frontend/src/components/dashboard/compiled-pdf-viewer.tsx`](../frontend/src/components/dashboard/compiled-pdf-viewer.tsx). عنوان رابط التنزيل نفسه عربي.

## مصادر ديناميكية قد تعرض الإنجليزية

### تفاصيل أخطاء API الخام

تعيد طبقة API المشتركة حقول `detail` و`message` من استجابة الخادم كما هي. إذا أرسل الخادم أو مكتبة خارجية رسالة إنجليزية، تصل إلى الواجهة دون ترجمة.

المصدر المركزي: [`frontend/src/lib/api.ts`](../frontend/src/lib/api.ts).

توجد مسارات مخصصة تفعل الشيء نفسه في:

- [`frontend/src/lib/api/articles.ts`](../frontend/src/lib/api/articles.ts)
- [`frontend/src/lib/api/issues.ts`](../frontend/src/lib/api/issues.ts)

تعرض الصفحات والمكوّنات التالية `err.message` أو `ApiError.message` للمستخدم مباشرة:

- [`frontend/src/app/admin/balaghat/page.tsx`](../frontend/src/app/admin/balaghat/page.tsx)
- [`frontend/src/app/admin/maqalat/[id]/page.tsx`](../frontend/src/app/admin/maqalat/%5Bid%5D/page.tsx)
- [`frontend/src/app/admin/maqalat/page.tsx`](../frontend/src/app/admin/maqalat/page.tsx)
- [`frontend/src/app/admin/mustakhdimin/page.tsx`](../frontend/src/app/admin/mustakhdimin/page.tsx)
- [`frontend/src/app/admin/page.tsx`](../frontend/src/app/admin/page.tsx)
- [`frontend/src/app/balaghat/page.tsx`](../frontend/src/app/balaghat/page.tsx)
- [`frontend/src/app/daawa/[token]/page.tsx`](../frontend/src/app/daawa/%5Btoken%5D/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/isharat/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/isharat/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/maqalati/[id]/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/maqalati/%5Bid%5D/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/maqalati/jadid/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/maqalati/jadid/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/maqalati/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/maqalati/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/murajaati/[assignmentId]/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/murajaati/%5BassignmentId%5D/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/murajaati/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/murajaati/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/tahriri/[id]/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/tahriri/%5Bid%5D/page.tsx)
- [`frontend/src/app/maktabi/(lawha)/tahriri/page.tsx`](../frontend/src/app/maktabi/%28lawha%29/tahriri/page.tsx)
- [`frontend/src/app/maktabi/maqalati/[id]/tahrir/page.tsx`](../frontend/src/app/maktabi/maqalati/%5Bid%5D/tahrir/page.tsx)
- [`frontend/src/components/dashboard/article-assets-panel.tsx`](../frontend/src/components/dashboard/article-assets-panel.tsx)
- [`frontend/src/components/dashboard/compiled-pdf-viewer.tsx`](../frontend/src/components/dashboard/compiled-pdf-viewer.tsx)
- [`frontend/src/components/dashboard/exported-tex-dev-panel.tsx`](../frontend/src/components/dashboard/exported-tex-dev-panel.tsx)
- [`frontend/src/components/issues/issue-image-thumbnail.tsx`](../frontend/src/components/issues/issue-image-thumbnail.tsx)
- [`frontend/src/components/notifications/notification-bell.tsx`](../frontend/src/components/notifications/notification-bell.tsx)
- [`frontend/src/components/settings/account-deletion-request-card.tsx`](../frontend/src/components/settings/account-deletion-request-card.tsx)
- [`frontend/src/components/settings/agent-tokens-panel.tsx`](../frontend/src/components/settings/agent-tokens-panel.tsx)
- [`frontend/src/components/settings/profile-form.tsx`](../frontend/src/components/settings/profile-form.tsx)

### واجهات Clerk المدمجة

لا يمرر [`frontend/src/components/app-clerk-provider.tsx`](../frontend/src/components/app-clerk-provider.tsx) إعداد `localization` إلى `ClerkProvider`، وحزمة `@clerk/localizations` غير مثبتة حاليًا.

قد تظهر الإنجليزية في:

- CAPTCHA داخل صفحة التسجيل.
- نافذة إعادة التحقق الأمني التي يستدعيها `useReverification` قبل إرسال طلب حذف الحساب.
- أخطاء Clerk الجديدة أو غير الموجودة في خريطة الترجمة اليدوية داخل [`frontend/src/lib/auth-ui.ts`](../frontend/src/lib/auth-ui.ts).

الرسالة `You're already signed in.` أصبحت مغطاة حاليًا بالترجمة اليدوية: `أنت مسجّل الدخول بالفعل.`

### بيانات OAuth الخارجية

قد تظهر بالإنجليزية لأنها تأتي من التطبيق الخارجي:

- اسم التطبيق.
- عنوان التطبيق ونطاق إعادة التوجيه.
- وصف scope غير معروف.
- قيمة scope نفسها عندما لا يوجد وصف أو ترجمة.

تعيد الدالة `scopeLabelAr` الوصف الخام أو اسم scope الخام عند عدم وجود ترجمة معروفة. المصدر: [`frontend/src/lib/oauth-consent.ts`](../frontend/src/lib/oauth-consent.ts).

### الأدوار والحالات غير المعروفة

تعيد صفحة إدارة المستخدمين قيمة الدور أو حالة الدعوة الخام إذا لم تكن موجودة في خريطة الترجمة. قد تظهر قيم مثل `reviewer` أو `pending` عند إضافة قيمة خادمية جديدة.

المصدر: [`frontend/src/app/admin/mustakhdimin/page.tsx`](../frontend/src/app/admin/mustakhdimin/page.tsx).

### عناصر رفع الملفات الأصلية

تستخدم بعض الصفحات عنصر `<input type="file">` الأصلي. قد يعرض المتصفح نصوصًا مثل `Choose file` و`No file chosen` إذا كانت لغة المتصفح أو نظام التشغيل إنجليزية.

المواضع تشمل:

- [`frontend/src/app/balaghat/page.tsx`](../frontend/src/app/balaghat/page.tsx)
- [`frontend/src/components/dashboard/article-assets-panel.tsx`](../frontend/src/components/dashboard/article-assets-panel.tsx)

## عناصر جرى التحقق منها ولا تحتاج إجراء حاليًا

- محرر BuTeX والمعاينة يمران `uiLocale="ar"`.
- التواريخ الظاهرة تستخدم محليّة أم القرى العربية.
- رسائل المصادقة المخصصة تمر عبر `translateClerkError`، مع بقاء خطر الرسائل الجديدة غير المعروفة كما ذُكر أعلاه.

