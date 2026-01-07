"""
Created on 18 June 2025
Updated 2 Jan 2026

@author: AD23883
@todo:

"""
import os
import logging
import holidays

# 1. Root Directory of the Project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Main Data Directory
DATA_DIR = os.path.join(BASE_DIR, 'Data')

# 3. Data Tier Subdirectories
RAW_DIR = os.path.join(DATA_DIR, 'Raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'Processed')
RESULTS_DIR = os.path.join(DATA_DIR, 'Results')

# Automatic Folder Creation
for folder in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR]:
    os.makedirs(folder, exist_ok=True)

# 4. Global Logging & Calendar Configuration
LOG_LEVEL = logging.DEBUG
US_HOLIDAYS = holidays.country_holidays('US')
PROXY_ON = False
PROXY = 'http://localhost:8080'

# 5. Data File Paths (Source of Truth)
ZIP_DATA_FILE = os.path.join(RAW_DIR, 'test-zip_code_database.csv')

# 6. Google API Values
KEY_LOC = DATA_DIR
KEY_FILE = "google_api_key"
GCP_PROJECT_ID = "house-hunt-project"
GCP_MONITOR_KEY = os.path.join(DATA_DIR, "monitor-key.json")
CHUNK_SIZE = 25

# API Rate Limiting
RATE_LIMIT_WAIT_SECONDS = 2  # Wait time when hitting rate limits
MAX_API_RETRIES = 3           # Maximum retry attempts for failed requests

# Unit Conversions
METERS_PER_MILE = 1609.34     # Conversion factor for distance calculations

# 7. Commute Specific Values
WORK_ADDR = "123 Main St. Anytown, MA 00000"
TARGET_STATES = ['MA', 'RI', 'NH']  # Add this line

MORNING_TIMES = ['07:00']
AFTERNOON_TIMES = ['17:00']
TRAFFIC_MODEL = 'best_guess'
AVOID_TOLLS = ''
MODE = 'driving'
LANGUAGE = 'en'
UNITS = 'imperial'

MAX_RANGE = 50

# 8. Processed & Results Paths
HOUSING_LOOKUP_FILE = os.path.join(PROCESSED_DIR, "housing_lookup.csv")
HISTORICAL_STATS_FILE = os.path.join(RESULTS_DIR, "historical_commute_stats.csv")
# API_USAGE_TRACKING_FILE = os.path.join(RESULTS_DIR, "usage_tracking.log")
API_MONTHLY_COUNTER = os.path.join(RESULTS_DIR, "monthly_API_usage_counter.txt")
APP_LOG_FILE = os.path.join(RESULTS_DIR, "app.log")

# ---- Older constants ----

# Location of different Data directories
# BASE_DIR = os.path.join(os.sep, "Users", "aedwa", "workspace", "house_hunt")
# HOUSE_DATA = os.path.join(BASE_DIR, DATA_DIR, 'House')
# SCHOOL_DATA = os.path.join(BASE_DIR, DATA_DIR, 'School')
# COMMUTE_DATA_DIR = os.path.join(BASE_DIR, DATA_DIR, 'Commute')
# TOWN_DATA = os.path.join(BASE_DIR, DATA_DIR, 'town')

# MAX_SCORE = 10
# MIN_SCORE = -10
# MEDIAN_SCORE = 0
#
# # Extension used when saving Excel files
# EXT = '.xlsx'
#
# # seconds from 1 Jan 1970 to 2 May 2016 07:00 EST
# EPOCH = datetime.datetime(1970,1,1,0,0,0)
# DEPARTURE_TIME = 1462186800