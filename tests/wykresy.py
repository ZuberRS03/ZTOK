
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


GENERATORS = [
    "CLASSICAL",
    "QUANTUM_IDEAL",
    "QUANTUM_NOISY",
]

LABELS = {
    "CLASSICAL": "Klasyczny PRNG",
    "QUANTUM_IDEAL": "Kwantowy idealny",
    "QUANTUM_NOISY": "Kwantowy z szumem",
}

COLORS = {
    "CLASSICAL": "#2563EB",
    "QUANTUM_IDEAL": "#8B5CF6",
    "QUANTUM_NOISY": "#D97706",
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


def save_plot(fig, output, filename):
    path = output / filename
    fig.savefig(path, dpi=240, bbox_inches="tight")
    print(f"Zapisano: {path}")


def main():

    root = Path(__file__).resolve().parent / "experiment_results"

    if not root.exists():
        raise SystemExit(
            "Brak folderu experiment_results. "
            "Najpierw uruchom eksperyment."
        )

    # Wybieramy tylko zakonczone eksperymenty podstawowe.
    # Pomijamy foldery noise_ oraz niepelne eksperymenty.
    folders = sorted(
        (
            folder for folder in root.iterdir()
            if folder.is_dir()
            and (folder / "summary.csv").is_file()
            and (folder / "results.csv").is_file()
        ),
        key=lambda folder: folder.name,
    )

    if not folders:
        raise SystemExit(
            "Nie znaleziono zakonczonego eksperymentu "
            "z plikami results.csv i summary.csv."
        )

    # Najnowszy zakonczony eksperyment podstawowy
    folder = folders[-1]

    results = pd.read_csv(
        folder / "results.csv",
        sep=";",
        encoding="utf-8-sig",
    )

    summary = pd.read_csv(
        folder / "summary.csv",
        sep=";",
        encoding="utf-8-sig",
    )

    if results.empty or summary.empty:
        raise SystemExit("Pliki wynikow sa puste.")

    # Sprawdzamy obecnosc wszystkich siedmiu testow.
    available = set(summary["test"])

    missing = [
        test for test in TESTS
        if test not in available
    ]

    if missing:
        raise SystemExit(
            "W wynikach brakuje testow: "
            + ", ".join(missing)
        )

    output = folder / "wykresy"
    output.mkdir(exist_ok=True)

    print(f"Odczytuje wyniki z:\n{folder}\n")

    lengths = sorted(summary["n_bits"].unique())

    length_labels = [
        f"{int(n):,}".replace(",", " ")
        for n in lengths
    ]

    alpha = float(results["alpha"].iloc[0])

    plt.rcParams.update({
        "font.size": 11,
        "axes.titlesize": 13,
        "figure.titlesize": 17,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "axes.facecolor": "#F8FAFC",
    })

    legend = [
        Patch(
            color=COLORS[g],
            label=LABELS[g]
        )
        for g in GENERATORS
    ]

    # =========================================================
    # WYKRES 1 — ZALICZANIE SIEDMIU TESTOW
    # =========================================================

    fig, axes = plt.subplots(
        1,
        len(lengths),
        figsize=(5.5 * len(lengths), 8),
        squeeze=False,
    )

    positions = np.arange(len(TESTS))

    for ax, n in zip(axes[0], lengths):

        for index, generator in enumerate(GENERATORS):

            selected = summary[
                (summary["generator"] == generator)
                & (summary["n_bits"] == n)
            ]

            rates = (
                selected.set_index("test")["pass_rate_percent"]
                .reindex(TESTS)
                .to_numpy(dtype=float)
            )

            y = positions + (index - 1) * 0.24

            ax.barh(
                y,
                rates,
                height=0.21,
                color=COLORS[generator],
            )

            for position, rate in zip(y, rates):

                if np.isnan(rate):
                    ax.text(
                        2,
                        position,
                        "SKIP",
                        va="center",
                        fontsize=9,
                        color=COLORS[generator],
                    )

                else:
                    inside = rate >= 25

                    ax.text(
                        rate / 2 if inside else min(rate + 2, 103),
                        position,
                        f"{rate:.1f}%",
                        ha="center" if inside else "left",
                        va="center",
                        color=(
                            "white"
                            if inside
                            else COLORS[generator]
                        ),
                        fontsize=9,
                    )

        ax.set_title(
            f"{int(n):,} bitow".replace(",", " ")
        )

        ax.set_yticks(positions, TESTS)
        ax.invert_yaxis()
        ax.set_xlim(0, 105)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xlabel("Zaliczone proby [%]")
        ax.grid(axis="x", alpha=0.2)
        ax.set_axisbelow(True)

    fig.suptitle("Zaliczanie testow statystycznych")

    fig.legend(
        handles=legend,
        loc="lower center",
        ncol=3,
        frameon=False,
    )

    fig.text(
        0.5,
        0.07,
        "Procent PASS liczony wsrod prob PASS/FAIL. "
        "SKIP oznacza pominiecie testu.",
        ha="center",
        fontsize=10,
    )

    fig.tight_layout(rect=(0, 0.12, 1, 0.93))

    save_plot(
        fig,
        output,
        "01_zaliczanie_testow.png"
    )

    plt.close(fig)

    # =========================================================
    # WYKRES 2 — CZAS GENEROWANIA
    # =========================================================

    # Czas powtarza sie w podsumowaniu dla kazdego testu.
    # Wybieramy jeden wiersz na generator i dlugosc.
    times = summary.drop_duplicates(
        ["generator", "n_bits"]
    )

    fig, ax = plt.subplots(figsize=(9, 5.5))

    for generator in GENERATORS:

        selected = times[
            times["generator"] == generator
        ].sort_values("n_bits")

        ax.plot(
            selected["n_bits"],
            selected["mean_generation_seconds"],
            marker="o",
            markersize=7,
            linewidth=2.5,
            color=COLORS[generator],
            label=LABELS[generator],
        )

    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.set_xticks(lengths, length_labels)

    ax.set_xlabel("Liczba bitow")
    ax.set_ylabel("Sredni czas generowania [s]")

    ax.set_title(
        "Czas generowania — skala logarytmiczna"
    )

    ax.grid(True, which="both", alpha=0.2)
    ax.legend(frameon=False)

    fig.tight_layout()

    save_plot(
        fig,
        output,
        "02_czas_generowania.png"
    )

    plt.close(fig)

    # =========================================================
    # WYKRES 3 — WARTOSCI P DLA SIEDMIU TESTOW
    # =========================================================

    # Serial zwraca dwie wartosci p.
    # Dlatego wykres ma osiem paneli.
    metrics = [
        ("Monobit", "p1", "Monobit"),
        ("Block Frequency", "p1", "Block Frequency"),
        ("Runs", "p1", "Runs"),
        ("Longest Run", "p1", "Longest Run"),
        ("Serial", "p1", "Serial — p1"),
        ("Serial", "p2", "Serial — p2"),
        (
            "Approximate Entropy",
            "p1",
            "Approximate Entropy"
        ),
        ("Autocorrelation", "p1", "Autocorrelation"),
    ]

    fig, axes = plt.subplots(
        3,
        3,
        figsize=(16, 12),
    )

    # Dziewiaty panel pozostaje pusty.
    axes.flat[-1].set_visible(False)

    for ax, (test, column, title) in zip(
        axes.flat,
        metrics
    ):

        for index, generator in enumerate(GENERATORS):

            for length_index, n in enumerate(lengths):

                selected = results[
                    (results["generator"] == generator)
                    & (results["n_bits"] == n)
                    & (results["test"] == test)
                ]

                values = (
                    selected[column]
                    .dropna()
                    .to_numpy(dtype=float)
                )

                if len(values) == 0:
                    continue

                # Rozsuwamy punkty, aby pokazac powtorzenia.
                x = (
                    length_index
                    + (index - 1) * 0.22
                    + np.linspace(
                        -0.055,
                        0.055,
                        len(values),
                    )
                )

                ax.scatter(
                    x,
                    values,
                    s=24,
                    alpha=0.65,
                    color=COLORS[generator],
                    edgecolors="none",
                )

        # Obszar odrzucenia hipotezy zerowej
        ax.axhspan(
            0,
            alpha,
            facecolor="#EF4444",
            alpha=0.10,
        )

        # Prog istotnosci
        ax.axhline(
            alpha,
            color="#EF4444",
            linestyle="--",
            linewidth=1.3,
        )

        ax.set_title(title)

        ax.set_xticks(
            range(len(lengths)),
            length_labels,
        )

        ax.set_xlim(-0.5, len(lengths) - 0.5)
        ax.set_ylim(-0.035, 1.035)

        ax.set_xlabel("Liczba bitow")
        ax.set_ylabel("Wartosc p")

        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)

    fig.suptitle(
        "Wartosci p w poszczegolnych powtorzeniach"
    )

    fig.legend(
        handles=legend,
        loc="lower center",
        ncol=3,
        frameon=False,
    )

    fig.text(
        0.5,
        0.06,
        f"Kazdy punkt to jedno powtorzenie. "
        f"Czerwona linia: prog α = {alpha}.",
        ha="center",
        fontsize=10,
    )

    fig.tight_layout(rect=(0, 0.11, 1, 0.93))

    save_plot(
        fig,
        output,
        "03_wartosci_p.png"
    )

    plt.close(fig)

    print(
        f"\nGotowe! Wszystkie 3 wykresy znajduja sie w:\n"
        f"{output}"
    )


if __name__ == "__main__":
    main()
