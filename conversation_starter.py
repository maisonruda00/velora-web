"""
CONVERSATION STARTER GENERATOR (IP-SAFE VERSION)
✅ No protected terms (sommelier, Master of Wine, critic names)
✅ Generic wine expertise terminology

Generates engaging talking points about wines for social dining experiences.
"""

def generate_conversation_starters(wine_name: str, producer: str, wine_type: str, 
                                   region: str = None, price: float = 0) -> list:
    """
    Generate 2-3 engaging conversation starters about the wine.
    
    IP-SAFE: No use of protected professional titles or critic names.
    """
    starters = []
    
    # Pairing wisdom (general principles, no protected terminology)
    pairing_wisdom = [
        "Wine experts recommend: match the wine's weight to the dish's richness, not just the color to the protein.",
        "In great pairings, the wine should make the food taste better AND the food should make the wine taste better—a true symbiosis.",
        "Acidity in wine is like salt in cooking: it brightens flavors and makes rich dishes feel lighter on the palate.",
    ]
    
    import random
    starters.append(random.choice(pairing_wisdom))
    
    # Wine type specific insights
    type_insights = {
        'Sparkling': "The pressure inside a Champagne bottle is about 90 PSI—three times that of a car tire.",
        'White': "White wines are often more terroir-expressive than reds because there's less tannin to mask the soil's mineral character.",
        'Red': "The polyphenols in red wine that make your mouth feel dry preserve the wine for decades of aging.",
        'Dessert': "Sweet wines were historically more prized than dry wines—preserving residual sugar was a mark of winemaking skill.",
    }
    
    if len(starters) < 2:
        starters.append(type_insights.get(wine_type, 
            "Great wines are defined not by power, but by balance—the interplay of fruit, acidity, and structure."))
    
    # Price context
    if price > 500 and len(starters) < 3:
        starters.append(f"At ${price:.0f}, this wine reflects not just quality but scarcity.")
    
    return starters[:3]

