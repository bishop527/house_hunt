"""
Utility functions for House Hunt project - REFACTORED VERSION

Key improvements:
- Extracted duplicate code from get_zips_within_range/get_towns_within_range
- Standardized variable naming (_df suffix for DataFrames)
- Improved error handling with centralized handlers
- Added constants for magic numbers
- Consistent f-string formatting
- Better function decomposition

Created on Nov 4, 2015
Updated 30 Jan 2026
"""

import sys
import googlemaps
import pandas as pd
import time
from tqdm import tqdm
from datetime import datetime, timedelta, timezone
from constants import *
from logging_config import setup_logger
from error_handlers import handle_api_error, handle_file_error

logger = setup_logger(__name__)


# ========================================
# API KEY MANAGEMENT
# ========================================

def get_google_api_key(key_loc=KEY_LOC, key_file=KEY_FILE):
    """Fetch the Google API key from file."""
    try:
        path = os.path.join(key_loc, key_file)
        with open(path, 'r') as file:
            key = file.readline().strip()
            logger.debug(f"API Key loaded from {path}")
            return key
    except FileNotFoundError:
        logger.error(f"API key file not found: {path}")
        return None
    except Exception as e:
        logger.error(f"Failed to read API key: {e}")
        return None


# ========================================
# TIME CALCULATIONS
# ========================================

def get_hours_until_first_time_check():
    """Calculate hours until first morning slot on Monday."""
    now = datetime.now()
    days_ahead = (0 - now.weekday() + DAYS_PER_WEEK) % DAYS_PER_WEEK
    target = now + timedelta(days=days_ahead)
    first_hour, first_min = map(int, MORNING_TIMES[0].split(':'))
    target = target.replace(
        hour=first_hour, minute=first_min,
        second=0, microsecond=0
    )
    if target <= now:
        target += timedelta(days=DAYS_PER_WEEK)
    return (target - now).total_seconds() / (
            SECONDS_PER_MINUTE * MINUTES_PER_HOUR
    )


# ========================================
# ZIP CODE DATA LOADING
# ========================================

def get_zip_data(states=None, include_county=False):
    """Load and filter ZIP code database."""
    if states is None:
        states = TARGET_STATES

    if not os.path.exists(ZIP_DATA_FILE):
        logger.critical(f"Source file not found: {ZIP_DATA_FILE}")
        sys.exit(1)

    logger.info(f"Parsing ZIP database: {ZIP_DATA_FILE}")

    cols_to_read = [
        'zip', 'type', 'decommissioned', 'primary_city',
        'state', 'latitude', 'longitude'
    ]
    dtype_dict = {
        'zip': str, 'type': str, 'decommissioned': int,
        'primary_city': str, 'state': str
    }

    if include_county:
        cols_to_read.append('county')
        dtype_dict['county'] = str

    try:
        zip_df = pd.read_csv(
            ZIP_DATA_FILE, header=0, usecols=cols_to_read,
            dtype=dtype_dict,
            converters={
                'latitude': lambda x: pd.to_numeric(x, errors='coerce'),
                'longitude': lambda x: pd.to_numeric(x, errors='coerce')
            }
        )
    except FileNotFoundError:
        logger.critical(f"ZIP database not found: {ZIP_DATA_FILE}")
        sys.exit(1)
    except pd.errors.ParserError as e:
        logger.critical(f"CSV parsing error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.critical(f"Column mismatch: {e}")
        sys.exit(1)

    rename_dict = {
        'zip': 'Zip', 'primary_city': 'Town',
        'state': 'State', 'latitude': 'Lat', 'longitude': 'Long'
    }
    if include_county:
        rename_dict['county'] = 'County'

    zip_df = zip_df.rename(columns=rename_dict)

    filtered_df = zip_df[
        (zip_df['State'].isin(states)) &
        (zip_df['type'] == "STANDARD") &
        (zip_df['decommissioned'] == 0)
        ].copy()

    filtered_df = filtered_df.drop(columns=['type', 'decommissioned'])

    missing_df = filtered_df[
        filtered_df['Zip'].isna() | filtered_df['Town'].isna() |
        filtered_df['State'].isna() | filtered_df['Lat'].isna() |
        filtered_df['Long'].isna()
        ]

    if len(missing_df) > 0:
        logger.warning(f"Found {len(missing_df)} rows with missing data")
        for idx, row in missing_df.iterrows():
            logger.warning(
                f"  Row {idx}: Zip={row.get('Zip', 'MISSING')}, "
                f"Town={row.get('Town', 'MISSING')}"
            )

    before_dropna = len(filtered_df)
    filtered_df = filtered_df.dropna(
        subset=['Zip', 'Town', 'State', 'Lat', 'Long']
    )
    dropped = before_dropna - len(filtered_df)

    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with missing data")

    filtered_df['Zip'] = filtered_df['Zip'].str.zfill(5)

    if len(filtered_df) == 0:
        logger.error(f"No zip codes found for states: {states}")
        sys.exit(1)

    logger.info(
        f"Loaded {len(filtered_df)} active standard ZIPs for "
        f"{', '.join(states)}"
    )

    return filtered_df.reset_index(drop=True)


def load_csv_with_zip(filepath):
    """Load CSV with proper Zip code handling."""
    if os.path.exists(filepath):
        try:
            data_df = pd.read_csv(filepath, dtype={'Zip': str})
            if 'Zip' in data_df.columns:
                data_df['Zip'] = data_df['Zip'].str.zfill(5)
            logger.info(f"Loaded {len(data_df)} records from {filepath}")
            return data_df
        except Exception as e:
            handle_file_error(e, filepath, "read", reraise=False)
            return pd.DataFrame()
    else:
        logger.info(f"File not found: {filepath}")
        return pd.DataFrame()


# ========================================
# API BUDGET MANAGEMENT
# ========================================

def check_api_budget(estimated_elements, limit=None):
    """
    Check if API budget allows for requested elements.

    Args:
        estimated_elements (int): Number of elements this request will use
        limit (int): Monthly limit (if None, uses tier-appropriate limit)

    Returns:
        tuple: (can_proceed: bool, current_usage: int)
    """
    # Get current usage from tier tracking
    tier_usage = get_current_usage_by_tier()

    if USE_TRAFFIC:
        current_usage = tier_usage['advanced']
        tier_name = 'Advanced'
        if limit is None:
            limit = API_MONTHLY_LIMIT_ADVANCED
    else:
        current_usage = tier_usage['basic']
        tier_name = 'Basic'
        if limit is None:
            limit = API_MONTHLY_LIMIT_BASIC

    if current_usage >= limit:
        logger.critical(
            f"MONTHLY BUDGET LIMIT REACHED for {tier_name} tier: "
            f"{current_usage:,} / {limit:,}"
        )
        sys.exit(1)

    projected = current_usage + estimated_elements
    if projected > limit:
        logger.warning(
            f"Budget warning ({tier_name} tier): "
            f"projected={projected:,} exceeds limit={limit:,} "
            f"(current={current_usage:,} + estimated={estimated_elements:,})"
        )

    return True, current_usage


def update_api_usage_by_tier(elements_used, use_traffic=None):
    """
    Track API usage separately by tier (Basic vs Advanced).

    Args:
        elements_used (int): Number of elements used this run
        use_traffic (bool): If None, uses USE_TRAFFIC constant

    Returns:
        tuple: (basic_count, advanced_count, tier_used)
    """
    # Determine tier - if not specified, use constant
    if use_traffic is None:
        use_traffic = USE_TRAFFIC

    tier = 'advanced' if use_traffic else 'basic'

    month_str = datetime.now().strftime('%Y-%m')

    # Load existing counts - INITIALIZE TO ZERO FIRST
    basic_count = 0
    advanced_count = 0

    if os.path.exists(API_TIER_TRACKING_FILE):
        try:
            with open(API_TIER_TRACKING_FILE, "r") as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) == 3 and parts[0] == month_str:
                        # Read the tier-specific count
                        if parts[1] == 'basic':
                            basic_count = int(parts[2])
                        elif parts[1] == 'advanced':
                            advanced_count = int(parts[2])
        except (ValueError, IndexError) as e:
            logger.warning(f"Error reading tier tracking file: {e}")
            # Reset to zero on error
            basic_count = 0
            advanced_count = 0

    # Update ONLY the appropriate tier
    if tier == 'basic':
        basic_count += elements_used
    else:  # tier == 'advanced'
        advanced_count += elements_used

    # Save updated counts (both tiers)
    try:
        with open(API_TIER_TRACKING_FILE, "w") as f:
            f.write(f"{month_str},basic,{basic_count}\n")
            f.write(f"{month_str},advanced,{advanced_count}\n")

        logger.info(
            f"Tier tracking updated: +{elements_used} ({tier}) | "
            f"Monthly: Basic={basic_count:,} Advanced={advanced_count:,}"
        )

    except IOError as e:
        logger.error(f"Failed to update tier tracking: {e}")
        raise

    return basic_count, advanced_count, tier


def get_current_usage_by_tier():
    """
    Get current month's usage breakdown by tier from local tracking.

    Returns:
        dict: {
            'basic': int,
            'advanced': int,
            'basic_remaining': int,
            'advanced_remaining': int,
            'total': int
        }
    """
    month_str = datetime.now().strftime('%Y-%m')
    basic_count = 0
    advanced_count = 0
    lines_read = 0
    malformed_lines = 0

    if os.path.exists(API_TIER_TRACKING_FILE):
        logger.debug(
            f"Reading tier usage from {API_TIER_TRACKING_FILE}"
        )
        try:
            with open(API_TIER_TRACKING_FILE, "r") as f:
                for line_num, line in enumerate(f, 1):
                    lines_read += 1
                    parts = line.strip().split(',')

                    # Validate format
                    if len(parts) != 3:
                        malformed_lines += 1
                        logger.warning(
                            f"Malformed line {line_num} in tier tracking: "
                            f"'{line.strip()}' (expected 3 fields, got "
                            f"{len(parts)})"
                        )
                        continue

                    # Only process current month
                    if parts[0] == month_str:
                        try:
                            if parts[1] == 'basic':
                                basic_count = int(parts[2])
                                logger.debug(
                                    f"Read basic tier: {basic_count}"
                                )
                            elif parts[1] == 'advanced':
                                advanced_count = int(parts[2])
                                logger.debug(
                                    f"Read advanced tier: {advanced_count}"
                                )
                            else:
                                logger.warning(
                                    f"Unknown tier '{parts[1]}' on line "
                                    f"{line_num}"
                                )
                        except ValueError as e:
                            logger.error(
                                f"Invalid count value on line {line_num}: "
                                f"'{parts[2]}' - {e}"
                            )

        except Exception as e:
            logger.error(f"Error reading tier usage file: {e}")
    else:
        logger.debug(
            f"Tier tracking file not found: {API_TIER_TRACKING_FILE}"
        )

    # Validation logging
    if lines_read > 0:
        logger.debug(
            f"Tier file read complete: {lines_read} lines, "
            f"{malformed_lines} malformed"
        )

    if basic_count == 0 and advanced_count == 0 and lines_read > 0:
        logger.warning(
            "Both tier counts are zero despite reading file - "
            "file may be corrupted or for wrong month"
        )

    logger.debug(
        f"Current usage: Basic={basic_count:,} Advanced={advanced_count:,} "
        f"Total={basic_count + advanced_count:,}"
    )

    return {
        'basic': basic_count,
        'advanced': advanced_count,
        'basic_remaining': max(0, API_MONTHLY_LIMIT_BASIC - basic_count),
        'advanced_remaining': max(0,
                                  API_MONTHLY_LIMIT_ADVANCED - advanced_count),
        'total': basic_count + advanced_count
    }


def calculate_tier_costs(basic_count, advanced_count):
    """
    Calculate costs for each tier based on usage.

    Args:
        basic_count (int): Basic tier elements used
        advanced_count (int): Advanced tier elements used

    Returns:
        dict: {
            'basic_cost': float,
            'advanced_cost': float,
            'total_cost': float
        }
    """
    # Basic tier: first 10k free, then $5/1000
    if basic_count <= API_MONTHLY_LIMIT_BASIC:
        basic_cost = 0.0
    else:
        billable_basic = basic_count - API_MONTHLY_LIMIT_BASIC
        basic_cost = (billable_basic / 1000) * 5.00

    # Advanced tier: first 5k free, then $10/1000
    if advanced_count <= API_MONTHLY_LIMIT_ADVANCED:
        advanced_cost = 0.0
    else:
        billable_advanced = advanced_count - API_MONTHLY_LIMIT_ADVANCED
        advanced_cost = (billable_advanced / 1000) * 10.00

    return {
        'basic_cost': basic_cost,
        'advanced_cost': advanced_cost,
        'total_cost': basic_cost + advanced_cost
    }


def _fetch_distances_from_google(addresses, destination, current_usage):
    """
    Internal: Query Google Distance Matrix API.

    This function contains the common logic extracted from
    get_zips_within_range() and get_towns_within_range().

    Args:
        addresses (list): List of address strings
        destination (str): Destination address
        current_usage (int): Current monthly API usage

    Returns:
        tuple: (results_list, elements_processed, requests_made)
    """
    # Validate API key
    api_key = get_google_api_key()
    if not api_key:
        logger.critical("Google API key not found")
        sys.exit(1)

    # Initialize client
    if PROXY_ON:
        logger.info("Initializing with Proxy")
        gmaps = googlemaps.Client(
            key=api_key,
            requests_kwargs={'proxies': {'https': PROXY}}
        )
    else:
        gmaps = googlemaps.Client(key=api_key)

    results_list = []
    elements_processed = 0
    requests_made = 0

    logger.info(
        f"Checking range for {len(addresses)} locations "
        f"against {destination}"
    )

    chunk_indices = list(range(0, len(addresses), CHUNK_SIZE))

    for i in tqdm(chunk_indices, desc="Processing locations",
                  unit="chunk", ncols=80):
        chunk = addresses[i: i + CHUNK_SIZE]

        try:
            request_params = {
                'origins': chunk,
                'destinations': destination,
                'mode': MODE,
                'units': UNITS
            }

            if AVOID:
                request_params['avoid'] = AVOID

            if USE_TRAFFIC:
                request_params['traffic_model'] = TRAFFIC_MODEL
                request_params['departure_time'] = 'now'

            response = gmaps.distance_matrix(**request_params)
            requests_made += 1

            response_status = response.get('status')

            if response_status == 'OVER_QUERY_LIMIT':
                logger.warning(
                    f"Rate limit hit. Waiting {RATE_LIMIT_WAIT_SECONDS}s..."
                )
                time.sleep(RATE_LIMIT_WAIT_SECONDS)

                logger.info("Retrying after rate limit...")
                try:
                    response = gmaps.distance_matrix(**request_params)
                    requests_made += 1
                    response_status = response.get('status')

                    if response_status != 'OK':
                        logger.error(f"Retry failed: {response_status}")
                        elements_processed += len(chunk)
                        continue
                except Exception as e:
                    logger.error(f"Retry failed: {e}")
                    continue

            elif response_status == 'OVER_DAILY_LIMIT':
                logger.critical("DAILY API LIMIT EXCEEDED - aborting")
                break

            elif response_status != 'OK':
                logger.error(f"API response error: {response_status}")
                if 'error_message' in response:
                    logger.error(f"Message: {response['error_message']}")
                elements_processed += len(chunk)
                continue

            elements_processed += len(chunk)

            # Process each row in response
            for idx, element in enumerate(response['rows']):
                status = element['elements'][0]['status']

                if status == 'OK':
                    dist_miles = round(
                        element['elements'][0]['distance']['value'] /
                        METERS_PER_MILE,
                        2
                    )
                    results_list.append({
                        'address': chunk[idx],
                        'distance_miles': dist_miles
                    })
                elif status == 'NOT_FOUND':
                    logger.warning(
                        f"Address not found: {chunk[idx]}"
                    )
                elif status == 'ZERO_RESULTS':
                    logger.debug(
                        f"No route found for {chunk[idx]}"
                    )
                else:
                    logger.warning(
                        f"API element error for {chunk[idx]}: {status}"
                    )

        except googlemaps.exceptions.ApiError as e:
            handle_api_error(e, "distance_matrix", reraise=False)
            elements_processed += len(chunk)
        except googlemaps.exceptions.TransportError as e:
            handle_api_error(e, "distance_matrix_transport", reraise=False)
        except googlemaps.exceptions.Timeout as e:
            handle_api_error(e, "distance_matrix_timeout", reraise=False)
        except KeyError as e:
            logger.error(f"Unexpected response structure: Missing {e}")
            elements_processed += len(chunk)
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")

    return results_list, elements_processed, requests_made


# ========================================
# LOCATION RANGE QUERIES
# ========================================

def get_zips_within_range(destination, zip_data_df, max_range,
                          force_refresh=False, max_cache_age_days=30):
    """
    Get zip codes within specified range of destination with cache age check.

    OPTIMIZATION: Added cache age validation.

    Args:
        destination (str): Destination address
        zip_data_df (pd.DataFrame): DataFrame with Zip, Town, State,
                                    Lat, Long columns
        max_range (float): Maximum distance in miles
        force_refresh (bool): Ignore cache and fetch fresh
        max_cache_age_days (int): Invalidate cache older than this

    Returns:
        list: Addresses (Town, State Zip) within range
    """
    cache_file = os.path.join(
        PROCESSED_DIR,
        f"zips_within_{max_range}mi.csv"
    )

    # Check cache with age validation
    if os.path.exists(cache_file) and not force_refresh:
        cache_age = datetime.now() - datetime.fromtimestamp(
            os.path.getmtime(cache_file)
        )

        if cache_age.days < max_cache_age_days:
            try:
                cached_df = pd.read_csv(cache_file)
                cached_addresses = cached_df['Full_Address'].tolist()
                logger.info(
                    f"Loaded {len(cached_addresses)} cached addresses "
                    f"from {cache_file} ({cache_age.days} days old, "
                    f"range: {max_range}mi)"
                )
                return cached_addresses
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}. Fetching fresh.")
        else:
            logger.info(
                f"Cache expired ({cache_age.days} days old, "
                f"max: {max_cache_age_days}), refreshing..."
            )

    valid_coords_df = zip_data_df.dropna(subset=['Lat', 'Long'])

    if len(valid_coords_df) < len(zip_data_df):
        missing_count = len(zip_data_df) - len(valid_coords_df)
        logger.warning(
            f"Filtered out {missing_count} ZIP codes with missing "
            f"coordinates"
        )

    # Build address list from valid coordinates only
    addresses = [
        f"{r.Town}, {r.State} {r.Zip}"
        for r in valid_coords_df.itertuples()
    ]

    # Check budget
    estimated_elements = len(addresses)
    can_proceed, current_usage = check_api_budget(estimated_elements)

    # Fetch distances
    results_list, elements_processed, requests_made = \
        _fetch_distances_from_google(addresses, destination, current_usage)

    # Filter by range
    zips_in_range = []
    filtered_results = []
    for result in results_list:
        if result['distance_miles'] <= max_range:
            zips_in_range.append(result['address'])
            filtered_results.append({
                'Full_Address': result['address'],
                'Distance_Miles': result['distance_miles']
            })

    # Update tier-based usage tracking
    update_api_usage_by_tier(elements_processed)

    # Log combined API usage and result
    tier_usage = get_current_usage_by_tier()
    logger.info(
        f"Range check complete: {len(zips_in_range)}/{len(addresses)} within "
        f"{max_range}mi | requests={requests_made} elements={elements_processed} | "
        f"Monthly: Basic={tier_usage['basic']:,} Advanced={tier_usage['advanced']:,}"
    )

    # Save cache
    if filtered_results:
        output_df = pd.DataFrame(filtered_results)
        try:
            output_df.to_csv(cache_file, index=False)
            logger.info(
                f"Saved {len(filtered_results)} locations to {cache_file}"
            )
        except IOError as e:
            logger.error(f"Failed to save results: {e}")
    else:
        logger.warning(
            f"No locations found within {max_range} miles"
        )

    return zips_in_range


def get_towns_within_range(destination, zip_data_df, max_range,
                           force_refresh=False, max_cache_age_days=30):
    """
    Get towns within specified range with cache age check.

    OPTIMIZATION: Added cache age validation.

    Args:
        destination (str): Destination address
        zip_data_df (pd.DataFrame): DataFrame with Zip, Town, State
        max_range (float): Maximum distance in miles
        force_refresh (bool): Ignore cache and fetch fresh
        max_cache_age_days (int): Invalidate cache older than this

    Returns:
        list: Town addresses (Town, State Zip) within range
    """
    cache_file = os.path.join(
        PROCESSED_DIR,
        f"towns_within_{max_range}mi.csv"
    )

    # Check cache with age validation
    if os.path.exists(cache_file) and not force_refresh:
        cache_age = datetime.now() - datetime.fromtimestamp(
            os.path.getmtime(cache_file)
        )

        if cache_age.days < max_cache_age_days:
            logger.info(f"Loading cached town results from {cache_file}")
            try:
                cached_df = pd.read_csv(cache_file)
                cached_towns = cached_df['Full_Address'].tolist()
                logger.info(
                    f"Loaded {len(cached_towns)} cached towns "
                    f"from {cache_file} ({cache_age.days} days old, "
                    f"range: {max_range}mi)"
                )
                return cached_towns
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}. Fetching fresh.")
        else:
            logger.info(
                f"Cache expired ({cache_age.days} days old, "
                f"max: {max_cache_age_days}), refreshing..."
            )

    valid_coords_df = zip_data_df.dropna(subset=['Lat', 'Long'])

    if len(valid_coords_df) < len(zip_data_df):
        missing_count = len(zip_data_df) - len(valid_coords_df)
        logger.warning(
            f"Filtered out {missing_count} ZIP codes with missing "
            f"coordinates"
        )

    # Group by town (one representative zip per town)
    town_groups_df = valid_coords_df.groupby(
        ['Town', 'State']
    ).first().reset_index()

    # Build addresses
    addresses = [
        f"{r.Town}, {r.State} {r.Zip}"
        for r in town_groups_df.itertuples()
    ]

    # Check budget
    estimated_elements = len(addresses)
    can_proceed, current_usage = check_api_budget(estimated_elements)

    # Fetch distances
    results_list, elements_processed, requests_made = \
        _fetch_distances_from_google(addresses, destination, current_usage)

    # Filter by range
    towns_in_range = []
    filtered_results = []
    for result in results_list:
        if result['distance_miles'] <= max_range:
            towns_in_range.append(result['address'])
            filtered_results.append({
                'Full_Address': result['address'],
                'Distance_Miles': result['distance_miles']
            })

    # Update tier-based usage tracking
    update_api_usage_by_tier(elements_processed)

    # Log combined API usage and result
    tier_usage = get_current_usage_by_tier()
    logger.info(
        f"Range check complete: {len(towns_in_range)}/{len(addresses)} within "
        f"{max_range}mi | requests={requests_made} elements={elements_processed} | "
        f"Monthly: Basic={tier_usage['basic']:,} Advanced={tier_usage['advanced']:,}"
    )

    # Save cache
    if filtered_results:
        output_df = pd.DataFrame(filtered_results)
        try:
            output_df.to_csv(cache_file, index=False)
            logger.info(f"Saved {len(filtered_results)} towns")
        except IOError as e:
            logger.error(f"Failed to save results: {e}")
    else:
        logger.warning(f"No towns found within {max_range} miles")

    return towns_in_range


def get_locations_within_range(destination, zip_data_df, max_range,
                               group_by='zip', force_refresh=False,
                               max_cache_age_days=30):
    """
    Dispatcher to get zips or towns within range with intelligent caching.

    OPTIMIZATION: Added cache age validation and force_refresh parameter.

    Args:
        destination (str): Destination address
        zip_data_df (pd.DataFrame): DataFrame with location data
        max_range (float): Maximum distance in miles
        group_by (str): 'zip' or 'town'
        force_refresh (bool): Ignore cache and fetch fresh (default: False)
        max_cache_age_days (int): Invalidate cache older than this (default: 30)

    Returns:
        list: Addresses within range
    """
    if group_by == 'zip':
        return get_zips_within_range(
            destination, zip_data_df, max_range, force_refresh,
            max_cache_age_days
        )
    elif group_by == 'town':
        return get_towns_within_range(
            destination, zip_data_df, max_range, force_refresh,
            max_cache_age_days
        )
    else:
        raise ValueError(
            f"group_by must be 'zip' or 'town', got '{group_by}'"
        )


# ========================================
# GOOGLE CLOUD MONITORING
# ========================================

def get_monthly_element_usage_from_google():
    """Query Google Cloud Monitoring for actual billable usage."""
    try:
        from google.cloud import monitoring_v3
        from google.oauth2 import service_account

        credentials = service_account.Credentials \
            .from_service_account_file(GCP_MONITOR_KEY)

        client = monitoring_v3.MetricServiceClient(credentials=credentials)
        project_name = f"projects/{GCP_PROJECT_ID}"

        now = datetime.now(timezone.utc)

        start_of_month = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        interval = monitoring_v3.TimeInterval({
            "end_time": {"seconds": int(now.timestamp())},
            "start_time": {"seconds": int(start_of_month.timestamp())}
        })

        results = client.list_time_series(
            request={
                "name": project_name,
                "filter": (
                    'metric.type="serviceruntime.googleapis.com/quota/'
                    'rate/net_usage" AND '
                    'resource.labels.service='
                    '"distance-matrix-backend.googleapis.com"'
                ),
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest
                .TimeSeriesView.FULL
            }
        )

        total_elements = 0
        for result in results:
            for point in result.points:
                total_elements += point.value.int64_value

        if USE_TRAFFIC:
            basic_elements = 0
            advanced_elements = total_elements
            tier_name = "Advanced"
            free_tier = API_MONTHLY_LIMIT_ADVANCED
        else:
            basic_elements = total_elements
            advanced_elements = 0
            tier_name = "Basic"
            free_tier = API_MONTHLY_LIMIT_BASIC

        logger.info(
            f"Google-reported usage: {total_elements:,} elements "
            f"({tier_name} tier)"
        )
        logger.info(
            f"Free tier limit: {free_tier:,}, "
            f"Remaining: {max(0, free_tier - total_elements):,}"
        )

        return basic_elements, advanced_elements, total_elements

    except Exception as e:
        logger.error(f"Failed to query Google Cloud Monitoring: {e}")
        return 0, 0, 0


def validate_local_tracking():
    """
    Compare local element tracking vs Google's actual count.
    Shows both overall and tier-specific breakdowns.
    """
    # Get local tier-specific counts
    tier_usage = get_current_usage_by_tier()

    # Get Google's count
    basic_google, advanced_google, google_count = \
        get_monthly_element_usage_from_google()

    # Calculate costs
    costs = calculate_tier_costs(
        tier_usage['basic'],
        tier_usage['advanced']
    )

    # Compare
    local_total = tier_usage['total']
    discrepancy = abs(local_total - google_count)

    # Determine current tier for logging
    current_tier = "Advanced" if USE_TRAFFIC else "Basic"

    logger.info(
        f"Validation: tier={current_tier} | "
        f"local={local_total:,} google={google_count:,} "
        f"delta={discrepancy:,} | "
        f"Basic={tier_usage['basic']:,}/{API_MONTHLY_LIMIT_BASIC:,} "
        f"Advanced={tier_usage['advanced']:,}/{API_MONTHLY_LIMIT_ADVANCED:,} | "
        f"cost=${costs['total_cost']:.2f}"
    )

    # Enhanced discrepancy analysis
    if google_count > 0:
        discrepancy_ratio = discrepancy / google_count
    else:
        discrepancy_ratio = 0.0

    if discrepancy > MAX_ACCEPTABLE_DISCREPANCY:
        if discrepancy_ratio > 0.5:
            logger.error(
                f"CRITICAL: Tracking severely out of sync - "
                f"local={local_total:,} google={google_count:,} "
                f"off={discrepancy_ratio:.1%} ({discrepancy:,} elements) - "
                f"check tier tracking file"
            )
        elif discrepancy_ratio > 0.1:
            logger.warning(
                f"Significant discrepancy: local={local_total:,} "
                f"google={google_count:,} off={discrepancy_ratio:.1%} - "
                f"consider checking billing reports"
            )
        else:
            logger.warning(
                f"Minor discrepancy: {discrepancy:,} elements "
                f"({discrepancy_ratio:.1%}) - likely timing variation"
            )
    else:
        logger.info(
            f"Tracking validation passed (delta={discrepancy:,} "
            f"within {MAX_ACCEPTABLE_DISCREPANCY} tolerance)"
        )

    return {
        'local_basic': tier_usage['basic'],
        'local_advanced': tier_usage['advanced'],
        'local_total': local_total,
        'google': google_count,
        'discrepancy': discrepancy,
        'discrepancy_ratio': discrepancy_ratio,
        'costs': costs,
        'tier_usage': tier_usage
    }