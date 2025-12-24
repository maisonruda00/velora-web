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
    wines = load_wines()
    food_input = food_input.lower()
    
    # 1. MOLECULAR ANALYSIS OF INPUT
    # We map keywords to structural needs
    needs = {
        "acid_boost": False,  # Needed for fat/salt
        "tannin_grip": False, # Needed for red meat
        "sweet_shield": False # Needed for spice/salt
    }
    
    # Simple Keyword Detection (The "Brain")
    if any(x in food_input for in ["steak", "beef", "lamb", "burger", "meat"]):
        needs["tannin_grip"] = True
    if any(x in food_input for in ["fish", "oyster", "sushi", "salad", "goat"]):
        needs["acid_boost"] = True
    if any(x in food_input for in ["spicy", "thai", "curry", "dessert"]):
        needs["sweet_shield"] = True
    if any(x in food_input for in ["cream", "butter", "lobster", "rich"]):
        needs["acid_boost"] = True # Acid cuts fat
    
    # 2. SCORING ENGINE
    scored_wines = []
    
    for wine in wines:
        score = 0
        profile = wine["profile"]
        
        # Budget Filter (Soft filter)
        if wine["price"] > budget * 1.2:
            continue
            
        # -- THE RULES --
        
        # Rule A: Red Meat requires Tannin
        if needs["tannin_grip"]:
            if wine["type"] == "red" and profile["tannin"] >= 7:
                score += 50
            elif wine["type"] == "white":
                score -= 50 # Penalty
                
        # Rule B: Fat/Oil requires Acid
        if needs["acid_boost"]:
            if profile["acid"] >= 7:
                score += 40
            if profile["body"] >= 7 and "rich" in wine["tags"]:
                score += 20 # Body match for rich food
                
        # Rule C: Spice requires Sweetness (or Low Tannin)
        if needs["sweet_shield"]:
            if profile["sugar"] >= 5:
                score += 50
            if profile["tannin"] > 5:
                score -= 30 # Tannin + Spice = Burning sensation
                
        # Tag Matching (Bonus)
        for tag in wine["tags"]:
            if tag in food_input:
                score += 15
                
        scored_wines.append({"wine": wine, "score": score})
    
    # 3. SELECT WINNER
    # Sort by score descending
    scored_wines.sort(key=lambda x: x["score"], reverse=True)
    
    if not scored_wines:
        return {"error": "No matches found in cellar."}
        
    best_match = scored_wines[0]["wine"]
    
    return {
        "wine": best_match["name"],
        "producer": best_match["producer"],
        "price": best_match["price"],
        "note": f"Selected for its {best_match['profile']['body']}/10 body and {best_match['profile']['acid']}/10 acidity, creating a perfect structural bridge.",
        "match_score": scored_wines[0]["score"]
    }
