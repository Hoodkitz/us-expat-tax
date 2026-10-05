"""
Modul 1 - Boot-Sequenz-Resilienz (Docker Compose UND Kubernetes).

Zweck: Verhindert einen Crash-Loop des Erica-Service, falls der
Vault-Agent (Init-Container ODER Sidecar) das ELSTER-Zertifikat noch
nicht in den RAM-Volume-Mount geschrieben hat, wenn der Hauptprozess
starten will.

VERWENDUNG ALS K8s-ENTRYPOINT-WRAPPER:
    Dieses Skript wird im Dockerfile des Erica-Service als ENTRYPOINT
    eingesetzt und ersetzt sich selbst (os.execvp) durch den echten
    ERiC-Wrapper-Prozess, SOBALD das Zertifikat bestätigt im tmpfs
    liegt. Dadurch bleibt PID 1 korrekt (kein Zombie-Prozess-Problem
    in Containern) und Signale (SIGTERM bei Pod-Terminierung) gehen
    direkt an den echten Prozess.

    Beispiel Dockerfile:
        ENTRYPOINT ["python3", "/app/vault_backoff.py", "--"]
        CMD ["/usr/local/bin/eric-wrapper-server", "--port", "8443"]

REDUNDANZ-PRINZIP (Defense in Depth gegen die Race Condition):
    In Kubernetes existiert bereits eine STRUKTURELLE Absicherung durch
    einen Init-Container (siehe k8s/erica-deployment.yaml), der den
    Vault-Agent im "-exit-after-auth"-Modus einmalig laufen lässt und
    das Zertifikat rendert, BEVOR der Haupt-Container überhaupt
    gestartet wird (Kubernetes garantiert: Init-Container muss
    erfolgreich terminieren, bevor reguläre Container starten).

    Dieses Skript ist die ZWEITE, unabhängige Verteidigungslinie:
    Sollte der Init-Container aus irgendeinem Grund entfernt oder
    fehlkonfiguriert werden (Manifest-Drift, menschlicher Fehler bei
    einem zukünftigen Deployment), verhindert dieser Wrapper trotzdem
    einen Crash-Loop, indem er selbst wartet, statt sich blind auf die
    Init-Container-Garantie zu verlassen.
"""

from __future__ import annotations

import logging
import os
import random
import sys
import time
from pathlib import Path

logger = logging.getLogger("erica.boot")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Pfad ist in Docker Compose UND Kubernetes identisch gehalten, um die
# Anwendungs-Konfiguration zwischen beiden Umgebungen nicht aufspalten
# zu müssen. Per ENV überschreibbar für Tests / abweichende Deployments.
CERT_PATH = Path(os.environ.get("ERIC_CERT_PATH", "/vault/secrets/elster.pfx"))

# Alle Backoff-Parameter sind per ENV konfigurierbar, damit Ops-Teams
# das Timing an reale Vault-Latenzen (z.B. HA-Vault-Cluster mit
# Raft-Konsens, Kubernetes-Auth-Round-Trip) anpassen können, ohne den
# Code selbst zu ändern.
DEFAULT_MAX_RETRIES = int(os.environ.get("VAULT_CERT_WAIT_MAX_RETRIES", "10"))
DEFAULT_BASE_DELAY_S = float(os.environ.get("VAULT_CERT_WAIT_BASE_DELAY_S", "1.0"))
DEFAULT_MAX_DELAY_S = float(os.environ.get("VAULT_CERT_WAIT_MAX_DELAY_S", "60.0"))


class VaultExchangeTimeout(RuntimeError):
    """Wird geworfen, wenn Vault nach allen Retries kein Zertifikat liefert."""


def wait_for_cert_injection(
    cert_path: Path = CERT_PATH,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY_S,
    max_delay: float = DEFAULT_MAX_DELAY_S,
) -> Path:
    """
    Exponentielles Backoff mit Jitter: delay = min(max_delay,
    base_delay * 2^n) + zufälliger Jitter (bis zu 10% des delay), um
    ein "Thundering Herd"-Problem zu vermeiden, falls viele Erica-
    Service-Replicas gleichzeitig neu starten (z.B. nach einem Node-
    Ausfall oder Rolling-Update) und alle gleichzeitig denselben
    Vault-Cluster nach Token-Exchange befragen.

    Prüft NICHT den kryptografischen Inhalt des Zertifikats (das
    übernimmt der ERiC-Wrapper selbst beim Laden), sondern nur, dass
    der Vault-Agent den tmpfs-Mount bereits mit nicht-leerem Inhalt
    befüllt hat - das genügt, um die Race Condition zu schließen.
    """
    for attempt in range(1, max_retries + 1):
        if cert_path.exists() and cert_path.stat().st_size > 0:
            logger.info(
                "Zertifikat im RAM-Volume verfügbar nach %d Versuch(en): %s",
                attempt, cert_path,
            )
            return cert_path

        delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
        jitter = random.uniform(0, delay * 0.1)
        sleep_for = delay + jitter
        logger.warning(
            "Vault-Token-Exchange / Zertifikats-Rendering noch nicht "
            "abgeschlossen (Versuch %d/%d, Pfad=%s). Warte %.2fs.",
            attempt, max_retries, cert_path, sleep_for,
        )
        time.sleep(sleep_for)

    raise VaultExchangeTimeout(
        f"Zertifikat nach {max_retries} Versuchen nicht unter {cert_path} "
        "verfügbar. Mögliche Ursachen: Vault ist 'sealed', der "
        "Kubernetes-Auth-Role-Binding ist falsch konfiguriert, oder der "
        "Init-Container ist fehlgeschlagen (siehe 'kubectl describe pod' "
        "/ Init-Container-Logs 'vault-agent-init')."
    )


def run_with_cert_gate(argv: list[str]) -> None:
    """
    Entrypoint-Wrapper-Funktion: wartet auf das Zertifikat und ersetzt
    den aktuellen Prozess (PID 1 im Container) per exec durch den
    eigentlichen Erica-Service-Prozess. Kein Python-Prozess bleibt als
    Zwischenschicht bestehen - Signal-Handling (SIGTERM/SIGINT bei Pod-
    Terminierung) funktioniert dadurch korrekt und direkt.
    """
    if not argv:
        raise ValueError(
            "run_with_cert_gate benötigt mindestens ein Kommando, z.B. "
            "['python3', 'vault_backoff.py', '--', '/usr/local/bin/eric-wrapper-server']"
        )

    wait_for_cert_injection()

    logger.info("Zertifikat bestätigt. Starte Erica-Service-Prozess: %s", argv)
    os.execvp(argv[0], argv)  # ersetzt den aktuellen Prozess, kehrt nie zurück


def _parse_cli_args(raw_args: list[str]) -> list[str]:
    """
    Erwartet die Aufrufform: `vault_backoff.py -- <echter-befehl> [args...]`.
    Alles nach dem literalen '--' wird 1:1 an os.execvp weitergereicht.
    """
    if "--" not in raw_args:
        raise ValueError(
            "Erwarteter Aufruf: vault_backoff.py -- <befehl> [args...]. "
            f"Erhalten: {raw_args}"
        )
    separator_index = raw_args.index("--")
    command = raw_args[separator_index + 1:]
    if not command:
        raise ValueError("Kein Befehl nach '--' angegeben.")
    return command


if __name__ == "__main__":
    try:
        command_to_run = _parse_cli_args(sys.argv[1:])
        run_with_cert_gate(command_to_run)
    except (VaultExchangeTimeout, ValueError) as exc:
        logger.error("Boot-Sequenz fehlgeschlagen: %s", exc)
        sys.exit(1)
