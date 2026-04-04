# MISSO-09 — Statement of Service Calculator

A command-line tool that computes creditable military service and validates the
Pay Entry Base Date (PEBD) per **DODFMR Volume 7A, Chapter 1**.

Built for use by administrative clerks, S1 personnel, and developers maintaining
military pay record systems.

---

## What It Does

- Accepts one or more service periods as input (branch, component, reason, dates)
- Calculates **gross creditable service** using the DODFMR 30-day month method
- Tracks **lost time** (UA/DES, CNFD, IHCA, etc.) with type, from/to dates, and
  actual calendar day counts
- Computes **net creditable service** (gross minus lost time)
- Derives the **Calculated PEBD** from today's date minus net creditable days
- Compares Calculated PEBD against the Recorded PEBD from the system (e.g. MCTFS)
- Outputs a formatted **Statement of Service Report** as a `.txt` file

---

## How to Build and Run

### Requirements
- [Go](https://golang.org/dl/) 1.18 or later

### Build
```bash
go build -o misso09 main.go
```

### Run
```bash
./misso09
```

The tool runs interactively in the terminal. Follow the prompts to enter the
EDIPI, reported PEBD, and service periods. Type `DONE` when finished entering
periods to generate the report.

Output file: `statement_of_service_report.txt` (created in the current directory)

---

## Input Format Guide

### Dates
All dates must be entered as `YYYY/MM/DD`.

| Example       | Meaning                  |
|---------------|--------------------------|
| `2026/01/11`  | January 11, 2026         |
| `PRESENT`     | Ongoing / current period |
| `DONE`        | Finish entering periods  |

> **Note:** Days of 31 are automatically normalized to 30 per DODFMR rules.
> February dates are also normalized to 30.

### Service Period Flow
```
FROM DATE  →  TO DATE  →  TIME LOST?  →  BRANCH  →  COMP  →  REASON
```
- Enter `PRESENT` at **TO DATE** if the period is still active
- Enter `DONE` at the **FROM DATE** prompt when all periods have been entered
- If there is lost time, you will be prompted for one or more lost time blocks

### Lost Time Block Flow
```
LOST REASON  →  LOST FROM DATE  →  LOST TO DATE  →  (add another?)
```
- Multiple lost time blocks can be added per service period
- Days are calculated automatically using actual calendar days (not DODFMR 30-day method)

---

## Valid Codes Reference

### BRANCH
| Code   | Branch                        |
|--------|-------------------------------|
| `USMC` | United States Marine Corps    |
| `USA`  | United States Army            |
| `USN`  | United States Navy            |
| `USAF` | United States Air Force       |
| `USSF` | United States Space Force     |
| `USCG` | United States Coast Guard     |
| `NG`   | National Guard                |

### COMP (Component)
| Code    | Meaning       |
|---------|---------------|
| `REG`   | Regular       |
| `RES`   | Reserve       |
| `STATE` | State         |
| `DEP`   | Delayed Entry Program (not creditable — excluded from calculations) |

### REASON (Service Reason)
| Code     | Meaning                              |
|----------|--------------------------------------|
| `ACT`    | Active Duty                          |
| `INACT`  | Inactive Duty                        |
| `IHCA`   | In Hands of Civil Authorities (creditable)          |
| `CNFD`   | Confined                          |
| `EXPECC` | Expired ECC                       |
| `UA/DES` | Unauthorized Absence / Desertion     |

### LOST REASON (Lost Time Type)
| Code     | Meaning                          |
|----------|----------------------------------|
| `UA/DES` | Unauthorized Absence / Desertion |
| `CNFD`   | Confined                         |
| `EXPECC` | Excess Leave / ECC               |
| `IHFA`   | Inhands Forg Authorities (non-creditable)  |
| `IHCA`   | Inhands Civilian Authorities (Not creditable)      |

---

## Example Walkthrough

### Scenario
A Marine enlisted on **2026/01/11**, had **4 days UA** from Jan 12–15,
then continued service through present. Reported PEBD in MCTFS is `2026/01/11`.

### Input Session
```
Enter EDIPI: 1184879022
Enter Reported PEBD (YYYY/MM/DD): 2026/01/11
Recorded: 2026/01/11

Enter service periods.
  - For TO DATE: type 'PRESENT' if the period is ongoing.
  - Type 'DONE' at the FROM DATE prompt when finished entering all periods.

FROM DATE (YYYY/MM/DD) or 'DONE' to finish: 2026/01/11
TO DATE   (YYYY/MM/DD) or 'PRESENT': PRESENT
Is there TIME LOST for this period? (yes/no): yes

  Lost Time Block #1
  LOST REASON (UA/DES, CNFD, EXPECC, IHFA, IHCA): UA/DES
  LOST FROM DATE (YYYY/MM/DD): 2026/01/12
  LOST TO DATE   (YYYY/MM/DD): 2026/01/15
  -> 4 calendar day(s) of lost time recorded.
  Add another lost time block for this period? (yes/no): no

BRANCH (USMC, NG, USAF, USN, USCG, USA, USSF): USMC
COMP (REG, RES, STATE, DEP): REG
REASON (ACT, IHCA, CNFD, EXPECC, INACT, UA/DES): ACT
-> Period added. Lost time for this period: 4 day(s).

FROM DATE (YYYY/MM/DD) or 'DONE' to finish: DONE
```

### Sample Report Output
```
                          STATEMENT OF SERVICE REPORT
             Per DODFMR Chapter 1 - Creditable Service Computation
================================================================================
EDIPI: 1184879022   Reported PEBD: 2026/01/11   AFADBD: See MCTFS TBIR
================================================================================
Branch    Component Reason   From (YYYY/MM/DD) To (YYYY/MM/DD)  TmLost
--------------------------------------------------------------------------------
USMC      REG       ACT      2026/01/11        PRESENT          4 days
USMC      REG       UA/DES   2026/01/12        2026/01/15       4 days
--------------------------------------------------------------------------------

Complete Service Timeline (DODFMR Method - Creditable Periods):
Start Date         End Date             Gross        Lost         Net
--------------------------------------------------------------------------------
2026/01/11         PRESENT              59 days      4 days       55 days

================================================================================
SERVICE SUMMARY AND PEBD VALIDATION:
--------------------------------------------------------------------------------
Gross Creditable Service: 59 days
Total Lost Time:          4 days
Net Creditable Service:   55 days (0y 1m 25d)

PEBD COMPARISON:
Recorded PEBD (System):   2026/01/11
Calculated PEBD (DODFMR): 2026/01/15
Validation Status:        4 days later than calculated PEBD
================================================================================
```

> In this example the 4-day discrepancy is expected — the lost time pushes the
> Calculated PEBD forward by exactly the number of days lost.

---

## Notes for Developers

- **DODFMR 30-day method** is used for all creditable service segment calculations
  (`computeSegmentDays30`). Days 31 and all February days normalize to 30.
- **Open periods** (PRESENT) do not add the `+1` inclusive day since today is not
  yet complete. Closed periods do add `+1`.
- **Lost time** uses actual calendar days (`computeLostDaysCalendar`), not the
  30-day method.
- **PEBD formula:** `today - (netCreditableDays - 1)`
- Periods with `COMP = DEP` are excluded from all calculations as non-creditable.
- The binary (`misso09`) is excluded from version control via `.gitignore`.
  Rebuild with `go build -o misso09 main.go`.