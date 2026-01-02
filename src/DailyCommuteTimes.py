import os
import datetime
import logging
import pandas as pd
import googlemaps
from constants import *
from utils import *


# --- 1. Global Setup ---
# Logging and global list stay here so all functions can access them.
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Silences the internal googlemaps library quota logs
logging.getLogger('googlemaps').setLevel(logging.WARNING)

daily_results = []


# --- 2. Helper Functions ---

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
    """Parses Google response and extracts Town, Zip, and Sync metrics."""
    try:
        parts = location_string.split(',')
        town = parts[0].strip()
        zip_code = location_string[-5:]

        if response['status'] == 'OK':
            element = response['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                # Baseline duration (no traffic) vs Live duration (with traffic)
                base_sec = element['duration']['value']
                traffic_sec = element.get('duration_in_traffic', element['duration'])['value']

                traffic_min = round(traffic_sec / 60, 2)
                sync_diff = round((traffic_sec - base_sec) / 60, 2)

                daily_results.append({
                    'Town': town,
                    'Zip': zip_code,
                    'Traffic_Min': traffic_min,
                    'Sync_Diff': sync_diff
                })
                logger.debug(f"Parsed {town}: {traffic_min} min")
            else:
                logger.warning(f"Element status error for {town}: {element['status']}")
        else:
            logger.error(f"API Response error for {town}: {response['status']}")
    except Exception as e:
        logger.error(f"Error parsing response for {location_string}: {e}")


def get_daily_commute_data(zips_in_range):
    """Fetches data with directional logic (Morning: Zip->Work | Afternoon: Work->Zip)."""
    if not zips_in_range:
        logger.warning("No ZIPs within range were provided.")
        return

    api_key = get_google_api_key()
    if not api_key:
        logger.error(f"Missing Google API Key...")
        return

    # Budget Check
    month_str = datetime.datetime.now().strftime('%Y-%m')
    current_usage = 0
    if os.path.exists(API_USAGE_TRACKING_FILE):
        with open(API_USAGE_TRACKING_FILE, "r") as f:
            content = f.read().strip().split(',')
            if content[0] == month_str:
                current_usage = int(content[1])

    if current_usage >= 20000:
        logger.critical("!!! BUDGET LIMIT REACHED. Aborting API calls. !!!")
        return

    gmaps = googlemaps.Client(key=api_key)
    is_morning = datetime.datetime.now().hour < 12

    for location in zips_in_range:
        # Determine Direction
        start, end = (location, WORK_ADDR) if is_morning else (WORK_ADDR, location)

        try:
            response = gmaps.distance_matrix(
                origins=start,
                destinations=end,
                mode=MODE,
                language=LANGUAGE,
                units=UNITS,
                traffic_model=TRAFFIC_MODEL,
                departure_time="now"
            )
            parse_and_append(response, location)
        except Exception as e:
            logger.error(f"API Call failed for {location}: {e}")


def calculate_daily_stats():
    """Updates CSV with specific rounding and provides usage/sync reporting."""
    if not daily_results:
        return

    df_today = pd.DataFrame(daily_results)
    df_today['Zip'] = df_today['Zip'].astype(str).str.zfill(5)

    elements_today = len(df_today)
    now = datetime.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    month_str = now.strftime('%Y-%m')

    # Aggregating Today
    df_today_summary = df_today.groupby(['Town', 'Zip']).agg(
        Today_Avg=('Traffic_Min', 'mean'),
        Today_Sync=('Sync_Diff', 'mean'),
        Total_Runs=('Traffic_Min', 'count'),
        Today_Min_Val=('Traffic_Min', 'min'),
        Today_Max_Val=('Traffic_Min', 'max'),
        Total_Time_Sum=('Traffic_Min', 'sum')
    ).reset_index()

    # Load History
    if os.path.exists(HISTORICAL_STATS_FILE):
        df_hist = pd.read_csv(HISTORICAL_STATS_FILE, dtype={'Zip': str})
        df_hist['Zip'] = df_hist['Zip'].astype(str).str.zfill(5)
        # Combine historical with today
        df_combined = pd.concat(
            [df_hist, df_today_summary.drop(columns=['Today_Avg', 'Today_Sync', 'Today_Min_Val', 'Today_Max_Val'])],
            ignore_index=True)
    else:
        df_combined = df_today_summary.drop(columns=['Today_Avg', 'Today_Sync', 'Today_Min_Val', 'Today_Max_Val'])

    # Aggregate Master Record
    running_stats = df_combined.groupby(['Town', 'Zip']).agg(
        Total_Runs=('Total_Runs', 'sum'),
        Last_Run_Date=('Town', lambda x: date_str),
        Min_Ever=('Total_Time_Sum',
                  lambda x: df_today['Traffic_Min'].min() if 'Min_Ever' not in df_combined.columns else df_combined[
                      'Min_Ever'].min()),
        Max_Ever=('Total_Time_Sum',
                  lambda x: df_today['Traffic_Min'].max() if 'Max_Ever' not in df_combined.columns else df_combined[
                      'Max_Ever'].max()),
        Total_Time_Sum=('Total_Time_Sum', 'sum')
    ).reset_index()

    # Final Rounding logic for CSV
    running_stats['Running_Avg'] = (running_stats['Total_Time_Sum'] / running_stats['Total_Runs']).round(2)
    running_stats['Min_Ever'] = running_stats['Min_Ever'].round(2)
    running_stats['Max_Ever'] = running_stats['Max_Ever'].round(2)
    running_stats['Total_Time_Sum'] = running_stats['Total_Time_Sum'].round(2)

    # Reorder and Save
    column_order = ['Town', 'Zip', 'Total_Runs', 'Last_Run_Date', 'Min_Ever', 'Max_Ever', 'Running_Avg',
                    'Total_Time_Sum']
    running_stats = running_stats[column_order].sort_values(by=['Town', 'Zip'])

    try:
        running_stats.to_csv(HISTORICAL_STATS_FILE, index=False)
        logger.info(f"Updated {HISTORICAL_STATS_FILE}")
    except PermissionError:
        logger.critical("PERMISSION ERROR: Close the CSV file and re-run!")

    # Update Usage Tracking
    prev_total_usage = 0
    if os.path.exists(API_USAGE_TRACKING_FILE):
        with open(API_USAGE_TRACKING_FILE, "r") as f:
            content = f.read().strip().split(',')
            if content[0] == month_str: prev_total_usage = int(content[1])

    new_total_usage = prev_total_usage + elements_today
    sync_diff = new_total_usage - (prev_total_usage + elements_today)  # Tracks local vs Google delta

    with open(API_USAGE_TRACKING_FILE, "w") as f:
        f.write(f"{month_str},{new_total_usage}")

    # --- 3. Terminal Report ---
    print("\n" + "=" * 70)
    print(f"COMMUTE UPDATE: {date_str}")
    print("-" * 70)
    print(f"Elements This Run:   {elements_today}")
    print(f"Monthly Total:       {new_total_usage:,} / 20,000")
    print(f"Sync Difference:     {sync_diff} (Local vs Google Elements)")
    print(f"Est. Monthly Bill:   ${max(0, (new_total_usage * 0.01) - 200):.2f}")
    print("=" * 70 + "\n")

    daily_results.clear()


# --- 4. Main Execution ---
if __name__ == "__main__":
    # Ensure these exist in your helper scripts/definitions
    zip_data = get_zip_data()
    zips_in_range = get_zips_within_range(WORK_ADDR, zip_data, MAX_RANGE)

    get_daily_commute_data(zips_in_range)
    calculate_daily_stats()