# AI-Connex Single-Purpose XLSX Parser Container Image
FROM python:3.11-slim@sha256:9c900dea9e8fb7e16277c179b555cc72d29a352dbc33cff48ad5a0412fd5bfc7

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

WORKDIR /home/appuser/app

RUN pip install --no-cache-dir openpyxl pandas pyarrow

COPY data-studio/parser-workers/xlsx_worker.py /home/appuser/app/xlsx_worker.py

USER 10001:10001

ENTRYPOINT ["python", "/home/appuser/app/xlsx_worker.py"]
