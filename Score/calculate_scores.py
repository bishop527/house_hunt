"""
Calculate and rank housing locations based on commute and housing data.

This module:
1. Loads commute and housing statistics
2. Applies user-configurable scoring algorithms
3. Generates ranked results with tier classifications
4. Outputs scored locations CSV and HTML report
"""
import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from constants import *
from utils import load_csv_with_zip

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    filename=APP_LOG_FILE,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
WORST_TAX_RATE = 3.0  # 3% is considered very high tax rate


class LocationScorer:
    """
    Scores housing locations based on commute and housing data.

    Uses configurable weights and preferences to calculate scores
    for each location, then ranks and assigns tiers.
    """

    def __init__(self, config_file=None):
        """
        Initialize scorer with configuration.

        Args:
            config_file (str): Path to JSON config file. If None,
                             uses default config.
        """
        self.config = self._load_config(config_file)
        self.commute_data = None
        self.housing_data = None
        self.scored_locations = None

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
            logger.error(
                f"Configuration file not found: {config_file}"
            )
            logger.error(
                "Create a score_config.json file with your preferences."
            )
            logger.error("Scoring cannot continue without configuration.")
            sys.exit(1)

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded config from {config_file}")

            # Validate required sections
            required_sections = ['weights', 'commute_preferences',
                               'housing_preferences']
            for section in required_sections:
                if section not in config:
                    logger.error(
                        f"Missing required section '{section}' "
                        f"in config file"
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

        # Load commute stats
        self.commute_data = load_csv_with_zip(COMMUTE_STATS_FILE)
        if self.commute_data.empty:
            logger.error(
                f"No commute data found at {COMMUTE_STATS_FILE}"
            )
            return False

        logger.info(
            f"Loaded {len(self.commute_data)} commute records"
        )

        # Load housing stats
        self.housing_data = load_csv_with_zip(HOUSING_STATS_FILE)
        if self.housing_data.empty:
            logger.error(
                f"No housing data found at {HOUSING_STATS_FILE}"
            )
            return False

        logger.info(
            f"Loaded {len(self.housing_data)} housing records"
        )

        return True

    def _score_commute_time(self, avg_time):
        """
        Score commute time based solely on average time (0-100 points).

        Args:
            avg_time (float): Average commute time in minutes

        Returns:
            float: Score 0-100
        """
        prefs = self.config['commute_preferences']
        ideal = prefs['ideal_time_minutes']
        max_acceptable = prefs['max_acceptable_time']

        if avg_time <= ideal:
            # Excellent: full points
            return COMMUTE_SCORE_MAX
        elif avg_time <= max_acceptable:
            # Acceptable: linear scale from max to 50% of max
            ratio = (avg_time - ideal) / (max_acceptable - ideal)
            return COMMUTE_SCORE_MAX - (ratio * (COMMUTE_SCORE_MAX / 2))
        else:
            # Poor: linear scale from 50% to 0
            worst = max_acceptable * WORST_COMMUTE_TIME_MULTIPLIER
            if avg_time >= worst:
                return MIN_SCORE
            ratio = (avg_time - max_acceptable) / (worst - max_acceptable)
            return (COMMUTE_SCORE_MAX / 2) - (ratio * (COMMUTE_SCORE_MAX / 2))

    def calculate_commute_score(self, row):
        """
        Calculate total commute score (0-100).

        Based solely on average commute time.

        Args:
            row (pd.Series): Row from commute_data DataFrame

        Returns:
            dict: {
                'commute_score': float
            }
        """
        commute_score = self._score_commute_time(row['Average_Time'])

        return {
            'commute_score': round(commute_score, 1)
        }

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
        budget_min = prefs['budget_min']
        budget_max = prefs['budget_max']
        budget_ideal = prefs['budget_ideal']

        bonus_points = 5.0
        penalty_range = 10.0
        max_score_over_budget = 35.0
        penalty_multiplier = 100.0

        if price <= budget_ideal:
            # Below or at ideal: full points, slight bonus for savings
            if price <= budget_min:
                return PRICE_SCORE_MAX
            ratio = (budget_ideal - price) / (budget_ideal - budget_min)
            return (PRICE_SCORE_MAX - bonus_points) + (ratio * bonus_points)

        elif price <= budget_max:
            # Within budget but above ideal: linear penalty
            ratio = (price - budget_ideal) / (budget_max - budget_ideal)
            return (PRICE_SCORE_MAX - bonus_points) - (ratio * penalty_range)

        else:
            # Over budget: exponential penalty
            overage_ratio = (price - budget_max) / budget_max

            # Exponential penalty: gets harsh quickly
            penalty = (overage_ratio ** 1.5) * penalty_multiplier

            score = max_score_over_budget - penalty
            return max(MIN_SCORE, score)

    def _score_housing_tax(self, tax_rate):
        """
        Score property tax rate (0-50 points).

        Args:
            tax_rate (float): Annual property tax rate as percentage
                             (e.g., 1.25 for 1.25%)

        Returns:
            float: Score 0-50
        """
        if pd.isna(tax_rate):
            return NEUTRAL_SCORE / 2  # Neutral if missing

        prefs = self.config['housing_preferences']
        ideal = prefs.get('ideal_tax_rate', 1.0)
        max_acceptable = prefs.get('max_acceptable_tax_rate', 1.5)

        if tax_rate <= ideal:
            # Excellent: at or below ideal rate
            return TAX_SCORE_MAX
        elif tax_rate <= max_acceptable:
            # Acceptable: between ideal and max
            ratio = (tax_rate - ideal) / (max_acceptable - ideal)
            penalty_range = 25.0
            return TAX_SCORE_MAX - (ratio * penalty_range)
        else:
            # Poor: above max acceptable
            if tax_rate >= WORST_TAX_RATE:
                return MIN_SCORE
            ratio = (tax_rate - max_acceptable) / (WORST_TAX_RATE - max_acceptable)
            remaining_points = 25.0
            return remaining_points - (ratio * remaining_points)

    def calculate_housing_score(self, row):
        """
        Calculate total housing score (0-100).

        Based on average price and tax rate only.

        Args:
            row (pd.Series): Row from housing_data DataFrame

        Returns:
            dict: {
                'housing_score': float,
                'price_score': float,
                'tax_score': float
            }
        """
        # Calculate sub-scores
        price_score = self._score_housing_price(
            row.get('Latest_Median_Sale')
        )
        tax_score = self._score_housing_tax(
            row.get('Tax_Rate')
        )

        # Equal weighting: 50 points each
        housing_score = price_score + tax_score

        return {
            'housing_score': round(housing_score, 1),
            'price_score': round(price_score, 1),
            'tax_score': round(tax_score, 1)
        }

    def _assign_tier(self, total_score):
        """
        Assign letter tier based on total score.

        Args:
            total_score (float): Total score 0-100

        Returns:
            str: Tier (A+, A, A-, B+, B, B-, C+, C, C-, D, F)
        """
        if total_score >= 95:
            return 'A+'
        elif total_score >= 90:
            return 'A'
        elif total_score >= 85:
            return 'A-'
        elif total_score >= 80:
            return 'B+'
        elif total_score >= 75:
            return 'B'
        elif total_score >= 70:
            return 'B-'
        elif total_score >= 65:
            return 'C+'
        elif total_score >= 60:
            return 'C'
        elif total_score >= 55:
            return 'C-'
        elif total_score >= 50:
            return 'D'
        else:
            return 'F'

    def score_all_locations(self):
        """
        Score all locations and create ranked results.

        Returns:
            pd.DataFrame: Scored and ranked locations
        """
        if self.commute_data is None or self.housing_data is None:
            logger.error("Data not loaded. Call load_data() first.")
            return None

        logger.info("Scoring all locations...")

        # Merge datasets on Zip
        merged = pd.merge(
            self.commute_data,
            self.housing_data,
            on='Zip',
            how='inner',
            suffixes=('_commute', '_housing')
        )

        if len(merged) == 0:
            logger.error("No matching records between datasets")
            return None

        logger.info(
            f"Found {len(merged)} locations with both commute "
            f"and housing data"
        )

        # Apply filters
        filters = self.config['filters']

        if filters.get('max_commute_time'):
            before = len(merged)
            merged = merged[
                merged['Average_Time'] <= filters['max_commute_time']
            ]
            logger.info(
                f"Filtered {before - len(merged)} locations "
                f"exceeding max commute time"
            )

        if filters.get('max_price'):
            before = len(merged)
            merged = merged[
                merged['Latest_Median_Sale'] <= filters['max_price']
            ]
            logger.info(
                f"Filtered {before - len(merged)} locations "
                f"exceeding max price"
            )

        # Calculate scores
        results = []

        for _, row in merged.iterrows():
            # Get commute scores
            commute_scores = self.calculate_commute_score(row)

            # Get housing scores
            housing_scores = self.calculate_housing_score(row)

            # Calculate weighted total
            weights = self.config['weights']
            total_score = (
                commute_scores['commute_score'] * weights['commute'] +
                housing_scores['housing_score'] * weights['housing']
            )

            # Assign tier
            tier = self._assign_tier(total_score)

            # Build result record
            result = {
                'Town': row.get('Town_commute', row.get('Town_housing')),
                'State': row.get('State_commute', row.get('State_housing')),
                'Zip': row['Zip'],
                'Total_Score': round(total_score, 1),
                'Tier': tier,
                'Commute_Score': commute_scores['commute_score'],
                'Housing_Score': housing_scores['housing_score'],
                'Avg_Commute_Min': row['Average_Time'],
                'Min_Commute_Min': row['Min_Time'],
                'Max_Commute_Min': row['Max_Time'],
                'Distance_Miles': row['Distance'],
                'Median_Price': row.get('Latest_Median_Sale'),
                'Price_Per_SqFt': row.get('Latest_PPSF'),
                'Homes_Sold': row.get('Latest_Homes_Sold'),
                'Inventory': row.get('Latest_Inventory'),
                'Commute_Runs': row.get('Total_Runs_commute', row.get('Total_Runs')),
                'Last_Updated': row.get('Last_Run_Date_commute')
            }

            results.append(result)

        # Convert to DataFrame
        self.scored_locations = pd.DataFrame(results)

        # No minimum score filtering - include all scored locations
        # (Filtering can be done in reporting/visualization if needed)

        # Sort by total score (descending)
        self.scored_locations = self.scored_locations.sort_values(
            'Total_Score',
            ascending=False
        ).reset_index(drop=True)

        # Add rank column
        self.scored_locations.insert(
            0,
            'Rank',
            range(1, len(self.scored_locations) + 1)
        )

        logger.info(
            f"Scored {len(self.scored_locations)} locations"
        )

        return self.scored_locations

    def save_results(self):
        """
        Save scored results to CSV.

        Uses file path from constants, not config.

        Returns:
            bool: True if successful
        """
        if self.scored_locations is None or len(
            self.scored_locations
        ) == 0:
            logger.error("No scored locations to save")
            return False

        output_file = SCORED_LOCATIONS_FILE

        try:
            self.scored_locations.to_csv(output_file, index=False)
            logger.info(
                f"Saved {len(self.scored_locations)} scored "
                f"locations to {output_file}"
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

        # Calculate averages safely (handle NaN)
        avg_price = df['Median_Price'].mean()

        return {
            'total_locations': len(df),
            'avg_total_score': round(df['Total_Score'].mean(), 1),
            'avg_commute_score': round(df['Commute_Score'].mean(), 1),
            'avg_housing_score': round(df['Housing_Score'].mean(), 1),
            'tier_counts': df['Tier'].value_counts().to_dict(),
            'top_location': {
                'town': df.iloc[0]['Town'],
                'zip': df.iloc[0]['Zip'],
                'score': df.iloc[0]['Total_Score']
            } if len(df) > 0 else None,
            'avg_commute_time': round(df['Avg_Commute_Min'].mean(), 1),
            'avg_price': int(avg_price) if pd.notna(avg_price) else 0,
        }


def calculate_scores(config_file=SCORE_CONFIG_FILE):
    """
    Main function to calculate and save location scores.

    Args:
        config_file (str): Path to JSON config file

    Returns:
        bool: True if successful
    """
    logger.info("=" * 70)
    logger.info("Starting location scoring")
    logger.info("=" * 70)

    # Initialize scorer
    scorer = LocationScorer(config_file)

    # Load data
    if not scorer.load_data():
        logger.error("Failed to load data. Aborting.")
        return False

    # Score locations
    results = scorer.score_all_locations()

    if results is None or len(results) == 0:
        logger.error("No locations scored. Aborting.")
        return False

    # Save results
    if not scorer.save_results():
        logger.error("Failed to save results.")
        return False

    # Print summary
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

    return True


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