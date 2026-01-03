"""
Airport Reference Data Loader
Loads airport data from OurAirports public dataset
"""

import requests
import csv
import io
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import DatabaseManager from 2_database folder
import importlib.util
db_setup_path = Path(__file__).parent.parent / '2_database' / 'db_setup.py'
spec = importlib.util.spec_from_file_location("db_setup", db_setup_path)
db_setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_setup)
DatabaseManager = db_setup.DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AirportDataLoader:
    """Loads airport reference data"""
    
    # OurAirports open data
    AIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
    
    def __init__(self):
        """Initialize loader"""
        self.db = DatabaseManager()
        self.db.connect()
    
    def download_airports(self):
        """Download airport data from OurAirports"""
        try:
            logger.info("Downloading airport data from OurAirports...")
            response = requests.get(self.AIRPORTS_URL, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            csv_data = csv.DictReader(io.StringIO(response.text))
            airports = list(csv_data)
            
            logger.info(f"Downloaded {len(airports)} airports")
            return airports
        
        except Exception as e:
            logger.error(f"Error downloading airports: {e}")
            return []
    
    def filter_major_airports(self, airports):
        """Filter for major airports only"""
        major_airports = []
        
        for airport in airports:
            # Include large and medium airports
            if airport.get('type') in ['large_airport', 'medium_airport']:
                major_airports.append(airport)
        
        logger.info(f"Filtered to {len(major_airports)} major airports")
        return major_airports
    
    def load_airports(self, airports):
        """Load airports into database"""
        try:
            batch_data = []
            
            for airport in airports:
                # Only include airports with valid ICAO/IATA codes
                icao = airport.get('ident') or airport.get('gps_code')
                iata = airport.get('iata_code')
                
                if not icao or icao == '':
                    continue
                
                # Prepare data
                data = (
                    icao,
                    iata if iata and iata != '' else None,
                    airport.get('name'),
                    airport.get('municipality'),
                    airport.get('iso_country'),
                    float(airport['latitude_deg']) if airport.get('latitude_deg') else None,
                    float(airport['longitude_deg']) if airport.get('longitude_deg') else None,
                    int(airport['elevation_ft']) if airport.get('elevation_ft') and airport['elevation_ft'] != '' else None,
                    None  # timezone - not in dataset
                )
                
                batch_data.append(data)
            
            # Batch insert
            insert_query = """
            INSERT INTO airports (
                icao_code, iata_code, airport_name, city, country,
                latitude, longitude, elevation_ft, timezone
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (icao_code) DO UPDATE SET
                iata_code = EXCLUDED.iata_code,
                airport_name = EXCLUDED.airport_name,
                city = EXCLUDED.city,
                country = EXCLUDED.country,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                elevation_ft = EXCLUDED.elevation_ft
            """
            
            self.db.execute_batch_insert(insert_query, batch_data)
            
            logger.info(f"Loaded {len(batch_data)} airports into database")
            return len(batch_data)
        
        except Exception as e:
            logger.error(f"Error loading airports: {e}")
            return 0
    
    def load_major_airports(self):
        """Main function to load major airports"""
        airports = self.download_airports()
        
        if not airports:
            logger.error("No airport data downloaded")
            return 0
        
        major_airports = self.filter_major_airports(airports)
        count = self.load_airports(major_airports)
        
        return count
    
    def get_statistics(self):
        """Get airport statistics"""
        stats = {}
        
        try:
            # Total airports
            query = "SELECT COUNT(*) as count FROM airports"
            result = self.db.execute_query(query)
            stats['total'] = result[0]['count'] if result else 0
            
            # By country
            query = """
            SELECT country, COUNT(*) as count 
            FROM airports 
            GROUP BY country 
            ORDER BY count DESC 
            LIMIT 10
            """
            result = self.db.execute_query(query)
            stats['top_countries'] = result
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return stats


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("Airport Reference Data Loader")
    print("="*60 + "\n")
    
    loader = AirportDataLoader()
    
    print("Loading major airports from OurAirports...")
    count = loader.load_major_airports()
    
    if count > 0:
        print(f"\n✅ Successfully loaded {count} airports")
        
        # Show statistics
        stats = loader.get_statistics()
        print(f"\nTotal airports in database: {stats['total']}")
        
        print("\nTop 10 countries by airport count:")
        for row in stats.get('top_countries', []):
            print(f"  {row['country']}: {row['count']}")
    else:
        print("\n❌ Failed to load airports")
    
    loader.db.close()


if __name__ == "__main__":
    main()