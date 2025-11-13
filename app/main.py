"""
Resume Improvement API - FastAPI Application
Provides resume analysis, scoring, AI-powered improvements, and PDF generation
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import logging
from contextlib import asynccontextmanager

# Import routers
from app.routers import analyze, improve, generate, templates
from app.utils.config import get_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
settings = get_settings()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute", f"{settings.RATE_LIMIT_PER_HOUR}/hour"],
    storage_uri="memory://",  # Use Redis in production: redis://localhost:6379
    strategy="fixed-window"
)
logger.info(f"Rate limiting enabled: {settings.RATE_LIMIT_PER_MINUTE}/min, {settings.RATE_LIMIT_PER_HOUR}/hour")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Resume Improvement API starting up...")
    # Load NLP models, initialize services, etc.
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        app.state.nlp = nlp
        logger.info("✅ spaCy model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load spaCy model: {e}")
        app.state.nlp = None

    yield

    # Shutdown
    logger.info("🛑 Resume Improvement API shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Resume Improvement API",
    description="AI-powered resume analysis, scoring, and improvement service",
    version="1.0.0",
    lifespan=lifespan
)

# Attach rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware - use environment variables
cors_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else settings.CORS_ORIGINS.split(",")
logger.info(f"CORS enabled for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )

# Include routers
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["Analysis"])
app.include_router(improve.router, prefix="/api/v1/improve", tags=["Improvement"])
app.include_router(generate.router, prefix="/api/v1/generate", tags=["Generation"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Resume Improvement API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "analyze": "/api/v1/analyze",
            "improve": "/api/v1/improve",
            "generate": "/api/v1/generate",
            "templates": "/api/v1/templates",
            "health": "/health",
            "docs": "/docs"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "nlp": app.state.nlp is not None
        }
    }

# Readiness check
@app.get("/ready")
async def readiness_check():
    """Readiness check for load balancers"""
    if app.state.nlp is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "reason": "NLP model not loaded"}
        )
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
