"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FilingRequirementRequest {
  category_of_filer: "1" | "2" | "3" | "4" | "5";
  ownership_percentage: number;
  is_officer_or_director: boolean;
  tax_year: number;
}

interface FilingRequirementResult {
  must_file: boolean;
  categories_triggered: string[];
  reasons: string[];
  penalty_if_not_filed: string;
  due_date: string;
}

interface SubpartFRequest {
  passive_income_usd: number;
  sales_income_usd: number;
  services_income_usd: number;
  foreign_base_company_income_usd: number;
  total_cfc_income_usd: number;
  tax_year: number;
}

interface SubpartFResult {
  subpart_f_total_usd: number;
  inclusion_required: boolean;
  high_tax_exception_may_apply: boolean;
  effective_foreign_rate_threshold_pct: number;
  recommendations: string[];
}

interface GiltiRequest {
  net_tested_income_usd: number;
  qualified_business_asset_investment_usd: number;
  deemed_tangible_income_return_pct: number;
  ownership_pct: number;
}

interface GiltiResult {
  gilti_inclusion_usd: number;
  dtir_usd: number;
  net_cfc_tested_income_usd: number;
  deduction_80pct_corporations: number;
  explanation: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token") ?? localStorage.getItem("access_token");
}

function fmtUSD(val: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(val);
}

// ---------------------------------------------------------------------------
// Shared styles (dark theme)
// ---------------------------------------------------------------------------

const S = {
  input:
    "w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500 text-sm",
  label: "block text-sm font-medium text-gray-300 mb-1",
  labelSm: "block text-xs text-gray-500 mb-1",
  btn: "px-6 py-2.5 rounded-md bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold transition-colors text-sm",
  card: "bg-gray-800 rounded-lg p-4 border border-gray-700",
  errorBox:
    "p-4 rounded-md bg-red-900/40 border border-red-700 text-red-300 text-sm",
};

// ---------------------------------------------------------------------------
// Tab 1: Filing Requirement
// ---------------------------------------------------------------------------

function FilingRequirementTab() {
  const [form, setForm] = useState<FilingRequirementRequest>({
    category_of_filer: "4",
    ownership_percentage: 0,
    is_officer_or_director: false,
    tax_year: new Date().getFullYear() - 1,
  });
  const [result, setResult] = useState<FilingRequirementResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      const resp = await fetch(`${API_BASE}/api/v1/form5471/filing-requirement`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(form),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail ?? `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const categoryLabels: Record<string, string> = {
    "1": "Category 1 — U.S. shareholder of a CFC (pre-TCJA / §965)",
    "2": "Category 2 — Officer/Director when 10%+ stock acquired",
    "3": "Category 3 — Acquired/disposed stock to reach ≥10% in a CFC",
    "4": "Category 4 — Control (>50% by vote or value)",
    "5": "Category 5 — U.S. shareholder owning ≥10% of a CFC",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <p style={{ color: "#9ca3af", fontSize: "0.875rem" }}>
        Determine whether you must file{" "}
        <strong style={{ color: "#fff" }}>Form 5471</strong> based on your
        category and ownership in a foreign corporation.
      </p>

      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}
      >
        {/* Category of filer */}
        <div>
          <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#d1d5db", marginBottom: "0.25rem" }}>
            Category of Filer
          </label>
          <select
            value={form.category_of_filer}
            onChange={(e) =>
              setForm({
                ...form,
                category_of_filer: e.target.value as FilingRequirementRequest["category_of_filer"],
              })
            }
            style={{
              width: "100%",
              padding: "0.5rem 0.75rem",
              borderRadius: "0.375rem",
              background: "#374151",
              border: "1px solid #4b5563",
              color: "#fff",
              fontSize: "0.875rem",
            }}
          >
            {(["1", "2", "3", "4", "5"] as const).map((c) => (
              <option key={c} value={c}>
                {categoryLabels[c]}
              </option>
            ))}
          </select>
        </div>

        {/* Ownership + Tax Year */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#d1d5db", marginBottom: "0.25rem" }}>
              Ownership Percentage (%)
            </label>
            <input
              type="number"
              min={0}
              max={100}
              step="0.1"
              value={form.ownership_percentage}
              onChange={(e) =>
                setForm({ ...form, ownership_percentage: parseFloat(e.target.value) || 0 })
              }
              style={{
                width: "100%",
                padding: "0.5rem 0.75rem",
                borderRadius: "0.375rem",
                background: "#374151",
                border: "1px solid #4b5563",
                color: "#fff",
                fontSize: "0.875rem",
              }}
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#d1d5db", marginBottom: "0.25rem" }}>
              Tax Year
            </label>
            <input
              type="number"
              min={2000}
              max={2099}
              value={form.tax_year}
              onChange={(e) =>
                setForm({ ...form, tax_year: parseInt(e.target.value) || 2024 })
              }
              style={{
                width: "100%",
                padding: "0.5rem 0.75rem",
                borderRadius: "0.375rem",
                background: "#374151",
                border: "1px solid #4b5563",
                color: "#fff",
                fontSize: "0.875rem",
              }}
            />
          </div>
        </div>

        {/* Officer/Director */}
        <label style={{ display: "flex", alignItems: "center", gap: "0.75rem", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={form.is_officer_or_director}
            onChange={(e) =>
              setForm({ ...form, is_officer_or_director: e.target.checked })
            }
            style={{ width: "1rem", height: "1rem" }}
          />
          <span style={{ fontSize: "0.875rem", color: "#d1d5db" }}>
            I am (or was) an officer or director of the foreign corporation
          </span>
        </label>

        <button type="submit" disabled={loading} style={{
          padding: "0.625rem 1.5rem",
          borderRadius: "0.375rem",
          background: loading ? "#374151" : "#2563eb",
          color: "#fff",
          fontWeight: 600,
          fontSize: "0.875rem",
          border: "none",
          cursor: loading ? "not-allowed" : "pointer",
          alignSelf: "flex-start",
        }}>
          {loading ? "Checking…" : "Check Filing Requirement"}
        </button>
      </form>

      {error && (
        <div style={{ padding: "1rem", borderRadius: "0.375rem", background: "rgba(127,29,29,0.4)", border: "1px solid #b91c1c", color: "#fca5a5", fontSize: "0.875rem" }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Must-file badge */}
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            padding: "1rem",
            borderRadius: "0.5rem",
            border: result.must_file ? "1px solid #b91c1c" : "1px solid #15803d",
            background: result.must_file ? "rgba(127,29,29,0.3)" : "rgba(20,83,45,0.3)",
          }}>
            <span style={{ fontSize: "1.25rem", fontWeight: 700, color: result.must_file ? "#f87171" : "#4ade80" }}>
              {result.must_file ? "⚠ Must File Form 5471" : "✓ No Filing Required"}
            </span>
          </div>

          {/* Categories triggered */}
          {result.categories_triggered.length > 0 && (
            <div style={{ background: "#1f2937", borderRadius: "0.5rem", padding: "1rem", border: "1px solid #374151" }}>
              <p style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "#6b7280", marginBottom: "0.5rem" }}>
                Categories Triggered
              </p>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {result.categories_triggered.map((c) => (
                  <span key={c} style={{ padding: "0.25rem 0.75rem", borderRadius: "9999px", background: "rgba(37,99,235,0.3)", border: "1px solid #2563eb", color: "#93c5fd", fontSize: "0.875rem", fontWeight: 600 }}>
                    Category {c}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Reasons */}
          <div style={{ background: "#1f2937", borderRadius: "0.5rem", padding: "1rem", border: "1px solid #374151" }}>
            <p style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "#6b7280", marginBottom: "0.5rem" }}>
              Analysis
            </p>
            <ul style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
              {result.reasons.map((r, i) => (
                <li key={i} style={{ fontSize: "0.875rem", color: "#d1d5db", display: "flex", gap: "0.5rem" }}>
                  <span style={{ color: "#60a5fa", marginTop: "0.125rem" }}>•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Penalty warning */}
          {result.must_file && (
            <div style={{ background: "rgba(120,53,15,0.2)", border: "1px solid #b45309", borderRadius: "0.5rem", padding: "1rem" }}>
              <p style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "#d97706", marginBottom: "0.5rem" }}>
                Penalty Warning
              </p>
              <p style={{ fontSize: "0.875rem", color: "#fde68a" }}>{result.penalty_if_not_filed}</p>
              <p style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: "0.5rem" }}>
                <strong>Due date:</strong> {result.due_date}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 2: Subpart F Income
// ---------------------------------------------------------------------------

function SubpartFTab() {
  const [form, setForm] = useState<SubpartFRequest>({
    passive_income_usd: 0,
    sales_income_usd: 0,
    services_income_usd: 0,
    foreign_base_company_income_usd: 0,
    total_cfc_income_usd: 0,
    tax_year: new Date().getFullYear() - 1,
  });
  const [result, setResult] = useState<SubpartFResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      const resp = await fetch(`${API_BASE}/api/v1/form5471/subpart-f-income`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(form),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail ?? `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const numField = (label: string, key: keyof SubpartFRequest) => (
    <div>
      <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#d1d5db", marginBottom: "0.25rem" }}>
        {label}
      </label>
      <input
        type="number"
        min={0}
        step="0.01"
        value={form[key] as number}
        onChange={(e) =>
          setForm({ ...form, [key]: parseFloat(e.target.value) || 0 })
        }
        style={{
          width: "100%",
          padding: "0.5rem 0.75rem",
          borderRadius: "0.375rem",
          background: "#374151",
          border: "1px solid #4b5563",
          color: "#fff",
          fontSize: "0.875rem",
        }}
      />
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <p style={{ color: "#9ca3af", fontSize: "0.875rem" }}>
        Enter the CFC&apos;s income components to calculate{" "}
        <strong style={{ color: "#fff" }}>Subpart F income</strong> that must be
        included in your gross income under IRC §951.
      </p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          {numField("Passive Income (USD)", "passive_income_usd")}
          {numField("Foreign Base Company Income (USD)", "foreign_base_company_income_usd")}
          {numField("Sales Income (USD)", "sales_income_usd")}
          {numField("Services Income (USD)", "services_income_usd")}
          {numField("Total CFC Gross Income (USD)", "total_cfc_income_usd")}
          <div>
            <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#d1d5db", marginBottom: "0.25rem" }}>
              Tax Year
            </label>
            <input
              type="number"
              min={2000}
              max={2099}
              value={form.tax_year}
              onChange={(e) =>
                setForm({ ...form, tax_year: parseInt(e.target.value) || 2024 })
              }
              style={{
                width: "100%",
                padding: "0.5rem 0.75rem",
                borderRadius: "0.375rem",
                background: "#374151",
                border: "1px solid #4b5563",
                color: "#fff",
                fontSize: "0.875rem",
              }}
            />
          </div>
        </div>

        <button type="submit" disabled={loading} style={{
          padding: "0.625rem 1.5rem",
          borderRadius: "0.375rem",
          background: loading ? "#374151" : "#2563eb",
          color: "#fff",
          fontWeight: 600,
          fontSize: "0.875rem",
          border: "none",
          cursor: loading ? "not-allowed" : "pointer",
          alignSelf: "flex-start",
        }}>
          {loading ? "Calculating…" : "Calculate Subpart F"}
        </button>
      </form>

      {error && (
        <div style={{ padding: "1rem", borderRadius: "0.375rem", background: "rgba(127,29,29,0.4)", border: "1px solid #b91c1c", color: "#fca5a5", fontSize: "0.875rem" }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Inclusion status */}
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1rem",
            borderRadius: "0.5rem",
            border: result.inclusion_required ? "1px solid #b91c1c" : "1px solid #15803d",
            background: result.inclusion_required ? "rgba(127,29,29,0.3)" : "rgba(20,83,45,0.3)",
          }}>
            <span style={{ fontSize: "1.125rem", fontWeight: 700, color: result.inclusion_required ? "#f87171" : "#4ade80" }}>
              {result.inclusion_required ? "⚠ Subpart F Inclusion Required" : "✓ No Subpart F Inclusion"}
            </span>
            <span style={{ fontSize: "1.5rem", fontWeight: 800, color: "#fff" }}>
              {fmtUSD(result.subpart_f_total_usd)}
            </span>
          </div>

          {/* High-tax exception */}
          {result.high_tax_exception_may_apply && (
            <div style={{ background: "rgba(30,58,138,0.3)", border: "1px solid #1d4ed8", borderRadius: "0.5rem", padding: "1rem" }}>
              <p style={{ fontSize: "0.875rem", color: "#93c5fd" }}>
                <strong>High-Tax Exception may apply</strong> — if the CFC&apos;s effective foreign tax
                rate is ≥{result.effective_foreign_rate_threshold_pct}%, certain Subpart F income
                may be excluded under Treas. Reg. §1.954-1(d).
              </p>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div style={{ background: "#1f2937", borderRadius: "0.5rem", padding: "1rem", border: "1px solid #374151" }}>
              <p style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "#6b7280", marginBottom: "0.5rem" }}>
                Recommendations
              </p>
              <ul style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
                {result.recommendations.map((r, i) => (
                  <li key={i} style={{ fontSize: "0.875rem", color: "#d1d5db", display: "flex", gap: "0.5rem" }}>
                    <span style={{ color: "#34d399", marginTop: "0.125rem" }}>→</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 3: GILTI Calculator
// ---------------------------------------------------------------------------

function GiltiTab() {
  const [form, setForm] = useState<GiltiRequest>({
    net_tested_income_usd: 0,
    qualified_business_asset_investment_usd: 0,
    deemed_tangible_income_return_pct: 10.0,
    ownership_pct: 100.0,
  });
  const [result, setResult] = useState<GiltiResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      const resp = await fetch(`${API_BASE}/api/v1/form5471/gilti-calculator`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(form),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail ?? `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const numField = (label: string, key: keyof GiltiRequest, step = "0.01", max?: number) => (
    <div>
      <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#d1d5db", marginBottom: "0.25rem" }}>
        {label}
      </label>
      <input
        type="number"
        min={0}
        max={max}
        step={step}
        value={form[key] as number}
        onChange={(e) =>
          setForm({ ...form, [key]: parseFloat(e.target.value) || 0 })
        }
        style={{
          width: "100%",
          padding: "0.5rem 0.75rem",
          borderRadius: "0.375rem",
          background: "#374151",
          border: "1px solid #4b5563",
          color: "#fff",
          fontSize: "0.875rem",
        }}
      />
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <p style={{ color: "#9ca3af", fontSize: "0.875rem" }}>
        Calculate your{" "}
        <strong style={{ color: "#fff" }}>GILTI inclusion</strong> under IRC
        §951A. GILTI = Net CFC Tested Income − Deemed Tangible Income Return
        (QBAI × 10%).
      </p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          {numField("Net CFC Tested Income (USD)", "net_tested_income_usd")}
          {numField("Qualified Business Asset Investment — QBAI (USD)", "qualified_business_asset_investment_usd")}
          {numField("Deemed Tangible Income Return (%)", "deemed_tangible_income_return_pct", "0.1", 100)}
          {numField("Your Ownership Percentage (%)", "ownership_pct", "0.1", 100)}
        </div>

        <button type="submit" disabled={loading} style={{
          padding: "0.625rem 1.5rem",
          borderRadius: "0.375rem",
          background: loading ? "#374151" : "#2563eb",
          color: "#fff",
          fontWeight: 600,
          fontSize: "0.875rem",
          border: "none",
          cursor: loading ? "not-allowed" : "pointer",
          alignSelf: "flex-start",
        }}>
          {loading ? "Calculating…" : "Calculate GILTI"}
        </button>
      </form>

      {error && (
        <div style={{ padding: "1rem", borderRadius: "0.375rem", background: "rgba(127,29,29,0.4)", border: "1px solid #b91c1c", color: "#fca5a5", fontSize: "0.875rem" }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Results grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            {[
              { label: "Net CFC Tested Income (pro-rated)", value: fmtUSD(result.net_cfc_tested_income_usd), color: "#fff" },
              { label: "Deemed Tangible Income Return (DTIR)", value: fmtUSD(result.dtir_usd), color: "#fbbf24" },
              { label: "GILTI Inclusion Amount", value: fmtUSD(result.gilti_inclusion_usd), color: result.gilti_inclusion_usd > 0 ? "#f87171" : "#4ade80" },
              { label: "§250 Deduction (C-Corps, 50%)", value: fmtUSD(result.deduction_80pct_corporations), color: "#34d399" },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: "#1f2937", borderRadius: "0.5rem", padding: "1rem", border: "1px solid #374151", textAlign: "center" }}>
                <p style={{ fontSize: "0.75rem", color: "#6b7280", marginBottom: "0.375rem" }}>{label}</p>
                <p style={{ fontSize: "1.375rem", fontWeight: 800, color }}>{value}</p>
              </div>
            ))}
          </div>

          {/* GILTI status */}
          <div style={{
            padding: "0.875rem 1rem",
            borderRadius: "0.5rem",
            border: result.gilti_inclusion_usd > 0 ? "1px solid #b91c1c" : "1px solid #15803d",
            background: result.gilti_inclusion_usd > 0 ? "rgba(127,29,29,0.3)" : "rgba(20,83,45,0.3)",
          }}>
            <span style={{ fontWeight: 700, color: result.gilti_inclusion_usd > 0 ? "#f87171" : "#4ade80" }}>
              {result.gilti_inclusion_usd > 0
                ? `⚠ GILTI inclusion of ${fmtUSD(result.gilti_inclusion_usd)} must be included in gross income.`
                : "✓ No GILTI inclusion — DTIR covers or exceeds tested income."}
            </span>
          </div>

          {/* Explanation */}
          <div style={{ background: "#1f2937", borderRadius: "0.5rem", padding: "1rem", border: "1px solid #374151" }}>
            <p style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "#6b7280", marginBottom: "0.5rem" }}>
              Calculation Detail
            </p>
            <p style={{ fontSize: "0.875rem", color: "#d1d5db", lineHeight: "1.6" }}>{result.explanation}</p>
          </div>

          {result.gilti_inclusion_usd > 0 && (
            <div style={{ background: "rgba(30,58,138,0.2)", border: "1px solid #1d4ed8", borderRadius: "0.5rem", padding: "1rem" }}>
              <p style={{ fontSize: "0.875rem", color: "#93c5fd" }}>
                <strong>Note for individuals:</strong> The §250 deduction is only available to C-corporations.
                Individuals may make a §962 election to be taxed as a corporation on GILTI income,
                which then allows the §250 deduction and access to foreign tax credits.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type Tab = "filing" | "subpartf" | "gilti";

export default function Form5471Page() {
  const [activeTab, setActiveTab] = useState<Tab>("filing");

  const tabs: { id: Tab; label: string }[] = [
    { id: "filing", label: "Filing Requirement" },
    { id: "subpartf", label: "Subpart F Income" },
    { id: "gilti", label: "GILTI Calculator" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#111827", color: "#fff" }}>
      {/* Header */}
      <header style={{ background: "#1f2937", borderBottom: "1px solid #374151", padding: "1rem 1.5rem" }}>
        <div style={{ maxWidth: "56rem", margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>
              Form 5471 — CFC Reporting Assistant
            </h1>
            <p style={{ fontSize: "0.875rem", color: "#9ca3af", marginTop: "0.25rem", marginBottom: 0 }}>
              Information Return of U.S. Persons With Respect to Certain Foreign Corporations (IRC §6038)
            </p>
          </div>
          <Link
            href="/dashboard"
            style={{ fontSize: "0.875rem", color: "#60a5fa", textDecoration: "none" }}
          >
            ← Dashboard
          </Link>
        </div>
      </header>

      <main style={{ maxWidth: "56rem", margin: "0 auto", padding: "2rem 1.5rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {/* Info banner */}
        <div style={{ background: "rgba(30,58,138,0.2)", border: "1px solid #1d4ed8", borderRadius: "0.5rem", padding: "1rem", fontSize: "0.875rem", color: "#bfdbfe" }}>
          <strong>Form 5471</strong> is required for U.S. persons with interests in Controlled Foreign
          Corporations (CFCs). Penalties start at <strong>$10,000</strong> per CFC per year.
          This tool covers Subpart F income (IRC §951) and GILTI (IRC §951A, added by TCJA 2017).
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", borderBottom: "1px solid #374151" }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "0.75rem 1.25rem",
                fontSize: "0.875rem",
                fontWeight: 500,
                border: "none",
                borderBottom: activeTab === tab.id ? "2px solid #3b82f6" : "2px solid transparent",
                background: "transparent",
                color: activeTab === tab.id ? "#60a5fa" : "#9ca3af",
                cursor: "pointer",
                marginBottom: "-1px",
                transition: "color 0.15s",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div style={{ background: "#1f2937", borderRadius: "0.75rem", border: "1px solid #374151", padding: "1.5rem" }}>
          {activeTab === "filing" && <FilingRequirementTab />}
          {activeTab === "subpartf" && <SubpartFTab />}
          {activeTab === "gilti" && <GiltiTab />}
        </div>

        {/* Disclaimer */}
        <p style={{ fontSize: "0.75rem", color: "#4b5563", textAlign: "center" }}>
          For informational purposes only. Consult a qualified US tax professional for advice.
          IRS reference:{" "}
          <a
            href="https://www.irs.gov/forms-pubs/about-form-5471"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "#2563eb" }}
          >
            irs.gov/forms-pubs/about-form-5471
          </a>
        </p>
      </main>
    </div>
  );
}
