# ⚛️ Kwantowy generator liczb losowych

Projekt przedstawia implementację oraz porównanie kilku metod generowania losowych ciągów bitowych.  
Oprócz samych generatorów zawiera zestaw testów statystycznych, eksperyment porównujący generatory oraz analizę wpływu szumu na jakość otrzymywanych sekwencji.

Projekt został przygotowany w języku **Python** z wykorzystaniem bibliotek **NumPy**, **Qiskit** i **Qiskit Aer**.

---

## 🎯 Cel projektu

Celem projektu jest porównanie właściwości statystycznych ciągów bitowych generowanych przez:

- klasyczny generator pseudolosowy,
- kwantowy generator wykorzystujący idealny symulator,
- kwantowy generator z zasymulowanym błędem odczytu.

Wygenerowane sekwencje są analizowane za pomocą siedmiu testów statystycznych.  
Dodatkowo badany jest wpływ rodzaju i intensywności szumu na wyniki generatora kwantowego.

> **Uwaga:** generatory kwantowe działają na symulatorze Qiskit Aer. Projekt nie wykorzystuje fizycznego komputera kwantowego.

---

## 🧩 Dostępne generatory

### 1. Klasyczny generator pseudolosowy

Generator wykorzystuje bibliotekę **NumPy**:

```python
np.random.randint(0, 2, size=length)
```

Zwraca ciąg pseudolosowych wartości `0` i `1`.

---

### 2. Kwantowy generator — idealny symulator

Generator wykorzystuje jednokubitowy obwód kwantowy:

```text
|0> ── H ── M
```

Kubit rozpoczyna w stanie `|0>`, następnie wykonywana jest bramka Hadamarda:

```text
H|0> = (|0> + |1>) / sqrt(2)
```

Po pomiarze prawdopodobieństwa otrzymania `0` i `1` są równe:

```text
P(0) = 0.5
P(1) = 0.5
```

Obwód wykonywany jest za pomocą `AerSimulator`.

---

### 3. Kwantowy generator — zaszumiony symulator

Generator wykorzystuje ten sam obwód co wariant idealny, ale dodatkowo stosuje model błędu odczytu `ReadoutError`.

Domyślna konfiguracja:

```text
P(0 -> 1) = 2%
P(1 -> 0) = 8%
```

Asymetryczny błąd odczytu powoduje przesunięcie oczekiwanej proporcji bitów z `50/50` do około:

```text
53% zer
47% jedynek
```

Pozwala to sprawdzić, jak testy statystyczne reagują na systematyczne zaburzenie rozkładu bitów.

---

## 📊 Testy statystyczne

Projekt implementuje siedem testów:

| Test | Sprawdzana właściwość |
|---|---|
| **Frequency (Monobit)** | globalna równowaga liczby zer i jedynek |
| **Block Frequency** | równowaga bitów w mniejszych blokach |
| **Runs** | liczba i długość serii identycznych bitów |
| **Longest Run of Ones** | długość najdłuższych serii jedynek |
| **Serial** | częstość występowania krótkich wzorców bitowych |
| **Approximate Entropy** | regularność i przewidywalność wzorców |
| **Autocorrelation** | zależność pomiędzy bitami oddalonymi o zadane przesunięcie |

Domyślny poziom istotności wynosi:

```text
alpha = 0.01
```

Interpretacja wyniku:

```text
p >= 0.01  -> PASS
p <  0.01  -> FAIL
```

Status `SKIP` oznacza, że dla danej sekwencji nie zostały spełnione warunki wymagane do wykonania testu.

---

## 🧪 Eksperymenty

### Eksperyment 1 — porównanie generatorów

Porównywane są:

```text
Classical PRNG
Quantum RNG - ideal simulator
Quantum RNG - noisy simulator
```

Dla każdego generatora badane są sekwencje o długości:

```text
1 000 bitów
10 000 bitów
100 000 bitów
```

Każda konfiguracja wykonywana jest **30 razy**.

Dla każdej sekwencji:

1. generowany jest ciąg bitów,
2. mierzony jest czas generowania,
3. wykonywanych jest siedem testów statystycznych,
4. zapisywane są wartości `p`,
5. zapisywany jest status `PASS`, `FAIL` lub `SKIP`,
6. wyniki są agregowane i zapisywane do plików CSV,
7. generowane są wykresy porównawcze.

---

### Eksperyment 2 — wpływ szumu

Badane są cztery konfiguracje błędów odczytu:

| Konfiguracja | `P(0 -> 1)` | `P(1 -> 0)` | Oczekiwane `P(1)` |
|---|---:|---:|---:|
| brak szumu | 0% | 0% | 50% |
| symetryczny | 2% | 2% | 50% |
| asymetryczny łagodny | 2% | 4% | 49% |
| asymetryczny silniejszy | 2% | 8% | 47% |

Eksperyment pozwala sprawdzić:

- wpływ szumu na proporcję zer i jedynek,
- wpływ długości sekwencji na wykrywalność zaburzeń,
- różnice pomiędzy szumem symetrycznym i asymetrycznym,
- wrażliwość poszczególnych testów statystycznych.

---

## 📁 Struktura projektu

```text
quantum-rng/
│
├── main.py
│
├── README.md
│
├── generators/
│   ├── __init__.py
│   ├── base_generator.py
│   ├── classical_generator.py
│   ├── quantum_generator.py
│   └── noisy_quantum_generator.py
│
├── tests/
│   ├── __init__.py
│   └── statistical_tests.py
│
├── experiments/
│   ├── __init__.py
│   ├── generator_comparison.py
│   └── noise_experiment.py
│
├── plots/
│   ├── __init__.py
│   ├── generator_comparison_plots.py
│   └── noise_plots.py
│
└── experiment_results/
    └── ...
```

### `generators/`

Zawiera implementacje generatorów.

Wszystkie implementują wspólną metodę:

```python
generate(length: int) -> list[int]
```

Parametr `length` oznacza liczbę bitów do wygenerowania.

Przykładowy wynik:

```python
[1, 0, 1, 1, 0, 0, 1]
```

---

### `tests/statistical_tests.py`

Zawiera implementację wszystkich siedmiu testów oraz funkcję:

```python
run_all_tests(bits, alpha=0.01)
```

Funkcja uruchamia cały zestaw testów na przekazanej sekwencji.

---

### `experiments/generator_comparison.py`

Realizuje główny eksperyment porównujący trzy generatory.

Zapisuje między innymi:

```text
results.csv
summary.csv
```

---

### `experiments/noise_experiment.py`

Realizuje eksperyment badający wpływ różnych konfiguracji szumu.

Zapisuje:

```text
noise_results.csv
noise_summary.csv
```

---

### `plots/`

Zawiera funkcje generujące wykresy na podstawie wyników zapisanych przez eksperymenty.

---

### `main.py`

Stanowi główny punkt wejścia do programu i udostępnia prosty interfejs terminalowy.

---

## 💻 Wymagane biblioteki

Należy zainstalować następujące biblioteki:

- NumPy
- Qiskit
- Qiskit Aer
- SciPy
- pandas
- Matplotlib
- Colorama

### NumPy

```bash
pip install numpy
```

### Qiskit

```bash
pip install qiskit
```

### Qiskit Aer

```bash
pip install qiskit-aer
```

### SciPy

```bash
pip install scipy
```

### pandas

```bash
pip install pandas
```

### Matplotlib

```bash
pip install matplotlib
```

### Colorama

```bash
pip install colorama
```

---

## ▶️ Uruchamianie

Program należy uruchomić z katalogu głównego projektu:

```bash
python main.py
```

Po uruchomieniu wyświetlane jest menu:

```text
=== QUANTUM RANDOM NUMBER GENERATOR ===

1. Generate random sequence
2. Run statistical tests
3. Compare generators
4. Analyze noise influence
0. Exit
```

---

## 🔢 1. Generate random sequence

Pozwala wybrać generator:

```text
1. Classical PRNG
2. Quantum RNG - ideal simulator
3. Quantum RNG - noisy simulator
0. Back
```

Następnie użytkownik podaje liczbę bitów do wygenerowania.

Dla długich sekwencji w terminalu wyświetlanych jest pierwszych 100 bitów.

---

## ✅ 2. Run statistical tests

Pozwala:

1. wybrać generator,
2. podać długość sekwencji,
3. wygenerować dane,
4. automatycznie uruchomić wszystkie siedem testów.

Przykładowy wynik:

```text
=== STATISTICAL TEST RESULTS ===

Monobit                PASS   p = 0.355611
Block Frequency        PASS   p = 0.409122
Runs                   PASS   p = 0.185768
Longest Run            PASS   p = 0.709275
Serial                 PASS   p1 = 0.335098, p2 = 0.248213
Approximate Entropy    PASS   p = 0.637525
Autocorrelation        PASS   p = 0.247380
```

Do wykonania testów wymagana jest sekwencja zawierająca co najmniej **100 bitów**.

---

## 📈 3. Compare generators

Uruchamia pełny eksperyment porównujący:

- generator klasyczny,
- idealny generator kwantowy,
- zaszumiony generator kwantowy.

Po zakończeniu zapisywane są wyniki CSV oraz generowane wykresy dotyczące:

- procentu zaliczonych testów,
- czasu generowania,
- wartości `p` w poszczególnych powtórzeniach.

---

## 🌫️ 4. Analyze noise influence

Uruchamia osobny eksperyment badający wpływ konfiguracji błędu odczytu.

Generowane są między innymi wykresy:

- średniej proporcji jedynek,
- wyników testu Monobit,
- wyników wszystkich siedmiu testów dla różnych konfiguracji szumu.

---

## 📂 Wyniki eksperymentów

Wyniki zapisywane są w katalogu:

```text
experiment_results/
```

Każde uruchomienie eksperymentu otrzymuje osobny katalog oznaczony datą i czasem.

Przykład:

```text
experiment_results/
└── 20261012_195302_966814/
    ├── results.csv
    ├── summary.csv
    └── wykresy/
        ├── 01_zaliczanie_testow.png
        ├── 02_czas_generowania.png
        └── 03_wartosci_p.png
```

Dzięki temu kolejne uruchomienia nie nadpisują wcześniejszych wyników.

---

## ℹ️ Interpretacja wyników

Zaliczenie testu statystycznego oznacza jedynie, że dla analizowanej sekwencji nie znaleziono podstaw do odrzucenia hipotezy o losowości przy przyjętym poziomie istotności.

Nie oznacza to automatycznie, że generator:

- jest idealnie losowy,
- jest nieprzewidywalny,
- nadaje się do zastosowań kryptograficznych.

Projekt służy przede wszystkim do porównania zachowania różnych metod generowania bitów oraz pokazania wpływu szumu na ich właściwości statystyczne.
