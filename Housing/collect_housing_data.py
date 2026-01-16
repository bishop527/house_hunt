"""
Collect housing price data for zip codes within range.

This module fetches housing market data from Redfin's public datasets
and HUD Fair Market Rent data as a fallback/supplement.

Data sources:
- Primary: Redfin public market data (monthly updates, free)
- Fallback: HUD Fair Market Rent (annual updates, free)
"""
import os
import logging
import gzip
import shutil
from datetime import datetime
from urllib.request import urlretrieve
import pandas as pd
from tqdm import tqdm

from constants import *
from utils import (
    get_zip_data,
    get_zips_within_range,
    load_csv_with_zip
)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    filename=APP_LOG_FILE,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def download_redfin_data():
    """
    Download latest Redfin market data if not already present.

    Downloads from Redfin's public S3 bucket and filters for:
    - Year 2025 data only
    - States: MA, RI, NH

    This reduces the 4GB+ file to a manageable size.

    Returns:
        bool: True if download successful or file exists
    """
    # Check if we already have recent data (less than 30 days old)
    if os.path.exists(REDFIN_DATA_FILE):
        file_age_days = (
            datetime.now() -
            datetime.fromtimestamp(os.path.getmtime(REDFIN_DATA_FILE))
        ).days

        if file_age_days < 30:
            logger.info(
                f"Using existing Redfin data "
                f"({file_age_days} days old)"
            )
            return True
        else:
            logger.info(
                f"Redfin data is {file_age_days} days old, "
                f"downloading fresh copy..."
            )

    try:
        logger.info("Downloading Redfin market data (this may take time)...")
        logger.info(f"URL: {REDFIN_DOWNLOAD_URL}")

        # Download compressed file
        gz_file = REDFIN_DATA_FILE + '.gz'
        urlretrieve(REDFIN_DOWNLOAD_URL, gz_file)

        logger.info("Download complete. Decompressing and filtering...")

        # Read compressed file in chunks and filter
        # This prevents loading 4GB into memory
        filtered_chunks = []

        with gzip.open(gz_file, 'rt') as f:
            # Read in chunks to handle large file
            chunk_iter = pd.read_csv(
                f,
                sep='\t',
                chunksize=100000,  # Process 100k rows at a time
                dtype={'REGION': str},
                low_memory=False
            )

            for chunk in tqdm(chunk_iter,
                            desc="Filtering data",
                            unit="chunk"):
                # Filter for 2025 data and target states
                # PERIOD_END format: YYYY-MM-DD
                filtered = chunk[
                    (chunk['PERIOD_END'].str.startswith('2025')) &
                    (chunk['STATE'].isin(['Massachusetts',
                                         'Rhode Island',
                                         'New Hampshire']))
                ].copy()

                if len(filtered) > 0:
                    filtered_chunks.append(filtered)

        # Combine filtered chunks
        if filtered_chunks:
            df_filtered = pd.concat(filtered_chunks, ignore_index=True)

            # Save filtered data
            df_filtered.to_csv(REDFIN_DATA_FILE, index=False, sep='\t')

            logger.info(
                f"Saved {len(df_filtered):,} filtered records to "
                f"{REDFIN_DATA_FILE}"
            )
        else:
            logger.warning("No data found matching filter criteria")
            return False

        # Clean up compressed file
        os.remove(gz_file)

        logger.info("Successfully processed Redfin data")
        return True

    except Exception as e:
        logger.error(f"Failed to download Redfin data: {e}")
        return False


def get_redfin_data(zip_code):
    """
    Get housing data from Redfin CSV for a specific zip code.

    Args:
        zip_code (str): 5-digit zip code (zero-padded)

    Returns:
        dict or None: Housing data if found, None otherwise
        {
            'zip': str,
            'median_sale_price': float,
            'median_list_price': float,
            'median_ppsf': float,  # Price per square foot
            'homes_sold': int,
            'inventory': int,
            'months_of_supply': float,
            'source': 'redfin',
            'period_end': str  # YYYY-MM-DD
        }
    """
    if not os.path.exists(REDFIN_DATA_FILE):
        logger.warning("Redfin data file not found. Downloading...")
        if not download_redfin_data():
            return None

    try:
        # Read Redfin TSV
        # Columns are in ALL CAPS
        # REGION format: "Zip Code: 02421"
        df = pd.read_csv(
            REDFIN_DATA_FILE,
            sep='\t',
            dtype={'REGION': str},
            low_memory=False
        )

        # Filter for this zip code
        # REGION_TYPE should be 'zip' (lowercase in data)
        # REGION format is "Zip Code: 02421"
        target_region = f"Zip Code: {zip_code.zfill(5)}"

        zip_data = df[
            (df['REGION_TYPE'] == 'zip code') &
            (df['REGION'] == target_region)
        ]

        if len(zip_data) == 0:
            logger.debug(f"No Redfin data found for zip {zip_code}")
            return None

        # Get most recent period
        zip_data = zip_data.sort_values('PERIOD_END',
                                         ascending=False).iloc[0]

        # Check minimum sample size
        # Handle NaN for HOMES_SOLD
        homes_sold = zip_data.get('HOMES_SOLD')
        if pd.isna(homes_sold) or homes_sold < MIN_SAMPLE_SIZE:
            logger.warning(
                f"Insufficient data for {zip_code}: "
                f"only {homes_sold} homes sold"
            )
            return None

        # Handle NaN values for INVENTORY
        # Using .get() with default prevents KeyError if column missing
        # Then check for NaN and convert to 0
        inventory_val = zip_data.get('INVENTORY')
        if pd.isna(inventory_val):
            inventory_val = 0

        # Extract values, handling NaN
        return {
            'zip': zip_code,
            'median_sale_price': (
                zip_data.get('MEDIAN_SALE_PRICE')
                if not pd.isna(zip_data.get('MEDIAN_SALE_PRICE'))
                else None
            ),
            'median_list_price': (
                zip_data.get('MEDIAN_LIST_PRICE')
                if not pd.isna(zip_data.get('MEDIAN_LIST_PRICE'))
                else None
            ),
            'median_ppsf': (
                zip_data.get('MEDIAN_PPSF')
                if not pd.isna(zip_data.get('MEDIAN_PPSF'))
                else None
            ),
            'homes_sold': int(homes_sold),
            'inventory': int(inventory_val),
            'months_of_supply': (
                zip_data.get('MONTHS_OF_SUPPLY')
                if not pd.isna(zip_data.get('MONTHS_OF_SUPPLY'))
                else None
            ),
            'source': 'redfin',
            'period_end': zip_data.get('PERIOD_END')
        }

    except Exception as e:
        logger.error(f"Error reading Redfin data for {zip_code}: {e}")
        return None


def get_hud_fmr_data(zip_code, state):
    """
    Get HUD Fair Market Rent data as fallback.

    HUD data is county-based, so we use the county associated with
    the zip code. This is less granular than Redfin but always available.

    Args:
        zip_code (str): 5-digit zip code
        state (str): 2-letter state abbreviation

    Returns:
        dict or None: FMR data if available
        {
            'zip': str,
            'fmr_0br': float,
            'fmr_1br': float,
            'fmr_2br': float,
            'fmr_3br': float,
            'fmr_4br': float,
            'source': 'hud_fmr',
            'year': str
        }
    """
    # For now, return None - HUD API integration can be added later
    # This would require:
    # 1. Zip -> County mapping
    # 2. HUD API call for county FMR
    # 3. Parse JSON response

    logger.debug(
        f"HUD FMR fallback not yet implemented for {zip_code}"
    )
    return None


def fetch_housing_data(addresses):
    """
    Fetch housing data for list of addresses.

    Args:
        addresses (list): List of "Town, State Zip" formatted addresses

    Returns:
        list: List of housing data dictionaries
    """
    results = []

    logger.info(f"Fetching housing data for {len(addresses)} zip codes")

    for address in tqdm(addresses,
                        desc="Collecting housing data",
                        unit="zip",
                        ncols=80):
        try:
            # Parse address: "Lexington, MA 02421"
            parts = address.split(',')
            town = parts[0].strip()
            state_zip = parts[1].strip().split()
            state = state_zip[0]
            zip_code = state_zip[1]

            # Try Redfin first
            data = get_redfin_data(zip_code)

            # Fall back to HUD if Redfin unavailable
            if data is None:
                data = get_hud_fmr_data(zip_code, state)

            if data is not None:
                # Add town and state to result
                data['town'] = town
                data['state'] = state
                results.append(data)
            else:
                logger.warning(
                    f"No housing data available for {address}"
                )

        except Exception as e:
            logger.error(f"Error processing {address}: {e}")
            continue

    logger.info(
        f"Successfully collected data for {len(results)} "
        f"out of {len(addresses)} zip codes"
    )

    return results


def load_historical_data():
    """
    Load historical housing statistics from CSV.

    Returns:
        pd.DataFrame: Historical data, or empty DataFrame if doesn't exist
    """
    df = load_csv_with_zip(HOUSING_STATS_FILE)
    if not df.empty:
        logger.info(
            f"Loaded {len(df)} records from {HOUSING_STATS_FILE}"
        )
    else:
        logger.info("No historical housing data found. Starting fresh.")
    return df


def update_statistics(results):
    """
    Update housing statistics with new results.

    Maintains running statistics similar to commute data:
    - Total number of data points collected
    - Last update date
    - Min/Max/Average prices

    Args:
        results (list): List of housing data dicts from fetch_housing_data()
    """
    if not results:
        logger.warning("No results to update statistics with.")
        return

    # Convert results to DataFrame
    df_today = pd.DataFrame(results)

    # Load historical data
    df_hist = load_historical_data()

    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')

    # Process each result
    updated_records = []

    for _, row in df_today.iterrows():
        town = row['town']
        state = row['state']
        zip_code = row['zip']

        # Find existing record
        if not df_hist.empty:
            existing = df_hist[df_hist['Zip'] == zip_code]
        else:
            existing = pd.DataFrame()

        if len(existing) > 0:
            # Update existing record
            rec = existing.iloc[0].to_dict()

            rec['Total_Runs'] += 1
            rec['Last_Run_Date'] = today

            # Update price statistics
            if 'median_sale_price' in row and pd.notna(
                row['median_sale_price']
            ):
                price = float(row['median_sale_price'])

                rec['Min_Price'] = min(rec.get('Min_Price', price),
                                       price)
                rec['Max_Price'] = max(rec.get('Max_Price', price),
                                       price)

                # Update running average
                old_avg = rec.get('Average_Price', price)
                old_count = rec['Total_Runs'] - 1
                new_avg = (old_avg * old_count + price) / rec['Total_Runs']
                rec['Average_Price'] = round(new_avg, 2)

            # Update latest values
            rec['Latest_Median_Sale'] = row.get('median_sale_price')
            rec['Latest_Median_List'] = row.get('median_list_price')
            rec['Latest_PPSF'] = row.get('median_ppsf')
            rec['Latest_Homes_Sold'] = row.get('homes_sold')
            rec['Latest_Inventory'] = row.get('inventory')

        else:
            # Create new record
            price = row.get('median_sale_price')

            rec = {
                'Town': town,
                'State': state,
                'Zip': zip_code,
                'Total_Runs': 1,
                'Last_Run_Date': today,
                'Min_Price': price,
                'Max_Price': price,
                'Average_Price': price,
                'Latest_Median_Sale': price,
                'Latest_Median_List': row.get('median_list_price'),
                'Latest_PPSF': row.get('median_ppsf'),
                'Latest_Homes_Sold': row.get('homes_sold'),
                'Latest_Inventory': row.get('inventory'),
                'Data_Source': row.get('source', 'redfin')
            }

        updated_records.append(rec)

    # Merge with historical records not updated today
    df_updated = pd.DataFrame(updated_records)

    if not df_hist.empty:
        updated_zips = set(df_updated['Zip'])
        df_unchanged = df_hist[~df_hist['Zip'].isin(updated_zips)]
        df_final = pd.concat([df_updated, df_unchanged],
                             ignore_index=True)
    else:
        df_final = df_updated

    # Sort by average price (most expensive first)
    df_final = df_final.sort_values(
        'Average_Price',
        ascending=False
    ).reset_index(drop=True)

    # Save to CSV
    try:
        df_final.to_csv(HOUSING_STATS_FILE, index=False)
        logger.info(
            f"Successfully updated {HOUSING_STATS_FILE} with "
            f"{len(df_updated)} records"
        )
    except PermissionError:
        logger.critical(
            f"!!! PERMISSION ERROR !!!\n"
            f"Cannot write to {HOUSING_STATS_FILE}.\n"
            f"Please close the file if open in another program."
        )
        raise
    except IOError as e:
        logger.error(f"Failed to save statistics: {e}")
        raise


def collect_housing_data():
    """
    Main function to collect and store housing data.

    This function:
    1. Loads zip codes within range of work
    2. Downloads/updates Redfin data if needed
    3. Fetches housing data for each zip
    4. Updates historical statistics
    """
    logger.info("=" * 70)
    logger.info("Starting housing data collection")
    logger.info("=" * 70)

    # Download/verify Redfin data
    logger.info("Checking Redfin data availability...")
    if not download_redfin_data():
        logger.error("Failed to obtain Redfin data. Aborting.")
        return

    # Get zip codes within range
    logger.info(
        f"Loading zip codes within {MAX_RANGE} miles of work..."
    )
    zip_data = get_zip_data()
    addresses = get_zips_within_range(WORK_ADDR, zip_data, MAX_RANGE)

    if not addresses:
        logger.error("No addresses found within range. Aborting.")
        return

    logger.info(f"Found {len(addresses)} addresses within range")

    # Fetch housing data
    results = fetch_housing_data(addresses)

    # Update statistics
    if results:
        update_statistics(results)

        # Print summary
        print("\n" + "=" * 70)
        print("HOUSING DATA COLLECTION COMPLETE")
        print("-" * 70)
        print(f"Addresses queried:     {len(addresses)}")
        print(f"Successful results:    {len(results)}")
        print(f"Data source:           Redfin (free)")
        print(f"API cost:              $0.00")
        print("=" * 70 + "\n")
    else:
        logger.warning("No housing data collected.")

    logger.info("Housing data collection completed successfully")


if __name__ == "__main__":
    try:
        collect_housing_data()
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        print("\nCollection interrupted by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {type(e).__name__}: {e}")
        print(f"\nFatal error occurred. Check logs at {APP_LOG_FILE}")
        raise