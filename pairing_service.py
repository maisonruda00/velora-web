"""
VELORA PAIRING SERVICE - PRODUCTION VERSION
Uses the FULL 14,651-wine database from MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv

From Gemini (Lead Architect) + Claude (System Engineer)
Chemistry-based wine pairing with complete molecular scoring.
"""
import csv
import os
from typing import List, Dict, Tuple, Optional


# =================================================================
# WINE DATABASE LOADER
# =================================================================

def load_wines() -> List[Dict]:
    """
    Loads the FULL 14,651-wine database from CSV.
    
    Returns:
        List of wine dictionaries with normalized properties
    """
    csv_path = os.path.join(os.path.dirname(__file__), 'MASTER_WINE_DATABASE_V23_READY_FOR_LAUNCH.csv')
    
    if not os.path.exists(csv_path):
        print(f"⚠️ Database not found at {csv_path}")
        return []
    
    wines = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Normalize and clean data
                    wine = {
                        'id': len(wines) + 1,
                        'name': row.get('wine_name', 'Unknown').strip(),
                        'producer': row.get('producer', 'Unknown').strip(),
                        'vintage': row.get('vintage', '').strip(),
                        'price': parse_float(row.get('price', '0'), default=0),
                        'type': normalize_type(row.get('section', 'Red')),
                        
                        # Molecular properties (normalized to 0-10 scale)
                        'acid': parse_float(row.get('acidity', '5'), default=5),
                        'tannin': parse_float(row.get('tannin', '5'), default=5),
                        'body': parse_float(row.get('body', '5'), default=5),
                        'sugar': estimate_sugar(row.get('section', ''), row.get('wine_name', '')),
                        
                        # Pairing data
                        'tags': parse_tags(row.get('pairing_tags', '')),
                        'why': row.get('insider_note', 'Selected for its molecular compatibility.').strip(),
                        
                        # Metadata
                        'restaurant': row.get('restaurant_id', '').strip(),
                        'bottle_size': row.get('bottle_size', '750ml').strip()
                    }
                    
                    wines.append(wine)
                    
                except Exception as e:
                    # Skip malformed rows but continue
                    continue
        
        print(f"✅ Loaded {len(wines)} wines from database")
        return wines
        
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        return []


def parse_float(value: str, default: float = 0.0) -> float:
    """Safely parse float from string."""
    if not value or value.strip() == '':
        return default
    try:
        return float(value.strip())
    except (ValueError, AttributeError):
        return default


def parse_tags(tags_str: str) -> List[str]:
    """Parse comma-separated tags into list."""
    if not tags_str:
        return []
    
    # Clean and lowercase tags
    tags = [tag.strip().lower().replace(' ', '_') for tag in tags_str.split(',')]
    return [tag for tag in tags if tag]  # Remove empty strings


def normalize_type(section: str) -> str:
    """Normalize wine type from section field."""
    section_lower = section.lower()
    
    if 'white' in section_lower or 'chardonnay' in section_lower:
        return 'White'
    elif 'red' in section_lower or 'burgundy' in section_lower or 'bordeaux' in section_lower:
        return 'Red'
    elif 'sparkling' in section_lower or 'champagne' in section_lower:
        return 'Sparkling'
    elif 'dessert' in section_lower or 'sweet' in section_lower or 'port' in section_lower:
        return 'Dessert'
    else:
        # Default to Red if unclear
        return 'Red'


def estimate_sugar(section: str, wine_name: str) -> float:
    """
    Estimate sugar content based on wine type.
    
    Returns:
        Sugar level 0-10 (0 = bone dry, 10 = very sweet)
    """
    section_lower = section.lower()
    name_lower = wine_name.lower()
    
    # Dessert wines
    if any(word in section_lower or word in name_lower for word in ['dessert', 'port', 'sauternes', 'tokaji']):
        return 8.0
    
    # Off-dry wines
    if any(word in section_lower or word in name_lower for word in ['riesling', 'moscato', 'vouvray']):
        # Check for dry indicators
        if 'brut' in name_lower or 'sec' in name_lower:
            return 1.0
        return 3.0  # Assume off-dry Riesling
    
    # Sparkling
    if 'sparkling' in section_lower or 'champagne' in section_lower:
        return 1.0  # Most Champagne is brut (dry)
    
    # Default: dry table wine
    return 1.0


# =================================================================
# FOOD CHEMISTRY ANALYZER
# =================================================================

class FoodAnalyzer:
    """
    Analyzes dish input to determine structural needs.
    
    The Golden Rules:
    - High Protein → Needs High Tannin
    - High Fat → Needs High Acid
    - Spicy/Heat → Needs Low Alcohol + Some Sugar
    - Sweet Dish → Needs Equal/Greater Sweetness
    - Delicate/Light → Needs Low Tannin
    - Rich/Heavy → Needs Structure
    """
    
    PROTEIN_KEYWORDS = [
        'steak', 'beef', 'ribeye', 'sirloin', 'filet', 'meat', 'lamb', 
        'venison', 'game', 'duck', 'pork', 'veal', 'burger', 'brisket',
        'wagyu', 'prime rib', 'tenderloin'
    ]
    
    FAT_KEYWORDS = [
        'fatty', 'rich', 'cream', 'butter', 'cheese', 'foie gras', 
        'fried', 'crispy', 'duck', 'pork belly', 'bacon', 'oil',
        'lobster', 'bisque'
    ]
    
    SPICY_KEYWORDS = [
        'spicy', 'hot', 'chili', 'pepper', 'curry', 'thai', 'szechuan',
        'jalapeño', 'habanero', 'wasabi', 'horseradish', 'vodka sauce'
    ]
    
    SWEET_KEYWORDS = [
        'dessert', 'chocolate', 'cake', 'sweet', 'caramel', 'honey',
        'fruit', 'tart', 'pie', 'pastry', 'sugar', 'cheesecake'
    ]
    
    DELICATE_KEYWORDS = [
        'oyster', 'shellfish', 'delicate', 'light', 'salad', 'vegetable',
        'fish', 'sole', 'halibut', 'sea bass', 'scallop', 'ceviche',
        'dover sole', 'turbot'
    ]
    
    ACIDIC_KEYWORDS = [
        'tomato', 'citrus', 'lemon', 'vinegar', 'pickled', 'ceviche',
        'acidic', 'tart', 'sour', 'marinara', 'pomodoro'
    ]
    
    EARTHY_KEYWORDS = [
        'mushroom', 'truffle', 'earthy', 'forest', 'umami', 'aged cheese',
        'porcini', 'morel', 'girolles'
    ]
    
    def analyze(self, dish_name: str) -> Dict:
        """
        Analyzes dish to determine chemical needs.
        
        Args:
            dish_name: Name/description of the dish
        
        Returns:
            Dictionary of structural requirements
        """
        dish_lower = dish_name.lower()
        
        # Detect food properties
        has_protein = any(kw in dish_lower for kw in self.PROTEIN_KEYWORDS)
        has_fat = any(kw in dish_lower for kw in self.FAT_KEYWORDS)
        has_spice = any(kw in dish_lower for kw in self.SPICY_KEYWORDS)
        has_sweet = any(kw in dish_lower for kw in self.SWEET_KEYWORDS)
        is_delicate = any(kw in dish_lower for kw in self.DELICATE_KEYWORDS)
        has_acid = any(kw in dish_lower for kw in self.ACIDIC_KEYWORDS)
        is_earthy = any(kw in dish_lower for kw in self.EARTHY_KEYWORDS)
        
        # Determine structural needs
        needs = {
            'min_tannin': 0,
            'max_tannin': 10,
            'min_acid': 0,
            'max_acid': 10,
            'min_body': 0,
            'max_body': 10,
            'min_sugar': 0,
            'max_sugar': 10,
            'tags': [],
            'reasoning': []
        }
        
        # Rule 1: High Protein → Needs High Tannin
        if has_protein:
            needs['min_tannin'] = 6
            needs['reasoning'].append("High protein requires tannin to bind")
            needs['tags'].extend(['beef', 'lamb', 'red_meat', 'steak'])
        
        # Rule 2: High Fat → Needs High Acid
        if has_fat:
            needs['min_acid'] = 6
            needs['reasoning'].append("Fat requires acid to cut richness")
        
        # Rule 3: Spicy → Low Alcohol, Some Sugar
        if has_spice:
            needs['max_tannin'] = 4  # Tannin amplifies heat
            needs['min_sugar'] = 2
            needs['reasoning'].append("Spice requires low tannin and residual sugar")
            needs['tags'].extend(['spicy', 'asian'])
        
        # Rule 4: Sweet → Needs Equal/Greater Sweetness
        if has_sweet:
            needs['min_sugar'] = 6
            needs['max_tannin'] = 3  # Dry tannins taste bitter with sugar
            needs['reasoning'].append("Sweetness requires equal or greater wine sweetness")
            needs['tags'].extend(['dessert', 'chocolate', 'sweet'])
        
        # Rule 5: Delicate → Low Tannin, Lighter Body
        if is_delicate:
            needs['max_tannin'] = 3
            needs['max_body'] = 6
            needs['reasoning'].append("Delicate flavors require gentle wine structure")
            needs['tags'].extend(['seafood', 'oysters', 'shellfish'])
        
        # Rule 6: Acidic Food → Match Acid or Go Higher
        if has_acid:
            needs['min_acid'] = 7
            needs['reasoning'].append("Acidic food requires matching wine acidity")
            needs['tags'].extend(['tomato', 'citrus', 'acidic_sauce'])
        
        # Rule 7: Earthy/Umami → Match Complexity
        if is_earthy:
            needs['min_body'] = 6
            needs['reasoning'].append("Earthy flavors pair with complex, aged wines")
            needs['tags'].extend(['mushroom', 'truffle', 'earthy'])
        
        # Default: If nothing detected, suggest versatile medium wines
        if not any([has_protein, has_fat, has_spice, has_sweet, is_delicate, has_acid, is_earthy]):
            needs['min_acid'] = 5
            needs['max_tannin'] = 6
            needs['reasoning'].append("Versatile pairing for balanced dish")
        
        return needs


# =================================================================
# PAIRING ENGINE
# =================================================================

class PairingEngine:
    """
    Scores and ranks wines based on food chemistry compatibility.
    Uses the FULL 14,651-wine database.
    """
    
    def __init__(self):
        self.wines = load_wines()
        self.analyzer = FoodAnalyzer()
        print(f"🧠 Pairing engine initialized with {len(self.wines)} wines")
    
    def score_wine(self, wine: Dict, needs: Dict) -> Tuple[float, str]:
        """
        Scores a wine's compatibility with food needs.
        
        Args:
            wine: Wine dictionary
            needs: Food chemistry requirements
        
        Returns:
            Tuple of (score, reasoning)
        """
        score = 100.0  # Start at perfect
        reasons = []
        
        # Check tannin compatibility
        if wine['tannin'] < needs['min_tannin']:
            penalty = (needs['min_tannin'] - wine['tannin']) * 10
            score -= penalty
            reasons.append(f"insufficient tannin (-{penalty:.0f})")
        elif wine['tannin'] > needs['max_tannin']:
            penalty = (wine['tannin'] - needs['max_tannin']) * 10
            score -= penalty
            reasons.append(f"excessive tannin (-{penalty:.0f})")
        
        # Check acidity compatibility
        if wine['acid'] < needs['min_acid']:
            penalty = (needs['min_acid'] - wine['acid']) * 8
            score -= penalty
            reasons.append(f"insufficient acidity (-{penalty:.0f})")
        elif wine['acid'] > needs['max_acid']:
            penalty = (wine['acid'] - needs['max_acid']) * 5
            score -= penalty
        
        # Check body compatibility
        if wine['body'] < needs['min_body']:
            penalty = (needs['min_body'] - wine['body']) * 6
            score -= penalty
            reasons.append(f"too light (-{penalty:.0f})")
        elif wine['body'] > needs['max_body']:
            penalty = (wine['body'] - needs['max_body']) * 6
            score -= penalty
            reasons.append(f"too heavy (-{penalty:.0f})")
        
        # Check sweetness compatibility
        if wine['sugar'] < needs['min_sugar']:
            penalty = (needs['min_sugar'] - wine['sugar']) * 12
            score -= penalty
            reasons.append(f"insufficient sweetness (-{penalty:.0f})")
        
        # Bonus for tag matches
        wine_tags = set(wine.get('tags', []))
        need_tags = set(needs.get('tags', []))
        tag_matches = wine_tags & need_tags
        
        if tag_matches:
            bonus = len(tag_matches) * 15
            score += bonus
            reasons.append(f"tag matches: {', '.join(tag_matches)} (+{bonus})")
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        return score, '; '.join(reasons) if reasons else 'perfect compatibility'
    
    def get_recommendation(self, dish_name: str, budget: int = 10000) -> Dict:
        """
        Gets best wine recommendation for a dish from FULL database.
        
        Args:
            dish_name: Name/description of the dish
            budget: Maximum price
        
        Returns:
            Dictionary with recommendation and reasoning
        """
        # Analyze food chemistry
        needs = self.analyzer.analyze(dish_name)
        
        # Filter wines by budget (allow 20% over budget for flexibility)
        affordable_wines = [w for w in self.wines if w['price'] <= budget * 1.2]
        
        if not affordable_wines:
            return {
                "success": False,
                "message": f"No wines found under ${budget}. Lowest price in cellar: ${min(w['price'] for w in self.wines):.0f}"
            }
        
        # Score all wines
        scored_wines = []
        for wine in affordable_wines:
            score, reason = self.score_wine(wine, needs)
            scored_wines.append({
                'wine': wine,
                'score': score,
                'reason': reason
            })
        
        # Sort by score (highest first)
        scored_wines.sort(key=lambda x: x['score'], reverse=True)
        
        # Get best match
        best = scored_wines[0]
        
        return {
            "success": True,
            "dish": dish_name,
            "wine": {
                "wine_name": best['wine']['name'],
                "producer": best['wine']['producer'],
                "type": best['wine']['type'],
                "price": best['wine']['price'],
                "score": round(best['score'], 1),
                "vintage": best['wine']['vintage']
            },
            "reasoning": {
                "chemistry": needs['reasoning'],
                "why": best['wine']['why'],
                "compatibility": best['reason']
            },
            "alternatives": [
                {
                    "name": alt['wine']['name'],
                    "producer": alt['wine']['producer'],
                    "price": alt['wine']['price'],
                    "score": round(alt['score'], 1)
                }
                for alt in scored_wines[1:4]  # Top 3 alternatives
            ]
        }


# =================================================================
# SINGLETON INSTANCE
# =================================================================
pairing_engine = PairingEngine()


# =================================================================
# TESTING
# =================================================================
if __name__ == "__main__":
    print("="*80)
    print("TESTING PAIRING ENGINE WITH FULL 14,651-WINE DATABASE")
    print("="*80)
    
    test_dishes = [
        ("Ribeye Steak", 500),
        ("Oysters on the Half Shell", 300),
        ("Spicy Thai Curry", 150),
        ("Chocolate Fondant", 400),
        ("Truffle Risotto", 600)
    ]
    
    for dish, budget in test_dishes:
        print(f"\n{'='*80}")
        print(f"Dish: {dish} | Budget: ${budget}")
        print('='*80)
        
        result = pairing_engine.get_recommendation(dish, budget=budget)
        
        if result['success']:
            print(f"\n✅ Recommended: {result['wine']['wine_name']}")
            print(f"   Producer: {result['wine']['producer']}")
            print(f"   Vintage: {result['wine']['vintage']}")
            print(f"   Type: {result['wine']['type']}")
            print(f"   Price: ${result['wine']['price']}")
            print(f"   Score: {result['wine']['score']}/100")
            print(f"\n💡 Chemistry:")
            for reason in result['reasoning']['chemistry']:
                print(f"   • {reason}")
            print(f"\n📖 Why: {result['reasoning']['why']}")
        else:
            print(f"❌ {result['message']}")
    
    print("\n" + "="*80)
    print(f"✅ PAIRING ENGINE TEST COMPLETE - {len(pairing_engine.wines)} wines active")
    print("="*80)
