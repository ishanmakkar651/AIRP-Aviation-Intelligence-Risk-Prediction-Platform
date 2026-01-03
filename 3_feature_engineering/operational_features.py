"""
Operational Features Extractor - FIXED TO PRESERVE CALLSIGNS
Extracts ML-ready operational features from flight data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict
import importlib.util


def load_db_manager():
    """Load DatabaseManager from 2_database folder"""
    db_path = Path(__file__).parent.parent / '2_database' / 'db_setup.py'
    spec = importlib.util.spec_from_file_location("db_setup", db_path)
    db_setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_setup)
    return db_setup.DatabaseManager()


class OperationalFeaturesExtractor:
    """Extracts operational features for ML models"""
    
    def __init__(self):
        """Initialize extractor"""
        self.db = load_db_manager()
        self.db.connect()
    
    def load_all_features(self) -> pd.DataFrame:
        """Load trajectory and fuel efficiency features - PRESERVE CALLSIGNS"""
        traj_path = Path(__file__).parent.parent / 'data' / 'trajectory_features.csv'
        fuel_path = Path(__file__).parent.parent / 'data' / 'fuel_efficiency_features.csv'
        
        if not traj_path.exists():
            raise FileNotFoundError("Run trajectory_analyzer.py first!")
        
        if fuel_path.exists():
            # Merge both feature sets - KEEP ALL COLUMNS including callsign
            traj_df = pd.read_csv(traj_path)
            fuel_df = pd.read_csv(fuel_path)
            
            # fuel_df already contains trajectory features, use it as base
            df = fuel_df.copy()
            
            # Verify callsign present
            if 'callsign' not in df.columns:
                print("⚠️  Warning: callsign not in fuel features, merging from trajectory features...")
                # Merge callsign from trajectory features
                if 'callsign' in traj_df.columns:
                    df = df.merge(
                        traj_df[['trajectory_id', 'callsign']],
                        on='trajectory_id',
                        how='left'
                    )
                    print("✅ Callsign merged from trajectory features")
        else:
            df = pd.read_csv(traj_path)
        
        print(f"✅ Loaded {len(df):,} flight records with features")
        
        # Verify and report callsign status
        if 'callsign' in df.columns:
            with_callsigns = df['callsign'].notna().sum()
            unique_callsigns = df['callsign'].nunique()
            print(f"✅ Callsign column present!")
            print(f"   With callsigns: {with_callsigns:,} ({100*with_callsigns/len(df):.1f}%)")
            print(f"   Unique callsigns: {unique_callsigns:,}")
        else:
            print("⚠️  WARNING: Callsign column missing! Dashboard will show 'UNKNOWN'")
            print("   Run: python 3_feature_engineering/trajectory_analyzer.py")
        
        return df
    
    def extract_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract time-based features
        
        Args:
            df: DataFrame with trajectory features
        
        Returns:
            DataFrame with added temporal features
        """
        df = df.copy()
        
        # Convert timestamps
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])
        
        # Extract time components
        df['hour_of_day'] = df['start_time'].dt.hour
        df['day_of_week'] = df['start_time'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Time period categories
        df['time_period'] = pd.cut(
            df['hour_of_day'],
            bins=[0, 6, 12, 18, 24],
            labels=['Night', 'Morning', 'Afternoon', 'Evening'],
            right=False
        )
        
        # Peak hours (based on your data: 8-10 AM had high traffic)
        df['is_peak_hour'] = df['hour_of_day'].isin([7, 8, 9, 10]).astype(int)
        
        print(f"✅ Extracted temporal features")
        return df
    
    def extract_performance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract aircraft performance features
        
        Args:
            df: DataFrame with trajectory features
        
        Returns:
            DataFrame with added performance features
        """
        df = df.copy()
        
        # Speed features (convert m/s to km/h for interpretability)
        df['avg_speed_kmh'] = df['avg_velocity_ms'] * 3.6
        df['max_speed_kmh'] = df['max_velocity_ms'] * 3.6
        df['speed_range_kmh'] = (df['max_velocity_ms'] - df['min_velocity_ms']) * 3.6
        
        # Speed coefficient of variation (normalized variability)
        df['speed_cv'] = np.sqrt(df['velocity_variance']) / df['avg_velocity_ms'].clip(lower=1)
        
        # Altitude features (convert to feet for aviation standard)
        df['max_altitude_ft'] = df['max_altitude_m'] * 3.28084
        df['avg_altitude_ft'] = df['avg_altitude_m'] * 3.28084
        df['altitude_range_ft'] = df['altitude_change_m'] * 3.28084
        
        # Altitude coefficient of variation
        df['altitude_cv'] = np.sqrt(df['altitude_variance']) / df['avg_altitude_m'].clip(lower=1)
        
        # Climb performance (where applicable)
        df['max_climb_rate_fpm'] = df['max_climb_rate_ms'] * 196.85  # feet per minute
        df['max_descent_rate_fpm'] = df['max_descent_rate_ms'] * 196.85
        
        # Distance per time features
        df['distance_per_minute'] = df['total_distance_km'] / df['duration_minutes'].clip(lower=1)
        
        # Efficiency ratio
        df['km_per_altitude_km'] = df['total_distance_km'] / (df['max_altitude_m'] / 1000).clip(lower=0.1)
        
        print(f"✅ Extracted performance features")
        return df
    
    def extract_operational_risk_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract operational risk indicators
        
        Args:
            df: DataFrame with trajectory features
        
        Returns:
            DataFrame with added risk features
        """
        df = df.copy()
        
        # Speed anomalies
        speed_mean = df['avg_velocity_ms'].mean()
        speed_std = df['avg_velocity_ms'].std()
        df['speed_zscore'] = (df['avg_velocity_ms'] - speed_mean) / speed_std
        df['is_speed_anomaly'] = (np.abs(df['speed_zscore']) > 2).astype(int)
        
        # Altitude anomalies
        alt_mean = df['max_altitude_m'].mean()
        alt_std = df['max_altitude_m'].std()
        df['altitude_zscore'] = (df['max_altitude_m'] - alt_mean) / alt_std
        df['is_altitude_anomaly'] = (np.abs(df['altitude_zscore']) > 2).astype(int)
        
        # High variability flags
        speed_var_threshold = df['velocity_variance'].quantile(0.9)
        df['high_speed_variability'] = (df['velocity_variance'] > speed_var_threshold).astype(int)
        
        alt_var_threshold = df['altitude_variance'].quantile(0.9)
        df['high_altitude_variability'] = (df['altitude_variance'] > alt_var_threshold).astype(int)
        
        # Rapid altitude changes
        df['rapid_altitude_change'] = (df['altitude_change_m'] > 8000).astype(int)  # > 8km change
        
        # Complex maneuvers indicator
        df['complex_maneuvers'] = (
            df['high_speed_variability'] | 
            df['high_altitude_variability']
        ).astype(int)
        
        print(f"✅ Extracted operational risk features")
        return df
    
    def extract_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract statistical aggregation features
        
        Args:
            df: DataFrame with trajectory features
        
        Returns:
            DataFrame with added statistical features
        """
        df = df.copy()
        
        # Data quality indicators
        df['data_completeness'] = df['num_points'] / df['duration_minutes'].clip(lower=1)
        
        # Trajectory complexity (more points = more complex)
        df['trajectory_complexity'] = np.log1p(df['num_points'])
        
        # Time utilization
        df['airborne_ratio'] = df['time_airborne_minutes'] / df['duration_minutes'].clip(lower=1)
        
        # Distance efficiency
        if 'straight_line_distance_km' in df.columns:
            df['route_efficiency'] = df['straight_line_distance_km'] / df['total_distance_km'].clip(lower=0.1)
        
        print(f"✅ Extracted statistical features")
        return df
    
    def create_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create categorical features and encode them
        
        Args:
            df: DataFrame with trajectory features
        
        Returns:
            DataFrame with encoded categorical features
        """
        df = df.copy()
        
        # One-hot encode trajectory type
        trajectory_dummies = pd.get_dummies(df['trajectory_type'], prefix='traj_type')
        df = pd.concat([df, trajectory_dummies], axis=1)
        
        # One-hot encode time period
        if 'time_period' in df.columns:
            time_dummies = pd.get_dummies(df['time_period'], prefix='time')
            df = pd.concat([df, time_dummies], axis=1)
        
        # One-hot encode efficiency category (if exists)
        if 'efficiency_category' in df.columns:
            efficiency_dummies = pd.get_dummies(df['efficiency_category'], prefix='efficiency')
            df = pd.concat([df, efficiency_dummies], axis=1)
        
        print(f"✅ Created categorical features")
        return df
    
    def extract_all_features(self) -> pd.DataFrame:
        """
        Extract all operational features - PRESERVES CALLSIGNS
        
        Returns:
            DataFrame with all features including callsigns
        """
        print("\n" + "="*70)
        print("OPERATIONAL FEATURES EXTRACTION - WITH CALLSIGNS")
        print("="*70)
        
        # Load base features
        print("\n1. Loading base features...")
        df = self.load_all_features()
        
        # Verify callsign before processing
        has_callsign_before = 'callsign' in df.columns
        if has_callsign_before:
            callsign_count_before = df['callsign'].notna().sum()
            print(f"   ✓ Starting with {callsign_count_before:,} callsigns")
        
        # Extract feature sets
        print("\n2. Extracting feature sets...")
        df = self.extract_temporal_features(df)
        df = self.extract_performance_features(df)
        df = self.extract_operational_risk_features(df)
        df = self.extract_statistical_features(df)
        df = self.create_categorical_features(df)
        
        # Verify callsign after processing
        if 'callsign' in df.columns:
            callsign_count_after = df['callsign'].notna().sum()
            print(f"\n✅ Callsign column preserved through all processing!")
            print(f"   Final count: {callsign_count_after:,} trajectories with callsigns")
            
            # Show sample
            print(f"\n   Sample callsigns in final data:")
            sample_callsigns = df[df['callsign'].notna()]['callsign'].head(10).tolist()
            for cs in sample_callsigns[:5]:
                print(f"     - {cs}")
        else:
            print(f"\n⚠️  WARNING: Callsign column lost during processing!")
        
        # Summary
        print(f"\n✅ Feature Extraction Complete")
        print(f"   Total records: {len(df):,}")
        print(f"   Total features: {len(df.columns)}")
        
        # Feature categories count
        temporal_features = [c for c in df.columns if any(x in c for x in ['hour', 'day', 'time', 'weekend', 'peak'])]
        performance_features = [c for c in df.columns if any(x in c for x in ['speed', 'altitude', 'velocity', 'climb', 'descent'])]
        risk_features = [c for c in df.columns if any(x in c for x in ['anomaly', 'variability', 'risk', 'zscore'])]
        
        print(f"\n   Feature Breakdown:")
        print(f"     Temporal features:    {len(temporal_features)}")
        print(f"     Performance features: {len(performance_features)}")
        print(f"     Risk features:        {len(risk_features)}")
        
        # Save to CSV
        output_path = Path(__file__).parent.parent / 'data' / 'operational_features.csv'
        df.to_csv(output_path, index=False)
        print(f"\n✅ All features saved to: {output_path}")
        
        # Verify saved file has callsigns
        if 'callsign' in df.columns:
            print(f"   ✓ Callsign column included in saved file")
        
        # Save feature names for reference
        feature_list_path = Path(__file__).parent.parent / 'data' / 'feature_names.txt'
        with open(feature_list_path, 'w', encoding='utf-8') as f:
            f.write("AIRP - Operational Features List\n")
            f.write("="*70 + "\n\n")
            f.write(f"Total Features: {len(df.columns)}\n")
            f.write(f"Total Samples: {len(df)}\n\n")
            
            if 'callsign' in df.columns:
                f.write("* Includes callsign column for flight identification\n\n")
            
            f.write("Feature List:\n")
            f.write("-"*70 + "\n")
            for col in sorted(df.columns):
                f.write(f"{col}\n")
        print(f"✅ Feature names saved to: {feature_list_path}")
        
        return df
    
    def get_ml_ready_features(self, df: pd.DataFrame = None) -> tuple:
        """
        Get features ready for ML models
        
        Args:
            df: Optional DataFrame, if None will load from file
        
        Returns:
            Tuple of (feature_matrix, feature_names, metadata)
        """
        if df is None:
            features_path = Path(__file__).parent.parent / 'data' / 'operational_features.csv'
            df = pd.read_csv(features_path)
        
        # Exclude non-feature columns (but KEEP for metadata)
        exclude_cols = [
            'trajectory_id', 'icao24', 'callsign', 'start_time', 'end_time',
            'start_lat', 'start_lon', 'end_lat', 'end_lon',
            'trajectory_type', 'time_period', 'efficiency_category'
        ]
        
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        
        # Get feature matrix
        X = df[feature_cols].fillna(0)  # Fill NaN with 0
        
        # Metadata - INCLUDE CALLSIGN
        metadata_cols = ['trajectory_id', 'icao24']
        if 'callsign' in df.columns:
            metadata_cols.append('callsign')
        
        metadata = df[metadata_cols].copy()
        
        print(f"\n✅ ML-Ready Features:")
        print(f"   Samples: {len(X):,}")
        print(f"   Features: {len(feature_cols)}")
        
        if 'callsign' in metadata.columns:
            print(f"   ✓ Metadata includes callsigns for {metadata['callsign'].notna().sum():,} flights")
        
        return X, feature_cols, metadata
    
    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("Operational Features Extractor")
    print("Aviation Intelligence & Risk Prediction Platform")
    print("="*70)
    
    extractor = OperationalFeaturesExtractor()
    
    try:
        # Extract all features
        features_df = extractor.extract_all_features()
        
        # Get ML-ready features
        print("\n" + "="*70)
        print("PREPARING ML-READY FEATURES")
        print("="*70)
        X, feature_names, metadata = extractor.get_ml_ready_features(features_df)
        
        print("\n" + "="*70)
        print("EXTRACTION COMPLETE")
        print("="*70)
        print(f"\n✅ All operational features extracted and saved!")
        print(f"✅ Data is ready for ML modeling (Phase 3)")
        
        if 'callsign' in features_df.columns:
            print(f"✅ Callsigns preserved and available for dashboard!")
        
        print(f"\nNext steps:")
        print(f"  1. Run ML models: python 4_models/train_all_models.py")
        print(f"  2. Launch dashboard: streamlit run 6_dashboard/app.py")
        print(f"  3. Dashboard will show real flight callsigns!")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Please run trajectory_analyzer.py first!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        extractor.close()


if __name__ == "__main__":
    main()