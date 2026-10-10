
from pathlib import Path
from datetime import datetime
from time import perf_counter
import csv
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Dodajemy główny katalog ZTOK do ścieżek Pythona
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generators.noisy_quantum_generator import NoisyQuantumGenerator
from testTest import run_all_tests


LENGTHS = [1000, 10000, 100000]
REPETITIONS = 30
ALPHA = 0.01

# Porównujemy cztery konfiguracje błędów odczytu.
NOISE_CONFIGS = {
    "IDEAL": (0.00, 0.00),
    "SYMMETRIC": (0.02, 0.02),
    "ASYMMETRIC_LOW": (0.02, 0.04),
    "ASYMMETRIC_HIGH": (0.02, 0.08),
}

LABELS = {
    "IDEAL": "Brak szumu",
    "SYMMETRIC": "Symetryczny 2% / 2%",
    "ASYMMETRIC_LOW": "Asymetryczny 2% / 4%",
    "ASYMMETRIC_HIGH": "Asymetryczny 2% / 8%",
}

COLORS = {
    "IDEAL": "#2563EB",
    "SYMMETRIC": "#8B5CF6",
    "ASYMMETRIC_LOW": "#16A34A",
    "ASYMMETRIC_HIGH": "#D97706",
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


# ============================================================
# EKSPERYMENT
# ============================================================

def run_experiment(output):

    records = []

    generators = {
        name: NoisyQuantumGenerator(
            error_0_to_1=p01,
            error_1_to_0=p10
        )
        for name, (p01, p10) in NOISE_CONFIGS.items()
    }

    total = len(NOISE_CONFIGS) * len(LENGTHS) * REPETITIONS
    completed = 0

    for n in LENGTHS:
        for repetition in range(1, REPETITIONS + 1):
            for name, generator in generators.items():

                completed += 1

                print(
                    f"[{completed}/{total}] "
                    f"{name}, n={n}, próba={repetition}",
                    flush=True
                )

                # Generowanie bitów
                start = perf_counter()
                bits = generator.generate(n)
                generation_time = perf_counter() - start

                if len(bits) != n:
                    raise ValueError("Nieprawidłowa długość sekwencji.")

                # Rzeczywisty udział jedynek
                ones_ratio = sum(bits) / n

                # Teoretyczny udział jedynek
                p01, p10 = NOISE_CONFIGS[name]
                expected_ones = 0.5 * (1 + p01 - p10)

                # Wszystkie 7 testów
                test_results = run_all_tests(bits, alpha=ALPHA)

                for result in test_results:

                    values = result["p_values"]

                    records.append({
                        "generator": name,
                        "n_bits": n,
                        "repetition": repetition,
                        "test": result["name"],
                        "status": result["status"],
                        "p1": values[0] if values else np.nan,
                        "p2": values[1] if len(values) > 1 else np.nan,
                        "ones_ratio": ones_ratio,
                        "expected_ones": expected_ones,
                        "generation_seconds": generation_time,
                    })

    df = pd.DataFrame(records)

    df.to_csv(
        output / "noise_results.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )

    # Podsumowanie statystyczne
    summary = (
        df.groupby(["generator", "n_bits", "test"], sort=False)
        .agg(
            passed=("status", lambda x: (x == "PASS").sum()),
            failed=("status", lambda x: (x == "FAIL").sum()),
            skipped=("status", lambda x: (x == "SKIP").sum()),
        )
        .reset_index()
    )

    evaluated = summary["passed"] + summary["failed"]

    summary["pass_rate_percent"] = np.where(
        evaluated > 0,
        100 * summary["passed"] / evaluated.replace(0, np.nan),
        np.nan
    )

    summary.to_csv(
        output / "noise_summary.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )

    return df, summary


# ============================================================
# WYKRES 1 — PROPORCJA JEDYNEK
# ============================================================

def plot_ones_ratio(df, output):

    # Jeden pomiar na sekwencję, nie na każdy test
    data = df.drop_duplicates(
        ["generator", "n_bits", "repetition"]
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(LENGTHS))
    width = 0.19

    for i, name in enumerate(NOISE_CONFIGS):

        means = []

        for n in LENGTHS:
            selected = data[
                (data["generator"] == name)
                & (data["n_bits"] == n)
            ]

            means.append(selected["ones_ratio"].mean() * 100)

        positions = x + (i - 1.5) * width

        ax.bar(
            positions,
            means,
            width=width,
            color=COLORS[name],
            label=LABELS[name],
        )

    ax.axhline(
        50,
        color="#DC2626",
        linestyle="--",
        linewidth=1.8,
        label="Idealny udział: 50%"
    )

    ax.set_xticks(x, ["1 000", "10 000", "100 000"])
    ax.set_xlabel("Długość sekwencji [bity]")
    ax.set_ylabel("Średni udział jedynek [%]")
    ax.set_title("Wpływ szumu na proporcję jedynek")

    # Pokazujemy odchylenia od 50% dokładniej.
    ax.set_ylim(44, 54)

    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, ncol=2)

    fig.tight_layout()
    fig.savefig(
        output / "01_proporcja_jedynek.png",
        dpi=240,
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# WYKRES 2 — ZALICZENIA TESTU MONOBIT
# ============================================================

def plot_monobit(summary, output):

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(LENGTHS))
    width = 0.19

    for i, name in enumerate(NOISE_CONFIGS):

        rates = []

        for n in LENGTHS:
            selected = summary[
                (summary["generator"] == name)
                & (summary["n_bits"] == n)
                & (summary["test"] == "Monobit")
            ]

            rates.append(
                selected["pass_rate_percent"].iloc[0]
                if not selected.empty else np.nan
            )

        positions = x + (i - 1.5) * width

        bars = ax.bar(
            positions,
            rates,
            width=width,
            color=COLORS[name],
            label=LABELS[name],
        )

        for bar, rate in zip(bars, rates):
            if not np.isnan(rate):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    rate + 1.5,
                    f"{rate:.1f}%",
                    ha="center",
                    fontsize=8,
                )

    ax.set_xticks(x, ["1 000", "10 000", "100 000"])
    ax.set_xlabel("Długość sekwencji [bity]")
    ax.set_ylabel("Zaliczone próby [%]")
    ax.set_title("Wpływ szumu na wyniki testu Monobit")
    ax.set_ylim(0, 112)

    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, ncol=2)

    fig.tight_layout()
    fig.savefig(
        output / "02_monobit_szum.png",
        dpi=240,
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# WYKRES 3 — WSZYSTKIE SIEDEM TESTÓW
# ============================================================

def plot_all_tests(summary, output):

    fig, axes = plt.subplots(
        1, len(LENGTHS),
        figsize=(17, 7),
        sharey=True
    )

    y = np.arange(len(TESTS))
    height = 0.19

    for ax, n in zip(axes, LENGTHS):

        for i, name in enumerate(NOISE_CONFIGS):

            selected = summary[
                (summary["generator"] == name)
                & (summary["n_bits"] == n)
            ]

            rates = (
                selected.set_index("test")["pass_rate_percent"]
                .reindex(TESTS)
                .to_numpy(dtype=float)
            )

            ax.barh(
                y + (i - 1.5) * height,
                rates,
                height=height,
                color=COLORS[name],
                label=LABELS[name],
            )

        ax.set_title(f"{n:,} bitów".replace(",", " "))
        ax.set_yticks(y, TESTS)
        ax.invert_yaxis()
        ax.set_xlim(0, 105)
        ax.set_xlabel("Zaliczone próby [%]")
        ax.grid(axis="x", alpha=0.2)
        ax.set_axisbelow(True)

    handles, labels = axes[0].get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=4,
        frameon=False
    )

    fig.suptitle(
        "Wpływ konfiguracji szumu na wyniki testów",
        fontsize=16
    )

    fig.tight_layout(rect=(0, 0.10, 1, 0.94))

    fig.savefig(
        output / "03_wszystkie_testy_szum.png",
        dpi=240,
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# MAIN
# ============================================================

def main():

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output = (
        Path(__file__).resolve().parent
        / "experiment_results"
        / f"noise_{stamp}"
    )

    output.mkdir(parents=True, exist_ok=True)

    print("EKSPERYMENT 2 — WPŁYW SZUMU")
    print(f"Liczba konfiguracji: {len(NOISE_CONFIGS)}")
    print(f"Liczba powtórzeń: {REPETITIONS}")
    print(f"Długości sekwencji: {LENGTHS}")
    print(f"Wyniki: {output}\n")

    df, summary = run_experiment(output)

    plot_ones_ratio(df, output)
    plot_monobit(summary, output)
    plot_all_tests(summary, output)

    print("\nGOTOWE!")
    print(f"Wyniki zapisano w: {output}")


if __name__ == "__main__":
    main()
