"""
Generate interactive HTML report from scored location data.

Creates a standalone HTML file with:
- Summary statistics
- Interactive data table
- Charts and visualizations
- Filtering and sorting capabilities
"""
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


def generate_html_report(scored_df, output_file, config=None):
    """
    Generate interactive HTML report.

    Args:
        scored_df (pd.DataFrame): Scored locations DataFrame
        output_file (str): Path to output HTML file
        config (dict): Scoring configuration (optional)

    Returns:
        bool: True if successful
    """
    if scored_df is None or len(scored_df) == 0:
        logger.error("No data to generate report")
        return False

    logger.info(f"Generating HTML report for {len(scored_df)} locations")

    # Calculate summary stats
    stats = {
        'total': len(scored_df),
        'avg_score': scored_df['Total_Score'].mean(),
        'avg_commute': scored_df['Avg_Commute_Min'].mean(),
        'avg_price': scored_df['Median_Price'].mean(),
        'tier_counts': scored_df['Tier'].value_counts().to_dict(),
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>House Hunt - Scored Locations Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 
                         Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
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

        tr:hover {{
            background: #f8fafc;
        }}

        .rank {{
            font-weight: 700;
            color: #667eea;
            font-size: 1.1rem;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏡 House Hunt Scoring Report</h1>
            <p>Ranked locations based on commute and housing preferences</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Locations</div>
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

    # Add table rows
    for _, row in scored_df.iterrows():
        tier_color = get_tier_color(row['Tier'])

        html += f"""
                    <tr data-tier="{row['Tier'][0]}" 
                        data-town="{row['Town'].lower()}" 
                        data-zip="{row['Zip']}">
                        <td class="rank">#{row['Rank']}</td>
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
                        <td>{format_currency(row['Median_Price'])}</td>
                        <td>${row['Price_Per_SqFt']:.0f}</td>
                    </tr>
"""

    # Close HTML
    html += f"""
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>Generated on {stats['generated']}</p>
            <p>Data sources: Google Maps API (commute), Redfin (housing)</p>
        </div>
    </div>

    <script>
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const tableBody = document.getElementById('tableBody');
        const rows = tableBody.getElementsByTagName('tr');

        searchInput.addEventListener('input', function() {{
            const searchTerm = this.value.toLowerCase();

            for (let row of rows) {{
                const town = row.dataset.town;
                const zip = row.dataset.zip;
                const matches = town.includes(searchTerm) || 
                               zip.includes(searchTerm);
                row.classList.toggle('hidden', !matches);
            }}
        }});

        // Filter by tier
        const filterBtns = document.querySelectorAll('.filter-btn');

        filterBtns.forEach(btn => {{
            btn.addEventListener('click', function() {{
                // Update active state
                filterBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                const tier = this.dataset.tier;

                for (let row of rows) {{
                    if (tier === 'all') {{
                        row.classList.remove('hidden');
                    }} else {{
                        const rowTier = row.dataset.tier;
                        row.classList.toggle('hidden', rowTier !== tier);
                    }}
                }}
            }});
        }});

        // Sortable columns
        const headers = document.querySelectorAll('th[data-sort]');
        let currentSort = {{ column: 'rank', ascending: true }};

        headers.forEach(header => {{
            header.addEventListener('click', function() {{
                const column = this.dataset.sort;
                const ascending = currentSort.column === column ? 
                                !currentSort.ascending : true;

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
                            a.cells[4].querySelector('.score-value')
                             .textContent
                        );
                        bVal = parseFloat(
                            b.cells[4].querySelector('.score-value')
                             .textContent
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
                        );
                        bVal = parseFloat(
                            b.cells[7].textContent.replace(/[$,]/g, '')
                        );
                        break;
                    case 'ppsf':
                        aVal = parseFloat(
                            a.cells[8].textContent.replace('$', '')
                        );
                        bVal = parseFloat(
                            b.cells[8].textContent.replace('$', '')
                        );
                        break;
                }}

                if (typeof aVal === 'string') {{
                    return ascending ? 
                           aVal.localeCompare(bVal) : 
                           bVal.localeCompare(aVal);
                }} else {{
                    return ascending ? aVal - bVal : bVal - aVal;
                }}
            }});

            // Re-append sorted rows
            rowsArray.forEach(row => tableBody.appendChild(row));
        }}
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
    # Test with sample data
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