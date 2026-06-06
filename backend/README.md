# خادم «البيان» (FastAPI)

هيكل أولي لواجهة برمجة التطبيقات لمجلة **البيان**. منطق قاعدة البيانات والمصادقة يُضاف لاحقًا في هذا المجلد وليس في تطبيق Next.js.

## المتطلبات

- Python **3.11** أو أحدث

## الإعداد والتشغيل (تطوير)

من مجلد `backend/`:

```bash
python -m venv .venv
```

تفعيل البيئة الافتراضية:

- Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

ثم:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- التوثيق التفاعلي (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- فحص الصحة: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## ما يُضاف لاحقًا

- طبقة **قاعدة بيانات** (مثل PostgreSQL) و**ORM** (مثل SQLAlchemy 2.0) وترحيلات **Alembic**
- **المصادقة** والتفويض للمحررين والمحكمين
- مخططات **Pydantic** ومسارات منظمة تحت `app/routers/`
