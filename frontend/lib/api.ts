const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// -----------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------

export interface TenantOut {
  email: string;
  tenant_name: string;
  tenant_id: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface TaxEvaluationRequest {
  foreign_earned_income_usd: string;
  german_income_tax_paid_usd: string;
  us_tax_liability_before_credits_usd: string;
  num_qualifying_children: number;
}

export interface TaxPathResult {
  credit_usd?: string;
  exclusion_usd?: string;
  resulting_tax_usd: string;
  ctc_unlocked: boolean;
  actc_refundable_usd: string;
}

export interface TaxEvaluationResult {
  recommended_path: string;
  recommendation_reason: string;
  ftc: TaxPathResult;
  feie: TaxPathResult;
}

// -----------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("jwt_token");
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// -----------------------------------------------------------------------
// Auth
// -----------------------------------------------------------------------

export async function apiRegister(
  email: string,
  password: string,
  tenant_name: string
): Promise<TenantOut> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, tenant_name }),
  });
  return handleResponse<TenantOut>(res);
}

export async function apiLogin(
  email: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse<TokenResponse>(res);
}

export async function apiMe(): Promise<TenantOut> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<TenantOut>(res);
}

// -----------------------------------------------------------------------
// FBAR types
// -----------------------------------------------------------------------

export interface FBAReporter {
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  country: string;
  ssn_last4: string;
}

export interface ForeignAccount {
  institution_name: string;
  country: string;
  account_number: string;
  max_balance_usd: string;
}

export interface FBARReport {
  reporter: FBAReporter;
  year: number;
  accounts: ForeignAccount[];
}

export async function apiFBARJson(report: FBARReport): Promise<any> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/fbar/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(report),
  });
  return handleResponse<any>(res);
}

export async function apiFBARPdf(report: FBARReport): Promise<Blob> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/fbar/generate/pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(report),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.blob();
}

// -----------------------------------------------------------------------
// FEIE (Form 2555) types
// -----------------------------------------------------------------------

export interface FEIECalculateRequest {
  tax_year: number;
  foreign_earned_income: number;
  housing_costs: number;
  days_in_foreign_country: number;
  bona_fide_resident: boolean;
  filing_status: "single" | "married_filing_jointly" | "married_filing_separately";
  employer_provided_housing: number;
}

export interface FEIECalculateResult {
  qualifies_pp: boolean;
  qualifies_bfr: boolean;
  qualifies: boolean;
  feie_limit: number;
  feie_exclusion: number;
  housing_exclusion: number;
  housing_base_amount: number;
  total_exclusion: number;
  taxable_income_estimate: number;
  form_2555_required: boolean;
  notes: string[];
}

export interface FEIEEligibilityRequest {
  days_outside_us: number;
  bona_fide_resident: boolean;
  us_citizen_or_green_card: boolean;
}

export interface FEIEEligibilityResult {
  eligible: boolean;
  test_passed: "physical_presence" | "bona_fide_residence" | "none";
  reason: string;
}

export async function apiFEIECalculate(
  payload: FEIECalculateRequest
): Promise<FEIECalculateResult> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/feie/calculate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<FEIECalculateResult>(res);
}

export async function apiFEIECheckEligibility(
  payload: FEIEEligibilityRequest
): Promise<FEIEEligibilityResult> {
  const res = await fetch(`${API_BASE}/api/v1/feie/check-eligibility`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<FEIEEligibilityResult>(res);
}

// -----------------------------------------------------------------------
// Tax Evaluation
// -----------------------------------------------------------------------

export async function apiEvaluate(
  payload: TaxEvaluationRequest
): Promise<TaxEvaluationResult> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/tax/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<TaxEvaluationResult>(res);
}
