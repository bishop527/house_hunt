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


'''
Extract relevant Data zip code database CSV file and return zip_data dataframe
Rename primary_city field to town

zip_data fields:
- zip
- type
- primary_city
- state
- latitude
- longitude
'''
def get_zip_data():
    """Reads the master ZIP database from Data/Raw/"""
    if not os.path.exists(ZIP_DATA_FILE):
        logger.critical(f"Source file not found: {ZIP_DATA_FILE}")
        sys.exit(1)

    logger.info(f"Parsing ZIP database: {ZIP_DATA_FILE}")
    try:
        df = pd.read_csv(ZIP_DATA_FILE, header=0,
                         usecols=['zip', 'type', 'primary_city', 'state', 'latitude', 'longitude'],
                         dtype={'zip': str, 'type': str, 'primary_city': str, 'state': str,
                                'latitude': str, 'longitude': str})

        df = df.rename(columns={
            'primary_city': 'Town',
            'zip': 'Zip',
            'state': 'State',
            'latitude': 'Lat',
            'longitude': 'Long'
        })

        # Filtering logic
        zip_data = df[df['State'].isin(['MA', 'RI', 'NH'])]
        zip_data = zip_data[zip_data['type'] == "STANDARD"]

        logger.info(f"Loaded {len(zip_data)} standard ZIPs for MA, RI, and NH.")
        return zip_data
    except Exception as e:
        logger.error(f"Error parsing ZIP data: {e}")
        sys.exit(1)


'''
Interrogate Google Maps API to return list of zip codes within a given range from origin to destination
max_range in miles
Orgins in the Street, Town, Zip format
zip_data fields:
- zip
- type
- town
- state
'''
def get_zips_within_range(destination, zip_data, max_range):
    """Interrogates Google Maps and saves results to Data/Processed/"""
    api_key = get_google_api_key()

    if PROXY_ON:
        logger.info("Initializing Google Maps client with Proxy settings.")
        gmaps = googlemaps.Client(key=api_key, requests_kwargs={
            'proxies': {'https': 'http://localhost:8080'}})
    else:
        gmaps = googlemaps.Client(key=api_key)

    addresses = [f"{r.Town}, {r.State} {r.Zip}" for r in zip_data.itertuples()]
    zips_in_range = []
    results_list = []

    logger.info(f"Checking range for {len(addresses)} locations against {destination} (Max: {max_range} miles)")

    for i in range(0, len(addresses), CHUNK_SIZE):
        chunk = addresses[i: i + CHUNK_SIZE]
        try:
            response = gmaps.distance_matrix(origins=chunk, destinations=destination,
                                             mode=MODE, units=UNITS)

            for idx, element in enumerate(response['rows']):
                status = element['elements'][0]['status']
                if status == 'OK':
                    dist_miles = element['elements'][0]['distance']['value'] / 1609.34
                    if dist_miles <= max_range:
                        zips_in_range.append(chunk[idx])
                        results_list.append({
                            'Full_Address': chunk[idx],
                            'Distance_Miles': round(dist_miles, 2)
                        })
                else:
                    logger.warning(f"Google API element error for {chunk[idx]}: {status}")
        except Exception as e:
            logger.error(f"Error processing chunk starting at index {i}: {e}")

    if results_list:
        output_df = pd.DataFrame(results_list)
        output_path = os.path.join(PROCESSED_DIR, f"towns_within_{max_range}mi.csv")
        output_df.to_csv(output_path, index=False)
        logger.info(f"Range check complete. Saved {len(results_list)} ZIPs to {output_path}")
    else:
        logger.warning("No ZIPs found within the specified range.")

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


