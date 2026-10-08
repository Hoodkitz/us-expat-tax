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

## 🚀 Installation

```bash
# Repository klonen
git clone https://github.com/Hoodkitz/us-expat-tax.git
cd us-expat-tax

# Virtual Environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Environment
cp .env.example .env
```

## 📖 Usage

```bash
# Server starten
uvicorn app.main:app --reload

# API Docs
# http://localhost:8000/docs
```

## 🔌 API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tax/calculate` | POST | Steuerberechnung |
| `/api/tax/ftc` | GET | Foreign Tax Credit |
| `/api/tax/feie` | GET | Foreign Earned Income Exclusion |
| `/api/bank/transactions` | GET | Banktransaktionen |

## 🤝 Contributing

Beiträge sind willkommen! Bitte lies [CONTRIBUTING.md](CONTRIBUTING.md) für Guidelines.

## 📄 License

MIT — Siehe [LICENSE](LICENSE).
