"""
VELORA FASTAPI APPLICATION (PRODUCTION-GRADE)
✅ Rate limiting enabled (10/minute)
✅ Comprehensive error handling
✅ Request logging with IDs
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
import time
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services safely
try:
    from auth_service import verify_access_code
    from pairing_service import get_recommendation
    logger.info("✅ Services imported successfully")
except ImportError as e:
    logger.error(f"❌ Service import failed: {e}")

# Initialize FastAPI
app = FastAPI(
    title="Velora - Molecular Wine Pairing",
    description="Professional wine pairing using molecular chemistry",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting (CRITICAL for production)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request Models
class LoginRequest(BaseModel):
    code: str

class ConsultRequest(BaseModel):
    food_input: str 
    budget: int = 1000

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("concierge_wizard.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error("Frontend file not found")
        return HTMLResponse(
            content="<h1>Velora</h1><p>System initializing...</p>",
            status_code=503
        )

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": time.time()
    }

@app.post("/login")
async def login(req: LoginRequest):
    try:
        return verify_access_code(req.code)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Authentication unavailable"}
        )

@app.post("/consult")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
async def consult(request: Request, body: ConsultRequest):
    """
    Get wine recommendation with rate limiting and error handling.
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]  # Short ID for logging
    
    try:
        # Validate input
        if not body.food_input or len(body.food_input) > 500:
            raise HTTPException(status_code=400, detail="Invalid food input")
        
        if body.budget < 0 or body.budget > 100000:
            raise HTTPException(status_code=400, detail="Invalid budget")
        
        logger.info(f"[{request_id}] Request: {body.food_input} @ ${body.budget}")
        
        # Get recommendation
        result = get_recommendation(
            food_input=body.food_input,
            budget=body.budget
        )
        
        # Log success
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"[{request_id}] Success in {elapsed_ms:.0f}ms")
        
        return result
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        # Log error with details
        logger.error(
            f"[{request_id}] Error: {type(e).__name__}: {e}",
            exc_info=True
        )
        
        # Return graceful error to user
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Unable to generate recommendation. Please try again.",
                "request_id": request_id
            }
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Velora...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        log_level="info"
    )
