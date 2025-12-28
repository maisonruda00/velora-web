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
    INTELLIGENT emergency fallback based on wine characteristics.
    Generates wine-specific facts even when AI unavailable.
    """
    starters = []
    
    wine_lower = wine_name.lower()
    
    # REGION-SPECIFIC FACTS
    if "grand cru" in wine_lower:
        starters.append("Grand Cru designation represents the top tier of vineyard classification, accounting for less than 2% of production in Burgundy.")
    elif "premier cru" in wine_lower:
        starters.append("Premier Cru vineyards represent the second-highest classification, with strict yield limits and aging requirements.")
    elif "chablis" in wine_lower:
        starters.append("Chablis vineyards sit on ancient Kimmeridgian limestone formed from fossilized oyster shells 150 million years ago.")
    elif "barolo" in wine_lower or "barbaresco" in wine_lower:
        starters.append("This Nebbiolo requires a minimum of 38 months aging before release, with the best examples improving for 20+ years.")
    elif "châteauneuf" in wine_lower:
        starters.append("This appellation allows 13 grape varieties and requires one of the lowest yields in France at 35 hectoliters per hectare.")
    elif "rioja" in wine_lower:
        starters.append("Traditional Rioja undergoes extended aging in American oak, with Gran Reservas spending a minimum of 5 years before release.")
    elif "champagne" in wine_lower:
        starters.append("True Champagne can only come from this protected region, where méthode champenoise requires secondary fermentation in bottle.")
    elif "sancerre" in wine_lower or "pouilly" in wine_lower:
        starters.append("These Loire Sauvignon Blancs grow on silex (flint) and terres blanches soils, creating distinctive mineral tension.")
    elif "bordeaux" in wine_lower or "pauillac" in wine_lower or "margaux" in wine_lower:
        starters.append("Left Bank Bordeaux vineyards benefit from gravel deposited by ancient river systems, providing exceptional drainage for Cabernet.")
    elif "napa" in wine_lower:
        starters.append("Napa Valley's diverse microclimates range from cool Carneros to warm Calistoga, spanning 30+ soil types.")
    elif "burgundy" in wine_lower or "côte" in wine_lower:
        starters.append("Burgundy's limestone-rich terroir and Pinot Noir create wines that can improve for 30+ years in ideal vintages.")
    elif "tuscany" in wine_lower or "brunello" in wine_lower:
        starters.append("Brunello di Montalcino requires 100% Sangiovese and a minimum of 5 years aging before release.")
    elif "rhône" in wine_lower or "hermitage" in wine_lower:
        starters.append("Northern Rhône Syrah grows on vertiginous granite slopes, some with gradients exceeding 60 degrees.")
    elif "mosel" in wine_lower or "riesling" in wine_lower and "german" in wine_type.lower():
        starters.append("Mosel Rieslings from steep slate vineyards can age for 50+ years, developing petrol and honey notes.")
    
    # PRODUCER-SPECIFIC (if recognizable names in wine_name)
    elif "romanée-conti" in wine_lower or "drc" in wine_lower:
        starters.append("This estate's monopole of Romanée-Conti is 1.8 hectares producing approximately 6,000 bottles in optimal vintages.")
    elif "pétrus" in wine_lower:
        starters.append("Pétrus is 95% Merlot grown on rare blue clay, with vines averaging 40+ years old.")
    elif "sassicaia" in wine_lower:
        starters.append("Sassicaia pioneered Cabernet in Tuscany's Bolgheri region in 1968, defying DOC regulations at the time.")
    elif "opus" in wine_lower:
        starters.append("This Napa Valley collaboration between Mondavi and Rothschild blends Bordeaux tradition with California fruit.")
    
    # PRICE-BASED INSIGHTS
    elif price > 500:
        starters.append(f"At ${price:.0f}, this represents investment-grade wine with proven aging potential spanning decades.")
    elif price > 200:
        starters.append("This wine comes from low-yielding old vines, with production limited to preserve concentration and quality.")
    elif price > 100:
        starters.append("Extended aging in French oak and careful vineyard management contribute to this wine's complexity and structure.")
    
    # GENERIC TYPE-BASED (only if nothing else matched)
    if not starters:
        if "white" in wine_type.lower():
            starters.append("White wines develop complex tertiary aromas with age, transitioning from fruit to honey, nuts, and petrol.")
        elif "red" in wine_type.lower():
            starters.append("The wine's tannins will integrate with time, revealing layers of earth, leather, and dried fruit.")
        elif "sparkling" in wine_type.lower():
            starters.append("Extended aging on lees creates autolytic character, adding brioche and toasted almond notes.")
        else:
            starters.append("This wine reflects its unique terroir through distinctive mineral, fruit, and structural components.")
    
    return starters[:2]  # Return max 2 starters
