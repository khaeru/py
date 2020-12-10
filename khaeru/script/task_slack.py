#!/usr/bin/env python3
"""Show slack time for scheduled tasks."""
from datetime import datetime, time, timedelta
from subprocess import check_output

from colorama import Fore as fg
import pandas as pd


# Current time zone
LOCAL_TZ = datetime.now().astimezone().tzinfo
NOW = datetime.now(LOCAL_TZ)


def eowd(dt):
    """Return the end-of-day on date *dt*."""
    return datetime.combine(dt.date(), time(hour=17), LOCAL_TZ)


def sowd(dt):
    """Return the start-of-day on date *dt*."""
    return datetime.combine(dt.date(), time(hour=9), LOCAL_TZ)


def get_tasks(query=["estimate.any:"]):
    # List of tasks with 'estimate' set
    cmd = ["task"] + query + ["-COMPLETED", "-DELETED", "export"]
    tw_json = check_output(cmd, text=True)

    # Convert to pd.DataFrame
    dt_columns = ["due", "entry"]
    info = pd.read_json(tw_json, convert_dates=dt_columns)

    try:
        info = info.sort_values("due")
    except KeyError:
        pass

    # Localize
    for column in dt_columns:
        try:
            info[column] = info[column].dt.tz_convert(LOCAL_TZ)
        except KeyError:
            pass

    try:
        # Convert 'estimate' to timedelta
        # - Add '0D' and '0S' to satisfy pandas parser.
        info["estimate"] = pd.to_timedelta(
            info["estimate"].str.replace("PT", "P0DT") + "0S"
        )
    except KeyError:
        pass

    return info


def work_time_until(when):
    """Return a time delta until *when* including working time."""
    if when.day == NOW.day:
        result = when - NOW
    else:
        # From now until EOD
        result = eowd(NOW) - NOW

        # Intervening days, if any
        result += timedelta(hours=8) * (when.day - NOW.day - 1)

        # From the start of day on the due date 'til the end time or EOD
        result += max(timedelta(0), min(when, eowd(when)) - sowd(when))

    return result


def td_str(td, fixed_width=True):
    """Format timedelta *td* as a string"""
    negative = td.days < 0

    # Split td.seconds into hours and minutes
    hours = td.seconds // 3600
    minutes = (td.seconds - 3600 * hours) // 60
    seconds = td.seconds - 3600 * hours - 60 * minutes

    if negative:
        # e.g. td.days is -1, hours is 23 → convert to -1
        hours = (abs(td.days) * 24) - hours - 1
    else:
        hours += td.days * 24

    if fixed_width:
        neg = "-" if negative else " "
        hour_width = 2
    else:
        neg = "-" if negative else ""
        hour_width = 0

    template = f"{neg}{{hours:{hour_width}}}:{{minutes:02}}:{{seconds:02}}"
    return template.format(**locals())


def main():
    """Estimated vs available time for tasks."""
    tasks = get_tasks()

    # Print results
    total_work = timedelta(0)
    for due, group_info in tasks.groupby("due"):
        # Estimated work by this due time
        work = group_info["estimate"].sum().to_pytimedelta()

        print(f"by {due:%a %d %b %H:%M}")

        for _, row in group_info.iterrows():
            print(f"{td_str(row.estimate)}  #{row.id}  {row.description}")

        if due < NOW:
            # Overdue
            print(f"{td_str(work)}  ---  work overdue\n")
            continue

        # Accumulated estimated work
        total_work += work

        # Slack time: time until due minus time to complete
        slack = work_time_until(due) - total_work
        # Percent slack time
        pct_slack = 100 * (slack / total_work)

        # Output colour
        if pct_slack > 10:
            color = fg.GREEN
        elif -10 < pct_slack < 10:
            color = fg.YELLOW
        else:
            color = fg.RED

        print(
            color,
            "{}  ---  slack for {} of work ({:.0f}%)".format(
                td_str(slack), td_str(total_work, fixed_width=False), pct_slack
            ),
            fg.RESET,
            "\n",
            sep="",
        )
