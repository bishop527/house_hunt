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
# GENERAL CONFIGURATION
# ========================================
# LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
# Tier selection strategy
AUTO_TIER_SELECTION = False  # If True, automatically choose optimal tier
USE_TRAFFIC = False           # Used when AUTO_TIER_SELECTION = False, Set to True for Advanced tier (with traffic data)
TRAFFIC_MODEL = 'best_guess'  # Used when USE_TRAFFIC=True
AVOID = None  # Options: None, 'highways', 'tolls'
API_MONTHLY_LIMIT_BASIC = 10000  # Basic tier (no traffic)
API_MONTHLY_LIMIT_ADVANCED = 5000  # Advanced tier (with traffic)
API_MONTHLY_LIMIT = API_MONTHLY_LIMIT_BASIC  # Current project limit

# ========================================
# Main Data Directory and Subdirectories
# ========================================
# Use location of this file to determine root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
# HOUSING_LOOKUP_FILE = os.path.join(PROCESSED_DIR, "housing_lookup.csv")

# ========================================
# DATA FILES - RESULTS
# ========================================
COMMUTE_STATS_FILE = os.path.join(RESULTS_DIR, "commute_stats.csv")
HOUSING_STATS_FILE = os.path.join(RESULTS_DIR, "housing_stats.csv")
API_TIER_TRACKING_FILE = os.path.join(LOGS_DIR, "monthly_API_usage_by_tier.txt")
SCORED_LOCATIONS_FILE = os.path.join(RESULTS_DIR, "scored_locations.csv")
SCORE_REPORT_FILE = os.path.join(RESULTS_DIR, "score_report.html")

# ========================================
# LOGS
# ========================================
APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")
COMMUTE_LOG_FILE = os.path.join(LOGS_DIR, 'commute.log')
HOUSING_LOG_FILE = os.path.join(LOGS_DIR, 'housing.log')
SCORE_LOG_FILE = os.path.join(LOGS_DIR, 'score.log')

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

# ========================================
# API RATE LIMITING & BUDGET
# ========================================
RATE_LIMIT_WAIT_SECONDS = 2  # Wait time when hitting rate limits
MAX_API_RETRIES = 3  # Maximum retry attempts for failed requests
MAX_ACCEPTABLE_DISCREPANCY = 183  # Elements between local/Google count

# ========================================
# COMMUTE DATA COLLECTION PARAMETERS
# ========================================
# Work Location
WORK_ADDR = "123 Main St. Anytown, MA 00000"

# Geographic Scope
TARGET_STATES = ['MA', 'RI', 'NH']
MAX_RANGE = 40  # Maximum distance in miles from work

# Collection Schedule
MORNING_TIMES = ['07:00']  # Morning collection times
AFTERNOON_TIMES = ['17:00']  # Afternoon collection times
NOON_HOUR = 17 # 12PM EST/EDT = 17:00 UTC (EST) or 16:00 UTC (EDT)

# Data Grouping
# LOCATION_GROUPING = 'zip'
LOCATION_GROUPING = 'town'

# ========================================
# HOUSING DATA COLLECTION PARAMETERS
# ========================================
# Data Sources
HOUSING_DATA_SOURCE = 'redfin'  # Primary: 'redfin', Fallback: 'hud'
PROPERTY_TAX_FILE = os.path.join(RAW_DIR, 'property_tax_rates.csv')
DEFAULT_MA_TAX_RATE = 12.1  # Default rate if town not found (per $1000)
DEFAULT_RI_TAX_RATE = 12.1  # Default rate if town not found (per $1000)
DEFAULT_NH_TAX_RATE = 17.6  # Default rate if town not found (per $1000)

# Redfin Configuration
REDFIN_DOWNLOAD_URL = (
    'https://redfin-public-data.s3.us-west-2.amazonaws.com/'
    'redfin_market_tracker/zip_code_market_tracker.tsv000.gz'
)
REDFIN_DATA_MAX_AGE_DAYS = 30  # Refresh if older than this

# HUD Fair Market Rent API (backup/supplementary)
HUD_FMR_API_URL = 'https://www.huduser.gov/hudapi/public/fmr/listcounties'
HUD_FMR_YEAR = '2025'  # Update annually

MIN_SAMPLE_SIZE = 1  # Minimum homes sold
PROPERTY_TYPES = ['Single Family', 'Condo', 'Townhouse'] # Property Type Filters

# SCORE MODULE CONSTANTS
# ========================================
SCORE_CONFIG_FILE = os.path.join(DATA_DIR, 'score_config.json')

DEFAULT_COMMUTE_WEIGHT = 0.60
DEFAULT_HOUSING_WEIGHT = 0.40

TIER_THRESHOLDS = {
    'A+': 95, 'A': 90, 'A-': 85,
    'B+': 80, 'B': 75, 'B-': 70,
    'C+': 65, 'C': 60, 'C-': 55,
    'D': 50, 'F': 0
}