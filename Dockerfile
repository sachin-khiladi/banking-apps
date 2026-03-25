# ─── Build stage ──────────────────────────────────────────────────────────────
# Installs Python dependencies into an isolated virtual environment.
# gcc is needed by some C-extension wheels; removed in the runtime stage.
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build toolchain and clean apt cache in a single layer
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.runtime.txt .

# Separate venv so COPY --from=builder gives a clean, portable Python tree
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade "setuptools>=80.9.0" "wheel>=0.46.2" \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.runtime.txt

# ─── Runtime stage ─────────────────────────────────────────────────────────── 
# Slim final image: no compiler, no build cache, no test code.
FROM python:3.11-slim AS runtime

RUN python -m pip install --no-cache-dir --upgrade "setuptools>=80.9.0" "wheel>=0.46.2"

# Security: run as a dedicated non-root user (UID/GID 1001)
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup \
               --no-create-home --shell /sbin/nologin appuser

# Copy only the pre-built virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Prepend venv bin; disable .pyc generation and stdout buffering
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy application source only — tests, infra, docs, and agent configs stay out
COPY src/ ./src/

# Drop privileges before the server starts
USER appuser

EXPOSE 8000

# Built-in health check — no curl/wget dependency required
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c \
        "import urllib.request, sys; \
         r = urllib.request.urlopen('http://localhost:8000/health', timeout=8); \
         sys.exit(0 if r.status == 200 else 1)" \
    || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
