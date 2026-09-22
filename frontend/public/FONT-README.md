# خطوط معاينة رموز المعادلات

تعتمد معاينة الخطوط في واجهة اختيار رموز المعادلات على خطوط BuTeX v7.1.0 المضمّنة داخل الحزمة نفسها.

يستدعي المكوّن `injectBuTeXStyles()` من `@drghaliasri/butex`، وهو يضيف تعريفات `@font-face` المضمّنة كـ data URLs للخطوط الأربعة:

- تكوين — `BuTeX Takween`
- ديواني — `Diwani Letter`
- ديواني مزخرف — `BuTeX Diwani Outline`
- مغربي — `Almaghribi Warsh Quran`

لذلك لا نحتفظ بنسخ ثانية من ملفات الخطوط داخل `frontend/public/`، وتبقى المعاينة متزامنة مع نسخة BuTeX التي يستخدمها التطبيق.

أما القيم المحفوظة فتستخدم أوامر BuTeX القياسية:

- `\\text{...}` — الافتراضي
- `\\butextakween{...}` — تكوين
- `\\butexdiwani{...}` — ديواني
- `\\butexdiwanioutline{...}` — ديواني مزخرف
- `\\butexmaghribi{...}` — مغربي
- قيمة خام بلا تغليف — للحالات المتقدمة
