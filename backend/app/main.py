"""FastAPI entry point [Member 2]"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import medicines, companies, sales, actions, alerts

app = FastAPI(title="Pharmacy Shelf")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (medicines, companies, sales, actions, alerts):
    app.include_router(r.router)

@app.get("/")
def root():
    return {"status": "ok"}
