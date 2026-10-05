"""
Verifizierung von compliance_state.py.

Beachte: die eigentlichen Schwellenwert-Berechnungen (FBAR/8938 bei
10.000 / 200.000 USD) werden bereits in
test_logic_engine.py::test_reporting_thresholds gegen die Engine
(evaluate_reporting_thresholds) verifiziert. Diese Datei prüft
zusätzlich, dass compliance_state.py ein reiner, verlustfreier
Pass-Through ist und dass flags_to_prompt_context() ausschließlich
Fakten ohne Bewertung ausgibt.
"""

import pytest

from app.modules.compliance_state import (
    ComplianceFlags,
    compute_compliance_flags,
    flags_to_prompt_context,
)


def test_pass_through_below_fbar_threshold():
    flags = compute_compliance_flags("5000")
    assert flags.fbar_required is False
    assert flags.form8938_required is False


def test_pass_through_above_fbar_threshold_only():
    flags = compute_compliance_flags("10001")
    assert flags.fbar_required is True
    assert flags.form8938_required is False


def test_pass_through_above_form8938_threshold_both_flags():
    flags = compute_compliance_flags("200001")
    assert flags.fbar_required is True
    assert flags.form8938_required is True


def test_boundary_exactly_at_fbar_threshold_not_triggered():
    # Regel ist strikt '>', nicht '>='
    flags = compute_compliance_flags("10000")
    assert flags.fbar_required is False


def test_result_is_frozen_dataclass():
    flags = compute_compliance_flags("1")
    with pytest.raises(Exception):
        flags.fbar_required = True  # type: ignore[misc]


def test_prompt_context_contains_only_facts_no_recommendation():
    flags = ComplianceFlags(
        fbar_required=True, form8938_required=False, max_balance_usd="15000"
    )
    context = flags_to_prompt_context(flags)

    assert "FBAR_REQUIRED=True" in context
    assert "FORM_8938_REQUIRED=False" in context
    assert "MAX_ACCOUNT_BALANCE_USD=15000" in context

    # Muss frei von Empfehlungs-/Bewertungssprache sein.
    for forbidden_word in ["sollte", "empfehl", "am besten", "spar"]:
        assert forbidden_word not in context.lower()


def test_same_input_always_same_output_determinism():
    a = compute_compliance_flags("42000")
    b = compute_compliance_flags("42000")
    assert a == b
