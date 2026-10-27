import os
import json
import pytest
import pandas as pd
from unittest.mock import patch
from Score.generate_dashboard import generate_dashboard

@pytest.fixture
def temp_environment(tmp_path):
    """
    Set up a temporary environment with mock files for dashboard generation.
    """
    results_dir = tmp_path / "Results"
    results_dir.mkdir()
    
    config_file = tmp_path / "score_config.json"
    output_file = tmp_path / "dashboard.html"
    
    # Create mock scored locations files
    mock_data = {
        'Town': ['Southborough', 'Dedham'],
        'State': ['MA', 'MA'],
        'Zip': ['01745', '02026'],
        'Total_Score': [84.1, 83.1],
        'Tier': ['B+', 'B+'],
        'Median_Price': [728750, 766000],
        'Avg_Commute_Min': [34.01, 25.62],
        'Crime_Score': [87.3, 56.5]
    }
    df = pd.DataFrame(mock_data)
    
    # We create Single_Family and Condo, leaving Townhouse missing to test robust handling
    df.to_csv(results_dir / "scored_locations-Single_Family.csv", index=False)
    df.to_csv(results_dir / "scored_locations-Condo.csv", index=False)
    
    # Create mock config file
    mock_config = {
        "weights": {
            "commute": 0.50,
            "housing": 0.35,
            "crime": 0.15
        },
        "housing_preferences": {
            "budget_min": 500000,
            "budget_max": 800000,
            "budget_ideal": 600000
        }
    }
    with open(config_file, 'w') as f:
        json.dump(mock_config, f)
        
    # Return the patched paths
    return {
        'RESULTS_DIR': str(results_dir),
        'SCORE_CONFIG_FILE': str(config_file),
        'DASHBOARD_OUTPUT_FILE': str(output_file),
        'results_dir_path': results_dir,
        'config_file_path': config_file,
        'output_file_path': output_file
    }

def test_generate_dashboard_success(temp_environment):
    """
    Test that the dashboard is generated successfully and contains correct embedded data.
    """
    env = temp_environment
    
    with patch('Score.generate_dashboard.RESULTS_DIR', env['RESULTS_DIR']), \
         patch('Score.generate_dashboard.SCORE_CONFIG_FILE', env['SCORE_CONFIG_FILE']), \
         patch('Score.generate_dashboard.DASHBOARD_OUTPUT_FILE', env['DASHBOARD_OUTPUT_FILE']):
         
        success = generate_dashboard()
        assert success is True
        assert os.path.exists(env['DASHBOARD_OUTPUT_FILE'])
        
        # Read output file and check content
        with open(env['DASHBOARD_OUTPUT_FILE'], 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Verify embedded data contains loaded property types
            assert "Single Family" in content
            assert "Condo" in content
            # Townhouse wasn't created, so it shouldn't be in the active tabs
            assert "Townhouse" not in content 
            
            # Verify config elements are embedded
            assert '"budget_ideal": 600000' in content
            assert '"commute": 0.5' in content
            
            # Verify sample data values are embedded
            assert '01745' in content
            assert 'Southborough' in content

def test_generate_dashboard_no_data(temp_environment):
    """
    Test that dashboard generation fails gracefully if no CSV data files are present.
    """
    env = temp_environment
    
    # Remove the mock CSV files
    os.remove(os.path.join(env['RESULTS_DIR'], "scored_locations-Single_Family.csv"))
    os.remove(os.path.join(env['RESULTS_DIR'], "scored_locations-Condo.csv"))
    
    with patch('Score.generate_dashboard.RESULTS_DIR', env['RESULTS_DIR']), \
         patch('Score.generate_dashboard.SCORE_CONFIG_FILE', env['SCORE_CONFIG_FILE']), \
         patch('Score.generate_dashboard.DASHBOARD_OUTPUT_FILE', env['DASHBOARD_OUTPUT_FILE']):
         
        success = generate_dashboard()
        assert success is False
        assert not os.path.exists(env['DASHBOARD_OUTPUT_FILE'])
