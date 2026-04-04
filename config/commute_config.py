import os
from .paths import DATA_DIR

# ========================================
# API Key / Configuration Files
# ========================================
KEY_LOC = DATA_DIR
KEY_FILE = "google_api_key"
GCP_MONITOR_KEY = os.path.join(DATA_DIR, "monitor-key.json")
WORK_ADDRESSES_FILE = "work_addresses.txt"
WORK_ADDRESSES_PATH = os.path.join(DATA_DIR, WORK_ADDRESSES_FILE)

# ========================================
# Request Parameters
# ========================================
CHUNK_SIZE = 25  # Addresses per API request
MODE = 'driving'
LANGUAGE = 'en'
UNITS = 'imperial'
TRAFFIC_MODEL = 'best_guess'
AVOID = None  # Options: None, 'highways', 'tolls'

# ========================================
# COMMUTE DATA COLLECTION PARAMETERS
# ========================================
WORK1_MAX_RANGE = 40  # Maximum distance in miles from Work Address 1
WORK2_MAX_RANGE = 40

# Legacy Collection Schedule - currently scheduled using Github actions
MORNING_TIMES = ['07:00']  # Morning collection times
AFTERNOON_TIMES = ['17:00']  # Afternoon collection times
NOON_HOUR = 17 # 12PM EST/EDT = 17:00 UTC (EST) or 16:00 UTC (EDT)

# Data Grouping
LOCATION_GROUPING = 'town'
