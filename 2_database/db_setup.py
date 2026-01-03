"""
Database Setup and Connection Module
Aviation Intelligence & Risk Prediction Platform (AIRP)
"""

import psycopg2
from psycopg2 import sql, extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import yaml
import os
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize database manager with config"""
        self.config_path = config_path
        self.config = self._load_config()
        self.db_config = self.config['database']
        self.conn = None
        self.cursor = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = Path(__file__).parent.parent / self.config_path
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            # First, try to connect to the target database to see if it exists
            try:
                test_conn = psycopg2.connect(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    database=self.db_config['name']
                )
                test_conn.close()
                logger.info(f"Database '{self.db_config['name']}' already exists")
                return
            except psycopg2.OperationalError:
                # Database doesn't exist, continue to create it
                pass
            
            # Connect to PostgreSQL server (default database)
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Create database
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(self.db_config['name'])
                )
            )
            logger.info(f"Database '{self.db_config['name']}' created successfully")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    def connect(self) -> psycopg2.extensions.connection:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['name'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            self.cursor = self.conn.cursor(cursor_factory=extras.RealDictCursor)
            logger.info("Database connection established")
            return self.conn
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def execute_schema(self, schema_file: str = "2_database/schema.sql"):
        """Execute SQL schema file"""
        try:
            schema_path = Path(__file__).parent.parent / schema_file
            
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            if not self.conn:
                self.connect()
            
            cursor = self.conn.cursor()
            cursor.execute(schema_sql)
            self.conn.commit()
            cursor.close()
            
            logger.info("Database schema executed successfully")
            
        except Exception as e:
            logger.error(f"Error executing schema: {e}")
            if self.conn:
                self.conn.rollback()
            raise
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        try:
            if not self.conn:
                self.connect()
            
            cursor = self.conn.cursor(cursor_factory=extras.RealDictCursor)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def execute_insert(self, query: str, params: Optional[tuple] = None) -> Optional[int]:
        """Execute an INSERT query and return last inserted ID"""
        try:
            if not self.conn:
                self.connect()
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            # Get last inserted ID if available
            try:
                last_id = cursor.fetchone()[0]
            except:
                last_id = None
            
            cursor.close()
            return last_id
            
        except Exception as e:
            logger.error(f"Error executing insert: {e}")
            if self.conn:
                self.conn.rollback()
            raise
    
    def execute_batch_insert(self, query: str, data: List[tuple]):
        """Execute batch insert for better performance"""
        try:
            if not self.conn:
                self.connect()
            
            cursor = self.conn.cursor()
            extras.execute_batch(cursor, query, data)
            self.conn.commit()
            cursor.close()
            
            logger.info(f"Batch insert completed: {len(data)} rows")
            
        except Exception as e:
            logger.error(f"Error executing batch insert: {e}")
            if self.conn:
                self.conn.rollback()
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
        """
        result = self.execute_query(query, (table_name,))
        return result[0]['exists'] if result else False
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        query = f"SELECT COUNT(*) as count FROM {table_name};"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def refresh_materialized_views(self):
        """Refresh all materialized views"""
        try:
            if not self.conn:
                self.connect()
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT refresh_analytics_views();")
            self.conn.commit()
            cursor.close()
            
            logger.info("Materialized views refreshed")
            
        except Exception as e:
            logger.error(f"Error refreshing views: {e}")
            raise


def setup_database():
    """Main setup function to initialize database"""
    logger.info("=" * 50)
    logger.info("Starting Database Setup")
    logger.info("=" * 50)
    
    db = DatabaseManager()
    
    try:
        # Step 1: Create database
        logger.info("Step 1: Creating database...")
        db.create_database()
        
        # Step 2: Connect to database
        logger.info("Step 2: Connecting to database...")
        db.connect()
        
        # Step 3: Execute schema
        logger.info("Step 3: Creating tables and schema...")
        db.execute_schema()
        
        # Step 4: Verify tables
        logger.info("Step 4: Verifying tables...")
        tables = [
            'airlines', 'aircraft', 'airports', 'flight_states',
            'weather_data', 'fuel_efficiency', 'risk_scores', 'predictions'
        ]
        
        for table in tables:
            if db.table_exists(table):
                logger.info(f"  ✓ Table '{table}' created successfully")
            else:
                logger.error(f"  ✗ Table '{table}' not found")
        
        logger.info("=" * 50)
        logger.info("Database Setup Complete!")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False
    
    finally:
        db.close()


def get_db_connection() -> DatabaseManager:
    """Get a database connection (for use in other modules)"""
    db = DatabaseManager()
    db.connect()
    return db


if __name__ == "__main__":
    # Run database setup
    success = setup_database()
    
    if success:
        print("\n✅ Database is ready for data collection!")
        print("\nNext steps:")
        print("1. Update config.yaml with API keys (optional for OpenSky)")
        print("2. Run data collectors: python 1_data_ingestion/opensky_collector.py")
    else:
        print("\n❌ Database setup failed. Please check logs and try again.")