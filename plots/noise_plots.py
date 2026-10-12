from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from experiments.noise_experiment import (
    LENGTHS,
    NOISE_CONFIGS,
    LABELS,
    COLORS,
    TESTS,
)


def plot_ones_ratio(
    df,
    output
):
    data = df.drop_duplicates(
        [
            "generator",
            "n_bits",
            "repetition"
        ]
    )

    fig, ax = plt.subplots(
        figsize=(
            10,
            6
        )
    )

    x = np.arange(
        len(LENGTHS)
    )

    width = 0.19

    for (
        i,
        name
    ) in enumerate(
        NOISE_CONFIGS
    ):

        means = []

        for n in LENGTHS:

            selected = data[
                (
                    data["generator"]
                    == name
                )
                &
                (
                    data["n_bits"]
                    == n
                )
            ]

            means.append(
                selected[
                    "ones_ratio"
                ].mean() * 100
            )

        positions = (
            x
            + (i - 1.5)
            * width
        )

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

    ax.set_xticks(
        x,
        [
            "1 000",
            "10 000",
            "100 000"
        ]
    )

    ax.set_xlabel(
        "Długość sekwencji [bity]"
    )

    ax.set_ylabel(
        "Średni udział jedynek [%]"
    )

    ax.set_title(
        "Wpływ szumu na proporcję jedynek"
    )

    ax.set_ylim(
        44,
        54
    )

    ax.grid(
        axis="y",
        alpha=0.2
    )

    ax.set_axisbelow(
        True
    )

    ax.legend(
        fontsize=9,
        ncol=2
    )

    fig.tight_layout()

    fig.savefig(
        output
        / "01_proporcja_jedynek.png",
        dpi=240,
        bbox_inches="tight"
    )

    plt.close(fig)


def plot_monobit(
    summary,
    output
):
    fig, ax = plt.subplots(
        figsize=(
            10,
            6
        )
    )

    x = np.arange(
        len(LENGTHS)
    )

    width = 0.19

    for (
        i,
        name
    ) in enumerate(
        NOISE_CONFIGS
    ):

        rates = []

        for n in LENGTHS:

            selected = summary[
                (
                    summary["generator"]
                    == name
                )
                &
                (
                    summary["n_bits"]
                    == n
                )
                &
                (
                    summary["test"]
                    == "Monobit"
                )
            ]

            rates.append(
                (
                    selected[
                        "pass_rate_percent"
                    ].iloc[0]
                    if not selected.empty
                    else np.nan
                )
            )

        positions = (
            x
            + (i - 1.5)
            * width
        )

        bars = ax.bar(
            positions,
            rates,
            width=width,
            color=COLORS[name],
            label=LABELS[name],
        )

        for (
            bar,
            rate
        ) in zip(
            bars,
            rates
        ):

            if not np.isnan(rate):

                ax.text(
                    (
                        bar.get_x()
                        + bar.get_width()
                        / 2
                    ),
                    rate + 1.5,
                    f"{rate:.1f}%",
                    ha="center",
                    fontsize=8,
                )

    ax.set_xticks(
        x,
        [
            "1 000",
            "10 000",
            "100 000"
        ]
    )

    ax.set_xlabel(
        "Długość sekwencji [bity]"
    )

    ax.set_ylabel(
        "Zaliczone próby [%]"
    )

    ax.set_title(
        "Wpływ szumu na wyniki testu Monobit"
    )

    ax.set_ylim(
        0,
        112
    )

    ax.grid(
        axis="y",
        alpha=0.2
    )

    ax.set_axisbelow(
        True
    )

    ax.legend(
        fontsize=9,
        ncol=2
    )

    fig.tight_layout()

    fig.savefig(
        output
        / "02_monobit_szum.png",
        dpi=240,
        bbox_inches="tight"
    )

    plt.close(fig)


def plot_all_tests(
    summary,
    output
):
    fig, axes = plt.subplots(
        1,
        len(LENGTHS),
        figsize=(
            17,
            7
        ),
        sharey=True
    )

    y = np.arange(
        len(TESTS)
    )

    height = 0.19

    for ax, n in zip(
        axes,
        LENGTHS
    ):

        for (
            i,
            name
        ) in enumerate(
            NOISE_CONFIGS
        ):

            selected = summary[
                (
                    summary["generator"]
                    == name
                )
                &
                (
                    summary["n_bits"]
                    == n
                )
            ]

            rates = (
                selected
                .set_index("test")[
                    "pass_rate_percent"
                ]
                .reindex(TESTS)
                .to_numpy(
                    dtype=float
                )
            )

            ax.barh(
                (
                    y
                    + (i - 1.5)
                    * height
                ),
                rates,
                height=height,
                color=COLORS[name],
                label=LABELS[name],
            )

        ax.set_title(
            (
                f"{n:,} bitów"
                .replace(",", " ")
            )
        )

        ax.set_yticks(
            y,
            TESTS
        )

        ax.invert_yaxis()

        ax.set_xlim(
            0,
            105
        )

        ax.set_xlabel(
            "Zaliczone próby [%]"
        )

        ax.grid(
            axis="x",
            alpha=0.2
        )

        ax.set_axisbelow(
            True
        )

    handles, labels = (
        axes[0]
        .get_legend_handles_labels()
    )

    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=4,
        frameon=False
    )

    fig.suptitle(
        "Wpływ konfiguracji szumu "
        "na wyniki testów",
        fontsize=16
    )

    fig.tight_layout(
        rect=(
            0,
            0.10,
            1,
            0.94
        )
    )

    fig.savefig(
        output
        / "03_wszystkie_testy_szum.png",
        dpi=240,
        bbox_inches="tight"
    )

    plt.close(fig)


def generate_noise_plots(
    folder
):
    folder = Path(folder)

    results_path = (
        folder
        / "noise_results.csv"
    )

    summary_path = (
        folder
        / "noise_summary.csv"
    )

    if (
        not results_path.is_file()
        or not summary_path.is_file()
    ):
        raise ValueError(
            "Brak plików wynikowych "
            "eksperymentu szumu."
        )

    df = pd.read_csv(
        results_path,
        sep=";",
        encoding="utf-8-sig"
    )

    summary = pd.read_csv(
        summary_path,
        sep=";",
        encoding="utf-8-sig"
    )

    plot_ones_ratio(
        df,
        folder
    )

    plot_monobit(
        summary,
        folder
    )

    plot_all_tests(
        summary,
        folder
    )

    print()
    print(
        "Wykresy analizy szumu "
        "zostały wygenerowane."
    )