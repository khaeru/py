import re
from configparser import ConfigParser
from datetime import datetime, time, timedelta
from itertools import islice, tee
from pathlib import Path
from subprocess import check_output
from typing import Any, Dict, Iterable, Tuple

import pandas as pd

# Current time zone
LOCAL_TZ = datetime.now().astimezone().tzinfo
NOW = datetime.now(LOCAL_TZ)
TODAY = NOW.date()
WEEKEND = [6, 7]


def eowd(dt):
    """Return the end-of-day on date *dt*."""
    return datetime.combine(dt.date(), time(hour=17), LOCAL_TZ)


def sowd(dt):
    """Return the start-of-day on date *dt*."""
    return datetime.combine(dt.date(), time(hour=9), LOCAL_TZ)


class TaskClient:
    def show(self, name):
        cfg = ConfigParser()
        cfg.read_string("[DEFAULT]\n" + check_output(["task", "_show"], text=True))
        return cfg["DEFAULT"][name]

    def uuid(self, query):
        return check_output(["task", query, "_uuid"], text=True).strip()

    def uuids(self, query="+PENDING"):
        return check_output(["task", query, "uuids"], text=True).strip().split(" ")

    def export(self, query=["estimate.any:"]):
        # List of tasks with 'estimate' set
        cmd = ["task"] + query + ["-COMPLETED", "-DELETED", "export"]
        tw_json = check_output(cmd)

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


client = TaskClient()


def work_time_until(when):
    """Return a time delta until *when* including working time."""
    result = timedelta(0)

    if when.date() > TODAY:
        # From now until EOD
        result += max(timedelta(0), eowd(NOW) - NOW)

        # Intervening days, if any
        result += timedelta(hours=8) * sum(
            map(
                lambda d: (TODAY + timedelta(days=d)).isoweekday() not in WEEKEND,
                range(1, (when.date() - TODAY).days),
            )
        )

    # From the start of day on the due date 'til the end time or EOD
    result += max(timedelta(0), min(when, eowd(when)) - max(NOW, sowd(when)))

    return result


def postponed(event: Dict[str, Any]) -> timedelta:
    """Return amount of time a task was postponed in `event`.

    FIXME this assumes the postponement is from the moment of modification to the new
    wait time.
    """
    info = event["diff"]

    if "wait" not in info.index:
        return timedelta()

    start = info.loc["wait", "a"] or info.loc["modified", "b"]
    return datetime.fromtimestamp(int(info.loc["wait", "b"])) - datetime.fromtimestamp(
        int(start)
    )


def read_undo_data():
    undo_data_path = (
        Path(client.show("data.location")).expanduser().joinpath("undo.data")
    )

    # Read undo data sections
    expr = re.compile(r'(?:^|" )([^\[:]+):"')

    def parse_line(line):
        name, line_data = line.split(" ", maxsplit=1)

        if name in ("old", "new"):
            t0, t1 = tee(filter(None, expr.split(line_data.strip('["]\n'))), 2)
            line_data = {
                k: v for k, v in zip(islice(t0, 0, None, 2), islice(t1, 1, None, 2))
            }
        return name, line_data

    def diff(a, b):
        data = []
        for key in sorted(set(a.keys()) | set(b.keys())):
            a_value = a.get(key, None)
            b_value = b.get(key, None)
            if a_value == b_value:
                continue
            data.append((key, a_value, b_value))

        return pd.DataFrame(data, columns="field a b".split()).set_index("field")

    events = []
    with open(undo_data_path, errors="replace") as f:
        event = {}
        for line in f:
            if line == "---\n":
                event["diff"] = diff(event.get("old", {}), event["new"])
                events.append(event)
                event = {}
            else:
                event.update([parse_line(line)])

    return events


def slip(task_uuid: str, events: Iterable[dict]) -> Tuple[int, timedelta]:
    """Return the number of times an event has been postponed, and the total time."""
    pp_count = 0
    pp_total = timedelta()

    for ev in events:
        pp = postponed(ev)
        if pp:
            pp_count += 1
            pp_total += pp

    return pp_count, pp_total


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
