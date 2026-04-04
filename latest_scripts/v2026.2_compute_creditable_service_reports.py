import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
INPUT_FILE = "D188.csv"   # change if needed
OUTPUT_DETAIL = "output_detail.csv"
OUTPUT_SUMMARY = "output_summary.csv"
REPORT_DIR = Path("reports")
PERSON_ID_COL = "Electronic Intrchg Person Id"  # EDIPI
PEBD_COL = "Pay Entry Base Date"                # reported PEBD (system)
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
LOST_APPLY_COL = "Service Data Tm Lost Apply flg"  # not used in mask anymore
REMARK_SEQ_COL = "Remark Sequence Number Rmk 188"
valid_branches = {"USMC", "NG", "USAF", "USN", "USCG", "USA", "USSF"}
valid_comp = {"REG", "RES", "STATE"}          # DEP excluded from creditable
valid_reasons = {"ACT", "IHCA", "CNFD", "EXPECC", "INACT", "UA/DES"}
lost_reasons = {"UA/DES", "CNFD", "EXPECC", "IHFA", "IHCA"}

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def read_input(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xlsx":
        df = pd.read_excel(path, dtype=str)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path, dtype=str, parse_dates=DATE_COLS)
    else:
        raise ValueError("INPUT_FILE must be .xlsx or .csv")
    # Filter rows with ADJ flag set
    df = df[df[ADJUST_FLAG_COL] != "1"]
    return df

def to_date(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_datetime(df[col], errors="coerce").dt.date

def adjust_day(day: int, month: int, year: int) -> int:
    """
    Apply DoDFMR Chapter 1 + practical adjustment rules to BOTH start and end dates.
    - Any 31 → 30
    - Feb 28 (non-leap) or 29 (leap) → 30 when used as end date or to normalize partial Feb
    - Feb 28 in leap year left as 28 only if it's not forced to 30 by context (but we adjust for consistency)
    """
    if day == 31:
        return 30
    if month == 2:
        is_leap = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
        if day in (28, 29):
            return 30   # Standard practice for creditable service ends/starts in Feb
    return day

def compute_segment_days_30(start: date, end: date) -> int:
    if start is None or end is None or start > end:
        return 0

    ys, ms, ds = start.year, start.month, start.day
    ye, me, de = end.year, end.month, end.day

    # Adjust both start and end days per regulation/practice
    ds = adjust_day(ds, ms, ys)
    de = adjust_day(de, me, ye)

    # Proper 30/360 subtraction with borrow
    days = de - ds
    months = me - ms
    years = ye - ys

    if days < 0:
        days += 30
        months -= 1

    if months < 0:
        months += 12
        years -= 1

    total = years * 360 + months * 30 + days + 1  # +1 makes it inclusive

    # For ongoing service ("PRESENT"), decide inclusivity
    # Most systems include the as-of date; comment out the next block if you want to exclude today
    # if end == date.today():
    #     total -= 1

    return max(total, 0)  # never negative

def ymd_from_days_30(total_days: int):
    years = total_days // 360
    rem = total_days % 360
    months = rem // 30
    days = rem % 30
    return years, months, days

def format_date(d) -> str:
    if pd.isna(d) or d is None:
        return "N/A"
    if isinstance(d, pd.Timestamp):
        d = d.date()
    return d.strftime("%Y/%m/%d")

def merge_creditable_segments(df_person: pd.DataFrame) -> pd.DataFrame:
    cred = df_person[df_person["is_creditable_for_basic_pay"]].copy()
    cred = cred.dropna(subset=["Service Data From Dt"])
    if len(cred) <= 1:
        return df_person
    cred = cred.sort_values(by=["Service Data From Dt", "Service Data To Dt"], ascending=[True, True])
    merged = []
    cur_start = None
    cur_end = None
    today = date.today()
    for _, r in cred.iterrows():
        s = r["Service Data From Dt"]
        e = r["Service Data To Dt"]
        e_eff = e if not pd.isna(e) else today
        if cur_start is None:
            cur_start, cur_end = s, e_eff
            continue
        if s <= (cur_end + timedelta(days=1)):
            if e_eff > cur_end:
                cur_end = e_eff
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = s, e_eff
    if cur_start is not None:
        merged.append((cur_start, cur_end))
    merged_rows = []
    base_row = cred.iloc[0].copy()
    for idx, (s, e_eff) in enumerate(merged, start=1):
        row = base_row.copy()
        row["Service Data From Dt"] = s
        row["Service Data To Dt"] = e_eff
        row["segment_days_actual"] = (e_eff - s).days + 1 if pd.notna(e_eff) and pd.notna(s) else 0
        row["segment_days_30"] = compute_segment_days_30(s, e_eff)
        row["lost_time_days"] = 0
        row["net_creditable_days"] = row["segment_days_30"]
        row[REMARK_SEQ_COL] = idx
        merged_rows.append(row)
    merged_df = pd.DataFrame(merged_rows)
    non_cred = df_person[~df_person["is_creditable_for_basic_pay"]].copy()
    combined = pd.concat([merged_df, non_cred], ignore_index=True)
    return combined

# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main(target_edipi: str | None = None):
    path = Path(INPUT_FILE)
    df = read_input(path)

    # Ensure date columns exist and convert
    for c in DATE_COLS:
        if c not in df.columns:
            df[c] = pd.NA
        else:
            df[c] = to_date(df, c)

    # Core numeric columns
    if REMARK_SEQ_COL not in df.columns:
        df[REMARK_SEQ_COL] = 0
    df[REMARK_SEQ_COL] = (
        pd.to_numeric(df[REMARK_SEQ_COL], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    # ------------------------------------------------------------------
    # SEGMENT DAYS (actual & 30-day method) ON ORIGINAL ROWS
    # ------------------------------------------------------------------
    df["segment_days_actual"] = (
        (df["Service Data To Dt"] - df["Service Data From Dt"]).apply(
            lambda x: x.days + 1 if pd.notna(x) else 0
        )
    )
    as_of = date.today()

    def segment_30_with_present(r):
        start = r["Service Data From Dt"]
        end = r["Service Data To Dt"]
        if end is None or pd.isna(end):
            end = as_of
        return compute_segment_days_30(start, end)

    df["segment_days_30"] = df.apply(segment_30_with_present, axis=1)

    # ------------------------------------------------------------------
    # LOST TIME DAYS (30-day method) ON ORIGINAL ROWS
    # ------------------------------------------------------------------
    df["lost_time_days"] = 0
    lost_mask = df[REASON_COL].isin(lost_reasons)
    df.loc[lost_mask, "lost_time_days"] = df.loc[lost_mask, "segment_days_30"]

    # ------------------------------------------------------------------
    # CREDITABLE FLAG ON ORIGINAL ROWS
    # ------------------------------------------------------------------
    df["is_creditable_for_basic_pay"] = False
    credit_mask = (
        (df[ADJUST_FLAG_COL].astype(str).str.strip() != "1") &
        (df[BRANCH_COL].isin(valid_branches)) &
        (df[COMP_COL].isin(valid_comp)) &
        (df[REASON_COL].isin(valid_reasons))
    )
    df.loc[credit_mask, "is_creditable_for_basic_pay"] = True

    df["net_creditable_days"] = 0
    df.loc[df["is_creditable_for_basic_pay"], "net_creditable_days"] = (
        df.loc[df["is_creditable_for_basic_pay"], "segment_days_30"]
        - df.loc[df["is_creditable_for_basic_pay"], "lost_time_days"]
    )

    df_detail = df.copy()

    # ------------------------------------------------------------------
    # MERGE OVERLAPPING CREDITABLE SEGMENTS PER PERSON
    # ------------------------------------------------------------------
    merged_list = []
    for edipi, grp in df.groupby(PERSON_ID_COL, as_index=False):
        merged_list.append(merge_creditable_segments(grp))
    df_merged = pd.concat(merged_list, ignore_index=True)

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------
    summary_pebd = (
        df_detail.groupby(PERSON_ID_COL, as_index=False)
        .agg(total_creditable_days=("net_creditable_days", "sum"))
    )

    summary_display = (
        df_detail.groupby(PERSON_ID_COL, as_index=False)
        .agg(
            gross_creditable_days=("segment_days_30", "sum"),
            total_lost_time=("lost_time_days", "sum"),
        )
    )
    summary_display["display_net_days"] = (
        summary_display["gross_creditable_days"] - summary_display["total_lost_time"]
    )

    summary = summary_pebd.merge(summary_display, on=PERSON_ID_COL, how="left")

    ymd = summary["total_creditable_days"].apply(ymd_from_days_30)
    summary[["years", "months", "days"]] = pd.DataFrame(ymd.tolist(), index=summary.index)

    if PEBD_COL in df.columns:
        pebd_per = df.groupby(PERSON_ID_COL, as_index=False)[PEBD_COL].first()
        summary = summary.merge(pebd_per, on=PERSON_ID_COL, how="left")
    else:
        summary[PEBD_COL] = pd.NaT

    as_of_pebd = date.today()
    summary["as_of_date"] = as_of_pebd

    def calc_pebd(row):
        d = row["as_of_date"]
        if pd.isna(d):
            return pd.NaT
        y, m, dd = int(row["years"]), int(row["months"]), int(row["days"])
        y0 = d.year - y
        m0 = d.month - m
        while m0 <= 0:
            m0 += 12
            y0 -= 1
        max_days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m0 - 1]
        day = min(d.day, max_days)
        temp = date(y0, m0, day)
        temp = temp - timedelta(days=dd)
        return temp

    summary["calculated_pebd"] = summary.apply(calc_pebd, axis=1)

    def diff_days(row):
        if pd.isna(row.get(PEBD_COL)) or pd.isna(row.get("calculated_pebd")):
            return pd.NA
        return (row[PEBD_COL] - row["calculated_pebd"]).days

    summary["pebd_diff_days"] = summary.apply(diff_days, axis=1)

    # ------------------------------------------------------------------
    # OPTIONAL FILTER BY EDIPI
    # ------------------------------------------------------------------
    if target_edipi is not None:
        df_detail = df_detail[df_detail[PERSON_ID_COL] == target_edipi].copy()
        summary = summary[summary[PERSON_ID_COL] == target_edipi].copy()

    # ------------------------------------------------------------------
    # WRITE CSV OUTPUTS
    # ------------------------------------------------------------------
    df_detail.to_csv(OUTPUT_DETAIL, index=False)
    summary.to_csv(OUTPUT_SUMMARY, index=False)

    # ------------------------------------------------------------------
    # GENERATE PER-PERSON TEXT REPORTS
    # ------------------------------------------------------------------
    REPORT_DIR.mkdir(exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for _, row in summary.iterrows():
        edipi = str(row[PERSON_ID_COL])
        reported_pebd = row.get(PEBD_COL, pd.NaT)
        calc_pebd_val = row.get("calculated_pebd", pd.NaT)
        gross = int(row["gross_creditable_days"])
        lost = int(row["total_lost_time"])
        net_display = int(row["display_net_days"])
        y, m, d = int(row["years"]), int(row["months"]), int(row["days"])
        diff = row.get("pebd_diff_days", pd.NA)
        sub = df_detail[df_detail[PERSON_ID_COL] == row[PERSON_ID_COL]].copy()
        sub = sub[sub[COMP_COL] != "DEP"]
        sub = sub.sort_values(by=["Service Data From Dt", "Service Data To Dt"], ascending=[True, True])

        lines = []
        lines.append("                          STATEMENT OF SERVICE REPORT                           ")
        lines.append("             Per DODFMR Chapter 1 - Creditable Service Computation              ")
        lines.append("=" * 80)
        lines.append("")
        lines.append(
            f"EDIPI: {edipi:<15} Reported PEBD: {format_date(reported_pebd):<15}  AFADBD: See MCTFS TBIR"
        )
        lines.append("=" * 80)
        lines.append("")
        lines.append("Branch       Component    Reason       From (YYYY/MM/DD)  To (YYYY/MM/DD)    TmLost")
        lines.append("-" * 80)
        for _, s in sub.iterrows():
            branch = str(s[BRANCH_COL])
            comp = str(s[COMP_COL])
            reason = str(s[REASON_COL])
            from_str = format_date(s["Service Data From Dt"])
            to_str = format_date(s["Service Data To Dt"])
            if pd.isna(s["Service Data To Dt"]):
                to_str = "PRESENT"
            lost_str = (
                f"{int(s['lost_time_days'])}d" if s["lost_time_days"] and int(s["lost_time_days"]) > 0 else "N/A"
            )
            lines.append(
                f"{branch:<12}{comp:<12}{reason:<12}{from_str:<18}{to_str:<18}{lost_str:<6}"
            )
        lines.append("-" * 80)
        lines.append("")
        lines.append("Complete Service Timeline (DODFMR Method - All Periods):")
        lines.append("Start Date         End Date               Days")
        lines.append("-" * 80)
        for _, s in sub.iterrows():
            from_str = format_date(s["Service Data From Dt"])
            to_str = format_date(s["Service Data To Dt"])
            if pd.isna(s["Service Data To Dt"]):
                to_str = "PRESENT"
            days_val = s.get("segment_days_30")
            days_30 = 0 if pd.isna(days_val) else int(days_val)
            lines.append(f"{from_str:<18}{to_str:<22}{days_30} days")
        lines.append("")
        lines.append("=" * 80)
        lines.append("SERVICE SUMMARY AND PEBD VALIDATION:")
        lines.append("-" * 80)
        lines.append(f"Gross Creditable Service: {gross:,} days")
        lines.append(f"Total Lost Time:          {lost:,} days")
        lines.append(f"Net Creditable Service:   {net_display:,} days ({y}y {m}m {d}d)")
        lines.append("")
        lines.append("PEBD COMPARISON:")
        lines.append(f"Recorded PEBD (System):   {format_date(reported_pebd)}")
        lines.append(f"Calculated PEBD (DODFMR): {format_date(calc_pebd_val)}")
        diff_str = "N/A" if pd.isna(diff) else f"{diff:+d} days"
        lines.append(f"Validation Status:        DIFF: {diff_str}")
        lines.append("=" * 80)
        lines.append(f"Generated on: {now_str}")
        lines.append("Report computed per DODFMR Chapter 1 regulations")
        lines.append("PEBD calculation uses DODFMR Y/M/D normalization method")

        report_path = REPORT_DIR / f"statement_of_service_{edipi}.txt"
        # report_path.write_text("\n".join(lines), encoding="utf-8")   # uncomment when ready

    print("Done.")
    print(f"Detail file:  {OUTPUT_DETAIL}")
    print(f"Summary file: {OUTPUT_SUMMARY}")
    print(f"Reports dir:  {REPORT_DIR.resolve()}")

if __name__ == "__main__":
    import sys
    main(target_edipi=sys.argv[1] if len(sys.argv) > 1 else None)