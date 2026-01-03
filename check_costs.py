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
    Queries Google Cloud Monitoring for Distance Matrix elements.
    Broad query to avoid 404 errors on specific labels.
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_MONITOR_KEY

    try:
        client = monitoring_v3.MetricServiceClient()
        project_path = f"projects/{GCP_PROJECT_ID}"

        now = datetime.datetime.now(datetime.timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        interval = monitoring_v3.TimeInterval({
            "end_time": {"seconds": int(now.timestamp())},
            "start_time": {"seconds": int(start_of_month.timestamp())},
        })

        results = client.list_time_series(
            name=project_path,
            filter='metric.type="serviceruntime.googleapis.com/api/request_count" AND resource.labels.service="distancematrix.googleapis.com"',
            interval=interval,
            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        )

        total_elements = 0
        for series in results:
            # Only count 'default_elements' as these are the actual billable units
            if series.metric.labels.get("quota_metric") == "distancematrix.googleapis.com/default_elements":
                for point in series.points:
                    total_elements += point.value.int64_value

        return total_elements

    except Exception as e:
        print(f"\n[!] Google Monitoring Error: {e}")
        return None


def run_financial_audit():
    now = datetime.datetime.now()
    month_str = now.strftime('%Y-%m')

    # 1. Local Usage
    local_usage = 0
    if os.path.exists(API_USAGE_TRACKING_FILE):
        with open(API_USAGE_TRACKING_FILE, "r") as f:
            content = f.read().strip().split(',')
            if len(content) >= 2 and content[0] == month_str:
                local_usage = int(content[1])

    # 2. Google Usage
    verified_usage = get_verified_usage()

    # 3. Calculations
    # We prioritize Verified usage, but use Local to calculate the 'Sync Lag'
    final_count = verified_usage if verified_usage is not None else local_usage
    raw_cost = final_count * 0.01
    free_tier_limit = 200.00
    billed_amount = max(0, raw_cost - free_tier_limit)

    # Progress Bar Calculation
    percent_used = min(100, (raw_cost / free_tier_limit) * 100)
    bar_length = 20
    filled_length = int(bar_length * percent_used // 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    # 4. Report
    print("\n" + "=" * 50)
    print(f"FINANCIAL AUDIT: {now.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    # Data Freshness Check
    if verified_usage is not None:
        lag = local_usage - verified_usage
        print(f"Google Verified:      {verified_usage:,} elements")
        print(f"Local Log Usage:      {local_usage:,} elements")
        if lag > 0:
            print(f"\n[!] DATA LAG WARNING: Google is behind by {lag:,} elements.")
            print("    Your local logs are more recent than the GCP API report.")
    else:
        print(f"Local Log Usage:      {local_usage:,} elements")
        print("Google Verified:      [OFFLINE/UNAVAILABLE]")

    print("-" * 50)
    print(f"Free Credit Used:     [{bar}] {percent_used:.1f}%")
    print(f"Current Raw Cost:     ${raw_cost:.2f}")
    print(f"ESTIMATED BILL:       ${billed_amount:.2f}")

    # Projection
    _, last_day = calendar.monthrange(now.year, now.month)
    projected_usage = (local_usage / now.day) * last_day
    projected_bill = max(0, (projected_usage * 0.01) - free_tier_limit)

    print("-" * 50)
    print(f"EOM Projected Bill:   ${projected_bill:.2f}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_financial_audit()