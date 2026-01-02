"""
Created on 18 June 2025

@author: AD23883
@todo:

"""
import os
import datetime
import holidays
import logging

# Set this to logging.DEBUG to see everything, or logging.INFO for a clean output
LOG_LEVEL = logging.DEBUG

MAX_SCORE = 10
MIN_SCORE = -10
MEDIAN_SCORE = 0

# Extension used when saving Excel files
EXT = '.xlsx'

# seconds from 1 Jan 1970 to 2 May 2016 07:00 EST
EPOCH = datetime.datetime(1970,1,1,0,0,0)
DEPARTURE_TIME = 1462186800

WORK_ADDR = '244 Wood St. Lexington, MA'
US_HOLIDAYS = holidays.country_holidays('US')

# Location of different data directories
BASE_DIR = os.path.join(os.sep, "Users", "aedwa", "workspace", "house_hunt")
DATA_DIR = os.path.join(BASE_DIR, 'data')
HOUSE_DATA = os.path.join(BASE_DIR, DATA_DIR, 'house')
SCHOOL_DATA = os.path.join(BASE_DIR, DATA_DIR, 'school')
COMMUTE_DATA_DIR = os.path.join(BASE_DIR, DATA_DIR, 'commute')
TOWN_DATA = os.path.join(BASE_DIR, DATA_DIR, 'town')
API_KEY_FILE = os.path.join(BASE_DIR, DATA_DIR, 'googleapi')

# Location of different files
DATA_FILE = 'test-zip_code_database.csv'
HISTORICAL_STATS_FILE = os.path.join(COMMUTE_DATA_DIR, "historical_commute_avg.csv")
API_USAGE_TRACKING_FILE = os.path.join(DATA_DIR, "monthly_API_usage_counter.txt")

# Google API values
KEY_LOC = DATA_DIR
KEY_FILE = "google_api_key"
GCP_PROJECT_ID = "house-hunt-project" # Found on your GCP Dashboard
GCP_MONITOR_KEY = os.path.join(DATA_DIR, "monitor-key.json")
CHUNK_SIZE = 25

# Commute Specific values
MORNING_TIMES = ['07:00']
AFTERNOON_TIMES = ['17:00']
TRAFFIC_MODEL = 'best_guess'
AVOID_TOLLS = ''
MODE = 'driving'
LANGUAGE = 'en'
UNITS = 'imperial'

MAX_RANGE = 50

