# AI-Connex Stage 6-8 Parser-Compile Container Image
FROM python:3.11-slim@sha256:9c900dea9e8fb7e16277c179b555cc72d29a352dbc33cff48ad5a0412fd5bfc7

RUN groupadd -g 10001 sandboxgroup && \
    useradd -u 10001 -g sandboxgroup -s /bin/sh -m sandboxuser

RUN mkdir -p /sandbox/input /sandbox/output /sandbox/contracts /sandbox/templates /sandbox/workers && \
    chown -R 10001:10001 /sandbox

WORKDIR /sandbox

RUN pip install --no-cache-dir \
    pydantic==2.6.0 \
    pyarrow==19.0.1 \
    datafusion==54.0.0 \
    orjson==3.9.15 \
    pyyaml==6.0.1

COPY contracts/ /sandbox/contracts/
COPY sandbox/templates/ /sandbox/templates/
COPY sandbox/workers/compile_worker.py /sandbox/workers/compile_worker.py

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/sandbox \
    SANDBOX_INPUT_DIR=/sandbox/input \
    SANDBOX_OUTPUT_DIR=/sandbox/output

USER 10001:10001

ENTRYPOINT ["python", "/sandbox/workers/compile_worker.py"]
