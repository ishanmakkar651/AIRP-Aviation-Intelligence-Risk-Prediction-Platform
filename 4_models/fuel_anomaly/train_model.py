"""
Fuel Inefficiency Anomaly Detection
Identifies unusual fuel consumption patterns
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
import joblib
import json
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns


class FuelAnomalyDetector:
    """Detects fuel inefficiency anomalies"""
    
    def __init__(self):
        """Initialize detector"""
        self.scaler = StandardScaler()
        self.anomaly_model = None
        self.model_info = {}
    
    def load_data(self) -> pd.DataFrame:
        """Load operational features with fuel efficiency data"""
        features_path = Path(__file__).parent.parent.parent / 'data' / 'operational_features.csv'
        df = pd.read_csv(features_path)
        print(f"✅ Loaded {len(df):,} flight records")
        return df
    
    def prepare_fuel_features(self, df: pd.DataFrame) -> tuple:
        """
        Prepare features specifically for fuel efficiency analysis
        
        Returns:
            (feature_matrix, feature_names, metadata)
        """
        fuel_feature_cols = [
            # Core efficiency metrics
            'fuel_efficiency_score',
            'altitude_stability_score',
            'speed_stability_score',
            'route_directness_score',
            
            # Variance indicators
            'altitude_variance',
            'velocity_variance',
            'altitude_cv',
            'speed_cv',
            
            # Performance metrics
            'avg_speed_kmh',
            'max_altitude_ft',
            'altitude_range_ft',
            'speed_range_kmh',
            
            # Operational metrics
            'distance_per_minute',
            'route_efficiency',
            'airborne_ratio',
            
            # Flight characteristics
            'duration_minutes',
            'total_distance_km'
        ]
        
        # Filter to existing columns
        available_cols = [c for c in fuel_feature_cols if c in df.columns]
        
        X = df[available_cols].fillna(0)
        metadata = df[['trajectory_id', 'icao24', 'callsign', 'start_time', 'efficiency_category']].copy()
        
        print(f"✅ Prepared {len(X):,} samples with {len(available_cols)} fuel features")
        
        return X, available_cols, metadata
    
    def train_anomaly_detector(self, X: pd.DataFrame) -> tuple:
        """
        Train Isolation Forest for fuel anomaly detection
        
        Args:
            X: Feature matrix
        
        Returns:
            (anomaly_labels, anomaly_scores)
        """
        print("\n🔍 Training fuel anomaly detection model...")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest with higher contamination for fuel issues
        # Expect ~10% of flights to have fuel inefficiency issues
        self.anomaly_model = IsolationForest(
            contamination=0.10,
            random_state=42,
            n_estimators=150,
            max_samples='auto',
            bootstrap=True,
            n_jobs=-1
        )
        
        anomaly_labels = self.anomaly_model.fit_predict(X_scaled)
        anomaly_scores = self.anomaly_model.score_samples(X_scaled)
        
        # Statistics
        n_anomalies = (anomaly_labels == -1).sum()
        print(f"✅ Detected {n_anomalies:,} fuel inefficiency anomalies ({100*n_anomalies/len(X):.1f}%)")
        
        return anomaly_labels, anomaly_scores
    
    def analyze_anomaly_patterns(self, df: pd.DataFrame) -> dict:
        """
        Analyze patterns in detected anomalies
        
        Args:
            df: DataFrame with anomaly labels
        
        Returns:
            Dictionary with pattern analysis
        """
        patterns = {}
        
        anomalous = df[df['fuel_anomaly'] == -1]
        normal = df[df['fuel_anomaly'] == 1]
        
        # Compare efficiency scores
        patterns['avg_efficiency_anomalous'] = anomalous['fuel_efficiency_score'].mean()
        patterns['avg_efficiency_normal'] = normal['fuel_efficiency_score'].mean()
        patterns['efficiency_difference'] = patterns['avg_efficiency_normal'] - patterns['avg_efficiency_anomalous']
        
        # Variance comparison
        patterns['avg_altitude_var_anomalous'] = anomalous['altitude_variance'].mean()
        patterns['avg_altitude_var_normal'] = normal['altitude_variance'].mean()
        
        patterns['avg_speed_var_anomalous'] = anomalous['velocity_variance'].mean()
        patterns['avg_speed_var_normal'] = normal['velocity_variance'].mean()
        
        # Route efficiency
        if 'route_efficiency' in df.columns:
            patterns['avg_route_eff_anomalous'] = anomalous['route_efficiency'].mean()
            patterns['avg_route_eff_normal'] = normal['route_efficiency'].mean()
        
        # Category distribution
        if 'efficiency_category' in anomalous.columns:
            patterns['anomaly_by_category'] = anomalous['efficiency_category'].value_counts().to_dict()
        
        return patterns
    
    def identify_inefficiency_causes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify likely causes of fuel inefficiency
        
        Args:
            df: DataFrame with anomalies
        
        Returns:
            DataFrame with cause flags
        """
        df = df.copy()
        
        # Initialize cause flags
        df['cause_altitude_instability'] = 0
        df['cause_speed_instability'] = 0
        df['cause_poor_routing'] = 0
        df['cause_holding_pattern'] = 0
        
        # Identify causes for anomalous flights
        anomalous = df['fuel_anomaly'] == -1
        
        # High altitude variance threshold (top 25% among anomalies)
        alt_var_threshold = df[anomalous]['altitude_variance'].quantile(0.75)
        df.loc[anomalous & (df['altitude_variance'] > alt_var_threshold), 'cause_altitude_instability'] = 1
        
        # High speed variance threshold
        speed_var_threshold = df[anomalous]['velocity_variance'].quantile(0.75)
        df.loc[anomalous & (df['velocity_variance'] > speed_var_threshold), 'cause_speed_instability'] = 1
        
        # Poor route efficiency
        if 'route_efficiency' in df.columns:
            route_eff_threshold = df[anomalous]['route_efficiency'].quantile(0.25)
            df.loc[anomalous & (df['route_efficiency'] < route_eff_threshold), 'cause_poor_routing'] = 1
        
        # Low speed efficiency (potential holding)
        if 'speed_efficiency' in df.columns:
            speed_eff_threshold = 150  # km/h
            df.loc[anomalous & (df['speed_efficiency'] < speed_eff_threshold), 'cause_holding_pattern'] = 1
        
        # Primary cause (most severe)
        causes = ['cause_altitude_instability', 'cause_speed_instability', 
                 'cause_poor_routing', 'cause_holding_pattern']
        
        def get_primary_cause(row):
            if row['fuel_anomaly'] != -1:
                return 'Normal Operation'
            
            active_causes = [c.replace('cause_', '').replace('_', ' ').title() 
                           for c in causes if row.get(c, 0) == 1]
            
            if not active_causes:
                return 'Unknown Inefficiency'
            elif len(active_causes) == 1:
                return active_causes[0]
            else:
                return 'Multiple Causes'
        
        df['primary_inefficiency_cause'] = df.apply(get_primary_cause, axis=1)
        
        return df
    
    def generate_visualizations(self, df: pd.DataFrame):
        """Generate analysis visualizations"""
        viz_dir = Path(__file__).parent / 'visualizations'
        viz_dir.mkdir(exist_ok=True)
        
        # 1. Efficiency score distribution by anomaly status
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        df[df['fuel_anomaly'] == 1]['fuel_efficiency_score'].hist(bins=30, ax=axes[0], alpha=0.7, color='green')
        axes[0].set_title('Normal Flights - Efficiency Distribution')
        axes[0].set_xlabel('Fuel Efficiency Score')
        axes[0].set_ylabel('Count')
        
        df[df['fuel_anomaly'] == -1]['fuel_efficiency_score'].hist(bins=30, ax=axes[1], alpha=0.7, color='red')
        axes[1].set_title('Anomalous Flights - Efficiency Distribution')
        axes[1].set_xlabel('Fuel Efficiency Score')
        axes[1].set_ylabel('Count')
        
        plt.tight_layout()
        plt.savefig(viz_dir / 'efficiency_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Visualization saved: {viz_dir / 'efficiency_distribution.png'}")
    
    def train_and_detect(self) -> pd.DataFrame:
        """
        Main training and detection pipeline
        
        Returns:
            DataFrame with anomaly detection results
        """
        print("\n" + "="*70)
        print("FUEL INEFFICIENCY ANOMALY DETECTION")
        print("="*70)
        
        # Load and prepare data
        print("\n1. Loading and preparing data...")
        df = self.load_data()
        X, feature_names, metadata = self.prepare_fuel_features(df)
        
        # Train anomaly detector
        print("\n2. Training anomaly detection model...")
        anomaly_labels, anomaly_scores = self.train_anomaly_detector(X)
        
        # Add results to dataframe
        df['fuel_anomaly'] = anomaly_labels
        df['fuel_anomaly_score'] = anomaly_scores
        
        # Normalize scores (lower score = more anomalous)
        min_score = anomaly_scores.min()
        max_score = anomaly_scores.max()
        df['fuel_anomaly_score_normalized'] = 100 * (anomaly_scores - min_score) / (max_score - min_score)
        
        # Analyze patterns
        print("\n3. Analyzing anomaly patterns...")
        patterns = self.analyze_anomaly_patterns(df)
        
        print(f"\n📊 Anomaly Pattern Analysis:")
        print(f"   Normal flights avg efficiency:    {patterns['avg_efficiency_normal']:.1f}")
        print(f"   Anomalous flights avg efficiency: {patterns['avg_efficiency_anomalous']:.1f}")
        print(f"   Efficiency difference:            {patterns['efficiency_difference']:.1f} points")
        
        # Identify causes
        print("\n4. Identifying inefficiency causes...")
        df = self.identify_inefficiency_causes(df)
        
        # Summary
        print("\n" + "="*70)
        print("DETECTION RESULTS")
        print("="*70)
        
        print(f"\n🔍 Anomaly Detection Summary:")
        print(f"   Total flights analyzed:     {len(df):,}")
        print(f"   Normal operations:          {(df['fuel_anomaly'] == 1).sum():,} ({100*(df['fuel_anomaly'] == 1).sum()/len(df):.1f}%)")
        print(f"   Fuel inefficiency detected: {(df['fuel_anomaly'] == -1).sum():,} ({100*(df['fuel_anomaly'] == -1).sum()/len(df):.1f}%)")
        
        print(f"\n📋 Inefficiency Causes:")
        cause_dist = df[df['fuel_anomaly'] == -1]['primary_inefficiency_cause'].value_counts()
        for cause, count in cause_dist.items():
            print(f"   {cause:25s}: {count:4d}")
        
        # Top inefficient flights
        print(f"\n⚠️  Top 10 Most Inefficient Flights:")
        inefficient = df[df['fuel_anomaly'] == -1].nsmallest(10, 'fuel_efficiency_score')[
            ['callsign', 'fuel_efficiency_score', 'primary_inefficiency_cause', 'altitude_variance', 'velocity_variance']
        ]
        for idx, row in inefficient.iterrows():
            print(f"   {row['callsign'] or 'N/A':12s}: Score {row['fuel_efficiency_score']:5.1f} | Cause: {row['primary_inefficiency_cause']}")
        
        # Generate visualizations
        print("\n5. Generating visualizations...")
        self.generate_visualizations(df)
        
        # Save results
        output_path = Path(__file__).parent.parent.parent / 'data' / 'fuel_anomalies.csv'
        fuel_output = df[['trajectory_id', 'icao24', 'callsign', 'start_time',
                         'fuel_efficiency_score', 'fuel_anomaly', 'fuel_anomaly_score_normalized',
                         'primary_inefficiency_cause']].copy()
        fuel_output.to_csv(output_path, index=False)
        print(f"\n✅ Anomaly detection results saved to: {output_path}")
        
        # Save model
        model_dir = Path(__file__).parent
        joblib.dump(self.scaler, model_dir / 'scaler.pkl')
        joblib.dump(self.anomaly_model, model_dir / 'anomaly_model.pkl')
        
        # Save model info
        self.model_info = {
            'trained_at': datetime.now().isoformat(),
            'n_samples': len(df),
            'n_features': len(feature_names),
            'feature_names': feature_names,
            'contamination': 0.10,
            'n_anomalies': int((df['fuel_anomaly'] == -1).sum()),
            'patterns': patterns,
            'cause_distribution': cause_dist.to_dict()
        }
        
        with open(model_dir / 'model_info.json', 'w') as f:
            json.dump(self.model_info, f, indent=2, default=str)
        
        print(f"✅ Model saved to: {model_dir}")
        
        return df


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("Fuel Inefficiency Anomaly Detection Training")
    print("Aviation Intelligence & Risk Prediction Platform")
    print("="*70)
    
    detector = FuelAnomalyDetector()
    
    try:
        # Train and detect anomalies
        results_df = detector.train_and_detect()
        
        print("\n" + "="*70)
        print("TRAINING COMPLETE")
        print("="*70)
        print("\n✅ Fuel anomaly detection model trained successfully!")
        print(f"✅ {len(results_df):,} flights analyzed")
        print(f"✅ Model and results saved")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()