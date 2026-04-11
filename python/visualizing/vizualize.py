import json
import os
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


def plot_balance(df: pd.DataFrame, out: Path) -> None:
    """plot the fluctuation of user's balance over time.

    Args:
        df (pd.DataFrame): the given data frame of the user's spending history.
        out (Path): the path for the output graph.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Post Date"], df["Balance"], color="tab:blue", linewidth=1.2)
    ax.set_title("Balance over time")
    ax.set_xlabel("Date")
    # Date axes use matplotlib's internal day numbers; plain Timestamp can be ignored.
    ax.set_xlim(
        float(mdates.datestr2num("2026-01-12")),
        float(mdates.datestr2num("2026-05-03")),
    )
    ax.set_ylabel("Balance ($)")
    ax.set_ylim(0, 1000)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_daily_spending(df: pd.DataFrame, out: Path) -> None:
    """plot the user's daily dining dollars usage over time.

    Args:
        df (pd.DataFrame): the given data frame of user's spending history.
        out (Path): the path for the output graph.
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
    )
    ax.set_title("Total spending per day")
    ax.set_xlabel("Day")
    ax.set_ylabel("Spent ($)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main() -> None:
    src = history_path()
    if not src.is_file():
        raise FileNotFoundError(f"Missing {src}")

    df = load_timeline(src)
    out_dir = Path(__file__).resolve().parents[2] / "results"
    out_dir.mkdir(exist_ok=True)
    plot_balance(df, out_dir / "balance_over_time.png")
    plot_daily_spending(df, out_dir / "daily_spending.png")
    print(f"Wrote {out_dir / 'balance_over_time.png'}")
    print(f"Wrote {out_dir / 'daily_spending.png'}")


if __name__ == "__main__":
    main()
