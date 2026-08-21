# AI-Connex Single-Purpose XLSX Parser Container Image
FROM python:3.11-slim

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

WORKDIR /home/appuser/app

RUN pip install --no-cache-dir openpyxl pandas pyarrow

COPY data-studio/parser-workers/xlsx_worker.py /home/appuser/app/xlsx_worker.py

USER 10001:10001

ENTRYPOINT ["python", "/home/appuser/app/xlsx_worker.py"]
