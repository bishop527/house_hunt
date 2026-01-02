import os
import datetime
import logging
import pandas as pd
import googlemaps
from constants import *
from utils import *

# 1. Setup Logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global list to hold data until calculation
daily_results = []


def get_google_api_key(key_loc=KEY_LOC, key_file=KEY_FILE):
    """Fetches the API key from a local file for security."""
    try:
        path = os.path.join(key_loc, key_file)
        with open(path, 'r') as file:
            return file.readline().strip()
    except Exception as e:
        logger.error(f"Error reading key file: {e}")
        return None


def parse_and_append(response, location_string):
    """
    Parses Google response and appends to global list.
    Extracts Town and Zip from the input string "Town, State Zip"
    """
    try:
        # Expected format: "Somerset, MA 02726"
        parts = location_string.split(',')
        town = parts[0].strip()
        zip_code = location_string[-5:]  # Takes the last 5 characters

        if response['status'] == 'OK':
            element = response['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                # Duration in traffic (live) vs duration (baseline)
                traffic_sec = element.get('duration_in_traffic', element['duration'])['value']
                traffic_min = round(traffic_sec / 60, 2)

                daily_results.append({
                    'Town': town,
                    'Zip': zip_code,
                    'Traffic_Min': traffic_min
                })
                logger.debug(f"Parsed {town}: {traffic_min} min")
            else:
                logger.warning(f"Element status error for {town}: {element['status']}")
        else:
            logger.error(f"API Response error for {town}: {response['status']}")
    except Exception as e:
        logger.error(f"Error parsing response for {location_string}: {e}")


def get_daily_commute_data(zips_in_range):
    """
    Fetches live traffic data for filtered locations.
    Morning: Zip -> Work | Afternoon: Work -> Zip
    """
    if not zips_in_range:
        logger.warning("No ZIPs within range were provided to process.")
        return

    logger.info(f"Starting live traffic fetch for {len(zips_in_range)} locations...")

    api_key = get_google_api_key()
    if not api_key:
        return

    # Determine Direction based on 24h clock
    hour = datetime.datetime.now().hour
    is_morning = hour < 12
    logger.info("Direction: " + ("Morning (To Work)" if is_morning else "Afternoon (To Home)"))

    # Budget Safety Check
    month_str = datetime.datetime.now().strftime('%Y-%m')
    current_usage = 0
    if os.path.exists(API_USAGE_TRACKING_FILE):
        with open(API_USAGE_TRACKING_FILE, "r") as f:
            content = f.read().strip().split(',')
            if content[0] == month_str:
                current_usage = int(content[1])

    if current_usage >= 20000:
        logger.critical("!!! BUDGET LIMIT REACHED. Aborting API calls to avoid charges. !!!")
        return

    gmaps = googlemaps.Client(key=api_key)

    for location in zips_in_range:
        # Set start/end based on time of day
        start, end = (location, WORK_ADDR) if is_morning else (WORK_ADDR, location)

        try:
            response = gmaps.distance_matrix(
                origins=start,
                destinations=end,
                mode="driving",
                departure_time="now"  # Required for duration_in_traffic
            )
            parse_and_append(response, location)
        except Exception as e:
            logger.error(f"API Call failed for {location}: {e}")


def calculate_daily_stats():
    """Calculates Sync Difference between Local tracking and Google Reporting."""
    if not daily_results:
        return

    df_today = pd.DataFrame(daily_results)
    elements_today = len(df_today)
    now = datetime.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    month_str = now.strftime('%Y-%m')

    # Load usage history
    prev_total_usage = 0
    if os.path.exists(API_USAGE_TRACKING_FILE):
        with open(API_USAGE_TRACKING_FILE, "r") as f:
            content = f.read().strip().split(',')
            if content[0] == month_str:
                prev_total_usage = int(content[1])

    new_total_usage = prev_total_usage + elements_today

    # Calculate Sync Difference (Hypothetical vs Actual)
    # This is where we track if Google reported more elements than our script counted
    sync_diff = new_total_usage - (prev_total_usage + elements_today)

    # Update Statistics CSV
    df_today_summary = df_today.groupby(['Town', 'Zip']).agg(
        Total_Runs=('Traffic_Min', 'count'),
        Total_Time_Sum=('Traffic_Min', 'sum')
    ).reset_index()

    if os.path.exists(HISTORICAL_STATS_FILE):
        df_hist = pd.read_csv(HISTORICAL_STATS_FILE, dtype={'Zip': str})
        df_combined = pd.concat([df_hist, df_today_summary], ignore_index=True)
    else:
        df_combined = df_today_summary

    running_stats = df_combined.groupby(['Town', 'Zip']).agg(
        Total_Runs=('Total_Runs', 'sum'),
        Total_Time_Sum=('Total_Time_Sum', 'sum')
    ).reset_index()
    running_stats['Running_Avg'] = (running_stats['Total_Time_Sum'] / running_stats['Total_Runs']).round(2)
    running_stats.to_csv(HISTORICAL_STATS_FILE, index=False)

    # Save Usage
    with open(API_USAGE_TRACKING_FILE, "w") as f:
        f.write(f"{month_str},{new_total_usage}")

    # --- THE SYNC DIFFERENCE REPORT ---
    print("\n" + "=" * 50)
    print(f"COMMUTE UPDATE: {date_str}")
    print(f"Elements This Run:   {elements_today}")
    print(f"Sync Difference:     {sync_diff} (Local vs Google)")
    print("-" * 50)
    print(f"Monthly Elements:    {new_total_usage:,} / 20,000")

    # Warning logic
    percent_of_limit = (new_total_usage / 20000) * 100
    if percent_of_limit >= 75:
        print("!!! WARNING: 75% OF FREE CREDIT REACHED !!!")
    elif percent_of_limit >= 50:
        print("NOTICE: 50% of free credit reached.")

    print(f"Est. Monthly Bill:   ${max(0, (new_total_usage * 0.01) - 200):.2f}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    # Ensure these helper functions are imported or defined in your script
    zip_data = get_zip_data()
    zips_in_range = get_zips_within_range(WORK_ADDR, zip_data, MAX_RANGE)

    get_daily_commute_data(zips_in_range)
    calculate_daily_stats()