"""
Modul 3 - US-DE Steuerlogik-Engine.

WICHTIG: Dieses Modul enthält KEINE LLM-Aufrufe. Jede Berechnung ist
deterministisch, nachvollziehbar und unit-testbar. Alle Geldbeträge
werden als sympy.Rational geführt, um Floating-Point-Rundungsfehler
bei Steuerbeträgen kategorisch auszuschließen.

Regelwerk (vereinfachtes Modell, Stand: allgemeine IRS-Logik für
Auslands-Amerikaner; ersetzt KEINE Steuerberatung):

  - Foreign Tax Credit (FTC / Form 1116) ist der Standard-Pfad ("Fast
    Path"), weil FTC im Gegensatz zu FEIE das Refundable Child Tax
    Credit (CTC) NICHT sperrt (Additional CTC bleibt zugänglich,
    solange Earned Income > 0 und FEIE nicht gleichzeitig für dasselbe
    Einkommen beansprucht wird).
  - Foreign Earned Income Exclusion (FEIE / Form 2555) wird PARALLEL
    berechnet (zum Vergleich / für Fälle ohne Kinder oder bei sehr
    niedriger US-Steuerlast), aber nur als expliziter Fallback genutzt,
    niemals automatisch bevorzugt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

import sympy as sp

# ---------------------------------------------------------------------------
# Konstanten (Steuerjahr-abhängig -> in Produktion aus versionierter
# JSON/YAML-Konfigurationsdatei pro Steuerjahr laden, NICHT hardcoden;
# hier als benannte Konstanten für Nachvollziehbarkeit im Code selbst).
# ---------------------------------------------------------------------------

FEIE_MAX_EXCLUSION_USD = sp.Integer(126_500)   # Beispielwert, jahresabhängig
CTC_PER_CHILD_USD = sp.Integer(2_000)
ACTC_REFUNDABLE_CAP_PER_CHILD_USD = sp.Integer(1_700)
FBAR_THRESHOLD_USD = sp.Integer(10_000)
FORM8938_THRESHOLD_USD = sp.Integer(200_000)


class TaxPath(str, Enum):
    FTC = "FTC_FORM_1116"       # Fast Path (Standard)
    FEIE = "FEIE_FORM_2555"     # Fallback


class IncomeCategory(str, Enum):
    """
    IRC Sec. 904(d) Einkommenskategorien ("Separate Limitation Income
    Categories"). Für den Auslands-Expat-Fall relevant sind primär:
      - GENERAL: aktives Erwerbseinkommen (Lohn, Gehalt, Selbständigkeit)
      - PASSIVE: passive Kapitalerträge (Zinsen, Dividenden, gewisse
        Veräußerungsgewinne)
    Weitere §904-Kategorien (z.B. "Section 901(j) income", "Certain
    income re-sourced by treaty") sind hier bewusst NICHT modelliert -
    das wäre über-vereinfachend fehlerhaft; wird als expliziter
    ValueError abgefangen, statt stillschweigend falsch zuzuordnen.
    """
    GENERAL = "general_category_income"
    PASSIVE = "passive_category_income"


@dataclass(frozen=True)
class TaxpayerInput:
    foreign_earned_income_usd: sp.Rational
    german_income_tax_paid_usd: sp.Rational  # bereits in USD umgerechnet
    us_tax_liability_before_credits_usd: sp.Rational
    num_qualifying_children: int
    filing_status: str = "MFJ"  # Married Filing Jointly / Single / etc.


@dataclass(frozen=True)
class PathResult:
    path: TaxPath
    credit_or_exclusion_amount_usd: sp.Rational
    resulting_us_tax_liability_usd: sp.Rational
    ctc_unlocked: bool
    actc_refundable_amount_usd: sp.Rational
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EngineResult:
    ftc_result: PathResult
    feie_result: PathResult
    recommended_path: TaxPath
    recommendation_reason: str


def _to_rational(value) -> sp.Rational:
    """Erzwingt exakte Rationalzahlen-Arithmetik, keine floats."""
    if isinstance(value, sp.Rational):
        return value
    if isinstance(value, (int, str, Decimal)):
        return sp.Rational(str(value))
    raise TypeError(f"Unerwarteter Typ für Geldbetrag: {type(value)}")


def compute_ftc_path(inp: TaxpayerInput) -> PathResult:
    """
    Foreign Tax Credit (Form 1116): Anrechnung der in Deutschland
    gezahlten Einkommensteuer auf die US-Steuerschuld, begrenzt auf
    die anteilige US-Steuer auf das ausländische Einkommen (Limitation).
    """
    german_tax = _to_rational(inp.german_income_tax_paid_usd)
    us_tax_before = _to_rational(inp.us_tax_liability_before_credits_usd)

    # FTC-Limitation vereinfachtes Modell:
    # Credit <= min(gezahlte ausländische Steuer, US-Steuer vor Credits)
    credit = sp.Min(german_tax, us_tax_before)
    resulting_tax = sp.Max(sp.Integer(0), us_tax_before - credit)

    notes = [
        "FTC lässt Earned Income für CTC-Zwecke vollständig 'aktiv', "
        "da kein Teil des Einkommens ausgeschlossen wird.",
    ]

    ctc_unlocked = inp.num_qualifying_children > 0
    actc_refundable = sp.Integer(0)
    if ctc_unlocked:
        # ACTC ist gedeckelt pro Kind UND durch 15% des Earned Income
        # oberhalb einer Freigrenze (hier vereinfacht: nur Cap pro Kind).
        actc_refundable = sp.Min(
            ACTC_REFUNDABLE_CAP_PER_CHILD_USD * inp.num_qualifying_children,
            CTC_PER_CHILD_USD * inp.num_qualifying_children,
        )
        notes.append(
            f"Additional Child Tax Credit (refundable) bis zu "
            f"{actc_refundable} USD verfügbar, da FTC-Pfad gewählt."
        )

    return PathResult(
        path=TaxPath.FTC,
        credit_or_exclusion_amount_usd=credit,
        resulting_us_tax_liability_usd=resulting_tax,
        ctc_unlocked=ctc_unlocked,
        actc_refundable_amount_usd=actc_refundable,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# IRC Sec. 904 - Kategorie-isolierte FTC-Limitation (General vs. Passive)
# ---------------------------------------------------------------------------
#
# ANTI-REWARD-HACKING-PRINZIP: Die Isolation wird NICHT durch eine
# nachträgliche Prüfung erzwungen, sondern strukturell dadurch, dass
# jede Kategorie ihre eigene Limitation und ihren eigenen Credit in
# einem eigenen, unveränderlichen CategoryLimitationResult erhält.
# Es existiert an keiner Stelle im Code ein gemeinsamer "Topf", aus
# dem eine Kategorie den Spielraum einer anderen ausleihen könnte.
# Ein Excess-Foreign-Tax-Betrag einer Kategorie (z.B. hohe deutsche
# Kapitalertragsteuer auf Zinsen, die die passive Limitation
# übersteigt) verfällt für DIESES Jahr in DIESER Kategorie - er wird
# NICHT automatisch gegen eine General-Category-Unterauslastung
# verrechnet (reale Carryback/Carryover-Regeln nach §904(c) sind
# hier bewusst nicht implementiert, siehe Hinweis in der Klasse unten).
# ---------------------------------------------------------------------------


class CategoryIsolationError(ValueError):
    """
    Wird geworfen, wenn ein Aufruf strukturell versucht, die §904-
    Kategorie-Trennung zu umgehen - z.B. doppelte Kategorie-Einträge
    (Pooling-Versuch) oder eine Dateninkonsistenz, die eine korrekte
    isolierte Limitation unmöglich macht.
    """


@dataclass(frozen=True)
class CategoryFinancials:
    category: IncomeCategory
    foreign_source_taxable_income_usd: sp.Rational
    foreign_tax_paid_usd: sp.Rational


@dataclass(frozen=True)
class CategoryLimitationResult:
    category: IncomeCategory
    foreign_source_taxable_income_usd: sp.Rational
    foreign_tax_paid_usd: sp.Rational
    section_904_limitation_usd: sp.Rational
    prior_carryover_available_usd: sp.Rational
    current_year_credit_used_usd: sp.Rational
    carryover_used_this_year_usd: sp.Rational
    allowed_credit_usd: sp.Rational  # = current_year_credit_used + carryover_used
    remaining_prior_carryovers_usd: sp.Rational  # ungenutzter Rest aus Vorjahren
    generated_carryover_for_next_year_usd: sp.Rational  # neuer Excess dieses Jahr


@dataclass(frozen=True)
class MultiCategoryFTCResult:
    category_results: tuple[CategoryLimitationResult, ...]
    total_allowed_credit_usd: sp.Rational
    resulting_us_tax_liability_usd: sp.Rational
    ctc_unlocked: bool
    actc_refundable_amount_usd: sp.Rational
    notes: list[str] = field(default_factory=list)


def _validate_categories(
    categories: list[CategoryFinancials],
    total_taxable_income_usd: sp.Rational,
    prior_year_carryovers: dict[IncomeCategory, sp.Rational],
) -> None:
    """Harte Vorbedingungen. Fail-Closed statt stillschweigend falsch rechnen."""
    seen: set[IncomeCategory] = set()
    for cat in categories:
        if cat.category in seen:
            raise CategoryIsolationError(
                f"Kategorie '{cat.category.value}' wurde mehrfach übergeben. "
                "Das Pooling zweier Einträge derselben §904-Kategorie in "
                "getrennten Positionen ist nicht zulässig - fasse sie vor "
                "dem Aufruf zu EINEM CategoryFinancials-Eintrag zusammen, "
                "sonst würde effektiv eine Kategorie zweimal limitiert "
                "und könnte (je nach Aufrufer-Logik) Excess-Beträge "
                "verdecken."
            )
        seen.add(cat.category)

        if cat.foreign_source_taxable_income_usd < 0:
            raise CategoryIsolationError(
                f"Negatives Auslandseinkommen in Kategorie "
                f"'{cat.category.value}' ist nicht zulässig."
            )
        if cat.foreign_tax_paid_usd < 0:
            raise CategoryIsolationError(
                f"Negative gezahlte Auslandssteuer in Kategorie "
                f"'{cat.category.value}' ist nicht zulässig."
            )

    income_sum = sum(
        (cat.foreign_source_taxable_income_usd for cat in categories),
        start=sp.Integer(0),
    )
    if income_sum > total_taxable_income_usd:
        raise CategoryIsolationError(
            f"Summe der Kategorie-Auslandseinkommen ({income_sum} USD) "
            f"übersteigt das angegebene Gesamt-Welteinkommen "
            f"({total_taxable_income_usd} USD). Das würde §904-Limitations-"
            "Verhältnisse > 1 erzeugen und ist ein Datenintegritätsfehler, "
            "keine gültige Steuersituation."
        )
    if total_taxable_income_usd <= 0 and income_sum > 0:
        raise CategoryIsolationError(
            "Gesamt-Welteinkommen ist <= 0, obwohl Kategorie-Einkommen "
            "vorhanden ist - Division für die §904-Ratio nicht definierbar."
        )

    # --- Carryover-spezifische Isolations-Guards ---------------------------
    for carryover_category, amount in prior_year_carryovers.items():
        if amount < 0:
            raise CategoryIsolationError(
                f"Negativer Carryover-Betrag für Kategorie "
                f"'{carryover_category.value}' ist nicht zulässig."
            )
        if carryover_category not in seen:
            raise CategoryIsolationError(
                f"Carryover für Kategorie '{carryover_category.value}' "
                "übergeben, aber diese Kategorie hat dieses Jahr keinen "
                "CategoryFinancials-Eintrag. Ein Carryover ohne "
                "zugehörige Kategorie-Limitation dieses Jahr kann nicht "
                "isoliert verrechnet werden - übergib mindestens einen "
                "Eintrag mit foreign_source_taxable_income_usd=0, "
                "foreign_tax_paid_usd=0 für diese Kategorie, falls dieses "
                "Jahr kein Einkommen dieser Kategorie vorlag (die "
                "Limitation ist dann 0, und der Carryover bleibt "
                "unangetastet als remaining_prior_carryovers erhalten)."
            )


def compute_ftc_by_category(
    categories: list[CategoryFinancials],
    total_taxable_income_usd,
    us_tax_liability_before_credits_usd,
    num_qualifying_children: int = 0,
    prior_year_carryovers: dict[IncomeCategory, object] | None = None,
) -> MultiCategoryFTCResult:
    """
    Berechnet den Foreign Tax Credit nach IRC Sec. 904 mit strikt
    isolierter Limitation pro Einkommenskategorie, inklusive §904(c)
    Carryover-Verrechnung (vereinfacht: EIN aggregierter Carryover-Pool
    pro Kategorie statt einer nach Entstehungsjahr gestaffelten FIFO-
    Queue mit 1-Jahr-Carryback / 10-Jahre-Carryforward-Verfall - das
    ist eine bewusste Vereinfachung für diese Iteration, siehe Hinweis
    unten).

    Verrechnungsreihenfolge pro Kategorie (§904(c)-Grundprinzip):
      1. Diesjährige Auslandssteuer wird zuerst bis zur Limitation
         angerechnet: current_year_credit = min(foreign_tax_paid, limitation)
      2. Verbleibender Spielraum ("Slack") = limitation - current_year_credit
      3. Der Slack wird MIT DEM CARRYOVER DERSELBEN KATEGORIE aufgefüllt
         (niemals mit einer anderen Kategorie): carryover_used = min(
         verfügbarer Carryover, Slack)
      4. Gesamt-Credit der Kategorie = current_year_credit + carryover_used
         (bleibt per Konstruktion <= limitation)
      5. Übersteigt die diesjährige Auslandssteuer die Limitation, entsteht
         ein NEUER Carryover für Folgejahre (generated_carryover_for_next_year).

    BEKANNTE VEREINFACHUNG (für Iteration 4 vorgemerkt): Die reale
    §904(c)-Regel erlaubt Carryback 1 Jahr zurück und Carryforward bis
    zu 10 Jahre, mit Verfall nach Ablauf und FIFO-Verbrauch nach
    Entstehungsjahr. Dieses Modul führt nur EINEN aggregierten Saldo
    pro Kategorie, ohne Alters-Tracking oder automatischen Verfall nach
    10 Jahren - eine Steuerberater-Prüfung bei sehr alten Carryovers
    bleibt bis zur nächsten Iteration erforderlich.
    """
    total_income = _to_rational(total_taxable_income_usd)
    us_tax_before = _to_rational(us_tax_liability_before_credits_usd)

    normalized_categories = [
        CategoryFinancials(
            category=cat.category,
            foreign_source_taxable_income_usd=_to_rational(cat.foreign_source_taxable_income_usd),
            foreign_tax_paid_usd=_to_rational(cat.foreign_tax_paid_usd),
        )
        for cat in categories
    ]

    normalized_carryovers: dict[IncomeCategory, sp.Rational] = {
        cat: _to_rational(amount)
        for cat, amount in (prior_year_carryovers or {}).items()
    }

    _validate_categories(normalized_categories, total_income, normalized_carryovers)

    category_results: list[CategoryLimitationResult] = []
    for cat in normalized_categories:
        if total_income == 0:
            limitation = sp.Integer(0)
        else:
            limitation = us_tax_before * (
                cat.foreign_source_taxable_income_usd / total_income
            )

        prior_carryover_available = normalized_carryovers.get(
            cat.category, sp.Integer(0)
        )

        # Schritt 1: diesjährige Auslandssteuer zuerst.
        current_year_credit = sp.Min(cat.foreign_tax_paid_usd, limitation)

        # Schritt 2+3: Slack MIT DEM CARRYOVER DERSELBEN KATEGORIE auffüllen.
        # Kein Zugriff auf normalized_carryovers[andere_kategorie] möglich,
        # da hier ausschließlich cat.category als Schlüssel verwendet wird -
        # das ist die strukturelle Isolations-Garantie für den Carryover-Pfad.
        slack = sp.Max(sp.Integer(0), limitation - current_year_credit)
        carryover_used = sp.Min(prior_carryover_available, slack)

        total_category_credit = current_year_credit + carryover_used
        remaining_prior_carryover = prior_carryover_available - carryover_used

        # Schritt 5: neuer Excess entsteht nur, wenn diesjährige Steuer
        # die Limitation übersteigt (dann ist slack=0, carryover_used=0).
        generated_carryover = sp.Max(
            sp.Integer(0), cat.foreign_tax_paid_usd - limitation
        )

        category_results.append(
            CategoryLimitationResult(
                category=cat.category,
                foreign_source_taxable_income_usd=cat.foreign_source_taxable_income_usd,
                foreign_tax_paid_usd=cat.foreign_tax_paid_usd,
                section_904_limitation_usd=limitation,
                prior_carryover_available_usd=prior_carryover_available,
                current_year_credit_used_usd=current_year_credit,
                carryover_used_this_year_usd=carryover_used,
                allowed_credit_usd=total_category_credit,
                remaining_prior_carryovers_usd=remaining_prior_carryover,
                generated_carryover_for_next_year_usd=generated_carryover,
            )
        )

    # KEIN gemeinsamer Topf: Summe erst NACH individueller Deckelung
    # (inkl. individuell verrechnetem Carryover pro Kategorie).
    total_credit = sum(
        (r.allowed_credit_usd for r in category_results), start=sp.Integer(0)
    )

    # Sanity-Assertion gegen Reward-Hacking / Implementierungsfehler:
    # Der Gesamt-Credit darf NIE die Summe der Einzel-Limitationen
    # übersteigen - auch nicht mit Carryover, da carryover_used <= slack
    # <= limitation - current_year_credit per Konstruktion gilt.
    total_limitation = sum(
        (r.section_904_limitation_usd for r in category_results), start=sp.Integer(0)
    )
    if total_credit > total_limitation:
        raise CategoryIsolationError(
            "Interner Invarianten-Verstoß: Gesamt-Credit "
            f"({total_credit}) übersteigt die Summe der isolierten "
            f"§904-Limitationen ({total_limitation}). Dies würde "
            "bedeuten, dass Kategorien (oder Carryover-Pools) "
            "quersubventioniert wurden. Übermittlung wird blockiert."
        )

    resulting_tax = sp.Max(sp.Integer(0), us_tax_before - total_credit)

    notes = [
        f"{len(category_results)} §904-Kategorie(n) isoliert berechnet: "
        + ", ".join(r.category.value for r in category_results),
    ]
    for r in category_results:
        if r.carryover_used_this_year_usd > 0:
            notes.append(
                f"Kategorie '{r.category.value}': {r.carryover_used_this_year_usd} USD "
                "Carryover aus Vorjahren genutzt, um die Limitation dieses "
                "Jahr zusätzlich zur laufenden Auslandssteuer auszuschöpfen."
            )
        if r.generated_carryover_for_next_year_usd > 0:
            notes.append(
                f"Kategorie '{r.category.value}': {r.generated_carryover_for_next_year_usd} USD "
                "Auslandssteuer über der Limitation - wird als NEUER "
                "Carryover für Folgejahre vorgemerkt (§904(c), vereinfacht "
                "ohne 10-Jahres-Verfallstracking; manuelle Prüfung "
                "empfohlen, sobald ein Carryover älter als 10 Jahre wird)."
            )
        if r.remaining_prior_carryovers_usd > 0:
            notes.append(
                f"Kategorie '{r.category.value}': {r.remaining_prior_carryovers_usd} USD "
                "Carryover aus Vorjahren bleiben ungenutzt und stehen "
                "grundsätzlich für Folgejahre zur Verfügung."
            )

    ctc_unlocked = num_qualifying_children > 0
    actc_refundable = sp.Integer(0)
    if ctc_unlocked:
        actc_refundable = sp.Min(
            ACTC_REFUNDABLE_CAP_PER_CHILD_USD * num_qualifying_children,
            CTC_PER_CHILD_USD * num_qualifying_children,
        )
        notes.append(
            f"Additional Child Tax Credit (refundable) bis zu "
            f"{actc_refundable} USD verfügbar (FTC-Pfad hält Earned "
            "Income vollständig aktiv)."
        )

    return MultiCategoryFTCResult(
        category_results=tuple(category_results),
        total_allowed_credit_usd=total_credit,
        resulting_us_tax_liability_usd=resulting_tax,
        ctc_unlocked=ctc_unlocked,
        actc_refundable_amount_usd=actc_refundable,
        notes=notes,
    )


def compute_feie_path(inp: TaxpayerInput) -> PathResult:
    """
    Foreign Earned Income Exclusion (Form 2555): Schließt bis zu
    FEIE_MAX_EXCLUSION_USD des Auslandseinkommens von der US-Besteuerung
    aus. WICHTIG: Sobald FEIE für einen Einkommensteil gewählt wird,
    kann für DENSELBEN Einkommensteil kein FTC mehr beansprucht werden,
    UND das ausgeschlossene Einkommen zählt i.d.R. nicht mehr als
    "Earned Income" für die refundable ACTC-Berechnung -> ACTC wird
    faktisch gesperrt, wenn das gesamte Einkommen ausgeschlossen ist.
    """
    income = _to_rational(inp.foreign_earned_income_usd)
    us_tax_before = _to_rational(inp.us_tax_liability_before_credits_usd)

    exclusion = sp.Min(income, FEIE_MAX_EXCLUSION_USD)
    remaining_taxable_ratio = (
        (income - exclusion) / income if income > 0 else sp.Integer(0)
    )
    # Vereinfachte proportionale Reduktion der US-Steuerschuld
    resulting_tax = sp.Max(sp.Integer(0), us_tax_before * remaining_taxable_ratio)

    fully_excluded = exclusion >= income
    ctc_unlocked = inp.num_qualifying_children > 0 and not fully_excluded
    actc_refundable = sp.Integer(0)

    notes = [
        f"FEIE schließt {exclusion} USD des Auslandseinkommens aus.",
    ]
    if fully_excluded:
        notes.append(
            "WARNUNG: Gesamtes Einkommen ausgeschlossen -> kein "
            "'Earned Income' übrig -> refundable ACTC gesperrt (0 USD)."
        )
    elif ctc_unlocked:
        actc_refundable = sp.Min(
            ACTC_REFUNDABLE_CAP_PER_CHILD_USD * inp.num_qualifying_children,
            CTC_PER_CHILD_USD * inp.num_qualifying_children,
        )

    return PathResult(
        path=TaxPath.FEIE,
        credit_or_exclusion_amount_usd=exclusion,
        resulting_us_tax_liability_usd=resulting_tax,
        ctc_unlocked=ctc_unlocked,
        actc_refundable_amount_usd=actc_refundable,
        notes=notes,
    )


def evaluate(inp: TaxpayerInput) -> EngineResult:
    """
    Kern-Entscheidungsfunktion: FTC ist IMMER der Standard-Pfad (Fast
    Path), außer die resultierende US-Steuerschuld unter FEIE ist
    strikt niedriger UND es gibt keine Kinder (sonst würde FEIE den
    ACTC kappen, was i.d.R. den Netto-Vorteil zunichtemacht).
    """
    ftc = compute_ftc_path(inp)
    feie = compute_feie_path(inp)

    ftc_net_benefit = ftc.resulting_us_tax_liability_usd - ftc.actc_refundable_amount_usd
    feie_net_benefit = feie.resulting_us_tax_liability_usd - feie.actc_refundable_amount_usd

    if inp.num_qualifying_children > 0:
        # Kinder vorhanden -> FTC bleibt Fast Path, es sei denn FEIE
        # ist auch NACH ACTC-Verlust klar günstiger.
        if feie_net_benefit < ftc_net_benefit:
            recommended = TaxPath.FEIE
            reason = (
                "FEIE führt trotz ACTC-Sperre zu einer niedrigeren "
                "Netto-Belastung als FTC in diesem Fall."
            )
        else:
            recommended = TaxPath.FTC
            reason = (
                "Standard-Pfad: FTC hält den (Additional) Child Tax "
                "Credit zugänglich; FEIE würde ihn sperren."
            )
    else:
        recommended = TaxPath.FTC if ftc_net_benefit <= feie_net_benefit else TaxPath.FEIE
        reason = "Keine Kinder -> reiner Vergleich der resultierenden US-Steuerschuld."

    return EngineResult(
        ftc_result=ftc,
        feie_result=feie,
        recommended_path=recommended,
        recommendation_reason=reason,
    )


# ---------------------------------------------------------------------------
# Form 8802 (US-Residency-Zertifizierung) - dynamische Datengenerierung
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Form8802Data:
    applicant_name: str
    tax_year: int
    us_address: str
    purpose_country: str = "Germany"
    treaty_article_reference: str = "US-Germany Income Tax Treaty"


def build_form_8802_payload(
    applicant_name: str,
    tax_year: int,
    us_address: str,
) -> Form8802Data:
    """
    Erstellt die strukturierten Felddaten für Form 8802. Reine
    Datentransformation, keine Steuerbewertung -> deterministisch.
    """
    if not applicant_name.strip():
        raise ValueError("applicant_name darf nicht leer sein.")
    if tax_year < 2000 or tax_year > 2100:
        raise ValueError(f"Unplausibles Steuerjahr: {tax_year}")

    return Form8802Data(
        applicant_name=applicant_name.strip(),
        tax_year=tax_year,
        us_address=us_address.strip(),
    )


# ---------------------------------------------------------------------------
# FBAR / FATCA (Form 8938) Compliance-Flags - deterministische State-Machine
# (wird von Modul 4 / Chat-Assistent read-only konsumiert, siehe
# chat_assistant.py -> compliance_state.py)
# ---------------------------------------------------------------------------

def evaluate_reporting_thresholds(max_account_balance_usd) -> dict:
    balance = _to_rational(max_account_balance_usd)
    return {
        "fbar_required": bool(balance > FBAR_THRESHOLD_USD),
        "form8938_required": bool(balance > FORM8938_THRESHOLD_USD),
        "max_balance_usd": str(balance),
    }
