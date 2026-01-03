"""
Quick Test Script for Predictive Maintenance
Runs analysis and shows key results
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from predictive_maintenance import PredictiveMaintenanceAnalyzer
import pandas as pd

def test_maintenance_prediction():
    """Test predictive maintenance analysis"""
    
    print("\n" + "="*70)
    print("TESTING PREDICTIVE MAINTENANCE MODULE")
    print("="*70)
    
    # Initialize analyzer
    analyzer = PredictiveMaintenanceAnalyzer()
    
    # Run analysis
    print("\n▶️  Running full analysis...")
    results = analyzer.run_full_analysis()
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    
    # Show top 5 critical aircraft
    critical = results[results['maintenance_priority'] == 'CRITICAL'].head(5)
    
    if len(critical) > 0:
        print("\n🔴 TOP 5 CRITICAL AIRCRAFT:")
        print("-" * 70)
        
        for idx, row in critical.iterrows():
            callsign = row.get('primary_callsign', 'UNKNOWN')
            airline = row.get('airline_name', 'Unknown')
            score = row['maintenance_score']
            window = row['maintenance_window']
            cost = row['estimated_cost_usd']
            
            print(f"\n{callsign} ({airline})")
            print(f"  Score: {score:.1f}/100")
            print(f"  Window: {window}")
            print(f"  Est. Cost: ${cost:,.0f}")
            print(f"  Causes: {row.get('primary_causes', 'N/A')[:60]}...")
    else:
        print("\n✅ No critical maintenance needs detected!")
    
    # Show overall statistics
    print("\n" + "="*70)
    print("OVERALL STATISTICS")
    print("="*70)
    
    total = len(results)
    critical_count = (results['maintenance_priority'] == 'CRITICAL').sum()
    high_count = (results['maintenance_priority'] == 'HIGH').sum()
    total_cost = results['estimated_cost_usd'].sum()
    
    print(f"\nTotal Aircraft: {total}")
    print(f"Critical: {critical_count} ({critical_count/total*100:.1f}%)")
    print(f"High Priority: {high_count} ({high_count/total*100:.1f}%)")
    print(f"Total Estimated Costs: ${total_cost:,.0f}")
    
    print("\n✅ Test completed successfully!")
    print(f"📊 Full results saved to: data/maintenance_predictions.csv")
    print(f"🚀 Launch dashboard to view interactive analysis:")
    print(f"   streamlit run 6_dashboard/app.py")
    
    return results


if __name__ == "__main__":
    test_maintenance_prediction()