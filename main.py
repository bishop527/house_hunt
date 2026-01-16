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
from constants import APP_LOG_FILE, LOG_LEVEL

def setup_logging():
    """Configure logging for main orchestrator"""

    # Clear any existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    # File handler (always logs to file)
    file_handler = logging.FileHandler(APP_LOG_FILE)
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(file_formatter)

    # Console handler (can be removed by --quiet)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(console_formatter)
    console_handler.name = 'console'  # Name it so we can remove it later

    # Configure root logger
    root_logger.setLevel(LOG_LEVEL)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return logging.getLogger(__name__)


def run_commute_collection(logger):
    """Run commute data collection module"""
    logger.info("=" * 70)
    logger.info("Starting Commute Data Collection")
    logger.info("=" * 70)

    try:
        collect_commute_data()
        logger.info("Commute collection completed successfully")
        return True
    except KeyboardInterrupt:
        logger.warning("Commute collection interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Commute collection failed: {e}", exc_info=True)
        return False


def run_school_analysis(logger):
    """Run school data analysis module (placeholder)"""
    logger.info("=" * 70)
    logger.info("Starting School Data Analysis")
    logger.info("=" * 70)

    # TODO: Implement when school module is ready
    logger.warning("School analysis module not yet implemented")
    return True


def run_housing_analysis(logger):
    """Run housing data analysis module (placeholder)"""
    logger.info("=" * 70)
    logger.info("Starting Housing Data Analysis")
    logger.info("=" * 70)

    # TODO: Implement when housing module is ready
    logger.warning("Housing analysis module not yet implemented")
    return True


def main():
    """Main entry point for House Hunt project"""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='House Hunt Data Collection and Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --commute              Run commute collection
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

    # Setup logging
    logger = setup_logging()

    # Suppress console output if --quiet
    if args.quiet:
        logging.getLogger().handlers = [
            h for h in logging.getLogger().handlers
            if not isinstance(h, logging.StreamHandler)
        ]

    logger.info(f"House Hunt execution started at {datetime.now()}")

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
    logger.info("=" * 70)
    logger.info("EXECUTION SUMMARY")
    logger.info("-" * 70)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for module, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        logger.info(f"{module.upper()}: {status}")

    logger.info("-" * 70)
    logger.info(
        f"Completed {success_count}/{total_count} modules successfully"
    )
    logger.info("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if success_count == total_count else 1)


if __name__ == "__main__":
    main()