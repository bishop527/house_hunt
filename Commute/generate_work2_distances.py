"""
Generate Work Address 2 distance file.

This script runs the commute collection module for Work Address 2 to generate
distance data, then saves it to work2_distances.csv.

Usage:
    python -m scripts.generate_work2_distances
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from constants import WORK_ADDR2, WORK2_COMMUTE_STATS_FILE, WORK1_COMMUTE_STATS_FILE
from utils import get_zip_data, get_locations_within_range
from Commute.collect_commute_data import fetch_commute_times
from logging_config import setup_logger

logger = setup_logger(__name__)


def generate_work2_distances(dry_run=False):
    """
    Generate Work Address 2 distance file using existing commute module.
    
    This function:
    1. Gets all locations within range of Work Address 2
    2. Fetches distances (no traffic data to save API calls)
    3. Saves to work2_distances.csv
    
    Args:
        dry_run (bool): If True, skip actual API calls
    
    Returns:
        bool: True if successful
    """
    logger.info("=" * 70)
    logger.info("GENERATING WORK ADDRESS 2 DISTANCE FILE")
    logger.info("-" * 70)
    logger.info(f"Work Address 2: {WORK_ADDR2}")
    logger.info("=" * 70)
    
    # Import here to avoid circular dependencies
    from constants import WORK1_MAX_RANGE, LOCATION_GROUPING, WORK2_MAX_RANGE
    
    # Temporarily use Work2 range for this operation
    range_to_use = WORK2_MAX_RANGE
    
    # Load zip data
    logger.info("Loading ZIP database...")
    zip_data = get_zip_data()
    
    # Get locations within range of Work Address 2
    logger.info(f"Finding locations within {range_to_use} miles of Work Address 2...")
    addresses = get_locations_within_range(
        WORK_ADDR2,
        zip_data,
        range_to_use,
        group_by=LOCATION_GROUPING,
        force_refresh=False
    )
    
    if not addresses:
        logger.error("No addresses found within range")
        return False
    
    logger.info(f"Found {len(addresses)} locations within {range_to_use} miles")
    
    # Fetch distances using existing commute module
    # Direction doesn't matter for distance-only calculation
    if dry_run:
        logger.info("DRY RUN: Simulating distance fetch from Google Maps API...")
        # Create dummy results for dry run
        results = [{
            'address': addr,
            'distance_miles': 25.0,
            'duration_minutes': 30.0,
            'status': 'OK'
        } for addr in addresses]
        elements_used = len(addresses)
    else:
        logger.info("Fetching distances from Google Maps API...")
        results, elements_used = fetch_commute_times(addresses, 'morning')
    
    if not results:
        logger.error("No results from distance fetch")
        return False
    
    # Save to work2_distances.csv
    import pandas as pd
    from datetime import datetime
    
    # Convert results to DataFrame
    records = []
    for r in results:
        if r['status'] == 'OK':
            # Parse address: "Town, State Zip" format
            address = r['address']
            
            # Split by comma to get Town and "State Zip"
            parts = address.split(',')
            if len(parts) >= 2:
                town = parts[0].strip()
                state_zip = parts[1].strip()
                
                # Split state_zip by space to separate State and Zip
                state_zip_parts = state_zip.split()
                if len(state_zip_parts) >= 2:
                    state = state_zip_parts[0]
                    zip_code = state_zip_parts[1]
                else:
                    state = ''
                    zip_code = state_zip if state_zip_parts else ''
            else:
                town = address
                state = ''
                zip_code = ''
            
            records.append({
                'Town': town,
                'State': state,
                'Zip': zip_code,
                'Distance': r['distance_miles'],
                'Total_Runs': 1,
                'Last_Run_Date': datetime.now().strftime('%Y-%m-%d'),
                'Min_Time': r['duration_minutes'],
                'Max_Time': r['duration_minutes'],
                'Average_Time': r['duration_minutes']
            })
    
    if not records:
        logger.error("No valid records to save")
        return False
    
    df = pd.DataFrame(records)
    df = df.sort_values('Distance').reset_index(drop=True)
    
    try:
        df.to_csv(WORK2_COMMUTE_STATS_FILE, index=False)
        
        logger.info("=" * 70)
        logger.info("WORK ADDRESS 2 DISTANCE FILE GENERATED")
        logger.info("-" * 70)
        logger.info(f"Total locations processed: {len(df)}")
        logger.info(f"Within {range_to_use} mile range: {len(df)}")
        logger.info(f"File saved to: {WORK2_COMMUTE_STATS_FILE}")
        logger.info("=" * 70)
        
        print(f"\n✓ Success! Generated {len(df)} Work Address 2 distance records")
        print(f"  File: {WORK2_COMMUTE_STATS_FILE}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save Work Address 2 distances: {e}")
        return False


def main():
    """Main entry point."""
    try:
        success = generate_work2_distances()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("Generation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {type(e).__name__}: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
