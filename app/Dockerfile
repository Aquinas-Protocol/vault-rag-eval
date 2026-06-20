# FastAPI demo service. Stateless; reaches Qdrant over .flycast and Neon over the
# pooled URL. Embeddings are committed (canned demo), so no model runtime is needed.
# Build context is the REPO ROOT (so src/, app/, fixtures/ are all available).
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# Editable install keeps vrag.config.REPO_ROOT == /app, so the committed fixtures
# (demo queries + their embeddings) resolve at runtime.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install -e ".[server]"

COPY app ./app
COPY fixtures ./fixtures

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
