# AGENTS.md

## Przeznaczenie pliku

Ten plik zawiera trwały kontekst pracy magisterskiej i instrukcje dla modeli językowych pomagających w jej pisaniu, redagowaniu, porządkowaniu oraz analizowaniu.

Nie jest to spis treści pracy. Układ rozdziałów i podrozdziałów może ulegać zmianie. Model powinien dostosowywać tekst do aktualnego polecenia użytkownika, a nie narzucać strukturę zapisaną w innych rozmowach lub wcześniejszych wersjach dokumentu.

Plik zawiera potwierdzoną konfigurację eksperymentu, to jest parametry środowiska, hiperparametry, strukturę zbiorów danych oraz układ katalogów projektu. Nie zawiera natomiast liczbowych wyników eksperymentów. Wyniki należy odczytywać z plików wynikowych wskazanych w dalszej części dokumentu albo pobierać od użytkownika. Nie wolno ich zgadywać ani odtwarzać z pamięci na podstawie podobnych projektów.

Jeżeli bieżące informacje przekazane przez użytkownika są sprzeczne z tym plikiem, pierwszeństwo mają najnowsze informacje użytkownika.

---

## Tytuł pracy

### Tytuł polski

```latex
\title{
    Badanie efektywności uczenia ze wzmocnieniem w adaptacyjnym sterowaniu ruchem drogowym
}
```

### Tytuł angielski

```latex
\engtitle{
    A Study on the Effectiveness of Reinforcement Learning in Adaptive Traffic Control
}
```

Praca dotyczy wykorzystania uczenia ze wzmocnieniem do sterowania sygnalizacją świetlną. Nie jest to ogólna praca o wszystkich metodach sztucznej inteligencji ani kompleksowe porównanie wielu rodzin algorytmów RL.

---

## Główny problem badawczy

Celem badania jest sprawdzenie, czy agent uczony metodą uczenia ze wzmocnieniem może skutecznie sterować sygnalizacją świetlną na wybranym skrzyżowaniu i osiągać lepsze rezultaty niż klasyczne, deterministyczne sposoby sterowania ruchem.

Punktem wyjścia była hipoteza, że uczenie ze wzmocnieniem ma duży potencjał w adaptacyjnym sterowaniu ruchem. Badanie ma jednak charakter eksperymentalny i porównawczy. Nie należy z góry zakładać, że algorytm RL jest lepszy od każdej metody klasycznej, w każdym scenariuszu i według każdej metryki.

W tekstach należy wyraźnie odróżniać:

- założenie lub hipotezę badawczą,
- procedurę eksperymentalną,
- zaobserwowane wyniki,
- interpretację wyników,
- ograniczenia wnioskowania.

Nie wolno przedstawiać hipotezy jako potwierdzonego faktu przed omówieniem wyników.

---

## Zakres eksperymentu

Badanie zostało przeprowadzone w środowisku symulacyjnym na modelu pojedynczego skrzyżowania ulic Belgradzkiej i alei Komisji Edukacji Narodowej.

Skrzyżowanie wybrano jako stosunkowo podstawowy, ale istotnie obciążony układ drogowy. Model umożliwia ruch z każdego wlotu w dostępnych kierunkach, z wyłączeniem zawracania. Na głównym kierunku, przebiegającym wzdłuż alei KEN, skręt w lewo jest chroniony osobną fazą. Pozostałe skręty nie mają analogicznej ochrony.

W środowisku odwzorowano geometrię skrzyżowania oraz zasady ruchu pojazdów. Ruch pieszy nie został uwzględniony. Jest to świadome ograniczenie zakresu, a jego dodanie może zostać wskazane jako kierunek dalszego rozwoju.

Praca dotyczy demonstratora badawczego działającego w symulacji. Nie jest to wdrożenie produkcyjne, certyfikowany sterownik ruchu ani system przetestowany na rzeczywistej infrastrukturze drogowej.

---

## Program sygnalizacji

Program sygnalizacji odwzorowuje organizację ruchu obowiązującą na skrzyżowaniu i obejmuje trzy fazy z sygnałem zielonym, rozdzielone fazami żółtymi po 3 s:

- faza A: aleja KEN, jazda na wprost i skręt w prawo z obu kierunków, lewoskręt zatrzymany,
- faza B: aleja KEN, chroniony skręt w lewo z obu kierunków,
- faza C: ulica Belgradzka, jazda na wprost, skręt w prawo oraz warunkowy skręt w lewo.

Wydzielony sygnał skrętu w lewo występuje wyłącznie na alei KEN. Na ulicy Belgradzkiej skręt w lewo odbywa się w ramach fazy ogólnej, przy ustąpieniu pierwszeństwa.

Sterowaniem objętych jest trzynaście pasów wlotowych na czterech wlotach. Wlot południowy alei KEN, z którego pojazdy poruszają się w kierunku północnym, ma cztery pasy, a pozostałe trzy wloty po trzy pasy. Nazwy wlotów odnoszą się do ich położenia względem środka skrzyżowania, nie do kierunku jazdy. Jeżeli w kodzie lub plikach wynikowych występują oznaczenia `N` i `S`, opisują one kierunek jazdy: `N` odpowiada fizycznie wlotowi południowemu, a `S` wlotowi północnemu. Identyfikator sygnalizacji to `GS_cluster_300048112_300048176_300048179_32126015`.

Sieć występuje w dwóch plikach o identycznej geometrii i identycznym układzie faz:

- `data/osm_fixed.net.xml` z logiką `static`, czasy zielone 14 s, 29 s, 29 s, cykl 81 s,
- `data/osm.net.xml` z logiką `actuated`, `minDur` równe 5 s oraz `maxDur` równe 21 s, 43 s i 44 s.

Odpowiadające im konfiguracje symulacji:

- `data/osm_static.sumocfg` dla sterowania stałoczasowego,
- `data/osm_actuated.sumocfg` dla sterowania akomodacyjnego,
- `data/osm.sumocfg` dla agenta DQN.

Agent DQN korzysta z pliku `osm_fixed.net.xml`, ponieważ biblioteka `sumo-rl` samodzielnie odbudowuje program sygnalizacji na podstawie zbioru stanów faz zielonych i generuje własne przejścia żółte. Czasy trwania faz zapisane w pliku sieci nie mają wpływu na działanie agenta.

W modelu nie odwzorowano sygnału czerwono-żółtego. Jest to uproszczenie stosowane jednakowo dla wszystkich porównywanych metod.

---

## Środowisko symulacyjne

Do modelowania ruchu wykorzystano SUMO, czyli Simulation of Urban Mobility.

SUMO pełni w projekcie rolę mikroskopowego symulatora ruchu. Odpowiada między innymi za:

- model sieci drogowej,
- ruch i dynamikę pojazdów,
- wyznaczone trasy przejazdów,
- logikę sygnalizacji świetlnej,
- wykonywanie kolejnych kroków symulacji,
- dostarczanie danych potrzebnych do obliczania obserwacji, nagrody i metryk.

Środowiskiem SUMO sterowano z poziomu Pythona przez interfejs TraCI. TraCI umożliwia uruchamianie kolejnych kroków symulacji, odczytywanie stanu ruchu oraz zmianę działania sygnalizacji.

W opisie pracy należy odróżniać:

- SUMO jako symulator,
- TraCI jako interfejs komunikacyjny,
- bibliotekę `sumo-rl` jako warstwę integrującą SUMO ze środowiskiem uczenia ze wzmocnieniem,
- własny kod jako warstwę dostosowującą środowisko, proces treningowy i sposób zbierania wyników.

---

## Modelowane metody sterowania

W badaniu porównywane są trzy główne podejścia.

### Sterowanie stałoczasowe

Jest to podstawowa metoda referencyjna. Sygnalizacja cyklicznie przechodzi przez ustaloną sekwencję faz, a czas trwania każdej fazy jest z góry określony. Program nie reaguje na bieżący stan ruchu.

W SUMO metoda ta jest realizowana jako statyczna logika sygnalizacji.

Czasy zielone wyznaczono proporcjonalnie do natężenia na pasie krytycznym każdej fazy, oszacowanego wyłącznie na podstawie scenariuszy ze zbioru treningowego. Podział ten jest zamrożony i nie wolno go przeliczać na danych walidacyjnych ani testowych.

### Sterowanie akomodacyjne

Jest to bardziej zaawansowana metoda klasyczna, reagująca na obecność i napływ pojazdów. Wykorzystuje mechanizm wykrywania przerw między pojazdami i może wydłużać aktywną fazę, dopóki utrzymuje się strumień ruchu.

Preferowane określenie w polskim tekście:

> sterowanie akomodacyjne typu gap-based

Po pierwszym wyjaśnieniu można używać skróconej nazwy „sterowanie akomodacyjne”.

Minimalny czas zielony wynosi 5 s, tak samo jak w środowisku agenta. Maksymalne czasy trwania faz odpowiadają około półtorakrotności czasów zielonych programu stałoczasowego.

Nie należy utożsamiać tej metody z uczeniem ze wzmocnieniem. Jest ona adaptacyjna w ograniczonym, regułowym sensie, ale nie uczy się polityki na podstawie doświadczeń.

### Sterowanie z wykorzystaniem DQN

Trzecim podejściem jest agent wykorzystujący algorytm Deep Q-Network. Agent obserwuje stan skrzyżowania i wybiera jedną z dostępnych decyzji dotyczących fazy sygnalizacji.

DQN jest główną metodą uczenia ze wzmocnieniem badaną w pracy.

---

## Sformułowanie problemu uczenia ze wzmocnieniem

### Agent

Agent odpowiada za wybór działania sygnalizacji świetlnej. Jego celem jest nauczenie się polityki ograniczającej negatywne skutki ruchu, zgodnie z przyjętą funkcją nagrody.

### Środowisko

Środowiskiem jest symulacja skrzyżowania w SUMO, udostępniona agentowi przez `sumo-rl` oraz własną warstwę integracyjną.

### Obserwacja

Przestrzeń obserwacji ma postać `Box(0.0, 1.0, (30,), float32)`. Wykorzystano domyślną reprezentację stanu z biblioteki `sumo-rl`, złożoną z czterech grup cech:

- kodowanie aktywnej fazy typu one-hot, 3 wartości,
- znacznik upłynięcia minimalnego czasu zielonego powiększonego o czas fazy żółtej, 1 wartość,
- gęstość pasów, 13 wartości,
- zapełnienie kolejki, 13 wartości.

Pojemność pasa wyznaczana jest jako jego długość podzielona przez sumę minimalnego odstępu między pojazdami oraz średniej długości pojazdu na tym pasie. Cały wektor jest znormalizowany do przedziału od 0 do 1.

### Akcje

Przestrzeń akcji ma postać `Discrete(3)`. Każda akcja wskazuje fazę zieloną obowiązującą w kolejnym oknie decyzyjnym.

Środowisko uwzględnia ograniczenia sterowania sygnalizacją, takie jak minimalny czas zielonego oraz przejścia przez fazę żółtą. Jeżeli agent wskaże fazę bieżącą, sygnalizacja ją kontynuuje. Jeżeli wskaże inną fazę przed upływem minimalnego czasu zielonego powiększonego o czas fazy żółtej, żądanie jest ignorowane. W pozostałym przypadku środowisko wprowadza fazę żółtą, a następnie włącza wskazaną fazę zieloną.

Agent nie powinien być opisywany tak, jakby mógł natychmiast i dowolnie przełączać sygnały bez zachowania reguł bezpieczeństwa modelu.

### Funkcja nagrody

W projekcie wykorzystano funkcję nagrody opartą na zmianie czasu oczekiwania, określaną w konfiguracji jako `diff-waiting-time`.

Jeżeli powstaje szczegółowy opis matematyczny, należy oprzeć go na rzeczywistej implementacji użytej w projekcie. Nie wolno wymyślać wzoru tylko na podstawie nazwy funkcji.

### Interwał decyzyjny

Agent podejmuje decyzje co 5 s symulacji. Czas fazy żółtej wynosi 3 s, a minimalny czas zielony 5 s. Te same wartości obowiązują podczas treningu, walidacji oraz oceny na zbiorze testowym.

Między decyzjami SUMO wykonuje kroki o długości jednej sekundy, a środowisko egzekwuje obowiązujące ograniczenia faz.

---

## Wybór algorytmu

Początkowo rozważano klasyczny, tablicowy Q-Learning.

Podejście to zostało odrzucone, ponieważ przestrzeń obserwacji jest ciągła i ma trzydzieści wymiarów. Jej bezpośrednia dyskretyzacja prowadziłaby do bardzo dużej liczby potencjalnych stanów, co czyniłoby tablicę Q niepraktyczną i utrudniało skuteczne uczenie.

Wybrano Deep Q-Network, ponieważ:

- przestrzeń obserwacji jest ciągła,
- przestrzeń akcji jest dyskretna,
- sieć neuronowa może aproksymować funkcję wartości akcji,
- DQN wykorzystuje mechanizmy stabilizujące uczenie, takie jak bufor doświadczeń i sieć docelowa,
- architektura MLP jest odpowiednia dla wektorowej reprezentacji obserwacji.

W tekście należy używać nazwy `MlpPolicy`, jeżeli mowa o nazwie polityki stosowanej przez Stable-Baselines3.

Nie należy twierdzić, że DQN jest obiektywnie najlepszym możliwym algorytmem dla tego problemu. Był naturalnym i uzasadnionym wyborem w przyjętym zakresie pracy.

---

## Stos technologiczny

W projekcie wykorzystano przede wszystkim:

- SUMO,
- Python,
- TraCI,
- `sumo-rl`,
- Stable-Baselines3,
- interfejs środowiska zgodny z Gymnasium lub warstwą używaną przez `sumo-rl`,
- Docker,
- pliki konfiguracyjne i trasy w formacie XML,
- skrypty do treningu, ewaluacji, agregacji wyników i generowania wykresów.

Docker służył przede wszystkim do izolacji zależności, uniknięcia instalowania środowiska treningowego bezpośrednio w macOS oraz utrzymywania symulatora, bibliotek i kodu w jednym środowisku. Pozwolił także ominąć problemy z działaniem SUMO obserwowane przy bezpośrednim uruchamianiu w systemie gospodarza. Kod i definicja obrazu nie są obecnie udostępniane wraz z pracą, dlatego nie należy przedstawiać konteneryzacji jako gwarancji możliwości niezależnego odtworzenia eksperymentu. Nie jest ona głównym wkładem naukowym pracy.

---

## Własne modyfikacje i wkład implementacyjny

Biblioteka `sumo-rl` została wykorzystana jako podstawa, ale nie wystarczała bez zmian do przeprowadzenia całego eksperymentu.

Przygotowano własną warstwę opartą na klasie `SumoEnvironment`. W szczególności dostosowano działanie metody `step` i sposób zbierania metryk tak, aby rezultaty uzyskiwane podczas ewaluacji agenta były porównywalne z wynikami metod referencyjnych.

W opisie wkładu należy podkreślać:

- integrację środowiska symulacyjnego z procesem treningowym,
- ujednolicenie zbierania metryk,
- obsługę scenariuszy ruchu i epizodów,
- przygotowanie procesu walidacji i testów,
- zapis modeli i checkpointów,
- automatyzację eksperymentów,
- analizę stabilności modeli.

Nie należy przedstawiać całej biblioteki `sumo-rl` jako autorskiej implementacji.

---

## Scenariusze ruchu

Scenariusze ruchu zostały wygenerowane przy użyciu skryptu `randomTrips.py` dostarczanego z SUMO.

Przygotowano scenariusze reprezentujące:

- lekkie natężenie ruchu,
- średnie natężenie ruchu,
- wysokie natężenie ruchu,
- zmienne, narastające natężenie ruchu.

W scenariuszach o stałym natężeniu pojazdy były generowane zgodnie z zadanym okresem napływu. Przygotowano wiele wariantów różniących się ziarnem generatora losowego, aby nie opierać wniosków na jednym konkretnym układzie tras.

Scenariusz zmienny łączy kolejne poziomy obciążenia w jednej symulacji. W bardziej losowych wariantach wykorzystano mechanizmy nieregularnego rozmieszczania czasów wyjazdu i dodatkowego różnicowania napływu pojazdów.

W projekcie występują między innymi opcje:

- `--period`,
- `--random-depart`,
- `--binomial`,
- `--seed`,
- `--route-file`.

Wygenerowane podróże są przekształcane na poprawne trasy. W przypadku użycia `--route-file` skrypt może uruchamiać `duarouter`, który wyznacza trasy i odrzuca podróże niemożliwe do zrealizowania w danej sieci.

Poziomy natężenia odpowiadają wartościom opcji `--period`:

- 5,0 s dla ruchu lekkiego,
- 2,5 s dla ruchu średniego,
- 1,25 s dla ruchu wysokiego.

Scenariusz zmienny powstaje przez podanie wszystkich trzech okresów jednocześnie wraz z opcjami `--random-depart` oraz `--binomial 4`.

Przykładowe komendy generowania zapisano w pliku `usefull_commands.md`.

---

## Podział danych eksperymentalnych

Eksperyment wykorzystuje rozdzielone zbiory treningowy, walidacyjny i testowy.

### Dane treningowe

Przygotowano dwa warianty zbioru treningowego, po 30 plików tras każdy, po 10 plików na każdy z trzech poziomów natężenia. Każdy scenariusz treningowy obejmuje 1800 s napływu pojazdów, a epizod treningowy trwa 2100 s, co pozwala sieci się opróżnić.

- `data/train/fixed/` z regularnymi czasami pojawiania się pojazdów, ziarna 1001–1010, 2001–2010 i 3001–3010,
- `data/train/randomized/` o podobnych poziomach natężenia, lecz z nieregularnymi czasami wyjazdu.

Celem porównania było sprawdzenie, czy większa losowość danych treningowych poprawia generalizację modelu. Wariant treningowy wybiera się zmienną `TRAIN_SET` w skrypcie `run_train_configs.sh`.

Zbiór treningowy posłużył także do wyznaczenia parametrów czasowych metod referencyjnych.

### Dane walidacyjne

Zbiór walidacyjny to cztery pliki w katalogu `data/valid/`, obejmujące ruch lekki, średni, wysoki oraz scenariusz zmienny. Każdy scenariusz trwa 3600 s. Służy do:

- wyboru odpowiedniej długości treningu,
- porównania wariantów danych treningowych,
- oceny stabilności modeli,
- doboru hiperparametrów,
- wyboru modelu końcowego.

Część porównań powtórzono na pięciu ziarnach symulacji SUMO, aby wnioski nie opierały się na pojedynczym przebiegu.

### Dane testowe

Zbiór testowy jest niezależny od danych treningowych i walidacyjnych. Obejmuje cztery grupy po pięć plików, każdy o długości 3600 s:

- `data/T1/` ruch lekki, ziarna 101–105,
- `data/T2/` ruch średni, ziarna 201–205,
- `data/T3/` ruch wysoki, ziarna 301–305,
- `data/G1/` ruch zmienny, ziarna 401–405.

Te same scenariusze testowe służą do porównania sterowania stałoczasowego, akomodacyjnego i DQN.

Dane testowe nie mogą służyć do:

- wyboru hiperparametrów,
- wyboru długości treningu,
- wyboru zbioru treningowego,
- poprawiania modelu po obejrzeniu wyników.

Końcowy model powinien zostać wybrany na podstawie walidacji, a następnie oceniony na zbiorze testowym.

---

## Przebieg eksperymentów z DQN

Proces badawczy obejmował kilka etapów.

### Wyznaczenie długości treningu

Najpierw trenowano konfigurację bazową, zapisując modele w kolejnych checkpointach. Każdy checkpoint oceniano na scenariuszach walidacyjnych.

Celem nie było wybranie modelu o największej liczbie kroków, lecz znalezienie punktu, w którym model osiąga dobre i stabilne wyniki. Zaobserwowane późniejsze pogorszenie wyników traktowano jako sygnał destabilizacji procesu uczenia lub utraty zdolności generalizacji.

Nie należy automatycznie określać tego zjawiska jako klasycznego przeuczenia. W DQN pogorszenie może wynikać także z niestabilności estymacji wartości Q, rozkładu doświadczeń w buforze, częstotliwości aktualizacji sieci docelowej, eksploracji lub interakcji hiperparametrów.

### Porównanie zbiorów treningowych

Powtórzono trening dla regularnego i bardziej losowego sposobu generowania danych. Modele porównano na tym samym zbiorze walidacyjnym.

Istotnym elementem badania jest to, że bardziej losowe dane treningowe nie muszą automatycznie prowadzić do lepszej generalizacji. Wnioski należy formułować wyłącznie dla zastosowanej konfiguracji, a nie jako uniwersalną zasadę.

### Dobór hiperparametrów

Punktem wyjścia była konfiguracja bazowa. Następnie prowadzono eksperymenty metodą zmiany jednego hiperparametru przy pozostawieniu pozostałych wartości bez zmian.

Badano parametry związane między innymi z:

- tempem uczenia,
- rozmiarem batcha,
- rozmiarem bufora doświadczeń,
- współczynnikiem dyskontowania,
- długością fazy eksploracji,
- częstotliwością aktualizacji sieci docelowej.

Dodatkowo sprawdzono połączenie wybranych zmian, aby ocenić, czy korzystne modyfikacje działające osobno przynoszą poprawę także razem.

Metoda zmiany jednego parametru ułatwia interpretację, lecz nie bada systematycznie wszystkich interakcji między hiperparametrami. To ograniczenie powinno zostać zaznaczone w analizie.

### Wybór modelu końcowego

Model końcowy został wybrany na podstawie działania na zbiorze walidacyjnym, stabilności procesu treningowego oraz porównania wariantów konfiguracji. Jest to konfiguracja bazowa wytrenowana na regularnym zbiorze treningowym.

Trening bazowy trwał 300 000 kroków, a modele zapisywano w checkpointach co 25 000 kroków. Model końcowy nie jest modelem z końca treningu, lecz checkpointem po 225 000 kroków, wskazanym przez walidację. Plik `data/models/dqn/dqn_final.zip` jest kopią pliku `data/models/checkpoints/dqn_fixed_225000_steps.zip`.

Wartość `total_timesteps` w konfiguracji bazowej określa zatem długość całego przebiegu treningowego, a nie liczbę kroków modelu końcowego.

Konfiguracja bazowa znajduje się w pliku `src/dqn/configs/base_config.yml`:

```yaml
environment:
  tls_id: GS_cluster_300048112_300048176_300048179_32126015
  decision_interval: 5
  yellow_time: 3
  min_green: 5
  num_seconds: 2100
  reward_fn: diff-waiting-time

training:
  total_timesteps: 300_000
  seed: 42
  learning_rate: 0.001
  buffer_size: 50000
  learning_starts: 1000
  batch_size: 64
  gamma: 0.99
  train_freq: 1
  target_update_interval: 500
  exploration_fraction: 0.2
  exploration_initial_eps: 1.0
  exploration_final_eps: 0.05
```

Polityka to `MlpPolicy` z domyślną architekturą Stable-Baselines3.

Warianty strojenia w katalogu `src/dqn/configs/` zmieniają pojedyncze hiperparametry względem konfiguracji bazowej i mają `total_timesteps` równe 225 000. Każdy wariant trenowany jest więc dokładnie do tej samej liczby kroków, którą ma model końcowy, dzięki czemu porównanie nie jest zaburzone różną długością treningu. Sufiks `225k` w nazwach plików w `data/models/finetune/` oznacza koniec treningu wariantu, a nie wybrany checkpoint.

### Analiza modelu kontrastowego

Oprócz modelu końcowego na zbiorze testowym oceniono również jeden model, który podczas strojenia wypadł najsłabiej na zbiorze walidacyjnym. Jest to wariant ze skróconą fazą eksploracji, zapisany jako `data/models/finetune/dqn_fixed_explore1e-1_225k.zip`.

Celem tego dodatkowego eksperymentu jest sprawdzenie, czy słabe wyniki walidacyjne przekładają się na słabą generalizację na niezależnym zbiorze testowym.

Nie należy traktować tego modelu jako kolejnego kandydata wybieranego na podstawie testu. Jest to analiza porównawcza wykonana po procesie selekcji głównego modelu.

---

## Metryki oceny

Metody są porównywane według kilku metryk, ponieważ jedna wartość nie opisuje wszystkich aspektów działania sygnalizacji.

W projekcie analizowane są:

- średnie opóźnienie,
- średni czas oczekiwania,
- średnia długość kolejki,
- przepustowość,
- częstotliwość przełączeń sygnalizacji.

Należy zachować rozróżnienie między opóźnieniem i czasem oczekiwania. Nie są to synonimy.

Przy szczegółowym opisie każdej metryki trzeba podać:

- definicję,
- źródło danych,
- sposób agregacji,
- jednostkę,
- interpretację,
- informację, czy większa czy mniejsza wartość jest korzystna.

Jeżeli definicja pochodzi z SUMO lub z własnej implementacji, należy oprzeć się na rzeczywistym kodzie albo dokumentacji. Nie wolno wymyślać definicji.

Średnie opóźnienie pełniło ważną rolę w porównywaniu modeli podczas walidacji, ale końcowa ocena metod nie powinna ignorować pozostałych metryk.

---

## Struktura projektu i pliki wynikowe

Kod źródłowy:

- `src/baseline/run_sim.py` uruchamia metody referencyjne przez czyste TraCI,
- `src/dqn/env.py` zawiera klasę `DqnSumoEnv`, czyli własną warstwę nad `sumo-rl`,
- `src/dqn/train.py` odpowiada za trening i zapis checkpointów,
- `src/dqn/evaluate.py` odpowiada za walidację i ocenę testową,
- `src/dqn/results.py` zawiera `EpisodeRecorder` oraz funkcje liczące metryki,
- `src/dqn/configs/` zawiera konfigurację bazową i warianty strojenia.

Skrypty uruchomieniowe w katalogu głównym: `run_baseline.sh`, `run_train_configs.sh`, `run_dqn_test.sh`. Dokumentacja komend znajduje się w `run_experiments.md`.

Pliki wynikowe w katalogu `data/`:

- `results.csv` oraz `results_<metoda>.csv` z oceną na zbiorze testowym,
- `validate_steps.csv` z oceną kolejnych checkpointów,
- `validate_steps_check_seed.csv` z powtórzeniem wyboru checkpointu na pięciu ziarnach,
- `validation_params.csv` z oceną wariantów hiperparametrów,
- `validation_params_check_seed.csv` z powtórzeniem porównania wariantów na pięciu ziarnach.

Wykresy powstają w notatniku `data/visualise.ipynb` i zapisywane są do `docs/tex/img2/`.

Wszystkie liczbowe wyniki należy odczytywać z tych plików. Nie wolno ich zgadywać.

Znana właściwość danych: w przebiegach DQN kolumna `phase` w `timeseries.csv` ma zawsze wartość 0, ponieważ `sumo-rl` steruje sygnalizacją przez `setRedYellowGreenState`. Zliczanie przełączeń jest poprawne, ponieważ porównuje łańcuchy stanu sygnałów, a nie numer fazy.

---

## Zasady uczciwego porównania

Podczas opisywania eksperymentu należy podkreślać, że:

- metody są oceniane na tych samych scenariuszach testowych,
- stosowany jest możliwie spójny sposób zbierania metryk,
- warianty scenariuszy różnią się ziarnami losowymi,
- dane testowe nie były widziane podczas treningu,
- strojenie wykonano na danych walidacyjnych,
- końcowe wnioski powinny uwzględniać zmienność pomiędzy wariantami scenariusza,
- nie należy wybierać pojedynczego korzystnego przebiegu i pomijać pozostałych.

Jeżeli dostępne są wyniki z wielu ziaren, preferowane jest przedstawianie średnich wraz z miarą rozrzutu lub rozkładem wyników.

---

## Ograniczenia badania

Należy pamiętać o następujących ograniczeniach:

- analizowane jest pojedyncze skrzyżowanie,
- ruch jest generowany syntetycznie,
- model nie został skalibrowany na podstawie pełnego zestawu rzeczywistych pomiarów ruchu, o ile użytkownik nie poda później inaczej,
- nie uwzględniono pieszych,
- nie analizuje się koordynacji wielu skrzyżowań,
- badanie nie obejmuje rzeczywistego wdrożenia,
- wykorzystano przede wszystkim jeden algorytm uczenia ze wzmocnieniem,
- zakres strojenia hiperparametrów jest ograniczony,
- funkcja nagrody reprezentuje tylko wybrany sposób definiowania celu,
- poprawa jednej metryki może odbywać się kosztem innej,
- zachowanie w symulacji nie gwarantuje identycznego działania w rzeczywistym ruchu.

Ograniczenia nie powinny być ukrywane. Ich wskazanie zwiększa wiarygodność pracy.

---

## Możliwe kierunki dalszego rozwoju

Jako potencjalne rozszerzenia można rozważać:

- dodanie pieszych i rowerzystów,
- uwzględnienie transportu publicznego,
- wykorzystanie rzeczywistych pomiarów natężenia,
- kalibrację parametrów ruchu w SUMO,
- sterowanie siecią wielu skrzyżowań,
- rozwiązanie wieloagentowe,
- porównanie DQN z innymi algorytmami RL,
- warianty Double DQN lub Dueling DQN,
- automatyczne strojenie hiperparametrów,
- bardziej złożoną funkcję nagrody,
- ograniczenia dotyczące komfortu i częstotliwości zmian sygnałów,
- testowanie zdarzeń nietypowych, awarii i blokad,
- integrację z rzeczywistymi detektorami ruchu.

Nie należy przedstawiać tych elementów jako zrealizowanych, chyba że użytkownik wyraźnie poda, że zostały dodane.

---

## Zasady pisania i redagowania

### Język

Praca jest pisana po polsku. Należy stosować formalny, techniczny i akademicki język, ale unikać nadmiernie skomplikowanych zdań oraz sztucznego napompowania tekstu.

Preferowane są:

- precyzyjne definicje,
- logiczne przejścia między akapitami,
- jasne wskazanie celu każdego fragmentu,
- konsekwentna terminologia,
- ostrożne formułowanie wniosków.

Należy unikać:

- marketingowego języka,
- nieuzasadnionych superlatyw,
- stwierdzeń typu „algorytm jest inteligentny”,
- ogólników bez technicznego znaczenia,
- powtarzania tej samej informacji w wielu miejscach,
- zdań sugerujących wyniki, których jeszcze nie przedstawiono.

### Interpunkcja i myślniki

Nie wolno używać długich myślników, tak zwanych em dashów (długi myślnik, znak Unicode U+2014). Zakaz obowiązuje w całej pracy oraz we wszystkich fragmentach redagowanych automatycznie.

Zamiast długiego myślnika należy:

- przeredagować zdanie tak, aby myślnik nie był potrzebny,
- użyć przecinka, dwukropka albo nawiasu, gdy pasuje to do treści,
- podzielić wypowiedź na dwa zdania,
- jeżeli myślnik jest rzeczywiście konieczny, na przykład jako wtrącenie, zastosować krótszą półpauzę „–” (znak Unicode U+2013) zgodnie z polską typografią.

Jeżeli w tekście pojawi się długi myślnik, na przykład wklejony z innego źródła, należy go usunąć i zastąpić poprawną interpunkcją.

### Osoba i styl narracji

Model powinien zachować styl otaczającego tekstu. Należy jednak pamiętać że praca ta jest pisana bezosobowo, i jeżeli użytkownik napisze fragment przez przypadek w pierwszej osobie, trzeba to poprawić aby praca była spójna.

Domyślnie preferowane są konstrukcje takie jak:

- „w ramach pracy przygotowano…”,
- „w badaniu wykorzystano…”,
- „przeprowadzono porównanie…”,
- „na podstawie wyników wybrano…”.

### Terminologia

Preferowane określenia:

- uczenie ze wzmocnieniem,
- algorytm DQN lub Deep Q-Network,
- agent,
- środowisko,
- obserwacja,
- przestrzeń akcji,
- funkcja nagrody,
- polityka,
- bufor doświadczeń,
- sieć docelowa,
- sterowanie stałoczasowe,
- sterowanie akomodacyjne,
- scenariusz natężenia ruchu,
- zbiór treningowy,
- zbiór walidacyjny,
- zbiór testowy,
- generalizacja,
- stabilność procesu uczenia.

Nie należy zamiennie używać określeń „walidacja” i „test”. Mają one inne role.

Nie należy nazywać każdego elementu „algorytmem”. Przykładowo SUMO jest symulatorem, TraCI interfejsem, `sumo-rl` biblioteką lub warstwą środowiska, a DQN algorytmem.

### Wyniki i liczby

Nie wolno wymyślać:

- wyników,
- wartości hiperparametrów,
- liczby kroków,
- czasów treningu,
- konfiguracji sprzętowej,
- liczby scenariuszy,
- wartości okresów generowania ruchu,
- ziaren,
- wersji bibliotek,
- procentowych przewag,
- wartości błędów lub odchyleń.

Jeżeli konkretna wartość nie została podana w bieżącym kontekście, należy:

- poprosić użytkownika o wartość,
- pozostawić jednoznaczny znacznik, na przykład `[DO UZUPEŁNIENIA]`,
- albo napisać opis bez wartości, jeżeli liczba nie jest konieczna.

Nie należy korzystać z wartości zapamiętanych z wcześniejszych wersji tekstu, jeżeli użytkownik nie potwierdził, że są nadal aktualne.

### Interpretacja wyników

Należy oddzielać opis obserwacji od wyjaśnienia przyczyn.

Poprawny schemat:

1. podanie wyniku lub obserwowanej różnicy,
2. porównanie metod,
3. ostrożna interpretacja,
4. wskazanie ograniczeń interpretacji.

Preferowane sformułowania:

- „może to wskazywać…”,
- „jednym z możliwych wyjaśnień jest…”,
- „w przyjętej konfiguracji…”,
- „wynik nie pozwala stwierdzić, że…”,
- „obserwacja wymaga ostrożnej interpretacji…”.

Nie należy przypisywać związku przyczynowego tylko dlatego, że dwa zjawiska wystąpiły jednocześnie.

### Kod i szczegóły implementacji

Fragmenty kodu powinny być krótkie i służyć wyjaśnieniu mechanizmu. Nie należy wklejać dużych klas ani całych plików, jeżeli nie są bezpośrednio analizowane.

Przy opisie kodu należy wyjaśniać:

- po co dany element istnieje,
- jaki problem rozwiązuje,
- jak przepływają dane,
- jakie są wejścia i wyjścia,
- jak wpływa na eksperyment.

Nie należy przepisywać kodu linia po linii bez szerszego kontekstu.

### Diagramy

Przydatne są diagramy pokazujące:

- architekturę systemu,
- komunikację SUMO–TraCI–Python,
- przepływ pojedynczej decyzji agenta,
- proces treningu i walidacji,
- podział danych,
- przepływ zbierania metryk.

Diagram powinien wspierać tekst, a nie powtarzać go bez dodatkowej wartości.

### Źródła

Twierdzenia dotyczące:

- działania SUMO,
- działania `randomTrips.py`,
- mechanizmu sterowania akomodacyjnego,
- teorii Q-Learningu i DQN,
- wyników innych badań,
- zalet i ograniczeń algorytmów,

powinny być poparte odpowiednimi źródłami.

Dla narzędzi należy preferować oficjalną dokumentację. Dla metod i badań należy preferować oryginalne publikacje naukowe oraz wiarygodne artykuły przeglądowe.

Nie wolno wymyślać cytowań, autorów, tytułów publikacji ani numerów DOI.

---

## Czego model nie powinien zakładać

Model pomagający w pracy nie powinien zakładać bez potwierdzenia:

- dokładnej ostatecznej struktury pracy,
- dokładnych wyników testowych i walidacyjnych,
- liczby wykonanych eksperymentów,
- dokładnych wersji oprogramowania,
- rodzaju sprzętu użytego do treningu,
- statystycznej istotności różnic,
- przewagi DQN we wszystkich scenariuszach,
- istnienia ruchu pieszego w modelu,
- wykorzystania rzeczywistych danych pomiarowych,
- zastosowania wielu algorytmów RL,
- wdrożenia systemu w rzeczywistym skrzyżowaniu.

---

## Zasada nadrzędna

Najważniejszym zadaniem modelu jest pomóc opisać rzeczywiście przeprowadzone badanie w sposób precyzyjny, spójny i naukowo uczciwy.

Model ma porządkować materiał, poprawiać język, wyjaśniać decyzje metodologiczne i pomagać w interpretacji, ale nie może uzupełniać braków fikcyjnymi faktami.

Gdy brakuje informacji potrzebnej do napisania konkretnego fragmentu, należy wyraźnie wskazać brak zamiast go zgadywać.
