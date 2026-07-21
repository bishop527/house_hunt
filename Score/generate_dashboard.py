import os
import json
import pandas as pd
from constants import RESULTS_DIR, SCORE_CONFIG_FILE, SCORE_REPORT_FILE

# Output path for the dashboard
DASHBOARD_OUTPUT_FILE = os.path.join(os.path.dirname(SCORE_REPORT_FILE), "dashboard.html")

def generate_dashboard():
    """
    Compile scored locations CSV files and configuration into a single,
    self-contained HTML dashboard with client-side scoring logic.
    """
    # 1. Load configuration defaults
    config = {}
    if os.path.exists(SCORE_CONFIG_FILE):
        try:
            with open(SCORE_CONFIG_FILE, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")
    
    # 2. Load scored locations for each property type
    property_types = ['Single_Family', 'Condo', 'Townhouse']
    data_by_type = {}
    
    for pt in property_types:
        csv_file = os.path.join(RESULTS_DIR, f"scored_locations-{pt}.csv")
        pt_display = pt.replace('_', ' ')
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file, dtype={'Zip': str})
                if 'Zip' in df.columns:
                    df['Zip'] = df['Zip'].fillna('').astype(str).str.zfill(5)
                # Convert NaN to None for proper JSON serialization
                df = df.where(df.notnull(), None)
                data_by_type[pt_display] = df.to_dict(orient='records')
                print(f"Loaded {len(df)} records for {pt_display}")
            except Exception as e:
                print(f"Warning: Failed to load {csv_file}: {e}")
        else:
            print(f"Info: {csv_file} not found, skipping property type {pt_display}")

    if not data_by_type:
        print("Error: No scored locations CSV files found. Cannot generate dashboard.")
        return False

    # 3. Generate self-contained HTML
    html_content = get_dashboard_html_template(data_by_type, config)
    
    # Ensure output directory exists (usually docs/ or Data/Results/)
    os.makedirs(os.path.dirname(DASHBOARD_OUTPUT_FILE), exist_ok=True)
    
    try:
        with open(DASHBOARD_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Successfully generated static dashboard at: {DASHBOARD_OUTPUT_FILE}")
        return True
    except Exception as e:
        print(f"Error: Failed to write dashboard file: {e}")
        return False

def get_dashboard_html_template(data_by_type, config):
    # Serialize data
    data_json = json.dumps(data_by_type)
    config_json = json.dumps(config)
    
    # Generate tabs HTML
    tabs_html = ""
    active_class = "active"
    for pt in data_by_type.keys():
        tabs_html += f'<button class="tab-btn {active_class}" onclick="switchPropertyType(\'{pt}\')">{pt}</button>'
        active_class = "" # only first one active
        
    default_pt = list(data_by_type.keys())[0]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>House Hunt - Interactive Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0f172a;
            --panel-bg: rgba(30, 41, 59, 0.7);
            --panel-border: rgba(255, 255, 255, 0.1);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --accent: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            
            --tier-a: #10b981;
            --tier-b: #3b82f6;
            --tier-c: #f59e0b;
            --tier-f: #ef4444;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: var(--text-primary);
            min-height: 100vh;
            overflow: hidden;
        }}

        .app-container {{
            display: flex;
            height: 100vh;
            padding: 1rem;
            gap: 1.5rem;
        }}

        .glass-panel {{
            background: var(--panel-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}

        /* Sidebar */
        .sidebar {{
            width: 350px;
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow: hidden;
        }}

        .sidebar-header {{
            padding: 1.5rem;
            border-bottom: 1px solid var(--panel-border);
        }}

        .sidebar-header h2 {{
            font-weight: 600;
            background: linear-gradient(to right, #60a5fa, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }}

        .controls-section {{
            flex: 1;
            overflow-y: auto;
            padding: 1.5rem;
        }}

        .controls-section::-webkit-scrollbar {{
            width: 6px;
        }}
        .controls-section::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }}

        .control-group {{
            margin-bottom: 2rem;
        }}

        .control-group h3 {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }}

        .slider-container {{
            margin-bottom: 1rem;
        }}

        .slider-container label {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            margin-bottom: 0.4rem;
        }}

        .slider-container label span {{
            font-variant-numeric: tabular-nums;
            color: var(--primary);
            font-weight: 600;
        }}

        input[type=range] {{
            -webkit-appearance: none;
            width: 100%;
            background: transparent;
        }}
        input[type=range]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            height: 16px;
            width: 16px;
            border-radius: 50%;
            background: var(--primary);
            cursor: pointer;
            margin-top: -6px;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
            transition: transform 0.1s;
        }}
        input[type=range]::-webkit-slider-thumb:hover {{
            transform: scale(1.2);
        }}
        input[type=range]::-webkit-slider-runnable-track {{
            width: 100%;
            height: 4px;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
        }}
        input[type=range].accent::-webkit-slider-thumb {{
            background: var(--accent);
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
        }}
        input[type=range].success::-webkit-slider-thumb {{
            background: var(--success);
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        }}

        .warning-text {{
            color: var(--danger);
            font-size: 0.75rem;
        }}
        .hidden {{
            display: none !important;
        }}

        /* Toggle Switch */
        .toggle-group {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .toggle-label {{
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}
        .switch-field {{
            display: flex;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--panel-border);
        }}
        .switch-field input {{
            position: absolute !important;
            clip: rect(0, 0, 0, 0);
            height: 1px;
            width: 1px;
            border: 0;
            overflow: hidden;
        }}
        .switch-field label {{
            background-color: transparent;
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 500;
            line-height: 1;
            text-align: center;
            padding: 8px 16px;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
        }}
        .switch-field label:hover {{
            color: var(--text-primary);
        }}
        .switch-field input:checked + label {{
            background-color: var(--primary);
            color: white;
            box-shadow: none;
        }}

        /* Main Content */
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            min-width: 0;
        }}

        .main-header {{
            padding: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .main-header h1 {{
            font-size: 1.5rem;
            font-weight: 600;
        }}

        .badge {{
            background: rgba(255,255,255,0.1);
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}

        .header-info {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        /* Tabs */
        .tabs-container {{
            display: flex;
            gap: 0.5rem;
            background: rgba(0, 0, 0, 0.2);
            padding: 0.25rem;
            border-radius: 10px;
            border: 1px solid var(--panel-border);
        }}
        .tab-btn {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.2s;
        }}
        .tab-btn.active {{
            background: var(--primary);
            color: white;
        }}
        .tab-btn:hover:not(.active) {{
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.05);
        }}

        /* Table */
        .table-container {{
            flex: 1;
            overflow: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}

        th {{
            position: sticky;
            top: 0;
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(4px);
            padding: 1rem;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--panel-border);
            z-index: 10;
            cursor: pointer;
            user-select: none;
        }}
        th.sort-active {{
            color: var(--primary);
        }}

        td {{
            padding: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.95rem;
        }}

        tbody tr.main-row {{
            transition: background-color 0.2s;
            cursor: pointer;
        }}

        tbody tr.main-row:hover {{
            background-color: rgba(255, 255, 255, 0.05);
        }}

        .details-row {{
            display: none;
            background-color: rgba(0, 0, 0, 0.2);
        }}

        .details-row.open {{
            display: table-row;
        }}

        .details-content {{
            padding: 1.5rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1.5rem;
            font-size: 0.9rem;
        }}

        .detail-item {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}

        .detail-label {{
            color: var(--text-secondary);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .detail-value {{
            font-weight: 500;
            color: var(--text-primary);
        }}

        .tier-badge {{
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.85rem;
            text-align: center;
            display: inline-block;
            min-width: 40px;
        }}

        .tier-a {{ background: rgba(16, 185, 129, 0.2); color: var(--tier-a); }}
        .tier-b {{ background: rgba(59, 130, 246, 0.2); color: var(--tier-b); }}
        .tier-c {{ background: rgba(245, 158, 11, 0.2); color: var(--tier-c); }}
        .tier-f {{ background: rgba(239, 68, 68, 0.2); color: var(--tier-f); }}
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar for Controls -->
        <aside class="sidebar glass-panel">
            <div class="sidebar-header">
                <h2>House Hunt</h2>
                <div class="toggle-group">
                    <label class="toggle-label">Group By:</label>
                    <div class="switch-field">
                        <input type="radio" id="group_zip" name="grouping_mode" value="zip" checked/>
                        <label for="group_zip">ZIP</label>
                        <input type="radio" id="group_town" name="grouping_mode" value="town" />
                        <label for="group_town">Town</label>
                    </div>
                </div>
                
                <div class="toggle-group" style="margin-top: 1rem;">
                    <label class="toggle-label">Filter:</label>
                    <div class="switch-field">
                        <input type="checkbox" id="show_excluded" onchange="updateDashboard()"/>
                        <label for="show_excluded">Show Tier F (Excluded)</label>
                    </div>
                </div>
            </div>

            <div class="controls-section">
                <!-- Global Weights -->
                <div class="control-group">
                    <h3>Global Weights</h3>
                    <div class="slider-container">
                        <label>Commute (<span id="val-weight-commute">50</span>%)</label>
                        <input type="range" id="weight-commute" min="0" max="100" value="50" class="slider primary">
                    </div>
                    <div class="slider-container">
                        <label>Housing (<span id="val-weight-housing">35</span>%)</label>
                        <input type="range" id="weight-housing" min="0" max="100" value="35" class="slider primary">
                    </div>
                    <div class="slider-container">
                        <label>Crime (<span id="val-weight-crime">15</span>%)</label>
                        <input type="range" id="weight-crime" min="0" max="100" value="15" class="slider primary">
                    </div>
                    <small id="weight-warning" class="warning-text hidden">Weights must sum to 100%</small>
                </div>

                <!-- Housing Sub-Weights -->
                <div class="control-group">
                    <h3>Housing Priority</h3>
                    <div class="slider-container">
                        <label>Price (<span id="val-hweight-price">60</span>%)</label>
                        <input type="range" id="hweight-price" min="0" max="100" value="60" class="slider accent">
                    </div>
                    <div class="slider-container">
                        <label>Price/SqFt (<span id="val-hweight-ppsf">30</span>%)</label>
                        <input type="range" id="hweight-ppsf" min="0" max="100" value="30" class="slider accent">
                    </div>
                    <div class="slider-container">
                        <label>Tax Rate (<span id="val-hweight-tax">10</span>%)</label>
                        <input type="range" id="hweight-tax" min="0" max="100" value="10" class="slider accent">
                    </div>
                    <small id="hweight-warning" class="warning-text hidden">Weights must sum to 100%</small>
                </div>

                <!-- Commute Preferences -->
                <div class="control-group">
                    <h3>Commute (Work 1)</h3>
                    <div class="slider-container">
                        <label>Ideal Time (<span id="val-commute-ideal">30</span>m)</label>
                        <input type="range" id="commute-ideal" min="5" max="120" value="30" step="5" class="slider">
                    </div>
                    <div class="slider-container">
                        <label>Max Time (<span id="val-commute-max">60</span>m)</label>
                        <input type="range" id="commute-max" min="10" max="120" value="60" step="5" class="slider">
                    </div>
                </div>

                <!-- Housing Budgets -->
                <div class="control-group">
                    <h3>Budget ($k)</h3>
                    <div class="slider-container">
                        <label>Min (<span id="val-budget-min">400</span>k)</label>
                        <input type="range" id="budget-min" min="100" max="2000" value="400" step="25" class="slider success">
                    </div>
                    <div class="slider-container">
                        <label>Ideal (<span id="val-budget-ideal">650</span>k)</label>
                        <input type="range" id="budget-ideal" min="200" max="2500" value="650" step="25" class="slider success">
                    </div>
                    <div class="slider-container">
                        <label>Max (<span id="val-budget-max">850</span>k)</label>
                        <input type="range" id="budget-max" min="300" max="3000" value="850" step="25" class="slider success">
                    </div>
                </div>
            </div>
        </aside>

        <!-- Main Content for Table -->
        <main class="main-content">
            <header class="main-header glass-panel">
                <div class="header-info">
                    <h1>Ranked Locations</h1>
                    <span id="result-count" class="badge">0 Results</span>
                </div>
                
                <!-- Property Type Tabs -->
                <div class="tabs-container">
                    {tabs_html}
                </div>
            </header>

            <div class="table-container glass-panel">
                <table id="results-table">
                    <thead>
                        <tr>
                            <th onclick="changeSort('Rank')">Rank</th>
                            <th onclick="changeSort('Tier')">Tier</th>
                            <th onclick="changeSort('Town')">Town</th>
                            <th onclick="changeSort('Zip')">Zip</th>
                            <th onclick="changeSort('Total_Score')">Score</th>
                            <th onclick="changeSort('Commute_Score')">Commute Score</th>
                            <th onclick="changeSort('Housing_Score')">Housing Score</th>
                            <th onclick="changeSort('Crime_Score')">Crime Score</th>
                            <th onclick="changeSort('Median_Price')">Price</th>
                            <th onclick="changeSort('Avg_Commute_Min')">Time (m)</th>
                        </tr>
                    </thead>
                    <tbody id="table-body">
                        <!-- Data rows will be injected here -->
                    </tbody>
                </table>
            </div>
        </main>
    </div>

    <script>
        // Embedded Data
        const rawDatasets = {data_json};
        let baseConfig = {config_json};
        
        let currentPropertyType = "{default_pt}";
        let currentSortKey = "Total_Score";
        let currentSortOrder = "desc"; // desc or asc

        // DOM Elements
        const elements = {{
            groupingModes: document.getElementsByName('grouping_mode'),
            weightCommute: document.getElementById('weight-commute'),
            weightHousing: document.getElementById('weight-housing'),
            weightCrime: document.getElementById('weight-crime'),
            hweightPrice: document.getElementById('hweight-price'),
            hweightPpsf: document.getElementById('hweight-ppsf'),
            hweightTax: document.getElementById('hweight-tax'),
            commuteIdeal: document.getElementById('commute-ideal'),
            commuteMax: document.getElementById('commute-max'),
            budgetMin: document.getElementById('budget-min'),
            budgetIdeal: document.getElementById('budget-ideal'),
            budgetMax: document.getElementById('budget-max'),
            valWeightCommute: document.getElementById('val-weight-commute'),
            valWeightHousing: document.getElementById('val-weight-housing'),
            valWeightCrime: document.getElementById('val-weight-crime'),
            valHweightPrice: document.getElementById('val-hweight-price'),
            valHweightPpsf: document.getElementById('val-hweight-ppsf'),
            valHweightTax: document.getElementById('val-hweight-tax'),
            valCommuteIdeal: document.getElementById('val-commute-ideal'),
            valCommuteMax: document.getElementById('val-commute-max'),
            valBudgetMin: document.getElementById('val-budget-min'),
            valBudgetIdeal: document.getElementById('val-budget-ideal'),
            valBudgetMax: document.getElementById('val-budget-max'),
            weightWarning: document.getElementById('weight-warning'),
            hweightWarning: document.getElementById('hweight-warning'),
            tableBody: document.getElementById('table-body'),
            resultCount: document.getElementById('result-count')
        }};

        let debounceTimer;

        // Scoring Constants
        const COMMUTE_SCORE_MAX = 100;
        const MIN_SCORE = 0;
        const NEUTRAL_SCORE = 50;
        const PRICE_SCORE_MAX = 50;
        const TAX_SCORE_MAX = 50;

        const TIER_THRESHOLDS = {{
            'A+': 95, 'A': 90, 'A-': 85,
            'B+': 80, 'B': 75, 'B-': 70,
            'C+': 65, 'C': 60, 'C-': 55,
            'D': 50, 'F': 0
        }};

        function assignTier(totalScore) {{
            for (const [tier, threshold] of Object.entries(TIER_THRESHOLDS)) {{
                if (totalScore >= threshold) return tier;
            }}
            return 'F';
        }}

        // Client-side Scoring Engine
        function scoreCommuteTime(avgTime, prefs, scoringBehavior) {{
            const ideal = prefs.ideal_time_minutes || 30;
            const maxAcceptable = prefs.max_acceptable_time || 45;
            if (avgTime === null || avgTime === undefined || isNaN(avgTime)) return 0;
            
            if (avgTime <= ideal) {{
                return COMMUTE_SCORE_MAX;
            }} else if (avgTime <= maxAcceptable) {{
                const denom = Math.max(maxAcceptable - ideal, 0.001);
                const ratio = (avgTime - ideal) / denom;
                return COMMUTE_SCORE_MAX - (ratio * (COMMUTE_SCORE_MAX / 2));
            }} else {{
                const multiplier = scoringBehavior.worst_commute_multiplier || 2.0;
                const worst = maxAcceptable * multiplier;
                if (avgTime >= worst) return MIN_SCORE;
                const denom = Math.max(worst - maxAcceptable, 0.001);
                const ratio = (avgTime - maxAcceptable) / denom;
                return (COMMUTE_SCORE_MAX / 2) - (ratio * (COMMUTE_SCORE_MAX / 2));
            }}
        }}

        function scoreHousingPrice(price, prefs) {{
            if (price === null || price === undefined || isNaN(price)) return MIN_SCORE;
            
            const budgetMin = prefs.budget_min;
            const budgetMax = prefs.budget_max;
            const budgetIdeal = prefs.budget_ideal;
            
            const bonusPoints = 5.0;
            const penaltyRange = 10.0;
            const maxScoreOverBudget = 35.0;
            const penaltyMultiplier = 100.0;
            
            if (price <= budgetIdeal) {{
                if (price <= budgetMin) return PRICE_SCORE_MAX;
                const denom = Math.max(budgetIdeal - budgetMin, 0.001);
                const ratio = (budgetIdeal - price) / denom;
                return (PRICE_SCORE_MAX - bonusPoints) + (ratio * bonusPoints);
            }} else if (price <= budgetMax) {{
                const denom = Math.max(budgetMax - budgetIdeal, 0.001);
                const ratio = (price - budgetIdeal) / denom;
                return (PRICE_SCORE_MAX - bonusPoints) - (ratio * penaltyRange);
            }} else {{
                const overageRatio = (price - budgetMax) / budgetMax;
                const penalty = Math.pow(overageRatio, 1.5) * penaltyMultiplier;
                return Math.max(MIN_SCORE, maxScoreOverBudget - penalty);
            }}
        }}

        function scoreHousingTax(taxRate, prefs, scoringBehavior) {{
            if (taxRate === null || taxRate === undefined || isNaN(taxRate)) return NEUTRAL_SCORE / 2;
            
            const ideal = prefs.ideal_tax_rate || 12.1;
            const maxAcceptable = prefs.max_acceptable_tax_rate || 20.0;
            
            if (taxRate <= ideal) {{
                return TAX_SCORE_MAX;
            }} else if (taxRate <= maxAcceptable) {{
                const denom = Math.max(maxAcceptable - ideal, 0.001);
                const ratio = (taxRate - ideal) / denom;
                return TAX_SCORE_MAX - (ratio * 25.0);
            }} else {{
                const worstTax = scoringBehavior.worst_tax_rate_per_1000 || 30.0;
                if (taxRate >= worstTax) return MIN_SCORE;
                const denom = Math.max(worstTax - maxAcceptable, 0.001);
                const ratio = (taxRate - maxAcceptable) / denom;
                return 25.0 - (ratio * 25.0);
            }}
        }}

        function scoreHousingPpsf(ppsf, prefs, scoringBehavior) {{
            if (ppsf === null || ppsf === undefined || isNaN(ppsf)) return NEUTRAL_SCORE / 2;
            
            const ideal = prefs.ideal_ppsf || 300;
            const maxAcceptable = prefs.max_acceptable_ppsf || 500;
            
            if (ppsf <= ideal) {{
                return TAX_SCORE_MAX;
            }} else if (ppsf <= maxAcceptable) {{
                const denom = Math.max(maxAcceptable - ideal, 0.001);
                const ratio = (ppsf - ideal) / denom;
                return TAX_SCORE_MAX - (ratio * 25.0);
            }} else {{
                const worst = scoringBehavior.worst_ppsf || 800.0;
                if (ppsf >= worst) return MIN_SCORE;
                const denom = Math.max(worst - maxAcceptable, 0.001);
                const ratio = (ppsf - maxAcceptable) / denom;
                return 25.0 - (ratio * 25.0);
            }}
        }}

        function computeScores(locations, config, groupingMode) {{
            const weights = config.weights || {{ commute: 0.5, housing: 0.35, crime: 0.15 }};
            const hWeights = config.housing_preferences.housing_weights || {{ price: 0.6, ppsf: 0.3, tax: 0.1 }};
            
            const cW = weights.commute;
            const hW = weights.housing;
            const crW = weights.crime;
            
            let targetLocations = locations;
            if (groupingMode === 'town') {{
                const townGroups = {{}};
                locations.forEach(loc => {{
                    const key = `${{loc.Town}}, ${{loc.State}}`;
                    if (!townGroups[key]) {{
                        townGroups[key] = [];
                    }}
                    townGroups[key].push(loc);
                }});
                
                targetLocations = Object.entries(townGroups).map(([key, locs]) => {{
                    const meanOf = (field1, field2) => {{
                        const vals = locs.map(l => {{
                            return l[field1] !== undefined && l[field1] !== null ? l[field1] : l[field2];
                        }}).filter(v => v !== null && v !== undefined && !isNaN(v));
                        if (vals.length === 0) return null;
                        return vals.reduce((a, b) => a + b, 0) / vals.length;
                    }};
                    
                    const sumOf = (field) => {{
                        const vals = locs.map(l => l[field]).filter(v => v !== null && v !== undefined && !isNaN(v));
                        if (vals.length === 0) return 0;
                        return vals.reduce((a, b) => a + b, 0);
                    }};

                    const zips = Array.from(new Set(locs.map(l => l.Zip).filter(z => z))).sort().join(', ');

                    return {{
                        Town: locs[0].Town,
                        State: locs[0].State,
                        Zip: zips,
                        Avg_Commute_Min: meanOf('Avg_Commute_Min'),
                        Min_Commute_Min: meanOf('Min_Commute_Min'),
                        Max_Commute_Min: meanOf('Max_Commute_Min'),
                        Distance_Miles: meanOf('Distance_Miles'),
                        Work2_Avg_Time: meanOf('Work2_Avg_Time'),
                        Work2_Distance: meanOf('Work2_Distance'),
                        Median_Price: meanOf('Median_Price', 'Latest_Median_Sale'),
                        Price_Per_SqFt: meanOf('Price_Per_SqFt', 'Latest_PPSF'),
                        Tax_Rate_Per_1000: meanOf('Tax_Rate_Per_1000'),
                        Homes_Sold: sumOf('Homes_Sold'),
                        Inventory: sumOf('Inventory'),
                        Crime_Score: meanOf('Crime_Score'),
                        High_Severity_Score: meanOf('High_Severity_Score'),
                        Medium_Severity_Score: meanOf('Medium_Severity_Score'),
                        Low_Severity_Score: meanOf('Low_Severity_Score'),
                        Population: meanOf('Population')
                    }};
                }});
            }}
            
            const processed = targetLocations.map(loc => {{
                // commute
                const commuteScore = scoreCommuteTime(
                    loc.Avg_Commute_Min,
                    config.work_address_1 ? config.work_address_1.preferences || config.work_address_1 : {{}},
                    config.scoring_behavior || {{}}
                );
                
                // housing
                const pScore = scoreHousingPrice(loc.Median_Price || loc.Latest_Median_Sale, config.housing_preferences);
                const tScore = scoreHousingTax(loc.Tax_Rate_Per_1000, config.housing_preferences, config.scoring_behavior || {{}});
                const ppsfScore = scoreHousingPpsf(loc.Price_Per_SqFt || loc.Latest_PPSF, config.housing_preferences, config.scoring_behavior || {{}});
                
                const weightedPrice = pScore * hWeights.price * 2;
                const weightedPpsf = ppsfScore * hWeights.ppsf * 2;
                const weightedTax = tScore * hWeights.tax * 2;
                const housingScore = weightedPrice + weightedPpsf + weightedTax;
                
                // crime
                const crimeScoreVal = loc.Crime_Score;
                
                let totalScore = 0;
                if (crimeScoreVal === null || crimeScoreVal === undefined || isNaN(crimeScoreVal)) {{
                    const norm = cW + hW;
                    totalScore = (commuteScore * (cW / norm)) + (housingScore * (hW / norm));
                }} else {{
                    totalScore = (commuteScore * cW) + (housingScore * hW) + (crimeScoreVal * crW);
                }}
                
                totalScore = Math.round(totalScore * 10) / 10;
                
                return {{
                    ...loc,
                    Commute_Score: Math.round(commuteScore * 10) / 10,
                    Housing_Score: Math.round(housingScore * 10) / 10,
                    Price_Score: Math.round(weightedPrice * 10) / 10,
                    PPSF_Score: Math.round(weightedPpsf * 10) / 10,
                    Tax_Score: Math.round(weightedTax * 10) / 10,
                    Total_Score: totalScore,
                    Tier: assignTier(totalScore)
                }};
            }});
            
            let results = processed;
            
            // Sort by current active sort configuration
            results.sort((a, b) => {{
                let valA = a[currentSortKey];
                let valB = b[currentSortKey];
                
                // Handle nulls
                if (valA === null || valA === undefined) return 1;
                if (valB === null || valB === undefined) return -1;
                
                if (typeof valA === 'string') {{
                    return currentSortOrder === 'desc' 
                        ? valB.localeCompare(valA)
                        : valA.localeCompare(valB);
                }} else {{
                    return currentSortOrder === 'desc'
                        ? valB - valA
                        : valA - valB;
                }}
            }});
            
            // Re-assign ranks
            results.forEach((loc, index) => {{
                loc.Rank = index + 1;
            }});
            
            return results;
        }}

        // Initialization
        function init() {{
            populateUIFromConfig();
            updateDashboard();
        }}

        // Populate sliders from configuration
        function populateUIFromConfig() {{
            if (baseConfig.weights) {{
                elements.weightCommute.value = baseConfig.weights.commute * 100;
                elements.weightHousing.value = baseConfig.weights.housing * 100;
                elements.weightCrime.value = baseConfig.weights.crime * 100;
            }}
            
            if (baseConfig.housing_preferences && baseConfig.housing_preferences.housing_weights) {{
                const hw = baseConfig.housing_preferences.housing_weights;
                elements.hweightPrice.value = hw.price * 100;
                elements.hweightPpsf.value = hw.ppsf * 100;
                elements.hweightTax.value = hw.tax * 100;
            }}

            const workPrefs = baseConfig.work_address_1 ? (baseConfig.work_address_1.preferences || baseConfig.work_address_1) : {{}};
            elements.commuteIdeal.value = workPrefs.ideal_time_minutes || 30;
            elements.commuteMax.value = workPrefs.max_acceptable_time || 45;

            if (baseConfig.housing_preferences) {{
                const hp = baseConfig.housing_preferences;
                elements.budgetMin.value = hp.budget_min / 1000;
                elements.budgetIdeal.value = hp.budget_ideal / 1000;
                elements.budgetMax.value = hp.budget_max / 1000;
            }}

            updateLabels();
        }}

        // Update slider value labels
        function updateLabels() {{
            elements.valWeightCommute.innerText = elements.weightCommute.value;
            elements.valWeightHousing.innerText = elements.weightHousing.value;
            elements.valWeightCrime.innerText = elements.weightCrime.value;
            
            elements.valHweightPrice.innerText = elements.hweightPrice.value;
            elements.valHweightPpsf.innerText = elements.hweightPpsf.value;
            elements.valHweightTax.innerText = elements.hweightTax.value;
            
            elements.valCommuteIdeal.innerText = elements.commuteIdeal.value;
            elements.valCommuteMax.innerText = elements.commuteMax.value;
            
            elements.valBudgetMin.innerText = elements.budgetMin.value;
            elements.valBudgetIdeal.innerText = elements.budgetIdeal.value;
            elements.valBudgetMax.innerText = elements.budgetMax.value;

            const totalWeight = parseInt(elements.weightCommute.value) + parseInt(elements.weightHousing.value) + parseInt(elements.weightCrime.value);
            if (totalWeight !== 100) {{
                elements.weightWarning.classList.remove('hidden');
            }} else {{
                elements.weightWarning.classList.add('hidden');
            }}

            const totalHweight = parseInt(elements.hweightPrice.value) + parseInt(elements.hweightPpsf.value) + parseInt(elements.hweightTax.value);
            if (totalHweight !== 100) {{
                elements.hweightWarning.classList.remove('hidden');
            }} else {{
                elements.hweightWarning.classList.add('hidden');
            }}
        }}

        function buildConfigFromUI() {{
            const config = JSON.parse(JSON.stringify(baseConfig));
            config.weights = {{
                commute: parseInt(elements.weightCommute.value) / 100,
                housing: parseInt(elements.weightHousing.value) / 100,
                crime: parseInt(elements.weightCrime.value) / 100
            }};

            if (!config.housing_preferences) config.housing_preferences = {{}};
            config.housing_preferences.housing_weights = {{
                price: parseInt(elements.hweightPrice.value) / 100,
                ppsf: parseInt(elements.hweightPpsf.value) / 100,
                tax: parseInt(elements.hweightTax.value) / 100
            }};

            if (!config.work_address_1) config.work_address_1 = {{}};
            const workPrefs = config.work_address_1.preferences || config.work_address_1;
            workPrefs.ideal_time_minutes = parseInt(elements.commuteIdeal.value);
            workPrefs.max_acceptable_time = parseInt(elements.commuteMax.value);

            config.housing_preferences.budget_min = parseInt(elements.budgetMin.value) * 1000;
            config.housing_preferences.budget_ideal = parseInt(elements.budgetIdeal.value) * 1000;
            config.housing_preferences.budget_max = parseInt(elements.budgetMax.value) * 1000;

            return config;
        }}

        function updateDashboard() {{
            const config = buildConfigFromUI();
            let groupingMode = 'zip';
            elements.groupingModes.forEach(radio => {{
                if (radio.checked) groupingMode = radio.value;
            }});

            const currentData = rawDatasets[currentPropertyType] || [];
            const scoredData = computeScores(currentData, config, groupingMode);
            
            renderTable(scoredData);
        }}

        function renderTable(data) {{
            const showExcluded = document.getElementById('show_excluded').checked;
            
            // Filter excluded first if needed
            let filteredData = data;
            if (!showExcluded) {{
                filteredData = data.filter(r => (r.Tier || 'F') !== 'F');
            }}

            elements.resultCount.innerText = `${{filteredData.length}} Results`;
            
            if (filteredData.length === 0) {{
                elements.tableBody.innerHTML = `<tr><td colspan="10" style="text-align:center">No locations found. Adjust filters/budgets.</td></tr>`;
                return;
            }}

            const html = filteredData.map((row, idx) => {{
                const tierLower = (row.Tier || 'F').charAt(0).toLowerCase();
                const price = row.Median_Price || row.Latest_Median_Sale;
                const priceStr = price ? `$${{price.toLocaleString()}}` : 'N/A';
                const time = row.Avg_Commute_Min;
                const timeStr = time ? time.toFixed(1) : 'N/A';
                const rowId = `row-${{idx}}`;
                
                return `
                    <tr class="main-row" onclick="toggleDetails('${{rowId}}')">
                        <td>#${{row.Rank || '-'}}</td>
                        <td><span class="tier-badge tier-${{tierLower}}">${{row.Tier || '-'}}</span></td>
                        <td>${{row.Town || 'Unknown'}}</td>
                        <td>${{row.Zip || '-'}}</td>
                        <td><strong>${{row.Total_Score || 0}}</strong></td>
                        <td>${{row.Commute_Score || 0}}</td>
                        <td>${{row.Housing_Score || 0}}</td>
                        <td>${{row.Crime_Score !== null && row.Crime_Score !== undefined ? row.Crime_Score : 'N/A'}}</td>
                        <td>${{priceStr}}</td>
                        <td>${{timeStr}}</td>
                    </tr>
                    <tr class="details-row" id="${{rowId}}-details">
                        <td colspan="10" style="padding: 0;">
                            <div class="details-content">
                                <div class="detail-item">
                                    <span class="detail-label">Price Score</span>
                                    <span class="detail-value">${{row.Price_Score || 0}}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">PPSF Score</span>
                                    <span class="detail-value">${{row.PPSF_Score || 0}}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Tax Score</span>
                                    <span class="detail-value">${{row.Tax_Score || 0}}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">High Crime Score</span>
                                    <span class="detail-value">${{row.High_Severity_Score !== null && row.High_Severity_Score !== undefined ? row.High_Severity_Score.toFixed(1) + '%' : 'N/A'}}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Work 2 Avg Time</span>
                                    <span class="detail-value">${{row.Work2_Avg_Time ? row.Work2_Avg_Time.toFixed(1) + ' min' : 'N/A'}}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Homes Sold (12mo)</span>
                                    <span class="detail-value">${{row.Homes_Sold !== null && row.Homes_Sold !== undefined ? row.Homes_Sold : 'N/A'}}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Inventory</span>
                                    <span class="detail-value">${{row.Inventory !== null && row.Inventory !== undefined ? row.Inventory : 'N/A'}}</span>
                                </div>
                            </div>
                        </td>
                    </tr>
                `;
            }}).join('');

            elements.tableBody.innerHTML = html;
        }}

        // Tab selection
        window.switchPropertyType = function(pt) {{
            currentPropertyType = pt;
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.toggle('active', btn.innerText === pt);
            }});
            updateDashboard();
        }};

        // Column sorting
        window.changeSort = function(key) {{
            if (currentSortKey === key) {{
                currentSortOrder = currentSortOrder === 'desc' ? 'asc' : 'desc';
            }} else {{
                currentSortKey = key;
                currentSortOrder = (key === 'Town' || key === 'Zip' || key === 'Tier') ? 'asc' : 'desc';
            }}

            // Update column headers classes if needed
            document.querySelectorAll('th').forEach(th => {{
                th.classList.toggle('sort-active', th.innerText.toLowerCase().includes(key.toLowerCase().replace('_', ' ')));
            }});

            updateDashboard();
        }};

        window.toggleDetails = function(rowId) {{
            const detailsRow = document.getElementById(rowId + '-details');
            if (detailsRow) {{
                detailsRow.classList.toggle('open');
            }}
        }};

        // Slider listeners
        const allInputs = document.querySelectorAll('input[type=range], input[type=radio]');
        allInputs.forEach(input => {{
            input.addEventListener('input', () => {{
                updateLabels();
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(updateDashboard, 150); // Faster update locally
            }});
        }});

        init();
    </script>
</body>
</html>"""

if __name__ == "__main__":
    generate_dashboard()
