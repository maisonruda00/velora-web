from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

# Import your existing services
from auth_service import verify_access_code
from db_client import db

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    code: str

# 1. SERVE THE HTML FRONTEND
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves your Concierge Wizard HTML"""
    # We assume the file is in the root directory
    with open("concierge_wizard.html", "r") as f:
        return f.read()

# 2. CONNECT THE LOGIN BUTTON
@app.post("/login")
async def login(request: LoginRequest):
    """Connects the frontend login button to your auth_service.py"""
    result = verify_access_code(request.code)
    
    if result["status"] == "success":
        return result
    else:
        return JSONResponse(status_code=401, content=result)

# 3. SERVE THE APP ICON (PWA)
@app.get("/manifest.json")
async def get_manifest():
    with open("manifest.json", "r") as f:
        return JSONResponse(content=eval(f.read()))

# 4. AUTO-CREATE GENESIS KEY (Since Supabase isn't ready)
@app.on_event("startup")
async def startup_event():
    if db.mode == "json":
        # Check if the founder key exists, if not, create it
        founder = db.get_user_by_code("GENESIS_KEY")
        if not founder:
            print("🌱 JSON Mode: Automatically seeding 'GENESIS_KEY' for you.")
            db.create_user(access_code="GENESIS_KEY", invites_remaining=1000, role="admin")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
# --- ADD THIS TO MAIN.PY ---
from pairing_service import get_recommendation

class ConsultRequest(BaseModel):
    food: str
    budget: int

@app.post("/consult")
async def consult(request: ConsultRequest):
    """The Brain Endpoint"""
    result = get_recommendation(request.food, request.budget)
    return result
