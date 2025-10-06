from typing import Dict

LINEAGE_COLOR_MAP: Dict[str, str] = {
    "SATIVA": "#E74C3C",
    "INDICA": "#8E44AD",
    "HYBRID": "#27AE60",
    "HYBRID/SATIVA": "#E74C3C",
    "HYBRID/INDICA": "#8E44AD",
    "CBD": "#F1C40F",
    "MIXED": "#1E3A8A",
    "PARAPHERNALIA": "#FF69B4",
}

TYPE_OVERRIDES: Dict[str, str] = {
    "all-in-one": "vape cartridge",
    "rosin": "concentrate",
    "mini buds": "flower",
    "bud": "flower",
    "pre-roll": "Pre-roll",
    "alcohol/ethanol extract": "rso/co2 tankers",
    "Alcohol/Ethanol Extract": "rso/co2 tankers",
    "alcohol ethanol extract": "rso/co2 tankers",
    "Alcohol Ethanol Extract": "rso/co2 tankers",
    "c02/ethanol extract": "rso/co2 tankers",
    "CO2 Concentrate": "rso/co2 tankers",
    "co2 concentrate": "rso/co2 tankers",
}

WORD_WEIGHT = 5
SCALE_FACTOR = 1.0