"""
Fare Normalizer — normalizes raw fare observations to a comparable base.
Handles taxes, fees, convenience charges, and stop adjustments.
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Stop penalty (approximate added cost for connections vs direct)
STOP_PENALTY = {
    0: 0.0,     # direct — no penalty
    1: -500.0,  # 1 stop — typically cheaper (we normalize up toward direct equivalency)
    2: -1000.0, # 2 stops
}

# Typical convenience charge ranges by OTA source
TYPICAL_CONVENIENCE_CHARGES = {
    "makemytrip": 350.0,
    "cleartrip": 200.0,
    "ixigo": 0.0,       # Ixigo typically shows total fares
    "yatra": 250.0,
    "goibibo": 300.0,
    "easemytrip": 150.0,
    "airindia_official": 0.0,   # Direct airline — no OTA markup
    "indigo_direct": 0.0,       # Direct airline — no OTA markup
    "google_flights": 0.0,
    "amadeus": 0.0,
    "demo_generator": 0.0,
}


def normalize_fare(
    total_fare: float,
    source: str,
    stops: int = 0,
    base_fare: Optional[float] = None,
    taxes: Optional[float] = None,
    convenience_charge: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Normalize a fare observation to a comparable base.

    Normalization steps:
    1. Subtract estimated convenience charge if not already separated
    2. Adjust for stops (make comparable to direct flight equivalent)
    3. Store both raw and normalized values

    Returns dict with:
        - raw_fare: original total fare
        - normalized_fare: adjusted comparable fare
        - convenience_charge_applied: amount subtracted
        - stop_adjustment: amount added for stop equivalency
        - normalization_notes: description of adjustments
    """
    raw_fare = total_fare
    notes = []

    # Step 1: Convenience charge adjustment
    if convenience_charge is not None:
        # If already separated, use it directly
        conv_charge = convenience_charge
    else:
        # Estimate from known OTA patterns
        conv_charge = TYPICAL_CONVENIENCE_CHARGES.get(source, 200.0)

    # Only subtract if we believe it's included in total_fare (OTA sources)
    # Direct airline sources already have clean fares
    if source in ("airindia_official", "indigo_direct", "amadeus", "demo_generator"):
        conv_charge = 0.0

    fare_ex_convenience = raw_fare - conv_charge
    if conv_charge > 0:
        notes.append(f"Removed estimated ₹{conv_charge:.0f} convenience charge ({source})")

    # Step 2: Stop equivalency adjustment
    # For index comparison purposes, we note the adjustment but keep both values
    stop_adj = STOP_PENALTY.get(stops, 0.0)
    # We do NOT apply stop adjustment to normalized_fare for index calculation
    # (the index captures actual market prices including stop variations)
    # stop_adj is stored for analytical reference only

    normalized_fare = fare_ex_convenience
    if normalized_fare < 500:
        # Sanity check — if normalization produces an absurd value, use raw
        logger.warning(f"Normalization produced low fare {normalized_fare} — reverting to raw")
        normalized_fare = raw_fare
        notes.append("Normalization reverted — result below threshold")

    return {
        "raw_fare": raw_fare,
        "normalized_fare": round(normalized_fare, 2),
        "convenience_charge_applied": conv_charge,
        "stop_adjustment_reference": stop_adj,
        "normalization_notes": "; ".join(notes) if notes else "No adjustments",
        "is_normalized": True,
    }
