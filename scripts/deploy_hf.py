"""Deploy the demo to a Hugging Face Docker Space.

Assembles the container build context (the app + its deps + committed fixtures +
the Space Dockerfile/start.sh/README) and pushes it to the Space repo, then sets
the Neon URL as a Space secret. The Space then builds the Dockerfile and runs the
qdrant server + the app.

    HF_SPACE=<user>/vault-rag-eval HF_TOKEN=<write-token> \
    NEON_DATABASE_URL=<pooled-url> python scripts/deploy_hf.py

Re-runnable: create_repo is idempotent and upload_folder overwrites.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi, create_repo

ROOT = Path(__file__).resolve().parents[1]
HF_SPACE = os.environ["HF_SPACE"]
TOKEN = os.environ["HF_TOKEN"]


def main() -> int:
    api = HfApi(token=TOKEN)
    create_repo(HF_SPACE, repo_type="space", space_sdk="docker", token=TOKEN, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        td = Path(tmp)
        for d in ("src", "app", "scripts", "fixtures"):
            shutil.copytree(ROOT / d, td / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy(ROOT / "pyproject.toml", td / "pyproject.toml")
        hf = ROOT / "deploy" / "hf-space"
        for f in ("Dockerfile", "start.sh", "README.md"):
            shutil.copy(hf / f, td / f)
        (td / ".gitattributes").write_text("* text=auto eol=lf\n", encoding="utf-8")
        api.upload_folder(
            folder_path=str(td), repo_id=HF_SPACE, repo_type="space",
            commit_message="deploy vault-rag-eval demo (qdrant server + app)",
        )

    neon = os.getenv("NEON_DATABASE_URL")
    if neon:
        api.add_space_secret(repo_id=HF_SPACE, key="NEON_DATABASE_URL", value=neon)
        print("set Space secret NEON_DATABASE_URL")
    print(f"pushed -> https://huggingface.co/spaces/{HF_SPACE}  (building…)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
