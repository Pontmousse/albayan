from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import admin, articles, editor, invitations, reviews, users

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
)

app.include_router(users.router)
app.include_router(articles.router)
app.include_router(admin.router)
app.include_router(invitations.router)
app.include_router(reviews.router)
app.include_router(editor.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "albayan-backend",
        "message": "مرحبًا بك في واجهة برمجة تطبيقات مجلة البيان.",
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "status": "healthy"}
