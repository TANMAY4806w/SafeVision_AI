"""
SafeVision AI — Main Application Entrypoint.
Runs the FastAPI edge microservice with real-time RTSP video streaming,
PPE detection, virtual geofencing, and GenAI OSHA auditing.
"""

import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api.routes import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SafeVision.Main")

# Initialize FastAPI app
app = FastAPI(
    title="SafeVision AI — Industrial Safety & Edge Video Analytics",
    description="Real-Time CCTV PPE Detection, Virtual Polygon Geofencing, and GenAI OSHA Compliance Auditing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for browser dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root():
    """Redirects root URL directly to Swagger API documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting SafeVision AI service on http://{host}:{port}...")
    uvicorn.run("main:app", host=host, port=port, reload=False)
