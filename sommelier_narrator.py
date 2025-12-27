"""
WINE NARRATOR (IP-SAFE + PRODUCTION-GRADE)
✅ Filename: sommelier_narrator.py (import compatibility)
✅ Class: WineAdvisor (IP safety)
✅ Persona: "The Curator" (luxury positioning)
"""
from functools import lru_cache
from llm_client import ai_client
import json
import logging

logger = logging.getLogger(__name__)

class WineAdvisor:
    """
    Luxury wine pairing descriptions using AI.
    Persona: "The Curator" - British, surgical, evocative.
    """
    
    def generate_pairing_story(self, wine_name: str, wine_type: str, 
                               dish_name: str, wine_properties: dict) -> str:
        """
        Generate sophisticated pairing note with caching.
        
        Returns AI-generated note or graceful fallback if AI unavailable.
        """
        try:
            # Serialize dict for cache key (LRU cache needs hashable types)
            props_json = json.dumps(wine_properties, sort_keys=True)
            cache_key = f"{wine_name}|||{wine_type}|||{dish_name}|||{props_json}"
            
            return self._generate_cached(cache_key, wine_name, dish_name, props_json)
            
        except Exception as e:
            logger.error(f"Wine Advisor Error: {e}")
            # Graceful fallback
            return f"A {wine_type} with balanced structure that complements the {dish_name}."
    
    @lru_cache(maxsize=500)
    def _generate_cached(self, cache_key: str, wine_name: str, 
                        dish_name: str, props_json: str) -> str:
        """
        Cached generation (500 most recent pairings).
        Cache hit = instant response, zero API cost.
        """
        try:
            wine_properties = json.loads(props_json)
            
            result = ai_client.generate_luxury_note(
                wine_name=wine_name,
                dish_name=dish_name,
                wine_properties=wine_properties
            )
            
            logger.info(f"Generated note for {wine_name} + {dish_name}")
            return result
            
        except Exception as e:
            logger.error(f"Cached generation failed: {e}")
            # Final fallback template
            return f"A balanced pairing that complements the {dish_name}."

# Singleton instance
narrator = WineAdvisor()

# =================================================================
# BACKWARD COMPATIBILITY ADAPTER
# Allows legacy pairing_service.py to call old function names
# =================================================================
def generate_sommelier_story(wine_name, producer, wine_type, dish_name, wine_details):
    """
    DEPRECATED: Legacy adapter for backward compatibility.
    New code should use: narrator.generate_pairing_story()
    """
    props = {"legacy_note": wine_details}
    return narrator.generate_pairing_story(wine_name, wine_type, dish_name, props)
