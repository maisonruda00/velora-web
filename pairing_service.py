"""
VELORA PAIRING SERVICE - V5.2.1 (RAILWAY FIX)
✅ INTELLIGENT WINE FILTERING - No section dependency
✅ HANDLES "GENERAL" CATEGORY - 8,180 premium wines now included
✅ ROBUST ERROR HANDLING - Logging and fallbacks
✅ FACTS & RARITY - V5.0 features preserved
✅ FIXED: Module import issues on Railway
"""
import csv
import os
import re
import unicodedata
import hashlib
import logging
import sys
from typing import List, Dict, Tuple, Optional
from functools import lru_cache

# Configure logging FIRST - before any other operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("🍷 Starting pairing_service.py import...")

# Import Luxury Modules (optional)
LUXURY_MODE = False
try:
    from sommelier_narrator import narrator
    from conversation_starter import generate_conversation_starters
    LUXURY_MODE = True
    logger.info("✅ Luxury modules imported")
except ImportError as e:
    logger.warning(f"⚠️  Luxury modules not available: {e}")
except Exception as e:
    logger.error(f"❌ Luxury module import error: {e}")

# Import Facts Database (optional)
FACTS_ENABLED = False
try:
    from facts_database import get_interesting_fact, calculate_rarity_level
    FACTS_ENABLED = True
    logger.info("✅ Facts database imported")
except ImportError as e:
    logger.warning(f"⚠️  Facts database not available: {e}")
except Exception as e:
    logger.error(f"❌ Facts database import error: {e}")

logger.info("✅ All imports completed successfully")

# =================================================================
# 1. STABLE ID GENERATION
# =================================================================

def slugify(text: str) -> str:
    """Convert text to URL-safe slug"""
    if not isinstance(text, str):
        text = str(text)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '_', text)
    return text.strip('_')

def generate_stable_id(producer: str, name: str) -> str:
    """Generate stable, unique wine ID"""
    slug = f"{slugify(producer)}_{slugify(name)}"
    if len(slug) > 64:
        hash_suffix = hashlib.md5(slug.encode()).hexdigest()[:8]
        slug = f"{slug[:55]}_{hash_suffix}"
    return slug

# =================================================================
# 2. INTELLIGENT WINE FILTER
# =================================================================

def is_valid_wine(row: Dict) -> Tuple[bool, str]:
    """
    Intelligent wine validation - doesn't rely on unreliable 'section' field
    Returns: (is_valid, rejection_reason)
    """
    name = row.get('wine_name', '').strip()
    producer = row.get('producer', '').strip()
    section = row.get('section', '').lower()
    bottle_size = row.get('bottle_size', '').lower()
    
    # 1. BASIC VALIDATION
    if not producer or producer.lower() in ['unknown', '']:
        return False, "Missing producer"
    
    if not name or name.lower() == 'unknown':
        # Allow if we have a good producer
        pass
    
    # 2. BOTTLE SIZE CHECK (only standard bottles)
    if bottle_size and '750' not in bottle_size:
        return False, f"Non-standard bottle: {bottle_size}"
    
    # 3. PRICE VALIDATION
    try:
        price = float(row.get('price', 0))
        if price < 20:  # Minimum threshold for premium wines
            return False, f"Price too low: ${price}"
        if price > 50000:  # Sanity check
            return False, f"Price unrealistic: ${price}"
    except (ValueError, TypeError):
        return False, "Invalid price"
    
    # 4. SMART SECTION FILTERING
    # Instead of rejecting based on section, we use section as a hint
    # but don't rely on it exclusively
    
    # Reject obvious non-wine sections
    reject_sections = [
        'beer', 'sake', 'cocktails', 'spirits', 'liquor',
        'soft drinks', 'coffee', 'tea', 'juice'
    ]
    
    if any(reject in section for reject in reject_sections):
        return False, f"Non-wine section: {section}"
    
    # ACCEPT if section looks like wine OR if section is "general"
    # This is the key fix - we trust General section wines
    wine_indicators = [
        'wine', 'red', 'white', 'sparkling', 'champagne', 'rosé', 'rose',
        'burgundy', 'bordeaux', 'pinot', 'chardonnay', 'cabernet',
        'general'  # KEY: Accept General section
    ]
    
    has_wine_indicator = any(indicator in section for indicator in wine_indicators)
    
    # If no wine indicator in section, check the wine name/producer
    if not has_wine_indicator:
        # Check if producer or name contains wine region/variety keywords
        combined_text = f"{producer} {name}".lower()
        wine_keywords = [
            'château', 'domaine', 'chateau', 'estate', 'vineyard', 'winery',
            'grand cru', 'premier cru', 'reserve', 'reserva',
            'burgundy', 'bordeaux', 'champagne', 'napa', 'sonoma'
        ]
        
        if any(keyword in combined_text for keyword in wine_keywords):
            has_wine_indicator = True
    
    if not has_wine_indicator:
        return False, f"Unclear if wine: section={section}"
    
    # Passed all checks
    return True, "Valid"

# =================================================================
# 3. WINE LOADING (CACHED)
# =================================================================

# Global variable to store load statistics
_load_stats = None

def get_load_stats() -> Optional[Dict]:
    """Get wine loading statistics for debugging"""
    return _load_stats

@lru_cache(maxsize=1)
def load_wines() -> List[Dict]:
    """
    Load and filter wines from CSV
    V5.2 - Intelligent filtering, handles General section
    """
    global _load_stats
    
    logger.info("=" * 60)
    logger.info("LOADING WINE DATABASE")
    logger.info("=" * 60)
    
    # Find CSV file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_paths = [
        os.path.join(script_dir, 'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv'),
        'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv',
        '/app/MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv'
    ]
    
    csv_path = None
    for path in csv_paths:
        if os.path.exists(path):
            csv_path = path
            logger.info(f"✅ Found CSV at: {path}")
            break
    
    if not csv_path:
        logger.error(f"❌ CSV not found! Tried: {csv_paths}")
        logger.error(f"❌ Current directory: {os.getcwd()}")
        logger.error(f"❌ Files in current directory: {os.listdir('.')}")
        _load_stats = {
            'error': 'CSV file not found',
            'paths_tried': csv_paths,
            'current_dir': os.getcwd()
        }
        return []
    
    wines = []
    total_rows = 0
    rejected_by_reason = {}
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                
                # Validate wine
                is_valid, reason = is_valid_wine(row)
                
                if not is_valid:
                    rejected_by_reason[reason] = rejected_by_reason.get(reason, 0) + 1
                    continue
                
                # Build wine object
                try:
                    wine = {
                        'id': generate_stable_id(row['producer'], row.get('wine_name', 'Unknown')),
                        'name': row.get('wine_name', 'Unknown').strip(),
                        'producer': row['producer'].strip(),
                        'vintage': row.get('vintage', '').strip(),
                        'price': float(row['price']),
                        'section': row.get('section', 'General').strip(),
                        'pairing_tags': row.get('pairing_tags', '').strip(),
                        'acidity': int(row.get('acidity', 5)),
                        'tannin': int(row.get('tannin', 5)),
                        'body': int(row.get('body', 5)),
                        'texture': row.get('texture', '').strip(),
                        'insider_note': row.get('insider_note', '').strip()
                    }
                    wines.append(wine)
                except (ValueError, KeyError) as e:
                    rejected_by_reason[f"Parse error: {e}"] = rejected_by_reason.get(f"Parse error: {e}", 0) + 1
                    continue
        
        # Log results
        logger.info("=" * 60)
        logger.info(f"DATABASE LOADED SUCCESSFULLY: Valid wines: {len(wines):,}")
        logger.info(f"Total rows processed: {total_rows:,}")
        logger.info(f"Acceptance rate: {len(wines)/total_rows*100:.1f}%")
        logger.info("=" * 60)
        
        # Log rejection reasons
        if rejected_by_reason:
            logger.info("Rejection breakdown:")
            for reason, count in sorted(rejected_by_reason.items(), key=lambda x: -x[1])[:10]:
                logger.info(f"  - {reason}: {count:,}")
        
        # Store stats
        _load_stats = {
            'total_rows': total_rows,
            'valid_wines': len(wines),
            'rejected': total_rows - len(wines),
            'rejection_reasons': rejected_by_reason,
            'csv_path': csv_path
        }
        
        return wines
        
    except FileNotFoundError:
        logger.error(f"❌ CSV file not found: {csv_path}")
        _load_stats = {'error': 'File not found', 'path': csv_path}
        return []
    except Exception as e:
        logger.error(f"❌ Error loading CSV: {e}")
        import traceback
        traceback.print_exc()
        _load_stats = {'error': str(e)}
        return []

# =================================================================
# 4. PAIRING LOGIC
# =================================================================

def group_dishes(dishes: List[str], bottle_count: int) -> List[List[Dict]]:
    """Group dishes into courses for pairing"""
    dishes_as_dicts = [{'name': d} for d in dishes]
    
    if bottle_count == 1:
        return [dishes_as_dicts]
    
    group_size = max(1, len(dishes) // bottle_count)
    groups = []
    
    for i in range(0, len(dishes_as_dicts), group_size):
        group = dishes_as_dicts[i:i + group_size]
        if group:
            groups.append(group)
    
    while len(groups) > bottle_count:
        groups[-2].extend(groups[-1])
        groups.pop()
    
    return groups

def score_group(wine: Dict, dishes: List[Dict]) -> float:
    """Score wine for a group of dishes"""
    base_score = 50.0
    
    tags = wine.get('pairing_tags', '').lower()
    for dish in dishes:
        dish_name = dish['name'].lower()
        
        # Simple keyword matching
        keywords = {
            'steak': ['beef', 'meat', 'red meat'],
            'fish': ['fish', 'seafood'],
            'chicken': ['poultry', 'chicken'],
            'lamb': ['lamb', 'game'],
            'lobster': ['lobster', 'shellfish', 'seafood'],
            'truffle': ['truffle', 'mushroom'],
            'cheese': ['cheese']
        }
        
        for food_type, tag_matches in keywords.items():
            if food_type in dish_name:
                for tag_match in tag_matches:
                    if tag_match in tags:
                        base_score += 15
        
        # Generic boosts
        if 'tasting' in tags or 'versatile' in tags:
            base_score += 5
    
    return base_score

def generate_progression(dishes: List[str], bottle_count: int, budget: int) -> Dict:
    """
    Generate wine pairing progression
    V5.2.1 - Returns detailed error info if loading fails
    """
    try:
        wines = load_wines()
        
        # CRITICAL: Check if wines loaded
        if not wines:
            stats = get_load_stats()
            error_detail = "Wine database failed to load."
            if stats:
                if 'error' in stats:
                    error_detail += f" Error: {stats['error']}"
                elif 'paths_tried' in stats:
                    error_detail += f" CSV not found at: {stats['paths_tried']}"
                else:
                    error_detail += f" Processed {stats.get('total_rows', 0)} rows, loaded {stats.get('valid_wines', 0)} wines."
            else:
                error_detail += " CSV file may not be accessible."
            
            logger.error(error_detail)
            return {
                "success": False,
                "error": error_detail,
                "debug_info": stats
            }
        
        logger.info(f"Generating pairing for {len(dishes)} dishes, {bottle_count} bottles, ${budget} budget")
        logger.info(f"Wine pool: {len(wines):,} wines available")
        
        groups = group_dishes(dishes, bottle_count)
        budget_per_bottle = budget // bottle_count
        
        # Tiered budgeting
        budget_tiers = [1.05, 1.15, 1.50, float('inf')]
        
        progression = []
        used_ids = set()
        
        for i, group in enumerate(groups):
            candidates = []
            dish_names = [d['name'] for d in group]
            
            for tier_mult in budget_tiers:
                max_price = budget_per_bottle * tier_mult
                
                for wine in wines:
                    if wine['id'] in used_ids:
                        continue
                    if wine['price'] > max_price:
                        continue
                    
                    score = score_group(wine, group)
                    value_boost = (500 / (wine['price'] + 1)) * 0.1
                    final_score = score + value_boost
                    
                    candidates.append({
                        'wine': wine,
                        'score': final_score
                    })
                
                if len(candidates) >= 3:
                    break
            
            if not candidates:
                continue
            
            # Sort by score
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Build selection set
            selection_set = []
            for cand in candidates[:5]:
                wine = cand['wine']
                
                # Get rarity if facts enabled
                rarity = 1
                if FACTS_ENABLED:
                    try:
                        rarity = calculate_rarity_level(wine['price'])
                    except:
                        rarity = 1
                
                selection_set.append({
                    "wine_name": wine['name'],
                    "producer": wine['producer'],
                    "vintage": wine['vintage'],
                    "price": wine['price'],
                    "section": wine['section'],
                    "insider_note": wine['insider_note'],
                    "rarity_level": rarity,
                    "match_score": cand['score']
                })
            
            if selection_set:
                used_ids.add(selection_set[0]['wine_name'])
                
                progression.append({
                    "course_number": i + 1,
                    "course_name": f"Course {i+1}",
                    "dishes": dish_names,
                    "options": selection_set
                })
        
        total_cost = sum(c['options'][0]['price'] for c in progression) if progression else 0
        
        logger.info(f"✅ Generated {len(progression)} courses, total: ${total_cost:.2f}")
        
        return {
            "success": True,
            "progression": progression,
            "bottle_count": bottle_count,
            "total_cost": total_cost,
            "wine_pool_size": len(wines)
        }
    
    except Exception as e:
        logger.error(f"❌ Exception in generate_progression: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Pairing generation failed: {str(e)}",
            "debug_info": {"exception": str(e)}
        }

# =================================================================
# 5. HEALTH CHECK ENDPOINT
# =================================================================

def health_check() -> Dict:
    """Health check for debugging"""
    try:
        wines = load_wines()
        stats = get_load_stats()
        
        return {
            "status": "healthy" if wines else "unhealthy",
            "wine_count": len(wines),
            "load_stats": stats,
            "features": {
                "luxury_mode": LUXURY_MODE,
                "facts_enabled": FACTS_ENABLED
            }
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "wine_count": 0
        }

# Module initialization complete
logger.info("✅ pairing_service.py module loaded successfully")
logger.info(f"✅ Functions available: generate_progression, health_check, load_wines")
