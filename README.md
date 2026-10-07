# Kwantowy generator liczb losowych

Projekt implementuje kilka metod generowania losowych ciągów bitowych oraz umożliwia ich późniejsze porównanie za pomocą testów statystycznych.

Aktualnie dostępne są:
- klasyczny generator pseudolosowy,
- kwantowy generator oparty na idealnym symulatorze,
- kwantowy generator z zasymulowanym szumem.

## Wymagane biblioteki

Należy zainstalować następujące biblioteki:

- NumPy
- Qiskit
- Qiskit Aer
- Colorama

Instalacja NumPy:

```bash
pip install numpy
```

Instalacja Qiskit:

```bash
pip install qiskit
```

Instalacja Qiskit Aer:

```bash
pip install qiskit-aer
```

Instalacja Colorama:

```bash
pip install colorama
```

## Uruchamianie

Program należy uruchomić z katalogu głównego projektu:

```bash
python main.py
```

Po uruchomieniu dostępne jest terminalowe menu:

```text
=== QUANTUM RANDOM NUMBER GENERATOR ===

1. Generate random sequence
2. Run statistical tests
3. Compare generators
0. Exit
```

W przypadku generowania sekwencji można wybrać źródło losowości:

```text
1. Classical PRNG
2. Quantum RNG - ideal simulator
3. Quantum RNG - noisy simulator
```

## Struktura projektu

```text
quantum-rng/
│
├── generators/
│   ├── base_generator.py
│   ├── classical_generator.py
│   ├── quantum_generator.py
│   └── noisy_quantum_generator.py
│
└── main.py
```

Wszystkie generatory implementują wspólną metodę:

```python
generate(length: int) -> list[int]
```

Parametr `length` określa liczbę generowanych bitów, a wynikiem jest lista zawierająca wartości `0` i `1`.

## Generatory

### Klasyczny generator pseudolosowy

Generator wykorzystujący bibliotekę NumPy do generowania ciągów pseudolosowych bitów.

### Kwantowy generator - idealny symulator

Generator wykorzystujący pojedynczy kubit, bramkę Hadamarda oraz pomiar. Obwód wykonywany jest za pomocą `AerSimulator`.

### Kwantowy generator - zaszumiony symulator

Generator wykorzystujący ten sam obwód kwantowy co wersja idealna, ale dodatkowo uwzględniający model błędu odczytu w celu zasymulowania niedoskonałości układu kwantowego.

## Planowane testy statystyczne

Planowane testy obejmują między innymi:

- Frequency (Monobit) Test,
- Block Frequency Test,
- Runs Test,
- Longest Run of Ones Test,
- Serial Test,
- Approximate Entropy Test,
- Autocorrelation Test.

## Cel projektu

Celem projektu jest porównanie jakości ciągów bitowych generowanych przez klasyczny generator pseudolosowy oraz symulowane generatory kwantowe. Wygenerowane sekwencje będą analizowane za pomocą zestawu testów statystycznych pozwalających ocenić ich losowość.
