
from numpy.testing import assert_almost_equal
from ordered_set import OrderedSet

from textgrid_tools.intervals.removing import get_sync_times


def test_component_last_equal_to_max_time():
  times = [
    (0, 2.2),  # 2.2
    (3, 4),  # 1.0
    (5.1, 6),  # 0.9
    (100, 100.5),  # 0.5
  ]

  result = get_sync_times(times, 100.5)

  assert len(result) == 4
  assert_almost_equal(result[0], 0)     # 0
  assert_almost_equal(result[1], 0.8)   # 3 - 2.2
  assert_almost_equal(result[2], 1.9)   # 5.1 - 2.2 - 1.0
  assert_almost_equal(result[3], 95.9)  # 100 - 2.2 - 1.0 - 0.9


def test_component_last_differs_from_max_time():
  times = [
    (0, 2.2),  # 2.2
    (3, 4),  # 1.0
    (5.1, 6),  # 0.9
    (100, 100.5),  # 0.5
  ]

  result = get_sync_times(times, 100.6)

  assert len(result) == 5
  assert_almost_equal(result[0], 0)     # 0
  assert_almost_equal(result[1], 0.8)   # 3 - 2.2
  assert_almost_equal(result[2], 1.9)   # 5.1 - 2.2 - 1.0 = 5.1 - 3.2
  assert_almost_equal(result[3], 95.9)  # 100 - 2.2 - 1.0 - 0.9 = 100 - 4.1
  assert_almost_equal(result[4], 96)  # 100.6 - 2.2 - 1.0 - 0.9 - 0.5 = 100.6 - 4.6


def test_empty__returns_empty():
  result = get_sync_times(set(), 1.5)
  assert result == OrderedSet()


def test_one_interval_equals_to_max_time__returns_min_time():
  times = [
    (0.5, 2.2),
  ]

  result = get_sync_times(times, 2.2)

  assert len(result) == 1
  assert_almost_equal(result[0], 0.5)


def test_one_interval_and_max_time_equals_to_max_time__returns_min_time():
  times = [
    (0.5, 2.2),
  ]

  result = get_sync_times(times, 2.2)

  assert len(result) == 1
  assert_almost_equal(result[0], 0.5)


def test_one_interval_and_max_time_equals_not_to_max_time__returns_min_time_and_adj_max_time():
  times = [
    (0.5, 2.2),
  ]

  result = get_sync_times(times, 2.3)

  assert len(result) == 2
  assert_almost_equal(result[0], 0.5)
  assert_almost_equal(result[1], 0.6)


def test_two_intervals_last_equals_to_max_time__returns_two_timepoints():
  times = [
    (0.5, 2.2),
    (2.3, 2.4),
  ]

  result = get_sync_times(times, 2.4)

  assert len(result) == 2
  assert_almost_equal(result[0], 0.5)
  assert_almost_equal(result[1], 0.6)
