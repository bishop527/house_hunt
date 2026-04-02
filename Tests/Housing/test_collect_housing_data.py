"""
Unit tests for Housing/collect_housing_data.py

Tests housing data collection with mocked Redfin data and property taxes.
Run with: python -m pytest Tests/Housing/test_collect_housing_data.py -v
"""
import os
import sys
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from Housing.collect_housing_data import (
    load_property_tax_rates,
    get_property_tax_rate,
    enrich_with_property_tax,
    get_redfin_data,
    get_historical_redfin_data,
    fetch_housing_data,
    update_statistics
)


# --- Fixtures ---

@pytest.fixture
def mock_property_tax_csv():
    """Sample property tax CSV data (without Source column)"""
    return """Town,State,Tax_Rate_Per_1000,Fiscal_Year,Last_Updated
Lexington,MA,17.85,2025,2025-01-15
Bedford,MA,16.42,2025,2025-01-15
Pawtucket,RI,28.45,2025,2025-01-15
Manchester,NH,21.34,2025,2025-01-15"""


@pytest.fixture
def mock_redfin_csv():
    """Sample Redfin CSV data with CAPS columns"""
    return """PERIOD_END\tREGION_TYPE\tREGION\tSTATE\tPROPERTY_TYPE\tMEDIAN_SALE_PRICE\tMEDIAN_LIST_PRICE\tMEDIAN_PPSF\tHOMES_SOLD\tINVENTORY\tMONTHS_OF_SUPPLY
2025-01-31\tzip code\tZip Code: 02421\tMassachusetts\tSingle Family Residential\t850000\t875000\t425\t12\t8\t2.5
2025-01-31\tzip code\tZip Code: 01730\tMassachusetts\tSingle Family Residential\t675000\t699000\t380\t8\t5\t3.1
2025-01-31\tzip code\tZip Code: 99999\tMassachusetts\tSingle Family Residential\t500000\t525000\t350\t2\t1\t1.5
2024-12-31\tzip code\tZip Code: 02421\tMassachusetts\tSingle Family Residential\t825000\t850000\t420\t10\t7\t2.3
2024-11-30\tzip code\tZip Code: 02421\tMassachusetts\tSingle Family Residential\t800000\t825000\t415\t9\t6\t2.1"""


@pytest.fixture
def sample_addresses():
    """Sample address list"""
    return [
        "Lexington, MA 02421",
        "Bedford, MA 01730",
        "Unknown Town, MA 99999"
    ]


# --- Test load_property_tax_rates ---

def test_load_property_tax_rates_success(tmp_path, mock_property_tax_csv,
                                         monkeypatch):
    """Test successful loading of property tax rates"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    df = load_property_tax_rates()

    assert len(df) == 4
    assert 'Lexington' in df['Town'].values
    assert 'Pawtucket' in df['Town'].values


def test_load_property_tax_rates_missing_file(tmp_path, monkeypatch):
    """Test handling of missing property tax file"""
    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tmp_path / "nonexistent.csv")
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    df = load_property_tax_rates()

    assert df.empty


def test_load_property_tax_rates_caching(tmp_path, mock_property_tax_csv,
                                         monkeypatch):
    """Test that tax rates are cached after first load"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    # First load
    df1 = load_property_tax_rates()

    # Delete file
    tax_file.unlink()

    # Second load should use cache (not error)
    df2 = load_property_tax_rates()

    assert len(df2) == 4  # Still has data from cache


# --- Test get_property_tax_rate ---

def test_get_property_tax_rate_found(tmp_path, mock_property_tax_csv,
                                     monkeypatch):
    """Test getting tax rate for town in database"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    result = get_property_tax_rate('Lexington', 'MA')

    assert result is not None
    assert result['tax_rate_per_1000'] == 17.85
    assert result['fiscal_year'] == 2025
    assert result['tax_data_source'] == 'database'


def test_get_property_tax_rate_case_insensitive(tmp_path,
                                                mock_property_tax_csv,
                                                monkeypatch):
    """Test that town name lookup is case insensitive"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    # Try different cases
    result1 = get_property_tax_rate('lexington', 'MA')
    result2 = get_property_tax_rate('LEXINGTON', 'MA')
    result3 = get_property_tax_rate('LeXiNgToN', 'MA')

    assert result1['tax_rate_per_1000'] == 17.85
    assert result2['tax_rate_per_1000'] == 17.85
    assert result3['tax_rate_per_1000'] == 17.85


def test_get_property_tax_rate_ma_default(tmp_path, mock_property_tax_csv,
                                          monkeypatch):
    """Test MA default rate used when town not found"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )
    monkeypatch.setattr(
        'Housing.collect_housing_data.DEFAULT_MA_TAX_RATE',
        17.50
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    result = get_property_tax_rate('Unknown Town', 'MA')

    assert result is not None
    assert result['tax_rate_per_1000'] == 17.50
    assert result['fiscal_year'] == 'N/A (default)'
    assert result['tax_data_source'] == 'MA_default'


def test_get_property_tax_rate_ri_default(tmp_path, mock_property_tax_csv,
                                          monkeypatch):
    """Test RI default rate used when town not found"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )
    monkeypatch.setattr(
        'Housing.collect_housing_data.DEFAULT_RI_TAX_RATE',
        28.00
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    result = get_property_tax_rate('Unknown Town', 'RI')

    assert result['tax_rate_per_1000'] == 28.00
    assert result['tax_data_source'] == 'RI_default'


def test_get_property_tax_rate_nh_default(tmp_path, mock_property_tax_csv,
                                          monkeypatch):
    """Test NH default rate used when town not found"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )
    monkeypatch.setattr(
        'Housing.collect_housing_data.DEFAULT_NH_TAX_RATE',
        22.00
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    result = get_property_tax_rate('Unknown Town', 'NH')

    assert result['tax_rate_per_1000'] == 22.00
    assert result['tax_data_source'] == 'NH_default'


def test_get_property_tax_rate_unknown_state_fallback(tmp_path,
                                                      mock_property_tax_csv,
                                                      monkeypatch):
    """Test fallback to MA default for unknown states"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )
    monkeypatch.setattr(
        'Housing.collect_housing_data.DEFAULT_MA_TAX_RATE',
        17.50
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    result = get_property_tax_rate('Some Town', 'CA')

    assert result['tax_rate_per_1000'] == 17.50


# --- Test enrich_with_property_tax ---

def test_enrich_with_property_tax_success(tmp_path, mock_property_tax_csv,
                                          monkeypatch):
    """Test enrichment with property tax data"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    data = {
        'town': 'Lexington',
        'state': 'MA',
        'median_sale_price': 850000
    }

    result = enrich_with_property_tax(data)

    assert result['tax_rate_per_1000'] == 17.85
    assert result['tax_data_source'] == 'database'
    # 850000 * 17.85 / 1000 = 15172.50
    assert result['estimated_annual_tax'] == 15172.50
    # 15172.50 / 12 = 1264.38
    assert result['estimated_monthly_tax'] == 1264.38


def test_enrich_with_property_tax_default_rate(tmp_path,
                                               mock_property_tax_csv,
                                               monkeypatch):
    """Test enrichment uses default when town not found"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )
    monkeypatch.setattr(
        'Housing.collect_housing_data.DEFAULT_MA_TAX_RATE',
        17.50
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    data = {
        'town': 'Unknown Town',
        'state': 'MA',
        'median_sale_price': 600000
    }

    result = enrich_with_property_tax(data)

    assert result['tax_rate_per_1000'] == 17.50
    assert result['tax_data_source'] == 'MA_default'
    # 600000 * 17.50 / 1000 = 10500
    assert result['estimated_annual_tax'] == 10500.00


def test_enrich_with_property_tax_missing_price(tmp_path,
                                                mock_property_tax_csv,
                                                monkeypatch):
    """Test enrichment when median price is missing"""
    tax_file = tmp_path / "property_tax_rates.csv"
    tax_file.write_text(mock_property_tax_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.PROPERTY_TAX_FILE',
        str(tax_file)
    )

    # Clear cache
    import Housing.collect_housing_data
    Housing.collect_housing_data._property_tax_cache = None

    data = {
        'town': 'Lexington',
        'state': 'MA',
        'median_sale_price': None
    }

    result = enrich_with_property_tax(data)

    assert result['tax_rate_per_1000'] == 17.85
    assert 'estimated_annual_tax' not in result


def test_enrich_with_property_tax_missing_town_state(monkeypatch):
    """Test enrichment with missing town/state"""
    data = {
        'median_sale_price': 600000
    }

    result = enrich_with_property_tax(data)

    # Should return unchanged
    assert 'tax_rate_per_1000' not in result


# --- Test get_redfin_data ---

def test_get_redfin_data_success(tmp_path, mock_redfin_csv, monkeypatch):
    """Test successful retrieval of Redfin data"""
    redfin_file = tmp_path / "redfin_market_data.csv"
    redfin_file.write_text(mock_redfin_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.REDFIN_DATA_FILE',
        str(redfin_file)
    )
    monkeypatch.setattr(
        'Housing.collect_housing_data.MIN_SAMPLE_SIZE',
        5
    )

    redfin_df = pd.read_csv(str(redfin_file), sep='\t')
    # Explicitly pass property types to match the mock data's "Single Family Residential"
    result = get_redfin_data('02421', redfin_df, property_types=['Single Family'])

    assert result is not None
    assert result['zip'] == '02421'
    assert result['median_sale_price'] == 850000
    assert result['median_list_price'] == 875000
    assert result['homes_sold'] == 12
    assert result['inventory'] == 8


def test_get_redfin_data_insufficient_sample(tmp_path, mock_redfin_csv,
                                             monkeypatch):
    """Test that data with low sample size is rejected"""
    redfin_file = tmp_path / "redfin_market_data.csv"
    redfin_file.write_text(mock_redfin_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.REDFIN_DATA_FILE',
        str(redfin_file)
    )
    monkeypatch.setattr(
        'Housing.collect_housing_data.MIN_SAMPLE_SIZE',
        5
    )

    redfin_df = pd.read_csv(str(redfin_file), sep='\t')
    # Zip 99999 has only 2 homes sold
    result = get_redfin_data('99999', redfin_df)

    assert result is None


def test_get_redfin_data_not_found(tmp_path, mock_redfin_csv, monkeypatch):
    """Test handling of zip not in Redfin data"""
    redfin_file = tmp_path / "redfin_market_data.csv"
    redfin_file.write_text(mock_redfin_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.REDFIN_DATA_FILE',
        str(redfin_file)
    )

    redfin_df = pd.read_csv(str(redfin_file), sep='\t')
    result = get_redfin_data('00000', redfin_df)

    assert result is None


def test_get_redfin_data_nan_inventory(tmp_path, monkeypatch):
    """Test handling of NaN inventory value"""
    csv_with_nan = """PERIOD_END\tREGION_TYPE\tREGION\tSTATE\tPROPERTY_TYPE\tMEDIAN_SALE_PRICE\tMEDIAN_LIST_PRICE\tMEDIAN_PPSF\tHOMES_SOLD\tINVENTORY\tMONTHS_OF_SUPPLY
2025-01-31\tzip code\tZip Code: 02421\tMassachusetts\tSingle Family Residential\t850000\t875000\t425\t12\tnan\t2.5"""

    redfin_file = tmp_path / "redfin_market_data.csv"
    redfin_file.write_text(csv_with_nan)

    monkeypatch.setattr(
        'Housing.collect_housing_data.REDFIN_DATA_FILE',
        str(redfin_file)
    )
    monkeypatch.setattr(
        'Housing.collect_housing_data.MIN_SAMPLE_SIZE',
        5
    )

    redfin_df = pd.read_csv(str(redfin_file), sep='\t')
    # Explicitly pass property types to match mock data
    result = get_redfin_data('02421', redfin_df, property_types=['Single Family'])

    assert result is not None
    assert result['inventory'] == 0  # NaN converted to 0


def test_get_redfin_data_nan_price(tmp_path, monkeypatch):
    """Test that safe_weighted_avg handles NaN prices correctly without crashing or skewing"""
    csv_with_nan_price = """PERIOD_END\tREGION_TYPE\tREGION\tSTATE\tPROPERTY_TYPE\tMEDIAN_SALE_PRICE\tMEDIAN_LIST_PRICE\tMEDIAN_PPSF\tHOMES_SOLD\tINVENTORY\tMONTHS_OF_SUPPLY
2025-01-31\tzip code\tZip Code: 02421\tMassachusetts\tSingle Family Residential\t850000\t875000\t425\t10\t8\t2.5
2025-01-31\tzip code\tZip Code: 02421\tMassachusetts\tCondo/Co-op\tnan\t500000\t300\t10\t5\t2.0"""

    redfin_file = tmp_path / "redfin_market_data.csv"
    redfin_file.write_text(csv_with_nan_price)

    monkeypatch.setattr(
        'Housing.collect_housing_data.REDFIN_DATA_FILE',
        str(redfin_file)
    )
    monkeypatch.setattr(
        'Housing.collect_housing_data.MIN_SAMPLE_SIZE',
        5
    )

    redfin_df = pd.read_csv(str(redfin_file), sep='\t')
    result = get_redfin_data('02421', redfin_df, property_types=['Single Family', 'Condo'])

    assert result is not None
    # 20 homes total, but only 10 have valid sale price. 
    # Average sale price is just the valid 850k.
    assert result['median_sale_price'] == 850000
    # Both have valid list prices. Avg list: (875k*10 + 500k*10) / 20 = 687500
    assert result['median_list_price'] == 687500


# --- Test get_historical_redfin_data ---

def test_get_historical_redfin_data_success(tmp_path, mock_redfin_csv,
                                            monkeypatch):
    """Test getting historical monthly data"""
    redfin_file = tmp_path / "redfin_market_data.csv"
    redfin_file.write_text(mock_redfin_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.REDFIN_DATA_FILE',
        str(redfin_file)
    )

    redfin_df = pd.read_csv(str(redfin_file), sep='\t')
    result = get_historical_redfin_data('02421', redfin_df, months=3, property_types=['Single Family'])

    assert result is not None
    assert result['months_of_data'] == 3
    assert result['min_monthly_price'] == 800000
    assert result['max_monthly_price'] == 850000
    assert result['avg_monthly_price'] == 825000  # (850 + 825 + 800) / 3


def test_get_historical_redfin_data_trend_increasing(tmp_path,
                                                     mock_redfin_csv,
                                                     monkeypatch):
    """Test price trend detection - increasing"""
    redfin_file = tmp_path / "redfin_market_data.csv"
    redfin_file.write_text(mock_redfin_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.REDFIN_DATA_FILE',
        str(redfin_file)
    )

    redfin_df = pd.read_csv(str(redfin_file), sep='\t')
    result = get_historical_redfin_data('02421', redfin_df, months=3, property_types=['Single Family'])

    # 850000 > 800000 * 1.05 = increasing
    assert result['price_trend'] == 'increasing'


def test_get_historical_redfin_data_not_found(tmp_path, mock_redfin_csv,
                                              monkeypatch):
    """Test handling of zip not found"""
    redfin_file = tmp_path / "redfin_market_data.csv"
    redfin_file.write_text(mock_redfin_csv)

    monkeypatch.setattr(
        'Housing.collect_housing_data.REDFIN_DATA_FILE',
        str(redfin_file)
    )

    redfin_df = pd.read_csv(str(redfin_file), sep='\t')
    result = get_historical_redfin_data('00000', redfin_df, months=12)

    assert result is None


# --- Test update_statistics ---

def test_update_statistics_new_zip(tmp_path, monkeypatch):
    """Test creating new record in statistics"""
    stats_file = tmp_path / "historical_housing_stats.csv"

    monkeypatch.setattr(
        'Housing.collect_housing_data.HOUSING_STATS_FILE',
        str(stats_file)
    )

    results = [
        {
            'town': 'Lexington',
            'state': 'MA',
            'zip': '02421',
            'median_sale_price': 850000,
            'median_list_price': 875000,
            'homes_sold': 12,
            'inventory': 8,
            'tax_rate_per_1000': 17.85,
            'tax_data_source': 'database',
            'estimated_annual_tax': 15172.50,
            'estimated_monthly_tax': 1264.38
        }
    ]

    with patch('Housing.collect_housing_data.load_historical_data') as mock_load:
        mock_load.return_value = pd.DataFrame()

        with patch('Housing.collect_housing_data.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 1)
            update_statistics(results)

    # Verify file was created with suffix
    # Property types defaults to ['All'] in constants, so suffix is _All
    expected_file = tmp_path / "historical_housing_stats_All.csv"
    assert expected_file.exists()

    df = pd.read_csv(expected_file, dtype={'Zip': str})
    assert len(df) == 1
    assert df.iloc[0]['Zip'] == '02421'
    assert df.iloc[0]['Average_Price'] == 850000
    assert df.iloc[0]['Tax_Data_Source'] == 'database'


def test_update_statistics_existing_zip(tmp_path, monkeypatch):
    """Test updating existing record"""
    # Create existing stats
    existing_stats = """Town,State,Zip,Total_Runs,Last_Run_Date,Min_Price,Max_Price,Average_Price,Latest_Median_Sale,Tax_Rate_Per_1000,Tax_Data_Source
Lexington,MA,02421,1,2026-01-01,850000,850000,850000,850000,17.85,database"""

    stats_file = tmp_path / "historical_housing_stats.csv"
    stats_file.write_text(existing_stats)

    monkeypatch.setattr(
        'Housing.collect_housing_data.HOUSING_STATS_FILE',
        str(stats_file)
    )

    results = [
        {
            'town': 'Lexington',
            'state': 'MA',
            'zip': '02421',
            'median_sale_price': 900000,  # Higher price
            'tax_rate_per_1000': 17.85,
            'tax_data_source': 'database'
        }
    ]

    with patch('Housing.collect_housing_data.load_csv_with_zip') as mock_load:
        mock_load.return_value = pd.read_csv(stats_file, dtype={'Zip': str})

        with patch('Housing.collect_housing_data.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 1)
            update_statistics(results)

    # Check for suffixed file
    expected_file = tmp_path / "historical_housing_stats_All.csv"
    df = pd.read_csv(expected_file, dtype={'Zip': str})
    assert df.iloc[0]['Total_Runs'] == 2
    assert df.iloc[0]['Max_Price'] == 900000
    # Average: (850000 + 900000) / 2 = 875000
    assert df.iloc[0]['Average_Price'] == 875000.0


def test_update_statistics_empty_results(monkeypatch):
    """Test handling of empty results"""
    # Should not raise error
    update_statistics([])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])