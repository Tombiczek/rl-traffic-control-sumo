#!/usr/bin/env bash
# Trening wariantow hiperparametrow z kolejka zadan.
#
#   MAX_PARALLEL=4 TRAIN_SET=fixed ./run_train_configs.sh
#
# TRAIN_SET: fixed | randomized  (zbior treningowy wybrany na etapie walidacji)

set -uo pipefail

MAX_PARALLEL="${MAX_PARALLEL:-4}"
TRAIN_SET="${TRAIN_SET:-fixed}"
# Docker ma ~7,6 GiB; jeden trening zajmuje ~1,2 GiB w stanie ustalonym.
MEM_LIMIT_GIB="${MEM_LIMIT_GIB:-5.5}"

CONFIGS=(
  batch128
  buffer1e5
  explore1e-1
  gamma98e-2
  lr3e-4
  lr5e-4
  lr3e-4_gamma98e-2
  tui1e3
)

LOG_DIR="logs/train_${TRAIN_SET}"
mkdir -p "$LOG_DIR" data/models/finetune

ile_dziala() { docker ps --filter "name=train-" --format '{{.Names}}' | grep -c . || true; }

pamiec_gib() {
  docker stats --no-stream --format '{{.MemUsage}}' 2>/dev/null \
    | awk -F'/' '{print $1}' \
    | awk '/GiB/{s+=$1} /MiB/{s+=$1/1024} END{printf "%.2f", s+0}'
}

czekaj_na_slot() {
  while :; do
    local n mem
    n=$(ile_dziala); mem=$(pamiec_gib)
    if [ "$n" -lt "$MAX_PARALLEL" ] && awk "BEGIN{exit !($mem < $MEM_LIMIT_GIB)}"; then
      return
    fi
    printf '\r%s  zajete: %s/%s slotow, RAM %s/%s GiB, czekam...' \
      "$(date +%H:%M:%S)" "$n" "$MAX_PARALLEL" "$mem" "$MEM_LIMIT_GIB"
    sleep 30
  done
}

echo "Zbior treningowy: ${TRAIN_SET} | limit rownoleglosci: ${MAX_PARALLEL} | limit RAM: ${MEM_LIMIT_GIB} GiB"
echo "Logi: ${LOG_DIR}/"
echo

URUCHOMIONE=()
for cfg in "${CONFIGS[@]}"; do
  czekaj_na_slot
  name="train-${cfg}"
  docker rm -f "$name" >/dev/null 2>&1 || true

  docker run -d --name "$name" \
    --env-file .env \
    -v "$PWD":/workspace \
    --platform=linux/amd64 \
    thesis-dqn train \
    --sumocfg-file /workspace/data/osm.sumocfg \
    --train-route-glob "/workspace/data/train/${TRAIN_SET}/routes_train_*.rou.xml" \
    --config-file "/workspace/src/dqn/configs/config_${cfg}.yml" \
    --model-path "/workspace/data/models/finetune/dqn_${TRAIN_SET}_${cfg}_225k.zip" \
    --checkpoint-freq 0 >/dev/null

  URUCHOMIONE+=("$name")
  printf '\r%s  start: %-28s (%s/%s slotow, RAM %s GiB)\n' \
    "$(date +%H:%M:%S)" "$name" "$(ile_dziala)" "$MAX_PARALLEL" "$(pamiec_gib)"
  sleep 10
done

echo
echo "Wszystkie zadania zakolejkowane. Oczekiwanie na zakonczenie..."
for name in "${URUCHOMIONE[@]}"; do
  kod=$(docker wait "$name" 2>/dev/null || echo "?")
  docker logs "$name" > "${LOG_DIR}/${name}.log" 2>&1 || true
  if [ "$kod" = "0" ]; then
    echo "$(date +%H:%M:%S)  OK    ${name}"
  else
    echo "$(date +%H:%M:%S)  BLAD  ${name} (kod ${kod}) -> ${LOG_DIR}/${name}.log"
  fi
done

echo
echo "Modele:"
ls -la data/models/finetune/ | grep "${TRAIN_SET}" || echo "  brak"
echo
echo "Sprzatanie zatrzymanych kontenerow:  docker rm \$(docker ps -aq --filter 'name=train-' --filter 'status=exited')"
