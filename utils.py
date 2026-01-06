'''
Created on Nov 4, 2015

@author: AD23883

'''
import sys
import os
import googlemaps
import pandas as pd
import logging
from datetime import datetime, timedelta
import time
from tqdm import tqdm  # for progress bar
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


def get_hours_until_first_time_check():
    """Calculates time until first morning time slot on Monday"""
    now = datetime.now()
    days_ahead = (0 - now.weekday() + 7) % 7
    target = now + timedelta(days=days_ahead)
    first_hour, first_min = map(int, MORNING_TIMES[0].split(':'))
    target = target.replace(hour=first_hour, minute=first_min, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=7)
    return (target - now).total_seconds() / 3600


'''
Parse the Zip Code Database csv file
CSV file format
- zip                   (USPS zip code)
- type                  (USPS Military, PO Box, Standard, or Unique)
- decommissioned        (0 or 1, whether or not USPS has decommissioned the zip)
- primary_city          (USPS listed primary city)
- acceptable_cities     (USPS alternate cities for zip codes used by multiple cities)
- unacceptable_citiies  (Alternate names that are not officially recognized by USPS)
- state                 (2 letter state abbreviation)
- county                (county with the largest percentage of the zip code population)
- timezone
- area_codes
- lattitude
- longitude
'''
def get_csv_data():
    csv_data_file = os.path.join(DATA_DIR, 'zip_code_database.csv')
    csv_data = pd.read_csv(csv_data_file)

    return csv_data


'''
Parse given CSV or Excel file and return a dataframe

Input files need to have the following fields
- zip
- type
- town
- state
- latitude
- longitude
'''
def get_town_data(file_name):

    print("Parsing {} file".format(file_name))
    try:
        town_data = pd.read_csv(file_name, header=0,
                                usecols=['zip','type','town','state','latitude','longitude'],
                                dtype={'zip':str, 'type':str, 'town':str, 'state':str, 'latitude':str, 'longitude':str})
        print("File Type: CSV")
    except pd.errors.ParserError:
        # This error typically occurs when a non-CSV file is attempted to be read as CSV
        pass
    except FileNotFoundError:
        return 'File not found'
    except Exception as e: # Catching a broader exception for other issues like FileNotFoundError
        print("  File not a CSV")
    
    try:
        town_data = pd.read_excel(file_name, header=0,
                                    usecols=['zip', 'type', 'town', 'state', 'latitude', 'longitude'],
                                    dtype={'zip': str, 'type': str, 'town': str, 'state': str, 'latitude': str, 'longitude': str})
        print("File Type: Excel")
    except pd.errors.ParserError:
        # This error typically occurs when a non-CSV file is attempted to be read as CSV
        pass
    except FileNotFoundError:
        return 'File not found'
    except Exception as e: # Catching a broader exception for other issues like FileNotFoundError
        print("  File Error: {}".format(e))
        return

    # Filter for only states = MA, RI, and NH
    town_data = town_data[(town_data['state'] == 'MA') | 
                          (town_data['state'] == 'RI') | 
                          (town_data['state'] == 'NH')]
    
    # Filter for only type = STANDARD
    # UNIQUE is usually associated with organization
    # PO BOX is usually undeliverable regions
    town_data = town_data[town_data['type'] == "STANDARD"]

    return town_data


'''
Interrogate Google Maps API to return list of towns within a given range from a given destination
'''
def get_towns_within_range(destination, max_range):

    town_data = get_town_data(os.path.join(DATA_DIR, 'zip_code_database.csv'))

    print('Downloading Data for towns within {} miles of {}'.format(max_range, destination))
    googleAPIkey = get_google_api_key()

    if PROXY_ON:
        gmaps = googlemaps.Client(key=googleAPIkey, requests_kwargs={
            'proxies': {'https': 'http://localhost:8080'}})
    else:
        gmaps = googlemaps.Client(key=googleAPIkey)

    mode = 'driving'
    language = 'en'
    units = 'imperial'
    batch_limit = 25
    batch = list()
    towns_in_range = pd.DataFrame()

    addresses = list()
    for row in town_data.itertuples():
        addresses.append(row.town + " " + row.state + ", " +  row.zip)

    lat_longs = list()
    for row in town_data.itertuples():
        lat_longs.append(row.latitude + "," + row.longitude)

    for x in range(0, len(lat_longs), batch_limit):
        batch.append(gmaps.distance_matrix(lat_longs[x:x + batch_limit], destination, ode=mode,
                                            language=language, units=units,
                                            traffic_model=TRAFFIC_MODEL))
    x = 0

    # Only care about origin_addresses and rows
    # disrgard destination_addresses and status
    selected_keys = ['origin_addresses', 'rows']
    filtered_batch = list()
    for each in batch:
        filtered_batch.append({key: each[key] for key in selected_keys if key in each})
    
    count = -1   # used to map back to addresses in the case of an error with API results
    for row in filtered_batch:
        row = pd.DataFrame.from_dict(row)
        for each in row.itertuples():
            count += 1
            if each.rows['elements'][0]['status'] != "ZERO_RESULTS":
                town = each.origin_addresses.split(', ')[1:-1]
                town = ' '.join(town)
                distance = float(each.rows['elements'][0]['distance']['text'].split(" ")[0])
                if distance < max_range:
                    # Add distance value to existing town Data
                    zip_code = town.split(" ")[-1]
                    new_df = town_data[town_data["zip"] == zip_code]
                    new_df = new_df.assign(distance = distance)
                    towns_in_range = pd.concat([towns_in_range,new_df])

            else:
                print("  ERROR with {}".format(addresses[count]))

    file_name = os.path.join(DATA_DIR, "town_data_" + str(max_range) + "mi.xlsx")
    towns_in_range.to_excel(file_name, index=False)
    
    print("Saved results to {}".format(file_name))

    return towns_in_range


def get_zip_data(states=None, include_county=False):
    """
    Reads zip code info from the zip database file defined by ZIP_DATA_FILE.
    Filters for STANDARD zip codes since the PO BOX and UNIQUE types are not
    relevant for this project.

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

    # Rename columns for easier reading in output
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
        ].copy()  # Use .copy() to avoid SettingWithCopyWarning

    # Drop columns no longer needed
    zip_data = zip_data.drop(columns=['type', 'decommissioned'])

    # Remove rows with missing CRITICAL data (Zip, Town, State only)
    before_dropna = len(zip_data)

    # Log rows with missing critical data before dropping
    missing_data = zip_data[
        zip_data['Zip'].isna() |
        zip_data['Town'].isna() |
        zip_data['State'].isna()
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
                f"Lat={row.get('Lat', 'N/A')}, "
                f"Long={row.get('Long', 'N/A')}"
            )

    # Drop rows with missing critical data
    zip_data = zip_data.dropna(subset=['Zip', 'Town', 'State'])
    dropped = before_dropna - len(zip_data)

    if dropped > 0:
        logger.warning(
            f"Dropped {dropped} rows with missing critical data "
            f"(Zip, Town, or State)"
        )

    # Log rows with missing Lat/Long (informational only)
    missing_coords = zip_data[
        zip_data['Lat'].isna() | zip_data['Long'].isna()
        ]
    if len(missing_coords) > 0:
        logger.info(
            f"{len(missing_coords)} rows missing Lat/Long coordinates "
            f"(will use address-based API calls)"
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


def get_zips_within_range(destination, zip_data, max_range):
    """
    Interrogates Google Maps API and returns list of zip codes within
    specified range of destination.

    Args:
        destination (str): Destination address
        zip_data (pd.DataFrame): DataFrame with Zip, Town, State,
                                 Lat, Long columns
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

    # Check API budget before making calls
    month_str = datetime.now().strftime('%Y-%m')
    current_usage = 0

    if os.path.exists(API_MONTHLY_COUNTER):
        try:
            with open(API_MONTHLY_COUNTER, "r") as f:
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
    elements_processed = 0  # Tracks billable elements (origins × destinations)
    requests_made = 0  # Tracks number of API requests made

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
                # Still update usage counter with what we've processed
                break

            elif response_status != 'OK':
                logger.error(
                    f"Google API response error: {response_status}"
                )
                # Log the error message if available
                if 'error_message' in response:
                    logger.error(
                        f"Error message: {response['error_message']}"
                    )
                # Count elements even if request failed (still billed)
                elements_processed += len(chunk)
                continue  # Skip this chunk but continue with others

            elements_processed += len(chunk)

            # Process each row in the response
            for idx, element in enumerate(response['rows']):
                status = element['elements'][0]['status']

                if status == 'OK':
                    # Convert meters to miles and round to 2 decimal places
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

        # Specific exception handling
        except googlemaps.exceptions.ApiError as e:
            logger.error(f"Google API error: {e}")
            # Count elements even if failed (may still be billed)
            elements_processed += len(chunk)
            continue  # Skip this chunk
        except googlemaps.exceptions.TransportError as e:
            logger.error(f"Network/transport error: {e}")
            continue  # Skip this chunk, don't count elements
        except googlemaps.exceptions.Timeout as e:
            logger.error(f"Timeout error: {e}")
            continue  # Skip this chunk, don't count elements
        except KeyError as e:
            logger.error(
                f"Unexpected response structure: Missing key {e}"
            )
            elements_processed += len(chunk)
            continue  # Skip this chunk
        except Exception as e:
            logger.error(
                f"Unexpected error: {type(e).__name__}: {e}"
            )
            continue  # Skip this chunk, don't count elements

    # Update usage tracking with actual elements processed
    new_total_usage = current_usage + elements_processed
    try:
        with open(API_MONTHLY_COUNTER, "w") as f:
            f.write(f"{month_str},{new_total_usage}")
        logger.info(
            f"API usage summary - Requests made: {requests_made}, "
            f"Elements processed: {elements_processed}, "
            f"Monthly total: {new_total_usage:,} / 20,000"
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

    # Return list of addresses within range
    logger.info(
        f"Returning {len(zips_in_range)} addresses within range"
    )
    return zips_in_range


# ------------ Old Functions

""" 
Appends the given DataFrame with the master workbook and names the worksheet the given sheetName 
"""
# def populateMaster(fileName, df):
#     for sheetName, data in df.items():
#         print("            Adding", sheetName, "to", fileName)
#         if os.path.isfile(fileName):
#             with pd.ExcelWriter(fileName, engine='openpyxl', mode="a", if_sheet_exists="replace") as writer:
#                 data.to_excel(writer, sheet_name=sheetName, index=True)
#         else:
#             writer = pd.ExcelWriter(fileName, engine='odf')
#             data.to_excel(writer, sheet_name=sheetName, index=False)
#             writer.save()


"""
Utility function to convert string of hours and minutes into minutes.
For example, string of 1 hour 3 min will return 63
duration string passed in is expected to be in 1 of the following formats
# hour # min
# hour
# min
"""
# def convertToMin(duration):
#     min = 0
#     fields = duration.split(' ')
#
#     """ fields has hour and min """
#     if len(fields) == 4:
#         min = int(fields[0]) * 60 + int(fields[2])
#     elif len(fields) == 2:
#         if "hour" in fields[1]:
#             min = int(fields[0]) * 60
#         elif "min" in fields[1]:
#             min = int(fields[0])
#         else:
#             "Encountered unknown format"
#     return min


"""
Exporting Data from the profiles.doe.mass.edu site does not save Data as
true Excel files. This mehtod will save the Data as an xls file so it 
can be used by libraries such as openpyxl and xlrd.
"""
# def convertToXLS(fileName, fileLocation, index=None, header=None, skiprows=None):
#     """ Convert to true xls file """
#     dfs = pd.read_html(os.path.join(fileLocation, fileName), index_col=index, skiprows=skiprows, header=header,
#                        thousands=None, )[-1]
#     writer = pd.ExcelWriter(os.path.join(fileLocation, fileName), engine="openpyxl")
#     dfs.to_excel(writer, "Sheet1")
#     writer.save()
# def setProxy(type='http'):
#     print("Turning on", type, "proxy")
#     proxy_on = True
#     proxy = urllib.ProxyHandler({type: 'localhost:8080'})
#     opener = urllib.build_opener(proxy)
#     urllib.install_opener(opener)


# def setCurrDir():
#     user = pwd.getpwuid(os.getuid())[0]
#
#     if platform.system() == "Darwin":
#         os.chdir("/Users/"+user+"/workspace/house_hunt/")
#         print "Changed directory to /Users/"+user+"/workspace/house_hunt/"
#     elif platform.system() == "Windows":
#         os.chdir("c:\\Users\\"+user+"\\workspace\\house_hunt\\")
#         print "Changed directory to c:\\Users\\"+user+"\\workspace\\house_hunt\\"

'''
Restrict score to no greater then maxScore and no less than MIN_SCORE
'''
# def normalizeScore(score):
#     if score > MAX_SCORE:
#         score = MAX_SCORE
#     elif score < MIN_SCORE:
#         score = MIN_SCORE
#     return score


