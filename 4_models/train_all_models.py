"""
Master ML Training Pipeline
Trains all ML models sequentially
"""

import sys
from pathlib import Path
import importlib.util
from datetime import datetime


def load_module(module_path: Path, module_name: str):
    """Dynamically load a Python module"""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)


def run_ml_pipeline():
    """Run complete ML training pipeline"""
    
    print_header("AIRP ML TRAINING PIPELINE")
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📚 Training 3 ML Models:")
    print("   1. Operational Risk Scoring (Ensemble)")
    print("   2. Fuel Inefficiency Detection (Anomaly Detection)")
    print("   3. Flight Performance Classification (XGBoost)")
    
    base_path = Path(__file__).parent
    models_trained = []
    
    try:
        # Model 1: Risk Scoring
        print_header("MODEL 1: OPERATIONAL RISK SCORING")
        
        risk_module = load_module(
            base_path / 'risk_scoring' / 'train_model.py',
            'risk_scoring'
        )
        
        risk_model = risk_module.RiskScoringModel()
        risk_results = risk_model.train_and_score()
        models_trained.append(('Risk Scoring', True))
        
        print(f"\n✅ Model 1 Complete: {len(risk_results):,} flights scored")
        
        # Model 2: Fuel Anomaly Detection
        print_header("MODEL 2: FUEL INEFFICIENCY DETECTION")
        
        fuel_module = load_module(
            base_path / 'fuel_anomaly' / 'train_model.py',
            'fuel_anomaly'
        )
        
        fuel_detector = fuel_module.FuelAnomalyDetector()
        fuel_results = fuel_detector.train_and_detect()
        models_trained.append(('Fuel Anomaly Detection', True))
        
        print(f"\n✅ Model 2 Complete: {(fuel_results['fuel_anomaly'] == -1).sum():,} anomalies detected")
        
        # Model 3: Performance Classifier
        print_header("MODEL 3: FLIGHT PERFORMANCE CLASSIFIER")
        
        perf_module = load_module(
            base_path / 'performance_classifier' / 'train_model.py',
            'performance_classifier'
        )
        
        perf_classifier = perf_module.PerformanceClassifier()
        perf_results = perf_classifier.train_and_evaluate()
        models_trained.append(('Performance Classifier', True))
        
        print(f"\n✅ Model 3 Complete: Test accuracy {perf_results['test_accuracy']:.3f}")
        
        # Pipeline Summary
        print_header("ML PIPELINE EXECUTION SUMMARY")
        
        print(f"\n🎯 Models Trained:")
        for model_name, success in models_trained:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"   {model_name:30s}: {status}")
        
        print(f"\n📊 Output Files Generated:")
        data_dir = Path(__file__).parent.parent / 'data'
        output_files = [
            'risk_scores.csv',
            'fuel_anomalies.csv'
        ]
        for file in output_files:
            filepath = data_dir / file
            if filepath.exists():
                print(f"   ✅ {filepath}")
            else:
                print(f"   ⚠️  {filepath} (not found)")
        
        print(f"\n📁 Model Artifacts Saved:")
        model_dirs = ['risk_scoring', 'fuel_anomaly', 'performance_classifier']
        for model_dir in model_dirs:
            model_path = Path(__file__).parent / model_dir
            if model_path.exists():
                model_files = list(model_path.glob('*.pkl')) + list(model_path.glob('*.json'))
                print(f"   {model_dir}:")
                for mf in model_files:
                    print(f"      ✅ {mf.name}")
        
        print(f"\n✅ All ML Models Trained Successfully!")
        print(f"\n🚀 Ready for Phase 4: Dashboard & LLM Integration")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline Error: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\n📋 Models Trained Before Error:")
        for model_name, success in models_trained:
            print(f"   {model_name}: {'✅' if success else '❌'}")
        
        return False


def main():
    """Main execution"""
    success = run_ml_pipeline()
    
    if success:
        print("\n" + "="*80)
        print("  NEXT STEPS")
        print("="*80)
        
        print("\n1. Review Model Results:")
        print("   - Check data/risk_scores.csv")
        print("   - Check data/fuel_anomalies.csv")
        print("   - Review visualizations in model folders")
        
        print("\n2. Analyze Model Performance:")
        print("   - Feature importance rankings")
        print("   - Confusion matrices")
        print("   - Anomaly detection patterns")
        
        print("\n3. Start Phase 4 (Dashboard & LLM):")
        print("   - Build Streamlit dashboard")
        print("   - Integrate Claude LLM")
        print("   - Create interactive visualizations")
        
        print("\n4. Use Your Models:")
        print("   - Score new flights for risk")
        print("   - Detect fuel inefficiencies")
        print("   - Predict performance categories")
        
        print("\n" + "="*80)
        
        # Generate quick insights
        print_header("QUICK INSIGHTS FROM YOUR MODELS")
        
        try:
            import pandas as pd
            
            # Risk scores
            risk_df = pd.read_csv(Path(__file__).parent.parent / 'data' / 'risk_scores.csv')
            print(f"\n⚠️  Risk Analysis:")
            print(f"   Total flights scored: {len(risk_df):,}")
            risk_dist = risk_df['risk_level'].value_counts()
            for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
                if level in risk_dist.index:
                    count = risk_dist[level]
                    pct = 100 * count / len(risk_df)
                    print(f"   {level:8s} risk: {count:4d} ({pct:5.1f}%)")
            
            # Fuel anomalies
            fuel_df = pd.read_csv(Path(__file__).parent.parent / 'data' / 'fuel_anomalies.csv')
            print(f"\n⛽ Fuel Efficiency Analysis:")
            print(f"   Total flights analyzed: {len(fuel_df):,}")
            anomalies = (fuel_df['fuel_anomaly'] == -1).sum()
            print(f"   Inefficient flights:    {anomalies:,} ({100*anomalies/len(fuel_df):.1f}%)")
            print(f"   Average efficiency:     {fuel_df['fuel_efficiency_score'].mean():.1f}/100")
            
        except Exception as e:
            print(f"   (Could not load results: {e})")
        
        print("\n" + "="*80)
    else:
        print("\n❌ ML Pipeline failed. Please check errors above and retry.")


if __name__ == "__main__":
    main()