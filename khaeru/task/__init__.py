"""Show slack time for scheduled tasks."""
from datetime import timedelta

from colorama import Fore as fg

from .common import (
    NOW,
    client,
    read_undo_data,
    slip,
    td_str,
    work_time_until,
)


def show_slack():
    """Estimated vs available time for tasks."""
    tasks = client.export()

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


def show_slip(task_uuids):
    """Estimated vs available time for tasks."""
    all_events = read_undo_data()

    for uuid in task_uuids:
        count, total = slip(
            uuid, filter(lambda e: e["new"]["uuid"] == uuid, all_events)
        )
        if count == 0:
            continue
        print(f"Task {uuid.split('-')[0]} postponed {count} time(s), total {total}")
