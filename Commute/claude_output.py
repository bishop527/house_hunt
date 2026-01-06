import sys
import os
import googlemaps
import pandas as pd
import logging
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


def get_zips_within_range(destination, zip_data, max_range):
    """
    Interrogates Google Maps API and returns list of zip codes within
    specified range of destination.

    Args:
        destination (str): Destination address
        zip_data (pd.DataFrame): DataFrame with Zip, Town, State, Lat, Long columns
        max_range (float): Maximum distance in miles

    Returns:
        list: List of full addresses (Town, State Zip) within range

    Raises:
        SystemExit: If API key missing or monthly budget exceeded
    """

    # Validate API key before proceeding
    api_key = get_google_api_key()
    if not api_key:
        logger.critical("Google API key not found. Cannot proceed.")
        sys.exit(1)

    # CRITICAL FIX #2: Check API budget before making calls
    month_str = datetime.now().strftime('%Y-%m')
    current_usage = 0

    if os.path.exists(API_USAGE_TRACKING_FILE):
        try:
            with open(API_USAGE_TRACKING_FILE, "r") as f:
                content = f.read().strip().split(',')
                if len(content) == 2 and content[0] == month_str:
                    current_usage = int(content[1])
                    logger.info(f"Current monthly usage: {current_usage:,}")
        except (ValueError, IndexError) as e:
            logger.warning(
                f"Error reading usage file, assuming 0 usage: {e}"
            )

    # Estimate elements needed for this run
    estimated_elements = len(zip_data)
    projected_usage = current_usage + estimated_elements

    if current_usage >= 20000:
        logger.critical(
            f"!!! MONTHLY BUDGET LIMIT REACHED !!!\n"
            f"Current usage: {current_usage:,} / 20,000\n"
            f"Aborting to prevent overage charges."
        )
        sys.exit(1)

    if projected_usage > 20000:
        logger.warning(
            f"!!! WARNING: This run may exceed budget !!!\n"
            f"Current usage: {current_usage:,}\n"
            f"Estimated elements: {estimated_elements:,}\n"
            f"Projected total: {projected_usage:,} / 20,000"
        )
        # Don't exit, but warn user - they can decide to continue

    # Initialize Google Maps client
    if PROXY_ON:
        logger.info("Initializing Google Maps client with Proxy settings.")
        gmaps = googlemaps.Client(
            key=api_key,
            requests_kwargs={
                'proxies': {'https': 'http://localhost:8080'}
            }
        )
    else:
        gmaps = googlemaps.Client(key=api_key)

    addresses = [
        f"{r.Town}, {r.State} {r.Zip}" for r in zip_data.itertuples()
    ]
    zips_in_range = []
    results_list = []
    actual_api_calls = 0

    logger.info(
        f"Checking range for {len(addresses)} locations against "
        f"{destination} (Max: {max_range} miles)"
    )

    # Process in chunks
    for i in range(0, len(addresses), CHUNK_SIZE):
        chunk = addresses[i: i + CHUNK_SIZE]

        try:
            response = gmaps.distance_matrix(
                origins=chunk,
                destinations=destination,
                mode=MODE,
                units=UNITS
            )

            # CRITICAL FIX #5: Validate top-level response status
            if response.get('status') != 'OK':
                logger.error(
                    f"Google API response error for chunk starting at "
                    f"index {i}: {response.get('status')}"
                )
                # Log the error message if available
                if 'error_message' in response:
                    logger.error(f"Error message: {response['error_message']}")
                continue  # Skip this chunk but continue with others

            actual_api_calls += len(chunk)

            # Process each row in the response
            for idx, element in enumerate(response['rows']):
                status = element['elements'][0]['status']

                if status == 'OK':
                    # Convert meters to miles
                    dist_miles = (
                            element['elements'][0]['distance'][
                                'value'] / 1609.34
                    )

                    if dist_miles <= max_range:
                        zips_in_range.append(chunk[idx])
                        results_list.append({
                            'Full_Address': chunk[idx],
                            'Distance_Miles': round(dist_miles, 2)
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
                        f"Google API element error for {chunk[idx]}: {status}"
                    )

        # CRITICAL FIX #3: Specific exception handling
        except googlemaps.exceptions.ApiError as e:
            logger.error(
                f"Google API error for chunk starting at index {i}: {e}"
            )
            continue  # Skip this chunk
        except googlemaps.exceptions.TransportError as e:
            logger.error(
                f"Network/transport error for chunk starting at index {i}: {e}"
            )
            continue  # Skip this chunk
        except googlemaps.exceptions.Timeout as e:
            logger.error(
                f"Timeout error for chunk starting at index {i}: {e}"
            )
            continue  # Skip this chunk
        except KeyError as e:
            logger.error(
                f"Unexpected response structure for chunk starting at "
                f"index {i}: Missing key {e}"
            )
            continue  # Skip this chunk
        except Exception as e:
            logger.error(
                f"Unexpected error processing chunk starting at index {i}: "
                f"{type(e).__name__}: {e}"
            )
            continue  # Skip this chunk

    # Update usage tracking with actual API calls made
    new_total_usage = current_usage + actual_api_calls
    try:
        with open(API_USAGE_TRACKING_FILE, "w") as f:
            f.write(f"{month_str},{new_total_usage}")
        logger.info(
            f"Updated usage tracking: {new_total_usage:,} / 20,000"
        )
    except IOError as e:
        logger.error(f"Failed to update usage tracking file: {e}")

    # Save results if any were found
    if results_list:
        output_df = pd.DataFrame(results_list)
        output_path = os.path.join(
            PROCESSED_DIR,
            f"towns_within_{max_range}mi.csv"
        )

        try:
            output_df.to_csv(output_path, index=False)
            logger.info(
                f"Range check complete. Saved {len(results_list)} "
                f"locations to {output_path}"
            )
        except IOError as e:
            logger.error(f"Failed to save results to CSV: {e}")
    else:
        logger.warning(
            f"No locations found within {max_range} miles of {destination}"
        )

    # CRITICAL FIX #4: Return value matches variable name
    logger.info(
        f"Returning {len(zips_in_range)} addresses within range"
    )
    return zips_in_range