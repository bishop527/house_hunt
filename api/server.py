import os
import sys
import json
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Add parent directory to path so we can import House Hunt modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from constants import SCORE_CONFIG_FILE
from Score.calculate_scores import LocationScorer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="House Hunt Dashboard API")

# Ensure ui directory exists
ui_dir = os.path.join(parent_dir, "ui")
if not os.path.exists(ui_dir):
    os.makedirs(ui_dir)

# Mount static files
app.mount("/static", StaticFiles(directory=ui_dir), name="static")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(ui_dir, "index.html"))

@app.get("/api/config")
def get_config():
    """Return the current default config from disk."""
    if os.path.exists(SCORE_CONFIG_FILE):
        with open(SCORE_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

@app.post("/api/config/save")
async def save_config(request: Request):
    """Save the provided config back to disk."""
    payload = await request.json()
    config = payload.get("config")
    if config:
        with open(SCORE_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return {"status": "success", "message": "Config saved"}
    return JSONResponse(status_code=400, content={"error": "No config provided"})

@app.post("/api/score")
async def score_locations(request: Request):
    """
    Accepts a config dictionary and a grouping mode.
    Runs the scoring engine in-memory and returns the results.
    """
    payload = await request.json()
    config_dict = payload.get("config", {})
    grouping_mode = payload.get("grouping_mode", "zip") # "zip" or "town"
    
    try:
        scorer = LocationScorer(config_dict=config_dict)
        if not scorer.load_data():
            return JSONResponse(status_code=500, content={"error": "Failed to load data. Have you run --commute and --housing?"})
            
        df = scorer.score_all_locations()
        
        if df is None or df.empty:
            return {"data": []}
            
        # Handle grouping
        import pandas as pd
        if grouping_mode == "town":
            def join_zips(x):
                return ", ".join(sorted(list(set(str(val).zfill(5) for val in x if val is not None))))

            agg_dict = {
                'Zip': join_zips,
                'Avg_Commute_Min': 'mean',
                'Min_Commute_Min': 'mean',
                'Max_Commute_Min': 'mean',
                'Distance_Miles': 'mean',
                'Median_Price': 'mean',
                'Price_Per_SqFt': 'mean',
                'Tax_Rate_Per_1000': 'mean',
                'Crime_Score': 'mean',
                'High_Severity_Score': 'mean',
                'Medium_Severity_Score': 'mean',
                'Low_Severity_Score': 'mean',
                'Population': 'mean',
                'Homes_Sold': 'sum',
                'Inventory': 'sum'
            }
            
            # Map work2 if enabled
            if 'Work2_Avg_Time' in df.columns:
                agg_dict['Work2_Avg_Time'] = 'mean'
            if 'Work2_Distance' in df.columns:
                agg_dict['Work2_Distance'] = 'mean'
                
            agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
            
            df_towns = df.groupby(['Town', 'State'], as_index=False).agg(agg_dict)
            
            results = []
            weights = config_dict.get('weights', {})
            c_w = weights.get('commute', 0.5)
            h_w = weights.get('housing', 0.35)
            cr_w = weights.get('crime', 0.15)
            
            for _, row in df_towns.iterrows():
                row_mapped = row.copy()
                row_mapped['Average_Time'] = row['Avg_Commute_Min']
                row_mapped['Latest_Median_Sale'] = row['Median_Price']
                row_mapped['Latest_PPSF'] = row['Price_Per_SqFt']
                
                # These expect dict/series with specific keys
                commute_scores = scorer.calculate_commute_score(row_mapped)
                housing_scores = scorer.calculate_housing_score(row_mapped)
                crime_score_val = row.get('Crime_Score')
                
                if pd.isna(crime_score_val):
                    norm = c_w + h_w
                    total_score = (
                        commute_scores['commute_score'] * (c_w / norm) +
                        housing_scores['housing_score'] * (h_w / norm)
                    )
                    crime_score_val = None
                else:
                    total_score = (
                        commute_scores['commute_score'] * c_w +
                        housing_scores['housing_score'] * h_w +
                        crime_score_val * cr_w
                    )
                
                tier = scorer._assign_tier(total_score)
                
                row_mapped['Commute_Score'] = commute_scores['commute_score']
                row_mapped['Housing_Score'] = housing_scores['housing_score']
                row_mapped['Price_Score'] = housing_scores['price_score']
                row_mapped['PPSF_Score'] = housing_scores['ppsf_score']
                row_mapped['Tax_Score'] = housing_scores['tax_score']
                row_mapped['Total_Score'] = round(total_score, 1)
                row_mapped['Tier'] = tier
                
                results.append(row_mapped)
                
            df = pd.DataFrame(results)
            df = df.sort_values(['Total_Score', 'Town'], ascending=[False, True]).reset_index(drop=True)
            df['Rank'] = range(1, len(df) + 1)
            
        # Convert NaN to None for JSON serialization
        df = df.where(df.notnull(), None)
        
        return {"data": df.to_dict(orient='records')}
        
    except Exception as e:
        logger.error(f"Error during scoring: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})
