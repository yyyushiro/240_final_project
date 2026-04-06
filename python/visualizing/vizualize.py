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
    # python/visualizing/vizualize.py -> repo/analyzing/history.json
    return Path(__file__).resolve().parents[2] / "analyzing" / "history.json"


def load_timeline(history_file: Path) -> pd.DataFrame:
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
    out_dir = Path(__file__).resolve().parent
    plot_balance(df, out_dir / "balance_over_time.png")
    plot_daily_spending(df, out_dir / "daily_spending.png")
    print(f"Wrote {out_dir / 'balance_over_time.png'}")
    print(f"Wrote {out_dir / 'daily_spending.png'}")


if __name__ == "__main__":
    main()
