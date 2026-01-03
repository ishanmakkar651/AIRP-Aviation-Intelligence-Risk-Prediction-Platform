"""
Operational Risk Scoring Model
Uses ensemble methods to score flight operational risk
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import json
from datetime import datetime


class RiskScoringModel:
    """Operational risk scoring using ensemble methods"""
    
    def __init__(self):
        """Initialize risk scoring model"""
        self.scaler = StandardScaler()
        self.anomaly_detector = None
        self.risk_weights = {
            'speed_anomaly': 0.25,
            'altitude_anomaly': 0.25,
            'high_speed_variability': 0.15,
            'high_altitude_variability': 0.15,
            'complex_maneuvers': 0.10,
            'low_fuel_efficiency': 0.10
        }
        self.model_info = {}
    
    def load_data(self) -> pd.DataFrame:
        """Load operational features"""
        features_path = Path(__file__).parent.parent.parent / 'data' / 'operational_features.csv'
        df = pd.read_csv(features_path)
        print(f"✅ Loaded {len(df):,} flight records")
        return df
    
    def prepare_risk_features(self, df: pd.DataFrame) -> tuple:
        """
        Prepare features for risk scoring
        
        Returns:
            (feature_matrix, feature_names, metadata)
        """
        # Select relevant risk features
        risk_feature_cols = [
            # Variance features
            'altitude_variance', 'velocity_variance',
            'altitude_cv', 'speed_cv',
            
            # Performance features
            'speed_range_kmh', 'altitude_range_ft',
            'max_climb_rate_fpm', 'max_descent_rate_fpm',
            
            # Statistical features
            'speed_zscore', 'altitude_zscore',
            
            # Efficiency features
            'fuel_efficiency_score',
            'altitude_stability_score',
            'speed_stability_score',
            
            # Operational features
            'duration_minutes',
            'total_distance_km',
            'avg_speed_kmh',
            'max_altitude_ft'
        ]
        
        # Filter to existing columns
        available_cols = [c for c in risk_feature_cols if c in df.columns]
        
        X = df[available_cols].fillna(0)
        metadata = df[['trajectory_id', 'icao24', 'callsign', 'start_time']].copy()
        
        print(f"✅ Prepared {len(X):,} samples with {len(available_cols)} features")
        
        return X, available_cols, metadata
    
    def detect_anomalies(self, X: pd.DataFrame) -> np.ndarray:
        """
        Detect operational anomalies using Isolation Forest
        
        Args:
            X: Feature matrix
        
        Returns:
            Anomaly scores (-1 = anomaly, 1 = normal)
        """
        print("\n🔍 Training anomaly detection model...")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        # contamination=0.05 means we expect ~5% of flights to be anomalous
        self.anomaly_detector = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1
        )
        
        anomaly_labels = self.anomaly_detector.fit_predict(X_scaled)
        anomaly_scores = self.anomaly_detector.score_samples(X_scaled)
        
        # Count anomalies
        n_anomalies = (anomaly_labels == -1).sum()
        print(f"✅ Detected {n_anomalies:,} anomalous flights ({100*n_anomalies/len(X):.1f}%)")
        
        return anomaly_labels, anomaly_scores
    
    def calculate_weighted_risk_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate weighted risk score from risk indicators
        
        Args:
            df: DataFrame with risk indicator columns
        
        Returns:
            DataFrame with risk scores added
        """
        df = df.copy()
        
        # Create low fuel efficiency flag
        df['low_fuel_efficiency'] = (df['fuel_efficiency_score'] < 60).astype(int)
        
        # Calculate weighted risk score (0-100)
        risk_score = 0
        
        for indicator, weight in self.risk_weights.items():
            if indicator in df.columns:
                risk_score += df[indicator] * weight * 100
        
        df['weighted_risk_score'] = risk_score
        
        return df
    
    def assign_risk_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assign risk levels based on multiple factors
        
        Args:
            df: DataFrame with risk scores
        
        Returns:
            DataFrame with risk levels assigned
        """
        df = df.copy()
        
        # Combine anomaly detection with weighted scores
        # Final risk score considers both
        df['final_risk_score'] = (
            0.6 * df['weighted_risk_score'] +  # 60% from indicators
            0.4 * (100 - df['anomaly_score_normalized'])  # 40% from anomaly detection
        )
        
        # Assign risk levels
        df['risk_level'] = pd.cut(
            df['final_risk_score'],
            bins=[0, 30, 60, 85, 100],
            labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        )
        
        return df
    
    def train_and_score(self) -> pd.DataFrame:
        """
        Main training and scoring pipeline
        
        Returns:
            DataFrame with risk scores and levels
        """
        print("\n" + "="*70)
        print("OPERATIONAL RISK SCORING MODEL")
        print("="*70)
        
        # Load and prepare data
        print("\n1. Loading and preparing data...")
        df = self.load_data()
        X, feature_names, metadata = self.prepare_risk_features(df)
        
        # Detect anomalies
        print("\n2. Detecting operational anomalies...")
        anomaly_labels, anomaly_scores = self.detect_anomalies(X)
        
        # Add anomaly results to dataframe
        df['is_anomaly'] = anomaly_labels
        df['anomaly_score'] = anomaly_scores
        
        # Normalize anomaly scores to 0-100 (higher = more normal)
        min_score = anomaly_scores.min()
        max_score = anomaly_scores.max()
        df['anomaly_score_normalized'] = 100 * (anomaly_scores - min_score) / (max_score - min_score)
        
        # Calculate weighted risk scores
        print("\n3. Calculating weighted risk scores...")
        df = self.calculate_weighted_risk_score(df)
        
        # Assign final risk levels
        print("\n4. Assigning risk levels...")
        df = self.assign_risk_levels(df)
        
        # Summary statistics
        print("\n" + "="*70)
        print("RISK SCORING RESULTS")
        print("="*70)
        
        print(f"\n📊 Risk Level Distribution:")
        risk_dist = df['risk_level'].value_counts().sort_index()
        for level, count in risk_dist.items():
            pct = 100 * count / len(df)
            print(f"   {level:12s}: {count:4d} ({pct:5.1f}%)")
        
        print(f"\n⚠️  Anomalous Flights: {(df['is_anomaly'] == -1).sum():,} ({100*(df['is_anomaly'] == -1).sum()/len(df):.1f}%)")
        
        print(f"\n📈 Risk Score Statistics:")
        print(f"   Mean:   {df['final_risk_score'].mean():.1f}")
        print(f"   Median: {df['final_risk_score'].median():.1f}")
        print(f"   Std:    {df['final_risk_score'].std():.1f}")
        
        # Top risky flights
        print(f"\n🚨 Top 10 Highest Risk Flights:")
        high_risk = df.nlargest(10, 'final_risk_score')[
            ['callsign', 'final_risk_score', 'risk_level', 'fuel_efficiency_score', 'is_anomaly']
        ]
        for idx, row in high_risk.iterrows():
            anomaly_flag = "⚠️ ANOMALY" if row['is_anomaly'] == -1 else ""
            print(f"   {row['callsign'] or 'N/A':12s}: Risk {row['final_risk_score']:5.1f} | {row['risk_level']:8s} | Efficiency {row['fuel_efficiency_score']:5.1f} {anomaly_flag}")
        
        # Save results
        output_path = Path(__file__).parent.parent.parent / 'data' / 'risk_scores.csv'
        risk_output = df[['trajectory_id', 'icao24', 'callsign', 'start_time',
                         'weighted_risk_score', 'anomaly_score_normalized', 
                         'final_risk_score', 'risk_level', 'is_anomaly']].copy()
        risk_output.to_csv(output_path, index=False)
        print(f"\n✅ Risk scores saved to: {output_path}")
        
        # Save model
        model_dir = Path(__file__).parent
        model_dir.mkdir(exist_ok=True, parents=True)
        
        joblib.dump(self.scaler, model_dir / 'scaler.pkl')
        joblib.dump(self.anomaly_detector, model_dir / 'anomaly_detector.pkl')
        
        # Save model info
        self.model_info = {
            'trained_at': datetime.now().isoformat(),
            'n_samples': len(df),
            'n_features': len(feature_names),
            'feature_names': feature_names,
            'risk_weights': self.risk_weights,
            'contamination': 0.05,
            'risk_distribution': risk_dist.to_dict()
        }
        
        with open(model_dir / 'model_info.json', 'w') as f:
            json.dump(self.model_info, f, indent=2)
        
        print(f"✅ Model saved to: {model_dir}")
        
        return df
    
    def predict_risk(self, X: pd.DataFrame) -> dict:
        """
        Predict risk for new flights
        
        Args:
            X: Feature matrix for new flights
        
        Returns:
            Dictionary with risk predictions
        """
        X_scaled = self.scaler.transform(X)
        
        anomaly_label = self.anomaly_detector.predict(X_scaled)
        anomaly_score = self.anomaly_detector.score_samples(X_scaled)
        
        # Normalize and calculate risk
        anomaly_score_norm = 100 * (anomaly_score - anomaly_score.min()) / (anomaly_score.max() - anomaly_score.min())
        
        return {
            'anomaly_label': anomaly_label,
            'anomaly_score': anomaly_score_norm,
        }


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("Operational Risk Scoring Model Training")
    print("Aviation Intelligence & Risk Prediction Platform")
    print("="*70)
    
    model = RiskScoringModel()
    
    try:
        # Train and score all flights
        results_df = model.train_and_score()
        
        print("\n" + "="*70)
        print("TRAINING COMPLETE")
        print("="*70)
        print("\n✅ Risk scoring model trained successfully!")
        print(f"✅ {len(results_df):,} flights scored")
        print(f"✅ Model saved for future predictions")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()