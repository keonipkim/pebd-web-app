// PEBD Calculator - Client-Side Implementation

// Date utility functions
function calculateInclusiveDays(startDate, endDate) {
    const d1 = new Date(startDate);
    const d2 = new Date(endDate);

    // Handle special end-of-month cases
    if (d2.getDate() === 31) {
        d2.setDate(30);
    } else if (d2.getMonth() === 1 && d2.getDate() === 29) {
        // Check if it's a leap year
        const isLeapYear = (d2.getFullYear() % 4 === 0 &&
                           (d2.getFullYear() % 100 !== 0 || d2.getFullYear() % 400 === 0));
        if (!isLeapYear) {
            d2.setDate(28);
        }
    }

    const diffTime = Math.abs(d2 - d1);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays + 1; // Include both start and end dates
}

function subtractDaysFromDate(dateStr, daysToSubtract) {
    const date = new Date(dateStr);
    date.setDate(date.getDate() - daysToSubtract);
    return date.toISOString().split('T')[0];
}

function addDaysToDate(dateStr, daysToAdd) {
    const date = new Date(dateStr);
    date.setDate(date.getDate() + daysToAdd);
    return date.toISOString().split('T')[0];
}

function totalDaysToYMD(totalDays) {
    const years = Math.floor(totalDays / 360);
    const remainingDays = totalDays % 360;
    const months = Math.floor(remainingDays / 30);
    const days = remainingDays % 30;

    if (months >= 12) {
        years += Math.floor(months / 12);
        months %= 12;
    }

    return `${years.toString().padStart(2, '0')} Years, ${months.toString().padStart(2, '0')} Months, ${days.toString().padStart(2, '0')} Days`;
}

// Service period calculation
function calculateServicePeriod(startDate, endDate, lostTime = 0, adjustFlag = false) {
    if (!startDate || !endDate) {
        throw new Error("Start and end dates are required");
    }

    const totalDays = calculateInclusiveDays(startDate, endDate);
    let netDays = totalDays - lostTime;

    if (adjustFlag) {
        netDays = Math.floor(netDays * 0.5); // Example adjustment
    }

    return { totalDays, netDays };
}

// Main PEBD calculation function
function calculatePEBD(doeaf, initialActiveDuty, eos, reentryDate, memberType,
                      servicePeriods, lostTimeData, adjustFlag, constructiveYears = 0, branch = "USMC") {
    // Validate inputs
    if (!initialActiveDuty || !eos) {
        throw new Error("Invalid date inputs");
    }

    // Calculate days for each period type
    let totalActiveDays = 0;
    let totalInactiveDays = 0;
    let totalLostDays = 0;
    let depDays = 0;

    // Process service periods (simplified for client-side)
    // In a full implementation, this would process the actual data from the UI

    // Calculate constructive service
    const constructiveDays = constructiveYears * 360;

    // Calculate net service days
    const netServiceDays = totalActiveDays + totalInactiveDays + totalLostDays + constructiveDays;

    // Calculate PEBD
    let calculatedPEBD;
    if (reentryDate) {
        calculatedPEBD = subtractDaysFromDate(reentryDate, netServiceDays);
    } else {
        calculatedPEBD = new Date().toISOString().split('T')[0]; // Current date if no reentry
    }

    return {
        pebd: calculatedPEBD,
        totalActiveDays: totalActiveDays,
        totalInactiveDays: totalInactiveDays,
        totalLostDays: totalLostDays,
        depDays: depDays,
        constructiveDays: constructiveDays,
        netServiceDays: netServiceDays,
        lostTime: lostTimeData,
        memberType: memberType,
        branch: branch,
        adjustFlag: adjustFlag
    };
}

// Validation functions
function validateDateInput(dateValue) {
    if (!dateValue) return false;
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    return dateRegex.test(dateValue);
}

function validatePositiveNumber(value) {
    return value >= 0;
}

// Export functions for use in web app
window.PEBDCalculator = {
    calculateInclusiveDays,
    subtractDaysFromDate,
    addDaysToDate,
    totalDaysToYMD,
    calculateServicePeriod,
    calculatePEBD,
    validateDateInput,
    validatePositiveNumber
};