'''
Created on Nov 4, 2015

@author: AD23883

Utility functions for House Hunt project.
'''
import sys
import os
import googlemaps
import pandas as pd
import logging
import time
from tqdm import tqdm
from datetime import datetime, timedelta
from constants import *

# Initialize Logger using constants
logger = logging.getLogger(__name__)


def get_google_api_key(key_loc=KEY_LOC, key_file=KEY_FILE):
    """Fetches the API key from the Data root."""
    try:
        path = os.path.join(key_loc, key_file)
        with open(path, 'r') as file:
            key = file.readline().strip()
            logger.debug(f"API Key successfully loaded from {path}")
            return key
    except Exception as e:
        logger.error(f"Failed to read API key file: {e}")
        return None


def check_api_budget(estimated_elements, limit=API_MONTHLY_LIMIT):
    """
    Check if API budget allows for the requested number of elements.

    Args:
        estimated_elements (int): Number of elements needed for this run
        limit (int): Monthly element limit (defaults to API_MONTHLY_LIMIT)

    Returns:
        tuple: (bool, int) - (can_proceed, current_usage)

    Raises:
        SystemExit: If monthly budget already exceeded
    """
    month_str = datetime.now().strftime('%Y-%m')
    current_usage = 0

    if os.path.exists(API_MONTHLY_COUNTER):
        try:
            with open(API_MONTHLY_COUNTER, "r") as f:
                content = f.read().strip().split(',')
                if len(content) == 2 and content[0] == month_str:
                    current_usage = int(content[1])
        except (ValueError, IndexError) as e:
            logger.warning(
                f"Error reading usage file, assuming 0 usage: {e}"
            )

    logger.info(f"Current monthly API usage: {current_usage:,} / {limit:,}")

    # Check if already at limit
    if current_usage >= limit:
        logger.critical(
            f"!!! MONTHLY BUDGET LIMIT REACHED !!!\n"
            f"Current usage: {current_usage:,} / {limit:,}\n"
            f"Aborting to prevent overage charges."
        )
        sys.exit(1)

    # Check if this run would exceed limit
    projected_usage = current_usage + estimated_elements
    if projected_usage > limit:
        logger.warning(
            f"!!! WARNING: This run may exceed budget !!!\n"
            f"Current usage: {current_usage:,}\n"
            f"Estimated elements: {estimated_elements:,}\n"
            f"Projected total: {projected_usage:,} / {limit:,}"
        )
        # Don't abort, but warn user

    return True, current_usage


def update_api_usage(elements_used):
    """
    Update the monthly API usage counter.

    Args:
        elements_used (int): Number of API elements processed in this run

    Returns:
        int: New total usage for the month
    """
    month_str = datetime.now().strftime('%Y-%m')
    current_usage = 0

    if os.path.exists(API_MONTHLY_COUNTER):
        try:
            with open(API_MONTHLY_COUNTER, "r") as f:
                content = f.read().strip().split(',')
                if len(content) == 2 and content[0] == month_str:
                    current_usage = int(content[1])
        except (ValueError, IndexError):
            pass

    new_total = current_usage + elements_used

    try:
        with open(API_MONTHLY_COUNTER, "w") as f:
            f.write(f"{month_str},{new_total}")
        logger.info(
            f"Updated API usage: {elements_used} elements this run, "
            f"{new_total:,} / {API_MONTHLY_LIMIT:,} monthly total"
        )
    except IOError as e:
        logger.error(f"Failed to update usage counter: {e}")

    return new_total


def load_csv_with_zip(filepath):
    """
    Load CSV file with proper Zip code handling.

    Ensures Zip codes are read as strings and zero-padded to 5 digits.

    Args:
        filepath (str): Path to CSV file

    Returns:
        pd.DataFrame: Loaded data, or empty DataFrame if file doesn't exist
    """
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath, dtype={'Zip': str})
            # Ensure Zip is zero-padded
            if 'Zip' in df.columns:
                df['Zip'] = df['Zip'].str.zfill(5)
            logger.info(f"Loaded {len(df)} records from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV from {filepath}: {e}")
            return pd.DataFrame()
    else:
        logger.info(f"File not found: {filepath}")
        return pd.DataFrame()


def get_hours_until_first_time_check():
    """Calculates time until first morning time slot on Monday"""
    now = datetime.now()
    days_ahead = (0 - now.weekday() + 7) % 7
    target = now + timedelta(days=days_ahead)
    first_hour, first_min = map(int, MORNING_TIMES[0].split(':'))
    target = target.replace(
        hour=first_hour,
        minute=first_min,
        second=0,
        microsecond=0
    )
    if target <= now:
        target += timedelta(days=7)
    return (target - now).total_seconds() / 3600


def get_zip_data(states=None, include_county=False):
    """
    Reads the master ZIP database from Data/Raw/ and filters for
    standard, active (non-decommissioned) zip codes.

    Args:
        states (list, optional): List of state abbreviations to filter.
                                Defaults to TARGET_STATES from constants.
        include_county (bool): If True, includes county column in
                              returned DataFrame. Default False.

    Returns:
        pd.DataFrame: Filtered zip code data with columns:
                     ['Zip', 'Town', 'State', 'Lat', 'Long'] and
                     optionally ['County']

    Raises:
        SystemExit: If file not found or critical parsing error occurs
    """
    if states is None:
        states = TARGET_STATES

    # Check file exists
    if not os.path.exists(ZIP_DATA_FILE):
        logger.critical(f"Source file not found: {ZIP_DATA_FILE}")
        sys.exit(1)

    logger.info(f"Parsing ZIP database: {ZIP_DATA_FILE}")

    # Build column list based on parameters
    cols_to_read = ['zip', 'type', 'decommissioned', 'primary_city',
                    'state', 'latitude', 'longitude']
    dtype_dict = {
        'zip': str,
        'type': str,
        'decommissioned': int,
        'primary_city': str,
        'state': str
    }

    if include_county:
        cols_to_read.append('county')
        dtype_dict['county'] = str

    try:
        # Read CSV with proper data types
        df = pd.read_csv(
            ZIP_DATA_FILE,
            header=0,
            usecols=cols_to_read,
            dtype=dtype_dict,
            # Convert lat/long to numeric, allowing NaN for missing values
            converters={
                'latitude': lambda x: pd.to_numeric(x, errors='coerce'),
                'longitude': lambda x: pd.to_numeric(x, errors='coerce')
            }
        )

    except FileNotFoundError:
        logger.critical(f"ZIP database file not found: {ZIP_DATA_FILE}")
        sys.exit(1)
    except pd.errors.ParserError as e:
        logger.critical(f"CSV parsing error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.critical(f"Column mismatch in ZIP database: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error reading ZIP data: {e}")
        sys.exit(1)

    # Rename columns for consistency
    rename_dict = {
        'zip': 'Zip',
        'primary_city': 'Town',
        'state': 'State',
        'latitude': 'Lat',
        'longitude': 'Long'
    }
    if include_county:
        rename_dict['county'] = 'County'

    df = df.rename(columns=rename_dict)

    # Filter: target states, standard type, active (not decommissioned)
    zip_data = df[
        (df['State'].isin(states)) &
        (df['type'] == "STANDARD") &
        (df['decommissioned'] == 0)
    ].copy()

    # Drop columns no longer needed
    zip_data = zip_data.drop(columns=['type', 'decommissioned'])

    # Remove rows with missing CRITICAL data (Zip, Town, State only)
    before_dropna = len(zip_data)

    # Log rows with missing critical data before dropping
    missing_data = zip_data[
        zip_data['Zip'].isna() |
        zip_data['Town'].isna() |
        zip_data['State'].isna() |
        zip_data['Lat'].isna() |
        zip_data['Long'].isna()
    ]

    if len(missing_data) > 0:
        logger.warning(
            f"Found {len(missing_data)} rows with missing critical data:"
        )
        for idx, row in missing_data.iterrows():
            logger.warning(
                f"  Row {idx}: Zip={row.get('Zip', 'MISSING')}, "
                f"Town={row.get('Town', 'MISSING')}, "
                f"State={row.get('State', 'MISSING')}, "
                f"Lat={row.get('Lat', 'MISSING')}, "
                f"Long={row.get('Long', 'MISSING')}"
            )

    # Drop rows with missing critical data
    zip_data = zip_data.dropna(subset=['Zip', 'Town', 'State', 'Lat', 'Long'])
    dropped = before_dropna - len(zip_data)

    if dropped > 0:
        logger.warning(
            f"Dropped {dropped} rows with missing critical data "
            f"(Zip, Town, State, Lat, or Long)"
        )

    # Ensure Zip codes are zero-padded to 5 digits
    zip_data['Zip'] = zip_data['Zip'].str.zfill(5)

    # Validate we have data
    if len(zip_data) == 0:
        logger.error(f"No zip codes found for states: {states}")
        sys.exit(1)

    logger.info(
        f"Loaded {len(zip_data)} active standard ZIPs for "
        f"{', '.join(states)}"
    )

    return zip_data.reset_index(drop=True)


def get_zips_within_range(destination, zip_data, max_range,
                          force_refresh=False):
    """
    Interrogates Google Maps API and returns list of zip codes within
    specified range of destination.

    Results are cached to avoid repeated API calls. Delete the cache file
    or use force_refresh=True to regenerate.

    Args:
        destination (str): Destination address
        zip_data (pd.DataFrame): DataFrame with Zip, Town, State,
                                 Lat, Long columns
        max_range (float): Maximum distance in miles
        force_refresh (bool): If True, ignore cache and fetch fresh data

    Returns:
        list: List of full addresses (Town, State Zip) within range

    Raises:
        SystemExit: If API key missing or monthly budget exceeded
    """
    # Cache file path
    cache_file = os.path.join(
        PROCESSED_DIR,
        f"towns_within_{max_range}mi.csv"
    )

    # Check for cached results
    if os.path.exists(cache_file) and not force_refresh:
        logger.info(f"Loading cached results from {cache_file}")
        try:
            cached_df = pd.read_csv(cache_file)
            cached_addresses = cached_df['Full_Address'].tolist()
            logger.info(
                f"Loaded {len(cached_addresses)} cached addresses "
                f"(range: {max_range}mi)"
            )
            return cached_addresses
        except Exception as e:
            logger.warning(f"Failed to read cache file: {e}. Fetching fresh.")

    # Validate API key before proceeding
    api_key = get_google_api_key()
    if not api_key:
        logger.critical("Google API key not found. Cannot proceed.")
        sys.exit(1)

    # Check API budget before making calls
    estimated_elements = len(zip_data)
    can_proceed, current_usage = check_api_budget(estimated_elements)

    # Initialize Google Maps client
    if PROXY_ON:
        logger.info("Initializing Google Maps client with Proxy settings.")
        gmaps = googlemaps.Client(
            key=api_key,
            requests_kwargs={
                'proxies': {'https': PROXY}
            }
        )
    else:
        gmaps = googlemaps.Client(key=api_key)

    addresses = [
        f"{r.Town}, {r.State} {r.Zip}" for r in zip_data.itertuples()
    ]
    zips_in_range = []
    results_list = []
    elements_processed = 0
    requests_made = 0

    logger.info(
        f"Checking range for {len(addresses)} locations against "
        f"{destination} (Max: {max_range} miles)"
    )

    # Process in chunks with progress bar
    chunk_indices = list(range(0, len(addresses), CHUNK_SIZE))

    for i in tqdm(chunk_indices,
                  desc="Processing locations",
                  unit="chunk",
                  ncols=80):
        chunk = addresses[i: i + CHUNK_SIZE]

        try:
            response = gmaps.distance_matrix(
                origins=chunk,
                destinations=destination,
                mode=MODE,
                units=UNITS
            )

            requests_made += 1

            # Validate top-level response status
            response_status = response.get('status')

            if response_status == 'OVER_QUERY_LIMIT':
                logger.warning(
                    f"Rate limit hit. "
                    f"Waiting {RATE_LIMIT_WAIT_SECONDS} seconds..."
                )
                time.sleep(RATE_LIMIT_WAIT_SECONDS)

                # Retry this chunk once
                logger.info("Retrying after rate limit...")
                try:
                    response = gmaps.distance_matrix(
                        origins=chunk,
                        destinations=destination,
                        mode=MODE,
                        units=UNITS
                    )
                    requests_made += 1
                    response_status = response.get('status')

                    if response_status != 'OK':
                        logger.error(
                            f"Retry failed: {response_status}"
                        )
                        elements_processed += len(chunk)
                        continue
                except Exception as e:
                    logger.error(f"Retry failed: {e}")
                    continue

            elif response_status == 'OVER_DAILY_LIMIT':
                logger.critical(
                    f"!!! DAILY API LIMIT EXCEEDED !!!\n"
                    f"Cannot continue processing. Try again tomorrow."
                )
                break

            elif response_status != 'OK':
                logger.error(
                    f"Google API response error: {response_status}"
                )
                if 'error_message' in response:
                    logger.error(
                        f"Error message: {response['error_message']}"
                    )
                elements_processed += len(chunk)
                continue

            elements_processed += len(chunk)

            # Process each row in the response
            for idx, element in enumerate(response['rows']):
                status = element['elements'][0]['status']

                if status == 'OK':
                    dist_miles = round(
                        element['elements'][0]['distance']['value'] /
                        METERS_PER_MILE,
                        2
                    )

                    if dist_miles <= max_range:
                        zips_in_range.append(chunk[idx])
                        results_list.append({
                            'Full_Address': chunk[idx],
                            'Distance_Miles': dist_miles
                        })
                elif status == 'NOT_FOUND':
                    logger.warning(
                        f"Address not found by Google: {chunk[idx]}"
                    )
                elif status == 'ZERO_RESULTS':
                    logger.debug(
                        f"No route found for {chunk[idx]} to {destination}"
                    )
                else:
                    logger.warning(
                        f"Google API element error for {chunk[idx]}: "
                        f"{status}"
                    )

        except googlemaps.exceptions.ApiError as e:
            logger.error(f"Google API error: {e}")
            elements_processed += len(chunk)
            continue
        except googlemaps.exceptions.TransportError as e:
            logger.error(f"Network/transport error: {e}")
            continue
        except googlemaps.exceptions.Timeout as e:
            logger.error(f"Timeout error: {e}")
            continue
        except KeyError as e:
            logger.error(
                f"Unexpected response structure: Missing key {e}"
            )
            elements_processed += len(chunk)
            continue
        except Exception as e:
            logger.error(
                f"Unexpected error: {type(e).__name__}: {e}"
            )
            continue

    # Update usage tracking
    new_total_usage = current_usage + elements_processed
    try:
        month_str = datetime.now().strftime('%Y-%m')
        with open(API_MONTHLY_COUNTER, "w") as f:
            f.write(f"{month_str},{new_total_usage}")
        logger.info(
            f"API usage summary - Requests made: {requests_made}, "
            f"Elements processed: {elements_processed}, "
            f"Monthly total: {new_total_usage:,} / 20,000"
        )
    except IOError as e:
        logger.error(f"Failed to update usage tracking file: {e}")

    # Save results CSV (serves as cache)
    if results_list:
        output_df = pd.DataFrame(results_list)

        try:
            output_df.to_csv(cache_file, index=False)
            logger.info(
                f"Saved {len(results_list)} locations to {cache_file}"
            )
        except IOError as e:
            logger.error(f"Failed to save results to CSV: {e}")
    else:
        logger.warning(
            f"No locations found within {max_range} miles of {destination}"
        )

    logger.info(
        f"Returning {len(zips_in_range)} addresses within range"
    )
    return zips_in_range