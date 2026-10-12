from math import erfc, sqrt, log

from scipy.special import gammaincc
from scipy.stats import binomtest


def validate_bits(bits):
    if len(bits) < 100:
        raise ValueError(
            "Wymagane jest co najmniej 100 bitów."
        )

    if any(bit not in (0, 1) for bit in bits):
        raise ValueError(
            "Sekwencja musi zawierać tylko 0 i 1."
        )

    return len(bits)


def make_result(
    name,
    p_values,
    alpha=0.01,
    note=""
):
    if not 0 < alpha < 1:
        raise ValueError(
            "Alpha musi należeć do przedziału (0, 1)."
        )

    values = [float(p) for p in p_values]

    if any(not 0 <= p <= 1 for p in values):
        raise ValueError(
            "Nieprawidłowa wartość p."
        )

    if not values:
        status = "SKIP"
    else:
        status = (
            "PASS"
            if all(p >= alpha for p in values)
            else "FAIL"
        )

    return {
        "name": name,
        "p_values": values,
        "status": status,
        "note": note,
    }


# 1. Frequency (Monobit) Test
def monobit_test(bits, alpha=0.01):
    n = validate_bits(bits)

    total = 2 * sum(
        int(bit) for bit in bits
    ) - n

    p = erfc(
        abs(total) / sqrt(2 * n)
    )

    return make_result(
        "Monobit",
        [p],
        alpha
    )


# 2. Block Frequency Test
def block_frequency_test(
    bits,
    alpha=0.01,
    block_size=None
):
    n = validate_bits(bits)

    if block_size is None:
        block_size = max(
            20,
            n // 50
        )

    if (
        not isinstance(block_size, int)
        or not 20 <= block_size <= n
    ):
        raise ValueError(
            "Rozmiar bloku musi być liczbą "
            "całkowitą od 20 do n."
        )

    count = n // block_size

    if (
        block_size <= 0.01 * n
        or count >= 100
    ):
        raise ValueError(
            "Wymagane M > 0.01*n "
            "i mniej niż 100 bloków."
        )

    chi2 = 0.0

    for i in range(count):
        block = bits[
            i * block_size:
            (i + 1) * block_size
        ]

        proportion = (
            sum(int(bit) for bit in block)
            / block_size
        )

        chi2 += (
            4
            * block_size
            * (proportion - 0.5) ** 2
        )

    p = gammaincc(
        count / 2,
        chi2 / 2
    )

    note = (
        f"M={block_size}, "
        f"bloki={count}, "
        f"pominięte bity={n % block_size}"
    )

    return make_result(
        "Block Frequency",
        [p],
        alpha,
        note
    )


# 3. Runs Test
def runs_test(bits, alpha=0.01):
    n = validate_bits(bits)

    proportion = (
        sum(int(bit) for bit in bits)
        / n
    )

    if (
        abs(proportion - 0.5)
        >= 2 / sqrt(n)
    ):
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

    expected = (
        2
        * n
        * proportion
        * (1 - proportion)
    )

    denominator = (
        2
        * sqrt(2 * n)
        * proportion
        * (1 - proportion)
    )

    p = erfc(
        abs(runs - expected)
        / denominator
    )

    return make_result(
        "Runs",
        [p],
        alpha,
        f"Liczba serii={runs}",
    )


# 4. Longest Run of Ones Test
def longest_run_test(
    bits,
    alpha=0.01
):
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

    frequencies = (
        [0] * len(probabilities)
    )

    for i in range(count):
        current = 0
        longest = 0

        for bit in bits[
            i * size:
            (i + 1) * size
        ]:
            current = (
                current + 1
                if bit == 1
                else 0
            )

            longest = max(
                longest,
                current
            )

        category = min(
            max(
                longest - lower,
                0
            ),
            len(probabilities) - 1,
        )

        frequencies[category] += 1

    chi2 = sum(
        (
            observed
            - count * probability
        ) ** 2
        / (count * probability)
        for observed, probability
        in zip(
            frequencies,
            probabilities
        )
    )

    p = gammaincc(
        (
            len(probabilities) - 1
        ) / 2,
        chi2 / 2
    )

    note = (
        f"M={size}, "
        f"bloki={count}, "
        f"pominięte bity={n % size}"
    )

    return make_result(
        "Longest Run",
        [p],
        alpha,
        note
    )


def _psi_squared(bits, size):
    if size == 0:
        return 0.0

    n = len(bits)

    counts = [
        0
    ] * (2 ** size)

    pattern = 0

    for bit in bits[:size]:
        pattern = (
            pattern << 1
        ) | int(bit)

    mask = (
        2 ** size
    ) - 1

    for start in range(n):
        counts[pattern] += 1

        next_bit = int(
            bits[
                (start + size) % n
            ]
        )

        pattern = (
            (pattern << 1) & mask
        ) | next_bit

    return (
        (2 ** size / n)
        * sum(
            c * c
            for c in counts
        )
        - n
    )


# 5. Serial Test
def serial_test(
    bits,
    alpha=0.01,
    m=2
):
    n = validate_bits(bits)

    if (
        not isinstance(m, int)
        or m < 2
    ):
        raise ValueError(
            "Parametr m musi być "
            "liczbą całkowitą >= 2."
        )

    if (
        m
        >= n.bit_length() - 3
    ):
        return make_result(
            "Serial",
            [],
            alpha,
            "Za mało bitów dla wybranego m.",
        )

    psi_m = _psi_squared(
        bits,
        m
    )

    psi_previous = _psi_squared(
        bits,
        m - 1
    )

    psi_before = _psi_squared(
        bits,
        m - 2
    )

    delta1 = max(
        0.0,
        psi_m - psi_previous
    )

    delta2 = max(
        0.0,
        psi_m
        - 2 * psi_previous
        + psi_before,
    )

    p1 = gammaincc(
        2 ** (m - 2),
        delta1 / 2
    )

    p2 = gammaincc(
        2 ** (m - 3),
        delta2 / 2
    )

    return make_result(
        "Serial",
        [p1, p2],
        alpha,
        f"m={m}; wyniki p1 i p2",
    )


# 6. Approximate Entropy Test
def approximate_entropy_test(
    bits,
    alpha=0.01,
    m=2
):
    n = validate_bits(bits)

    if (
        not isinstance(m, int)
        or m < 1
    ):
        raise ValueError(
            "Parametr m musi być "
            "liczbą całkowitą >= 1."
        )

    if (
        m
        >= n.bit_length() - 6
    ):
        return make_result(
            "Approximate Entropy",
            [],
            alpha,
            "Za mało bitów dla wybranego m.",
        )

    def phi(size):
        counts = [
            0
        ] * (2 ** size)

        pattern = 0

        for bit in bits[:size]:
            pattern = (
                pattern << 1
            ) | int(bit)

        mask = (
            2 ** size
        ) - 1

        for start in range(n):
            counts[pattern] += 1

            next_bit = int(
                bits[
                    (start + size) % n
                ]
            )

            pattern = (
                (pattern << 1)
                & mask
            ) | next_bit

        return sum(
            (count / n)
            * log(count / n)
            for count in counts
            if count > 0
        )

    approximate_entropy = (
        phi(m)
        - phi(m + 1)
    )

    chi2 = max(
        0.0,
        2
        * n
        * (
            log(2)
            - approximate_entropy
        ),
    )

    p = gammaincc(
        2 ** (m - 1),
        chi2 / 2
    )

    return make_result(
        "Approximate Entropy",
        [p],
        alpha,
        (
            f"m={m}; "
            f"ApEn={approximate_entropy:.6f}"
        ),
    )


# 7. Autocorrelation Test
def autocorrelation_test(
    bits,
    alpha=0.01,
    lag=1
):
    n = validate_bits(bits)

    if (
        not isinstance(lag, int)
        or not 1 <= lag < n
    ):
        raise ValueError(
            "Przesunięcie lag musi być "
            "liczbą całkowitą od 1 do n-1."
        )

    pairs = n - lag

    different = sum(
        int(
            bits[i]
            != bits[i + lag]
        )
        for i in range(pairs)
    )

    p = binomtest(
        different,
        n=pairs,
        p=0.5,
        alternative="two-sided",
    ).pvalue

    correlation = (
        1
        - 2 * different / pairs
    )

    return make_result(
        "Autocorrelation",
        [p],
        alpha,
        (
            f"lag={lag}; "
            f"r={correlation:.6f}; "
            f"różniące się pary="
            f"{different}/{pairs}"
        ),
    )


def run_all_tests(
    bits,
    alpha=0.01
):
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

    return [
        function(
            bits,
            alpha=alpha
        )
        for function in functions
    ]