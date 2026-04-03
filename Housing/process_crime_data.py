import os
import pandas as pd
from constants import (
    CRIME_DATA_FILE, POPULATION_DATA_FILE, CRIME_SCORES_FILE,
    MA_CRIME_SEVERITY_WEIGHTS, HOUSING_LOG_FILE
)
from logging_config import setup_logger

logger = setup_logger(__name__, log_file=HOUSING_LOG_FILE)

def _calculate_score(rate, ideal, max_acc, worst):
    """
    Score crime linearly from 100 to 0.
    rate <= ideal: 100
    ideal < rate <= max_acc: 100 to 50
    max_acc < rate <= worst: 50 to 0
    rate > worst: 0
    """
    if pd.isna(rate):
        return None
    if rate <= ideal:
        return 100.0
    elif rate <= max_acc:
        denom = max(max_acc - ideal, 0.001)
        return 100.0 - ((rate - ideal) / denom) * 50.0
    else:
        if rate >= worst:
            return 0.0
        denom = max(worst - max_acc, 0.001)
        return 50.0 - ((rate - max_acc) / denom) * 50.0

def process_crime_scores():
    logger.info("STARTED: Crime Data Processing")
    if not os.path.exists(CRIME_DATA_FILE) or not os.path.exists(POPULATION_DATA_FILE):
        logger.error("Missing crime or population raw data files.")
        return False

    logger.info("Loading crime data...")
    try:
        crime_df = pd.read_csv(CRIME_DATA_FILE)
    except Exception as e:
        logger.error(f"Failed to load crime data: {e}", exc_info=True)
        return False

    logger.info("Loading population data...")
    try:
        pop_df = pd.read_csv(POPULATION_DATA_FILE)
    except Exception as e:
        logger.error(f"Failed to load population data: {e}", exc_info=True)
        return False

    # Clean population data (remove commas and convert to int)
    pop_df['2024'] = pop_df['2024'].astype(str).str.replace(',', '').astype(int)
    
    # Map weights
    crime_df['Weight'] = crime_df['Arrest Offense'].map(MA_CRIME_SEVERITY_WEIGHTS).fillna(0)
    
    crime_df['Town'] = crime_df['Town'].str.title().str.strip()
    
    # Calculate Severity Counts per town
    high_severity_counts = crime_df[crime_df['Weight'] == 5].groupby('Town').size().reset_index(name='High_Severity_Count')
    medium_severity_counts = crime_df[crime_df['Weight'] == 3].groupby('Town').size().reset_index(name='Medium_Severity_Count')
    low_severity_counts = crime_df[crime_df['Weight'] == 1].groupby('Town').size().reset_index(name='Low_Severity_Count')

    # Aggregate by Town
    town_crimes = crime_df.groupby('Town')['Weight'].sum().reset_index()
    town_crimes.rename(columns={'Weight': 'Total_Crime_Weight'}, inplace=True)
    
    # Merge counts
    town_crimes = pd.merge(town_crimes, high_severity_counts, on='Town', how='left').fillna(0)
    town_crimes = pd.merge(town_crimes, medium_severity_counts, on='Town', how='left').fillna(0)
    town_crimes = pd.merge(town_crimes, low_severity_counts, on='Town', how='left').fillna(0)

    # Merge with population
    pop_df['Municipality'] = pop_df['Municipality'].str.title().str.strip()
    merged = pd.merge(town_crimes, pop_df, left_on='Town', right_on='Municipality', how='inner')
    
    if merged.empty:
        logger.error("Failed to merge crime and population data on Town/Municipality names.")
        return False
        
    # Calculate per capita (per 1000 residents)
    merged['Crime_Rate_Per_1000'] = (merged['Total_Crime_Weight'] / merged['2024']) * 1000
    
    # Normalize to 0-100 score using piecewise linear scaling
    merged['Crime_Score'] = merged['Crime_Rate_Per_1000'].apply(
        lambda r: _calculate_score(r, ideal=0.0, max_acc=15.0, worst=30.0)
    ).round(1)
    
    merged['High_Severity_Per_1000'] = (merged['High_Severity_Count'] / merged['2024']) * 1000
    merged['High_Severity_Score'] = merged['High_Severity_Per_1000'].apply(
        lambda r: _calculate_score(r, ideal=0.0, max_acc=1.0, worst=2.5)
    ).round(1)

    merged['Medium_Severity_Per_1000'] = (merged['Medium_Severity_Count'] / merged['2024']) * 1000
    merged['Medium_Severity_Score'] = merged['Medium_Severity_Per_1000'].apply(
        lambda r: _calculate_score(r, ideal=0.0, max_acc=3.0, worst=7.0)
    ).round(1)

    merged['Low_Severity_Per_1000'] = (merged['Low_Severity_Count'] / merged['2024']) * 1000
    merged['Low_Severity_Score'] = merged['Low_Severity_Per_1000'].apply(
        lambda r: _calculate_score(r, ideal=0.0, max_acc=5.0, worst=11.0)
    ).round(1)
    
    output_df = merged.rename(columns={'2024': 'Population'})
    output_df = output_df[['Town', 'Crime_Score', 'Crime_Rate_Per_1000', 'Total_Crime_Weight', 'Population', 
                           'High_Severity_Score', 'Medium_Severity_Score', 'Low_Severity_Score',
                           'High_Severity_Per_1000', 'Medium_Severity_Per_1000', 'Low_Severity_Per_1000',
                           'High_Severity_Count', 'Medium_Severity_Count', 'Low_Severity_Count']]
    
    try:
        output_df.to_csv(CRIME_SCORES_FILE, index=False)
        logger.info(f"Successfully processed crime data and saved to {CRIME_SCORES_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save crime scores: {e}", exc_info=True)
        return False
    finally:
        logger.info("COMPLETED: Crime Data Processing")

if __name__ == "__main__":
    process_crime_scores()
