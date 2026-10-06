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
// Totalization Agreement types & API
// -----------------------------------------------------------------------

export interface TotalizationRequest {
  country: string;
  employment_type: "employee" | "self_employed";
  years_in_us: number;
  years_in_country: number;
  us_citizen: boolean;
}

export interface TotalizationResult {
  agreement_exists: boolean;
  agreement_countries: string[];
  applicable_system: string;
  avoid_double_taxation: boolean;
  fica_exempt: boolean;
  explanation: string;
}

export async function apiTotalizationCheck(
  payload: TotalizationRequest
): Promise<TotalizationResult> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/totalization/check`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<TotalizationResult>(res);
}

export async function apiTotalizationCountries(): Promise<{
  count: number;
  countries: string[];
}> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/totalization/countries`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<{ count: number; countries: string[] }>(res);
}

// -----------------------------------------------------------------------
// FBAR Penalties types & API
// -----------------------------------------------------------------------

export interface FBARPenaltyRequest {
  violation_type: "non_willful" | "willful" | "fraud";
  years_of_violation: number;
  max_account_balance: number;
  filed_late: boolean;
  voluntary_disclosure: boolean;
}

export interface PenaltyBreakdownItem {
  description: string;
  amount: number;
}

export interface FBARPenaltyResult {
  min_penalty: number;
  max_penalty: number;
  criminal_risk: boolean;
  streamlined_eligible: boolean;
  penalty_breakdown: PenaltyBreakdownItem[];
  recommendation: string;
}

export async function apiFBARPenalties(
  payload: FBARPenaltyRequest
): Promise<FBARPenaltyResult> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/fbar/penalties`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<FBARPenaltyResult>(res);
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

// -----------------------------------------------------------------------
// State Tax Filing Obligations
// -----------------------------------------------------------------------

export interface StateTaxObligationsRequest {
  state: string;
  days_in_state: number;
  domicile_state: string;
  income_source: "employment" | "self_employment" | "investment" | "rental";
  moved_abroad_year: number;
  maintained_home: boolean;
  driver_license_state?: string;
  voter_reg_state?: string;
}

export interface StateTaxObligationsResult {
  filing_required: boolean;
  reason: string;
  nexus_type: "domicile" | "statutory_resident" | "nonresident" | "none";
  safe_harbor_days: number;
  days_remaining_safe_harbor: number;
  filing_deadline: string;
  estimated_form: string;
  recommendations: string[];
  warning_flags: string[];
}

export interface StateTaxStateInfo {
  code: string;
  name: string;
  has_income_tax: boolean;
  safe_harbor_days: number;
  statutory_resident_days: number;
  notes: string;
}

export interface StateTaxStatesResult {
  count: number;
  states: StateTaxStateInfo[];
  note: string;
}

export interface StateTaxDomicileRequest {
  original_state: string;
  years_abroad: number;
  maintained_home: boolean;
  voter_registered_in_state: boolean;
  driver_license_in_state: boolean;
  bank_accounts_in_state: boolean;
  family_in_state: boolean;
  returned_to_state_days_per_year: number;
  intent_to_return: boolean;
  business_ties_in_state: boolean;
  vehicle_registered_in_state: boolean;
}

export interface StateTaxDomicileResult {
  domicile_abandoned: boolean;
  risk_score: number;
  factors_for: string[];
  factors_against: string[];
  summary: string;
}

export async function apiStateTaxObligations(
  payload: StateTaxObligationsRequest
): Promise<StateTaxObligationsResult> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/state-tax/obligations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<StateTaxObligationsResult>(res);
}

export async function apiStateTaxStates(): Promise<StateTaxStatesResult> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/state-tax/states`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<StateTaxStatesResult>(res);
}

export async function apiStateTaxDomicileAnalysis(
  payload: StateTaxDomicileRequest
): Promise<StateTaxDomicileResult> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/state-tax/domicile-analysis`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<StateTaxDomicileResult>(res);
}

// -----------------------------------------------------------------------
// Form 8938 FATCA types & API
// -----------------------------------------------------------------------

export interface ForeignAccount8938 {
  account_name: string;
  account_type: string;
  country: string;
  max_value_usd: number;
}

export interface FilingRequirement8938Request {
  filing_status: "single" | "mfj" | "mfs" | "hoh";
  accounts: ForeignAccount8938[];
  tax_year: number;
}

export interface FilingRequirement8938Result {
  filing_required: boolean;
  threshold_usd: number;
  total_value_usd: number;
  reasons: string[];
  penalty_if_not_filed: number;
  recommendation: string;
}

export interface PenaltyCalculation8938Request {
  filing_status: "single" | "mfj" | "mfs" | "hoh";
  accounts: ForeignAccount8938[];
  tax_year: number;
  days_unreported: number;
  is_willful: boolean;
}

export interface PenaltyResult8938 {
  base_penalty: number;
  continued_failure_penalty: number;
  willful_penalty: number;
  total_penalty: number;
  days_unreported: number;
  is_willful: boolean;
  explanation: string;
}

export interface Form8938Overview {
  title: string;
  filing_requirement: string;
  thresholds: Record<string, number>;
  penalties: Record<string, number>;
  account_types: string[];
  recommendation: string;
}

export async function apiForm8938FilingRequirement(
  payload: FilingRequirement8938Request
): Promise<FilingRequirement8938Result> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/form8938/filing-requirement`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<FilingRequirement8938Result>(res);
}

export async function apiForm8938PenaltyCalculator(
  payload: PenaltyCalculation8938Request
): Promise<PenaltyResult8938> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/form8938/penalty-calculator`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<PenaltyResult8938>(res);
}

export async function apiForm8938Overview(): Promise<Form8938Overview> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/form8938/overview`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<Form8938Overview>(res);
}

// -----------------------------------------------------------------------
// Form 8865 Foreign Partnerships types & API
// -----------------------------------------------------------------------

export interface Partnership8865 {
  name: string;
  country: string;
  ownership_percentage: number;
  us_controlled: boolean;
  fair_market_value_usd: number;
  capital_contributed_usd?: number;
  reportable_event?: boolean;
}

export interface FilingRequirement8865Request {
  tax_year: number;
  partnerships: Partnership8865[];
}

export interface FilingRequirement8865Result {
  filing_required: boolean;
  categories: string[];
  total_partnerships: number;
  reasons: string[];
  penalty_if_not_filed: number;
  recommendation: string;
}

export interface IncomeSummary8865Request {
  tax_year: number;
  partnership_name: string;
  subpart_f_income_usd: number;
  gilti_usd: number;
  qbi_199a_usd: number;
  ordinary_income_usd: number;
  capital_gain_usd: number;
  foreign_tax_paid_usd: number;
}

export interface IncomeSummary8865Result {
  total_income_usd: number;
  foreign_tax_credit_eligible: boolean;
  notes: string[];
}

export interface PenaltyCalculation8865Request {
  tax_year: number;
  partnerships: Partnership8865[];
  days_unreported: number;
  is_willful: boolean;
}

export interface PenaltyResult8865 {
  base_penalty: number;
  continued_failure_penalty: number;
  willful_penalty: number;
  total_penalty: number;
  explanation: string;
}

export interface Form8865Overview {
  title: string;
  category_1: string;
  category_2: string;
  category_3: string;
  category_4: string;
  category_5: string;
  penalties: string;
  filing_deadline: string;
}

export async function apiForm8865FilingRequirement(
  payload: FilingRequirement8865Request
): Promise<FilingRequirement8865Result> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/form8865/filing-requirement`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<FilingRequirement8865Result>(res);
}

export async function apiForm8865IncomeSummary(
  payload: IncomeSummary8865Request
): Promise<IncomeSummary8865Result> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/form8865/income-summary`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<IncomeSummary8865Result>(res);
}

export async function apiForm8865PenaltyCalculation(
  payload: PenaltyCalculation8865Request
): Promise<PenaltyResult8865> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/form8865/penalty-calculation`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<PenaltyResult8865>(res);
}

export async function apiForm8865Overview(): Promise<Form8865Overview> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/form8865/overview`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<Form8865Overview>(res);
}
