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

# Import project modules
from Commute.collect_commute_data import collect_commute_data
from Housing.collect_housing_data import collect_housing_data
from constants import APP_LOG_FILE, SCORED_LOCATIONS_FILE, SCORE_REPORT_FILE
from utils import load_csv_with_zip
from logging_config import setup_logger
from Score.calculate_scores import calculate_scores
from Score.generate_report import generate_html_report


def run_commute_collection(logger, limit=None, dry_run=False, force=False):
    """Run commute data collection module"""
    logger.info("STARTED: Commute Data Collection")

    try:
        success = collect_commute_data(limit=limit, dry_run=dry_run, force=force)
        if success:
            logger.info("COMPLETED: Commute Data Collection")
        else:
            logger.error("FAILED: Commute Data Collection")
        return success
    except KeyboardInterrupt:
        logger.warning("Commute collection interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Commute collection failed: {e}", exc_info=True)
        return False


def run_housing_collection(logger, limit=None, dry_run=False, force_refresh=False, property_types=None):
    """Run housing data collection module"""
    pt_str = ", ".join(property_types) if property_types else "All"
    logger.info(f"STARTED: Housing Data Collection ({pt_str})")

    if force_refresh:
        logger.info("Force refresh enabled: Will clear historical data for queried zips")

    try:
        success = collect_housing_data(limit=limit, dry_run=dry_run, force_refresh=force_refresh, property_types=property_types)
        if success:
            logger.info(f"COMPLETED: Housing Data Collection ({pt_str})")
        else:
            logger.error(f"FAILED: Housing Data Collection ({pt_str})")
        return success
    except KeyboardInterrupt:
        logger.warning("Housing data collection interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Housing data collection failed: {e}", exc_info=True)
        return False


def run_scoring(logger, config=None, property_types=None):
    pt_str = ", ".join(property_types) if property_types else "All"
    logger.info(f"STARTED: Scoring ({pt_str})")
    try:
        success, scored_file, filtered_df, config_out = calculate_scores(property_types=property_types)
        if success:
            logger.info(f"Generating HTML report from {scored_file}...")
            scored_df = load_csv_with_zip(scored_file)
            generate_html_report(scored_df, SCORE_REPORT_FILE,
                                 config=config_out, filtered_df=filtered_df, property_types=property_types)
        logger.info(f"COMPLETED: Scoring ({pt_str})")
        return success
    except Exception as e:
        logger.error(f"Scoring failed: {e}", exc_info=True)
        return False


def run_work2_generation(logger, dry_run=False):
    """Run Work Address 2 distance generation"""
    logger.info("STARTED: Work Address 2 Distance Generation")
    
    try:
        from Commute.generate_work2_distances import generate_work2_distances
        from constants import ENABLE_SECOND_WORK_ADDRESS
        
        if not ENABLE_SECOND_WORK_ADDRESS:
            logger.warning("Work Address 2 is disabled in constants.py")
            logger.info("Set ENABLE_SECOND_WORK_ADDRESS = True to enable this feature")
            return False
        
        if dry_run:
            logger.info("DRY RUN: Would generate Work Address 2 distances")
            return True
            
        success = generate_work2_distances()
        if success:
            logger.info("COMPLETED: Work Address 2 Distance Generation")
        else:
            logger.error("FAILED: Work Address 2 Distance Generation")
        return success
    except KeyboardInterrupt:
        logger.warning("Work2 generation interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Work2 generation failed: {e}", exc_info=True)
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
  python main.py --score                Run score module
  python main.py --all                  Run all modules
  python main.py --commute --housing    Run commute and schools
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
        '--work2',
        action='store_true',
        help='Generate Work Address 2 distance data')

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

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit the number of locations processed'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Skip actual API calls and just log what would happen'
    )

    parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='Force refresh: clear historical data for queried zips before updating (housing only)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip all interactive prompts (useful for GitHub Actions/CI)'
    )

    args = parser.parse_args()

        # If no arguments, show help
    if not any([args.commute, args.score, args.housing, args.all, args.work2]):
        parser.print_help()
        sys.exit(0)

    # Setup logging (with console output unless --quiet)
    logger = setup_logger(
        __name__,
        log_file=APP_LOG_FILE,
        include_console=not args.quiet
    )

    logger.info("STARTED: House Hunt Execution")

        # Import here to avoid circular imports / missing references
    from constants import PROPERTY_TYPES
    
    # Track module success (only for modules that actually run)
    module_success = {}

    # Run Work Address 2 generation if requested
    if args.work2:
        success = run_work2_generation(logger, dry_run=args.dry_run)
        module_success['work2'] = success

        # Run commute collection (independent of property types)
        if args.all or args.commute:
            success = run_commute_collection(
                logger, limit=args.limit, dry_run=args.dry_run, force=args.force
            )
            module_success['commute'] = success

    # Run housing/scoring iteratively for EACH property type
    if args.all or args.housing or args.score:
        active_property_types = PROPERTY_TYPES
        if 'All' in active_property_types:
            active_property_types = ['Single Family', 'Condo', 'Townhouse']

        for pt in active_property_types:
            logger.info(f"=== Starting execution for Property Type: {pt} ===")
            if args.all or args.housing:
                success = run_housing_collection(
                    logger, limit=args.limit, dry_run=args.dry_run, force_refresh=args.force_refresh, property_types=[pt]
                )
                module_success['housing'] = module_success.get('housing', True) and success

            if args.all or args.score:
                success = run_scoring(logger, property_types=[pt])
                module_success['score'] = module_success.get('score', True) and success

    # Summary
    success_count = sum(1 for v in module_success.values() if v)
    total_count = len(module_success)

    logger.info("EXECUTION SUMMARY:")
    for module, success in module_success.items():
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"  {module.upper()}: {status}")

    logger.info(
        f"COMPLETED: House Hunt | {success_count}/{total_count} modules successful"
    )

    # Exit with appropriate code
    sys.exit(0 if success_count == total_count else 1)


if __name__ == "__main__":
    main()