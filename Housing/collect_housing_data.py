"""
Collect housing price data for zip codes within range.

This module fetches housing market data from Redfin's public datasets
and HUD Fair Market Rent data as a fallback/supplement.

Data sources:
- Primary: Redfin public market data (monthly updates, free)
- Fallback: HUD Fair Market Rent (annual updates, free)
"""
import os
import logging
import gzip
from datetime import datetime
from urllib.request import urlretrieve
import pandas as pd
from tqdm import tqdm
from logging_config import setup_logger, silence_verbose_loggers

from constants import *
from utils import (
    get_zip_data,
    get_zips_within_range,
    load_csv_with_zip
)

# Configure logging
logger = setup_logger(__name__, log_file=HOUSING_LOG_FILE)
silence_verbose_loggers()

# Module-level cache for property tax rates
_property_tax_cache = None


def download_redfin_data():
    """
    Download latest Redfin market data if not already present.

    Downloads from Redfin's public S3 bucket and filters for:
    - Year 2025 data only
    - States: MA, RI, NH

    This reduces the 4GB+ file to a manageable size.

    Returns:
        bool: True if download successful or file exists
    """
    # Check if we already have recent data based on tracker file
    cache_tracker_file = os.path.join(os.path.dirname(REDFIN_DATA_FILE), '.redfin_last_downloaded')
    if os.path.exists(REDFIN_DATA_FILE) and os.path.exists(cache_tracker_file):
        try:
            with open(cache_tracker_file, 'r') as f:
                last_download_str = f.read().strip()
                last_download_date = datetime.fromisoformat(last_download_str)
                
            file_age_days = (datetime.now() - last_download_date).days
            
            if file_age_days < REDFIN_DATA_MAX_AGE_DAYS:
                logger.info(
                    f"Using existing Redfin data "
                    f"({file_age_days} days old)"
                )
                return True
            else:
                logger.info(
                    f"Redfin data is {file_age_days} days old, "
                    f"downloading fresh copy..."
                )
        except Exception as e:
            logger.warning(f"Failed to read cache tracker: {e}. Re-downloading...")
            
    else:
        logger.info(f"Redfin data or cache tracker not found, downloading fresh copy...")

    try:
        logger.info("Downloading Redfin market data (this may take time)...")
        logger.info(f"URL: {REDFIN_DOWNLOAD_URL}")

        # Download compressed file
        gz_file = REDFIN_DATA_FILE + '.gz'
        urlretrieve(REDFIN_DOWNLOAD_URL, gz_file)

        logger.info("Download complete. Decompressing and filtering...")

        # Read compressed file in chunks and filter
        # This prevents loading 4GB into memory
        filtered_chunks = []

        with gzip.open(gz_file, 'rt') as f:
            # Read in chunks to handle large file
            chunk_iter = pd.read_csv(
                f,
                sep='\t',
                chunksize=100000,  # Process 100k rows at a time
                dtype={'REGION': str},
                low_memory=False
            )

            current_year = str(datetime.now().year)
            previous_year = str(datetime.now().year - 1)
            
            # Derive full state names from target abbreviations
            target_state_names = [STATE_ABBR_TO_NAME.get(abbr) for abbr in TARGET_STATES if STATE_ABBR_TO_NAME.get(abbr)]

            for chunk in tqdm(chunk_iter,
                            desc="Filtering data",
                            unit="chunk"):
                # Filter for current and previous year data and target states
                # PERIOD_END format: YYYY-MM-DD
                filtered = chunk[
                    (chunk['PERIOD_END'].str.startswith(current_year) |
                     chunk['PERIOD_END'].str.startswith(previous_year)) &
                    (chunk['STATE'].isin(target_state_names))
                ].copy()

                if len(filtered) > 0:
                    filtered_chunks.append(filtered)

        # Combine filtered chunks
        if filtered_chunks:
            df_filtered = pd.concat(filtered_chunks, ignore_index=True)

            # Save filtered data
            df_filtered.to_csv(REDFIN_DATA_FILE, index=False, sep='\t')

            logger.info(
                f"Saved {len(df_filtered):,} filtered records to "
                f"{REDFIN_DATA_FILE}"
            )
        else:
            logger.warning("No data found matching filter criteria")
            return False

        # Clean up compressed file
        os.remove(gz_file)
        
        # Update cache tracker
        try:
            cache_tracker_file = os.path.join(os.path.dirname(REDFIN_DATA_FILE), '.redfin_last_downloaded')
            with open(cache_tracker_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logger.warning(f"Failed to update cache tracker: {e}")

        logger.info("Successfully processed Redfin data")
        return True

    except Exception as e:
        logger.error(f"Failed to download Redfin data: {e}")
        return False


def get_redfin_data(zip_code, redfin_df, property_types=None):
    """
    Get housing data from Redfin CSV for a specific zip code.

    Args:
        zip_code (str): 5-digit zip code (zero-padded)
        redfin_df (pd.DataFrame): The pre-loaded Redfin DataFrame
        property_types (list): List of property types to query

    Returns:
        dict or None: Housing data if found, None otherwise
    """
    try:
        target_region = f"Zip Code: {zip_code.zfill(5)}"

        zip_data = redfin_df[
            (redfin_df['REGION_TYPE'] == 'zip code') &
            (redfin_df['REGION'] == target_region)
        ]

        if len(zip_data) == 0:
            logger.debug(f"No Redfin data found for zip {zip_code}")
            return None

        prop_type_mapping = {
            'Single Family': 'Single Family Residential',
            'Condo': 'Condo/Co-op',
            'Townhouse': 'Townhouse',
            'All': 'All Residential'
        }
        active_property_types = property_types if property_types is not None else PROPERTY_TYPES
        allowed = [prop_type_mapping[pt] for pt in active_property_types if pt in prop_type_mapping]

        filtered_zip_data = zip_data[zip_data['PROPERTY_TYPE'].isin(allowed)]

        if len(filtered_zip_data) == 0:
             logger.debug(f"No '{active_property_types}' property type data found for zip {zip_code}")
             return None

        # Sort by PERIOD_END descending to find latest month
        filtered_zip_data = filtered_zip_data.sort_values('PERIOD_END', ascending=False)
        latest_period = filtered_zip_data.iloc[0]['PERIOD_END']
        
        # Get all records matching the latest month (could be different property types)
        latest_data = filtered_zip_data[filtered_zip_data['PERIOD_END'] == latest_period]

        total_homes_sold = latest_data['HOMES_SOLD'].sum()
        if pd.isna(total_homes_sold) or total_homes_sold < MIN_SAMPLE_SIZE:
             logger.warning(
                 f"Insufficient data for {zip_code}: "
                 f"only {total_homes_sold} homes sold for requested property types"
             )
             return None

        # Weighted aggregate calculation
        if len(latest_data) == 1:
             median_sale = latest_data.iloc[0]['MEDIAN_SALE_PRICE']
             median_list = latest_data.iloc[0]['MEDIAN_LIST_PRICE']
             median_ppsf = latest_data.iloc[0]['MEDIAN_PPSF']
             months_supply = latest_data.iloc[0]['MONTHS_OF_SUPPLY']
             inventory_val = latest_data.iloc[0].get('INVENTORY', 0)
        else:
             weights = latest_data['HOMES_SOLD'] / total_homes_sold
             weights = weights.fillna(0)
             median_sale = (latest_data['MEDIAN_SALE_PRICE'] * weights).sum()
             median_list = (latest_data['MEDIAN_LIST_PRICE'] * weights).sum()
             median_ppsf = (latest_data['MEDIAN_PPSF'] * weights).sum()
             months_supply_series = latest_data['MONTHS_OF_SUPPLY'].dropna()
             months_supply = months_supply_series.mean() if len(months_supply_series) > 0 else None
             inventory_val = latest_data['INVENTORY'].sum(skipna=True)

        if pd.isna(inventory_val):
             inventory_val = 0

        return {
            'zip': zip_code,
            'median_sale_price': float(median_sale) if pd.notna(median_sale) else None,
            'median_list_price': float(median_list) if pd.notna(median_list) else None,
            'median_ppsf': int(median_ppsf) if pd.notna(median_ppsf) else None,
            'homes_sold': int(total_homes_sold),
            'inventory': int(inventory_val),
            'months_of_supply': float(months_supply) if pd.notna(months_supply) else None,
            'source': 'redfin',
            'period_end': latest_period
        }

    except Exception as e:
        logger.error(f"Error reading Redfin data for {zip_code}: {e}")
        return None


def get_hud_fmr_data(zip_code, state):
    """
    Get HUD Fair Market Rent data as fallback.

    HUD data is county-based, so we use the county associated with
    the zip code. This is less granular than Redfin but always available.

    Args:
        zip_code (str): 5-digit zip code
        state (str): 2-letter state abbreviation

    Returns:
        dict or None: FMR data if available
        {
            'zip': str,
            'fmr_0br': float,
            'fmr_1br': float,
            'fmr_2br': float,
            'fmr_3br': float,
            'fmr_4br': float,
            'source': 'hud_fmr',
            'year': str
        }
    """
    # For now, return None - HUD API integration can be added later
    # This would require:
    # 1. Zip -> County mapping
    # 2. HUD API call for county FMR
    # 3. Parse JSON response

    logger.debug(
        f"HUD FMR fallback not yet implemented for {zip_code}"
    )
    return None


def load_property_tax_rates():
    """
    Load property tax rates from CSV.

    Uses caching to avoid re-reading file multiple times per run.

    Returns:
        pd.DataFrame: Tax rates by town and state
    """
    global _property_tax_cache

    if _property_tax_cache is not None:
        return _property_tax_cache

    if os.path.exists(PROPERTY_TAX_FILE):
        try:
            _property_tax_cache = pd.read_csv(PROPERTY_TAX_FILE)
            logger.info(
                f"Loaded {len(_property_tax_cache)} property tax rates"
            )
            return _property_tax_cache
        except Exception as e:
            logger.error(f"Failed to load property tax rates: {e}")
            _property_tax_cache = pd.DataFrame()
            return _property_tax_cache
    else:
        logger.warning(
            f"Property tax file not found: {PROPERTY_TAX_FILE}"
        )
        _property_tax_cache = pd.DataFrame()
        return _property_tax_cache


def get_property_tax_rate(town, state):
    """
    Get property tax rate for a specific town.

    Uses state-specific defaults when town not found in database.

    Args:
        town (str): Town name (case insensitive)
        state (str): State abbreviation (MA, RI, NH)

    Returns:
        dict: Tax information (always returns a value)
        {
            'tax_rate_per_1000': float,
            'fiscal_year': str,
            'tax_data_source': str  # 'database' or 'state_default'
        }
    """
    tax_df = load_property_tax_rates()

    # Try to find in database first (case-insensitive)
    if not tax_df.empty:
        tax_row = tax_df[
            (tax_df['Town'].str.lower() == town.lower()) &
            (tax_df['State'] == state)
        ]

        if len(tax_row) > 0:
            row = tax_row.iloc[0]
            return {
                'tax_rate_per_1000': row['Tax_Rate_Per_1000'],
                'fiscal_year': row['Fiscal_Year'],
                'tax_data_source': 'database'
            }

    # Not found in database - use state default
    logger.warning(
        f"No tax rate found for {town}, {state} - "
        f"using state default"
    )

    # Determine default based on state
    if state == 'MA':
        default_rate = DEFAULT_MA_TAX_RATE
    elif state == 'RI':
        default_rate = DEFAULT_RI_TAX_RATE
    elif state == 'NH':
        default_rate = DEFAULT_NH_TAX_RATE
    else:
        # Fallback for unexpected states
        default_rate = DEFAULT_MA_TAX_RATE
        logger.warning(
            f"Unknown state '{state}', using MA default rate"
        )

    return {
        'tax_rate_per_1000': default_rate,
        'fiscal_year': 'N/A (default)',
        'tax_data_source': f'{state}_default'
    }


def enrich_with_property_tax(data):
    """
    Add property tax information to housing data.

    Always adds tax data - uses state defaults when town not in database.

    Args:
        data (dict): Housing data dictionary

    Returns:
        dict: Enriched with tax_rate, estimated_annual_tax, etc.
    """
    town = data.get('town')
    state = data.get('state')

    if not town or not state:
        logger.warning(
            "Missing town or state in data - cannot calculate tax"
        )
        return data

    # Get tax info (always returns a value)
    tax_info = get_property_tax_rate(town, state)

    data['tax_rate_per_1000'] = tax_info['tax_rate_per_1000']
    data['tax_fiscal_year'] = tax_info['fiscal_year']
    data['tax_data_source'] = tax_info['tax_data_source']

    # Calculate estimated annual property tax
    median_price = data.get('median_sale_price')
    if median_price and not pd.isna(median_price):
        data['estimated_annual_tax'] = round(
            (median_price * tax_info['tax_rate_per_1000']) / 1000,
            2
        )
        # Monthly tax
        data['estimated_monthly_tax'] = round(
            data['estimated_annual_tax'] / 12,
            2
        )

    return data


def get_historical_redfin_data(zip_code, redfin_df, months=12, property_types=None):
    """
    Get historical monthly data from Redfin for min/max/avg calculation.

    Args:
        zip_code (str): 5-digit zip code
        redfin_df (pd.DataFrame): The pre-loaded Redfin DataFrame
        months (int): Number of months to look back
        property_types (list): List of property types to query

    Returns:
        dict or None: Historical statistics
    """
    try:
        target_region = f"Zip Code: {zip_code.zfill(5)}"

        zip_data = redfin_df[
            (redfin_df['REGION_TYPE'] == 'zip code') &
            (redfin_df['REGION'] == target_region)
        ]

        if len(zip_data) == 0:
            return None

        prop_type_mapping = {
            'Single Family': 'Single Family Residential',
            'Condo': 'Condo/Co-op',
            'Townhouse': 'Townhouse',
            'All': 'All Residential'
        }
        active_property_types = property_types if property_types is not None else PROPERTY_TYPES
        allowed = [prop_type_mapping[pt] for pt in active_property_types if pt in prop_type_mapping]

        filtered_zip_data = zip_data[zip_data['PROPERTY_TYPE'].isin(allowed)]

        if len(filtered_zip_data) == 0:
             logger.debug(f"No '{active_property_types}' property type data found for zip {zip_code}")
             return None

        # Group by PERIOD_END to summarize multiple property types in a single month
        def weighted_avg_price(x):
            total_sold = x['HOMES_SOLD'].sum()
            if total_sold > 0:
                return (x['MEDIAN_SALE_PRICE'] * x['HOMES_SOLD']).sum() / total_sold
            return x['MEDIAN_SALE_PRICE'].mean()

        monthly_avg = filtered_zip_data.groupby('PERIOD_END', as_index=False).apply(weighted_avg_price, include_groups=False).rename(columns={None: 'MEDIAN_SALE_PRICE'})

        monthly_avg = monthly_avg.sort_values('PERIOD_END', ascending=False).head(months)

        prices = monthly_avg['MEDIAN_SALE_PRICE'].dropna()

        if len(prices) == 0:
            return None

        if len(prices) >= 2:
            recent_price = prices.iloc[0]
            old_price = prices.iloc[-1]
            if recent_price > old_price * 1.05:  # 5% increase
                trend = 'increasing'
            elif recent_price < old_price * 0.95:  # 5% decrease
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'

        return {
            'min_monthly_price': int(prices.min()),
            'max_monthly_price': int(prices.max()),
            'avg_monthly_price': int(prices.mean()),
            'months_of_data': len(prices),
            'price_trend': trend
        }

    except Exception as e:
        logger.error(f"Error reading historical Redfin data for {zip_code}: {e}")
        return None


def fetch_housing_data(addresses, property_types=None):
    """
    Fetch housing data for list of addresses.

    Args:
        addresses (list): List of "Town, State Zip" formatted addresses
        property_types (list): List of property types

    Returns:
        tuple: (results: list, failed_zips: list)
            - results: List of housing data dictionaries with valid data
            - failed_zips: List of dicts for zips with no property type data
    """
    results = []
    failed_zips = []  # Track zips with no property type data

    logger.info(f"Fetching housing data for {len(addresses)} zip codes")
    
    # Load Redfin TSV into memory exactly once to prevent O(N) disk reads
    redfin_df = None
    if os.path.exists(REDFIN_DATA_FILE):
        logger.info(f"Loading {REDFIN_DATA_FILE} TSV into memory...")
        redfin_df = pd.read_csv(
            REDFIN_DATA_FILE,
            sep='\t',
            dtype={'REGION': str},
            low_memory=False
        )
    else:
        logger.warning(f"Redfin data file not found at {REDFIN_DATA_FILE}")

    for address in tqdm(addresses,
                        desc="Collecting housing data",
                        unit="zip",
                        ncols=80):
        try:
            # Parse address: "Lexington, MA 02421"
            parts = address.split(',')
            town = parts[0].strip()
            state_zip = parts[1].strip().split()
            state = state_zip[0]
            zip_code = state_zip[1]

            data = None
            if redfin_df is not None:
                 data = get_redfin_data(zip_code, redfin_df, property_types=property_types)

            # Fall back to HUD if Redfin unavailable
            if data is None:
                data = get_hud_fmr_data(zip_code, state)

            if data is not None:
                # Add town and state to result
                data['town'] = town
                data['state'] = state

                # Enrich with property tax data
                data = enrich_with_property_tax(data)

                # Get historical monthly statistics
                if redfin_df is not None:
                    historical = get_historical_redfin_data(zip_code, redfin_df, months=12, property_types=property_types)
                    if historical:
                        data.update(historical)

                results.append(data)
            else:
                # Track zips with no property type data for filtered report
                logger.warning(
                    f"No housing data available for {address}"
                )
                # Format property types nicely for display
                active_property_types = property_types if property_types is not None else PROPERTY_TYPES
                prop_types_str = ', '.join(active_property_types) if active_property_types else 'N/A'
                failed_zips.append({
                    'Town': town,
                    'State': state,
                    'Zip': zip_code,
                    'Filter_Reason': f'No {prop_types_str} data available',
                    'Property_Types_Requested': prop_types_str
                })

        except Exception as e:
            logger.error(f"Error processing {address}: {e}")
            continue

    logger.info(
        f"Successfully collected data for {len(results)} "
        f"out of {len(addresses)} zip codes"
    )

    if failed_zips:
        logger.info(
            f"{len(failed_zips)} zip codes excluded due to missing property type data"
        )

    return results, failed_zips


def load_historical_data(property_types=None):
    """
    Load historical housing statistics from CSV.

    Args:
        property_types (list): Property types list for distinguishing files.

    Returns:
        pd.DataFrame: Historical data, or empty DataFrame if doesn't exist
    """
    active_property_types = property_types if property_types is not None else PROPERTY_TYPES
    _prop_type_suffix = "_".join(pt.replace(" ", "_") for pt in active_property_types) if active_property_types else "All"
    housing_stats_file = HOUSING_STATS_FILE.replace(".csv", f"_{_prop_type_suffix}.csv")

    df = load_csv_with_zip(housing_stats_file)
    if not df.empty:
        logger.info(
            f"Loaded {len(df)} records from {housing_stats_file}"
        )
    else:
        logger.info(f"No historical housing data found at {housing_stats_file}. Starting fresh.")
    return df


def update_statistics(results, force_refresh=False, queried_addresses=None, property_types=None):
    """
    Update housing statistics with new results.

    Maintains running statistics similar to commute data:
    - Total number of data points collected
    - Last update date
    - Min/Max/Average prices
    - Monthly price tracking (hybrid approach)

    Args:
        results (list): List of housing data dicts from fetch_housing_data()
        force_refresh (bool): If True, remove historical data for queried zips
        queried_addresses (list): List of addresses that were queried this run
        property_types (list): Property types to suffix the stats file
    """
    if not results:
        logger.warning("No results to update statistics with.")
        return

    # Convert results to DataFrame
    df_today = pd.DataFrame(results)

    # Load historical data
    df_hist = load_historical_data(property_types=property_types)

    # If force_refresh, remove historical data for all queried zips
    if force_refresh and queried_addresses and not df_hist.empty:
        queried_zips = set([addr.split()[-1] for addr in queried_addresses])
        original_count = len(df_hist)
        df_hist = df_hist[~df_hist['Zip'].isin(queried_zips)]
        removed_count = original_count - len(df_hist)
        if removed_count > 0:
            logger.info(
                f"Force refresh: Removed {removed_count} historical records "
                f"for queried zips"
            )

    # Get today's date and month
    today = datetime.now().strftime('%Y-%m-%d')
    month_str = datetime.now().strftime('%Y-%m')

    # Process each result
    updated_records = []

    for _, row in df_today.iterrows():
        town = row['town']
        state = row['state']
        zip_code = row['zip']

        # Find existing record
        if not df_hist.empty:
            existing = df_hist[df_hist['Zip'] == zip_code]
        else:
            existing = pd.DataFrame()

        if len(existing) > 0:
            # Update existing record
            rec = existing.iloc[0].to_dict()

            rec['Total_Runs'] += 1
            rec['Last_Run_Date'] = today

            # Update price statistics (all-time min/max/avg)
            if 'median_sale_price' in row and pd.notna(
                row['median_sale_price']
            ):
                price = float(row['median_sale_price'])

                rec['Min_Price'] = min(rec.get('Min_Price', price),
                                       price)
                rec['Max_Price'] = max(rec.get('Max_Price', price),
                                       price)

                # Update running average
                old_avg = rec.get('Average_Price', price)
                old_count = rec['Total_Runs'] - 1
                new_avg = (old_avg * old_count + price) / rec['Total_Runs']
                rec['Average_Price'] = round(new_avg, 2)

            # Update latest values
            rec['Latest_Median_Sale'] = row.get('median_sale_price')
            rec['Latest_Median_List'] = row.get('median_list_price')
            rec['Latest_PPSF'] = row.get('median_ppsf')
            rec['Latest_Homes_Sold'] = row.get('homes_sold')
            rec['Latest_Inventory'] = row.get('inventory')

            # Update property tax info
            rec['Tax_Rate_Per_1000'] = row.get('tax_rate_per_1000')
            rec['Tax_Data_Source'] = row.get('tax_data_source')
            rec['Estimated_Annual_Tax'] = row.get('estimated_annual_tax')
            rec['Estimated_Monthly_Tax'] = row.get('estimated_monthly_tax')

            # Update historical monthly stats (from Redfin historical data)
            rec['Min_Monthly_Price'] = row.get('min_monthly_price')
            rec['Max_Monthly_Price'] = row.get('max_monthly_price')
            rec['Avg_Monthly_Price'] = row.get('avg_monthly_price')
            rec['Months_Of_Data'] = row.get('months_of_data')
            rec['Price_Trend'] = row.get('price_trend')

        else:
            # Create new record
            price = row.get('median_sale_price')

            rec = {
                'Town': town,
                'State': state,
                'Zip': zip_code,
                'Total_Runs': 1,
                'Last_Run_Date': today,
                'Min_Price': price,
                'Max_Price': price,
                'Average_Price': price,
                'Latest_Median_Sale': price,
                'Latest_Median_List': row.get('median_list_price'),
                'Latest_PPSF': row.get('median_ppsf'),
                'Latest_Homes_Sold': row.get('homes_sold'),
                'Latest_Inventory': row.get('inventory'),
                'Data_Source': row.get('source', 'redfin'),
                'Tax_Rate_Per_1000': row.get('tax_rate_per_1000'),
                'Tax_Data_Source': row.get('tax_data_source'),
                'Estimated_Annual_Tax': row.get('estimated_annual_tax'),
                'Estimated_Monthly_Tax': row.get('estimated_monthly_tax'),
                'Min_Monthly_Price': row.get('min_monthly_price'),
                'Max_Monthly_Price': row.get('max_monthly_price'),
                'Avg_Monthly_Price': row.get('avg_monthly_price'),
                'Months_Of_Data': row.get('months_of_data'),
                'Price_Trend': row.get('price_trend')
            }

        updated_records.append(rec)

    # Merge with historical records not updated today
    df_updated = pd.DataFrame(updated_records)

    if not df_hist.empty:
        updated_zips = set(df_updated['Zip'])
        df_unchanged = df_hist[~df_hist['Zip'].isin(updated_zips)]
        df_final = pd.concat([df_updated, df_unchanged],
                             ignore_index=True)
    else:
        df_final = df_updated

    # Sort by average price (most expensive first)
    df_final = df_final.sort_values(
        'Average_Price',
        ascending=False
    ).reset_index(drop=True)

    # Save to CSV
    try:
        active_property_types = property_types if property_types is not None else PROPERTY_TYPES
        _prop_type_suffix = "_".join(pt.replace(" ", "_") for pt in active_property_types) if active_property_types else "All"
        housing_stats_file = HOUSING_STATS_FILE.replace(".csv", f"_{_prop_type_suffix}.csv")

        df_final.to_csv(housing_stats_file, index=False)
        logger.info(
            f"Successfully updated {housing_stats_file} with "
            f"{len(df_updated)} records"
        )
    except PermissionError:
        logger.critical(
            f"Permission denied writing to {housing_stats_file} - "
            f"file may be open in another program"
        )
        raise
    except IOError as e:
        logger.error(f"Failed to save statistics: {e}")
        raise


def collect_housing_data(limit=None, dry_run=False, force_refresh=False, property_types=None):
    """
    Main function to collect and store housing data.

    This function:
    1. Loads zip codes within range of work
    2. Downloads/updates Redfin data if needed
    3. Fetches housing data for each zip
    4. Updates historical statistics

    Args:
        limit (int, optional): Limit processing to first N addresses
        dry_run (bool): If True, simulate collection without real API calls
        force_refresh (bool): If True, remove historical data for all queried zips
                             before updating (useful after changing filters)
        property_types (list): Property types to suffix the stats file and filter records
    """
    logger.info("STARTED: Housing data collection")

    # Download/verify Redfin data
    if not download_redfin_data():
        logger.error("Failed to obtain Redfin data. Aborting.")
        return False

    # Get zip codes within range
    logger.info(
        f"Loading zip codes within {MAX_RANGE} miles of work..."
    )
    zip_data = get_zip_data()
    addresses = get_zips_within_range(WORK_ADDR, zip_data, MAX_RANGE)

    if not addresses:
        logger.error("No addresses found within range. Aborting.")
        return False

    if limit:
        logger.info(f"Limiting processing to first {limit} addresses")
        addresses = addresses[:limit]

    logger.info(f"Found {len(addresses)} addresses within range")

    # Fetch housing data
    if dry_run:
        logger.info(f"DRY RUN: Would have requested housing data for {len(addresses)} locations")
        results = [
            {
                'zip': addr.split()[-1],
                'town': addr.split(',')[0],
                'state': addr.split(',')[1].strip().split()[0],
                'median_sale_price': 500000.0,
                'median_list_price': 525000.0,
                'median_ppsf': 300,
                'homes_sold': 5,
                'inventory': 10,
                'source': 'dry-run',
                'tax_rate_per_1000': 12.0,
                'estimated_annual_tax': 6000.0,
                'estimated_monthly_tax': 500.0
            } for addr in addresses
        ]
    else:
        results, failed_zips = fetch_housing_data(addresses, property_types=property_types)

    # Save failed zips to CSV for scoring module (scoped by property types)
    if not dry_run and failed_zips:
        failed_df = pd.DataFrame(failed_zips)
        active_property_types = property_types if property_types is not None else PROPERTY_TYPES
        _prop_type_suffix = "_".join(pt.replace(" ", "_") for pt in active_property_types) if active_property_types else "All"
        failed_file = os.path.join(RESULTS_DIR, f'housing_filtered_zips-{_prop_type_suffix}.csv')
        try:
            failed_df.to_csv(failed_file, index=False)
            logger.info(f"Saved {len(failed_zips)} filtered zips to {failed_file}")
        except Exception as e:
            logger.warning(f"Failed to save filtered zips: {e}")
    else:
        failed_zips = [] # Ensure initialized for logger below

    # Update statistics
    if results:
        update_statistics(results, force_refresh=force_refresh, queried_addresses=addresses)
        logger.info(
            f"COMPLETED: Housing collection | "
            f"queried={len(addresses)} collected={len(results)} excluded={len(failed_zips)} | "
            f"source=Redfin cost=$0.00"
        )
        return True
    else:
        logger.warning("No housing data collected.")
        return False


if __name__ == "__main__":
    try:
        collect_housing_data()
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
    except Exception as e:
        logger.critical(f"Fatal error: {type(e).__name__}: {e}")
        raise