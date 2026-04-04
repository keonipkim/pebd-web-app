import pandas as pd
import os
import time
import datetime
from datetime import timedelta
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import warnings
from dateutil.relativedelta import relativedelta
import calendar

warnings.filterwarnings('ignore')

summary_lines = []
def print_and_capture(line=""):
    print(line)
    summary_lines.append(line)

def get_normalized_day_for_calculation(date):
    if pd.isna(date):
        return date
    if date.day == 31:
        return 30
    elif date.month == 2 and date.day == 28 and not calendar.isleap(date.year):
        return 30
    elif date.month == 2 and date.day == 29:
        return 30
    else:
        return date.day

def compute_service_dodfmr_ymd(from_date, to_date):
    if pd.isna(from_date) or pd.isna(to_date):
        return (0, 0, 0)
    start_year, start_month = from_date.year, from_date.month
    end_year, end_month = to_date.year, to_date.month
    start_day = get_normalized_day_for_calculation(from_date)
    end_day = get_normalized_day_for_calculation(to_date)
    if end_day < start_day:
        end_day += 30
        end_month -= 1
    if end_month < start_month:
        end_month += 12
        end_year -= 1
    years = end_year - start_year
    months = end_month - start_month
    days = end_day - start_day + 1
    if days >= 30:
        months += days // 30
        days = days % 30
    if months >= 12:
        years += months // 12
        months = months % 12
    return (years, months, days)

def sum_ymd_periods(periods):
    total_y, total_m, total_d = 0, 0, 0
    for y, m, d in periods:
        total_y += y
        total_m += m
        total_d += d
    if total_d >= 30:
        total_m += total_d // 30
        total_d = total_d % 30
    if total_m >= 12:
        total_y += total_m // 12
        total_m = total_m % 12
    return (total_y, total_m, total_d)

def ymd_to_approx_days(ymd):
    y, m, d = ymd
    return y * 365 + m * 30 + d

def calculate_pebd_dodfmr_method(ref_date, net_creditable_days):
    if net_creditable_days <= 0:
        return ref_date
    remaining_days = net_creditable_days - 1
    years_to_subtract = remaining_days // 365
    remaining_days %= 365
    months_to_subtract = remaining_days // 30
    days_to_subtract = remaining_days % 30
    result_year = ref_date.year - years_to_subtract
    result_month = ref_date.month - months_to_subtract
    ref_normalized_day = get_normalized_day_for_calculation(ref_date)
    result_day = ref_normalized_day - days_to_subtract
    if result_day < 1:
        result_day += 30
        result_month -= 1
    if result_month < 1:
        result_month += 12
        result_year -= 1
    try:
        if result_month == 2:
            if calendar.isleap(result_year):
                result_day = min(result_day, 29)
            else:
                result_day = min(result_day, 28)
        elif result_month in [4, 6, 9, 11]:
            result_day = min(result_day, 30)
        else:
            result_day = min(result_day, 31)
        return pd.Timestamp(result_year, result_month, result_day)
    except ValueError:
        return ref_date - timedelta(days=net_creditable_days - 1)

def is_last_day_of_month(date):
    if pd.isna(date):
        return False
    return date.day == calendar.monthrange(date.year, date.month)[1]

def periods_are_continuous(prev_end, next_start):
    if next_start == prev_end + timedelta(days=1):
        return True
    if is_last_day_of_month(prev_end) and is_last_day_of_month(next_start):
        next_month_expected = (prev_end.month % 12) + 1
        next_year_expected = prev_end.year + 1 if prev_end.month == 12 else prev_end.year
        return next_start.month == next_month_expected and next_start.year == next_year_expected
    return False

def merge_all_periods(periods):
    if not periods:
        return []
    sorted_periods = sorted(periods, key=lambda p: p[0])
    merged = []
    for start, end in sorted_periods:
        if not merged:
            merged.append([start, end])
        else:
            last_start, last_end = merged[-1]
            if periods_are_continuous(last_end, start):
                merged[-1][1] = max(last_end, end)
            else:
                merged.append([start, end])
    return merged

def sum_gross_creditable_days(all_periods_timeline):
    merged = merge_all_periods(all_periods_timeline)
    total_ymd = (0, 0, 0)
    for start, end in merged:
        ymd = compute_service_dodfmr_ymd(start, end)
        total_ymd = tuple(map(sum, zip(total_ymd, ymd)))
    total_ymd = sum_ymd_periods([total_ymd])
    total_days = ymd_to_approx_days(total_ymd)
    return total_days, merged

def calculate_lost_time_days(all_periods_info, special_reason_codes):
    lost_periods = []
    for info in all_periods_info:
        if info['reason'] in special_reason_codes:
            lost_periods.append(compute_service_dodfmr_ymd(info['from_dt'], info['to_dt']))
    total_lost_ymd = (0, 0, 0)
    for y, m, d in lost_periods:
        total_lost_ymd = tuple(map(sum, zip(total_lost_ymd, (y, m, d))))
    total_lost_ymd = sum_ymd_periods([total_lost_ymd])
    return ymd_to_approx_days(total_lost_ymd)

AS_OF_DATE = pd.Timestamp(datetime.datetime.now().date() - timedelta(days=1))

def process_person_worker(args):
    uuid, person_df, _, special_reason_codes = args
    reported_pebd = person_df['Pay Entry Base Date'].dropna().iloc[0] \
        if not person_df['Pay Entry Base Date'].dropna().empty else None
    edipi = person_df.get('Electronic Intrchg Person Id')
    edipi = '' if pd.isna(edipi.iloc[0]) else edipi.iloc[0]
    creditable_periods = person_df[person_df['IsCreditable'] == True]

    if (len(creditable_periods) == 1 and 
        creditable_periods['Service Data To Dt'].isna().iloc[0]):
        from_dt = creditable_periods['Service Data From Dt'].iloc[0]
        match = pd.to_datetime(reported_pebd) == pd.to_datetime(from_dt)
        return {
            'uuid': uuid,
            'edipi': edipi,
            'reported_pebd': reported_pebd.strftime('%Y/%m/%d') if pd.notna(reported_pebd) else None,
            'calculated_pebd': from_dt.strftime('%Y/%m/%d'),
            'difference_days': 0 if match else None,
            'total_creditable_days': 0,
            'creditable_periods': 1,
            'fraudulent_periods': person_df['is_fraudulent'].sum(),
            'aggregated_periods': 0,
            'total_lost_days': 0,
            'net_service_days': 0,
            'service_years_months_days': None
        }

    all_periods = []
    all_periods_info = []
    latest_open_from = None
    has_open_period = False
    for _, row in person_df.iterrows():
        if not row['IsCreditable']:
            continue
        branch = row['Service Data Branch Svc Cd'].upper()
        component = row['Service Data Comp Of Svc Cd'].upper()
        reason = row['Service Data Reason Cd'].upper()
        from_dt = pd.to_datetime(row['Service Data From Dt'])
        to_dt = pd.to_datetime(row['Service Data To Dt'])
        if pd.notna(from_dt) and pd.notna(to_dt):
            all_periods.append((from_dt, to_dt))
            all_periods_info.append({'from_dt': from_dt, 'to_dt': to_dt, 'reason': reason, 'branch': branch})
        elif pd.notna(from_dt) and pd.isna(to_dt):
            latest_open_from = from_dt
            has_open_period = True
            all_periods_info.append({'from_dt': from_dt, 'to_dt': AS_OF_DATE, 'reason': reason, 'branch': branch})

    if latest_open_from:
        all_periods.append((latest_open_from, AS_OF_DATE))
        if all_periods_info and all_periods_info[-1]['to_dt'] == AS_OF_DATE:
            all_periods_info[-1]['to_dt'] = AS_OF_DATE

    if not all_periods:
        return {
            'uuid': uuid, 'edipi': edipi, 
            'reported_pebd': reported_pebd.strftime('%Y/%m/%d') if pd.notna(reported_pebd) else None,
            'calculated_pebd': None, 'difference_days': None,
            'total_creditable_days': 0, 'creditable_periods': len(creditable_periods),
            'fraudulent_periods': person_df['is_fraudulent'].sum(),
            'aggregated_periods': 0, 'total_lost_days': 0,
            'net_service_days': 0, 'service_years_months_days': None
        }

    gross_creditable_days, merged_timeline = sum_gross_creditable_days(all_periods)
    total_lost_days = calculate_lost_time_days(all_periods_info, special_reason_codes)
    net_creditable_days = gross_creditable_days - total_lost_days
    net_creditable_days = max(net_creditable_days, 0)

    if has_open_period:
        ref_date = AS_OF_DATE
    else:
        ref_date = merged_timeline[-1][1] if merged_timeline else AS_OF_DATE

    if net_creditable_days > 0:
        calculated_pebd_timestamp = calculate_pebd_dodfmr_method(ref_date, net_creditable_days)
        calculated_pebd = calculated_pebd_timestamp.strftime('%Y/%m/%d') if calculated_pebd_timestamp else None
    else:
        calculated_pebd = None

    if calculated_pebd and net_creditable_days > 0:
        ymd = relativedelta(ref_date, pd.to_datetime(calculated_pebd))
        years_months_days = f"{ymd.years} years, {ymd.months} months, {ymd.days} days"
    else:
        years_months_days = None

    difference_days = (
        (pd.to_datetime(reported_pebd) - pd.to_datetime(calculated_pebd)).days
        if pd.notna(reported_pebd) and pd.notna(calculated_pebd) else None
    )

    return {
        'uuid': uuid,
        'edipi': edipi,
        'reported_pebd': reported_pebd.strftime('%Y/%m/%d') if pd.notna(reported_pebd) else None,
        'calculated_pebd': calculated_pebd,
        'difference_days': difference_days,
        'total_creditable_days': gross_creditable_days,
        'creditable_periods': len(creditable_periods),
        'fraudulent_periods': person_df['is_fraudulent'].sum(),
        'aggregated_periods': person_df.get('aggregated_to_reg_act', pd.Series(False)).sum(),
        'total_lost_days': total_lost_days,
        'net_service_days': int(net_creditable_days),
        'service_years_months_days': years_months_days
    }

class PEBDValidator:
    def __init__(self):
        self.VALID_COMPONENTS = ['REG', 'RES', 'STATE']
        self.SPECIAL_REASON_CODES = ['CNFD', 'EXPECC', 'IHCA', 'IHFA', 'RTFD', 'UA/DES']

    def exclude_fraudulent_periods(self, d188_df, d601_df):
        d188_df = d188_df.copy()
        d188_df['is_fraudulent'] = False
        if d601_df is not None and not d601_df.empty:
            for col in ['Service Data From Dt', 'Service Data To Dt']:
                d188_df[col] = pd.to_datetime(d188_df[col], errors='coerce')
            d601_df['Pay Status From Date'] = pd.to_datetime(d601_df['Pay Status From Date'], errors='coerce')
            d601_df['Pay Status To Date'] = pd.to_datetime(d601_df['Pay Status To Date'], errors='coerce')
            d188_df = d188_df.reset_index().rename(columns={'index': 'd188_idx'})
            merged = d188_df.merge(d601_df, on='Uuid', how='left')
            overlap = (
                (merged['Service Data From Dt'] <= merged['Pay Status To Date']) &
                (merged['Service Data To Dt'] >= merged['Pay Status From Date'])
            )
            fraud_idx = merged.loc[overlap, 'd188_idx'].unique()
            d188_df.loc[d188_df['d188_idx'].isin(fraud_idx), 'is_fraudulent'] = True
            d188_df.drop(columns='d188_idx', inplace=True)
        return d188_df

    def clean_adjust_flag(self, val):
        if pd.isna(val):
            return ''
        sval = str(val).strip().upper()
        return '1' if sval in ['1', '1.0'] else 'A' if sval in ['A', 'A.0'] else sval

    def process_and_validate(self, d188_df, d601_df, parallel=True):
        d188_df = self.exclude_fraudulent_periods(d188_df, d601_df)
        for col in ['Service Data From Dt', 'Service Data To Dt', 'Pay Entry Base Date']:
            d188_df[col] = pd.to_datetime(d188_df[col], errors='coerce')
        if 'Service Data Tm Lost Apply Flg' not in d188_df.columns:
            d188_df['Service Data Tm Lost Apply Flg'] = 'N/A'
        d188_df['Service Data Adjust Flg'] = d188_df['Service Data Adjust Flg'].apply(self.clean_adjust_flag)
        is_not_adj = ~d188_df['Service Data Adjust Flg'].isin(['1', 'A'])
        is_core = d188_df['Service Data Comp Of Svc Cd'].isin(self.VALID_COMPONENTS)
        is_reason = d188_df['Service Data Reason Cd'].isin(['ACT', 'INACT'] + self.SPECIAL_REASON_CODES)
        is_not_tm_lost_flagged = d188_df['Service Data Tm Lost Apply Flg'].astype(str).str.upper() != 'Y'
        is_not_fraud = ~d188_df['is_fraudulent']
        is_not_dep_inact = ~(
            (d188_df['Service Data Comp Of Svc Cd'].str.upper() == 'DEP') &
            (d188_df['Service Data Reason Cd'].str.upper() == 'INACT')
        )
        d188_df['IsCreditable'] = (is_not_adj & is_core & is_reason &
                                   is_not_tm_lost_flagged & is_not_fraud & is_not_dep_inact)
        d188_df['aggregated_to_reg_act'] = False
        self.d188_audit_df = d188_df.copy()
        grouped = list(d188_df.groupby('Uuid', sort=False))
        args = [(uuid, group, None, self.SPECIAL_REASON_CODES) for uuid, group in grouped]
        if parallel:
            with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
                results = list(executor.map(process_person_worker, args))
        else:
            results = [process_person_worker(arg) for arg in args]
        return pd.DataFrame(results)

    def separate_matches_mismatches(self, results_df):
        matches = results_df[
            ((results_df['difference_days'] == 0) |
             ((results_df['reported_pebd'].notna()) &
              (results_df['calculated_pebd'].notna()) &
              (results_df['reported_pebd'] == results_df['calculated_pebd'])))
        ].copy()
        mismatches = results_df[~results_df.index.isin(matches.index)].copy()
        return matches, mismatches

    def display_results(self, matches, mismatches, all_results):
        print_and_capture("=" * 100)
        print_and_capture("PEBD VALIDATION RESULTS (CORRECTED COMPONENT-BASED DEP FILTERING)")
        print_and_capture("=" * 100)
        total = len(all_results)
        print_and_capture(f"Total Records: {total}")
        print_and_capture(f"Matches: {len(matches)} ({len(matches)/total*100:.1f}%)")
        print_and_capture(f"Mismatches: {len(mismatches)} ({len(mismatches)/total*100:.1f}%)\n")
        if not mismatches.empty:
            print_and_capture("Mismatch details:")
            print_and_capture(f" - Max Diff: {mismatches['difference_days'].max()} days")
            print_and_capture(f" - Min Diff: {mismatches['difference_days'].min()} days")
            print_and_capture(f" - Avg Diff: {mismatches['difference_days'].mean():.1f} days")
        all_results['reported_pebd_year'] = pd.to_datetime(all_results['reported_pebd'], errors='coerce').dt.year
        print_and_capture("\nMatch/Mismatch Breakdown by Reported PEBD Year:")
        print_and_capture(f"{'Year':<6} {'Total':<8} {'Matches':<10} {'Mismatches':<12} {'Match %':>8} {'Mismatch %':>11}")
        print_and_capture("-" * 65)
        for year, group in all_results.groupby('reported_pebd_year'):
            total = len(group)
            match_count = len(group[group.index.isin(matches.index)])
            mismatch_count = len(group[group.index.isin(mismatches.index)])
            match_pct = match_count / total * 100 if total else 0
            mismatch_pct = mismatch_count / total * 100 if total else 0
            print_and_capture(f"{year:<6} {total:<8} {match_count:<10} {mismatch_count:<12} {match_pct:>7.1f}% {mismatch_pct:>10.1f}%")
        print_and_capture("")  # Extra newline

def export_matches_by_year_excel_or_csv(df, filename_base):
    try:
        df['reported_pebd_year'] = pd.to_datetime(df['reported_pebd'], errors='coerce').dt.year
        with pd.ExcelWriter(filename_base + ".xlsx") as writer:
            for year, group in df.groupby('reported_pebd_year'):
                group.drop(columns='reported_pebd_year', errors='ignore').to_excel(
                    writer, sheet_name=str(int(year)), index=False
                )
        print_and_capture(f"\nExported matches by PEBD year to Excel: {filename_base}.xlsx")
    except Exception as e:
        print_and_capture(f"Excel export failed: {e}.\nFalling back to per-year CSV files...")
        for year, group in df.groupby('reported_pebd_year'):
            yearf = str(int(year)) if pd.notnull(year) else 'unknown'
            group.drop(columns='reported_pebd_year', errors='ignore').to_csv(f"{filename_base}_{yearf}.csv", index=False)
            print_and_capture(f"Exported matches for year {yearf} to CSV: {filename_base}_{yearf}.csv")

def export_mismatches_by_year_excel_or_csv(df, filename_base):
    try:
        df['reported_pebd_year'] = pd.to_datetime(df['reported_pebd'], errors='coerce').dt.year
        with pd.ExcelWriter(filename_base + ".xlsx") as writer:
            for year, group in df.groupby('reported_pebd_year'):
                group.drop(columns='reported_pebd_year', errors='ignore').to_excel(
                    writer, sheet_name=str(int(year)), index=False
                )
        print_and_capture(f"\nExported mismatches by PEBD year to Excel: {filename_base}.xlsx")
    except Exception as e:
        print_and_capture(f"Excel export failed: {e}.\nFalling back to per-year CSV files...")
        for year, group in df.groupby('reported_pebd_year'):
            yearf = str(int(year)) if pd.notnull(year) else 'unknown'
            group.drop(columns='reported_pebd_year', errors='ignore').to_csv(f"{filename_base}_{yearf}.csv", index=False)
            print_and_capture(f"Exported mismatches for year {yearf} to CSV: {filename_base}_{yearf}.csv")

def main():
    print_and_capture("Starting PEBD Validation with CORRECTED component-based DEP filtering...")
    print_and_capture("FIXED: Now properly checking component (not branch) for DEP/INACT exclusion")
    print_and_capture("Always uses AS_OF_DATE as reference when open periods exist")
    print_and_capture("Matching Statement of Service Report calculation logic exactly")
    print_and_capture("DODFMR compliant with Y/M/D normalization\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    d188_path = os.path.join(base_dir, 'd188_roster.csv')
    d601_path = os.path.join(base_dir, 'd601_pay_status.csv')

    if not os.path.exists(d188_path) or not os.path.exists(d601_path):
        print_and_capture("Input files not found.")
        return

    d188_df = pd.read_csv(d188_path)
    d601_df = pd.read_csv(d601_path)

    validator = PEBDValidator()
    start = time.time()
    results = validator.process_and_validate(d188_df, d601_df, parallel=True)
    end = time.time()

    print_and_capture(f"\nCorrected PEBD validation completed in {end - start:.2f} seconds.")

    matches, mismatches = validator.separate_matches_mismatches(results)
    validator.display_results(matches, mismatches, results)

    output_dir = os.path.join(base_dir, "latest_scripts")

    results.to_csv(os.path.join(output_dir, "pebd_all_results_corrected_final.csv"), index=False)
    matches.to_csv(os.path.join(output_dir, "pebd_matches_corrected_final.csv"), index=False)
    validator.d188_audit_df.to_csv(os.path.join(output_dir, "pebd_audit_log_corrected_final.csv"), index=False)

    export_matches_by_year_excel_or_csv(
        matches,
        filename_base=os.path.join(output_dir, "pebd_matches_by_year_corrected_final")
    )
    export_mismatches_by_year_excel_or_csv(
        mismatches,
        filename_base=os.path.join(output_dir, "pebd_mismatches_by_year_corrected_final")
    )

    print_and_capture("\nExported all results with CORRECTED component-based DEP filtering.")
    print_and_capture("\nOutput files created:")
    print_and_capture("- pebd_all_results_corrected_final.csv")
    print_and_capture("- pebd_matches_corrected_final.csv")
    print_and_capture("- pebd_audit_log_corrected_final.csv")
    print_and_capture("- pebd_matches_by_year_corrected_final(.xlsx or .csv)")
    print_and_capture("- pebd_mismatches_by_year_corrected_final(.xlsx or .csv)")

    summary_path = os.path.join(output_dir, "pebd_summary_report.txt")
    with open(summary_path, "w") as f:
        f.write('\n'.join(summary_lines))
    print_and_capture(f"\nWrote summary report to {summary_path}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
