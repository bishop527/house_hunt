
def get_verified_usage():
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

        # --- UPDATED FILTER ---
        # We switch from 'api/request_count' to 'serviceruntime.googleapis.com/quota/consumed_usage'
        # and filter for the specific metric 'Elements'
        results = client.list_time_series(
            name=project_path,
            filter=(
                'metric.type="serviceruntime.googleapis.com/quota/consumed_usage" '
                'AND resource.labels.service="distancematrix.googleapis.com" '
                'AND metric.labels.quota_metric="distancematrix.googleapis.com/default_elements"'
            ),
            interval=interval,
            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        )

        total_verified = 0
        for series in results:
            for point in series.points:
                # Usage metrics are often returned as 'double_value' or 'int64_value'
                # consumed_usage typically uses int64
                total_verified += point.value.int64_value

        return total_verified

    except Exception as e:
        print(f"\n[!] Could not connect to Google Monitoring: {e}")
        return None





def get_hours_until_next_run(target_time_str):
    """Calculates hours until a specific time slot."""
    now = datetime.now()
    try:
        target_hour, target_min = map(int, target_time_str.split(':'))
        target = now.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)

        if target <= now:
            target += timedelta(days=1)

        diff = (target - now).total_seconds() / 3600
        logger.debug(f"Time until next run ({target_time_str}): {round(diff, 2)} hours")
        return diff
    except Exception as e:
        logger.error(f"Error calculating time until next run: {e}")
        return 0