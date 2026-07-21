# Fixing Scoring Module KeyErrors

- **Cascade ID**: `d3dd1e55-454d-437c-a10d-fec6c9568e36`
- **Steps**: 53
- **Status**: CASCADE_RUN_STATUS_IDLE
- **Created**: 2026-05-25T19:23:13.799344400Z
- **Last Modified**: 2026-05-25T19:24:25.161917800Z
- **Workspace**: file:///c:/Users/aedwa/workspace/house_hunt
- **Exported**: 2026-07-11 00:23:46

---

## 🧑 User  `2026-05-25T19:23:13`
=========================== short test summary info ===========================
FAILED Tests/Score/test_calculate_scores.py::test_calculate_commute_score - K...
FAILED Tests/Score/test_calculate_scores.py::test_score_all_locations - KeyEr...
FAILED Tests/Score/test_calculate_scores.py::test_score_all_locations_with_filters
FAILED Tests/Score/test_calculate_scores.py::test_save_results - KeyError: 'W...
FAILED Tests/Score/test_calculate_scores.py::test_get_summary_stats - KeyErro...
FAILED Tests/Score/test_calculate_scores.py::test_calculate_scores_main_function
FAILED Tests/test_utils.py::test_get_zips_within_range_cache_age_valid - Asse...
================== 7 failed, 104 passed, 1 warning in 4.25s ===================

### 🔧 Tool: `run_command`  `2026-05-25T19:23:17`
```bash
pytest Tests/Score/test_calculate_scores.py
```
* (in `c:\Users\aedwa\workspace\house_hunt`) → exit 1*

<details><summary>📤 Output</summary>

```
PS C:\Users\aedwa\workspace\house_hunt>
PS C:\Users\aedwa\workspace\house_hunt> ^C
PS C:\Users\aedwa\workspace\house_hunt> cd 'c:\Users\aedwa\workspace\house_hunt'
PS C:\Users\aedwa\workspace\house_hunt> pytest Tests/Score/test_calculate_scores.py
pytest: The term 'pytest' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
```

</details>

### 🔧 Tool: `command_status`  `2026-05-25T19:23:21`
`[Check Command Status]`

### 🔧 Tool: `run_command`  `2026-05-25T19:23:25`
```bash
python -m pytest Tests/Score/test_calculate_scores.py
```
* (in `c:\Users\aedwa\workspace\house_hunt`) → exit 1*

<details><summary>📤 Output</summary>

```
PS C:\Users\aedwa\workspace\house_hunt>
PS C:\Users\aedwa\workspace\house_hunt> ^C
PS C:\Users\aedwa\workspace\house_hunt> cd 'c:\Users\aedwa\workspace\house_hunt'
PS C:\Users\aedwa\workspace\house_hunt> pytest Tests/Score/test_calculate_scores.py
pytest: The term 'pytest' is not recognized as a name of a cmdlet, function, script file, or executable program.     
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
PS C:\Users\aedwa\workspace\house_hunt> cd 'c:\Users\aedwa\workspace\house_hunt'
PS C:\Users\aedwa\workspace\house_hunt> python -m pytest Tests/Score/test_calculate_scores.py
Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases.
```

</details>

### 🔧 Tool: `command_status`  `2026-05-25T19:23:29`
`[Check Command Status]`

### 🔧 Tool: `run_command`  `2026-05-25T19:23:31`
```bash
dir
```
* (in `c:\Users\aedwa\workspace\house_hunt`) → exit 0*

<details><summary>📤 Output</summary>

```

    Directory: C:\Users\aedwa\workspace\house_hunt

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----           5/25/2026  3:19 PM                __pycache__
d----           2/11/2026  8:54 PM                .github
d----           3/21/2026  9:37 AM                .idea
d----           1/13/2026 11:44 AM                .pytest_cache
d----           3/20/2026  7:01 PM                .venv
d----           3/30/2026  9:34 PM                .vscode
d----            4/4/2026  8:18 AM                Archive
d----            4/2/2026  9:05 AM                Artifacts
d----           5/22/2026  8:27 PM                Commute
d----            4/4/2026  1:17 PM                config
d----            4/4/2026  8:29 AM                Data
d----           5/22/2026  7:54 PM                docs
d----            4/2/2026  9:12 PM                Housing
d----           1/13/2026  8:55 PM                htmlcov
d----            4/2/2026  7:38 AM                Score
d----            4/2/2026 10:35 PM                Tests
-a---           1/17/2026  1:40 PM            117 .coveragearc
-a---            4/4/2026  8:55 AM            454 .env.example
-a---            4/2/2026 10:41 PM            560 .gitignore
-a---            4/4/2026  1:42 PM           2869 constants.py
-a---            4/4/2026  1:20 PM           1661 environments.py
-a---            4/4/2026  8:26 AM           4113 error_handlers.py
-a---           3/26/2026  7:54 PM            126 house_hunt.code-workspace
-a---            3/1/2026  4:32 PM           2781 logging_config.py
-a---           5/22/2026  8:27 PM           8231 main.py
-a---           1/17/2026  1:40 PM            228 pytest.ini
-a---            4/2/2026  6:16 PM             98 README.md
-a---            4/4/2026  9:00 AM            269 replace_text.txt
-a---           3/21/2026  9:06 AM           2116 requirements-all.txt
-a---           3/24/2026  7:20 PM            112 requirements.txt
-a---           5/25/2026  3:19 PM          34985 utils.py
```

</details>

### 🔧 Tool: `view_file`  `2026-05-25T19:23:36`
`file:///c:/Users/aedwa/workspace/house_hunt/Score/calculate_scores.py` (1136 lines, 48680 bytes)

### 🔧 Tool: `view_file`  `2026-05-25T19:23:40`
`file:///c:/Users/aedwa/workspace/house_hunt/Tests/Score/test_calculate_scores.py` (476 lines, 15631 bytes)

### 🔧 Tool: `view_file`  `2026-05-25T19:23:50`
`file:///c:/Users/aedwa/workspace/house_hunt/Score/calculate_scores.py` (1136 lines, 48680 bytes)

### 🔧 Tool: `view_file`  `2026-05-25T19:23:55`
`file:///c:/Users/aedwa/workspace/house_hunt/Tests/test_utils.py` (1110 lines, 38694 bytes)

### 🔧 Tool: `view_file`  `2026-05-25T19:24:00`
`file:///c:/Users/aedwa/workspace/house_hunt/Tests/test_utils.py` (1110 lines, 38694 bytes)

### 🔧 Tool: `view_file`  `2026-05-25T19:24:03`
`file:///c:/Users/aedwa/workspace/house_hunt/utils.py` (987 lines, 34985 bytes)

### 🔧 Tool: `view_file`  `2026-05-25T19:24:05`
`file:///c:/Users/aedwa/workspace/house_hunt/utils.py` (987 lines, 34985 bytes)

### 🔧 Tool: `code_edit`  `2026-05-25T19:24:21`
[Code Edit] file:///C:/Users/aedwa/.gemini/antigravity/brain/d3dd1e55-454d-437c-a10d-fec6c9568e36/implementation_plan.md
Create implementation plan to fix test failures.

```diff
+# Fix Test Failures in Scoring and Utils
+
+The project recently underwent a refactor for "Dual Work Address Symmetrical Pipeline", which introduced new column names (`Work1_Distance`, `Work1_Average_Time`, etc.) and new configuration structures. However, the unit tests and some parts of the scoring logic were not fully updated to handle these changes, leading to `KeyError` and `AssertionError`.
+
+## User Review Required
+
+> [!IMPORTANT]
+> The scoring logic now strictly expects `Work1_` and `Work2_` prefixed columns after data loading. I will update the tests to follow this pattern. I will also add backward compatibility for the configuration file structure where appropriate.
+
+## Proposed Changes
+
+### [Scoring Module](file:///c:/Users/aedwa/workspace/house_hunt/Score/calculate_scores.py)
+
+#### [MODIFY] [calculate_scores.py](file:///c:/Users/aedwa/workspace/house_hunt/Score/calculate_scores.py)
+- Update `calculate_commute_score` to handle cases where `Work1_` prefix might be missing (for unit test compatibility) or ensure it consistently uses the new names.
+- Update `score_all_locations` to use the correct renamed columns (`Work1_Distance`, `Work1_Average_Time`) in filters and final result dictionary.
+- Update `_score_commute_time` to fall back to `commute_preferences` if `work_address_N` is not found in the config.
+
+### [Scoring Tests](file:///c:/Users/aedwa/workspace/house_hunt/Tests/Score/test_calculate_scores.py)
+
+#### [MODIFY] [test_calculate_scores.py](file:///c:/Users/aedwa/workspace/house_hunt/Tests/Score/test_calculate_scores.py)
+- Update `sample_commute_data` fixture (or individual tests) to use the new `Work1_` prefixed column names to match the expected state after `load_data()`.
+- Update `sample_config` to include `work_address_1` section to match the new scraper/scorer expectations.
+
+### [Utility Tests](file:///c:/Users/aedwa/workspace/house_hunt/Tests/test_utils.py)
+
+#### [MODIFY] [test_utils.py](file:///c:/Users/aedwa/workspace/house_hunt/Tests/test_utils.py)
+- Update `test_get_zips_within_range_cache_age_valid` and `test_get_zips_within_range_cache_age_expired` to use the new unified cache filename: `locations_within_range_30mi.csv`.
+
+## Open Questions
+
+None at this time.
+
+## Verification Plan
+
+### Automated Tests
+- Run `python -m pytest Tests/Score/test_calculate_scores.py`
+- Run `python -m pytest Tests/test_utils.py`
+- Run the full suite: `python -m pytest`
+
+### Manual Verification
+- None required as these are unit test fixes.
+
```

## 🤖 Assistant  `2026-05-25T19:24:21`
I've analyzed the test failures and identified that they were caused by the recent refactor to the "Dual Work Address Symmetrical Pipeline". Specifically, the scoring logic now expects `Work1_` and `Work2_` prefixed columns, which were not properly handled in the unit tests and some parts of the scoring logic itself. Additionally, the utility tests were using an outdated cache filename convention.

I have created an [implementation plan](file:///C:/Users/aedwa/.gemini/antigravity/brain/d3dd1e55-454d-437c-a10d-fec6c9568e36/implementation_plan.md) to address these issues.

Once you approve the plan, I will proceed with the fixes.

*Model: `MODEL_PLACEHOLDER_M20` | Stop: `STOP_REASON_STOP_PATTERN`*
