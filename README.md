# US Expat Tax Helper – Backend

FastAPI backend for US expatriates filing both German (ELSTER) and US (IRS) tax returns.
Runs on EKS inside a Linkerd mTLS service mesh with HashiCorp Vault for secrets management.

[![CI](https://github.com/Hoodkitz/us-expat-tax/actions/workflows/ci.yml/badge.svg)](https://github.com/Hoodkitz/us-expat-tax/actions)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Features

- **Tax Logic Engine**: Deterministische Berechnung von FTC vs. FEIE
- **PSD2/Tink Integration**: Bankdaten-Import
- **ELSTER Export**: Deutsche Steuererklärung
- **IRS Export**: US-Steuererklärung

## Rechtlicher Hinweis / Disclaimer

Diese Software liefert **unverbindliche Orientierungswerte** und leistet **keine Steuer-, Rechts- oder
Buchhaltungsberatung**. Sie ersetzt keinen Steuerberater, CPA oder Enrolled Agent. Die Verantwortung fuer
Steuererklaerungen liegt allein beim Nutzer. Jede API-Antwort traegt den Header `X-Tax-Disclaimer`, der Text ist
oeffentlich unter `GET /api/v1/disclaimer` abrufbar, das Frontend zeigt ihn im Footer, und der Chat-Assistent
(`guardrails/`, `app/modules/chat_assistant.py`) blockt Beratungsanfragen. Steuerwerte sind auf Tax Year 2025
ausgelegt und muessen jaehrlich geprueft werden.

## Installation

```bash
# Backend (Python 3.11)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env      # SECRET_KEY, TOLLGATE_SERVER_SECRET setzen
uvicorn app.main:app --reload   # http://localhost:8000/docs
pytest -q                       # tests/ + app/tests/

# Frontend (Node 20+)
cd frontend
npm ci --legacy-peer-deps
npm run dev                     # http://localhost:3000
npm run typecheck && npm run lint && npm test && npm run build
```

### Docker

```bash
# Dev/Demo: Backend + Frontend
docker compose -f docker-compose.dev.yml up --build

# Prod-aehnlich (Vault, ERiC-Stub, mTLS-Edge): benoetigt SECRET_KEY, TOLLGATE_SERVER_SECRET
# sowie Vault-TLS-Zertifikate in vault/config/tls/ und vault/certs/ca.pem (nicht im Repo).
docker compose up --build
```

## Konfiguration

| Variable | Zweck |
|----------|-------|
| `SECRET_KEY` | JWT-Signatur (Pflicht, >=32 Zeichen bei `APP_ENV=production`) |
| `TOLLGATE_SERVER_SECRET` | Signatur der Haftungsverzicht-Quittung (ohne Wert: 503) |
| `CORS_ORIGINS` | Komma-getrennte erlaubte Frontend-Origins |
| `APP_ENV` | `production` aktiviert strikte Secret-Pruefung |

## Bekannte Einschraenkungen (vor Go-Live)

- ELSTER-Uebermittlung ist ein Mock; ERiC-Bibliothek + Organisationszertifikat fehlen (`erica-service/erica_stub.py`).
- Mandanten werden in einer JSON-Datei gespeichert (`backend/app/data`), nicht in einer Datenbank.
- Mehrere Formular-Module sind vereinfachte Naeherungen (z. B. Form 6251 Regular Tax, Form 2106 ohne Berechtigungspruefung nach IRC 67(g)).
- Keine Zahlungs-/Abo-Pruefung im Backend (siehe separates Landing-Repo).

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tax/evaluate` | POST | FTC vs. FEIE |
| `/api/v1/compliance/flags` | GET | FBAR/FATCA-Flags |
| `/api/v1/disclaimer` | GET | Rechtlicher Hinweis (oeffentlich) |
| `/api/v1/<form>/calculate` | POST | Formular-Berechnung (JWT) |
| `/auth/register`, `/auth/login` | POST | Mandanten-Auth |

## 🤝 Contributing

Beiträge sind willkommen! Bitte lies [CONTRIBUTING.md](CONTRIBUTING.md) für Guidelines.

## 📄 License

MIT — Siehe [LICENSE](LICENSE).
