from typing import Dict, List, Optional

class IndexCalculator:
    """
    Calculates the Airfare Price Index (APIx) based on route weights and fares.
    """
    
    @classmethod
    def calculate_index(
        cls, 
        current_fares: Dict[str, float], 
        base_fares: Dict[str, float], 
        route_weights: Dict[str, float]
    ) -> Optional[float]:
        """
        Calculate Laspeyres-type price index.
        
        Args:
            current_fares: Dict mapping route_code to average current fare
            base_fares: Dict mapping route_code to average base period fare
            route_weights: Dict mapping route_code to its weight (summing to 1.0)
            
        Returns:
            The calculated index value, or None if insufficient data.
        """
        index_sum = 0.0
        total_weight_used = 0.0
        
        for route, weight in route_weights.items():
            current = current_fares.get(route)
            base = base_fares.get(route)
            
            if current and base and base > 0:
                price_relative = current / base
                index_sum += price_relative * weight
                total_weight_used += weight
                
        if total_weight_used == 0:
            return None
            
        # Rebase if some routes are missing to maintain mathematical consistency
        final_index = (index_sum / total_weight_used) * 100.0
        return round(final_index, 2)
