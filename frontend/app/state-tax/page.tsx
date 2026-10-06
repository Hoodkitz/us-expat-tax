"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiMe,
  apiStateTaxObligations,
  apiStateTaxStates,
  apiStateTaxDomicileAnalysis,
  StateTaxObligationsRequest,
  StateTaxObligationsResult,
  StateTaxStateInfo,
  StateTaxStatesResult,
  StateTaxDomicileRequest,
  StateTaxDomicileResult,
} from "@/lib/api";

const US_STATES: { code: string; name: string }[] = [
  { code: "AK", name: "Alaska" }, { code: "AL", name: "Alabama" },
  { code: "AR", name: "Arkansas" }, { code: "AZ", name: "Arizona" },
  { code: "CA", name: "California" }, { code: "CO", name: "Colorado" },
  { code: "CT", name: "Connecticut" }, { code: "DE", name: "Delaware" },
  { code: "FL", name: "Florida" }, { code: "GA", name: "Georgia" },
  { code: "HI", name: "Hawaii" }, { code: "IA", name: "Iowa" },
  { code: "ID", name: "Idaho" }, { code: "IL", name: "Illinois" },
  { code: "IN", name: "Indiana" }, { code: "KS", name: "Kansas" },
  { code: "KY", name: "Kentucky" }, { code: "LA", name: "Louisiana" },
  { code: "MA", name: "Massachusetts" }, { code: "MD", name: "Maryland" },
  { code: "ME", name: "Maine" }, { code: "MI", name: "Michigan" },
  { code: "MN", name: "Minnesota" }, { code: "MO", name: "Missouri" },
  { code: "MS", name: "Mississippi" }, { code: "MT", name: "Montana" },
  { code: "NC", name: "North Carolina" }, { code: "ND", name: "North Dakota" },
  { code: "NE", name: "Nebraska" }, { code: "NH", name: "New Hampshire" },
  { code: "NJ", name: "New Jersey" }, { code: "NM", name: "New Mexico" },
  { code: "NV", name: "Nevada" }, { code: "NY", name: "New York" },
  { code: "OH", name: "Ohio" }, { code: "OK", name: "Oklahoma" },
  { code: "OR", name: "Oregon" }, { code: "PA", name: "Pennsylvania" },
  { code: "RI", name: "Rhode Island" }, { code: "SC", name: "South Carolina" },
  { code: "SD", name: "South Dakota" }, { code: "TN", name: "Tennessee" },
  { code: "TX", name: "Texas" }, { code: "UT", name: "Utah" },
  { code: "VA", name: "Virginia" }, { code: "VT", name: "Vermont" },
  { code: "WA", name: "Washington" }, { code: "WI", name: "Wisconsin" },
  { code: "WV", name: "West Virginia" }, { code: "WY", name: "Wyoming" },
];

type Tab = "obligations" | "domicile" | "states";

export default function StateTaxPage() {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("obligations");

  // Obligations form
  const [state, setState] = useState("CA");
  const [daysInState, setDaysInState] = useState("30");
  const [domicileState, setDomicileState] = useState("TX");
  const [incomeSource, setIncomeSource] = useState<"employment" | "self_employment" | "investment" | "rental">("employment");
  const [movedAbroadYear, setMovedAbroadYear] = useState("2023");
  const [maintainedHome, setMaintainedHome] = useState(false);
  const [driverLicenseState, setDriverLicenseState] = useState("");
  const [voterRegState, setVoterRegState] = useState("");

  // Domicile form
  const [domOrigState, setDomOrigState] = useState("CA");
  const [yearsAbroad, setYearsAbroad] = useState("2");
  const [domMaintainedHome, setDomMaintainedHome] = useState(false);
  const [voterReg, setVoterReg] = useState(false);
  const [driverLic, setDriverLic] = useState(false);
  const [bankAccounts, setBankAccounts] = useState(false);
  const [familyInState, setFamilyInState] = useState(false);
  const [returnDays, setReturnDays] = useState("10");
  const [intentToReturn, setIntentToReturn] = useState(false);
  const [businessTies, setBusinessTies] = useState(false);
  const [vehicleReg, setVehicleReg] = useState(false);

  // Results
  const [obligationsResult, setObligationsResult] = useState<StateTaxObligationsResult | null>(null);
  const [domicileResult, setDomicileResult] = useState<StateTaxDomicileResult | null>(null);
  const [statesData, setStatesData] = useState<StateTaxStateInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) { router.replace("/auth/login"); return; }
    apiMe().then(() => setAuthReady(true)).catch(() => {
      localStorage.removeItem("jwt_token");
      router.replace("/auth/login");
    });
  }, [router]);

  useEffect(() => {
    if (authReady && activeTab === "states" && statesData.length === 0) {
      apiStateTaxStates().then((d: StateTaxStatesResult) => setStatesData(d.states)).catch(() => {});
    }
  }, [authReady, activeTab, statesData.length]);

  async function handleObligationsSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setObligationsResult(null);
    setLoading(true);
    try {
      const payload: StateTaxObligationsRequest = {
        state,
        days_in_state: parseInt(daysInState),
        domicile_state: domicileState,
        income_source: incomeSource,
        moved_abroad_year: parseInt(movedAbroadYear),
        maintained_home: maintainedHome,
        driver_license_state: driverLicenseState || undefined,
        voter_reg_state: voterRegState || undefined,
      };
      const data = await apiStateTaxObligations(payload);
      setObligationsResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function handleDomicileSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setDomicileResult(null);
    setLoading(true);
    try {
      const payload: StateTaxDomicileRequest = {
        original_state: domOrigState,
        years_abroad: parseFloat(yearsAbroad),
        maintained_home: domMaintainedHome,
        voter_registered_in_state: voterReg,
        driver_license_in_state: driverLic,
        bank_accounts_in_state: bankAccounts,
        family_in_state: familyInState,
        returned_to_state_days_per_year: parseInt(returnDays),
        intent_to_return: intentToReturn,
        business_ties_in_state: businessTies,
        vehicle_registered_in_state: vehicleReg,
      };
      const data = await apiStateTaxDomicileAnalysis(payload);
      setDomicileResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  if (!authReady) return null;

  const nexusColors: Record<string, string> = {
    domicile: "bg-red-50 border-red-200 text-red-800",
    statutory_resident: "bg-orange-50 border-orange-200 text-orange-800",
    nonresident: "bg-yellow-50 border-yellow-200 text-yellow-800",
    none: "bg-green-50 border-green-200 text-green-800",
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <span className="font-extrabold text-brand-800 text-lg">🇺🇸 US Expat Tax</span>
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">Dashboard</Link>
          <Link href="/fbar" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">FBAR</Link>
          <Link href="/fbar-penalties" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">FBAR Penalties</Link>
          <Link href="/totalization" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">Totalization</Link>
          <Link href="/feie" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">FEIE</Link>
          <Link href="/history" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">History</Link>
          <Link href="/state-tax" className="rounded-lg bg-brand-700 px-4 py-1.5 text-sm text-white font-semibold">State Tax</Link>
          <Link href="/auth/logout" className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-100 transition-colors">Logout</Link>
        </div>
      </nav>

      <main className="mx-auto max-w-4xl px-4 py-10 space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">🏛️ State Tax Filing Obligations</h1>
          <p className="text-sm text-gray-500 mt-1">
            Understand your US state income tax filing requirements as an expat — all 50 states, domicile rules, safe harbor days.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-200">
          {(["obligations", "domicile", "states"] as Tab[]).map(tab => (
            <button
              key={tab}
              onClick={() => { setActiveTab(tab); setError(null); }}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors capitalize ${
                activeTab === tab
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab === "obligations" ? "Filing Obligations" : tab === "domicile" ? "Domicile Analysis" : "All 50 States"}
            </button>
          ))}
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
        )}

        {/* OBLIGATIONS TAB */}
        {activeTab === "obligations" && (
          <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
            <form onSubmit={handleObligationsSubmit} className="space-y-5">
              <div className="grid gap-5 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">State to Analyze <span className="text-red-500">*</span></label>
                  <select value={state} onChange={e => setState(e.target.value)} required
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none">
                    {US_STATES.map(s => <option key={s.code} value={s.code}>{s.name} ({s.code})</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Days in State (this year) <span className="text-red-500">*</span></label>
                  <input type="number" min={0} max={366} required value={daysInState} onChange={e => setDaysInState(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Domicile State <span className="text-red-500">*</span></label>
                  <select value={domicileState} onChange={e => setDomicileState(e.target.value)} required
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none">
                    {US_STATES.map(s => <option key={s.code} value={s.code}>{s.name} ({s.code})</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Income Source <span className="text-red-500">*</span></label>
                  <select value={incomeSource} onChange={e => setIncomeSource(e.target.value as typeof incomeSource)} required
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none">
                    <option value="employment">Employment</option>
                    <option value="self_employment">Self-Employment</option>
                    <option value="investment">Investment</option>
                    <option value="rental">Rental</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Year Moved Abroad <span className="text-red-500">*</span></label>
                  <input type="number" min={1900} max={2100} required value={movedAbroadYear} onChange={e => setMovedAbroadYear(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Driver&apos;s License State (optional)</label>
                  <select value={driverLicenseState} onChange={e => setDriverLicenseState(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none">
                    <option value="">— None / Foreign —</option>
                    {US_STATES.map(s => <option key={s.code} value={s.code}>{s.name} ({s.code})</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Voter Registration State (optional)</label>
                  <select value={voterRegState} onChange={e => setVoterRegState(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none">
                    <option value="">— None —</option>
                    {US_STATES.map(s => <option key={s.code} value={s.code}>{s.name} ({s.code})</option>)}
                  </select>
                </div>
                <div className="flex items-center gap-3 sm:col-span-2">
                  <input type="checkbox" id="maintained_home" checked={maintainedHome} onChange={e => setMaintainedHome(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
                  <label htmlFor="maintained_home" className="text-sm font-medium text-gray-700">Maintained a home / permanent place of abode in this state</label>
                </div>
              </div>
              <button type="submit" disabled={loading}
                className="rounded-lg bg-brand-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-800 disabled:opacity-50 transition-colors">
                {loading ? "Analyzing…" : "Analyze Filing Obligations"}
              </button>
            </form>

            {/* Result */}
            {obligationsResult && (
              <div className="mt-8 space-y-5">
                {/* Filing Status Badge */}
                <div className={`rounded-xl border p-5 ${obligationsResult.filing_required ? "bg-red-50 border-red-200" : "bg-green-50 border-green-200"}`}>
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{obligationsResult.filing_required ? "⚠️" : "✅"}</span>
                    <div>
                      <p className={`text-lg font-bold ${obligationsResult.filing_required ? "text-red-800" : "text-green-800"}`}>
                        Filing {obligationsResult.filing_required ? "Required" : "Not Required"}
                      </p>
                      <p className="text-sm text-gray-600 mt-0.5">{obligationsResult.reason}</p>
                    </div>
                  </div>
                </div>

                {/* Nexus & Safe Harbor */}
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className={`rounded-xl border p-4 ${nexusColors[obligationsResult.nexus_type] || "bg-gray-50 border-gray-200"}`}>
                    <p className="text-xs font-semibold uppercase tracking-wide opacity-70">Nexus Type</p>
                    <p className="text-lg font-bold mt-1 capitalize">{obligationsResult.nexus_type.replace("_", " ")}</p>
                  </div>
                  <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-blue-700 opacity-80">Safe Harbor</p>
                    <p className="text-lg font-bold text-blue-800 mt-1">{obligationsResult.safe_harbor_days} days</p>
                  </div>
                  <div className={`rounded-xl border p-4 ${obligationsResult.days_remaining_safe_harbor < 30 ? "bg-orange-50 border-orange-200" : "bg-gray-50 border-gray-200"}`}>
                    <p className="text-xs font-semibold uppercase tracking-wide opacity-70">Days Remaining</p>
                    <p className={`text-lg font-bold mt-1 ${obligationsResult.days_remaining_safe_harbor < 30 ? "text-orange-700" : "text-gray-700"}`}>
                      {obligationsResult.days_remaining_safe_harbor}
                    </p>
                  </div>
                </div>

                {/* Filing info */}
                {obligationsResult.filing_required && (
                  <div className="rounded-xl border border-gray-200 bg-white p-4 grid gap-3 sm:grid-cols-2">
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase">Form</p>
                      <p className="text-sm font-medium text-gray-800 mt-0.5">{obligationsResult.estimated_form}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase">Deadline</p>
                      <p className="text-sm font-medium text-gray-800 mt-0.5">{obligationsResult.filing_deadline}</p>
                    </div>
                  </div>
                )}

                {/* Warning flags */}
                {obligationsResult.warning_flags.length > 0 && (
                  <div className="rounded-xl border border-red-200 bg-red-50 p-4 space-y-2">
                    <p className="text-sm font-bold text-red-700">⚠️ Warning Flags</p>
                    <ul className="space-y-1">
                      {obligationsResult.warning_flags.map((f: string, i: number) => (
                        <li key={i} className="text-sm text-red-700 flex gap-2"><span>•</span><span>{f}</span></li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recommendations */}
                {obligationsResult.recommendations.length > 0 && (
                  <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 space-y-2">
                    <p className="text-sm font-bold text-blue-700">💡 Recommendations</p>
                    <ul className="space-y-1">
                      {obligationsResult.recommendations.map((r: string, i: number) => (
                        <li key={i} className="text-sm text-blue-700 flex gap-2"><span>•</span><span>{r}</span></li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {/* DOMICILE ANALYSIS TAB */}
        {activeTab === "domicile" && (
          <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
            <h2 className="text-lg font-bold text-gray-800 mb-1">Domicile Abandonment Analysis</h2>
            <p className="text-sm text-gray-500 mb-6">Check whether you&apos;ve successfully abandoned your state domicile as a US expat.</p>
            <form onSubmit={handleDomicileSubmit} className="space-y-5">
              <div className="grid gap-5 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Original State <span className="text-red-500">*</span></label>
                  <select value={domOrigState} onChange={e => setDomOrigState(e.target.value)} required
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none">
                    {US_STATES.map(s => <option key={s.code} value={s.code}>{s.name} ({s.code})</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Years Living Abroad <span className="text-red-500">*</span></label>
                  <input type="number" min={0} step={0.5} required value={yearsAbroad} onChange={e => setYearsAbroad(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Return Visits (days/year) <span className="text-red-500">*</span></label>
                  <input type="number" min={0} max={366} required value={returnDays} onChange={e => setReturnDays(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" />
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  { id: "dom_home", value: domMaintainedHome, setter: setDomMaintainedHome, label: "Maintained home in original state" },
                  { id: "voter_reg", value: voterReg, setter: setVoterReg, label: "Voter registration still in original state" },
                  { id: "driver_lic", value: driverLic, setter: setDriverLic, label: "Driver's license still in original state" },
                  { id: "bank_acc", value: bankAccounts, setter: setBankAccounts, label: "Primary bank accounts in original state" },
                  { id: "family", value: familyInState, setter: setFamilyInState, label: "Family (spouse/dependents) in original state" },
                  { id: "intent", value: intentToReturn, setter: setIntentToReturn, label: "Expressed intent to return to original state" },
                  { id: "biz_ties", value: businessTies, setter: setBusinessTies, label: "Active business ties in original state" },
                  { id: "vehicle", value: vehicleReg, setter: setVehicleReg, label: "Vehicle registered in original state" },
                ].map(item => (
                  <div key={item.id} className="flex items-center gap-3">
                    <input type="checkbox" id={item.id} checked={item.value} onChange={e => item.setter(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
                    <label htmlFor={item.id} className="text-sm text-gray-700">{item.label}</label>
                  </div>
                ))}
              </div>

              <button type="submit" disabled={loading}
                className="rounded-lg bg-brand-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-800 disabled:opacity-50 transition-colors">
                {loading ? "Analyzing…" : "Analyze Domicile"}
              </button>
            </form>

            {domicileResult && (
              <div className="mt-8 space-y-5">
                <div className={`rounded-xl border p-5 ${domicileResult.domicile_abandoned ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{domicileResult.domicile_abandoned ? "✅" : "⚠️"}</span>
                    <div>
                      <p className={`text-lg font-bold ${domicileResult.domicile_abandoned ? "text-green-800" : "text-red-800"}`}>
                        Domicile {domicileResult.domicile_abandoned ? "Likely Abandoned" : "Likely NOT Abandoned"}
                      </p>
                      <p className="text-sm text-gray-600 mt-0.5">{domicileResult.summary}</p>
                    </div>
                  </div>
                </div>

                {/* Risk Score */}
                <div className="rounded-xl border border-gray-200 bg-white p-4">
                  <p className="text-sm font-semibold text-gray-600 mb-2">Risk Score: {domicileResult.risk_score}/100</p>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${domicileResult.risk_score < 40 ? "bg-green-500" : domicileResult.risk_score < 70 ? "bg-yellow-500" : "bg-red-500"}`}
                      style={{ width: `${domicileResult.risk_score}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">0 = clearly abandoned · 100 = clearly retained</p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  {domicileResult.factors_for.length > 0 && (
                    <div className="rounded-xl border border-green-200 bg-green-50 p-4 space-y-2">
                      <p className="text-sm font-bold text-green-700">✅ Factors Supporting Abandonment</p>
                      <ul className="space-y-1">
                        {domicileResult.factors_for.map((f: string, i: number) => (
                          <li key={i} className="text-sm text-green-700 flex gap-2"><span>•</span><span>{f}</span></li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {domicileResult.factors_against.length > 0 && (
                    <div className="rounded-xl border border-red-200 bg-red-50 p-4 space-y-2">
                      <p className="text-sm font-bold text-red-700">⚠️ Risk Factors (Retained Ties)</p>
                      <ul className="space-y-1">
                        {domicileResult.factors_against.map((f: string, i: number) => (
                          <li key={i} className="text-sm text-red-700 flex gap-2"><span>•</span><span>{f}</span></li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>
        )}

        {/* ALL 50 STATES TAB */}
        {activeTab === "states" && (
          <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-gray-800 mb-4">All 50 States — Income Tax & Safe Harbor Overview</h2>
            {statesData.length === 0 ? (
              <p className="text-sm text-gray-400">Loading state data…</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left">
                      <th className="py-2 pr-4 font-semibold text-gray-600">State</th>
                      <th className="py-2 pr-4 font-semibold text-gray-600">Income Tax</th>
                      <th className="py-2 pr-4 font-semibold text-gray-600">Safe Harbor</th>
                      <th className="py-2 font-semibold text-gray-600">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {statesData.map(s => (
                      <tr key={s.code} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                        <td className="py-2 pr-4 font-semibold text-gray-800">{s.name} <span className="text-gray-400 text-xs">({s.code})</span></td>
                        <td className="py-2 pr-4">
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${s.has_income_tax ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}`}>
                            {s.has_income_tax ? "Yes" : "No Tax"}
                          </span>
                        </td>
                        <td className="py-2 pr-4 text-gray-600">{s.safe_harbor_days} days</td>
                        <td className="py-2 text-gray-500 text-xs">{s.notes}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        <p className="text-xs text-gray-400 text-center">
          This tool provides general information only. Consult a qualified tax professional for advice specific to your situation.
        </p>
      </main>
    </div>
  );
}
