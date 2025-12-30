"""
VELORA KNOWLEDGE BASE (FACT ENGINE) - V5.0
✅ Layer 1: Producer-Specific Facts (High Value - "Billionaire Grade")
✅ Layer 2: Tag-Based Facts (Broad Coverage - "Sommelier Knowledge")
✅ Layer 3: Fallback (Generic but elegant)
"""
import random
import re
import unicodedata

# =================================================================
# LAYER 1: PRODUCER-SPECIFIC FACTS (The "Billionaire" Details)
# =================================================================

PRODUCER_FACTS = {
    # Tier 5: Unicorns (The Legends)
    'domaine_de_la_romanee_conti': [
        "DRC produces only ~6,000 bottles of Romanée-Conti annually, making it one of the world's rarest wines.",
        "During WWII, the Nazis specifically searched for DRC wines due to their legendary status.",
        "The vineyard is plowed by horses to avoid compacting the precious soil.",
        "Aubert de Villaine co-manages DRC and also makes affordable wines under his own label in Bouzeron."
    ],
    'domaine_leroy': [
        "Lalou Bize-Leroy co-managed DRC before creating her own estate, which rivals it in quality.",
        "Leroy yields are absurdly low - sometimes just 15 hectoliters per hectare (vs. 35-40 typical).",
        "The estate practices extreme biodynamics, including burying cow horns filled with manure."
    ],
    'egon_muller': [
        "Egon Müller's Scharzhofberger Trockenbeerenauslese is routinely the world's most expensive white wine.",
        "The estate has been in the Müller family since 1797.",
        "In exceptional years, their TBA can age for 100+ years."
    ],
    'screaming_eagle': [
        "The first vintage (1992) received a near-perfect score, instantly creating cult status.",
        "Production is so limited that the mailing list waiting time is over a decade.",
        "The original vineyard was planted on volcanic soils in Oakville."
    ],
    
    # Tier 4: Rare (The Icons)
    'chateau_margaux': [
        "Thomas Jefferson famously cited Château Margaux as a top growth in 1787.",
        "The estate is known as the 'Versailles of the Médoc' due to its neoclassical architecture.",
        "Paul Pontallier, the late director, was one of Bordeaux's most respected winemakers."
    ],
    'chateau_latour': [
        "Château Latour's Grand Vin is known for requiring 20-30 years before it hits its stride.",
        "The estate refused to participate in the En Primeur system starting in 2012.",
        "The famous tower (La Tour) on the label dates from the 17th century."
    ],
    'chateau_petrus': [
        "Pétrus is 100% Merlot - extremely rare for a top Bordeaux.",
        "The clay soil of Pétrus is unique in Pomerol and holds water during droughts.",
        "Jean-Pierre Moueix famously hand-selected every grape that went into Pétrus."
    ],
    'gaja': [
        "Angelo Gaja is credited with single-handedly putting Piedmont on the world stage.",
        "He controversially introduced French barriques to Barbaresco in the 1970s.",
        "Gaja withdrew from the DOCG system for years to have blending freedom."
    ],
    'giuseppe_mascarello': [
        "Monprivato is a monopole vineyard, entirely owned by the Mascarello family.",
        "Maria Teresa Mascarello famously refuses to use new oak, sticking to traditional large Slavonian casks.",
        "The wines are known for extraordinary longevity - 30-50 years is not uncommon."
    ],
    
    # Tier 3: Scarce (The Masters)
    'kistler': [
        "Kistler is widely considered the benchmark for California Chardonnay.",
        "They isolate their own yeast strains from specific vineyards rather than using commercial yeast.",
        "The winery is notoriously secretive - visitors are almost never allowed."
    ],
    'leflaive': [
        "Anne-Claude Leflaive pioneered biodynamics in Burgundy in the 1990s.",
        "She famously buried cow horns filled with manure (Preparation 500) to channel cosmic forces.",
        "Leflaive's Puligny-Montrachet is the gold standard for white Burgundy."
    ],
    'caymus': [
        "The Wagner family rejected the concept of 'terroir' for decades, focusing on a consistent 'house style.'",
        "Caymus Special Selection changed Napa Valley by proving that extreme ripeness and extract could work.",
        "Chuck Wagner is one of the few winemakers to appear on the cover of Wine Spectator multiple times."
    ],
    'beaucastel': [
        "Beaucastel 'flash heats' their grapes at 80°C immediately after harvest—a controversial technique.",
        "This 'thermovinification' kills enzymes and prevents oxidation, preserving fruit character.",
        "The Perrin family has owned Beaucastel since 1909 and uses all 13 permitted Châteauneuf grapes."
    ],
    'sine_qua_non': [
        "Manfred Krankl releases wines under different whimsical names every vintage.",
        "Each label is a unique work of art commissioned from contemporary artists.",
        "SQN is notoriously difficult to obtain - most allocation goes to long-term mailing list members."
    ],
    'penfolds': [
        "Penfolds Grange is Australia's most iconic wine, first made in 1951 by Max Schubert.",
        "Schubert was initially ordered to stop making Grange because management thought it was too different.",
        "The wine is made from multiple vineyards across South Australia, prioritizing quality over terroir."
    ],
    
    # Tier 2: Quality (The Craftsmen)
    'cloudy_bay': [
        "Cloudy Bay put New Zealand Sauvignon Blanc on the map in the 1980s.",
        "The name comes from the body of water (Cloudy Bay) that Captain Cook sailed through.",
        "Kevin Judd, the founding winemaker, is also a renowned photographer."
    ],
    'ridge': [
        "Ridge Monte Bello consistently scores 100 points - one of California's greatest Cabernets.",
        "Paul Draper pioneered natural winemaking in California, using native yeasts and minimal intervention.",
        "The Monte Bello vineyard sits at 2,600 feet elevation with limestone soils - rare for California."
    ]
}

# =================================================================
# LAYER 2: TAG-BASED FACTS (The "Sommelier" Knowledge)
# =================================================================

TAG_FACTS = {
    # Terroir Tags
    'volcanic': [
        "Wines from volcanic soil often exhibit a distinct smoky, saline minerality.",
        "Volcanic terroir provides excellent drainage, forcing roots deep into mineral-rich earth.",
        "Mt. Etna in Sicily and Santorini in Greece are famous for volcanic wine terroirs."
    ],
    'limestone': [
        "Limestone soils are prized in Burgundy and Champagne for producing elegant, mineral wines.",
        "The porous nature of limestone provides good drainage while retaining some moisture.",
        "Many of the world's greatest white wines come from limestone terroirs."
    ],
    'clay': [
        "Clay soils retain water and warmth, producing fuller-bodied, richer wines.",
        "Merlot and Cabernet Franc particularly thrive in clay soils.",
        "Pomerol's famous blue clay is responsible for the richness of Pétrus and other top wines."
    ],
    'schist': [
        "Schist is a metamorphic rock that retains heat during the day and releases it at night.",
        "The Douro Valley's schist terraces produce some of the world's finest Port.",
        "Schist imparts a distinctive mineral character and allows vines to dig deep for water."
    ],
    'granite': [
        "Granite produces wines with pronounced acidity and intense aromatics.",
        "Beaujolais' granite slopes are ideal for Gamay, producing vibrant, fruity wines.",
        "The mineral content in granite can give wines a flinty, steely quality."
    ],
    
    # Production Method Tags
    'biodynamic': [
        "This producer follows biodynamic cycles, often bottling according to the lunar calendar.",
        "Biodynamics views the vineyard as a single, self-sustaining organism.",
        "Biodynamic preparations include burying cow horns and using herbal teas on the vines."
    ],
    'organic': [
        "This estate uses no synthetic pesticides, herbicides, or fertilizers in the vineyard.",
        "Organic viticulture promotes biodiversity and soil health.",
        "Many top estates have transitioned to organic farming in recent decades."
    ],
    'natural': [
        "Natural winemaking uses native yeasts, no additives, and minimal sulfites.",
        "These wines can be unpredictable but often show incredible terroir expression.",
        "Natural wines have a devoted following for their authenticity and vibrancy."
    ],
    'single_vineyard': [
        "Single vineyard wines showcase the unique character of one specific site.",
        "These wines are the ultimate expression of terroir and vintage.",
        "Single vineyard bottlings are typically a producer's most prestigious offerings."
    ],
    
    # Vineyard Characteristics
    'old_vines': [
        "Old vines (30+ years) produce less fruit but with more concentrated flavors.",
        "The root systems of old vines dig deep, accessing unique minerals and water.",
        "Some of the world's greatest wines come from centenarian vines."
    ],
    'high_altitude': [
        "High altitude protects the grapes' acidity, ensuring freshness despite the sun.",
        "Diurnal shifts (hot days, cold nights) at altitude thicken grape skins for better structure.",
        "Argentina's Mendoza and Northern Italy's Alto Adige are famous for high-altitude wines."
    ],
    'steep_slopes': [
        "Steep slopes provide excellent drainage and sun exposure.",
        "Germany's Mosel Valley and the Rhône's Côte-Rôtie are famous for impossibly steep vineyards.",
        "These vineyards are often hand-harvested due to the extreme angles."
    ],
    
    # Winemaking Techniques
    'barrel_fermented': [
        "Barrel fermentation integrates oak flavors more harmoniously than barrel aging alone.",
        "This technique is common in top white Burgundy and premium Chardonnay.",
        "The wine develops a creamy texture from lees contact during fermentation."
    ],
    'amphora': [
        "Amphorae are clay vessels used for fermentation and aging, dating back thousands of years.",
        "The porous clay allows micro-oxygenation without the flavor of oak.",
        "Josko Gravner pioneered the modern use of Georgian amphorae in Italy."
    ],
    'sur_lie': [
        "Aging 'sur lie' (on the lees) adds texture, complexity, and a creamy mouthfeel.",
        "This technique is traditional in Muscadet and sparkling wine production.",
        "The dead yeast cells release compounds that enhance the wine's body and flavor."
    ],
    
    # Historical/Cultural
    'female_winemaker': [
        "This estate is run by a woman winemaker - still relatively rare in the wine world.",
        "Pioneering women like Lalou Bize-Leroy and Anne-Claude Leflaive changed the industry.",
        "Female winemakers are increasingly recognized for their contributions to quality."
    ],
    'family_estate': [
        "This winery has been family-owned for multiple generations.",
        "Family estates often prioritize long-term quality over short-term profits.",
        "The accumulated knowledge of generations shows in the wines' consistency."
    ],
    'historic_estate': [
        "This estate has centuries of winemaking history and tradition.",
        "Historic estates often occupy the best vineyard sites, secured long ago.",
        "The weight of tradition can be both a blessing and a burden."
    ],
    
    # Regional Characteristics
    'classified_growth': [
        "This wine is from a classified estate - officially recognized for quality.",
        "The 1855 Bordeaux Classification remains influential today.",
        "Classified wines typically command premium prices due to their pedigree."
    ],
    'grand_cru': [
        "Grand Cru is the highest classification in Burgundy and Alsace.",
        "These vineyards have been recognized for centuries as producing superior wines.",
        "Grand Cru wines represent less than 2% of Burgundy's production."
    ],
    'premier_cru': [
        "Premier Cru is the second-highest classification in Burgundy.",
        "These vineyards produce wines of excellent quality, just below Grand Cru.",
        "Many Premier Cru wines rival Grand Crus in quality and complexity."
    ]
}

# =================================================================
# 3. HELPER FUNCTIONS
# =================================================================

def slugify(text: str) -> str:
    """
    Normalize text for matching (same as pairing_service).
    """
    if not isinstance(text, str):
        text = str(text)
    
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '_', text)
    return text.strip('_')

# =================================================================
# 4. MAIN FUNCTION
# =================================================================

def get_interesting_fact(wine_obj: dict) -> str:
    """
    Retrieves the most specific fact available for a wine.
    
    Priority:
        1. Producer-specific facts (storytelling)
        2. Tag-based facts (educational)
        3. Generic fallback (elegant)
    
    Args:
        wine_obj: Wine dictionary with 'producer', 'name', 'type', 'region', 'tags'
    
    Returns:
        An interesting fact string
    """
    
    # Layer 1: Check Producer-Specific Facts
    producer_key = slugify(wine_obj.get('producer', ''))
    
    if producer_key in PRODUCER_FACTS:
        return random.choice(PRODUCER_FACTS[producer_key])
    
    # Layer 2: Check Tag-Based Facts
    tags = wine_obj.get('tags', [])
    if tags:
        for tag in tags:
            tag_normalized = tag.lower().strip()
            if tag_normalized in TAG_FACTS:
                return random.choice(TAG_FACTS[tag_normalized])
    
    # Layer 3: Generic Fallback (still elegant)
    wine_type = wine_obj.get('type', 'wine')
    region = wine_obj.get('region', '')
    producer = wine_obj.get('producer', 'this producer')
    
    fallbacks = [
        f"A classic example of {wine_type} from {region}." if region else f"A distinguished {wine_type}.",
        f"{producer} is known for producing wines of exceptional quality and character.",
        f"This wine showcases the distinctive terroir and winemaking style of {region}." if region else "This wine exemplifies fine winemaking craftsmanship.",
        f"A wine that perfectly demonstrates why {region} is renowned worldwide." if region else "A wine that exemplifies quality and tradition."
    ]
    
    return random.choice(fallbacks)

# =================================================================
# 5. RARITY SCORING (Multi-Factor System)
# =================================================================

def calculate_rarity_level(wine_obj: dict) -> int:
    """
    Calculate wine rarity on 1-5 scale using multi-factor analysis.
    
    Factors:
        - Producer prestige (allocated producers)
        - Vineyard classification (monopole, Grand Cru)
        - Production volume (if available)
        - Price tier (expensive often correlates with rarity)
    
    Returns:
        1 = Common/Available
        2 = Quality (good distribution)
        3 = Scarce (limited availability)
        4 = Rare (collector's item)
        5 = Unicorn (virtually unobtainable)
    """
    rarity = 1  # Default: Available
    
    producer_key = slugify(wine_obj.get('producer', ''))
    wine_name_lower = wine_obj.get('name', '').lower()
    wine_type_lower = wine_obj.get('type', '').lower()
    price = wine_obj.get('price', 0)
    
    # Tier 5: Unicorns (Allocated Producers)
    ALLOCATED_PRODUCERS = [
        'domaine_de_la_romanee_conti',
        'domaine_leroy',
        'egon_muller',
        'screaming_eagle',
        'sine_qua_non',
        'harlan_estate',
        'colgin_cellars',
        'bryant_family',
        'schrader_cellars'
    ]
    
    if producer_key in ALLOCATED_PRODUCERS:
        return 5
    
    # Tier 4: Rare (Monopole Vineyards & Grand Cru Burgundy)
    MONOPOLE_VINEYARDS = ['monprivato', 'la_tache', 'romanee_conti', 'clos_de_tart']
    
    for monopole in MONOPOLE_VINEYARDS:
        if monopole in slugify(wine_name_lower):
            rarity = max(rarity, 4)
    
    if 'grand cru' in wine_name_lower and 'burgundy' in wine_type_lower:
        rarity = max(rarity, 4)
    
    if 'barolo riserva' in wine_name_lower or 'brunello riserva' in wine_name_lower:
        rarity = max(rarity, 4)
    
    # Tier 3: Scarce (Premier Cru, Classified Growths, High Price)
    if 'premier cru' in wine_name_lower:
        rarity = max(rarity, 3)
    
    if any(term in wine_name_lower for term in ['first growth', '1er cru', 'classé']):
        rarity = max(rarity, 3)
    
    # Check production volume if available
    production = wine_obj.get('production_volume', 0)
    if production and production < 5000:
        rarity = max(rarity, 3)
    
    if price > 300:
        rarity = max(rarity, 3)
    
    # Tier 2: Quality (Classified wines, moderate price)
    if price > 100:
        rarity = max(rarity, 2)
    
    return min(rarity, 5)  # Cap at 5
