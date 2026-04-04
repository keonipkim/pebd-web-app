import pandas as pd
from pathlib import Path

# ───────────────────────────────────────────────────────────────
# Threshold settings – change these two values as needed
# ───────────────────────────────────────────────────────────────
PEBD_THRESHOLD_PLUS  = 5    # allowed days when reported PEBD is LATER than calculated
PEBD_THRESHOLD_MINUS = 5    # allowed days when reported PEBD is EARLIER than calculated
IGNORE_THRESHOLD     = False   # Set to True to ignore thresholds → treat ALL as mismatches
# ───────────────────────────────────────────────────────────────

def calculate_statistics(df):
    required = {'Pay Entry Base Date', 'calculated_pebd'}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required - set(df.columns)}")

    df = df.copy()
    df['Pay Entry Base Date'] = pd.to_datetime(df['Pay Entry Base Date'], errors='coerce')
    df['calculated_pebd']     = pd.to_datetime(df['calculated_pebd'],     errors='coerce')

    df_valid = df.dropna(subset=['Pay Entry Base Date', 'calculated_pebd'])

    total_records = len(df_valid)

    df_valid['pebd_diff_days'] = (df_valid['Pay Entry Base Date'] - df_valid['calculated_pebd']).dt.days.abs()

    if IGNORE_THRESHOLD:
        df_valid['is_match'] = False
    else:
        lower_bound = df_valid['calculated_pebd'] - pd.Timedelta(days=PEBD_THRESHOLD_MINUS)
        upper_bound = df_valid['calculated_pebd'] + pd.Timedelta(days=PEBD_THRESHOLD_PLUS)
        df_valid['is_match'] = (df_valid['Pay Entry Base Date'] >= lower_bound) & \
                               (df_valid['Pay Entry Base Date'] <= upper_bound)

    matches     = df_valid['is_match'].sum()
    mismatches  = total_records - matches
    match_pct   = matches / total_records * 100 if total_records > 0 else 0
    mismatch_pct = 100 - match_pct

    stats_diff = df_valid['pebd_diff_days'].describe()

    df_valid['Reported PEBD Year'] = df_valid['Pay Entry Base Date'].dt.year

    breakdown = (
        df_valid.groupby('Reported PEBD Year', as_index=False)
        .agg(
            Total_Records = ('is_match', 'count'),
            Matches       = ('is_match', 'sum')
        )
    )

    # ─── Clean long-term fix: force integer types ───────────────────
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
    path = report_dir / "statistics.csv"

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
    path = report_dir / "statistics.txt"

    with path.open("w", encoding="utf-8") as f:
        s = stats
        d = s['diff_stats']

        f.write("═" * 100 + "\n")
        f.write("PEBD VALIDATION RESULTS (Component-based DEP filtering)\n")
        f.write("═" * 100 + "\n\n")

        # ─────────────── Top summary ───────────────
        label_width = 36
        num_width   = 15
        pct_width   = 8

        mode = " (THRESHOLD IGNORED — ALL RECORDS SHOWN AS MISMATCH)" if IGNORE_THRESHOLD else ""
        f.write(f"{'Total valid date pairs':<{label_width}}: {s['total_records']:>{num_width},d}{mode}\n")

        threshold_str = f"±{PEBD_THRESHOLD_MINUS}/{PEBD_THRESHOLD_PLUS}"
        matches_label = f"Matches ({threshold_str} days)"
        f.write(f"{matches_label:<{label_width}}: {s['matches']:>{num_width},d}   ({s['match_percentage']:>{pct_width}.1f}%)\n")
        f.write(f"{'Mismatches':<{label_width}}: {s['mismatches']:>{num_width},d}   ({s['mismatch_percentage']:>{pct_width}.1f}%)\n\n")

        # ─────────────── Difference stats ───────────────
        f.write("Difference statistics (absolute days):\n")
        f.write(f"  • Max diff ........................ : {d['max']:>{num_width}.0f} days\n")
        f.write(f"  • Min diff ........................ : {d['min']:>{num_width}.0f} days\n")
        f.write(f"  • Avg diff ........................ : {d['mean']:>{num_width}.1f} days\n\n")

        # ─────────────── Year breakdown ───────────────
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

            # Header
            f.write(
                f"{'Year':^{col_widths['year']}} "
                f"{'Total Records':>{col_widths['total']}} "
                f"{'Matches':>{col_widths['matches']}} "
                f"{'Mismatches':>{col_widths['mismatches']}} "
                f"{'Match %':>{col_widths['match_pct']}} "
                f"{'Mismatch %':>{col_widths['mismatch_pct']}}\n"
            )
            f.write("-" * (sum(col_widths.values()) + 5) + "\n")  # +5 for spaces

            # Data rows – safe integer formatting
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
    df['Pay Entry Base Date'] = pd.to_datetime(df['Pay Entry Base Date'], errors='coerce')
    df['calculated_pebd']     = pd.to_datetime(df['calculated_pebd'],     errors='coerce')

    df_valid = df.dropna(subset=['Pay Entry Base Date', 'calculated_pebd'])

    df_valid['pebd_diff_days'] = (df_valid['Pay Entry Base Date'] - df_valid['calculated_pebd']).dt.days.abs()

    if IGNORE_THRESHOLD:
        mismatches_df = df_valid.copy()
        print("THRESHOLD IGNORED → saving ALL valid records to mismatch table")
    else:
        lower_bound = df_valid['calculated_pebd'] - pd.Timedelta(days=PEBD_THRESHOLD_MINUS)
        upper_bound = df_valid['calculated_pebd'] + pd.Timedelta(days=PEBD_THRESHOLD_PLUS)
        mismatches_df = df_valid[
            ~((df_valid['Pay Entry Base Date'] >= lower_bound) & (df_valid['Pay Entry Base Date'] <= upper_bound))
        ].copy()

    if mismatches_df.empty:
        print("No records outside threshold → mismatch table not created.")
        return

    mismatches_df = mismatches_df.sort_values('pebd_diff_days', ascending=False)
    mismatches_df['Reported PEBD']   = mismatches_df['Pay Entry Base Date'].dt.strftime('%Y-%m-%d')
    mismatches_df['Calculated PEBD'] = mismatches_df['calculated_pebd'].dt.strftime('%Y-%m-%d')
    mismatches_df['Reported PEBD Year'] = mismatches_df['Pay Entry Base Date'].dt.year

    output_path = report_dir / "pebd_stats_mismatch_tbl.csv"
    report_dir.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(f"# PEBD {'ALL Records (threshold ignored)' if IGNORE_THRESHOLD else 'Mismatch'} Table\n")
        f.write(f"# Tolerance window: -{PEBD_THRESHOLD_MINUS} / +{PEBD_THRESHOLD_PLUS} days\n")
        f.write("# Sorted by largest absolute difference first\n\n")

    mismatches_df.to_csv(output_path, mode='a', index=False)
    print(f"Saved {len(mismatches_df):,} records → {output_path}")


def main():
    INPUT_FILE = 'output_summary.csv'
    REPORT_DIR = Path('/home/keonipkim/projects/MISSO-09/latest_scripts/reports')

    df = pd.read_csv(INPUT_FILE)
    stats = calculate_statistics(df)

    save_mismatches_detail(df, REPORT_DIR)

    save_statistics_to_csv(stats, REPORT_DIR)
    save_statistics_to_txt(stats, REPORT_DIR)

    print("Done. Reports + pebd_stats_mismatch_tbl.csv saved.")


if __name__ == "__main__":
    main()