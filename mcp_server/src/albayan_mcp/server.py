from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from pydantic import AnyHttpUrl

from albayan_mcp.call_logging import McpCallLoggingMiddleware
from albayan_mcp.settings import settings
from albayan_mcp.token_verifier import PassThroughTokenVerifier
from albayan_mcp.tools.assets import register_asset_tools
from albayan_mcp.tools.articles import register_article_tools
from albayan_mcp.tools.profile import register_profile_tools
from albayan_mcp.tools.drafts import register_draft_tools


def create_server() -> MCPServer:
    auth = None
    token_verifier = None

    if settings.oauth_enabled:
        from mcp.server.auth.settings import AuthSettings

        # طبقة MCP OAuth تستخدم نطاقات هوية Clerk القياسية فقط؛
        # صلاحيات التطبيق (profile:read وغيرها) تُفرض في FastAPI.
        # openid مطلوب: ChatGPT يطلبه دائماً عند authorize، وClerk يرفض
        # أي نطاق لم يُسجَّل به العميل عبر DCR (invalid_scope).
        auth = AuthSettings(
            issuer_url=AnyHttpUrl(settings.clerk_issuer_url),
            resource_server_url=AnyHttpUrl(settings.mcp_resource_url),
            required_scopes=["openid", "profile", "email"],
        )
        token_verifier = PassThroughTokenVerifier()

    server = MCPServer(
        "albayan",
        title="مجلة البيان",
        instructions=(
            "خادم MCP لمجلة البيان. يستدعي واجهة FastAPI فقط — "
            "المصادقة والتفويض والمراجعات والحفظ على الخادم الخلفي. "
            "قبل تحرير المقال افحص outline للتنقل أو blocks للهويات الدقيقة، ولا تخترع "
            "معرّفات الكتل أو الحقول أو الرموز أو القوائم أو الجداول. استخدم أحدث revision "
            "كـ base_revision، وعند revision_conflict أعد قراءة المسودة قبل المحاولة. "
            "خصّص command_id واحدًا لكل تعديل منطقي ولا تعِد استخدامه لحمولة مختلفة. "
            "فضّل أمر Document2 موجهاً على إنشاء مستند خام كامل. لا تستدع compile_draft "
            "إلا بطلب صريح؛ فهو ينشئ المعاينة من المراجعة الموثوقة على الخادم، دون إنشاء "
            "LaTeX أو مفاتيح أصول أو hash. افحص get_compile_status قبل طلب PDF. "
            "للصور، استخدم list_article_assets قبل الاسترجاع، وارفع فقط ملفاً "
            "اختاره المستخدم. بعد الرفع مرّر asset_id العائد إلى "
            "insert_figure أو update_figure، ولا تخترع مسار أصل. "
            "يمكن إنشاء المسودات وتحديث عنوانها وملخصها عبر "
            "أدوات المقال المخصصة؛ لا تعدّل authors داخل Document2، ولا توجد أداة تقديم "
            "أو حذف أو إدارة مؤلفين."
            " يستطيع المؤلف البشري مراجعة سجل المسودة واستعادة لقطة سابقة من الواجهة؛ "
            "لا توجد أداة استعادة للوكيل، وتبقى تعديلاته ظاهرة في السجل مع مصدرها."
            " أدوات المسودة متاحة أيضاً أثناء حالة revision_requested كي يساعد الوكيل "
            "في التعديل، لكن طلب التعديلات وإعادة التقديم والقرارات وكشف هويات المراجعين "
            "تبقى عمليات بشرية فقط."
        ),
        auth=auth,
        token_verifier=token_verifier,
        middleware=[McpCallLoggingMiddleware()],
    )

    # Tool implementations belong under tools/; keep this module composition-only.
    register_profile_tools(server)
    register_article_tools(server)
    register_draft_tools(server)
    register_asset_tools(server)

    return server
