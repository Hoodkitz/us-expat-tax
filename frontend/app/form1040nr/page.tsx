"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FilingRequirementRequest {
  tax_year: number;
  days_in_us_current_year: number;
  days_in_us_prior_year_1: number;
  days_in_us_prior_year_2: number;
  treaty_country?: string;
  is_student: boolean;
  is_teacher: boolean;
  has_us_sourced_income: boolean;
  gross_income: number;
}

interface FilingRequirementResponse {
  tax_year: number;
  resident_status: string;
  must_file: boolean;
  substantial_presence_days: string;
  passes_substantial_presence_test: boolean;
  treaty_exemption_applies: boolean;
  filing_deadline: string;
  extension_deadline: string;
  reasoning: string;
}

interface IncomeItem {
  description: string;
  income_type: string;
  gross_amount: number;
  us_sourced: boolean;
  treaty_exempt: boolean;
  treaty_article?: string;
  withheld_amount: number;
}

interface IncomeSummaryRequest {
  tax_year: number;
  income_items: IncomeItem[];
  standard_deduction_claimed: boolean;
  itemized_deductions: number;
}

interface IncomeSummaryResponse {
  tax_year: number;
  total_eci: string;
  total_fdap: string;
  total_capital_gains: string;
  total_us_sourced: string;
  total_foreign_sourced: string;
  total_treaty_exempt: string;
  taxable_eci: string;
  taxable_fdap: string;
  standard_deduction: string;
  itemized_deductions: string;
  total_tax_before_credits: string;
  effective_rate: string;
}

interface WithholdingCreditRequest {
  tax_year: number;
  chapter_3_withheld: number;
  chapter_4_withheld: number;
  backup_withheld: number;
  estimated_tax_paid: number;
  prior_year_overpayment: number;
}

interface WithholdingCreditResponse {
  tax_year: number;
  total_chapter_3_credit: string;
  total_chapter_4_credit: string;
  total_backup_credit: string;
  total_estimated_tax: string;
  total_credits: string;
  refundable_amount: string;
  non_refundable_amount: string;
}

interface PenaltyCalculatorRequest {
  tax_year: number;
  filing_deadline: string;
  actual_filing_date?: string;
  tax_owed: number;
  was_extension_filed: boolean;
  reasonable_cause: boolean;
}

interface PenaltyCalculatorResponse {
  tax_year: number;
  days_late: number;
  late_filing_penalty: string;
  late_payment_penalty: string;
  interest_charges: string;
  total_penalties: string;
  minimum_penalty_applies: boolean;
  minimum_penalty_amount: string;
  waived_due_to_reasonable_cause: boolean;
  total_amount_due: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Form1040NRPage() {
  const [taxYear, setTaxYear] = useState<number>(2024);
  const [activeTab, setActiveTab] = useState<string>("filing");

  // Filing Requirement
  const [daysCurrentYear, setDaysCurrentYear] = useState<number>(0);
  const [daysPriorYear1, setDaysPriorYear1] = useState<number>(0);
  const [daysPriorYear2, setDaysPriorYear2] = useState<number>(0);
  const [treatyCountry, setTreatyCountry] = useState<string>("");
  const [isStudent, setIsStudent] = useState<boolean>(false);
  const [isTeacher, setIsTeacher] = useState<boolean>(false);
  const [hasUSIncome, setHasUSIncome] = useState<boolean>(false);
  const [grossIncome, setGrossIncome] = useState<number>(0);
  const [filingResult, setFilingResult] = useState<FilingRequirementResponse | null>(null);

  // Income Summary
  const [incomeItems, setIncomeItems] = useState<IncomeItem[]>([]);
  const [useStdDeduction, setUseStdDeduction] = useState<boolean>(true);
  const [itemizedDed, setItemizedDed] = useState<number>(0);
  const [incomeResult, setIncomeResult] = useState<IncomeSummaryResponse | null>(null);

  // Withholding
  const [ch3, setCh3] = useState<number>(0);
  const [ch4, setCh4] = useState<number>(0);
  const [backup, setBackup] = useState<number>(0);
  const [est, setEst] = useState<number>(0);
  const [overpay, setOverpay] = useState<number>(0);
  const [whtResult, setWhtResult] = useState<WithholdingCreditResponse | null>(null);

  // Penalty
  const [filingDL, setFilingDL] = useState<string>("");
  const [actualFD, setActualFD] = useState<string>("");
  const [taxOwed, setTaxOwed] = useState<number>(0);
  const [ext, setExt] = useState<boolean>(false);
  const [rc, setRc] = useState<boolean>(false);
  const [penResult, setPenResult] = useState<PenaltyCalculatorResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const apiCall = async (endpoint: string, data: any): Promise<any> => {
    const token = localStorage.getItem("token");
    const res = await fetch(`http://localhost:8000/api/v1/form1040nr/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "API error");
    }
    return res.json();
  };

  const checkFiling = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await apiCall("filing-requirement", {
        tax_year: taxYear,
        days_in_us_current_year: daysCurrentYear,
        days_in_us_prior_year_1: daysPriorYear1,
        days_in_us_prior_year_2: daysPriorYear2,
        treaty_country: treatyCountry || undefined,
        is_student: isStudent,
        is_teacher: isTeacher,
        has_us_sourced_income: hasUSIncome,
        gross_income: grossIncome,
      });
      setFilingResult(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calcIncome = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await apiCall("income-summary", {
        tax_year: taxYear,
        income_items: incomeItems,
        standard_deduction_claimed: useStdDeduction,
        itemized_deductions: itemizedDed,
      });
      setIncomeResult(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calcWht = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await apiCall("withholding-credit", {
        tax_year: taxYear,
        chapter_3_withheld: ch3,
        chapter_4_withheld: ch4,
        backup_withheld: backup,
        estimated_tax_paid: est,
        prior_year_overpayment: overpay,
      });
      setWhtResult(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calcPen = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await apiCall("penalty-calculator", {
        tax_year: taxYear,
        filing_deadline: filingDL,
        actual_filing_date: actualFD || undefined,
        tax_owed: taxOwed,
        was_extension_filed: ext,
        reasonable_cause: rc,
      });
      setPenResult(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const addIncome = () => {
    setIncomeItems([
      ...incomeItems,
      {
        description: "",
        income_type: "eci",
        gross_amount: 0,
        us_sourced: true,
        treaty_exempt: false,
        withheld_amount: 0,
      },
    ]);
  };

  const updateIncome = (idx: number, field: string, value: any) => {
    const u = [...incomeItems];
    u[idx] = { ...u[idx], [field]: value };
    setIncomeItems(u);
  };

  const removeIncome = (idx: number) => {
    setIncomeItems(incomeItems.filter((_, i) => i !== idx));
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "2rem", fontWeight: "bold", marginBottom: "0.5rem" }}>
        Form 1040-NR
      </h1>
      <p style={{ marginBottom: "1.5rem", color: "#666" }}>
        Non-Resident Alien Tax Return - Resident-Status-Test, US-Sourced Income, Chapter 3/4 WHT
      </p>

      <div style={{ marginBottom: "1.5rem" }}>
        <label>
          <strong>Steuerjahr:</strong>
          <input
            type="number"
            value={taxYear}
            onChange={(e) => setTaxYear(parseInt(e.target.value) || 2024)}
            style={{ marginLeft: "0.5rem", padding: "0.25rem" }}
          />
        </label>
      </div>

      {error && <div style={{ color: "red", marginBottom: "1rem" }}>{error}</div>}

      <div style={{ borderBottom: "1px solid #ccc", marginBottom: "1rem" }}>
        <button
          onClick={() => setActiveTab("filing")}
          style={{
            padding: "0.5rem 1rem",
            background: activeTab === "filing" ? "#007bff" : "transparent",
            color: activeTab === "filing" ? "#fff" : "#000",
            border: "none",
            cursor: "pointer",
          }}
        >
          Filing Requirement
        </button>
        <button
          onClick={() => setActiveTab("income")}
          style={{
            padding: "0.5rem 1rem",
            background: activeTab === "income" ? "#007bff" : "transparent",
            color: activeTab === "income" ? "#fff" : "#000",
            border: "none",
            cursor: "pointer",
          }}
        >
          Income Summary
        </button>
        <button
          onClick={() => setActiveTab("wht")}
          style={{
            padding: "0.5rem 1rem",
            background: activeTab === "wht" ? "#007bff" : "transparent",
            color: activeTab === "wht" ? "#fff" : "#000",
            border: "none",
            cursor: "pointer",
          }}
        >
          Withholding
        </button>
        <button
          onClick={() => setActiveTab("penalty")}
          style={{
            padding: "0.5rem 1rem",
            background: activeTab === "penalty" ? "#007bff" : "transparent",
            color: activeTab === "penalty" ? "#fff" : "#000",
            border: "none",
            cursor: "pointer",
          }}
        >
          Penalties
        </button>
      </div>

      {activeTab === "filing" && (
        <div>
          <h2>Filing Requirement Test</h2>
          <form onSubmit={checkFiling}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <label>
                Tage in USA (aktuell):
                <input
                  type="number"
                  value={daysCurrentYear}
                  onChange={(e) => setDaysCurrentYear(parseInt(e.target.value) || 0)}
                  style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
                />
              </label>
              <label>
                Tage in USA (Vorjahr 1):
                <input
                  type="number"
                  value={daysPriorYear1}
                  onChange={(e) => setDaysPriorYear1(parseInt(e.target.value) || 0)}
                  style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
                />
              </label>
              <label>
                Tage in USA (Vorjahr 2):
                <input
                  type="number"
                  value={daysPriorYear2}
                  onChange={(e) => setDaysPriorYear2(parseInt(e.target.value) || 0)}
                  style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
                />
              </label>
            </div>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              Treaty Country:
              <input
                type="text"
                value={treatyCountry}
                onChange={(e) => setTreatyCountry(e.target.value)}
                style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
              />
            </label>
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ marginRight: "1rem" }}>
                <input type="checkbox" checked={isStudent} onChange={(e) => setIsStudent(e.target.checked)} />
                Student
              </label>
              <label style={{ marginRight: "1rem" }}>
                <input type="checkbox" checked={isTeacher} onChange={(e) => setIsTeacher(e.target.checked)} />
                Teacher
              </label>
              <label>
                <input type="checkbox" checked={hasUSIncome} onChange={(e) => setHasUSIncome(e.target.checked)} />
                US-Sourced Income
              </label>
            </div>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              Gross Income:
              <input
                type="number"
                value={grossIncome}
                onChange={(e) => setGrossIncome(parseFloat(e.target.value) || 0)}
                style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
              />
            </label>
            <button type="submit" disabled={loading} style={{ padding: "0.5rem 1rem", background: "#007bff", color: "#fff", border: "none", cursor: "pointer" }}>
              {loading ? "Prüfe..." : "Berechnen"}
            </button>
          </form>

          {filingResult && (
            <div style={{ marginTop: "1.5rem", padding: "1rem", background: "#f0f0f0", borderRadius: "4px" }}>
              <h3>Ergebnis</h3>
              <p><strong>Must File:</strong> {filingResult.must_file ? "YES" : "NO"}</p>
              <p><strong>Resident Status:</strong> {filingResult.resident_status}</p>
              <p><strong>SPT Days:</strong> {filingResult.substantial_presence_days}</p>
              <p><strong>Passes SPT:</strong> {filingResult.passes_substantial_presence_test ? "Yes" : "No"}</p>
              <p><strong>Treaty Exemption:</strong> {filingResult.treaty_exemption_applies ? "Yes" : "No"}</p>
              <p><strong>Filing Deadline:</strong> {filingResult.filing_deadline}</p>
              <p><strong>Extension Deadline:</strong> {filingResult.extension_deadline}</p>
              <p><strong>Reasoning:</strong> {filingResult.reasoning}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === "income" && (
        <div>
          <h2>Income Summary (ECI vs FDAP)</h2>
          <form onSubmit={calcIncome}>
            <div style={{ marginBottom: "1rem" }}>
              {incomeItems.map((item, idx) => (
                <div key={idx} style={{ border: "1px solid #ccc", padding: "0.5rem", marginBottom: "0.5rem" }}>
                  <input
                    placeholder="Description"
                    value={item.description}
                    onChange={(e) => updateIncome(idx, "description", e.target.value)}
                    style={{ width: "100%", padding: "0.25rem", marginBottom: "0.25rem" }}
                  />
                  <select
                    value={item.income_type}
                    onChange={(e) => updateIncome(idx, "income_type", e.target.value)}
                    style={{ width: "100%", padding: "0.25rem", marginBottom: "0.25rem" }}
                  >
                    <option value="eci">ECI</option>
                    <option value="fdap">FDAP</option>
                    <option value="capital_gains">Capital Gains</option>
                    <option value="rental">Rental</option>
                    <option value="other">Other</option>
                  </select>
                  <input
                    type="number"
                    placeholder="Amount"
                    value={item.gross_amount}
                    onChange={(e) => updateIncome(idx, "gross_amount", parseFloat(e.target.value) || 0)}
                    style={{ width: "100%", padding: "0.25rem", marginBottom: "0.25rem" }}
                  />
                  <input
                    type="number"
                    placeholder="Withheld"
                    value={item.withheld_amount}
                    onChange={(e) => updateIncome(idx, "withheld_amount", parseFloat(e.target.value) || 0)}
                    style={{ width: "100%", padding: "0.25rem", marginBottom: "0.25rem" }}
                  />
                  <label style={{ marginRight: "1rem" }}>
                    <input type="checkbox" checked={item.us_sourced} onChange={(e) => updateIncome(idx, "us_sourced", e.target.checked)} />
                    US-Sourced
                  </label>
                  <label style={{ marginRight: "1rem" }}>
                    <input type="checkbox" checked={item.treaty_exempt} onChange={(e) => updateIncome(idx, "treaty_exempt", e.target.checked)} />
                    Treaty Exempt
                  </label>
                  <button type="button" onClick={() => removeIncome(idx)} style={{ padding: "0.25rem 0.5rem", background: "red", color: "#fff", border: "none" }}>
                    Remove
                  </button>
                </div>
              ))}
              <button type="button" onClick={addIncome} style={{ padding: "0.5rem 1rem", background: "#28a745", color: "#fff", border: "none", cursor: "pointer" }}>
                + Add Income Item
              </button>
            </div>

            <label style={{ marginBottom: "1rem", display: "block" }}>
              <input type="checkbox" checked={useStdDeduction} onChange={(e) => setUseStdDeduction(e.target.checked)} />
              Standard Deduction ($14,600)
            </label>

            {!useStdDeduction && (
              <label style={{ marginBottom: "1rem", display: "block" }}>
                Itemized Deductions:
                <input
                  type="number"
                  value={itemizedDed}
                  onChange={(e) => setItemizedDed(parseFloat(e.target.value) || 0)}
                  style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
                />
              </label>
            )}

            <button type="submit" disabled={loading || incomeItems.length === 0} style={{ padding: "0.5rem 1rem", background: "#007bff", color: "#fff", border: "none", cursor: "pointer" }}>
              {loading ? "Berechne..." : "Berechnen"}
            </button>
          </form>

          {incomeResult && (
            <div style={{ marginTop: "1.5rem", padding: "1rem", background: "#f0f0f0", borderRadius: "4px" }}>
              <h3>Ergebnis</h3>
              <p><strong>Total ECI:</strong> ${incomeResult.total_eci}</p>
              <p><strong>Total FDAP:</strong> ${incomeResult.total_fdap}</p>
              <p><strong>Capital Gains:</strong> ${incomeResult.total_capital_gains}</p>
              <p><strong>US-Sourced:</strong> ${incomeResult.total_us_sourced}</p>
              <p><strong>Foreign-Sourced:</strong> ${incomeResult.total_foreign_sourced}</p>
              <p><strong>Treaty Exempt:</strong> ${incomeResult.total_treaty_exempt}</p>
              <p><strong>Taxable ECI:</strong> ${incomeResult.taxable_eci}</p>
              <p><strong>Taxable FDAP:</strong> ${incomeResult.taxable_fdap}</p>
              <p><strong>Total Tax:</strong> ${incomeResult.total_tax_before_credits}</p>
              <p><strong>Effective Rate:</strong> {incomeResult.effective_rate}%</p>
            </div>
          )}
        </div>
      )}

      {activeTab === "wht" && (
        <div>
          <h2>Withholding Tax Credits</h2>
          <form onSubmit={calcWht}>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              Chapter 3 Withheld (30%):
              <input
                type="number"
                value={ch3}
                onChange={(e) => setCh3(parseFloat(e.target.value) || 0)}
                style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
              />
            </label>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              Chapter 4 Withheld (FATCA):
              <input
                type="number"
                value={ch4}
                onChange={(e) => setCh4(parseFloat(e.target.value) || 0)}
                style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
              />
            </label>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              Backup Withholding:
              <input
                type="number"
                value={backup}
                onChange={(e) => setBackup(parseFloat(e.target.value) || 0)}
                style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
              />
            </label>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              Estimated Tax Paid:
              <input
                type="number"
                value={est}
                onChange={(e) => setEst(parseFloat(e.target.value) || 0)}
                style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
              />
            </label>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              Prior Year Overpayment:
              <input
                type="number"
                value={overpay}
                onChange={(e) => setOverpay(parseFloat(e.target.value) || 0)}
                style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
              />
            </label>
            <button type="submit" disabled={loading} style={{ padding: "0.5rem 1rem", background: "#007bff", color: "#fff", border: "none", cursor: "pointer" }}>
              {loading ? "Berechne..." : "Berechnen"}
            </button>
          </form>

          {whtResult && (
            <div style={{ marginTop: "1.5rem", padding: "1rem", background: "#f0f0f0", borderRadius: "4px" }}>
              <h3>Credits</h3>
              <p><strong>Chapter 3:</strong> ${whtResult.total_chapter_3_credit}</p>
              <p><strong>Chapter 4:</strong> ${whtResult.total_chapter_4_credit}</p>
              <p><strong>Backup:</strong> ${whtResult.total_backup_credit}</p>
              <p><strong>Estimated:</strong> ${whtResult.total_estimated_tax}</p>
              <p><strong>Total Credits:</strong> ${whtResult.total_credits}</p>
              <p><strong>Refundable:</strong> ${whtResult.refundable_amount}</p>
              <p><strong>Non-Refundable:</strong> ${whtResult.non_refundable_amount}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === "penalty" && (
        <div>
          <h2>Penalty Calculator (§6072)</h2>
          <form onSubmit={calcPen}>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              Filing Deadline:
              <input
                type="date"
                value={filingDL}
                onChange={(e) => setFilingDL(e.target.value)}
                style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
              />
            </label>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              Actual Filing Date:
              <input
                type="date"
                value={actualFD}
                onChange={(e) => setActualFD(e.target.value)}
                style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
              />
            </label>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              Tax Owed:
              <input
                type="number"
                value={taxOwed}
                onChange={(e) => setTaxOwed(parseFloat(e.target.value) || 0)}
                style={{ width: "100%", padding: "0.25rem", marginTop: "0.25rem" }}
              />
            </label>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              <input type="checkbox" checked={ext} onChange={(e) => setExt(e.target.checked)} />
              Extension Filed
            </label>
            <label style={{ marginBottom: "1rem", display: "block" }}>
              <input type="checkbox" checked={rc} onChange={(e) => setRc(e.target.checked)} />
              Reasonable Cause
            </label>
            <button type="submit" disabled={loading || !filingDL} style={{ padding: "0.5rem 1rem", background: "#007bff", color: "#fff", border: "none", cursor: "pointer" }}>
              {loading ? "Berechne..." : "Berechnen"}
            </button>
          </form>

          {penResult && (
            <div style={{ marginTop: "1.5rem", padding: "1rem", background: "#f0f0f0", borderRadius: "4px" }}>
              <h3>Penalty Breakdown</h3>
              <p><strong>Days Late:</strong> {penResult.days_late}</p>
              <p><strong>Late Filing Penalty:</strong> ${penResult.late_filing_penalty}</p>
              <p><strong>Late Payment Penalty:</strong> ${penResult.late_payment_penalty}</p>
              <p><strong>Interest:</strong> ${penResult.interest_charges}</p>
              <p><strong>Total Penalties:</strong> ${penResult.total_penalties}</p>
              <p><strong>Total Due:</strong> ${penResult.total_amount_due}</p>
              {penResult.minimum_penalty_applies && <p><strong>Minimum Penalty:</strong> ${penResult.minimum_penalty_amount}</p>}
              {penResult.waived_due_to_reasonable_cause && <p style={{ color: "green" }}>Penalties waived due to reasonable cause</p>}
            </div>
          )}
        </div>
      )}

      <div style={{ marginTop: "2rem", textAlign: "center" }}>
        <Link href="/" style={{ color: "#007bff" }}>
          ← Zurück zum Dashboard
        </Link>
      </div>
    </div>
  );
}
