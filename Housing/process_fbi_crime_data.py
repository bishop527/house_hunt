import os
import pandas as pd
from constants import (
    RAW_DIR, POPULATION_DATA_FILE, FBI_CRIME_SCORES_FILE, HOUSING_LOG_FILE
)
from logging_config import setup_logger

logger = setup_logger(__name__, log_file=HOUSING_LOG_FILE)

def pass_fbi_mapping(offense_name):
    """
    Map general FBI NIBRS offense descriptors to our severity weights.
    Returns 5 (High), 3 (Medium), 1 (Low), or 0 for ignored anomalies.
    """
    offense = str(offense_name).lower()
    
    # High Severity
    if any(k in offense for k in ['murder', 'homicide', 'rape', 'robbery', 'aggravated assault', 'kidnapping']):
        return 5
    # Medium Severity
    elif any(k in offense for k in ['burglary', 'motor vehicle theft', 'arson', 'weapon']):
        return 3
    # Low Severity
    elif any(k in offense for k in ['larceny', 'theft', 'assault', 'fraud', 'vandalism', 'drug']):
        return 1
    return 0

def _calculate_score(rate, ideal, max_acc, worst):
    """
    Score crime linearly from 100 to 0.
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

def process_fbi_crime_scores():
    logger.info("STARTED: FBI Crime Data Processing (NIBRS Relational)")
    
    fbi_dir = os.path.join(RAW_DIR, '..', 'Crime_Data')
    agencies_file = os.path.join(fbi_dir, 'agencies.csv')
    incidents_file = os.path.join(fbi_dir, 'NIBRS_incident.csv')
    offenses_file = os.path.join(fbi_dir, 'NIBRS_OFFENSE.csv')
    offense_types_file = os.path.join(fbi_dir, 'NIBRS_OFFENSE_TYPE.csv')

    required_files = [agencies_file, incidents_file, offenses_file, offense_types_file, POPULATION_DATA_FILE]
    for required_file in required_files:
        if not os.path.exists(required_file):
            logger.error(f"Missing required file: {required_file}")
            return False

    logger.info("Loading FBI NIBRS tables and population data...")
    try:
        # Load tables
        agencies = pd.read_csv(agencies_file)
        # Filter to MA if standard
        if 'state_abbr' in agencies.columns:
            agencies = agencies[agencies['state_abbr'] == 'MA'].copy()
        
        # Clean town name from agency name
        if 'pub_agency_name' in agencies.columns:
            agencies['Town'] = agencies['pub_agency_name'].str.replace(' Police Department', '', case=False)
            agencies['Town'] = agencies['Town'].str.replace(' PD', '', case=False)
            agencies['Town'] = agencies['Town'].str.title().str.strip()
        else:
            logger.error("Expected 'pub_agency_name' column in agencies.csv")
            return False

        incidents = pd.read_csv(incidents_file)
        offenses = pd.read_csv(offenses_file)
        offense_types = pd.read_csv(offense_types_file)

        # Merge Pipeline
        # 1. Map offense code to their names
        df_offenses = pd.merge(offenses, offense_types, on='offense_code', how='left')
        
        # 2. Join offenses to incidents to get agency_id
        df_incidents = pd.merge(df_offenses, incidents[['incident_id', 'agency_id']], on='incident_id', how='left')
        
        # 3. Join incidents to agencies to get Town
        crime_df = pd.merge(df_incidents, agencies[['agency_id', 'Town']], on='agency_id', how='inner')
        
        # Bring in population
        pop_df = pd.read_csv(POPULATION_DATA_FILE)
        pop_df['2024'] = pop_df['2024'].astype(str).str.replace(',', '').astype(int)
        pop_df['Municipality'] = pop_df['Municipality'].str.title().str.strip()

    except Exception as e:
        logger.error(f"Failed to load or merge FBI logic: {e}", exc_info=True)
        return False

    # Map weights based on detailed NIBRS offense names
    crime_df['Weight'] = crime_df['offense_name'].apply(pass_fbi_mapping)
    
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
    merged = pd.merge(town_crimes, pop_df, left_on='Town', right_on='Municipality', how='inner')
    
    if merged.empty:
        logger.warning("FBI dataset yielded no valid location overlaps after agency name cleaning.")
        return False
        
    # Calculate per capita (per 1000 residents)
    merged['Crime_Rate_Per_1000'] = (merged['Total_Crime_Weight'] / merged['2024']) * 1000
    
    # Normalize to 0-100 score using piecewise linear scaling
    merged['Crime_Score'] = merged['Crime_Rate_Per_1000'].apply(
        lambda r: _calculate_score(r, ideal=0.0, max_acc=35.0, worst=70.0)
    ).round(1)
    
    merged['High_Severity_Per_1000'] = (merged['High_Severity_Count'] / merged['2024']) * 1000
    merged['High_Severity_Score'] = merged['High_Severity_Per_1000'].apply(
        lambda r: _calculate_score(r, ideal=0.0, max_acc=3.0, worst=6.0)
    ).round(1)

    merged['Medium_Severity_Per_1000'] = (merged['Medium_Severity_Count'] / merged['2024']) * 1000
    merged['Medium_Severity_Score'] = merged['Medium_Severity_Per_1000'].apply(
        lambda r: _calculate_score(r, ideal=0.0, max_acc=3.0, worst=7.0)
    ).round(1)

    merged['Low_Severity_Per_1000'] = (merged['Low_Severity_Count'] / merged['2024']) * 1000
    merged['Low_Severity_Score'] = merged['Low_Severity_Per_1000'].apply(
        lambda r: _calculate_score(r, ideal=0.0, max_acc=18.0, worst=35.0)
    ).round(1)
    
    output_df = merged.rename(columns={'2024': 'Population'})
    output_df = output_df[['Town', 'Crime_Score', 'Crime_Rate_Per_1000', 'Total_Crime_Weight', 'Population', 
                           'High_Severity_Score', 'Medium_Severity_Score', 'Low_Severity_Score',
                           'High_Severity_Per_1000', 'Medium_Severity_Per_1000', 'Low_Severity_Per_1000',
                           'High_Severity_Count', 'Medium_Severity_Count', 'Low_Severity_Count']]
    
    try:
        output_df.to_csv(FBI_CRIME_SCORES_FILE, index=False)
        logger.info(f"Successfully processed FBI crime data and saved to {FBI_CRIME_SCORES_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save FBI crime scores: {e}", exc_info=True)
        return False
    finally:
        logger.info("COMPLETED: FBI Crime Data Processing")

if __name__ == "__main__":
    process_fbi_crime_scores()
