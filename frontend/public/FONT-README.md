# خط المغربي (وَرْش)

الواجهة تتوقع ملف الخط تحت المسار التالي (كما في `src/app/globals.css`):

- `public/Almaghribi-warch.ttf`

إذا كان اسم ملفك مختلفًا أو الامتداد `.otf`، إمّا:

1. انسخ الملف إلى `frontend/public/` وسمّه بالضبط `Almaghribi-warch.ttf`، أو  
2. عدّل السطر `src` داخل `@font-face` في `src/app/globals.css` ليطابق اسم الملف الفعلي.

بدون الملف سيظهر في الطرفية: `GET /Almaghribi-warch.ttf 404` (وهذا طبيعي حتى تضع الخط).
