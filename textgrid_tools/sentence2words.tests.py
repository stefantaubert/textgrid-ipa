import unittest

import numpy as np

from textgrid_tools.remove_silence import remove_from_array, remove_silence
from textgrid_tools.sentence2words import add_words


class UnitTests(unittest.TestCase):
  def test(self):
    pass


if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(UnitTests)
  unittest.TextTestRunner(verbosity=2).run(suite)
