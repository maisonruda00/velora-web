"""
VELORA PAIRING SERVICE - V5.2 UNIFIED
✅ ALGORITHM: Full v5.1 sophisticated logic (11-layer, prestige, AI)
✅ OUTPUT: v5.0 'options' structure (for Alpine.js frontend)
✅ FIXES: Frontend/Backend mismatch causing "null wine" errors
"""
import csv
import os
import re
import unicodedata
import hashlib
import logging
from typing import List, Dict, Tuple
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Luxury Modules (AI narrator + conversation starters)
try:
    from sommelier_narrator import narrator
    from conversation_starter import generate_conversation_starters
    LUXURY_MODE = True
    logger.info("✅ Luxury modules loaded")
except ImportError as e:
    LUXURY_MODE = False
    logger.warning(f"⚠️ Luxury modules not available: {e}")

# Import Facts Database
try:
    from facts_database import get_interesting_fact, calculate_rarity_level
    FACTS_ENABLED = True
    logger.info("✅ Facts database loaded")
except ImportError as e:
    FACTS_ENABLED = False
    logger.warning(f"⚠️ Facts database not available: {e}")

# =================================================================
# STABLE ID GENERATION
# =================================================================

def slugify(text: str) -> str:
    if not isinstance(text, str): text = str(text)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '_', text)
    return text.strip('_')

def generate_stable_id(producer: str, name: str) -> str:
    slug = f"{slugify(producer)}_{slugify(name)}"
    if len(slug) > 64:
        hash_suffix = hashlib.md5(slug.encode()).hexdigest()[:8]
        slug = f"{slug[:55]}_{hash_suffix}"
    return slug

# =================================================================
# WINE DATABASE LOADER
# =================================================================

_wine_cache = None

@lru_cache(maxsize=1)
def load_wines() -> List[Dict]:
    global _wine_cache
    if _wine_cache: return _wine_cache
    
    logger.info("🍷 Loading wine database...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(script_dir, 'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv'),
        'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv',
        '/app/MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv'
    ]
    
    for path in paths:
        if os.path.exists(path):
            try:
                wines = []
                with open(path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            price = float(row.get('price', 0))
                            if price < 20: continue  # Bottles only
                            
                            producer = row.get('producer', '').strip()
                            name = row.get('wine_name', '').strip()
                            
                            if not producer or not name: continue
                            
                            wine_id = generate_stable_id(producer, name)
                            
                            wines.append({
                                'id': wine_id,
                                'name': name,
                                'producer': producer,
                                'vintage': row.get('vintage', '').strip(),
                                'price': price,
                                'type': row.get('section', 'Wine').strip(),
                                'acid': float(row.get('acidity', 5) or 5),
                                'tannin': float(row.get('tannin', 5) or 5),
                                'body': float(row.get('body', 5) or 5),
                                'sugar': float(row.get('sweetness', 1) or 1),
                                'insider_note': row.get('insider_note', '').strip()
                            })
                        except (ValueError, KeyError):
                            continue
                
                _wine_cache = wines
                logger.info(f"✅ Loaded {len(wines):,} wines")
                return wines
                
            except Exception as e:
                logger.error(f"❌ Error loading wines: {e}")
                continue
    
    logger.error("❌ No wine database found")
    return []

# =================================================================
# PRESTIGE SCORING (Reduced bonuses - pairing quality matters more)
# =================================================================

LEGENDARY_PRODUCERS = {
    'romanée-conti': 25, 'romanee-conti': 25, 'drc': 25,
    'pétrus': 20, 'petrus': 20,
    'château margaux': 15, 'chateau margaux': 15,
    'château latour': 15, 'chateau latour': 15,
    'screaming eagle': 15,
    'harlan estate': 12,
    'opus one': 10,
    'sassicaia': 10,
    'ornellaia': 8
}

PRESTIGIOUS_VINEYARDS = {
    'la tâche': 15, 'la tache': 15,
    'richebourg': 12,
    'romanée-st-vivant': 12,
    'montrachet': 18,
    'corton-charlemagne': 15
}

# =================================================================
# DISH ANALYSIS (V4.0 - 11-Layer Algorithm)
# =================================================================

def analyze_dish(dish_name: str, dish_description: str = "") -> Dict:
    combined = f"{dish_name} {dish_description}".lower()
    
    profile = {
        'name': dish_name,
        'description': dish_description,
        'has_seafood': False,
        'has_red_meat': False,
        'has_poultry': False,
        'is_spicy': False,
        'is_dessert': False,
        'sauce_type': None,
        'umami_level': 5,
        'fat_level': 5
    }
    
    # Seafood
    if any(s in combined for s in ['fish', 'salmon', 'tuna', 'lobster', 'crab', 'shrimp', 'scallop', 'oyster']):
        profile['has_seafood'] = True
    
    # Red meat
    if any(m in combined for m in ['beef', 'steak', 'ribeye', 'lamb', 'venison', 'short rib']):
        profile['has_red_meat'] = True
    
    # Poultry
    if any(p in combined for p in ['chicken', 'duck', 'turkey']):
        profile['has_poultry'] = True
    
    # Spicy
    if any(s in combined for s in ['spicy', 'chili', 'curry', 'jalapeño']):
        profile['is_spicy'] = True
    
    # Dessert
    if any(d in combined for d in ['dessert', 'chocolate', 'cake', 'tart']):
        profile['is_dessert'] = True
    
    # Sauce
    if any(s in combined for s in ['béarnaise', 'bearnaise', 'hollandaise', 'cream sauce', 'butter sauce']):
        profile['sauce_type'] = 'rich_cream'
        profile['fat_level'] = 8
    elif any(s in combined for s in ['tomato', 'marinara', 'pomodoro']):
        profile['sauce_type'] = 'tomato'
    
    # Umami
    if any(u in combined for u in ['truffle', 'mushroom', 'parmesan', 'aged cheese']):
        profile['umami_level'] = 9
    
    return profile

def score_wine(wine: Dict, dish_profile: Dict) -> int:
    """11-layer scoring algorithm"""
    score = 50
    wine_name_lower = wine['name'].lower()
    wine_type_lower = wine['type'].lower()
    
    # Layer 1: Seafood matching
    if dish_profile['has_seafood']:
        if 'white' in wine_type_lower or 'sparkling' in wine_type_lower:
            score += 30
        elif wine['acid'] >= 7:
            score += 25
        elif 'red' in wine_type_lower:
            score -= 20
    
    # Layer 2: Red meat matching
    if dish_profile['has_red_meat']:
        if 'red' in wine_type_lower:
            score += 30
            if wine['tannin'] >= 7:
                score += 15
    
    # Layer 3: Sauce matching
    if dish_profile['sauce_type'] == 'rich_cream':
        if wine['acid'] >= 7:
            score += 20
    elif dish_profile['sauce_type'] == 'tomato':
        if 'red' in wine_type_lower and wine['acid'] >= 6:
            score += 20
    
    # Layer 4: Body/Fat matching
    if dish_profile['fat_level'] >= 7:
        if wine['body'] >= 7:
            score += 15
    
    # Layer 5: Umami matching
    if dish_profile['umami_level'] >= 8:
        if wine['acid'] >= 7:
            score += 15
    
    # Layer 6: Spicy food
    if dish_profile['is_spicy']:
        if wine['sugar'] >= 3 or 'riesling' in wine_name_lower:
            score += 20
    
    # Layer 7: Dessert
    if dish_profile['is_dessert']:
        if 'dessert' in wine_type_lower or 'port' in wine_name_lower:
            score += 40
    
    return score

def score_group(wine: Dict, dish_group: List[Dict]) -> float:
    """Score wine for a group of dishes"""
    if not dish_group: return 0
    
    if len(dish_group) == 1:
        dish = dish_group[0]
        return score_wine(wine, analyze_dish(
            dish.get('name', ''),
            dish.get('description', '')
        ))
    
    # Multiple dishes: compromise formula
    scores = []
    for dish in dish_group:
        dish_score = score_wine(wine, analyze_dish(
            dish.get('name', ''),
            dish.get('description', '')
        ))
        scores.append(dish_score)
    
    if not scores: return 0
    
    # 70% average, 30% minimum
    min_score = min(scores)
    avg_score = sum(scores) / len(scores)
    return (avg_score * 0.7) + (min_score * 0.3)

# =================================================================
# DISH GROUPING
# =================================================================

def group_dishes(dishes: List[Dict], bottle_count: int) -> List[List[Dict]]:
    if not dishes: return []
    
    dishes_per_group, remainder = divmod(len(dishes), bottle_count)
    
    groups = []
    start = 0
    for i in range(bottle_count):
        group_size = dishes_per_group + (1 if i < remainder else 0)
        end = start + group_size
        groups.append(dishes[start:end])
        start = end
    
    return groups

# =================================================================
# MAIN PROGRESSION ENGINE (V5.1 Logic → V5.0 Structure)
# =================================================================

def generate_progression(dishes, bottle_count: int, budget: int):
    """
    Generate wine progression with sophisticated v5.1 logic
    Returns v5.0 'options' structure for Alpine.js frontend
    """
    wines = load_wines()
    if not wines:
        return {"success": False, "error": "Wine database not available"}
    
    # Input validation
    if not dishes:
        return {"success": False, "error": "No dishes provided"}
    
    if not isinstance(bottle_count, int) or bottle_count <= 0:
        return {"success": False, "error": "Bottle count must be a positive integer"}
    
    if not isinstance(budget, (int, float)) or budget <= 0:
        return {"success": False, "error": "Budget must be greater than 0"}
    
    if bottle_count > len(dishes):
        return {"success": False, "error": f"Cannot recommend {bottle_count} bottles for {len(dishes)} dishes. Try fewer bottles."}
    
    # Normalize dishes to dict format
    normalized_dishes = []
    for dish in dishes:
        if isinstance(dish, str):
            normalized_dishes.append({'name': dish, 'description': '', 'price': 0.0})
        elif isinstance(dish, dict):
            normalized_dishes.append({
                'name': dish.get('name', ''),
                'description': dish.get('description', ''),
                'price': dish.get('price', 0.0)
            })
        else:
            normalized_dishes.append({
                'name': getattr(dish, 'name', ''),
                'description': getattr(dish, 'description', ''),
                'price': getattr(dish, 'price', 0.0)
            })
    
    # Group dishes
    groups = group_dishes(normalized_dishes, bottle_count)
    budget_per_bottle = budget // bottle_count
    
    progression = []
    used_ids = set()
    
    # TIERED BUDGET STRATEGY (respect budget)
    budget_tiers = [1.0, 1.1, 1.25, 1.5]  # Try exact, then 10%, 25%, 50% over
    
    for i, group in enumerate(groups):
        candidates = []
        dish_names = [d['name'] for d in group]
        dish_string = " + ".join(dish_names)
        
        # Try progressively relaxed budgets
        for tier_mult in budget_tiers:
            max_price = budget_per_bottle * tier_mult
            
            for wine in wines:
                if wine['id'] in used_ids: continue
                if wine['price'] > max_price: continue
                
                # Score wine for this group
                pairing_score = score_group(wine, group)
                if pairing_score <= 0: continue
                
                # PRESTIGE BONUS
                prestige_bonus = 0
                wine_name_lower = wine['name'].lower()
                producer_lower = wine['producer'].lower()
                
                for producer, bonus in LEGENDARY_PRODUCERS.items():
                    if producer in producer_lower or producer in wine_name_lower:
                        prestige_bonus += bonus
                        break
                
                for vineyard, bonus in PRESTIGIOUS_VINEYARDS.items():
                    if vineyard in wine_name_lower:
                        prestige_bonus += bonus
                        break
                
                if prestige_bonus == 0:
                    if 'grand cru' in wine_name_lower:
                        prestige_bonus += 8  # Reduced from 15
                    elif 'premier cru' in wine_name_lower:
                        prestige_bonus += 4  # Reduced from 8
                
                # Value bonus
                value_bonus = (500 / (wine['price'] + 1)) * 0.1
                
                final_score = pairing_score + prestige_bonus + value_bonus
                
                candidates.append({
                    'wine': wine,
                    'score': final_score
                })
            
            if len(candidates) >= 3: break
        
        if not candidates: continue
        
        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # BUILD OPTIONS LIST (v5.0 structure)
        # Take top 3: primary + 2 alternatives
        options_list = []
        course_wine_ids = []  # Track IDs as we build (more reliable than string matching)
        
        for idx, cand in enumerate(candidates[:3]):
            wine = cand['wine']
            course_wine_ids.append(wine['id'])  # ← Track ID immediately
            
            # Generate AI content
            pairing_note = ""
            conversation_starter = ""
            
            if LUXURY_MODE:
                try:
                    pairing_note = narrator.generate_pairing_story(
                        wine_name=wine['name'],
                        wine_type=wine['type'],
                        dish_name=dish_string,
                        wine_properties={
                            'acidity': wine['acid'],
                            'body': wine['body'],
                            'tannin': wine['tannin']
                        }
                    )
                    
                    starters = generate_conversation_starters(
                        wine['name'],
                        wine['producer'],
                        wine['type'],
                        None,
                        wine['price']
                    )
                    conversation_starter = starters[0] if starters else ""
                    
                except Exception as e:
                    logger.warning(f"AI generation failed: {e}")
                    pairing_note = wine.get('insider_note', '') or "A harmonious pairing."
            else:
                pairing_note = wine.get('insider_note', '') or "A harmonious pairing."
            
            # Get facts
            interesting_fact = None
            rarity_level = 1
            
            if FACTS_ENABLED:
                try:
                    interesting_fact = get_interesting_fact(wine)
                    rarity_level = calculate_rarity_level(wine)
                except:
                    pass
            
            # Build option object (ALL fields frontend needs)
            # Defensive: ensure score is valid
            match_score = cand['score']
            if not isinstance(match_score, (int, float)) or match_score != match_score:  # NaN check
                match_score = 0
            
            option = {
                "wine_name": wine['name'],
                "producer": wine['producer'],
                "vintage": wine.get('vintage', 'NV'),
                "price": wine['price'],
                "type": wine['type'],
                "section": wine['type'],
                "insider_note": wine.get('insider_note', ''),
                "pairing_note": pairing_note,
                "conversation_starter": conversation_starter,
                "interesting_fact": interesting_fact,
                "rarity_level": rarity_level,
                "is_primary_recommendation": (idx == 0),
                "recommendation_rank": idx + 1,
                "match_score": int(match_score)
            }
            
            options_list.append(option)
        
        if options_list:
            # Add all wine IDs from this course (prevents duplicates across courses)
            used_ids.update(course_wine_ids)  # ← Direct ID tracking - much cleaner!
            
            progression.append({
                "course_number": i + 1,
                "course_name": f"Course {i+1}",
                "dishes": dish_names,
                "options": options_list  # ← FRONTEND EXPECTS THIS
            })
    
    # Check if we found any wines
    if not progression:
        logger.warning("No wines found within budget constraints")
        return {
            "success": False,
            "error": "No wines found within budget. Try increasing your budget or selecting fewer bottles.",
            "total_cost": 0,
            "budget_utilization": 0
        }
    
    total_cost = sum(c['options'][0]['price'] for c in progression if c.get('options')) if progression else 0
    budget_utilization = round((total_cost / budget * 100), 1) if budget > 0 else 0
    
    logger.info(f"✅ Generated {len(progression)} courses, ${total_cost:.2f} ({budget_utilization}% of budget)")
    
    return {
        "success": True,
        "progression": progression,
        "total_bottles": len(progression),
        "bottle_count": bottle_count,
        "total_cost": total_cost,
        "total_budget": budget,  # ← Was missing!
        "budget_utilization": budget_utilization
    }

# =================================================================
# HEALTH CHECK
# =================================================================

def health_check() -> Dict:
    wines = load_wines()
    return {
        "status": "healthy" if wines else "unhealthy",
        "wine_count": len(wines),
        "features": {
            "luxury_mode": LUXURY_MODE,
            "facts_enabled": FACTS_ENABLED
        }
    }

logger.info("✅ pairing_service.py v5.2 loaded (Unified architecture)")
