package main

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"time"
)

// LostBlock represents a single block of lost time within a service period.
type LostBlock struct {
	Reason   string
	FromDate string
	ToDate   string
	Days     int // actual calendar days
}

type InputData struct {
	FROMDATE   string
	TODATE     string // "" or "PRESENT" or specific YYYY/MM/DD
	BRANCH     string
	COMP       string
	REASON     string
	LostBlocks []LostBlock
	TIMELOST   int // sum of all LostBlock.Days
}

type Summary struct {
	EDIPI           string
	ReportedPEBD    string
	CalculatedPEBD  string
	GrossCreditable int
	TotalLost       int
	NetCreditable   int
	Years           int
	Months          int
	Days            int
	AsOfDate        string
	GeneratedOn     string
}

var (
	validBranches = map[string]bool{
		"USMC": true, "NG": true, "USAF": true, "USN": true,
		"USCG": true, "USA": true, "USSF": true,
	}
	validComp = map[string]bool{
		"REG": true, "RES": true, "STATE": true, "DEP": true,
	}
	validReasons = map[string]bool{
		"ACT":   true, "IHCA": true, "CNFD": true, "EXPECC": true,
		"INACT": true, "UA/DES": true,
	}
	validLostReasons = map[string]bool{
		"UA/DES": true, "CNFD": true, "EXPECC": true,
		"IHFA":   true, "IHCA": true,
	}
)

func isCreditable(p InputData) bool {
	return p.COMP != "DEP" && validReasons[p.REASON]
}

func adjustDay(d, m, y int) int {
	if d == 31 {
		return 30
	}
	if m == 2 {
		return 30
	}
	return d
}

func formatDateForDisplay(dateStr string) string {
	if dateStr == "PRESENT" {
		return "PRESENT"
	}
	if dateStr == "" {
		return "N/A"
	}
	parts := strings.Split(dateStr, "/")
	if len(parts) != 3 {
		return dateStr
	}
	y, _ := strconv.Atoi(parts[0])
	m, _ := strconv.Atoi(parts[1])
	d, _ := strconv.Atoi(parts[2])
	d = adjustDay(d, m, y)
	return fmt.Sprintf("%04d/%02d/%02d", y, m, d)
}

// computeSegmentDays30 calculates creditable days per DODFMR Chapter 1.
// Closed periods (fixed end date): +1 inclusive.
// Open periods (PRESENT / today not yet complete): no +1.
func computeSegmentDays30(start, end string) int {
	isOpen := end == "" || strings.ToUpper(end) == "PRESENT"
	endDate := end
	if isOpen {
		endDate = time.Now().Format("2006/01/02")
	}

	sParts := strings.Split(start, "/")
	eParts := strings.Split(endDate, "/")
	if len(sParts) != 3 || len(eParts) != 3 {
		return 0
	}

	ys, _ := strconv.Atoi(sParts[0])
	ms, _ := strconv.Atoi(sParts[1])
	ds, _ := strconv.Atoi(sParts[2])
	ye, _ := strconv.Atoi(eParts[0])
	me, _ := strconv.Atoi(eParts[1])
	de, _ := strconv.Atoi(eParts[2])

	ds = adjustDay(ds, ms, ys)
	de = adjustDay(de, me, ye)

	days := de - ds
	months := me - ms
	years := ye - ys
	if days < 0 {
		days += 30
		months--
	}
	if months < 0 {
		months += 12
		years--
	}

	inclusive := 1
	if isOpen {
		inclusive = 0
	}
	return max(years*360+months*30+days+inclusive, 0)
}

// computeLostDaysCalendar calculates actual calendar days for a lost time block.
func computeLostDaysCalendar(start, end string) int {
	t1 := parseDate(start)
	t2 := parseDate(end)
	if t1.IsZero() || t2.IsZero() {
		return 0
	}
	diff := int(t2.Sub(t1).Hours()/24) + 1 // inclusive
	if diff < 0 {
		return 0
	}
	return diff
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func ymdFromDays30(days int) (int, int, int) {
	y := days / 360
	rem := days % 360
	m := rem / 30
	d := rem % 30
	return y, m, d
}

func parseDate(s string) time.Time {
	normalized := strings.ReplaceAll(s, "/", "-")
	t, err := time.Parse("2006-01-02", normalized)
	if err != nil {
		log.Printf("Failed to parse date %q: %v", s, err)
		return time.Time{}
	}
	return t
}

func computeTotals(periods []InputData) (gross, lost, net int) {
	for _, p := range periods {
		if !isCreditable(p) {
			continue
		}
		seg := computeSegmentDays30(p.FROMDATE, p.TODATE)
		periodNet := seg - p.TIMELOST
		if periodNet < 0 {
			periodNet = 0
		}
		gross += seg
		lost += p.TIMELOST
		net += periodNet
	}
	return
}

func readDate(scanner *bufio.Scanner, prompt string) string {
	for {
		fmt.Print(prompt)
		if !scanner.Scan() {
			log.Fatal("Input ended unexpectedly")
		}
		s := strings.TrimSpace(scanner.Text())
		upper := strings.ToUpper(s)

		if upper == "PRESENT" {
			return "PRESENT"
		}
		if upper == "DONE" {
			return "DONE"
		}
		if s == "" {
			fmt.Println("-> Please enter a date, 'PRESENT', or 'DONE' to finish.\n")
			continue
		}

		parts := strings.Split(s, "/")
		if len(parts) != 3 {
			fmt.Println("-> Invalid format. Use YYYY/MM/DD, 'PRESENT', or 'DONE'.\n")
			continue
		}

		y, errY := strconv.Atoi(parts[0])
		m, errM := strconv.Atoi(parts[1])
		d, errD := strconv.Atoi(parts[2])

		if errY != nil || errM != nil || errD != nil ||
			m < 1 || m > 12 ||
			d < 1 || d > 31 {
			fmt.Println("-> Invalid date. Use YYYY/MM/DD (e.g., 2026/01/11), 'PRESENT', or 'DONE'.\n")
			continue
		}

		_ = y
		return s
	}
}

func askYesNo(scanner *bufio.Scanner, prompt string) bool {
	for {
		fmt.Print(prompt)
		if !scanner.Scan() {
			return false
		}
		ans := strings.ToLower(strings.TrimSpace(scanner.Text()))
		if ans == "yes" || ans == "y" {
			return true
		}
		if ans == "no" || ans == "n" {
			return false
		}
		fmt.Println("-> Please answer yes or no.\n")
	}
}

func askChoice(scanner *bufio.Scanner, label string, options []string) string {
	for {
		fmt.Printf("%s (%s): ", label, strings.Join(options, ", "))
		if !scanner.Scan() {
			return ""
		}
		choice := strings.ToUpper(strings.TrimSpace(scanner.Text()))
		for _, opt := range options {
			if choice == opt {
				return choice
			}
		}
		fmt.Println("-> Invalid choice. Try again.\n")
	}
}

func keys(m map[string]bool) []string {
	var list []string
	for k := range m {
		list = append(list, k)
	}
	return list
}

// collectLostBlocks prompts the user to enter one or more lost time blocks.
func collectLostBlocks(scanner *bufio.Scanner) []LostBlock {
	var blocks []LostBlock
	blockNum := 1
	for {
		fmt.Printf("\n  Lost Time Block #%d\n", blockNum)
		reason := askChoice(scanner, "  LOST REASON", keys(validLostReasons))
		from := readDate(scanner, "  LOST FROM DATE (YYYY/MM/DD): ")
		to := readDate(scanner, "  LOST TO DATE   (YYYY/MM/DD): ")
		days := computeLostDaysCalendar(from, to)
		fmt.Printf("  -> %d calendar day(s) of lost time recorded.\n", days)

		blocks = append(blocks, LostBlock{
			Reason:   reason,
			FromDate: from,
			ToDate:   to,
			Days:     days,
		})
		blockNum++

		if !askYesNo(scanner, "  Add another lost time block for this period? (yes/no): ") {
			break
		}
	}
	return blocks
}

func sumLostBlocks(blocks []LostBlock) int {
	total := 0
	for _, b := range blocks {
		total += b.Days
	}
	return total
}

func generateSummary(edipi, reportedPEBD string, periods []InputData) Summary {
	gross, totalLost, net := computeTotals(periods)
	y, m, d := ymdFromDays30(net)

	// PEBD = today - (net days) where net is in DODFMR 30-day months format
	today := time.Now()
	
	// Convert net days to years/months/days and subtract properly
	years, months, days := y, m, d
	
	// Subtract years, months, and days from today
	calcTime := today.AddDate(-years, -months, -days)
	calcPEBD := calcTime.Format("2006/01/02")

	now := time.Now()
	return Summary{
		EDIPI:           edipi,
		ReportedPEBD:    reportedPEBD,
		CalculatedPEBD:  calcPEBD,
		GrossCreditable: gross,
		TotalLost:       totalLost,
		NetCreditable:   net,
		Years:           y,
		Months:          m,
		Days:            d,
		AsOfDate:        now.Format("2006/01/02"),
		GeneratedOn:     now.Format("2006-01-02 15:04:05"),
	}
}

func writeReport(summary Summary, periods []InputData) error {
	f, err := os.Create("statement_of_service_report.txt")
	if err != nil {
		return err
	}
	defer f.Close()

	// Consistent column format used for every row in the main table
	// Branch(6) Comp(9) Reason(8) From(16) To(16) TmLost
	const rowFmt = "%-6s %-9s %-8s %-16s %-16s %s"

	var lines []string
	lines = append(lines,
		"                          STATEMENT OF SERVICE REPORT                           ",
		"             Per DODFMR Chapter 1 - Creditable Service Computation              ",
		strings.Repeat("=", 80),
		fmt.Sprintf("EDIPI: %s   Reported PEBD: %s   AFADBD: See MCTFS TBIR",
			summary.EDIPI, summary.ReportedPEBD),
		strings.Repeat("=", 80),
		fmt.Sprintf(rowFmt, "Branch", "Component", "Reason", "From (YYYY/MM/DD)", "To (YYYY/MM/DD)", "TmLost"),
		strings.Repeat("-", 80),
	)

	for _, p := range periods {
		if !isCreditable(p) {
			continue
		}
		to := formatDateForDisplay(p.TODATE)
		lostStr := "N/A"
		if p.TIMELOST > 0 {
			lostStr = fmt.Sprintf("%d days", p.TIMELOST)
		}

		// Main service period row
		lines = append(lines, fmt.Sprintf(rowFmt,
			p.BRANCH, p.COMP, p.REASON,
			formatDateForDisplay(p.FROMDATE), to, lostStr))

		// Each lost time block as its own full aligned row
		// Branch and Comp carry over from parent period; Reason = lost reason
		for _, lb := range p.LostBlocks {
			lines = append(lines, fmt.Sprintf(rowFmt,
				p.BRANCH, p.COMP, lb.Reason,
				formatDateForDisplay(lb.FromDate),
				formatDateForDisplay(lb.ToDate),
				fmt.Sprintf("%d days", lb.Days)))
		}
	}

	lines = append(lines,
		strings.Repeat("-", 80),
		"",
		"Complete Service Timeline (DODFMR Method - Creditable Periods):",
		fmt.Sprintf("%-18s %-20s %-12s %-12s %-12s", "Start Date", "End Date", "Gross", "Lost", "Net"),
		strings.Repeat("-", 80),
	)

	for _, p := range periods {
		if !isCreditable(p) {
			continue
		}
		gross := computeSegmentDays30(p.FROMDATE, p.TODATE)
		net := gross - p.TIMELOST
		if net < 0 {
			net = 0
		}
		to := formatDateForDisplay(p.TODATE)
		lines = append(lines, fmt.Sprintf("%-18s %-20s %-12s %-12s %-12s",
			formatDateForDisplay(p.FROMDATE), to,
			fmt.Sprintf("%d days", gross),
			fmt.Sprintf("%d days", p.TIMELOST),
			fmt.Sprintf("%d days", net),
		))
	}

	lines = append(lines,
		"",
		strings.Repeat("=", 80),
		"SERVICE SUMMARY AND PEBD VALIDATION:",
		strings.Repeat("-", 80),
		fmt.Sprintf("Gross Creditable Service: %d days", summary.GrossCreditable),
		fmt.Sprintf("Total Lost Time:          %d days", summary.TotalLost),
		fmt.Sprintf("Net Creditable Service:   %d days (%dy %dm %dd)",
			summary.NetCreditable, summary.Years, summary.Months, summary.Days),
		"",
		"PEBD COMPARISON:",
		fmt.Sprintf("Recorded PEBD (System):   %s", summary.ReportedPEBD),
		fmt.Sprintf("Calculated PEBD (DODFMR): %s", summary.CalculatedPEBD),
	)

	diff := dateDiff(summary.ReportedPEBD, summary.CalculatedPEBD)
	diffStr := "MATCH"
	if diff != 0 {
		direction := "later than"
		if diff < 0 {
			direction = "earlier than"
		}
		abs := diff
		if abs < 0 {
			abs = -abs
		}
		diffStr = fmt.Sprintf("%d days %s calculated PEBD", abs, direction)
	}
	lines = append(lines, fmt.Sprintf("Validation Status:        %s", diffStr))

	lines = append(lines,
		strings.Repeat("=", 80),
		fmt.Sprintf("Generated on: %s", summary.GeneratedOn),
		"Report computed per DODFMR Chapter 1 regulations",
		"PEBD calculation uses DODFMR Y/M/D normalization method",
		"Lost time computed using actual calendar days",
	)

	_, err = f.WriteString(strings.Join(lines, "\n") + "\n")
	return err
}

func dateDiff(d1, d2 string) int {
	t1 := parseDate(d1)
	t2 := parseDate(d2)
	if t1.IsZero() || t2.IsZero() {
		return 0
	}
	return int(t1.Sub(t2).Hours() / 24)
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)

	fmt.Print("Enter EDIPI: ")
	scanner.Scan()
	edipi := strings.TrimSpace(scanner.Text())

	reportedPEBD := readDate(scanner, "Enter Reported PEBD (YYYY/MM/DD): ")
	fmt.Printf("Recorded: %s\n\n", reportedPEBD)

	var periods []InputData
	fmt.Println("Enter service periods.")
	fmt.Println("  - For TO DATE: type 'PRESENT' if the period is ongoing.")
	fmt.Println("  - Type 'DONE' at the FROM DATE prompt when finished entering all periods.\n")

	for {
		from := readDate(scanner, "FROM DATE (YYYY/MM/DD) or 'DONE' to finish: ")
		if strings.ToUpper(from) == "DONE" {
			break
		}

		to := readDate(scanner, "TO DATE   (YYYY/MM/DD) or 'PRESENT': ")

		var lostBlocks []LostBlock
		if askYesNo(scanner, "Is there TIME LOST for this period? (yes/no): ") {
			lostBlocks = collectLostBlocks(scanner)
		}

		branch := askChoice(scanner, "BRANCH", keys(validBranches))
		comp := askChoice(scanner, "COMP", keys(validComp))
		reason := askChoice(scanner, "REASON", keys(validReasons))

		totalLost := sumLostBlocks(lostBlocks)

		periods = append(periods, InputData{
			FROMDATE:   from,
			TODATE:     to,
			BRANCH:     branch,
			COMP:       comp,
			REASON:     reason,
			LostBlocks: lostBlocks,
			TIMELOST:   totalLost,
		})
		fmt.Printf("-> Period added. Lost time for this period: %d day(s).\n\n", totalLost)
	}

	if len(periods) == 0 {
		fmt.Println("No periods entered. Exiting.")
		return
	}

	summary := generateSummary(edipi, reportedPEBD, periods)

	err := writeReport(summary, periods)
	if err != nil {
		log.Fatalf("Failed to write report: %v", err)
	}

	fmt.Println("\nReport created: statement_of_service_report.txt")
	fmt.Printf("As of: %s | Calculated PEBD: %s\n", summary.AsOfDate, summary.CalculatedPEBD)
	fmt.Println("Done.")
}
