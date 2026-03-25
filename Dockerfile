# 多階段構建 - 開發階段
FROM python:3.10-slim as builder

# 安裝構建依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"


COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser


RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*


COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app


COPY --chown=appuser:appuser . .


RUN mkdir -p /app/static/uploads /app/logs && \
    chown -R appuser:appuser /app


USER appuser


ENV FLASK_APP=microblog.py
ENV FLASK_DEBUG=0
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1


EXPOSE 5000


HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1


CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"] 