# Al-Bayan monorepo

مجلة علمية عربية — واجهة **Next.js** في `frontend/` وخادم **FastAPI** في `backend/`.

## المتطلبات

| جزء       | المتطلب        |
| --------- | -------------- |
| الواجهة   | Node.js (LTS)  |
| الخلفية   | Python 3.11+ (conda موصى به) |
| قاعدة البيانات (تطوير) | Docker |

## التشغيل السريع (كل الخدمات)

من جذر المستودع، بعد إعداد conda وملفات `.env`:

```bash
./launch.sh
```

يفتح السكربت:

1. PostgreSQL عبر Docker (`backend/database`, منفذ **5434** افتراضيًا)
2. ترحيلات Alembic
3. الخلفية FastAPI في طرفية منفصلة (conda)
4. الواجهة Next.js في طرفية منفصلة

متغير اختياري: `CONDA_ENV_NAME=my_env1 ./launch.sh` لتغيير اسم بيئة conda (الافتراضي: `my_env1`).

### الواجهة (Next.js) — يدويًا

```bash
cd frontend
npm install
npm run dev
```

التطبيق المحلي: [http://localhost:3000](http://localhost:3000)

انسخ `frontend/.env.example` إلى `frontend/.env.local` وعدّل `NEXT_PUBLIC_API_URL` عند الحاجة (افتراضيًا `http://localhost:8000`).

### الخلفية (FastAPI)

راجع تعليمات التثبيت والتشغيل في [backend/README.md](backend/README.md).

باختصار:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- التوثيق: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- الصحة: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## هيكل المستودع

- `frontend/` — واجهة المستخدم (App Router، عربي/RTL).
- `backend/` — واجهة برمجة التطبيقات والمنطق الخادمي وقاعدة البيانات.
- `documentation/` — توثيق التصميم؛ راجع [database-schema.md](documentation/database-schema.md) لمخطط PostgreSQL.

## Docker

غير مضمّن في الإصدار الأول؛ يمكن إضافة صور منفصلة للواجهة والخلفية لاحقًا.

## استكشاف أخطاء الواجهة (Next)

### `Cannot find module './239.js'` (أو أرقام مشابهة) من مجلد `.next`

غالبًا بسبب **كاش بناء تالف** أثناء `npm run dev` بعد تغييرات كثيرة أو إيقاف غير نظيف.

1. أوقف الخادم (`Ctrl+C`).
2. من مجلد `frontend/` شغّل:

```bash
npm run clean
npm run dev
```

أو مرة واحدة: `npm run dev:clean`

### `GET /Almaghribi-warch.ttf 404`

الخط غير موجود في `frontend/public/` بالاسم المتوقع. راجع [frontend/public/FONT-README.md](frontend/public/FONT-README.md).

### `GET /sw.js 404`

طلب من المتصفح أو إضافة؛ غالبًا غير ضار. إذا تكرر مع أخطاء أخرى، جرّب مسح بيانات الموقع للـ localhost أو إغلاق تبويب قديم بعد `npm run clean`.
