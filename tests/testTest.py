from math import erfc, sqrt, log
from time import perf_counter
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import csv
import hashlib

from scipy.special import gammaincc
from scipy.stats import binomtest

from generators.classical_generator import ClassicalGenerator
from generators.quantum_generator import QuantumGenerator
from generators.noisy_quantum_generator import NoisyQuantumGenerator


# Ustawienia eksperymentów.
LENGTHS = [1000, 10000, 100000]
REPETITIONS = 30
ALPHA = 0.01


def validate_bits(bits):
    if len(bits) < 100:
        raise ValueError("Wymagane jest co najmniej 100 bitów.")

    if any(bit not in (0, 1) for bit in bits):
        raise ValueError("Sekwencja musi zawierać tylko 0 i 1.")

    return len(bits)


def make_result(name, p_values, alpha=0.01, note=""):
    if not 0 < alpha < 1:
        raise ValueError("Alpha musi należeć do przedziału (0, 1).")

    values = [float(p) for p in p_values]

    if any(not 0 <= p <= 1 for p in values):
        raise ValueError("Nieprawidłowa wartość p.")

    if not values:
        status = "SKIP"
    else:
        status = "PASS" if all(p >= alpha for p in values) else "FAIL"

    return {
        "name": name,
        "p_values": values,
        "status": status,
        "note": note,
    }


# 1. Frequency (Monobit) Test.
def monobit_test(bits, alpha=0.01):
    n = validate_bits(bits)

    total = 2 * sum(int(bit) for bit in bits) - n
    p = erfc(abs(total) / sqrt(2 * n))

    return make_result("Monobit", [p], alpha)


# 2. Block Frequency Test.
def block_frequency_test(bits, alpha=0.01, block_size=None):
    n = validate_bits(bits)

    if block_size is None:
        block_size = max(20, n // 50)

    if not isinstance(block_size, int) or not 20 <= block_size <= n:
        raise ValueError(
            "Rozmiar bloku musi być liczbą całkowitą od 20 do n."
        )

    count = n // block_size

    if block_size <= 0.01 * n or count >= 100:
        raise ValueError(
            "Wymagane M > 0.01*n i mniej niż 100 bloków."
        )

    chi2 = 0.0

    for i in range(count):
        block = bits[i * block_size:(i + 1) * block_size]
        proportion = sum(int(bit) for bit in block) / block_size
        chi2 += 4 * block_size * (proportion - 0.5) ** 2

    p = gammaincc(count / 2, chi2 / 2)

    note = (
        f"M={block_size}, bloki={count}, "
        f"pominięte bity={n % block_size}"
    )

    return make_result("Block Frequency", [p], alpha, note)


# 3. Runs Test — liczba serii jednakowych bitów.
def runs_test(bits, alpha=0.01):
    n = validate_bits(bits)
    proportion = sum(int(bit) for bit in bits) / n

    if abs(proportion - 0.5) >= 2 / sqrt(n):
        return make_result(
            "Runs",
            [],
            alpha,
            "Niespełniony warunek wstępny: "
            "proporcja jedynek zbyt daleka od 0.5.",
        )

    runs = 1 + sum(
        int(bits[i] != bits[i - 1])
        for i in range(1, n)
    )

    expected = 2 * n * proportion * (1 - proportion)
    denominator = (
        2 * sqrt(2 * n) * proportion * (1 - proportion)
    )

    p = erfc(abs(runs - expected) / denominator)

    return make_result(
        "Runs",
        [p],
        alpha,
        f"Liczba serii={runs}",
    )


# 4. Longest Run of Ones Test.
def longest_run_test(bits, alpha=0.01):
    n = validate_bits(bits)

    if n < 128:
        return make_result(
            "Longest Run",
            [],
            alpha,
            "Wymagane minimum 128 bitów.",
        )

    if n < 6272:
        size = 8
        lower = 1
        probabilities = [
            55 / 256,
            94 / 256,
            59 / 256,
            48 / 256,
        ]

    elif n < 750000:
        size = 128
        lower = 4
        probabilities = [
            0.1174,
            0.2430,
            0.2493,
            0.1752,
            0.1027,
            0.1124,
        ]

    else:
        size = 10000
        lower = 10
        probabilities = [
            0.0882,
            0.2092,
            0.2483,
            0.1933,
            0.1208,
            0.0675,
            0.0727,
        ]

    count = n // size
    frequencies = [0] * len(probabilities)

    for i in range(count):
        current = 0
        longest = 0

        for bit in bits[i * size:(i + 1) * size]:
            current = current + 1 if bit == 1 else 0
            longest = max(longest, current)

        category = min(
            max(longest - lower, 0),
            len(probabilities) - 1,
        )

        frequencies[category] += 1

    chi2 = sum(
        (observed - count * probability) ** 2
        / (count * probability)
        for observed, probability
        in zip(frequencies, probabilities)
    )

    p = gammaincc((len(probabilities) - 1) / 2, chi2 / 2)

    note = (
        f"M={size}, bloki={count}, "
        f"pominięte bity={n % size}"
    )

    return make_result("Longest Run", [p], alpha, note)


def _psi_squared(bits, size):
    if size == 0:
        return 0.0

    n = len(bits)
    counts = [0] * (2 ** size)
    pattern = 0

    for bit in bits[:size]:
        pattern = (pattern << 1) | int(bit)

    mask = (2 ** size) - 1

    for start in range(n):
        counts[pattern] += 1
        next_bit = int(bits[(start + size) % n])
        pattern = ((pattern << 1) & mask) | next_bit

    return (2 ** size / n) * sum(c * c for c in counts) - n


# 5. Serial Test — zwraca dwie wartości p.
def serial_test(bits, alpha=0.01, m=2):
    n = validate_bits(bits)

    if not isinstance(m, int) or m < 2:
        raise ValueError(
            "Parametr m musi być liczbą całkowitą >= 2."
        )

    if m >= n.bit_length() - 3:
        return make_result(
            "Serial",
            [],
            alpha,
            "Za mało bitów dla wybranego m.",
        )

    psi_m = _psi_squared(bits, m)
    psi_previous = _psi_squared(bits, m - 1)
    psi_before = _psi_squared(bits, m - 2)

    delta1 = max(0.0, psi_m - psi_previous)
    delta2 = max(
        0.0,
        psi_m - 2 * psi_previous + psi_before,
    )

    p1 = gammaincc(2 ** (m - 2), delta1 / 2)
    p2 = gammaincc(2 ** (m - 3), delta2 / 2)

    return make_result(
        "Serial",
        [p1, p2],
        alpha,
        f"m={m}; wyniki p1 i p2",
    )


# 6. Approximate Entropy Test.
def approximate_entropy_test(bits, alpha=0.01, m=2):
    n = validate_bits(bits)

    if not isinstance(m, int) or m < 1:
        raise ValueError(
            "Parametr m musi być liczbą całkowitą >= 1."
        )

    # Zalecenie NIST: m < floor(log2(n)) - 5.
    if m >= n.bit_length() - 6:
        return make_result(
            "Approximate Entropy",
            [],
            alpha,
            "Za mało bitów dla wybranego m.",
        )

    def phi(size):
        counts = [0] * (2 ** size)
        pattern = 0

        for bit in bits[:size]:
            pattern = (pattern << 1) | int(bit)

        mask = (2 ** size) - 1

        for start in range(n):
            counts[pattern] += 1
            next_bit = int(bits[(start + size) % n])
            pattern = ((pattern << 1) & mask) | next_bit

        return sum(
            (count / n) * log(count / n)
            for count in counts
            if count > 0
        )

    approximate_entropy = phi(m) - phi(m + 1)

    chi2 = max(
        0.0,
        2 * n * (log(2) - approximate_entropy),
    )

    p = gammaincc(2 ** (m - 1), chi2 / 2)

    return make_result(
        "Approximate Entropy",
        [p],
        alpha,
        f"m={m}; ApEn={approximate_entropy:.6f}",
    )


# 7. Autocorrelation Test — bitowy wariant dwumianowy.
# Hipoteza: niezależne bity, prawdopodobieństwa 0 i 1 równe 0.5.
def autocorrelation_test(bits, alpha=0.01, lag=1):
    n = validate_bits(bits)

    if not isinstance(lag, int) or not 1 <= lag < n:
        raise ValueError(
            "Przesunięcie lag musi być liczbą całkowitą od 1 do n-1."
        )

    pairs = n - lag

    different = sum(
        int(bits[i] != bits[i + lag])
        for i in range(pairs)
    )

    p = binomtest(
        different,
        n=pairs,
        p=0.5,
        alternative="two-sided",
    ).pvalue

    # Korelacja przy kodowaniu bitów jako -1 i +1.
    correlation = 1 - 2 * different / pairs

    return make_result(
        "Autocorrelation",
        [p],
        alpha,
        f"lag={lag}; r={correlation:.6f}; "
        f"różniące się pary={different}/{pairs}",
    )


def run_all_tests(bits, alpha=0.01):
    validate_bits(bits)

    functions = [
        monobit_test,
        block_frequency_test,
        runs_test,
        longest_run_test,
        serial_test,
        approximate_entropy_test,
        autocorrelation_test,
    ]

    # Wszystkie testy analizują tę samą sekwencję.
    return [
        function(bits, alpha=alpha)
        for function in functions
    ]


def main():
    if not LENGTHS or REPETITIONS < 1:
        raise ValueError(
            "Podaj długości sekwencji i dodatnią liczbę powtórzeń."
        )

    if any(not isinstance(n, int) or n < 100 for n in LENGTHS):
        raise ValueError(
            "Długości muszą być liczbami całkowitymi >= 100."
        )

    if not 0 < ALPHA < 1:
        raise ValueError("ALPHA musi należeć do przedziału (0, 1).")

    generators = {
        "CLASSICAL": ClassicalGenerator(),
        "QUANTUM_IDEAL": QuantumGenerator(),
        "QUANTUM_NOISY": NoisyQuantumGenerator(),
    }

    # Każde uruchomienie dostaje osobny folder.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    output = (
        Path(__file__).resolve().parent
        / "experiment_results"
        / stamp
    )

    output.mkdir(parents=True)

    details_path = output / "results.csv"
    summary_path = output / "summary.csv"

    groups = {}
    total = len(generators) * len(LENGTHS) * REPETITIONS
    completed = 0

    fields = [
        "generator",
        "n_bits",
        "repetition",
        "test",
        "alpha",
        "p1",
        "p2",
        "status",
        "generation_seconds",
        "suite_seconds",
        "sequence_sha256",
        "note",
    ]

    print(f"Liczba sekwencji: {total}", flush=True)
    print("Liczba testów dla każdej sekwencji: 7", flush=True)
    print(f"Wyniki: {output}", flush=True)

    with details_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter=";",
        )

        writer.writeheader()
        handle.flush()

        for n in LENGTHS:
            for repetition in range(1, REPETITIONS + 1):
                for name, generator in generators.items():
                    print(
                        f"[{completed + 1}/{total}] {name}, "
                        f"bity={n}, powtórzenie={repetition}: ",
                        end="",
                        flush=True,
                    )

                    # Czas generowania sekwencji.
                    start = perf_counter()
                    bits = generator.generate(n)
                    generation_seconds = perf_counter() - start

                    if len(bits) != n:
                        raise ValueError(
                            f"{name} zwrócił {len(bits)} "
                            f"zamiast {n} bitów."
                        )

                    validate_bits(bits)

                    fingerprint = hashlib.sha256(
                        bytes(bits)
                    ).hexdigest()

                    # Czas wykonania całego zestawu testów.
                    start = perf_counter()
                    results = run_all_tests(bits, alpha=ALPHA)
                    suite_seconds = perf_counter() - start

                    for result in results:
                        p = result["p_values"]

                        writer.writerow({
                            "generator": name,
                            "n_bits": n,
                            "repetition": repetition,
                            "test": result["name"],
                            "alpha": ALPHA,
                            "p1": p[0] if p else "",
                            "p2": p[1] if len(p) > 1 else "",
                            "status": result["status"],
                            "generation_seconds": generation_seconds,
                            "suite_seconds": suite_seconds,
                            "sequence_sha256": fingerprint,
                            "note": result["note"],
                        })

                        key = (name, n, result["name"])

                        if key not in groups:
                            groups[key] = {
                                "PASS": 0,
                                "FAIL": 0,
                                "SKIP": 0,
                                "generation_sum": 0.0,
                                "suite_sum": 0.0,
                                "hashes": set(),
                            }

                        group = groups[key]
                        group[result["status"]] += 1
                        group["generation_sum"] += generation_seconds
                        group["suite_sum"] += suite_seconds
                        group["hashes"].add(fingerprint)

                    # Zapis wyników po każdej sekwencji.
                    handle.flush()
                    completed += 1

                    print(
                        " | ".join(
                            f"{r['name']}={r['status']}"
                            for r in results
                        ),
                        flush=True,
                    )

    summary_fields = [
        "generator",
        "n_bits",
        "test",
        "alpha",
        "total_trials",
        "evaluated_trials",
        "passed",
        "failed",
        "skipped",
        "pass_rate_percent",
        "unique_sequences",
        "mean_generation_seconds",
        "mean_suite_seconds",
    ]

    with summary_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=summary_fields,
            delimiter=";",
        )

        writer.writeheader()

        for (name, n, test), group in groups.items():
            evaluated = group["PASS"] + group["FAIL"]
            trials = evaluated + group["SKIP"]

            pass_rate = (
                100 * group["PASS"] / evaluated
                if evaluated else ""
            )

            writer.writerow({
                "generator": name,
                "n_bits": n,
                "test": test,
                "alpha": ALPHA,
                "total_trials": trials,
                "evaluated_trials": evaluated,
                "passed": group["PASS"],
                "failed": group["FAIL"],
                "skipped": group["SKIP"],
                "pass_rate_percent": pass_rate,
                "unique_sequences": len(group["hashes"]),
                "mean_generation_seconds":
                    group["generation_sum"] / trials,
                "mean_suite_seconds":
                    group["suite_sum"] / trials,
            })

    print("\nGotowe.")
    print(f"Szczegółowe wyniki: {details_path}")
    print(f"Podsumowanie: {summary_path}")


if __name__ == "__main__":
    main()