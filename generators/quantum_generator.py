from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from generators.base_generator import RandomGenerator


class QuantumGenerator(RandomGenerator):

  def __init__(self):
    self.simulator = AerSimulator()

  def generate(self, length: int) -> list[int]:
    if length <= 0:
      raise ValueError("Length must be greater than 0.")

    circuit = QuantumCircuit(1, 1)

    circuit.h(0)
    circuit.measure(0, 0)

    transpiled_circuit = transpile(circuit, self.simulator)

    job = self.simulator.run(
      transpiled_circuit,
      shots=length,
      memory=True
    )

    result = job.result()
    memory = result.get_memory(transpiled_circuit)

    return [int(bit) for bit in memory]