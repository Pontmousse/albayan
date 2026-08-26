# AGENTS.md — مجلة البيان (Al-Bayan)

إرشادات للوكلاء/المساعدين الذين يعملون على هذا المستودع.

## الهيكل

- **`frontend/`** — تطبيق **Next.js** (App Router، TypeScript، Tailwind). كل ما يخص الواجهة والتجربة البصرية والتوجيه الأمامي.
- **`backend/`** — تطبيق **Python FastAPI**. واجهة برمجة التطبيقات، التحكيم، النماذج الخادمية، و**قاعدة البيانات** عند إضافتها.

**قاعدة:** لا تضع منطق قاعدة بيانات أو أسرار خادمية داخل `frontend/`. استهلك الـ API من المتصفح عبر `NEXT_PUBLIC_API_URL` (انظر `frontend/.env.example`).

## أعلام الميزات (feature flags)

| العلم | الواجهة | الخلفية | يتحكم في |
|-------|---------|---------|----------|
| MCP | `NEXT_PUBLIC_MCP_ENABLED` | `MCP_ENABLED` | وكلاء MCP: زر «وكلاء»، `/wukala`، إدارة المفاتيح، مصادقة `alb_` |
| تطوير | `NEXT_PUBLIC_DEV_MODE` | `DEV_MODE` | تشخيص التجميع: `compile.log`، لوحة TeX المُصدَّر، JSON حي في المحرر |

الخلفية تحمي واجهات MCP بـ `MCP_ENABLED` — لا تعتمد على علم الواجهة وحده.

## العربية واتجاه النص

- الجذر في الواجهة: `lang="ar"` و `dir="rtl"` في `frontend/src/app/layout.tsx`.
- فضّل في Tailwind الأدوات المنطقية (`ms-`, `me-`, `ps-`, `pe-`, `start`, `end`) بدلًا من `left`/`right` حيث أمكن.

## التواريخ الظاهرة

- كل تاريخ يظهر للمستخدم في الواجهة هجري أم القرى عبر `formatDate` / `formatDateTime` / `formatHijriYear` في `frontend/src/lib/format-date.ts` (`ar-SA-u-ca-islamic-umalqura`).
- لا تستدعِ `Intl.DateTimeFormat` لتواريخ الواجهة خارج هذا الملف.
- أبقِ `dateTime` على `<time>` (وأي حمولة API) بالميلادي ISO.

## النسخ إلى الحافظة

- أزرار النسخ أيقونة الحافظة المشتركة `CopyButton` في `frontend/src/components/ui/copy-button.tsx` — بلا نص «نسخ» ظاهر.

## أوامر مفيدة

| المجلد    | الأمر           |
| --------- | --------------- |
| جذر المستودع | `./launch.sh` (Docker DB + migrations + backend + frontend) |
| `frontend/` | `npm run dev`   |
| `frontend/` | `npm run lint`  |
| `frontend/` | `npm run build` |
| `backend/`  | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (بعد تفعيل venv وتثبيت المتطلبات) |

لتجميع ملفّ المعاينة عيّن `COMPILER_URL` (مثال `http://localhost:8082`) في بيئة الخلفية وشغّل المترجم المشترك. تصدير LaTeX يتم في الواجهة عبر BuTeX؛ الخلفية Python فقط وتستقبل نص TeX + مفاتيح الصور.

## CORS

الخلفية تسمح حاليًا بأصل التطوير `http://localhost:3000`. عند النشر، حدّث القائمة في `backend/app/main.py` أو استخدم متغيرات بيئة.

## جودة الكود (اختياري لاحقًا)

- **Python:** يمكن إضافة Ruff أو mypy عند توسيع الخلفية.
- **Next:** يشغّل `npm run lint` بعد تغييرات الواجهة.

## الأمان

- لا تُلحق ملفات `.env` الحقيقية أو مفاتيح API بالـ commit.
- تحقق من صلاحيات المسارات والمصادقة قبل تعريض أي بيانات حساسة.
