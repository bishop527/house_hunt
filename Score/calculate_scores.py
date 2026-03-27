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
    SCORE_CONFIG_FILE, COMMUTE_STATS_FILE, HOUSING_STATS_FILE,
    SCORED_LOCATIONS_FILE, LOCATION_GROUPING, RESULTS_DIR,
    REDFIN_DATA_FILE, PROCESSED_DIR, MAX_RANGE, PROPERTY_TYPES
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
                             # e.g. 12.1 per $1k -> 1.21%


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
        self.commute_data = None
        self.housing_data = None
        self.scored_locations = None
        self.prev_ranks = {}
        self.property_types = property_types if property_types is not None else PROPERTY_TYPES
        
        # Compute dynamic filename for scored locations based on PROPERTY_TYPES
        _prop_type_suffix = "_".join(pt.replace(" ", "_") for pt in self.property_types) if self.property_types else "All"
        self.scored_locations_file = os.path.join(
            RESULTS_DIR, f"scored_locations-{_prop_type_suffix}.csv"
        )

    def _derive_housing_from_redfin(self):
        """
        Re-derive housing stats from the local Redfin CSV using the current
        PROPERTY_TYPES constant — no download required.

        Reads the zip-within-range cache to get the address list, then calls
        fetch_housing_data() which filters the local Redfin file by
        PROPERTY_TYPES and enriches each zip with property tax data.

        Returns:
            pd.DataFrame | None: Housing data in housing_stats column format,
                                 or None if the zip cache or Redfin file is missing.
        """
        # Import here to avoid circular imports at module level
        from Housing.collect_housing_data import fetch_housing_data

        zip_cache = os.path.join(PROCESSED_DIR, f"zips_within_{MAX_RANGE}mi.csv")
        if not os.path.exists(zip_cache):
            logger.warning(
                f"Zip cache not found ({zip_cache}). "
                f"Run --housing first to build it, then re-score."
            )
            return None

        try:
            addresses = pd.read_csv(zip_cache)['Full_Address'].tolist()
        except Exception as e:
            logger.warning(f"Failed to read zip cache: {e}")
            return None

        logger.info(
            f"Re-deriving housing data from local Redfin CSV "
            f"for {len(addresses)} zips | PROPERTY_TYPES={self.property_types}"
        )

        results, failed_zips = fetch_housing_data(addresses, property_types=self.property_types)
        if not results and not failed_zips:
            logger.warning("No housing results or filtered zips re-derived from Redfin.")
            return None

        # Convert failed_zips to a standardized DataFrame for scoring module
        if failed_zips:
            self.housing_filtered = pd.DataFrame(failed_zips)
            # Ensure columns match expected score_all_locations format
            if 'Zip' in self.housing_filtered.columns:
                self.housing_filtered['Zip'] = self.housing_filtered['Zip'].astype(str).str.zfill(5)
            logger.info(f"Captured {len(failed_zips)} zips missing {self.property_types} data via re-derivation")
        else:
            self.housing_filtered = pd.DataFrame()
        
        if not results:
            return None

        # Map raw result keys → housing_stats column names expected by scorer
        records = []
        for r in results:
            records.append({
                'Town':                r.get('town'),
                'State':               r.get('state'),
                'Zip':                 str(r.get('zip', '')).zfill(5),
                'Latest_Median_Sale':  r.get('median_sale_price'),
                'Latest_Median_List':  r.get('median_list_price'),
                'Latest_PPSF':         r.get('median_ppsf'),
                'Latest_Homes_Sold':   r.get('homes_sold'),
                'Latest_Inventory':    r.get('inventory'),
                'Tax_Rate_Per_1000':   r.get('tax_rate_per_1000'),
                'Estimated_Monthly_Tax': r.get('estimated_monthly_tax'),
                'Price_Trend':         r.get('price_trend'),
                'Min_Monthly_Price':   r.get('min_monthly_price'),
                'Max_Monthly_Price':   r.get('max_monthly_price'),
                'Avg_Monthly_Price':   r.get('avg_monthly_price'),
            })

        df = pd.DataFrame(records)
        df['Zip'] = df['Zip'].str.zfill(5)
        logger.info(
            f"Re-derived {len(df)} housing records from Redfin "
            f"(PROPERTY_TYPES={self.property_types})"
        )
        return df

    def _load_config(self, config_file):
        """
        Load scoring configuration from JSON file.

        Args:
            config_file (str): Path to JSON config file

        Returns:
            dict: Configuration dictionary

        Raises:
            SystemExit: If config file is missing or invalid
        """
        if config_file is None:
            config_file = SCORE_CONFIG_FILE

        if not os.path.exists(config_file):
            logger.error(f"Configuration file not found: {config_file}")
            logger.error(
                "Create a score_config.json file with your preferences."
            )
            logger.error("Scoring cannot continue without configuration.")
            sys.exit(1)

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded config from {config_file}")

            required_sections = [
                'weights', 'commute_preferences', 'housing_preferences'
            ]
            for section in required_sections:
                if section not in config:
                    logger.error(
                        f"Missing required section '{section}' in config file"
                    )
                    sys.exit(1)

            return config

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)

    def load_data(self):
        """
        Load commute and housing data from CSV files.

        Returns:
            bool: True if data loaded successfully
        """
        logger.info("Loading commute and housing data...")

        # Load previous ranks to calculate rank changes
        # Load previous ranks to calculate rank changes
        if os.path.exists(self.scored_locations_file):
            try:
                prev_df = pd.read_csv(self.scored_locations_file, dtype={'Zip': str})
                if 'Rank' in prev_df.columns and 'Zip' in prev_df.columns:
                    prev_df['Zip'] = prev_df['Zip'].astype(str).str.zfill(5)
                    self.prev_ranks = prev_df.set_index('Zip')['Rank'].to_dict()
                    logger.info(
                        f"Loaded previous ranks for {len(self.prev_ranks)} locations "
                        f"from {os.path.basename(self.scored_locations_file)}"
                    )
            except Exception as e:
                logger.error(f"Error loading previous scored locations: {e}")

        self.commute_data = load_csv_with_zip(COMMUTE_STATS_FILE)
        if self.commute_data.empty:
            logger.error(f"No commute data found at {COMMUTE_STATS_FILE}")
            return False
        logger.info(f"Loaded {len(self.commute_data)} commute records")

        # Re-derive housing from local Redfin CSV if available, so PROPERTY_TYPES
        # changes take effect immediately without re-running --housing.
        if os.path.exists(REDFIN_DATA_FILE):
            self.housing_data = self._derive_housing_from_redfin()
            if self.housing_data is None or self.housing_data.empty:
                logger.warning(
                    "Re-derivation from Redfin failed — "
                    "falling back to housing_stats.csv"
                )
                self.housing_data = load_csv_with_zip(HOUSING_STATS_FILE)
        else:
            logger.info(
                "Redfin data file not found — loading housing_stats.csv"
            )
            _prop_type_suffix = "_".join(pt.replace(" ", "_") for pt in self.property_types) if self.property_types else "All"
            housing_stats_file = HOUSING_STATS_FILE.replace(".csv", f"_{_prop_type_suffix}.csv")
            self.housing_data = load_csv_with_zip(housing_stats_file)

        if self.housing_data.empty:
            logger.error(f"No housing data found at {HOUSING_STATS_FILE}")
            return False
        logger.info(f"Loaded {len(self.housing_data)} housing records")

        # Load zips filtered out during housing collection (no property type data)
        _prop_type_suffix = "_".join(pt.replace(" ", "_") for pt in self.property_types) if self.property_types else "All"
        housing_filtered_file = os.path.join(RESULTS_DIR, f'housing_filtered_zips-{_prop_type_suffix}.csv')
        
        if os.path.exists(housing_filtered_file):
            try:
                housing_filtered_df = pd.read_csv(housing_filtered_file, dtype={'Zip': str})
                if 'Zip' in housing_filtered_df.columns:
                    housing_filtered_df['Zip'] = housing_filtered_df['Zip'].str.zfill(5)
                logger.info(f"Loaded {len(housing_filtered_df)} housing-filtered zips")
                self.housing_filtered = housing_filtered_df
            except Exception as e:
                logger.warning(f"Failed to load housing filtered zips: {e}")
                self.housing_filtered = pd.DataFrame()
        else:
            self.housing_filtered = pd.DataFrame()

        return True

    def _score_commute_time(self, avg_time):
        """
        Score commute time (0-100 points).

        Args:
            avg_time (float): Average commute time in minutes

        Returns:
            float: Score 0-100
        """
        prefs = self.config['commute_preferences']
        ideal = prefs['ideal_time_minutes']
        max_acceptable = prefs['max_acceptable_time']

        if avg_time <= ideal:
            return COMMUTE_SCORE_MAX
        elif avg_time <= max_acceptable:
            # Linear scale from 100 down to 50
            ratio = (avg_time - ideal) / (max_acceptable - ideal)
            return COMMUTE_SCORE_MAX - (ratio * (COMMUTE_SCORE_MAX / 2))
        else:
            # Linear scale from 50 down to 0
            behavior = self.config.get('scoring_behavior', {})
            multiplier = behavior.get('worst_commute_multiplier', 2.0)
            worst = max_acceptable * multiplier
            if avg_time >= worst:
                return MIN_SCORE
            ratio = (avg_time - max_acceptable) / (worst - max_acceptable)
            return (COMMUTE_SCORE_MAX / 2) - (ratio * (COMMUTE_SCORE_MAX / 2))

    def calculate_commute_score(self, row):
        """
        Calculate total commute score (0-100).

        Args:
            row (pd.Series): Merged data row

        Returns:
            dict: {'commute_score': float}
        """
        commute_score = self._score_commute_time(row['Average_Time'])
        return {'commute_score': round(commute_score, 1)}

    def _score_housing_price(self, price):
        """
        Score housing price (0-50 points).

        Uses exponential penalty for over-budget locations.

        Args:
            price (float): Median sale price

        Returns:
            float: Score 0-50
        """
        if pd.isna(price):
            return MIN_SCORE

        prefs = self.config['housing_preferences']
        budget_min   = prefs['budget_min']
        budget_max   = prefs['budget_max']
        budget_ideal = prefs['budget_ideal']

        bonus_points        = 5.0
        penalty_range       = 10.0
        max_score_over_budget = 35.0
        penalty_multiplier  = 100.0

        if price <= budget_ideal:
            if price <= budget_min:
                return PRICE_SCORE_MAX
            ratio = (budget_ideal - price) / (budget_ideal - budget_min)
            return (PRICE_SCORE_MAX - bonus_points) + (ratio * bonus_points)

        elif price <= budget_max:
            ratio = (price - budget_ideal) / (budget_max - budget_ideal)
            return (PRICE_SCORE_MAX - bonus_points) - (ratio * penalty_range)

        else:
            overage_ratio = (price - budget_max) / budget_max
            penalty = (overage_ratio ** 1.5) * penalty_multiplier
            return max(MIN_SCORE, max_score_over_budget - penalty)

    def _score_housing_tax(self, tax_rate):
        """
        Score property tax effective rate (0-50 points).

        Args:
            tax_rate (float): Effective tax rate per $1000.

        Returns:
            float: Score 0-50
        """
        if pd.isna(tax_rate):
            return NEUTRAL_SCORE / 2  # Neutral (25) if data missing

        prefs = self.config['housing_preferences']
        ideal          = prefs.get('ideal_tax_rate', 12.1)
        max_acceptable = prefs.get('max_acceptable_tax_rate', 20.0)

        if tax_rate <= ideal:
            return TAX_SCORE_MAX
        elif tax_rate <= max_acceptable:
            ratio = (tax_rate - ideal) / (max_acceptable - ideal)
            return TAX_SCORE_MAX - (ratio * 25.0)
        else:
            behavior = self.config.get('scoring_behavior', {})
            worst_tax = behavior.get('worst_tax_rate_per_1000', 30.0)
            if tax_rate >= worst_tax:
                return MIN_SCORE
            ratio = (tax_rate - max_acceptable) / (
                worst_tax - max_acceptable
            )
            return 25.0 - (ratio * 25.0)

    def _score_housing_ppsf(self, ppsf):
        """
        Score housing price per square foot (0-50 points).

        Args:
            ppsf (float): Price per square foot

        Returns:
            float: Score 0-50
        """
        if pd.isna(ppsf):
            return NEUTRAL_SCORE / 2  # Neutral (25) if data missing

        prefs = self.config['housing_preferences']
        ideal          = prefs.get('ideal_ppsf', 300)
        max_acceptable = prefs.get('max_acceptable_ppsf', 500)

        if ppsf <= ideal:
            return TAX_SCORE_MAX
        elif ppsf <= max_acceptable:
            ratio = (ppsf - ideal) / (max_acceptable - ideal)
            return TAX_SCORE_MAX - (ratio * 25.0)
        else:
            behavior = self.config.get('scoring_behavior', {})
            worst = behavior.get('worst_ppsf', 800.0)
            if ppsf >= worst:
                return MIN_SCORE
            ratio = (ppsf - max_acceptable) / (worst - max_acceptable)
            return 25.0 - (ratio * 25.0)

    def calculate_housing_score(self, row):
        """
        Calculate total housing score (0-100).

        Args:
            row (pd.Series): Merged data row

        Returns:
            dict: {
                'housing_score': float,
                'price_score':   float,
                'tax_score':     float
            }
        """
        price_score = self._score_housing_price(
            row.get('Latest_Median_Sale')
        )

        tax_score = self._score_housing_tax(row.get('Tax_Rate_Per_1000'))
        
        ppsf_score = self._score_housing_ppsf(row.get('Latest_PPSF'))

        prefs = self.config.get('housing_preferences', {})
        weights = prefs.get('housing_weights', {'price': 0.6, 'ppsf': 0.3, 'tax': 0.1})
        price_weight = weights.get('price', 0.6)
        ppsf_weight  = weights.get('ppsf', 0.3)
        tax_weight   = weights.get('tax', 0.1)

        weighted_price_score = price_score * price_weight * 2
        weighted_ppsf_score  = ppsf_score * ppsf_weight * 2
        weighted_tax_score   = tax_score * tax_weight * 2
        
        housing_score = weighted_price_score + weighted_ppsf_score + weighted_tax_score

        return {
            'housing_score': round(housing_score, 1),
            'price_score':   round(weighted_price_score, 1),
            'ppsf_score':    round(weighted_ppsf_score, 1),
            'tax_score':     round(weighted_tax_score, 1)
        }

    def _assign_tier(self, total_score):
        """
        Assign letter tier based on total score.

        Args:
            total_score (float): Total score 0-100

        Returns:
            str: Tier (A+, A, A-, B+, B, B-, C+, C, C-, D, F)
        """
        if total_score >= 95:  return 'A+'
        elif total_score >= 90: return 'A'
        elif total_score >= 85: return 'A-'
        elif total_score >= 80: return 'B+'
        elif total_score >= 75: return 'B'
        elif total_score >= 70: return 'B-'
        elif total_score >= 65: return 'C+'
        elif total_score >= 60: return 'C'
        elif total_score >= 55: return 'C-'
        elif total_score >= 50: return 'D'
        else:                   return 'F'

    def _merge_datasets(self):
        """
        Merge commute and housing datasets.

        When LOCATION_GROUPING='town', commute data holds one representative
        Zip per town. Merging on Zip would silently drop all other Zips for
        that town from the housing data. Instead we merge on Town+State so
        every housing Zip inherits that town's commute stats.

        When LOCATION_GROUPING='zip', each row is already a unique Zip so
        the standard Zip merge is correct.

        Returns:
            pd.DataFrame | None: Merged DataFrame, or None if empty
        """
        if LOCATION_GROUPING == 'town':
            # Drop the representative Zip from commute so housing Zip
            # comes through cleanly — one result row per housing Zip.
            commute_for_merge = self.commute_data.drop(
                columns=['Zip'], errors='ignore'
            )
            merged = pd.merge(
                commute_for_merge,
                self.housing_data,
                on=['Town', 'State'],
                how='inner',
                suffixes=('_commute', '_housing')
            )
            logger.info(
                f"Town-grouping merge on Town+State: "
                f"{len(self.commute_data)} commute towns x "
                f"{len(self.housing_data)} housing zips "
                f"-> {len(merged)} rows"
            )
        else:
            merged = pd.merge(
                self.commute_data,
                self.housing_data,
                on='Zip',
                how='inner',
                suffixes=('_commute', '_housing')
            )
            logger.info(
                f"Zip-grouping merge on Zip: {len(merged)} rows"
            )

        return merged if len(merged) > 0 else None

    @staticmethod
    def _resolve(row, *keys):
        """
        Return the first non-null value among the given keys in row.

        Used to handle suffixed column names after a merge.
        e.g. _resolve(row, 'Town_commute', 'Town_housing', 'Town')
        """
        for key in keys:
            val = row.get(key)
            if val is not None and not (
                isinstance(val, float) and pd.isna(val)
            ):
                return val
        return None

    def score_all_locations(self):
        """
        Score all locations and create ranked results.

        Returns:
            pd.DataFrame: Scored and ranked locations, or None on failure
        """
        if self.commute_data is None or self.housing_data is None:
            logger.error("Data not loaded. Call load_data() first.")
            return None

        logger.info("Scoring all locations...")

        merged = self._merge_datasets()
        if merged is None:
            logger.error("No matching records between datasets after merge.")
            return None

        # Apply filters
        filters = self.config.get('filters', {})

        filtered_rows = []

        if filters.get('max_commute_time'):
            max_time = filters['max_commute_time']
            mask = merged['Average_Time'] > max_time
            dropped = merged[mask].copy()
            dropped['Filter_Reason'] = dropped['Average_Time'].apply(
                lambda t: f"Commute > {max_time} min (actual: {t:.1f} min)"
            )
            filtered_rows.append(dropped)
            merged = merged[~mask]
            logger.info(
                f"Commute filter: removed {len(dropped)} locations "
                f"exceeding {filters['max_commute_time']} min"
            )

        if filters.get('max_price'):
            max_price = filters['max_price']
            mask = merged['Latest_Median_Sale'] > max_price
            dropped = merged[mask].copy()
            dropped['Filter_Reason'] = dropped['Latest_Median_Sale'].apply(
                lambda p: f"Price > ${max_price:,} (actual: ${int(p):,})"
                if pd.notna(p) else f"Price > ${max_price:,} (actual: N/A)"
            )
            filtered_rows.append(dropped)
            merged = merged[~mask]
            logger.info(
                f"Price filter: removed {len(dropped)} locations "
                f"exceeding ${filters['max_price']:,}"
            )

        if len(merged) == 0:
            logger.error("No locations remain after filtering.")
            return None

        # Combine filter-based exclusions with housing property type exclusions
        all_filtered = []

        if filtered_rows:
            filtered_combined = pd.concat(filtered_rows, ignore_index=True)
            # Resolve Town/State the same way as scored rows
            filtered_combined['Town'] = filtered_combined.apply(
                lambda r: self._resolve(r, 'Town', 'Town_commute', 'Town_housing'),
                axis=1
            )
            filtered_combined['State'] = filtered_combined.apply(
                lambda r: self._resolve(r, 'State', 'State_commute', 'State_housing'),
                axis=1
            )
            filtered_standardized = filtered_combined[[
                'Town', 'State', 'Zip', 'Filter_Reason',
                'Average_Time', 'Distance', 'Latest_Median_Sale',
                'Latest_PPSF', 'Tax_Rate_Per_1000'
            ]].rename(columns={
                'Average_Time': 'Avg_Commute_Min',
                'Distance': 'Distance_Miles',
                'Latest_Median_Sale': 'Median_Price',
                'Latest_PPSF': 'Price_Per_SqFt',
            })
            all_filtered.append(filtered_standardized)

        # Add housing-filtered zips (no property type data)
        if hasattr(self, 'housing_filtered') and not self.housing_filtered.empty:
            # These zips have commute data but no housing data
            housing_only_filtered = self.housing_filtered.copy()
            # Add empty columns to match the structure
            housing_only_filtered['Avg_Commute_Min'] = None
            housing_only_filtered['Distance_Miles'] = None
            housing_only_filtered['Median_Price'] = None
            housing_only_filtered['Price_Per_SqFt'] = None
            housing_only_filtered['Tax_Rate_Per_1000'] = None

            all_filtered.append(housing_only_filtered[[
                'Town', 'State', 'Zip', 'Filter_Reason',
                'Avg_Commute_Min', 'Distance_Miles', 'Median_Price',
                'Price_Per_SqFt', 'Tax_Rate_Per_1000'
            ]])

            logger.info(
                f"Added {len(housing_only_filtered)} zips filtered for missing property type data"
            )

        if all_filtered:
            self.filtered_locations = pd.concat(all_filtered, ignore_index=True)
        else:
            self.filtered_locations = pd.DataFrame()

        # Calculate scores
        weights = self.config['weights']
        results = []

        for _, row in merged.iterrows():
            commute_scores = self.calculate_commute_score(row)
            housing_scores = self.calculate_housing_score(row)

            total_score = (
                commute_scores['commute_score'] * weights['commute'] +
                housing_scores['housing_score'] * weights['housing']
            )

            tier = self._assign_tier(total_score)

            # Resolve Town/State — column names differ by merge mode
            town  = self._resolve(row, 'Town', 'Town_commute', 'Town_housing')
            state = self._resolve(row, 'State', 'State_commute', 'State_housing')

            result = {
                'Town':              town,
                'State':             state,
                'Zip':               row['Zip'],
                'Total_Score':       round(total_score, 1),
                'Tier':              tier,
                # Scores
                'Commute_Score':     commute_scores['commute_score'],
                'Housing_Score':     housing_scores['housing_score'],
                'Price_Score':       housing_scores['price_score'],
                'PPSF_Score':        housing_scores['ppsf_score'],
                'Tax_Score':         housing_scores['tax_score'],
                # Commute detail
                'Avg_Commute_Min':   row['Average_Time'],
                'Min_Commute_Min':   row['Min_Time'],
                'Max_Commute_Min':   row['Max_Time'],
                'Distance_Miles':    row['Distance'],
                'Commute_Runs':      self._resolve(
                                         row,
                                         'Total_Runs_commute',
                                         'Total_Runs'
                                     ),
                'Last_Updated':      self._resolve(
                                         row,
                                         'Last_Run_Date_commute',
                                         'Last_Run_Date'
                                     ),
                # Housing detail
                'Median_Price':      row.get('Latest_Median_Sale'),
                'Price_Per_SqFt':    row.get('Latest_PPSF'),
                'Homes_Sold':        row.get('Latest_Homes_Sold'),
                'Inventory':         row.get('Latest_Inventory'),
                'Tax_Rate_Per_1000': row.get('Tax_Rate_Per_1000'),
                'Est_Monthly_Tax':   row.get('Estimated_Monthly_Tax'),
                'Price_Trend':       row.get('Price_Trend'),
                'Min_Monthly_Price': row.get('Min_Monthly_Price'),
                'Max_Monthly_Price': row.get('Max_Monthly_Price'),
            }

            results.append(result)

        self.scored_locations = pd.DataFrame(results)

        # Sort by Total_Score descending, then Town ascending alphabetically for tie-breaking
        self.scored_locations = self.scored_locations.sort_values(
            ['Total_Score', 'Town'], ascending=[False, True]
        ).reset_index(drop=True)

        self.scored_locations.insert(
            0, 'Rank', range(1, len(self.scored_locations) + 1)
        )

        # Calculate Rank Change
        def get_rank_change(row):
            if row['Zip'] in self.prev_ranks:
                return self.prev_ranks[row['Zip']] - row['Rank']
            return 'New'
            
        self.scored_locations['Rank_Change'] = self.scored_locations.apply(get_rank_change, axis=1)

        logger.info(f"Scored {len(self.scored_locations)} locations")
        return self.scored_locations

    def save_results(self):
        """
        Save scored results to CSV.

        Returns:
            bool: True if successful
        """
        if self.scored_locations is None or len(self.scored_locations) == 0:
            logger.error("No scored locations to save")
            return False

        try:
            self.scored_locations.to_csv(self.scored_locations_file, index=False)
            logger.info(
                f"Saved {len(self.scored_locations)} scored locations "
                f"to {self.scored_locations_file}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return False

    def get_summary_stats(self):
        """
        Get summary statistics of scoring results.

        Returns:
            dict: Summary statistics
        """
        if self.scored_locations is None or len(self.scored_locations) == 0:
            return {}

        df = self.scored_locations
        avg_price = df['Median_Price'].mean()

        return {
            'total_locations':   len(df),
            'avg_total_score':   round(df['Total_Score'].mean(), 1),
            'avg_commute_score': round(df['Commute_Score'].mean(), 1),
            'avg_housing_score': round(df['Housing_Score'].mean(), 1),
            'tier_counts':       df['Tier'].value_counts().to_dict(),
            'top_location': {
                'town':  df.iloc[0]['Town'],
                'zip':   df.iloc[0]['Zip'],
                'score': df.iloc[0]['Total_Score']
            } if len(df) > 0 else None,
            'avg_commute_time': round(df['Avg_Commute_Min'].mean(), 1),
            'avg_price': int(avg_price) if pd.notna(avg_price) else 0,
        }


def calculate_scores(config_file=SCORE_CONFIG_FILE, property_types=None):
    """
    Main function to calculate and save location scores.

    Args:
        config_file (str): Path to JSON config file
        property_types (list, optional): Property types to use for execution.

    Returns:
        bool: True if successful
    """
    logger.info("=" * 70)
    logger.info("Starting location scoring")
    logger.info("=" * 70)

    scorer = LocationScorer(config_file, property_types=property_types)

    if not scorer.load_data():
        logger.error("Failed to load data. Aborting.")
        return False, pd.DataFrame(), scorer.config

    results = scorer.score_all_locations()

    if results is None or len(results) == 0:
        logger.error("No locations scored. Aborting.")
        return False, pd.DataFrame(), scorer.config

    if not scorer.save_results():
        logger.error("Failed to save results.")
        return False, pd.DataFrame(), scorer.config

    stats = scorer.get_summary_stats()

    print("\n" + "=" * 70)
    print("LOCATION SCORING COMPLETE")
    print("-" * 70)
    print(f"Total locations scored:    {stats['total_locations']}")
    print(f"Average total score:       {stats['avg_total_score']}/100")
    print(f"Average commute score:     {stats['avg_commute_score']}/100")
    print(f"Average housing score:     {stats['avg_housing_score']}/100")
    print()
    print("Tier Distribution:")
    for tier in sorted(stats['tier_counts'].keys()):
        print(f"  {tier}: {stats['tier_counts'][tier]} locations")
    print()
    if stats['top_location']:
        print(
            f"Top Location: {stats['top_location']['town']} "
            f"({stats['top_location']['zip']}) - "
            f"Score: {stats['top_location']['score']}"
        )
    print("=" * 70 + "\n")

    logger.info("Location scoring completed successfully")
    return True, scorer.scored_locations_file, scorer.filtered_locations, scorer.config


if __name__ == "__main__":
    try:
        calculate_scores()
    except KeyboardInterrupt:
        logger.info("Scoring interrupted by user")
        print("\nScoring interrupted by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {type(e).__name__}: {e}")
        print(f"\nFatal error occurred. Check logs at {APP_LOG_FILE}")
        raise