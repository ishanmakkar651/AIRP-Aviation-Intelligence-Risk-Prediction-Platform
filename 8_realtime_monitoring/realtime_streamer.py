"""
Real-Time Flight Data Stream Processor
Fetches and processes live flight data from OpenSky Network API
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import time
from pathlib import Path
import json

class RealTimeFlightStreamer:
    """Streams and processes real-time flight data"""
    
    def __init__(self):
        """Initialize streamer"""
        self.api_url = "https://opensky-network.org/api/states/all"
        self.data_dir = Path('data/realtime')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Define region of interest (optional - can be global)
        # India region as example
        self.bounds = {
            'lat_min': 8.0,   # Southern India
            'lat_max': 37.0,  # Northern India
            'lon_min': 68.0,  # Western India
            'lon_max': 97.0   # Eastern India
        }
        
        # Risk thresholds
        self.risk_thresholds = {
            'altitude_min': 1000,      # meters
            'altitude_max': 15000,     # meters
            'speed_min': 50,           # m/s (~180 km/h)
            'speed_max': 300,          # m/s (~1080 km/h)
            'vertical_rate_max': 15,   # m/s
        }
    
    def fetch_live_data(self):
        """Fetch current flight states from OpenSky API"""
        print(f"\n🔄 Fetching live flight data from OpenSky Network...")
        print(f"   Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        try:
            # Make API request
            response = requests.get(self.api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'states' in data and data['states']:
                    # Convert to DataFrame
                    columns = [
                        'icao24', 'callsign', 'origin_country', 'time_position',
                        'last_contact', 'longitude', 'latitude', 'baro_altitude',
                        'on_ground', 'velocity', 'true_track', 'vertical_rate',
                        'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'
                    ]
                    
                    df = pd.DataFrame(data['states'], columns=columns)
                    
                    # Clean data
                    df = self._clean_flight_data(df)
                    
                    print(f"✅ Fetched {len(df)} active flights")
                    return df
                else:
                    print("⚠️ No flight data available")
                    return pd.DataFrame()
            
            elif response.status_code == 429:
                print("⚠️ Rate limit exceeded. Please wait before next request.")
                return pd.DataFrame()
            else:
                print(f"❌ API Error: Status {response.status_code}")
                return pd.DataFrame()
        
        except requests.exceptions.Timeout:
            print("❌ Request timeout - OpenSky API not responding")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return pd.DataFrame()
    
    def _clean_flight_data(self, df):
        """Clean and preprocess flight data"""
        
        # Remove flights on ground
        df = df[df['on_ground'] == False].copy()
        
        # Clean callsigns
        df['callsign'] = df['callsign'].str.strip()
        df = df[df['callsign'].notna()]
        
        # Remove invalid positions
        df = df[df['latitude'].notna() & df['longitude'].notna()]
        
        # Convert timestamps
        df['last_contact'] = pd.to_datetime(df['last_contact'], unit='s', utc=True)
        
        # Filter by region (optional)
        if self.bounds:
            df = df[
                (df['latitude'] >= self.bounds['lat_min']) &
                (df['latitude'] <= self.bounds['lat_max']) &
                (df['longitude'] >= self.bounds['lon_min']) &
                (df['longitude'] <= self.bounds['lon_max'])
            ]
        
        # Fill missing values
        df['baro_altitude'] = df['baro_altitude'].fillna(0)
        df['velocity'] = df['velocity'].fillna(0)
        df['vertical_rate'] = df['vertical_rate'].fillna(0)
        
        return df
    
    def calculate_real_time_risk(self, df):
        """Calculate real-time risk scores for active flights"""
        print(f"\n📊 Calculating real-time risk scores...")
        
        if len(df) == 0:
            return df
        
        # Initialize risk score
        df['risk_score'] = 0.0
        df['risk_factors'] = ''
        
        for idx, flight in df.iterrows():
            risk_score = 0
            risk_factors = []
            
            # Altitude anomalies
            altitude = flight['baro_altitude']
            if altitude < self.risk_thresholds['altitude_min'] and altitude > 0:
                risk_score += 30
                risk_factors.append('Very Low Altitude')
            elif altitude > self.risk_thresholds['altitude_max']:
                risk_score += 20
                risk_factors.append('Very High Altitude')
            
            # Speed anomalies
            speed = flight['velocity']
            if speed < self.risk_thresholds['speed_min'] and speed > 0:
                risk_score += 25
                risk_factors.append('Very Low Speed')
            elif speed > self.risk_thresholds['speed_max']:
                risk_score += 20
                risk_factors.append('Very High Speed')
            
            # Vertical rate anomalies
            vert_rate = abs(flight['vertical_rate']) if pd.notna(flight['vertical_rate']) else 0
            if vert_rate > self.risk_thresholds['vertical_rate_max']:
                risk_score += 15
                risk_factors.append('Rapid Altitude Change')
            
            # Missing data penalty
            if pd.isna(flight['baro_altitude']) or flight['baro_altitude'] == 0:
                risk_score += 10
                risk_factors.append('Missing Altitude Data')
            
            df.at[idx, 'risk_score'] = min(risk_score, 100)  # Cap at 100
            df.at[idx, 'risk_factors'] = ', '.join(risk_factors) if risk_factors else 'Normal'
        
        # Classify risk level
        df['risk_level'] = df['risk_score'].apply(self._classify_risk)
        
        # Count by risk level
        risk_counts = df['risk_level'].value_counts()
        print(f"   Risk Distribution:")
        for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            count = risk_counts.get(level, 0)
            print(f"      {level}: {count} flights")
        
        return df
    
    def _classify_risk(self, score):
        """Classify risk level based on score"""
        if score >= 70:
            return 'CRITICAL'
        elif score >= 50:
            return 'HIGH'
        elif score >= 30:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def save_snapshot(self, df):
        """Save current snapshot to file"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        
        # Save latest snapshot
        latest_path = self.data_dir / 'latest_snapshot.csv'
        df.to_csv(latest_path, index=False)
        
        # Save timestamped snapshot
        snapshot_path = self.data_dir / f'snapshot_{timestamp}.csv'
        df.to_csv(snapshot_path, index=False)
        
        print(f"\n💾 Snapshot saved: {latest_path}")
        
        # Also save as JSON for web display
        json_path = self.data_dir / 'latest_snapshot.json'
        df_json = df.copy()
        
        # Convert timestamps to strings for JSON
        if 'last_contact' in df_json.columns:
            df_json['last_contact'] = df_json['last_contact'].astype(str)
        
        with open(json_path, 'w') as f:
            json.dump(df_json.to_dict('records'), f, indent=2)
        
        return latest_path
    
    def generate_summary_stats(self, df):
        """Generate summary statistics for dashboard"""
        if len(df) == 0:
            return None
        
        stats = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_flights': len(df),
            'by_risk_level': df['risk_level'].value_counts().to_dict(),
            'avg_altitude': df['baro_altitude'].mean(),
            'avg_speed': df['velocity'].mean(),
            'max_altitude': df['baro_altitude'].max(),
            'max_speed': df['velocity'].max(),
            'unique_countries': df['origin_country'].nunique(),
            'top_countries': df['origin_country'].value_counts().head(5).to_dict(),
        }
        
        # Save stats
        stats_path = self.data_dir / 'summary_stats.json'
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        return stats
    
    def run_continuous_stream(self, interval=30, duration=None):
        """
        Run continuous streaming
        
        Args:
            interval: Seconds between updates (default 30, API limit is ~10 seconds)
            duration: Total duration in minutes (None = infinite)
        """
        print("\n" + "="*70)
        print("REAL-TIME FLIGHT STREAMING STARTED")
        print("="*70)
        print(f"Update interval: {interval} seconds")
        print(f"Region: {self.bounds if self.bounds else 'Global'}")
        print(f"Press Ctrl+C to stop")
        print("="*70)
        
        start_time = time.time()
        update_count = 0
        
        try:
            while True:
                update_count += 1
                
                print(f"\n{'='*70}")
                print(f"UPDATE #{update_count}")
                print(f"{'='*70}")
                
                # Fetch live data
                df = self.fetch_live_data()
                
                if len(df) > 0:
                    # Calculate risk
                    df = self.calculate_real_time_risk(df)
                    
                    # Save snapshot
                    self.save_snapshot(df)
                    
                    # Generate stats
                    stats = self.generate_summary_stats(df)
                    
                    # Display summary
                    if stats:
                        print(f"\n📊 Current Stats:")
                        print(f"   Active Flights: {stats['total_flights']}")
                        print(f"   Avg Altitude: {stats['avg_altitude']:.0f} m")
                        print(f"   Avg Speed: {stats['avg_speed']:.1f} m/s")
                
                # Check duration
                if duration:
                    elapsed_minutes = (time.time() - start_time) / 60
                    if elapsed_minutes >= duration:
                        print(f"\n✅ Completed {duration} minutes of streaming")
                        break
                
                # Wait for next update
                print(f"\n⏳ Next update in {interval} seconds...")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Streaming stopped by user")
        except Exception as e:
            print(f"\n❌ Error in streaming: {e}")
        
        print(f"\n{'='*70}")
        print(f"STREAMING SESSION COMPLETE")
        print(f"Total updates: {update_count}")
        print(f"Duration: {(time.time() - start_time) / 60:.1f} minutes")
        print(f"{'='*70}")


def main():
    """Main execution"""
    streamer = RealTimeFlightStreamer()
    
    # Single fetch for testing
    print("\n🧪 TEST MODE: Fetching single snapshot...")
    df = streamer.fetch_live_data()
    
    if len(df) > 0:
        df = streamer.calculate_real_time_risk(df)
        streamer.save_snapshot(df)
        stats = streamer.generate_summary_stats(df)
        
        print("\n✅ Test successful!")
        print(f"📁 Data saved to: {streamer.data_dir}")
        print("\nTo start continuous streaming:")
        print("   streamer.run_continuous_stream(interval=30)")
    else:
        print("\n⚠️ No data fetched. Check API availability.")


if __name__ == "__main__":
    main()