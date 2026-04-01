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
LOG_LEVEL = logging.DEBUG
# LOG_LEVEL = logging.INFO

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
# TODO: Does this belong in constants?
for folder in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR, LOGS_DIR]:
    os.makedirs(folder, exist_ok=True)

# ========================================
# DATA FILES - RAW
# ========================================
# ZIP_DATA_FILE = os.path.join(RAW_DIR, 'small-zip_code_database.csv')
ZIP_DATA_FILE = os.path.join(RAW_DIR, 'zip_code_database.csv')
REDFIN_DATA_FILE = os.path.join(RAW_DIR, 'reduced-redfin_market_data.csv')
CRIME_DATA_FILE = os.path.join(RAW_DIR, 'MA-Crime_Data-2025.csv')
POPULATION_DATA_FILE = os.path.join(RAW_DIR, 'MA-Town_Population-2024.csv')

# ========================================
# DATA FILES - PROCESSED
# ========================================
# HOUSING_LOOKUP_FILE = os.path.join(PROCESSED_DIR, "housing_lookup.csv")
CRIME_SCORES_FILE = os.path.join(PROCESSED_DIR, "crime_scores_by_town.csv")

# ========================================
# DATA FILES - RESULTS
# ========================================
# TODO: look into renaming COMMUTE_STATS_FILE since there are now 2 work addresses
COMMUTE_STATS_FILE = os.path.join(RESULTS_DIR, "commute_stats.csv")
HOUSING_STATS_FILE = os.path.join(RESULTS_DIR, "housing_stats.csv")
API_TIER_TRACKING_FILE = os.path.join(LOGS_DIR, "monthly_API_usage_by_tier.txt")
SCORED_LOCATIONS_FILE = os.path.join(RESULTS_DIR, "scored_locations.csv")
SCORE_REPORT_FILE = os.path.join(RESULTS_DIR, "score_report.html")
WORK2_DISTANCES_FILE = os.path.join(RESULTS_DIR, "work2_distances.csv")

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
# Work Address Configuration
WORK_ADDRESSES_FILE = "work_addresses.txt"
WORK_ADDRESSES_PATH = os.path.join(DATA_DIR, WORK_ADDRESSES_FILE)

# TODO: Does this belong in constants?
def _load_work_addresses():
    """
    Load work addresses from secure file.
    
    Expected format in work_addresses.txt:
    WORK_ADDR1=123 Main St. City, State 12345
    WORK_ADDR2=456 Oak Ave. Town, State 67890
    
    Returns:
        dict: {'WORK_ADDR1': str, 'WORK_ADDR2': str}
    """
    addresses = {}
    
    if not os.path.exists(WORK_ADDRESSES_PATH):
        # Fall back to hardcoded addresses for backward compatibility
        return {
            'WORK_ADDR1': "123 Main St. Anytown, MA 00000",
            'WORK_ADDR2': "200 Chauncy St. Mansfield, MA 02048"
        }
    
    try:
        with open(WORK_ADDRESSES_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    addresses[key.strip()] = value.strip()
        
        return addresses
    except Exception as e:
        print(f"Error loading work addresses: {e}")
        # Fall back to hardcoded addresses
        return {
            'WORK_ADDR1': "123 Main St. Anytown, MA 00000",
            'WORK_ADDR2': "200 Chauncy St. Mansfield, MA 02048"
        }

# Load addresses
_work_addresses = _load_work_addresses()
WORK_ADDR1 = _work_addresses.get('WORK_ADDR1', "WORK_ADDRESS_1_NOT_SET")
WORK_ADDR2 = _work_addresses.get('WORK_ADDR2', "WORK_ADDRESS_2_NOT_SET")
ENABLE_SECOND_WORK_ADDRESS = True  # Set to True to enable second work address functionality


# Geographic Scope
TARGET_STATES = ['MA', 'RI', 'NH']

STATE_ABBR_TO_NAME = {
    'AK': 'Alaska', 'AL': 'Alabama', 'AR': 'Arkansas', 'AZ': 'Arizona', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DC': 'District of Columbia', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'IA': 'Iowa', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana',
    'MA': 'Massachusetts', 'MD': 'Maryland', 'ME': 'Maine', 'MI': 'Michigan', 'MN': 'Minnesota',
    'MO': 'Missouri', 'MS': 'Mississippi', 'MT': 'Montana', 'NC': 'North Carolina', 'ND': 'North Dakota',
    'NE': 'Nebraska', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NV': 'Nevada',
    'NY': 'New York', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
    'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
    'TX': 'Texas', 'UT': 'Utah', 'VA': 'Virginia', 'VT': 'Vermont', 'WA': 'Washington',
    'WI': 'Wisconsin', 'WV': 'West Virginia', 'WY': 'Wyoming'
}

# TODO: Rename MAX_RANGE to WORK1_MAX_RANGE
MAX_RANGE = 40  # Maximum distance in miles from Work Address 1
WORK2_MAX_RANGE = 40

# Legacy Collection Schedule - currently scheduled using Github actions
MORNING_TIMES = ['07:00']  # Morning collection times
AFTERNOON_TIMES = ['17:00']  # Afternoon collection times
NOON_HOUR = 17 # 12PM EST/EDT = 17:00 UTC (EST) or 16:00 UTC (EDT)

# Data Grouping
# TODO: Add description of what these are used for
# LOCATION_GROUPING = 'zip'
LOCATION_GROUPING = 'town'

# ========================================
# HOUSING DATA COLLECTION PARAMETERS
# ========================================
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
# Property Type Filter - select 1 or more of the following options
# Single Family
# Condo
# Townhouse
# All (will use all residential property types)
# PROPERTY_TYPES = ['Single Family']
# PROPERTY_TYPES = ['Condo']
# PROPERTY_TYPES = ['Townhouse']
PROPERTY_TYPES = ['All']

# ========================================
# SCORE MODULE CONSTANTS
# ========================================
SCORE_CONFIG_FILE = os.path.join(DATA_DIR, 'score_config.json')

TIER_THRESHOLDS = {
    'A+': 95, 'A': 90, 'A-': 85,
    'B+': 80, 'B': 75, 'B-': 70,
    'C+': 65, 'C': 60, 'C-': 55,
    'D': 50, 'F': 0
}

# TODO: Rename to MA_CRIME_SEVERITY_WEIGHTS
CRIME_SEVERITY_WEIGHTS = {
    # Massachusetts Crime Categories
    'Murder and Nonnegligent Manslaughter': 5,
    'Aggravated Assault': 5,
    'Robbery': 5,
    'Statutory Rape': 5,
    'Rape': 5,
    'Sodomy': 5,
    'Criminal Sexual Contact': 5,
    'Incest': 5,
    'Human Trafficking, Commercial Sex Acts': 5,
    'Human Trafficking, Involuntary Servitude': 5,
    'Negligent Manslaughter': 5,
    'Kidnapping/Abduction': 5,

    'Burglary/Breaking & Entering': 3,
    'Motor Vehicle Theft': 3,
    'Simple Assault': 3,
    'Arson': 3,
    'Weapon Law Violations': 3,
    'Animal Cruelty': 3,
    'Purse-snatching': 3,
    #'Assisting or Promoting Prostitution': 3,
    #'Embezzlement': 3,
    #'Wire Fraud': 3,
    #'Intimidation': 3,
    #'Extortion/Blackmail': 3,

    'Driving Under the Influence': 1,
    'Disorderly Conduct': 1,
    'Drug/Narcotic Violations': 1,
    'Trespass of Real Property': 1,
    'Stolen Property Offenses': 1,
    'Counterfeiting/Forgery': 1,
    'Credit Card/Automatic Teller Fraud': 1,
    'All Other Larceny': 1,
    'Destruction/Damage/Vandalism of Property': 1,    
    'Theft From Building': 1,
    'Theft From Motor Vehicle': 1,
    'Theft of Motor Vehicle Parts/Accessories': 1,
    'Pocket-picking': 1,
    'Drug Equipment Violations': 1,
    'Impersonation': 1,
    #'All Other Offenses': 1,
    #'False Pretenses/Swindle/Confidence Game': 1,
    #'Family Offenses (Nonviolent)': 1,
    #'Liquor Law Violations': 1,
    #'Pornography/Obscene Material': 1,
    #'Shoplifting': 1,
    #'Identity Theft': 1,
    #'Purchasing Prostitution': 1,
    #'Prostitution': 1,
    #'Curfew/Loitering/Vagrancy Violations': 1,
    #'Operating/Promoting/Assisting Gambling': 1,
    #'Welfare Fraud': 1,
}
