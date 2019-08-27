#!/usr/bin/env python3
from datetime import datetime, time, timedelta
from subprocess import check_output

import pandas as pd


# Current time zone
LOCAL_TZ = datetime.now().astimezone().tzinfo


def eod(dt):
    """Return the end-of-day on date *dt*."""
    return datetime.combine(dt.date(), time(hour=17), LOCAL_TZ)


def sod(dt):
    """Return the start-of-day on date *dt*."""
    return datetime.combine(dt.date(), time(hour=9), LOCAL_TZ)


def get_tasks():
    # List of tasks with 'estimate' set
    tw_json = check_output(['task', 'estimate.any:', 'export'], text=True)

    # Convert to pd.DataFrame
    info = pd.read_json(tw_json, convert_dates=['due', 'entry']) \
             .sort_values('due')

    # Convert 'estimate' to timedelta
    # - Add '0D' and '0S' to satisfy pandas parser.
    info['estimate'] = pd.to_timedelta(
        info['estimate'].str.replace('PT', 'P0DT') + '0S')

    # The parsed (pandas?) UTC is not the same as datetime.timezone.utc
    return info, info.loc[0, 'due'].tzinfo


def work_time_until(when):
    """Return a time delta until *when* including working time."""
    result = when - NOW

    if result.components.days >= 1:
        # From now until EOD
        result = eod(NOW) - NOW

        # Intervening days
        result += timedelta(hours=8) * (when - NOW).components.days

        # From the start of day on the due date 'til the end time or EOD
        result += (when if when < eod(when) else eod(when)) - sod(when)

    return result


def td_str(td):
    td = td.to_pytimedelta()
    hours = td.seconds // 3600
    minutes = (td.seconds - 3600 * hours) // 60
    seconds = td.seconds - 3600 * hours - 60 * minutes
    # TODO this is incorrect
    hours += (8 * td.days if td.days > 0 else 24 * td.days)
    return f'{hours:2}:{minutes:02}:{seconds:02}'


def main():
    """Estimated vs available time for tasks."""

    global NOW

    tasks, UTC = get_tasks()

    # Current time in pandas UTC
    NOW = datetime.now(UTC)

    # Slack time: time until due minus time to complete
    tasks['slack'] = tasks['due'].apply(work_time_until) - tasks['estimate']

    # Print results

    accumulated = timedelta(0)
    for due, group_info in tasks.groupby('due'):
        total_est = group_info['estimate'].sum()
        accumulated += total_est
        slack = work_time_until(due) - accumulated

        # Due time in the local timezone
        due_ = due.astimezone(LOCAL_TZ)

        print(f'Until {due_:%m-%d %H:%M} -- {td_str(accumulated)} of work, '
              f' {td_str(slack)} slack')

        for _, row in group_info.iterrows():
            print(f'  {td_str(row.estimate)} -- {row.id} {row.description}')

        print()
