# AI-Connex Stage 1-5 Parser-Discovery Container Image
FROM python:3.11-slim@sha256:9c900dea9e8fb7e16277c179b555cc72d29a352dbc33cff48ad5a0412fd5bfc7

RUN groupadd -g 10001 sandboxgroup && \
    useradd -u 10001 -g sandboxgroup -s /bin/sh -m sandboxuser

RUN mkdir -p /sandbox/input /sandbox/output /sandbox/contracts /sandbox/registries /sandbox/workers && \
    chown -R 10001:10001 /sandbox

WORKDIR /sandbox

# Install discovery dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pydantic==2.6.0 \
    pyarrow==19.0.1 \
    polars==1.43.2 \
    orjson==3.9.15 \
    ijson==3.2.3 \
    python-magic==0.4.27

COPY contracts/ /sandbox/contracts/
COPY registries/ /sandbox/registries/
COPY sandbox/workers/discovery_worker.py /sandbox/workers/discovery_worker.py

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/sandbox \
    SANDBOX_INPUT_DIR=/sandbox/input \
    SANDBOX_OUTPUT_DIR=/sandbox/output

USER 10001:10001

ENTRYPOINT ["python", "/sandbox/workers/discovery_worker.py"]
