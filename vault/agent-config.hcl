# Vault Agent Konfiguration für den Erica-Service-Container.
# Zweck: Organisationszertifikat (.pfx) NIE auf Platte schreiben.
# Der "sink" zeigt auf ein tmpfs-Mount, das RAM-only ist und beim
# Container-Stop verworfen wird (siehe docker-compose.yml: tmpfs).

vault {
  address = "https://vault:8200"
  retry {
    num_retries = 8   # exponentielles Backoff, siehe backoff-Formel unten
  }
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path   = "/run/secrets/role_id"
      secret_id_file_path = "/run/secrets/secret_id"
    }
  }

  sink "file" {
    config = {
      path = "/run/secrets/eric-cert/organisation.pfx"   # tmpfs, RAM-only
      mode = 0600
    }
  }
}

template {
  source      = "/vault/templates/eric-cert.pfx.tpl"
  destination = "/run/secrets/eric-cert/organisation.pfx"
  perms       = "0600"
  # kein "create_dest_dirs" auf persistenten Pfaden -> nur tmpfs-Ziel zulässig
}

# Boot-Sequenz-Hinweis: Falls der Token-Exchange verzögert ist, regelt
# `vault_backoff.py` (im erica-service) das exponentielle Retry der
# Anwendung selbst, unabhängig vom Agent-internen Retry.
