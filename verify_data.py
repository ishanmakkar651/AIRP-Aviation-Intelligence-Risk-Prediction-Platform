"""
Data Verification Script
Check Phase 1 data collection results before starting Phase 2
"""

from pathlib import Path
import importlib.util
from datetime import datetime

def load_db_manager():
    """Load DatabaseManager from 2_database folder"""
    db_path = Path(__file__).parent / '2_database' / 'db_setup.py'
    spec = importlib.util.spec_from_file_location("db_setup", db_path)
    db_setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_setup)
    return db_setup.DatabaseManager()

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def main():
    """Main verification function"""
    
    print_header("AIRP - PHASE 1 DATA COLLECTION VERIFICATION")
    
    # Load database manager
    db = load_db_manager()
    
    try:
        db.connect()
        print("\n✅ Database connection successful")
        
        # 1. BASIC COUNTS
        print_header("1. COLLECTION SUMMARY")
        
        total = db.get_table_row_count('flight_states')
        print(f"\n📊 Total Flight State Records: {total:,}")
        
        result = db.execute_query("SELECT COUNT(DISTINCT icao24) FROM flight_states")
        unique_aircraft = result[0]['count']
        print(f"✈️  Unique Aircraft Tracked: {unique_aircraft:,}")
        
        result = db.execute_query("SELECT COUNT(DISTINCT callsign) FROM flight_states WHERE callsign IS NOT NULL")
        unique_flights = result[0]['count']
        print(f"🎫 Unique Flight Callsigns: {unique_flights:,}")
        
        airports = db.get_table_row_count('airports')
        print(f"🏢 Airports in Database: {airports:,}")
        
        # 2. TIME RANGE
        print_header("2. DATA COVERAGE")
        
        result = db.execute_query("""
            SELECT 
                MIN(timestamp) as first_record,
                MAX(timestamp) as last_record,
                MAX(timestamp) - MIN(timestamp) as duration
            FROM flight_states
        """)
        
        if result and result[0]['first_record']:
            first = result[0]['first_record']
            last = result[0]['last_record']
            duration = result[0]['duration']
            
            print(f"\n📅 First Record: {first}")
            print(f"📅 Last Record:  {last}")
            print(f"⏱️  Duration:     {duration}")
            
            # Calculate hours
            if duration:
                total_seconds = duration.total_seconds()
                hours = total_seconds / 3600
                print(f"⏰ Total Hours:  {hours:.1f} hours")
        
        # 3. DATA COMPLETENESS
        print_header("3. DATA QUALITY")
        
        result = db.execute_query("""
            SELECT 
                COUNT(*) as total,
                COUNT(latitude) as with_position,
                COUNT(longitude) as with_longitude,
                COUNT(velocity) as with_velocity,
                COUNT(baro_altitude) as with_altitude,
                COUNT(callsign) as with_callsign,
                COUNT(heading) as with_heading
            FROM flight_states
        """)
        
        if result:
            total = result[0]['total']
            
            print(f"\n✅ Data Completeness (out of {total:,} records):")
            print(f"   Position (lat/lon): {100.0 * result[0]['with_position'] / total:.1f}%")
            print(f"   Velocity:           {100.0 * result[0]['with_velocity'] / total:.1f}%")
            print(f"   Altitude:           {100.0 * result[0]['with_altitude'] / total:.1f}%")
            print(f"   Callsign:           {100.0 * result[0]['with_callsign'] / total:.1f}%")
            print(f"   Heading:            {100.0 * result[0]['with_heading'] / total:.1f}%")
        
        # 4. COLLECTION TIMELINE
        print_header("4. COLLECTION TIMELINE")
        
        result = db.execute_query("""
            SELECT 
                DATE_TRUNC('hour', timestamp) as hour,
                COUNT(*) as records,
                COUNT(DISTINCT icao24) as aircraft
            FROM flight_states
            GROUP BY hour
            ORDER BY hour DESC
            LIMIT 10
        """)
        
        print("\n📈 Last 10 Hours of Collection:")
        print(f"{'Hour':<25} {'Records':>10} {'Aircraft':>10}")
        print("-" * 47)
        for row in result:
            print(f"{str(row['hour']):<25} {row['records']:>10,} {row['aircraft']:>10,}")
        
        # 5. TOP TRACKED FLIGHTS
        print_header("5. MOST TRACKED FLIGHTS")
        
        result = db.execute_query("""
            SELECT 
                callsign,
                COUNT(*) as position_updates,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen
            FROM flight_states
            WHERE callsign IS NOT NULL
            GROUP BY callsign
            ORDER BY position_updates DESC
            LIMIT 10
        """)
        
        print("\n🏆 Top 10 Most Tracked Flights:")
        print(f"{'Callsign':<12} {'Updates':>10} {'Duration'}")
        print("-" * 50)
        for row in result:
            duration = row['last_seen'] - row['first_seen']
            print(f"{row['callsign']:<12} {row['position_updates']:>10,} {str(duration)}")
        
        # 6. ALTITUDE DISTRIBUTION
        print_header("6. ALTITUDE DISTRIBUTION")
        
        result = db.execute_query("""
            SELECT 
                CASE 
                    WHEN baro_altitude < 1000 THEN 'Ground/Low (< 1km)'
                    WHEN baro_altitude < 5000 THEN 'Climb/Descent (1-5km)'
                    WHEN baro_altitude < 10000 THEN 'Cruise Low (5-10km)'
                    ELSE 'Cruise High (> 10km)'
                END as altitude_band,
                COUNT(*) as count,
                ROUND(AVG(velocity)::numeric, 1) as avg_speed_ms
            FROM flight_states
            WHERE baro_altitude IS NOT NULL
            GROUP BY altitude_band
            ORDER BY MIN(baro_altitude)
        """)
        
        print("\n✈️  Flight Altitude Distribution:")
        print(f"{'Altitude Band':<25} {'Count':>12} {'Avg Speed (m/s)':>18}")
        print("-" * 57)
        for row in result:
            print(f"{row['altitude_band']:<25} {row['count']:>12,} {row['avg_speed_ms']:>18}")
        
        # 7. PHASE 2 READINESS CHECK
        print_header("7. PHASE 2 READINESS CHECK")
        
        checks = []
        
        # Check 1: Minimum records
        if total >= 10000:
            checks.append(("✅", f"Sufficient data: {total:,} records (minimum: 10,000)"))
        else:
            checks.append(("❌", f"Insufficient data: {total:,} records (need: 10,000+)"))
        
        # Check 2: Unique aircraft
        if unique_aircraft >= 1000:
            checks.append(("✅", f"Diverse aircraft: {unique_aircraft:,} unique (minimum: 1,000)"))
        else:
            checks.append(("⚠️ ", f"Limited aircraft: {unique_aircraft:,} unique (ideal: 1,000+)"))
        
        # Check 3: Data completeness
        result = db.execute_query("""
            SELECT 
                100.0 * COUNT(latitude) / COUNT(*) as pos_pct
            FROM flight_states
        """)
        pos_pct = result[0]['pos_pct']
        if pos_pct >= 90:
            checks.append(("✅", f"Good data quality: {pos_pct:.1f}% position completeness"))
        else:
            checks.append(("⚠️ ", f"Data quality issue: {pos_pct:.1f}% position completeness"))
        
        # Check 4: Time coverage
        result = db.execute_query("""
            SELECT EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp))) / 3600 as hours
            FROM flight_states
        """)
        hours = result[0]['hours'] if result and result[0]['hours'] else 0
        if hours >= 12:
            checks.append(("✅", f"Sufficient time range: {hours:.1f} hours (minimum: 12)"))
        else:
            checks.append(("⚠️ ", f"Limited time range: {hours:.1f} hours (ideal: 24+)"))
        
        print()
        for status, message in checks:
            print(f"{status} {message}")
        
        # Final verdict
        all_passed = all(check[0] == "✅" for check in checks)
        
        print_header("VERDICT")
        
        if all_passed:
            print("\n🎉 READY FOR PHASE 2!")
            print("\nYou have collected sufficient high-quality data.")
            print("You can now proceed with feature engineering and ML modeling.")
            print("\nNext step: Type 'START PHASE 2' to begin!")
        else:
            print("\n⚠️  PHASE 2 POSSIBLE BUT NOT IDEAL")
            print("\nYou can proceed with Phase 2, but collecting more data is recommended.")
            print("Consider running the collector for another 12-24 hours for better results.")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()