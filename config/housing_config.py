# ========================================
# HOUSING DATA COLLECTION PARAMETERS
# ========================================
HOUSING_DATA_SOURCE = 'redfin'  # Primary: 'redfin', Fallback: 'hud'
USE_FBI_CRIME_DATA = True      # Toggle to swap between FBI baseline and standard Crime Data
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
PROPERTY_TYPES = ['All']
