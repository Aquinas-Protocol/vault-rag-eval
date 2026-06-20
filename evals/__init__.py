"""Keyless retrieval-eval harness.

Drives the real ``vrag.retrieve.search()`` with cached query embeddings and scores
page-level (slug) relevance against a reviewed gold set. The only step that needs
Ollama is embedding a gold query on a cache miss; in keyless mode (CI) a miss is a
hard error, so the whole eval runs with no daemon and no key.
"""
