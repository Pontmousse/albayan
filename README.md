# البيان — منصة مجلة علمية عربية

البيان منصة لنشر الأبحاث العلمية باللغة العربية. يجمع هذا المستودع واجهة **Next.js**، وخادم **FastAPI**، وأدوات **MCP** للمساعدة في التأليف العلمي. تُحرَّر المقالات عبر مستندات **BuTeX Document2** المنظمة؛ وتُنشئ تعديلات المسودات مراجعات غير قابلة للتعديل.

> **حالة المشروع:** يصف هذا الملف ما هو موجود في فرع `develop`. دعم **تأليف الكتب** وإعادة تسمية محرر **BuTeX Document2** مقترحان قيد التصميم، وليسا ميزتين منفذتين.

## ابدأ من هنا

| الجزء | التقنية | الموقع |
| --- | --- | --- |
| الواجهة | Next.js / React / TypeScript | [`frontend/`](frontend/) |
| الخادم | FastAPI / SQLAlchemy / PostgreSQL | [`backend/`](backend/) |
| واجهة الوكلاء للمستخدمين | MCP فوق FastAPI | [`mcp_server/`](mcp_server/) |
| تشخيص بيئة التطوير | Developer MCP مستقل | [`dev_mcp_server/`](dev_mcp_server/) |
| وصف البنية | وثائق المعمارية الحالية | [`docs/architecture/`](docs/architecture/README.md) |

**المتطلبات المحلية:** Node.js LTS وPython 3.11+ وDocker لتشغيل PostgreSQL. يتطلب مسار `./launch.sh` وجود conda وبيئة Python مناسبة؛ ويمكن تشغيل الواجهة والخلفية يدويًا بدلاً منه.

### تشغيل سريع (باستخدام conda)

1. جهّز ملفات الإعداد المحلية من ملفات `.env.example` في `frontend/` و`backend/`، واضبط خدمة Clerk وقاعدة البيانات والخدمات اللازمة. لا تضع مفاتيح حقيقية في Git.
2. تأكد من إعداد بيئة conda وتبعيات الواجهة والخلفية.
3. من جذر المستودع شغّل:

```bash
./launch.sh
# اسم البيئة الافتراضي: my_env1
# أو CONDA_ENV_NAME=your_env ./launch.sh
```

يشغّل السكربت PostgreSQL المحلية عبر Docker (المنفذ 5434 افتراضيًا)، ويطبّق ترحيلات Alembic، ثم يشغّل FastAPI وNext.js.

### تشغيل يدوي

من جذر المستودع، شغّل قاعدة البيانات أولاً:

```bash
cd backend/database
docker compose up -d
```

ثم الخلفية (في طرفية منفصلة):

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ثم الواجهة (في طرفية منفصلة):

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

- الواجهة: <http://localhost:3000>
- توثيق API التفاعلي: <http://localhost:8000/docs>
- فحص صحة الخادم: <http://localhost:8000/health>

عدّل إعدادات البيئة قبل التشغيل، ولا سيما `DATABASE_URL` وبيانات Clerk و`NEXT_PUBLIC_API_URL`. تتطلب بعض الوظائف خدمات خارجية مهيّأة (BuTeX worker وBurhan والتجميع وتخزين الملفات)، وقد لا تعمل دونها. لمزيد من تفاصيل الخلفية راجع [دليلها](backend/README.md).

## الوثائق

تنظيم الوثائق في أربعة أقسام: [المعمارية](docs/architecture/README.md)، [التطوير](docs/development/README.md)، [المقترحات](docs/proposals/README.md)، و[الأرشيف التاريخي](docs/archive/README.md). يمكنك البدء من [فهرس الوثائق](docs/README.md).

### المعمارية

ابدأ من [فهرس المعمارية](docs/architecture/README.md)، ثم اختر الجزء الذي تريد فهمه:

- [حدود النظام وتدفق الطلبات](docs/architecture/system.md)
- [واجهة المستخدم ومحرر المقالات](docs/architecture/frontend.md)
- [FastAPI والبيانات والصلاحيات](docs/architecture/backend.md)
- [المسودات والمراجعات والتحكيم](docs/architecture/authoring.md)
- [المعادلات: البيان ↔ برهان ↔ BuTeX](docs/architecture/equations.md)
- [MCP للمستخدمين وDeveloper MCP للتشخيص](docs/architecture/mcp.md)

## المقترحات النشطة (غير منفذة)

هذه مستندات تصميم، **وليست** وصفًا لميزات متاحة حالياً:

- [توحيد أسماء محرر BuTeX وإزالة الأسماء/الواجهات القديمة](docs/proposals/butex-document2-naming.md).
- [تأليف الكتب في البيان](docs/proposals/book-authoring.md) و[التصميم المقابل في BuTeX](https://gitlab.com/drghaliasri/butex/-/blob/develop/docs/book-editor-plan.md).

ما زالت بعض المستندات القديمة موجودة خارج الأقسام الأربعة خلال الانتقال التدريجي. يوجّه فهرس الوثائق إلى المصادر المعتمدة. **لا تُعدّ الملفات القديمة مرجعاً أعلى من الشيفرة أو وثائق المعمارية الجديدة** عند تعارض الوصف مع التنفيذ.

## المساهمة

تبدأ تغييرات التطوير والتوثيق من `develop`، وتُفتح PRs إليه لا إلى `main`. انظر [`AGENTS.md`](AGENTS.md) لإرشادات المساهمين والوكلاء. هذه المرحلة توثيقية فقط: لا تغييرات على التطبيق أو قاعدة البيانات أو الخدمات أو إعدادات CI.
