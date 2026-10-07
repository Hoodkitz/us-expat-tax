"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AlertCircle, CheckCircle, FileText, DollarSign, Calculator, AlertTriangle } from "lucide-react"

interface FilingRequirementResult {
  tax_year: number
  resident_status: string
  must_file: boolean
  substantial_presence_days: string
  passes_substantial_presence_test: boolean
  treaty_exemption_applies: boolean
  filing_deadline: string
  extension_deadline: string
  reasoning: string
}

interface IncomeItem {
  description: string
  income_type: string
  gross_amount: number
  us_sourced: boolean
  treaty_exempt: boolean
  treaty_article?: string
  withheld_amount: number
  withholding_type?: string
}

interface IncomeSummaryResult {
  tax_year: number
  total_eci: string
  total_fdap: string
  total_capital_gains: string
  total_us_sourced: string
  total_foreign_sourced: string
  total_treaty_exempt: string
  taxable_eci: string
  taxable_fdap: string
  standard_deduction: string
  itemized_deductions: string
  total_tax_before_credits: string
  effective_rate: string
}

interface WithholdingCreditResult {
  tax_year: number
  total_chapter_3_credit: string
  total_chapter_4_credit: string
  total_backup_credit: string
  total_estimated_tax: string
  total_credits: string
  refundable_amount: string
  non_refundable_amount: string
}

interface PenaltyResult {
  tax_year: number
  days_late: number
  late_filing_penalty: string
  late_payment_penalty: string
  interest_charges: string
  total_penalties: string
  minimum_penalty_applies: boolean
  minimum_penalty_amount: string
  waived_due_to_reasonable_cause: boolean
  total_amount_due: string
}

export default function Form1040NRPage() {
  const [taxYear, setTaxYear] = useState(2024)
  const [activeTab, setActiveTab] = useState("filing-requirement")

  // Filing Requirement state
  const [daysCurrentYear, setDaysCurrentYear] = useState(0)
  const [daysPriorYear1, setDaysPriorYear1] = useState(0)
  const [daysPriorYear2, setDaysPriorYear2] = useState(0)
  const [treatyCountry, setTreatyCountry] = useState("")
  const [isStudent, setIsStudent] = useState(false)
  const [isTeacher, setIsTeacher] = useState(false)
  const [hasUSIncome, setHasUSIncome] = useState(false)
  const [grossIncome, setGrossIncome] = useState(0)
  const [filingResult, setFilingResult] = useState<FilingRequirementResult | null>(null)

  // Income Summary state
  const [incomeItems, setIncomeItems] = useState<IncomeItem[]>([])
  const [useStandardDeduction, setUseStandardDeduction] = useState(true)
  const [itemizedDeductions, setItemizedDeductions] = useState(0)
  const [incomeSummary, setIncomeSummary] = useState<IncomeSummaryResult | null>(null)

  // Withholding Credit state
  const [chapter3Withheld, setChapter3Withheld] = useState(0)
  const [chapter4Withheld, setChapter4Withheld] = useState(0)
  const [backupWithheld, setBackupWithheld] = useState(0)
  const [estimatedTax, setEstimatedTax] = useState(0)
  const [priorYearOverpayment, setPriorYearOverpayment] = useState(0)
  const [withholdingResult, setWithholdingResult] = useState<WithholdingCreditResult | null>(null)

  // Penalty Calculator state
  const [filingDeadline, setFilingDeadline] = useState("")
  const [actualFilingDate, setActualFilingDate] = useState("")
  const [taxOwed, setTaxOwed] = useState(0)
  const [extensionFiled, setExtensionFiled] = useState(false)
  const [reasonableCause, setReasonableCause] = useState(false)
  const [penaltyResult, setPenaltyResult] = useState<PenaltyResult | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const apiCall = async (endpoint: string, data: any) => {
    const token = localStorage.getItem("token")
    const response = await fetch(`http://localhost:8000/api/v1/form1040nr/${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || "API-Fehler")
    }

    return response.json()
  }

  const checkFilingRequirement = async () => {
    setLoading(true)
    setError("")
    try {
      const result = await apiCall("filing-requirement", {
        tax_year: taxYear,
        days_in_us_current_year: daysCurrentYear,
        days_in_us_prior_year_1: daysPriorYear1,
        days_in_us_prior_year_2: daysPriorYear2,
        treaty_country: treatyCountry || null,
        is_student: isStudent,
        is_teacher: isTeacher,
        has_us_sourced_income: hasUSIncome,
        gross_income: grossIncome,
      })
      setFilingResult(result)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const calculateIncomeSummary = async () => {
    setLoading(true)
    setError("")
    try {
      const result = await apiCall("income-summary", {
        tax_year: taxYear,
        income_items: incomeItems,
        standard_deduction_claimed: useStandardDeduction,
        itemized_deductions: itemizedDeductions,
      })
      setIncomeSummary(result)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const calculateWithholding = async () => {
    setLoading(true)
    setError("")
    try {
      const result = await apiCall("withholding-credit", {
        tax_year: taxYear,
        chapter_3_withheld: chapter3Withheld,
        chapter_4_withheld: chapter4Withheld,
        backup_withheld: backupWithheld,
        estimated_tax_paid: estimatedTax,
        prior_year_overpayment: priorYearOverpayment,
      })
      setWithholdingResult(result)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const calculatePenalty = async () => {
    setLoading(true)
    setError("")
    try {
      const result = await apiCall("penalty-calculator", {
        tax_year: taxYear,
        filing_deadline: filingDeadline,
        actual_filing_date: actualFilingDate || null,
        tax_owed: taxOwed,
        was_extension_filed: extensionFiled,
        reasonable_cause: reasonableCause,
      })
      setPenaltyResult(result)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const addIncomeItem = () => {
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
    ])
  }

  const updateIncomeItem = (index: number, field: string, value: any) => {
    const updated = [...incomeItems]
    updated[index] = { ...updated[index], [field]: value }
    setIncomeItems(updated)
  }

  const removeIncomeItem = (index: number) => {
    setIncomeItems(incomeItems.filter((_, i) => i !== index))
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Form 1040-NR</h1>
        <p className="text-muted-foreground">
          Non-Resident Alien Tax Return - Resident-Status-Test, US-Sourced Income, Chapter 3/4 Withholding
        </p>
      </div>

      <div className="mb-6">
        <Label htmlFor="tax_year">Steuerjahr</Label>
        <Input
          id="tax_year"
          type="number"
          value={taxYear}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTaxYear(parseInt(e.target.value))}
          className="w-40"
        />
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="filing-requirement">
            <FileText className="w-4 h-4 mr-2" />
            Filing Requirement
          </TabsTrigger>
          <TabsTrigger value="income-summary">
            <DollarSign className="w-4 h-4 mr-2" />
            Income Summary
          </TabsTrigger>
          <TabsTrigger value="withholding">
            <Calculator className="w-4 h-4 mr-2" />
            Withholding Credits
          </TabsTrigger>
          <TabsTrigger value="penalties">
            <AlertTriangle className="w-4 h-4 mr-2" />
            Penalty Calculator
          </TabsTrigger>
        </TabsList>

        {/* Filing Requirement Tab */}
        <TabsContent value="filing-requirement">
          <Card>
            <CardHeader>
              <CardTitle>Resident Status & Filing Requirement Test</CardTitle>
              <CardDescription>
                Substantial Presence Test (SPT), Treaty Tiebreaker, Filing Thresholds
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Tage in USA (aktuelles Jahr)</Label>
                  <Input
                    type="number"
                    value={daysCurrentYear}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDaysCurrentYear(parseInt(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <Label>Tage in USA (Vorjahr 1)</Label>
                  <Input
                    type="number"
                    value={daysPriorYear1}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDaysPriorYear1(parseInt(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <Label>Tage in USA (Vorjahr 2)</Label>
                  <Input
                    type="number"
                    value={daysPriorYear2}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDaysPriorYear2(parseInt(e.target.value) || 0)}
                  />
                </div>
              </div>

              <div>
                <Label>Treaty Country (optional)</Label>
                <Input
                  value={treatyCountry}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTreatyCountry(e.target.value)}
                  placeholder="z.B. Germany, India, China"
                />
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Checkbox checked={isStudent} onCheckedChange={(c: boolean) => setIsStudent(c)} />
                  <Label>Student</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox checked={isTeacher} onCheckedChange={(c: boolean) => setIsTeacher(c)} />
                  <Label>Teacher</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox checked={hasUSIncome} onCheckedChange={(c: boolean) => setHasUSIncome(c)} />
                  <Label>US-Sourced Income</Label>
                </div>
              </div>

              <div>
                <Label>Gross Income</Label>
                <Input
                  type="number"
                  value={grossIncome}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setGrossIncome(parseFloat(e.target.value) || 0)}
                />
              </div>

              <Button onClick={checkFilingRequirement} disabled={loading}>
                {loading ? "Prüfe..." : "Filing Requirement prüfen"}
              </Button>

              {filingResult && (
                <div className="mt-4 space-y-4">
                  <Alert variant={filingResult.must_file ? "default" : "destructive"}>
                    {filingResult.must_file ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <AlertCircle className="h-4 w-4" />
                    )}
                    <AlertDescription>
                      <strong>
                        {filingResult.must_file ? "FILING REQUIRED" : "NO FILING REQUIRED"}
                      </strong>
                    </AlertDescription>
                  </Alert>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <strong>Resident Status:</strong> {filingResult.resident_status}
                    </div>
                    <div>
                      <strong>Substantial Presence Days:</strong> {filingResult.substantial_presence_days}
                    </div>
                    <div>
                      <strong>Passes SPT:</strong>{" "}
                      {filingResult.passes_substantial_presence_test ? "Yes" : "No"}
                    </div>
                    <div>
                      <strong>Treaty Exemption:</strong>{" "}
                      {filingResult.treaty_exemption_applies ? "Yes" : "No"}
                    </div>
                    <div>
                      <strong>Filing Deadline:</strong> {filingResult.filing_deadline}
                    </div>
                    <div>
                      <strong>Extension Deadline:</strong> {filingResult.extension_deadline}
                    </div>
                  </div>

                  <div>
                    <strong>Reasoning:</strong>
                    <p className="text-sm text-muted-foreground">{filingResult.reasoning}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Income Summary Tab */}
        <TabsContent value="income-summary">
          <Card>
            <CardHeader>
              <CardTitle>Income Summary (ECI vs FDAP)</CardTitle>
              <CardDescription>
                Effectively Connected Income (progressive) vs Fixed, Determinable, Annual, Periodic (30%)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                {incomeItems.map((item, index) => (
                  <div key={index} className="border p-4 rounded space-y-2">
                    <div className="grid grid-cols-4 gap-2">
                      <Input
                        placeholder="Beschreibung"
                        value={item.description}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateIncomeItem(index, "description", e.target.value)}
                      />
                      <Select
                        value={item.income_type}
                        onValueChange={(v: string) => updateIncomeItem(index, "income_type", v)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="eci">ECI</SelectItem>
                          <SelectItem value="fdap">FDAP</SelectItem>
                          <SelectItem value="capital_gains">Capital Gains</SelectItem>
                          <SelectItem value="rental">Rental</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                      <Input
                        type="number"
                        placeholder="Betrag"
                        value={item.gross_amount}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          updateIncomeItem(index, "gross_amount", parseFloat(e.target.value) || 0)
                        }
                      />
                      <Input
                        type="number"
                        placeholder="Withheld"
                        value={item.withheld_amount}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          updateIncomeItem(index, "withheld_amount", parseFloat(e.target.value) || 0)
                        }
                      />
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={item.us_sourced}
                          onCheckedChange={(c: boolean) => updateIncomeItem(index, "us_sourced", c)}
                        />
                        <Label>US-Sourced</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={item.treaty_exempt}
                          onCheckedChange={(c: boolean) => updateIncomeItem(index, "treaty_exempt", c)}
                        />
                        <Label>Treaty Exempt</Label>
                      </div>
                      <Button variant="destructive" size="sm" onClick={() => removeIncomeItem(index)}>
                        Entfernen
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              <Button variant="outline" onClick={addIncomeItem}>
                + Income Item hinzufügen
              </Button>

              <div className="border-t pt-4">
                <div className="flex items-center space-x-2 mb-4">
                  <Checkbox
                    checked={useStandardDeduction}
                    onCheckedChange={(c: boolean) => setUseStandardDeduction(c)}
                  />
                  <Label>Standard Deduction verwenden ($14,600)</Label>
                </div>

                {!useStandardDeduction && (
                  <div>
                    <Label>Itemized Deductions</Label>
                    <Input
                      type="number"
                      value={itemizedDeductions}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setItemizedDeductions(parseFloat(e.target.value) || 0)}
                    />
                  </div>
                )}
              </div>

              <Button onClick={calculateIncomeSummary} disabled={loading || incomeItems.length === 0}>
                {loading ? "Berechne..." : "Income Summary berechnen"}
              </Button>

              {incomeSummary && (
                <div className="mt-4 border p-4 rounded space-y-2 bg-muted">
                  <h3 className="font-bold">Ergebnis</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <strong>Total ECI:</strong> ${incomeSummary.total_eci}
                    </div>
                    <div>
                      <strong>Total FDAP:</strong> ${incomeSummary.total_fdap}
                    </div>
                    <div>
                      <strong>Capital Gains:</strong> ${incomeSummary.total_capital_gains}
                    </div>
                    <div>
                      <strong>US-Sourced:</strong> ${incomeSummary.total_us_sourced}
                    </div>
                    <div>
                      <strong>Foreign-Sourced:</strong> ${incomeSummary.total_foreign_sourced}
                    </div>
                    <div>
                      <strong>Treaty Exempt:</strong> ${incomeSummary.total_treaty_exempt}
                    </div>
                    <div>
                      <strong>Taxable ECI:</strong> ${incomeSummary.taxable_eci}
                    </div>
                    <div>
                      <strong>Taxable FDAP:</strong> ${incomeSummary.taxable_fdap}
                    </div>
                    <div>
                      <strong>Standard Deduction:</strong> ${incomeSummary.standard_deduction}
                    </div>
                    <div>
                      <strong>Itemized Deductions:</strong> ${incomeSummary.itemized_deductions}
                    </div>
                    <div className="col-span-2 pt-2 border-t">
                      <strong className="text-lg">Total Tax:</strong>{" "}
                      <span className="text-lg font-bold">
                        ${incomeSummary.total_tax_before_credits}
                      </span>
                    </div>
                    <div className="col-span-2">
                      <strong>Effective Rate:</strong> {incomeSummary.effective_rate}%
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Withholding Credits Tab */}
        <TabsContent value="withholding">
          <Card>
            <CardHeader>
              <CardTitle>Withholding Tax Credits</CardTitle>
              <CardDescription>Chapter 3, Chapter 4 (FATCA), Backup Withholding</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Chapter 3 Withheld (30%)</Label>
                  <Input
                    type="number"
                    value={chapter3Withheld}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setChapter3Withheld(parseFloat(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <Label>Chapter 4 Withheld (FATCA)</Label>
                  <Input
                    type="number"
                    value={chapter4Withheld}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setChapter4Withheld(parseFloat(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <Label>Backup Withholding</Label>
                  <Input
                    type="number"
                    value={backupWithheld}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setBackupWithheld(parseFloat(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <Label>Estimated Tax Paid</Label>
                  <Input
                    type="number"
                    value={estimatedTax}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEstimatedTax(parseFloat(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <Label>Prior Year Overpayment</Label>
                  <Input
                    type="number"
                    value={priorYearOverpayment}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPriorYearOverpayment(parseFloat(e.target.value) || 0)}
                  />
                </div>
              </div>

              <Button onClick={calculateWithholding} disabled={loading}>
                {loading ? "Berechne..." : "Withholding Credits berechnen"}
              </Button>

              {withholdingResult && (
                <div className="mt-4 border p-4 rounded space-y-2 bg-muted">
                  <h3 className="font-bold">Credits</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <strong>Chapter 3 Credit:</strong> ${withholdingResult.total_chapter_3_credit}
                    </div>
                    <div>
                      <strong>Chapter 4 Credit:</strong> ${withholdingResult.total_chapter_4_credit}
                    </div>
                    <div>
                      <strong>Backup Credit:</strong> ${withholdingResult.total_backup_credit}
                    </div>
                    <div>
                      <strong>Estimated Tax:</strong> ${withholdingResult.total_estimated_tax}
                    </div>
                    <div className="col-span-2 pt-2 border-t">
                      <strong className="text-lg">Total Credits:</strong>{" "}
                      <span className="text-lg font-bold">${withholdingResult.total_credits}</span>
                    </div>
                    <div>
                      <strong>Refundable:</strong> ${withholdingResult.refundable_amount}
                    </div>
                    <div>
                      <strong>Non-Refundable:</strong> ${withholdingResult.non_refundable_amount}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Penalty Calculator Tab */}
        <TabsContent value="penalties">
          <Card>
            <CardHeader>
              <CardTitle>Penalty Calculator (§6072)</CardTitle>
              <CardDescription>
                Late Filing (5%/month), Late Payment (0.5%/month), Interest (8%/year)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Filing Deadline</Label>
                  <Input
                    type="date"
                    value={filingDeadline}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFilingDeadline(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Actual Filing Date (optional)</Label>
                  <Input
                    type="date"
                    value={actualFilingDate}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setActualFilingDate(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Tax Owed</Label>
                  <Input
                    type="number"
                    value={taxOwed}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTaxOwed(parseFloat(e.target.value) || 0)}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    checked={extensionFiled}
                    onCheckedChange={(c: boolean) => setExtensionFiled(c)}
                  />
                  <Label>Extension Filed</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    checked={reasonableCause}
                    onCheckedChange={(c: boolean) => setReasonableCause(c)}
                  />
                  <Label>Reasonable Cause</Label>
                </div>
              </div>

              <Button onClick={calculatePenalty} disabled={loading || !filingDeadline}>
                {loading ? "Berechne..." : "Penalties berechnen"}
              </Button>

              {penaltyResult && (
                <div className="mt-4 border p-4 rounded space-y-2 bg-muted">
                  <h3 className="font-bold">Penalty Breakdown</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <strong>Days Late:</strong> {penaltyResult.days_late}
                    </div>
                    <div>
                      <strong>Late Filing Penalty:</strong> ${penaltyResult.late_filing_penalty}
                    </div>
                    <div>
                      <strong>Late Payment Penalty:</strong> ${penaltyResult.late_payment_penalty}
                    </div>
                    <div>
                      <strong>Interest Charges:</strong> ${penaltyResult.interest_charges}
                    </div>
                    <div className="col-span-2 pt-2 border-t">
                      <strong className="text-lg">Total Penalties:</strong>{" "}
                      <span className="text-lg font-bold">${penaltyResult.total_penalties}</span>
                    </div>
                    <div className="col-span-2">
                      <strong>Total Amount Due:</strong> ${penaltyResult.total_amount_due}
                    </div>
                    {penaltyResult.minimum_penalty_applies && (
                      <div className="col-span-2">
                        <Alert>
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>
                            Minimum penalty of ${penaltyResult.minimum_penalty_amount} applies
                          </AlertDescription>
                        </Alert>
                      </div>
                    )}
                    {penaltyResult.waived_due_to_reasonable_cause && (
                      <div className="col-span-2">
                        <Alert>
                          <CheckCircle className="h-4 w-4" />
                          <AlertDescription>
                            Penalties waived due to reasonable cause (interest remains)
                          </AlertDescription>
                        </Alert>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
