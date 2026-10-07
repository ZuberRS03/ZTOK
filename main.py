from cmath import sqrt

from generators.classical_generator import ClassicalGenerator
from generators.quantum_generator import QuantumGenerator
from generators.noisy_quantum_generator import NoisyQuantumGenerator

def display_main_menu():
    print()
    print("=== QUANTUM RANDOM NUMBER GENERATOR ===")
    print()
    print("1. Generate random sequence")
    print("2. Run statistical tests")
    print("3. Compare generators")
    print("0. Exit")

def display_generator_menu():
    print()
    print("Choose generator:")
    print("1. Classical PRNG")
    print("2. Quantum RNG - ideal simulator")
    print("3. Quantum RNG - noisy simulator")
    print("0. Back")

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

    length = get_sequence_length()

    if length is None:
        return

    if choice == "1":
        generator = ClassicalGenerator()
        bits = generator.generate(length)
        display_generated_sequence(bits)

    elif choice == "2":
        generator = QuantumGenerator()
        bits = generator.generate(length)
        display_generated_sequence(bits)

    elif choice == "3":
        generator = NoisyQuantumGenerator()
        bits = generator.generate(length)
        display_generated_sequence(bits)

    else:
        print("\nInvalid option.")


def run_statistical_tests():
    display_generator_menu()

    choice = input("\nChoice: ")

    if choice == "0":
        return

    length = get_sequence_length()

    if length is None:
        return

    print()
    print("Selected generator:")

    if choice == "1":
        print("Classical PRNG")

    elif choice == "2":
        print("Quantum RNG - ideal simulator")

    elif choice == "3":
        print("Quantum RNG - noisy simulator")

    else:
        print("Invalid option.")
        return

    print(f"Sequence length: {length}")

    # TODO: Create selected generator
    # TODO: Generate bit sequence
    # TODO: Run all implemented statistical tests
    # TODO: Display test names, p-values and PASS/FAIL results

    print()
    print("Statistical tests are not implemented yet.")


def compare_generators():
    length = get_sequence_length()

    if length is None:
        return

    print()
    print("Generators to compare:")
    print("- Classical PRNG")
    print("- Quantum RNG - ideal simulator")
    print("- Quantum RNG - noisy simulator")
    print("- Quantum RNG - real quantum hardware")

    print()
    print(f"Sequence length for each generator: {length}")

    # TODO: Generate sequences using all available generators
    # TODO: Run the same statistical tests for every generator
    # TODO: Measure generation time
    # TODO: Collect results
    # TODO: Display comparison table
    # TODO: Optionally save results to CSV
    # TODO: Optionally generate plots

    print()
    print("Generator comparison is not implemented yet.")


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

        elif choice == "0":
            print("\nExiting program.")
            break

        else:
            print("\nInvalid option.")


if __name__ == "__main__":
    main()
