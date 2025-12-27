"""
VELORA PAIRING SERVICE - V3.2 FINAL MERGE
✅ FIX: Added total_cost and budget_utilization (Claude's Finding)
✅ LOGIC: Uses divmod grouping to prevent "1 Bottle" bug (Gemini's Fix)
✅ BUDGET: Uses tiered fallback to prevent "Zero Results" (Gemini's Fix)
"""
import csv
import os
import statistics
import math
from typing import List, Dict, Tuple
from functools import lru_cache

# Import Luxury Modules
try:
    from sommelier_narrator import narrator
    from conversation_starter import generate_conversation_starters
    LUXURY_MODE = True
except ImportError:
    LUXURY_MODE = False

# =================================================================
# 1. DATABASE LOADER
# =================================================================
_wine_cache = None

def load_wines() -> List[Dict]:
    global _wine_cache
    if _wine_cache: return _wine_cache
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(script_dir, 'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv'),
        'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv'
    ]
    
    for path in paths:
        if os.path.exists(path):
            try:
                wines = []
                with open(path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if not row.get('price') or not row.get('wine_name'): continue
                        wines.append({
                            'id': len(wines), 
                            'name': row.get('wine_name', '').strip(),
                            'producer': row.get('producer', '').strip(),
                            'price': float(row.get('price', 0)),
                            'type': row.get('section', 'Red'),
                            'acid': float(row.get('acidity', 5) or 5),
                            'tannin': float(row.get('tannin', 5) or 5),
                            'body': float(row.get('body', 5) or 5),
                            'sugar': float(row.get('sweetness', 1) or 1),
                            'why': row.get('insider_note', '')
                        })
                _wine_cache = wines
                return wines
            except Exception: pass
    return []

# =================================================================
# 2. ANALYSIS LOGIC
# =================================================================
def analyze_dish(food_input: str) -> Dict:
    f = food_input.lower()
    is_asian = any(x in f for x in ['soy', 'ginger', 'curry', 'thai', 'spicy'])
    return {
        'fat_level': 8 if any(x in f for x in ['steak', 'rib', 'pork', 'foie']) else 5, 
        'protein_level': 8 if any(x in f for x in ['steak', 'beef', 'lamb']) else 5, 
        'is_dessert': any(x in f for x in ['cake', 'chocolate', 'ice cream']), 
        'has_seafood': any(x in f for x in ['fish', 'oyster', 'scallop', 'crab']),
        'is_spicy': 'spicy' in f,
        'is_asian': is_asian,
        'name': food_input
    }

def score_wine(wine: Dict, dish_profile: Dict) -> float:
    score = 50
    if dish_profile['has_seafood'] and 'White' in wine['type']: score += 30
    if dish_profile['protein_level'] > 7 and 'Red' in wine['type']: score += 30
    if dish_profile['is_asian'] and wine['sugar'] > 2 and wine['type'] == 'White': score += 25 # Riesling boost
    if dish_profile['is_spicy'] and wine['tannin'] > 6: score -= 30 # Avoid high tannin with spice
    return score

def group_dishes(dishes: List[str], bottle_count: int):
    """
    CRITICAL LOGIC: Distribute dishes evenly across bottles.
    Prevents the "1 Bottle" bug by forcing a split.
    """
    if not dishes: return []
    if len(dishes) < bottle_count:
        return [[{'name': d} for d in dishes] for _ in range(bottle_count)]

    classified = [{'name': d} for d in dishes]
    groups = []
    k, m = divmod(len(classified), bottle_count)
    
    for i in range(bottle_count):
        start = i * k + min(i, m)
        end = (i + 1) * k + min(i + 1, m)
        groups.append(classified[start:end])
    return groups

def score_group(wine, dish_group):
    if not dish_group: return 0
    return score_wine(wine, analyze_dish(dish_group[0]['name']))

# =================================================================
# 3. PROGRESSION ENGINE (With Cost Fixes)
# =================================================================
def generate_progression(dishes: List[str], bottle_count: int, budget: int):
    wines = load_wines()
    if not wines: return {"success": False, "error": "Database error"}
    
    groups = group_dishes(dishes, bottle_count)
    budget_per_bottle = budget // bottle_count
    
    progression = []
    used_ids = set()
    used_producers = set()
    
    # Tiered Budget Strategy (V3.1)
    budget_tiers = [1.05, 1.15, 1.50, float('inf')]
    
    for i, group in enumerate(groups):
        candidates = []
        dish_names = [d['name'] for d in group]
        dish_string = " + ".join(dish_names)
        
        for tier_mult in budget_tiers:
            max_price = budget_per_bottle * tier_mult
            
            for wine in wines:
                if wine['id'] in used_ids: continue
                if wine['producer'] in used_producers: continue
                if wine['price'] > max_price: continue
                
                score = score_group(wine, group)
                
                # Value Bonus (V3.0)
                value_bonus = 500 / (wine['price'] + 1)
                final_score = score + (value_bonus * 0.1)
                
                candidates.append({'wine': wine, 'score': final_score})
            
            if candidates: break
            
        candidates.sort(key=lambda x: x['score'], reverse=True)
        if not candidates: continue
        
        best = candidates[0]['wine']
        used_ids.add(best['id'])
        used_producers.add(best['producer'])
        
        # Luxury Content
        luxury = {}
        if LUXURY_MODE:
            try:
                note = narrator.generate_pairing_story(best['name'], best['type'], dish_string, {'acidity': best['acid'], 'body': best['body']})
                starters = generate_conversation_starters(best['name'], best['producer'], best['type'], None, best['price'])
                luxury = {'pairing_note': note, 'conversation_starters': starters}
            except:
                luxury = {'pairing_note': "A harmonious pairing.", 'conversation_starters': []}

        # Alternatives
        alternatives_data = []
        for cand in candidates[1:3]:
            alt = cand['wine']
            alt_lux = {}
            if LUXURY_MODE:
                try:
                    alt_note = narrator.generate_pairing_story(alt['name'], alt['type'], dish_string, {'acidity': alt['acid'], 'body': alt['body']})
                    alt_starters = generate_conversation_starters(alt['name'], alt['producer'], alt['type'], None, alt['price'])
                    alt_lux = {'pairing_note': alt_note, 'conversation_starters': alt_starters}
                except: pass
            
            alternatives_data.append({
                "wine_name": alt['name'], "producer": alt['producer'], "price": alt['price'],
                "pairing_note": alt_lux.get('pairing_note', ''),
                "conversation_starters": alt_lux.get('conversation_starters', [])
            })

        progression.append({
            "course_number": i + 1,
            "course_name": f"Course {i+1}",
            "dishes": dish_names,
            "primary": {
                "wine_name": best['name'], "producer": best['producer'], 
                "price": best['price'], "type": best['type']
            },
            "luxury": luxury,
            "alternatives": alternatives_data
        })
    
    # CRITICAL FIX: Calculate totals (Claude's Contribution)
    total_cost = sum(c['primary']['price'] for c in progression)
    budget_utilization = round((total_cost / budget * 100), 1) if budget > 0 else 0
    
    return {
        "success": True,
        "progression": progression,
        "total_cost": total_cost,
        "budget_utilization": budget_utilization
    }
