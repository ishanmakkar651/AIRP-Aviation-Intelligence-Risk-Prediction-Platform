"""
OpenSky Network Data Collector
Collects real-time flight data from OpenSky Network API
"""

import requests
import time
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import DatabaseManager from 2_database folder
import importlib.util
db_setup_path = Path(__file__).parent.parent / '2_database' / 'db_setup.py'
spec = importlib.util.spec_from_file_location("db_setup", db_setup_path)
db_setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_setup)
DatabaseManager = db_setup.DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenSkyCollector:
    """Collects flight data from OpenSky Network"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize collector with configuration"""
        self.config = self._load_config(config_path)
        self.api_config = self.config['apis']['opensky']
        self.base_url = self.api_config['base_url']
        self.rate_limit = self.api_config['rate_limit_seconds']
        
        # Get active region bounding box
        active_region = self.api_config['active_region']
        self.bbox = self.api_config['bbox'][active_region]
        
        self.db = DatabaseManager(config_path)
        self.db.connect()
        
        self.session = requests.Session()
        self.last_request_time = 0
        
        logger.info(f"OpenSky Collector initialized for region: {active_region}")
        logger.info(f"Bounding box: {self.bbox}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML"""
        config_file = Path(__file__).parent.parent / config_path
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get_states(self) -> Optional[List[Dict]]:
        """
        Get all current flight states within configured bounding box
        
        Returns:
            List of flight state dictionaries, or None if error
        """
        try:
            self._respect_rate_limit()
            
            # OpenSky API parameters
            params = {
                'lamin': self.bbox[0],  # min latitude
                'lamax': self.bbox[1],  # max latitude
                'lomin': self.bbox[2],  # min longitude
                'lomax': self.bbox[3],  # max longitude
            }
            
            url = f"{self.base_url}/states/all"
            
            logger.info(f"Fetching flight data from OpenSky Network...")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and 'states' in data and data['states']:
                    states = data['states']
                    timestamp = data.get('time', int(time.time()))
                    
                    logger.info(f"Retrieved {len(states)} flight states")
                    return self._parse_states(states, timestamp)
                else:
                    logger.warning("No flight states returned from API")
                    return []
            
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded. Waiting before retry...")
                time.sleep(60)
                return None
            
            else:
                logger.error(f"API request failed: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"Error fetching states: {e}")
            return None
    
    def _parse_states(self, states: List, timestamp: int) -> List[Dict]:
        """
        Parse OpenSky state vectors into structured format
        
        OpenSky state vector format:
        [0] icao24, [1] callsign, [2] origin_country, [3] time_position,
        [4] last_contact, [5] longitude, [6] latitude, [7] baro_altitude,
        [8] on_ground, [9] velocity, [10] true_track, [11] vertical_rate,
        [12] sensors, [13] geo_altitude, [14] squawk, [15] spi, [16] position_source
        """
        parsed_states = []
        
        for state in states:
            try:
                parsed_state = {
                    'icao24': state[0].strip() if state[0] else None,
                    'callsign': state[1].strip() if state[1] else None,
                    'origin_country': state[2],
                    'time_position': state[3],
                    'last_contact': datetime.fromtimestamp(state[4]) if state[4] else None,
                    'longitude': state[5],
                    'latitude': state[6],
                    'baro_altitude': state[7],
                    'on_ground': state[8],
                    'velocity': state[9],
                    'heading': state[10],
                    'vertical_rate': state[11],
                    'geo_altitude': state[13],
                    'squawk': state[14],
                    'spi': state[15],
                    'position_source': state[16],
                    'timestamp': datetime.fromtimestamp(timestamp),
                }
                
                # Only include states with valid position
                if parsed_state['latitude'] and parsed_state['longitude']:
                    parsed_states.append(parsed_state)
            
            except Exception as e:
                logger.warning(f"Error parsing state vector: {e}")
                continue
        
        return parsed_states
    
    def save_aircraft(self, icao24: str, callsign: Optional[str] = None) -> bool:
        """
        Save or update aircraft information
        
        Args:
            icao24: ICAO24 aircraft identifier
            callsign: Flight callsign (optional)
        
        Returns:
            True if successful
        """
        try:
            # Check if aircraft exists
            query = "SELECT aircraft_id FROM aircraft WHERE icao24 = %s"
            result = self.db.execute_query(query, (icao24,))
            
            if not result:
                # Insert new aircraft
                insert_query = """
                INSERT INTO aircraft (icao24, registration, operator)
                VALUES (%s, %s, %s)
                ON CONFLICT (icao24) DO NOTHING
                RETURNING aircraft_id
                """
                
                # Extract operator from callsign (first 3 chars typically airline code)
                operator = callsign[:3] if callsign and len(callsign) >= 3 else None
                
                self.db.execute_insert(insert_query, (icao24, None, operator))
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving aircraft {icao24}: {e}")
            return False
    
    def save_states(self, states: List[Dict]) -> int:
        """
        Batch save flight states to database
        
        Args:
            states: List of parsed flight state dictionaries
        
        Returns:
            Number of states saved
        """
        if not states:
            return 0
        
        try:
            # Prepare batch insert data
            batch_data = []
            
            for state in states:
                # Ensure aircraft exists
                self.save_aircraft(state['icao24'], state['callsign'])
                
                # Prepare state data for insertion
                state_tuple = (
                    state['icao24'],
                    state['callsign'],
                    state['latitude'],
                    state['longitude'],
                    state['baro_altitude'],
                    state['geo_altitude'],
                    state['velocity'],
                    state['vertical_rate'],
                    state['heading'],
                    state['on_ground'],
                    state['squawk'],
                    state['spi'],
                    state['position_source'],
                    state['last_contact'],
                    state['timestamp']
                )
                
                batch_data.append(state_tuple)
            
            # Batch insert
            insert_query = """
            INSERT INTO flight_states (
                icao24, callsign, latitude, longitude,
                baro_altitude, geo_altitude, velocity, vertical_rate,
                heading, on_ground, squawk, spi, position_source,
                last_contact, timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.db.execute_batch_insert(insert_query, batch_data)
            
            logger.info(f"Saved {len(batch_data)} flight states to database")
            return len(batch_data)
        
        except Exception as e:
            logger.error(f"Error saving states: {e}")
            return 0
    
    def collect_once(self) -> int:
        """
        Perform one collection cycle
        
        Returns:
            Number of states collected
        """
        states = self.get_states()
        
        if states:
            count = self.save_states(states)
            return count
        
        return 0
    
    def collect_continuous(self, interval_minutes: int = 10, duration_hours: Optional[int] = None):
        """
        Continuously collect data at specified intervals
        
        Args:
            interval_minutes: Minutes between collections
            duration_hours: Total hours to collect (None for infinite)
        """
        logger.info("=" * 60)
        logger.info("Starting continuous data collection")
        logger.info(f"Collection interval: {interval_minutes} minutes")
        if duration_hours:
            logger.info(f"Duration: {duration_hours} hours")
        else:
            logger.info("Duration: Infinite (Ctrl+C to stop)")
        logger.info("=" * 60)
        
        start_time = time.time()
        collection_count = 0
        total_states = 0
        
        try:
            while True:
                collection_start = time.time()
                
                # Collect data
                count = self.collect_once()
                
                if count > 0:
                    collection_count += 1
                    total_states += count
                    
                    avg_per_collection = total_states / collection_count
                    elapsed_hours = (time.time() - start_time) / 3600
                    
                    logger.info(f"Collection #{collection_count}: {count} states")
                    logger.info(f"Total: {total_states} states ({avg_per_collection:.0f} avg)")
                    logger.info(f"Runtime: {elapsed_hours:.2f} hours")
                
                # Check if duration exceeded
                if duration_hours:
                    elapsed = (time.time() - start_time) / 3600
                    if elapsed >= duration_hours:
                        logger.info(f"Duration of {duration_hours} hours reached. Stopping.")
                        break
                
                # Wait for next interval
                collection_time = time.time() - collection_start
                sleep_time = max(0, (interval_minutes * 60) - collection_time)
                
                if sleep_time > 0:
                    logger.info(f"Waiting {sleep_time/60:.1f} minutes until next collection...")
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            logger.info("\nCollection stopped by user")
        
        finally:
            logger.info("=" * 60)
            logger.info("Collection Summary:")
            logger.info(f"Total collections: {collection_count}")
            logger.info(f"Total flight states: {total_states}")
            logger.info(f"Runtime: {(time.time() - start_time) / 3600:.2f} hours")
            logger.info("=" * 60)
            self.db.close()
    
    def get_statistics(self) -> Dict:
        """Get collection statistics from database"""
        stats = {}
        
        try:
            # Total states
            query = "SELECT COUNT(*) as count FROM flight_states"
            result = self.db.execute_query(query)
            stats['total_states'] = result[0]['count'] if result else 0
            
            # Unique aircraft
            query = "SELECT COUNT(DISTINCT icao24) as count FROM flight_states"
            result = self.db.execute_query(query)
            stats['unique_aircraft'] = result[0]['count'] if result else 0
            
            # Date range
            query = """
            SELECT MIN(timestamp) as first_record, MAX(timestamp) as last_record 
            FROM flight_states
            """
            result = self.db.execute_query(query)
            if result and result[0]['first_record']:
                stats['first_record'] = result[0]['first_record']
                stats['last_record'] = result[0]['last_record']
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return stats


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("OpenSky Network Data Collector")
    print("Aviation Intelligence & Risk Prediction Platform")
    print("="*60 + "\n")
    
    collector = OpenSkyCollector()
    
    # Show current statistics
    stats = collector.get_statistics()
    print("Current Database Statistics:")
    print(f"  Total flight states: {stats.get('total_states', 0):,}")
    print(f"  Unique aircraft: {stats.get('unique_aircraft', 0):,}")
    if 'first_record' in stats:
        print(f"  First record: {stats['first_record']}")
        print(f"  Last record: {stats['last_record']}")
    print()
    
    # Collection options
    print("Collection Options:")
    print("1. Single collection (test)")
    print("2. Collect for 1 hour (6 collections)")
    print("3. Collect for 24 hours (144 collections)")
    print("4. Continuous collection (manual stop)")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        print("\nPerforming single test collection...")
        count = collector.collect_once()
        print(f"\n✅ Collected {count} flight states")
    
    elif choice == "2":
        collector.collect_continuous(interval_minutes=10, duration_hours=1)
    
    elif choice == "3":
        collector.collect_continuous(interval_minutes=10, duration_hours=24)
    
    elif choice == "4":
        collector.collect_continuous(interval_minutes=10, duration_hours=None)
    
    else:
        print("Invalid option")
        return
    
    # Show final statistics
    stats = collector.get_statistics()
    print("\n" + "="*60)
    print("Final Database Statistics:")
    print(f"  Total flight states: {stats.get('total_states', 0):,}")
    print(f"  Unique aircraft: {stats.get('unique_aircraft', 0):,}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()