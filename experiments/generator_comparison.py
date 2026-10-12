from datetime import datetime
from pathlib import Path
from time import perf_counter
import csv
import hashlib

from generators.classical_generator import ClassicalGenerator
from generators.quantum_generator import QuantumGenerator
from generators.noisy_quantum_generator import NoisyQuantumGenerator

from tests.statistical_tests import (
    run_all_tests,
    validate_bits,
)


LENGTHS = [
    1000,
    10000,
    100000,
]

REPETITIONS = 30
ALPHA = 0.01


def run_generator_comparison():
    if (
        not LENGTHS
        or REPETITIONS < 1
    ):
        raise ValueError(
            "Podaj długości sekwencji "
            "i dodatnią liczbę powtórzeń."
        )

    if any(
        not isinstance(n, int)
        or n < 100
        for n in LENGTHS
    ):
        raise ValueError(
            "Długości muszą być "
            "liczbami całkowitymi >= 100."
        )

    if not 0 < ALPHA < 1:
        raise ValueError(
            "ALPHA musi należeć "
            "do przedziału (0, 1)."
        )

    generators = {
        "CLASSICAL":
            ClassicalGenerator(),

        "QUANTUM_IDEAL":
            QuantumGenerator(),

        "QUANTUM_NOISY":
            NoisyQuantumGenerator(),
    }

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    project_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    output = (
        project_root
        / "experiment_results"
        / stamp
    )

    output.mkdir(
        parents=True
    )

    details_path = (
        output
        / "results.csv"
    )

    summary_path = (
        output
        / "summary.csv"
    )

    groups = {}

    total = (
        len(generators)
        * len(LENGTHS)
        * REPETITIONS
    )

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

    print(
        f"Liczba sekwencji: {total}",
        flush=True
    )

    print(
        "Liczba testów dla "
        "każdej sekwencji: 7",
        flush=True
    )

    print(
        f"Wyniki: {output}",
        flush=True
    )

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

            for repetition in range(
                1,
                REPETITIONS + 1
            ):

                for (
                    name,
                    generator
                ) in generators.items():

                    print(
                        f"[{completed + 1}/{total}] "
                        f"{name}, "
                        f"bity={n}, "
                        f"powtórzenie={repetition}: ",
                        end="",
                        flush=True,
                    )

                    start = perf_counter()

                    bits = generator.generate(
                        n
                    )

                    generation_seconds = (
                        perf_counter()
                        - start
                    )

                    if len(bits) != n:
                        raise ValueError(
                            f"{name} zwrócił "
                            f"{len(bits)} "
                            f"zamiast {n} bitów."
                        )

                    validate_bits(bits)

                    fingerprint = (
                        hashlib.sha256(
                            bytes(bits)
                        ).hexdigest()
                    )

                    start = perf_counter()

                    results = run_all_tests(
                        bits,
                        alpha=ALPHA
                    )

                    suite_seconds = (
                        perf_counter()
                        - start
                    )

                    for result in results:
                        p = result[
                            "p_values"
                        ]

                        writer.writerow({
                            "generator":
                                name,

                            "n_bits":
                                n,

                            "repetition":
                                repetition,

                            "test":
                                result["name"],

                            "alpha":
                                ALPHA,

                            "p1":
                                (
                                    p[0]
                                    if p
                                    else ""
                                ),

                            "p2":
                                (
                                    p[1]
                                    if len(p) > 1
                                    else ""
                                ),

                            "status":
                                result["status"],

                            "generation_seconds":
                                generation_seconds,

                            "suite_seconds":
                                suite_seconds,

                            "sequence_sha256":
                                fingerprint,

                            "note":
                                result["note"],
                        })

                        key = (
                            name,
                            n,
                            result["name"]
                        )

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

                        group[
                            result["status"]
                        ] += 1

                        group[
                            "generation_sum"
                        ] += generation_seconds

                        group[
                            "suite_sum"
                        ] += suite_seconds

                        group[
                            "hashes"
                        ].add(
                            fingerprint
                        )

                    handle.flush()

                    completed += 1

                    print(
                        " | ".join(
                            (
                                f"{r['name']}="
                                f"{r['status']}"
                            )
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

        for (
            name,
            n,
            test
        ), group in groups.items():

            evaluated = (
                group["PASS"]
                + group["FAIL"]
            )

            trials = (
                evaluated
                + group["SKIP"]
            )

            pass_rate = (
                100
                * group["PASS"]
                / evaluated
                if evaluated
                else ""
            )

            writer.writerow({
                "generator":
                    name,

                "n_bits":
                    n,

                "test":
                    test,

                "alpha":
                    ALPHA,

                "total_trials":
                    trials,

                "evaluated_trials":
                    evaluated,

                "passed":
                    group["PASS"],

                "failed":
                    group["FAIL"],

                "skipped":
                    group["SKIP"],

                "pass_rate_percent":
                    pass_rate,

                "unique_sequences":
                    len(
                        group["hashes"]
                    ),

                "mean_generation_seconds":
                    (
                        group["generation_sum"]
                        / trials
                    ),

                "mean_suite_seconds":
                    (
                        group["suite_sum"]
                        / trials
                    ),
            })

    print()
    print("Eksperyment zakończony.")
    print(
        f"Szczegółowe wyniki: "
        f"{details_path}"
    )
    print(
        f"Podsumowanie: "
        f"{summary_path}"
    )

    return output