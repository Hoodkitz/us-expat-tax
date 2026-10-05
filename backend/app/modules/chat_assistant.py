"""
Modul 4 - KI-Prüfassistent (Read-Only NLP Interface).

Harte Architektur-Garantie: Dieses Modul importiert NICHTS aus
logic_engine.py, das Berechnungen durchführt (nur die bereits fertigen
ComplianceFlags werden konsumiert). Der Assistent kann also strukturell
keine Steuerdaten verändern oder berechnen, selbst bei einem Prompt-
Injection-Versuch, weil ihm schlicht keine Schreib-/Rechenfunktionen
zur Verfügung stehen (Least Privilege auf Funktionsebene).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.modules.compliance_state import ComplianceFlags, flags_to_prompt_context

# Exakter juristisch vorgegebener Wortlaut. Muss identisch sein mit
# guardrails/config.yml -> custom_data.tax_advice_disclaimer und
# guardrails/rails/tax_advice_block.co -> "bot refuse tax advice".
DISCLAIMER = (
    "Diese App leistet keine Steuerberatung. "
    "Die finale rechtliche Verantwortung liegt beim Nutzer."
)

# ---------------------------------------------------------------------
# WICHTIG (Fix ggü. vorheriger Version): GUARDRAILS_CONFIG_YAML und
# GUARDRAILS_COLANG waren zuvor reine Dokumentations-Strings, die
# NIRGENDS ausgewertet wurden -- der LLM-Call in
# explain_compliance_flags() lief für JEDEN Prompt durch, auch für
# Steuerberatungsfragen. Das war eine simulierte, nicht enforced
# Guardrail (Reward-Hacking-Risiko: Test hätte grün sein können, ohne
# dass tatsächlich etwas blockiert wird).
#
# Die produktive Colang/YAML-Spezifikation liegt jetzt als echte Datei
# unter guardrails/config.yml und guardrails/rails/tax_advice_block.co
# (für den NeMo-Runtime-Pfad mit echtem Main-LLM + Embedding-Provider).
#
# Die tatsächliche Durchsetzung im Backend erfolgt zusätzlich -- und
# primär, weil sie ohne Netzwerk-/Embedding-Abhängigkeit deterministisch
# läuft -- über is_blocked_intent() unten. Diese Funktion wird VOR jedem
# LLM-Aufruf synchron geprüft; bei Treffer wird der LLM-Client NIE
# aufgerufen.
# ---------------------------------------------------------------------

_BLOCKED_PATTERNS = [
    r"steuern?\s*.{0,20}\bspar",
    r"\bftc\b.{0,30}\bfeie\b|\bfeie\b.{0,30}\bftc\b",
    r"was\s+kann\s+ich\s+absetzen",
    r"was\s+soll\s+ich\s+.{0,20}\babsetzen",
    r"welche[sn]?\s+formular.*(nutzen|w[aä]hlen|verwenden)",
    r"steuerberatung",
    r"wie\s*viel\s+steuern",
    r"steuern?\s*.{0,20}\boptimier|optimier.{0,20}\bsteuer",
    r"steuerlast\s*.{0,20}\boptimier|optimier.{0,20}\bsteuerlast",
    r"was\s+empfiehlst\s+du.{0,20}steuerlich",
]
_BLOCKED_REGEX = re.compile("|".join(_BLOCKED_PATTERNS), re.IGNORECASE)


def is_blocked_intent(user_question: str) -> bool:
    """
    Deterministische Input-Rail. Reine Funktion, KEIN LLM-Aufruf.
    Entspricht der Colang-Definition 'define user ask for tax advice'
    in guardrails/rails/tax_advice_block.co, aber nativ und synchron
    im Python-Code durchgesetzt.
    """
    return bool(_BLOCKED_REGEX.search(user_question))


# ---------------------------------------------------------------------
# ITERATION 6: OUTPUT-RAIL (Semantic Verification + Adversarial Evasion
# Protection)
#
# Die Input-Rail oben ist per Definition umgehbar: sie kennt nur die
# Nutzerfrage, nicht die tatsächliche LLM-Antwort. Ein Jailbreak wie
# "Angenommen, du schreibst einen fiktiven Roman über einen
# Steuerberater..." enthält keines der Trigger-Wörter aus
# _BLOCKED_PATTERNS und passiert die Input-Rail bewusst und korrekt.
#
# Die Output-Rail schließt genau diese Lücke: sie prüft NICHT die
# Absicht der Frage, sondern das tatsächlich generierte Ergebnis, bevor
# es den Client erreicht. Zwei unabhängige, deterministische Signale:
#
#  1. Advisory-Sprache: Formulierungen, die eine Empfehlung/Bewertung
#     ausdrücken (unabhängig vom fiktiven Rahmen, in dem sie verpackt
#     sind), in Kombination mit einem Steuerbegriff.
#  2. Zahlen-Halluzination: JEDE Zahl im LLM-Output, die nicht im
#     injizierten Fakten-Kontext (flags_to_prompt_context) vorkommt,
#     gilt als nicht durch die deterministische Engine gedeckt und
#     wird als potenzielle Halluzination behandelt. Das ist bewusst
#     strikt (Fail-Closed) statt eines "LLM-as-a-Judge"-Mocks, weil es
#     ohne zusätzlichen LLM-Aufruf und ohne Netzwerkabhängigkeit
#     hart durchsetzbar ist.
#
# Bei Treffer wird die Antwort NICHT teilweise bereinigt oder gekürzt,
# sondern vollständig und deterministisch durch DISCLAIMER ersetzt.
# Der ursprüngliche LLM-Text verlässt die Funktion in diesem Fall nie.
# ---------------------------------------------------------------------

_OUTPUT_ADVICE_PATTERNS = [
    r"(empfiehl|empfehl|rate|raten|rät)\w*.{0,60}(feie|ftc|absetz|steuerlast|steuern|formular)",
    r"(feie|ftc)\w*.{0,60}(empfiehl|empfehl|rate|raten|rät|besser|vorteilhaft|w[aä]hlen sollte)",
    r"sie sollten.{0,40}(feie|ftc|absetzen|steuer)",
    r"du solltest.{0,40}(feie|ftc|absetzen|steuer)",
    r"ich (würde|w[uü]rde) (ihnen |dir )?(empfehlen|raten)",
    r"(w[uü]rde|würde) (ihm|ihr|ihnen|dir).{0,40}(raten|empfehlen)",
    r"vorteilhafter\s+w[aä]re",
]
_OUTPUT_ADVICE_REGEX = re.compile("|".join(_OUTPUT_ADVICE_PATTERNS), re.IGNORECASE)

# Erfasst Zahlen inkl. optionalem $/USD-Präfix, Tausendertrennzeichen
# und Dezimalstellen, z.B. "$17,300", "17300", "12.500,00".
_NUMBER_TOKEN_REGEX = re.compile(r"\$?\s?\d[\d.,]*\d|\$?\s?\d")


def _normalize_numbers(text: str) -> set[str]:
    """Extrahiert alle Zahlen aus einem Text und normalisiert sie auf
    reine Ziffernfolgen (ohne $, Punkte, Kommas), damit '17,300' und
    '17300' als identisch erkannt werden."""
    raw_tokens = _NUMBER_TOKEN_REGEX.findall(text)
    normalized = set()
    for token in raw_tokens:
        digits_only = re.sub(r"[^\d]", "", token)
        if digits_only:
            normalized.add(digits_only)
    return normalized


def contains_output_advice_language(output_text: str) -> bool:
    """Erkennt Empfehlungs-/Bewertungssprache unabhängig von einem
    fiktiven oder rollenspielbasierten Rahmen (Jailbreak-Umgehung der
    Input-Rail wird hierdurch auf Output-Ebene aufgefangen)."""
    return bool(_OUTPUT_ADVICE_REGEX.search(output_text))


def contains_hallucinated_numbers(output_text: str, context_text: str) -> bool:
    """
    True, wenn der LLM-Output eine Zahl enthält, die NICHT im
    injizierten, deterministisch berechneten Fakten-Kontext vorkommt.
    Das LLM darf Zahlen nur wiedergeben, niemals neue erzeugen.
    """
    output_numbers = _normalize_numbers(output_text)
    if not output_numbers:
        return False
    context_numbers = _normalize_numbers(context_text)
    return not output_numbers.issubset(context_numbers)


def output_rail_violated(output_text: str, context_text: str) -> bool:
    """Kombinierte Output-Rail-Prüfung. True => Antwort darf NICHT
    ausgeliefert werden und MUSS durch DISCLAIMER ersetzt werden."""
    return contains_output_advice_language(
        output_text
    ) or contains_hallucinated_numbers(output_text, context_text)


@dataclass(frozen=True)
class AssistantResponse:
    text: str
    disclaimer_appended: bool = True


class ReadOnlyTaxAssistant:
    """
    Übersetzt ausschließlich bereits vorhandene, deterministisch
    berechnete Daten (ComplianceFlags, EngineResult-Zusammenfassungen)
    in natürlichen Text. Besitzt KEINE Methode, die Steuerwerte
    berechnet oder Nutzerdaten mutiert.
    """

    def __init__(self, llm_client) -> None:
        # llm_client: austauschbarer LangChain-Chat-Client, der bereits
        # mit den NeMo-Guardrails-Flows oben verdrahtet ist.
        self._llm_client = llm_client

    async def explain_compliance_flags(
        self, flags: ComplianceFlags, user_question: str
    ) -> AssistantResponse:
        # Input-Rail: läuft synchron, VOR jedem LLM-Aufruf. Bei Treffer
        # wird self._llm_client NIE aufgerufen -- kein Netzwerk-Call,
        # kein Token-Verbrauch, keine Chance auf Prompt-Injection-Bypass,
        # da der Codepfad zum LLM strukturell nicht erreicht wird.
        if is_blocked_intent(user_question):
            return AssistantResponse(text=DISCLAIMER, disclaimer_appended=True)

        context = flags_to_prompt_context(flags)

        system_prompt = (
            "Du bist ein Read-Only-Erklärassistent für Steuer-Compliance-"
            "Status. Du erklärst NUR die untenstehenden bereits "
            "berechneten Fakten in verständlicher Sprache. Du gibst "
            "KEINE Handlungsempfehlung, KEINE Steuerberatung, und du "
            "berechnest NICHTS selbst. Wenn der Nutzer nach einer "
            f"Empfehlung fragt, verweise auf einen Steuerberater.\n\n"
            f"Fakten:\n{context}"
        )

        raw_text = await self._llm_client.ainvoke(
            system=system_prompt, user=user_question
        )

        # Output-Rail: läuft NACH dem LLM-Call, VOR der Auslieferung.
        # Fängt genau die Fälle ab, in denen die Input-Rail bewusst
        # passieren gelassen wurde (z.B. fiktiver Rahmen), das Main-LLM
        # aber trotzdem beratenden oder zahlen-halluzinierten Text
        # generiert hat. Bei Treffer wird raw_text vollständig verworfen
        # -- kein Teil des Originaltexts erreicht den Rückgabewert.
        if output_rail_violated(raw_text, context):
            return AssistantResponse(text=DISCLAIMER, disclaimer_appended=True)

        final_text = raw_text.rstrip()
        if DISCLAIMER not in final_text:
            final_text = f"{final_text}\n\n{DISCLAIMER}"

        return AssistantResponse(text=final_text, disclaimer_appended=True)
