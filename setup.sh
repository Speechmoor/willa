#!/usr/bin/env bash
# Bring a fresh clone to the point where `./run.sh` works.
#
#   ./setup.sh              English only, about 6 GB of model downloads
#   ./setup.sh --translate  adds the nine-language pipeline, about 2.4 GB more
#   ./setup.sh --check      report what is missing and change nothing
#
# Safe to re-run. Every step is skipped if it has already been done.

set -euo pipefail
cd "$(dirname "$0")"

TRANSLATE=0
CHECK=0
for arg in "$@"; do
  case "$arg" in
    --translate) TRANSLATE=1 ;;
    --check)     CHECK=1 ;;
    -h|--help)   sed -n '2,10p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

ok()   { printf '  \033[32mok\033[0m    %s\n' "$1"; }
todo() { printf '  \033[33mtodo\033[0m  %s\n' "$1"; }
bad()  { printf '  \033[31mfail\033[0m  %s\n' "$1"; }
step() { printf '\n\033[1m%s\033[0m\n' "$1"; }

MISSING=0
need() { if [ "$CHECK" = 1 ]; then todo "$1"; MISSING=1; return 1; fi; return 0; }

# --- Python ----------------------------------------------------------------
# pydantic-core has no 3.14 wheels, so pip compiles it from Rust and PyO3
# rejects the interpreter. Pick an interpreter we know works.
step "Python"
PY=""
for c in python3.13 python3.12 python3.11 python3; do
  command -v "$c" >/dev/null 2>&1 || continue
  v=$("$c" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
  case "$v" in 3.11|3.12|3.13) PY="$c"; break ;; esac
done
if [ -z "$PY" ]; then
  bad "need Python 3.11, 3.12 or 3.13 (3.14 cannot build pydantic-core)"
  echo "        macOS:  brew install python@3.12"
  echo "        Ubuntu: sudo apt install python3.12 python3.12-venv"
  # Under --check, keep going so one run reports everything that is missing.
  if [ "$CHECK" = 1 ]; then MISSING=1; else exit 1; fi
else
  ok "$PY ($("$PY" -c 'import sys; print(sys.version.split()[0])'))"
fi

# --- virtualenv and dependencies -------------------------------------------
step "Dependencies"
if [ -d .venv ]; then ok ".venv exists"
elif [ -n "$PY" ]; then
  if need "create .venv"; then "$PY" -m venv .venv; ok "created .venv"; fi
else
  todo "create .venv"; MISSING=1
fi
if [ -d .venv ] && [ -x .venv/bin/python ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
  if python -c 'import fastapi, uvicorn, numpy, pydantic, httpx, pypdf, cryptography' 2>/dev/null; then
    ok "requirements.txt satisfied"
  elif need "pip install -r requirements.txt"; then
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    ok "installed requirements.txt"
  fi
  if [ "$TRANSLATE" = 1 ]; then
    if python -c 'import torch, transformers, sentencepiece' 2>/dev/null; then
      ok "translation extras satisfied"
    elif need "pip install -r requirements-translate.txt"; then
      pip install --quiet -r requirements-translate.txt
      ok "installed translation extras"
    fi
  fi
fi

# --- Ollama ----------------------------------------------------------------
step "Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  bad "ollama is not installed — https://ollama.com/download"
  [ "$CHECK" = 1 ] && MISSING=1 || exit 1
else
  ok "ollama installed"
  if curl -fsS --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    ok "ollama is serving on 127.0.0.1:11434"
    for m in qwen3:8b nomic-embed-text; do
      if ollama list 2>/dev/null | awk '{print $1}' | grep -qx "$m"; then
        ok "$m"
      elif need "ollama pull $m"; then
        echo "        pulling $m, this is the large one..."
        ollama pull "$m"
        ok "pulled $m"
      fi
    done
  else
    bad "ollama is installed but not serving — run 'ollama serve' in another terminal"
    [ "$CHECK" = 1 ] && MISSING=1 || exit 1
  fi
fi

# --- corpus and index ------------------------------------------------------
# The Acts and Rules are committed, so a clone does not need the network for
# them. The index is derived and is rebuilt here, because a stale index fails
# silently by returning plausible passages from the wrong text.
step "Corpus and index"
if [ -s corpus/Small_Claims_Courts_Act_61_of_1984.pdf ]; then
  ok "corpus present ($(ls corpus/*.pdf | wc -l | tr -d ' ') documents, committed)"
else
  if need "python scripts/fetch_corpus.py"; then
    python scripts/fetch_corpus.py; ok "fetched corpus"
  fi
fi
if [ -s data/index.npz ] && [ data/index.npz -nt corpus/Small_Claims_Courts_Act_61_of_1984.pdf ]; then
  ok "index built"
elif need "python scripts/ingest.py"; then
  python scripts/ingest.py
  ok "built index"
fi

# --- translator ------------------------------------------------------------
if [ "$TRANSLATE" = 1 ]; then
  step "Translator"
  if [ -d models ] && [ -n "$(ls -A models 2>/dev/null)" ]; then
    ok "NLLB present in models/"
  elif need "python scripts/fetch_translator.py"; then
    echo "        downloading NLLB-200-distilled-600M, about 2.4 GB..."
    python scripts/fetch_translator.py
    python scripts/build_ui_translations.py
    python scripts/fetch_reference.py
    ok "translator ready"
  fi
fi

# --- done ------------------------------------------------------------------
if [ "$CHECK" = 1 ]; then
  if [ "$MISSING" = 1 ]; then
    printf '\n\033[33mNot ready.\033[0m Run ./setup.sh to do the steps marked todo.\n'; exit 1
  fi
  printf '\n\033[32mReady.\033[0m Run ./run.sh\n'; exit 0
fi

printf '\n\033[32mReady.\033[0m\n\n'
echo "  ./run.sh                     start Willa on http://127.0.0.1:8000"
echo "  python scripts/check_rules.py  the statutory gate, 26 fixtures, instant"
[ "$TRANSLATE" = 0 ] && echo "  ./setup.sh --translate       add the other eight languages"
echo
