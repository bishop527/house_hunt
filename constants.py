"""
Configuration constants for House Hunt project.
Bridge module that re-exports constants from specialized modules for backward compatibility.

Created: 18 June 2025
Updated: 04 April 2026 (Final Reorganization & Lazy Loading)
"""
import holidays

# Re-export from specialized modules
from config.paths import *
from config.app_config import *
from config.scoring_config import *
from config.housing_config import *
from config.commute_config import *

# ========================================
# UNIVERSAL CONSTANTS
# ========================================
US_HOLIDAYS = holidays.country_holidays('US')
TARGET_STATES = ['MA', 'RI', 'NH']

METERS_PER_MILE = 1609.34
SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7

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

# ========================================
# DYNAMIC LOADING (Lazy)
# ========================================
def __getattr__(name):
    """
    Handle lazy loading of WORK_ADDR1 and WORK_ADDR2.
    Ensures that file I/O only happens when these variables are actually accessed.
    Delegates actual implementation to environments.py.
    """
    if name in ('WORK_ADDR1', 'WORK_ADDR2'):
        try:
            from environments import get_work_address
            # WORK_ADDRESSES_PATH is imported from config.commute_config via wildcard above
            return get_work_address(name, WORK_ADDRESSES_PATH)
        except Exception:
            return f"{name}_NOT_SET"
            
    raise AttributeError(f"module {__name__} has no attribute {name}")


# ========================================
# WILDCARD IMPORT SUPPORT
# ========================================
# Since WORK_ADDR1/2 are dynamic, we must define __all__ to ensure 
# "from constants import *" picks them up correctly.
__all__ = [
    name for name in dir() if not name.startswith('_') 
] + ['WORK_ADDR1', 'WORK_ADDR2']
