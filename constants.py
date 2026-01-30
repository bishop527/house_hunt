"""
Created on 18 June 2025
Updated 2 Jan 2026

@author: AD23883
@todo:

"""
import os
import logging
import holidays

# Use location of this file to determine root directory of the Project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Main Data Directory and Subdirectories
DATA_DIR = os.path.join(BASE_DIR, 'Data')
RAW_DIR = os.path.join(DATA_DIR, 'Raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'Processed')
RESULTS_DIR = os.path.join(DATA_DIR, 'Results')
LOGS_DIR = os.path.join(DATA_DIR, 'Logs')

# Automatic Data Folder Creation
for folder in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR, LOGS_DIR]:
    os.makedirs(folder, exist_ok=True)

# Data/Raw Files
ZIP_DATA_FILE = os.path.join(RAW_DIR, 'zip_code_database.csv')
# ZIP_DATA_FILE = os.path.join(RAW_DIR, 'small-zip_code_database.csv')

# Data/Processed Files
HOUSING_LOOKUP_FILE = os.path.join(PROCESSED_DIR, "housing_lookup.csv")

# Data/Results Files
COMMUTE_STATS_FILE = os.path.join(RESULTS_DIR, "commute_stats.csv")
API_MONTHLY_COUNTER = os.path.join(RESULTS_DIR, "monthly_API_usage_counter.txt")

# Data/Logs Files
APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")

# Global Configurations
LOG_LEVEL = logging.DEBUG
US_HOLIDAYS = holidays.country_holidays('US')
PROXY_ON = False
PROXY = 'http://localhost:8080'
METERS_PER_MILE = 1609.34


# COMMUTE MODULE CONSTANTS
# ========================================
# Google API Values
KEY_LOC = DATA_DIR
KEY_FILE = "google_api_key"
GCP_PROJECT_ID = "house-hunt-project"
GCP_MONITOR_KEY = os.path.join(DATA_DIR, "monitor-key.json")
CHUNK_SIZE = 25

# API Rate Limiting
RATE_LIMIT_WAIT_SECONDS = 2 # Wait time when hitting rate limits
MAX_API_RETRIES = 3         # Maximum retry attempts for failed requests
# API_MONTHLY_LIMIT = 5000    # Free tier monthly limit for Distance Matrix Advanced which is used to track live traffic
API_MONTHLY_LIMIT = 13000


# Commute Specific Values
WORK_ADDR = "123 Main St. Anytown, MA 00000"
TARGET_STATES = ['MA', 'RI', 'NH']

MORNING_TIMES = ['07:00']
AFTERNOON_TIMES = ['17:00']

USE_TRAFFIC = False             # Set to True when you want traffic data
TRAFFIC_MODEL = 'best_guess'    # use for advanced query that includes traffic

# Can only use 1 avoid at a time due to bug in python library
# AVOID = None
AVOID = 'highways'
# AVOID = 'tolls'

MODE = 'driving'
LANGUAGE = 'en'
UNITS = 'imperial'

MAX_RANGE = 40

# Group location data either by zip code or town name
# LOCATION_GROUPING = 'zip'
LOCATION_GROUPING = 'town'

# HOUSE MODULE CONSTANTS
# ========================================

# Housing Data Sources
HOUSING_DATA_SOURCE = 'redfin'  # Primary: 'redfin', Fallback: 'hud'

# Redfin Data Files (download from https://www.redfin.com/news/data-center/)
# REDFIN_DATA_FILE = os.path.join(RAW_DIR, 'redfin_market_data.csv')
REDFIN_DATA_FILE = os.path.join(RAW_DIR, 'reduced-redfin_market_data.csv')
REDFIN_DOWNLOAD_URL = 'https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/zip_code_market_tracker.tsv000.gz'

# HUD Fair Market Rent API (backup/supplementary)
HUD_FMR_API_URL = 'https://www.huduser.gov/hudapi/public/fmr/listcounties'
HUD_FMR_YEAR = '2024'  # Update annually

# Housing Results Files
HOUSING_STATS_FILE = os.path.join(RESULTS_DIR, "historical_housing_stats.csv")
HOUSING_LOOKUP_FILE = os.path.join(PROCESSED_DIR, "housing_lookup.csv")

# Housing Query Parameters
PROPERTY_TYPES = ['Single Family', 'Condo', 'Townhouse']  # Filter types
MIN_SAMPLE_SIZE = 5  # Minimum homes sold to consider data reliable

# ---- Older constants ----

# MAX_SCORE = 10
# MIN_SCORE = -10
# MEDIAN_SCORE = 0

# # seconds from 1 Jan 1970 to 2 May 2016 07:00 EST
# EPOCH = datetime.datetime(1970,1,1,0,0,0)
# DEPARTURE_TIME = 1462186800