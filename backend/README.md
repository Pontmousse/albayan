# خادم «البيان» (FastAPI)

واجهة برمجة التطبيقات لمجلة **البيان** — FastAPI مع PostgreSQL ومصادقة Clerk.

## المتطلبات

- Python **3.11** أو أحدث
- Docker (لقاعدة PostgreSQL المحلية)

## قاعدة البيانات المحلية (Docker)

من مجلد `backend/database/`:

```bash
docker compose up -d
docker compose ps   # التحقق من healthcheck
```

- المنفذ الافتراضي على المضيف: **5434** (لتجنب التعارض مع مشاريع أخرى على 5433)
- البيانات في `tmpfs` — تُمسح عند إيقاف الحاوية

انسخ `backend/.env.example` إلى `backend/.env` وعدّل `DATABASE_URL` و`CLERK_SECRET_KEY`.

## الإعداد والتشغيل (تطوير)

من مجلد `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- التوثيق التفاعلي (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- فحص الصحة: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## مسارات API الرئيسية

| Method | Path | الوصف |
|--------|------|--------|
| `GET` | `/api/v1/users/me` | الملف الشخصي (يتطلّب Bearer token من Clerk) |
| `PATCH` | `/api/v1/users/me` | تحديث الاسم والانتماء والنبذة |

## قاعدة البيانات

الجداول: `users`, `articles`, `article_versions`, `article_authors`, `article_reviewers`, `reviews`.

**حالة المخطوطة** على `article_versions.status` (وليس `articles`): `draft` = قابل للتحرير؛ غير ذلك = مجمّد. آخر إصدار (`ORDER BY version_number DESC LIMIT 1`) هو مصدر الحقيقة.

الشرح الكامل للتصميم والعلاقات: [documentation/database-schema.md](../documentation/database-schema.md).

## ترحيلات Alembic

```bash
alembic revision --autogenerate -m "وصف التغيير"
alembic upgrade head
```
