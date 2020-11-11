import unittest

import numpy as np


class UnitTests(unittest.TestCase):
  def test(self):
    pass


if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(UnitTests)
  unittest.TextTestRunner(verbosity=2).run(suite)
