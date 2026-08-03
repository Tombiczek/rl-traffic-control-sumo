#!/usr/bin/env bash
set -euo pipefail

METHOD_NAME="$1"   # actuated | fixed
SUMOCFG="$2"       # osm_actuated.sumocfg | osm_static.sumocfg
PORT="$3"          # 8813 | 8814

OUT="data/out/${METHOD_NAME}"
RESULTS="data/results_${METHOD_NAME}.csv"
mkdir -p "$OUT"

for route_file in data/T1/routes_*.rou.xml data/T2/routes_*.rou.xml \
                  data/T3/routes_*.rou.xml data/G1/routes_*.rou.xml; do
  folder=$(basename "$(dirname "$route_file")")
  case "$folder" in
    T1) demand="low" ;;
    T2) demand="medium" ;;
    T3) demand="high" ;;
    G1) demand="random" ;;
    *)  echo "Pomijam: $route_file"; continue ;;
  esac
  seed=$(basename "$route_file" | sed -E 's/.*_([0-9]+)\.rou\.xml/\1/')
  container="sumo-${METHOD_NAME}-${seed}"

  echo ">>> ${METHOD_NAME} | ${route_file} | demand=${demand} seed=${seed}"

  docker rm -f "$container" >/dev/null 2>&1 || true
  docker run --rm -d --name "$container" \
    --platform=linux/amd64 \
    -p "${PORT}:${PORT}" \
    -v "$PWD":/data -w /data \
    ghcr.io/eclipse-sumo/sumo:v1_25_0 \
    sumo -c "/data/data/${SUMOCFG}" \
      -r "/data/${route_file}" \
      --remote-port "${PORT}" \
      --seed "${seed}" \
      --no-warnings \
      --tripinfo-output "/data/${OUT}/tripinfo.xml" \
      --statistic-output "/data/${OUT}/statistic.xml" >/dev/null

  sleep 3

  TRACI_PORT="$PORT" METHOD="$METHOD_NAME" DEMAND="$demand" SEED="$seed" \
  OUT_DIR="$OUT" RESULTS_CSV="$RESULTS" \
    .venv/bin/python src/baseline/run_sim.py

  docker rm -f "$container" >/dev/null 2>&1 || true
done

echo "Gotowe: ${RESULTS}"