"""
VELORA V5.0 - PRODUCTION SERVER
✅ Stable IDs support
✅ Facts database integration
✅ Rate limiting
✅ Menu/Restaurant endpoints
✅ Input validation
✅ Comprehensive error handling
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import V5.0 services
try:
    from pairing_service import generate_progression, load_wines
    logger.info("✅ V5.0 Pairing service imported successfully")
    PAIRING_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ Pairing service import failed: {e}")
    PAIRING_AVAILABLE = False
    def generate_progression(*args, **kwargs):
        return {"success": False, "error": "Pairing service not available"}
    def load_wines():
        return []

# Verify Facts Database
try:
    from facts_database import get_interesting_fact, calculate_rarity_level
    logger.info("✅ Facts database imported successfully")
    FACTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Facts database not available: {e}")
    FACTS_AVAILABLE = False

app = FastAPI(
    title="Velora Digital Sommelier",
    version="5.0.0",
    description="AI-powered wine pairing with stable IDs and facts database"
)

# CORS Configuration
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
# REQUEST MODELS (V5.0 - Enhanced Validation)
# =================================================================

class ProgressionRequest(BaseModel):
    """V5.0: Accepts list of dish names with validation"""
    dishes: List[str]
    bottle_count: int
    budget: int = 1000
    
    @validator('dishes')
    def validate_dishes(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Please select at least one dish')
        if len(v) > 20:
            raise ValueError('Maximum 20 dishes allowed')
        return v
    
    @validator('bottle_count')
    def validate_bottle_count(cls, v):
        if v < 1:
            raise ValueError('Bottle count must be at least 1')
        if v > 10:
            raise ValueError('Maximum 10 bottles allowed')
        return v
    
    @validator('budget')
    def validate_budget(cls, v):
        if v < 100:
            raise ValueError('Minimum budget is $100')
        if v > 50000:
            raise ValueError('Maximum budget is $50,000')
        return v

# =================================================================
# MENU DATA LOADER
# =================================================================

_menu_cache = None
_menu_cache_time = 0
CACHE_TTL = 300  # 5 minutes

def load_menus():
    """Load restaurant menus from menus.json with caching"""
    global _menu_cache, _menu_cache_time
    
    # Check cache
    if _menu_cache and (time.time() - _menu_cache_time < CACHE_TTL):
        return _menu_cache
    
    try:
        menu_files = ['menus.json', 'FINAL_menus_v4.0.json']
        
        for menu_file in menu_files:
            if os.path.exists(menu_file):
                with open(menu_file, "r", encoding='utf-8') as f:
                    menus = json.load(f)
                    _menu_cache = menus
                    _menu_cache_time = time.time()
                    logger.info(f"✅ Loaded menus for {len(menus)} restaurants from {menu_file}")
                    return menus
        
        logger.error("❌ No menu file found")
        return {}
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid menus.json: {e}")
        return {}
    except Exception as e:
        logger.error(f"❌ Error loading menus: {e}")
        return {}

# =================================================================
# ROUTES
# =================================================================

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main frontend"""
    html_files = [
        'concierge_wizard.html',
        'VELORA_V5_QUICK_DEPLOY.html',
        'FINAL_concierge_wizard_v4.0.html'
    ]
    
    for html_file in html_files:
        try:
            if os.path.exists(html_file):
                with open(html_file, "r", encoding='utf-8') as f:
                    logger.info(f"✅ Serving {html_file}")
                    return f.read()
        except Exception as e:
            logger.error(f"❌ Error reading {html_file}: {e}")
            continue
    
    # Fallback error page
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head><title>Velora - Setup Required</title></head>
        <body style="font-family: Arial; padding: 40px; text-align: center;">
            <h1>🍷 Velora Digital Sommelier</h1>
            <p>Frontend file missing. Please ensure one of these files exists:</p>
            <ul style="list-style: none;">
                <li>concierge_wizard.html</li>
                <li>VELORA_V5_QUICK_DEPLOY.html</li>
                <li>FINAL_concierge_wizard_v4.0.html</li>
            </ul>
            <p>Contact support for assistance.</p>
        </body>
        </html>
        """,
        status_code=500
    )

@app.get("/health")
async def health_check():
    """Health check endpoint with service status"""
    # Check wine database
    wines = load_wines()
    
    return {
        "status": "healthy",
        "version": "5.0.0",
        "timestamp": time.time(),
        "services": {
            "pairing": PAIRING_AVAILABLE,
            "facts": FACTS_AVAILABLE,
            "menus": bool(load_menus())
        },
        "stats": {
            "wines_loaded": len(wines) if wines else 0,
            "restaurants": len(load_menus())
        },
        "features": [
            "stable_ids",
            "facts_database",
            "progression",
            "restaurants",
            "menus"
        ]
    }

@app.get("/restaurants")
async def get_restaurants():
    """
    Returns list of available restaurants
    V5.0: Cached for performance
    """
    data = load_menus()
    
    if not data:
        raise HTTPException(
            status_code=503,
            detail="Restaurant data temporarily unavailable. Please try again."
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
    Returns the menu for a specific restaurant
    V5.0: Enhanced error handling
    """
    data = load_menus()
    
    if not data:
        raise HTTPException(
            status_code=503,
            detail="Menu data temporarily unavailable"
        )
    
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
            "cuisine": restaurant.get("cuisine"),
            "price_range": restaurant.get("price_range")
        },
        "menus": restaurant.get("menus", {})
    }

@app.post("/consult/progression")
@limiter.limit("10/minute")
async def progression(request: Request, body: ProgressionRequest):
    """
    V5.0: Multi-dish, multi-bottle pairing with facts and stable IDs
    
    Returns:
    - progression: List of courses with wine options
    - Each wine includes: stable ID, facts, rarity level
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        if not PAIRING_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Pairing service temporarily unavailable"
            )
        
        logger.info(
            f"[{request_id}] Progression request: "
            f"{len(body.dishes)} dishes, {body.bottle_count} bottles, ${body.budget}"
        )
        
        # Call V5.0 progression logic
        result = generate_progression(
            dishes=body.dishes,
            bottle_count=body.bottle_count,
            budget=body.budget
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        if result.get("success"):
            logger.info(
                f"[{request_id}] Success in {elapsed_ms:.0f}ms - "
                f"Generated {len(result.get('progression', []))} courses"
            )
        else:
            logger.warning(
                f"[{request_id}] Pairing failed: {result.get('error', 'Unknown error')}"
            )
        
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        # Validation errors from Pydantic
        logger.warning(f"[{request_id}] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Unable to generate wine pairing. Our sommelier has been notified."
        )

@app.get("/wines/stats")
async def wine_statistics():
    """
    V5.0: Returns statistics about the wine database
    Useful for debugging and monitoring
    """
    try:
        wines = load_wines()
        
        if not wines:
            return {"error": "Wine database not loaded"}
        
        # Calculate statistics
        types = {}
        price_ranges = {"under_100": 0, "100_300": 0, "300_1000": 0, "over_1000": 0}
        
        for wine in wines:
            wine_type = wine.get('type', 'Unknown')
            types[wine_type] = types.get(wine_type, 0) + 1
            
            price = wine.get('price', 0)
            if price < 100:
                price_ranges['under_100'] += 1
            elif price < 300:
                price_ranges['100_300'] += 1
            elif price < 1000:
                price_ranges['300_1000'] += 1
            else:
                price_ranges['over_1000'] += 1
        
        return {
            "total_wines": len(wines),
            "wine_types": types,
            "price_distribution": price_ranges,
            "features": {
                "stable_ids": True,
                "facts_database": FACTS_AVAILABLE
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating wine stats: {e}")
        raise HTTPException(status_code=500, detail="Unable to generate statistics")

# =================================================================
# ERROR HANDLERS
# =================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    logger.error(f"Internal error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Our team has been notified."
        }
    )

# =================================================================
# STARTUP
# =================================================================

@app.on_event("startup")
async def startup_event():
    """Run checks on startup"""
    logger.info("=" * 60)
    logger.info("🍷 VELORA V5.0 DIGITAL SOMMELIER")
    logger.info("=" * 60)
    
    # Check wine database
    wines = load_wines()
    logger.info(f"📊 Wine Database: {len(wines)} wines loaded")
    
    # Check menus
    menus = load_menus()
    logger.info(f"🍽️  Restaurants: {len(menus)} menus loaded")
    
    # Check services
    logger.info(f"✨ Facts Database: {'✅ Available' if FACTS_AVAILABLE else '❌ Not Available'}")
    logger.info(f"🤖 Pairing Service: {'✅ Available' if PAIRING_AVAILABLE else '❌ Not Available'}")
    
    logger.info("=" * 60)
    logger.info("✅ Server ready to accept requests")
    logger.info("=" * 60)

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"🚀 Starting Velora V5.0 on port {port}")
    logger.info(f"📍 Access at: http://localhost:{port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
