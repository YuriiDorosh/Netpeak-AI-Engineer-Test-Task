from collections import Counter
from datetime import datetime, timezone


def build_output(results: list[dict]) -> list[dict]:
    return results


def build_report(results: list[dict]) -> str:
    total = len(results)
    failed = [r for r in results if r.get("error")]
    ok = [r for r in results if not r.get("error")]

    categories: Counter = Counter()
    priorities: Counter = Counter()
    departments: Counter = Counter()
    needs_clarification: list[str] = []

    for r in ok:
        a = r["analysis"]
        categories[a["category"]] += 1
        priorities[a["priority"]] += 1
        dept = a.get("target_department")
        if dept:
            departments[dept] += 1
        if a.get("needs_clarification"):
            needs_clarification.append(str(r["id"]))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# AI Request Processing Report",
        f"",
        f"Generated: {now}  ",
        f"Total requests processed: **{total}** ({len(ok)} OK, {len(failed)} failed)",
        f"",
        f"---",
        f"",
        f"## By Category",
        f"",
        f"| Category | Count |",
        f"|---|---|",
    ]
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        lines.append(f"| {cat} | {count} |")

    lines += [
        f"",
        f"## By Priority",
        f"",
        f"| Priority | Count |",
        f"|---|---|",
    ]
    for pri in ("high", "medium", "low"):
        lines.append(f"| {pri} | {priorities.get(pri, 0)} |")

    lines += [
        f"",
        f"## By Department",
        f"",
        f"| Department | Count |",
        f"|---|---|",
    ]
    if departments:
        for dept, count in sorted(departments.items(), key=lambda x: -x[1]):
            lines.append(f"| {dept} | {count} |")
    else:
        lines.append(f"| *(no departments detected)* | — |")

    lines += [
        f"",
        f"## Requests Needing Clarification ({len(needs_clarification)})",
        f"",
    ]
    if needs_clarification:
        for rid in needs_clarification:
            summary = next(
                (r["analysis"]["short_summary"] for r in ok if str(r["id"]) == rid),
                "—",
            )
            lines.append(f"- **{rid}**: {summary}")
    else:
        lines.append("*None — all requests are clear enough to act on.*")

    if failed:
        lines += [
            f"",
            f"## Failed Rows",
            f"",
        ]
        for r in failed:
            lines.append(f"- **{r['id']}**: {r['error']}")

    return "\n".join(lines)
