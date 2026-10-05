# US Expat Tax Helper – Backend

FastAPI backend for US expatriates filing both German (ELSTER) and US (IRS) tax returns.
Runs on EKS inside a Linkerd mTLS service mesh with HashiCorp Vault for secrets management.

## Architecture

```
Browser / Client
       │  HTTPS
       ▼
linkerd-proxy-edge (mTLS boundary)
       │  mTLS
       ├──▶ backend  (FastAPI, port 127.0.0.1:8000)
       │       ├── Module 1: Tax Logic Engine  (FTC vs FEIE, deterministic)
       │       ├── Module 2: PSD2/Tink Interface  (read-only bank transactions)
       │       ├── Module 3: Compliance Flags  (FBAR / FATCA thresholds)
       │       ├── Module 4: OCR Lohnsteuerbescheinigung
       │       └── Module 5: Submission Saga  (ELSTER → IRS unlock)
       │
       └──▶ erica-service  (ERiC ELSTER wrapper, port 127.0.0.1:8443)
                └── vault-agent (injects .pfx cert into tmpfs, RAM-only)

vault  (HashiCorp Vault 1.16, HA with Raft, AppRole auth)
```

## Key Services

| Service | Purpose |
|---|---|
| `backend` | FastAPI API – tax evaluation, compliance checks, submission orchestration |
| `erica-service` | ELSTER filing via ERiC library; cert injected from Vault into tmpfs |
| `vault` | Secrets management; ELSTER .pfx cert never touches persistent disk |

## Quick Start (Docker Compose)

```bash
cp .env.example .env
# Fill in VAULT_ADDR, TINK_CLIENT_ID/SECRET, DATABASE_URL
docker compose up --build
```

The edge proxy listens on `https://localhost:8443`.

## Kubernetes / EKS Deployment

Manifests live in `k8s/`:

| Manifest | Purpose |
|---|---|
| `namespace-and-serviceaccounts.yaml` | Namespace + IRSA service accounts |
| `fastapi-deployment.yaml` | Backend Deployment + Service |
| `erica-deployment.yaml` | Erica Deployment with Vault init-container |
| `erica-vault-agent-configmap.yaml` | Vault Agent template config |
| `linkerd-mtls-authorization.yaml` | Linkerd `AuthorizationPolicy` (zero-trust) |
| `network-policies.yaml` | Kubernetes NetworkPolicy (deny-all + allow-list) |

Deploy (CI uses `deploy.yml`):

```bash
kubectl apply -f k8s/
```

## Environment Variables

See [`.env.example`](.env.example) for a full, annotated reference.

## Security Notes

- The ELSTER organisation certificate (`.pfx`) is **never written to persistent storage**.
  Vault Agent renders it exclusively into a `tmpfs` mount that is destroyed with the container.
- All inter-service traffic is mTLS-enforced via Linkerd; `LINKERD2_PROXY_IDENTITY_MODE=required`
  prevents plain-text fallback.
- The submission flow is gated behind a TOTP 2FA check (`/api/v1/submission/tollgate`).
  US forms (1040/1116) are only unlocked after a confirmed ELSTER Transferticket.
- Tink integration uses **read-only** OAuth scopes (`accounts:read`, `transactions:read`).
  Payment scopes are explicitly excluded.
- Guardrails configuration is in `guardrails/` (input/output validation for LLM-adjacent paths).

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `POST` | `/api/v1/tax/evaluate` | FTC vs FEIE recommendation (deterministic) |
| `GET` | `/api/v1/compliance/flags` | FBAR / FATCA compliance flags |
| `POST` | `/api/v1/submission/tollgate` | 2FA gate; returns signed waiver token |
