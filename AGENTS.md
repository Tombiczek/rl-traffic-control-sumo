# AGENTS.md

## Przeznaczenie pliku

Ten plik zawiera trwały kontekst pracy magisterskiej i instrukcje dla modeli językowych pomagających w jej pisaniu, redagowaniu, porządkowaniu oraz analizowaniu.

Nie jest to spis treści pracy. Układ rozdziałów i podrozdziałów może ulegać zmianie. Model powinien dostosowywać tekst do aktualnego polecenia użytkownika, a nie narzucać strukturę zapisaną w innych rozmowach lub wcześniejszych wersjach dokumentu.

Plik celowo nie zawiera dokładnych wyników eksperymentów, końcowych wartości hiperparametrów, liczby kroków, ziaren losowych, liczby plików ani szczegółowych wartości konfiguracji. Dane te użytkownik będzie przekazywał podczas pisania odpowiednich fragmentów. Nie wolno ich zgadywać ani odtwarzać z pamięci na podstawie podobnych projektów.

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

### Sterowanie akomodacyjne

Jest to bardziej zaawansowana metoda klasyczna, reagująca na obecność i napływ pojazdów. Wykorzystuje mechanizm wykrywania przerw między pojazdami i może wydłużać aktywną fazę, dopóki utrzymuje się strumień ruchu.

Preferowane określenie w polskim tekście:

> sterowanie akomodacyjne typu gap-based

Po pierwszym wyjaśnieniu można używać skróconej nazwy „sterowanie akomodacyjne”.

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

Stan przekazywany agentowi jest wielowymiarowym wektorem wartości ciągłych, znormalizowanych do wspólnego zakresu. Reprezentuje on bieżącą sytuację ruchową oraz informacje potrzebne do podejmowania decyzji.

Przy pisaniu szczegółowego opisu należy używać rzeczywistej definicji obserwacji z implementacji. Nie wolno samodzielnie zgadywać znaczenia poszczególnych elementów wektora.

### Akcje

Przestrzeń akcji jest dyskretna. Dostępne działania odpowiadają dozwolonym fazom ruchu na skrzyżowaniu.

Środowisko uwzględnia ograniczenia sterowania sygnalizacją, takie jak minimalny czas zielonego oraz przejścia przez fazę żółtą. Agent nie powinien być opisywany tak, jakby mógł natychmiast i dowolnie przełączać sygnały bez zachowania reguł bezpieczeństwa modelu.

### Funkcja nagrody

W projekcie wykorzystano funkcję nagrody opartą na zmianie czasu oczekiwania, określaną w konfiguracji jako `diff-waiting-time`.

Jeżeli powstaje szczegółowy opis matematyczny, należy oprzeć go na rzeczywistej implementacji użytej w projekcie. Nie wolno wymyślać wzoru tylko na podstawie nazwy funkcji.

### Interwał decyzyjny

Agent podejmuje decyzje w ustalonych odstępach czasu symulacji. Między decyzjami SUMO wykonuje kolejne kroki, a środowisko egzekwuje obowiązujące ograniczenia faz.

Dokładna wartość interwału powinna zostać podana dopiero wtedy, gdy użytkownik ją potwierdzi w kontekście danego fragmentu.

---

## Wybór algorytmu

Początkowo rozważano klasyczny, tablicowy Q-Learning.

Podejście to zostało odrzucone, ponieważ przestrzeń obserwacji jest ciągła i wielowymiarowa. Jej bezpośrednia dyskretyzacja prowadziłaby do bardzo dużej liczby potencjalnych stanów, co czyniłoby tablicę Q niepraktyczną i utrudniało skuteczne uczenie.

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

Docker służy przede wszystkim do zapewnienia powtarzalności środowiska i izolacji zależności. Nie jest głównym wkładem naukowym pracy.

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

Dokładne wartości okresów, ziaren, czasów symulacji i liczby plików nie są zapisane w tym dokumencie. Należy pobrać je od użytkownika lub z aktualnych plików projektu przed przygotowaniem szczegółowej tabeli lub opisu.

---

## Podział danych eksperymentalnych

Eksperyment wykorzystuje rozdzielone zbiory treningowy, walidacyjny i testowy.

### Dane treningowe

Przygotowano dwa podejścia do generowania danych treningowych:

- scenariusze o stałym natężeniu i regularnych czasach pojawiania się pojazdów,
- scenariusze o podobnych poziomach natężenia, lecz bardziej nieregularnych czasach wyjazdu.

Celem było sprawdzenie, czy większa losowość danych treningowych poprawia generalizację modelu.

### Dane walidacyjne

Zbiór walidacyjny obejmuje różne poziomy natężenia oraz scenariusz dynamiczny. Służy do:

- wyboru odpowiedniej długości treningu,
- porównania wariantów danych treningowych,
- oceny stabilności modeli,
- doboru hiperparametrów,
- wyboru modelu końcowego.

### Dane testowe

Zbiór testowy jest niezależny od danych treningowych i walidacyjnych. Te same scenariusze testowe służą do porównania sterowania stałoczasowego, akomodacyjnego i DQN.

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

Model końcowy został wybrany na podstawie działania na zbiorze walidacyjnym, stabilności procesu treningowego oraz porównania wariantów konfiguracji.

Ten plik nie wskazuje dokładnej końcowej wartości tempa uczenia ani innych wartości hiperparametrów. Przed napisaniem fragmentu o modelu końcowym należy poprosić użytkownika o aktualną, potwierdzoną konfigurację.

### Analiza modelu niestabilnego

Oprócz modelu końcowego na zbiorze testowym oceniono również jeden model, który podczas strojenia wykazywał bardzo słabe lub niestabilne zachowanie. Wybrano wariant związany z rzadszą aktualizacją sieci docelowej.

Celem tego dodatkowego eksperymentu jest sprawdzenie, czy niestabilność i słabe wyniki walidacyjne przekładają się na słabą generalizację na niezależnym zbiorze testowym.

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
- końcowej konfiguracji najlepszego modelu,
- dokładnych wyników testowych,
- wartości hiperparametrów,
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
