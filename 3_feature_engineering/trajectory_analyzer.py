"""
Flight Trajectory Analyzer - WORKS WITH EXISTING DATABASE
Extracts and analyzes complete flight paths from position data
Includes callsign extraction without requiring trajectory_id column
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import importlib.util
import sys

# Load DatabaseManager
def load_db_manager():
    """Load DatabaseManager from 2_database folder"""
    db_path = Path(__file__).parent.parent / '2_database' / 'db_setup.py'
    spec = importlib.util.spec_from_file_location("db_setup", db_path)
    db_setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_setup)
    return db_setup.DatabaseManager()


class TrajectoryAnalyzer:
    """Analyzes flight trajectories and extracts features"""
    
    def __init__(self):
        """Initialize analyzer"""
        self.db = load_db_manager()
        self.db.connect()
    
    def get_all_flights(self) -> pd.DataFrame:
        """
        Retrieve all flight state data as DataFrame WITH CALLSIGNS
    
        Returns:
            DataFrame with all flight states
        """
        query = """
        SELECT 
            icao24,
            callsign,
            latitude,
            longitude,
            baro_altitude,
            geo_altitude,
            velocity,
            vertical_rate,
            heading,
            on_ground,
            timestamp
        FROM flight_states
        ORDER BY icao24, timestamp
        """
    
        results = self.db.execute_query(query)
        df = pd.DataFrame(results)
    
        # Convert Decimal columns to float
        numeric_columns = [
            'latitude', 'longitude', 'baro_altitude', 'geo_altitude',
            'velocity', 'vertical_rate', 'heading'
        ]
    
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    
        print(f"✅ Loaded {len(df):,} flight state records")
        
        # Check callsign availability
        if 'callsign' in df.columns:
            with_callsigns = df['callsign'].notna().sum()
            unique_callsigns = df['callsign'].nunique()
            print(f"   Callsigns: {with_callsigns:,} records ({unique_callsigns:,} unique)")
        
        return df
    
    def group_into_trajectories(self, df: pd.DataFrame, 
                               max_gap_minutes: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Group position records into individual flight trajectories
        
        Args:
            df: DataFrame with flight states
            max_gap_minutes: Maximum gap to consider same flight
        
        Returns:
            Dictionary mapping trajectory_id to trajectory DataFrame
        """
        trajectories = {}
        
        # Group by aircraft
        grouped = df.groupby('icao24')
        
        trajectory_count = 0
        
        for icao24, aircraft_df in grouped:
            aircraft_df = aircraft_df.sort_values('timestamp').reset_index(drop=True)
            
            # Find gaps in time series
            time_diffs = aircraft_df['timestamp'].diff()
            
            # Split on gaps > max_gap_minutes
            gap_threshold = timedelta(minutes=max_gap_minutes)
            split_points = time_diffs > gap_threshold
            
            # Assign trajectory IDs
            trajectory_ids = split_points.cumsum()
            
            # Create separate trajectory for each segment
            for traj_id in trajectory_ids.unique():
                mask = trajectory_ids == traj_id
                traj_df = aircraft_df[mask].copy()
                
                if len(traj_df) >= 3:  # Minimum 3 points for meaningful trajectory
                    # Create unique trajectory ID
                    trajectory_key = trajectory_count
                    trajectories[trajectory_key] = traj_df
                    trajectory_count += 1
        
        print(f"✅ Identified {len(trajectories):,} flight trajectories")
        print(f"   Average points per trajectory: {len(df) / len(trajectories):.1f}")
        
        return trajectories
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate distance between two lat/lon points (Haversine formula)
        
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        # Convert Decimal to float first
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Earth radius in km
        r = 6371
        
        return c * r
    
    def calculate_distances_vectorized(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        """
        Vectorized calculation of distances between consecutive points
        
        Args:
            lats: Array of latitudes
            lons: Array of longitudes
        
        Returns:
            Array of distances in kilometers
        """
        # Convert to radians
        lats_rad = np.radians(lats.astype(float))
        lons_rad = np.radians(lons.astype(float))
        
        # Calculate differences between consecutive points
        dlat = np.diff(lats_rad)
        dlon = np.diff(lons_rad)
        
        # Vectorized Haversine formula
        lat1 = lats_rad[:-1]
        lat2 = lats_rad[1:]
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Earth radius in km
        r = 6371
        
        return c * r
    
    def extract_trajectory_features(self, trajectory_df: pd.DataFrame, trajectory_id: int) -> Dict:
        """
        Extract features from a single trajectory WITH CALLSIGN
        
        Args:
            trajectory_df: DataFrame with trajectory points
            trajectory_id: Unique identifier for this trajectory
        
        Returns:
            Dictionary of features
        """
        features = {}
        
        # Basic info - INCLUDE TRAJECTORY_ID
        features['trajectory_id'] = trajectory_id
        features['icao24'] = trajectory_df['icao24'].iloc[0]
        
        # **CRITICAL: Extract callsign properly**
        # Get most common non-null callsign for this trajectory
        if 'callsign' in trajectory_df.columns:
            callsigns = trajectory_df['callsign'].dropna()
            if len(callsigns) > 0:
                # Remove empty strings
                callsigns = callsigns[callsigns.astype(str).str.strip() != '']
                if len(callsigns) > 0:
                    # Get most frequent callsign (optimized to avoid calling mode() twice)
                    mode_values = callsigns.mode()
                    features['callsign'] = mode_values[0] if len(mode_values) > 0 else callsigns.iloc[0]
                else:
                    features['callsign'] = None
            else:
                features['callsign'] = None
        else:
            features['callsign'] = None
        
        features['num_points'] = len(trajectory_df)
        
        # Time features
        features['start_time'] = trajectory_df['timestamp'].min()
        features['end_time'] = trajectory_df['timestamp'].max()
        features['duration_minutes'] = (features['end_time'] - features['start_time']).total_seconds() / 60
        
        # Position features
        features['start_lat'] = float(trajectory_df['latitude'].iloc[0])
        features['start_lon'] = float(trajectory_df['longitude'].iloc[0])
        features['end_lat'] = float(trajectory_df['latitude'].iloc[-1])
        features['end_lon'] = float(trajectory_df['longitude'].iloc[-1])
        
        # Calculate total distance using vectorized method (performance optimization)
        if len(trajectory_df) > 1:
            lats = trajectory_df['latitude'].values
            lons = trajectory_df['longitude'].values
            distances = self.calculate_distances_vectorized(lats, lons)
            features['total_distance_km'] = np.sum(distances)
        else:
            features['total_distance_km'] = 0.0
        
        features['avg_speed_kmh'] = (features['total_distance_km'] / features['duration_minutes'] * 60) if features['duration_minutes'] > 0 else 0
        
        # Altitude features (filter out None values)
        valid_altitudes = trajectory_df['baro_altitude'].dropna()
        if len(valid_altitudes) > 0:
            features['max_altitude_m'] = float(valid_altitudes.max())
            features['min_altitude_m'] = float(valid_altitudes.min())
            features['avg_altitude_m'] = float(valid_altitudes.mean())
            features['altitude_change_m'] = features['max_altitude_m'] - features['min_altitude_m']
            features['altitude_variance'] = float(valid_altitudes.var())
        else:
            features['max_altitude_m'] = None
            features['min_altitude_m'] = None
            features['avg_altitude_m'] = None
            features['altitude_change_m'] = None
            features['altitude_variance'] = None
        
        # Velocity features (filter out None values)
        valid_velocities = trajectory_df['velocity'].dropna()
        if len(valid_velocities) > 0:
            features['max_velocity_ms'] = float(valid_velocities.max())
            features['min_velocity_ms'] = float(valid_velocities.min())
            features['avg_velocity_ms'] = float(valid_velocities.mean())
            features['velocity_variance'] = float(valid_velocities.var())
        else:
            features['max_velocity_ms'] = None
            features['min_velocity_ms'] = None
            features['avg_velocity_ms'] = None
            features['velocity_variance'] = None
        
        # Vertical rate features
        valid_vr = trajectory_df['vertical_rate'].dropna()
        if len(valid_vr) > 0:
            features['max_climb_rate_ms'] = float(valid_vr.max())
            features['max_descent_rate_ms'] = float(valid_vr.min())
            features['avg_vertical_rate_ms'] = float(valid_vr.mean())
        else:
            features['max_climb_rate_ms'] = None
            features['max_descent_rate_ms'] = None
            features['avg_vertical_rate_ms'] = None
        
        # Ground status
        features['time_on_ground_minutes'] = (trajectory_df['on_ground'] == True).sum() * (features['duration_minutes'] / features['num_points'])
        features['time_airborne_minutes'] = features['duration_minutes'] - features['time_on_ground_minutes']
        
        # Flight phase detection (simple heuristic)
        if features['max_altitude_m'] and features['max_altitude_m'] > 3000:  # > 3km suggests cruise
            features['includes_cruise'] = True
        else:
            features['includes_cruise'] = False
        
        return features
    
    def analyze_all_trajectories(self, save_to_db: bool = True) -> pd.DataFrame:
        """
        Analyze all trajectories and extract features WITH CALLSIGNS
        
        Args:
            save_to_db: If True, save features to database
        
        Returns:
            DataFrame with trajectory features including callsigns
        """
        print("\n" + "="*70)
        print("TRAJECTORY ANALYSIS - WITH CALLSIGNS")
        print("="*70)
        
        # Load data
        print("\n1. Loading flight state data...")
        df = self.get_all_flights()
        
        # Group into trajectories
        print("\n2. Grouping into trajectories...")
        trajectories = self.group_into_trajectories(df)
        
        # Extract features
        print("\n3. Extracting trajectory features...")
        trajectory_features = []
        
        for traj_id, traj_df in trajectories.items():
            features = self.extract_trajectory_features(traj_df, traj_id)
            trajectory_features.append(features)
        
        features_df = pd.DataFrame(trajectory_features)
        
        # Display summary
        print(f"\n✅ Extracted features from {len(features_df):,} trajectories")
        
        # Callsign statistics
        if 'callsign' in features_df.columns:
            with_callsigns = features_df['callsign'].notna().sum()
            unique_callsigns = features_df['callsign'].nunique()
            print(f"\n📡 Callsign Statistics:")
            print(f"    With callsigns: {with_callsigns:,} ({100*with_callsigns/len(features_df):.1f}%)")
            print(f"    Unique callsigns: {unique_callsigns:,}")
            
            # Show sample callsigns
            if with_callsigns > 0:
                print(f"\n    Sample callsigns:")
                sample = features_df[features_df['callsign'].notna()]['callsign'].head(10)
                for cs in sample:
                    print(f"      {cs}")
        
        print("\n📊 Trajectory Statistics:")
        print(f"  Duration (minutes):")
        print(f"    Mean:   {features_df['duration_minutes'].mean():.1f}")
        print(f"    Median: {features_df['duration_minutes'].median():.1f}")
        print(f"    Max:    {features_df['duration_minutes'].max():.1f}")
        
        print(f"\n  Distance (km):")
        print(f"    Mean:   {features_df['total_distance_km'].mean():.1f}")
        print(f"    Median: {features_df['total_distance_km'].median():.1f}")
        print(f"    Max:    {features_df['total_distance_km'].max():.1f}")
        
        print(f"\n  Altitude (meters):")
        valid_alt = features_df['max_altitude_m'].dropna()
        print(f"    Mean max:   {valid_alt.mean():.0f}")
        print(f"    Median max: {valid_alt.median():.0f}")
        
        # Classify trajectories
        features_df['trajectory_type'] = features_df.apply(self._classify_trajectory, axis=1)
        
        print(f"\n  Trajectory Types:")
        type_counts = features_df['trajectory_type'].value_counts()
        for traj_type, count in type_counts.items():
            print(f"    {traj_type}: {count:,} ({100*count/len(features_df):.1f}%)")
        
        # Save to CSV
        output_path = Path(__file__).parent.parent / 'data' / 'trajectory_features.csv'
        output_path.parent.mkdir(exist_ok=True)
        features_df.to_csv(output_path, index=False)
        print(f"\n✅ Features saved to: {output_path}")
        
        # Show sample with callsigns
        if 'callsign' in features_df.columns:
            print(f"\n📋 Sample trajectories with callsigns:")
            sample_cols = ['trajectory_id', 'callsign', 'icao24', 'duration_minutes', 'total_distance_km']
            sample_df = features_df[features_df['callsign'].notna()][sample_cols].head(10)
            if len(sample_df) > 0:
                print(sample_df.to_string(index=False))
        
        return features_df
    
    def _classify_trajectory(self, row: pd.Series) -> str:
        """Classify trajectory type based on features"""
        if row['duration_minutes'] < 10:
            return 'Ground/Taxi'
        elif row['duration_minutes'] < 60 and row.get('max_altitude_m', 0) and row['max_altitude_m'] < 3000:
            return 'Short/Regional'
        elif row.get('max_altitude_m', 0) and row['max_altitude_m'] >= 9000:
            return 'Long-Haul/Cruise'
        elif row.get('max_altitude_m', 0) and row['max_altitude_m'] >= 3000:
            return 'Medium-Range'
        else:
            return 'Incomplete/Unknown'
    
    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("Flight Trajectory Analyzer")
    print("Aviation Intelligence & Risk Prediction Platform")
    print("="*70)
    
    analyzer = TrajectoryAnalyzer()
    
    try:
        # Analyze all trajectories
        features_df = analyzer.analyze_all_trajectories()
        
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)
        print(f"\n✅ Trajectory features saved and ready for ML modeling!")
        print(f"   Total trajectories: {len(features_df):,}")
        
        if 'callsign' in features_df.columns:
            with_callsigns = features_df['callsign'].notna().sum()
            print(f"   With callsigns: {with_callsigns:,} ({100*with_callsigns/len(features_df):.1f}%)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()