# Minimal Vault server config for the docker-compose stack.
# Production: use integrated storage + auto-unseal and real certificates.
ui = false
storage "file" { path = "/vault/data" }
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/vault/config/tls/server.pem"
  tls_key_file  = "/vault/config/tls/server.key"
}
disable_mlock = false
