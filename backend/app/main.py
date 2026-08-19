import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.routers import auth, collaborative, live_collaboration, masters, reports, roles, users
from app.supabase_client import supabase

app = FastAPI()


def _cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "")
    origins = [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]
    return origins or ["http://localhost:5173", "http://127.0.0.1:5173"]


# 開発用LANの共有ホストを許可する。認証・編集権限は各API/WebSocket側で別途検証する。
DEFAULT_CORS_ORIGIN_REGEX = (
    r"^https?://(?:localhost|127(?:\.\d{1,3}){3}|10(?:\.\d{1,3}){3}|"
    r"192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})"
    r"(?::\d+)?$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX") or DEFAULT_CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(masters.router)
app.include_router(reports.router)
app.include_router(live_collaboration.router)
app.include_router(collaborative.router)


@app.get("/")
def read_root():
    return {"message": "FastAPI is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/test-reports")
def get_test_reports():
    response = supabase.table("test_reports").select("*").execute()
    return response.data
