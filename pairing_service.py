"""
VELORA PAIRING SERVICE - V5.0 STABLE ARCHITECTURE
✅ Stable IDs: Persist across CSV sorts/edits (CRITICAL FIX)
✅ Vintage Safe: IDs based on Producer+Name only (handles inventory rolls)
✅ Dual Lookup: Returns both list and dictionary
✅ All V4.0 features preserved: Regional matching, texture pairing, 11-layer algorithm
"""
import csv
import os
import re
import unicodedata
import hashlib
from typing import List, Dict, Tuple
from functools import lru_cache

# Import Luxury Modules
try:
    from sommelier_narrator import narrator
    from conversation_starter import generate_conversation_starters
    LUXURY_MODE = True
except ImportError:
    LUXURY_MODE = False

# Import Facts Database (V5.0)
try:
    from facts_database import get_interesting_fact, calculate_rarity_level
    FACTS_ENABLED = True
except ImportError:
    FACTS_ENABLED = False
    print("⚠️  Facts database not found - install facts_database.py")

# =================================================================
# 1. STABLE ID GENERATION (THE FOUNDATION - GEMINI'S FIX)
# =================================================================

def slugify(text: str) -> str:
    """
    Creates a URL-safe, readable identifier.
    Handles unicode, accents, special characters.
    
    Examples:
        "Château Margaux" → "chateau_margaux"
        "Domaine de la Romanée-Conti" → "domaine_de_la_romanee_conti"
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Normalize unicode (Château → Chateau, é → e)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Lowercase
    text = text.lower()
    
    # Remove non-alphanumeric (keep spaces and hyphens temporarily)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    
    # Replace spaces and hyphens with underscores
    text = re.sub(r'[\s-]+', '_', text)
    
    # Clean up trailing/leading underscores
    return text.strip('_')

def generate_stable_id(producer: str, name: str) -> str:
    """
    Generates a persistent ID based on identity, NOT position.
    CRITICAL: Does NOT include vintage (Gemini's insight - handles inventory rollover)
    
    Examples:
        "Château Margaux", "Pavillon Rouge" → "chateau_margaux_pavillon_rouge"
        "Jordan", "Cabernet Sauvignon" → "jordan_cabernet_sauvignon"
    
    The vintage changes (2018→2019), but ID stays the same!
    """
    slug = f"{slugify(producer)}_{slugify(name)}"
    
    # Handle very long names (database column limits)
    if len(slug) > 64:
        # Keep first 55 chars + hash of full string for uniqueness
        hash_suffix = hashlib.md5(slug.encode()).hexdigest()[:8]
        slug = f"{slug[:55]}_{hash_suffix}"
    
    return slug

# =================================================================
# 2. DATABASE LOADER (THE FIX - STABLE IDS)
# =================================================================

_wine_list_cache = None
_wine_dict_cache = None

def load_wines() -> Tuple[List[Dict], Dict[str, Dict]]:
    """
    Load wines with Stable IDs.
    
    Returns:
        Tuple of (wines_list, wines_dict)
        - wines_list: List of wine objects (for iteration)
        - wines_dict: Dictionary lookup by stable ID (for curated pairings)
    
    CRITICAL CHANGE: IDs are now stable strings like "chateau_margaux_pavillon_rouge"
    instead of position-based integers like 123.
    """
    global _wine_list_cache, _wine_dict_cache
    if _wine_list_cache and _wine_dict_cache:
        return _wine_list_cache, _wine_dict_cache
    
    # STRICT WINE-ONLY SECTIONS (from V4.0)
    VALID_WINE_SECTIONS = {
        'red wine', 'white wine', 'sparkling', 'champagne', 'rosé', 'rose', 'dessert wine',
        'red wines', 'white wines', 'sparkling wines', 'champagne & sparkling',
        'french red wine', 'french white wine', 'italian red wine', 'italian white wine',
        'spanish red wine', 'spanish white wine', 'usa red wine', 'domestic red wine',
        'napa valley cabernet', 'bordeaux', 'burgundy', 'red burgundy', 'white burgundy',
        'pinot noir', 'cabernet sauvignon', 'chardonnay', 'sauvignon blanc', 'riesling',
        'champagne & sparkling wines', 'red', 'white', 'sparkling wine'
    }
    
    # BLACKLIST - explicitly exclude these (from V4.0)
    EXCLUDE_SECTIONS = {
        'spirits', 'beer', 'cocktails', 'cocktail', 'grappa', 'amari',
        'italian amari', 'aperitif', 'digestif', 'liqueur', 'liquor',
        'zero proof', 'non-alcoholic', 'non alcoholic', 'non alcoholic beverages',
        'non-alcoholic/low alcohol', 'low alcohol',
        'other beverages', 'beverages',
        'water', 'mineral water', 'sparkling water',
        'general', 'à la carte', 'entrees', 'appetizers', 'desserts', 'sides',
        'reserve list', 'large format', 'half bottles', 'by the glass', 'btg'
    }
    
    # BLACKLIST - non-wine items in names (from V4.0)
    EXCLUDE_NAMES = {
        'egg', 'water', 'beer', 'ale', 'lager', 'vodka', 'whiskey', 'whisky', 'gin',
        'rum', 'tequila', 'mezcal', 'cognac', 'brandy', 'coffee', 'tea', 'soda',
        'juice', 'budweiser', 'coors', 'miller', 'corona'
    }
    
    # BOTTLE-ONLY FILTER (from V4.0)
    VALID_BOTTLE_SIZES = {
        '750ml', '750', '1.5l', '1500ml', 'magnum', '3l', '3000ml', 'double magnum',
        '6l', '6000ml', 'imperial', '375ml', 'half bottle', '500ml', 'nv', '2019',
        '2020', '2021', '2022', '2023', '2024'
    }
    
    GLASS_INDICATORS = {
        'glass', 'glass pour', 'by the glass', 'btg', 'pour'
    }
    
    MINIMUM_BOTTLE_PRICE = 20.0
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(script_dir, 'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv'),
        'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv'
    ]
    
    wines_list = []
    wines_dict = {}
    seen_ids = {}  # Track for collision detection
    
    for path in paths:
        if os.path.exists(path):
            try:
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
                        is_valid_section = any(valid in section for valid in VALID_WINE_SECTIONS)
                        
                        if not is_valid_section and section:
                            # Skip unless we can identify it's wine from other clues
                            if not row.get('producer', '').strip():
                                continue
                        
                        try:
                            price = float(row.get('price', 0))
                            if price <= 0:
                                continue
                            
                            # BOTTLE-ONLY FILTER
                            if price < MINIMUM_BOTTLE_PRICE:
                                continue
                            
                            bottle_size = row.get('bottle_size', '').strip().lower()
                            
                            if any(glass_ind in bottle_size for glass_ind in GLASS_INDICATORS):
                                continue
                            
                            if bottle_size.isdigit():
                                ml_size = int(bottle_size)
                                if ml_size < 375:
                                    continue
                            
                            if bottle_size and not any(valid in bottle_size for valid in VALID_BOTTLE_SIZES):
                                continue
                        
                        except:
                            continue
                        
                        # ===== CRITICAL CHANGE: STABLE ID GENERATION =====
                        producer = row.get('producer', '').strip()
                        
                        # Generate stable ID (no vintage!)
                        base_id = generate_stable_id(producer, wine_name)
                        
                        # Handle collision (same wine listed twice in CSV)
                        if base_id in seen_ids:
                            seen_ids[base_id] += 1
                            wine_id = f"{base_id}_{seen_ids[base_id]}"
                        else:
                            seen_ids[base_id] = 1
                            wine_id = base_id
                        
                        # Create wine object
                        wine_obj = {
                            'id': wine_id,  # ← STABLE STRING ID
                            'name': wine_name,
                            'producer': producer,
                            'vintage': row.get('vintage', '').strip(),  # ← Data, not identity
                            'price': price,
                            'type': row.get('section', 'Red'),
                            'acid': float(row.get('acidity', 5) or 5),
                            'tannin': float(row.get('tannin', 5) or 5),
                            'body': float(row.get('body', 5) or 5),
                            'sugar': float(row.get('sweetness', 1) or 1),
                            'why': row.get('insider_note', ''),
                            'tags': []  # Will populate in Phase 2
                        }
                        
                        wines_list.append(wine_obj)
                        wines_dict[wine_id] = wine_obj
                
                _wine_list_cache = wines_list
                _wine_dict_cache = wines_dict
                
                print(f"✅ Loaded {len(wines_list)} wines with STABLE IDs")
                print(f"   Sample IDs: {list(wines_dict.keys())[:3]}")
                return wines_list, wines_dict
            
            except Exception as e:
                print(f"❌ Error loading wines: {e}")
                continue
    
    print(f"❌ No wine database found")
    return [], {}

# =================================================================
# 3. ALL V4.0 PAIRING LOGIC (PRESERVED)
# =================================================================

# Regional matching database (from V4.0)
REGIONAL_PAIRINGS = {
    'italian': {
        'keywords': ['pasta', 'risotto', 'osso buco', 'carbonara', 'bolognese', 
                     'parmigiana', 'prosciutto', 'mozzarella', 'italian', 'tuscan',
                     'sicilian', 'neapolitan', 'venetian', 'piedmont'],
        'wine_regions': ['italy', 'italian', 'tuscany', 'piedmont', 'veneto', 'sicily',
                        'chianti', 'barolo', 'barbaresco', 'brunello', 'montepulciano',
                        'vermentino', 'pinot grigio', 'soave']
    },
    'french': {
        'keywords': ['coq au vin', 'cassoulet', 'confit', 'ratatouille', 'bouillabaisse',
                     'french', 'provençal', 'burgundy', 'lyonnaise'],
        'wine_regions': ['france', 'french', 'bordeaux', 'burgundy', 'rhône', 'rhone',
                        'loire', 'alsace', 'champagne', 'côtes', 'cotes', 'beaujolais']
    },
    'spanish': {
        'keywords': ['paella', 'tapas', 'jamón', 'jamon', 'chorizo', 'gazpacho',
                     'spanish', 'basque', 'catalan', 'andalusian'],
        'wine_regions': ['spain', 'spanish', 'rioja', 'ribera', 'priorat', 'navarra',
                        'rías baixas', 'rias baixas', 'rueda', 'albariño', 'albarino',
                        'tempranillo', 'garnacha']
    },
    'asian': {
        'keywords': ['sushi', 'sashimi', 'tempura', 'teriyaki', 'ramen', 'pho',
                     'pad thai', 'curry', 'dim sum', 'szechuan', 'chinese', 'japanese',
                     'thai', 'vietnamese', 'korean'],
        'wine_regions': []  # Asian food pairs with many regions, focus on style
    },
    'american': {
        'keywords': ['burger', 'bbq', 'brisket', 'ribs', 'steak', 'american'],
        'wine_regions': ['california', 'napa', 'sonoma', 'paso robles', 'oregon',
                        'washington', 'usa', 'american']
    }
}

# Texture pairing database (from V4.0)
TEXTURE_PAIRINGS = {
    'crispy': {
        'keywords': ['crispy', 'fried', 'tempura', 'crunchy', 'breaded', 'crusted'],
        'wine_styles': ['sparkling', 'champagne', 'high acid', 'light body']
    },
    'creamy': {
        'keywords': ['creamy', 'cream sauce', 'alfredo', 'béchamel', 'rich sauce'],
        'wine_styles': ['full body', 'oak', 'chardonnay', 'white burgundy']
    },
    'rich': {
        'keywords': ['rich', 'fatty', 'butter', 'foie gras', 'duck confit'],
        'wine_styles': ['high acid', 'sparkling', 'dessert wine']
    },
    'light': {
        'keywords': ['light', 'delicate', 'steamed', 'poached', 'fresh'],
        'wine_styles': ['light body', 'crisp', 'refreshing', 'pinot grigio', 'vinho verde']
    }
}

def analyze_dish(dish_name: str, dish_description: str = "") -> Dict:
    """
    Analyzes a dish to extract pairing characteristics.
    Uses BOTH name and description (V4.0 enhancement).
    """
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
        'fat_level': 5,
        'cuisine': None,
        'texture': None
    }
    
    # Seafood detection
    seafood = ['fish', 'salmon', 'tuna', 'cod', 'halibut', 'sea bass', 'shellfish', 
               'lobster', 'crab', 'shrimp', 'scallop', 'oyster', 'mussel', 'clam']
    if any(item in combined for item in seafood):
        profile['has_seafood'] = True
    
    # Red meat detection
    red_meat = ['beef', 'steak', 'ribeye', 'sirloin', 'filet', 'lamb', 'venison', 
                'bison', 'short rib', 'prime rib', 'wagyu']
    if any(item in combined for item in red_meat):
        profile['has_red_meat'] = True
    
    # Poultry detection
    poultry = ['chicken', 'duck', 'turkey', 'quail', 'pheasant', 'poussin']
    if any(item in combined for item in poultry):
        profile['has_poultry'] = True
    
    # Spice detection
    spicy = ['spicy', 'hot', 'chili', 'jalapeño', 'sriracha', 'curry', 'cayenne']
    if any(item in combined for item in spicy):
        profile['is_spicy'] = True
    
    # Dessert detection
    dessert = ['dessert', 'chocolate', 'cake', 'tart', 'mousse', 'ice cream', 
               'sorbet', 'pudding', 'sweet', 'fruit']
    if any(item in combined for item in dessert):
        profile['is_dessert'] = True
    
    # Sauce detection (V4.0 enhancement)
    if any(s in combined for s in ['béarnaise', 'bearnaise', 'hollandaise', 'cream sauce', 
                                     'butter sauce', 'beurre blanc']):
        profile['sauce_type'] = 'rich_cream'
        profile['fat_level'] = 8
    elif any(s in combined for s in ['tomato', 'marinara', 'red sauce', 'pomodoro']):
        profile['sauce_type'] = 'tomato'
    elif any(s in combined for s in ['soy', 'teriyaki', 'hoisin']):
        profile['sauce_type'] = 'umami'
        profile['umami_level'] = 7
    
    # Umami level (V4.0 enhancement)
    if any(u in combined for u in ['truffle', 'mushroom', 'parmesan', 'aged cheese']):
        profile['umami_level'] = 9
    elif any(u in combined for u in ['soy', 'miso', 'fish sauce']):
        profile['umami_level'] = 8
    
    # Cuisine detection (V4.0 enhancement)
    for cuisine, data in REGIONAL_PAIRINGS.items():
        if any(keyword in combined for keyword in data['keywords']):
            profile['cuisine'] = cuisine
            break
    
    # Texture detection (V4.0 enhancement)
    for texture, data in TEXTURE_PAIRINGS.items():
        if any(keyword in combined for keyword in data['keywords']):
            profile['texture'] = texture
            break
    
    return profile

def score_wine(wine: Dict, dish_profile: Dict) -> int:
    """
    11-Layer scoring algorithm (V4.0 complete).
    Returns score 0-200+
    """
    score = 50  # Base score
    wine_name_lower = wine['name'].lower()
    wine_type_lower = wine['type'].lower()
    wine_producer_lower = wine.get('producer', '').lower()
    
    # Layer 1: Classic Pairings (+40)
    classic_pairs = {
        ('chablis', 'oyster'): 40,
        ('sancerre', 'goat cheese'): 40,
        ('barolo', 'truffle'): 40,
        ('sauternes', 'foie gras'): 40,
        ('champagne', 'caviar'): 40,
        ('riesling', 'spicy'): 40
    }
    
    for (wine_key, food_key), bonus in classic_pairs.items():
        if wine_key in wine_name_lower and food_key in dish_profile['name'].lower():
            score += bonus
    
    # Layer 2: Seafood Matching (+30)
    if dish_profile['has_seafood']:
        if 'white' in wine_type_lower or 'sparkling' in wine_type_lower:
            score += 30
        elif wine['acid'] >= 7:
            score += 25
    
    # Layer 3: Red Meat Pairing (+30)
    if dish_profile['has_red_meat']:
        if 'red' in wine_type_lower:
            score += 30
            if wine['tannin'] >= 7:
                score += 15  # High tannin for fatty meat
    
    # Layer 4: Sauce Matching (+20)
    if dish_profile['sauce_type'] == 'rich_cream':
        if wine['acid'] >= 7:
            score += 20  # Acid cuts cream
    elif dish_profile['sauce_type'] == 'tomato':
        if 'red' in wine_type_lower and wine['acid'] >= 6:
            score += 20
    
    # Layer 5: Body/Weight (+15)
    if dish_profile['fat_level'] >= 7:
        if wine['body'] >= 7:
            score += 15
    
    # Layer 6: Umami (+15)
    if dish_profile['umami_level'] >= 8:
        if wine['acid'] >= 7:
            score += 15
    
    # Layer 7: Asian Cuisine (+25)
    if dish_profile['cuisine'] == 'asian':
        if any(r in wine_name_lower for r in ['riesling', 'gewürztraminer', 'grüner']):
            score += 25
    
    # Layer 8: Spicy Food (+20)
    if dish_profile['is_spicy']:
        if wine['sugar'] >= 3 or 'riesling' in wine_name_lower:
            score += 20
    
    # Layer 9: Dessert (+40)
    if dish_profile['is_dessert']:
        if 'dessert' in wine_type_lower or 'port' in wine_name_lower:
            score += 40
    
    # Layer 10: Regional Matching (+25) - V4.0 NEW
    if dish_profile['cuisine']:
        cuisine_data = REGIONAL_PAIRINGS.get(dish_profile['cuisine'])
        if cuisine_data and cuisine_data['wine_regions']:
            wine_info = f"{wine_name_lower} {wine_producer_lower} {wine_type_lower}"
            if any(region in wine_info for region in cuisine_data['wine_regions']):
                score += 25
    
    # Layer 11: Texture Pairing (+15) - V4.0 NEW
    if dish_profile['texture']:
        texture_data = TEXTURE_PAIRINGS.get(dish_profile['texture'])
        if texture_data:
            wine_info = f"{wine_name_lower} {wine_type_lower}"
            if any(style in wine_info for style in texture_data['wine_styles']):
                score += 15
    
    return score

def generate_progression(dishes: List, bottle_count: int, budget: float) -> Dict:
    """
    Generate wine progression using all V4.0 logic with STABLE IDS.
    
    Args:
        dishes: List of dish objects with name/description/price
        bottle_count: Number of bottles to recommend
        budget: Total budget
    
    Returns:
        Dictionary with success status and wine progression
    """
    # Load wines with stable IDs
    wines_list, wines_dict = load_wines()
    
    if not wines_list:
        return {'success': False, 'error': 'No wines loaded'}
    
    # Normalize dish objects (V4.0 compatibility)
    normalized_dishes = []
    for dish in dishes:
        if isinstance(dish, dict):
            normalized_dishes.append(dish)
        elif isinstance(dish, str):
            normalized_dishes.append({'name': dish, 'description': '', 'price': 0})
        else:
            normalized_dishes.append({'name': str(dish), 'description': '', 'price': 0})
    
    # Analyze all dishes
    dish_profiles = []
    for dish in normalized_dishes:
        profile = analyze_dish(dish['name'], dish.get('description', ''))
        profile['price'] = dish.get('price', 0)
        dish_profiles.append(profile)
    
    # Group dishes by course (V4.0 logic)
    groups = []
    dishes_per_group = len(dish_profiles) // bottle_count
    remainder = len(dish_profiles) % bottle_count
    
    start_idx = 0
    for i in range(bottle_count):
        group_size = dishes_per_group + (1 if i < remainder else 0)
        end_idx = start_idx + group_size
        
        group_dishes = dish_profiles[start_idx:end_idx]
        groups.append({
            'dishes': [d['name'] for d in group_dishes],
            'profiles': group_dishes
        })
        
        start_idx = end_idx
    
    # Budget allocation
    budget_per_bottle = budget / bottle_count
    
    # Generate recommendations
    progression = []
    used_wines = set()
    
    for idx, group in enumerate(groups):
        # Score all wines for this group
        scored_wines = []
        for wine in wines_list:
            if wine['id'] in used_wines:
                continue
            
            # Calculate average score across all dishes in group
            total_score = 0
            for profile in group['profiles']:
                total_score += score_wine(wine, profile)
            
            avg_score = total_score / len(group['profiles']) if group['profiles'] else 0
            
            # Budget filter
            if wine['price'] <= budget_per_bottle * 1.3:  # 30% flexibility
                scored_wines.append((avg_score, wine))
        
        # Sort by score
        scored_wines.sort(reverse=True, key=lambda x: x[0])
        
        # Pick top 3 (primary + 2 alternatives)
        recommendations = []
        for score, wine in scored_wines[:3]:
            # Build base recommendation
            rec = {
                'wine_id': wine['id'],  # ← STABLE ID
                'wine_name': wine['name'],
                'producer': wine['producer'],
                'vintage': wine.get('vintage', 'NV'),
                'price': wine['price'],
                'type': wine['type'],
                'match_score': int(score),
                'reasoning': f"Pairs well with {', '.join(group['dishes'][:2])}"
            }
            
            # Add interesting fact if available (V5.0 enhancement)
            if FACTS_ENABLED:
                rec['interesting_fact'] = get_interesting_fact(wine)
                rec['rarity_level'] = calculate_rarity_level(wine)
            else:
                rec['interesting_fact'] = None
                rec['rarity_level'] = 1
            
            recommendations.append(rec)
        
        if recommendations:
            used_wines.add(recommendations[0]['wine_id'])
            
            progression.append({
                'course_number': idx + 1,
                'dishes': group['dishes'],
                'primary': recommendations[0],
                'alternatives': recommendations[1:] if len(recommendations) > 1 else []
            })
    
    return {
        'success': True,
        'progression': progression,
        'total_bottles': len(progression),
        'total_cost': sum(c['primary']['price'] for c in progression)
    }

# =================================================================
# 4. BACKWARD COMPATIBILITY
# =================================================================

def load_wines_legacy() -> List[Dict]:
    """
    Legacy function for backward compatibility.
    Returns just the list (old behavior).
    """
    wines_list, _ = load_wines()
    return wines_list
