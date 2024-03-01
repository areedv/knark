# temp stage
FROM python:slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

COPY . /app
RUN pip install --upgrade build && \
    python -m build

# final stage
FROM python:slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libdmtx0b \
    libzbar0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=builder /app/dist /dist

RUN pip install --no-cache /dist/knarkscan*.whl
