from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    admin,
    admin_mcp,
    agent_tokens,
    articles,
    donations,
    draft_equations,
    draft_references,
    editor,
    equation_mappings,
    invitations,
    issues,
    mcp_logs,
    notifications,
    public,
    revision_summaries,
    reviews,
    users,
    webhooks,
)

app = FastAPI(
    title="البيان API",
    description="واجهة برمجة تطبيقات مجلة البيان العلمية (هيكل أولي للتطوير).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(public.router)
app.include_router(donations.router)
app.include_router(users.router)
app.include_router(webhooks.router)
app.include_router(agent_tokens.router)
app.include_router(articles.router)
app.include_router(draft_equations.router)
app.include_router(draft_references.router)
app.include_router(equation_mappings.router)
app.include_router(revision_summaries.router)
app.include_router(admin.router)
app.include_router(admin_mcp.router)
app.include_router(mcp_logs.router)
app.include_router(invitations.router)
app.include_router(reviews.router)
app.include_router(editor.router)
app.include_router(notifications.router)
app.include_router(issues.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "albayan-backend",
        "message": "مرحبًا بك في واجهة برمجة تطبيقات مجلة البيان.",
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "status": "healthy"}
