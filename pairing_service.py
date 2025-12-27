"""
VELORA PAIRING SERVICE - V2.0 INTEGRATED (GEMINI FIX)
✅ Combines existing functional logic with V2.0 progression
✅ Uses load_wines(), score_wine() - NO PairingEngine class
✅ Table/group pairing logic properly integrated
"""
import csv
import os
import statistics
from typing import List, Dict, Tuple
from functools import lru_cache

# Import Luxury Modules
try:
    from sommelier_narrator import narrator
    from conversation_starter import generate_conversation_starters
    LUXURY_MODE = True
except ImportError:
    LUXURY_MODE = False
    print("⚠️ Running without luxury features (sommelier_narrator/conversation_starter not found)")

# =================================================================
# CORE WINE DATABASE LOADER
# =================================================================

_wine_cache = None

def load_wines() -> List[Dict]:
    """
    Load wine database from CSV.
    Uses caching to avoid reloading.
    """
    global _wine_cache
    if _wine_cache:
        return _wine_cache
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try multiple paths
    paths = [
        os.path.join(script_dir, 'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv'),
        'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv',
        os.path.join(script_dir, 'MASTER_WINE_DATABASE.csv'),
        'MASTER_WINE_DATABASE.csv'
    ]
    
    for path in paths:
        if os.path.exists(path):
            try:
                wines = []
                with open(path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Determine wine type from section
                        section = row.get('section', '').lower()
                        w_type = 'Red'
                        if 'white' in section:
                            w_type = 'White'
                        elif 'sparkling' in section or 'champagne' in section:
                            w_type = 'Sparkling'
                        elif 'dessert' in section or 'sweet' in section:
                            w_type = 'Dessert'
                        elif 'rose' in section or 'rosé' in section:
                            w_type = 'Rosé'
                        
                        wines.append({
                            'id': len(wines),
                            'name': row.get('wine_name', '').strip(),
                            'producer': row.get('producer', '').strip(),
                            'price': float(row.get('price', 0) or 0),
                            'type': w_type,
                            'vintage': row.get('vintage', '').strip(),
                            'acid': float(row.get('acidity', 5) or 5),
                            'tannin': float(row.get('tannin', 5) or 5),
                            'body': float(row.get('body', 5) or 5),
                            'sugar': float(row.get('sweetness', 1) or 1),
                            'tags': row.get('pairing_tags', '').lower(),
                            'why': row.get('insider_note', '').strip()
                        })
                
                _wine_cache = wines
                print(f"✅ Loaded {len(wines)} wines from {path}")
                return wines
                
            except Exception as e:
                print(f"❌ CSV load error from {path}: {e}")
                continue
    
    print("❌ No wine database found")
    return []

# =================================================================
# DISH ANALYSIS
# =================================================================

def analyze_dish(food_input: str) -> Dict:
    """
    Analyze dish characteristics for pairing.
    Returns profile dict with key properties.
    """
    f = food_input.lower()
    
    profile = {
        'fat_level': 5,
        'protein_level': 5,
        'sweetness_level': 1,
        'acidity_level': 3,
        'umami_level': 3,
        'is_dessert': False,
        'is_delicate': False,
        'has_seafood': False,
        'has_red_meat': False,
        'has_spice': False
    }
    
    # Dessert detection
    if any(w in f for w in ['cake', 'chocolate', 'dessert', 'ice cream', 'tart', 'pie']):
        profile.update({
            'is_dessert': True,
            'sweetness_level': 9
        })
    
    # Red meat detection
    elif any(w in f for w in ['steak', 'beef', 'lamb', 'ribeye', 'wagyu', 'veal']):
        profile.update({
            'has_red_meat': True,
            'protein_level': 9,
            'fat_level': 8
        })
    
    # Seafood detection
    elif any(w in f for w in ['fish', 'oyster', 'scallop', 'lobster', 'crab', 'shrimp', 'salmon', 'tuna', 'bass', 'halibut']):
        profile.update({
            'has_seafood': True,
            'is_delicate': True,
            'protein_level': 7,
            'fat_level': 3
        })
    
    # Poultry
    elif any(w in f for w in ['chicken', 'duck', 'turkey']):
        profile.update({
            'protein_level': 7,
            'fat_level': 6
        })
    
    # Rich/fatty foods
    if any(w in f for w in ['cream', 'butter', 'cheese', 'carbonara', 'alfredo']):
        profile['fat_level'] = min(10, profile['fat_level'] + 3)
    
    # Spicy foods
    if any(w in f for w in ['spicy', 'hot', 'chili', 'jalapeño']):
        profile['has_spice'] = True
    
    # Acidic foods
    if any(w in f for w in ['tomato', 'lemon', 'vinegar', 'citrus']):
        profile['acidity_level'] = 7
    
    return profile

# =================================================================
# WINE SCORING
# =================================================================

def score_wine(wine: Dict, dish_profile: Dict) -> float:
    """
    Score how well a wine pairs with a dish profile.
    Returns score 0-100.
    """
    score = 0.0
    
    fat = dish_profile['fat_level']
    protein = dish_profile['protein_level']
    is_dessert = dish_profile['is_dessert']
    has_seafood = dish_profile['has_seafood']
    has_red_meat = dish_profile['has_red_meat']
    has_spice = dish_profile['has_spice']
    
    # Rule 1: Fat needs Acid (most important for rich dishes)
    if fat >= 7:
        if wine['acid'] >= 7:
            score += 30
        elif wine['acid'] >= 5:
            score += 15
        else:
            score -= 10
    
    # Rule 2: Protein needs Tannin (especially red meat)
    if protein >= 7:
        if wine['type'] == 'Red' and wine['tannin'] >= 7:
            score += 30
        elif wine['type'] == 'Red' and wine['tannin'] >= 5:
            score += 15
    
    # Rule 3: Sweetness matching
    if is_dessert:
        if wine['sugar'] >= 6:
            score += 40  # Sweet wine with dessert
        else:
            score -= 30  # Dry wine with dessert
    else:
        # Savory food
        if wine['sugar'] >= 6:
            score -= 20  # Sweet wine with savory food
        else:
            score += 10  # Dry wine with savory food
    
    # Rule 4: Seafood preferences
    if has_seafood:
        if wine['type'] in ['White', 'Sparkling']:
            score += 25
        elif wine['type'] == 'Red':
            score -= 20  # Red wine with delicate fish
    
    # Rule 5: Red meat preferences
    if has_red_meat:
        if wine['type'] == 'Red':
            score += 20
        elif wine['type'] == 'White':
            score -= 10
    
    # Rule 6: Spicy food
    if has_spice:
        if wine['sugar'] >= 3:
            score += 15  # Slight sweetness helps with spice
        if wine['tannin'] <= 4:
            score += 10  # Low tannin better with spice
    
    # Ensure non-negative
    return max(0, score)

# =================================================================
# SINGLE DISH RECOMMENDATION (V1.0 Compatible)
# =================================================================

def get_recommendation(food_input: str, budget: int = 1000) -> Dict:
    """
    Get wine recommendation for a single dish.
    V1.0 compatible endpoint.
    """
    wines = load_wines()
    
    if not wines:
        return {
            "success": False,
            "error": "Wine database not available"
        }
    
    dish_profile = analyze_dish(food_input)
    
    # Score all affordable wines
    candidates = []
    for wine in wines:
        if wine['price'] <= budget * 1.1:  # Allow 10% over budget
            wine_score = score_wine(wine, dish_profile)
            if wine_score > 0:
                candidates.append({
                    'wine': wine,
                    'score': wine_score
                })
    
    # Sort by score
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    if not candidates:
        return {
            "success": False,
            "message": "No suitable wines found within budget"
        }
    
    best = candidates[0]['wine']
    
    # Generate luxury content
    luxury = {}
    if LUXURY_MODE:
        try:
            story = narrator.generate_pairing_story(
                wine_name=best['name'],
                wine_type=best['type'],
                dish_name=food_input,
                wine_properties={
                    'acidity': best['acid'],
                    'tannin': best['tannin'],
                    'body': best['body']
                }
            )
            
            starters = generate_conversation_starters(
                wine_name=best['name'],
                producer=best['producer'],
                wine_type=best['type'],
                price=best['price']
            )
            
            luxury = {
                'pairing_note': story,
                'conversation_starters': starters
            }
        except Exception as e:
            print(f"⚠️ Luxury content generation failed: {e}")
            luxury = {
                'pairing_note': f"This {best['type']} wine pairs excellently with {food_input}.",
                'conversation_starters': []
            }
    
    return {
        "success": True,
        "wine": {
            "wine_name": best['name'],
            "producer": best['producer'],
            "price": best['price'],
            "type": best['type'],
            "score": candidates[0]['score']
        },
        "luxury": luxury,
        "reasoning": {
            "why": best['why']
        }
    }

# =================================================================
# V2.0: TABLE/GROUP PROGRESSION LOGIC
# =================================================================

def classify_dish_type(dish_name: str) -> Dict:
    """
    Classify dish for grouping into courses.
    Returns type, wine preference, and weight (1-10).
    """
    d = dish_name.lower()
    
    # Light/delicate foods
    if any(x in d for x in ['oyster', 'ceviche', 'carpaccio', 'salad', 'vegetable', 'soup']):
        return {'type': 'light', 'pref': 'white', 'weight': 2}
    
    # Seafood (generally light-medium)
    if any(x in d for x in ['fish', 'tuna', 'salmon', 'scallop', 'lobster', 'crab', 'halibut', 'bass']):
        return {'type': 'seafood', 'pref': 'white', 'weight': 4}
    
    # Poultry (medium)
    if any(x in d for x in ['chicken', 'turkey', 'veal']):
        return {'type': 'poultry', 'pref': 'versatile', 'weight': 6}
    
    # Rich poultry/game
    if any(x in d for x in ['duck', 'quail', 'venison']):
        return {'type': 'game', 'pref': 'red', 'weight': 7}
    
    # Red meat (heavy)
    if any(x in d for x in ['steak', 'beef', 'lamb', 'ribeye', 'wagyu', 'short rib']):
        return {'type': 'red_meat', 'pref': 'red', 'weight': 9}
    
    # Pasta (depends on sauce)
    if 'pasta' in d or 'risotto' in d:
        if any(x in d for x in ['cream', 'carbonara', 'alfredo']):
            return {'type': 'rich_pasta', 'pref': 'white', 'weight': 5}
        elif any(x in d for x in ['ragu', 'bolognese', 'meat']):
            return {'type': 'meat_pasta', 'pref': 'red', 'weight': 7}
        else:
            return {'type': 'pasta', 'pref': 'versatile', 'weight': 5}
    
    # Default: medium weight, versatile
    return {'type': 'medium', 'pref': 'versatile', 'weight': 5}

def group_dishes(dishes: List[str], bottle_count: int) -> List[List[Dict]]:
    """
    Group dishes into courses based on weight and wine compatibility.
    Returns list of dish groups (one group per bottle).
    """
    # Classify all dishes
    classified = [{'name': d, **classify_dish_type(d)} for d in dishes]
    
    if bottle_count == 1:
        # All dishes in one group
        return [classified]
    
    elif bottle_count == 2:
        # Split into light vs heavy
        light = [d for d in classified if d['weight'] <= 5]
        heavy = [d for d in classified if d['weight'] > 5]
        
        # Handle edge cases
        if not light and not heavy:
            return [classified]
        elif not light:
            # All heavy: split in half
            mid = len(heavy) // 2
            return [heavy[:mid], heavy[mid:]]
        elif not heavy:
            # All light: split in half
            mid = len(light) // 2
            return [light[:mid], light[mid:]]
        else:
            # Normal case: light first, heavy second
            return [light, heavy]
    
    elif bottle_count == 3:
        # Sort by weight and split into thirds
        sorted_dishes = sorted(classified, key=lambda x: x['weight'])
        
        third = max(1, len(sorted_dishes) // 3)
        
        group1 = sorted_dishes[:third]
        group2 = sorted_dishes[third:third*2]
        group3 = sorted_dishes[third*2:]
        
        return [group1, group2, group3]
    
    else:
        # Fallback
        return [classified]

def score_wine_for_group(wine: Dict, dish_group: List[Dict]) -> float:
    """
    Score wine for MULTIPLE dishes (table pairing).
    Returns average compatibility score.
    """
    if not dish_group:
        return 0.0
    
    scores = []
    for dish in dish_group:
        profile = analyze_dish(dish['name'])
        dish_score = score_wine(wine, profile)
        scores.append(dish_score)
    
    # Calculate average
    avg_score = statistics.mean(scores)
    
    # Penalty if wine fails badly with any dish
    min_score = min(scores)
    if min_score < 20:
        avg_score -= 20  # Significant penalty for poor compatibility
    
    return max(0, avg_score)

def generate_progression(dishes: List[str], bottle_count: int, budget: int) -> Dict:
    """
    Generate wine progression for table/group dining.
    
    Args:
        dishes: List of dish names
        bottle_count: Number of bottles (1-3)
        budget: Total budget for all bottles
    
    Returns:
        Progression dict with courses and wine recommendations
    """
    wines = load_wines()
    
    if not wines:
        return {
            "success": False,
            "error": "Wine database not available"
        }
    
    # Group dishes intelligently
    groups = group_dishes(dishes, bottle_count)
    
    # Budget per bottle
    budget_per_bottle = budget // bottle_count
    
    progression = []
    used_ids = set()
    
    for i, group in enumerate(groups):
        candidates = []
        dish_names = [d['name'] for d in group]
        
        # Score all affordable wines for this group
        for wine in wines:
            if wine['id'] in used_ids:
                continue
            if wine['price'] > budget_per_bottle * 1.2:  # Allow 20% over
                continue
            
            group_score = score_wine_for_group(wine, group)
            
            if group_score > 0:
                candidates.append({
                    'wine': wine,
                    'score': group_score
                })
        
        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        if not candidates:
            # No wines found for this group
            continue
        
        # Select best wine
        best = candidates[0]['wine']
        used_ids.add(best['id'])
        
        # Generate luxury content
        luxury = {}
        if LUXURY_MODE:
            try:
                combined_dishes = " + ".join(dish_names)
                
                note = narrator.generate_pairing_story(
                    wine_name=best['name'],
                    wine_type=best['type'],
                    dish_name=combined_dishes,
                    wine_properties={
                        'acidity': best['acid'],
                        'tannin': best['tannin'],
                        'body': best['body']
                    }
                )
                
                starters = generate_conversation_starters(
                    wine_name=best['name'],
                    producer=best['producer'],
                    wine_type=best['type'],
                    price=best['price']
                )
                
                luxury = {
                    'pairing_note': note,
                    'conversation_starters': starters
                }
            except Exception as e:
                print(f"⚠️ Luxury content error for course {i+1}: {e}")
                luxury = {
                    'pairing_note': f"This {best['type']} wine complements all dishes in this course.",
                    'conversation_starters': []
                }
        
        # Determine course name
        course_name = "Opening Course" if i == 0 else "Main Course"
        if i == len(groups) - 1:
            course_name = "Grand Finale"
        
        # Generate luxury content for alternatives
        alternatives_with_luxury = []
        for alt_candidate in candidates[1:3]:  # Top 2 alternatives
            alt_wine = alt_candidate['wine']
            alt_luxury = {}
            
            if LUXURY_MODE:
                try:
                    combined_dishes = " + ".join(dish_names)
                    
                    # Generate pairing note for alternative
                    alt_note = narrator.generate_pairing_story(
                        wine_name=alt_wine['name'],
                        wine_type=alt_wine['type'],
                        dish_name=combined_dishes,
                        wine_properties={
                            'acidity': alt_wine['acid'],
                            'tannin': alt_wine['tannin'],
                            'body': alt_wine['body']
                        }
                    )
                    
                    # Generate conversation starters for alternative
                    alt_starters = generate_conversation_starters(
                        wine_name=alt_wine['name'],
                        producer=alt_wine['producer'],
                        wine_type=alt_wine['type'],
                        price=alt_wine['price']
                    )
                    
                    alt_luxury = {
                        'pairing_note': alt_note,
                        'conversation_starters': alt_starters
                    }
                except Exception as e:
                    print(f"⚠️ Alternative luxury content error: {e}")
                    alt_luxury = {
                        'pairing_note': f"An excellent alternative {alt_wine['type']} wine for this course.",
                        'conversation_starters': []
                    }
            
            alternatives_with_luxury.append({
                "wine_name": alt_wine['name'],
                "producer": alt_wine['producer'],
                "price": alt_wine['price'],
                "type": alt_wine['type'],
                "compatibility_score": round(alt_candidate['score'], 1),
                "pairing_note": alt_luxury.get('pairing_note', ''),
                "conversation_starters": alt_luxury.get('conversation_starters', [])
            })
        
        # Build course entry
        progression.append({
            "course_number": i + 1,
            "course_name": course_name,
            "dishes": dish_names,
            "dish_count": len(dish_names),
            "primary": {
                "wine_name": best['name'],
                "producer": best['producer'],
                "price": best['price'],
                "type": best['type'],
                "compatibility_score": round(candidates[0]['score'], 1)
            },
            "luxury": luxury,
            "alternatives": alternatives_with_luxury
        })
    
    return {
        "success": True,
        "bottle_count": bottle_count,
        "total_budget": budget,
        "budget_per_bottle": budget_per_bottle,
        "progression": progression,
        "pairing_philosophy": f"Table pairing for {len(dishes)} dishes across {bottle_count} bottle(s)"
    }
