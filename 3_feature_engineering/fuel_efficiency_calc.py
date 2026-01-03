"""
Fuel Efficiency Calculator
Detects fuel inefficiency patterns in flight operations
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import importlib.util


def load_db_manager():
    """Load DatabaseManager from 2_database folder"""
    db_path = Path(__file__).parent.parent / '2_database' / 'db_setup.py'
    spec = importlib.util.spec_from_file_location("db_setup", db_path)
    db_setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_setup)
    return db_setup.DatabaseManager()


class FuelEfficiencyCalculator:
    """Calculates fuel efficiency metrics and identifies inefficient patterns"""
    
    def __init__(self):
        """Initialize calculator"""
        self.db = load_db_manager()
        self.db.connect()
    
    def load_trajectory_features(self) -> pd.DataFrame:
        """Load trajectory features from CSV"""
        features_path = Path(__file__).parent.parent / 'data' / 'trajectory_features.csv'
        
        if not features_path.exists():
            raise FileNotFoundError(
                "Trajectory features not found. Run trajectory_analyzer.py first!"
            )
        
        df = pd.read_csv(features_path)
        print(f"✅ Loaded {len(df):,} trajectory features")
        return df
    
    def detect_altitude_oscillations(self, trajectory_df: pd.DataFrame, 
                                    threshold_m: float = 300) -> Dict:
        """
        Detect unnecessary altitude changes (fuel inefficient)
        
        Args:
            trajectory_df: DataFrame with trajectory features
            threshold_m: Altitude change threshold in meters
        
        Returns:
            Dictionary with oscillation metrics
        """
        metrics = {}
        
        # Calculate altitude variance
        metrics['altitude_variance'] = trajectory_df['altitude_variance'].mean()
        metrics['high_variance_flights'] = (trajectory_df['altitude_variance'] > 500000).sum()
        metrics['pct_high_variance'] = 100 * metrics['high_variance_flights'] / len(trajectory_df)
        
        # Flights with excessive altitude changes
        metrics['excessive_altitude_change'] = (trajectory_df['altitude_change_m'] > threshold_m * 3).sum()
        
        return metrics
    
    def detect_speed_instability(self, trajectory_df: pd.DataFrame) -> Dict:
        """
        Detect speed instability (indicates inefficient operations)
        
        Args:
            trajectory_df: DataFrame with trajectory features
        
        Returns:
            Dictionary with speed metrics
        """
        metrics = {}
        
        # Speed variance
        metrics['avg_velocity_variance'] = trajectory_df['velocity_variance'].mean()
        
        # High variance flights
        high_variance_threshold = trajectory_df['velocity_variance'].quantile(0.75)
        metrics['high_speed_variance_flights'] = (trajectory_df['velocity_variance'] > high_variance_threshold).sum()
        metrics['pct_high_speed_variance'] = 100 * metrics['high_speed_variance_flights'] / len(trajectory_df)
        
        return metrics
    
    def detect_holding_patterns(self, trajectory_df: pd.DataFrame) -> Dict:
        """
        Detect holding patterns (circular routes indicating delays)
        
        Heuristic: Low distance for long duration suggests holding pattern
        
        Args:
            trajectory_df: DataFrame with trajectory features
        
        Returns:
            Dictionary with holding pattern metrics
        """
        metrics = {}
        
        # Calculate speed efficiency ratio
        # Low ratio (distance / duration) suggests hovering/holding
        trajectory_df['speed_efficiency'] = trajectory_df['total_distance_km'] / (trajectory_df['duration_minutes'] / 60)
        
        # Identify potential holding patterns
        # Flights with < 100 km/h average speed for > 15 minutes
        potential_holding = (
            (trajectory_df['speed_efficiency'] < 100) & 
            (trajectory_df['duration_minutes'] > 15) &
            (trajectory_df['trajectory_type'] != 'Ground/Taxi')
        )
        
        metrics['potential_holding_patterns'] = potential_holding.sum()
        metrics['pct_holding_patterns'] = 100 * metrics['potential_holding_patterns'] / len(trajectory_df)
        
        return metrics
    
    def calculate_efficiency_score(self, trajectory_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate overall fuel efficiency score for each trajectory
        
        Score components:
        - Altitude stability (30%)
        - Speed stability (30%)
        - Route directness (20%)
        - Holding patterns (20%)
        
        Args:
            trajectory_df: DataFrame with trajectory features
        
        Returns:
            DataFrame with efficiency scores
        """
        df = trajectory_df.copy()
        
        # Normalize metrics to 0-100 scale
        
        # 1. Altitude stability score (lower variance = higher score)
        max_alt_var = df['altitude_variance'].quantile(0.95)
        df['altitude_stability_score'] = 100 * (1 - df['altitude_variance'].clip(0, max_alt_var) / max_alt_var)
        
        # 2. Speed stability score (lower variance = higher score)
        max_speed_var = df['velocity_variance'].quantile(0.95)
        df['speed_stability_score'] = 100 * (1 - df['velocity_variance'].clip(0, max_speed_var) / max_speed_var)
        
        # 3. Route directness score
        # Compare actual distance to straight-line distance
        df['straight_line_distance_km'] = df.apply(
            lambda row: self._calculate_distance(
                row['start_lat'], row['start_lon'],
                row['end_lat'], row['end_lon']
            ), axis=1
        )
        df['route_directness'] = df['straight_line_distance_km'] / df['total_distance_km'].clip(lower=0.1)
        df['route_directness_score'] = 100 * df['route_directness'].clip(0, 1)
        
        # 4. Holding pattern penalty
        df['speed_efficiency'] = df['total_distance_km'] / (df['duration_minutes'] / 60)
        df['no_holding_score'] = df['speed_efficiency'].clip(0, 200) / 200 * 100
        
        # Calculate overall efficiency score (weighted average)
        df['fuel_efficiency_score'] = (
            0.30 * df['altitude_stability_score'] +
            0.30 * df['speed_stability_score'] +
            0.20 * df['route_directness_score'] +
            0.20 * df['no_holding_score']
        )
        
        # Classify efficiency
        df['efficiency_category'] = pd.cut(
            df['fuel_efficiency_score'],
            bins=[0, 40, 60, 80, 100],
            labels=['Poor', 'Fair', 'Good', 'Excellent']
        )
        
        return df
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points (Haversine)"""
    # Convert Decimal to float if needed
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return c * 6371  # Earth radius in km
    
    def analyze_fuel_efficiency(self) -> pd.DataFrame:
        """
        Main analysis function
        
        Returns:
            DataFrame with fuel efficiency analysis
        """
        print("\n" + "="*70)
        print("FUEL EFFICIENCY ANALYSIS")
        print("="*70)
        
        # Load trajectory features
        print("\n1. Loading trajectory features...")
        df = self.load_trajectory_features()
        
        # Filter out ground operations
        flight_df = df[df['trajectory_type'] != 'Ground/Taxi'].copy()
        print(f"   Analyzing {len(flight_df):,} airborne trajectories")
        
        # Detect patterns
        print("\n2. Detecting inefficiency patterns...")
        
        altitude_metrics = self.detect_altitude_oscillations(flight_df)
        print(f"\n   Altitude Oscillations:")
        print(f"     High variance flights: {altitude_metrics['high_variance_flights']} ({altitude_metrics['pct_high_variance']:.1f}%)")
        
        speed_metrics = self.detect_speed_instability(flight_df)
        print(f"\n   Speed Instability:")
        print(f"     High variance flights: {speed_metrics['high_speed_variance_flights']} ({speed_metrics['pct_high_speed_variance']:.1f}%)")
        
        holding_metrics = self.detect_holding_patterns(flight_df)
        print(f"\n   Holding Patterns:")
        print(f"     Potential holding patterns: {holding_metrics['potential_holding_patterns']} ({holding_metrics['pct_holding_patterns']:.1f}%)")
        
        # Calculate efficiency scores
        print("\n3. Calculating efficiency scores...")
        efficiency_df = self.calculate_efficiency_score(flight_df)
        
        # Summary statistics
        print(f"\n✅ Fuel Efficiency Analysis Complete")
        print(f"\n   Overall Efficiency Distribution:")
        for category in ['Excellent', 'Good', 'Fair', 'Poor']:
            count = (efficiency_df['efficiency_category'] == category).sum()
            pct = 100 * count / len(efficiency_df)
            print(f"     {category:12s}: {count:4d} ({pct:5.1f}%)")
        
        print(f"\n   Average Efficiency Score: {efficiency_df['fuel_efficiency_score'].mean():.1f}/100")
        print(f"   Median Efficiency Score:  {efficiency_df['fuel_efficiency_score'].median():.1f}/100")
        
        # Identify most/least efficient
        print(f"\n   Top 5 Most Efficient Flights:")
        top_5 = efficiency_df.nlargest(5, 'fuel_efficiency_score')[['callsign', 'fuel_efficiency_score', 'duration_minutes', 'total_distance_km']]
        for idx, row in top_5.iterrows():
            print(f"     {row['callsign'] or 'N/A':12s}: Score {row['fuel_efficiency_score']:.1f}, {row['duration_minutes']:.0f} min, {row['total_distance_km']:.0f} km")
        
        print(f"\n   Top 5 Least Efficient Flights:")
        bottom_5 = efficiency_df.nsmallest(5, 'fuel_efficiency_score')[['callsign', 'fuel_efficiency_score', 'duration_minutes', 'total_distance_km']]
        for idx, row in bottom_5.iterrows():
            print(f"     {row['callsign'] or 'N/A':12s}: Score {row['fuel_efficiency_score']:.1f}, {row['duration_minutes']:.0f} min, {row['total_distance_km']:.0f} km")
        
        # Save results
        output_path = Path(__file__).parent.parent / 'data' / 'fuel_efficiency_features.csv'
        efficiency_df.to_csv(output_path, index=False)
        print(f"\n✅ Efficiency features saved to: {output_path}")
        
        return efficiency_df
    
    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("Fuel Efficiency Calculator")
    print("Aviation Intelligence & Risk Prediction Platform")
    print("="*70)
    
    calculator = FuelEfficiencyCalculator()
    
    try:
        # Analyze fuel efficiency
        efficiency_df = calculator.analyze_fuel_efficiency()
        
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)
        print(f"\nFuel efficiency analysis complete!")
        print(f"Results saved and ready for ML modeling.")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Please run trajectory_analyzer.py first to generate trajectory features.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        calculator.close()


if __name__ == "__main__":
    main()