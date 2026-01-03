"""
Quick Start Script for Real-Time Monitoring
Run this to fetch live data and test the system
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from realtime_streamer import RealTimeFlightStreamer

def quick_start():
    """Quick start - fetch one snapshot and test"""
    print("\n" + "="*70)
    print("REAL-TIME MONITORING - QUICK START")
    print("="*70)
    
    streamer = RealTimeFlightStreamer()
    
    print("\n1️⃣  Fetching live flight data...")
    df = streamer.fetch_live_data()
    
    if len(df) == 0:
        print("\n⚠️ No flights detected in the region.")
        print("   This could mean:")
        print("   - No active flights in the defined region")
        print("   - OpenSky API rate limit reached")
        print("   - API temporarily unavailable")
        print("\n💡 Try again in a few minutes or expand the region in realtime_streamer.py")
        return
    
    print("\n2️⃣  Calculating real-time risk scores...")
    df = streamer.calculate_real_time_risk(df)
    
    print("\n3️⃣  Saving snapshot...")
    streamer.save_snapshot(df)
    
    print("\n4️⃣  Generating statistics...")
    stats = streamer.generate_summary_stats(df)
    
    print("\n" + "="*70)
    print("✅ QUICK START COMPLETE!")
    print("="*70)
    
    print(f"\n📊 Summary:")
    print(f"   Active Flights: {len(df)}")
    
    if 'risk_level' in df.columns:
        risk_dist = df['risk_level'].value_counts()
        print(f"\n   Risk Distribution:")
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = risk_dist.get(level, 0)
            print(f"      {level}: {count} flights")
    
    if 'origin_country' in df.columns:
        print(f"\n   Top Countries:")
        for country, count in df['origin_country'].value_counts().head(5).items():
            print(f"      {country}: {count} flights")
    
    print(f"\n📁 Data Location:")
    print(f"   {streamer.data_dir}")
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("\n1. View dashboard:")
    print("   streamlit run 6_dashboard/app.py")
    print("   → Navigate to 'Real-Time Monitoring' page")
    
    print("\n2. Start continuous streaming:")
    print("   python 8_realtime_monitoring/start_continuous.py")
    
    print("\n3. Or run in Python:")
    print("   >>> from realtime_streamer import RealTimeFlightStreamer")
    print("   >>> streamer = RealTimeFlightStreamer()")
    print("   >>> streamer.run_continuous_stream(interval=30)")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    quick_start()