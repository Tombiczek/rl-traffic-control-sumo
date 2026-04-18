Generowanie plików które definiują napływ pojazdów:
```bash
docker run --rm -v "$PWD/data":/data ghcr.io/eclipse-sumo/sumo:v1_25_0 \
  python3 /usr/share/sumo/tools/randomTrips.py \
    -n /data/osm.net.xml.gz \
    -o /data/trips_T1.trips.xml \
    --route-file /data/routes_T1.rou.xml \
    -e 3600 \
    --period 5.0 \
    --seed 101
```
Flaga `--period` kontroluje natężenie ruchu. Wartość na przykład `5.0` oznacza że generujemy pojazd średnio raz na 5 sekund.

Ustaliliśmy wstępnie, że:
- period 5.0 -> mały ruch (T1)
- period 2.5 -> 2x większy (T2)
- period 1.25 -> 4x większy (T3)

I na ten moment powinno to sensownie symulować mały/średni/duży ruch na skrzyżowaniu.

Jeszcze generowanie losowego ruchu:
```bash
seeds=(401 402 403 404 405)
for i in {0..4}; do
  docker run --rm -v "$PWD/data":/data ghcr.io/eclipse-sumo/sumo:v1_25_0 \
    python3 /usr/share/sumo/tools/randomTrips.py \
      -n /data/osm.net.xml.gz \
      -o /data/G1/trips_G1_${seeds[$i]}.trips.xml \
      --route-file /data/G1/routes_G1_${seeds[$i]}.rou.xml \
      -e 3600 \
      --period 5.0 2.5 1.25 \
      --random-depart \
      --binomial 4 \
      --seed ${seeds[$i]}
done
```
---

Aby zrobić sanity-check i uruchomić symulację bez TraCI w konsoli używając obrazu dockerowego wykonujemy komendę:
```bash
docker compose run --rm sumo \
  sumo -c /data/data/osm.sumocfg --seed 42 --no-warnings --quit-on-end
```
Zależnie jaki napływ pojazdów będzie akurat zdefiniowany w `osm.sumocofig` taka symulacja się uruchomi.
To uruchamia się wtedy w trybie `actuated` tak jak jest to zdefiniowane w pliku `osm.net.xml`.

Wynik dla tego sanity checku to jest (Dla T1):
```bash
Simulation ended at time: 3674.00.
Reason: All vehicles have left the simulation.
Performance:
 Duration: 0.21s
 Real time factor: 17412.3
 UPS: 178791.469194
Vehicles:
 Inserted: 720
 Running: 0
 Waiting: 0
Statistics (avg of 720):
 RouteLength: 463.31
 Speed: 9.01
 Duration: 52.40
 WaitingTime: 7.27
 TimeLoss: 17.66
 DepartDelay: 0.09
```


Zapasowe komendy które można dodać do `docker-compose.yml`
```bash
--summary-output /data/data/out/sumo_summary.xml
--queue-output /data/data/out/queue.xml
```
---

```bash
docker compose up -d sumo
.venv/bin/python src/run_sim.py
```

Literatura: [DEVELOPMENT OF A TRAFFIC SIGNAL PERFORMANCE MEASUREMENT SYSTEM (TSPMS)](https://www.researchgate.net/profile/Kevin-Balke/publication/265992572_DEVELOPMENT_OF_A_TRAFFIC_SIGNAL_PERFORMANCE_MEASUREMENT_SYSTEM_TSPMS/links/54be97660cf28ce68e69d8f5/DEVELOPMENT-OF-A-TRAFFIC-SIGNAL-PERFORMANCE-MEASUREMENT-SYSTEM-TSPMS.pdf)
### Metryki zgodne z literaturą
- `time`
- `phase`
- `queue_N`, `queue_S`, `queue_E`, `queue_W`
- `queue_total`
- `vehicles per cycle` (to jest podane w pliku `statistics.xml`)

**Congestion metrics**
(To wszystko można policzyć ze zbieranych wcześniej kolejek z każdego kierunku)
- `mean queue length`
- `max queue length`
- `mean queue per approach`
- `max queue per approach`

**Delay metrics**
- `mean waiting time` z pliku `tripinfo.xml` mogę wyciągnąć dla każdego pojazdu `waitingTime`
- `mean delay (timeLoss)` z pliku `tripinfo.xml` mogę wyciągnąć dla każdego pojazdu `timeLoss`

**Fairness**
- `95 percentile waiting time` tak samo z pliku `tripinfo.xml` mogę wyciągnąć dla każdego pojazdu `waitingTime`
- `max waiting time` tak samo z pliku `tripinfo.xml` mogę wyciągnąć dla każdego pojazdu `waitingTime`

**Flow**
- `throughput` czyli liczba pojazdów, która opuszcza skrzyżowanie w godzinę. Można spokojnie policzyć to z pliku `tripinfo.xml`

Wniosek jest taki, że zbieram już wszystkie potrzebne dane. Z moich czterech metryk plus `tripinfo.xml` jestem wstanie wyliczyć wszystko to czego potrzebuje.

---
Zbudowanie obrazu:
```bash
docker build -f src/dqn/Dockerfile -t thesis-dqn .
```


Uruchamianie treningu DQN:
```bash
docker run --rm -it \
  --env-file .env \
  -v "$PWD":/workspace \
  --platform=linux/amd64 \
  thesis-dqn train \
  --sumocfg-file /workspace/data/osm.sumocfg \
  --train-route-glob "/workspace/data/train/fixed/routes_train_*.rou.xml" \
  --config-file /workspace/src/dqn/base_config.yml \
  --model-path /workspace/data/models/dqn/dqn_fixed_base_5k.zip \
```

Uruchomienie ewaluacji modelu DQN na zbiorze walidacyjnym:
```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  thesis-dqn evaluate \
  --sumocfg-file /workspace/data/osm.sumocfg \
  --route-file /workspace/data/T3/routes_T3_305.rou.xml \
  --model-path /workspace/data/models/dqn/dqn_fixed_base_5k.zip \
  --validate

```

Uruchamianie ewaluacji modelu DQN:
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