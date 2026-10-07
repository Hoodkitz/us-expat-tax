"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiMe } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type ActiveTab = "overview" | "deductions" | "home-office" | "vehicle";
type HomeOfficeMethod = "simplified" | "actual";
type VehicleMethod = "standard_mileage" | "actual";

interface ScheduleCFormState {
  // Income
  gross_receipts: string;
  returns_and_allowances: string;
  cost_of_goods_sold: string;
  other_income: string;
  
  // Common expenses
  advertising: string;
  commissions_and_fees: string;
  contract_labor: string;
  insurance: string;
  legal_and_professional: string;
  office_expense: string;
  supplies: string;
  utilities: string;
  wages: string;
  meals: string;
  other_expenses: string;
}

interface HomeOfficeSimplified {
  method: "simplified";
  square_footage: number;
}

interface HomeOfficeActual {
  method: "actual";
  business_square_footage: number;
  total_home_square_footage: number;
  direct_expenses: number;
  mortgage_interest: number;
  real_estate_taxes: number;
  utilities: number;
  insurance: number;
}

interface VehicleStandardMileage {
  method: "standard_mileage";
  business_miles: number;
  total_miles: number;
  parking_and_tolls: number;
}

interface VehicleActualExpenses {
  method: "actual";
  business_miles: number;
  total_miles: number;
  gasoline: number;
  insurance: number;
  repairs_and_maintenance: number;
  depreciation: number;
  parking_and_tolls: number;
}

interface ScheduleCResult {
  gross_income: number;
  returns_and_allowances: number;
  net_gross_income: number;
  cost_of_goods_sold: number;
  gross_profit: number;
  other_income: number;
  total_income: number;
  total_expenses: number;
  home_office_deduction: number;
  vehicle_deduction: number;
  meals_deduction_adjustment: number;
  net_profit_or_loss: number;
  flows_to_schedule_se: boolean;
  expense_breakdown: {
    ordinary_expenses: number;
    home_office: number;
    vehicle: number;
    meals_50_percent_limit: number;
  };
}

interface HomeOfficeResult {
  method: HomeOfficeMethod;
  deduction_amount: number;
  business_use_percentage: number | null;
  square_footage_used: number;
  details: Record<string, any>;
}

interface VehicleResult {
  method: VehicleMethod;
  deduction_amount: number;
  business_use_percentage: number;
  business_miles: number;
  total_miles: number;
  qualifies_for_listed_property: boolean;
  details: Record<string, any>;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function usd(n: number) {
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

async function apiScheduleCCalculate(data: any): Promise<ScheduleCResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch("http://localhost:8000/api/v1/schedule-c/calculate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

async function apiHomeOfficeCalculate(data: HomeOfficeSimplified | HomeOfficeActual): Promise<HomeOfficeResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch("http://localhost:8000/api/v1/schedule-c/home-office", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

async function apiVehicleCalculate(data: VehicleStandardMileage | VehicleActualExpenses): Promise<VehicleResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch("http://localhost:8000/api/v1/schedule-c/vehicle", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------
export default function ScheduleCPage() {
  const router = useRouter();
  const [tab, setTab] = useState<ActiveTab>("overview");
  const [homeOfficeMethod, setHomeOfficeMethod] = useState<HomeOfficeMethod>("simplified");
  const [vehicleMethod, setVehicleMethod] = useState<VehicleMethod>("standard_mileage");
  
  const [form, setForm] = useState<ScheduleCFormState>({
    gross_receipts: "150000",
    returns_and_allowances: "0",
    cost_of_goods_sold: "0",
    other_income: "0",
    advertising: "0",
    commissions_and_fees: "0",
    contract_labor: "0",
    insurance: "0",
    legal_and_professional: "0",
    office_expense: "0",
    supplies: "5000",
    utilities: "0",
    wages: "0",
    meals: "2000",
    other_expenses: "0",
  });

  const [homeOfficeSimplified, setHomeOfficeSimplified] = useState<HomeOfficeSimplified>({
    method: "simplified",
    square_footage: 200,
  });

  const [homeOfficeActual, setHomeOfficeActual] = useState<HomeOfficeActual>({
    method: "actual",
    business_square_footage: 300,
    total_home_square_footage: 2000,
    direct_expenses: 0,
    mortgage_interest: 18000,
    real_estate_taxes: 0,
    utilities: 2400,
    insurance: 1200,
  });

  const [vehicleStandard, setVehicleStandard] = useState<VehicleStandardMileage>({
    method: "standard_mileage",
    business_miles: 12000,
    total_miles: 15000,
    parking_and_tolls: 500,
  });

  const [vehicleActual, setVehicleActual] = useState<VehicleActualExpenses>({
    method: "actual",
    business_miles: 12000,
    total_miles: 15000,
    gasoline: 3000,
    insurance: 1200,
    repairs_and_maintenance: 800,
    depreciation: 4000,
    parking_and_tolls: 500,
  });

  const [result, setResult] = useState<ScheduleCResult | null>(null);
  const [homeOfficeResult, setHomeOfficeResult] = useState<HomeOfficeResult | null>(null);
  const [vehicleResult, setVehicleResult] = useState<VehicleResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiMe()
      .then((user) => console.log("Logged in as:", user.email))
      .catch(() => router.push("/"));
  }, [router]);

  const handleCalculate = async () => {
    setError("");
    try {
      const homeOffice = homeOfficeMethod === "simplified" 
        ? homeOfficeSimplified
        : homeOfficeActual;

      const vehicle = vehicleMethod === "standard_mileage"
        ? vehicleStandard
        : vehicleActual;

      const data = {
        income_expenses: {
          gross_receipts: parseFloat(form.gross_receipts),
          returns_and_allowances: parseFloat(form.returns_and_allowances),
          cost_of_goods_sold: parseFloat(form.cost_of_goods_sold),
          other_income: parseFloat(form.other_income),
          advertising: parseFloat(form.advertising),
          commissions_and_fees: parseFloat(form.commissions_and_fees),
          contract_labor: parseFloat(form.contract_labor),
          insurance: parseFloat(form.insurance),
          legal_and_professional: parseFloat(form.legal_and_professional),
          office_expense: parseFloat(form.office_expense),
          supplies: parseFloat(form.supplies),
          utilities: parseFloat(form.utilities),
          wages: parseFloat(form.wages),
          meals: parseFloat(form.meals),
          other_expenses: parseFloat(form.other_expenses),
        },
        home_office: homeOffice,
        vehicle: vehicle,
      };

      const res = await apiScheduleCCalculate(data);
      setResult(res);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleHomeOfficeCalculate = async () => {
    setError("");
    try {
      const data = homeOfficeMethod === "simplified"
        ? homeOfficeSimplified
        : homeOfficeActual;
      
      const res = await apiHomeOfficeCalculate(data);
      setHomeOfficeResult(res);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleVehicleCalculate = async () => {
    setError("");
    try {
      const data = vehicleMethod === "standard_mileage"
        ? vehicleStandard
        : vehicleActual;
      
      const res = await apiVehicleCalculate(data);
      setVehicleResult(res);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white shadow-sm rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Schedule C</h1>
              <p className="text-gray-600 mt-1">Profit or Loss From Business (Sole Proprietorship)</p>
            </div>
            <Link
              href="/dashboard"
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              ← Dashboard
            </Link>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white shadow-sm rounded-lg mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setTab("overview")}
                className={`py-4 px-6 text-sm font-medium ${
                  tab === "overview"
                    ? "border-b-2 border-blue-500 text-blue-600"
                    : "text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setTab("deductions")}
                className={`py-4 px-6 text-sm font-medium ${
                  tab === "deductions"
                    ? "border-b-2 border-blue-500 text-blue-600"
                    : "text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Deductions
              </button>
              <button
                onClick={() => setTab("home-office")}
                className={`py-4 px-6 text-sm font-medium ${
                  tab === "home-office"
                    ? "border-b-2 border-blue-500 text-blue-600"
                    : "text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Home Office
              </button>
              <button
                onClick={() => setTab("vehicle")}
                className={`py-4 px-6 text-sm font-medium ${
                  tab === "vehicle"
                    ? "border-b-2 border-blue-500 text-blue-600"
                    : "text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Vehicle
              </button>
            </nav>
          </div>
        </div>

        {/* Overview Tab */}
        {tab === "overview" && (
          <div className="bg-white shadow-sm rounded-lg p-6 space-y-6">
            <h2 className="text-xl font-semibold">Business Income & Expenses</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gross Receipts
                </label>
                <input
                  type="number"
                  value={form.gross_receipts}
                  onChange={(e) => setForm({ ...form, gross_receipts: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Returns & Allowances
                </label>
                <input
                  type="number"
                  value={form.returns_and_allowances}
                  onChange={(e) => setForm({ ...form, returns_and_allowances: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cost of Goods Sold
                </label>
                <input
                  type="number"
                  value={form.cost_of_goods_sold}
                  onChange={(e) => setForm({ ...form, cost_of_goods_sold: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Other Income
                </label>
                <input
                  type="number"
                  value={form.other_income}
                  onChange={(e) => setForm({ ...form, other_income: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>

            <h3 className="text-lg font-semibold mt-6">Business Expenses</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Advertising</label>
                <input
                  type="number"
                  value={form.advertising}
                  onChange={(e) => setForm({ ...form, advertising: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Supplies</label>
                <input
                  type="number"
                  value={form.supplies}
                  onChange={(e) => setForm({ ...form, supplies: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Legal & Professional</label>
                <input
                  type="number"
                  value={form.legal_and_professional}
                  onChange={(e) => setForm({ ...form, legal_and_professional: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Meals (50% deductible)</label>
                <input
                  type="number"
                  value={form.meals}
                  onChange={(e) => setForm({ ...form, meals: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Wages</label>
                <input
                  type="number"
                  value={form.wages}
                  onChange={(e) => setForm({ ...form, wages: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Other Expenses</label>
                <input
                  type="number"
                  value={form.other_expenses}
                  onChange={(e) => setForm({ ...form, other_expenses: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>

            <button
              onClick={handleCalculate}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 font-medium mt-6"
            >
              Calculate Schedule C
            </button>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            {result && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mt-6">
                <h3 className="text-lg font-semibold text-blue-900 mb-4">Schedule C Results</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="font-medium">Total Income:</span>
                    <span className="font-mono">{usd(result.total_income)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Total Expenses:</span>
                    <span className="font-mono">{usd(result.total_expenses)}</span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span className="ml-4">• Home Office:</span>
                    <span className="font-mono">{usd(result.home_office_deduction)}</span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span className="ml-4">• Vehicle:</span>
                    <span className="font-mono">{usd(result.vehicle_deduction)}</span>
                  </div>
                  <div className="border-t pt-3 flex justify-between text-lg font-bold">
                    <span className={result.net_profit_or_loss >= 0 ? "text-green-700" : "text-red-700"}>
                      Net {result.net_profit_or_loss >= 0 ? "Profit" : "Loss"}:
                    </span>
                    <span className={`font-mono ${result.net_profit_or_loss >= 0 ? "text-green-700" : "text-red-700"}`}>
                      {usd(result.net_profit_or_loss)}
                    </span>
                  </div>
                  {result.flows_to_schedule_se && (
                    <div className="bg-yellow-50 border border-yellow-200 p-3 rounded mt-4">
                      <p className="text-sm text-yellow-800">
                        ✓ This profit flows to <strong>Schedule SE</strong> for self-employment tax calculation
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Deductions Tab */}
        {tab === "deductions" && (
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Business Deductions Summary</h2>
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">Home Office Deduction</h3>
                <p className="text-sm text-gray-600 mb-2">
                  Two methods available:
                </p>
                <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
                  <li><strong>Simplified:</strong> $5/sqft, max 300 sqft ($1,500 max)</li>
                  <li><strong>Actual:</strong> Track all home expenses, prorate by business %</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">Vehicle Deduction</h3>
                <p className="text-sm text-gray-600 mb-2">
                  Two methods available:
                </p>
                <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
                  <li><strong>Standard Mileage:</strong> 67¢/mile for business miles (2024)</li>
                  <li><strong>Actual Expenses:</strong> Total expenses × business use %</li>
                  <li>Requires &gt;50% business use for listed property status</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">Meals Limitation</h3>
                <p className="text-sm text-gray-700">
                  Only 50% of business meal expenses are deductible (IRC §274(n))
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                <h3 className="font-semibold text-blue-900 mb-2">💡 Important Requirements</h3>
                <ul className="text-sm text-blue-800 list-disc list-inside space-y-1">
                  <li>Regular and continuous business activity (not hobby)</li>
                  <li>Intent to make a profit (profit motive test)</li>
                  <li>Proper substantiation for all expenses</li>
                  <li>Mileage logs required for vehicle deductions</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Home Office Tab */}
        {tab === "home-office" && (
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Home Office Deduction</h2>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Method</label>
              <select
                value={homeOfficeMethod}
                onChange={(e) => setHomeOfficeMethod(e.target.value as HomeOfficeMethod)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="simplified">Simplified ($5/sqft)</option>
                <option value="actual">Actual Expenses</option>
              </select>
            </div>

            {homeOfficeMethod === "simplified" ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Square Footage (max 300)
                  </label>
                  <input
                    type="number"
                    value={homeOfficeSimplified.square_footage}
                    onChange={(e) =>
                      setHomeOfficeSimplified({ ...homeOfficeSimplified, square_footage: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Business Square Footage
                  </label>
                  <input
                    type="number"
                    value={homeOfficeActual.business_square_footage}
                    onChange={(e) =>
                      setHomeOfficeActual({ ...homeOfficeActual, business_square_footage: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Total Home Square Footage
                  </label>
                  <input
                    type="number"
                    value={homeOfficeActual.total_home_square_footage}
                    onChange={(e) =>
                      setHomeOfficeActual({ ...homeOfficeActual, total_home_square_footage: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Mortgage Interest
                  </label>
                  <input
                    type="number"
                    value={homeOfficeActual.mortgage_interest}
                    onChange={(e) =>
                      setHomeOfficeActual({ ...homeOfficeActual, mortgage_interest: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Utilities
                  </label>
                  <input
                    type="number"
                    value={homeOfficeActual.utilities}
                    onChange={(e) =>
                      setHomeOfficeActual({ ...homeOfficeActual, utilities: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Insurance
                  </label>
                  <input
                    type="number"
                    value={homeOfficeActual.insurance}
                    onChange={(e) =>
                      setHomeOfficeActual({ ...homeOfficeActual, insurance: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
            )}

            <button
              onClick={handleHomeOfficeCalculate}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 font-medium mt-6"
            >
              Calculate Home Office Deduction
            </button>

            {homeOfficeResult && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 mt-6">
                <h3 className="text-lg font-semibold text-green-900 mb-4">Home Office Result</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="font-medium">Method:</span>
                    <span className="capitalize">{homeOfficeResult.method}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Square Footage:</span>
                    <span>{homeOfficeResult.square_footage_used} sqft</span>
                  </div>
                  {homeOfficeResult.business_use_percentage && (
                    <div className="flex justify-between">
                      <span className="font-medium">Business Use %:</span>
                      <span>{homeOfficeResult.business_use_percentage}%</span>
                    </div>
                  )}
                  <div className="border-t pt-2 flex justify-between text-lg font-bold text-green-700">
                    <span>Deduction:</span>
                    <span className="font-mono">{usd(homeOfficeResult.deduction_amount)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Vehicle Tab */}
        {tab === "vehicle" && (
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Vehicle Deduction</h2>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Method</label>
              <select
                value={vehicleMethod}
                onChange={(e) => setVehicleMethod(e.target.value as VehicleMethod)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="standard_mileage">Standard Mileage (67¢/mile)</option>
                <option value="actual">Actual Expenses</option>
              </select>
            </div>

            {vehicleMethod === "standard_mileage" ? (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Business Miles
                  </label>
                  <input
                    type="number"
                    value={vehicleStandard.business_miles}
                    onChange={(e) =>
                      setVehicleStandard({ ...vehicleStandard, business_miles: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Total Miles
                  </label>
                  <input
                    type="number"
                    value={vehicleStandard.total_miles}
                    onChange={(e) =>
                      setVehicleStandard({ ...vehicleStandard, total_miles: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Parking & Tolls
                  </label>
                  <input
                    type="number"
                    value={vehicleStandard.parking_and_tolls}
                    onChange={(e) =>
                      setVehicleStandard({ ...vehicleStandard, parking_and_tolls: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Business Miles
                  </label>
                  <input
                    type="number"
                    value={vehicleActual.business_miles}
                    onChange={(e) =>
                      setVehicleActual({ ...vehicleActual, business_miles: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Total Miles
                  </label>
                  <input
                    type="number"
                    value={vehicleActual.total_miles}
                    onChange={(e) =>
                      setVehicleActual({ ...vehicleActual, total_miles: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gasoline
                  </label>
                  <input
                    type="number"
                    value={vehicleActual.gasoline}
                    onChange={(e) =>
                      setVehicleActual({ ...vehicleActual, gasoline: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Insurance
                  </label>
                  <input
                    type="number"
                    value={vehicleActual.insurance}
                    onChange={(e) =>
                      setVehicleActual({ ...vehicleActual, insurance: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Repairs & Maintenance
                  </label>
                  <input
                    type="number"
                    value={vehicleActual.repairs_and_maintenance}
                    onChange={(e) =>
                      setVehicleActual({ ...vehicleActual, repairs_and_maintenance: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Depreciation
                  </label>
                  <input
                    type="number"
                    value={vehicleActual.depreciation}
                    onChange={(e) =>
                      setVehicleActual({ ...vehicleActual, depreciation: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Parking & Tolls
                  </label>
                  <input
                    type="number"
                    value={vehicleActual.parking_and_tolls}
                    onChange={(e) =>
                      setVehicleActual({ ...vehicleActual, parking_and_tolls: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
            )}

            <button
              onClick={handleVehicleCalculate}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 font-medium mt-6"
            >
              Calculate Vehicle Deduction
            </button>

            {vehicleResult && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 mt-6">
                <h3 className="text-lg font-semibold text-green-900 mb-4">Vehicle Result</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="font-medium">Method:</span>
                    <span className="capitalize">{vehicleResult.method.replace("_", " ")}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Business Miles:</span>
                    <span>{vehicleResult.business_miles.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Business Use %:</span>
                    <span>{vehicleResult.business_use_percentage}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Qualifies for Listed Property:</span>
                    <span className={vehicleResult.qualifies_for_listed_property ? "text-green-600" : "text-red-600"}>
                      {vehicleResult.qualifies_for_listed_property ? "Yes (>50%)" : "No (<50%)"}
                    </span>
                  </div>
                  <div className="border-t pt-2 flex justify-between text-lg font-bold text-green-700">
                    <span>Deduction:</span>
                    <span className="font-mono">{usd(vehicleResult.deduction_amount)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
