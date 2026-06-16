from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.routers import auth, roles, users
from app.supabase_client import supabase

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)


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
