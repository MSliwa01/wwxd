"""Draw the README charts into docs/img/.

Run from the repo root:

    uv run --with matplotlib python bench/charts/make_charts.py

Numbers come from bench/runs/2026-10-10 and 2026-10-11 where the raw data is
simple to read. The rest are copied from bench/RESULTS.md, with the section named
next to them.
"""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "bench" / "runs" / "2026-10-10"
OUT = ROOT / "docs" / "img"

# Light chart card. The card is solid so the chart reads the same on GitHub's
# light and dark themes; only the rounded corners are transparent.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BORDER = "#d9d8d2"

# Categorical slots in fixed order (validated: adjacent CVD dE >= 9.1 on light).
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GRAY, GRAY_2 = "#9a9893", "#6f6d68"

DPI = 200  # 2x of a 100 dpi layout


def _font() -> str:
    names = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("Inter", "Noto Sans", "Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"):
        if name in names:
            return name
    return "sans-serif"


plt.rcParams.update(
    {
        "font.family": _font(),
        "font.size": 11,
        "text.color": INK,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_2,
        "axes.labelsize": 11,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "axes.facecolor": SURFACE,
        "axes.grid": False,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
    }
)


def card(width: float, height: float) -> plt.Figure:
    """A figure with a rounded light card behind everything."""
    fig = plt.figure(figsize=(width, height))
    fig.patch.set_alpha(0)
    fig.patches.append(
        FancyBboxPatch(
            (0.004, 0.004),
            0.992,
            0.992,
            boxstyle="round,pad=0,rounding_size=0.025",
            transform=fig.transFigure,
            facecolor=SURFACE,
            edgecolor=BORDER,
            linewidth=1,
            mutation_aspect=width / height,
            zorder=-10,
        )
    )
    return fig


def header(fig: plt.Figure, title: str, subtitle: str, top: float) -> None:
    fig.text(0.045, top, title, fontsize=17, fontweight="bold", color=INK, va="top")
    fig.text(0.045, top - 0.075, subtitle, fontsize=11.5, color=INK_2, va="top")


def footer(fig: plt.Figure, text: str) -> None:
    fig.text(0.045, 0.035, text, fontsize=9.5, color=MUTED, va="bottom")
    fig.text(0.955, 0.035, "github.com/MSliwa01/wwxd", fontsize=9.5, color=MUTED, va="bottom", ha="right")


def tidy(ax: plt.Axes, grid_axis: str = "both") -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(1)
    ax.tick_params(length=0, pad=6)
    if grid_axis:
        ax.grid(True, axis=grid_axis, color=GRID, linewidth=1, linestyle="-")
        ax.set_axisbelow(True)


def save(fig: plt.Figure, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, dpi=DPI, facecolor="none")
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


# 1. Opinion bench ----------------------------------------------------------

# bench/RESULTS.md, "Web search vs a vault". Four arms ranked together on the 24
# opinion questions, scores averaged over the four judges. To add an arm, add a run
# name and a dict; the chart lays itself out from this list.
OPINION_RUNS = ROOT / "bench" / "runs" / "2026-10-11"
OPINION_JUDGES = ["opus", "haiku", "lite", "muse"]
OPINION_ARMS = [
    # "place" puts the label left of the point, or above or below it.
    {"arm": "op-raw", "label": "Raw Opus", "color": GRAY, "place": "left"},
    {"arm": "op-persona", "label": '"Be decisive, as X"', "color": GRAY_2, "place": "below"},
    {"arm": "op-web", "label": "Opus + web search", "color": ORANGE, "place": "above"},
    {"arm": "op-prose", "label": "Opus + wwxd", "color": BLUE, "place": "left"},
]


def opinion_stats() -> None:
    """Fill each arm's mean decisiveness and grounding and its contradicted picks."""
    names = "-".join(a["arm"] for a in OPINION_ARMS)
    for arm in OPINION_ARMS:
        means = {"decisiveness": [], "grounding": []}
        arm["contradicts"] = 0
        for judge in OPINION_JUDGES:
            per_judge = {k: [] for k in means}
            for vault in ("hormozi", "yc"):
                path = OPINION_RUNS / f"{vault}-web" / f"rank-{names}-{judge}.jsonl"
                for line in path.read_text().splitlines():
                    row = json.loads(line) if line.strip() else {}
                    if not row.get("ranking"):
                        continue
                    s = row["scores"][arm["arm"]]
                    for k in per_judge:
                        per_judge[k].append(s[k])
                    arm["contradicts"] += str(s.get("consistent_with_person", "")).lower() == "no"
            for k in means:
                means[k].append(statistics.mean(per_judge[k]))
        arm["decisive"] = round(statistics.mean(means["decisiveness"]), 1)
        arm["grounded"] = round(statistics.mean(means["grounding"]), 1)


def chart_opinion() -> None:
    opinion_stats()
    fig = card(9.0, 6.8)
    header(
        fig,
        "A persona prompt or web search makes Opus decisive, not grounded",
        "24 \"should I do X or Y?\" questions, scored 1 to 5, mean of four judges from three labs",
        0.945,
    )
    ax = fig.add_axes([0.105, 0.2, 0.85, 0.6])
    tidy(ax)
    ax.set_xlim(1, 5.25)
    ax.set_ylim(1, 5.35)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_xlabel("Decisiveness: picks one option and commits", labelpad=10)
    ax.set_ylabel("Grounding: reasons the person really holds", labelpad=10)

    # Quiet region labels.
    ax.text(5.2, 1.2, "decisive but not grounded", fontsize=10, color=MUTED, ha="right", style="italic")
    ax.text(1.15, 5.1, "grounded in what they said", fontsize=10, color=MUTED, ha="left", style="italic")

    for arm in OPINION_ARMS:
        xy = (arm["decisive"], arm["grounded"])
        ax.scatter(*xy, s=190, color=arm["color"], edgecolors=SURFACE, linewidths=2.5, zorder=3)
        n = arm["contradicts"]
        picks = "no pick contradicts the person" if n == 0 else f"{n} picks contradict the person"
        sub = f'{arm["decisive"]} decisive, {arm["grounded"]} grounded\n{picks}'
        # (x offset, name y offset, name va, sub y offset, sub va) in points.
        dx, name_dy, name_va, sub_dy, sub_va = {
            "left": (-14, 2, "bottom", -2, "top"),
            "above": (-8, 48, "bottom", 10, "bottom"),
            "below": (-8, -10, "top", -28, "top"),
        }[arm["place"]]
        ax.annotate(arm["label"], xy, xytext=(dx, name_dy), textcoords="offset points",
                    fontsize=12, fontweight="bold", color=INK, ha="right", va=name_va)
        ax.annotate(sub, xy, xytext=(dx, sub_dy), textcoords="offset points",
                    fontsize=10, color=INK_2, ha="right", va=sub_va, linespacing=1.25)

    footer(fig, "Judges: Opus 5.5, Haiku 5.5, Gemini 3.5 Flash Lite, Muse Spark 1.3. Data: bench/runs/2026-10-11.")
    save(fig, "chart-opinion.png")


# 2. Model and effort -------------------------------------------------------

MODELS = [("opus", "Opus 5.5", BLUE), ("sonnet", "Sonnet 5.5", ORANGE), ("haiku", "Haiku 5.5", AQUA)]
EFFORTS = ["medium", "high", "xhigh"]
VAULTS = ["hormozi", "yc"]
JUDGES = ["opus", "haiku"]


def answer_stats() -> dict[tuple[str, str], dict[str, float]]:
    """Mean rank (of 9, averaged over the two Claude judges) and median seconds per answer."""
    ranks: dict[str, dict[str, list[int]]] = {j: {} for j in JUDGES}
    for judge in JUDGES:
        for vault in VAULTS:
            path = RUNS / f"{vault}-model-effort" / f"rank-9-arms-{judge}.jsonl"
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                for pos, arm in enumerate(json.loads(line)["ranking"], start=1):
                    ranks[judge].setdefault(arm, []).append(pos)
    out = {}
    for model, _, _ in MODELS:
        for effort in EFFORTS:
            arm = f"ask-{model}-{effort}"
            secs = []
            for vault in VAULTS:
                path = RUNS / f"{vault}-model-effort" / f"{arm}-answers.jsonl"
                secs += [json.loads(line)["seconds"] for line in path.read_text().splitlines() if line.strip()]
            out[(model, effort)] = {
                "rank": statistics.mean(statistics.mean(ranks[j][arm]) for j in JUDGES),
                "seconds": statistics.median(secs),
            }
    return out


def compile_stats() -> dict[tuple[str, str], dict[str, float]]:
    """Gold evidence found (of 17) and list-price cost per source."""
    rows = json.loads((RUNS / "compile-metrics.json").read_text())
    sessions: dict[tuple[str, str], int] = {}
    with open(RUNS / "compile-sessions.csv", newline="") as f:
        for row in csv.DictReader(f):
            key = (row["model"], row["effort"])
            sessions[key] = sessions.get(key, 0) + 1
    out = {}
    for r in rows:
        key = (r["model"], r["effort"])
        found = int(r["evidence_recall"].split("/")[0])
        out[key] = {"gold": found, "cost": r["cost"] / r["sessions"]}
        assert sessions.get(key, r["sessions"]) >= r["sessions"], key
    return out


def chart_model_effort() -> None:
    ans = answer_stats()
    comp = compile_stats()

    fig = card(12.0, 6.6)
    header(
        fig,
        "Opus at effort high gives the best answers for the time",
        "Each line is one model at effort medium, high and xhigh. No advisor model.",
        0.945,
    )

    # Left: answering.
    ax = fig.add_axes([0.075, 0.17, 0.52, 0.575])
    tidy(ax)
    ax.set_xlim(15, 66)
    ax.set_ylim(9, 1)  # rank 1 is best, so best sits at the top
    ax.set_yticks([1, 3, 5, 7, 9])
    ax.set_xlabel("Median seconds per answer", labelpad=8)
    ax.set_ylabel("Mean rank of 9 (1 is best)", labelpad=8)
    ax.set_title("Answering 12 questions, ranked by an Opus and a Haiku judge", loc="left", fontsize=11.5, color=INK, pad=12)

    for model, name, color in MODELS:
        xs = [ans[(model, e)]["seconds"] for e in EFFORTS]
        ys = [ans[(model, e)]["rank"] for e in EFFORTS]
        ax.plot(xs, ys, color=color, linewidth=2, zorder=2)
        ax.scatter(xs, ys, s=70, color=color, edgecolors=SURFACE, linewidths=2, zorder=3)
        # Model name at the xhigh end of each line.
        ax.text(xs[-1] + 1.3, ys[-1], name, fontsize=10.5, fontweight="bold", color=INK, va="center")

    # Effort names along the Haiku line, which sits apart from the others.
    for e in EFFORTS:
        p = ans[("haiku", e)]
        ax.text(p["seconds"], p["rank"] + 0.55, e, fontsize=9.5, color=MUTED, ha="center", va="top")

    rec = ans[("opus", "high")]
    ax.scatter(rec["seconds"], rec["rank"], s=320, facecolors="none", edgecolors=INK, linewidths=1.5, zorder=4)
    ax.annotate(
        f"Opus high, the pick\nrank {rec['rank']:.1f}, {rec['seconds']:.0f} s",
        xy=(rec["seconds"], rec["rank"]),
        xytext=(rec["seconds"] - 9, rec["rank"] - 0.95),
        fontsize=10, color=INK, ha="right", va="center",
        arrowprops={"arrowstyle": "-", "color": INK_2, "lw": 1, "shrinkA": 2, "shrinkB": 10},
    )
    xh = ans[("opus", "xhigh")]
    ax.text(xh["seconds"] + 0.2, xh["rank"] - 0.45, "xhigh: no better, slower", fontsize=9.5, color=INK_2, ha="center", va="bottom")

    # Right: compiling.
    bx = fig.add_axes([0.715, 0.17, 0.255, 0.575])
    tidy(bx)
    bx.set_xscale("log")
    bx.set_xlim(0.02, 3.5)
    bx.set_xticks([0.03, 0.1, 0.3, 1, 3])
    bx.set_xticklabels(["$0.03", "$0.10", "$0.30", "$1", "$3"])
    bx.minorticks_off()
    bx.set_ylim(0, 17)
    bx.set_yticks([0, 5, 10, 15, 17])
    bx.set_xlabel("Cost per source, list price", labelpad=8)
    bx.set_ylabel("Key evidence found, of 17", labelpad=8)
    bx.set_title("Compiling 4 sources", loc="left", fontsize=11.5, color=INK, pad=12)
    for model, name, color in MODELS:
        xs = [comp[(model, e)]["cost"] for e in EFFORTS]
        ys = [comp[(model, e)]["gold"] for e in EFFORTS]
        bx.plot(xs, ys, color=color, linewidth=2, zorder=2)
        bx.scatter(xs, ys, s=60, color=color, edgecolors=SURFACE, linewidths=2, zorder=3)
    sh = comp[("sonnet", "high")]
    bx.annotate(
        "Sonnet high", xy=(sh["cost"], sh["gold"]), xytext=(0.09, 15.2),
        fontsize=9.5, color=INK, ha="center",
        arrowprops={"arrowstyle": "-", "color": INK_2, "lw": 1, "shrinkA": 2, "shrinkB": 6},
    )
    hk = comp[("haiku", "high")]
    bx.text(hk["cost"], hk["gold"] - 1.3, "Haiku misses\nabout two thirds", fontsize=9.5, color=INK_2, ha="center", va="top")

    # Legend, one row above both panels.
    x = 0.045
    for _, name, color in MODELS:
        fig.patches.append(FancyBboxPatch((x, 0.817), 0.018, 0.006, boxstyle="round,pad=0,rounding_size=0.003",
                                          transform=fig.transFigure, facecolor=color, edgecolor="none"))
        fig.text(x + 0.024, 0.82, name, fontsize=10.5, color=INK_2, va="center")
        x += 0.11

    footer(fig, "One run per configuration. Data: bench/runs/2026-10-10.")
    save(fig, "chart-model-effort.png")


# 3. Judges -----------------------------------------------------------------

LABS = {"Anthropic": BLUE, "NVIDIA": ORANGE, "Muse": AQUA, "Google": YELLOW}

# bench/RESULTS.md, "A judge from Google" (main bench, wwxd vs raw Opus pairs).
JUDGE_ROWS = [
    {"judge": "Opus 5.5", "lab": "Anthropic", "wins": 40, "pairs": 40, "note": ""},
    {"judge": "Haiku 5.5", "lab": "Anthropic", "wins": 40, "pairs": 40, "note": ""},
    {"judge": "Nemotron 3 Ultra", "lab": "NVIDIA", "wins": 39, "pairs": 40, "note": ""},
    {"judge": "Muse Spark 1.3", "lab": "Muse", "wins": 35, "pairs": 36, "note": "4 pairs failed on opencode errors"},
    {"judge": "Gemini 3.5 Flash Lite", "lab": "Google", "wins": 34, "pairs": 40, "note": "no access to the transcripts"},
]


def chart_judges() -> None:
    n = len(JUDGE_ROWS)
    fig = card(9.0, 1.9 + 0.62 * n)
    h = fig.get_figheight()
    header(fig, "Judges from four labs prefer wwxd", "Share of main-bench questions where the judge picked Opus + wwxd over Opus alone", 1 - 0.35 / h)

    top = 1 - 1.2 / h
    bottom = 0.85 / h
    ax = fig.add_axes([0.3, bottom, 0.56, top - bottom])
    tidy(ax, grid_axis="x")
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_yticks([])

    bar_h = 0.38  # 0.38 of a 0.62 in row is about 24 px at 1x
    for i, row in enumerate(JUDGE_ROWS):
        share = 100 * row["wins"] / row["pairs"]
        color = LABS[row["lab"]]
        ax.barh(i, share, height=bar_h, color=color, edgecolor="none", zorder=2)
        ax.text(share + 1.2, i, f'{row["wins"]} of {row["pairs"]}', fontsize=11, fontweight="bold", color=INK, va="center")
        ax.text(-2.5, i - 0.08, row["judge"], fontsize=11.5, color=INK, ha="right", va="bottom", fontweight="bold")
        sub = row["lab"] + (f', {row["note"]}' if row["note"] else "")
        ax.text(-2.5, i + 0.04, sub, fontsize=9.5, color=INK_2, ha="right", va="top")

    footer(fig, "Same answer pairs and prompt for every judge. Data: bench/RESULTS.md.")
    save(fig, "chart-judges.png")


if __name__ == "__main__":
    chart_opinion()
    chart_model_effort()
    chart_judges()
