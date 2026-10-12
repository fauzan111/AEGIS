# AEGIS gate: the OBSERVE/FINGERPRINT/SCORE/DECIDE pipeline
# (src/aegis_detect.py) plus the Streamlit dashboard (src/aegis_dashboard.py),
# built from the repo root: docker build -f infra/docker/aegis-gate/Dockerfile .
#
# Phase 2 is a lift-and-shift of what already runs locally: the baked-in
# data/aegis_traffic.csv is what the dashboard's live-attack-injection tab
# fits its baselines against (load_live_pipeline() in aegis_dashboard.py),
# not just a build artifact. Reading from S3 instead is Phase 3 work.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/aegis_detect.py src/aegis_dashboard.py src/generate_synthetic_traffic.py src/
COPY data/aegis_traffic.csv data/aegis_traffic.csv
COPY assets/hero_landscape.jpg assets/fastweb_vodafone_badge.png assets/

# Regenerate reports/scored_windows.csv from the baked-in traffic at build
# time, rather than copying a possibly-stale pre-computed CSV, so the image
# always ships a result consistent with its own code and data.
RUN python src/aegis_detect.py

# The `aegis` namespace is labeled at the `privileged` Pod Security Standard
# (other workloads in it need that), which means this container gets no
# PSS backstop of its own - run as a real non-root user so there's still a
# defense-in-depth layer if the chart's securityContext is ever loosened.
RUN useradd --create-home --uid 10001 aegis && chown -R aegis:aegis /app
USER aegis

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["streamlit", "run", "src/aegis_dashboard.py", \
            "--server.address=0.0.0.0", "--server.port=8501", \
            "--server.headless=true"]
