"""
CONVERSATION STARTER GENERATOR - AI-POWERED VERSION
✅ Generates wine-specific conversation starters using AI
✅ Fallback to wine-specific templates (not generic facts)

Generates engaging talking points about wines for social dining experiences.
"""
import logging
from llm_client import ai_client

logger = logging.getLogger(__name__)

def generate_conversation_starters(wine_name: str, producer: str, wine_type: str, 
                                   region: str = None, price: float = 0) -> list:
    """
    Generate 2-3 engaging conversation starters about the wine.
    
    UPGRADED: Now uses AI to generate wine-specific facts instead of generic templates.
    """
    try:
        # Use AI to generate wine-specific conversation starters
        starters = ai_client.generate_conversation_starters(
            wine_name=wine_name,
            producer=producer,
            wine_type=wine_type,
            region=region,
            price=price
        )
        
        if starters and len(starters) >= 2:
            logger.info(f"✅ AI conversation starters for {wine_name}")
            return starters[:3]  # Return top 3
        else:
            # This shouldn't happen (AI client has its own fallback)
            # but just in case
            return _emergency_fallback(wine_name, wine_type, price)
            
    except Exception as e:
        logger.warning(f"⚠️ Conversation starter error: {e}")
        return _emergency_fallback(wine_name, wine_type, price)


def _emergency_fallback(wine_name: str, wine_type: str, price: float) -> list:
    """
    Emergency fallback if AI client completely fails.
    Still more specific than old generic facts.
    """
    starters = []
    
    if "Grand Cru" in wine_name:
        starters.append("Grand Cru status represents less than 2% of total production.")
    elif "Chablis" in wine_name:
        starters.append("Chablis vineyards sit on ancient oyster fossils from the Jurassic period.")
    elif "Barolo" in wine_name:
        starters.append("Barolo requires a minimum of 38 months aging before release.")
    else:
        starters.append("This wine represents a specific terroir expression.")
    
    if price > 500:
        starters.append(f"At ${price:.0f}, this is investment-grade wine with proven aging potential.")
    
    return starters[:3]
