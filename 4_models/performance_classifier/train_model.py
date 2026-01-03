"""
Flight Performance Classifier
Predicts flight efficiency category using XGBoost
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import xgboost as xgb
import joblib
import json
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


class PerformanceClassifier:
    """Classifies flight performance into efficiency categories"""
    
    def __init__(self):
        """Initialize classifier"""
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.model = None
        self.feature_importance = None
        self.model_info = {}
    
    def load_data(self) -> pd.DataFrame:
        """Load operational features"""
        features_path = Path(__file__).parent.parent.parent / 'data' / 'operational_features.csv'
        df = pd.read_csv(features_path)
        print(f"✅ Loaded {len(df):,} flight records")
        return df
    
    def prepare_classification_features(self, df: pd.DataFrame) -> tuple:
        """
        Prepare features for efficiency classification
        
        Returns:
            (X, y, feature_names, metadata)
        """
        # Select predictive features (excluding efficiency scores themselves)
        feature_cols = [
            # Temporal
            'hour_of_day', 'day_of_week', 'is_weekend', 'is_peak_hour',
            
            # Flight characteristics
            'duration_minutes', 'total_distance_km',
            'max_altitude_ft', 'avg_altitude_ft',
            'avg_speed_kmh', 'max_speed_kmh',
            
            # Variance/stability
            'altitude_variance', 'velocity_variance',
            'altitude_cv', 'speed_cv',
            'altitude_range_ft', 'speed_range_kmh',
            
            # Performance
            'max_climb_rate_fpm', 'max_descent_rate_fpm',
            'distance_per_minute', 'km_per_altitude_km',
            
            # Operational
            'airborne_ratio', 'trajectory_complexity',
            
            # Risk indicators
            'is_speed_anomaly', 'is_altitude_anomaly',
            'high_speed_variability', 'high_altitude_variability',
            'complex_maneuvers'
        ]
        
        # Filter to existing columns
        available_cols = [c for c in feature_cols if c in df.columns]
        
        # Target variable
        if 'efficiency_category' not in df.columns:
            raise ValueError("efficiency_category column not found!")
        
        # Remove rows with missing target
        df_clean = df[df['efficiency_category'].notna()].copy()
        
        X = df_clean[available_cols].fillna(0)
        y = df_clean['efficiency_category']
        metadata = df_clean[['trajectory_id', 'icao24', 'callsign', 'start_time', 'fuel_efficiency_score']].copy()
        
        print(f"✅ Prepared {len(X):,} samples with {len(available_cols)} features")
        print(f"\n📊 Target Distribution:")
        for category, count in y.value_counts().sort_index().items():
            pct = 100 * count / len(y)
            print(f"   {category:12s}: {count:4d} ({pct:5.1f}%)")
        
        return X, y, available_cols, metadata
    
    def train_model(self, X_train, y_train, X_test, y_test) -> dict:
        """
        Train XGBoost classifier
        
        Returns:
            Dictionary with training results
        """
        print("\n🤖 Training XGBoost classifier...")
        
        # Encode labels
        y_train_encoded = self.label_encoder.fit_transform(y_train)
        y_test_encoded = self.label_encoder.transform(y_test)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost
        self.model = xgb.XGBClassifier(
            objective='multi:softmax',
            num_class=len(self.label_encoder.classes_),
            max_depth=6,
            learning_rate=0.1,
            n_estimators=200,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            eval_metric='mlogloss'
        )
        
        # Fit model
        self.model.fit(
            X_train_scaled, y_train_encoded,
            eval_set=[(X_test_scaled, y_test_encoded)],
            verbose=False
        )
        
        # Predictions
        y_train_pred = self.model.predict(X_train_scaled)
        y_test_pred = self.model.predict(X_test_scaled)
        
        # Convert back to labels
        y_train_pred_labels = self.label_encoder.inverse_transform(y_train_pred)
        y_test_pred_labels = self.label_encoder.inverse_transform(y_test_pred)
        
        # Metrics
        train_accuracy = accuracy_score(y_train, y_train_pred_labels)
        test_accuracy = accuracy_score(y_test, y_test_pred_labels)
        
        print(f"✅ Training complete!")
        print(f"   Training accuracy:   {train_accuracy:.3f}")
        print(f"   Test accuracy:       {test_accuracy:.3f}")
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        results = {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'y_test': y_test,
            'y_test_pred': y_test_pred_labels,
            'confusion_matrix': confusion_matrix(y_test, y_test_pred_labels),
            'classification_report': classification_report(y_test, y_test_pred_labels)
        }
        
        return results
    
    def evaluate_model(self, results: dict):
        """Print detailed model evaluation"""
        print("\n" + "="*70)
        print("MODEL EVALUATION")
        print("="*70)
        
        print(f"\n📊 Classification Report:")
        print(results['classification_report'])
        
        print(f"\n🎯 Confusion Matrix:")
        cm = results['confusion_matrix']
        labels = self.label_encoder.classes_
        
        # Pretty print confusion matrix
        cm_df = pd.DataFrame(cm, index=labels, columns=labels)
        print(cm_df)
        
        print(f"\n⭐ Top 10 Most Important Features:")
        for idx, row in self.feature_importance.head(10).iterrows():
            print(f"   {row['feature']:30s}: {row['importance']:.4f}")
    
    def generate_visualizations(self, results: dict):
        """Generate model evaluation visualizations"""
        viz_dir = Path(__file__).parent / 'visualizations'
        viz_dir.mkdir(exist_ok=True)
        
        # 1. Confusion Matrix Heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        cm = results['confusion_matrix']
        labels = self.label_encoder.classes_
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=labels, yticklabels=labels, ax=ax)
        ax.set_title('Confusion Matrix - Efficiency Classification')
        ax.set_xlabel('Predicted Category')
        ax.set_ylabel('True Category')
        plt.tight_layout()
        plt.savefig(viz_dir / 'confusion_matrix.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # 2. Feature Importance
        fig, ax = plt.subplots(figsize=(10, 8))
        top_features = self.feature_importance.head(15)
        ax.barh(range(len(top_features)), top_features['importance'])
        ax.set_yticks(range(len(top_features)))
        ax.set_yticklabels(top_features['feature'])
        ax.set_xlabel('Importance Score')
        ax.set_title('Top 15 Feature Importance')
        ax.invert_yaxis()
        plt.tight_layout()
        plt.savefig(viz_dir / 'feature_importance.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"\n✅ Visualizations saved to: {viz_dir}/")
    
    def train_and_evaluate(self) -> dict:
        """
        Main training and evaluation pipeline
        
        Returns:
            Dictionary with results
        """
        print("\n" + "="*70)
        print("FLIGHT PERFORMANCE CLASSIFIER")
        print("="*70)
        
        # Load and prepare data
        print("\n1. Loading and preparing data...")
        df = self.load_data()
        X, y, feature_names, metadata = self.prepare_classification_features(df)
        
        # Train/test split
        print("\n2. Splitting data (80% train, 20% test)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        print(f"   Training samples: {len(X_train):,}")
        print(f"   Test samples:     {len(X_test):,}")
        
        # Train model
        print("\n3. Training XGBoost classifier...")
        results = self.train_model(X_train, y_train, X_test, y_test)
        
        # Evaluate
        print("\n4. Evaluating model performance...")
        self.evaluate_model(results)
        
        # Visualizations
        print("\n5. Generating visualizations...")
        self.generate_visualizations(results)
        
        # Save model
        print("\n6. Saving model...")
        model_dir = Path(__file__).parent
        
        joblib.dump(self.scaler, model_dir / 'scaler.pkl')
        joblib.dump(self.label_encoder, model_dir / 'label_encoder.pkl')
        joblib.dump(self.model, model_dir / 'xgboost_model.pkl')
        
        # Save feature importance
        self.feature_importance.to_csv(model_dir / 'feature_importance.csv', index=False)
        
        # Save model info
        self.model_info = {
            'trained_at': datetime.now().isoformat(),
            'n_samples': len(X),
            'n_features': len(feature_names),
            'feature_names': feature_names,
            'classes': self.label_encoder.classes_.tolist(),
            'train_accuracy': float(results['train_accuracy']),
            'test_accuracy': float(results['test_accuracy']),
            'model_params': self.model.get_params()
        }
        
        with open(model_dir / 'model_info.json', 'w') as f:
            json.dump(self.model_info, f, indent=2, default=str)
        
        print(f"✅ Model saved to: {model_dir}")
        
        return results


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("Flight Performance Classifier Training")
    print("Aviation Intelligence & Risk Prediction Platform")
    print("="*70)
    
    classifier = PerformanceClassifier()
    
    try:
        # Train and evaluate
        results = classifier.train_and_evaluate()
        
        print("\n" + "="*70)
        print("TRAINING COMPLETE")
        print("="*70)
        print("\n✅ Performance classifier trained successfully!")
        print(f"✅ Test accuracy: {results['test_accuracy']:.3f}")
        print(f"✅ Model saved for future predictions")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()