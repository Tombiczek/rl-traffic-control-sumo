# Uruchamianie eksperymentów

Zestaw komend do przeprowadzenia całego eksperymentu po korekcie programu sygnalizacji.
Wszystkie polecenia uruchamiaj z katalogu głównego repozytorium.

---

## 0. Stan wyjściowy

### Pliki sieci

| Plik | Program | Zastosowanie |
|---|---|---|
| `data/osm.net.xml` | `actuated`, `minDur=5`, `maxDur=50` | sterowanie akomodacyjne |
| `data/osm_fixed.net.xml` | `static`, cykl 81 s | sterowanie stałoczasowe oraz agent DQN |

Oba pliki mają identyczną geometrię i ten sam układ trzech faz zielonych:

```
faza 0 (14s)  rrrrGGGrrrrrGGGr   KEN: w prawo i na wprost, lewoskręt czerwony
faza 1  (3s)  rrrryyyrrrrryyyr   żółte
faza 2 (29s)  rrrrrrrGrrrrrrrG   KEN: bezkolizyjny lewoskręt
faza 3  (3s)  rrrrrrryrrrrrrry   żółte
faza 4 (29s)  GGGgrrrrGGGgrrrr   Belgradzka: trzy kierunki, lewoskręt warunkowy
faza 5  (3s)  yyyyrrrryyyyrrrr   żółte
```

Indeksy sygnałów: `0-3` Belgradzka wsch., `4-7` al. KEN płn., `8-11` Belgradzka zach., `12-15` al. KEN płd.
W każdej grupie kolejność: w prawo, na wprost, na wprost, w lewo.

### Dobór parametrów sterowania referencyjnego

Parametry obu metod referencyjnych wyznaczono **wyłącznie na podstawie zbioru
treningowego**, na scenariuszach o dużym natężeniu (`data/train/fixed/routes_train_heavy_*`).
Zbiór testowy nie był w tym celu wykorzystywany, dzięki czemu żadna z porównywanych
metod nie miała wcześniejszego kontaktu z danymi testowymi.

Czasy zielone wyznaczono proporcjonalnie do natężeń pasa krytycznego, przy nasyceniu
1800 poj./h na pas i cyklu 81 s:

| Faza | Pas krytyczny | Natężenie krytyczne $y$ | Czas zielony | `maxDur` |
|---|---|---|---|---|
| A: KEN prosto i w prawo | 229 poj./h | 0,127 | 14 s | 21 s |
| B: KEN lewoskręt | 463 poj./h | 0,257 | 29 s | 43 s |
| C: Belgradzka | 477 poj./h | 0,265 | 29 s | 44 s |
| suma $Y$ | | 0,649 | cykl 81 s | |

Podział okazał się stabilny względem doboru danych, co potwierdza jego odporność:

| Zbiór | A | B | C | $Y$ |
|---|---|---|---|---|
| treningowy regularny | 14 s | 29 s | 29 s | 0,649 |
| treningowy losowy | 14 s | 28 s | 29 s | 0,604 |
| walidacyjny | 14 s | 29 s | 30 s | 0,661 |

Dla sterowania akomodacyjnego wartość `maxDur` ustawiono jako około 1,5-krotność
zaprojektowanego czasu zielonego, zamiast domyślnej dla SUMO wartości 50 s jednakowej
dla wszystkich faz. Domyślna wartość pozwalała fazie A wydłużać się do 50 s, mimo że
jej zapotrzebowanie wynosi 14 s, co przy nasyceniu odbierało czas pozostałym fazom.
Obie metody referencyjne są więc dostrojone do porównywalnego standardu praktyki
projektowej i żadna nie jest sztucznie osłabiona.

Lewoskręt z południowego wlotu al. KEN jest najcięższą relacją na skrzyżowaniu.
Wynika to z syntetycznego charakteru ruchu generowanego przez `randomTrips.py`,
który losuje pary źródło-cel równomiernie, i nie odpowiada rozkładowi ruchu
typowemu dla arterii.

> **Parametry metod referencyjnych są od tego momentu zamrożone.** Dalsze ich
> strojenie po zobaczeniu wyników agenta DQN oznaczałoby dopasowywanie punktu
> odniesienia do rezultatu.

### Konfiguracje SUMO

| Plik | Sieć | Zastosowanie |
|---|---|---|
| `data/osm_actuated.sumocfg` | `osm.net.xml` | metoda akomodacyjna |
| `data/osm_static.sumocfg` | `osm_fixed.net.xml` | metoda stałoczasowa |
| `data/osm.sumocfg` | `osm_fixed.net.xml` | trening i ewaluacja DQN |

### Skutki zmiany programu sygnalizacji

Trzy fazy zielone zamiast czterech oznaczają:

- przestrzeń akcji `Discrete(3)`
- obserwacja **30-wymiarowa** zamiast 31

Wszystkie modele trzeba wytrenować od nowa. Pliki tras pozostają ważne i nie wymagają ponownego wygenerowania.

---

## 1. Weryfikacja przed startem

### Środowisko Pythona

Dowiązanie `.venv/bin/python` wskazuje na `/opt/homebrew/opt/python@3.13`, którego
już nie ma, ponieważ Homebrew podniósł wersję Pythona. Skrypty metod referencyjnych
uruchamiają `run_sim.py` lokalnie, więc środowisko trzeba odtworzyć:

```bash
rm -rf .venv
uv sync          # albo: python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -c "import traci; print('traci OK')"
```

### Sanity check obu sieci

Szybkie uruchomienie bez TraCI:

```bash
# akomodacyjne
docker run --rm --platform=linux/amd64 -v "$PWD":/data -w /data \
  ghcr.io/eclipse-sumo/sumo:v1_25_0 \
  sumo -c /data/data/osm_actuated.sumocfg \
    -r /data/data/T3/routes_T3_301.rou.xml \
    --seed 301 --no-warnings --quit-on-end

# stałoczasowe
docker run --rm --platform=linux/amd64 -v "$PWD":/data -w /data \
  ghcr.io/eclipse-sumo/sumo:v1_25_0 \
  sumo -c /data/data/osm_static.sumocfg \
    -r /data/data/T3/routes_T3_301.rou.xml \
    --seed 301 --no-warnings --quit-on-end
```

Porównaj `TimeLoss` i `WaitingTime` z wynikami sprzed zmiany. Jeżeli dla sterowania
stałoczasowego wyraźnie wzrosły, sprawdź kolejkę na pasie lewoskrętu al. KEN.
Lewoskręt ma teraz tylko 6 s na cykl 81 s i nie może już jechać warunkowo w fazie głównej.
W razie potrzeby przesuń kilka sekund z fazy 33 s na fazę 6 s w obu plikach sieci jednocześnie.

---

## 2. Metody referencyjne, oba warianty równolegle

Skrypt przyjmuje nazwę metody, konfigurację SUMO i port TraCI, więc oba warianty
mogą działać jednocześnie w osobnych kontenerach i na osobnych portach.

Zapisz jako `scripts/run_baseline.sh`:

```bash
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
```

Nadanie uprawnień:

```bash
chmod +x run_baseline.sh
```

Uruchomienie obu wariantów jednocześnie:

```bash
./run_baseline.sh actuated osm_actuated.sumocfg 8813 &
./run_baseline.sh fixed    osm_static.sumocfg   8814 &
wait
```

Scalenie wyników w jeden plik:

```bash
{ head -1 data/results_actuated.csv; tail -n +2 -q data/results_*.csv; } > data/results.csv
wc -l data/results.csv   # oczekiwane 41 wierszy: naglowek + 2 x 20
```

---

## 3. Trening DQN

Konfiguracje leżą w `src/dqn/configs/`. Budowa obrazu:

```bash
docker build -f src/dqn/Dockerfile -t thesis-dqn .
```

### Konfiguracja bazowa, oba zbiory treningowe równolegle

Trening zapisuje checkpointy co 25 000 kroków do `data/models/checkpoints/`.
Nazwa pliku powstaje z prefiksu i numeru kroku, na przykład
`dqn_fixed_base_300k_25000_steps.zip`. Domyślnym prefiksem jest nazwa pliku modelu,
można ją nadpisać opcją `--checkpoint-prefix`. Wartość `--checkpoint-freq 0` wyłącza
zapisywanie checkpointów.

```bash
docker run --rm -d --name train-fixed \
  --env-file .env -v "$PWD":/workspace --platform=linux/amd64 \
  thesis-dqn train \
  --sumocfg-file /workspace/data/osm.sumocfg \
  --train-route-glob "/workspace/data/train/fixed/routes_train_*.rou.xml" \
  --config-file /workspace/src/dqn/configs/base_config.yml \
  --model-path /workspace/data/models/dqn/dqn_fixed_base_300k.zip \
  --checkpoint-dir /workspace/data/models/checkpoints \
  --checkpoint-freq 25000 \
  --checkpoint-prefix dqn_fixed

docker run --rm -d --name train-random \
  --env-file .env -v "$PWD":/workspace --platform=linux/amd64 \
  thesis-dqn train \
  --sumocfg-file /workspace/data/osm.sumocfg \
  --train-route-glob "/workspace/data/train/randomized/routes_train_*.rou.xml" \
  --config-file /workspace/src/dqn/configs/base_config.yml \
  --model-path /workspace/data/models/dqn/dqn_random_base_300k.zip \
  --checkpoint-dir /workspace/data/models/checkpoints \
  --checkpoint-freq 25000 \
  --checkpoint-prefix dqn_random
```

Kontrola zapisanych checkpointów w trakcie treningu:

```bash
ls -1 data/models/checkpoints/ | sort -t_ -k3 -n
```

Podgląd postępu i oczekiwanie na koniec:

```bash
docker logs -f train-fixed
docker wait train-fixed train-random
```

### Warianty hiperparametrów

Każdy wariant to osobny kontener. Uruchamiaj tyle naraz, ile udźwignie maszyna.

### Warianty hiperparametrów

Osiem wariantów uruchamia skrypt `run_train_configs.sh` z kolejką zadań. Nie startuje
wszystkiego naraz, tylko pilnuje limitu równoległości oraz zużycia pamięci przez
kontenery, i dokłada kolejne zadanie dopiero po zwolnieniu zasobów.

```bash
chmod +x run_train_configs.sh
MAX_PARALLEL=4 TRAIN_SET=fixed ./run_train_configs.sh
```

Parametry:

| Zmienna | Domyślnie | Znaczenie |
|---|---|---|
| `MAX_PARALLEL` | `4` | ile treningów naraz |
| `TRAIN_SET` | `fixed` | `fixed` albo `randomized`, zgodnie z wyborem po walidacji |
| `MEM_LIMIT_GIB` | `5.5` | próg łącznego zużycia pamięci przez kontenery |

Skrypt liczy wszystkie kontenery o nazwie `train-*`, więc uwzględnia także trwające
treningi konfiguracji bazowej i nie przekroczy limitu.

Warianty porównuje się na modelu końcowym po 225 000 kroków, dlatego checkpointy są
tu zbędne i wyłączone przez `--checkpoint-freq 0`.

### Dobór liczby równoległych treningów

Ograniczeniem jest pamięć, nie procesor. Pomiary na maszynie docelowej:

| Zasób | Wartość |
|---|---|
| rdzenie dostępne dla Dockera | 10 |
| pamięć dostępna dla Dockera | 7,65 GiB |
| zużycie CPU przez jeden trening | ~115% |
| zużycie pamięci przez jeden trening | ~1,0 do 1,2 GiB |
| tempo uczenia | ~44 kroki/s przy dwóch treningach |

Procesor wystarczyłby na osiem treningów, ale pamięć pozwala bezpiecznie na cztery
do pięciu. Przy czterech równoległych osiem wariantów po 225 000 kroków zajmuje
około trzech godzin.

Monitorowanie w trakcie:

```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
docker logs -f train-lr3e-4 | grep -E "total_timesteps|fps"
```

Sprzątanie po zakończeniu:

```bash
docker rm $(docker ps -aq --filter 'name=train-' --filter 'status=exited')
```

Kontrola:

```bash
docker ps --filter "name=train-" --format "table {{.Names}}\t{{.Status}}"
```

---

## 4. Walidacja

> **Ważne.** Parametr `--min-green 5` musi być podany jawnie. Domyślna wartość
> w skrypcie ewaluacyjnym to 10, a trening odbywa się przy 5. Rozjazd tych wartości
> był błędem poprzedniej serii eksperymentów i nie może się powtórzyć.

### Wybór długości treningu na podstawie checkpointów

```bash
for model in data/models/checkpoints/*.zip; do
  for route_file in data/valid/routes_valid_*.rou.xml; do
    echo ">>> $(basename "$model") | $(basename "$route_file")"
    docker run --rm -v "$PWD":/workspace --platform=linux/amd64 \
      thesis-dqn evaluate \
      --sumocfg-file /workspace/data/osm.sumocfg \
      --route-file "/workspace/${route_file}" \
      --model-path "/workspace/${model}" \
      --min-green 5 --yellow-time 3 --decision-interval 5 \
      --validate
  done
done
```

### Warianty hiperparametrów

```bash
for model in data/models/finetune/*.zip; do
  for route_file in data/valid/routes_valid_*.rou.xml; do
    echo ">>> $(basename "$model") | $(basename "$route_file")"
    docker run --rm -v "$PWD":/workspace --platform=linux/amd64 \
      thesis-dqn evaluate \
      --sumocfg-file /workspace/data/osm.sumocfg \
      --route-file "/workspace/${route_file}" \
      --model-path "/workspace/${model}" \
      --min-green 5 --yellow-time 3 --decision-interval 5 \
      --validate
  done
done
```

Wyniki trafiają do `data/validation_results.csv`. Na ich podstawie wybierasz model końcowy.
Zbioru testowego na tym etapie nie dotykasz.

---

## 5. Ewaluacja testowa

Uruchamiaj dopiero po zamrożeniu konfiguracji modelu końcowego.

Zapisz jako `scripts/run_dqn_test.sh`:

```bash
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
```

Uruchomienie modelu końcowego oraz modelu niestabilnego równolegle:

```bash
chmod +x scripts/run_dqn_test.sh
./scripts/run_dqn_test.sh data/models/dqn/dqn_final.zip          dqn &
./scripts/run_dqn_test.sh data/models/finetune/dqn_fixed_tui1e3_225k.zip dqn-tui-1e3 &
wait
```

Scalenie wszystkich wyników:

```bash
{ head -1 data/results_actuated.csv; tail -n +2 -q data/results_*.csv; } > data/results.csv
```

---

## 6. Kontrola wyników

Szybkie podsumowanie po metodach:

```bash
python3 -c "
import csv, collections, statistics as st
rows=list(csv.DictReader(open('data/results.csv')))
agg=collections.defaultdict(list)
for r in rows: agg[r['method']].append(r)
print(f\"{'metoda':<14}{'n':>4}{'opoznienie':>12}{'oczekiwanie':>13}{'kolejka':>10}{'przepust.':>11}{'przel./h':>10}\")
for m,v in sorted(agg.items()):
    f=lambda k: st.mean(float(x[k]) for x in v)
    print(f\"{m:<14}{len(v):>4}{f('mean_delay'):>12.2f}{f('mean_waiting'):>13.2f}{f('mean_queue'):>10.2f}{f('throughput'):>11.1f}{f('switching_freq'):>10.1f}\")
"
```

---

## 7. Uwagi

- **Porty TraCI.** Każdy równoległy kontener SUMO musi mieć własny port. W skryptach
  metod referencyjnych użyto 8813 i 8814.
- **Katalogi wyjściowe.** Każda metoda pisze do własnego `data/out/<metoda>`, inaczej
  równoległe przebiegi nadpisywałyby sobie `tripinfo.xml`.
- **Pliki wynikowe.** Każda metoda pisze do własnego `data/results_<metoda>.csv`,
  co eliminuje kolizje przy równoległym dopisywaniu. Scalanie jest osobnym krokiem.
- **`run_sim.py`** przyjmuje zmienne środowiskowe `TRACI_PORT`, `METHOD`, `DEMAND`,
  `SEED`, `OUT_DIR`, `RESULTS_CSV`. Bez nich działa jak dotychczas.
- **`docker-compose.yml`** ma zaszyty port 8813 i `osm.sumocfg`, więc nie nadaje się
  do równoległych przebiegów. Skrypty używają `docker run` z jawnymi parametrami.
- **Zbiór testowy** wykorzystujesz wyłącznie w kroku 5, po zamrożeniu konfiguracji.
