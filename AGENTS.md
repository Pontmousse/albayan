# AGENTS.md — مجلة البيان (Al-Bayan)

إرشادات للوكلاء/المساعدين الذين يعملون على هذا المستودع.

## الهيكل

- **`frontend/`** — تطبيق **Next.js** (App Router، TypeScript، Tailwind). كل ما يخص الواجهة والتجربة البصرية والتوجيه الأمامي.
- **`backend/`** — تطبيق **Python FastAPI**. واجهة برمجة التطبيقات، التحكيم، النماذج الخادمية، و**قاعدة البيانات** عند إضافتها.

**قاعدة:** لا تضع منطق قاعدة بيانات أو أسرار خادمية داخل `frontend/`. استهلك الـ API من المتصفح عبر `NEXT_PUBLIC_API_URL` (انظر `frontend/.env.example`).

## العربية واتجاه النص

- الجذر في الواجهة: `lang="ar"` و `dir="rtl"` في `frontend/src/app/layout.tsx`.
- فضّل في Tailwind الأدوات المنطقية (`ms-`, `me-`, `ps-`, `pe-`, `start`, `end`) بدلًا من `left`/`right` حيث أمكن.

## أوامر مفيدة

| المجلد    | الأمر           |
| --------- | --------------- |
| جذر المستودع | `./launch.sh` (Docker DB + migrations + backend + frontend) |
| `frontend/` | `npm run dev`   |
| `frontend/` | `npm run lint`  |
| `frontend/` | `npm run build` |
| `backend/`  | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (بعد تفعيل venv وتثبيت المتطلبات) |

## CORS

الخلفية تسمح حاليًا بأصل التطوير `http://localhost:3000`. عند النشر، حدّث القائمة في `backend/app/main.py` أو استخدم متغيرات بيئة.

## جودة الكود (اختياري لاحقًا)

- **Python:** يمكن إضافة Ruff أو mypy عند توسيع الخلفية.
- **Next:** يشغّل `npm run lint` بعد تغييرات الواجهة.

## الأمان

- لا تُلحق ملفات `.env` الحقيقية أو مفاتيح API بالـ commit.
- تحقق من صلاحيات المسارات والمصادقة قبل تعريض أي بيانات حساسة.

## Cursor Cloud specific instructions

The startup update script only refreshes project deps (`backend/.venv` via pip, `frontend` via npm). System deps (PostgreSQL 16, `python3.12-venv`) are baked into the VM snapshot. `./launch.sh` is NOT usable here — it assumes conda, Docker, and a GUI terminal, none of which are present. Start each service manually.

### PostgreSQL (native, not Docker)
- Docker is not installed, so the repo's `backend/database/docker-compose.yml` is not used. Instead a native PostgreSQL 16 cluster runs on host port **5434** (matches the app's default `DATABASE_URL`). Unlike the Docker setup, its storage is on-disk (data + role `albayan_user` + db `albayan` + applied migrations persist in the snapshot).
- Postgres does NOT auto-start on VM boot. Start it: `sudo pg_ctlcluster 16 main start` (verify: `pg_lsclusters`).
- If the role/db are ever missing: `sudo -u postgres psql -p 5434 -c "CREATE ROLE albayan_user LOGIN PASSWORD 'albayan_password';"` then `... -c "CREATE DATABASE albayan OWNER albayan_user;"`, then re-run migrations.

### Backend (FastAPI)
- Activate the venv: `cd backend && . .venv/bin/activate`.
- Apply migrations after a fresh DB: `alembic upgrade head`.
- Run: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (Swagger at `/docs`, `/health`).
- Auth is Clerk-based: without `CLERK_SECRET_KEY` (in `backend/.env`), all authenticated endpoints return HTTP 503 (`المصادقة غير مُهيّأة`). Unauthenticated endpoints (`/`, `/health`, `/docs`) work regardless.

### Frontend (Next.js)
- Run: `cd frontend && npm run dev` (port 3000). Copy `.env.example` → `.env.local`.
- The frontend CANNOT boot without a **real** Clerk publishable key: `clerkMiddleware` runs on nearly all routes, so a missing/placeholder `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` makes even the public homepage return HTTP 500 (`Publishable key not valid`). Set real `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` + `CLERK_SECRET_KEY` (from an external Clerk instance) in `frontend/.env.local` to run any UI/auth flow.
- S3 is optional: only the manuscript document body endpoints (`GET/PUT /api/v1/articles/{id}/document`) need `S3_*` in `backend/.env`; they return 503 otherwise. The rest of the article workflow (create, list, submit) works without S3.
