"""
Fix Missing Callsigns - Add to Operational Features
Run this ONCE to add callsigns to your data
"""

import pandas as pd
import psycopg2
from pathlib import Path

def add_callsigns_to_features():
    """Add callsigns from database to operational_features.csv"""
    
    print("=" * 70)
    print("FIXING MISSING CALLSIGNS")
    print("=" * 70)
    
    # Database connection
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5434,
        database="airp_db",
        user="airp_user",
        password="airp_secure_2024"
    )
    
    # Load existing operational features
    print("\n1. Loading operational_features.csv...")
    op_df = pd.read_csv('data/operational_features.csv')
    print(f"   ✓ Loaded {len(op_df)} trajectories")
    print(f"   Columns: {len(op_df.columns)}")
    
    # Check if callsign already exists
    if 'callsign' in op_df.columns:
        print(f"   ⚠️  Callsign column already exists!")
        print(f"   Unique values: {op_df['callsign'].nunique()}")
        print(f"   Missing values: {op_df['callsign'].isna().sum()}")
    
    # Get callsigns from database
    print("\n2. Fetching callsigns from database...")
    
    query = """
    SELECT DISTINCT 
        trajectory_id,
        callsign,
        icao24
    FROM flight_states
    WHERE callsign IS NOT NULL
    ORDER BY trajectory_id
    """
    
    callsign_df = pd.read_sql(query, conn)
    print(f"   ✓ Found {len(callsign_df)} trajectories with callsigns")
    
    # Show sample
    print("\n3. Sample callsigns from database:")
    print(callsign_df.head(10))
    
    # Merge callsigns
    print("\n4. Merging callsigns into operational features...")
    
    # Drop existing callsign column if present
    if 'callsign' in op_df.columns:
        op_df = op_df.drop(columns=['callsign'])
    
    # Merge
    op_df = op_df.merge(
        callsign_df[['trajectory_id', 'callsign']],
        on='trajectory_id',
        how='left'
    )
    
    # Clean callsigns
    op_df['callsign'] = op_df['callsign'].fillna('UNKNOWN')
    op_df['callsign'] = op_df['callsign'].replace('', 'UNKNOWN')
    op_df['callsign'] = op_df['callsign'].str.strip()
    
    print(f"   ✓ Merged complete!")
    print(f"   Total trajectories: {len(op_df)}")
    print(f"   With callsigns: {(op_df['callsign'] != 'UNKNOWN').sum()}")
    print(f"   Unknown: {(op_df['callsign'] == 'UNKNOWN').sum()}")
    
    # Save updated file
    print("\n5. Saving updated operational_features.csv...")
    op_df.to_csv('data/operational_features.csv', index=False)
    print("   ✓ Saved!")
    
    # Show sample results
    print("\n6. Sample results:")
    sample = op_df[['trajectory_id', 'callsign', 'fuel_efficiency_score', 'duration_minutes']].head(20)
    print(sample)
    
    # Statistics
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total trajectories: {len(op_df)}")
    print(f"With callsigns: {(op_df['callsign'] != 'UNKNOWN').sum()} ({100*(op_df['callsign'] != 'UNKNOWN').sum()/len(op_df):.1f}%)")
    print(f"Unknown: {(op_df['callsign'] == 'UNKNOWN').sum()} ({100*(op_df['callsign'] == 'UNKNOWN').sum()/len(op_df):.1f}%)")
    print(f"Unique callsigns: {op_df['callsign'].nunique()}")
    
    print("\nTop 10 airlines by flight count:")
    if (op_df['callsign'] != 'UNKNOWN').sum() > 0:
        airlines = op_df[op_df['callsign'] != 'UNKNOWN']['callsign'].str[:3].value_counts().head(10)
        for airline, count in airlines.items():
            print(f"  {airline}: {count} flights")
    
    print("\n✅ COMPLETE! Restart your dashboard to see callsigns.")
    
    conn.close()

if __name__ == "__main__":
    try:
        add_callsigns_to_features()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        