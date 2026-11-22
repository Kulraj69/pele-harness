"""Render design figures and TODO panels, or plot a normalized measured CSV.

CSV columns: config,model,task_id,repeat,score,cost_usd,failure_category.
One row per task/repeat/config/model; costs are agent USD, excluding judge cost.
Blank cost means unrecorded, never zero; score-only panels are used in that case.
"""
import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def read_results(source):
    reader = csv.DictReader(source)
    required = {"config", "model", "task_id", "repeat", "score", "cost_usd", "failure_category"}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("CSV requires columns: " + ",".join(sorted(required)))
    rows, seen = [], set()
    for line, row in enumerate(reader, 2):
        try:
            row = {key: (value or "").strip() for key, value in row.items() if key is not None}
            key = tuple(row[name] for name in ("config", "model", "task_id", "repeat"))
            if not all(key) or key in seen:
                raise ValueError("missing identifiers or duplicate task/repeat")
            score = float(row["score"])
            cost = float(row["cost_usd"]) if row["cost_usd"] else None
            if not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError("score must be finite and in [0,1]")
            if cost is not None and (not math.isfinite(cost) or cost < 0):
                raise ValueError("cost_usd must be finite and non-negative")
            seen.add(key)
            rows.append({**row, "score": score, "cost_usd": cost})
        except (ValueError, TypeError) as exc:
            raise ValueError(f"CSV line {line}: {exc}") from exc
    if not rows:
        raise ValueError("CSV has no measured rows")
    return rows


def save(fig, output, name):
    fig.savefig(output / name, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"wrote {output / name}")


def canvas(title):
    fig, ax = plt.subplots(figsize=(10, 5.625))
    fig.set_facecolor("#f4f7fb")
    ax.set_facecolor("#f4f7fb")
    fig.suptitle(title, fontsize=20, weight="bold", color="#132b46", y=.94)
    fig.subplots_adjust(left=.12, right=.95, bottom=.17, top=.82)
    return fig, ax


def placeholder(output, name, title, text):
    fig, ax = canvas(title)
    ax.axis("off")
    ax.text(.5, .61, "TODO · REAL DEV RUNS REQUIRED", ha="center", va="center",
            transform=ax.transAxes, fontsize=18, weight="bold", color="#92591b")
    ax.text(.5, .36, text, ha="center", va="center", transform=ax.transAxes,
            fontsize=13, linespacing=1.6, color="#35495e")
    save(fig, output, name)


def design_figures(output):
    fig, ax = canvas("Files first · bounded engineering verification")
    ax.set(xlim=(0, 10), ylim=(0, 6))
    ax.axis("off")

    def box(x, y, width, height, text, color="#e2edf8"):
        ax.add_patch(FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.12",
                                   facecolor=color, edgecolor="#527ba0", linewidth=1.3))
        ax.text(x + width / 2, y + height / 2, text, ha="center", va="center",
                fontsize=10, linespacing=1.45, color="#132b46")

    def arrow(start, end, label=None):
        ax.annotate("", xy=end, xytext=start,
                    arrowprops={"arrowstyle": "<->", "color": "#527ba0", "lw": 1.5})
        if label:
            ax.text((start[0]+end[0])/2, (start[1]+end[1])/2+.16, label,
                    ha="center", fontsize=9, color="#35495e")

    box(.15, 3.8, 2.1, 1.2, "Evaluator\nTask + limits\nWebSocket")
    box(3.15, 3.55, 3.5, 1.7, "Harness container\nserve.py → taskbridge → harness.py\nPi 1.1.0 + workflow NOTE\nfirst agent_end → ≤1 follow-up")
    box(7.6, 3.8, 2.1, 1.2, "Model endpoint\nClaude Opus 5.5\nNative Anthropic")
    box(3.15, .7, 3.5, 1.6, "task-tools.ts + taskbridge relay\nread / write / edit / bash\nPi MCP → codemode discovery\nHTTP only to declared task MCP")
    box(7.6, .7, 2.1, 1.6, "Task container\nFiles + Python scripts\nDeliverable outputs\nLocal MCP servers", "#ddf1e7")
    arrow((2.4, 4.4), (3, 4.4))
    arrow((6.8, 4.4), (7.45, 4.4))
    arrow((4.9, 3.4), (4.9, 2.45), "tool actions")
    arrow((6.8, 1.5), (7.45, 1.5))
    fig.text(.5, .065, "Implemented architecture • no measured engineering performance yet",
             ha="center", fontsize=11, color="#35495e")
    save(fig, output, "architecture.png")

    fig = plt.figure(figsize=(10, 5.625), facecolor="#10283f")
    fig.text(.08, .83, "PHYSICAL-ENGINEERING'S LAST EXAM", color="#72d8c1", fontsize=13, weight="bold")
    fig.text(.08, .52, "Files first.\nThen verify.", color="white", fontsize=44, weight="bold", linespacing=1.15)
    fig.text(.08, .28, "Pi + an engineering workflow + one bounded audit", color="#cbd9e7", fontsize=17)
    fig.text(.08, .13, "DESIGN DRAFT  /  NOT YET EVALUATED ON DEV SET", color="#f2c27e", fontsize=12, weight="bold")
    save(fig, output, "cover.png")


def evidence_figures(output, rows):
    if rows is None:
        placeholder(output, "score-vs-cost.png", "Score versus agent cost",
                    "No measured scores or costs are available.\nNo synthetic points are plotted.")
        placeholder(output, "failure-breakdown.png", "Dev-set failure breakdown",
                    "No measured task outcomes are available.\nReplace with categorized trace-backed failures.")
        return
    groups = defaultdict(list)
    for row in rows:
        groups[(row["config"], row["model"])].append(row)
    missing_cost = any(row["cost_usd"] is None for row in rows)
    fig, ax = canvas("Recorded scores · cost unavailable" if missing_cost else "Measured score versus agent cost")
    score_labels = []
    for (config, model), group in sorted(groups.items()):
        score = sum(row["score"] for row in group) / len(group)
        tasks = len({row["task_id"] for row in group})
        if missing_cost:
            position = len(score_labels)
            score_labels.append(f"{config}\n{model}\n{tasks} tasks, {len(group)} runs")
            ax.bar(position, score, width=.4, color="#527ba0")
            ax.text(position, score+.025, f"{score:.6f}", ha="center", fontsize=12)
        else:
            cost = sum(row["cost_usd"] for row in group) / len(group)
            ax.scatter(cost, score, s=65, label=f"{config} / {model}: {tasks} tasks, {len(group)} runs")
    ax.set(ylabel="Mean recorded task score", ylim=(-.03, 1.03))
    if missing_cost:
        ax.set_xticks(range(len(score_labels)), score_labels, fontsize=9)
        fig.subplots_adjust(bottom=.25)
        fig.text(.5, .04, "Agent cost unrecorded: no score-versus-cost points plotted; blank is not zero.", ha="center", fontsize=10)
    else:
        ax.set_xlabel("Mean agent cost per task-run (USD; judge excluded)")
        ax.legend(fontsize=8, loc="best")
    ax.grid(alpha=.2)
    save(fig, output, "score-vs-cost.png")

    counts = Counter(row["failure_category"] or "unspecified" for row in rows if row["score"] < 1)
    fig, ax = canvas("Measured sub-perfect task-runs by category")
    fig.subplots_adjust(left=.26, bottom=.24)
    if counts:
        labels, values = zip(*sorted(counts.items()))
        ax.barh(labels, values, color="#527ba0")
        ax.set_xlabel("Task-runs with score < 1 (all supplied configurations)")
        ax.xaxis.get_major_locator().set_params(integer=True)
    else:
        ax.axis("off")
        ax.text(.5, .5, "No sub-perfect scores in supplied rows", ha="center", transform=ax.transAxes)
    series = ", ".join(sorted({row["config"] for row in rows}))
    fig.text(.5, .09, series, ha="center", fontsize=10)
    fig.text(.5, .04, "Categories supplied by analyst; shortfalls are not automatically root causes.", ha="center", fontsize=9)
    save(fig, output, "failure-breakdown.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, help="Normalized measured CSV; never use mock results")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    try:
        if args.results:
            with args.results.open(newline="", encoding="utf-8") as source:
                rows = read_results(source)
        else:
            rows = None
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    args.out.mkdir(parents=True, exist_ok=True)
    design_figures(args.out)
    evidence_figures(args.out, rows)


if __name__ == "__main__":
    main()
