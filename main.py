from generators.classical_generator import ClassicalGenerator
from generators.quantum_generator import QuantumGenerator
from generators.noisy_quantum_generator import NoisyQuantumGenerator

from tests.statistical_tests import run_all_tests

from experiments.generator_comparison import run_generator_comparison
from experiments.noise_experiment import run_noise_experiment

from plots.generator_comparison_plots import generate_comparison_plots
from plots.noise_plots import generate_noise_plots


def display_main_menu():
    print()
    print("=== QUANTUM RANDOM NUMBER GENERATOR ===")
    print()
    print("1. Generate random sequence")
    print("2. Run statistical tests")
    print("3. Compare generators")
    print("4. Analyze noise influence")
    print("0. Exit")


def display_generator_menu():
    print()
    print("Choose generator:")
    print("1. Classical PRNG")
    print("2. Quantum RNG - ideal simulator")
    print("3. Quantum RNG - noisy simulator")
    print("0. Back")


def create_generator(choice):
    if choice == "1":
        return ClassicalGenerator()

    if choice == "2":
        return QuantumGenerator()

    if choice == "3":
        return NoisyQuantumGenerator()

    return None


def display_generated_sequence(bits: list[int]):
    light_blue = "\033[94m"
    reset = "\033[0m"

    print()
    print(f"Generated {len(bits)} bits:")

    if len(bits) <= 100:
        sequence = "".join(map(str, bits))
        print(f"{light_blue}{sequence}{reset}")
    else:
        sequence = "".join(map(str, bits[:100]))
        print(f"{light_blue}{sequence}...{reset}")
        print("(showing first 100 bits)")


def display_test_results(results):
    green = "\033[92m"
    red = "\033[91m"
    yellow = "\033[93m"
    reset = "\033[0m"

    print()
    print("=== STATISTICAL TEST RESULTS ===")
    print()

    for result in results:
        name = result["name"]
        status = result["status"]
        p_values = result["p_values"]
        note = result["note"]

        if status == "PASS":
            status_text = f"{green}{status}{reset}"
        elif status == "FAIL":
            status_text = f"{red}{status}{reset}"
        else:
            status_text = f"{yellow}{status}{reset}"

        if len(p_values) == 1:
            p_text = f"p = {p_values[0]:.6f}"
        elif len(p_values) == 2:
            p_text = (
                f"p1 = {p_values[0]:.6f}, "
                f"p2 = {p_values[1]:.6f}"
            )
        else:
            p_text = "no p-value"

        print(
            f"{name:<22} "
            f"{status_text:<15} "
            f"{p_text}"
        )

        if note:
            print(f"  {note}")


def get_sequence_length():
    try:
        length = int(input("Number of bits to generate: "))

        if length <= 0:
            print("Number of bits must be greater than 0.")
            return None

        return length

    except ValueError:
        print("Invalid number.")
        return None


def generate_sequence():
    display_generator_menu()

    choice = input("\nChoice: ")

    if choice == "0":
        return

    generator = create_generator(choice)

    if generator is None:
        print("\nInvalid option.")
        return

    length = get_sequence_length()

    if length is None:
        return

    bits = generator.generate(length)

    display_generated_sequence(bits)


def run_statistical_tests():
    display_generator_menu()

    choice = input("\nChoice: ")

    if choice == "0":
        return

    generator = create_generator(choice)

    if generator is None:
        print("\nInvalid option.")
        return

    length = get_sequence_length()

    if length is None:
        return

    if length < 100:
        print(
            "\nStatistical tests require "
            "at least 100 bits."
        )
        return

    print()
    print("Generating sequence...")

    bits = generator.generate(length)

    print("Running statistical tests...")

    results = run_all_tests(bits)

    display_test_results(results)


def compare_generators():
    print()
    print("=== GENERATOR COMPARISON ===")
    print()
    print("This experiment will compare:")
    print("- Classical PRNG")
    print("- Quantum RNG - ideal simulator")
    print("- Quantum RNG - noisy simulator")
    print()

    output = run_generator_comparison()

    print()
    print("Generating plots...")

    generate_comparison_plots(output)

    print()
    print("Generator comparison completed.")
    print(f"Results saved to: {output}")


def analyze_noise():
    print()
    print("=== NOISE INFLUENCE ANALYSIS ===")
    print()

    output = run_noise_experiment()

    print()
    print("Generating plots...")

    generate_noise_plots(output)

    print()
    print("Noise analysis completed.")
    print(f"Results saved to: {output}")


def main():
    while True:
        display_main_menu()

        choice = input("\nChoice: ")

        if choice == "1":
            generate_sequence()

        elif choice == "2":
            run_statistical_tests()

        elif choice == "3":
            compare_generators()

        elif choice == "4":
            analyze_noise()

        elif choice == "0":
            print("\nExiting program.")
            break

        else:
            print("\nInvalid option.")


if __name__ == "__main__":
    main()