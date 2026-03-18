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

---

To co powinno zostać policzone na końcu to:
- średni czas oczekiwania,
- średnie opóźnienie / time loss,
- throughput,
- średnia długość kolejki,
- maksymalna długość kolejki,
- liczba przełączeń faz.
- Rozbite per wlot / per kierunek
- średni czas oczekiwania dla N/S/E/W,
- max queue dla N/S/E/W,
- liczba obsłużonych pojazdów dla każdego wlotu.

---
```bash
docker compose up -d sumo
.venv/bin/python src/run_sim.py
```