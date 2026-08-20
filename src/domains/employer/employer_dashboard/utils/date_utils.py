from datetime import datetime, timedelta, timezone
import calendar

def get_dashboard_date_ranges(filter_str: str):
    """
    បំប្លែង Filter String ទៅជា (Current Start, Current End) និង (Previous Start, Previous End)
    ឧទាហរណ៍ filter_str: "today", "this_week", "this_month", "2026-08", "2026-08-15,2026-08-20"
    """
    now = datetime.now(timezone.utc)
    
    # លំនាំដើម (Default)
    current_start = now
    current_end = now
    prev_start = now
    prev_end = now

    filter_str = filter_str.lower().strip() if filter_str else "this_month"

    if filter_str == "today":
        current_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        current_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        prev_start = current_start - timedelta(days=1)
        prev_end = current_end - timedelta(days=1)

    elif filter_str == "this_week":
        current_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        current_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        prev_start = current_start - timedelta(weeks=1)
        prev_end = current_end - timedelta(weeks=1)

    elif filter_str == "this_month":
        current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # រកខែមុន
        first_day_of_current_month = current_start
        last_day_of_prev_month = first_day_of_current_month - timedelta(days=1)
        prev_start = last_day_of_prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_end = last_day_of_prev_month.replace(hour=23, minute=59, second=59, microsecond=999999)

    elif filter_str == "this_year":
        current_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        current_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        prev_start = current_start.replace(year=now.year - 1)
        prev_end = current_start.replace(year=now.year - 1, month=12, day=31, hour=23, minute=59, second=59)

    elif filter_str == "all_time":
        current_start = datetime(2000, 1, 1, tzinfo=timezone.utc)
        current_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        prev_start = current_start # អត់មាន Trend ទេសម្រាប់ All Time
        prev_end = current_start

    # 🟢 សម្រាប់ Custom Month (ឧ. "2026-08")
    elif len(filter_str) == 7 and "-" in filter_str:
        try:
            year, month = map(int, filter_str.split("-"))
            current_start = datetime(year, month, 1, tzinfo=timezone.utc)
            _, last_day = calendar.monthrange(year, month)
            current_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
            
            # ខែមុននៃខែដែលបានរើស
            last_day_prev = current_start - timedelta(days=1)
            prev_start = last_day_prev.replace(day=1)
            prev_end = last_day_prev.replace(hour=23, minute=59, second=59)
        except ValueError:
            current_start = now.replace(day=1)

    # 🟢 សម្រាប់ Custom Date Range (ឧ. "2026-08-15,2026-08-20")
    elif "," in filter_str:
        try:
            start_str, end_str = filter_str.split(",")
            current_start = datetime.strptime(start_str.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            current_end = datetime.strptime(end_str.strip(), "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            
            delta = current_end - current_start
            prev_start = current_start - delta
            prev_end = current_end - delta
        except ValueError:
            current_start = now.replace(day=1)

    return (current_start, current_end), (prev_start, prev_end)