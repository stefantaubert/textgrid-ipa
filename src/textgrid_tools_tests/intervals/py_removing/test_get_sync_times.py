
from numpy.testing import assert_almost_equal

from textgrid_tools.intervals.removing import get_sync_times


def test_component():
  times = [
    (0, 2.001),
    (3, 4),
    (5.15, 6),
    (100, 100.123),
  ]

  result = get_sync_times(times)

  assert len(result) == 4
  assert_almost_equal(result[0], 0)
  assert_almost_equal(result[1], 0.999)
  assert_almost_equal(result[2], 2.149)
  assert_almost_equal(result[3], 96.149)
