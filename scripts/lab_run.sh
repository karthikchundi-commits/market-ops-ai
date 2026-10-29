#!/usr/bin/env bash
# One-command lab runner (BITS virtual lab / any Linux VM, CPU only).
#
#   bash scripts/lab_run.sh all       # setup -> env -> data -> train -> index -> eval -> serve
#   bash scripts/lab_run.sh <step>    # setup | env | data | train | index | eval | serve | stop | curl
#
# Logs go to logs/<step>.log and are also printed, so each step can be screenshotted.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
PY=.venv/bin/python
export PYTHONIOENCODING=utf-8 TOKENIZERS_PARALLELISM=false

# Pick a local LLM that fits the VM's memory (1.5B needs ~8 GB free in float32).
mem_gb=$(awk '/MemTotal/ {printf "%d", $2/1048576}' /proc/meminfo)
if [ -z "${LOCAL_LLM:-}" ]; then
  if [ "$mem_gb" -ge 14 ]; then export LOCAL_LLM=Qwen/Qwen2.5-1.5B-Instruct
  else export LOCAL_LLM=Qwen/Qwen2.5-0.5B-Instruct; fi
fi

banner() { printf '\n==================== %s ====================\n' "$1"; }

setup() {
  banner "SETUP"
  python3 -m venv .venv
  $PY -m pip install -q --upgrade pip
  $PY -m pip install -q -r requirements.txt
  $PY -c "import torch, transformers, faiss, streamlit, fastapi; print('torch', torch.__version__, '| transformers', transformers.__version__, '| streamlit', streamlit.__version__)"
}

env_info() {
  banner "LAB ENVIRONMENT"
  echo "user: $(whoami)   host: $(hostname)   date: $(date)"
  grep PRETTY_NAME /etc/os-release || true
  echo "CPUs: $(nproc)"; free -h | head -2
  $PY --version
  $PY -c "import torch; print('torch', torch.__version__, '| CUDA available:', torch.cuda.is_available())"
  echo "LOCAL_LLM=$LOCAL_LLM  LLM_BACKEND=${LLM_BACKEND:-auto}"
}

data()  { banner "PART II - DATASET";     $PY data/generate_tickets.py 2>&1 | tee logs/data.log; }
train() { banner "PART II - FINE-TUNING"; $PY training/finetune_classifier.py --epochs "${EPOCHS:-3}" 2>&1 | grep -vE "it/s\]|s/it\]" | tee logs/train.log; }
index() { banner "PART III - RAG INDEX";  $PY rag/build_index.py 2>&1 | grep -vE "it/s\]|s/it\]" | tee logs/index.log; }
evaluate() { banner "PART IV - EVALUATION"; $PY scripts/evaluate.py 2>&1 | grep -vE "it/s\]|s/it\]|Warning|warn" | tee logs/eval.log; }

serve() {
  banner "START API + UI"
  stop >/dev/null 2>&1 || true
  nohup $PY -m uvicorn app.api:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
  nohup $PY -m streamlit run app/ui.py --server.headless true --server.port 8501 \
        --browser.gatherUsageStats false > logs/ui.log 2>&1 &
  for _ in $(seq 1 60); do curl -sf localhost:8000/health >/dev/null && break; sleep 2; done
  curl -s localhost:8000/health; echo
  echo "API docs: http://localhost:8000/docs"
  echo "Web UI  : http://localhost:8501"
}

stop() { pkill -f "uvicorn app.api:app" || true; pkill -f "streamlit run app/ui.py" || true; echo "stopped"; }

curl_demo() {
  banner "REST API CALLS"
  set -x
  curl -s -w '\nHTTP %{http_code}\n' localhost:8000/health
  curl -s -w '\nHTTP %{http_code}\n' -X POST localhost:8000/classify -H 'Content-Type: application/json' \
       -d '{"text":"Invoice INV-551902 for September shows administrative charges 18% higher than August; please provide a breakdown."}'
  curl -s -w '\nHTTP %{http_code}\n' -X POST localhost:8000/extract -H 'Content-Type: application/json' \
       -d '{"text":"CT-3 tripped at HE14 on 2026-09-21 due to a transformer fault at BRIDGEPORT 138KV; forced outage of 180 MW."}'
  curl -s -w '\nHTTP %{http_code}\n' -X POST localhost:8000/classify -H 'Content-Type: application/json' -d '{"text":""}'
  { set +x; } 2>/dev/null
}

case "${1:-all}" in
  setup) setup ;; env) env_info ;; data) data ;; train) train ;; index) index ;;
  eval) evaluate ;; serve) serve ;; stop) stop ;; curl) curl_demo ;;
  all) setup; env_info; data; train; index; evaluate; serve; curl_demo ;;
  *) echo "unknown step: $1"; exit 1 ;;
esac
