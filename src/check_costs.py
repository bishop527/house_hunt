import os
import datetime
import calendar
from google.cloud import monitoring_v3
from constants import (
    API_USAGE_TRACKING_FILE,
    GCP_PROJECT_ID,
    GCP_MONITOR_KEY
)


def get_verified_usage():
    """
    Queries Google Cloud Monitoring for the actual number of
    Distance Matrix API elements processed this month.
    """
    # Set credentials for the service account
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_MONITOR_KEY

    try:
        client = monitoring_v3.MetricServiceClient()
        project_path = f"projects/{GCP_PROJECT_ID}"

        # Define Time Interval: Start of current month (UTC) to Now
        now = datetime.datetime.now(datetime.timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        interval = monitoring_v3.TimeInterval({
            "end_time": {"seconds": int(now.timestamp())},
            "start_time": {"seconds": int(start_of_month.timestamp())},
        })

        # Filter for the Distance Matrix API request count
        results = client.list_time_series(
            name=project_path,
            filter='metric.type="serviceruntime.googleapis.com/api/request_count" AND resource.labels.service="distancematrix.googleapis.com"',
            interval=interval,
            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        )

        total_verified = 0
        for series in results:
            for point in series.points:
                total_verified += point.value.int64_value

        return total_verified

    except Exception as e:
        print(f"\n[!] Could not connect to Google Monitoring: {e}")
        return None


def run_financial_audit():
    """
    Calculates costs based on local logs and Google Verified data.
    """
    now = datetime.datetime.now()
    month_str = now.strftime('%Y-%m')

    # 1. Read Local Usage Log
    local_usage = 0
    if os.path.exists(API_USAGE_TRACKING_FILE):
        with open(API_USAGE_TRACKING_FILE, "r") as f:
            content = f.read().strip().split(',')
            if len(content) == 2 and content[0] == month_str:
                local_usage = int(content[1])
    else:
        print(f"Local tracking file not found at: {API_USAGE_TRACKING_FILE}")

    # 2. Get Google Verified Usage
    print(f"Fetching verified data from Google for {month_str}...")
    verified_usage = get_verified_usage()

    # 3. Calculations
    # Use verified usage if available, otherwise fall back to local
    final_count = verified_usage if verified_usage is not None else local_usage

    # Distance Matrix Advanced is $0.01 per element
    raw_cost = final_count * 0.01
    billed_amount = max(0, raw_cost - 200.00)

    # Projection for end of month
    _, last_day = calendar.monthrange(now.year, now.month)
    days_passed = now.day if now.day > 0 else 1
    projected_usage = (final_count / days_passed) * last_day
    projected_bill = max(0, (projected_usage * 0.01) - 200.00)

    # 4. Display Report
    print("\n" + "=" * 50)
    print(f"FINANCIAL AUDIT: {now.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    print(f"Local Log Usage:      {local_usage:,} elements")

    if verified_usage is not None:
        print(f"Google Verified:      {verified_usage:,} elements")
        # Alert if local log is out of sync
        if abs(local_usage - verified_usage) > 0:
            print(f"(!) Sync Difference:  {abs(local_usage - verified_usage):,}")
    else:
        print("Google Verified:      [DATA UNAVAILABLE]")

    print("-" * 50)
    print(f"Current Raw Cost:     ${raw_cost:.2f}")
    print(f"Google Credit:       -${min(200.0, raw_cost):.2f}")
    print(f"ESTIMATED BILL NOW:   ${billed_amount:.2f}")
    print("-" * 50)
    print(f"EOM Projected Usage:  {int(projected_usage):,} elements")
    print(f"EOM Projected Bill:   ${projected_bill:.2f}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_financial_audit()