"""
VELORA V2.0 - PRODUCTION SERVER (GEMINI INTEGRATION FIX)
✅ Rate Limiting
✅ Menu/Restaurant Endpoints  
✅ Progression Logic (Properly Integrated)
✅ All endpoints working
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional
import os
import json
import logging
import time
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import services
try:
    from pairing_service import get_recommendation, generate_progression
    logger.info("✅ Pairing service imported successfully")
except ImportError as e:
    logger.error(f"❌ Service import failed: {e}")
    # Define fallback functions
    def get_recommendation(*args, **kwargs):
        return {"success": False, "error": "Pairing service not available"}
    def generate_progression(*args, **kwargs):
        return {"success": False, "error": "Progression service not available"}

app = FastAPI(title="Velora Digital Sommelier", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# =================================================================
# REQUEST MODELS
# =================================================================

class ConsultRequest(BaseModel):
    food_input: str 
    budget: int = 1000

class ProgressionRequest(BaseModel):
    dishes: List[str]
    bottle_count: int
    budget: int = 1000

# =================================================================
# MENU DATA LOADER
# =================================================================

def load_menus():
    """Load restaurant menus from menus.json"""
    try:
        with open("menus.json", "r", encoding='utf-8') as f:
            menus = json.load(f)
            logger.info(f"✅ Loaded menus for {len(menus)} restaurants")
            return menus
    except FileNotFoundError:
        logger.error("❌ menus.json not found")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid menus.json: {e}")
        return {}

# =================================================================
# ROUTES
# =================================================================

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main frontend"""
    try:
        with open("concierge_wizard.html", "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error("❌ concierge_wizard.html not found")
        return HTMLResponse(
            content="<h1>Velora</h1><p>Frontend file missing. Please contact support.</p>",
            status_code=500
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": ["progression", "restaurants", "menus"]
    }

@app.get("/restaurants")
async def get_restaurants():
    """
    Returns list of available restaurants.
    NEW in V2.0
    """
    data = load_menus()
    
    if not data:
        return JSONResponse(
            status_code=503,
            content={"error": "Restaurant data unavailable"}
        )
    
    restaurants = []
    for key, val in data.items():
        restaurants.append({
            "id": val.get("id", key),
            "name": val.get("name", "Unknown"),
            "location": val.get("location", ""),
            "cuisine": val.get("cuisine", ""),
            "price_range": val.get("price_range", "$$$")
        })
    
    logger.info(f"✅ Returning {len(restaurants)} restaurants")
    return {"restaurants": restaurants}

@app.get("/restaurant/{restaurant_id}/menu")
async def get_menu(restaurant_id: str):
    """
    Returns the menu for a specific restaurant.
    NEW in V2.0
    """
    data = load_menus()
    
    if restaurant_id not in data:
        logger.warning(f"⚠️ Restaurant not found: {restaurant_id}")
        raise HTTPException(
            status_code=404, 
            detail=f"Restaurant '{restaurant_id}' not found"
        )
    
    restaurant = data[restaurant_id]
    logger.info(f"✅ Returning menu for {restaurant.get('name')}")
    
    return {
        "restaurant": {
            "id": restaurant_id,
            "name": restaurant.get("name"),
            "location": restaurant.get("location"),
            "cuisine": restaurant.get("cuisine")
        },
        "menus": restaurant.get("menus", {})
    }

@app.post("/consult")
@limiter.limit("10/minute")
async def consult(request: Request, body: ConsultRequest):
    """
    Single dish consultation (V1.0 compatible).
    Uses existing pairing logic.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        logger.info(f"[{request_id}] Consult: {body.food_input}, budget: ${body.budget}")
        
        result = get_recommendation(
            food_input=body.food_input, 
            budget=body.budget
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"[{request_id}] Success in {elapsed_ms:.0f}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"[{request_id}] Consult error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={
                "success": False,
                "error": "Unable to generate recommendation. Please try again.",
                "request_id": request_id
            }
        )

@app.post("/consult/progression")
@limiter.limit("5/minute")
async def progression(request: Request, body: ProgressionRequest):
    """
    Table progression consultation (V2.0).
    NEW: Multi-dish, multi-bottle pairing.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        # Validate input
        if not body.dishes or len(body.dishes) == 0:
            raise HTTPException(
                status_code=400,
                detail="No dishes selected. Please select at least one dish."
            )
        
        if body.bottle_count < 1 or body.bottle_count > 3:
            raise HTTPException(
                status_code=400,
                detail="Bottle count must be between 1 and 3"
            )
        
        logger.info(
            f"[{request_id}] Progression: {len(body.dishes)} dishes, "
            f"{body.bottle_count} bottles, ${body.budget}"
        )
        
        # Call progression logic
        result = generate_progression(
            dishes=body.dishes,
            bottle_count=body.bottle_count,
            budget=body.budget
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"[{request_id}] Progression success in {elapsed_ms:.0f}ms")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Progression error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Unable to generate wine progression. Please try again.",
                "request_id": request_id
            }
        )

# =================================================================
# STARTUP
# =================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting Velora v2.0 on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
