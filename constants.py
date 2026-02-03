"""
Configuration constants for House Hunt project.

Created: 18 June 2025
Updated: 30 Jan 2026

@author: AD23883
"""
import os
import logging
import holidays

# ========================================
# PATHS AND DIRECTORIES
# ========================================
# Use location of this file to determine root directory
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

# ========================================
# DATA FILES - RAW
# ========================================
# ZIP_DATA_FILE = os.path.join(RAW_DIR, 'small-zip_code_database.csv')
ZIP_DATA_FILE = os.path.join(RAW_DIR, 'zip_code_database.csv')
REDFIN_DATA_FILE = os.path.join(RAW_DIR, 'reduced-redfin_market_data.csv')

# ========================================
# DATA FILES - PROCESSED
# ========================================
HOUSING_LOOKUP_FILE = os.path.join(PROCESSED_DIR, "housing_lookup.csv")

# ========================================
# DATA FILES - RESULTS
# ========================================
COMMUTE_STATS_FILE = os.path.join(RESULTS_DIR, "commute_stats.csv")
HOUSING_STATS_FILE = os.path.join(RESULTS_DIR, "historical_housing_stats.csv")
API_MONTHLY_COUNTER_FILE = os.path.join(RESULTS_DIR, "monthly_API_usage_counter.txt")

# ========================================
# DATA FILES - LOGS
# ========================================
APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")

# ========================================
# LOGGING CONFIGURATION
# ========================================
LOG_LEVEL = logging.DEBUG

# ========================================
# GENERAL CONFIGURATION
# ========================================
US_HOLIDAYS = holidays.country_holidays('US')
PROXY_ON = False
PROXY = 'http://localhost:8080'

# ========================================
# UNIT CONVERSIONS
# ========================================
METERS_PER_MILE = 1609.34
SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7

# ========================================
# GOOGLE MAPS API CONFIGURATION
# ========================================
# API Key Location
KEY_LOC = DATA_DIR
KEY_FILE = "google_api_key"

# GCP Monitoring
GCP_PROJECT_ID = "house-hunt-project"
GCP_MONITOR_KEY = os.path.join(DATA_DIR, "monitor-key.json")

# Request Parameters
CHUNK_SIZE = 25  # Addresses per API request
MODE = 'driving'
LANGUAGE = 'en'
UNITS = 'imperial'

# Route Preferences (can only use 1 at a time due to library bug)
AVOID = 'highways'  # Options: None, 'highways', 'tolls'

# Traffic Configuration
USE_TRAFFIC = False  # Set to True for Advanced tier (with traffic data)
TRAFFIC_MODEL = 'best_guess'  # Used when USE_TRAFFIC=True

# ========================================
# API RATE LIMITING & BUDGET
# ========================================
# Monthly Limits (free tier)
API_MONTHLY_LIMIT_BASIC = 10000  # Basic tier (no traffic)
API_MONTHLY_LIMIT_ADVANCED = 5000  # Advanced tier (with traffic)
API_MONTHLY_LIMIT = 13000  # Current project limit

# Rate Limiting
RATE_LIMIT_WAIT_SECONDS = 2  # Wait time when hitting rate limits
MAX_API_RETRIES = 3  # Maximum retry attempts for failed requests

# Usage Validation
MAX_ACCEPTABLE_DISCREPANCY = 100  # Elements between local/Google count

# ========================================
# COMMUTE COLLECTION PARAMETERS
# ========================================
# Work Location
WORK_ADDR = "123 Main St. Anytown, MA 00000"

# Geographic Scope
TARGET_STATES = ['MA', 'RI', 'NH']
MAX_RANGE = 40  # Maximum distance in miles from work

# Collection Schedule
MORNING_TIMES = ['07:00']  # Morning collection times
AFTERNOON_TIMES = ['17:00']  # Afternoon collection times
NOON_HOUR = 12

# Data Grouping
# LOCATION_GROUPING = 'zip'
LOCATION_GROUPING = 'town'

# ========================================
# HOUSING DATA PARAMETERS
# ========================================
# Data Sources
HOUSING_DATA_SOURCE = 'redfin'  # Primary: 'redfin', Fallback: 'hud'

# Redfin Configuration
REDFIN_DOWNLOAD_URL = (
    'https://redfin-public-data.s3.us-west-2.amazonaws.com/'
    'redfin_market_tracker/zip_code_market_tracker.tsv000.gz'
)
REDFIN_DATA_MAX_AGE_DAYS = 30  # Refresh if older than this

# HUD Fair Market Rent API (backup/supplementary)
HUD_FMR_API_URL = 'https://www.huduser.gov/hudapi/public/fmr/listcounties'
HUD_FMR_YEAR = '2024'  # Update annually

# Data Quality Thresholds
MIN_SAMPLE_SIZE = 5  # Minimum homes sold to consider data reliable

# Property Type Filters
PROPERTY_TYPES = ['Single Family', 'Condo', 'Townhouse']

# ========================================
# BACKWARD COMPATIBILITY
# ========================================
# Alias for old constant name
API_MONTHLY_COUNTER = API_MONTHLY_COUNTER_FILE