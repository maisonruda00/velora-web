import json
import os

# Load the wine database
def load_wines():
    try:
        with open("wines.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_recommendation(food_input: str, budget: int = 1000):
    wines_data = load_wines()
    # Handle the case where the JSON might be wrapped in a "wines" key or is a direct list
    if isinstance(wines_data, dict) and "wines" in wines_data:
        wines = wines_data["wines"]
    else:
        wines = wines_data

    food_input = food_input.lower()
    
    # 1. MOLECULAR ANALYSIS OF INPUT
    # We map keywords to structural needs
    needs = {
        "acid_boost": False,  # Needed for fat/salt
        "tannin_grip": False, # Needed for red meat
        "sweet_shield": False # Needed for spice/salt
    }
    
    # Simple Keyword Detection (The "Brain")
    # FIX: Corrected "for x in" syntax below
    if any(x in food_input for x in ["steak", "beef", "lamb", "burger", "meat", "ribeye"]):
        needs["tannin_grip"] = True
    if any(x in food_input for x in ["fish", "oyster", "sushi", "salad", "goat", "seafood"]):
        needs["acid_boost"] = True
    if any(x in food_input for x in ["spicy", "thai", "curry", "dessert", "cake"]):
        needs["sweet_shield"] = True
    if any(x in food_input for x in ["cream", "butter", "lobster", "rich", "fatty"]):
        needs["acid_boost"] = True # Acid cuts fat
    
    # 2. SCORING ENGINE
    scored_wines = []
    
    for wine in wines:
        score = 0
        profile = wine.get("profile", {})
        # Fallback if profile is missing (handling different JSON structures)
        if not profile: 
             profile = {
                 "acid": wine.get("acid", 5),
                 "tannin": wine.get("tannin", 5),
                 "body": wine.get("body", 5),
                 "sugar": wine.get("sugar", 1)
             }

        # Budget Filter (Soft filter)
        if wine["price"] > budget * 1.2:
            continue
            
        # -- THE RULES --
        
        # Rule A: Red Meat requires Tannin
        if needs["tannin_grip"]:
            if wine["type"] == "Red" and profile["tannin"] >= 7:
                score += 50
            elif wine["type"] == "White":
                score -= 50 # Penalty
                
        # Rule B: Fat/Oil requires Acid
        if needs["acid_boost"]:
            if profile["acid"] >= 7:
                score += 40
            if profile["body"] >= 7 and "rich" in wine.get("tags", []):
                score += 20 # Body match for rich food
                
        # Rule C: Spice requires Sweetness (or Low Tannin)
        if needs["sweet_shield"]:
            if profile["sugar"] >= 5:
                score += 50
            if profile["tannin"] > 5:
                score -= 30 # Tannin + Spice = Burning sensation
                
        # Tag Matching (Bonus)
        for tag in wine.get("tags", []):
            if tag in food_input:
                score += 15
                
        scored_wines.append({"wine": wine, "score": score})
    
    # 3. SELECT WINNER
    # Sort by score descending
    scored_wines.sort(key=lambda x: x["score"], reverse=True)
    
    if not scored_wines:
        # Fallback if strict filtering removed everything
        return {
            "success": False, 
            "message": "No wines found. Try increasing budget."
        }
        
    best_match = scored_wines[0]["wine"]
    best_profile = best_match.get("profile") or {
        "acid": best_match.get("acid"), 
        "body": best_match.get("body")
    }

    return {
        "success": True,
        "dish": food_input,
        "wine": best_match,
        "reasoning": {
            "chemistry": ["Selected based on molecular matching."],
            "why": best_match.get("why", "A chemically perfect match."),
            "compatibility": f"Score: {scored_wines[0]['score']}"
        }
    }
