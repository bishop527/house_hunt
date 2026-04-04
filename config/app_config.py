import logging

# ========================================
# GENERAL CONFIGURATION
# ========================================
LOG_LEVEL = logging.INFO

ENABLE_SECOND_WORK_ADDRESS = True  # Set to True to enable second work address functionality

# Tier selection strategy
AUTO_TIER_SELECTION = True  # If True, automatically choose optimal tier
USE_TRAFFIC = False           # Used when AUTO_TIER_SELECTION = False
API_MONTHLY_LIMIT_BASIC = 10000  # Basic tier (no traffic)
API_MONTHLY_LIMIT_ADVANCED = 5000  # Advanced tier (with traffic)
API_MONTHLY_LIMIT = API_MONTHLY_LIMIT_BASIC  # Current project limit

# ========================================
# API RATE LIMITING & BUDGET
# ========================================
RATE_LIMIT_WAIT_SECONDS = 2  # Wait time when hitting rate limits
MAX_API_RETRIES = 3  # Maximum retry attempts for failed requests
MAX_ACCEPTABLE_DISCREPANCY = 183  # Elements between local/Google count
