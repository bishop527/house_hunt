"""
Generate interactive HTML report from scored location data.

Creates a standalone HTML file with:
- Summary statistics
- Interactive data table with clickable row detail modal
- Collapsed section showing locations filtered out and why
- Filtering and sorting capabilities

Updated:
- Added row detail modal, NaN fix for PPSF, json import
- Added filtered_df parameter; renders collapsed filtered-out section
"""
import json
import os
import logging
import pandas as pd
from datetime import datetime
from constants import *

logger = logging.getLogger(__name__)


def format_currency(value):
    """Format value as currency."""
    if pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"


def format_number(value, decimals=1):
    """Format number with specified decimals."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def get_tier_color(tier):
    """Get color for tier badge."""
    if tier.startswith('A'):
        return '#22c55e'  # Green
    elif tier.startswith('B'):
        return '#3b82f6'  # Blue
    elif tier.startswith('C'):
        return '#f59e0b'  # Orange
    elif tier.startswith('D'):
        return '#ef4444'  # Red
    else:
        return '#6b7280'  # Gray


def _build_row_details(row):
    """
    Build the details dict embedded in each table row as a data attribute.

    Args:
        row (pd.Series): A scored locations row

    Returns:
        str: HTML-safe JSON string
    """
    def safe_int(val):
        return int(val) if pd.notna(val) else None

    def safe_float(val):
        return float(val) if pd.notna(val) else None

    # Handle rank change which can be float/int or 'New'
    rc = row.get('Rank_Change')
    if pd.isna(rc):
        rc_val = 'New'
    else:
        rc_val = rc if isinstance(rc, str) else safe_int(rc)

    details = {
        'rank':          safe_int(row.get('Rank')),
        'rank_change':   rc_val,
        'total_score':   safe_float(row.get('Total_Score')),
        'tier':          str(row.get('Tier', '')),
        'commute_score': safe_float(row.get('Commute_Score')),
        'housing_score': safe_float(row.get('Housing_Score')),
        'price_score':   safe_float(row.get('Price_Score')),
        'ppsf_score':    safe_float(row.get('PPSF_Score')),
        'tax_score':     safe_float(row.get('Tax_Score')),
        'avg_commute':   safe_float(row.get('Avg_Commute_Min')),
        'min_commute':   safe_float(row.get('Min_Commute_Min')),
        'max_commute':   safe_float(row.get('Max_Commute_Min')),
        'distance':      safe_float(row.get('Distance_Miles')),
        'median_price':  safe_int(row.get('Median_Price')),
        'ppsf':          safe_float(row.get('Price_Per_SqFt')),
        'homes_sold':    safe_int(row.get('Homes_Sold')),
        'inventory':     safe_int(row.get('Inventory')),
        'tax_rate':      safe_float(row.get('Tax_Rate_Per_1000')),
        'monthly_tax':   safe_float(row.get('Est_Monthly_Tax')),
        'price_trend':   str(row.get('Price_Trend') or 'N/A'),
        'min_monthly':   safe_int(row.get('Min_Monthly_Price')),
        'max_monthly':   safe_int(row.get('Max_Monthly_Price')),
        'commute_runs':  safe_int(row.get('Commute_Runs')),
        'last_updated':  str(row.get('Last_Updated') or 'N/A'),
    }

    return (
        json.dumps(details)
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )


def _build_filtered_section(filtered_df):
    """
    Build the collapsed HTML section listing filtered-out locations.

    Rendered as a <details> element beneath the main table so it is
    hidden by default and does not clutter the primary results.

    Args:
        filtered_df (pd.DataFrame): Rows dropped during scoring filters.
            Expected columns: Town, State, Zip, Filter_Reason,
            Avg_Commute_Min, Distance_Miles, Median_Price, Price_Per_SqFt.

    Returns:
        str: HTML string, or empty string if filtered_df is None/empty.
    """
    if filtered_df is None or len(filtered_df) == 0:
        return ""

    rows_html = ""
    for _, row in filtered_df.sort_values('Town').iterrows():
        rows_html += f"""
                    <tr>
                        <td><strong>{row.get('Town', 'N/A')}</strong></td>
                        <td>{row.get('State', 'N/A')}</td>
                        <td>{row.get('Zip', 'N/A')}</td>
                        <td style="color:#ef4444; font-weight:500;">{row.get('Filter_Reason', 'N/A')}</td>
                        <td>{format_number(row.get('Avg_Commute_Min'))} min</td>
                        <td>{format_number(row.get('Distance_Miles'))} mi</td>
                        <td>{format_currency(row.get('Median_Price'))}</td>
                        <td>{format_currency(row.get('Price_Per_SqFt'))}</td>
                    </tr>"""

    return f"""
        <details class="filtered-section">
            <summary class="filtered-summary">
                <span class="filtered-count">
                    &#x26A0; {len(filtered_df)} location(s) filtered out
                </span>
                <span class="filtered-hint">click to expand</span>
            </summary>
            <div class="filtered-body">
                <p class="filtered-description">
                    These locations were excluded before scoring based on the limits set in your config file.
                </p>
                <table class="filtered-table">
                    <thead>
                        <tr>
                            <th>Town</th>
                            <th>State</th>
                            <th>ZIP</th>
                            <th>Reason Filtered</th>
                            <th>Avg Commute</th>
                            <th>Distance</th>
                            <th>Median Price</th>
                            <th>$/sqft</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
        </details>"""


def generate_html_report(scored_df, output_file, config=None, filtered_df=None):
    """
    Generate interactive HTML report.

    Args:
        scored_df (pd.DataFrame): Scored locations DataFrame
        output_file (str): Path to output HTML file
        config (dict): Scoring configuration (optional)
        filtered_df (pd.DataFrame): Locations dropped by filters (optional).
            If provided, rendered in a collapsed section below the main table.

    Returns:
        bool: True if successful
    """
    if scored_df is None or len(scored_df) == 0:
        logger.error("No data to generate report")
        return False

    # Derive filename from active PROPERTY_TYPES (e.g. score_report_SingleFamily.html)
    prop_suffix = "_".join(pt.replace(" ", "") for pt in PROPERTY_TYPES)
    base, ext = os.path.splitext(output_file)
    output_file = f"{base}_{prop_suffix}{ext}"

    # Determine Zillow URL path component based on PROPERTY_TYPES
    zillow_path = ""
    if len(PROPERTY_TYPES) == 1:
        pt = PROPERTY_TYPES[0]
        if pt == 'Single Family':
            zillow_path = "houses/"
        elif pt == 'Condo':
            zillow_path = "condos/"
        elif pt == 'Townhouse':
            zillow_path = "townhomes/"

    # Load config if not provided
    if config is None:
        try:
            with open(SCORE_CONFIG_FILE, 'r') as f:
                 config = json.load(f)
            logger.info(f"Loaded config from {SCORE_CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Failed to load config in generate_html_report: {e}")

    logger.info(f"Generating HTML report for {len(scored_df)} locations")
    if filtered_df is not None and len(filtered_df) > 0:
        logger.info(
            f"Including {len(filtered_df)} filtered locations in report"
        )
        
    # Extract housing weights for dynamic score maximums
    prefs = config.get('housing_preferences', {}) if config else {}
    weights = prefs.get('housing_weights', {'price': 0.6, 'ppsf': 0.3, 'tax': 0.1})
    max_price_score = int(weights.get('price', 0.6) * 100)
    max_ppsf_score  = int(weights.get('ppsf', 0.3) * 100)
    max_tax_score   = int(weights.get('tax', 0.1) * 100)

    # Calculate summary stats
    stats = {
        'total':       len(scored_df),
        'avg_score':   scored_df['Total_Score'].mean(),
        'avg_commute': scored_df['Avg_Commute_Min'].mean(),
        'avg_price':   scored_df['Median_Price'].mean(),
        'tier_counts': scored_df['Tier'].value_counts().to_dict(),
        'generated':   datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'filtered':    len(filtered_df) if filtered_df is not None else 0,
    }

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>House Hunt - {prop_suffix} Scoring Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }}

        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            padding: 2rem;
            background: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
        }}

        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .stat-label {{
            color: #64748b;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .stat-value {{
            color: #1e293b;
            font-size: 2rem;
            font-weight: 700;
        }}

        .controls {{
            padding: 2rem;
            background: white;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }}

        .search-box {{
            flex: 1;
            min-width: 250px;
        }}

        .search-box input {{
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.2s;
        }}

        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .filter-group {{
            display: flex;
            gap: 0.5rem;
        }}

        .filter-btn {{
            padding: 0.75rem 1.5rem;
            border: 2px solid #e2e8f0;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .filter-btn:hover {{
            border-color: #667eea;
            background: #f0f4ff;
        }}

        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}

        .table-container {{
            padding: 2rem;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }}

        th {{
            background: #f8fafc;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: #475569;
            border-bottom: 2px solid #e2e8f0;
            cursor: pointer;
            user-select: none;
        }}

        th:hover {{
            background: #f1f5f9;
        }}

        td {{
            padding: 1rem;
            border-bottom: 1px solid #e2e8f0;
            color: #1e293b;
        }}

        tbody tr {{
            cursor: pointer;
            transition: background 0.15s;
        }}
        tbody tr:hover {{
            background: #eef2ff !important;
        }}

        .rank-cell {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}

        .rank-number {{
            font-weight: 700;
            color: #667eea;
            font-size: 1.1rem;
        }}

        .rank-change {{
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.1rem 0.3rem;
            border-radius: 4px;
            background: #f8fafc;
        }}

        .tier-badge {{
            display: inline-block;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            font-weight: 700;
            color: white;
            font-size: 0.9rem;
        }}

        .score-bar {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .score-value {{
            font-weight: 700;
            min-width: 45px;
        }}

        .bar {{
            flex: 1;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
        }}

        .bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
            transition: width 0.3s;
        }}

        .footer {{
            padding: 2rem;
            text-align: center;
            color: #64748b;
            font-size: 0.9rem;
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
        }}

        .hidden {{
            display: none !important;
        }}

        /* ── Filtered section ───────────────────────────────────────────── */
        .filtered-section {{
            margin: 0 2rem 2rem;
            border: 1px solid #fde68a;
            border-radius: 10px;
            overflow: hidden;
            background: #fffbeb;
        }}

        .filtered-summary {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.85rem 1.25rem;
            cursor: pointer;
            list-style: none;
            user-select: none;
        }}

        /* Remove default <details> triangle in all browsers */
        .filtered-summary::-webkit-details-marker {{ display: none; }}

        .filtered-summary:hover {{ background: #fef3c7; }}

        .filtered-count {{
            color: #92400e;
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .filtered-hint {{
            color: #b45309;
            font-size: 0.8rem;
            font-style: italic;
        }}

        details[open] .filtered-hint {{ display: none; }}

        .filtered-body {{
            padding: 1rem 1.25rem 1.25rem;
            border-top: 1px solid #fde68a;
        }}

        .filtered-description {{
            color: #78350f;
            font-size: 0.85rem;
            margin-bottom: 1rem;
        }}

        .filtered-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }}

        .filtered-table th {{
            background: #fef3c7;
            color: #78350f;
            font-weight: 600;
            padding: 0.6rem 0.75rem;
            border-bottom: 1px solid #fde68a;
            cursor: default;
            text-align: left;
        }}

        .filtered-table th:hover {{ background: #fef3c7; }}

        .filtered-table td {{
            padding: 0.6rem 0.75rem;
            border-bottom: 1px solid #fde68a;
            color: #78350f;
            opacity: 0.8;
        }}

        .filtered-table tr:last-child td {{ border-bottom: none; }}

        /* ── Modal ──────────────────────────────────────────────────────── */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}
        .modal-overlay.open {{ display: flex; }}

        .modal {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            max-width: 700px;
            width: 90%;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 25px 80px rgba(0,0,0,0.4);
            position: relative;
        }}
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.5rem;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 1rem;
        }}
        .modal-title {{ font-size: 1.4rem; font-weight: 700; color: #1e293b; }}
        .modal-title a {{
            color: inherit;
            text-decoration: none;
            transition: color 0.15s;
        }}
        .modal-title a:hover {{
            color: #3b82f6;
            text-decoration: underline;
        }}
        .modal-subtitle {{ color: #64748b; font-size: 0.9rem; margin-top: 0.25rem; }}
        .modal-close {{
            background: none; border: none;
            font-size: 1.5rem; cursor: pointer;
            color: #94a3b8; line-height: 1;
            padding: 0.25rem;
        }}
        .modal-close:hover {{ color: #1e293b; }}

        .detail-section {{ margin-bottom: 1.5rem; }}
        .detail-section-title {{
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
            margin-bottom: 0.75rem;
        }}
        .score-row {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.75rem;
        }}
        .score-label {{ flex: 1; color: #475569; font-size: 0.95rem; }}
        .score-pill {{
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.9rem;
            color: white;
            min-width: 60px;
            text-align: center;
        }}
        .score-bar-wrap {{
            flex: 2;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
        }}
        .score-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
        }}
        .detail-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem 2rem;
        }}
        .detail-item {{ display: flex; justify-content: space-between; }}
        .detail-key {{ color: #64748b; font-size: 0.9rem; }}
        .detail-val {{ font-weight: 600; color: #1e293b; font-size: 0.9rem; }}
        .trend-up    {{ color: #059669; }}
        .trend-down  {{ color: #dc2626; }}
        .trend-stable {{ color: #94a3b8; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>&#x1F3E1; House Hunt &mdash; {prop_suffix} Scoring Report</h1>
            <p>Ranked locations based on commute and housing preferences</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Scored</div>
                <div class="stat-value">{stats['total']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Score</div>
                <div class="stat-value">{stats['avg_score']:.1f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Commute</div>
                <div class="stat-value">{stats['avg_commute']:.1f} min</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Price</div>
                <div class="stat-value">${stats['avg_price'] / 1000:.0f}k</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Filtered Out</div>
                <div class="stat-value" style="color:#d97706;">
                    {stats['filtered']}
                </div>
            </div>
        </div>

        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput"
                       placeholder="Search by town or zip code...">
            </div>
            <div class="filter-group">
                <button class="filter-btn active" data-tier="all">
                    All Tiers
                </button>
                <button class="filter-btn" data-tier="A">A-Tier</button>
                <button class="filter-btn" data-tier="B">B-Tier</button>
                <button class="filter-btn" data-tier="C">C-Tier</button>
            </div>
        </div>

        <div class="table-container">
            <table id="dataTable">
                <thead>
                    <tr>
                        <th data-sort="rank">Rank</th>
                        <th data-sort="town">Town</th>
                        <th data-sort="zip">ZIP</th>
                        <th data-sort="tier">Tier</th>
                        <th data-sort="score">Score</th>
                        <th data-sort="commute">Commute</th>
                        <th data-sort="distance">Distance</th>
                        <th data-sort="price">Median Price</th>
                        <th data-sort="ppsf">$/sqft</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
"""

    # Add scored table rows
    for _, row in scored_df.iterrows():
        tier_color = get_tier_color(row['Tier'])
        details_json = _build_row_details(row)

        rank_change = row.get('Rank_Change', 'New')
        if pd.isna(rank_change) or rank_change == 'New':
            change_html = '<span class="rank-change trend-stable">New</span>'
        else:
            try:
                change_val = int(rank_change)
                if change_val > 0:
                    change_html = f'<span class="rank-change trend-up">&#9650; {change_val}</span>'
                elif change_val < 0:
                    change_html = f'<span class="rank-change trend-down">&#9660; {abs(change_val)}</span>'
                else:
                    change_html = '<span class="rank-change trend-stable">-</span>'
            except ValueError:
                change_html = f'<span class="rank-change trend-stable">{rank_change}</span>'

        html += f"""
                    <tr data-tier="{row['Tier'][0]}"
                        data-town="{row['Town'].lower()}"
                        data-zip="{row['Zip']}"
                        data-details="{details_json}"
                        onclick="openModal(this)">
                        <td>
                            <div class="rank-cell">
                                <span class="rank-number">#{row['Rank']}</span>
                                {change_html}
                            </div>
                        </td>
                        <td><strong>{row['Town']}</strong></td>
                        <td>{row['Zip']}</td>
                        <td>
                            <span class="tier-badge"
                                  style="background: {tier_color}">
                                {row['Tier']}
                            </span>
                        </td>
                        <td>
                            <div class="score-bar">
                                <span class="score-value">
                                    {row['Total_Score']:.1f}
                                </span>
                                <div class="bar">
                                    <div class="bar-fill"
                                         style="width: {row['Total_Score']}%">
                                    </div>
                                </div>
                            </div>
                        </td>
                        <td>{row['Avg_Commute_Min']:.1f} min</td>
                        <td>{row['Distance_Miles']:.1f} mi</td>
                        <td>{format_currency(row.get('Median_Price'))}</td>
                        <td>{format_currency(row.get('Price_Per_SqFt'))}</td>
                    </tr>
"""

    # Build filtered section (empty string if no filtered locations)
    filtered_section_html = _build_filtered_section(filtered_df)

    html += f"""
                </tbody>
            </table>
        </div>

        {filtered_section_html}

        <!-- Row detail modal -->
        <div class="modal-overlay" id="detailModal">
            <div class="modal">
                <div class="modal-header">
                    <div>
                        <div class="modal-title" id="modalTitle"></div>
                        <div class="modal-subtitle" id="modalSubtitle"></div>
                    </div>
                    <button class="modal-close" id="modalClose">&#x2715;</button>
                </div>
                <div id="modalBody"></div>
            </div>
        </div>

        <div class="footer">
            <p>Generated on {stats['generated']}</p>
            <p>Data sources: Google Maps API (commute), Redfin (housing)</p>
            <p style="margin-top:0.5rem; font-size:0.8rem; color:#94a3b8;">
                Click any row to see full scoring details
            </p>
        </div>
    </div>

    <script>
        // ── Search ──────────────────────────────────────────────────────────
        const searchInput = document.getElementById('searchInput');
        const tableBody   = document.getElementById('tableBody');
        const rows        = tableBody.getElementsByTagName('tr');

        searchInput.addEventListener('input', function() {{
            const searchTerm = this.value.toLowerCase();
            for (let row of rows) {{
                const town = row.dataset.town;
                const zip  = row.dataset.zip;
                row.classList.toggle(
                    'hidden',
                    !town.includes(searchTerm) && !zip.includes(searchTerm)
                );
            }}
        }});

        // ── Tier filter ─────────────────────────────────────────────────────
        const filterBtns = document.querySelectorAll('.filter-btn');

        filterBtns.forEach(btn => {{
            btn.addEventListener('click', function() {{
                filterBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                const tier = this.dataset.tier;
                for (let row of rows) {{
                    if (tier === 'all') {{
                        row.classList.remove('hidden');
                    }} else {{
                        row.classList.toggle('hidden', row.dataset.tier !== tier);
                    }}
                }}
            }});
        }});

        // ── Sortable columns ─────────────────────────────────────────────────
        const headers = document.querySelectorAll('th[data-sort]');
        let currentSort = {{ column: 'rank', ascending: true }};

        headers.forEach(header => {{
            header.addEventListener('click', function() {{
                const column    = this.dataset.sort;
                const ascending = currentSort.column === column
                                  ? !currentSort.ascending : true;
                currentSort = {{ column, ascending }};
                sortTable(column, ascending);
            }});
        }});

        function sortTable(column, ascending) {{
            const rowsArray = Array.from(rows);

            rowsArray.sort((a, b) => {{
                let aVal, bVal;
                switch(column) {{
                    case 'rank':
                        aVal = parseInt(a.cells[0].textContent.slice(1));
                        bVal = parseInt(b.cells[0].textContent.slice(1));
                        break;
                    case 'town':
                        aVal = a.cells[1].textContent;
                        bVal = b.cells[1].textContent;
                        break;
                    case 'zip':
                        aVal = a.cells[2].textContent;
                        bVal = b.cells[2].textContent;
                        break;
                    case 'tier':
                        aVal = a.cells[3].textContent.trim();
                        bVal = b.cells[3].textContent.trim();
                        break;
                    case 'score':
                        aVal = parseFloat(
                            a.cells[4].querySelector('.score-value').textContent
                        );
                        bVal = parseFloat(
                            b.cells[4].querySelector('.score-value').textContent
                        );
                        break;
                    case 'commute':
                        aVal = parseFloat(a.cells[5].textContent);
                        bVal = parseFloat(b.cells[5].textContent);
                        break;
                    case 'distance':
                        aVal = parseFloat(a.cells[6].textContent);
                        bVal = parseFloat(b.cells[6].textContent);
                        break;
                    case 'price':
                        aVal = parseFloat(
                            a.cells[7].textContent.replace(/[$,]/g, '')
                        ) || 0;
                        bVal = parseFloat(
                            b.cells[7].textContent.replace(/[$,]/g, '')
                        ) || 0;
                        break;
                    case 'ppsf':
                        aVal = parseFloat(
                            a.cells[8].textContent.replace(/[$,]/g, '')
                        ) || 0;
                        bVal = parseFloat(
                            b.cells[8].textContent.replace(/[$,]/g, '')
                        ) || 0;
                        break;
                }}

                if (typeof aVal === 'string') {{
                    return ascending
                           ? aVal.localeCompare(bVal)
                           : bVal.localeCompare(aVal);
                }}
                return ascending ? aVal - bVal : bVal - aVal;
            }});

            rowsArray.forEach(row => tableBody.appendChild(row));
        }}

        // ── Modal ────────────────────────────────────────────────────────────
        const modal      = document.getElementById('detailModal');
        const modalClose = document.getElementById('modalClose');

        function fmt(val, prefix='', suffix='', fallback='N/A') {{
            return (val !== null && val !== undefined)
                ? prefix + Number(val).toLocaleString() + suffix
                : fallback;
        }}

        function scoreColor(score, max) {{
            max = max || 100;
            const pct = score / max;
            if (pct >= 0.8) return '#22c55e';
            if (pct >= 0.6) return '#3b82f6';
            if (pct >= 0.4) return '#f59e0b';
            return '#ef4444';
        }}

        function trendClass(trend) {{
            if (!trend || trend === 'N/A') return '';
            if (trend === 'increasing') return 'trend-up';
            if (trend === 'decreasing') return 'trend-down';
            return 'trend-stable';
        }}

        function openModal(row) {{
            const raw = row.dataset.details
                .replace(/&quot;/g, '"')
                .replace(/&#39;/g, "'");
            const d    = JSON.parse(raw);
            const town = row.querySelector('td:nth-child(2)').textContent.trim();

            let zillowUrl = '';
            const zPath = '{zillow_path}';
            if (zPath) {{
                zillowUrl = 'https://www.zillow.com/' + row.dataset.zip + '/' + zPath;
            }} else {{
                zillowUrl = 'https://www.zillow.com/homes/' + row.dataset.zip + '_rb/';
            }}
            document.getElementById('modalTitle').innerHTML = 
                `<a href="${{zillowUrl}}" target="_blank" title="View on Zillow">${{town}} &#x2197;</a>`;
            document.getElementById('modalSubtitle').textContent =
                'ZIP: ' + row.dataset.zip +
                ' \u00b7 Rank #' + d.rank +
                ' \u00b7 ' + d.tier + ' Tier';

            const trendLabel = d.price_trend === 'increasing' ? '\u2191 Increasing'
                             : d.price_trend === 'decreasing' ? '\u2193 Decreasing'
                             : d.price_trend === 'stable'     ? '\u2192 Stable'
                             : 'N/A';

            const taxRateStr = d.tax_rate !== null
                ? d.tax_rate.toFixed(2) + ' per $1k'
                : 'N/A';

            const monthlyTaxStr = d.monthly_tax !== null
                ? '$' + Math.round(d.monthly_tax).toLocaleString()
                : 'N/A';

            const priceRangeStr =
                (d.min_monthly !== null && d.max_monthly !== null)
                ? '$' + d.min_monthly.toLocaleString() +
                  ' \u2013 $' + d.max_monthly.toLocaleString()
                : 'N/A';

            document.getElementById('modalBody').innerHTML = `
                <div class="detail-section">
                    <div class="detail-section-title">Overall Score</div>
                    <div class="score-row">
                        <span class="score-label">Total Score</span>
                        <span class="score-pill"
                              style="background:${{scoreColor(d.total_score)}}">
                            ${{d.total_score}}
                        </span>
                        <div class="score-bar-wrap">
                            <div class="score-bar-fill"
                                 style="width:${{d.total_score}}%"></div>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <div class="detail-section-title">
                        Commute &mdash; ${{d.commute_score}}/100
                    </div>
                    <div class="score-row">
                        <span class="score-label">Commute Score</span>
                        <span class="score-pill"
                              style="background:${{scoreColor(d.commute_score)}}">
                            ${{d.commute_score}}
                        </span>
                        <div class="score-bar-wrap">
                            <div class="score-bar-fill"
                                 style="width:${{d.commute_score}}%"></div>
                        </div>
                    </div>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-key">Avg Time</span>
                            <span class="detail-val">
                                ${{d.avg_commute !== null
                                    ? d.avg_commute.toFixed(1) + ' min' : 'N/A'}}
                            </span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Distance</span>
                            <span class="detail-val">
                                ${{d.distance !== null
                                    ? d.distance.toFixed(1) + ' mi' : 'N/A'}}
                            </span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Best Time</span>
                            <span class="detail-val">
                                ${{d.min_commute !== null
                                    ? d.min_commute + ' min' : 'N/A'}}
                            </span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Worst Time</span>
                            <span class="detail-val">
                                ${{d.max_commute !== null
                                    ? d.max_commute + ' min' : 'N/A'}}
                            </span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Data Runs</span>
                            <span class="detail-val">${{fmt(d.commute_runs)}}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Last Updated</span>
                            <span class="detail-val">${{d.last_updated}}</span>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <div class="detail-section-title">
                        Housing &mdash; ${{d.housing_score}}/100
                    </div>
                    <div class="score-row">
                        <span class="score-label">Price Score</span>
                        <span class="score-pill"
                              style="background:${{scoreColor(d.price_score, {max_price_score})}}">
                            ${{d.price_score}}/{max_price_score}
                        </span>
                        <div class="score-bar-wrap">
                            <div class="score-bar-fill"
                                 style="width:${{d.price_score / {max_price_score} * 100}}%"></div>
                        </div>
                    </div>
                    <div class="score-row">
                        <span class="score-label">PPSF Score</span>
                        <span class="score-pill"
                              style="background:${{scoreColor(d.ppsf_score, {max_ppsf_score})}}">
                            ${{d.ppsf_score}}/{max_ppsf_score}
                        </span>
                        <div class="score-bar-wrap">
                            <div class="score-bar-fill"
                                 style="width:${{d.ppsf_score / {max_ppsf_score} * 100}}%"></div>
                        </div>
                    </div>
                    <div class="score-row">
                        <span class="score-label">Tax Score</span>
                        <span class="score-pill"
                              style="background:${{scoreColor(d.tax_score, {max_tax_score})}}">
                            ${{d.tax_score}}/{max_tax_score}
                        </span>
                        <div class="score-bar-wrap">
                            <div class="score-bar-fill"
                                 style="width:${{d.tax_score / {max_tax_score} * 100}}%"></div>
                        </div>
                    </div>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-key">Median Price</span>
                            <span class="detail-val">${{fmt(d.median_price, '$')}}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Price/SqFt</span>
                            <span class="detail-val">
                                ${{d.ppsf !== null
                                    ? '$' + d.ppsf.toFixed(0) : 'N/A'}}
                            </span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Tax Rate</span>
                            <span class="detail-val">${{taxRateStr}}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Est. Monthly Tax</span>
                            <span class="detail-val">${{monthlyTaxStr}}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Homes Sold</span>
                            <span class="detail-val">${{fmt(d.homes_sold)}}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Inventory</span>
                            <span class="detail-val">${{fmt(d.inventory)}}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">12-Mo Range</span>
                            <span class="detail-val">${{priceRangeStr}}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-key">Price Trend</span>
                            <span class="detail-val ${{trendClass(d.price_trend)}}">
                                ${{trendLabel}}
                            </span>
                        </div>
                    </div>
                </div>
            `;

            modal.classList.add('open');
        }}

        modalClose.addEventListener('click', () =>
            modal.classList.remove('open')
        );
        modal.addEventListener('click', e => {{
            if (e.target === modal) modal.classList.remove('open');
        }});
        document.addEventListener('keydown', e => {{
            if (e.key === 'Escape') modal.classList.remove('open');
        }});
    </script>
</body>
</html>
"""

    # Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info(f"HTML report generated: {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to write HTML report: {e}")
        return False


if __name__ == "__main__":
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils import load_csv_with_zip

    scored_file = os.path.join(RESULTS_DIR, "scored_locations.csv")
    output_file = os.path.join(RESULTS_DIR, "score_report.html")

    if os.path.exists(scored_file):
        df = load_csv_with_zip(scored_file)
        success = generate_html_report(df, output_file)

        if success:
            print(f"\nReport generated: {output_file}")
            print("Open in browser to view interactive report.")
        else:
            print("Failed to generate report.")
    else:
        print(f"Scored data file not found: {scored_file}")
        print("Run calculate_scores.py first.")