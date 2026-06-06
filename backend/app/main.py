from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="البيان API",
    description="واجهة برمجة تطبيقات مجلة البيان العلمية (هيكل أولي للتطوير).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "albayan-backend",
        "message": "مرحبًا بك في واجهة برمجة تطبيقات مجلة البيان.",
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "status": "healthy"}
