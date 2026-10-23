FROM python:3.11-slim
WORKDIR /app
COPY vault_backoff.py erica_stub.py ./
RUN useradd --system --uid 10002 erica
USER erica
EXPOSE 8443
# Waits (with backoff) until vault-agent has written the ELSTER certificate to
# the tmpfs mount, then execs the real server. Replace the CMD with the
# ERiC wrapper once the proprietary ERiC library is installed in this image.
ENTRYPOINT ["python3", "/app/vault_backoff.py", "--"]
CMD ["python3", "/app/erica_stub.py"]
