"""
Collect commute time data for zip codes within range of work location.

This module fetches real-time commute data from Google Maps API and maintains
a running history of commute statistics for each zip code.
"""
import os
import logging
from datetime import datetime
import pandas as pd
import googlemaps
from tqdm import tqdm
from constants import *
from utils import (
    get_google_api_key,
    get_zip_data,
    get_zips_within_range,
    check_api_budget,
    update_api_usage,
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

# Silence googlemaps internal logging
logging.getLogger('googlemaps').setLevel(logging.WARNING)


def determine_direction():
    """
    Determine commute direction based on current time.

    Simple logic: Before noon = morning, After noon = afternoon.
    Assumes script is scheduled to run at appropriate times.

    Returns:
        str: 'morning' or 'afternoon'
    """
    current_hour = datetime.now().hour

    if current_hour < 12:
        logger.info("Before noon - collecting morning commute data")
        return 'morning'
    else:
        logger.info("After noon - collecting afternoon commute data")
        return 'afternoon'


def fetch_commute_times(addresses, direction):
    """
    Fetch commute times from Google Maps API.

    Args:
        addresses (list): List of full addresses (Town, State Zip)
        direction (str): 'morning' or 'afternoon'

    Returns:
        tuple: (list of results dicts, int elements_processed)

    Each result dict contains:
        - address: Full address string
        - distance_miles: Baseline distance (no traffic)
        - duration_minutes: Current commute time with traffic
        - status: API status for this element
    """
    # Validate API key
    api_key = get_google_api_key()
    if not api_key:
        logger.critical("Google API key not found. Cannot proceed.")
        raise SystemExit(1)

    # Initialize Google Maps client
    if PROXY_ON:
        logger.info("Initializing Google Maps client with Proxy.")
        gmaps = googlemaps.Client(
            key=api_key,
            requests_kwargs={'proxies': {'https': PROXY}}
        )
    else:
        gmaps = googlemaps.Client(key=api_key)

    # Set origin and destination based on direction
    if direction == 'morning':
        logger.info(
            f"Morning commute: {len(addresses)} locations → {WORK_ADDR}"
        )
        origins = addresses
        destinations = WORK_ADDR
    else:
        logger.info(
            f"Afternoon commute: {WORK_ADDR} → {len(addresses)} locations"
        )
        origins = WORK_ADDR
        destinations = addresses

    results = []
    elements_processed = 0
    requests_made = 0

    # Process in chunks with progress bar
    chunk_indices = list(range(0, len(addresses), CHUNK_SIZE))

    for i in tqdm(chunk_indices,
                  desc=f"Fetching {direction} commute times",
                  unit="chunk",
                  ncols=80):

        # For afternoon, we need to reverse the logic
        if direction == 'morning':
            chunk_origins = addresses[i: i + CHUNK_SIZE]
            chunk_destinations = destinations
        else:
            chunk_origins = origins
            chunk_destinations = addresses[i: i + CHUNK_SIZE]

        try:
            response = gmaps.distance_matrix(
                origins=chunk_origins,
                destinations=chunk_destinations,
                mode=MODE,
                units=UNITS,
                traffic_model=TRAFFIC_MODEL,
                departure_time="now"
            )

            requests_made += 1

            # Validate response
            if response.get('status') != 'OK':
                logger.error(
                    f"API response error: {response.get('status')}"
                )
                if 'error_message' in response:
                    logger.error(
                        f"Error message: {response['error_message']}"
                    )
                # Still count elements (may be billed)
                if direction == 'morning':
                    elements_processed += len(chunk_origins)
                else:
                    elements_processed += len(chunk_destinations)
                continue

            # Process each result
            # Morning: multiple origins (addresses) → 1 destination (work)
            #   Response has multiple rows, one per origin
            # Afternoon: 1 origin (work) → multiple destinations (addresses)
            #   Response has 1 row with multiple elements

            if direction == 'morning':
                elements_processed += len(chunk_origins)
                logger.debug(
                    f"Processing {len(response['rows'])} rows from API response"
                )
                for idx, row in enumerate(response['rows']):
                    process_element(
                        chunk_origins[idx],
                        row,
                        results
                    )
            else:
                # Afternoon: 1 row, multiple elements
                elements_processed += len(chunk_destinations)
                if len(response['rows']) > 0:
                    row = response['rows'][0]  # Only 1 row for 1 origin
                    logger.debug(
                        f"Processing {len(row['elements'])} elements from "
                        f"API response"
                    )
                    for idx, element_data in enumerate(row['elements']):
                        # Create a row structure for process_element
                        element_row = {'elements': [element_data]}
                        process_element(
                            chunk_destinations[idx],
                            element_row,
                            results
                        )

        except googlemaps.exceptions.ApiError as e:
            logger.error(f"Google API error: {e}")
            if direction == 'morning':
                elements_processed += len(chunk_origins)
            else:
                elements_processed += len(chunk_destinations)
            continue
        except googlemaps.exceptions.TransportError as e:
            logger.error(f"Network/transport error: {e}")
            continue
        except googlemaps.exceptions.Timeout as e:
            logger.error(f"Timeout error: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            continue

    logger.info(
        f"Completed {requests_made} requests, "
        f"processed {elements_processed} elements, "
        f"collected {len(results)} valid results"
    )

    return results, elements_processed


def process_element(address, element, results):
    """
    Process a single API response element.

    Args:
        address (str): Full address for this element
        element (dict): API response element
        results (list): List to append result to
    """
    status = element['elements'][0]['status']

    if status == 'OK':
        # Extract distance (baseline, no traffic)
        distance_miles = round(
            element['elements'][0]['distance']['value'] /
            METERS_PER_MILE,
            2
        )

        # Extract duration with traffic
        duration_seconds = element['elements'][0].get(
            'duration_in_traffic',
            element['elements'][0]['duration']
        )['value']
        duration_minutes = round(duration_seconds / 60, 2)

        results.append({
            'address': address,
            'distance_miles': distance_miles,
            'duration_minutes': duration_minutes,
            'status': 'OK'
        })
    else:
        logger.warning(f"Status '{status}' for address: {address}")
        results.append({
            'address': address,
            'distance_miles': None,
            'duration_minutes': None,
            'status': status
        })


def load_historical_data():
    """
    Load historical commute statistics from CSV.

    Returns:
        pd.DataFrame: Historical data, or empty DataFrame if file
                     doesn't exist
    """
    df = load_csv_with_zip(COMMUTE_STATS_FILE)
    if not df.empty:
        logger.info(
            f"Loaded {len(df)} records from {COMMUTE_STATS_FILE}"
        )
    else:
        logger.info("No historical data file found. Starting fresh.")
    return df


def update_statistics(results):
    """
    Update commute statistics with new results.

    Args:
        results (list): List of result dicts from fetch_commute_times()

    The function updates the historical CSV with:
        - New runs added to Total Runs
        - Updated Last Run Date
        - Updated Min/Max/Average times
    """
    if not results:
        logger.warning("No results to update statistics with.")
        return

    # Convert results to DataFrame
    df_today = pd.DataFrame(results)

    # Filter only successful results
    df_today = df_today[df_today['status'] == 'OK'].copy()

    if len(df_today) == 0:
        logger.warning("No successful API results to process.")
        return

    # Extract Town, State, and Zip from address (e.g., "Lexington, MA 02421")
    df_today[['Town', 'State', 'Zip']] = df_today['address'].str.extract(
        r'^(.+?),\s+([A-Z]{2})\s+(\d{5})$'
    )
    df_today['Zip'] = df_today['Zip'].str.zfill(5)

    # Load historical data
    df_hist = load_historical_data()

    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')

    # Process each result
    updated_records = []

    for _, row in df_today.iterrows():
        town = row['Town']
        state = row['State']
        zip_code = row['Zip']
        distance = row['distance_miles']
        duration = row['duration_minutes']

        # Find existing record
        if not df_hist.empty:
            existing = df_hist[df_hist['Zip'] == zip_code]
        else:
            existing = pd.DataFrame()

        if len(existing) > 0:
            # Update existing record
            rec = existing.iloc[0].to_dict()

            # Ensure State column exists (for old records without it)
            if 'State' not in rec or pd.isna(rec.get('State')):
                rec['State'] = state

            rec['Total_Runs'] += 1
            rec['Last_Run_Date'] = today

            # Handle old column names (migration from old format)
            if 'Min_Time' in rec:
                rec['Min_Time'] = min(rec['Min_Time'], duration)
            elif 'Min_Ever' in rec:
                rec['Min_Time'] = min(rec['Min_Ever'], duration)
            else:
                rec['Min_Time'] = duration

            if 'Max_Time' in rec:
                rec['Max_Time'] = max(rec['Max_Time'], duration)
            elif 'Max_Ever' in rec:
                rec['Max_Time'] = max(rec['Max_Ever'], duration)
            else:
                rec['Max_Time'] = duration

            # Update running average
            if 'Average_Time' in rec:
                old_avg = rec['Average_Time']
            elif 'Running_Avg' in rec:
                old_avg = rec['Running_Avg']
            else:
                old_avg = duration

            old_count = rec['Total_Runs'] - 1
            new_avg = (old_avg * old_count + duration) / rec['Total_Runs']
            rec['Average_Time'] = round(new_avg, 2)

            # Remove old column names if they exist
            rec.pop('Min_Ever', None)
            rec.pop('Max_Ever', None)
            rec.pop('Running_Avg', None)
            rec.pop('Total_Time_Sum', None)
        else:
            # Create new record
            rec = {
                'Town': town,
                'State': state,
                'Zip': zip_code,
                'Distance': distance,
                'Total_Runs': 1,
                'Last_Run_Date': today,
                'Min_Time': duration,
                'Max_Time': duration,
                'Average_Time': duration
            }

        updated_records.append(rec)

    # Merge with historical records not updated today
    df_updated = pd.DataFrame(updated_records)

    if not df_hist.empty:
        # Keep historical records that weren't updated
        updated_zips = set(df_updated['Zip'])
        df_unchanged = df_hist[~df_hist['Zip'].isin(updated_zips)]
        df_final = pd.concat(
            [df_updated, df_unchanged],
            ignore_index=True
        )
    else:
        df_final = df_updated

    # Ensure we have the correct columns in the correct order
    expected_columns = [
        'Town', 'State', 'Zip', 'Distance', 'Total_Runs',
        'Last_Run_Date', 'Min_Time', 'Max_Time', 'Average_Time'
    ]

    # Add any missing columns with default values
    for col in expected_columns:
        if col not in df_final.columns:
            df_final[col] = None

    # Remove any extra columns from old format
    df_final = df_final[expected_columns]

    # Sort by Town and Zip
    df_final = df_final.sort_values(
        ['Town', 'Zip']
    ).reset_index(drop=True)

    # Convert to int for clean display (no .0 suffix)
    df_final['Distance'] = df_final['Distance'].astype(int)
    df_final['Min_Time'] = df_final['Min_Time'].astype(int)
    df_final['Max_Time'] = df_final['Max_Time'].astype(int)
    # Average_Time stays as float for precision

    # Save to CSV
    try:
        df_final.to_csv(COMMUTE_STATS_FILE, index=False)
        logger.info(
            f"Successfully updated {COMMUTE_STATS_FILE} with "
            f"{len(df_updated)} records"
        )
    except PermissionError:
        logger.critical(
            f"!!! PERMISSION ERROR !!!\n"
            f"Cannot write to {COMMUTE_STATS_FILE}.\n"
            f"Please close the file if open in another program."
        )
        raise
    except IOError as e:
        logger.error(f"Failed to save statistics: {e}")
        raise


def collect_commute_data():
    """
    Main function to collect and store commute data.

    This function:
    1. Determines commute direction based on time
    2. Loads zip codes within range
    3. Checks API budget
    4. Fetches commute times from Google Maps
    5. Updates historical statistics
    6. Updates API usage counter
    """
    logger.info("=" * 70)
    logger.info("Starting commute data collection")
    logger.info("=" * 70)

    # Determine direction
    direction = determine_direction()
    logger.info(f"Direction: {direction} commute")

    # Get zip codes within range
    logger.info(f"Loading zip codes within {MAX_RANGE} miles of work...")
    zip_data = get_zip_data()
    addresses = get_zips_within_range(WORK_ADDR, zip_data, MAX_RANGE)

    if not addresses:
        logger.error("No addresses found within range. Aborting.")
        return

    logger.info(f"Found {len(addresses)} addresses within range")

    # Check API budget (budget check also done in get_zips_within_range)
    can_proceed, current_usage = check_api_budget(len(addresses))

    if not can_proceed:
        return

    # Fetch commute times
    results, elements_used = fetch_commute_times(addresses, direction)

    # Update statistics
    if results:
        update_statistics(results)

    # Update API usage
    new_total = update_api_usage(elements_used)

    # Print summary
    print("\n" + "=" * 70)
    print(f"COMMUTE DATA COLLECTION COMPLETE - {direction.upper()}")
    print("-" * 70)
    print(f"Addresses queried:     {len(addresses)}")
    print(f"Successful results:    {len([r for r in results if r['status'] == 'OK'])}")
    print(f"API elements used:     {elements_used}")
    print(f"Monthly usage:         {new_total:,} / {API_MONTHLY_LIMIT:,}")
    print(f"Estimated cost:        ${max(0, (new_total - 40000) * 0.005):.2f}")
    print("=" * 70 + "\n")

    logger.info("Commute data collection completed successfully")


if __name__ == "__main__":
    try:
        collect_commute_data()
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        print("\nCollection interrupted by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {type(e).__name__}: {e}")
        print(f"\nFatal error occurred. Check logs at {APP_LOG_FILE}")
        raise