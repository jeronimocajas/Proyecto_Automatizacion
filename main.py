from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
from core.config import settings
from core.database import engine, Base
from routers import auth, solicitudes, archivos, admin, convocatorias

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title="Sistema de Auxilios Económicos CECAR",
    description="API para gestión de solicitudes de auxilio económico estudiantil",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,          prefix="/api/auth",          tags=["Autenticación"])
app.include_router(solicitudes.router,   prefix="/api/solicitudes",   tags=["Solicitudes"])
app.include_router(archivos.router,      prefix="/api/archivos",      tags=["Archivos"])
app.include_router(admin.router,         prefix="/api/admin",         tags=["Administración"])
app.include_router(convocatorias.router, prefix="/api/convocatorias", tags=["Convocatorias"])

# Archivos estáticos (css y js)
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")

# Páginas HTML
@app.get("/")
async def index():
    return FileResponse("index.html")

@app.get("/admin.html")
async def admin_page():
    return FileResponse("admin.html")

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
