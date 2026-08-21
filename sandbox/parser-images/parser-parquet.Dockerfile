# AI-Connex Single-Purpose Parquet Inspection Container Image
FROM python:3.11-slim

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

WORKDIR /home/appuser/app

RUN pip install --no-cache-dir pyarrow pandas

COPY data-studio/parser-workers/parquet_worker.py /home/appuser/app/parquet_worker.py

USER 10001:10001

ENTRYPOINT ["python", "/home/appuser/app/parquet_worker.py"]
