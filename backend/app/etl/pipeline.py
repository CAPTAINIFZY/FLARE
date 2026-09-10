from typing import List, Dict, Any
from app.schemas.fare import FareObservation
from app.etl.normalizer import Normalizer
from app.etl.outlier_detection import OutlierDetector

class ETLPipeline:
    """
    Coordinates the transformation and validation of raw observations.
    """

    @classmethod
    def process_batch(cls, observations: List[FareObservation]) -> List[Dict[str, Any]]:
        """
        Processes a batch of raw FareObservations.
        Returns a list of dictionaries ready to be inserted into the database.
        """
        processed = []
        
        # 1. Normalization
        normalized_obs = [Normalizer.normalize_observation(obs) for obs in observations]
        
        # 2. Deduplication (within this batch)
        # Assuming duplicate if same source, route, airline, flight_number, travel_date, and total_fare
        seen = set()
        deduped_obs = []
        for obs in normalized_obs:
            identifier = (
                obs.source, obs.route, obs.airline, obs.flight_number, 
                obs.travel_date, obs.total_fare, obs.advance_purchase_days
            )
            if identifier not in seen:
                seen.add(identifier)
                deduped_obs.append(obs)
                
        # 3. Outlier Detection & Quality Scoring
        evaluated_obs = OutlierDetector.flag_outliers(deduped_obs)
        
        # 4. Prepare for DB
        for obs, is_outlier, quality_score in evaluated_obs:
            obs_dict = obs.model_dump()
            obs_dict['cleaned_value'] = obs.total_fare if not is_outlier else None
            obs_dict['outlier_flag'] = is_outlier
            obs_dict['quality_score'] = quality_score
            processed.append(obs_dict)
            
        return processed
