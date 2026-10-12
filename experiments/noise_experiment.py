from pathlib import Path
from datetime import datetime
from time import perf_counter

import numpy as np
import pandas as pd

from generators.noisy_quantum_generator import (
    NoisyQuantumGenerator
)

from tests.statistical_tests import (
    run_all_tests
)


LENGTHS = [
    1000,
    10000,
    100000,
]

REPETITIONS = 30
ALPHA = 0.01


NOISE_CONFIGS = {
    "IDEAL":
        (0.00, 0.00),

    "SYMMETRIC":
        (0.02, 0.02),

    "ASYMMETRIC_LOW":
        (0.02, 0.04),

    "ASYMMETRIC_HIGH":
        (0.02, 0.08),
}


LABELS = {
    "IDEAL":
        "Brak szumu",

    "SYMMETRIC":
        "Symetryczny 2% / 2%",

    "ASYMMETRIC_LOW":
        "Asymetryczny 2% / 4%",

    "ASYMMETRIC_HIGH":
        "Asymetryczny 2% / 8%",
}


COLORS = {
    "IDEAL":
        "#2563EB",

    "SYMMETRIC":
        "#8B5CF6",

    "ASYMMETRIC_LOW":
        "#16A34A",

    "ASYMMETRIC_HIGH":
        "#D97706",
}


TESTS = [
    "Monobit",
    "Block Frequency",
    "Runs",
    "Longest Run",
    "Serial",
    "Approximate Entropy",
    "Autocorrelation",
]


def run_experiment(output):
    records = []

    generators = {
        name:
            NoisyQuantumGenerator(
                error_0_to_1=p01,
                error_1_to_0=p10
            )

        for name, (
            p01,
            p10
        ) in NOISE_CONFIGS.items()
    }

    total = (
        len(NOISE_CONFIGS)
        * len(LENGTHS)
        * REPETITIONS
    )

    completed = 0

    for n in LENGTHS:

        for repetition in range(
            1,
            REPETITIONS + 1
        ):

            for (
                name,
                generator
            ) in generators.items():

                completed += 1

                print(
                    f"[{completed}/{total}] "
                    f"{name}, "
                    f"n={n}, "
                    f"próba={repetition}",
                    flush=True
                )

                start = perf_counter()

                bits = generator.generate(
                    n
                )

                generation_time = (
                    perf_counter()
                    - start
                )

                if len(bits) != n:
                    raise ValueError(
                        "Nieprawidłowa "
                        "długość sekwencji."
                    )

                ones_ratio = (
                    sum(bits) / n
                )

                p01, p10 = (
                    NOISE_CONFIGS[name]
                )

                expected_ones = (
                    0.5
                    * (
                        1
                        + p01
                        - p10
                    )
                )

                test_results = (
                    run_all_tests(
                        bits,
                        alpha=ALPHA
                    )
                )

                for result in test_results:

                    values = result[
                        "p_values"
                    ]

                    records.append({
                        "generator":
                            name,

                        "n_bits":
                            n,

                        "repetition":
                            repetition,

                        "test":
                            result["name"],

                        "status":
                            result["status"],

                        "p1":
                            (
                                values[0]
                                if values
                                else np.nan
                            ),

                        "p2":
                            (
                                values[1]
                                if len(values) > 1
                                else np.nan
                            ),

                        "ones_ratio":
                            ones_ratio,

                        "expected_ones":
                            expected_ones,

                        "generation_seconds":
                            generation_time,
                    })

    df = pd.DataFrame(
        records
    )

    df.to_csv(
        output
        / "noise_results.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )

    summary = (
        df
        .groupby(
            [
                "generator",
                "n_bits",
                "test"
            ],
            sort=False
        )
        .agg(
            passed=(
                "status",
                lambda x:
                    (x == "PASS").sum()
            ),

            failed=(
                "status",
                lambda x:
                    (x == "FAIL").sum()
            ),

            skipped=(
                "status",
                lambda x:
                    (x == "SKIP").sum()
            ),
        )
        .reset_index()
    )

    evaluated = (
        summary["passed"]
        + summary["failed"]
    )

    summary[
        "pass_rate_percent"
    ] = np.where(
        evaluated > 0,
        (
            100
            * summary["passed"]
            / evaluated.replace(
                0,
                np.nan
            )
        ),
        np.nan
    )

    summary.to_csv(
        output
        / "noise_summary.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )

    return df, summary


def run_noise_experiment():
    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
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
        / f"noise_{stamp}"
    )

    output.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "EKSPERYMENT 2 — WPŁYW SZUMU"
    )

    print(
        f"Liczba konfiguracji: "
        f"{len(NOISE_CONFIGS)}"
    )

    print(
        f"Liczba powtórzeń: "
        f"{REPETITIONS}"
    )

    print(
        f"Długości sekwencji: "
        f"{LENGTHS}"
    )

    print(
        f"Wyniki: {output}"
    )

    print()

    run_experiment(
        output
    )

    print()
    print("Eksperyment zakończony.")

    return output