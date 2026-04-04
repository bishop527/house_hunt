import os

# ========================================
# Main Data Directory and Subdirectories
# ========================================
# Use location of this file to determine root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'Data')
RAW_DIR = os.path.join(DATA_DIR, 'Raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'Processed')
RESULTS_DIR = os.path.join(DATA_DIR, 'Results')
LOGS_DIR = os.path.join(DATA_DIR, 'Logs')

# ========================================
# DATA FILES - RAW
# ========================================
ZIP_DATA_FILE = os.path.join(RAW_DIR, 'zip_code_database.csv')
REDFIN_DATA_FILE = os.path.join(RAW_DIR, 'reduced-redfin_market_data.csv')
CRIME_DATA_FILE = os.path.join(RAW_DIR, 'MA-Crime_Data-2025.csv')
FBI_CRIME_DATA_FILE = os.path.join(RAW_DIR, 'FBI-Crime_Data.csv')
POPULATION_DATA_FILE = os.path.join(RAW_DIR, 'MA-Town_Population-2024.csv')
PROPERTY_TAX_FILE = os.path.join(RAW_DIR, 'property_tax_rates.csv')

# ========================================
# DATA FILES - PROCESSED
# ========================================
CRIME_SCORES_FILE = os.path.join(PROCESSED_DIR, "crime_scores_by_town.csv")
FBI_CRIME_SCORES_FILE = os.path.join(PROCESSED_DIR, "fbi_crime_scores_by_town.csv")
RANGE_LOOKUP_FILE = os.path.join(PROCESSED_DIR, "locations_within_range.csv")

# ========================================
# DATA FILES - RESULTS
# ========================================
WORK1_COMMUTE_STATS_FILE = os.path.join(RESULTS_DIR, "work1_commute_stats.csv")
HOUSING_STATS_FILE = os.path.join(RESULTS_DIR, "housing_stats.csv")
SCORED_LOCATIONS_FILE = os.path.join(RESULTS_DIR, "scored_locations.csv")
SCORE_REPORT_FILE = os.path.join(RESULTS_DIR, "score_report.html")
WORK2_COMMUTE_STATS_FILE = os.path.join(RESULTS_DIR, "work2_commute_stats.csv")

# ========================================
# LOGS
# ========================================
API_TIER_TRACKING_FILE = os.path.join(LOGS_DIR, "monthly_API_usage_by_tier.txt")
APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")
COMMUTE_LOG_FILE = os.path.join(LOGS_DIR, 'commute.log')
HOUSING_LOG_FILE = os.path.join(LOGS_DIR, 'housing.log')
SCORE_LOG_FILE = os.path.join(LOGS_DIR, 'score.log')

# ========================================
# CONFIGURATION FILES
# ========================================
SCORE_CONFIG_FILE = os.path.join(DATA_DIR, 'score_config.json')
