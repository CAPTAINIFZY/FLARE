import statistics
from typing import List, Tuple
from app.schemas.fare import FareObservation

class OutlierDetector:
    """
    Detects anomalies in fares. Simple z-score or MAD based detection.
    """
    
    @classmethod
    def flag_outliers(cls, observations: List[FareObservation]) -> List[Tuple[FareObservation, bool, float]]:
        """
        Returns a list of tuples: (Observation, is_outlier, quality_score)
        """
        if not observations:
            return []
            
        fares = [obs.total_fare for obs in observations if obs.total_fare is not None and obs.total_fare > 0]
        
        if len(fares) < 3:
            # Not enough data to determine outliers statistically within this batch
            return [(obs, False, 1.0) for obs in observations]
            
        median_fare = statistics.median(fares)
        
        # Calculate Median Absolute Deviation (MAD)
        abs_deviations = [abs(f - median_fare) for f in fares]
        mad = statistics.median(abs_deviations)
        
        # If MAD is 0 (all prices same), then no outliers
        if mad == 0:
            return [(obs, False, 1.0) for obs in observations]
            
        results = []
        for obs in observations:
            if obs.total_fare is None or obs.total_fare <= 0:
                results.append((obs, True, 0.0)) # Invalid fare is an outlier/poor quality
                continue
                
            # Modified Z-score based on MAD
            # z = 0.6745 * (x - median) / MAD
            modified_z = 0.6745 * (obs.total_fare - median_fare) / mad
            
            is_outlier = abs(modified_z) > 3.5
            
            # Quality score (1.0 to 0.0)
            quality_score = max(0.0, 1.0 - (abs(modified_z) / 10.0))
            if is_outlier:
                quality_score = min(quality_score, 0.4)
                
            results.append((obs, is_outlier, round(quality_score, 2)))
            
        return results
