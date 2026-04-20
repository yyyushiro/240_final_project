import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import cast

# Writable config dir (avoids ~/.matplotlib when not available)
_viz_dir = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(_viz_dir / ".matplotlib"))
(_viz_dir / ".matplotlib").mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

DATE_FMT = "%m/%d/%Y %H:%M:%S"

_DEFAULT_SEMESTER_START = "2026-01-12"
_DEFAULT_SEMESTER_END = "2026-05-03"


@dataclass(frozen=True)
class ExpectationParams:
    beginning_balance: float
    semester_start: str
    semester_end: str
    days_total: int


def history_path() -> Path:
    """return the file path for the output graph images.

    Returns:
        Path: the file path for the output graph images.
    """
    return Path(__file__).resolve().parents[2] / "jsons" / "history.json"


def load_timeline(history_file: Path) -> pd.DataFrame:
    """load the json file and convert its data into the data frame.

    Args:
        history_file (Path): the path for the json file.

    Returns:
        pd.DataFrame: the data frame having the ginve history data.
    """
    with open(history_file, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["timelineData"]
    df = pd.DataFrame(
        rows,
        columns=["Post Date", "Location", "Amount", "Balance"],
    )
    df["Post Date"] = pd.to_datetime(df["Post Date"], format=DATE_FMT)
    df = df.sort_values("Post Date").reset_index(drop=True)
    return df


def load_expectation_params(history_file: Path) -> ExpectationParams:
    """Semester window and beginning balance for expectation overlays.

    Prefer ``status.json`` (matches analyze.cpp). Otherwise use history balances
    and the same default semester dates as the analyzer.
    """
    status_file = history_file.parent / "status.json"
    if status_file.is_file():
        with open(status_file, encoding="utf-8") as f:
            s = json.load(f)
        return ExpectationParams(
            beginning_balance=float(s["beginning_balance"]),
            semester_start=str(s["semester_start"]),
            semester_end=str(s["semester_end"]),
            days_total=int(s["days_total"]),
        )

    with open(history_file, encoding="utf-8") as f:
        data = json.load(f)
    begin = float(data["balances"]["beginning_balance"])
    d0 = date.fromisoformat(_DEFAULT_SEMESTER_START)
    d1 = date.fromisoformat(_DEFAULT_SEMESTER_END)
    return ExpectationParams(
        beginning_balance=begin,
        semester_start=_DEFAULT_SEMESTER_START,
        semester_end=_DEFAULT_SEMESTER_END,
        days_total=max(1, (d1 - d0).days),
    )


def plot_balance(df: pd.DataFrame, out: Path, exp: ExpectationParams) -> None:
    """plot the fluctuation of user's balance over time.

    Args:
        df (pd.DataFrame): the given data frame of the user's spending history.
        out (Path): the path for the output graph.
        exp (ExpectationParams): semester window and beginning balance for the even-pace line.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(
        df["Post Date"],
        df["Balance"],
        color="tab:blue",
        linewidth=1.2,
        label="Actual balance",
    )
    t0 = pd.Timestamp(exp.semester_start)
    t1 = pd.Timestamp(exp.semester_end)
    pace_x = [float(mdates.date2num(t0)), float(mdates.date2num(t1))]
    ax.plot(
        pace_x,
        [exp.beginning_balance, 0.0],
        color="tab:orange",
        linestyle="--",
        linewidth=1.2,
        label="Even pace",
    )
    ax.set_title("Balance over time")
    ax.set_xlabel("Date")
    ax.set_xlim(pace_x[0], pace_x[1])
    ax.set_ylabel("Balance ($)")
    ax.set_ylim(0, 1000)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_daily_spending(df: pd.DataFrame, out: Path, exp: ExpectationParams) -> None:
    """plot the user's daily dining dollars usage over time.

    Args:
        df (pd.DataFrame): the given data frame of user's spending history.
        out (Path): the path for the output graph.
        exp (ExpectationParams): used for average daily even-spend reference line.
    """
    tmp = df.assign(day=df["Post Date"].dt.normalize())
    daily = cast(
        pd.DataFrame,
        tmp.groupby("day", as_index=False)["Amount"].sum(),
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(
        daily["day"],
        daily["Amount"],
        width=0.8,
        color="tab:green",
        align="center",
        label="Daily spent",
    )
    avg_per_day = exp.beginning_balance / float(exp.days_total)
    ax.axhline(
        avg_per_day,
        color="tab:orange",
        linestyle="--",
        linewidth=1.2,
        label="Avg $/day if even",
    )
    amounts = daily["Amount"].to_numpy(dtype=float, copy=False)
    bar_max = float(amounts.max()) if len(amounts) else 0.0
    y_top = max(bar_max, avg_per_day) * 1.05
    ax.set_ylim(0.0, y_top if y_top > 0 else 1.0)
    ax.set_title("Total spending per day")
    ax.set_xlabel("Day")
    ax.set_ylabel("Spent ($)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(loc="upper right")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main() -> None:
    src = history_path()
    if not src.is_file():
        raise FileNotFoundError(f"Missing {src}")

    df = load_timeline(src)
    exp = load_expectation_params(src)
    out_dir = Path(__file__).resolve().parents[2] / "results"
    out_dir.mkdir(exist_ok=True)
    plot_balance(df, out_dir / "balance_over_time.png", exp)
    plot_daily_spending(df, out_dir / "daily_spending.png", exp)
    print(f"Wrote {out_dir / 'balance_over_time.png'}")
    print(f"Wrote {out_dir / 'daily_spending.png'}")


if __name__ == "__main__":
    main()
