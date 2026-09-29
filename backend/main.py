from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
import os

from backend.database import init_db
from backend.routers import (
    institutions,
    buildings,
    parcels,
    rights,
    encumbrances,
    topology,
    analytics,
    ingestion,
    ai_pipeline
)

app = FastAPI(
    title="National 3D ULPIN & Volumetric Cadastre Platform",
    description="Department of Land Resources (DoLR) | Ministry of Rural Development, Government of India. "
                "Enterprise ISO 19152 LADM v2 Multi-Building 3D Cadastral REST API & Spatial Registry.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for open frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(institutions.router)
app.include_router(buildings.router)
app.include_router(parcels.router)
app.include_router(rights.router)
app.include_router(encumbrances.router)
app.include_router(topology.router)
app.include_router(analytics.router)
app.include_router(ingestion.router)
app.include_router(ai_pipeline.router, prefix="/api/ai", tags=["AI Pipeline"])


# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/app")

@app.get("/app", include_in_schema=False)
def app_view():
    app_html = os.path.join(frontend_dir, "app.html")
    if os.path.exists(app_html):
        return FileResponse(app_html)
    return RedirectResponse(url="/studio")

@app.get("/studio", include_in_schema=False)
@app.get("/floorplan-studio", include_in_schema=False)
def floorplan_studio_view():
    studio_html = os.path.join(frontend_dir, "floorplan_3d_studio.html")
    if os.path.exists(studio_html):
        return FileResponse(
            studio_html,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return RedirectResponse(url="/app")

@app.get("/health", tags=["System Health"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": "3D ULPIN Cadastral Engine",
        "version": "2.0.0",
        "cadastral_standard": "ISO 19152 LADM v2"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8005))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
