"""
VELORA PAIRING SERVICE - V3.2 PRODUCTION (Gemini Merge + Claude Fixes)
✅ Grouping Logic: divmod distribution (prevents 1-bottle bug)
✅ Budget Strategy: Tiered fallback (prevents zero results)
✅ Cost Tracking: total_cost + budget_utilization (Claude's fix)
✅ Quality Checks: Filters bad data
✅ Cuisine Awareness: Riesling boost for Asian food
"""
import csv
import os
from typing import List, Dict
from functools import lru_cache

# Import Luxury Modules
try:
    from sommelier_narrator import narrator
    from conversation_starter import generate_conversation_starters
    LUXURY_MODE = True
except ImportError:
    LUXURY_MODE = False

# =================================================================
# DATABASE LOADER
# =================================================================
_wine_cache = None

def load_wines() -> List[Dict]:
    """Load wine database with STRICT wine-only filtering"""
    global _wine_cache
    if _wine_cache:
        return _wine_cache
    
    # STRICT WINE-ONLY SECTIONS
    VALID_WINE_SECTIONS = {
        'red wine', 'white wine', 'sparkling', 'champagne', 'rosé', 'rose', 'dessert wine',
        'red wines', 'white wines', 'sparkling wines', 'champagne & sparkling',
        'french red wine', 'french white wine', 'italian red wine', 'italian white wine',
        'spanish red wine', 'spanish white wine', 'usa red wine', 'domestic red wine',
        'napa valley cabernet', 'bordeaux', 'burgundy', 'red burgundy', 'white burgundy',
        'pinot noir', 'cabernet sauvignon', 'chardonnay', 'sauvignon blanc', 'riesling',
        'champagne & sparkling wines', 'red', 'white', 'sparkling wine'
    }
    
    # BLACKLIST - explicitly exclude these
    EXCLUDE_SECTIONS = {
        'spirits', 'beer', 'cocktails', 'zero proof', 'non-alcoholic', 'water',
        'general', 'à la carte', 'entrees', 'appetizers', 'desserts', 'sides',
        'reserve list', 'large format', 'half bottles'  # These are categories, not wine types
    }
    
    # BLACKLIST - non-wine items in names
    EXCLUDE_NAMES = {
        'egg', 'water', 'beer', 'ale', 'lager', 'vodka', 'whiskey', 'whisky', 'gin',
        'rum', 'tequila', 'mezcal', 'cognac', 'brandy', 'coffee', 'tea', 'soda',
        'juice', 'budweiser', 'coors', 'miller', 'corona'
    }
    
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
                        # Quality check: skip invalid entries
                        if not row.get('price') or not row.get('wine_name'):
                            continue
                        
                        wine_name = row.get('wine_name', '').strip()
                        if not wine_name or wine_name.lower() == 'unknown':
                            continue
                        
                        # STRICT FILTER: Check if name contains non-wine keywords
                        name_lower = wine_name.lower()
                        if any(exclude in name_lower for exclude in EXCLUDE_NAMES):
                            continue
                        
                        # STRICT FILTER: Check section
                        section = row.get('section', '').strip().lower()
                        
                        # Skip if in blacklist
                        if any(exclude in section for exclude in EXCLUDE_SECTIONS):
                            continue
                        
                        # Skip if bottle size is in section (bad data)
                        if 'ml' in section or 'oz' in section or 'l' == section:
                            continue
                        
                        # Only allow if section contains wine-related terms
                        # OR if section is empty but name looks like wine
                        is_valid_section = any(valid in section for valid in VALID_WINE_SECTIONS)
                        
                        if not is_valid_section and section:
                            # Skip unless we can identify it's wine from other clues
                            # Check if producer name exists (wines have producers, food doesn't)
                            if not row.get('producer', '').strip():
                                continue
                        
                        try:
                            price = float(row.get('price', 0))
                            if price <= 0:
                                continue
                        except:
                            continue
                        
                        wines.append({
                            'id': len(wines),
                            'name': wine_name,
                            'producer': row.get('producer', '').strip(),
                            'price': price,
                            'type': row.get('section', 'Red'),
                            'acid': float(row.get('acidity', 5) or 5),
                            'tannin': float(row.get('tannin', 5) or 5),
                            'body': float(row.get('body', 5) or 5),
                            'sugar': float(row.get('sweetness', 1) or 1),
                            'why': row.get('insider_note', '')
                        })
                
                _wine_cache = wines
                print(f"✅ Loaded {len(wines)} WINES ONLY (filtered out non-wine items)")
                return wines
            except Exception as e:
                print(f"❌ Error loading wines: {e}")
                continue
    
    print(f"❌ No wine database found")
    return []

# =================================================================
# DISH ANALYSIS
# =================================================================
def analyze_dish(food_input: str) -> Dict:
    """Analyze dish characteristics for pairing"""
    f = food_input.lower()
    
    # Cuisine detection
    is_asian = any(x in f for x in ['soy', 'ginger', 'curry', 'thai', 'chinese', 
                                     'indian', 'korean', 'japanese', 'szechuan',
                                     'peking', 'tandoori', 'kimchi'])
    
    return {
        'fat_level': 8 if any(x in f for x in ['steak', 'rib', 'pork', 'foie gras', 'butter']) else 5,
        'protein_level': 8 if any(x in f for x in ['steak', 'beef', 'lamb', 'wagyu']) else 5,
        'is_dessert': any(x in f for x in ['cake', 'chocolate', 'ice cream', 'tart', 'dessert']),
        'has_seafood': any(x in f for x in ['fish', 'oyster', 'scallop', 'crab', 'lobster', 'octopus']),
        'is_spicy': any(x in f for x in ['spicy', 'chili', 'hot', 'vindaloo']),
        'is_asian': is_asian,
        'name': food_input
    }

def score_wine(wine: Dict, dish_profile: Dict) -> float:
    """Score wine for dish compatibility"""
    score = 50  # Base score
    
    # Seafood pairing
    if dish_profile['has_seafood']:
        if 'White' in wine['type']:
            score += 30
        elif 'Red' in wine['type'] and wine['tannin'] > 6:
            score -= 20  # Tannin clashes with seafood
    
    # Red meat pairing
    if dish_profile['protein_level'] > 7:
        if 'Red' in wine['type']:
            score += 30
            if wine['tannin'] >= 7:
                score += 10  # High tannin good for fatty meat
    
    # Asian cuisine boost for Riesling
    if dish_profile['is_asian']:
        if 'Riesling' in wine['type'] or 'riesling' in wine['name'].lower():
            score += 25
        elif wine['type'] == 'White' and wine['sugar'] > 2:
            score += 20  # Off-dry whites
        elif 'Red' in wine['type'] and wine['tannin'] > 6:
            score -= 30  # Heavy reds clash with Asian
    
    # Spicy food
    if dish_profile['is_spicy']:
        if wine['sugar'] > 2:
            score += 20  # Off-dry helps with spice
        if wine['tannin'] > 6:
            score -= 30  # Tannin amplifies spice
    
    # Dessert
    if dish_profile['is_dessert']:
        if 'Dessert' in wine['type'] or wine['sugar'] >= 5:
            score += 40
        elif 'Sparkling' in wine['type']:
            score += 15
    
    return max(score, 0)

# =================================================================
# GROUPING LOGIC (Gemini's proven math)
# =================================================================
def group_dishes(dishes: List[str], bottle_count: int) -> List[List[Dict]]:
    """
    CRITICAL: Distribute dishes evenly across bottles using divmod
    Prevents 1-bottle bug by forcing proper distribution
    """
    if not dishes:
        return []
    
    classified = [{'name': d} for d in dishes]
    
    # Edge case: more bottles than dishes
    if len(dishes) < bottle_count:
        return [[classified[i % len(classified)]] for i in range(bottle_count)]
    
    # divmod distribution
    groups = []
    k, m = divmod(len(classified), bottle_count)
    
    for i in range(bottle_count):
        start = i * k + min(i, m)
        end = (i + 1) * k + min(i + 1, m)
        groups.append(classified[start:end])
    
    return groups

def score_group(wine: Dict, dish_group: List[Dict]) -> float:
    """Score wine for a group of dishes"""
    if not dish_group:
        return 0
    
    # Score based on dominant dish (first in group)
    return score_wine(wine, analyze_dish(dish_group[0]['name']))

# =================================================================
# MAIN PROGRESSION ENGINE
# =================================================================
def generate_progression(dishes: List[str], bottle_count: int, budget: int):
    """
    Generate wine progression for multiple dishes
    V3.2: Complete merge of all fixes
    """
    wines = load_wines()
    if not wines:
        return {"success": False, "error": "Wine database not available"}
    
    if not dishes:
        return {"success": False, "error": "No dishes provided"}
    
    if budget <= 0:
        return {"success": False, "error": "Budget must be greater than $0"}
    
    if bottle_count <= 0:
        return {"success": False, "error": "Bottle count must be at least 1"}
    
    # Group dishes
    groups = group_dishes(dishes, bottle_count)
    budget_per_bottle = budget // bottle_count
    
    progression = []
    used_ids = set()
    used_producers = set()  # Diversity constraint
    
    # TIERED BUDGET STRATEGY (Gemini's fix)
    budget_tiers = [1.05, 1.15, 1.50, float('inf')]  # 5%, 15%, 50%, any
    
    for i, group in enumerate(groups):
        candidates = []
        dish_names = [d['name'] for d in group]
        dish_string = " + ".join(dish_names)
        
        # Try progressively relaxed budgets
        for tier_mult in budget_tiers:
            max_price = budget_per_bottle * tier_mult
            
            for wine in wines:
                if wine['id'] in used_ids:
                    continue
                if wine['price'] > max_price:
                    continue
                
                # Score wine for this group
                pairing_score = score_group(wine, group)
                if pairing_score <= 0:
                    continue
                
                # Value optimization
                value_bonus = 500 / (wine['price'] + 1)
                final_score = pairing_score + (value_bonus * 0.1)
                
                # Diversity penalty (avoid duplicate producers)
                if wine['producer'] in used_producers:
                    final_score *= 0.7
                
                candidates.append({'wine': wine, 'score': final_score})
            
            if candidates:
                break  # Found wines at this tier
        
        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        if not candidates:
            # Should never happen with inf tier, but just in case
            continue
        
        # Select best wine
        best = candidates[0]['wine']
        used_ids.add(best['id'])
        used_producers.add(best['producer'])
        
        # Generate luxury content
        luxury = {}
        if LUXURY_MODE:
            try:
                note = narrator.generate_pairing_story(
                    wine_name=best['name'],
                    wine_type=best['type'],
                    dish_name=dish_string,
                    wine_properties={
                        'acidity': best['acid'],
                        'body': best['body'],
                        'tannin': best['tannin']
                    }
                )
                starters = generate_conversation_starters(
                    best['name'],
                    best['producer'],
                    best['type'],
                    None,
                    best['price']
                )
                luxury = {
                    'pairing_note': note,
                    'conversation_starters': starters
                }
            except Exception as e:
                print(f"⚠️ AI content failed: {e}")
                luxury = {
                    'pairing_note': "A harmonious pairing.",
                    'conversation_starters': []
                }
        else:
            luxury = {
                'pairing_note': "A harmonious pairing.",
                'conversation_starters': []
            }
        
        # Generate alternatives
        alternatives_data = []
        for cand in candidates[1:3]:  # Next 2 best
            alt = cand['wine']
            alt_lux = {}
            
            if LUXURY_MODE:
                try:
                    alt_note = narrator.generate_pairing_story(
                        alt['name'],
                        alt['type'],
                        dish_string,
                        {'acidity': alt['acid'], 'body': alt['body']}
                    )
                    alt_starters = generate_conversation_starters(
                        alt['name'],
                        alt['producer'],
                        alt['type'],
                        None,
                        alt['price']
                    )
                    alt_lux = {
                        'pairing_note': alt_note,
                        'conversation_starters': alt_starters
                    }
                except:
                    pass
            
            alternatives_data.append({
                "wine_name": alt['name'],
                "producer": alt['producer'],
                "price": alt['price'],
                "type": alt['type'],
                "pairing_note": alt_lux.get('pairing_note', ''),
                "conversation_starters": alt_lux.get('conversation_starters', [])
            })
        
        progression.append({
            "course_number": i + 1,
            "course_name": f"Course {i+1}",
            "dishes": dish_names,
            "primary": {
                "wine_name": best['name'],
                "producer": best['producer'],
                "price": best['price'],
                "type": best['type']
            },
            "luxury": luxury,
            "alternatives": alternatives_data
        })
    
    # CRITICAL FIX: Calculate total cost (Claude's contribution)
    total_cost = sum(c['primary']['price'] for c in progression)
    budget_utilization = round((total_cost / budget * 100), 1) if budget > 0 else 0
    
    return {
        "success": True,
        "progression": progression,
        "total_cost": total_cost,
        "budget_utilization": budget_utilization,
        "bottle_count": bottle_count,
        "total_budget": budget
    }

# =================================================================
# LEGACY SUPPORT (for old /consult endpoint)
# =================================================================
def get_recommendation(food_input: str, budget: int = 1000):
    """Single dish recommendation (legacy endpoint)"""
    result = generate_progression(
        dishes=[food_input],
        bottle_count=1,
        budget=budget
    )
    
    if not result.get('success'):
        return result
    
    # Convert to old format
    course = result['progression'][0]
    return {
        "success": True,
        "wine": course['primary']['wine_name'],
        "producer": course['primary']['producer'],
        "price": course['primary']['price'],
        "type": course['primary']['type'],
        "pairing_note": course['luxury']['pairing_note'],
        "conversation_starters": course['luxury']['conversation_starters'],
        "alternatives": course['alternatives']
    }
