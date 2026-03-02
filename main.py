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


def run_school_analysis(logger):
    """Run school data analysis module (placeholder)"""
    logger.info("STARTED: School analysis")

    # TODO: Implement when school module is ready
    logger.warning("School analysis module not yet implemented")
    return True


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
        '--schools',
        action='store_true',
        help='Analyze school data'
    )

    parser.add_argument(
        '--housing',
        action='store_true',
        help='Analyze housing data'
    )

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

    if args.all or args.schools:
        results['schools'] = run_school_analysis(logger)

    if args.all or args.housing:
        results['housing'] = run_housing_analysis(logger)

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