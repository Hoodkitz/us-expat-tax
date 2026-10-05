"""
Modul 4 - Deterministische Compliance-State-Machine.

Das LLM DARF diese Flags nur in natürlichen Text übersetzen. Es darf
sie weder berechnen noch verändern. Die State-Machine selbst enthält
keinerlei LLM-Logik.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.logic_engine import evaluate_reporting_thresholds


@dataclass(frozen=True)
class ComplianceFlags:
    fbar_required: bool
    form8938_required: bool
    max_balance_usd: str


def compute_compliance_flags(max_account_balance_usd) -> ComplianceFlags:
    """Reiner Pass-Through zur bereits verifizierten Engine-Funktion."""
    raw = evaluate_reporting_thresholds(max_account_balance_usd)
    return ComplianceFlags(**raw)


def flags_to_prompt_context(flags: ComplianceFlags) -> str:
    """
    Erzeugt einen strikt faktischen Kontext-String für das LLM. Enthält
    NUR die berechneten Fakten, keine Bewertung, keine Handlungsempfehlung.
    Das LLM soll diesen Text lediglich in natürliche Sprache übertragen.
    """
    lines = [
        f"FBAR_REQUIRED={flags.fbar_required}",
        f"FORM_8938_REQUIRED={flags.form8938_required}",
        f"MAX_ACCOUNT_BALANCE_USD={flags.max_balance_usd}",
    ]
    return "\n".join(lines)
