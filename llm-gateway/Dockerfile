FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir ".[api,anthropic]" && useradd -m app
USER app
ENV PROVIDERS=mock
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]
