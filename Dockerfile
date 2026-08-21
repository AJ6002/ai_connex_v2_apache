# AI-Connex Apache Production Base Image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy contracts, registries, and data-studio modules
COPY contracts/ /app/contracts/
COPY registries/ /app/registries/
COPY data-studio/ /app/data-studio/
COPY tests/ /app/tests/

# Install core python packages
RUN pip install --no-cache-dir pydantic pyarrow pytest

ENV PYTHONUNBUFFERED=1

CMD ["python", "-c", "import contracts; print('AI-Connex Apache Base Container Ready')"]
