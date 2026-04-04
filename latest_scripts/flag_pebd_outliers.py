import pandas as pd
from pathlib import Path
from datetime import date, timedelta

# --------------------------------------------------
# CONFIG - same as your main script where possible
# --------------------------------------------------
INPUT_FILE = "D188.csv"
OUTPUT_OUTLIERS = "pebd_outliers_tolerance_5.csv"
TOLERANCE_DAYS = 5

PERSON_ID_COL = "Electronic Intrchg Person Id"
PEBD_COL = "Pay Entry Base Date"
DATE_COLS = [
    "Armed Forces Orig Entry Date",
    "Pay Entry Base Date",
    "Service Data From Dt",
    "Service Data To Dt",
    "Service Data Orig Entry Dt",
    "Service Data Act Du Base Dt",
    "Service Data Pay Entry Base Dt",
]
BRANCH_COL = "Service Data Branch Svc Cd"
COMP_COL = "Service Data Comp Of Svc Cd"
REASON_COL = "Service Data Reason Cd"
ADJUST_FLAG_COL = "Service Data Adjust Flg"
valid_branches = {"USMC", "NG", "USAF", "USN", "USCG", "USA", "USSF"}
valid_comp = {"REG", "RES", "STATE"}
valid_reasons = {"ACT", "IHCA", "CNFD", "EXPECC", "INACT", "UA/DES"}
lost_reasons = {"UA/DES", "CNFD", "EXPECC", "IHFA", "IHCA"}

# --------------------------------------------------
# HELPERS (copy-pasted from your fixed version)
# --------------------------------------------------
def to_date(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_datetime(df[col], errors="coerce").dt.date

def adjust_day(day: int, month: int, year: int) -> int:
    if day == 31:
        return 30
    if month == 2:
        is_leap = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
        if day in (28, 29):
            return 30
    return day

def compute_segment_days_30(start: date, end: date) -> int:
    if start is None or end is None or start > end:
        return 0
    ys, ms, ds = start.year, start.month, start.day
    ye, me, de = end.year, end.month, end.day
    ds = adjust_day(ds, ms, ys)
    de = adjust_day(de, me, ye)
    days = de - ds
    months = me - ms
    years = ye - ys
    if days < 0:
        days += 30
        months -= 1
    if months < 0:
        months += 12
        years -= 1
    total = years * 360 + months * 30 + days + 1
    return max(total, 0)

def ymd_from_days_30(total_days: int):
    years = total_days // 360
    rem = total_days % 360
    months = rem // 30
    days = rem % 30
    return years, months, days

def calc_pebd(as_of: date, years: int, months: int, days: int) -> date | None:
    if years == 0 and months == 0 and days == 0:
        return as_of
    y0 = as_of.year - years
    m0 = as_of.month - months
    while m0 <= 0:
        m0 += 12
        y0 -= 1
    max_days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m0 - 1]
    day = min(as_of.day, max_days)
    temp = date(y0, m0, day)
    temp -= timedelta(days=days)
    return temp

# --------------------------------------------------
# MAIN LOGIC
# --------------------------------------------------
def main():
    path = Path(INPUT_FILE)
    if not path.exists():
        print(f"Input file not found: {path}")
        return

    print("Reading input data...")
    df = pd.read_csv(path, dtype=str, parse_dates=DATE_COLS)

    # Basic filtering (same as main script)
    df = df[df[ADJUST_FLAG_COL] != "1"]

    for c in DATE_COLS:
        if c in df.columns:
            df[c] = to_date(df, c)

    df["segment_days_30"] = 0
    as_of = date.today()
    for idx, row in df.iterrows():
        start = row["Service Data From Dt"]
        end = row["Service Data To Dt"]
        if pd.isna(end):
            end = as_of
        if pd.notna(start):
            df.at[idx, "segment_days_30"] = compute_segment_days_30(start, end)

    df["lost_time_days"] = 0
    lost_mask = df[REASON_COL].isin(lost_reasons)
    df.loc[lost_mask, "lost_time_days"] = df.loc[lost_mask, "segment_days_30"]

    credit_mask = (
        (df[BRANCH_COL].isin(valid_branches)) &
        (df[COMP_COL].isin(valid_comp)) &
        (df[REASON_COL].isin(valid_reasons))
    )
    df["net_creditable_days"] = 0
    df.loc[credit_mask, "net_creditable_days"] = (
        df.loc[credit_mask, "segment_days_30"] - df.loc[credit_mask, "lost_time_days"]
    )

    # Summarize per person
    print("Summarizing per EDIPI...")
    summary = (
        df.groupby(PERSON_ID_COL, as_index=False)
        .agg(
            total_net_days=("net_creditable_days", "sum"),
            gross_days=("segment_days_30", "sum"),
            lost_days=("lost_time_days", "sum"),
            reported_pebd=(PEBD_COL, "first")
        )
    )

    # YMD and calculated PEBD
    ymd = summary["total_net_days"].apply(ymd_from_days_30)
    summary[["years", "months", "days"]] = pd.DataFrame(ymd.tolist(), index=summary.index)

    summary["as_of_date"] = as_of
    summary["calculated_pebd"] = summary.apply(
        lambda r: calc_pebd(r["as_of_date"], int(r["years"]), int(r["months"]), int(r["days"])),
        axis=1
    )

    # Fixed PEBD difference calculation
    reported_dt = pd.to_datetime(summary["reported_pebd"], errors="coerce")
    calc_dt     = pd.to_datetime(summary["calculated_pebd"], errors="coerce")
    summary["pebd_diff_days"] = (reported_dt - calc_dt).dt.days

    # Filter outliers
    outliers = summary[
        (abs(summary["pebd_diff_days"]) > TOLERANCE_DAYS) |
        (summary["pebd_diff_days"].isna())
    ].copy()

    outliers["diff_abs"] = outliers["pebd_diff_days"].abs()
    outliers = outliers.sort_values("diff_abs", ascending=False)

    # Select useful columns for triage
    cols_to_keep = [
        PERSON_ID_COL,
        "reported_pebd",
        "calculated_pebd",
        "pebd_diff_days",
        "total_net_days",
        "years", "months", "days",
        "gross_days", "lost_days",
        "as_of_date"
    ]
    outliers = outliers[[c for c in cols_to_keep if c in outliers.columns]]

    print(f"Found {len(outliers)} outliers (diff > ±{TOLERANCE_DAYS} days or missing)")
    outliers.to_csv(OUTPUT_OUTLIERS, index=False)
    print(f"Outliers saved to: {OUTPUT_OUTLIERS}")

if __name__ == "__main__":
    main()