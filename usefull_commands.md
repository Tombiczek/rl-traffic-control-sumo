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
- period 5.0 -> mały ruch
- period 2.5 -> 2x większy
- period 1.25 -> 4x większy

I na ten moment powinno to sensownie symulować mały/średni/duży ruch na skrzyżowaniu.

---

Aby zrobić sanity-check i uruchomić symulację bez TraCI w konsoli używając obrazu dockerowego wykonujemy komendę:
```bash
docker compose run --rm sumo \
  sumo -c /data/data/osm.sumocfg --seed 42 --no-warnings --quit-on-end
```
Zależnie jaki napływ pojazdów będzie akurat zdefiniowany w `osm.sumocofig` taka symulacja się uruchomi.
To uruchamia się wtedy w trybie `actuated` tak jak jest to zdefiniowane w pliku `osm.net.xml`.