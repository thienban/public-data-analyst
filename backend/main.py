from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import companies, analysis, dpe, dvf, insee

app = FastAPI(
    title="Public Data Analyst — Intelligence Économique",
    description="Analyse stratégique des secteurs Bâtiment & IT via APIs publiques françaises",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(analysis.router)
app.include_router(dpe.router)
app.include_router(dvf.router)
app.include_router(insee.router)


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
