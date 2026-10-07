from abc import ABC, abstractmethod


class RandomGenerator(ABC):

  @abstractmethod
  def generate(self, length: int) -> list[int]:
    """
    Generates a sequence of random bits.

    Args:
      length: Number of bits to generate.

    Returns:
      List containing 0 and 1 values.
    """
    pass