#!/usr/bin/env bash
set -euo pipefail

MODEL="$1"        # np. data/models/dqn/dqn_final.zip
METHOD_NAME="$2"  # np. dqn

for route_file in data/T1/routes_*.rou.xml data/T2/routes_*.rou.xml \
                  data/T3/routes_*.rou.xml data/G1/routes_*.rou.xml; do
  folder=$(basename "$(dirname "$route_file")")
  case "$folder" in
    T1) demand="low" ;;
    T2) demand="medium" ;;
    T3) demand="high" ;;
    G1) demand="random" ;;
    *)  continue ;;
  esac
  seed=$(basename "$route_file" | sed -E 's/.*_([0-9]+)\.rou\.xml/\1/')

  echo ">>> ${METHOD_NAME} | ${route_file} | demand=${demand} seed=${seed}"

  docker run --rm -v "$PWD":/workspace --platform=linux/amd64 \
    thesis-dqn evaluate \
    --sumocfg-file /workspace/data/osm.sumocfg \
    --route-file "/workspace/${route_file}" \
    --model-path "/workspace/${MODEL}" \
    --results-csv "/workspace/data/results_${METHOD_NAME}.csv" \
    --out-dir "/workspace/data/out/${METHOD_NAME}" \
    --min-green 5 --yellow-time 3 --decision-interval 5 \
    --method "$METHOD_NAME" \
    --demand "$demand" \
    --seed "$seed"
done