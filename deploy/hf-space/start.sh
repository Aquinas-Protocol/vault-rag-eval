#!/usr/bin/env bash
# Boot: start the Qdrant server, wait until ready, seed it from the committed
# fixtures (storage is ephemeral on Spaces), then serve the FastAPI app.
set -euo pipefail

export QDRANT__STORAGE__STORAGE_PATH=/tmp/qdrant/storage
mkdir -p "$QDRANT__STORAGE__STORAGE_PATH"

echo ">> starting qdrant server"
( cd /qdrant && exec ./qdrant ) &

python3 - <<'PY'
import time, urllib.request
for _ in range(60):
    try:
        urllib.request.urlopen("http://127.0.0.1:6333/readyz", timeout=2)
        print(">> qdrant ready"); break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("qdrant did not become ready")
PY

echo ">> seeding qdrant from committed fixtures"
python3 scripts/seed_stores.py --qdrant --recreate

echo ">> starting app on :7860"
exec uvicorn app.main:app --host 0.0.0.0 --port 7860
