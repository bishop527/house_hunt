"""
Collect commute time data - OPTIMIZED VERSION

Key optimizations:
- Check cache before parsing zip database
- Single unified budget check
- GCP validation only at end
- Eliminated redundant file reads

This module fetches real-time commute data from Google Maps API and
maintains running history of commute statistics for each zip code.
"""

from datetime import datetime
import pandas as pd
import googlemaps
from tqdm import tqdm
from constants import *
from utils import (
    get_google_api_key,
    get_zip_data,
    get_locations_within_range,
    load_csv_with_zip,
    update_api_usage_by_tier,
    validate_local_tracking,
    get_current_usage_by_tier,
    determine_optimal_tier
)
from logging_config import setup_logger, silence_verbose_loggers
from error_handlers import handle_api_error, handle_file_error

# Configure logging
logger = setup_logger(__name__, log_file=COMMUTE_LOG_FILE)
silence_verbose_loggers()


# ========================================
# DIRECTION DETERMINATION
# ========================================

def determine_direction():
    """
    Determine commute direction based on current time.

    Simple logic: Before noon = morning, After noon = afternoon.

    Returns:
        str: 'morning' or 'afternoon'
    """
    current_hour = datetime.now().hour

    if current_hour < NOON_HOUR:
        return 'morning'
    else:
        return 'afternoon'


# ========================================
# API DATA FETCHING
# ========================================

def fetch_commute_times(addresses, direction):
    """
    Fetch commute times from Google Maps API.

    Args:
        addresses (list): List of full addresses (Town, State Zip)
        direction (str): 'morning' or 'afternoon'

    Returns:
        tuple: (results: list, elements_processed: int)

    Each result dict contains:
        - address: Full address string
        - distance_miles: Baseline distance
        - duration_minutes: Commute time with traffic
        - status: API status for this element
    """
    # Validate API key
    api_key = get_google_api_key()
    if not api_key:
        logger.critical("Google API key not found")
        raise SystemExit(1)

    # Initialize client
    if PROXY_ON:
        logger.info("Initializing Google Maps client with Proxy")
        gmaps = googlemaps.Client(
            key=api_key,
            requests_kwargs={'proxies': {'https': PROXY}}
        )
    else:
        gmaps = googlemaps.Client(key=api_key)

    # Set origin and destination based on direction
    if direction == 'morning':
        logger.info(f"Morning commute: {len(addresses)} locations -> {WORK_ADDR}")
        origins = addresses
        destinations = WORK_ADDR
    else:
        logger.info(f"Afternoon commute: {WORK_ADDR} -> {len(addresses)} locations")
        origins = WORK_ADDR
        destinations = addresses

    results = []
    elements_processed = 0
    requests_made = 0

    # Process in chunks
    chunk_indices = list(range(0, len(addresses), CHUNK_SIZE))

    for i in tqdm(chunk_indices,
                  desc=f"Fetching {direction} commute times",
                  unit="chunk", ncols=80):

        # Set up chunk based on direction
        if direction == 'morning':
            chunk_origins = addresses[i: i + CHUNK_SIZE]
            chunk_destinations = destinations
        else:
            chunk_origins = origins
            chunk_destinations = addresses[i: i + CHUNK_SIZE]

        try:
            # Build request parameters
            request_params = {
                'origins': chunk_origins,
                'destinations': chunk_destinations,
                'mode': MODE,
                'units': UNITS
            }

            if AVOID:
                request_params['avoid'] = AVOID

            # Add traffic only if enabled
            if USE_TRAFFIC:
                request_params['traffic_model'] = TRAFFIC_MODEL
                request_params['departure_time'] = 'now'
                logger.debug("Using Advanced tier (with traffic)")
            else:
                logger.debug("Using Basic tier (no traffic)")

            response = gmaps.distance_matrix(**request_params)
            requests_made += 1

            # Validate response
            if response.get('status') != 'OK':
                logger.error(f"API error: {response.get('status')}")
                if 'error_message' in response:
                    logger.error(f"Message: {response['error_message']}")
                # Still count elements (may be billed)
                if direction == 'morning':
                    elements_processed += len(chunk_origins)
                else:
                    elements_processed += len(chunk_destinations)
                continue

            # Process results based on direction
            if direction == 'morning':
                elements_processed += len(chunk_origins)
                logger.debug(
                    f"Processing {len(response['rows'])} rows from API"
                )
                for idx, row in enumerate(response['rows']):
                    _process_element(chunk_origins[idx], row, results)
            else:
                # Afternoon: 1 row, multiple elements
                elements_processed += len(chunk_destinations)
                if len(response['rows']) > 0:
                    row = response['rows'][0]
                    logger.debug(
                        f"Processing {len(row['elements'])} elements"
                    )
                    for idx, element_data in enumerate(row['elements']):
                        element_row = {'elements': [element_data]}
                        _process_element(
                            chunk_destinations[idx],
                            element_row,
                            results
                        )

        except googlemaps.exceptions.ApiError as e:
            handle_api_error(e, "fetch_commute_times", reraise=False)
            if direction == 'morning':
                elements_processed += len(chunk_origins)
            else:
                elements_processed += len(chunk_destinations)
        except googlemaps.exceptions.TransportError as e:
            handle_api_error(e, "fetch_commute_times_transport", reraise=False)
        except googlemaps.exceptions.Timeout as e:
            handle_api_error(e, "fetch_commute_times_timeout", reraise=False)
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")

    logger.info(
        f"Completed {requests_made} requests, "
        f"processed {elements_processed} elements, "
        f"collected {len(results)} valid results"
    )

    return results, elements_processed


def _process_element(address, element, results):
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
        duration_data = element['elements'][0].get(
            'duration_in_traffic',
            element['elements'][0]['duration']
        )
        duration_minutes = round(
            duration_data['value'] / SECONDS_PER_MINUTE,
            2
        )

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


# ========================================
# HISTORICAL DATA MANAGEMENT
# ========================================

def load_historical_data():
    """
    Load historical commute statistics from CSV.

    Returns:
        pd.DataFrame: Historical data, or empty DataFrame if missing
    """
    historical_df = load_csv_with_zip(COMMUTE_STATS_FILE)
    if not historical_df.empty:
        logger.info(
            f"Loaded {len(historical_df)} records from "
            f"{COMMUTE_STATS_FILE}"
        )
    else:
        logger.info("No historical data found. Starting fresh.")
    return historical_df


def update_statistics(results):
    """
    Update commute statistics with new results.

    Args:
        results (list): List of result dicts from fetch_commute_times()
    """
    if not results:
        logger.warning("No results to update statistics with.")
        return

    # Convert to DataFrame
    current_df = pd.DataFrame(results)

    # Filter only successful results
    current_df = current_df[current_df['status'] == 'OK'].copy()

    if len(current_df) == 0:
        logger.warning("No successful API results to process.")
        return

    # Extract location components from address
    current_df[['Town', 'State', 'Zip']] = current_df['address'].str.extract(
        r'^(.+?),\s+([A-Z]{2})\s+(\d{5})$'
    )
    current_df['Zip'] = current_df['Zip'].str.zfill(5)

    # Load historical data
    historical_df = load_historical_data()

    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')

    # Process each result
    updated_records = []

    for _, row in current_df.iterrows():
        location_record = _update_location_record(
            row, historical_df, today
        )
        updated_records.append(location_record)

    # Merge with unchanged historical records
    updated_df = pd.DataFrame(updated_records)

    if not historical_df.empty:
        updated_zips = set(updated_df['Zip'])
        unchanged_df = historical_df[
            ~historical_df['Zip'].isin(updated_zips)
        ]
        final_df = pd.concat(
            [updated_df, unchanged_df],
            ignore_index=True
        )
    else:
        final_df = updated_df

    # Ensure correct columns and order
    expected_columns = [
        'Town', 'State', 'Zip', 'Distance', 'Total_Runs',
        'Last_Run_Date', 'Min_Time', 'Max_Time', 'Average_Time'
    ]

    for col in expected_columns:
        if col not in final_df.columns:
            final_df[col] = None

    final_df = final_df[expected_columns]

    # Sort by Town and Zip
    final_df = final_df.sort_values(
        ['Town', 'Zip']
    ).reset_index(drop=True)

    # Convert to int for clean display
    final_df['Distance'] = final_df['Distance'].astype(int)
    final_df['Min_Time'] = final_df['Min_Time'].astype(int)
    final_df['Max_Time'] = final_df['Max_Time'].astype(int)

    # Save to CSV
    try:
        final_df.to_csv(COMMUTE_STATS_FILE, index=False)
        logger.info(
            f"Successfully updated {COMMUTE_STATS_FILE} with "
            f"{len(updated_df)} records"
        )
    except PermissionError:
        handle_file_error(
            PermissionError(),
            COMMUTE_STATS_FILE,
            "write",
            reraise=True
        )
    except IOError as e:
        handle_file_error(e, COMMUTE_STATS_FILE, "write", reraise=True)


def _update_location_record(row, historical_df, today):
    """
    Update or create a single location record.

    Args:
        row (pd.Series): Current data row
        historical_df (pd.DataFrame): Historical data
        today (str): Today's date string

    Returns:
        dict: Updated location record
    """
    town = row['Town']
    state = row['State']
    zip_code = row['Zip']
    distance = row['distance_miles']
    duration = row['duration_minutes']

    # Find existing record
    if not historical_df.empty:
        existing_df = historical_df[historical_df['Zip'] == zip_code]
    else:
        existing_df = pd.DataFrame()

    if len(existing_df) > 0:
        # Update existing record
        location_record = existing_df.iloc[0].to_dict()

        # Ensure State column exists (for old records)
        if 'State' not in location_record or pd.isna(
            location_record.get('State')
        ):
            location_record['State'] = state

        location_record['Total_Runs'] += 1
        location_record['Last_Run_Date'] = today

        # Update min/max/average (handle old column names)
        location_record['Min_Time'] = min(
            location_record.get('Min_Time', duration),
            duration
        )
        location_record['Max_Time'] = max(
            location_record.get('Max_Time', duration),
            duration
        )

        old_avg = location_record.get('Average_Time', duration)
        old_count = location_record['Total_Runs'] - 1
        new_avg = (old_avg * old_count + duration) / location_record['Total_Runs']
        location_record['Average_Time'] = round(new_avg, 2)

    else:
        # Create new record
        location_record = {
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

    return location_record


# ========================================
# OPTIMIZED BUDGET CHECKING
# ========================================

def _check_budget_once(estimated_elements):
    """
    Unified budget check - replaces multiple redundant checks.

    OPTIMIZATION: Single function that reads tier usage once and
    performs all budget validation in one place.

    Args:
        estimated_elements (int): Number of elements this request will use

    Returns:
        dict: {
            'can_proceed': bool,
            'current_usage': int,
            'estimated': int,
            'projected': int,
            'tier_usage': dict
        }
    """
    # Read local tracking ONCE
    tier_usage = get_current_usage_by_tier()

    if USE_TRAFFIC:
        current_usage = tier_usage['advanced']
        limit = API_MONTHLY_LIMIT_ADVANCED
        tier_name = 'Advanced'
    else:
        current_usage = tier_usage['basic']
        limit = API_MONTHLY_LIMIT_BASIC
        tier_name = 'Basic'

    # Check if already at limit
    if current_usage >= limit:
        logger.critical(
            f"MONTHLY BUDGET LIMIT REACHED: {current_usage:,} / {limit:,}"
        )
        return {
            'can_proceed': False,
            'current_usage': current_usage,
            'estimated': estimated_elements,
            'projected': current_usage + estimated_elements,
            'tier_usage': tier_usage
        }

    # Project usage
    projected = current_usage + estimated_elements

    # Warn if would exceed
    if projected > limit:
        logger.warning(
            f"Budget warning: projected={projected:,} exceeds limit={limit:,} "
            f"(current={current_usage:,} + estimated={estimated_elements:,})"
        )
        response = input("Continue anyway? (yes/no): ").lower()
        if response != 'yes':
            logger.info("User aborted to prevent exceeding budget")
            return {
                'can_proceed': False,
                'current_usage': current_usage,
                'estimated': estimated_elements,
                'projected': projected,
                'tier_usage': tier_usage
            }

    logger.info(
        f"Budget check passed: {projected:,}/{limit:,} "
        f"(current={current_usage:,} + estimated={estimated_elements:,})"
    )

    return {
        'can_proceed': True,
        'current_usage': current_usage,
        'estimated': estimated_elements,
        'projected': projected,
        'tier_usage': tier_usage
    }


def _load_addresses_within_range():
    """
    Load addresses within MAX_RANGE with OPTIMIZED cache-first logic.

    OPTIMIZATION: Check cache existence BEFORE loading zip database.
    Avoid parsing 44MB file when cache already exists.

    Returns:
        list: Addresses within range, or None if none found
    """
    # Build cache filename
    cache_file = os.path.join(
        PROCESSED_DIR,
        f"{LOCATION_GROUPING}s_within_{MAX_RANGE}mi.csv"
    )

    # OPTIMIZATION: Check cache FIRST
    if os.path.exists(cache_file):
        try:
            logger.info(f"Loading addresses from cache: {cache_file}")
            cached_df = pd.read_csv(cache_file)
            addresses = cached_df['Full_Address'].tolist()
            logger.info(
                f"Found {len(addresses)} cached addresses "
                f"(skipped zip database parsing)"
            )
            return addresses
        except Exception as e:
            logger.warning(f"Cache read failed: {e}. Building fresh...")

    # Cache miss - do full pipeline
    logger.info(
        f"Cache not found, loading ZIP database and building address list..."
    )
    zip_codes_df = get_zip_data()
    addresses = get_locations_within_range(
        WORK_ADDR, zip_codes_df, MAX_RANGE,
        group_by=LOCATION_GROUPING
    )

    if not addresses:
        logger.error("No addresses found within range")
        return None

    logger.info(f"Found {len(addresses)} addresses within range")
    return addresses


# ========================================
# MAIN COLLECTION FUNCTION (OPTIMIZED)
# ========================================

def collect_commute_data(limit=None, dry_run=False):
    """
    Main function to collect and store commute data - OPTIMIZED VERSION.

    OPTIMIZATIONS APPLIED:
    1. Check cache before parsing zip database (saves 2-3s per run)
    2. Single unified budget check (eliminates redundant file reads)
    3. GCP validation only at end (saves ~500ms-1s, reduces API quota)
    4. Eliminated duplicate budget logic

    This orchestrator function:
    1. Determines commute direction
    2. Loads addresses (cache-first)
    3. Checks API budget (unified, single call)
    4. Fetches commute times
    5. Updates historical statistics
    6. Updates API usage counter
    7. Validates against Google (once, at end)
    8. Logs final summary
    """
    # Determine which tier to use
    global USE_TRAFFIC
    direction = determine_direction()
    logger.info(f"STARTED: Commute collection ({direction})")

    if AUTO_TIER_SELECTION:
        USE_TRAFFIC, tier_reason = determine_optimal_tier()
        logger.info(f"Auto tier selection: {tier_reason}")

        # Check if both tiers exhausted
        if "exhausted" in tier_reason.lower():
            logger.critical("Cannot proceed - monthly API budget exhausted")
            logger.info("Wait until next month or manually adjust limits")
            return False
    else:
        tier_name = "Advanced (with traffic)" if USE_TRAFFIC else "Basic (no traffic)"
        logger.info(f"Manual tier selection: {tier_name}")

        # Still check if selected tier has budget
        tier_usage = get_current_usage_by_tier()
        if USE_TRAFFIC:
            current = tier_usage['advanced']
            limit = API_MONTHLY_LIMIT_ADVANCED
        else:
            current = tier_usage['basic']
            limit = API_MONTHLY_LIMIT_BASIC

        if current >= limit:
            logger.critical(
                f"Selected tier exhausted: {current:,}/{limit:,} used"
            )

    # OPTIMIZATION: Load addresses (cache-first, skip zip DB if possible)
    addresses = _load_addresses_within_range()
    if not addresses:
        return False

    # Apply limit if requested
    if limit:
        logger.info(f"Limiting processing to first {limit} addresses")
        addresses = addresses[:limit]

    # OPTIMIZATION: Single unified budget check (no GCP call yet)
    budget_info = _check_budget_once(len(addresses))
    if not budget_info['can_proceed']:
        return False

    # Fetch commute times
    if dry_run:
        logger.info(f"DRY RUN: Would have requested commute data for {len(addresses)} locations")
        results = [
            {
                'address': addr,
                'distance_miles': 10.0,
                'duration_minutes': 15.0,
                'status': 'OK'
            } for addr in addresses
        ]
        elements_used = len(addresses)
    else:
        results, elements_used = fetch_commute_times(addresses, direction)

    # Update statistics
    if results:
        update_statistics(results)

    # Update tier-specific tracking
    if not dry_run:
        basic_count, advanced_count, tier = update_api_usage_by_tier(elements_used)
        # OPTIMIZATION: Validate usage ONCE at end (single GCP call)
        final_validation = validate_local_tracking()
    else:
        logger.info("DRY RUN: Skipping API usage tracking and GCP validation")
        final_validation = {
            'success': True,
            'tier_usage': get_current_usage_by_tier(),
            'costs': {'total_cost': 0.0},
            'discrepancy': 0,
            'discrepancy_ratio': 0.0
        }
        tier = "dry-run"

    validation_success = final_validation.get('success', False)
    
    tier_usage = final_validation['tier_usage']
    costs = final_validation['costs']

    ok_count = len([r for r in results if r['status'] == 'OK'])
    logger.info(
        f"COMPLETED: {direction} | "
        f"queried={len(addresses)} ok={ok_count} | "
        f"elements={elements_used} ({tier}) | "
        f"Basic={tier_usage['basic']:,}/{API_MONTHLY_LIMIT_BASIC:,} "
        f"Advanced={tier_usage['advanced']:,}/{API_MONTHLY_LIMIT_ADVANCED:,} | "
        f"cost=${costs['total_cost']:.2f}"
    )

    if not validation_success:
        logger.error("Validation failed during commute collection")
        return False

    if final_validation['discrepancy'] > MAX_ACCEPTABLE_DISCREPANCY:
        logger.warning(
            f"DISCREPANCY: {final_validation['discrepancy']:,} elements "
            f"({final_validation['discrepancy_ratio']:.1%})"
        )
    
    if dry_run:
        logger.info("DRY RUN COMPLETED SUCCESSFULLY")
        
    return True


if __name__ == "__main__":
    try:
        collect_commute_data()
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
    except Exception as e:
        logger.critical(f"Fatal error: {type(e).__name__}: {e}")
        raise