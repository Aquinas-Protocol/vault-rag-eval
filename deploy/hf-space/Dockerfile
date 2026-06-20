# Hugging Face Space (Docker SDK): the real qdrant/qdrant SERVER + the FastAPI demo
# in ONE container. The app reaches Qdrant over localhost; Neon (a Space secret) is
# the lexical arm. Spaces have ephemeral storage, so Qdrant is re-seeded from the
# committed fixtures on every boot (120 vectors, sub-second).
#
# Built FROM the qdrant image so the server binary + config are present and known-
# good; Python + the app are layered on top.
FROM qdrant/qdrant:v1.18.2

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip3 install --break-system-packages -e ".[server]"
COPY app ./app
COPY scripts ./scripts
COPY fixtures ./fixtures
COPY start.sh ./start.sh

# App -> local Qdrant; Qdrant writes to ephemeral /tmp.
ENV QDRANT_URL=http://127.0.0.1:6333 \
    QDRANT__STORAGE__STORAGE_PATH=/tmp/qdrant/storage \
    VRAG_EMBED_MODEL=nomic-embed-text

EXPOSE 7860
CMD ["bash", "start.sh"]
