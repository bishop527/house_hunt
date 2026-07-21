# Fixing Scoring Module NameError

- **Cascade ID**: `3144db2d-8772-4471-a42c-7cde3be7b84e`
- **Steps**: 65
- **Status**: CASCADE_RUN_STATUS_IDLE
- **Created**: 2026-04-02T22:58:24.282174300Z
- **Last Modified**: 2026-04-02T23:00:15.734667800Z
- **Workspace**: file:///c:/Users/aedwa/workspace/house_hunt
- **Exported**: 2026-07-11 00:23:48

---

## 🧑 User  `2026-04-02T22:58:24`
running the housing and score modules results in the following errors
PS C:\Users\aedwa\workspace\house_hunt> & C:/Users/aedwa/workspace/house_hunt/.venv/Scripts/Activate.ps1
(.venv) PS C:\Users\aedwa\workspace\house_hunt>  & 'c:\Users\aedwa\workspace\house_hunt\.venv\Scripts\python.exe' 'c:\Users\aedwa\.antigravity\extensions\ms-pythonace\house_hunt/main.py' '--commute'
c:\Users\aedwa\workspace\house_hunt\.venv\Lib\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.6.3) or chardet (7.2.0)/charset_normalizer (3.4.6) doesn't match a supported version!
  warnings.warn(
22:55:36 Thu UTC [INFO] STARTED: House Hunt Execution
22:55:36 Thu UTC [INFO] STARTED: Commute Data Collection
Processing locations: 100%|██████████████████| 32/32 [00:05<00:00,  5.57chunk/s]
Fetching afternoon commute times: 100%|████████| 4/4 [00:00<00:00,  4.43chunk/s]
22:55:45 Thu UTC [INFO] COMPLETED: Commute Data Collection
22:55:45 Thu UTC [INFO] EXECUTION SUMMARY:
22:55:45 Thu UTC [INFO]   COMMUTE: SUCCESS
22:55:45 Thu UTC [INFO] COMPLETED: House Hunt | 1/1 modules successful
(.venv) PS C:\Users\aedwa\workspace\house_hunt>  c:; cd 'c:\Users\aedwa\workspace\house_hunt'; & 'c:\Users\aedwa\workspace\house_hunt\.venv\Scripts\python.exe' 'c:\Users\aedwa\.antigravity\extensions\ms-python.debugpy-2025.18.0-win32-x64\bundled\libs\debugpy\launcher' '52384' '--' 'C:\Users\aedwa\workspace\house_hunt/main.py' '--housing' '--force-refresh' '--score' 
c:\Users\aedwa\workspace\house_hunt\.venv\Lib\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.6.3) or chardet (7.2.0)/charset_normalizer (3.4.6) doesn't match a supported version!
  warnings.warn(
22:57:17 Thu UTC [INFO] STARTED: House Hunt Execution
22:57:17 Thu UTC [INFO] === Starting execution for Property Type: Single Family ===
22:57:17 Thu UTC [INFO] STARTED: Housing Data Collection (Single Family)
22:57:17 Thu UTC [INFO] Force refresh enabled: Will clear historical data for queried zips
Collecting housing data: 100%|███████████████| 186/186 [00:02<00:00, 72.89zip/s]
22:57:20 Thu UTC [INFO] COMPLETED: Housing Data Collection (Single Family)
22:57:20 Thu UTC [INFO] STARTED: Scoring (Single Family)
22:57:20 Thu UTC [ERROR] Scoring failed: name 'WORK_ADDR1' is not defined
Traceback (most recent call last):
  File "C:\Users\aedwa\workspace\house_hunt/main.py", line 74, in run_scoring
    success, scored_file, filtered_df, config_out = calculate_scores(property_types=property_types)
                                                    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aedwa\workspace\house_hunt\Score\calculate_scores.py", line 980, in calculate_scores
    if not scorer.load_data():
           ~~~~~~~~~~~~~~~~^^
  File "C:\Users\aedwa\workspace\house_hunt\Score\calculate_scores.py", line 302, in load_data
    self.housing_data = self._derive_housing_from_redfin()
                        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\Users\aedwa\workspace\house_hunt\Score\calculate_scores.py", line 105, in _derive_housing_from_redfin
    WORK_ADDR1,
    ^^^^^^^^^^
NameError: name 'WORK_ADDR1' is not defined
22:57:20 Thu UTC [INFO] === Starting execution for Property Type: Condo ===
22:57:20 Thu UTC [INFO] STARTED: Housing Data Collection (Condo)
22:57:20 Thu UTC [INFO] Force refresh enabled: Will clear historical data for queried zips
Collecting housing data: 100%|███████████████| 186/186 [00:02<00:00, 83.54zip/s]
22:57:23 Thu UTC [INFO] COMPLETED: Housing Data Collection (Condo)
22:57:23 Thu UTC [INFO] STARTED: Scoring (Condo)
22:57:23 Thu UTC [ERROR] Scoring failed: name 'WORK_ADDR1' is not defined
Traceback (most recent call last):
  File "C:\Users\aedwa\workspace\house_hunt/main.py", line 74, in run_scoring
    success, scored_file, filtered_df, config_out = calculate_scores(property_types=property_types)
                                                    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aedwa\workspace\house_hunt\Score\calculate_scores.py", line 980, in calculate_scores
    if not scorer.load_data():
           ~~~~~~~~~~~~~~~~^^
  File "C:\Users\aedwa\workspace\house_hunt\Score\calculate_scores.py", line 302, in load_data
    self.housing_data = self._derive_housing_from_redfin()
                        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\Users\aedwa\workspace\house_hunt\Score\calculate_scores.py", line 105, in _derive_housing_from_redfin
    WORK_ADDR1,
    ^^^^^^^^^^
NameError: name 'WORK_ADDR1' is not defined
22:57:23 Thu UTC [INFO] === Starting execution for Property Type: Townhouse ===
22:57:23 Thu UTC [INFO] STARTED: Housing Data Collection (Townhouse)
22:57:23 Thu UTC [INFO] Force refresh enabled: Will clear historical data for queried zips
Collecting housing data: 100%|███████████████| 186/186 [00:02<00:00, 87.53zip/s]
22:57:26 Thu UTC [INFO] COMPLETED: Housing Data Collection (Townhouse)
22:57:26 Thu UTC [INFO] STARTED: Scoring (Townhouse)
22:57:26 Thu UTC [ERROR] Scoring failed: name 'WORK_ADDR1' is not defined
Traceback (most recent call last):
  File "C:\Users\aedwa\workspace\house_hunt/main.py", line 74, in run_scoring
    success, scored_file, filtered_df, config_out = calculate_scores(property_types=property_types)
                                                    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aedwa\workspace\house_hunt\Score\calculate_scores.py", line 980, in calculate_scores
    if not scorer.load_data():
           ~~~~~~~~~~~~~~~~^^
  File "C:\Users\aedwa\workspace\house_hunt\Score\calculate_scores.py", line 302, in load_data
    self.housing_data = self._derive_housing_from_redfin()
                        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\Users\aedwa\workspace\house_hunt\Score\calculate_scores.py", line 105, in _derive_housing_from_redfin
    WORK_ADDR1,
    ^^^^^^^^^^
NameError: name 'WORK_ADDR1' is not defined
22:57:26 Thu UTC [INFO] EXECUTION SUMMARY:
22:57:26 Thu UTC [INFO]   HOUSING: SUCCESS
22:57:26 Thu UTC [INFO]   SCORE: FAILED
22:57:26 Thu UTC [INFO] COMPLETED: House Hunt | 1/2 modules successful

### 🔧 Tool: `list_dir`  `2026-04-02T22:58:27`
`[List Directory]`

### 🔧 Tool: `view_file`  `2026-04-02T22:58:28`
`file:///c:/Users/aedwa/workspace/house_hunt/Score/calculate_scores.py` (1045 lines, 44136 bytes)

### 🔧 Tool: `view_file`  `2026-04-02T22:58:28`
`file:///c:/Users/aedwa/workspace/house_hunt/constants.py` (258 lines, 9831 bytes)

### 🔧 Tool: `view_file`  `2026-04-02T22:58:45`
`file:///c:/Users/aedwa/workspace/house_hunt/Score/calculate_scores.py` (1045 lines, 44136 bytes)

### 🔧 Tool: `code_edit`  `2026-04-02T22:58:57`
[Code Edit] file:///c:/Users/aedwa/workspace/house_hunt/Score/calculate_scores.py
Added missing WORK_ADDR1 import to calculate_scores.py.

```diff
 """
 Calculate and rank housing locations based on commute and housing data.
 
 This module:
 1. Loads commute and housing statistics
 2. Applies user-configurable scoring algorithms
 3. Generates ranked results with tier classifications
 4. Outputs scored locations CSV
 
 Updated:
 - Replaced wildcard import with explicit constants
 - Fixed merge to handle LOCATION_GROUPING='town' (all zips per town now included)
 - Fixed _score_housing_tax to use Tax_Rate_Per_1000 column (was reading
   non-existent 'Tax_Rate' column, causing all tax scores to return neutral 25)
 - Added Price_Score, Tax_Score, Tax_Rate_Per_1000, Est_Monthly_Tax,
   Price_Trend, Min_Monthly_Price, Max_Monthly_Price to result dict
   (required by generate_report.py modal)
 - Switched to logging_config.setup_logger for consistency with other modules
 """
 import os
 import sys
 import json
 import pandas as pd
 from constants import (
     LOG_LEVEL, APP_LOG_FILE, SCORE_LOG_FILE,
     SCORE_CONFIG_FILE, WORK1_COMMUTE_STATS_FILE, HOUSING_STATS_FILE, CRIME_SCORES_FILE,
     SCORED_LOCATIONS_FILE, LOCATION_GROUPING, RESULTS_DIR,
     REDFIN_DATA_FILE, PROCESSED_DIR, WORK1_MAX_RANGE, PROPERTY_TYPES,
     ENABLE_SECOND_WORK_ADDRESS, WORK2_DISTANCES_FILE, WORK2_MAX_RANGE,
-    TIER_THRESHOLDS
+    TIER_THRESHOLDS, WORK_ADDR1
 )
 from utils import load_csv_with_zip
 from logging_config import setup_logger
 
 logger = setup_logger(__name__, log_file=SCORE_LOG_FILE)
 
 # Scoring constants (avoid magic numbers)
 MAX_SCORE = 100
 MIN_SCORE = 0
 NEUTRAL_SCORE = 50
 
 # Commute scoring constants
 COMMUTE_SCORE_MAX = 100
 WORST_COMMUTE_TIME_MULTIPLIER = 2.0  # Worst case is 2x max acceptable
 
 # Housing scoring constants
 HOUSING_SCORE_MAX = 100
 PRICE_SCORE_MAX = 50
 TAX_SCORE_MAX = 50
 
 class LocationScorer:
     """
     Scores housing locations based on commute and housing data.
 
     Uses configurable weights and preferences to calculate scores
     for each location, then ranks and assigns tiers.
     """
 
     def __init__(self, config_file=None, property_types=None):
         """
         Initialize scorer with configuration.
 
         Args:
             config_file (str): Path to JSON config file. If None,
                              uses default config.
             property_types (list, optional): Property types to use for execution.
         """
         self.filtered_locations = None
         self.config = self._load_config(config_file)
         self._validate_weights()
         self.commute_data = None
         self.housing_data = None
         self.scored_locations = None
         self.prev_ranks = {}
         self.property_types = property_types if property_types is not None else PROPERTY_TYPES
         self.work2_data = pd.DataFrame()
         self.housing_filtered = pd.DataFrame()
         
         # Compute dynamic filename for scored locations based on PROPERTY_TYPES
         _prop_type
... (truncated, 45197 chars total)
```

### 🔧 Tool: `view_file`  `2026-04-02T22:59:01`
`file:///c:/Users/aedwa/workspace/house_hunt/main.py` (270 lines, 9753 bytes)

### 🔧 Tool: `view_file`  `2026-04-02T22:59:04`
`file:///c:/Users/aedwa/workspace/house_hunt/Housing/collect_housing_data.py` (897 lines, 33333 bytes)

### 🔧 Tool: `view_file`  `2026-04-02T22:59:07`
`file:///c:/Users/aedwa/workspace/house_hunt/Commute/collect_commute_data.py` (803 lines, 27973 bytes)

### 🔧 Tool: `view_file`  `2026-04-02T22:59:10`
`file:///c:/Users/aedwa/workspace/house_hunt/Score/generate_report.py` (1283 lines, 51345 bytes)

### 🔧 Tool: `run_command`  `2026-04-02T22:59:13`
```bash
python main.py --housing --force-refresh --score --limit 5
```
* (in `c:\Users\aedwa\workspace\house_hunt`) → exit 1*

<details><summary>📤 Output</summary>

```
s.
PS C:\Users\aedwa\workspace\house_hunt> cd 'c:\Users\aedwa\workspace\house_hunt'
PS C:\Users\aedwa\workspace\house_hunt> Remove-Item -Path "Data/Processed/towns_within_40mi.csv", "Data/Processed/zips_within_40mi.csv" -Force -ErrorAction SilentlyContinue
PS C:\Users\aedwa\workspace\house_hunt> ^C
PS C:\Users\aedwa\workspace\house_hunt> cd 'c:\Users\aedwa\workspace\house_hunt'
PS C:\Users\aedwa\workspace\house_hunt> python main.py --housing --force-refresh --score --limit 5

Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases.
```

</details>

### 🔧 Tool: `command_status`  `2026-04-02T22:59:17`
`[Check Command Status]`

### 🔧 Tool: `list_dir`  `2026-04-02T22:59:20`
`[List Directory]`

### 🔧 Tool: `run_command`  `2026-04-02T22:59:28`
```bash
.venv\Scripts\python.exe main.py --housing --force-refresh --score --limit 5
```
* (in `c:\Users\aedwa\workspace\house_hunt`) → exit 0*

<details><summary>📤 Output</summary>

```
C:\Users\aedwa\workspace\house_hunt\.venv\Lib\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.6.







                                                                                                                             se.csv...v...t (7.2.0)/charset_normalizer (3.4.6) doesn't match a supported version!
22:59:41 Thu UTC [INFO] COMPLETED: Scoring (Townhouse)ily)
22:59:41 Thu UTC [INFO] EXECUTION SUMMARY:tion for Property Type: Townhouse ===
22:59:41 Thu UTC [INFO]   HOUSING: SUCCESSata Collection (Townhouse)ngle Family ===
22:59:41 Thu UTC [INFO]   SCORE: SUCCESSabled: Will clear historical data for queried zips
22:59:41 Thu UTC [INFO] COMPLETED: House Hunt | 2/2 modules successful3.51zip/s]eried zips
22:59:38 Thu UTC [INFO] COMPLETED: Housing Data Collection (Townhouse)8.06zip/s]
```

</details>

### 🔧 Tool: `command_status`  `2026-04-02T22:59:32`
`[Check Command Status]`

### 🔧 Tool: `code_edit`  `2026-04-02T22:59:49`
[Code Edit] file:///C:/Users/aedwa/.gemini/antigravity/brain/3144db2d-8772-4471-a42c-7cde3be7b84e/walkthrough.md
Created walkthrough for the NameError fix.

```diff
+# Walkthrough - Fixed NameError in Scoring Module
+
+The scoring module was failing with a `NameError: name 'WORK_ADDR1' is not defined` after a previous refactor of constants. This occurred specifically during the "re-derivation" step when running with `--score`.
+
+## Changes Made
+
+### Scoring Module
+#### [MODIFY] [calculate_scores.py](file:///c:/Users/aedwa/workspace/house_hunt/Score/calculate_scores.py)
+- Added `WORK_ADDR1` to the explicit import list from `constants.py`.
+- Verified that other constants like `WORK2_MAX_RANGE` and `ENABLE_SECOND_WORK_ADDRESS` were already correctly imported.
+
+## Verification Results
+
+### Automated Tests
+I ran the main execution script with local housing and scoring modules enabled:
+```powershell
+.venv\Scripts\python.exe main.py --housing --force-refresh --score --limit 5
+```
+
+**Result:**
+- **HOUSING**: SUCCESS
+- **SCORE**: SUCCESS
+- **Execution Summary**: 2/2 modules successful
+
+The `NameError` is resolved, and the scoring pipeline now correctly re-derives housing data from the local Redfin CSV when property types change.
+
```

## 🤖 Assistant  `2026-04-02T22:59:50`
The `NameError: name 'WORK_ADDR1' is not defined` in `Score/calculate_scores.py` has been resolved. This error was caused by a missing import after a recent refactor where wildcard imports were replaced with explicit constants in that file, but `WORK_ADDR1` was omitted from the list.

### Changes Made
- **[calculate_scores.py](file:///c:/Users/aedwa/workspace/house_hunt/Score/calculate_scores.py)**: Added `WORK_ADDR1` to the `constants` import list.
- Verified that other related constants (`WORK2_MAX_RANGE`, `ENABLE_SECOND_WORK_ADDRESS`, etc.) were already correctly imported.

### Verification Results
I verified the fix by running the sequence of modules that previously failed:
```powershell
.venv\Scripts\python.exe main.py --housing --force-refresh --score --limit 5
```
**Results:**
- **HOUSING**: SUCCESS
- **SCORE**: SUCCESS
- **Execution Summary**: 2/2 modules successful

The scoring module now correctly re-derives housing data from the local Redfin CSV when property types or work addresses are updated.

For a full summary of the changes, see the [walkthrough.md](file:///C:/Users/aedwa/.gemini/antigravity/brain/3144db2d-8772-4471-a42c-7cde3be7b84e/walkthrough.md).

*Model: `MODEL_PLACEHOLDER_M47` | Stop: `STOP_REASON_STOP_PATTERN`*
