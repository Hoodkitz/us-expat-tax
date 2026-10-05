"""
Verifizierung der Steuerlogik-Engine. Nichts gilt als korrekt, bevor
diese Tests grün sind (Prinzip: "Verifizierung zuerst").
"""

import sympy as sp
import pytest

from app.modules.logic_engine import (
    TaxpayerInput,
    TaxPath,
    compute_ftc_path,
    compute_feie_path,
    evaluate,
    build_form_8802_payload,
    evaluate_reporting_thresholds,
    IncomeCategory,
    CategoryFinancials,
    CategoryIsolationError,
    compute_ftc_by_category,
)


def test_ftc_credit_capped_at_us_tax_before_credits():
    inp = TaxpayerInput(
        foreign_earned_income_usd=sp.Integer(90_000),
        german_income_tax_paid_usd=sp.Integer(25_000),
        us_tax_liability_before_credits_usd=sp.Integer(15_000),
        num_qualifying_children=0,
    )
    result = compute_ftc_path(inp)
    # Deutsche Steuer (25k) > US-Steuer vor Credits (15k) -> Credit gedeckelt auf 15k
    assert result.credit_or_exclusion_amount_usd == sp.Integer(15_000)
    assert result.resulting_us_tax_liability_usd == sp.Integer(0)


def test_ftc_keeps_ctc_unlocked_with_children():
    inp = TaxpayerInput(
        foreign_earned_income_usd=sp.Integer(90_000),
        german_income_tax_paid_usd=sp.Integer(10_000),
        us_tax_liability_before_credits_usd=sp.Integer(15_000),
        num_qualifying_children=2,
    )
    result = compute_ftc_path(inp)
    assert result.ctc_unlocked is True
    assert result.actc_refundable_amount_usd == sp.Integer(3_400)  # 2 * 1700


def test_feie_full_exclusion_blocks_actc():
    inp = TaxpayerInput(
        foreign_earned_income_usd=sp.Integer(80_000),
        german_income_tax_paid_usd=sp.Integer(10_000),
        us_tax_liability_before_credits_usd=sp.Integer(12_000),
        num_qualifying_children=1,
    )
    result = compute_feie_path(inp)
    assert result.credit_or_exclusion_amount_usd == sp.Integer(80_000)  # < FEIE-Cap
    assert result.resulting_us_tax_liability_usd == sp.Integer(0)
    assert result.ctc_unlocked is False
    assert result.actc_refundable_amount_usd == sp.Integer(0)


def test_recommendation_prefers_ftc_when_children_present_and_close():
    inp = TaxpayerInput(
        foreign_earned_income_usd=sp.Integer(90_000),
        german_income_tax_paid_usd=sp.Integer(12_000),
        us_tax_liability_before_credits_usd=sp.Integer(12_500),
        num_qualifying_children=2,
    )
    engine_result = evaluate(inp)
    assert engine_result.recommended_path == TaxPath.FTC


def test_no_floating_point_used_anywhere():
    inp = TaxpayerInput(
        foreign_earned_income_usd=sp.Rational("90000.33"),
        german_income_tax_paid_usd=sp.Rational("12000.11"),
        us_tax_liability_before_credits_usd=sp.Rational("12500.99"),
        num_qualifying_children=1,
    )
    result = compute_ftc_path(inp)
    assert isinstance(result.credit_or_exclusion_amount_usd, sp.Rational)
    # Exakte Bruch-Arithmetik statt float-Rundung
    assert result.credit_or_exclusion_amount_usd.q != 0


def test_form_8802_rejects_empty_name():
    with pytest.raises(ValueError):
        build_form_8802_payload("", 2025, "123 Main St")


def test_form_8802_valid_payload():
    payload = build_form_8802_payload("Jane Doe", 2025, "123 Main St, Anytown, US")
    assert payload.tax_year == 2025
    assert payload.applicant_name == "Jane Doe"


@pytest.mark.parametrize(
    "balance,expected_fbar,expected_8938",
    [
        (5_000, False, False),
        (10_001, True, False),
        (200_001, True, True),
    ],
)
def test_reporting_thresholds(balance, expected_fbar, expected_8938):
    flags = evaluate_reporting_thresholds(balance)
    assert flags["fbar_required"] is expected_fbar
    assert flags["form8938_required"] is expected_8938


# ---------------------------------------------------------------------------
# IRC Sec. 904 - Kategorie-isolierte FTC-Limitation
# ---------------------------------------------------------------------------

def test_category_isolation_high_german_salary_and_high_capital_gains():
    """
    Kernszenario: hohes deutsches Gehalt (General Category, deutsche
    Steuer UNTER der Limitation -> voller Credit + Slack) plus hohe
    globale Kapitalerträge (Passive Category, ausländische Steuer
    ÜBER der Limitation -> Excess verfällt).

    Der entscheidende Beweis: der Slack aus General darf NICHT den
    Excess aus Passive auffangen. Der Gesamt-Credit muss exakt der
    Summe der zwei UNABHÄNGIG gedeckelten Credits entsprechen -
    nicht min(Gesamt-Auslandssteuer, Gesamt-US-Steuer).
    """
    general = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(120_000),
        foreign_tax_paid_usd=sp.Integer(15_000),  # < eigene Limitation
    )
    passive = CategoryFinancials(
        category=IncomeCategory.PASSIVE,
        foreign_source_taxable_income_usd=sp.Integer(30_000),
        foreign_tax_paid_usd=sp.Integer(20_000),  # >> eigene Limitation (hohe KapESt)
    )
    total_income = sp.Integer(150_000)
    us_tax_before = sp.Integer(25_000)

    result = compute_ftc_by_category(
        categories=[general, passive],
        total_taxable_income_usd=total_income,
        us_tax_liability_before_credits_usd=us_tax_before,
        num_qualifying_children=0,
    )

    general_result = next(r for r in result.category_results if r.category == IncomeCategory.GENERAL)
    passive_result = next(r for r in result.category_results if r.category == IncomeCategory.PASSIVE)

    # General-Limitation = 25000 * 120000/150000 = 20000 -> Credit = min(15000, 20000) = 15000
    assert general_result.section_904_limitation_usd == sp.Integer(20_000)
    assert general_result.allowed_credit_usd == sp.Integer(15_000)
    assert general_result.generated_carryover_for_next_year_usd == sp.Integer(0)

    # Passive-Limitation = 25000 * 30000/150000 = 5000 -> Credit = min(20000, 5000) = 5000
    assert passive_result.section_904_limitation_usd == sp.Integer(5_000)
    assert passive_result.allowed_credit_usd == sp.Integer(5_000)
    assert passive_result.generated_carryover_for_next_year_usd == sp.Integer(15_000)  # verfällt dieses Jahr, wird Carryover

    # ENTSCHEIDENDER TEST: Gesamt-Credit ist 15000 + 5000 = 20000,
    # NICHT min(15000+20000, 25000) = 25000 (das wäre Quersubventionierung).
    assert result.total_allowed_credit_usd == sp.Integer(20_000)
    assert result.total_allowed_credit_usd != sp.Min(
        general.foreign_tax_paid_usd + passive.foreign_tax_paid_usd, us_tax_before
    )
    assert result.resulting_us_tax_liability_usd == sp.Integer(5_000)  # 25000 - 20000


def test_category_isolation_rejects_duplicate_category_pooling():
    """
    Zwei Einträge für dieselbe Kategorie (Pooling-Versuch) müssen
    hart abgelehnt werden - das ist der geforderte Anti-Reward-
    Hacking-Guard.
    """
    general_1 = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(50_000),
        foreign_tax_paid_usd=sp.Integer(5_000),
    )
    general_2 = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(20_000),
        foreign_tax_paid_usd=sp.Integer(10_000),
    )

    with pytest.raises(CategoryIsolationError):
        compute_ftc_by_category(
            categories=[general_1, general_2],
            total_taxable_income_usd=sp.Integer(70_000),
            us_tax_liability_before_credits_usd=sp.Integer(12_000),
        )


def test_category_isolation_rejects_income_sum_exceeding_total():
    """Dateninkonsistenz: Kategorie-Einkommen > Gesamt-Welteinkommen."""
    general = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(100_000),
        foreign_tax_paid_usd=sp.Integer(10_000),
    )
    passive = CategoryFinancials(
        category=IncomeCategory.PASSIVE,
        foreign_source_taxable_income_usd=sp.Integer(60_000),
        foreign_tax_paid_usd=sp.Integer(5_000),
    )

    with pytest.raises(CategoryIsolationError):
        compute_ftc_by_category(
            categories=[general, passive],
            total_taxable_income_usd=sp.Integer(150_000),  # < 100000+60000
            us_tax_liability_before_credits_usd=sp.Integer(20_000),
        )


def test_category_isolation_rejects_negative_amounts():
    bad_category = CategoryFinancials(
        category=IncomeCategory.PASSIVE,
        foreign_source_taxable_income_usd=sp.Integer(-1),
        foreign_tax_paid_usd=sp.Integer(100),
    )
    with pytest.raises(CategoryIsolationError):
        compute_ftc_by_category(
            categories=[bad_category],
            total_taxable_income_usd=sp.Integer(50_000),
            us_tax_liability_before_credits_usd=sp.Integer(5_000),
        )


def test_category_isolation_zero_total_income_with_zero_category_income():
    """Randfall: kein Einkommen überhaupt -> Limitation 0, kein Credit, kein Crash."""
    zero_general = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(0),
        foreign_tax_paid_usd=sp.Integer(0),
    )
    result = compute_ftc_by_category(
        categories=[zero_general],
        total_taxable_income_usd=sp.Integer(0),
        us_tax_liability_before_credits_usd=sp.Integer(0),
    )
    assert result.total_allowed_credit_usd == sp.Integer(0)
    assert result.resulting_us_tax_liability_usd == sp.Integer(0)


def test_category_isolation_single_category_only_general():
    """Nur General Category vorhanden (kein Passive-Einkommen) - Standardfall."""
    general = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(90_000),
        foreign_tax_paid_usd=sp.Integer(18_000),
    )
    result = compute_ftc_by_category(
        categories=[general],
        total_taxable_income_usd=sp.Integer(90_000),
        us_tax_liability_before_credits_usd=sp.Integer(15_000),
        num_qualifying_children=2,
    )
    # Limitation = 15000 * 90000/90000 = 15000 -> Credit = min(18000, 15000) = 15000
    assert result.total_allowed_credit_usd == sp.Integer(15_000)
    assert result.resulting_us_tax_liability_usd == sp.Integer(0)
    assert result.ctc_unlocked is True
    assert result.actc_refundable_amount_usd == sp.Integer(3_400)


def test_category_isolation_exact_rational_arithmetic_no_float_drift():
    """Stellt sicher, dass auch bei krummen Verhältnissen exakt gerechnet wird."""
    general = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Rational("33333.33"),
        foreign_tax_paid_usd=sp.Rational("7000.00"),
    )
    result = compute_ftc_by_category(
        categories=[general],
        total_taxable_income_usd=sp.Rational("100000.00"),
        us_tax_liability_before_credits_usd=sp.Rational("21000.00"),
    )
    limitation = result.category_results[0].section_904_limitation_usd
    assert isinstance(limitation, sp.Rational)
    assert limitation.q != 1 or limitation == sp.nsimplify(limitation)  # bleibt exakter Bruch/Wert, kein Float


# ---------------------------------------------------------------------------
# IRC Sec. 904(c) - Carryover-Tracking über mehrere Steuerjahre
# ---------------------------------------------------------------------------

def test_carryover_multi_year_vector_generation_then_usage():
    """
    Multi-Year-Testvektor (wie gefordert):

    Jahr 1: Hohes DE-Gehalt -> deutsche Steuer übersteigt die Limitation
            -> es entsteht ein Excess-Credit ('General'), der als
            Carryover für Folgejahre vorgemerkt wird.

    Jahr 2: Niedriges DE-Gehalt, aber hohes US-Gehalt (weiterhin
            'General'-Kategorie) -> die Limitation dieses Jahr ist klein
            (da der Anteil des Auslandseinkommens am Gesamteinkommen
            klein ist), aber die diesjährige deutsche Steuer liegt
            UNTER der Limitation -> der entstehende Slack wird mit dem
            Carryover aus Jahr 1 aufgefüllt, sodass die Limitation
            dieses Jahr VOLLSTÄNDIG ausgeschöpft wird (die auf das
            Auslandseinkommen entfallende US-Steuer wird auf 0 gesenkt).

    WICHTIG: "Eliminieren" bezieht sich auf die anteilige US-Steuer
    AUF DAS AUSLANDSEINKOMMEN (= die Limitation), nicht auf die
    gesamte US-Steuerschuld - letztere bleibt bestehen, soweit sie auf
    rein US-amerikanisches Einkommen entfällt. Genau das ist der Sinn
    von §904: FTC darf niemals US-Steuer auf US-Einkommen verringern.
    """
    # --- Jahr 1 --------------------------------------------------------
    general_y1 = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(150_000),
        foreign_tax_paid_usd=sp.Integer(35_000),  # hohe deutsche Steuer
    )
    result_y1 = compute_ftc_by_category(
        categories=[general_y1],
        total_taxable_income_usd=sp.Integer(150_000),
        us_tax_liability_before_credits_usd=sp.Integer(25_000),
        prior_year_carryovers=None,  # kein Carryover aus noch früheren Jahren
    )
    y1_general = result_y1.category_results[0]

    # Limitation = 25000 * 150000/150000 = 25000
    assert y1_general.section_904_limitation_usd == sp.Integer(25_000)
    # Credit dieses Jahr = min(35000, 25000) = 25000
    assert y1_general.current_year_credit_used_usd == sp.Integer(25_000)
    assert y1_general.carryover_used_this_year_usd == sp.Integer(0)  # kein Vorjahres-Carryover vorhanden
    # Excess = 35000 - 25000 = 10000 -> wird zu Carryover für Jahr 2
    assert y1_general.generated_carryover_for_next_year_usd == sp.Integer(10_000)
    assert result_y1.resulting_us_tax_liability_usd == sp.Integer(0)  # 25000 - 25000

    carryover_into_year_2 = {
        IncomeCategory.GENERAL: y1_general.generated_carryover_for_next_year_usd,
    }
    assert carryover_into_year_2[IncomeCategory.GENERAL] == sp.Integer(10_000)

    # --- Jahr 2 ----------------------------------------------------------
    # Niedriges DE-Gehalt (15.000 USD, 2.000 USD deutsche Steuer darauf),
    # aber hohes US-Gehalt -> Gesamteinkommen 200.000 USD, hohe
    # US-Steuerschuld vor Credits (45.000 USD).
    general_y2 = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(15_000),
        foreign_tax_paid_usd=sp.Integer(2_000),
    )
    result_y2 = compute_ftc_by_category(
        categories=[general_y2],
        total_taxable_income_usd=sp.Integer(200_000),
        us_tax_liability_before_credits_usd=sp.Integer(45_000),
        prior_year_carryovers=carryover_into_year_2,
    )
    y2_general = result_y2.category_results[0]

    # Limitation = 45000 * 15000/200000 = 3375
    assert y2_general.section_904_limitation_usd == sp.Integer(3_375)
    # Diesjährige deutsche Steuer (2000) liegt UNTER der Limitation (3375)
    assert y2_general.current_year_credit_used_usd == sp.Integer(2_000)
    # Slack = 3375 - 2000 = 1375 -> aus Carryover (10000 verfügbar) gedeckt
    assert y2_general.prior_carryover_available_usd == sp.Integer(10_000)
    assert y2_general.carryover_used_this_year_usd == sp.Integer(1_375)
    # Gesamt-Credit Kategorie = 2000 + 1375 = 3375 == Limitation (voll ausgeschöpft)
    assert y2_general.allowed_credit_usd == sp.Integer(3_375)
    assert y2_general.allowed_credit_usd == y2_general.section_904_limitation_usd
    # Rest-Carryover für Jahr 3 = 10000 - 1375 = 8625
    assert y2_general.remaining_prior_carryovers_usd == sp.Integer(8_625)
    # Kein neuer Excess dieses Jahr (Steuer < Limitation)
    assert y2_general.generated_carryover_for_next_year_usd == sp.Integer(0)

    # Gesamte US-Steuerschuld sinkt NUR um den kategorie-eigenen Credit,
    # NICHT auf 0 - der Großteil der Steuer entfällt auf US-Einkommen
    # und darf durch FTC nicht berührt werden (Kernprinzip §904).
    assert result_y2.resulting_us_tax_liability_usd == sp.Integer(45_000 - 3_375)
    assert result_y2.resulting_us_tax_liability_usd == sp.Integer(41_625)


def test_carryover_rejects_negative_amount():
    general = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(50_000),
        foreign_tax_paid_usd=sp.Integer(5_000),
    )
    with pytest.raises(CategoryIsolationError):
        compute_ftc_by_category(
            categories=[general],
            total_taxable_income_usd=sp.Integer(50_000),
            us_tax_liability_before_credits_usd=sp.Integer(8_000),
            prior_year_carryovers={IncomeCategory.GENERAL: sp.Integer(-500)},
        )


def test_carryover_rejects_orphaned_category_without_current_year_entry():
    """
    Carryover für PASSIVE übergeben, aber nur GENERAL hat dieses Jahr
    einen CategoryFinancials-Eintrag -> muss hart abgelehnt werden,
    sonst könnte ein Carryover 'im Nichts' verschwinden oder (schlimmer)
    versehentlich falsch zugeordnet werden.
    """
    general = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(50_000),
        foreign_tax_paid_usd=sp.Integer(5_000),
    )
    with pytest.raises(CategoryIsolationError):
        compute_ftc_by_category(
            categories=[general],
            total_taxable_income_usd=sp.Integer(50_000),
            us_tax_liability_before_credits_usd=sp.Integer(8_000),
            prior_year_carryovers={IncomeCategory.PASSIVE: sp.Integer(1_000)},
        )


def test_carryover_cannot_cross_subsidize_between_categories():
    """
    Anti-Reward-Hacking: General hat Slack (könnte einen Carryover
    aufnehmen), aber der verfügbare Carryover liegt in PASSIVE. Der
    General-Slack darf NICHT durch den Passive-Carryover gefüllt
    werden - beide Kategorien müssen jeweils bei 0 Carryover-Nutzung
    für den fremden Pool bleiben.
    """
    general = CategoryFinancials(
        category=IncomeCategory.GENERAL,
        foreign_source_taxable_income_usd=sp.Integer(100_000),
        foreign_tax_paid_usd=sp.Integer(5_000),  # weit unter der Limitation -> viel Slack
    )
    passive = CategoryFinancials(
        category=IncomeCategory.PASSIVE,
        foreign_source_taxable_income_usd=sp.Integer(50_000),
        foreign_tax_paid_usd=sp.Integer(2_000),
    )
    result = compute_ftc_by_category(
        categories=[general, passive],
        total_taxable_income_usd=sp.Integer(150_000),
        us_tax_liability_before_credits_usd=sp.Integer(30_000),
        prior_year_carryovers={IncomeCategory.PASSIVE: sp.Integer(50_000)},
    )
    general_result = next(r for r in result.category_results if r.category == IncomeCategory.GENERAL)
    passive_result = next(r for r in result.category_results if r.category == IncomeCategory.PASSIVE)

    # General hat KEINEN eigenen Carryover -> carryover_used muss 0 sein,
    # obwohl in PASSIVE reichlich Carryover verfügbar wäre.
    assert general_result.prior_carryover_available_usd == sp.Integer(0)
    assert general_result.carryover_used_this_year_usd == sp.Integer(0)

    # Passive nutzt seinen EIGENEN Carryover nur bis zu SEINER Limitation,
    # nicht bis zum General-Slack.
    # Passive-Limitation = 30000 * 50000/150000 = 10000
    assert passive_result.section_904_limitation_usd == sp.Integer(10_000)
    # Slack Passive = 10000 - 2000 = 8000 -> Carryover-Nutzung gedeckelt auf 8000,
    # obwohl 50000 verfügbar wären.
    assert passive_result.carryover_used_this_year_usd == sp.Integer(8_000)
    assert passive_result.remaining_prior_carryovers_usd == sp.Integer(42_000)
