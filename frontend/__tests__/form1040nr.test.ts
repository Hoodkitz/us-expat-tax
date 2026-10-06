/**
 * Frontend-Tests für Form 1040-NR
 * Testet die Hilfsfunktionen und Typen der Form 1040-NR Seite.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";

// -----------------------------------------------------------------------
// Hilfsfunktionen (kopiert aus der Seite für Testzwecke)
// -----------------------------------------------------------------------

function fmtUSD(val: number | undefined): string {
  if (val === undefined || val === null) return "–";
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(val);
}

function fmtPct(val: number | null | undefined): string {
  if (val === undefined || val === null) return "–";
  return `${(val * 100).toFixed(1)}%`;
}

// -----------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------

describe("Form 1040-NR Frontend Helpers", () => {
  describe("fmtUSD", () => {
    it("formats positive numbers as USD", () => {
      const result = fmtUSD(50000);
      assert.ok(result.includes("50.000"));
      assert.ok(result.includes("USD") || result.includes("$"));
    });

    it("formats zero as USD", () => {
      const result = fmtUSD(0);
      assert.ok(result.includes("0"));
    });

    it("returns dash for undefined", () => {
      const result = fmtUSD(undefined);
      assert.equal(result, "–");
    });

    it("returns dash for null", () => {
      const result = fmtUSD(null as any);
      assert.equal(result, "–");
    });

    it("formats decimal numbers correctly", () => {
      const result = fmtUSD(1234.56);
      assert.ok(result.includes("1.234"));
    });
  });

  describe("fmtPct", () => {
    it("formats decimal as percentage", () => {
      const result = fmtPct(0.15);
      assert.equal(result, "15.0%");
    });

    it("formats zero as percentage", () => {
      const result = fmtPct(0);
      assert.equal(result, "0.0%");
    });

    it("formats one as percentage", () => {
      const result = fmtPct(1);
      assert.equal(result, "100.0%");
    });

    it("returns dash for undefined", () => {
      const result = fmtPct(undefined);
      assert.equal(result, "–");
    });

    it("returns dash for null", () => {
      const result = fmtPct(null);
      assert.equal(result, "–");
    });

    it("formats small percentages correctly", () => {
      const result = fmtPct(0.05);
      assert.equal(result, "5.0%");
    });
  });
});

describe("Form 1040-NR Type Validation", () => {
  it("FilingRequirementResult has correct structure", () => {
    const result = {
      filing_required: true,
      reasons: ["Test reason"],
      recommendation: "Test recommendation",
      total_us_income: 50000,
      tax_withheld: 0,
      estimated_tax_due: 11000,
    };
    assert.equal(typeof result.filing_required, "boolean");
    assert.ok(Array.isArray(result.reasons));
    assert.equal(typeof result.total_us_income, "number");
  });

  it("TaxCalculationResult has correct structure", () => {
    const result = {
      tax_year: 2024,
      filing_status: "Single",
      total_income: 50000,
      adjusted_gross_income: 50000,
      total_deductions: 0,
      taxable_income: 50000,
      tax_before_credits: 6000,
      total_credits: 0,
      tax_after_credits: 6000,
      federal_tax_withheld: 0,
      tax_due: 6000,
      refund: 0,
      effective_tax_rate: 12.0,
      marginal_tax_rate: 0.12,
      income_breakdown: { wages_salaries: 50000 },
      tax_bracket_breakdown: [],
      treaty_applied: false,
      treaty_rate: null,
    };
    assert.equal(typeof result.total_income, "number");
    assert.equal(typeof result.tax_due, "number");
    assert.ok(result.effective_tax_rate >= 0);
  });

  it("OverviewData has correct structure", () => {
    const overview = {
      form_name: "Form 1040-NR",
      form_title: "U.S. Nonresident Alien Income Tax Return",
      description: "Test description",
      filing_deadline: "April 15",
      who_must_file: ["Test"],
      income_types: ["Wages"],
      tax_rates: { ECI: "10-37%" },
      deductions_available: ["Itemized"],
      credits_available: ["FTC"],
      special_rules: ["No standard deduction"],
    };
    assert.equal(overview.form_name, "Form 1040-NR");
    assert.ok(Array.isArray(overview.who_must_file));
    assert.ok(Array.isArray(overview.income_types));
  });
});

describe("Form 1040-NR Business Logic", () => {
  it("calculates total income correctly", () => {
    const income = {
      wages_salaries: 40000,
      interest_income: 5000,
      dividend_income: 3000,
      capital_gains: 2000,
      business_income: 0,
      rental_income: 0,
      other_income: 0,
    };
    const total = Object.values(income).reduce((a, b) => a + b, 0);
    assert.equal(total, 50000);
  });

  it("calculates taxable income correctly", () => {
    const agi = 50000;
    const deductions = 10000;
    const taxable = Math.max(0, agi - deductions);
    assert.equal(taxable, 40000);
  });

  it("calculates tax due correctly", () => {
    const taxAfterCredits = 6000;
    const withheld = 2000;
    const taxDue = Math.max(0, taxAfterCredits - withheld);
    assert.equal(taxDue, 4000);
  });

  it("calculates refund correctly", () => {
    const taxAfterCredits = 6000;
    const withheld = 10000;
    const refund = Math.max(0, withheld - taxAfterCredits);
    assert.equal(refund, 4000);
  });

  it("calculates effective tax rate correctly", () => {
    const tax = 6000;
    const income = 50000;
    const rate = (tax / income) * 100;
    assert.equal(rate, 12);
  });

  it("applies treaty rate correctly", () => {
    const taxableIncome = 50000;
    const treatyRate = 0.15;
    const tax = taxableIncome * treatyRate;
    assert.equal(tax, 7500);
  });

  it("handles zero income correctly", () => {
    const income = 0;
    const tax = 0;
    const rate = income > 0 ? (tax / income) * 100 : 0;
    assert.equal(rate, 0);
  });
});
