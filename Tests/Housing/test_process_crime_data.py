import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from Housing.process_crime_data import process_crime_scores
from constants import MA_CRIME_SEVERITY_WEIGHTS

@pytest.fixture
def mock_crime_df():
    return pd.DataFrame({
        'Town': ['Lexington', 'Bedford', 'Bedford'],
        'Arrest Offense': ['Aggravated Assault', 'Shoplifting', 'Unknown Offense']
    })

@pytest.fixture
def mock_pop_df():
    return pd.DataFrame({
        'Municipality': ['Lexington', 'Bedford'],
        '2024': ['34,000', '14,000']
    })

@patch('Housing.process_crime_data.os.path.exists')
@patch('Housing.process_crime_data.pd.read_csv')
@patch('Housing.process_crime_data.pd.DataFrame.to_csv')
def test_process_crime_scores_success(mock_to_csv, mock_read_csv, mock_exists, mock_crime_df, mock_pop_df):
    mock_exists.return_value = True
    
    # Mock read_csv to return crime_df for first call, pop_df for second
    mock_read_csv.side_effect = [mock_crime_df, mock_pop_df]
    
    success = process_crime_scores()
    assert success is True
    
    # Verify the output DataFrame was passed to to_csv
    assert mock_to_csv.called
    output_df = mock_to_csv.call_args[0][0] if not mock_to_csv.call_args else mock_to_csv.call_args_list[0][0]
    # Actually mock_to_csv is bound to the DataFrame instance.
    # The dataframe was saved. We can inspect process_crime_scores logic by patching pd.DataFrame.to_csv
    # and seeing the shape or data.
    
@patch('Housing.process_crime_data.os.path.exists')
def test_process_crime_scores_missing_files(mock_exists):
    mock_exists.return_value = False
    
    success = process_crime_scores()
    assert success is False
