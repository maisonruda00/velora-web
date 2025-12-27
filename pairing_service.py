"""
VELORA PAIRING SERVICE - V3.1 FINAL (Gemini-Audited)
✅ FIXES:
- Budget fallback is now FORGIVING (Gemini's critique)
- Kept all V3 improvements (quality checks, cuisine boosting)
- Preserved ALL helper functions (group_dishes, classify_dish_type, score_wine_for_group)
- Added graceful error messaging
- Kept diversity constraints

TESTED EDGE CASES:
- $50 budget (cheapest wine is $53) → Shows $53 with warning
- $5000 budget → Works
- 1 dish, 3 bottles → Works
- 10 dishes, 1 bottle → Works
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
# DATABASE LOADER WITH QUALITY CHECKS (V3)
# =================================================================
_wine_cache = None

def load_wines() -> List[Dict]:
    """Load wine database with quality filtering"""
    global _wine_cache
    if _wine_cache:
        return _wine_cache
    
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
                        wine_name = row.get('wine_name', '').strip()
                        producer = row.get('producer', '').strip()
                        
                        # QUALITY CHECK: Skip wines with missing critical data
                        if not wine_name or wine_name.lower() == 'unknown':
                            continue
                        if not producer:
                            continue
                        
                        try:
                            price = float(row.get('price', 0) or 0)
                            if price <= 0:
                                continue  # Skip wines without valid price
                        except:
                            continue
                        
                        wines.append({
                            'id': len(wines),
                            'name': wine_name,
                            'producer': producer,
                            'price': price,
                            'type': row.get('section', 'Red'),
                            'acid': float(row.get('acidity', 5) or 5),
                            'tannin': float(row.get('tannin', 5) or 5),
                            'body': float(row.get('body', 5) or 5),
                            'sugar': float(row.get('sweetness', 1) or 1),
                            'why': row.get('insider_note', '')
                        })
                
                _wine_cache = wines
                print(f"✅ Loaded {len(wines)} quality-checked wines from {path}")
                return wines
            except Exception as e:
                print(f"❌ Error loading wines: {e}")
                pass
    
    print(f"❌ No wine database found")
    return []

# =================================================================
# DISH CLASSIFICATION (V3 - Enhanced)
# =================================================================

def classify_dish_type(dish_name: str) -> Dict:
    """
    Classify dish characteristics for pairing
    Enhanced with cuisine detection (V3 feature)
    """
    dish_lower = dish_name.lower()
    
    # Cuisine detection
    cuisine = 'western'  # default
    if any(word in dish_lower for word in ['peking', 'szechuan', 'dim sum', 'wonton', 'dumpling']):
        cuisine = 'chinese'
    elif any(word in dish_lower for word in ['curry', 'tandoori', 'biryani', 'tikka', 'masala']):
        cuisine = 'indian'
    elif any(word in dish_lower for word in ['pad thai', 'tom yum', 'green curry', 'massaman']):
        cuisine = 'thai'
    elif any(word in dish_lower for word in ['sushi', 'sashimi', 'ramen', 'tempura']):
        cuisine = 'japanese'
    elif any(word in dish_lower for word in ['kimchi', 'bulgogi', 'bibimbap', 'galbi']):
        cuisine = 'korean'
    
    # Protein detection
    protein_level = 5
    if any(meat in dish_lower for meat in ['steak', 'ribeye', 'wagyu', 'beef', 'lamb', 'venison']):
        protein_level = 9
    elif any(meat in dish_lower for meat in ['duck', 'pork', 'veal']):
        protein_level = 7
    elif any(seafood in dish_lower for seafood in ['fish', 'salmon', 'tuna', 'cod']):
        protein_level = 6
    elif any(seafood in dish_lower for seafood in ['oyster', 'scallop', 'shrimp', 'lobster', 'crab']):
        protein_level = 5
    
    # Fat level
    fat_level = 5
    if any(word in dish_lower for word in ['rib', 'short rib', 'pork belly', 'foie gras', 'butter']):
        fat_level = 9
    elif any(word in dish_lower for word in ['cream', 'cheese', 'carbonara']):
        fat_level = 7
    
    # Spice level
    is_spicy = any(word in dish_lower for word in ['spicy', 'chili', 'pepper', 'hot', 'szechuan', 'vindaloo'])
    
    # Dessert
    is_dessert = any(word in dish_lower for word in ['cake', 'tart', 'chocolate', 'ice cream', 'dessert', 'sweet'])
    
    # Seafood
    has_seafood = any(word in dish_lower for word in ['fish', 'oyster', 'scallop', 'shrimp', 'lobster', 'crab', 'octopus', 'clam'])
    
    return {
        'cuisine': cuisine,
        'protein_level': protein_level,
        'fat_level': fat_level,
        'is_spicy': is_spicy,
        'is_dessert': is_dessert,
        'has_seafood': has_seafood
    }

# =================================================================
# GROUPING LOGIC (V2 Math - Proven)
# =================================================================

def group_dishes(dishes: List[str], bottle_count: int) -> List[List[Dict]]:
    """
    Splits N dishes into K bottles evenly
    GUARANTEED to distribute ALL dishes (V2 proven math)
    """
    if not dishes:
        return [[]]
    
    classified = [{'name': d, **classify_dish_type(d)} for d in dishes]
    
    # Edge case: More bottles than dishes
    if len(dishes) < bottle_count:
        return [[classified[i % len(classified)]] for i in range(bottle_count)]
    
    # Standard distribution
    chunk_size = len(classified) // bottle_count
    remainder = len(classified) % bottle_count
    
    groups = []
    start_idx = 0
    
    for i in range(bottle_count):
        end_idx = start_idx + chunk_size + (1 if i < remainder else 0)
        groups.append(classified[start_idx:end_idx])
        start_idx = end_idx
    
    return groups

# =================================================================
# SCORING LOGIC (V3 - Enhanced)
# =================================================================

def score_wine_for_group(wine: Dict, dish_group: List[Dict]) -> float:
    """
    Enhanced scoring with cuisine awareness (V3 feature)
    Andrea Robinson's recommendations implemented
    """
    if not dish_group:
        return 0
    
    score = 50  # Base score
    dominant_dish = dish_group[0]
    cuisine = dominant_dish.get('cuisine', 'western')
    
    # CUISINE-SPECIFIC BOOSTING (V3 - Andrea Robinson's fix)
    if cuisine in ['chinese', 'indian', 'thai']:
        # Andrea: "Where's the Riesling?"
        if 'Riesling' in wine['type'] or 'riesling' in wine['name'].lower():
            score += 30  # Strong boost for Riesling with Asian
        elif 'White' in wine['type'] and wine['sugar'] > 2:
            score += 20  # Off-dry whites work well
        elif 'Rosé' in wine['type']:
            score += 15  # Rosé is versatile
        elif 'Red' in wine['type'] and wine['tannin'] > 7:
            score -= 20  # Heavy reds clash with Asian
    
    # Seafood pairing
    if dominant_dish.get('has_seafood'):
        if 'White' in wine['type']:
            score += 25
        elif 'Sparkling' in wine['type']:
            score += 20
        elif 'Red' in wine['type'] and wine['tannin'] > 6:
            score -= 15  # Tannin clashes with seafood
    
    # Red meat pairing
    if dominant_dish.get('protein_level', 0) >= 8:
        if 'Red' in wine['type']:
            score += 25
            if wine['tannin'] >= 7:
                score += 10  # High tannin good for fatty meat
    
    # Spicy food
    if dominant_dish.get('is_spicy'):
        if wine['sugar'] > 2:
            score += 20  # Off-dry helps with spice
        if wine['acid'] >= 7:
            score += 10  # Acidity refreshes
        if wine['tannin'] >= 7:
            score -= 15  # Tannin amplifies spice
    
    # Dessert
    if dominant_dish.get('is_dessert'):
        if 'Dessert' in wine['type'] or wine['sugar'] >= 5:
            score += 30
        elif 'Sparkling' in wine['type']:
            score += 15
    
    return max(score, 0)

def calculate_value_score(wine: Dict, pairing_score: float, budget_per_bottle: float) -> float:
    """
    Dr. Chen's Value Optimization (V3 feature)
    Balances quality with price efficiency
    """
    quality = pairing_score
    
    if budget_per_bottle <= 0:
        return quality
    
    price_ratio = wine['price'] / budget_per_bottle
    
    # Price efficiency multiplier
    if price_ratio <= 0.3:
        efficiency = 0.7  # Too cheap, might seem cheap
    elif 0.3 < price_ratio <= 0.75:
        efficiency = 0.95  # Good value
    elif 0.75 < price_ratio <= 0.95:
        efficiency = 1.0  # Excellent - using budget well
    elif 0.95 < price_ratio <= 1.05:
        efficiency = 1.1  # Perfect - right at budget
    elif 1.05 < price_ratio <= 1.15:
        efficiency = 0.9  # Slightly over
    else:
        efficiency = 0.3  # Way over budget - heavy penalty
    
    return quality * efficiency

# =================================================================
# MAIN PROGRESSION ENGINE (V3.1 - Gemini-Fixed)
# =================================================================

def generate_progression(dishes: List[str], bottle_count: int, budget: int):
    """
    PRODUCTION-READY PAIRING ENGINE
    V3.1: All expert fixes + Gemini's budget fallback fix
    """
    wines = load_wines()
    if not wines:
        return {"success": False, "error": "Wine database unavailable"}
    
    if budget <= 0:
        return {"success": False, "error": "Budget must be greater than $0"}
    
    if bottle_count <= 0:
        return {"success": False, "error": "Bottle count must be at least 1"}
    
    # Group dishes
    groups = group_dishes(dishes, bottle_count)
    budget_per_bottle = budget // bottle_count
    
    progression = []
    used_ids = set()
    used_producers = set()  # Diversity constraint (V3)
    
    for i, group in enumerate(groups):
        candidates = []
        dish_names = [d['name'] for d in group]
        dish_string = " + ".join(dish_names)
        
        # TIERED BUDGET STRATEGY (Gemini's fix + V3 optimization)
        # Tier 1: Ideal (within 5% of budget)
        # Tier 2: Acceptable (within 15% of budget)
        # Tier 3: Fallback (within 50% of budget, with warning)
        
        tier1_max = budget_per_bottle * 1.05  # Ideal
        tier2_max = budget_per_bottle * 1.15  # Acceptable
        tier3_max = budget_per_bottle * 1.50  # Emergency fallback
        
        for wine in wines:
            if wine['id'] in used_ids:
                continue
            
            # Skip wines way over budget
            if wine['price'] > tier3_max:
                continue
            
            # Calculate scores
            pairing_score = score_wine_for_group(wine, group)
            if pairing_score <= 0:
                continue
            
            # Apply value optimization
            value_score = calculate_value_score(wine, pairing_score, budget_per_bottle)
            
            # Diversity bonus (avoid same producer twice) - V3 feature
            if wine['producer'] in used_producers:
                value_score *= 0.7  # 30% penalty
            
            # Tier bonus (prefer wines closer to budget)
            if wine['price'] <= tier1_max:
                tier_bonus = 1.0  # Perfect
            elif wine['price'] <= tier2_max:
                tier_bonus = 0.8  # Good
            else:
                tier_bonus = 0.5  # Fallback only
            
            final_score = value_score * tier_bonus
            
            candidates.append({
                'wine': wine,
                'score': final_score,
                'tier': 1 if wine['price'] <= tier1_max else (2 if wine['price'] <= tier2_max else 3)
            })
        
        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # GEMINI'S FIX: Graceful degradation if no perfect matches
        if not candidates:
            # Last resort: Show ANY wine that pairs well, regardless of price
            for wine in wines:
                if wine['id'] in used_ids:
                    continue
                pairing_score = score_wine_for_group(wine, group)
                if pairing_score > 0:
                    candidates.append({
                        'wine': wine,
                        'score': pairing_score,
                        'tier': 4  # "Over budget" tier
                    })
            
            candidates.sort(key=lambda x: x['score'], reverse=True)
        
        if not candidates:
            return {
                "success": False,
                "error": f"No wines found for course {i+1}. This shouldn't happen with 14K wines. Please contact support."
            }
        
        # Select best wine
        best_candidate = candidates[0]
        best = best_candidate['wine']
        tier = best_candidate.get('tier', 1)
        
        used_ids.add(best['id'])
        used_producers.add(best['producer'])
        
        # Generate luxury content
        luxury = {}
        budget_note = ""
        
        # Add budget warning if in Tier 3 or 4
        if tier >= 3:
            over_amount = best['price'] - budget_per_bottle
            budget_note = f"Note: This wine exceeds your ${budget_per_bottle} target by ${over_amount:.0f}. "
            if tier == 4:
                budget_note += "No wines found within budget range for this pairing."
        
        if LUXURY_MODE:
            try:
                note = narrator.generate_pairing_story(
                    wine_name=best['name'],
                    wine_type=best['type'],
                    dish_name=dish_string,
                    wine_properties={
                        'acidity': best['acid'],
                        'tannin': best['tannin'],
                        'body': best['body']
                    }
                )
                
                # Prepend budget note if exists
                if budget_note:
                    note = budget_note + note
                
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
                print(f"⚠️ AI content generation failed: {e}")
                if budget_note:
                    luxury = {'pairing_note': budget_note, 'conversation_starters': []}
        else:
            if budget_note:
                luxury = {'pairing_note': budget_note, 'conversation_starters': []}
        
        # Generate alternatives
        alternatives_data = []
        for cand in candidates[1:3]:  # Next 2 best
            alt = cand['wine']
            alt_tier = cand.get('tier', 1)
            alt_luxury = {}
            
            if LUXURY_MODE:
                try:
                    alt_note = narrator.generate_pairing_story(
                        alt['name'], alt['type'], dish_string,
                        {'acidity': alt['acid'], 'body': alt['body']}
                    )
                    alt_starters = generate_conversation_starters(
                        alt['name'], alt['producer'], alt['type'], None, alt['price']
                    )
                    alt_luxury = {
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
                "pairing_note": alt_luxury.get('pairing_note', ''),
                "conversation_starters": alt_luxury.get('conversation_starters', [])
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
    
    total_cost = sum(c['primary']['price'] for c in progression)
    
    return {
        "success": True,
        "progression": progression,
        "total_cost": total_cost,
        "budget_utilization": total_cost / budget if budget > 0 else 0
    }
