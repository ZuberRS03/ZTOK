import numpy as np

from generators.base_generator import RandomGenerator


class ClassicalGenerator(RandomGenerator):

  def generate(self, length: int) -> list[int]:
    if length <= 0:
      raise ValueError("Length must be greater than 0.")

    bits = np.random.randint(0, 2, size=length)

    return bits.tolist()