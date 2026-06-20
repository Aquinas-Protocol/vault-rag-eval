# vault-rag-eval — reproducible, keyless build.
#
#   make install   editable install (vrag package + dev deps)
#   make fixtures  rebuild index + manifest + query embeddings from corpus/
#   make eval      score the gold set, keyless, gate on baseline
#   make test      provenance + unit tests
#   make scan      denylist tripwire over corpus + committed JSON
#
# `fixtures` needs Ollama up (it embeds on cache miss). Everything else is keyless:
# embeddings are served from the committed content-addressed cache, and a miss is
# a hard error.

PY ?= python

.PHONY: install fixtures fixtures-keyless eval test scan clean

install:
	$(PY) -m pip install -e ".[dev]"

fixtures:
	$(PY) scripts/make_fixtures.py

fixtures-keyless:
	$(PY) scripts/make_fixtures.py --keyless

eval:
	$(PY) -m evals.run --keyless --gate

test:
	$(PY) -m pytest -q

scan:
	$(PY) scripts/denylist_scan.py

clean:
	$(PY) -c "import shutil,glob,os; [shutil.rmtree(p,ignore_errors=True) for p in glob.glob('**/__pycache__',recursive=True)+['.pytest_cache']]"
