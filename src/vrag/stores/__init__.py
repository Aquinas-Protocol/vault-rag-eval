"""Cloud store adapters: Qdrant (dense vectors) and Postgres (metadata + tsvector
lexical arm). The in-process backend in ``vrag.retrieve`` mirrors these for dev and
the fast keyless eval; these are what the deployed FastAPI service talks to.
"""
