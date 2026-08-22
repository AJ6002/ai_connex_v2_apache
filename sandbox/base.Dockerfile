# AI-Connex Level 4 Common Sandbox Base Image
# Pinned python:3.11-slim by digest
FROM python:3.11-slim@sha256:9c900dea9e8fb7e16277c179b555cc72d29a352dbc33cff48ad5a0412fd5bfc7

# Establish non-root user 10001:10001
RUN groupadd -g 10001 sandboxgroup && \
    useradd -u 10001 -g sandboxgroup -s /bin/sh -m sandboxuser

# Create standard sandbox directory layout with strict permissions
RUN mkdir -p /sandbox/input /sandbox/output /sandbox/contracts /sandbox/workers && \
    chown -R 10001:10001 /sandbox

WORKDIR /sandbox

# Upgrade pip & install common runtime contracts dependencies
RUN pip install --no-cache-dir \
    pydantic==2.6.0 \
    pyarrow==19.0.1 \
    orjson==3.9.15

# Environment configuration conventions
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SANDBOX_INPUT_DIR=/sandbox/input \
    SANDBOX_OUTPUT_DIR=/sandbox/output

# Switch to non-root execution context
USER 10001:10001

CMD ["python", "-c", "import pydantic, pyarrow, orjson; print('AI-Connex Common Sandbox Base Container Ready')"]
