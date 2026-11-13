"""Render pilot counts and limitations for the command-line report."""


def render(summary):
    """Present independent observations without a combined quality score."""
    return "\n".join([f"Pilot: {summary['measurement_kind']}", *summary["warnings"],
                      *[_group(group) for group in summary["groups"]],
                      f"Pending adjudications: {len(summary['pending_adjudications'])}"])


def _group(group):
    """Describe one agent and condition with separate quality and process counts."""
    counts, costs = group["counts"], group["usage"]["cost"]
    return (f"{group['benchmark']} / {group['agent_id']} / {group['condition']}:\n"
            f"  planned={counts['planned']}; started={counts['started']}; evaluated={counts['evaluated']}; pending={counts['pending']}\n"
            f"  quality_passed={counts['quality_passed']}; process_passed={counts['process_passed']}; quality_pass_rate={group['quality_pass_rate']}\n"
            f"  independent_groups={group['independent_groups']}; scenarios={group['scenario_count']}; repetitions={group['repetitions']}\n"
            f"  cost total={costs['total']}; known_total={costs['known_total']}; unknown_count={costs['unknown_count']}\n"
            f"  statuses={group['statuses']}")
