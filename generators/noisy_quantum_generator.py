from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError

from generators.base_generator import RandomGenerator


class NoisyQuantumGenerator(RandomGenerator):

  def __init__(
    self,
    error_0_to_1: float = 0.02,
    error_1_to_0: float = 0.08
  ):
    if not 0 <= error_0_to_1 <= 1:
      raise ValueError("error_0_to_1 must be between 0 and 1.")

    if not 0 <= error_1_to_0 <= 1:
      raise ValueError("error_1_to_0 must be between 0 and 1.")

    self.error_0_to_1 = error_0_to_1
    self.error_1_to_0 = error_1_to_0

    self.noise_model = self._create_noise_model()

    self.simulator = AerSimulator(
      noise_model=self.noise_model
    )

  def _create_noise_model(self) -> NoiseModel:
    noise_model = NoiseModel()

    readout_error = ReadoutError([
      [
        1 - self.error_0_to_1,
        self.error_0_to_1
      ],
      [
        self.error_1_to_0,
        1 - self.error_1_to_0
      ]
    ])

    noise_model.add_all_qubit_readout_error(readout_error)

    return noise_model

  def generate(self, length: int) -> list[int]:
    if length <= 0:
      raise ValueError("Length must be greater than 0.")

    circuit = QuantumCircuit(1, 1)

    circuit.h(0)
    circuit.measure(0, 0)

    transpiled_circuit = transpile(
      circuit,
      self.simulator
    )

    job = self.simulator.run(
      transpiled_circuit,
      shots=length,
      memory=True
    )

    result = job.result()
    memory = result.get_memory(transpiled_circuit)

    return [int(bit) for bit in memory]