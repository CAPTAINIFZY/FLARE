import numpy as np
from datetime import date
from typing import List, Dict

class BacktestRunner:
    """
    Compares the calculated Airfare Price Index against reference historical data (e.g., DGCA).
    Calculates statistical metrics: MAE, RMSE, Correlation.
    """
    
    @classmethod
    def run_backtest(
        cls, 
        our_index_data: List[float], 
        reference_data: List[float]
    ) -> Dict[str, float]:
        """
        Runs the backtest given two time-aligned series.
        
        Args:
            our_index_data: Array of APIx values
            reference_data: Array of Reference index values
            
        Returns:
            Dictionary with MAE, RMSE, and Correlation.
        """
        if not our_index_data or not reference_data or len(our_index_data) != len(reference_data):
            raise ValueError("Data series must be non-empty and of equal length.")
            
        our_array = np.array(our_index_data)
        ref_array = np.array(reference_data)
        
        # Mean Absolute Error (MAE)
        mae = np.mean(np.abs(our_array - ref_array))
        
        # Root Mean Squared Error (RMSE)
        rmse = np.sqrt(np.mean((our_array - ref_array) ** 2))
        
        # Correlation Coefficient
        correlation = np.corrcoef(our_array, ref_array)[0, 1]
        
        return {
            "MAE": round(float(mae), 4),
            "RMSE": round(float(rmse), 4),
            "Correlation": round(float(correlation), 4)
        }
