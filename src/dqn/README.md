# DQN SUMO module

Osobny moduł eksperymentalny do trenowania i ewaluacji sterownika sygnalizacji świetlnej z użyciem:

- `sumo-rl` jako warstwy integracji z SUMO,
- `stable-baselines3.DQN` jako gotowego algorytmu,
- formatu wyników zgodnego z baseline `fixed` / `actuated`.

## Założenia

- Domyślny `tls_id` i mapowanie pasów `N/S/E/W` odpowiadają obecnemu scenariuszowi z pracy.
- Dla innej sieci można nadpisać `--tls-id` i przekazać `--lane-map-file`.
- Ewaluacja zapisuje `tripinfo.xml`, `statistic.xml`, `summary.csv`, `timeseries.csv`, a potem dopisuje jeden wiersz do `results.csv` w tym samym układzie kolumn co baseline.

Przykładowy `lane-map-file` w JSON:

```json
{
  "N": ["lane_a", "lane_b"],
  "S": ["lane_c"],
  "E": ["lane_d"],
  "W": ["lane_e"]
}
```

## Build

```bash
docker build -f src/dqn/Dockerfile -t thesis-dqn .
```

## Trening

Przykład na wszystkich trasach z katalogów `T1` i `T2`:

```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  thesis-dqn train \
  --sumocfg-file /workspace/data/osm.sumocfg \
  --train-route-glob "/workspace/data/T1/routes_*.rou.xml" "/workspace/data/T2/routes_*.rou.xml" \
  --model-path /workspace/data/models/dqn/dqn_model.zip \
  --total-timesteps 50000
```

Jeżeli chcesz jawnie wskazać sieć zamiast korzystać z `sumocfg`:

```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  thesis-dqn train \
  --net-file /workspace/data/osm_fixed.net.xml \
  --train-route-glob "/workspace/data/T1/routes_*.rou.xml" \
  --model-path /workspace/data/models/dqn/dqn_model.zip
```

## Ewaluacja

Przykład zgodny z aktualnym baseline:

```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  thesis-dqn evaluate \
  --sumocfg-file /workspace/data/osm.sumocfg \
  --route-file /workspace/data/T3/routes_T3_305.rou.xml \
  --model-path /workspace/data/models/dqn/dqn_model.zip \
  --results-csv /workspace/data/results.csv \
  --out-dir /workspace/data/out \
  --method dqn \
  --demand high \
  --seed 305
```

Po ewaluacji:

- bieżące pliki wyjściowe trafiają do `/workspace/data/out`,
- następnie są archiwizowane do katalogu `/workspace/data/out/run_<demand>_<seed>_<method>`,
- do `/workspace/data/results.csv` dopisywany jest jeden nowy wiersz z tymi samymi kolumnami co baseline.

## Gdzie zapisuje się model

Domyślnie:

```text
/workspace/data/models/dqn/dqn_model.zip
```

Ścieżkę można zmienić przez `--model-path`.

## Upload do Hugging Face Hub

Upload jest opcjonalny i uruchamia się flagą `--upload-to-hub`.

Wymagane zmienne środowiskowe:

- `HF_TOKEN`
- `HF_REPO_ID`
- opcjonalnie `HF_PATH_IN_REPO`

Przykład:

```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  -e HF_TOKEN=hf_xxx \
  -e HF_REPO_ID=twoj-login/sumo-dqn \
  thesis-dqn train \
  --sumocfg-file /workspace/data/osm.sumocfg \
  --train-route-glob "/workspace/data/T1/routes_*.rou.xml" \
  --model-path /workspace/data/models/dqn/dqn_model.zip \
  --upload-to-hub
```

## Entrypoint

Kontener używa:

```bash
python -m src.dqn.entrypoint
```

Dostępne komendy:

- `train`
- `evaluate`
