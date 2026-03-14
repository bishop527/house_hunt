#!/usr/bin/env python3
"""
House Hunt - Main Entry Point

Orchestrates data collection and analysis for house hunting project.
Modules can be run individually or together based on command-line args.

Usage:
    python main.py --commute          # Collect commute data only
    python main.py --all              # Run all collection modules
    python main.py --help             # Show usage
"""

import sys
import logging
import argparse
from datetime import datetime

# Import project modules
from Commute.collect_commute_data import collect_commute_data
from Housing.collect_housing_data import collect_housing_data
from constants import APP_LOG_FILE
from logging_config import setup_logger
from Score.calculate_scores import calculate_scores
from Score.generate_report import generate_html_report

def run_commute_collection(logger):
    """Run commute data collection module"""
    logger.info("STARTED: Commute data collection")

    try:
        collect_commute_data()
        logger.info("COMPLETED: Commute data collection")
        return True
    except KeyboardInterrupt:
        logger.warning("Commute collection interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Commute collection failed: {e}", exc_info=True)
        return False


def run_housing_analysis(logger):
    """Run housing data analysis module (placeholder)"""
    logger.info("STARTED: Housing data collection")

    try:
        collect_housing_data()
        logger.info("COMPLETED: Housing data collection")
        return True
    except KeyboardInterrupt:
        logger.warning("Housing data collection interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Housing data collection failed: {e}", exc_info=True)
        return False


def run_scoring(logger, config_file=None):
    """Run location scoring module"""
    logger.info("STARTED: Scoring (via main.py)")

    try:
        success = calculate_scores(config_file)

        if success:
            logger.info("Generating HTML report...")
            scored_df = load_csv_with_zip(SCORED_LOCATIONS_FILE)
            generate_html_report(scored_df, SCORE_REPORT_FILE)

        logger.info("COMPLETED: Scoring")
        return success
    except Exception as e:
        logger.error(f"Scoring failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point for House Hunt project"""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='House Hunt Data Collection and Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --commute              Run commute collection
  python main.py --housing              Run housing collection
  python main.py --all                  Run all modules
  python main.py --commute --schools    Run commute and schools
  python main.py --quite                Suppresses console output
        """
    )

    parser.add_argument(
        '--commute',
        action='store_true',
        help='Collect commute data'
    )

    parser.add_argument(
        '--housing',
        action='store_true',
        help='Analyze housing data'
    )

    parser.add_argument(
        '--score',
        action='store_true',
        help='Score locations and generate report')

    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all collection and analysis modules'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress console output (log to file only)'
    )

    args = parser.parse_args()

    # If no arguments, show help
    if not any([args.commute, args.schools, args.housing, args.all]):
        parser.print_help()
        sys.exit(0)

    # Setup logging (with console output unless --quiet)
    logger = setup_logger(
        __name__,
        log_file=APP_LOG_FILE,
        include_console=not args.quiet
    )

    logger.info(f"STARTED: House Hunt execution")

    # Track module success
    results = {}

    # Run requested modules
    if args.all or args.commute:
        results['commute'] = run_commute_collection(logger)

    if args.all or args.housing:
        results['housing'] = run_housing_analysis(logger)

    if args.all or args.score:
        results['score'] = run_scoring(logger, args.config)

    # Summary
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    logger.info("EXECUTION SUMMARY:")
    for module, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"  {module.upper()}: {status}")

    logger.info(
        f"COMPLETED: House Hunt | {success_count}/{total_count} modules successful"
    )

    # Exit with appropriate code
    sys.exit(0 if success_count == total_count else 1)


if __name__ == "__main__":
    main()