#!/usr/bin/env python3
"""
Validation script for performance optimizations
Checks that all optimized code compiles and has the expected methods
"""

import ast
import sys
from pathlib import Path

def check_file_syntax(filepath):
    """Check if a Python file has valid syntax"""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)

def check_method_exists(filepath, class_name, method_name):
    """Check if a method exists in a class"""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == method_name:
                        return True
        return False
    except (FileNotFoundError, SyntaxError, IOError) as e:
        print(f"  ⚠️  Error checking {filepath}: {e}")
        return False

def main():
    print("🔍 Validating Performance Optimizations...\n")
    
    files_to_check = [
        '2_database/db_setup.py',
        '3_feature_engineering/trajectory_analyzer.py',
        '3_feature_engineering/operational_features.py',
        '8_realtime_monitoring/realtime_streamer.py',
        '1_data_ingestion/opensky_collector.py',
    ]
    
    all_valid = True
    
    # Check syntax
    print("📝 Checking Python Syntax...")
    for filepath in files_to_check:
        valid, error = check_file_syntax(filepath)
        if valid:
            print(f"  ✅ {filepath}")
        else:
            print(f"  ❌ {filepath}: {error}")
            all_valid = False
    
    print("\n🔧 Checking Optimization Methods...")
    
    # Check database connection pooling
    if check_method_exists('2_database/db_setup.py', 'DatabaseManager', 'init_pool'):
        print("  ✅ Connection pooling: init_pool() method exists")
    else:
        print("  ❌ Connection pooling: init_pool() method missing")
        all_valid = False
    
    if check_method_exists('2_database/db_setup.py', 'DatabaseManager', 'get_conn'):
        print("  ✅ Connection pooling: get_conn() method exists")
    else:
        print("  ❌ Connection pooling: get_conn() method missing")
        all_valid = False
    
    # Check vectorized distance calculation
    if check_method_exists('3_feature_engineering/trajectory_analyzer.py', 'TrajectoryAnalyzer', 'calculate_distances_vectorized'):
        print("  ✅ Vectorized distances: calculate_distances_vectorized() method exists")
    else:
        print("  ❌ Vectorized distances: calculate_distances_vectorized() method missing")
        all_valid = False
    
    # Check batch aircraft saving
    if check_method_exists('1_data_ingestion/opensky_collector.py', 'OpenSkyCollector', 'save_aircraft_batch'):
        print("  ✅ Batch operations: save_aircraft_batch() method exists")
    else:
        print("  ❌ Batch operations: save_aircraft_batch() method missing")
        all_valid = False
    
    # Check snapshot rotation
    if check_method_exists('8_realtime_monitoring/realtime_streamer.py', 'RealTimeFlightStreamer', 'rotate_snapshots'):
        print("  ✅ File rotation: rotate_snapshots() method exists")
    else:
        print("  ❌ File rotation: rotate_snapshots() method missing")
        all_valid = False
    
    print("\n📊 Checking Database Schema...")
    schema_path = Path('2_database/schema.sql')
    if schema_path.exists():
        # Read schema file once for efficiency
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        indexes_to_check = [
            'idx_flight_states_icao_time',
            'idx_flight_states_callsign_time',
            'idx_flight_states_time_icao',
            'idx_aircraft_updated'
        ]
        
        for index in indexes_to_check:
            if index in schema:
                print(f"  ✅ Index exists: {index}")
            else:
                print(f"  ❌ Index missing: {index}")
                all_valid = False
    else:
        print("  ❌ Schema file not found")
        all_valid = False
    
    print("\n" + "="*60)
    if all_valid:
        print("✅ All validations passed!")
        return 0
    else:
        print("❌ Some validations failed - please review above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
