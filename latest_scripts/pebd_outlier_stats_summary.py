import pandas as pd
from pathlib import Path

# ───────────────────────────────────────────────────────────────
# Configuration – change these as needed
# ───────────────────────────────────────────────────────────────
INPUT_FILE = "pebd_outliers_tolerance_5.csv"           # ← your outliers file
REPORT_DIR = Path("reports")                           # or full path if preferred

PEBD_THRESHOLD_PLUS  = 0     # days allowed when reported > calculated
PEBD_THRESHOLD_MINUS = 0     # days allowed when reported < calculated
IGNORE_THRESHOLD     = False   # True = treat ALL as mismatches (ignores thresholds)
# ───────────────────────────────────────────────────────────────

PERSON_ID_COL = "Electronic Intrchg Person Id"
REPORTED_PEBD_COL = "reported_pebd"
CALC_PEBD_COL     = "calculated_pebd"


def calculate_statistics(df):
    required = {REPORTED_PEBD_COL, CALC_PEBD_COL}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required - set(df.columns)}")

    df = df.copy()
    df[REPORTED_PEBD_COL] = pd.to_datetime(df[REPORTED_PEBD_COL], errors='coerce')
    df[CALC_PEBD_COL]     = pd.to_datetime(df[CALC_PEBD_COL],     errors='coerce')

    df_valid = df.dropna(subset=[REPORTED_PEBD_COL, CALC_PEBD_COL])

    total_records = len(df_valid)

    df_valid['pebd_diff_days'] = (df_valid[REPORTED_PEBD_COL] - df_valid[CALC_PEBD_COL]).dt.days.abs()

    if IGNORE_THRESHOLD:
        df_valid['is_match'] = False
    else:
        lower_bound = df_valid[CALC_PEBD_COL] - pd.Timedelta(days=PEBD_THRESHOLD_MINUS)
        upper_bound = df_valid[CALC_PEBD_COL] + pd.Timedelta(days=PEBD_THRESHOLD_PLUS)
        df_valid['is_match'] = (df_valid[REPORTED_PEBD_COL] >= lower_bound) & \
                               (df_valid[REPORTED_PEBD_COL] <= upper_bound)

    matches     = df_valid['is_match'].sum()
    mismatches  = total_records - matches
    match_pct   = matches / total_records * 100 if total_records > 0 else 0
    mismatch_pct = 100 - match_pct

    stats_diff = df_valid['pebd_diff_days'].describe()

    df_valid['Reported PEBD Year'] = df_valid[REPORTED_PEBD_COL].dt.year

    breakdown = (
        df_valid.groupby('Reported PEBD Year', as_index=False)
        .agg(
            Total_Records = ('is_match', 'count'),
            Matches       = ('is_match', 'sum')
        )
    )

    breakdown['Total_Records'] = breakdown['Total_Records'].astype(int)
    breakdown['Matches']       = breakdown['Matches'].astype(int)
    breakdown['Mismatches']    = breakdown['Total_Records'] - breakdown['Matches']

    breakdown['Match_%']    = breakdown['Matches'] / breakdown['Total_Records'] * 100
    breakdown['Mismatch_%'] = 100 - breakdown['Match_%']

    return {
        'total_records': total_records,
        'matches': matches,
        'mismatches': mismatches,
        'match_percentage': match_pct,
        'mismatch_percentage': mismatch_pct,
        'diff_stats': stats_diff,
        'breakdown_by_year': breakdown
    }


def save_statistics_to_csv(stats, report_dir: Path):
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "outliers_statistics.csv"

    with path.open("w", encoding="utf-8") as f:
        f.write("Total Records,Matches,Mismatches,Match %,Mismatch %,Max Diff Days,Min Diff Days,Avg Diff Days\n")
        s = stats
        d = s['diff_stats']
        f.write(
            f"{s['total_records']},{s['matches']},{s['mismatches']},"
            f"{s['match_percentage']:.1f},{s['mismatch_percentage']:.1f},"
            f"{d['max']},{d['min']},{d['mean']:.1f}\n"
        )


def save_statistics_to_txt(stats, report_dir: Path):
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "outliers_statistics.txt"

    with path.open("w", encoding="utf-8") as f:
        s = stats
        d = s['diff_stats']

        f.write("═" * 100 + "\n")
        f.write("PEBD OUTLIERS STATISTICS\n")
        f.write("═" * 100 + "\n\n")

        label_width = 36
        num_width   = 15
        pct_width   = 8

        mode = " (THRESHOLD IGNORED — ALL SHOWN AS MISMATCH)" if IGNORE_THRESHOLD else ""
        f.write(f"{'Total valid outliers with dates':<{label_width}}: {s['total_records']:>{num_width},d}{mode}\n")

        threshold_str = f"±{PEBD_THRESHOLD_MINUS}/{PEBD_THRESHOLD_PLUS}"
        matches_label = f"Within tolerance ({threshold_str} days)"
        f.write(f"{matches_label:<{label_width}}: {s['matches']:>{num_width},d}   ({s['match_percentage']:>{pct_width}.1f}%)\n")
        f.write(f"{'Mismatches / outside tolerance':<{label_width}}: {s['mismatches']:>{num_width},d}   ({s['mismatch_percentage']:>{pct_width}.1f}%)\n\n")

        f.write("Difference statistics (absolute days):\n")
        f.write(f"  • Max diff ........................ : {d['max']:>{num_width}.0f} days\n")
        f.write(f"  • Min diff ........................ : {d['min']:>{num_width}.0f} days\n")
        f.write(f"  • Avg diff ........................ : {d['mean']:>{num_width}.1f} days\n\n")

        if not s['breakdown_by_year'].empty:
            f.write("Breakdown by Reported PEBD Year:\n\n")

            col_widths = {
                'year': 6,
                'total': 14,
                'matches': 10,
                'mismatches': 12,
                'match_pct': 10,
                'mismatch_pct': 12
            }

            f.write(
                f"{'Year':^{col_widths['year']}} "
                f"{'Total':>{col_widths['total']}} "
                f"{'Within Tol':>{col_widths['matches']}} "
                f"{'Outside Tol':>{col_widths['mismatches']}} "
                f"{'Within %':>{col_widths['match_pct']}} "
                f"{'Outside %':>{col_widths['mismatch_pct']}}\n"
            )
            f.write("-" * (sum(col_widths.values()) + 5) + "\n")

            for _, row in s['breakdown_by_year'].iterrows():
                year = int(row['Reported PEBD Year'])
                f.write(
                    f"{year:>{col_widths['year']}} "
                    f"{int(row['Total_Records']):>{col_widths['total']},d} "
                    f"{int(row['Matches']):>{col_widths['matches']},d} "
                    f"{int(row['Mismatches']):>{col_widths['mismatches']},d} "
                    f"{row['Match_%']:>{col_widths['match_pct']}.1f} "
                    f"{row['Mismatch_%']:>{col_widths['mismatch_pct']}.1f}\n"
                )

            f.write("\n")


def save_mismatches_detail(df, report_dir: Path):
    df = df.copy()
    df[REPORTED_PEBD_COL] = pd.to_datetime(df[REPORTED_PEBD_COL], errors='coerce')
    df[CALC_PEBD_COL]     = pd.to_datetime(df[CALC_PEBD_COL],     errors='coerce')

    df_valid = df.dropna(subset=[REPORTED_PEBD_COL, CALC_PEBD_COL])

    df_valid['pebd_diff_days'] = (df_valid[REPORTED_PEBD_COL] - df_valid[CALC_PEBD_COL]).dt.days.abs()

    if IGNORE_THRESHOLD:
        mismatches_df = df_valid.copy()
    else:
        lower_bound = df_valid[CALC_PEBD_COL] - pd.Timedelta(days=PEBD_THRESHOLD_MINUS)
        upper_bound = df_valid[CALC_PEBD_COL] + pd.Timedelta(days=PEBD_THRESHOLD_PLUS)
        mismatches_df = df_valid[
            ~((df_valid[REPORTED_PEBD_COL] >= lower_bound) & (df_valid[REPORTED_PEBD_COL] <= upper_bound))
        ].copy()

    if mismatches_df.empty:
        print("No records outside tolerance → mismatch table not created.")
        return

    mismatches_df = mismatches_df.sort_values('pebd_diff_days', ascending=False)
    mismatches_df['Reported PEBD']   = mismatches_df[REPORTED_PEBD_COL].dt.strftime('%Y-%m-%d')
    mismatches_df['Calculated PEBD'] = mismatches_df[CALC_PEBD_COL].dt.strftime('%Y-%m-%d')
    mismatches_df['Reported PEBD Year'] = mismatches_df[REPORTED_PEBD_COL].dt.year

    output_path = report_dir / "outliers_mismatch_detail.csv"
    report_dir.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(f"# PEBD Outliers {'All Records (threshold ignored)' if IGNORE_THRESHOLD else 'Mismatch Detail'}\n")
        f.write(f"# Current tolerance window: -{PEBD_THRESHOLD_MINUS} / +{PEBD_THRESHOLD_PLUS} days\n")
        f.write("# Sorted by largest absolute difference\n\n")

    mismatches_df.to_csv(output_path, mode='a', index=False)
    print(f"Saved {len(mismatches_df):,} detailed mismatch records → {output_path}")


def main():
    df = pd.read_csv(INPUT_FILE)
    stats = calculate_statistics(df)

    save_mismatches_detail(df, REPORT_DIR)
    save_statistics_to_csv(stats, REPORT_DIR)
    save_statistics_to_txt(stats, REPORT_DIR)

    print("\nDone. Reports + outliers_mismatch_detail.csv saved in:", REPORT_DIR.resolve())


if __name__ == "__main__":
    main()