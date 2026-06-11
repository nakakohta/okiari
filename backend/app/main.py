from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.supabase_client import supabase

app = FastAPI()


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