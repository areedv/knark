# temp stage
FROM python:3.8.10-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

COPY . /app
RUN pip install --upgrade build && \
    python -m build

# final stage
FROM python:3.8.10-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libdmtx0b \
    libzbar0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=builder /app/dist /dist

RUN pip install --no-cache /dist/knarkscan*.whl

ENTRYPOINT ["python", "/usr/local/lib/python3.8/site-packages/knarkscan/main.py", "-c", "/config/config.yaml"]

